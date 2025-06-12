#stCryptoPY_v0alpha versão 

import streamlit as st
import os
import struct
from pathlib import Path
import time  # For simulating delays/retries if needed, and for timing operations
import filelock # For cross-platform file locking
import csv
import tempfile
import heapq
import io
import pandas as pd
import json
import logging
import traceback
import hashlib
import math
from matplotlib import pyplot as plt
from collections import Counter, defaultdict
from typing import Tuple, Optional, Dict, Callable,List, Union, Any, Iterator
from datetime import datetime, date

# --- Cryptography Imports (for RSA and AES) ---
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag as CryptoInvalidTag # Renomeado para evitar conflito

# ====================================================================
# Path Constants
# ====================================================================
# The 'Documents' folder is usually in the user's home directory
DOCUMENTS_PATH = Path.home() / "Documents"
DATA_FOLDER = DOCUMENTS_PATH / "Data"
# --- Constants ---
DB_FILE = DATA_FOLDER/ 'traffic_accidents.db'
IDX_FILE = DATA_FOLDER/'traffic_accidents.idx'
BTR_FILE = DATA_FOLDER/'traffic_accidents.btr'
BACKUP_DIR = DATA_FOLDER/ 'backups'
LOCK_FILE = DATA_FOLDER/ 'traffic_accidents.lock' # Dedicated lock file
#CSV
DEFAULT_EXTENSION = ".csv"
CSV_DELIMITER = ';'

MAX_RECORDS_PER_PAGE = 20
MAX_FILE_SIZE_MB = 100 # Maximum CSV file size for import - CHANGED FROM 10 TO 100
CHUNK_SIZE = 4096     # Read/write chunk size for file operations (4KB)
MAX_BACKUPS = 5       # Keep only the last N backups
MAX_LOG_ENTRIES_DISPLAY = 10 # Max number of log entries to display in the registry

# Constants for Huffman
HUFFMAN_SOURCE_FOLDER = DATA_FOLDER 
HUFFMAN_COMPRESSED_FOLDER = HUFFMAN_SOURCE_FOLDER / "Huffman"
HUFFMAN_COMPRESSED_EXTENSION = ".huff"
MIN_COMPRESSION_SIZE = 100 # Minimum file size to apply compression
BUFFER_SIZE = 8192 # 8KB buffer size for I/O operations

# Constants for LZW
LZW_SOURCE_FOLDER = DATA_FOLDER
LZW_COMPRESSED_FOLDER = HUFFMAN_SOURCE_FOLDER / "LZW"
LZW_COMPRESSED_EXTENSION = ".lzw"

# Add a new constant for temporary files within the DATA_FOLDER structure
TEMP_FOLDER = DATA_FOLDER / "Temp"

# New constant for encrypted files
ENCRYPT_FOLDER = DATA_FOLDER / "Encrypt"

# Ensure that the data folder and its subdirectories exist
DATA_FOLDER.mkdir(parents=True, exist_ok=True)
HUFFMAN_SOURCE_FOLDER.mkdir(parents=True, exist_ok=True)
HUFFMAN_COMPRESSED_FOLDER.mkdir(parents=True, exist_ok=True)
LZW_COMPRESSED_FOLDER.mkdir(parents=True, exist_ok=True)
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)
ENCRYPT_FOLDER.mkdir(parents=True, exist_ok=True) # Create the encryption folder

# Define predefined files for testing
PREDEFINED_FILES = {
    "Data File (.db)": DB_FILE,
    "Index File (.idx)": IDX_FILE,
    "B-Tree File (.btr)": BTR_FILE,
}

# Create dummy files for testing if they do not exist
for name, path in PREDEFINED_FILES.items():
    if not path.exists():
        with open(path, "wb") as f:
            f.write(f"Example content for {name}. This is a dummy file used for testing compression and encryption operations in the Streamlit application. It contains some repetitive text to allow for effective compression algorithm demonstration. The size of this file might vary based on the 'Example content' to ensure it's above the minimum compression size for proper testing.".encode() * 50) # Added more content to make it larger for compression

# Create a dummy text file for encryption testing if it does not exist
TEST_TEXT_FILE = DATA_FOLDER / "test_document.txt"
if not TEST_TEXT_FILE.exists():
    with open(TEST_TEXT_FILE, "w", encoding="utf-8") as f:
        f.write("This is a test document for encryption and decryption. " * 100) # Make it reasonably large

# Configure logging
logging.basicConfig(
    level=logging.INFO, # Set to logging.DEBUG to see detailed date parsing attempts
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traffic_accidents.log'), # Log to a file
        logging.StreamHandler() # Also log to console
    ]
)
logger = logging.getLogger(__name__)



# --- Data Fields ---
# Define all fields for the DataObject and their expected types/validation rules
FIELDS = [
    'crash_date', 'traffic_control_device', 'weather_condition', 
    'lighting_condition', 'first_crash_type', 'trafficway_type',
    'alignment', 'roadway_surface_cond', 'road_defect', 'crash_type',
    'intersection_related_i', 'damage', 'prim_contributory_cause',
    'num_units', 'most_severe_injury', 'injuries_total', 'injuries_fatal',
    'injuries_incapacitating', 'injuries_non_incapacitating',
    'injuries_reported_not_evident', 'injuries_no_indication',
    'crash_hour', 'crash_day_of_week', 'crash_month'
]

# --- Custom Exceptions ---
class DataValidationError(Exception):
    """Custom exception for data validation errors within DataObject."""
    pass

class DatabaseError(Exception):
    """Custom exception for database operations and file I/O errors."""
    pass

class FileLockError(Exception):
    """Custom exception for errors acquiring/releasing file locks."""
    pass

# ====================================================================
# Blowfish Implementation
# ====================================================================

# P_INIT and S_INIT constants
P_INIT = [
    0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344, 0xA4093822, 0x299F31D0,
    0x082EFA98, 0xEC4E6C89, 0x452821E6, 0x38D01377, 0xBE5466CF, 0x34E90C6C,
    0xC0AC29B7, 0xC97C50DD, 0x3F84D5B5, 0xB5470917, 0x9216D5D9, 0x8979FB1B
]

S_INIT = [
    [
        0xD1310BA6, 0x98DFB5AC, 0x2FFD72DB, 0xD01ADFB7, 0xB8E1AFED, 0x6A267E96,
        0xBA7C9045, 0xF12C7F99, 0x24A19947, 0xB3916CF7, 0x0801F2E2, 0x858EFC16,
        0x636920D8, 0x71574E69, 0xA458FE3E, 0x1BBEB41B
    ],
    [
        0xE01BECD3, 0x86FA67DB, 0xF9D50F25, 0xBA7C9045, 0xF12C7F99, 0x24A19947,
        0xB3916CF7, 0x0801F2E2, 0x858EFC16, 0x636920D8, 0x71574E69, 0xA458FE3E,
        0x1BBEB41B, 0xE01BECD3, 0x86FA67DB, 0xF9D50F25
    ],
    [
        0x26027E2D, 0x94B7E38C, 0x0119E153, 0x858ECDBA, 0x98DFB5AC, 0x2FFD72DB,
        0xD01ADFB7, 0xB8E1AFED, 0x6A267E96, 0xBA7C9045, 0xF12C7F99, 0x24A19947,
        0xB3916CF7, 0x0801F2E2, 0x858EFC16, 0x636920D8
    ],
    [
        0x71574E69, 0xA458FE3E, 0x1BBEB41B, 0xE01BECD3, 0x86FA67DB, 0xF9D50F25,
        0xBA7C9045, 0xF12C7F99, 0x24A19947, 0xB3916CF7, 0x0801F2E2, 0x858EFC16,
        0x636920D8, 0x71574E69, 0xA458FE3E, 0x1BBEB41B
    ]
]

class Blowfish:
    def __init__(self, key):
        self.P = list(P_INIT)  # Make a copy
        self.S = [list(s_arr) for s_arr in S_INIT] # Make a deep copy

        key_bytes = key
        key_len = len(key_bytes)
        
        j = 0
        for i in range(18):
            # Ensure key_bytes is long enough for struct.unpack, pad with zeros if not
            chunk = key_bytes[j:j+4]
            if len(chunk) < 4:
                chunk += b'\x00' * (4 - len(chunk))
            self.P[i] ^= struct.unpack('>I', chunk)[0]
            j = (j + 4) % key_len

        L = 0
        R = 0
        for i in range(0, 18, 2):
            L, R = self._encrypt_block(L, R)
            self.P[i] = L
            self.P[i+1] = R

        for i in range(4):
            for j in range(0, 256, 2):
                L, R = self._encrypt_block(L, R)
                self.S[i][j] = L
                self.S[i][j+1] = R

    def _feistel(self, x):
        h = self.S[0][x >> 24 & 0xFF] + self.S[1][x >> 16 & 0xFF]
        h ^= self.S[2][x >> 8 & 0xFF]
        h += self.S[3][x & 0xFF]
        return h & 0xFFFFFFFF

    def _encrypt_block(self, L, R):
        for i in range(16):
            L ^= self.P[i]
            R ^= self._feistel(L)
            L, R = R, L # Swap L and R
        R ^= self.P[16]
        L ^= self.P[17]
        return L, R # Don't swap after last round

    def _decrypt_block(self, L, R):
        for i in range(17, 1, -1):
            L ^= self.P[i]
            R ^= self._feistel(L)
            L, R = R, L # Swap L and R
        R ^= self.P[1]
        L ^= self.P[0]
        return L, R # Don't swap after last round

    def encrypt(self, data):
        # Pad data to be a multiple of 8 bytes (Blowfish block size)
        padding_len = 8 - (len(data) % 8)
        data += bytes([padding_len]) * padding_len

        encrypted_data = b''
        for i in range(0, len(data), 8):
            block = data[i:i+8]
            L = struct.unpack('>I', block[:4])[0]
            R = struct.unpack('>I', block[4:8])[0]
            L, R = self._encrypt_block(L, R)
            encrypted_data += struct.pack('>II', L, R)
        return encrypted_data

    def decrypt(self, data):
        decrypted_data = b''
        for i in range(0, len(data), 8):
            block = data[i:i+8]
            L = struct.unpack('>I', block[:4])[0]
            R = struct.unpack('>I', block[4:8])[0]
            L, R = self._decrypt_block(L, R)
            decrypted_data += struct.pack('>II', L, R)
        
        # Remove padding
        if not decrypted_data: # Handle empty decrypted data
            raise ValueError("Dados descriptografados vazios. Senha incorreta ou arquivo corrompido?")

        padding_len = decrypted_data[-1]
        if padding_len > 8 or padding_len == 0: # Invalid padding, possibly corrupted data or no padding
            # Attempt to return raw data if padding is clearly invalid but data exists
            # This is a heuristic to handle cases where padding byte might be part of data
            # For strict correctness, a better padding scheme (like PKCS7) would be needed
            # For simplicity, if padding is > 8 or 0, we assume it's corrupt.
            raise ValueError("Padding incorreto ou dados corrompidos. Senha incorreta ou arquivo não Blowfish?")
        
        # Verify padding integrity: all padding bytes should match padding_len
        if not all(byte == padding_len for byte in decrypted_data[-padding_len:]):
             raise ValueError("Integridade do padding violada. Senha incorreta ou arquivo corrompido.")

        return decrypted_data[:-padding_len]

def derive_key_pbkdf2(password: bytes, salt: bytes, dk_len: int = 16, iterations: int = 10000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=dk_len,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password)

def blowfish_encrypt_file(input_file: str, output_file: str, password: str):
    salt = os.urandom(16)
    key = derive_key_pbkdf2(password.encode(), salt, dk_len=32) # Blowfish key can be up to 56 bytes, using 32 for common practice.
    
    cipher = Blowfish(key)
    with open(input_file, 'rb') as f:
        plaintext = f.read()
    
    ciphertext = cipher.encrypt(plaintext)
    
    with open(output_file, 'wb') as f:
        f.write(salt)
        f.write(ciphertext)

def blowfish_decrypt_file(input_file: str, output_file: str, password: str):
    with open(input_file, 'rb') as f:
        salt = f.read(16)
        ciphertext = f.read()
    
    key = derive_key_pbkdf2(password.encode(), salt, dk_len=32)
    cipher = Blowfish(key)
    
    try:
        plaintext = cipher.decrypt(ciphertext)
    except ValueError as e:
        raise ValueError(f"Erro ao descriptografar: {e}")
    
    with open(output_file, 'wb') as f:
        f.write(plaintext)

