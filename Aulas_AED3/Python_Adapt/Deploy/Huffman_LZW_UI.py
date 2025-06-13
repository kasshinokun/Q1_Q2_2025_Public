import os
import time
import struct
import heapq
import io
import pandas as pd
from matplotlib import pyplot as plt
import streamlit as st
import tempfile
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional, Dict, Tuple, Callable

# Constantes universais
UNIVERSAL_FOLDER=Path.home() /"Documents"/"Data"
UNIVERSAL_COMPRESSED_FOLDER=UNIVERSAL_FOLDER/"Compress"
TEMP_FOLDER = UNIVERSAL_FOLDER/"Temp"

# Constantes para Huffman
MIN_COMPRESSION_SIZE = 100  # Tamanho mínimo do arquivo para aplicar compressão
BUFFER_SIZE = 8192  # Tamanho do buffer de 8KB para operações de I/O

# Extensões
# para CSV
DEFAULT_EXTENSION = ".csv"
# para Huffman
HUFFMAN_COMPRESSED_EXTENSION = ".huff"
# para LZW
LZW_COMPRESSED_EXTENSION = ".lzw"

# Garanta que os diretórios existam
Path(UNIVERSAL_FOLDER).mkdir(parents=True, exist_ok=True)
Path(UNIVERSAL_COMPRESSED_FOLDER).mkdir(parents=True, exist_ok=True)
Path(TEMP_FOLDER).mkdir(parents=True, exist_ok=True)

# Implementação Huffman
class Node:
    __slots__ = ['char', 'freq', 'left', 'right']  # Otimização de memória
    
    def __init__(self, char: Optional[bytes], freq: int, 
                 left: Optional['Node'] = None, 
                 right: Optional['Node'] = None):
        self.char = char  # Armazenado como bytes
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other: 'Node'):
        return self.freq < other.freq

