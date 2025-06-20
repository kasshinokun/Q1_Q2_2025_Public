package estagio3.addons;
import java.io.*;
import java.nio.file.Files; // Usado para leitura conveniente de arquivos para verificação
import java.nio.file.Paths; // Usado para leitura conveniente de arquivos para verificação
import java.util.*;

public class LZ78Unified {
	// --- Método Principal para Teste e Execução ---
    public static void main(String[] args) {
    	createSampleData();
    }
    public static void demonstrationLZW() {
        System.out.println("----------- Processo LZ78 versão estável (Baseado no arquivo de dados da etapa 1) ----------------------------------------------------");

        // Define os caminhos dos arquivos para entrada, saída comprimida e saída descomprimida
        String inputFile = "LZW/traffic_accidents.db"; // Example input file name
        String compressedFile = "LZW/brazilian_portuguese_sample.lz78"; // Compressed output file
        String decompressedFile = "data/traffic_accidents.db"; // Decompressed output file
        
        // Verifica se o arquivo de entrada existe ou está vazio. Caso contrário, cria alguns dados de exemplo para teste.
        File testFile = new File(inputFile);
        if (!testFile.exists() || testFile.length() == 0) {
            System.out.println("Criando arquivo de entrada de exemplo com dados em português do Brasil: " + inputFile);
            createSampleData();
        }
        
        compressProcess(inputFile, compressedFile);
        decompressProcess(inputFile, compressedFile,  decompressedFile);
    
    }
    
    // --- Constantes ---
    private static final int INITIAL_DICTIONARY_SIZE = 256; // Para bytes únicos (0-255)
    private static final int MAX_DICTIONARY_SIZE = 65536; // Máximo de 2^16 entradas, incluindo o código de reset (0)
    // O número de bits necessários para representar MAX_DICTIONARY_SIZE - 1
    // Para 65536, são 16 bits (log2(65536) = 16).
    private static final int MAX_CODE_BITS = (int) Math.ceil(Math.log(MAX_DICTIONARY_SIZE) / Math.log(2));
    private static final int BUFFER_SIZE = 8192; // Tamanho do buffer de 8KB para streams bufferizados

    // Código especial para sinalizar um reset de dicionário (corresponde ao símbolo nulo 0 do código C)
    private static final int RESET_CODE = 0;
    // Número de bits para armazenar o MAX_DICTIONARY_SIZE no cabeçalho do arquivo (como no código C)
    private static final int DICTIONARY_SIZE_HEADER_BITS = 20;
    // Taxa de uso do dicionário para acionar um reset (corresponde ao DICT_MAX_USAGE_RATIO do código C)
    private static final double DICT_RESET_USAGE_RATIO = 0.8;


    // --- Classe Aninhada Privada para Nó da Trie (Dicionário de Compressão) ---
    // Esta classe representa um nó na Trie (árvore de prefixos) usada para o dicionário de compressão.
    // Cada nó armazena seus filhos (próximos bytes possíveis em uma sequência) e o código do dicionário
    // se o caminho para este nó forma uma sequência completa e reconhecida.
    private static class TrieNode {
        Map<Byte, TrieNode> children; // Mapeia um byte para o próximo TrieNode na sequência
        int code; // O código do dicionário atribuído à sequência que termina neste nó

        public TrieNode() {
            children = new HashMap<>();
            code = -1; // -1 indica que nenhum código foi atribuído ainda, significando que este nó não é o fim de uma entrada de dicionário
        }
    }

    // --- Classe Aninhada Estática Privada para Stream de Saída de Bits ---
    // Esta classe permite escrever dados bit a bit em um OutputStream subjacente.
    // Ela armazena bits em bytes e os escreve quando um byte completo é acumulado ou ao fechar.
    private static class BitOutputStream implements AutoCloseable {
        private BufferedOutputStream out; // O stream de saída bufferizado subjacente
        private int currentByte; // Armazena bits à medida que são acumulados (0-255)
        private int bitsInCurrentByte; // Conta quantos bits estão atualmente em currentByte (0-7)

