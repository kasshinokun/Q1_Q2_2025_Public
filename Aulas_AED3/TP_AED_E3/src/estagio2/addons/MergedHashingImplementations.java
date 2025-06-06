package estagio2.addons;
import java.io.*;
import java.nio.ByteBuffer; // Mantido do original, embora não explicitamente usado na lógica mesclada
import java.nio.channels.FileChannel; // Mantido do original, embora não explicitamente usado na lógica mesclada
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Stream;
import java.util.zip.CRC32;
import java.nio.charset.StandardCharsets; // Adicionado para conversão robusta de string para byte

public class MergedHashingImplementations {
    private static final String FB_CSV_FILE = "src/estagio2/addons/persons_for_fb_hashing.csv";
    private static final String FB_HASH_STORAGE_FILE = "src/estagio2/addons/extendible_hash_storage.dat"; // Para diretório, páginas, metadados
    private static final String FB_EXTERNAL_DATA_RECORDS_FILE = "src/estagio2/addons/persons_external_records.dat"; // Dados reais da pessoa

    public static void main(String[] args) {
        System.out.println("Iniciando a Suíte de Testes de Implementações de Hashing...");
        System.out.println("Data/Hora Atual: " + new Date());
        System.out.println("Diretório de trabalho atual: " + Paths.get(".").toAbsolutePath().normalize().toString());
        System.out.println("Nota: As operações de arquivo dependem das permissões da IDE/ambiente.");

        ExtensibleHashingCSV.runExtensibleHashingCSV();
        System.out.println("\n=================================================\n");
        MergedHashingImplementations.runFileBasedExtendibleHashing();

        System.out.println("\nSuíte de Testes de Implementações de Hashing Finalizada.");
        System.out.println("Verifique o console para saída, erros e arquivos .dat/.csv criados.");
    }
    
    
    
    
    private FileBasedEHash<Integer, Long> extendibleHash;
    private RandomAccessFile hashStorageRaf; // RAF para a estrutura de hash em si
    // RAF para externalDataStorageFile é gerenciado por operação para simplicidade ou pode ser um membro

    public MergedHashingImplementations() throws IOException {
        hashStorageRaf = new RandomAccessFile(FB_HASH_STORAGE_FILE, "rw");

        FileBasedDirectory directory = new FileBasedDirectory(hashStorageRaf);
        FileBasedDataStore dataStore = new FileBasedDataStore(hashStorageRaf); // Ambos usam o mesmo RAF
        this.extendibleHash = new FileBasedEHash<>(directory, dataStore, hashStorageRaf); // Metadados também no mesmo RAF
    }

    public void processCSVAndStorePositions() throws IOException {
        // Cria CSV de teste se não existir
        File csvFileObj = new File(FB_CSV_FILE);
        if (!csvFileObj.exists()) {
            System.out.println("Criando CSV de teste para FileBasedHashing: " + FB_CSV_FILE);
            try (PrintWriter writer = new PrintWriter(csvFileObj)) {
                Random random = new Random();
                for (int i = 1; i <= 210000; i++) { // Suficiente para causar algumas divisões
                    writer.println(i + ", Person " + i + ", Age " + random.nextInt(18, 80));
                }
            }
        }
        
        try (RandomAccessFile externalDataRaf = new RandomAccessFile(FB_EXTERNAL_DATA_RECORDS_FILE, "rw")) {
            externalDataRaf.setLength(0); // Limpar dados externos existentes

            try (Stream<String> lines = Files.lines(Paths.get(FB_CSV_FILE), StandardCharsets.UTF_8)) {
                long currentPosition = 0;
                for (String line : (Iterable<String>) lines::iterator) {
                    if (line.trim().isEmpty()) continue;
                    String[] parts = line.split(",");
                    if (parts.length > 0) {
                        try {
                            int id = Integer.parseInt(parts[0].trim());
                            externalDataRaf.seek(currentPosition);
                            externalDataRaf.writeInt(id); // Armazenar ID para verificação
                            externalDataRaf.writeUTF(line); // Armazenar linha completa (UTF gerencia o comprimento)

                            extendibleHash.put(id, currentPosition); // Armazenar deslocamento do início do registro
                            currentPosition = externalDataRaf.getFilePointer(); // Atualizar para o próximo registro

                        } catch (NumberFormatException e) {
                            System.err.println("Pulando ID inválido em FileBasedHashing: " + parts[0]);
                        } catch (IOException e) {
                            System.err.println("IOException durante o processamento CSV para FileBasedHashing (ID: " + parts[0] + "): " + e.getMessage());
                            e.printStackTrace(); // Mais detalhes
                        }
                    }
                }
            }
        } // externalDataRaf é fechado aqui por try-with-resources
        
        extendibleHash.save();
        System.out.println("Processamento CSV e armazenamento de FileBasedHashing concluídos.");
    }

    public String getPersonData(int id) throws IOException {
        Long position = extendibleHash.get(id);
        if (position != null) {
            try (RandomAccessFile raf = new RandomAccessFile(FB_EXTERNAL_DATA_RECORDS_FILE, "r")) {
                raf.seek(position);
                int retrievedId = raf.readInt();
                String line = raf.readUTF();
                if (retrievedId == id) {
                    return line;
                } else {
                    System.err.println("FB Hashing: ID incompatível no deslocamento para a chave " + id + ". Esperado " + id + ", encontrado " + retrievedId);
                    return null;
                }
            }
        }
        return null;
    }

    public void close() throws IOException {
        if (extendibleHash != null) extendibleHash.close(); // Salva metadados do hash
        if (hashStorageRaf != null) hashStorageRaf.close();
        System.out.println("Recursos de FileBasedExtendibleHashing fechados.");
    }