class HuffmanProcessor:
    @staticmethod
    def generate_tree(data: bytes, progress_callback: Optional[Callable[[float, str], None]] = None) -> Optional[Node]:
        """Geração otimizada de árvore com rastreamento de progresso"""
        if not data:
            return None
            
        if len(data) == 1:
            return Node(data, 1)  # Lida com o caso de um único byte

        if progress_callback:
            progress_callback(0, "Analisando conteúdo do arquivo...")

        # Usa Counter para análise de frequência de bytes
        byte_count = Counter(data)
        
        # Lida com o caso de um único byte
        if len(byte_count) == 1:
            byte = next(iter(byte_count))
            return Node(bytes([byte]), byte_count[byte])
        
        if progress_callback:
            progress_callback(0.2, "Construindo fila de prioridade...")

        nodes = [Node(bytes([byte]), freq) for byte, freq in byte_count.items()]
        heapq.heapify(nodes)

        if progress_callback:
            progress_callback(0.3, "Construindo árvore de Huffman...")

        total_nodes = len(nodes)
        while len(nodes) > 1:
            left = heapq.heappop(nodes)
            right = heapq.heappop(nodes)
            heapq.heappush(nodes, Node(None, left.freq + right.freq, left, right))
            
            if progress_callback and len(nodes) % 10 == 0:
                progress = 0.3 + 0.7 * (1 - len(nodes)/total_nodes)
                progress_callback(progress, f"Mesclando nós: {len(nodes)} restantes")

        if progress_callback:
            progress_callback(1.0, "Árvore de Huffman completa!")
            time.sleep(0.3)

        return nodes[0]

    @staticmethod
    def build_codebook(root: Optional[Node]) -> Dict[bytes, str]:
        """Geração otimizada de livro de códigos com DFS iterativo"""
        if not root:
            return {}

        codebook = {}
        stack = [(root, "")]
        
        while stack:
            node, code = stack.pop()
            if node.char is not None:
                codebook[node.char] = code or '0'
            else:
                stack.append((node.right, code + '1'))
                stack.append((node.left, code + '0'))
        
        return codebook

    @staticmethod
    def compress_file(input_path: str, output_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[int, int, float, float]:
        """Compressão otimizada com rastreamento de progresso"""
        start_time = time.time()
        
        # Lê o arquivo de entrada como binário
        with open(input_path, 'rb') as file:
            data = file.read()

        if not data:
            return 0, 0, 0.0, 0.0

        original_size = len(data)
        
        
        # Ignora a compressão para arquivos pequenos
        if original_size < MIN_COMPRESSION_SIZE:
            with open(output_path, 'wb') as file:
                file.write(data)
            return original_size, original_size, 0.0, time.time() - start_time

        # Passo 1: Constrói a árvore de Huffman
        if progress_callback:
            progress_callback(0, "Construindo Árvore de Huffman...")
        root = HuffmanProcessor.generate_tree(
            data, 
            lambda p, m: progress_callback(p * 0.3, f"Huffman: {m}") if progress_callback else None
        )

        # Passo 2: Constrói o livro de códigos
        if progress_callback:
            progress_callback(0.3, "Gerando dicionário de codificação...")
        codebook = HuffmanProcessor.build_codebook(root)
        
        # Cria pesquisa reversa para codificação mais rápida
        encode_table = {byte[0]: code for byte, code in codebook.items()}  # byte[0] pois sabemos que são bytes únicos

        # Passo 3: Comprime os dados
        if progress_callback:
            progress_callback(0.4, "Comprimindo dados...")

        with open(output_path, 'wb') as file:
            # Escreve a tabela de caracteres (formato otimizado)
            file.write(struct.pack('I', len(codebook)))
            for byte, code in codebook.items():
                file.write(struct.pack('B', byte[0]))  # Byte único
                file.write(struct.pack('B', len(code)))
                file.write(struct.pack('I', int(code, 2)))

            # Escreve o tamanho dos dados
            file.write(struct.pack('I', original_size))

            # Escrita de bits em buffer
            buffer = bytearray()
            current_byte = 0
            bit_count = 0
            bytes_processed = 0
            
            for byte in data:
                code = encode_table[byte]
                for bit in code:
                    current_byte = (current_byte << 1) | (bit == '1')
                    bit_count += 1
                    if bit_count == 8:
                        buffer.append(current_byte)
                        if len(buffer) >= BUFFER_SIZE:
                            file.write(buffer)
                            buffer.clear()
                        current_byte = 0
                        bit_count = 0
                
                bytes_processed += 1
                if progress_callback and bytes_processed % 1000 == 0:
                    progress = 0.4 + 0.6 * (bytes_processed / original_size)
                    progress_callback(progress, f"Comprimidos {bytes_processed}/{original_size} bytes")

            # Descarrega bits restantes
            if bit_count > 0:
                current_byte <<= (8 - bit_count)
                buffer.append(current_byte)
            
            if buffer:
                file.write(buffer)
            
            # Escreve o tamanho do preenchimento
            file.write(struct.pack('B', (8 - bit_count) % 8))

        compressed_size = os.path.getsize(output_path)
        compression_ratio = (original_size - compressed_size) / original_size * 100
        process_time = time.time() - start_time

        if progress_callback:
            progress_callback(1.0, "Compressão completa!")

        return original_size, compressed_size, compression_ratio, process_time

    @staticmethod
    def decompress_file(input_path: str, output_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[int, int, float, float]:
        """Descompressão otimizada com rastreamento de progresso"""
        start_time = time.time()
        
        # Descompressão reestruturada com preenchimento considerado
        with open(input_path, 'rb') as file:
            # Lê a tabela de caracteres
            table_size = struct.unpack('I', file.read(4))[0]
            code_table = {}
            max_code_length = 0
            
            if progress_callback:
                progress_callback(0.1, "Lendo metadados...")

            for i in range(table_size):
                byte = struct.unpack('B', file.read(1))[0]
                code_length = struct.unpack('B', file.read(1))[0]
                code_int = struct.unpack('I', file.read(4))[0]
                code = format(code_int, f'0{code_length}b')
                code_table[code] = bytes([byte])
                max_code_length = max(max_code_length, code_length)
                
                if progress_callback and i % 100 == 0:
                    progress = 0.1 + 0.2 * (i / table_size)
                    progress_callback(progress, f"Carregando tabela de códigos: {i}/{table_size}")

            # Lê o tamanho original dos dados
            data_size = struct.unpack('I', file.read(4))[0]

            # Obtém a posição atual (após ler a tabela e data_size)
            current_read_pos = file.tell()
            
            # Busca o fim do arquivo, lê o último byte (preenchimento) e depois volta
            file.seek(-1, os.SEEK_END)
            padding_bits = struct.unpack('B', file.read(1))[0]
            
            # Volta para onde os dados começam (após o cabeçalho, antes do byte de preenchimento)
            file.seek(current_read_pos)

            if progress_callback:
                progress_callback(0.3, "Preparando para decodificar...")

            result = io.BytesIO()
            current_bits = ""
            bytes_decoded = 0
            
            # Lê todos os dados comprimidos restantes, excluindo o último byte de preenchimento
            compressed_data_bytes = file.read() # Lê da posição atual até EOF-1 (byte de preenchimento)

            total_compressed_bits = len(compressed_data_bytes) * 8 - padding_bits
            bits_processed = 0

            for byte_val in compressed_data_bytes:
                bits_in_byte = format(byte_val, '08b')
                
                # Adiciona bits apenas se não atingimos o fim dos bits comprimidos significativos
                for bit in bits_in_byte:
                    if bits_processed < total_compressed_bits:
                        current_bits += bit
                        bits_processed += 1
                        
                        # Tenta decodificar a partir de current_bits
                        while True:
                            found_match = False
                            # Itera até max_code_length ou comprimento de current_bits
                            for length in range(1, min(len(current_bits), max_code_length) + 1):
                                prefix = current_bits[:length]
                                if prefix in code_table:
                                    result.write(code_table[prefix])
                                    bytes_decoded += 1
                                    current_bits = current_bits[length:]
                                    found_match = True
                                    
                                    if bytes_decoded >= data_size:
                                        # Decodificou todos os bytes originais, para.
                                        break
                            if bytes_decoded >= data_size:
                                break # Sai do loop de decodificação interno
                            if not found_match:
                                break # Nenhuma correspondência encontrada para o prefixo current_bits, espera por mais bits
                        
                        if bytes_decoded >= data_size:
                            break # Sai do loop de bits
                    else:
                        break # Excedeu total_compressed_bits (incluindo preenchimento)
                
                if bytes_decoded >= data_size:
                    break # Sai do loop de bytes
                
                if progress_callback and bytes_decoded % 1000 == 0:
                    progress = 0.3 + 0.7 * (bytes_decoded / data_size)
                    progress_callback(progress, f"Decodificados {bytes_decoded}/{data_size} bytes")

        # Escreve os dados decodificados
        with open(output_path, 'wb') as file:
            final_decoded_data = result.getvalue()
            # Garante que apenas os dados até o data_size original sejam gravados
            file.write(final_decoded_data[:data_size])

        compressed_size = os.path.getsize(input_path)
        decompressed_size = os.path.getsize(output_path)
        compression_ratio = (compressed_size - decompressed_size) / compressed_size * 100 # Esta proporção é geralmente para compressão
        process_time = time.time() - start_time

        if progress_callback:
            progress_callback(1.0, "Descompressão completa!")

        return compressed_size, decompressed_size, compression_ratio, process_time


# Implementação LZW
class LZWProcessor:
    @staticmethod
    def compress(input_file_path: str, output_file_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[int, int, float, float]:
        """Comprime um arquivo usando o algoritmo LZW com códigos de comprimento variável"""
        start_time = time.time()
        
        try:
            # Lê o arquivo de entrada como bytes
            with open(input_file_path, 'rb') as f:
                data = f.read()
            
            original_size = len(data)
            if not data:
                return 0, 0, 0.0, 0.0

            # Inicializa o dicionário com todos os bytes únicos possíveis
            dictionary = {bytes([i]): i for i in range(256)}
            next_code = 256
            compressed_data = []
            w = bytes()
            
            total_bytes = len(data)
            processed_bytes = 0
            
            # Determina o número mínimo de bits necessários inicialmente
            bits = 9  # Começa com 9 bits (pode representar até 511)
            max_code = 2**bits - 1
            
            for byte in data:
                c = bytes([byte])
                wc = w + c
                if wc in dictionary:
                    w = wc
                else:
                    compressed_data.append(dictionary[w])
                    # Adiciona wc ao dicionário
                    if next_code <= 2**24 - 1: # Adiciona apenas se o tamanho do dicionário estiver dentro do limite
                        dictionary[wc] = next_code
                        next_code += 1
                    
                    # Aumenta o comprimento dos bits se necessário (apenas se o dicionário crescer além do max_code atual)
                    if next_code > max_code and bits < 24:  # Limita a 24 bits (dicionário de 16MB)
                        bits += 1
                        max_code = 2**bits - 1
                    
                    w = c
                
                processed_bytes += 1
                if progress_callback and processed_bytes % 1000 == 0:
                    progress = processed_bytes / total_bytes
                    progress_callback(progress, f"Comprimindo... {processed_bytes}/{total_bytes} bytes processados")
            
            if w:
                compressed_data.append(dictionary[w])
            
            # Escreve os dados comprimidos no arquivo de saída
            with open(output_file_path, 'wb') as f:
                # Escreve o cabeçalho com o número de códigos e bits iniciais
                f.write(len(compressed_data).to_bytes(4, byteorder='big'))
                f.write(bits.to_bytes(1, byteorder='big'))
                
                # Empacota os códigos em bytes
                buffer = 0
                buffer_length = 0
                
                for code in compressed_data:
                    current_code_bits = math.ceil(math.log2(next_code)) if next_code > 1 else 1
                    if current_code_bits < 9: current_code_bits = 9
                    if current_code_bits > 24: current_code_bits = 24
                    
                    buffer = (buffer << current_code_bits) | code
                    buffer_length += current_code_bits
                    
                    while buffer_length >= 8:
                        byte = (buffer >> (buffer_length - 8)) & 0xFF
                        f.write(bytes([byte]))
                        buffer_length -= 8
                        buffer = buffer & ((1 << buffer_length) - 1)
                
                # Escreve os bits restantes
                if buffer_length > 0:
                    byte = (buffer << (8 - buffer_length)) & 0xFF
                    f.write(bytes([byte]))
            
            compressed_size = os.path.getsize(output_file_path)
            compression_ratio = (original_size - compressed_size) / original_size * 100
            process_time = time.time() - start_time

            if progress_callback:
                progress_callback(1.0, "Compressão completa!")

            return original_size, compressed_size, compression_ratio, process_time
        
        except Exception as e:
            if progress_callback:
                progress_callback(1.0, f"Erro durante a compressão: {str(e)}")
            raise e

    @staticmethod
    def decompress(input_file_path: str, output_file_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[int, int, float, float]:
        """Descomprime um arquivo usando o algoritmo LZW com códigos de comprimento variável"""
        start_time = time.time()
        
        try:
            # Lê o arquivo comprimido
            with open(input_file_path, 'rb') as f:
                # Lê o cabeçalho
                num_codes = int.from_bytes(f.read(4), byteorder='big')
                initial_bits = int.from_bytes(f.read(1), byteorder='big') # 'bits' renomeado para 'initial_bits' para clareza
                
                # Lê todos os dados restantes
                compressed_bytes = f.read()
            
            compressed_size = os.path.getsize(input_file_path)
            
            # Inicializa o dicionário com todos os bytes únicos possíveis
            dictionary = {i: bytes([i]) for i in range(256)}
            next_code = 256
            decompressed_data = bytearray()
            
            # Desempacota bits em códigos
            buffer = 0
            buffer_length = 0
            byte_pos = 0
            codes = []
            
            # Gerencia dinamicamente os bits para decodificação
            current_bits = initial_bits
            
            while len(codes) < num_codes:
                # Preenche o buffer
                while buffer_length < current_bits and byte_pos < len(compressed_bytes):
                    buffer = (buffer << 8) | compressed_bytes[byte_pos]
                    byte_pos += 1
                    buffer_length += 8
                
                if buffer_length < current_bits:
                    break  # Fim dos dados ou bits insuficientes para o próximo código
                
                # Extrai o código
                code = (buffer >> (buffer_length - current_bits)) & ((1 << current_bits) - 1)
                codes.append(code)
                buffer_length -= current_bits
                buffer = buffer & ((1 << buffer_length) - 1)
                
                # Atualiza o progresso
                if progress_callback and len(codes) % 1000 == 0:
                    progress = len(codes) / num_codes
                    progress_callback(progress, f"Lendo dados comprimidos... {len(codes)}/{num_codes} códigos processados")
            
            # Verifica se obtivemos todos os códigos esperados
            if len(codes) != num_codes:
                raise ValueError(f"Esperava {num_codes} códigos, mas obteve {len(codes)}")
            
            # Processa os códigos
            w = dictionary[codes[0]]
            decompressed_data.extend(w)
            
            for code in codes[1:]:
                # Ajusta `current_bits` dinamicamente com base em `next_code` durante a descompressão
                if next_code >= (1 << current_bits) and current_bits < 24:
                    current_bits += 1

                if code in dictionary:
                    entry = dictionary[code]
                elif code == next_code:
                    entry = w + w[:1]
                else:
                    raise ValueError(f"Código comprimido inválido: {code}")
                
                decompressed_data.extend(entry)
                
                # Adiciona w + entry[0] ao dicionário
                if next_code <= 2**24 - 1:
                    dictionary[next_code] = w + entry[:1]
                    next_code += 1
                
                w = entry
                
                # Atualiza o progresso
                progress = len(decompressed_data) / (num_codes * 3) # Estima aproximadamente com base no tamanho médio da entrada
                if progress_callback and len(decompressed_data) % 100000 == 0:  # Atualiza a cada 100KB
                    progress_callback(min(1.0, progress), f"Descomprimindo... {len(decompressed_data)//1024}KB processados") # Limita a 1.0

            # Escreve os dados descomprimidos no arquivo de saída
            with open(output_file_path, 'wb') as f:
                f.write(decompressed_data)
            
            decompressed_size = os.path.getsize(output_file_path)
            compression_ratio = (compressed_size - decompressed_size) / compressed_size * 100 
            process_time = time.time() - start_time

            if progress_callback:
                progress_callback(1.0, "Descompressão completa!")

            return compressed_size, decompressed_size, compression_ratio, process_time
        
        except Exception as e:
            if progress_callback:
                progress_callback(1.0, f"Erro durante a descompressão: {str(e)}")
            raise e

def compare_algorithms(input_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> pd.DataFrame:
    """Compara o desempenho dos algoritmos Huffman e LZW no mesmo arquivo"""
    results = []
    
    # Cria caminhos de saída temporários
    huffman_output = os.path.join(TEMP_FOLDER, "temp_huffman.huff")
    lzw_output = os.path.join(TEMP_FOLDER, "temp_lzw.lzw")
    
    # Cria caminhos de saída descomprimidos temporários para verificação
    huffman_decompressed_output = os.path.join(TEMP_FOLDER, os.path.basename(input_path) + ".huffout")
    lzw_decompressed_output = os.path.join(TEMP_FOLDER, os.path.basename(input_path) + ".lzwout")

    # Testa Huffman
    if progress_callback:
        progress_callback(0, "Testando compressão Huffman...")
    huff_compress = HuffmanProcessor.compress_file(input_path, huffman_output, 
        lambda p, m: progress_callback(p * 0.3, f"Huffman: {m}") if progress_callback else None)
    
    if progress_callback:
        progress_callback(0.4, "Testando descompressão Huffman...")
    huff_decompress = HuffmanProcessor.decompress_file(huffman_output, huffman_decompressed_output, 
        lambda p, m: progress_callback(0.4 + p * 0.2, f"Huffman: {m}") if progress_callback else None)
    
    # Testa LZW
    if progress_callback:
        progress_callback(0.6, "Testando compressão LZW...")
    lzw_compress = LZWProcessor.compress(input_path, lzw_output, 
        lambda p, m: progress_callback(0.6 + p * 0.2, f"LZW: {m}") if progress_callback else None)
    
    if progress_callback:
        progress_callback(0.8, "Testando descompressão LZW...")
    lzw_decompress = LZWProcessor.decompress(lzw_output, lzw_decompressed_output, 
        lambda p, m: progress_callback(0.8 + p * 0.2, f"LZW: {m}") if progress_callback else None)
    
    # Limpa arquivos temporários
    for f in [huffman_output, lzw_output, huffman_decompressed_output, lzw_decompressed_output]:
        try:
            if os.path.exists(f):
                os.remove(f)
        except OSError as e: # Captura OSError específico para operações de arquivo
            st.warning(f"Não foi possível excluir o arquivo temporário {f}: {e}")
            pass # Continua mesmo que a limpeza falhe para um arquivo
    
    # Prepara resultados
    results.append({
        'Algorithm': 'Huffman',
        'Original Size (KB)': huff_compress[0] / 1024,
        'Compressed Size (KB)': huff_compress[1] / 1024,
        'Compression Ratio (%)': huff_compress[2],
        'Compression Time (s)': huff_compress[3],
        'Decompression Time (s)': huff_decompress[3],
        'Total Time (s)': huff_compress[3] + huff_decompress[3]
    })
    
    results.append({
        'Algorithm': 'LZW',
        'Original Size (KB)': lzw_compress[0] / 1024,
        'Compressed Size (KB)': lzw_compress[1] / 1024,
        'Compression Ratio (%)': lzw_compress[2],
        'Compression Time (s)': lzw_compress[3],
        'Decompression Time (s)': lzw_decompress[3],
        'Total Time (s)': lzw_compress[3] + lzw_decompress[3]
    })
    
    return pd.DataFrame(results)

def plot_comparison(df: pd.DataFrame):
    """Cria gráficos de comparação"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Taxa de Compressão
    df.plot.bar(x='Algorithm', y='Compression Ratio (%)', ax=axes[0,0], 
                title='Comparação de Taxa de Compressão', legend=False)
    axes[0,0].set_ylabel('Taxa (%)')
    
    # Tempo de Compressão
    df.plot.bar(x='Algorithm', y='Compression Time (s)', ax=axes[0,1], 
                title='Comparação de Tempo de Compressão', legend=False)
    axes[0,1].set_ylabel('Tempo (s)')
    
    # Tempo de Descompressão
    df.plot.bar(x='Algorithm', y='Decompression Time (s)', ax=axes[1,0], 
                title='Comparação de Tempo de Descompressão', legend=False)
    axes[1,0].set_ylabel('Tempo (s)')
    
    # Tempo Total
    df.plot.bar(x='Algorithm', y='Total Time (s)', ax=axes[1,1], 
                title='Comparação de Tempo Total de Processamento', legend=False)
    axes[1,1].set_ylabel('Tempo (s)')
    
    plt.tight_layout()
    return fig

# UI Unificada do Streamlit
def main():
    st.title("Ferramenta de Compressão/Descompressão de Arquivos")
    
    # Inicializa elementos de progresso
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    def update_progress(progress: float, message: str):
        progress_bar.progress(progress)
        progress_text.text(message)
    
    # Usa selectbox em vez de abas
    selected_view = st.selectbox(
        "Selecionar Visualização:", 
        ("Compressão/Descompressão", "Comparação de Algoritmos"), 
        key="main_view_select"
    )

    # Inicializa variáveis para caminhos de arquivo e diretórios temporários fora dos blocos condicionais
    input_path_tab1 = None
    output_path_tab1 = None
    temp_dir_tab1 = None
    input_path_compare = None
    temp_dir_compare = None

    if selected_view == "Compressão/Descompressão":
        # Seleção do algoritmo
        algorithm = st.radio("Selecionar Algoritmo:", ("Huffman", "LZW"), key="algo_select")
        
        # Seleção da operação
        operation = st.radio("Selecionar Operação:", ("Compressão", "Descompressão"), key="op_select")
        
        # Determina os tipos de arquivo permitidos para upload
        allowed_types = []
        if operation == "Compressão":
            allowed_types = [".lzw", ".huff", ".csv", ".db", ".idx", ".btr"]
        else: # Descompressão
            if algorithm == "Huffman":
                allowed_types = [".huff"]
            elif algorithm == "LZW":
                allowed_types = [".lzw"]
        
        # Seleção de arquivo
        file_source = st.radio("Selecionar Origem do Arquivo:", ("Padrão", "Escolha do Usuário"), key="file_source")
        
        selected_file = None
        uploaded_file = None

        if file_source == "Padrão":
            try:
                # A pasta de origem padrão depende do algoritmo
                source_folder = UNIVERSAL_FOLDER if operation == "Compressão" else UNIVERSAL_COMPRESSED_FOLDER
                
                default_files = []
                if os.path.exists(source_folder):
                    # Filtra arquivos com base na operação e algoritmo para arquivos padrão
                    for file in os.listdir(source_folder):
                        file_ext = os.path.splitext(file)[1]
                        if operation == "Compressão" and file_ext in allowed_types:
                            default_files.append(file)
                        elif operation == "Descompressão" and file_ext in allowed_types:
                            default_files.append(file)


                if default_files:
                    selected_file = st.selectbox(f"Selecione um arquivo de {source_folder.name}:", default_files)
                    input_path_tab1 = os.path.join(source_folder, selected_file)
                else:
                    st.warning(f"Nenhum arquivo {', '.join(allowed_types)} encontrado em {source_folder}")
            except Exception as e:
                st.error(f"Erro ao acessar o diretório padrão: {str(e)}")
        else: # Escolha do Usuário
            # Aplica os allowed_types dinâmicos para o uploader de arquivos
            uploaded_file = st.file_uploader(
                "Carregar um arquivo:", 
                type=[ext.strip('.') for ext in allowed_types], # Streamlit espera extensões sem o ponto inicial
                key="upload_tab1"
            )
            if uploaded_file:
                # Salva em um diretório temporário para processamento
                temp_dir_tab1 = tempfile.mkdtemp()
                input_path_tab1 = os.path.join(temp_dir_tab1, uploaded_file.name)
                with open(input_path_tab1, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.info(f"Arquivo '{uploaded_file.name}' carregado temporariamente.")

        if input_path_tab1 and st.button(f"Executar {operation}"):
            progress_bar.progress(0)
            progress_text.text(f"Iniciando {operation.lower()}...")
            
            output_folder = UNIVERSAL_COMPRESSED_FOLDER
            
            try:
                if operation == "Compressão":
                    original_file_name, _ = os.path.splitext(os.path.basename(input_path_tab1))
                    output_ext = HUFFMAN_COMPRESSED_EXTENSION if algorithm == "Huffman" else LZW_COMPRESSED_EXTENSION
                    output_file_name = f"{original_file_name}{output_ext}"
                    output_path_tab1 = os.path.join(output_folder, output_file_name)

                    if algorithm == "Huffman":
                        orig_s, comp_s, ratio, proc_t = HuffmanProcessor.compress_file(input_path_tab1, output_path_tab1, update_progress)
                    else: # LZW
                        orig_s, comp_s, ratio, proc_t = LZWProcessor.compress(input_path_tab1, output_path_tab1, update_progress)
                    
                    st.success(f"Compressão {algorithm} Concluída!")
                    st.write(f"Tamanho Original: {orig_s / 1024:.2f} KB")
                    st.write(f"Tamanho Comprimido: {comp_s / 1024:.2f} KB")
                    st.write(f"Taxa de Compressão: {ratio:.2f}%")
                    st.write(f"Tempo Gasto: {proc_t:.4f} segundos")

                    if comp_s > 0: # Garante que o arquivo foi criado antes de oferecer o download
                        with open(output_path_tab1, "rb") as f_out:
                            st.download_button(
                                label=f"Baixar Arquivo Comprimido ({output_ext})",
                                data=f_out.read(),
                                file_name=output_file_name,
                                mime="application/octet-stream"
                            )

                else: # Descompressão
                    # Para descompressão, o arquivo de saída geralmente volta para a pasta de origem com uma nova extensão
                    original_file_name, _ = os.path.splitext(os.path.basename(input_path_tab1))
                    # Assumindo que queremos nomear o arquivo descomprimido com uma extensão reconhecível
                    output_file_name = f"{original_file_name}.decompressed"
                    output_path_tab1 = os.path.join(TEMP_FOLDER, output_file_name) # Descomprime para temp por enquanto
                    
                    if algorithm == "Huffman":
                        comp_s, decomp_s, ratio, proc_t = HuffmanProcessor.decompress_file(input_path_tab1, output_path_tab1, update_progress)
                    else: # LZW
                        comp_s, decomp_s, ratio, proc_t = LZWProcessor.decompress(input_path_tab1, output_path_tab1, update_progress)
                    
                    st.success(f"Descompressão {algorithm} Concluída!")
                    st.write(f"Tamanho Comprimido: {comp_s / 1024:.2f} KB")
                    st.write(f"Tamanho Descomprimido: {decomp_s / 1024:.2f} KB")
                    st.write(f"Tempo Gasto: {proc_t:.4f} segundos")

                    if decomp_s > 0:
                        with open(output_path_tab1, "rb") as f_out:
                            st.download_button(
                                label=f"Baixar Arquivo Descomprimido ({output_file_name})",
                                data=f_out.read(),
                                file_name=output_file_name,
                                mime="application/octet-stream"
                            )
            
            except FileNotFoundError:
                st.error("Arquivo não encontrado. Por favor, certifique-se de que o arquivo existe no caminho especificado.")
            except Exception as e:
                st.error(f"Erro durante {operation.lower()}: {str(e)}")
            finally:
                # Limpa o arquivo temporário carregado se foi usado para tab1
                if uploaded_file and temp_dir_tab1 and os.path.exists(temp_dir_tab1): # Verifica se temp_dir_tab1 foi realmente criado
                    try:
                        if os.path.exists(input_path_tab1): # Remove apenas se foi realmente criado em temp
                            os.remove(input_path_tab1)
                        os.rmdir(temp_dir_tab1)
                    except OSError as e:
                        st.warning(f"Não foi possível limpar o diretório de upload temporário: {str(e)}")
                # Limpa a saída descomprimida temporária, se aplicável
                if operation == "Descompressão" and output_path_tab1 and os.path.exists(output_path_tab1):
                     try:
                        os.remove(output_path_tab1)
                     except OSError as e:
                        st.warning(f"Não foi possível limpar o arquivo de saída descomprimido temporário: {str(e)}")

                progress_bar.progress(1.0)
                time.sleep(0.5)
    
    elif selected_view == "Comparação de Algoritmos":
        st.header("Comparação de Desempenho de Algoritmos")
        st.write("Compare os algoritmos Huffman e LZW no mesmo arquivo")
        
        compare_file_source = st.radio(
            "Selecione o arquivo para comparação:", 
            ("CSV Padrão", "Escolha do Usuário"), 
            key="compare_source"
        )
        
        compare_file = None
        compare_uploaded = None
        
        if compare_file_source == "CSV Padrão":
            try:
                default_files = []
                if os.path.exists(UNIVERSAL_FOLDER):
                    for file in os.listdir(UNIVERSAL_FOLDER):
                        if file.endswith(DEFAULT_EXTENSION): # Apenas CSV para comparação padrão
                            default_files.append(file)
                
                if default_files:
                    compare_file = st.selectbox("Selecione um arquivo CSV para comparação:", default_files)
                    input_path_compare = os.path.join(UNIVERSAL_FOLDER, compare_file)
                else:
                    st.warning(f"Nenhum arquivo CSV encontrado em {UNIVERSAL_FOLDER}")
            except Exception as e:
                st.error(f"Erro ao acessar o diretório de origem: {str(e)}")
        else:
            # Para comparação, permite .lzw, .huff, .csv, .db, .idx, .btr
            compare_uploaded_allowed_types = [".lzw", ".huff", ".csv", ".db", ".idx", ".btr"]
            uploaded_file_types_for_st = [ext.strip('.') for ext in compare_uploaded_allowed_types]

            compare_uploaded = st.file_uploader(
                "Carregar um arquivo para comparação", 
                type=uploaded_file_types_for_st,
                key="compare_upload"
            )
            if compare_uploaded:
                # Salva em local temporário
                temp_dir_compare = tempfile.mkdtemp()
                input_path_compare = os.path.join(temp_dir_compare, compare_uploaded.name)
                with open(input_path_compare, "wb") as f:
                    f.write(compare_uploaded.getbuffer())
        
        if (compare_file or compare_uploaded) and st.button("Executar Comparação"):
            progress_bar.progress(0)
            progress_text.text("Iniciando comparação...")
            
            try:
                # Executa comparação
                df = compare_algorithms(input_path_compare, update_progress)
                
                # Exibe resultados
                st.success("Comparação concluída!")
                st.dataframe(df.style.format({
                    'Original Size (KB)': '{:.2f}',
                    'Compressed Size (KB)': '{:.2f}',
                    'Compression Ratio (%)': '{:.2f}',
                    'Compression Time (s)': '{:.4f}',
                    'Decompression Time (s)': '{:.4f}',
                    'Total Time (s)': '{:.4f}'
                }))
                
                # Mostra gráficos
                fig = plot_comparison(df)
                st.pyplot(fig)
                
                # Oferece download dos resultados
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Baixar Resultados como CSV",
                    data=csv,
                    file_name="compression_comparison.csv",
                    mime="text/csv"
                )
            
            except Exception as e:
                st.error(f"Erro durante a comparação: {str(e)}")
            finally:
                # Limpa arquivos temporários para a aba de comparação
                if compare_uploaded and temp_dir_compare and os.path.exists(temp_dir_compare): # Verifica se temp_dir_compare foi realmente criado
                    try:
                        if input_path_compare and os.path.exists(input_path_compare): # Remove apenas se foi realmente criado em temp
                            os.remove(input_path_compare)
                        os.rmdir(temp_dir_compare)
                    except OSError as e:
                        st.warning(f"Não foi possível limpar o diretório de upload temporário de comparação: {str(e)}")
                
                progress_bar.progress(1.0)
                time.sleep(0.5)

if __name__ == "__main__":
    main()