        public BitOutputStream(OutputStream os) {
            this.out = new BufferedOutputStream(os);
            this.currentByte = 0;
            this.bitsInCurrentByte = 0;
        }

        /**
         * Escreve um número especificado de bits de um valor inteiro para o stream.
         * Os bits são escritos do mais significativo para o menos significativo.
         * @param value O valor inteiro do qual os bits serão escritos.
         * @param numBits O número de bits a serem escritos (1 a 32).
         * @throws IOException Se ocorrer um erro de E/S.
         * @throws IllegalArgumentException Se numBits estiver fora do intervalo ou o valor não couber em numBits.
         */
        public void writeBits(int value, int numBits) throws IOException {
            if (numBits <= 0 || numBits > 32) {
                throw new IllegalArgumentException("O número de bits deve estar entre 1 e 32.");
            }
            // Verifica se o valor se encaixa no número especificado de bits para valores positivos.
            // Isso é importante para garantir a integridade dos dados durante a compressão.
            // Para valores de 32 bits, (1 << numBits) transborda, então trate separadamente ou use 1L.
            if (numBits < 32 && (value < 0 || value >= (1 << numBits))) {
                 throw new IllegalArgumentException(String.format("O valor %d não cabe em %d bits.", value, numBits));
            }
            // Para numBits == 32, o valor pode ser qualquer int, então nenhuma verificação de intervalo é necessária para valores positivos.

            // Itera do bit mais significativo para o menos significativo
            for (int i = numBits - 1; i >= 0; i--) {
                // Extrai o i-ésimo bit do valor
                boolean bit = ((value >> i) & 1) == 1;

                // Define o bit correspondente em currentByte
                if (bit) {
                    currentByte |= (1 << (7 - bitsInCurrentByte)); // Define o bit da esquerda (MSB primeiro)
                }

                bitsInCurrentByte++; // Incrementa o contador de bits

                // Se um byte completo for acumulado, escreva-o no stream de saída
                if (bitsInCurrentByte == 8) {
                    out.write(currentByte);
                    currentByte = 0; // Reinicia o buffer de bytes
                    bitsInCurrentByte = 0; // Reinicia o contador de bits
                }
            }
        }

        /**
         * Escreve um único byte no stream. Quaisquer bits parciais atualmente armazenados em buffer são descarregados
         * como um byte completo antes de escrever o novo byte. Isso garante o alinhamento de bytes.
         * @param b O byte a ser escrito.
         * @throws IOException Se ocorrer um erro de E/S.
         */
        public void writeByte(byte b) throws IOException {
            // Descarrega quaisquer bits parciais restantes em currentByte antes de escrever um byte completo.
            // Isso garante que as leituras subsequentes sejam alinhadas por bytes.
            if (bitsInCurrentByte > 0) {
                out.write(currentByte);
                currentByte = 0;
                bitsInCurrentByte = 0;
            }
            out.write(b); // Escreve o byte real
        }

        /**
         * Fecha o BitOutputStream, descarregando quaisquer bits restantes em buffer.
         * @throws IOException Se ocorrer um erro de E/S durante o descarregamento ou fechamento do stream subjacente.
         */
        @Override
        public void close() throws IOException {
            // Descarrega quaisquer bits restantes que ainda não formaram um byte completo
            if (bitsInCurrentByte > 0) {
                out.write(currentByte);
            }
            out.close(); // Fecha o stream subjacente
        }
    }

    // --- Classe Aninhada Estática Privada para Stream de Entrada de Bits ---
    // Esta classe permite ler dados bit a bit de um InputStream subjacente.
    // Ela armazena bytes em buffer e fornece métodos para ler um número especificado de bits ou um byte completo.
    private static class BitInputStream implements AutoCloseable {
        private BufferedInputStream in; // O stream de entrada bufferizado subjacente
        private int currentByte; // Armazena o byte atual lido do stream
        private int bitsInCurrentByte; // Conta quantos bits restam em currentByte (0-8)
        private boolean eofReached = false; // Sinalizador para indicar se o EOF do stream subjacente foi atingido