# ====================================================================
# RSA and AES Hybrid Implementation
# ====================================================================

class CryptographyHandler:
    @staticmethod
    def generate_rsa_keys(key_name: str = "rsa_key", key_size: int = 2048) -> Tuple[Path, Path]:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        private_key_path = ENCRYPT_FOLDER / f"{key_name}_private.pem"
        public_key_path = ENCRYPT_FOLDER / f"{key_name}_public.pem"

        with open(private_key_path, "wb") as f:
            f.write(private_pem)

        with open(public_key_path, "wb") as f:
            f.write(public_pem)
        
        return public_key_path, private_key_path

    @staticmethod
    def hybrid_encrypt_file(input_file: str, public_key_file: str, output_file: str):
        with open(input_file, 'rb') as f:
            plaintext = f.read()

        with open(public_key_file, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
        
        # Generate a random AES key (session key)
        session_key = os.urandom(32) # AES-256 key
        
        # Encrypt the session key with RSA
        encrypted_session_key = public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Encrypt the data with AES using the session key (AES-256 GCM recommended)
        iv = os.urandom(16) # Initialization vector for AES
        cipher = Cipher(algorithms.AES(session_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        tag = encryptor.tag # Authentication tag for GCM

        # Write everything to the output file: encrypted_session_key, iv, tag, ciphertext
        with open(output_file, 'wb') as f:
            f.write(encrypted_session_key)
            f.write(iv)
            f.write(tag)
            f.write(ciphertext)

    @staticmethod
    def hybrid_decrypt_file(input_file: str, private_key_file: str, output_file: str):
        with open(private_key_file, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None, # Assuming no password for private key
                backend=default_backend()
            )
        
        with open(input_file, 'rb') as f:
            rsa_key_size_bytes = private_key.key_size // 8 # Get key size after loading private key
            encrypted_session_key = f.read(rsa_key_size_bytes)
            iv = f.read(16) # AES IV size
            tag = f.read(16) # AES GCM tag size
            ciphertext = f.read()
        
        # Decrypt the session key with RSA
        try:
            session_key = private_key.decrypt(
                encrypted_session_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except Exception as e:
            raise ValueError(f"Erro ao descriptografar a chave de sessão RSA: {e}. Chave privada incorreta ou arquivo corrompido.")

        # Decrypt the data with AES using the session key
        cipher = Cipher(algorithms.AES(session_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        
        try:
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        except CryptoInvalidTag:
            raise ValueError("Tag de autenticação inválida. Arquivo corrompido ou senha/chave incorreta.")
        except Exception as e:
            raise e

        with open(output_file, 'wb') as f:
            f.write(plaintext)

# ====================================================================
# Compression Implementation (Huffman and LZW)
# ====================================================================

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

# ====================================================================
# Streamlit UI Functions
# ====================================================================

def show_encryption_ui():
    st.title("Ferramenta de Criptografia de Arquivos")

    # Opções para o selectbox
    operations = [
        "Blowfish Criptografar",
        "Blowfish Descriptografar",
        "Gerar Chaves RSA",
        "Híbrida (AES + RSA) Criptografar",
        "Híbrida (AES + RSA) Descriptografar"
    ]
    
    selected_operation = st.selectbox("Selecione a Operação de Criptografia", operations)

    # Common variables for file paths
    input_file_path = None
    public_key_file_path = None
    private_key_file_path = None
    
    # Select file source
    if selected_operation != "Gerar Chaves RSA": # Key generation doesn't need input file
        file_source = st.radio(
            "Selecionar Origem do Arquivo:", 
            ("Padrão", "Escolha do Usuário"), 
            key="crypto_file_source"
        )
        
        # Temporary directory for user uploads
        temp_dir_upload = None

        if file_source == "Padrão":
            default_files_options = {}
            if selected_operation in ["Blowfish Criptografar", "Híbrida (AES + RSA) Criptografar"]:
                # For encryption, offer general data files
                default_files_options["test_document.txt"] = TEST_TEXT_FILE
                for name, path in PREDEFINED_FILES.items():
                    default_files_options[name] = path
            elif selected_operation == "Blowfish Descriptografar":
                # For Blowfish decryption, list .enc.bf files from ENCRYPT_FOLDER
                for file_name in os.listdir(ENCRYPT_FOLDER):
                    if file_name.endswith(".enc.bf"):
                        default_files_options[file_name] = ENCRYPT_FOLDER / file_name
            elif selected_operation == "Híbrida (AES + RSA) Descriptografar":
                # For Hybrid decryption, list .enc.aes_rsa files from ENCRYPT_FOLDER
                for file_name in os.listdir(ENCRYPT_FOLDER):
                    if file_name.endswith(".enc.aes_rsa"):
                        default_files_options[file_name] = ENCRYPT_FOLDER / file_name
            
            if default_files_options:
                selected_file_name = st.selectbox(f"Selecione um arquivo:", list(default_files_options.keys()), key="default_crypto_file_select")
                input_file_path = default_files_options[selected_file_name]
            else:
                st.warning(f"Nenhum arquivo padrão encontrado para '{selected_operation}'. Por favor, tente a opção 'Escolha do Usuário'.")
        else: # Escolha do Usuário
            # Determine allowed types for file uploader
            allowed_types = []
            if selected_operation in ["Blowfish Criptografar", "Híbrida (AES + RSA) Criptografar"]:
                # For encryption, allow any type
                allowed_types = [] # Setting to empty list means no type filter
            elif selected_operation == "Blowfish Descriptografar":
                allowed_types = ["bf"] # Blowfish encrypted files
            elif selected_operation == "Híbrida (AES + RSA) Descriptografar":
                allowed_types = ["aes_rsa"] # Hybrid encrypted files
            
            uploaded_file = st.file_uploader(
                "Carregar um arquivo:", 
                type=allowed_types if allowed_types else None, # If empty, allows any type
                key="upload_crypto_main"
            )
            if uploaded_file:
                temp_dir_upload = tempfile.mkdtemp()
                input_file_path = os.path.join(temp_dir_upload, uploaded_file.name)
                with open(input_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.info(f"Arquivo '{uploaded_file.name}' carregado temporariamente.")

    # Specific fields for each operation
    if selected_operation == "Blowfish Criptografar":
        st.header("Criptografia Blowfish")
        output_filename = st.text_input("Nome do arquivo de saída (será salvo em 'Documents/Data/Encrypt')", 
                                        value=f"{Path(input_file_path).stem}.enc.bf" if input_file_path else "", 
                                        key="blowfish_output_enc")
        password = st.text_input("Senha para Blowfish", type="password", key="blowfish_password_enc")

        if st.button("Criptografar com Blowfish", key="btn_blowfish_enc"):
            if input_file_path and output_filename and password:
                output_path = ENCRYPT_FOLDER / output_filename
                try:
                    blowfish_encrypt_file(str(input_file_path), str(output_path), password)
                    st.success(f"Arquivo criptografado com sucesso em '{output_path}'!")
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Baixar Arquivo Criptografado",
                            data=f.read(),
                            file_name=output_filename,
                            mime="application/octet-stream"
                        )
                except Exception as e:
                    st.error(f"Erro na criptografia Blowfish: {e}")
                finally:
                    if temp_dir_upload and os.path.exists(temp_dir_upload):
                        try:
                            os.remove(input_file_path)
                            os.rmdir(temp_dir_upload)
                        except OSError as e:
                            st.warning(f"Não foi possível limpar o diretório temporário: {e}")
            else:
                st.warning("Por favor, selecione um arquivo de entrada, forneça um nome de saída e uma senha.")

    elif selected_operation == "Blowfish Descriptografar":
        st.header("Descriptografia Blowfish")
        output_filename = st.text_input("Nome do arquivo de saída (ex: arquivo.dec.bf)", 
                                        value=f"{Path(input_file_path).stem.replace('.enc','')}.dec.bf" if input_file_path else "", 
                                        key="blowfish_output_dec")
        password = st.text_input("Senha para Blowfish", type="password", key="blowfish_password_dec")

        if st.button("Descriptografar com Blowfish", key="btn_blowfish_dec"):
            if input_file_path and output_filename and password:
                with tempfile.TemporaryDirectory() as temp_dir_output: # Use a new temp dir for output
                    output_path = os.path.join(temp_dir_output, output_filename)
                    try:
                        blowfish_decrypt_file(str(input_file_path), output_path, password)
                        st.success(f"Arquivo descriptografado com sucesso em '{output_filename}'!")
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Baixar Arquivo Descriptografado",
                                data=f.read(),
                                file_name=output_filename,
                                mime="application/octet-stream"
                            )
                    except Exception as e:
                        st.error(f"Erro na descriptografia Blowfish: {e}")
                    finally:
                        if temp_dir_upload and os.path.exists(temp_dir_upload):
                            try:
                                os.remove(input_file_path)
                                os.rmdir(temp_dir_upload)
                            except OSError as e:
                                st.warning(f"Não foi possível limpar o diretório temporário: {e}")
            else:
                st.warning("Por favor, selecione um arquivo de entrada, forneça um nome de saída e uma senha.")
    
    elif selected_operation == "Gerar Chaves RSA":
        st.header("Geração de Chaves RSA")
        key_name = st.text_input("Nome base para os arquivos de chave", value="minhas_chaves", key="rsa_key_name")
        key_size = st.selectbox("Tamanho da chave RSA (bits)", options=[1024, 2048, 4096], index=1, key="rsa_key_size")

        if st.button("Gerar Chaves RSA", key="btn_rsa_keys"):
            try:
                public_key_path, private_key_path = CryptographyHandler.generate_rsa_keys(key_name, key_size)
                
                st.success(f"Chaves RSA geradas com sucesso e salvas em '{ENCRYPT_FOLDER}': '{public_key_path.name}' e '{private_key_path.name}'")
                
                # Para download no Streamlit, precisamos ler o conteúdo das chaves
                with open(public_key_path, "rb") as f:
                    st.download_button(
                        label="Baixar Chave Pública",
                        data=f.read(),
                        file_name=public_key_path.name,
                        mime="application/x-pem-file"
                    )
                with open(private_key_path, "rb") as f:
                    st.download_button(
                        label="Baixar Chave Privada",
                        data=f.read(),
                        file_name=private_key_path.name,
                        mime="application/x-pem-file"
                    )
            except Exception as e:
                st.error(f"Erro ao gerar chaves RSA: {e}")

    elif selected_operation == "Híbrida (AES + RSA) Criptografar":
        st.header("Criptografia Híbrida (AES + RSA)")
        # --- Public Key Selection ---
        st.subheader("Seleção da Chave Pública")
        key_file_source_enc = st.radio("Origem da Chave Pública:", ("Padrão", "Escolha do Usuário"), key="pk_source_enc")
        
        if key_file_source_enc == "Padrão":
            default_pk_files = {p.name: p for p in ENCRYPT_FOLDER.glob("*.pem") if "public" in p.name}
            if default_pk_files:
                selected_pk_name = st.selectbox("Selecione uma Chave Pública:", list(default_pk_files.keys()), key="default_pk_enc")
                public_key_file_path = default_pk_files[selected_pk_name]
            else:
                st.warning("Nenhuma chave pública (.pem) encontrada na pasta 'Documents/Data/Encrypt'. Por favor, gere uma ou carregue-a.")
        else: # Escolha do Usuário
            uploaded_pk_file = st.file_uploader("Carregar chave pública (.pem)", type=["pem"], key="upload_pk_enc")
            if uploaded_pk_file:
                temp_dir_pk_upload = tempfile.mkdtemp()
                public_key_file_path = os.path.join(temp_dir_pk_upload, uploaded_pk_file.name)
                with open(public_key_file_path, "wb") as f:
                    f.write(uploaded_pk_file.getbuffer())
                st.info(f"Chave pública '{uploaded_pk_file.name}' carregada temporariamente.")

        # --- Output Filename ---
        default_output_name = ""
        if input_file_path:
            base_name = os.path.splitext(Path(input_file_path).name)[0]
            default_output_name = f"{base_name}.enc.aes_rsa"
        output_filename = st.text_input("Nome do arquivo de saída (será salvo em 'Documents/Data/Encrypt')", 
                                        value=default_output_name, 
                                        key="hybrid_output_enc")

        if st.button("Criptografar Híbrido", key="btn_hybrid_enc"):
            if input_file_path and public_key_file_path and output_filename:
                output_path = ENCRYPT_FOLDER / output_filename
                try:
                    CryptographyHandler.hybrid_encrypt_file(str(input_file_path), str(public_key_file_path), str(output_path))
                    st.success(f"Arquivo criptografado hibridamente com sucesso em '{output_path}'!")
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Baixar Arquivo Híbrido Criptografado",
                            data=f.read(),
                            file_name=output_filename,
                            mime="application/octet-stream"
                        )
                except Exception as e:
                    st.error(f"Erro na criptografia híbrida: {e}")
                finally:
                    if temp_dir_upload and os.path.exists(temp_dir_upload):
                        try:
                            os.remove(input_file_path)
                            os.rmdir(temp_dir_upload)
                        except OSError as e:
                            st.warning(f"Não foi possível limpar o diretório de arquivo de entrada temporário: {e}")
                    if 'temp_dir_pk_upload' in locals() and temp_dir_pk_upload and os.path.exists(temp_dir_pk_upload):
                         try:
                             os.remove(public_key_file_path)
                             os.rmdir(temp_dir_pk_upload)
                         except OSError as e:
                             st.warning(f"Não foi possível limpar o diretório de chave pública temporário: {e}")
            else:
                st.warning("Por favor, selecione um arquivo de entrada, uma chave pública e forneça um nome de saída.")

    elif selected_operation == "Híbrida (AES + RSA) Descriptografar":
        st.header("Descriptografia Híbrida (AES + RSA)")
        # --- Private Key Selection ---
        st.subheader("Seleção da Chave Privada")
        key_file_source_dec = st.radio("Origem da Chave Privada:", ("Padrão", "Escolha do Usuário"), key="pk_source_dec")
        
        if key_file_source_dec == "Padrão":
            default_pr_files = {p.name: p for p in ENCRYPT_FOLDER.glob("*.pem") if "private" in p.name}
            if default_pr_files:
                selected_pr_name = st.selectbox("Selecione uma Chave Privada:", list(default_pr_files.keys()), key="default_pr_dec")
                private_key_file_path = default_pr_files[selected_pr_name]
            else:
                st.warning("Nenhuma chave privada (.pem) encontrada na pasta 'Documents/Data/Encrypt'. Por favor, gere uma ou carregue-a.")
        else: # Escolha do Usuário
            uploaded_pr_file = st.file_uploader("Carregar chave privada (.pem)", type=["pem"], key="upload_pr_dec")
            if uploaded_pr_file:
                temp_dir_pr_upload = tempfile.mkdtemp()
                private_key_file_path = os.path.join(temp_dir_pr_upload, uploaded_pr_file.name)
                with open(private_key_file_path, "wb") as f:
                    f.write(uploaded_pr_file.getbuffer())
                st.info(f"Chave privada '{uploaded_pr_file.name}' carregada temporariamente.")

        # --- Output Filename ---
        default_output_name = ""
        if input_file_path:
            base_name = os.path.splitext(Path(input_file_path).name)[0]
            if base_name.endswith(".enc"): # Assuming the .aes_rsa is part of the name
                base_name = base_name[:-4]
            default_output_name = f"{base_name}.dec.aes_rsa"
        
        output_filename = st.text_input("Nome do arquivo de saída (ex: arquivo.dec.aes_rsa)", 
                                        value=default_output_name, 
                                        key="hybrid_output_dec")

        if st.button("Descriptografar Híbrido", key="btn_hybrid_dec"):
            if input_file_path and private_key_file_path and output_filename:
                with tempfile.TemporaryDirectory() as temp_dir_output: # Use a new temp dir for output
                    output_path = os.path.join(temp_dir_output, output_filename)
                    try:
                        CryptographyHandler.hybrid_decrypt_file(str(input_file_path), str(private_key_file_path), output_path)
                        st.success(f"Arquivo descriptografado hibridamente com sucesso em '{output_filename}'!")
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Baixar Arquivo Híbrido Descriptografado",
                                data=f.read(),
                                file_name=output_filename,
                                mime="application/octet-stream"
                            )
                    except Exception as e:
                        st.error(f"Erro na descriptografia híbrida: {e}")
                    finally:
                        if temp_dir_upload and os.path.exists(temp_dir_upload):
                            try:
                                os.remove(input_file_path)
                                os.rmdir(temp_dir_upload)
                            except OSError as e:
                                st.warning(f"Não foi possível limpar o diretório de arquivo de entrada temporário: {e}")
                        if 'temp_dir_pr_upload' in locals() and temp_dir_pr_upload and os.path.exists(temp_dir_pr_upload):
                            try:
                                os.remove(private_key_file_path)
                                os.rmdir(temp_dir_pr_upload)
                            except OSError as e:
                                st.warning(f"Não foi possível limpar o diretório de chave privada temporário: {e}")
            else:
                st.warning("Por favor, selecione um arquivo de entrada, uma chave privada e forneça um nome de saída.")

def show_compression_ui():
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
            # Permite .csv e os novos tipos de arquivo predefinidos para compressão
            allowed_types = [".csv"] + [os.path.splitext(f.name)[1] for f in PREDEFINED_FILES.values()] + ["txt"] # Added .txt
        else: # Descompressão
            if algorithm == "Huffman":
                allowed_types = [HUFFMAN_COMPRESSED_EXTENSION]
            elif algorithm == "LZW":
                allowed_types = [LZW_COMPRESSED_EXTENSION]
        
        # Seleção de arquivo
        file_source = st.radio("Selecionar Origem do Arquivo:", ("Padrão", "Escolha do Usuário"), key="file_source")
        
        selected_file_name = None
        uploaded_file = None

        if file_source == "Padrão":
            try:
                default_files_options = {}
                if operation == "Compressão":
                    # Adiciona arquivos predefinidos à lista de opções
                    default_files_options["test_document.txt"] = TEST_TEXT_FILE
                    for name, path in PREDEFINED_FILES.items():
                        default_files_options[name] = path
                    # Adiciona outros arquivos CSV da pasta HUFFMAN_SOURCE_FOLDER, se houver
                    for file_name in os.listdir(HUFFMAN_SOURCE_FOLDER):
                        if file_name.endswith(DEFAULT_EXTENSION) and file_name not in [p.name for p in PREDEFINED_FILES.values()]:
                            default_files_options[file_name] = HUFFMAN_SOURCE_FOLDER / file_name

                else: # Descompressão
                    # Lista arquivos comprimidos específicos para descompressão
                    target_folder = HUFFMAN_COMPRESSED_FOLDER if algorithm == "Huffman" else LZW_COMPRESSED_FOLDER
                    target_ext = HUFFMAN_COMPRESSED_EXTENSION if algorithm == "Huffman" else LZW_COMPRESSED_EXTENSION
                    for file_name in os.listdir(target_folder):
                        if file_name.endswith(target_ext):
                            default_files_options[file_name] = target_folder / file_name

                if default_files_options:
                    # Usar as chaves (nomes amigáveis) no selectbox
                    selected_file_name = st.selectbox(f"Selecione um arquivo:", list(default_files_options.keys()))
                    input_path_tab1 = default_files_options[selected_file_name]
                else:
                    st.warning(f"Nenhum arquivo {', '.join(allowed_types)} encontrado para a operação selecionada.")
            except Exception as e:
                st.error(f"Erro ao acessar o diretório padrão: {str(e)}")
        else: # Escolha do Usuário
            # Streamlit espera extensões sem o ponto inicial
            uploaded_file_types_for_st = [ext.strip('.') for ext in allowed_types if ext] if "" not in allowed_types else []
            uploaded_file = st.file_uploader(
                "Carregar um arquivo:", 
                type=uploaded_file_types_for_st if uploaded_file_types_for_st else None, # If empty, allows any type
                key="upload_tab1"
            )
            if uploaded_file:
                # Saves to a temporary directory for processing
                temp_dir_tab1 = tempfile.mkdtemp()
                input_path_tab1 = os.path.join(temp_dir_tab1, uploaded_file.name)
                with open(input_path_tab1, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.info(f"Arquivo '{uploaded_file.name}' carregado temporariamente.")

        # Input for output filename for compression
        default_output_comp_name = ""
        if input_path_tab1 and operation == "Compressão":
            base_name_comp = os.path.splitext(os.path.basename(input_path_tab1))[0]
            output_ext_comp = HUFFMAN_COMPRESSED_EXTENSION if algorithm == "Huffman" else LZW_COMPRESSED_EXTENSION
            default_output_comp_name = f"{base_name_comp}{output_ext_comp}"
        
        output_filename_comp = ""
        if operation == "Compressão":
            output_filename_comp = st.text_input(f"Nome do arquivo de saída (será salvo em 'Documents/Data/Source/{algorithm.capitalize()}')", # Adjusted path string
                                                value=default_output_comp_name, key="output_filename_comp")
        
        if input_path_tab1 and st.button(f"Executar {operation}", key="btn_exec_comp"):
            progress_bar.progress(0)
            progress_text.text(f"Iniciando {operation.lower()}...")
            
            output_folder = HUFFMAN_COMPRESSED_FOLDER if algorithm == "Huffman" else LZW_COMPRESSED_FOLDER
            
            try:
                if operation == "Compressão":
                    if not output_filename_comp:
                        st.warning("Por favor, forneça um nome para o arquivo de saída compactado.")
                        return # Exit function if output filename is empty
                    
                    output_path_tab1 = os.path.join(output_folder, output_filename_comp)

                    if algorithm == "Huffman":
                        orig_s, comp_s, ratio, proc_t = HuffmanProcessor.compress_file(input_path_tab1, output_path_tab1, update_progress)
                    else: # LZW
                        orig_s, comp_s, ratio, proc_t = LZWProcessor.compress(input_path_tab1, output_path_tab1, update_progress)
                    
                    st.success(f"Compressão {algorithm} Concluída!")
                    st.write(f"Tamanho Original: {orig_s / 1024:.2f} KB")
                    st.write(f"Tamanho Comprimido: {comp_s / 1024:.2f} KB")
                    st.write(f"Taxa de Compressão: {ratio:.2f}%")
                    st.write(f"Tempo Gasto: {proc_t:.4f} segundos")

                    if comp_s > 0:
                        with open(output_path_tab1, "rb") as f_out:
                            st.download_button(
                                label=f"Baixar Arquivo Comprimido ({output_ext_comp})",
                                data=f_out.read(),
                                file_name=output_filename_comp,
                                mime="application/octet-stream"
                            )

                else: # Descompressão
                    original_file_name_base, _ = os.path.splitext(os.path.basename(input_path_tab1))
                    # Remove the compression extension (.huff or .lzw) for the decompressed filename
                    if original_file_name_base.endswith(HUFFMAN_COMPRESSED_EXTENSION.strip('.')):
                        original_file_name_base = original_file_name_base[:-len(HUFFMAN_COMPRESSED_EXTENSION.strip('.'))]
                    elif original_file_name_base.endswith(LZW_COMPRESSED_EXTENSION.strip('.')):
                        original_file_name_base = original_file_name_base[:-len(LZW_COMPRESSED_EXTENSION.strip('.'))]

                    output_file_name = f"{original_file_name_base}.decompressed"
                    output_path_tab1 = os.path.join(TEMP_FOLDER, output_file_name) # Decompress to temp for now
                    
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
                if uploaded_file and temp_dir_tab1 and os.path.exists(temp_dir_tab1):
                    try:
                        if os.path.exists(input_path_tab1):
                            os.remove(input_path_tab1)
                        os.rmdir(temp_dir_tab1)
                    except OSError as e:
                        st.warning(f"Não foi possível limpar o diretório de upload temporário: {str(e)}")
                if operation == "Descompressão" and output_path_tab1 and os.path.exists(output_path_tab1):
                    try:
                        os.remove(output_path_tab1)
                    except OSError as e:
                        st.warning(f"Não foi possível limpar o arquivo de saída descomprimido temporário: {str(e)}")

        progress_bar.progress(1.0)
        time.sleep(0.5)
    
    elif selected_view == "Comparação de Algoritmos":
        st.subheader("Comparação de Desempenho de Algoritmos")
        st.write("Compare os algoritmos Huffman e LZW no mesmo arquivo")
        
        compare_file_source = st.radio(
            "Selecione o arquivo para comparação:", 
            ("Padrão", "Escolha do Usuário"), # Renomeado "CSV Padrão" para "Padrão"
            key="compare_source_comp"
        )
        
        compare_file_path = None # Renomeado de compare_file para compare_file_path
        compare_uploaded_file = None # Renomeado de compare_uploaded para compare_uploaded_file
        temp_dir_compare_upload = None
        
        if compare_file_source == "Padrão":
            try:
                default_compare_files_options = {}
                # Add all predefined files for comparison
                default_compare_files_options["test_document.txt"] = TEST_TEXT_FILE
                for name, path in PREDEFINED_FILES.items():
                    default_compare_files_options[name] = path
                # Add CSV files from HUFFMAN_SOURCE_FOLDER, if any
                for file_name in os.listdir(HUFFMAN_SOURCE_FOLDER):
                    if file_name.endswith(DEFAULT_EXTENSION) and file_name not in [p.name for p in PREDEFINED_FILES.values()]:
                        default_compare_files_options[file_name] = HUFFMAN_SOURCE_FOLDER / file_name
                
                if default_compare_files_options:
                    selected_compare_file_name = st.selectbox("Selecione um arquivo para comparação:", list(default_compare_files_options.keys()))
                    compare_file_path = default_compare_files_options[selected_compare_file_name]
                else:
                    st.warning(f"Nenhum arquivo CSV ou arquivo de dados predefinido encontrado para comparação em {HUFFMAN_SOURCE_FOLDER} ou {DATA_FOLDER}.")
            except Exception as e:
                st.error(f"Erro ao acessar o diretório de origem para comparação: {str(e)}")
        else:
            # For comparison, allows .txt, .csv, .lzw, .huff, .db, .idx, .btr
            compare_uploaded_allowed_types = ["txt", DEFAULT_EXTENSION, HUFFMAN_COMPRESSED_EXTENSION, LZW_COMPRESSED_EXTENSION] + [os.path.splitext(f.name)[1] for f in PREDEFINED_FILES.values()]
            uploaded_file_types_for_st = [ext.strip('.') for ext in compare_uploaded_allowed_types]

            compare_uploaded_file = st.file_uploader(
                "Carregar um arquivo para comparação", 
                type=uploaded_file_types_for_st,
                key="compare_upload_comp"
            )
            if compare_uploaded_file:
                # Saves to temporary location
                temp_dir_compare_upload = tempfile.mkdtemp()
                compare_file_path = os.path.join(temp_dir_compare_upload, compare_uploaded_file.name)
                with open(compare_file_path, "wb") as f:
                    f.write(compare_uploaded_file.getbuffer())
        
        if compare_file_path and st.button("Executar Comparação", key="btn_exec_compare_comp"):
            progress_bar.progress(0)
            progress_text.text("Iniciando comparação...")
            
            try:
                df = compare_algorithms(compare_file_path, update_progress)
                
                st.success("Comparação concluída!")
                st.dataframe(df.style.format({
                    'Original Size (KB)': '{:.2f}',
                    'Compressed Size (KB)': '{:.2f}',
                    'Compression Ratio (%)': '{:.2f}',
                    'Compression Time (s)': '{:.4f}',
                    'Decompression Time (s)': '{:.4f}',
                    'Total Time (s)': '{:.4f}'
                }))
                
                fig = plot_comparison(df)
                st.pyplot(fig)
                
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
                if compare_uploaded_file and temp_dir_compare_upload and os.path.exists(temp_dir_compare_upload):
                    try:
                        if compare_file_path and os.path.exists(compare_file_path):
                            os.remove(compare_file_path)
                        os.rmdir(temp_dir_compare_upload)
                    except OSError as e:
                        st.warning(f"Não foi possível limpar o diretório de upload temporário de comparação: {str(e)}")
                
    # Reset progress bar and text after any operation
    progress_bar.empty()
    progress_text.empty()


# --- DataObject Class ---
class DataObject:
    """
    Represents a traffic accident record with enhanced validation and serialization.
    Each instance corresponds to a single record in the database.
    """
    
    def __init__(self, row_data: Optional[List[str]] = None):
        """
        Initializes a DataObject.
        If row_data is provided, it attempts to populate fields from it and validate.
        """
        # Initialize all fields with type-appropriate default values
        self._initialize_defaults()
        
        if row_data is not None:
            try:
                self._initialize_from_row(row_data)
                # Perform comprehensive validation after initialization
                if not self.validate():
                    raise DataValidationError("Data validation failed during initialization.")
            except (DataValidationError, ValueError) as e:
                logger.error(f"Error initializing DataObject from row: {str(e)} | Row: {row_data}")
                raise DataValidationError(f"Invalid data for record: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error during DataObject initialization: {traceback.format_exc()}")
                raise DatabaseError(f"Internal error during data initialization: {str(e)}")

    def _initialize_defaults(self):
        """Initializes all fields with safe and type-appropriate default values."""
        self.crash_date = ""
        self.traffic_control_device = "UNKNOWN"
        self.weather_condition = "UNKNOWN"
        self.lighting_condition = "UNKNOWN"
        self.first_crash_type = "UNKNOWN"
        self.trafficway_type = "UNKNOWN"
        self.alignment = "UNKNOWN"
        self.roadway_surface_cond = "UNKNOWN"
        self.road_defect = "NONE"
        self.crash_type = "UNKNOWN"
        self.intersection_related_i = "NO"
        self.damage = "UNKNOWN"
        self.prim_contributory_cause = "UNKNOWN"
        self.num_units = 0
        self.most_severe_injury = "NONE"
        self.injuries_total = 0.0
        self.injuries_fatal = 0.0
        self.injuries_incapacitating = 0.0
        self.injuries_non_incapacitating = 0.0
        self.injuries_reported_not_evident = 0.0
        self.injuries_no_indication = 0.0
        self.crash_hour = 0
        self.crash_day_of_week = 1 # Monday
        self.crash_month = 1      # January

    def _initialize_from_row(self, row_data: List[str]):
        """
        Populates object fields from a list of strings (e.g., from a CSV row).
        Performs basic type conversion and uses validation helpers.
        """
        if len(row_data) != len(FIELDS):
            raise ValueError(f"Expected {len(FIELDS)} fields, but got {len(row_data)}.")
        
        # Processed data: strip whitespace and convert empty strings to None
        processed_data = [value.strip() if isinstance(value, str) else None for value in row_data]
        
        self.crash_date = self._validate_date(processed_data[0])
        self.traffic_control_device = self._validate_string(processed_data[1], "traffic_control_device", allow_empty=True)
        self.weather_condition = self._validate_string(processed_data[2], "weather_condition", allow_empty=True)
        self.lighting_condition = self._validate_string(processed_data[3], "lighting_condition", allow_empty=True)
        self.first_crash_type = self._validate_string(processed_data[4], "first_crash_type", allow_empty=True)
        self.trafficway_type = self._validate_string(processed_data[5], "trafficway_type", allow_empty=True)
        self.alignment = self._validate_string(processed_data[6], "alignment", allow_empty=True)
        self.roadway_surface_cond = self._validate_string(processed_data[7], "roadway_surface_cond", allow_empty=True)
        self.road_defect = self._validate_string(processed_data[8], "road_defect", allow_empty=True)
        self.crash_type = self._validate_string(processed_data[9], "crash_type", allow_empty=False) # Required field
        self.intersection_related_i = self._validate_yes_no(processed_data[10])
        self.damage = self._validate_string(processed_data[11], "damage", allow_empty=True)
        self.prim_contributory_cause = self._validate_string(processed_data[12], "prim_contributory_cause", allow_empty=True)
        self.num_units = self._validate_positive_int(processed_data[13], "num_units", min_val=0)
        self.most_severe_injury = self._validate_string(processed_data[14], "most_severe_injury", allow_empty=True)
        self.injuries_total = self._validate_positive_float(processed_data[15], "injuries_total", min_val=0.0)
        self.injuries_fatal = self._validate_positive_float(processed_data[16], "injuries_fatal", min_val=0.0)
        self.injuries_incapacitating = self._validate_positive_float(processed_data[17], "injuries_incapacitating", min_val=0.0)
        self.injuries_non_incapacitating = self._validate_positive_float(processed_data[18], "injuries_non_incapacitating", min_val=0.0)
        self.injuries_reported_not_evident = self._validate_positive_float(processed_data[19], "injuries_reported_not_evident", min_val=0.0)
        self.injuries_no_indication = self._validate_positive_float(processed_data[20], "injuries_no_indication", min_val=0.0)
        self.crash_hour = self._validate_range(processed_data[21], "crash_hour", 0, 23)
        self.crash_day_of_week = self._validate_range(processed_data[22], "crash_day_of_week", 1, 7) # 1=Monday, 7=Sunday
        self.crash_month = self._validate_range(processed_data[23], "crash_month", 1, 12)

    @staticmethod
    def _validate_date(date_str: Optional[str]) -> str:
        """
        Validates and standardizes a date string to YYYY-MM-DD format.
        Handles various common input formats including those with time and AM/PM.
        Raises DataValidationError if a non-empty string cannot be parsed.
        """
        logger.debug(f"[_validate_date] Input date_str: '{date_str}' ({type(date_str)})")
        if not date_str:
            logger.debug(f"[_validate_date] Input date_str is empty/None. Returning ''")
            return "" # Return empty string for None or empty input
        
        date_str = date_str.strip()
        if not date_str: # After stripping, if it becomes empty
            logger.debug(f"[_validate_date] Input date_str became empty after stripping. Returning ''")
            return ""

        # Try multiple common date and datetime formats
        # Added formats to handle time and AM/PM
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d', 
                    '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', # 24-hour time
                    '%m/%d/%Y %I:%M:%S %p', '%Y-%m-%d %I:%M:%S %p'): # 12-hour time with AM/PM
            try:
                dt = datetime.strptime(date_str, fmt)
                formatted_date = dt.strftime('%Y-%m-%d') # Always store as YYYY-MM-DD
                logger.debug(f"[_validate_date] Successfully parsed '{date_str}' with '{fmt}'. Returning '{formatted_date}'")
                return formatted_date
            except ValueError:
                logger.debug(f"[_validate_date] Failed to parse '{date_str}' with format '{fmt}'")
                continue # Try next format
        
        # If execution reaches here, it means date_str was not empty but could not be parsed
        logger.error(f"[_validate_date] Failed to parse date string '{date_str}' into any known format. Raising DataValidationError.")
        raise DataValidationError(f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD or common date/datetime format (e.g., MM/DD/YYYY, DD-MM-YYYY, or with time/AM/PM).")

    @staticmethod
    def _validate_string(value: Optional[str], field_name: str, max_len: int = 255, allow_empty: bool = True) -> str:
        """
        Validates and sanitizes string fields.
        Converts None to "UNKNOWN" if not allowed to be empty.
        Truncates to max_len and removes problematic characters.
        """
        if value is None:
            return "UNKNOWN" if not allow_empty else ""
        
        value = str(value).strip()
        
        if not value:
            return "UNKNOWN" if not allow_empty else ""
            
        # Basic sanitization: remove delimiters and newlines that could break CSV/JSON
        value = value.replace(CSV_DELIMITER, ',').replace('\n', ' ').replace('\r', '')
        
        return value[:max_len] # Truncate to max_len

    @staticmethod
    def _validate_yes_no(value: Optional[str]) -> str:
        """Validates input for 'Yes'/'No' fields."""
        if value is None:
            return "NO"
        
        value = str(value).strip().lower()
        return "YES" if value in ('yes', 'y', 'true', '1') else "NO"

    @staticmethod
    def _validate_positive_int(value: Optional[str], field_name: str, min_val: int = 0) -> int:
        """Validates and converts a value to a non-negative integer."""
        try:
            # Handle empty string or None by returning min_val
            if value is None or value == '':
                return min_val
            
            num = int(float(value)) # Convert via float to handle "5.0"
            if num < min_val:
                logger.warning(f"Integer value for {field_name} ({num}) is less than minimum {min_val}. Setting to {min_val}.")
                return min_val
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    @staticmethod
    def _validate_positive_float(value: Optional[str], field_name: str, min_val: float = 0.0) -> float:
        """Validates and converts a value to a non-negative float."""
        try:
            # Handle empty string or None by returning min_val
            if value is None or value == '':
                return min_val
            
            num = float(value)
            if num < min_val:
                logger.warning(f"Float value for {field_name} ({num}) is less than minimum {min_val}. Setting to {min_val}.")
                return min_val
            return round(num, 2) # Round to 2 decimal places for consistency
        except (ValueError, TypeError):
            logger.warning(f"Invalid float value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    @staticmethod
    def _validate_range(value: Optional[str], field_name: str, min_val: int, max_val: int) -> int:
        """Validates a numeric field to be within a specific integer range."""
        try:
            # Handle empty string or None by returning min_val
            if value is None or value == '':
                return min_val
            
            num = int(float(value)) # Convert via float to handle "12.0"
            if not (min_val <= num <= max_val):
                logger.warning(f"Value for {field_name} ({num}) is out of range [{min_val}-{max_val}]. Setting to {min_val}.")
                return min_val # Default to min_val if out of range
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid numeric value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val
            
    def to_bytes(self) -> bytes:
        """
        Serializes the DataObject into bytes using JSON format.
        Uses sorted keys for consistent byte representation.
        """
        try:
            data_dict = {attr: getattr(self, attr) for attr in FIELDS}
            # Ensure JSON is compact and consistent for hashing
            return json.dumps(data_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
        except TypeError as e:
            logger.error(f"Serialization TypeError in DataObject: {e}. Data dict: {data_dict}")
            raise DatabaseError(f"Failed to serialize record due to invalid data type: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected serialization error in DataObject: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to serialize record: {str(e)}")

    @classmethod
    def from_bytes(cls, byte_data: bytes) -> 'DataObject':
        """
        Deserializes byte data back into a DataObject instance.
        Handles various deserialization errors.
        """
        if not byte_data:
            raise DataValidationError("Attempted to deserialize empty byte data.")
        
        try:
            data_dict = json.loads(byte_data.decode('utf-8'))
            obj = cls() # Create an empty object with defaults
            
            # Populate fields from deserialized dictionary
            for key in FIELDS: # Iterate through FIELDS to ensure all are set
                if key in data_dict:
                    setattr(obj, key, data_dict[key])
                else:
                    # If a field is missing in data_dict, it keeps its default value
                    logger.warning(f"Field '{key}' missing during deserialization. Using default value.")
            
            # Re-validate the deserialized object to ensure data integrity
            if not obj.validate():
                raise DataValidationError("Deserialized object failed re-validation.")
            
            return obj
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"JSON/Unicode decode error during deserialization: {e} | Data: {byte_data[:100]}...")
            raise DatabaseError("Invalid data format during deserialization.")
        except DataValidationError as e:
            logger.error(f"Data validation error after deserialization: {e}")
            raise DatabaseError(f"Corrupt data after deserialization: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected deserialization error: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to deserialize record: {str(e)}")

    def validate(self) -> bool:
        """
        Performs comprehensive semantic validation on the DataObject's fields.
        Ensures consistency and correctness of data.
        """
        try:
            # 1. Required fields check
            if not self.crash_date: 
                raise DataValidationError("Crash date is required.")
            if not self.crash_type or self.crash_type == "UNKNOWN":
                raise DataValidationError("Crash type is required.")
            if not isinstance(self.num_units, int) or self.num_units < 0:
                raise DataValidationError("Number of units must be a non-negative integer.")
            if not isinstance(self.injuries_total, (int, float)) or self.injuries_total < 0:
                raise DataValidationError("Total injuries must be a non-negative number.")
            
            # 2. Date format validation (already done by _validate_date but double-check)
            if self.crash_date: # Only check if not empty
                try:
                    datetime.strptime(self.crash_date, '%Y-%m-%d')
                except ValueError:
                    raise DataValidationError("Invalid crash date format (expected YYYY-MM-DD).")
            
            # 3. Consistency checks for injuries
            total_reported_injuries = (
                self.injuries_fatal + self.injuries_incapacitating +
                self.injuries_non_incapacitating + self.injuries_reported_not_evident +
                self.injuries_no_indication
            )
            # Allow for slight floating point inaccuracies or where total includes unclassified injuries
            if self.injuries_total < total_reported_injuries - 0.01: # Small tolerance for float comparison
                logger.warning(f"Total injuries ({self.injuries_total}) less than sum of specific injuries ({total_reported_injuries}).")
                # For now, this is a warning, not an error that fails validation.
                # Could be changed to an error if strict consistency is required.
            
            # 4. Range validation (already done by _validate_range, but for robustness)
            if not (0 <= self.crash_hour <= 23):
                raise DataValidationError("Crash hour out of valid range (0-23).")
            if not (1 <= self.crash_day_of_week <= 7):
                raise DataValidationError("Crash day of week out of valid range (1-7).")
            if not (1 <= self.crash_month <= 12):
                raise DataValidationError("Crash month out of valid range (1-12).")

            return True
        except DataValidationError as e:
            logger.warning(f"DataObject validation failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during DataObject validation: {traceback.format_exc()}")
            return False
            
    def __repr__(self) -> str:
        """Provides a string representation of the DataObject for debugging."""
        return f"DataObject(ID=N/A, Date='{self.crash_date}', Type='{self.crash_type}', TotalInjuries={self.injuries_total})"

# --- TrafficAccidentsDB Class ---
class TrafficAccidentsDB:
    """
    Handles all database operations for traffic accident records.
    Implements file-based storage with robust locking, backups, and error recovery.
    """
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.lock_file_path = LOCK_FILE
        self._ensure_directories()
        self._last_read_id = 0 # To track the last ID in the file header
        self._lock = filelock.FileLock(self.lock_file_path) # Initialize filelock

    def _ensure_directories(self):
        """Ensures the database and backup directories exist with appropriate permissions."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            os.makedirs(BACKUP_DIR, exist_ok=True)
            # Set permissions for the directories (e.g., rwx for owner, rx for group/others)
            os.chmod(os.path.dirname(self.db_path), 0o755)
            os.chmod(BACKUP_DIR, 0o755)
            logger.info(f"Ensured DB directory '{os.path.dirname(self.db_path)}' and backup directory '{BACKUP_DIR}' exist.")
        except OSError as e:
            logger.critical(f"OS error ensuring directories: {e}")
            raise DatabaseError(f"Failed to create necessary directories: {str(e)}")
        except Exception as e:
            logger.critical(f"Unexpected error ensuring directories: {traceback.format_exc()}")
            raise DatabaseError(f"Critical error initializing database paths: {str(e)}")

    def _acquire_lock(self, timeout: int = 10, interval: float = 0.5):
        """
        Acquires an exclusive file lock to ensure single-process access to the database.
        Implements a timeout and retry mechanism using filelock.
        """
        try:
            self._lock.acquire(timeout=timeout)
            logger.debug(f"Acquired lock on {self.lock_file_path}")
        except filelock.Timeout:
            raise FileLockError(f"Failed to acquire file lock on {self.lock_file_path} within {timeout} seconds. Another process might be holding the lock.")
        except Exception as e:
            logger.error(f"Error acquiring file lock: {e}")
            raise FileLockError(f"Failed to acquire file lock: {str(e)}")

    def _release_lock(self):
        """Releases the acquired file lock."""
        try:
            self._lock.release()
            logger.debug(f"Released lock on {self.lock_file_path}")
        except Exception as e:
            logger.error(f"Error releasing file lock: {e}")
            # Don't re-raise, as it might prevent cleanup

    def _create_backup(self):
        """
        Creates a timestamped backup of the database file and manages backup rotation.
        Keeps only the last MAX_BACKUPS.
        """
        try:
            if not os.path.exists(self.db_path):
                logger.info("No database file found to backup.")
                return
            
            # Clean up old backups first
            backups = sorted(Path(BACKUP_DIR).glob("backup_*.db"))
            while len(backups) >= MAX_BACKUPS:
                oldest = backups.pop(0)
                try:
                    os.unlink(oldest)
                    logger.info(f"Removed old backup: {oldest}")
                except OSError as e:
                    logger.warning(f"Could not remove old backup '{oldest}': {e}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
            
            with open(self.db_path, 'rb') as src:
                with open(backup_path, 'wb') as dst:
                    while True:
                        chunk = src.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        dst.write(chunk)
            
            logger.info(f"Created database backup: {backup_path}")
        except Exception as e:
            logger.error(f"Backup failed: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to create database backup: {str(e)}")

    def get_last_id(self) -> int:
        """Reads the last recorded ID from the database file header."""
        try:
            self._acquire_lock()
            if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) < 4:
                return 0 # File doesn't exist or is too small for an ID header
            
            with open(self.db_path, 'rb') as f:
                id_bytes = f.read(4)
                if len(id_bytes) == 4:
                    self._last_read_id = struct.unpack('I', id_bytes)[0]
                    return self._last_read_id
                else:
                    logger.warning("DB file header is corrupt or incomplete. Resetting last ID to 0.")
                    return 0
        except FileLockError:
            raise # Re-raise if lock failed
        except FileNotFoundError:
            return 0
        except struct.error as e:
            logger.error(f"Structural error reading last ID: {e}")
            raise DatabaseError("Database header corrupt, cannot read last ID.")
        except Exception as e:
            logger.error(f"Error getting last ID: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to retrieve last ID: {str(e)}")
        finally:
            self._release_lock()

    def update_last_id(self, new_id: int):
        """Updates the last recorded ID in the database file header."""
        try:
            self._acquire_lock()
            # Ensure file exists, create with initial ID 0 if not
            mode = 'r+b' if os.path.exists(self.db_path) and os.path.getsize(self.db_path) >= 4 else 'wb'
            with open(self.db_path, mode) as f:
                f.seek(0) # Go to the beginning of the file
                f.write(struct.pack('I', new_id))
                f.flush()
                os.fsync(f.fileno()) # Ensure data is written to disk
            logger.debug(f"Updated last ID to {new_id}")
            self._last_read_id = new_id
        except FileLockError:
            raise # Re-raise if lock failed
        except Exception as e:
            logger.error(f"Error updating last ID: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to update last ID: {str(e)}")
        finally:
            self._release_lock()

    def read_records_paginated(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Reads records from the database file with pagination.
        Includes error recovery for individual corrupt records.
        Returns raw record data (with 'data_bytes').
        """
        records = []
        records_read_count = 0
        try:
            self._acquire_lock()
            if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) < 4:
                logger.info("No database file or empty file to read records from.")
                return []
                
            with open(self.db_path, 'rb') as f:
                f.read(4) # Skip last ID header
                
                current_record_id_in_file = 0 # Logical ID counter for records in file
                while True:
                    current_pos = f.tell()
                    try:
                        record_data_raw = self._read_next_record_raw(f)
                        if record_data_raw is None: # End of file
                            break
                        
                        current_record_id_in_file += 1 # Increment for each record successfully read (raw)
                        
                        # Apply offset
                        if current_record_id_in_file <= offset:
                            continue
                        
                        # Apply limit
                        if limit is not None and records_read_count >= limit:
                            break
                        
                        # Store raw data for session state compatibility
                        records.append(record_data_raw)
                        records_read_count += 1

                    except (DatabaseError) as e: # Only catch DatabaseError (structural issues here)
                        logger.warning(f"Skipping corrupt record at position {current_pos}: {str(e)}. Attempting to recover...")
                        f.seek(current_pos + CHUNK_SIZE) # Try to jump ahead
                        continue # Continue to the next record
                    except Exception as e:
                        logger.error(f"Unexpected error while reading record at {current_pos}: {traceback.format_exc()}")
                        break # Fatal error for current read, cannot continue safely
        
            logger.info(f"Successfully read {len(records)} raw records from the database (offset: {offset}, limit: {limit}).")
            return records
        except FileLockError:
            raise
        except FileNotFoundError:
            return [] # No database file, return empty list
        except Exception as e:
            logger.error(f"Error reading paginated records: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to read paginated records: {str(e)}")
        finally:
            self._release_lock()


    def read_record_by_id(self, search_id: int) -> Optional[Dict[str, Any]]:
        """
        Reads a specific record by its ID.
        Performs a linear scan, as binary search is not practical for this file structure.
        Returns the raw record data (with 'data_bytes').
        """
        if search_id <= 0:
            raise ValueError("Record ID must be positive.")
        
        try:
            self._acquire_lock()
            if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) < 4:
                return None
                
            with open(self.db_path, 'rb') as f:
                f.read(4) # Skip last ID header
                
                while True:
                    current_pos = f.tell() # Store current position for potential recovery
                    try:
                        record_data_raw = self._read_next_record_raw(f)
                        if record_data_raw is None: # End of file
                            break
                        
                        if record_data_raw['id'] == search_id:
                            return record_data_raw # Return raw data for subsequent DataObject creation
                    except (DatabaseError) as e:
                        logger.warning(f"Skipping corrupt record at position {current_pos} during ID search: {str(e)}")
                        # Try to jump past the corrupt record
                        f.seek(current_pos + CHUNK_SIZE)
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error during search for ID {search_id} at {current_pos}: {traceback.format_exc()}")
                        break # Stop search on unexpected error
            
            return None # Record not found
        except FileLockError:
            raise
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error searching for record {search_id}: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to search for record {search_id}: {str(e)}")
        finally:
            self._release_lock()

    def _read_next_record_raw(self, file_obj) -> Optional[Dict[str, Any]]:
        """
        Reads the raw binary components of the next record from the file.
        Does not perform DataObject deserialization here.
        Raises DatabaseError for structural corruption.
        """
        try:
            # Read fixed-size header components
            id_bytes = file_obj.read(4)
            if not id_bytes: return None # End of file
            
            validation_byte = file_obj.read(1)
            if not validation_byte: raise DatabaseError("Incomplete record header: missing validation byte.")
            
            size_bytes = file_obj.read(4)
            if not size_bytes: raise DatabaseError("Incomplete record header: missing size bytes.")
            
            # Unpack binary data
            try:
                record_id = struct.unpack('I', id_bytes)[0]
                validation_flag = struct.unpack('?', validation_byte)[0]
                data_size = struct.unpack('I', size_bytes)[0]
            except struct.error as e:
                raise DatabaseError(f"Corrupt record header structure: {str(e)}")
            
            # Validate size before attempting to read data
            if not (0 < data_size <= 10 * 1024 * 1024): # Max 10MB per record
                raise DatabaseError(f"Invalid record data size ({data_size} bytes). Corrupt header or too large.")
            
            data_bytes = file_obj.read(data_size)
            if len(data_bytes) != data_size:
                raise DatabaseError(f"Incomplete record data: expected {data_size} bytes, got {len(data_bytes)}.")
            
            # Calculate checksum for data integrity verification
            checksum = hashlib.md5(data_bytes).hexdigest()
            
            return {
                'id': record_id,
                'validation': validation_flag,
                'size': data_size,
                'checksum': checksum,
                'data_bytes': data_bytes
            }
        except DatabaseError: # Re-raise custom DB errors as they are specific structural issues
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading raw record: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to read raw record data: {str(e)}")

    def write_record(self, data_object: DataObject) -> int:
        """
        Writes a single DataObject to the database file.
        Acquires a lock, creates a backup, appends the record, and updates the last ID.
        """
        if not isinstance(data_object, DataObject):
            raise TypeError("Expected DataObject instance to write.")
        
        # Pre-validate the object before attempting to write
        if not data_object.validate():
            raise DataValidationError("Attempted to write an invalid DataObject.")

        try:
            self._acquire_lock()
            self._create_backup() # Backup before modification
            
            last_id = self.get_last_id() # Get last ID with lock acquired
            new_id = last_id + 1 if last_id > 0 else 1
            
            obj_bytes = data_object.to_bytes()
            size = len(obj_bytes)
            validation_flag = data_object.validate() # Final validation flag
            
            # Use 'ab' (append binary) to append records.
            # If the file is new or empty, 'wb' (write binary) will create/truncate it,
            # ensuring the header is written correctly.
            mode = 'ab' if os.path.exists(self.db_path) and os.path.getsize(self.db_path) >= 4 else 'wb'
            with open(self.db_path, mode) as f:
                # If opening in 'wb' mode, write the initial ID header (0 for now, updated later)
                if mode == 'wb':
                    f.write(struct.pack('I', 0)) # Placeholder for last ID
                
                # Write record header: ID, validation flag, size of data
                f.write(struct.pack('I', new_id))
                f.write(struct.pack('?', validation_flag))
                f.write(struct.pack('I', size))
                f.write(obj_bytes) # Write the actual data bytes
                
                f.flush()
                os.fsync(f.fileno()) # Ensure data is physically written
                
            self.update_last_id(new_id) # Update the file header with the new last ID
            logger.info(f"Successfully wrote record {new_id} to database.")
            return new_id
        except (FileLockError, DatabaseError, DataValidationError):
            raise # Re-raise specific exceptions
        except Exception as e:
            logger.error(f"Unexpected error writing record: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to write record: {str(e)}")
        finally:
            self._release_lock()

    def _read_csv_iter(self, csv_path: str) -> Iterator[List[str]]:
        """
        Reads CSV file line by line and yields raw row data as a list of strings.
        Handles file encoding and basic CSV errors.
        """
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f, delimiter=CSV_DELIMITER)
                
                # Skip header
                try:
                    next(reader)
                except StopIteration:
                    logger.warning(f"CSV file '{csv_path}' is empty or only contains a header.")
                    return # No data rows to yield
                
                for line_num, row in enumerate(reader, 2): # Start counting from line 2 (after header)
                    yield row
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            raise DatabaseError(f"CSV file not found: {csv_path}")
        except csv.Error as e:
            logger.error(f"CSV parsing error in '{csv_path}': {e}")
            raise DatabaseError(f"Error parsing CSV file: {str(e)}")
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error reading CSV '{csv_path}': {e}. Ensure UTF-8 encoding.")
            raise DatabaseError(f"Encoding error reading CSV. Please ensure it's UTF-8: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error reading CSV file: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to read CSV file: {str(e)}")

    def write_from_csv(
        self, 
        csv_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        Bulk imports records from a CSV file into the database.
        Processes records in a streaming fashion to optimize memory usage.
        Provides progress updates via callback.
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        file_size = os.path.getsize(csv_path)
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"CSV file size ({file_size / (1024*1024):.2f}MB) exceeds maximum allowed of {MAX_FILE_SIZE_MB}MB.")
        
        imported_count = 0
        try:
            self._acquire_lock()
            self._create_backup() # Backup before bulk operation
            
            # Get the current last ID to calculate new IDs sequentially
            last_id = self.get_last_id()
            current_id = last_id + 1 if last_id > 0 else 1

            # Count total records for accurate progress reporting (requires a separate pass)
            total_records = 0
            with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                total_records = sum(1 for line in f) - 1 # Subtract header line

            if total_records <= 0:
                logger.warning(f"No data rows found in CSV file '{csv_path}'.")
                return 0 # No records to import
                
            # Determine initial write mode: 'ab' for append, 'wb' for new file (initial header)
            mode = 'ab' if os.path.exists(self.db_path) and os.path.getsize(self.db_path) >= 4 else 'wb'
            
            with open(self.db_path, mode) as f:
                if mode == 'wb':
                    f.write(struct.pack('I', 0)) # Placeholder for last ID in new file
                
                for i, row in enumerate(self._read_csv_iter(csv_path)):
                    try:
                        # Attempt to create DataObject from the raw row data
                        data_obj = DataObject(row)
                        
                        obj_bytes = data_obj.to_bytes()
                        size = len(obj_bytes)
                        validation_flag = data_obj.validate()
                        
                        f.write(struct.pack('I', current_id))
                        f.write(struct.pack('?', validation_flag))
                        f.write(struct.pack('I', size))
                        f.write(obj_bytes)
                        
                        imported_count += 1
                        current_id += 1 # Increment for the next record
                        
                        # Update progress if callback is provided
                        if progress_callback:
                            progress_callback(i + 1, total_records) # i+1 because enumerate is 0-indexed
                            
                    except (DataValidationError, DatabaseError) as e:
                        logger.warning(f"Skipping invalid record from CSV line {i+2}: {str(e)}") # +2 for 0-indexed i, and header
                        # Continue processing other records even if one fails
                    except Exception as e:
                        logger.error(f"Unexpected error processing CSV line {i+2}: {traceback.format_exc()}")
                        # If an unexpected error occurs, log it and continue
                        
                f.flush()
                os.fsync(f.fileno()) # Ensure all written data is on disk
                
            # Update the last ID in the header after all records are written
            self.update_last_id(current_id - 1)
            logger.info(f"Successfully imported {imported_count} records from CSV.")
            return imported_count
        except (FileLockError, DatabaseError, ValueError, FileNotFoundError):
            raise # Re-raise specific exceptions
        except Exception as e:
            logger.error(f"Unexpected error during CSV import: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to import from CSV: {str(e)}")
        finally:
            self._release_lock()

# --- Streamlit UI Functions ---

def setup_ui():
    """Configures the Streamlit page and applies custom CSS styling."""
    st.set_page_config(
        page_title="Traffic Accidents DB", 
        layout="wide",
        page_icon="🚗"
    )
    
    # Custom CSS for better styling and responsiveness
    st.markdown("""
        <style>
            /* Progress bar styling */
            .stProgress > div > div > div > div {
                background-color: #4CAF50; /* Green */
            }
            /* Main container padding */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1200px; /* Limit content width */
            }
            /* Sidebar styling */
            .sidebar .sidebar-content {
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
            }
            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                color: #2c3e50; /* Darker text for readability */
            }
            /* Custom alert styling */
            .stAlert {
                border-left: 5px solid;
                border-radius: 8px;
                padding: 10px 15px;
                margin-bottom: 15px;
            }
            .stAlert.success { border-color: #4CAF50; background-color: #e6ffe6; }
            .stAlert.info { border-color: #2196F3; background-color: #e0f2fe; }
            .stAlert.warning { border-color: #ff9800; background-color: #fff3e0; }
            .stAlert.error { border-color: #f44336; background-color: #ffe0e0; }

            /* Button styling */
            .stButton>button {
                background-color: #007bff; /* Primary blue */
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                border: none;
                transition: all 0.3s ease;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            }
            .stButton>button:hover {
                background-color: #0056b3; /* Darker blue on hover */
                transform: translateY(-2px); /* Slight lift effect */
                box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
            }
            .stButton>button:active {
                transform: translateY(0);
                box_shadow: 1px 1px 3px rgba(0,0,0,0.2);
            }
            /* Expander styling */
            .streamlit-expanderHeader {
                background-color: #e9ecef; /* Light gray */
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
            /* Text input and selectbox styling */
            .stTextInput>div>div>input, .stSelectbox>div>div>select {
                border-radius: 5px;
                border: 1px solid #ced4da;
                padding: 8px;
            }
            /* Responsive columns */
            @media (max-width: 768px) {
                .main .block-container {
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
                .st-cf { /* Target columns for smaller screens */
                    flex-direction: column;
                }
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🚗 Traffic Accidents Database Manager")
    st.caption("A comprehensive system for managing traffic accident records")
    
    try:
        db = TrafficAccidentsDB() # Initialize DB handler
        
        with st.sidebar:
            st.header("Navigation")
            operation = st.selectbox(
                "Select Operation",
                ["📄 View All Records", 
                 "🔍 Search by ID", 
                 "📤 Import from CSV", 
                 "✍️ Add New Record",
                 "📦 Compactação ",
                 "🔒 Criptografia ",
                 ],
                label_visibility="visible",
                key="sidebar_operation" # Ensure unique key
            )
            
            st.divider()
            st.header("Database Info")
            try:
                last_id = db.get_last_id()
                st.metric("Last Record ID", last_id if last_id > 0 else "No records yet")
            except Exception as e:
                st.error(f"Could not retrieve last record ID: {str(e)}")
                logger.error(f"Failed to get last ID for sidebar: {e}")
            
            st.markdown("---") # Visual separator
            st.subheader("Actions")
            if st.button("🔄 Refresh Application", use_container_width=True, help="Reloads the entire Streamlit application."):
                st.rerun() # Use st.rerun for a full app refresh

            st.markdown("---") # Visual separator
            display_update_registry() # New: Display the update registry
        
        # Dispatch based on selected operation
        if operation == "📄 View All Records":
            view_all_records(db)
        elif operation == "🔍 Search by ID":
            search_by_id(db)
        elif operation == "📤 Import from CSV":
            import_from_csv(db)
        elif operation == "✍️ Add New Record":
            add_new_record(db)
        elif operation == "📦 Compactação ":
            show_compression_ui()
        elif operation == "🔒 Criptografia ":  
            show_encryption_ui() 
    except DatabaseError as e:
        st.error(f"🚨 A critical database error occurred: {str(e)}. Please check application logs.")
        logger.critical(f"Critical DatabaseError in main application setup: {traceback.format_exc()}")
    except FileLockError as e:
        st.error(f"🔒 Failed to acquire file lock: {str(e)}. Another process might be using the database.")
        logger.critical(f"FileLockError in main application setup: {traceback.format_exc()}")
    except Exception as e:
        st.error(f"❌ An unexpected error occurred: {str(e)}. Please try again or contact support.")
        logger.critical(f"Unexpected error in main application setup: {traceback.format_exc()}")

def display_record_data(data_obj: DataObject):
    """
    Displays the details of a single DataObject in a user-friendly format.
    Handles missing attributes gracefully.
    """
    # Removed the isinstance check here as it was causing issues due to Streamlit reruns
    # and objects being from a "previous" class definition in memory.
    # We now trust that DataObject.from_bytes() has already ensured it's a valid object.
    try:
        cols = st.columns(2)
        
        with cols[0]:
            st.subheader("Accident Details")
            st.markdown(f"**Date:** `{getattr(data_obj, 'crash_date', 'N/A')}`")
            st.markdown(f"**Type:** `{getattr(data_obj, 'crash_type', 'N/A')}`")
            st.markdown(f"**Traffic Control:** `{getattr(data_obj, 'traffic_control_device', 'N/A')}`")
            st.markdown(f"**Weather:** `{getattr(data_obj, 'weather_condition', 'N/A')}`")
            st.markdown(f"**Lighting:** `{getattr(data_obj, 'lighting_condition', 'N/A')}`")
            st.markdown(f"**First Crash Type:** `{getattr(data_obj, 'first_crash_type', 'N/A')}`")
            st.markdown(f"**Road Surface:** `{getattr(data_obj, 'roadway_surface_cond', 'N/A')}`")
            st.markdown(f"**Road Defect:** `{getattr(data_obj, 'road_defect', 'N/A')}`")
        
        with cols[1]:
            st.subheader("Impact Details")
            st.markdown(f"**Units Involved:** `{getattr(data_obj, 'num_units', 0)}`")
            st.markdown(f"**Total Injuries:** `{getattr(data_obj, 'injuries_total', 0.0):.2f}`")
            st.markdown(f"**Fatal Injuries:** `{getattr(data_obj, 'injuries_fatal', 0.0):.2f}`")
            st.markdown(f"**Incapacitating:** `{getattr(data_obj, 'injuries_incapacitating', 0.0):.2f}`")
            st.markdown(f"**Non-Incapacitating:** `{getattr(data_obj, 'injuries_non_incapacitating', 0.0):.2f}`")
            st.markdown(f"**Reported Not Evident:** `{getattr(data_obj, 'injuries_reported_not_evident', 0.0):.2f}`")
            st.markdown(f"**No Indication:** `{getattr(data_obj, 'injuries_no_indication', 0.0):.2f}`")
            st.markdown(f"**Primary Cause:** `{getattr(data_obj, 'prim_contributory_cause', 'N/A')}`")
            st.markdown(f"**Intersection Related:** `{getattr(data_obj, 'intersection_related_i', 'NO')}`")

            st.subheader("Temporal Details")
            st.markdown(f"**Crash Hour:** `{getattr(data_obj, 'crash_hour', 0)}`")
            st.markdown(f"**Day of Week:** `{getattr(data_obj, 'crash_day_of_week', 1)}`")
            st.markdown(f"**Month:** `{getattr(data_obj, 'crash_month', 1)}`")
    except Exception as e:
        logger.error(f"Error displaying record data: {traceback.format_exc()}")
        st.error("Failed to display record details due to an internal error.")

def view_all_records(db: TrafficAccidentsDB):
    """
    Displays records with pagination and filtering options.
    Records are fetched in chunks to optimize performance.
    """
    st.header("All Records")
    
    # Get total records from the database header (most efficient way)
    total_records_in_db = db.get_last_id()

    if total_records_in_db == 0:
        st.info("No records found in the database. Try importing from CSV or adding a new record.")
        return

    # --- Filtering and Pagination Controls ---
    with st.expander("🔍 Filter & Sort Records", expanded=True):
        filter_cols = st.columns(3)
        with filter_cols[0]:
            search_query = st.text_input("Search Crash Type", key="search_crash_type_all", help="Enter text to filter by crash type.")
        with filter_cols[1]:
            min_injuries = st.number_input("Min Total Injuries", min_value=0.0, value=0.0, step=0.1, key="min_injuries_all", help="Only show records with at least this many total injuries.")
        with filter_cols[2]:
            only_valid = st.checkbox("Show Only Valid Records", value=False, key="only_valid_checkbox", help="Toggle to display only records marked as valid.")
        
        # We'll load records on demand, so 'all_records_raw' in session state is no longer needed globally
        # Instead, we will fetch based on current page and filters.

    # Pagination controls
    page_cols = st.columns([1, 1, 2])
    with page_cols[0]:
        page_size = st.selectbox(
            "Records per page",
            [10, 20, 50, 100, total_records_in_db], # Option to show all records if applicable
            index=1, # Default to 20 per page
            key="view_page_size"
        )
    
    # Calculate total pages based on the actual total records in DB, not just filtered ones
    total_pages = max(1, (total_records_in_db + page_size - 1) // page_size) 
    
    # Create a list of page numbers for the selectbox
    page_options = list(range(1, total_pages + 1))
    
    with page_cols[1]:
        # Determine the initial index for the selectbox to maintain current page if possible
        # Ensure the selected page is within the valid range
        current_page = st.selectbox(
            "Page", 
            options=page_options,
            index=min(st.session_state.get("view_page_num", 1), total_pages) - 1, # Default to page 1, adjust for 0-indexed selectbox
            key="view_page_num"
        )

    # Calculate offset for fetching records
    start_offset = (current_page - 1) * page_size
    
    # Fetch only the records for the current page
    current_page_raw_records = []
    with st.spinner(f"Loading records for page {current_page}..."):
        try:
            current_page_raw_records = db.read_records_paginated(offset=start_offset, limit=page_size)
            logger.info(f"Loaded {len(current_page_raw_records)} raw records for page {current_page}.")
        except DatabaseError as e:
            st.error(f"Failed to load records for current page: {str(e)}")
            logger.error(f"Error loading paginated records: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred while loading page records: {str(e)}")
            logger.error(f"Unexpected error in view_all_records pagination: {traceback.format_exc()}")


    # Filter records based on the fetched subset
    filtered_records_with_obj = [] # Will store {id, validation, checksum, data_obj_instance}
    for record_raw in current_page_raw_records:
        try:
            # Reconstruct DataObject from raw bytes for filtering and display
            data_obj = DataObject.from_bytes(record_raw['data_bytes'])
            
            # Apply 'only_valid' filter
            if only_valid and not record_raw.get('validation', True): 
                continue
            
            # Apply search query filter (case-insensitive)
            if search_query:
                if not getattr(data_obj, 'crash_type', '').lower().startswith(search_query.lower()):
                    continue
            
            # Apply min injuries filter
            if getattr(data_obj, 'injuries_total', 0.0) < min_injuries:
                continue
            
            # Add the reconstructed object and its original metadata
            filtered_records_with_obj.append({
                'id': record_raw['id'],
                'validation': record_raw['validation'],
                'size': record_raw['size'],
                'checksum': record_raw['checksum'],
                'data': data_obj # This is now the DataObject instance
            })
        except (DataValidationError, DatabaseError) as e:
            logger.warning(f"Skipping record ID {record_raw.get('id', 'N/A')} due to deserialization/validation error: {e}")
            continue # Skip corrupt or invalid records during display
        except Exception as e:
            logger.error(f"Unexpected error processing raw record for display (ID: {record_raw.get('id', 'N/A')}): {traceback.format_exc()}")
            continue

    st.info(f"Displaying {len(filtered_records_with_obj)} record(s) on page {current_page} after filtering.")
    
    if not filtered_records_with_obj:
        st.warning("No records match your current filters on this page.")
    
    for i, record_with_obj in enumerate(filtered_records_with_obj):
        # Use a unique key for each expander based on record ID
        expander_key = f"record_expander_{record_with_obj['id']}"
        with st.expander(
            f"📝 Record ID: {record_with_obj['id']} "
            f"({'✅ Valid' if record_with_obj['validation'] else '❌ Invalid'}) "
            f"- {getattr(record_with_obj['data'], 'crash_date', 'N/A')} - {getattr(record_with_obj['data'], 'crash_type', 'N/A')}",
            expanded=False # Start collapsed
        ):
            tab1, tab2, tab3 = st.tabs(["Data View", "Raw Data", "Checksum Info"])
            with tab1:
                display_record_data(record_with_obj['data']) # Pass the reconstructed DataObject
            with tab2:
                # Convert DataObject back to dict for JSON display
                record_data_dict = {field: getattr(record_with_obj['data'], field, None) for field in FIELDS}
                st.json(record_data_dict)
            with tab3:
                st.markdown(f"**Record Size (bytes):** `{record_with_obj['size']}`")
                st.markdown(f"**MD5 Checksum:** `{record_with_obj['checksum']}`")
                st.info("Checksum helps verify data integrity. Mismatches could indicate corruption.")
    
    st.caption(f"Showing records {start_offset + 1}-{start_offset + len(filtered_records_with_obj)} of {total_records_in_db} (Total: {total_records_in_db})")


def search_by_id(db: TrafficAccidentsDB):
    """
    Provides an interface to search for a specific record by its ID.
    Displays detailed information for the found record.
    """
    st.header("Search Record by ID")
    
    # Use session state to store search result and error message
    if 'search_result_id' not in st.session_state:
        st.session_state.search_result_id = None
    if 'search_error_id' not in st.session_state:
        st.session_state.search_error_id = None

    col1, col2 = st.columns([1, 3])
    
    with col1:
        last_id = db.get_last_id() # Get last ID to set max_value for input
        search_id_input = st.number_input(
            "Enter Record ID", 
            min_value=1, 
            max_value=last_id if last_id > 0 else 1000000, # Provide a large max if no records
            step=1,
            value=1, # Default value
            key="search_id_input",
            help=f"Enter a numeric ID to search (e.g., between 1 and {last_id if last_id > 0 else 'N/A'})."
        )
        
        search_button_clicked = st.button("🔎 Search", key="search_button")
        clear_search_button_clicked = st.button("🗑️ Clear Search", key="clear_search_button")
        
        if search_button_clicked:
            if search_id_input > last_id and last_id > 0:
                st.session_state.search_error_id = f"ID {search_id_input} is greater than the last recorded ID ({last_id})."
                st.session_state.search_result_id = None
            else:
                with st.spinner(f"Searching for record ID {search_id_input}..."):
                    try:
                        record_raw = db.read_record_by_id(search_id_input) # Get raw data
                        if record_raw:
                            # Reconstruct DataObject for display
                            record_with_obj = {
                                'id': record_raw['id'],
                                'validation': record_raw['validation'],
                                'size': record_raw['size'],
                                'checksum': record_raw['checksum'],
                                'data': DataObject.from_bytes(record_raw['data_bytes'])
                            }
                            st.session_state.search_result_id = record_with_obj
                            st.session_state.search_error_id = None
                        else:
                            st.session_state.search_result_id = None
                            st.session_state.search_error_id = f"Record ID {search_id_input} not found in the database."
                    except (DatabaseError, DataValidationError, ValueError) as e:
                        st.session_state.search_error_id = f"Search failed: {str(e)}"
                        st.session_state.search_result_id = None
                    except Exception as e:
                        st.session_state.search_error_id = f"An unexpected error occurred during search: {str(e)}"
                        logger.error(f"Unexpected error during search_by_id: {traceback.format_exc()}")
                        st.session_state.search_result_id = None
        
        if clear_search_button_clicked:
            st.session_state.search_result_id = None
            st.session_state.search_error_id = None
            st.rerun() # Rerun to clear the display area cleanly
            
    with col2:
        if st.session_state.search_result_id:
            record_with_obj = st.session_state.search_result_id
            st.success(f"✅ Found record ID: {record_with_obj['id']}")
            
            tab1, tab2, tab3 = st.tabs(["Data View", "Raw JSON", "Checksum Info"])
            with tab1:
                display_record_data(record_with_obj['data']) # Pass the reconstructed DataObject
            with tab2:
                # Convert DataObject back to dict for JSON display
                record_data_dict = {field: getattr(record_with_obj['data'], field, None) for field in FIELDS}
                st.json(record_data_dict)
            with tab3:
                st.markdown(f"**Record Size (bytes):** `{record_with_obj['size']}`")
                st.markdown(f"**MD5 Checksum:** `{record_with_obj['checksum']}`")
                st.info("Checksum helps verify data integrity. Mismatches could indicate corruption.")
        elif st.session_state.search_error_id:
            st.error(st.session_state.search_error_id)
        else:
            st.info("Enter an ID and click 'Search' to find a record.")

def import_from_csv(db: TrafficAccidentsDB):
    """
    Handles CSV file upload and imports records into the database.
    Provides real-time progress updates and detailed results.
    """
    st.header("Import Records from CSV")
    
    try:
        uploaded_file = st.file_uploader(
            "Choose a CSV file to import", 
            type="csv",
            key="csv_uploader",
            help=f"Select a CSV file (max {MAX_FILE_SIZE_MB}MB) with traffic accident data. Data should be delimited by '{CSV_DELIMITER}'."
        )
        
        if uploaded_file is not None:
            # Display uploaded file details
            st.info(f"File '{uploaded_file.name}' uploaded. Size: {uploaded_file.size / (1024*1024):.2f} MB")
            
            # Frontend check for file size (already done by DB class, but good for UX)
            if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"🚫 File size exceeds maximum allowed of {MAX_FILE_SIZE_MB}MB.")
                return
            
            # Use a temporary file to save the uploaded content
            # Streamlit runs in different environments, tempfile is safest
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            if st.button("🚀 Start Import", key="import_button", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                result_container = st.empty()
                
                def update_progress(current: int, total: int):
                    """Callback function to update the Streamlit progress bar and status text."""
                    if total > 0:
                        progress = min(int((current / total) * 100), 100)
                    else:
                        progress = 100 # Handle case of 0 total records gracefully
                    progress_bar.progress(progress)
                    status_text.markdown(
                        f"**Progress:** {current}/{total} records ({progress}%)"
                    )
                
                try:
                    with st.spinner("Importing records... This may take a while for large files."):
                        start_time = time.time()
                        imported_count = db.write_from_csv(tmp_path, update_progress)
                        duration = time.time() - start_time
                    
                    progress_bar.progress(100) # Ensure 100% completion
                    status_text.empty() # Clear status text
                    
                    result_container.success(
                        f"🎉 Import complete! Successfully imported {imported_count} records.  \n"
                        f"**Last Record ID:** {db.get_last_id()}  \n"
                        f"**Time elapsed:** {duration:.2f} seconds"
                    )
                    st.balloons()
                    # Rerun to refresh 'View All Records' or 'Search by ID' if user navigates there
                    st.rerun() 
                except (DatabaseError, FileLockError, ValueError, FileNotFoundError) as e:
                    progress_bar.empty()
                    status_text.empty()
                    result_container.error(f"❌ Import failed: {str(e)}")
                    logger.error(f"CSV import failed: {traceback.format_exc()}")
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    result_container.error(f"❌ An unexpected error occurred during import: {str(e)}")
                    logger.error(f"Unexpected error during CSV import: {traceback.format_exc()}")
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        logger.info(f"Cleaned up temporary CSV file: {tmp_path}")
        else:
            st.info("Upload a CSV file to begin the import process.")
    except Exception as e:
        logger.error(f"Error in import_from_csv UI setup: {traceback.format_exc()}")
        st.error(f"An error occurred while setting up the CSV import interface: {str(e)}")


def add_new_record(db: TrafficAccidentsDB):
    """
    Provides a form for users to manually add a new accident record.
    Includes input validation and clear feedback.
    """
    st.header("Add New Accident Record")
    
    with st.form("record_form", clear_on_submit=True):
        st.subheader("Required Accident Details (*)")
        cols_req = st.columns(2)
        
        with cols_req[0]:
            crash_date = st.date_input(
                "Crash Date*",
                value=date.today(),
                help="Date of the accident (YYYY-MM-DD)",
                key="add_crash_date"
            )
        with cols_req[1]:
            crash_type = st.text_input(
                "Crash Type*",
                help="Main type of collision (e.g., Rear-End, Head-On, Side-Swipe, Rollover)",
                key="add_crash_type"
            )
        
        cols_units_inj = st.columns(2)
        with cols_units_inj[0]:
            num_units = st.number_input(
                "Number of Units Involved*",
                min_value=0,
                max_value=999,
                value=1,
                step=1,
                help="Total number of vehicles/units involved in the crash.",
                key="add_num_units"
            )
        with cols_units_inj[1]:
            injuries_total = st.number_input(
                "Total Injuries*",
                min_value=0.0,
                value=0.0,
                step=0.1,
                help="Total count of all injuries (fatal, incapacitating, etc.).",
                key="add_injuries_total"
            )

        st.subheader("Optional Details")
        cols1 = st.columns(3)
        with cols1[0]:
            traffic_control_device = st.selectbox(
                "Traffic Control Device",
                ["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN", "YIELD SIGN", "NONE", "OTHER"],
                index=0, key="add_tcd"
            )
            weather_condition = st.selectbox(
                "Weather Condition",
                ["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG", "SEVERE CROSSWINDS", "SLEET", "OTHER"],
                index=0, key="add_weather"
            )
            lighting_condition = st.selectbox(
                "Lighting Condition",
                ["UNKNOWN", "DAYLIGHT", "DARK - LIGHTED", "DARK - NOT LIGHTED", "DUSK/DAWN"],
                index=0, key="add_lighting"
            )
        with cols1[1]:
            first_crash_type = st.text_input(
                "First Crash Type (Specific)",
                help="More specific first contact point, if known.",
                key="add_first_crash_type"
            )
            trafficway_type = st.text_input(
                "Trafficway Type",
                help="Type of roadway (e.g., INTERSTATE, LOCAL STREET, ALLEY)",
                key="add_trafficway_type"
            )
            alignment = st.text_input(
                "Alignment",
                help="Roadway alignment (e.g., STRAIGHT AND LEVEL, CURVE ON GRADE)",
                key="add_alignment"
            )
            roadway_surface_cond = st.selectbox(
                "Roadway Surface Condition",
                ["UNKNOWN", "DRY", "WET", "SNOW/ICE", "SAND/MUD/DIRT/OIL"],
                index=0, key="add_surface_cond"
            )
        with cols1[2]:
            road_defect = st.selectbox(
                "Road Defect",
                ["NONE", "RUT, HOLES", "SHOULDER DEFECT", "DEBRIS ON ROADWAY", "OTHER"],
                index=0, key="add_road_defect"
            )
            intersection_related_i = st.selectbox(
                "Intersection Related?",
                ["NO", "YES"],
                index=0, key="add_intersection_related"
            )
            damage = st.text_input(
                "Damage Description",
                help="Brief description of property in damage.",
                key="add_damage"
            )
            prim_contributory_cause = st.text_input(
                "Primary Contributory Cause",
                help="Main factor contributing to the crash (e.g., UNSAFE SPEED, FAILED TO YIELD)",
                key="add_prim_cause"
            )
            most_severe_injury = st.selectbox(
                "Most Severe Injury",
                ["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"],
                index=0, key="add_most_severe_injury"
            )

        st.subheader("Detailed Injuries & Temporal Data")
        inj_cols = st.columns(3)
        with inj_cols[0]:
            injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0, value=0.0, step=0.1, key="add_injuries_fatal")
            injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0, value=0.0, step=0.1, key="add_injuries_incapacitating")
        with inj_cols[1]:
            injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0, value=0.0, step=0.1, key="add_injuries_non_incapacitating")
            injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0, value=0.0, step=0.1, key="add_injuries_reported_not_evident")
        with inj_cols[2]:
            injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0, value=0.0, step=0.1, key="add_injuries_no_indication")
        
        temp_cols = st.columns(3)
        with temp_cols[0]:
            crash_hour = st.slider("Crash Hour (0-23)", 0, 23, 12, key="add_crash_hour")
        with temp_cols[1]:
            crash_day_of_week = st.slider("Day of Week (1=Monday, 7=Sunday)", 1, 7, 1, key="add_crash_day_of_week")
        with temp_cols[2]:
            crash_month = st.slider("Month (1-12)", 1, 12, datetime.now().month, key="add_crash_month")
        
        submitted = st.form_submit_button("💾 Save Record", use_container_width=True)
        
        if submitted:
            # Basic frontend validation for required fields
            if crash_date is None: 
                st.error("🚨 Crash Date is a required field and cannot be empty.")
            elif not crash_type:
                st.error("🚨 Crash Type is a required field.")
            elif num_units is None or num_units < 0:
                st.error("🚨 Number of Units must be a non-negative number.")
            elif injuries_total is None or injuries_total < 0:
                st.error("🚨 Total Injuries must be a non-negative number.")
            else:
                try:
                    # Convert date object to string for DataObject, ensuring it's not None
                    crash_date_str = crash_date.strftime('%Y-%m-%d') if crash_date else ""
                    logger.debug(f"Crash date string from form for DataObject: '{crash_date_str}'")

                    # Construct a list of strings mimicking a CSV row based on FIELDS order
                    row_data = [""] * len(FIELDS)
                    row_data[0] = crash_date_str
                    row_data[1] = traffic_control_device
                    row_data[2] = weather_condition
                    row_data[3] = lighting_condition
                    row_data[4] = first_crash_type
                    row_data[5] = trafficway_type
                    row_data[6] = alignment
                    row_data[7] = roadway_surface_cond
                    row_data[8] = road_defect
                    row_data[9] = crash_type
                    row_data[10] = intersection_related_i
                    row_data[11] = damage
                    row_data[12] = prim_contributory_cause
                    row_data[13] = str(num_units)
                    row_data[14] = most_severe_injury
                    row_data[15] = str(injuries_total)
                    row_data[16] = str(injuries_fatal)
                    row_data[17] = str(injuries_incapacitating)
                    row_data[18] = str(injuries_non_incapacitating)
                    row_data[19] = str(injuries_reported_not_evident)
                    row_data[20] = str(injuries_no_indication)
                    row_data[21] = str(crash_hour)
                    row_data[22] = str(crash_day_of_week)
                    row_data[23] = str(crash_month)
                    
                    # Create DataObject and write to DB
                    new_record_obj = DataObject(row_data) # DataObject constructor performs validation
                    new_id = db.write_record(new_record_obj)
                    
                    st.success(f"🎉 Record saved successfully with ID: **{new_id}**")
                    st.balloons()
                    # Rerun to clear the form and update database info in sidebar
                    st.rerun() 
                except (DatabaseError, DataValidationError, ValueError) as e:
                    st.error(f"❌ Error saving record: {str(e)}")
                    logger.error(f"Failed to save new record: {traceback.format_exc()}")
                except Exception as e:
                    st.error(f"❌ An unexpected error occurred while saving: {str(e)}")
                    logger.error(f"Unexpected error saving new record: {traceback.format_exc()}")

def display_update_registry():
    """
    Reads recent updates from the log file and displays them in a Streamlit expander.
    """
    st.subheader("Activity Log")
    log_file_path = 'traffic_accidents.log'
    
    if not os.path.exists(log_file_path):
        st.info("No activity log found yet.")
        return

    with st.expander("Recent Updates", expanded=False):
        try:
            # Read the last N lines of the log file for efficiency
            # A more robust solution for very large logs would involve a dedicated log parser
            # or a separate small registry file.
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Filter and display relevant log entries in reverse order
            update_entries = []
            for line in reversed(lines):
                if "Record saved successfully with ID:" in line or "Successfully imported" in line:
                    # Extract timestamp and message
                    try:
                        # Log format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                        # Example: '2023-10-27 10:30:00,123 - __main__ - INFO - Record saved successfully with ID: 1'
                        parts = line.split(' - ', 3) # Split into 4 parts
                        if len(parts) >= 4:
                            timestamp_str = parts[0]
                            message = parts[3].strip() # Get the actual log message
                            update_entries.append(f"**`{timestamp_str}`** `{message}`")
                            if len(update_entries) >= MAX_LOG_ENTRIES_DISPLAY:
                                break
                    except Exception as e:
                        logger.warning(f"Failed to parse log line for registry: {line.strip()} - {e}")
                        continue
            
            if update_entries:
                for entry in update_entries:
                    st.markdown(entry)
            else:
                st.info("No recent record updates or imports found in the log.")
        except Exception as e:
            st.error(f"Could not read activity log: {str(e)}")
            logger.error(f"Error reading activity log: {traceback.format_exc()}")

# --- Main Application Entry Point ---
if __name__ == "__main__":
    # Ensure the DB directory is created before any DB operations
    # This is done within TrafficAccidentsDB.__init__ but can be called standalone
    # to catch early errors if __init__ fails before setup_ui can handle it.
    try:
        os.makedirs(DATA_FOLDER, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
    except OSError as e:
        st.error(f"Critical: Cannot create database directories. Please check permissions for {DATA_FOLDER}. Error: {e}")
        logger.critical(f"Initial directory creation failed: {traceback.format_exc()}")
        st.stop() # Stop the app if directories cannot be created

    setup_ui() # Start the Streamlit UI