    public static void runFileBasedExtendibleHashing() {
        System.out.println("\n--- Executando Teste de FileBasedExtendibleHashing ---\n");
        
        //Exclusão de arquivos
        new File(FB_CSV_FILE).delete();
        new File(FB_HASH_STORAGE_FILE).delete();
        new File(FB_EXTERNAL_DATA_RECORDS_FILE).delete();

        MergedHashingImplementations storage = null;
        try {
            storage = new MergedHashingImplementations();
            storage.processCSVAndStorePositions();

            int[] searchIds = {1, 15, 30, 49, 50, 100, 7,210000}; // Testa existentes e não existentes
            for (int searchId : searchIds) {
                System.out.println("\nBuscando pessoa com ID (FB): " + searchId);
                String personData = storage.getPersonData(searchId);
                if (personData != null) {
                    System.out.println("Dados para o ID " + searchId + ": " + personData);
                } else {
                    System.out.println("Pessoa com ID " + searchId + " não encontrada.");
                }
            }

        } catch (IOException e) {
            System.err.println("Erro durante a operação de armazenamento de FileBasedHashing: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) { // Captura quaisquer outras exceções de tempo de execução inesperadas
            System.err.println("Erro geral durante a operação de armazenamento de FileBasedHashing: " + e.getMessage());
            e.printStackTrace();
        } finally {
            if (storage != null) {
                try {
                    storage.close();
                } catch (IOException e) {
                    System.err.println("Erro ao fechar o armazenamento de FileBasedHashing: " + e.getMessage());
                }
            }
        }
        System.out.println("--- Teste de FileBasedExtendibleHashing Finalizado ---");
    }

    
}



// --- Shared Helper Classes/Interfaces ---

interface Entry<K, V> {
    K key();
    V value();

    static <K, V> Entry<K, V> createEntry(K key, V value) {
        return new SimpleEntry<>(key, value);
    }
}

class SimpleEntry<K, V> implements Entry<K, V> {
    private final K key;
    private final V value;

    public SimpleEntry(K key, V value) {
        this.key = key;
        this.value = value;
    }

    @Override
    public K key() {
        return key;
    }

    @Override
    public V value() {
        return value;
    }

    @Override
    public String toString() {
        return "Entry{" + "key=" + key + ", value=" + value + '}';
    }
}

class EHashStats {
    // Espaço reservado para estatísticas, pode ser expandido
    @Override
    public String toString() {
        return " EHashStats{}"; // Representação básica
    }
}

interface Page<K, V> {
    boolean contains(K key) throws IOException;
    V get(K key) throws IOException;
    void put(K key, V value) throws IOException;
    boolean hasSpaceFor(K key, V value) throws IOException;
    int depth() throws IOException;
    long getId(); // Geralmente o deslocamento do arquivo
    Collection<Entry<K, V>> getEntries() throws IOException;
    void incrementLocalDepth() throws IOException;
    void clearEntriesForSplit() throws IOException; // Auxiliar adicionado
}

interface Directory {
    long getPageOffset(long hashCode);
    int getGlobalDepth();
    void extend() throws IOException;
    void put(long directoryIndex, long pageOffset) throws IOException; // Changed from bucketOffset to pageOffset
    void load(RandomAccessFile raf) throws IOException;
    void save(RandomAccessFile raf) throws IOException;
    long getDirectoryIndex(long hashCode);
}

interface DataStore<K, V> {
    Page<K, V> getPage(long pageOffset) throws IOException;
    Page<K, V> allocateNewPage(int depth) throws IOException;
    void writePage(Page<K,V> page) throws IOException;
    long getNextAvailableOffset();
}


// --- ExtensibleHashingCSV Implementation ---

@SuppressWarnings("unused")
class ExtensibleHashingCSV {

    private static final int BUCKET_SIZE = 1024;
    private static final String DATA_FILE_CSV = "csv/AI/data_csv.dat";
    private static final String INDEX_FILE_CSV = "csv/AI/index_csv.dat";
    private static final String REGISTRY_FILE_CSV = "csv/AI/registry_csv.dat";
    private static final String CSV_INPUT_FILE = "csv/AI/random_people_for_csv_hashing.csv";

    private RandomAccessFile dataFile;
    private FileChannel dataChannel; // Não usado ativamente na lógica, mas parte da estrutura original
    private RandomAccessFile indexFile;
    private FileChannel indexChannel; // Não usado ativamente
    private int globalDepth;
    private List<Bucket> directory;

    private static class Bucket {
        int localDepth;
        HashMap<String, Long> entries;

        public Bucket(int localDepth) {
            this.localDepth = localDepth;
            this.entries = new HashMap<>(BUCKET_SIZE);
        }

        @Override
        public String toString() {
            return "Bucket@"+Integer.toHexString(hashCode()) + "{" + "ld=" + localDepth + ", entries=" + entries.size() + '}';
        }
    }

    public ExtensibleHashingCSV() {
        this.globalDepth = 1;
        int initialDirectorySize = 1 << globalDepth;
        this.directory = new ArrayList<>(initialDirectorySize);
        for (int i = 0; i < initialDirectorySize; i++) {
            directory.add(new Bucket(globalDepth));
        }
    }

    private void initializeFiles() throws IOException {
        dataFile = new RandomAccessFile(DATA_FILE_CSV, "rw");
        dataChannel = dataFile.getChannel();
        indexFile = new RandomAccessFile(INDEX_FILE_CSV, "rw");
        indexChannel = indexFile.getChannel();
    }

    private void closeFiles() throws IOException {
        if (dataChannel != null) dataChannel.close();
        if (dataFile != null) dataFile.close();
        if (indexChannel != null) indexChannel.close();
        if (indexFile != null) indexFile.close();
        System.out.println("Arquivos ExtensibleHashingCSV fechados.");
    }