        public BitInputStream(InputStream is) {
            this.in = new BufferedInputStream(is);
            this.currentByte = 0;
            this.bitsInCurrentByte = 0;
        }

        /**
         * Lê um único bit do stream.
         * @return 0 ou 1 se um bit for lido, ou -1 se o fim do stream for atingido.
         * @throws IOException Se ocorrer um erro de E/S.
         */
        private int readBit() throws IOException {
            // Se não houver bits restantes em currentByte, leia um novo byte do stream subjacente
            if (bitsInCurrentByte == 0) {
                int read = in.read();
                if (read == -1) {
                    eofReached = true; // Marca EOF quando o stream subjacente retorna -1
                    return -1; // Sinaliza EOF
                }
                currentByte = read; // Armazena o novo byte
                bitsInCurrentByte = 8; // Define o contador de bits para 8
            }

            // Extrai o bit mais significativo de currentByte
            int bit = (currentByte >> (bitsInCurrentByte - 1)) & 1;
            bitsInCurrentByte--; // Decrementa o contador de bits
            return bit;
        }

        /**
         * Lê um número especificado de bits do stream e reconstrói um inteiro.
         * Os bits são lidos do mais significativo para o menos significativo.
         * @param numBits O número de bits a serem lidos (1 a 32).
         * @return O valor inteiro reconstruído a partir dos bits.
         * @throws IOException Se ocorrer um erro de E/S ou fim inesperado do stream.
         * @throws IllegalArgumentException Se numBits estiver fora do intervalo.
         * @throws EOFException Se o fim do stream for atingido antes que todos os bits possam ser lidos.
         */
        public int readBits(int numBits) throws IOException {
            if (numBits <= 0 || numBits > 32) {
                throw new IllegalArgumentException("O número de bits deve estar entre 1 e 32.");
            }
            if (eofReached) { // Verifica o sinalizador EOF antes de tentar ler
                throw new EOFException("Tentativa de ler bits após o fim do stream.");
            }

            int value = 0;
            for (int i = 0; i < numBits; i++) {
                int bit = readBit();
                if (bit == -1) {
                    eofReached = true; // Garante que o sinalizador EOF seja definido em caso de falha de leitura parcial
                    throw new EOFException("Fim inesperado do stream ao ler " + numBits + " bits.");
                }
                value = (value << 1) | bit; // Adiciona o bit ao valor
            }
            return value;
        }

        /**
         * Lê um único byte do stream. Este método lida com casos em que o stream
         * pode não estar em um limite de byte após uma leitura de bits anterior, descartando os bits restantes.
         * @return O byte lido.
         * @throws IOException Se ocorrer um erro de E/S.
         * @throws EOFException Se o fim do stream for atingido.
         */
        public byte readByte() throws IOException {
            // Se houver bits parciais armazenados em buffer de uma chamada readBits() anterior,
            // descarte-os para alinhar ao próximo limite de byte completo.
            // Isso é crucial para o formato LZ78, onde um byte completo segue um código de comprimento variável.
            if (bitsInCurrentByte > 0) {
                currentByte = 0; // Limpa o byte parcial
                bitsInCurrentByte = 0; // Reinicia o contador de bits
            }
            // Agora, leia o próximo byte completo do stream subjacente.
            int b = in.read();
            if (b == -1) {
                eofReached = true;
                throw new EOFException("Fim inesperado do stream ao ler um byte.");
            }
            return (byte) b;
        }

        /**
         * Verifica se o fim do stream foi atingido.
         * @return true se for EOF, false caso contrário.
         */
        public boolean isEOF() {
            // O EOF é realmente atingido quando o stream subjacente atingiu o EOF e todos os bits armazenados em buffer foram consumidos.
            // Precisamos tentar uma leitura no stream subjacente para confirmar o EOF se bitsInCurrentByte for 0
            // e eofReached ainda não estiver definido (significando que ainda não tentamos ler além do último byte).
            if (bitsInCurrentByte == 0 && !eofReached) {
                try {
                    in.mark(1); // Marca a posição atual para redefinir mais tarde
                    if (in.read() == -1) { // Tenta ler um byte para verificar o EOF
                        eofReached = true;
                    }
                    in.reset(); // Redefine para a posição marcada
                } catch (IOException e) {
                    // Se ocorrer uma exceção durante mark/read/reset, é mais seguro assumir que não é EOF
                    // ou lidar com a exceção específica se ela indicar EOF. Por enquanto, apenas ignore.
                }
            }
            return eofReached && bitsInCurrentByte == 0;
        }

        /**
         * Fecha o BitInputStream.
         * @throws IOException Se ocorrer um erro de E/S durante o fechamento do stream subjacente.
         */
        @Override
        public void close() throws IOException {
            in.close();
        }
    }