    private void loadRegistry() throws IOException {
        File registry = new File(REGISTRY_FILE_CSV);
        if (registry.exists() && registry.length() > 0) {
            try (DataInputStream dis = new DataInputStream(new BufferedInputStream(new FileInputStream(registry)))) {
                this.globalDepth = dis.readInt();
                int directorySize = 1 << this.globalDepth;
                this.directory = new ArrayList<>(directorySize); // Inicializar com capacidade correta
                for (int i = 0; i < directorySize; i++) {
                    if (dis.available() < (Integer.BYTES * 2) ) { // Verificação básica para dados suficientes para o cabeçalho do bucket
                         System.err.println("Arquivo de registro corrompido ou incompleto no índice de diretório " + i);
                         // Alternativa: adicionar um bucket padrão ou lidar com o erro de forma mais elegante
                         this.directory.add(new Bucket(this.globalDepth)); // Adicionar um novo bucket padrão
                         continue; // Ou quebrar, dependendo do tratamento de erro desejado
                    }
                    int localDepth = dis.readInt();
                    Bucket bucket = new Bucket(localDepth);
                    int bucketEntryCount = dis.readInt();
                    for (int j = 0; j < bucketEntryCount; j++) {
                         if (dis.available() == 0 ) { // Verificar antes de ler chave/deslocamento
                            System.err.println("Arquivo de registro terminou inesperadamente ao ler entradas para o bucket " + i);
                            break;
                        }
                        String key = dis.readUTF();
                        long offset = dis.readLong();
                        bucket.entries.put(key, offset);
                    }
                    this.directory.add(bucket);
                }
                System.out.println("Registro carregado. Profundidade Global: " + this.globalDepth + ", Tamanho do Diretório: " + directory.size());
                 if(directory.size() != directorySize){
                    System.err.println("Aviso de carregamento de registro: Tamanho de diretório esperado " + directorySize + ", mas carregado " + directory.size());
                    // Potencialmente preencher o restante com novos buckets
                    for(int k=directory.size(); k < directorySize; k++){
                        directory.add(new Bucket(this.globalDepth));
                    }
                }

            }
        } else {
            System.out.println("Nenhum registro encontrado ou vazio, inicializando novo. Profundidade Global: " + this.globalDepth);
            int initialDirectorySize = 1 << globalDepth;
            this.directory = new ArrayList<>(initialDirectorySize);
            for (int i = 0; i < initialDirectorySize; i++) {
                directory.add(new Bucket(globalDepth));
            }
        }
    }