    // --- Método de Compressão ---
    /**
     * Comprime o arquivo de entrada usando o algoritmo LZ78 e escreve os dados comprimidos no arquivo de saída.
     * Este método opera em streams de bytes, tornando-o agnóstico à codificação e adequado para qualquer tipo de arquivo,
     * incluindo texto codificado em UTF-8 com caracteres em português do Brasil.
     * @param inputFilePath O caminho para o arquivo de entrada a ser comprimido.
     * @param outputFilePath O caminho para o arquivo de saída onde os dados comprimidos serão gravados.
     * @throws IOException Se ocorrer um erro de E/S durante as operações de arquivo.
     */
    public void compress(String inputFilePath, String outputFilePath) throws IOException {
        TrieNode root = new TrieNode();
        int nextCode; // Próximo código disponível para novas sequências

        // Usa try-with-resources para fechamento automático de streams.
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(inputFilePath), BUFFER_SIZE);
             BitOutputStream bos = new BitOutputStream(new FileOutputStream(outputFilePath))) {

            // Escreve MAX_DICTIONARY_SIZE como um cabeçalho. Isso permite que o descompressor saiba o limite.
            bos.writeBits(MAX_DICTIONARY_SIZE, DICTIONARY_SIZE_HEADER_BITS);

            // Inicializa o dicionário para compressão.
            // O Código 0 é reservado para RESET_CODE. Códigos 1-256 para bytes únicos.
            // `nextCode` começará de INITIAL_DICTIONARY_SIZE + 1 (ou seja, 257).
            nextCode = initializeCompressionDictionary(root);

            // O número de bits necessários para representar os códigos atuais do dicionário.
            // Começa com 9 bits porque os códigos 1-256 cabem em 8, mas 257 precisa de 9.
            int currentCodeBits = 9;

            TrieNode currentNode = root; // Começa a correspondência a partir da raiz da Trie
            int byteRead;

            // Lê o arquivo de entrada byte a byte
            while ((byteRead = bis.read()) != -1) {
                byte currentByte = (byte) byteRead;

                // Tenta estender a sequência atual anexando o currentByte.
                TrieNode nextNode = currentNode.children.get(currentByte);

                if (nextNode != null) {
                    // A sequência estendida é encontrada no dicionário.
                    // Continua construindo a sequência atual movendo para o próximo nó na Trie.
                    currentNode = nextNode;
                } else {
                    // A sequência estendida NÃO é encontrada no dicionário.
                    // Isso significa que `currentNode` representa a sequência mais longa encontrada até agora que ESTÁ no dicionário.

                    // Saída do código para o `currentNode` (o prefixo mais longo correspondente).
                    bos.writeBits(currentNode.code, currentCodeBits);
                    // Saída do `currentByte` que causou a incompatibilidade. Este byte é anexado à
                    // sequência decodificada durante a descompressão.
                    bos.writeByte(currentByte);

                    // Adiciona a nova sequência (representada por `currentNode` + `currentByte`) ao dicionário.
                    // Esta nova sequência é o que `nextNode` teria sido se existisse.
                    if (nextCode < MAX_DICTIONARY_SIZE) {
                        TrieNode newNode = new TrieNode();
                        newNode.code = nextCode++; // Atribui um novo código a esta nova sequência
                        currentNode.children.put(currentByte, newNode); // Adiciona-o à Trie

                        // Aumenta dinamicamente o número de bits usados para códigos se o tamanho do dicionário
                        // ultrapassar um limite de potência de 2. Isso garante que todos os códigos possam ser representados.
                        if (nextCode > (1 << currentCodeBits) && currentCodeBits < MAX_CODE_BITS) {
                            currentCodeBits++;
                        }
                    }

                    // Verifica se o dicionário precisa ser reiniciado
                    if (nextCode >= MAX_DICTIONARY_SIZE * DICT_RESET_USAGE_RATIO && nextCode < MAX_DICTIONARY_SIZE) {
                        // Escreve o RESET_CODE especial para sinalizar o descompressor
                        bos.writeBits(RESET_CODE, currentCodeBits); // Usa currentCodeBits para o código de reset
                        // Reinicializa o dicionário
                        root = new TrieNode(); // Limpa a Trie antiga
                        nextCode = initializeCompressionDictionary(root); // Preenche novamente com os bytes iniciais
                        currentCodeBits = 9; // Reinicia os bits do código para o valor inicial
                    }

                    // Reinicia `currentNode` para o nó que representa o `currentByte`.
                    // Este `currentByte` se torna o início da próxima pesquisa de sequência.
                    // É garantido que esteja no dicionário porque todos os bytes únicos são pré-inicializados.
                    currentNode = root.children.get(currentByte);
                }
            }

            // Após o loop, se `currentNode` não for a raiz (significando que os últimos bytes formaram uma sequência
            // que foi encontrada no dicionário até o EOF), gera seu código.
            // Não há byte final para esta última sequência.
            if (currentNode != root && currentNode.code != -1) {
                bos.writeBits(currentNode.code, currentCodeBits);
            }
        }
    }

    // Auxiliar para inicializar/reiniciar o dicionário de compressão
    // Retorna o próximo código disponível após a inicialização
    private int initializeCompressionDictionary(TrieNode root) {
        root.children.clear(); // Limpa as entradas existentes na Trie
        // Os códigos começam em 1 para bytes únicos (0-255). O Código 0 é RESET_CODE.
        int codeCounter = 1;
        for (int i = 0; i < INITIAL_DICTIONARY_SIZE; i++) {
            TrieNode node = new TrieNode();
            node.code = codeCounter++; // Atribui códigos 1-256 para bytes 0-255
            root.children.put((byte) i, node);
        }
        return codeCounter; // Retorna 257 (o próximo código para novas sequências)
    }


    // --- Método de Descompressão ---
    /**
     * Descomprime o arquivo de entrada (comprimido com LZ78) e escreve os dados originais no arquivo de saída.
     * Este método também opera em streams de bytes, reconstruindo corretamente as sequências de bytes originais,
     * incluindo aquelas que representam caracteres UTF-8 multi-byte.
     * @param inputFilePath O caminho para o arquivo de entrada comprimido.
     * @param outputFilePath O caminho para o arquivo de saída onde os dados descomprimidos serão gravados.
     * @throws IOException Se ocorrer um erro de E/S durante as operações de arquivo ou se o arquivo comprimido estiver corrompido.
     */
    public void decompress(String inputFilePath, String outputFilePath) throws IOException {
        List<byte[]> dictionary = new ArrayList<>(); // Dicionário de descompressão
        int nextCode; // Próximo código disponível para novas sequências

        // Usa try-with-resources para fechamento automático de streams.
        try (BitInputStream bis = new BitInputStream(new FileInputStream(inputFilePath));
             BufferedOutputStream bos = new BufferedOutputStream(new FileOutputStream(outputFilePath), BUFFER_SIZE)) {

            // Lê MAX_DICTIONARY_SIZE do cabeçalho
            int maxDictSizeFromHeader = bis.readBits(DICTIONARY_SIZE_HEADER_BITS);
            // Opcionalmente, valida maxDictSizeFromHeader em relação à constante MAX_DICTIONARY_SIZE.
            // Para simplificar, assumiremos que eles correspondem.

            // Inicializa o dicionário para descompressão.
            // O Código 0 é reservado para RESET_CODE. Códigos 1-256 para bytes únicos.
            nextCode = initializeDecompressionDictionary(dictionary);

            // O número de bits esperado para ler os códigos atuais do dicionário.
            // Começa com 9 bits porque os códigos 1-256 cabem em 8, mas 257 precisa de 9.
            int currentCodeBits = 9;

            byte[] previousSequence = null; // Armazena a sequência decodificada anteriormente
            boolean isFirstCodeOfSegment = true; // Sinalizador para rastrear se é o primeiro código após o cabeçalho ou reset

            // Lê códigos e bytes do arquivo comprimido
            while (true) {
                int code;
                try {
                    code = bis.readBits(currentCodeBits); // Lê o próximo código
                } catch (EOFException e) {
                    break; // Fim do arquivo atingido, sai do loop
                }

                // Verifica o código de reset do dicionário
                if (code == RESET_CODE) {
                    // Reinicializa o dicionário
                    nextCode = initializeDecompressionDictionary(dictionary);
                    currentCodeBits = 9; // Reinicia os bits do código para o valor inicial
                    previousSequence = null; // Reinicia a sequência anterior
                    isFirstCodeOfSegment = true; // O próximo código será o primeiro de um novo segmento
                    continue; // Pula para a próxima iteração para ler o próximo código/byte real
                }

                byte newByte;
                try {
                    newByte = bis.readByte(); // Lê o byte associado ao código
                } catch (EOFException e) {
                    // Isso lida com o caso especial da última sequência no arquivo,
                    // que é apenas um código sem um byte final.
                    if (code < dictionary.size()) {
                        byte[] sequence = dictionary.get(code); // Recupera a sequência para o último código
                        bos.write(sequence); // Escreve no output
                    } else {
                        // Este caso teoricamente não deveria acontecer se o arquivo comprimido for válido
                        // e a lógica de compressão estiver correta para a última sequência.
                        throw new IOException("Erro de descompressão: EOF inesperado após o código " + code +
                                ". Possível arquivo corrompido ou erro de lógica de compressão para a última sequência.");
                    }
                    break; // Sai do loop após lidar com o último código
                }

                byte[] decodedSequence;
                // Verifica se o código lido já está no dicionário
                if (code < dictionary.size()) {
                    decodedSequence = dictionary.get(code); // Recupera a sequência diretamente
                } else {
                    // Verificação de diagnóstico: Se for o primeiro código de um segmento e não estiver no intervalo inicial do dicionário, é um erro.
                    if (isFirstCodeOfSegment) {
                        throw new IOException("Erro de descompressão: O primeiro código do segmento (" + code + ") é inválido. Esperado 1-" + INITIAL_DICTIONARY_SIZE + ".");
                    }
                    // Este é o caso "K-K-c" (código == dictionary.size()).
                    // Isso significa que o código se refere à sequência que está *prestes a ser adicionada* ao dicionário.
                    // Esta sequência é formada pela `previousSequence` mais o `newByte`.
                    if (previousSequence == null) {
                        // Isso idealmente não deveria ser alcançado se a verificação `isFirstCodeOfSegment` estiver correta
                        // e o stream comprimido for válido. Implica uma falha lógica mais profunda ou corrupção.
                        throw new IOException("Erro de descompressão: Código inválido " + code + " (previousSequence é nulo, mas não é o primeiro código do segmento).");
                    }
                    // Constrói a nova sequência: previousSequence + newByte
                    decodedSequence = Arrays.copyOf(previousSequence, previousSequence.length + 1);
                    decodedSequence[previousSequence.length] = newByte;
                }

                // Escreve a sequência decodificada no arquivo de saída
                bos.write(decodedSequence);

                // Adiciona a nova sequência (decodedSequence + newByte) ao dicionário.
                // Esta nova entrada é formada a partir da sequência decodificada *atual* e do `currentByte` *atual*.
                // Aplica-se a todas as entradas, desde que o dicionário não esteja cheio.
                if (nextCode < maxDictSizeFromHeader) { // Usa o tamanho máximo do dicionário do cabeçalho
                    byte[] newEntry = Arrays.copyOf(decodedSequence, decodedSequence.length + 1);
                    newEntry[decodedSequence.length] = newByte; // Anexa o newByte
                    dictionary.add(newEntry); // Adiciona a nova sequência ao dicionário
                    nextCode++; // Incrementa o próximo código disponível

                    // Aumenta dinamicamente o número de bits para códigos, espelhando a lógica de compressão.
                    if (nextCode > (1 << currentCodeBits) && currentCodeBits < MAX_CODE_BITS) {
                        currentCodeBits++;
                    }
                }

                // Atualiza `previousSequence` para a sequência que acabou de ser decodificada.
                // Isso será usado na próxima iteração para formar novas entradas de dicionário.
                previousSequence = decodedSequence;
                isFirstCodeOfSegment = false; // Não é mais o primeiro código do segmento
            }
        }
    }

    // Auxiliar para inicializar/reiniciar o dicionário de descompressão
    // Retorna o próximo código disponível após a inicialização
    private int initializeDecompressionDictionary(List<byte[]> dictionary) {
        dictionary.clear();
        dictionary.add(null); // Índice 0 reservado para RESET_CODE
        int codeCounter = 1; // Os códigos para bytes únicos começam em 1
        for (int i = 0; i < INITIAL_DICTIONARY_SIZE; i++) {
            dictionary.add(new byte[]{(byte) i}); // Os códigos 1-256 mapeiam para bytes 0-255
            codeCounter++;
        }
        return codeCounter; // Retorna 257 (o próximo código para novas sequências)
    }
    // ---Processo de Compressão ---
    public static void compressProcess(String inputFile, String compressedFile) {
    	LZ78Unified lz78 = new LZ78Unified(); // Cria uma instância do algoritmo LZ78 unificado
        System.out.println("Processo de Compressão ---------------------------------------------------------");
        try {
            long startTime = System.currentTimeMillis(); // Registra o tempo de início para a compressão
            lz78.compress(inputFile, compressedFile); // Executa a compressão
            long endTime = System.currentTimeMillis(); // Registra o tempo de fim
            System.out.println("Compressão bem-sucedida! Tempo gasto: " + (endTime - startTime) + "ms");
            long inputSize = getSize(inputFile);
            long compressedSize = getSize(compressedFile);
            System.out.println("Tamanho de entrada: " + inputSize + " bytes");
            System.out.println("Tamanho comprimido: " + compressedSize + " bytes");
            if (inputSize > 0) {
                float compressionPercentage = ((float) compressedSize / inputSize) * 100;
                System.out.println(String.format("Porcentagem de compressão: %.2f%% do arquivo original.", compressionPercentage));
            } else {
                System.out.println("Não é possível calcular a porcentagem de compressão para um arquivo de entrada vazio.");
            }
        } catch (IOException e) {
            System.err.println("A compressão falhou: " + e.getMessage());
            e.printStackTrace(); // Imprime o rastreamento da pilha para depuração
        }
    }
    // ---Processo de Descompressão ---
    public static void decompressProcess(String inputFile,String compressedFile, String decompressedFile) {
    	LZ78Unified lz78 = new LZ78Unified(); // Cria uma instância do algoritmo LZ78 unificado
    	System.out.println("\nProcesso de Descompressão -------------------------------------------------------");
        try {
            long startTime = System.currentTimeMillis(); // Registra o tempo de início para a descompressão
            lz78.decompress(compressedFile, decompressedFile); // Executa a descompressão
            long endTime = System.currentTimeMillis(); // Registra o tempo de fim
            System.out.println("Descompressão bem-sucedida! Tempo gasto: " + (endTime - startTime) + "ms");
            long decompressedSize = getSize(decompressedFile);
            System.out.println("Tamanho descomprimido: " + decompressedSize + " bytes");
        } catch (IOException e) {
            System.err.println("A descompressão falhou: " + e.getMessage());
            e.printStackTrace(); // Imprime o rastreamento da pilha para depuração
        }

        // Verifica se os arquivos original e descomprimido são idênticos (para arquivos menores)
        try {
            // Realiza a verificação byte a byte apenas para arquivos menores que 1MB para evitar problemas de memória com arquivos muito grandes.
            if (getSize(inputFile) < 1000000) {
                byte[] original = Files.readAllBytes(Paths.get(inputFile));
                byte[] decompressed = Files.readAllBytes(Paths.get(decompressedFile));
                if (Arrays.equals(original, decompressed)) {
                    System.out.println("\nVerificação: Os arquivos original e descomprimido são idênticos.");
                } else {
                    System.err.println("\nVerificação: Incompatibilidade entre os arquivos original e descomprimido!");
                }
            } else {
                System.out.println("\nPulando a verificação byte a byte para arquivos grandes (>" + (1000000 / (1024 * 1024)) + "MB).");
            }
        } catch (IOException e) {
            System.err.println("Erro durante a verificação: " + e.getMessage());
        }
        System.out.println("----------- Processo Concluído ----------------------------------------------------");
    }

    // --- Método Auxiliar para Obter o Tamanho do Arquivo ---
    /**
     * Retorna o tamanho de um arquivo em bytes.
     * @param filename O caminho para o arquivo.
     * @return O tamanho do arquivo em bytes, ou -1 se o arquivo não existir ou ocorrer um erro.
     */
    public static long getSize(String filename) {
        File file = new File(filename);
        if (file.exists()) {
            return file.length();
        }
        return -1; // Indica que o arquivo não foi encontrado ou ocorreu um erro
    }

    // --- Método Auxiliar para Criar Dados de Exemplo para Teste ---
    /**
     * Cria um arquivo de entrada fictício com dados de texto repetitivos para testar a compressão e descompressão.
     * Este método usa explicitamente a codificação UTF-8 para escrever os dados de exemplo.
     * @param filePath O caminho onde o arquivo de exemplo será criado.
     */
    public static void createSampleData() {
    	 String filePath = "LZW/brazilian_portuguese_sample.txt"; // Nome do arquivo de entrada de exemplo
         String compressedFile = "LZW/brazilian_portuguese_sample.lz78"; // Arquivo de saída comprimido
         String decompressedFile = "LZW/brazilian_portuguese_sample_decompressed.txt"; // Arquivo de saída descomprimido
    	
    	
        try (OutputStreamWriter writer = new OutputStreamWriter(new FileOutputStream(filePath), "UTF-8")) {
            // Uma string repetitiva com caracteres em português do Brasil para demonstrar a eficácia da compressão
            // para sequências UTF-8 multi-byte.
            String data = "Olá! Este é um exemplo de texto em português do Brasil para compressão LZ78. " +
                          "A compressão de dados é uma área fascinante. " +
                          "Vamos ver como o algoritmo lida com caracteres como 'ç', 'ã', 'é', 'í', 'ó', 'ú'. " +
                          "Repetindo a frase para melhor compressão: ";
            // Repete os dados várias vezes para tornar o arquivo um pouco maior para resultados de compressão mais significativos
            for (int i = 0; i < 2; i++) { // Repetições reduzidas ligeiramente para teste mais rápido
                writer.write(data);
            }
            // Adiciona alguns dados únicos no final para garantir que o tratamento de EOF seja robusto e a última sequência seja tratada corretamente
            writer.write("FIM_DO_ARQUIVO_MARCADOR_XYZ.");
        } catch (IOException e) {
            System.err.println("Erro ao criar o arquivo de dados de exemplo: " + e.getMessage());
            e.printStackTrace();
        }
        compressProcess(filePath, compressedFile);
        decompressProcess(filePath, compressedFile,  decompressedFile);
    }
}






        

        