    private void saveRegistry() throws IOException {
        try (DataOutputStream dos = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(REGISTRY_FILE_CSV)))) {
            dos.writeInt(this.globalDepth);
            for (Bucket bucket : this.directory) {
                dos.writeInt(bucket.localDepth);
                dos.writeInt(bucket.entries.size());
                for (Map.Entry<String, Long> entry : bucket.entries.entrySet()) {
                    dos.writeUTF(entry.getKey());
                    dos.writeLong(entry.getValue());
                }
            }
            System.out.println("Registro salvo. Profundidade Global: " + this.globalDepth);
        }
    }

    public void processCSV(String csvFilePath, Function<String, String> keyExtractor) throws IOException {
        File csvFileObj = new File(csvFilePath);
        if (!csvFileObj.exists()) {
            System.err.println("Arquivo CSV não encontrado: " + csvFilePath);
            System.out.println("Criando arquivo CSV de teste: " + csvFilePath);
            try (PrintWriter writer = new PrintWriter(csvFileObj)) {
                for (int i = 1; i <= 210000; i++) {
                    writer.println(i + ", FirstName" + i + ", LastName" + i + ", Value" + (i * 10));
                }
            }
        }

        try (BufferedReader br = new BufferedReader(new FileReader(csvFilePath))) {
            String line;
            dataFile.seek(dataFile.length()); // Começar a escrever no final do arquivo de dados
            long currentOffset = dataFile.getFilePointer();

            while ((line = br.readLine()) != null) {
                if (line.trim().isEmpty()) continue;
                String key;
                try {
                    key = keyExtractor.apply(line);
                } catch (ArrayIndexOutOfBoundsException e) {
                    System.err.println("Pulando linha CSV malformada (falha na extração da chave): " + line);
                    continue;
                }
                byte[] recordBytes = (line + System.lineSeparator()).getBytes(StandardCharsets.UTF_8);
                dataFile.write(recordBytes);
                insert(key, currentOffset); // Armazenar o deslocamento onde o registro *começa*
                currentOffset = dataFile.getFilePointer(); // Atualizar para o *próximo* registro
            }
            System.out.println("Processamento CSV concluído para ExtensibleHashingCSV.");
        }
    }

    private int hash(String key) {
        CRC32 crc = new CRC32();
        crc.update(key.getBytes(StandardCharsets.UTF_8));
        return (int) crc.getValue();
    }

    private int getBucketIndex(int hashValue, int depth) {
        if (depth == 0) return 0; // Evita problemas com 1<<0 - 1
        return hashValue & ((1 << depth) - 1);
    }

    private void insert(String key, long offset) throws IOException {
        int bucketIndex = getBucketIndex(hash(key), globalDepth);
        Bucket bucket = directory.get(bucketIndex);

        if (bucket.entries.containsKey(key) || bucket.entries.size() < BUCKET_SIZE) {
            bucket.entries.put(key, offset);
        } else {
            splitBucket(bucketIndex, key, offset); // Passa chave/deslocamento que causou a divisão
            // Após a divisão, a chave que causou a divisão ainda precisa ser inserida.
            // O splitBucket agora reinserirá tudo, incluindo o novo.
            // Então, uma chamada recursiva direta pode não ser necessária se a divisão lidar com isso.
            // Vamos tentar novamente a inserção para a chave específica se splitBucket não garantir seu posicionamento.
            // Para segurança, deixe splitBucket lidar com a redistribuição, e tentamos novamente a inserção.
            insert(key,offset); // Chamada recursiva após tentativa de divisão
        }
    }


    private void splitBucket(int bucketIndexToSplit, String keyCausingSplit, long offsetCausingSplit) throws IOException {
        Bucket oldBucket = directory.get(bucketIndexToSplit);
        int oldLocalDepth = oldBucket.localDepth;

        if (oldLocalDepth == globalDepth) {
            int oldDirSize = directory.size();
            if (oldDirSize >= (Integer.MAX_VALUE / 2)) {
                 System.err.println("Tamanho máximo do diretório atingido, não pode dobrar mais.");
                 // Potencialmente tentar lidar com o estouro de outras formas ou parar
                 // Por enquanto, podemos ficar presos se BUCKET_SIZE for muito pequeno e as chaves colidirem muito.
                 // Isso levaria a um estouro de pilha em chamadas de inserção repetidas.
                 return; // Não pode dividir mais se o diretório não pode crescer
            }
            for (int i = 0; i < oldDirSize; i++) {
                directory.add(directory.get(i)); // Ponteiros duplicados por enquanto
            }
            globalDepth++;
            System.out.println("ExtHashingCSV: Profundidade global aumentada para: " + globalDepth);
        }

        int newLocalDepth = oldLocalDepth + 1;
        Bucket newBucket = new Bucket(newLocalDepth);
        oldBucket.localDepth = newLocalDepth; // O bucket antigo também recebe a nova profundidade local

        // Atualizar ponteiros de diretório
        // Iterar por todo o diretório. Para cada entrada, se ela apontava para oldBucket,
        // reavaliar com base no (oldLocalDepth)-ésimo bit do hash.
        for (int i = 0; i < directory.size(); i++) {
            // Verificar se o padrão de hash desta entrada de diretório (até oldLocalDepth) corresponde ao bucket que se dividiu
            // E se esta entrada realmente apontava para a instância oldBucket
            int prefixMaskForOldBucket = (1 << oldLocalDepth) -1;
            if ((getBucketIndex(hash("any_key_that_would_map_to_original_bucket"), oldLocalDepth) == (i & prefixMaskForOldBucket))
                && directory.get(i) == oldBucket) { // Verificação mais robusta: directory.get(i) == oldBucket (ou uma lista de ponteiros para oldBucket)

                // O novo bit distintivo está na posição 'oldLocalDepth' (indexado em 0)
                // Se esse bit em 'i' (o índice do diretório) for 1, ele aponta para newBucket
                if (((i >> oldLocalDepth) & 1) == 1) {
                    directory.set(i, newBucket);
                }
                // caso contrário, continua a apontar para oldBucket (que já está lá por duplicação ou era o original)
            }
        }
        // Garantir que o índice específico que era `bucketIndexToSplit` e seu par estejam corretos
        // Aquele que difere no (oldLocalDepth)-ésimo bit de bucketIndexToSplit agora aponta para newBucket
        int pairIndex = bucketIndexToSplit ^ (1 << oldLocalDepth);
        if (pairIndex < directory.size()) { // Verificar limites, especialmente se globalDepth não cresceu, mas local sim
             directory.set(pairIndex, newBucket);
        }
         // E o bucketIndexToSplit original ainda deve apontar para oldBucket (já definido ou duplicado).
        directory.set(bucketIndexToSplit, oldBucket);


        // Redistribuir entradas
        Map<String, Long> tempEntries = new HashMap<>(oldBucket.entries);
        oldBucket.entries.clear();
        tempEntries.put(keyCausingSplit, offsetCausingSplit); // Adicionar a entrada que causou a divisão

        for (Map.Entry<String, Long> entry : tempEntries.entrySet()) {
            // Reinserir: isso usará o globalDepth atualizado e os novos localDepths
            // Esta reinserção é crucial e deve posicionar os itens corretamente.
            int targetBucketIndex = getBucketIndex(hash(entry.getKey()), globalDepth);
            Bucket targetBucket = directory.get(targetBucketIndex);
            if (targetBucket.entries.size() < BUCKET_SIZE || targetBucket.entries.containsKey(entry.getKey())) {
                targetBucket.entries.put(entry.getKey(), entry.getValue());
            } else {
                // Este caso idealmente não deveria acontecer se BUCKET_SIZE > 0 e a lógica de divisão for perfeita,
                // a menos que tenhamos uma chave que não possa ser colocada mesmo após uma divisão (ex: BUCKET_SIZE muito pequeno)
                // Isso poderia levar a um StackOverflowError se chamarmos recursivamente insert/split daqui.
                // Por enquanto, assumimos que BUCKET_SIZE é adequado.
                // Se acontecer, imprima o erro. A inserção externa tentará novamente.
                 System.err.println("ExtHashingCSV: Erro durante a redistribuição na divisão. Bucket ainda cheio para a chave: " + entry.getKey());
                 System.err.println("Bucket Alvo: " + targetBucket + " índice: " + targetBucketIndex);
                 System.err.println("Tamanho do Diretório: " + directory.size() + " profundidadeGlobal: " + globalDepth);
            }
        }
    }


    public long findRecordOffset(String key) throws IOException {
        int hashVal = hash(key);
        int bucketIndex = getBucketIndex(hashVal, globalDepth);
        if (bucketIndex < 0 || bucketIndex >= directory.size()) {
            System.err.println("Erro ExtHashingCSV: Índice de bucket " + bucketIndex + " fora dos limites. Chave: " + key + ", Profundidade Global: " + globalDepth);
            return -1L;
        }
        Bucket bucket = directory.get(bucketIndex);
        return bucket.entries.getOrDefault(key, -1L);
    }

    public String readRecord(long offset) throws IOException {
        if (offset == -1L) {
            return null;
        }
        if (offset >= dataFile.length()) {
            System.err.println("Erro ExtHashingCSV: Deslocamento " + offset + " está além do comprimento do arquivo de dados " + dataFile.length());
            return null;
        }
        dataFile.seek(offset);
        return dataFile.readLine(); // Nota: readLine() tem implicações de conjunto de caracteres.
    }

    public static void runExtensibleHashingCSV() {
        System.out.println("--- Executando Teste ExtensibleHashingCSV ---");
        ExtensibleHashingCSV hashing = new ExtensibleHashingCSV();

        new File(DATA_FILE_CSV).delete();
        new File(REGISTRY_FILE_CSV).delete();
        new File(INDEX_FILE_CSV).delete();

        try {
            hashing.initializeFiles();
            hashing.loadRegistry();
            hashing.processCSV(CSV_INPUT_FILE, line -> line.split(",")[0]);
            hashing.saveRegistry();

            System.out.println("ExtHashingCSV: Estado do diretório após o processamento:");
            for (int i = 0; i < hashing.directory.size(); i++) {
                Bucket b = hashing.directory.get(i);
                System.out.println("Dir[" + i + "] -> " + b + " (Entradas: " + b.entries.keySet() + ")");
            }

        } catch (IOException e) {
            System.err.println("IOException no processamento principal de ExtensibleHashingCSV: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("Exceção Geral no processamento principal de ExtensibleHashingCSV: " + e.getMessage());
            e.printStackTrace();
        } finally {
            try {
                hashing.closeFiles();
            } catch (IOException e) {
                System.err.println("IOException durante closeFiles: " + e.getMessage());
            }
        }

        System.out.println("\n--- Teste de Leitura para ExtensibleHashingCSV ---");
        ExtensibleHashingCSV hashingRead = new ExtensibleHashingCSV();
        try {
            hashingRead.initializeFiles();
            hashingRead.loadRegistry();

            String[] searchKeys = {"1", "5", "10", "15", "20", "1000" }; // Testa existentes e não existentes
            for(String searchKey : searchKeys) {
                System.out.println("Buscando por chave: " + searchKey);
                long offset = hashingRead.findRecordOffset(searchKey);
                if (offset != -1L) {
                    String record = hashingRead.readRecord(offset);
                    System.out.println("Registro encontrado para a chave '" + searchKey + "': " + record);
                } else {
                    System.out.println("Registro com a chave '" + searchKey + "' não encontrado.");
                }
            }
        } catch (IOException e) {
            System.err.println("IOException no teste de leitura de ExtensibleHashingCSV: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("Exceção Geral no teste de leitura de ExtensibleHashingCSV: " + e.getMessage());
            e.printStackTrace();
        } finally {
            try {
                hashingRead.closeFiles();
            } catch (IOException e) {
                System.err.println("IOException durante closeFiles do teste de leitura: " + e.getMessage());
            }
        }
        System.out.println("--- Teste ExtensibleHashingCSV Finalizado ---");
    }
}


// --- FileBasedExtendibleHashing Implementation ---

class FileBasedPage implements Page<Integer, Long> {
    private static final int MAX_ENTRIES = 3;
    private final long fileOffset;
    private int localDepth;
    private final RandomAccessFile raf;
    private int entryCount;
    private Map<Integer, Long> entriesMap; // Cache em memória

    private static final int HEADER_SIZE = Integer.BYTES * 2; // contagemEntradas, profundidadeLocal
    private static final int ENTRY_SIZE = Integer.BYTES + Long.BYTES; // chave, valor

    public FileBasedPage(long fileOffset, int depthToSetIfNew, RandomAccessFile raf) throws IOException {
        this.fileOffset = fileOffset;
        this.raf = raf;
        this.entriesMap = new LinkedHashMap<>(); // Preservar ordem de inserção para reescrita consistente, se necessário

        boolean isNewPage = raf.length() <= fileOffset || (raf.length() < fileOffset + HEADER_SIZE);

        raf.seek(fileOffset);
        if (isNewPage) {
            this.localDepth = depthToSetIfNew;
            this.entryCount = 0;
            raf.writeInt(this.entryCount);
            raf.writeInt(this.localDepth);
            // Opcional: Estender arquivo para reservar espaço para MAX_ENTRIES (pode ser lento)
            // raf.setLength(Math.max(raf.length(), fileOffset + HEADER_SIZE + MAX_ENTRIES * ENTRY_SIZE));
        } else {
            this.entryCount = raf.readInt();
            this.localDepth = raf.readInt();
            for (int i = 0; i < this.entryCount; i++) {
                // Verificar se bytes suficientes permanecem para uma entrada
                if (raf.getFilePointer() + ENTRY_SIZE > raf.length()) {
                     System.err.println("Erro FBPage: Arquivo terminou prematuramente ao ler entradas para a página no deslocamento " + fileOffset);
                     this.entryCount = i; // Ajustar contagem de entradas para o que foi realmente lido
                     break;
                }
                entriesMap.put(raf.readInt(), raf.readLong());
            }
            // Se entryCount do cabeçalho não corresponder ao que foi lido (ex: devido a corrupção)
             if (this.entryCount != entriesMap.size() && this.entryCount > 0) {
                System.err.println("Aviso FBPage: Entradas incompatíveis para a página " + fileOffset + ". Cabeçalho: " + this.entryCount + ", Carregado: " + entriesMap.size());
                this.entryCount = entriesMap.size(); // Corrigir contagem de entradas com base nos dados carregados
                persistHeader(); // Persistir cabeçalho corrigido
            }
        }
    }

    private void persistHeader() throws IOException {
        raf.seek(fileOffset);
        raf.writeInt(entryCount);
        raf.writeInt(localDepth);
    }

    private void persistEntries() throws IOException {
        raf.seek(fileOffset + HEADER_SIZE);
        for (Map.Entry<Integer, Long> mapEntry : entriesMap.entrySet()) {
            raf.writeInt(mapEntry.getKey());
            raf.writeLong(mapEntry.getValue());
        }
        // Opcional: limpar quaisquer dados antigos restantes se o novo entryCount for menor que o anterior
        // long endOfValidData = fileOffset + HEADER_SIZE + entriesMap.size() * ENTRY_SIZE;
        // if (raf.getFilePointer() < endOfValidData + ENTRY_SIZE) { /* preencher ou truncar */ }
    }


    @Override
    public boolean contains(Integer key) {
        return entriesMap.containsKey(key);
    }

    @Override
    public Long get(Integer key) {
        return entriesMap.get(key);
    }

    @Override
    public void put(Integer key, Long value) throws IOException {
        boolean newKey = !entriesMap.containsKey(key);
        if (newKey && entryCount >= MAX_ENTRIES) {
            throw new IllegalStateException("FBPage full at offset " + fileOffset + ". Cannot add new key: " + key);
        }
        entriesMap.put(key, value);
        if (newKey) {
            entryCount++;
        }
        persistHeader();
        persistEntries(); // Reescrever todas as entradas para simplificar
    }

    @Override
    public boolean hasSpaceFor(Integer key, Long value) {
        return entriesMap.containsKey(key) || entryCount < MAX_ENTRIES;
    }

    @Override
    public int depth() {
        return localDepth;
    }

    @Override
    public void incrementLocalDepth() throws IOException {
        this.localDepth++;
        persistHeader();
    }

    @Override
    public long getId() {
        return fileOffset;
    }

    @Override
    public Collection<Entry<Integer, Long>> getEntries() {
        List<Entry<Integer, Long>> currentEntries = new ArrayList<>();
        for (Map.Entry<Integer, Long> mapEntry : entriesMap.entrySet()) {
            currentEntries.add(Entry.createEntry(mapEntry.getKey(), mapEntry.getValue()));
        }
        return currentEntries;
    }

    @Override
    public void clearEntriesForSplit() throws IOException {
        this.entriesMap.clear();
        this.entryCount = 0;
        persistHeader(); // Write empty state
        // PersistEntries is not strictly needed if header is 0, but good for full clear
        raf.seek(fileOffset + HEADER_SIZE); // Position after header
        // Optional: fill with zeros or truncate if this page's space is fixed.
        // For now, just updating header and in-memory map is enough before redistribution.
    }
}

class FileBasedDirectory implements Directory {
    private static final int INITIAL_GLOBAL_DEPTH = 1;
    private static final long DIR_METADATA_OFFSET = 0; // Profundidade global
    private static final int GLOBAL_DEPTH_BYTES = Integer.BYTES;
    private static final long DIR_ENTRIES_OFFSET = GLOBAL_DEPTH_BYTES; // Os deslocamentos das páginas começam após a profundidade global

    private int globalDepth;
    private List<Long> pageOffsets; // Lista em memória de deslocamentos de páginas (Long: deslocamento de arquivo de uma Página)
    // Ref do RandomAccessFile não armazenada aqui, passada para os métodos.

    public FileBasedDirectory(RandomAccessFile raf) throws IOException {
        this.pageOffsets = new ArrayList<>();
        load(raf);
    }

    @Override
    public int getGlobalDepth() {
        return globalDepth;
    }

    @Override
    public long getDirectoryIndex(long hashCode) {
        if (globalDepth == 0) return 0;
        return hashCode & ((1L << globalDepth) - 1);
    }

    @Override
    public long getPageOffset(long hashCode) {
        int index = (int) getDirectoryIndex(hashCode);
        if (index >= 0 && index < pageOffsets.size()) {
            return pageOffsets.get(index);
        }
        System.err.println("Erro FBDirectory: Índice " + index + " fora dos limites. Hash: " + hashCode + ", PG: " + globalDepth);
        return 0L; // 0L indica que nenhuma página foi alocada ou erro
    }

    @Override
    public void extend() throws IOException {
        int oldSize = 1 << globalDepth;
        this.globalDepth++;
        int newSize = 1 << globalDepth;
        
        if (newSize < oldSize || newSize > (Integer.MAX_VALUE / Long.BYTES) ) { // Verificação de estouro ou limite prático
            System.err.println("FBDirectory: Não é possível estender o diretório. Novo tamanho muito grande ou estouro.");
            this.globalDepth--; // Reverter
            throw new IOException("Limite de tamanho do diretório atingido.");
        }

        List<Long> newPageOffsets = new ArrayList<>(Collections.nCopies(newSize, 0L));
        for (int i = 0; i < oldSize; i++) {
            newPageOffsets.set(i, pageOffsets.get(i));
            newPageOffsets.set(i | oldSize, pageOffsets.get(i)); // Ponteiros duplicados
        }
        this.pageOffsets = newPageOffsets;
        System.out.println("FBDirectory: Estendido. Nova profundidade global: " + this.globalDepth + ", Novo tamanho: " + newSize);
    }

    @Override
    public void put(long directoryIndex, long pageOffset) throws IOException {
        if (directoryIndex >= 0 && directoryIndex < pageOffsets.size()) {
            pageOffsets.set((int) directoryIndex, pageOffset);
        } else {
            System.err.println("Erro FBDirectory: Tentativa de inserção em índice inválido " + directoryIndex + " (tamanho: " + pageOffsets.size() + ")");
            throw new IOException("Índice de diretório inválido para inserção: " + directoryIndex);
        }
    }

    @Override
    public void load(RandomAccessFile raf) throws IOException {
        if (raf.length() >= DIR_METADATA_OFFSET + GLOBAL_DEPTH_BYTES) {
            raf.seek(DIR_METADATA_OFFSET);
            this.globalDepth = raf.readInt();
            if(this.globalDepth < 0 || this.globalDepth > 30) { // Verificação de sanidade da profundidade
                System.err.println("Aviso FBDirectory: Profundidade global irrazoável " + this.globalDepth + " carregada. Reiniciando.");
                initializeDefaultDirectoryState();
                return;
            }

            int expectedSize = 1 << this.globalDepth;
            this.pageOffsets = new ArrayList<>(Collections.nCopies(expectedSize, 0L)); // Inicializar com 0L padrão

            if (raf.length() >= DIR_ENTRIES_OFFSET + (long) expectedSize * Long.BYTES) {
                raf.seek(DIR_ENTRIES_OFFSET);
                for (int i = 0; i < expectedSize; i++) {
                     if (raf.getFilePointer() + Long.BYTES > raf.length()) {
                        System.err.println("Erro FBDirectory: Arquivo terminou ao ler deslocamentos de página no índice " + i);
                        // Preencher o restante com 0L ou lidar com o erro. O loop atual será interrompido.
                        break;
                    }
                    pageOffsets.set(i, raf.readLong());
                }
                System.out.println("FBDirectory: Carregado do arquivo. Profundidade global: " + globalDepth + ", Tamanho: " + expectedSize);
                 if (pageOffsets.stream().filter(p -> p != 0L).count() == 0 && expectedSize > 2) {
                    System.out.println("Aviso FBDirectory: O diretório carregado parece ter todos os deslocamentos zero.");
                }
            } else {
                System.out.println("FBDirectory: O arquivo existe, mas está incompleto para as entradas. Profundidade carregada: " + globalDepth + ". Inicializando deslocamentos de página para 0L.");
            }
        } else {
            System.out.println("FBDirectory: Arquivo não encontrado ou muito pequeno. Inicializando novo diretório.");
            initializeDefaultDirectoryState();
        }
    }

    private void initializeDefaultDirectoryState() {
        this.globalDepth = INITIAL_GLOBAL_DEPTH;
        int initialSize = 1 << this.globalDepth;
        this.pageOffsets = new ArrayList<>(Collections.nCopies(initialSize, 0L));
    }

    @Override
    public void save(RandomAccessFile raf) throws IOException {
        raf.seek(DIR_METADATA_OFFSET);
        raf.writeInt(this.globalDepth);
        raf.seek(DIR_ENTRIES_OFFSET);
        for (Long offset : this.pageOffsets) {
            raf.writeLong(offset);
        }
        // Garantir que o arquivo tenha pelo menos este comprimento
        // raf.setLength(Math.max(raf.length(), DIR_ENTRIES_OFFSET + (long)pageOffsets.size() * Long.BYTES));
        System.out.println("FBDirectory: Salvo. Profundidade global: " + this.globalDepth);
    }
}

class FileBasedDataStore implements DataStore<Integer, Long> {
    private final RandomAccessFile dataRaf;
    private long nextAvailablePageOffset;
    // Começar as páginas de dados após algum espaço reservado para o diretório e metadados de hash
    private static final long DATA_PAGES_START_OFFSET = 4096; // ex: 4KB
    private static final long PAGE_ALLOCATION_SIZE = 512; // Alocar em blocos deste tamanho (aprox. tamanho da página)


    public FileBasedDataStore(RandomAccessFile raf) throws IOException {
        this.dataRaf = raf;
        if (dataRaf.length() < DATA_PAGES_START_OFFSET) {
            this.nextAvailablePageOffset = DATA_PAGES_START_OFFSET;
        } else {
            this.nextAvailablePageOffset = dataRaf.length();
        }
        // Alinhar a um limite de bloco para organização
        if (this.nextAvailablePageOffset % PAGE_ALLOCATION_SIZE != 0) {
            this.nextAvailablePageOffset = ((this.nextAvailablePageOffset / PAGE_ALLOCATION_SIZE) + 1) * PAGE_ALLOCATION_SIZE;
        }
        System.out.println("FBDataStore: Inicializado. Próximo deslocamento de página disponível: " + this.nextAvailablePageOffset);
    }

    @Override
    public Page<Integer, Long> getPage(long pageOffset) throws IOException {
        if (pageOffset < DATA_PAGES_START_OFFSET && pageOffset != 0L) { // 0L pode ser legítimo se significar "sem página"
            System.err.println("Aviso FBDataStore: Tentativa de obter página em deslocamento suspeito: " + pageOffset);
        }
        return new FileBasedPage(pageOffset, -1, dataRaf); // -1 profundidade, construtor da Página lê o real
    }

    @Override
    public Page<Integer, Long> allocateNewPage(int depthForNewPage) throws IOException {
        long newPageFileOffset = nextAvailablePageOffset;
        Page<Integer, Long> newPage = new FileBasedPage(newPageFileOffset, depthForNewPage, dataRaf); // Inicializa em disco
        nextAvailablePageOffset += PAGE_ALLOCATION_SIZE; // Avança pelo bloco de alocação fixo
        System.out.println("FBDataStore: Nova página alocada em " + newPageFileOffset + " profundidade " + depthForNewPage + ". Próximo livre: " + nextAvailablePageOffset);
        return newPage;
    }

    @Override
    public void writePage(Page<Integer, Long> page) throws IOException {
        // FileBasedPage.put() já persiste. Este método é um espaço reservado
        // ou poderia ser usado se a interface Page fosse mais abstrata sobre a persistência.
    }

    @Override
    public long getNextAvailableOffset() {
        return nextAvailablePageOffset;
    }
}

class BinUtils {
    public static long[] enumerateValues(int globalDepth, int localDepth, long prefix) {
        if (globalDepth < localDepth) return new long[]{prefix}; // Ou lançar erro
        long count = 1L << (globalDepth - localDepth);
        long[] result = new long[(int) count]; // Problema de cast potencial se a contagem for enorme
        for (int i = 0; i < count; i++) {
            result[i] = (prefix << (globalDepth - localDepth)) | i;
        }
        return result;
    }
}

class FileBasedEHash<K extends Number & Comparable<K>, V> { // Tipo de chave para exemplo
    private final Directory directory;
    private final DataStore<K, V> dataStore;
    private final RandomAccessFile metadataFile;
    private final EHashStats stats = new EHashStats();
    private long size = 0;
    private boolean dirty = false;

    // Usando um deslocamento distinto para o tamanho da tabela hash dentro do arquivo de metadados/hash
    private static final long HASH_SIZE_METADATA_OFFSET = 2048; // Exemplo de deslocamento, após o espaço do diretório

    public FileBasedEHash(Directory directory, DataStore<K, V> dataStore, RandomAccessFile metadataRaf) throws IOException {
        this.directory = directory;
        this.dataStore = dataStore;
        this.metadataFile = metadataRaf; // Pode ser o mesmo RAF que o diretório/datastore
        loadSize();
    }

    public boolean contains(K key) throws IOException {
        long hashCode = key.hashCode();
        long pageOffset = directory.getPageOffset(hashCode);
        if (pageOffset != 0L) {
            Page<K, V> page = dataStore.getPage(pageOffset);
            return page.contains(key);
        }
        return false;
    }

    public V get(K key) throws IOException {
        long hashCode = key.hashCode();
        long pageOffset = directory.getPageOffset(hashCode);
        if (pageOffset != 0L) {
            Page<K, V> page = dataStore.getPage(pageOffset);
            return page.get(key);
        }
        return null;
    }

    public void put(K key, V value) throws IOException {
        long hashCode = key.hashCode();
        long pageOffset = directory.getPageOffset(hashCode);
        Page<K, V> page;

        if (pageOffset == 0L) { // Nenhuma página para esta entrada do diretório de hash ainda
            page = dataStore.allocateNewPage(directory.getGlobalDepth());
            pageOffset = page.getId();
            long dirIndex = directory.getDirectoryIndex(hashCode);
            directory.put(dirIndex, pageOffset);
            // Se outras entradas do diretório também mapeiam para esta página recém-criada devido à profundidade_global,
            // elas também devem ser atualizadas. Esta simples inserção (dirIndex, pageOffset) define apenas uma.
            // Um sistema robusto poderia inicializar várias entradas de diretório apontando para a primeira página.
            // Por enquanto, isso depende das divisões para propagar os ponteiros.
        } else {
            page = dataStore.getPage(pageOffset);
        }

        if (page.contains(key)) { // Atualizar chave existente
            page.put(key, value);
            dirty = true;
            // dataStore.writePage(page); // Se page.put() não autopersistir completamente. Assume-se que sim.
            return; // O tamanho não muda na atualização
        }

        if (!page.hasSpaceFor(key, value)) {
            // A página está cheia, realizar divisão
            int oldPageLocalDepth = page.depth();

            if (oldPageLocalDepth == directory.getGlobalDepth()) {
                directory.extend(); // Isso aumenta a profundidade global
            }

            int newSplitPagesLocalDepth = oldPageLocalDepth + 1;
            Page<K, V> newPage1 = dataStore.allocateNewPage(newSplitPagesLocalDepth);
            Page<K, V> newPage2 = dataStore.allocateNewPage(newSplitPagesLocalDepth);

            // Coletar todas as entradas da página antiga + a nova entrada a ser inserida
            List<Entry<K, V>> entriesToRedistribute = new ArrayList<>(page.getEntries());
            entriesToRedistribute.add(Entry.createEntry(key, value));
            page.clearEntriesForSplit(); // A página antiga agora está vazia, pronta para ser potencialmente reutilizada ou seu espaço anotado como livre

            // Redistribuir entradas para newPage1 e newPage2
            for (Entry<K, V> entry : entriesToRedistribute) {
                long entryHash = entry.key().hashCode();
                // Usar o bit na posição 'oldPageLocalDepth' (indexado em 0) para decidir
                if (((entryHash >> oldPageLocalDepth) & 1) == 0) {
                    newPage1.put(entry.key(), entry.value());
                } else {
                    newPage2.put(entry.key(), entry.value());
                }
            }
            // dataStore.writePage(newPage1); // Assume-se que page.put persiste
            // dataStore.writePage(newPage2);

            // Atualizar ponteiros de diretório. Todas as entradas de diretório que anteriormente apontavam para a
            // 'página' original precisam ser atualizadas.
            long oldPageDirPrefix = directory.getDirectoryIndex(hashCode) & ((1L << oldPageLocalDepth) - 1);

            for (long i = 0; i < (1L << directory.getGlobalDepth()); i++) {
                if ((i & ((1L << oldPageLocalDepth) - 1)) == oldPageDirPrefix) {
                    if (((i >> oldPageLocalDepth) & 1) == 0) {
                        directory.put(i, newPage1.getId());
                    } else {
                        directory.put(i, newPage2.getId());
                    }
                }
            }
            // A nova entrada (chave, valor) foi agora colocada em newPage1 ou newPage2.
        } else { // A página tem espaço
            page.put(key, value);
            // dataStore.writePage(page);
        }
        size++;
        dirty = true;
    }

    public long size() {
        return size;
    }

    public void save() throws IOException {
        if (dirty) {
            directory.save(metadataFile); // O diretório se salva usando o RAF
            saveSize(); // Tamanho da própria tabela hash
            dirty = false;
            System.out.println("FileBasedEHash: Salvo. Tamanho: " + size);
        }
    }

    private void loadSize() throws IOException {
        if (metadataFile.length() >= HASH_SIZE_METADATA_OFFSET + Long.BYTES) {
            metadataFile.seek(HASH_SIZE_METADATA_OFFSET);
            this.size = metadataFile.readLong();
            System.out.println("FileBasedEHash: Tamanho carregado: " + this.size);
        } else {
            this.size = 0;
            System.out.println("FileBasedEHash: Metadados de tamanho não encontrados ou arquivo muito pequeno, tamanho definido para 0.");
        }
    }

    private void saveSize() throws IOException {
        metadataFile.seek(HASH_SIZE_METADATA_OFFSET);
        metadataFile.writeLong(size);
    }

    public void close() throws IOException {
        save();
        // RAF para metadataFile é gerenciado externamente (por MergedHashingImplementations)
        System.out.println("FileBasedEHash: Fechado (RAF gerenciado externamente).");
    }
}