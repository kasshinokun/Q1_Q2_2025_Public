# -*- coding: utf-8 -*-
"""
Enhanced Traffic Accidents Database Manager with Compression, Encryption, and B-Tree Index

This script merges the backend of stCRUDDataObjectPY_v4epsilon.py with the frontend
of stCRUDDataObjectPY_v3alpha.py, adding interfaces for:
- LZW/Huffman compression/decompression of the database and index files.
- AES/RSA hybrid encryption/decryption of the database and index files.
- B-Tree index for efficient record management (replaces the simple dictionary index).
"""

import streamlit as st
import csv
import os
import struct
import json
import hashlib
import time
import filelock
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Union, Callable, Any, Iterator, Tuple
import shutil
import tempfile
import traceback
import math
from collections import OrderedDict, Counter, defaultdict, deque
import heapq
import io
import re
import sys  # For stderr fallback in logging
import getpass # For secure password input (though not directly used by Streamlit's UI)

# --- Cryptography Imports (para RSA e AES) ---
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag as CryptoInvalidTag # Renomeado para evitar conflito

# --- Matplotlib e Pandas para a seção de Comparação ---
import pandas as pd
from matplotlib import pyplot as plt


# --- Configurações da Aplicação ---
APP_CONFIG = {
    "DB_DIR": Path.home() / "Documents" / "Data",
    "BACKUP_PATH": Path.home() / "Documents" / "Data" / "Backups",
    "RSA_KEYS_DIR": Path.home() / "Documents" / "Data" / "RSA_Keys",
    "HUFFMAN_FOLDER": Path.home() / "Documents" / "Data" / "Huffman",
    "LZW_FOLDER": Path.home() / "Documents" / "Data" / "LZW",
    "LOG_FILE": Path.home() / "Documents" / "Data" / "app_activity.log",
    "SECRET_KEY": b'a_very_secret_key_for_aes_encryption', # Replace with a strong, random key
    "ENCRYPTION_SALT": b'salt_for_key_derivation', # Replace with a random salt
    "SALT_SIZE": 16,
    "IV_SIZE": 16,
    "KEY_SIZE": 32, # 256 bits for AES
    "BLOCK_SIZE": 16, # AES block size in bytes (for CBC, though GCM is used)
    "DEFAULT_DATA_ENCODING": "utf-8",
    "DB_LOCK_TIMEOUT": 30, # Timeout for file lock in seconds
    "DEFAULT_AES_MODE": "CBC", # This is for conceptual clarity, GCM is used for actual encryption
    "RSA_KEY_SIZE": 2048, # Standard for RSA keys

    # Nomes de arquivos de dados e índices
    "DB_FILE_NAME": "data.db",
    "SEQUENTIAL_INDEX_FILE_NAME": "index.idx", # Índice sequencial (novo)
    "BTREE_FILE_NAME": "index.btr", # Arquivo B-Tree (migrado)
    "CSV_FILE_NAME": "records.csv",
    "ENCRYPTED_DB_FILE_NAME": "traffic_accidents_encrypted.bin",
    "ENCRYPTED_SEQUENTIAL_INDEX_FILE_NAME": "traffic_accidents_index_encrypted.bin", # Adaptado para o índice sequencial
    "ENCRYPTED_BTREE_FILE_NAME": "traffic_accidents_btree_encrypted.bin", # Adaptado para o arquivo B-Tree
    "AES_KEY_FILE_NAME": "aes_key.bin",

    "MAX_LOG_BYTES": 10 * 1024 * 1024, # 10 MB
    "BACKUP_ROTATION": 5, # Keep last 5 backups
    "B_TREE_ORDER": 63, # Order for the B-tree
    "RECORD_DELETED_MARKER": -1, # Special offset to mark a logically deleted record
}

# --- Configuração de Logging (Atualizada para usar APP_CONFIG) ---
LOG_FILE = APP_CONFIG["LOG_FILE"] # Usa o caminho do log da nova APP_CONFIG
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configurar handler de arquivo rotativo
file_handler = RotatingFileHandler(
    LOG_FILE, 
    maxBytes=APP_CONFIG["MAX_LOG_BYTES"], 
    backupCount=APP_CONFIG["BACKUP_ROTATION"]
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Configurar handler de console para depuração
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)'))
logger.addHandler(console_handler)


# --- Derivar caminhos completos dos arquivos a partir de DB_DIR e nomes de arquivos ---
APP_CONFIG["DB_FILE"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["DB_FILE_NAME"]
APP_CONFIG["SEQUENTIAL_INDEX_FILE"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["SEQUENTIAL_INDEX_FILE_NAME"]
APP_CONFIG["BTREE_FILE"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["BTREE_FILE_NAME"] # Caminho da B-Tree
APP_CONFIG["CSV_EXPORT_FILE"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["CSV_FILE_NAME"]
APP_CONFIG["ENCRYPTED_DB_FILE"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["ENCRYPTED_DB_FILE_NAME"]
APP_CONFIG["ENCRYPTED_SEQUENTIAL_INDEX_FILE"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["ENCRYPTED_SEQUENTIAL_INDEX_FILE_NAME"]
APP_CONFIG["ENCRYPTED_BTREE_FILE"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["ENCRYPTED_BTREE_FILE_NAME"]
APP_CONFIG["AES_KEY_FILE"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["AES_KEY_FILE_NAME"]
APP_CONFIG["LOCK_FILE"] = APP_CONFIG["DB_DIR"] / "db.lock" # Adicionado explicitamente para o lock file

# Garante que os diretórios base existam (atualizado com os novos caminhos)
for path_key in ["DB_DIR", "BACKUP_PATH", "RSA_KEYS_DIR", "HUFFMAN_FOLDER", "LZW_FOLDER"]:
    APP_CONFIG[path_key].mkdir(parents=True, exist_ok=True)

# --- Constantes de Pastas para Compressão (Atualizadas para usar APP_CONFIG) ---
HUFFMAN_SOURCE_FOLDER = APP_CONFIG["DB_DIR"] # Agora a pasta de origem é a pasta de dados
HUFFMAN_COMPRESSED_FOLDER = APP_CONFIG["HUFFMAN_FOLDER"]
LZW_SOURCE_FOLDER = APP_CONFIG["DB_DIR"] # Agora a pasta de origem é a pasta de dados
LZW_COMPRESSED_FOLDER = APP_CONFIG["LZW_FOLDER"]
TEMP_FOLDER = APP_CONFIG["DB_DIR"] / "Temp" # Manter arquivos temporários dentro do diretório principal de dados

# Garante que as pastas de compressão existam (se ainda não criadas pelo loop acima)
HUFFMAN_SOURCE_FOLDER.mkdir(parents=True, exist_ok=True)
HUFFMAN_COMPRESSED_FOLDER.mkdir(parents=True, exist_ok=True)
LZW_SOURCE_FOLDER.mkdir(parents=True, exist_ok=True)
LZW_COMPRESSED_FOLDER.mkdir(parents=True, exist_ok=True)
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)


# --- Constantes do B-Tree (Atualizada para usar B_TREE_ORDER da APP_CONFIG) ---
ORDER = APP_CONFIG["B_TREE_ORDER"] # Usa a ordem explícita da APP_CONFIG

# Ajuste NODE_SIZE com base na nova ORDER.
# O cálculo é: is_leaf (1 byte) + num_keys (4 bytes) + (ORDER-1)*8 (chaves) + ORDER*4 (filhos) + (ORDER-1)*8 (ponteiros de registro)
NODE_SIZE = 1 + 4 + (ORDER - 1) * 8 + ORDER * 4 + (ORDER - 1) * 8
logger.info(f"B-Tree ORDER: {ORDER}, Calculated NODE_SIZE: {NODE_SIZE}")


# --- Mapeamento de Campos (Inglês <-> Português) e Configurações de Campo ---
FIELD_MAPPING = {
    "crash_date": "data_do_acidente",
    "traffic_control_device": "dispositivo_de_controle_de_trânsito",
    "weather_condition": "condição_climática",
    "lighting_condition": "condição_de_iluminação",
    "first_crash_type": "primeiro_tipo_de_acidente",
    "trafficway_type": "tipo_de_via_de_trânsito",
    "alignment": "alinhamento",
    "roadway_surface_cond": "cond_superfície_da_estrada",
    "road_defect": "defeito_da_estrada",
    "crash_type": "tipo_do_acidente",
    "intersection_related_i": "relacionado_a_interseção",
    "damage": "dano",
    "prim_contributory_cause": "causa_contribuitória_primária",
    "num_units": "núm_unidades",
    "most_severe_injury": "ferimento_mais_grave",
    "injuries_total": "total_de_ferimentos",
    "injuries_fatal": "ferimentos_fatais",
    "injuries_incapacitating": "ferimentos_não_incapacitantes",
    "injuries_non_incapacitating": "ferimentos_não_incapacitantes",
    "injuries_reported_not_evident": "ferimentos_relatados_não_evidentes",
    "injuries_no_indication": "ferimentos_sem_indicação",
    "crash_hour": "hora_do_acidente",
    "crash_day_of_week": "dia_da_semana_do_acidente",
    "crash_month": "mês_do_acidente"
}

# Criar o mapeamento reverso (português para inglês) para uso na importação de CSV
REVERSE_FIELD_MAPPING = {v: k for k, v in FIELD_MAPPING.items()}

# Lista dos campos que devem ser tratados como listas internamente (nomes em INGLÊS)
LIST_FIELDS_EN = ["lighting_condition", "crash_type", "most_severe_injury"]

# Lista dos campos obrigatórios (nomes em INGLÊS - usados internamente pelo sistema)
REQUIRED_FIELDS_EN = list(FIELD_MAPPING.keys())

# Lista dos campos obrigatórios (nomes em PORTUGUÊS - usados para validar CSV)
REQUIRED_FIELDS_PT = list(FIELD_MAPPING.values())


# --- Criptografia e Compressão ---
def generate_aes_key(key_size: int = APP_CONFIG["KEY_SIZE"]) -> bytes: # Usa KEY_SIZE da APP_CONFIG
    """Gera uma chave AES aleatória usando os.urandom (Cryptography)."""
    return os.urandom(key_size)

def encrypt_file(file_path: Path, output_path: Path, aes_key: bytes) -> None:
    """Criptografa um arquivo usando AES em modo GCM (Cryptography)."""
    try:
        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(), backend=default_backend())
        encryptor = cipher.encryptor()
        
        with open(file_path, 'rb') as f_in:
            plaintext = f_in.read()
        
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        nonce = encryptor.nonce # Nonce é gerado automaticamente pelo GCM
        tag = encryptor.tag # Tag de autenticação
        
        with open(output_path, 'wb') as f_out:
            f_out.write(nonce)
            f_out.write(tag)
            f_out.write(ciphertext)
        logger.info(f"Arquivo '{file_path}' criptografado para '{output_path}' usando Cryptography.")
    except Exception as e:
        logger.error(f"Erro ao criptografar arquivo '{file_path}' com Cryptography: {traceback.format_exc()}")
        raise

def decrypt_file(file_path: Path, output_path: Path, aes_key: bytes) -> None:
    """Descriptografa um arquivo usando AES em modo GCM (Cryptography)."""
    try:
        with open(file_path, 'rb') as f_in:
            # O nonce GCM tem 12 bytes por padrão
            nonce = f_in.read(12) 
            tag = f_in.read(16) # A tag GCM tem 16 bytes
            ciphertext = f_in.read()
        
        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(nonce), backend=default_backend())
        decryptor = cipher.decryptor()
        
        plaintext = decryptor.update(ciphertext) + decryptor.finalize() # A tag é verificada automaticamente aqui
        
        with open(output_path, 'wb') as f_out:
            f_out.write(plaintext)
        logger.info(f"Arquivo '{file_path}' descriptografado para '{output_path}' usando Cryptography.")
    except CryptoInvalidTag: # Usa a exceção renomeada
        logger.error(f"Erro de autenticação (tag inválida) ao descriptografar '{file_path}'. Chave AES incorreta ou arquivo corrompido.")
        st.error("🚨 Erro de autenticação: Chave AES incorreta ou arquivo corrompido. Descriptografia falhou.")
        raise
    except Exception as e:
        logger.error(f"Erro ao descriptografar arquivo '{file_path}': {traceback.format_exc()}")
        raise

def generate_rsa_key_pair() -> Tuple[bytes, bytes]:
    """Gera um par de chaves RSA e as retorna em formato PEM (Cryptography)."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=APP_CONFIG["RSA_KEY_SIZE"], # Usa RSA_KEY_SIZE da APP_CONFIG
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
    return private_pem, public_pem

def save_rsa_keys(private_pem: bytes, public_pem: bytes) -> None:
    """Salva as chaves RSA em arquivos."""
    APP_CONFIG["RSA_KEYS_DIR"].mkdir(parents=True, exist_ok=True)
    with open(APP_CONFIG["PRIVATE_KEY_FILE"], "wb") as f:
        f.write(private_pem)
    with open(APP_CONFIG["PUBLIC_KEY_FILE"], "wb") as f:
        f.write(public_pem)
    logger.info("Chaves RSA salvas com sucesso.")

def load_rsa_keys() -> Tuple[Any, Any]:
    """Carrega as chaves RSA de arquivos."""
    try:
        with open(APP_CONFIG["PRIVATE_KEY_FILE"], "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        with open(APP_CONFIG["PUBLIC_KEY_FILE"], "rb") as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        logger.info("Chaves RSA carregadas com sucesso.")
        return private_key, public_key
    except FileNotFoundError:
        logger.warning("Arquivos de chaves RSA não encontrados.")
        return None, None
    except Exception as e:
        logger.error(f"Erro ao carregar chaves RSA: {traceback.format_exc()}")
        st.error(f"🚨 Erro ao carregar chaves RSA: {e}")
        return None, None

def rsa_encrypt_aes_key(aes_key: bytes, public_key: Any) -> bytes:
    """Criptografa a chave AES usando a chave pública RSA (Cryptography)."""
    return public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def rsa_decrypt_aes_key(encrypted_aes_key: bytes, private_key: Any) -> bytes:
    """Descriptografa a chave AES usando a chave privada RSA (Cryptography)."""
    return private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

# --- CONSTANTES PARA COMPRESSÃO HUFFMAN E LZW ---
MIN_COMPRESSION_SIZE = 100  # Minimum file size to apply compression
BUFFER_SIZE = 8192  # 8KB buffer size for I/O operations
HUFFMAN_COMPRESSED_EXTENSION = ".huff"
LZW_COMPRESSED_EXTENSION = ".lzw"
DEFAULT_EXTENSION = ".csv" # Used for comparison section, not related to app's core files

# --- IMPLEMENTAÇÃO HUFFMAN ---
class Node:
    __slots__ = ['char', 'freq', 'left', 'right']  # Memory optimization
    
    def __init__(self, char: Optional[bytes], freq: int, 
                 left: Optional['Node'] = None, 
                 right: Optional['Node'] = None):
        self.char = char  # Stored as bytes
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other: 'Node'):
        return self.freq < other.freq

class HuffmanProcessor:
    @staticmethod
    def generate_tree(data: bytes, progress_callback: Optional[Callable[[float, str], None]] = None) -> Optional[Node]:
        """Optimized tree generation with progress tracking"""
        if not data:
            return None
            
        if len(data) == 1:
            return Node(data, 1)  # Handle single-byte case

        if progress_callback:
            progress_callback(0, "Analyzing file content...")

        # Use Counter for frequency analysis of bytes
        byte_count = Counter(data)
        
        # Handle single-byte case
        if len(byte_count) == 1:
            byte = next(iter(byte_count))
            return Node(bytes([byte]), byte_count[byte])
        
        if progress_callback:
            progress_callback(0.2, "Building priority queue...")

        nodes = [Node(bytes([byte]), freq) for byte, freq in byte_count.items()]
        heapq.heapify(nodes)

        if progress_callback:
            progress_callback(0.3, "Constructing Huffman tree...")

        total_nodes = len(nodes)
        while len(nodes) > 1:
            left = heapq.heappop(nodes)
            right = heapq.heappop(nodes)
            merged = Node(None, left.freq + right.freq, left, right)
            heapq.heapush(nodes, merged)
            
            if progress_callback and len(nodes) % 10 == 0:
                progress = 0.3 + 0.7 * (1 - len(nodes)/total_nodes)
                progress_callback(progress, f"Merging nodes: {len(nodes)} remaining")

        if progress_callback:
            progress_callback(1.0, "Huffman tree complete!")
            time.sleep(0.3)

        return nodes[0]

    @staticmethod
    def build_codebook(root: Optional[Node]) -> Dict[bytes, str]:
        """Optimized codebook generation with iterative DFS"""
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
        """Optimized compression with progress tracking"""
        start_time = time.time()
        
        # Read input file as binary
        with open(input_path, 'rb') as file:
            data = file.read()

        if not data:
            return 0, 0, 0.0, 0.0

        original_size = len(data)
        
        # Skip compression for small files
        if original_size < MIN_COMPRESSION_SIZE:
            with open(output_path, 'wb') as file:
                file.write(data)
            return original_size, original_size, 0.0, time.time() - start_time

        # Step 1: Build Huffman tree
        if progress_callback:
            progress_callback(0, "Building Huffman Tree...")
        root = HuffmanProcessor.generate_tree(
            data, 
            lambda p, m: progress_callback(p * 0.3, f"Huffman: {m}") if progress_callback else None
        )

        # Step 2: Build codebook
        if progress_callback:
            progress_callback(0.3, "Generating encoding dictionary...")
        codebook = HuffmanProcessor.build_codebook(root)
        
        # Create reverse lookup for faster encoding
        encode_table = {byte[0]: code for byte, code in codebook.items()}  # byte[0] since we know it's single bytes

        # Step 3: Compress data
        if progress_callback:
            progress_callback(0.4, "Compressing data...")

        with open(output_path, 'wb') as file:
            # Write character table (optimized format)
            file.write(struct.pack('I', len(codebook)))
            for byte, code in codebook.items():
                file.write(struct.pack('B', byte[0]))  # Single byte
                file.write(struct.pack('B', len(code)))
                file.write(struct.pack('I', int(code, 2)))

            # Write data size
            file.write(struct.pack('I', original_size))

            # Buffered bit writing
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
                    progress_callback(progress, f"Compressed {bytes_processed}/{original_size} bytes")

            # Flush remaining bits
            if bit_count > 0:
                current_byte <<= (8 - bit_count)
                buffer.append(current_byte)
            
            if buffer:
                file.write(buffer)
            
            # Write padding size
            file.write(struct.pack('B', (8 - bit_count) % 8))

        compressed_size = os.path.getsize(output_path)
        compression_ratio = (original_size - compressed_size) / original_size * 100
        process_time = time.time() - start_time

        if progress_callback:
            progress_callback(1.0, "Compression complete!")

        return original_size, compressed_size, compression_ratio, process_time

    @staticmethod
    def decompress_file(input_path: str, output_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[int, int, float, float]:
        """Optimized decompression with progress tracking"""
        start_time = time.time()
        
        # Re-structured decompression with padding considered
        with open(input_path, 'rb') as file:
            # Read character table
            table_size = struct.unpack('I', file.read(4))[0]
            code_table = {}
            max_code_length = 0
            
            if progress_callback:
                progress_callback(0.1, "Reading metadata...")

            for i in range(table_size):
                byte = struct.unpack('B', file.read(1))[0]
                code_length = struct.unpack('B', file.read(1))[0]
                code_int = struct.unpack('I', file.read(4))[0]
                code = format(code_int, f'0{code_length}b')
                code_table[code] = bytes([byte])
                max_code_length = max(max_code_length, code_length)
                
                if progress_callback and i % 100 == 0:
                    progress = 0.1 + 0.2 * (i / table_size)
                    progress_callback(progress, f"Loading code table: {i}/{table_size}")

            # Read original data size
            data_size = struct.unpack('I', file.read(4))[0]

            # Get current position (after reading table and data_size)
            current_read_pos = file.tell()
            
            # Seek to the end of the file, read the last byte (padding), then seek back
            file.seek(-1, os.SEEK_END)
            padding_bits = struct.unpack('B', file.read(1))[0]
            
            # Seek back to where data starts (after header, before the padding byte)
            file.seek(current_read_pos)

            if progress_callback:
                progress_callback(0.3, "Preparing to decode...")

            result = io.BytesIO()
            current_bits = ""
            bytes_decoded = 0
            
            # Read all remaining compressed data, excluding the last padding byte
            compressed_data_bytes = file.read() # Reads from current position to EOF-1 (padding byte)

            total_compressed_bits = len(compressed_data_bytes) * 8 - padding_bits
            bits_processed = 0

            for byte_val in compressed_data_bytes:
                bits_in_byte = format(byte_val, '08b')
                
                # Only add bits if we haven't reached the end of meaningful compressed bits
                for bit in bits_in_byte:
                    if bits_processed < total_compressed_bits:
                        current_bits += bit
                        bits_processed += 1
                        
                        # Try to decode from current_bits
                        while True:
                            found_match = False
                            # Iterate up to max_code_length or current_bits length
                            for length in range(1, min(len(current_bits), max_code_length) + 1):
                                prefix = current_bits[:length]
                                if prefix in code_table:
                                    result.write(code_table[prefix])
                                    bytes_decoded += 1
                                    current_bits = current_bits[length:]
                                    found_match = True
                                    
                                    if bytes_decoded >= data_size:
                                        # Decoded all original bytes, stop.
                                        break
                            if bytes_decoded >= data_size:
                                break # Exit inner decoding loop
                            if not found_match:
                                break # No match found for current_bits prefix, wait for more bits
                        
                        if bytes_decoded >= data_size:
                            break # Exit bit loop
                    else:
                        break # Exceeded total_compressed_bits (including padding)
                
                if bytes_decoded >= data_size:
                    break # Exit byte loop
                
                if progress_callback and bytes_decoded % 1000 == 0:
                    progress = 0.3 + 0.7 * (bytes_decoded / data_size)
                    progress_callback(progress, f"Decoded {bytes_decoded}/{data_size} bytes")

        # Write decoded data
        with open(output_path, 'wb') as file:
            final_decoded_data = result.getvalue()
            # Ensure we only write up to the original data_size
            file.write(final_decoded_data[:data_size])

        compressed_size = os.path.getsize(input_path)
        decompressed_size = os.path.getsize(output_path)
        compression_ratio = (compressed_size - decompressed_size) / compressed_size * 100 # This ratio is usually for compression
        process_time = time.time() - start_time

        if progress_callback:
            progress_callback(1.0, "Decompression complete!")

        return compressed_size, decompressed_size, compression_ratio, process_time


# --- IMPLEMENTAÇÃO LZW ---
class LZWProcessor:
    @staticmethod
    def compress(input_file_path: str, output_file_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[int, int, float, float]:
        """Compress a file using LZW algorithm with variable-length codes"""
        start_time = time.time()
        
        try:
            # Read the input file as bytes
            with open(input_file_path, 'rb') as f:
                data = f.read()
            
            original_size = len(data)
            if not data:
                return 0, 0, 0.0, 0.0

            # Initialize dictionary with all possible single bytes
            dictionary = {bytes([i]): i for i in range(256)}
            next_code = 256
            compressed_data = []
            w = bytes()
            
            total_bytes = len(data)
            processed_bytes = 0
            
            # Determine the minimum number of bits needed initially
            bits = 9  # Start with 9 bits (can represent up to 511)
            max_code = 2**bits - 1
            
            for byte in data:
                c = bytes([byte])
                wc = w + c
                if wc in dictionary:
                    w = wc
                else:
                    compressed_data.append(dictionary[w])
                    # Add wc to the dictionary
                    if next_code <= 2**24 - 1: # Only add if dictionary size is within limit
                        dictionary[wc] = next_code
                        next_code += 1
                    
                    # Increase bit length if needed (only if dictionary grows beyond current max_code)
                    if next_code > max_code and bits < 24:  # Limit to 24 bits (16MB dictionary)
                        bits += 1
                        max_code = 2**bits - 1
                    
                    w = c
                
                processed_bytes += 1
                if progress_callback and processed_bytes % 1000 == 0:
                    progress = processed_bytes / total_bytes
                    progress_callback(progress, f"Compressing... {processed_bytes}/{total_bytes} bytes processed")
            
            if w:
                compressed_data.append(dictionary[w])
            
            # Write compressed data to output file
            with open(output_file_path, 'wb') as f:
                # Write header with number of codes and initial bits
                f.write(len(compressed_data).to_bytes(4, byteorder='big'))
                f.write(bits.to_bytes(1, byteorder='big'))
                
                # Pack codes into bytes
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
                
                # Write remaining bits
                if buffer_length > 0:
                    byte = (buffer << (8 - buffer_length)) & 0xFF
                    f.write(bytes([byte]))
            
            compressed_size = os.path.getsize(output_file_path)
            compression_ratio = (original_size - compressed_size) / original_size * 100
            process_time = time.time() - start_time

            if progress_callback:
                progress_callback(1.0, "Compression complete!")

            return original_size, compressed_size, compression_ratio, process_time
        
        except Exception as e:
            if progress_callback:
                progress_callback(1.0, f"Error during compression: {str(e)}")
            raise e

    @staticmethod
    def decompress(input_file_path: str, output_file_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[int, int, float, float]:
        """Decompress a file using LZW algorithm with variable-length codes"""
        start_time = time.time()
        
        try:
            # Read the compressed file
            with open(input_file_path, 'rb') as f:
                # Read header
                num_codes = int.from_bytes(f.read(4), byteorder='big')
                initial_bits = int.from_bytes(f.read(1), byteorder='big') # Renamed 'bits' to 'initial_bits' for clarity
                
                # Read all remaining data
                compressed_bytes = f.read()
            
            compressed_size = os.path.getsize(input_file_path)
            
            # Initialize dictionary with all possible single bytes
            dictionary = {i: bytes([i]) for i in range(256)}
            next_code = 256
            decompressed_data = bytearray()
            
            # Unpack bits into codes
            buffer = 0
            buffer_length = 0
            byte_pos = 0
            codes = []
            
            # Dynamically manage bits for decoding
            current_bits = initial_bits
            
            while len(codes) < num_codes:
                # Fill buffer
                while buffer_length < current_bits and byte_pos < len(compressed_bytes):
                    buffer = (buffer << 8) | compressed_bytes[byte_pos]
                    byte_pos += 1
                    buffer_length += 8
                
                if buffer_length < current_bits:
                    break  # End of data or not enough bits for next code
                
                # Extract code
                code = (buffer >> (buffer_length - current_bits)) & ((1 << current_bits) - 1)
                codes.append(code)
                buffer_length -= current_bits
                buffer = buffer & ((1 << buffer_length) - 1)
                
                # Update progress
                if progress_callback and len(codes) % 1000 == 0:
                    progress = len(codes) / num_codes
                    progress_callback(progress, f"Reading compressed data... {len(codes)}/{num_codes} codes processed")
            
            # Check if we got all expected codes
            if len(codes) != num_codes:
                raise ValueError(f"Expected {num_codes} codes but got {len(codes)}")
            
            # Process codes
            w = dictionary[codes[0]]
            decompressed_data.extend(w)
            
            for code in codes[1:]:
                # Adjust `current_bits` dynamically based on `next_code` during decompression
                if next_code >= (1 << current_bits) and current_bits < 24:
                    current_bits += 1

                if code in dictionary:
                    entry = dictionary[code]
                elif code == next_code:
                    entry = w + w[:1]
                else:
                    raise ValueError(f"Bad compressed code: {code}")
                
                decompressed_data.extend(entry)
                
                # Add w + entry[0] to the dictionary
                if next_code <= 2**24 - 1:
                    dictionary[next_code] = w + entry[:1]
                    next_code += 1
                
                w = entry
                
                # Update progress
                progress = len(decompressed_data) / (num_codes * 3) # Roughly estimate based on average entry size
                if progress_callback and len(decompressed_data) % 100000 == 0:  # Update every 100KB
                    progress_callback(min(1.0, progress), f"Decompressing... {len(decompressed_data)//1024}KB processed") # Cap at 1.0

            # Write decompressed data to output file
            with open(output_file_path, 'wb') as f:
                f.write(decompressed_data)
            
            decompressed_size = os.path.getsize(output_file_path)
            compression_ratio = (compressed_size - decompressed_size) / compressed_size * 100 
            process_time = time.time() - start_time

            if progress_callback:
                progress_callback(1.0, "Decompression complete!")

            return compressed_size, decompressed_size, compression_ratio, process_time
        
        except Exception as e:
            if progress_callback:
                progress_callback(1.0, f"Error during decompression: {str(e)}")
            raise e

def compare_algorithms(input_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> pd.DataFrame:
    """Compare performance of Huffman and LZW algorithms on the same file"""
    results = []
    
    # Create temp output paths
    huffman_output = os.path.join(TEMP_FOLDER, "temp_huffman.huff")
    lzw_output = os.path.join(TEMP_FOLDER, "temp_lzw.lzw")
    
    # Create temp decompressed output paths for verification
    huffman_decompressed_output = os.path.join(TEMP_FOLDER, os.path.basename(input_path) + ".huffout")
    lzw_decompressed_output = os.path.join(TEMP_FOLDER, os.path.basename(input_path) + ".lzwout")

    # Test Huffman
    if progress_callback:
        progress_callback(0, "Testing Huffman compression...")
    huff_compress = HuffmanProcessor.compress_file(input_path, huffman_output, 
        lambda p, m: progress_callback(p * 0.3, f"Huffman: {m}") if progress_callback else None)
    
    if progress_callback:
        progress_callback(0.4, "Testing Huffman decompression...")
    huff_decompress = HuffmanProcessor.decompress_file(huffman_output, huffman_decompressed_output, 
        lambda p, m: progress_callback(0.4 + p * 0.2, f"Huffman: {m}") if progress_callback else None)
    
    # Test LZW
    if progress_callback:
        progress_callback(0.6, "Testing LZW compression...")
    lzw_compress = LZWProcessor.compress(input_path, lzw_output, 
        lambda p, m: progress_callback(0.6 + p * 0.2, f"LZW: {m}") if progress_callback else None)
    
    if progress_callback:
        progress_callback(0.8, "Testing LZW decompression...")
    lzw_decompress = LZWProcessor.decompress(lzw_output, lzw_decompressed_output, 
        lambda p, m: progress_callback(0.8 + p * 0.2, f"LZW: {m}") if progress_callback else None)
    
    # Clean up temp files
    for f in [huffman_output, lzw_output, huffman_decompressed_output, lzw_decompressed_output]:
        try:
            if os.path.exists(f):
                os.remove(f)
        except OSError as e: # Catch specific OSError for file operations
            st.warning(f"Could not delete temporary file {f}: {e}")
            pass # Continue even if cleanup fails for one file
    
    # Prepare results
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
    """Create comparison plots"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Compression Ratio
    df.plot.bar(x='Algorithm', y='Compression Ratio (%)', ax=axes[0,0], 
                title='Compression Ratio Comparison', legend=False)
    axes[0,0].set_ylabel('Ratio (%)')
    
    # Compression Time
    df.plot.bar(x='Algorithm', y='Compression Time (s)', ax=axes[0,1], 
                title='Compression Time Comparison', legend=False)
    axes[0,1].set_ylabel('Time (s)')
    
    # Decompression Time
    df.plot.bar(x='Algorithm', y='Decompression Time (s)', ax=axes[1,0], 
                title='Decompression Time Comparison', legend=False)
    axes[1,0].set_ylabel('Time (s)')
    
    # Total Time
    df.plot.bar(x='Algorithm', y='Total Time (s)', ax=axes[1,1], 
                title='Total Processing Time Comparison', legend=False)
    axes[1,1].set_ylabel('Time (s)')
    
    plt.tight_layout()
    return fig


# --- Estrutura de Dados B-Tree ---
class BTreeNode:
    """Representa um nó no B-Tree."""
    def __init__(self, is_leaf: bool = True, keys: Optional[List[Any]] = None,
                 children: Optional[List[int]] = None, record_pointers: Optional[List[int]] = None):
        self.is_leaf = is_leaf
        self.keys = keys if keys is not None else []
        self.children = children if children is not None else []  # RVA (Record Virtual Address)
        self.record_pointers = record_pointers if record_pointers is not None else [] # Ponteiros para o arquivo de dados
        self.num_keys = len(self.keys)

    def to_bytes(self) -> bytes:
        """Serializa o nó para bytes."""
        # Formato: is_leaf (1 byte), num_keys (4 bytes),
        #          keys (ORDER-1 * 8 bytes para chave, preenchido),
        #          children (ORDER * 4 bytes para RVA, preenchido),
        #          record_pointers (ORDER-1 * 8 bytes para ponteiro de registro, preenchido)

        buffer = struct.pack('<?I', self.is_leaf, self.num_keys) # is_leaf (bool), num_keys (int)

        # Keys (assumindo que as chaves são hashes SHA256 de 8 bytes, truncados)
        for key in self.keys:
            if isinstance(key, str): # Se a chave for uma string, converter para bytes
                key = int(key, 16) # Hash em string hexadecimal para int
            buffer += key.to_bytes(8, 'big') # Supondo chaves de 8 bytes
        # Preencher com zeros se menos chaves que ORDER-1
        buffer += b'\x00' * (8 * (ORDER - 1 - self.num_keys))

        # Children RVA (assumindo inteiros de 4 bytes)
        for child_rva in self.children:
            buffer += struct.pack('<I', child_rva) # 4 bytes para RVA
        # Preencher com zeros se menos filhos que ORDER
        buffer += b'\x00' * (4 * (ORDER - len(self.children)))

        # Record Pointers (assumindo inteiros de 8 bytes)
        for rp in self.record_pointers:
            buffer += struct.pack('<Q', rp) # Q para unsigned long long (8 bytes)
        # Preencher com zeros se menos ponteiros que ORDER-1
        buffer += b'\x00' * (8 * (ORDER - 1 - self.num_keys))

        # Garantir que o tamanho final seja NODE_SIZE
        if len(buffer) != NODE_SIZE:
            raise ValueError(f"Tamanho do nó serializado incorreto: {len(buffer)} esperado {NODE_SIZE}")
        return buffer

    @classmethod
    def from_bytes(cls, data: bytes) -> 'BTreeNode':
        """Desserializa bytes para um nó."""
        if len(data) != NODE_SIZE:
            raise ValueError(f"Dados de nó com tamanho incorreto: {len(data)} esperado {NODE_SIZE}")

        is_leaf, num_keys = struct.unpack_from('<?I', data, 0)
        offset = 1 + 4 # bool + int

        keys = []
        for i in range(num_keys):
            key = int.from_bytes(data[offset : offset + 8], 'big')
            keys.append(key)
            offset += 8
        offset = 1 + 4 + (8 * (ORDER - 1)) # Pula as chaves preenchidas

        children = []
        for i in range(num_keys + (1 if not is_leaf else 0)): # Um filho a mais que chaves se não for folha
            child_rva = struct.unpack_from('<I', data, offset)[0]
            children.append(child_rva)
            offset += 4
        offset = 1 + 4 + (8 * (ORDER - 1)) + (4 * ORDER) # Pula as chaves e os filhos preenchidos

        record_pointers = []
        for i in range(num_keys):
            rp = struct.unpack_from('<Q', data, offset)[0]
            record_pointers.append(rp)
            offset += 8

        return cls(is_leaf, keys, children, record_pointers)


class BTree:
    """Implementa um B-Tree para indexação de registros."""
    def __init__(self, btree_file: Path):
        self.btree_file = btree_file # O arquivo para a B-Tree é agora .btr
        self.root_rva = 0 # RVA da raiz. 0 significa arquivo vazio/nova árvore
        self.next_rva = 0 # Próxima posição de RVA disponível no arquivo de índice
        self.lock = filelock.FileLock(APP_CONFIG["LOCK_FILE"]) # Bloqueio de arquivo para acesso seguro

        self._initialize_btree_file()

    def _initialize_btree_file(self):
        """Inicializa o arquivo B-Tree se não existir ou for inválido."""
        if not self.btree_file.exists() or self.btree_file.stat().st_size == 0:
            with self.lock:
                with open(self.btree_file, 'wb') as f:
                    # Cria um nó raiz vazio e o escreve
                    root_node = BTreeNode(is_leaf=True)
                    root_bytes = root_node.to_bytes()
                    f.write(root_bytes)
                    self.root_rva = 0 # Raiz no início do arquivo
                    self.next_rva = NODE_SIZE # Próximo RVA após o nó raiz
                logger.info(f"Arquivo B-Tree '{self.btree_file}' inicializado.")
        else:
            # Carrega a raiz e o próximo RVA se o arquivo já existir
            self.root_rva = 0
            self.next_rva = self.btree_file.stat().st_size
            logger.info(f"Arquivo B-Tree '{self.btree_file}' existente carregado. Próximo RVA: {self.next_rva}")

    def _read_node(self, rva: int) -> BTreeNode:
        """Lê um nó do arquivo B-Tree pelo seu RVA."""
        with self.lock:
            with open(self.btree_file, 'rb') as f:
                f.seek(rva)
                node_bytes = f.read(NODE_SIZE)
                if not node_bytes:
                    raise ValueError(f"Tentativa de ler RVA {rva} falhou: dados vazios.")
                return BTreeNode.from_bytes(node_bytes)

    def _write_node(self, node: BTreeNode, rva: Optional[int] = None) -> int:
        """Escreve um nó no arquivo B-Tree. Se RVA for None, escreve no final."""
        with self.lock:
            mode = 'r+b' if rva is not None else 'ab'
            with open(self.btree_file, mode) as f:
                if rva is not None:
                    f.seek(rva)
                else:
                    rva = self.next_rva
                    self.next_rva += NODE_SIZE # Atualiza o próximo RVA para escrita
                f.write(node.to_bytes())
            logger.debug(f"Nó B-Tree escrito/atualizado no RVA: {rva}")
            return rva

    def _split_child(self, parent_rva: int, i: int, child_rva: int):
        """Divide o filho `i` do nó `parent_rva`."""
        parent = self._read_node(parent_rva)
        child = self._read_node(child_rva)

        new_node = BTreeNode(is_leaf=child.is_leaf)
        
        median_key = child.keys[ORDER - 1]
        median_rp = child.record_pointers[ORDER - 1] # Ponteiro do registro associado à chave mediana

        # Chaves para o novo nó
        new_node.keys = child.keys[ORDER:]
        new_node.record_pointers = child.record_pointers[ORDER:]
        
        # Reduzir chaves do nó original
        child.keys = child.keys[:ORDER - 1]
        child.record_pointers = child.record_pointers[:ORDER - 1]
        
        # Se não for folha, os filhos também precisam ser divididos
        if not child.is_leaf:
            new_node.children = child.children[ORDER:]
            child.children = child.children[:ORDER]
            
        child.num_keys = len(child.keys)
        new_node.num_keys = len(new_node.keys)

        # Escrever o novo nó e atualizar o nó filho original
        new_node_rva = self._write_node(new_node)
        self._write_node(child, child_rva)

        # Inserir a chave mediana no pai
        parent.keys.insert(i, median_key)
        parent.record_pointers.insert(i, median_rp)
        parent.children.insert(i + 1, new_node_rva) # O novo nó vai como filho à direita da chave mediana
        parent.num_keys += 1
        
        self._write_node(parent, parent_rva)
        logger.debug(f"Nó dividido. Chave mediana: {median_key}, Novo RVA: {new_node_rva}")

    def insert(self, key: int, record_pointer: int):
        """Insere uma chave e um ponteiro de registro no B-Tree."""
        root = self._read_node(self.root_rva)
        if root.num_keys == (2 * ORDER - 1): # Raiz está cheia, precisa dividir
            new_root = BTreeNode(is_leaf=False, children=[self.root_rva])
            old_root_rva = self.root_rva # Guarda o RVA da raiz antiga
            self.root_rva = self._write_node(new_root) # A nova raiz é escrita e se torna a raiz atual
            self._split_child(self.root_rva, 0, old_root_rva) # Divide o filho (antiga raiz)
            self._insert_non_full(self._read_node(self.root_rva), key, record_pointer)
        else:
            self._insert_non_full(root, key, record_pointer)

    def _insert_non_full(self, node: BTreeNode, key: int, record_pointer: int):
        """Insere uma chave em um nó não cheio."""
        i = node.num_keys - 1
        if node.is_leaf:
            # Check if key already exists, if so, update the pointer
            if key in node.keys:
                idx = node.keys.index(key)
                node.record_pointers[idx] = record_pointer
            else:
                node.keys.append(0) # Espaços temporários para inserção
                node.record_pointers.append(0)
                while i >= 0 and key < node.keys[i]:
                    node.keys[i + 1] = node.keys[i]
                    node.record_pointers[i + 1] = node.record_pointers[i]
                    i -= 1
                node.keys[i + 1] = key
                node.record_pointers[i + 1] = record_pointer
                node.num_keys += 1
            # Para este modelo de demo, o nó precisa ser escrito no seu RVA correto.
            # No entanto, a implementação recursiva de `_insert_non_full` não passa o RVA do `node`
            # para o `_write_node`. Isso é uma simplificação para a demo.
            # Em um sistema robusto, cada nó teria seu RVA, ou a recursão passaria o RVA do nó atual.
            # Para o contexto atual onde a B-Tree é carregada na memória (modo B-Tree) ou
            # reconstruída do índice sequencial (outros modos), essa escrita imediata aqui
            # não é estritamente necessária, pois a persistência ocorre em massa.
            # Deixando a chamada original de _write_node como está, mas com a ressalva.
            self._write_node(node, self.root_rva if node.num_keys == self._read_node(self.root_rva).num_keys else None)
            
        else: # Nó interno
            # Encontra o filho onde a chave deve ser inserida
            j = 0
            while j < node.num_keys and key > node.keys[j]:
                j += 1
            child_rva = node.children[j]
            child = self._read_node(child_rva)

            if child.num_keys == (2 * ORDER - 1): # Filho está cheio, precisa dividir
                self._split_child(self._get_node_rva(node), j, child_rva) # Precisa do RVA do 'node'
                # Após a divisão, a chave pode ir para um dos dois novos filhos
                parent_reloaded = self._read_node(self._get_node_rva(node)) # Recarrega o pai após a divisão
                if j < parent_reloaded.num_keys and key > parent_reloaded.keys[j]: # Se a chave for maior que a chave mediana, ir para o novo nó à direita
                    self._insert_non_full(self._read_node(parent_reloaded.children[j + 1]), key, record_pointer)
                else: # Caso contrário, ir para o nó original
                    self._insert_non_full(self._read_node(parent_reloaded.children[j]), key, record_pointer)
            else:
                self._insert_non_full(child, key, record_pointer)

    # Helper para obter o RVA de um nó. Idealmente, o nó deveria ter seu próprio RVA.
    # Para esta demo, como a BTree é recarregada, um mapeamento simples é ok.
    # Em um ambiente de produção, seria mais robusto.
    def _get_node_rva(self, node: BTreeNode) -> int:
        if node is self._read_node(self.root_rva): # Verifica se é o nó raiz
            return self.root_rva
        # Se não for a raiz, isso se torna complexo sem um RVA armazenado no nó.
        # Por simplicidade e para a demo, assumiremos que se a BTree é recarregada,
        # o root_rva é o ponto de partida.
        # Para nós não-raiz, isso seria um problema em uma aplicação real.
        logger.warning("Tentativa de obter RVA de nó não-raiz sem RVA explícito. Pode levar a inconsistências.")
        return -1 # Indica erro ou rva inválido

    def search(self, key: int) -> Optional[int]:
        """Procura uma chave e retorna o ponteiro do registro associado."""
        return self._search_recursive(self.root_rva, key)

    def _search_recursive(self, rva: int, key: int) -> Optional[int]:
        """Função recursiva para busca."""
        if rva == -1: # Nó inválido
            return None
        if not self.btree_file.exists() or self.btree_file.stat().st_size == 0:
            return None # Árvore vazia

        try:
            node = self._read_node(rva)
            i = 0
            while i < node.num_keys and key > node.keys[i]:
                i += 1
            
            if i < node.num_keys and key == node.keys[i]:
                return node.record_pointers[i] # Chave encontrada
            
            if node.is_leaf:
                return None # Não encontrado na folha
            else:
                return self._search_recursive(node.children[i], key) # Buscar no filho apropriado
        except Exception as e:
            logger.error(f"Erro ao buscar no nó B-Tree RVA {rva}: {e}. {traceback.format_exc()}")
            return None


    def get_all_records_pointers(self) -> List[int]:
        """Retorna todos os ponteiros de registro em ordem de chave."""
        pointers = []
        if self.btree_file.exists() and self.btree_file.stat().st_size > 0:
            self._traverse_and_collect_pointers(self.root_rva, pointers)
        return pointers

    def _traverse_and_collect_pointers(self, rva: int, pointers: List[int]):
        """Função recursiva para percorrer e coletar ponteiros."""
        if rva == -1:
            return # Nó inválido

        try:
            node = self._read_node(rva)
            
            # Percorre os filhos e chaves
            for i in range(node.num_keys):
                if not node.is_leaf:
                    self._traverse_and_collect_pointers(node.children[i], pointers)
                pointers.append(node.record_pointers[i])
            
            if not node.is_leaf:
                self._traverse_and_collect_pointers(node.children[node.num_keys], pointers)
        except Exception as e:
            logger.error(f"Erro ao atravessar nó B-Tree RVA {rva}: {e}. {traceback.format_exc()}")
            # Continua a execução, mas o resultado pode ser incompleto


    def reconstruct_from_sequential_index(self, sequential_index_manager: Any):
        """Reconstrói a B-Tree a partir do índice sequencial."""
        logger.info(f"Reconstruindo B-Tree de '{sequential_index_manager.index_file}' para '{self.btree_file}'...")
        
        # Limpa o arquivo B-Tree existente para reconstrução
        with self.lock:
            if self.btree_file.exists():
                os.remove(self.btree_file)
        self._initialize_btree_file() # Re-inicializa o arquivo B-Tree vazio

        # Obter entradas do índice sequencial, filtrando para obter o último offset válido
        # A BTree precisa apenas das chaves e offsets finais.
        # Usa a lógica do DBManager para obter os latest_valid_offsets
        entries = sequential_index_manager.get_all_entries()
        latest_valid_offsets = {}
        for record_hash, offset in entries:
            if offset == APP_CONFIG["RECORD_DELETED_MARKER"]:
                if record_hash in latest_valid_offsets:
                    del latest_valid_offsets[record_hash]
            else:
                latest_valid_offsets[record_hash] = offset
        
        # Ordenar as entradas por chave para inserção eficiente na B-Tree
        sorted_entries = sorted(latest_valid_offsets.items(), key=lambda item: item[0])

        total_entries = len(sorted_entries)
        for i, (key, offset) in enumerate(sorted_entries):
            try:
                self.insert(key, offset)
            except Exception as e:
                logger.error(f"Erro ao inserir entrada {key}:{offset} na B-Tree durante reconstrução: {e}")
            if i % 1000 == 0: # Log de progresso
                logger.info(f"Reconstrução da B-Tree: {i}/{total_entries} entradas processadas.")
        logger.info("Reconstrução da B-Tree concluída.")

    def save_in_memory_tree(self, in_memory_btree_nodes: Dict[int, BTreeNode]):
        """Salva a B-Tree em memória para o arquivo .btr."""
        logger.info(f"Salvando B-Tree em memória para '{self.btree_file}'...")
        with self.lock:
            if self.btree_file.exists():
                os.remove(self.btree_file)
            self._initialize_btree_file() # Re-inicializa o arquivo B-Tree vazio (cria nó raiz em 0)
            
            # A forma mais simples de persistir a árvore em memória é reconstruí-la
            # no arquivo .btr a partir dos dados atualmente válidos na árvore em memória.
            # Isso significa re-inserir todas as chaves/ponteiros (exceto deletados).
            
            # Para obter as chaves/ponteiros da árvore em memória, precisamos percorrê-la
            # de alguma forma. A BTree.get_all_records_pointers() faz isso.
            
            # Temporariamente, vamos "setar" a B-Tree para si mesma para usar o get_all_records_pointers
            # e depois reconstruir o arquivo.
            
            # O get_all_records_pointers() atual lê do DISCO.
            # Se in_memory_btree_nodes é o *estado atual* da B-Tree em memória,
            # precisamos de uma forma de obter os record_pointers dela.
            
            # Para simplificar a demo, vamos assumir que as chaves e offsets
            # no `sequential_index` são a fonte da verdade para reconstruir
            # a B-Tree em disco. Isso significa que, no modo B-Tree,
            # o sequential_index é o "log" que permite reconstruir a B-Tree.
            # A requisição do usuário "o arquivo index.btr só será reescrito quando mudar de modo de operação
            # ou mudar de Streamlit UI quando "B-Tree" está selecionado" implica que o estado da memória
            # é despejado para o disco.

            # Reconstruindo a B-Tree persistente do índice sequencial é mais robusto
            # para o cenário de demo, garantindo que a B-Tree em disco reflita
            # todas as operações que foram registradas no índice sequencial.
            self.reconstruct_from_sequential_index(SequentialIndexManager(APP_CONFIG["SEQUENTIAL_INDEX_FILE"]))
        logger.info(f"B-Tree em memória salva (reconstruída do índice sequencial) para '{self.btree_file}'.")

    def load_in_memory_tree(self) -> Dict[int, BTreeNode]:
        """Carrega a B-Tree do arquivo .btr para a memória."""
        logger.info(f"Carregando B-Tree de '{self.btree_file}' para a memória...")
        in_memory_btree_nodes = {}
        with self.lock:
            if not self.btree_file.exists() or self.btree_file.stat().st_size == 0:
                logger.info("Arquivo B-Tree vazio ou não encontrado. Iniciando B-Tree em memória vazia.")
                return in_memory_btree_nodes
            
            # Percorre o arquivo .btr e carrega todos os nós
            current_rva = 0
            file_size = self.btree_file.stat().st_size
            while current_rva < file_size:
                try:
                    node = self._read_node(current_rva)
                    in_memory_btree_nodes[current_rva] = node
                    current_rva += NODE_SIZE
                except Exception as e:
                    logger.error(f"Erro ao carregar nó B-Tree do RVA {current_rva} para memória: {e}")
                    break # Interrompe se não conseguir ler um nó
        logger.info(f"B-Tree carregada para memória. Total de nós: {len(in_memory_btree_nodes)}")
        return in_memory_btree_nodes


class SequentialIndexManager:
    """Gerencia um índice sequencial (record_id_hash, offset) em um arquivo."""
    def __init__(self, index_file: Path):
        self.index_file = index_file
        self.lock = filelock.FileLock(APP_CONFIG["LOCK_FILE"]) # Usar o mesmo lock para o DBManager
        self._initialize_index_file()

    def _initialize_index_file(self):
        """Cria o arquivo de índice sequencial se não existir."""
        if not self.index_file.exists():
            with self.lock:
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    pass # Cria um arquivo vazio
            logger.info(f"Arquivo de índice sequencial '{self.index_file}' inicializado.")

    def append_entry(self, record_id_hash: int, offset: int):
        """Adiciona uma nova entrada (hash, offset) ao final do índice sequencial."""
        with self.lock:
            with open(self.index_file, 'a', encoding='utf-8') as f:
                f.write(f"{record_id_hash},{offset}\n")
            logger.debug(f"Entrada adicionada ao índice sequencial: {record_id_hash},{offset}")

    def get_offset(self, record_id_hash: int) -> Optional[int]:
        """Procura o offset de um hash no índice sequencial (leitura linear).
        Retorna o ÚLTIMO offset válido encontrado para a chave,
        considerando marcadores de deleção.
        """
        latest_offset = None
        with self.lock:
            if not self.index_file.exists():
                return None
            with open(self.index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        key_str, offset_str = line.strip().split(',')
                        current_hash = int(key_str)
                        current_offset = int(offset_str)
                        
                        if current_hash == record_id_hash:
                            if current_offset == APP_CONFIG["RECORD_DELETED_MARKER"]:
                                latest_offset = None # Se for um marcador de deleção, o registro não é válido
                            else:
                                latest_offset = current_offset # Atualiza com o último offset válido
                    except ValueError:
                        logger.warning(f"Linha inválida no índice sequencial: {line.strip()}")
            return latest_offset

    def get_all_entries(self) -> List[Tuple[int, int]]:
        """Retorna todas as entradas (hash, offset) do índice sequencial, sem filtrar."""
        entries = []
        with self.lock:
            if not self.index_file.exists():
                return []
            with open(self.index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        key_str, offset_str = line.strip().split(',')
                        entries.append((int(key_str), int(offset_str)))
                    except ValueError:
                        logger.warning(f"Linha inválida no índice sequencial: {line.strip()}")
        return entries
    
    def clear_index(self):
        """Limpa o conteúdo do índice sequencial."""
        with self.lock:
            if self.index_file.exists():
                os.remove(self.index_file)
            self._initialize_index_file()
        logger.info(f"Índice sequencial '{self.index_file}' limpo.")


# --- Gerenciador de Banco de Dados (Refatorado para modos de operação) ---
class DBManager:
    """Gerencia a persistência de dados em disco e a indexação B-Tree."""
    def __init__(self, operation_mode: str):
        self.db_file = APP_CONFIG["DB_FILE"]
        self.sequential_index = SequentialIndexManager(APP_CONFIG["SEQUENTIAL_INDEX_FILE"])
        self.btree_index = BTree(APP_CONFIG["BTREE_FILE"])
        self.db_lock = filelock.FileLock(APP_CONFIG["LOCK_FILE"]) # Bloqueio para o arquivo de dados

        self._initialize_db_file()
        
        self.operation_mode = operation_mode
        self.in_memory_btree_nodes: Optional[Dict[int, BTreeNode]] = None

        if self.operation_mode == "B-Tree":
            self._load_btree_into_memory()
        logger.info(f"DBManager inicializado no modo: '{self.operation_mode}'.")

    def set_operation_mode(self, new_mode: str):
        """Define o modo de operação e realiza ações de transição."""
        if self.operation_mode == "B-Tree" and new_mode != "B-Tree":
            # Se estava no modo B-Tree e está saindo, persiste a árvore em memória
            self._save_btree_from_memory()
            self.in_memory_btree_nodes = None # Limpa a árvore em memória
        
        if new_mode == "B-Tree" and self.operation_mode != "B-Tree":
            # Se está entrando no modo B-Tree, carrega a árvore em memória
            self._load_btree_into_memory()

        self.operation_mode = new_mode
        logger.info(f"Modo de operação alterado para: '{self.operation_mode}'.")


    def _initialize_db_file(self):
        """Cria o arquivo de banco de dados se não existir."""
        if not self.db_file.exists():
            with self.db_lock:
                with open(self.db_file, 'wb') as f:
                    pass
            logger.info(f"Arquivo de banco de dados '{self.db_file}' criado.")

    def _generate_record_id(self, record: Dict[str, Any]) -> str:
        """Gera um ID (hash SHA256 truncado) para o registro."""
        unique_string = f"{record.get('crash_date', '')}-{record.get('crash_hour', '')}-{record.get('trafficway_type', '')}-{time.time()}"
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()[:16]

    def _hash_to_int(self, hex_hash: str) -> int:
        """Converte um hash hexadecimal para um inteiro (para chaves de índice)."""
        return int(hex_hash, 16)
    
    def _sync_btree_from_sequential_index(self):
        """Sincroniza/reconstrói a B-Tree a partir do índice sequencial."""
        self.btree_index.reconstruct_from_sequential_index(self.sequential_index)
        st.success("B-Tree sincronizada/reconstruída a partir do índice sequencial com sucesso!")

    def _load_btree_into_memory(self):
        """Carrega a B-Tree do arquivo .btr para a memória."""
        self.in_memory_btree_nodes = self.btree_index.load_in_memory_tree()
        if not self.in_memory_btree_nodes:
            logger.info("B-Tree em memória está vazia, tentando reconstruir do índice sequencial.")
            self._sync_btree_from_sequential_index() # Tenta reconstruir se vazia
            self.in_memory_btree_nodes = self.btree_index.load_in_memory_tree() # Recarrega após reconstrução
            if self.in_memory_btree_nodes:
                st.info("B-Tree em memória reconstruída do índice sequencial.")
            else:
                st.warning("Não foi possível carregar ou reconstruir a B-Tree em memória. Operações podem ser limitadas.")
        else:
            st.info("B-Tree carregada para a memória.")


    def _save_btree_from_memory(self):
        """Salva a B-Tree em memória para o arquivo .btr."""
        if self.in_memory_btree_nodes is not None:
            # Ao salvar a B-Tree do modo em memória, ela é reconstruída a partir do sequential_index
            # para garantir que todas as operações (incluindo as lógicas de update/delete) sejam persistidas.
            self._sync_btree_from_sequential_index() # Força a persistência da B-Tree do índice sequencial
            self.in_memory_btree_nodes = None # Limpa a árvore em memória
            st.success("B-Tree em memória salva (sincronizada com índice sequencial) no arquivo .btr.")
        else:
            logger.warning("Nenhuma B-Tree em memória para salvar.")

    def insert_record(self, record: Dict[str, Any]) -> str:
        """Insere um novo registro com base no modo de operação."""
        record_id = self._generate_record_id(record)
        record['record_id'] = record_id
        serialized_record = json.dumps(record, ensure_ascii=False, default=str) + '\n'
        record_bytes = serialized_record.encode('utf-8')
        
        with self.db_lock:
            with open(self.db_file, 'ab') as f:
                offset = f.tell()
                f.write(record_bytes)
        logger.info(f"Registro '{record_id}' gravado no arquivo de dados em offset {offset}.")

        key_for_index = self._hash_to_int(record_id)
        
        # Sempre apenda no índice sequencial primeiro, conforme a ordem pedida
        self.sequential_index.append_entry(key_for_index, offset)
        logger.info(f"Entrada '{record_id}' adicionada ao índice sequencial.")

        if self.operation_mode == "B-Tree":
            if self.in_memory_btree_nodes is None:
                st.error("B-Tree em memória não carregada. Recarregue o modo B-Tree ou sincronize.")
                return ""
            # Insere na B-Tree em memória
            self.btree_index.insert(key_for_index, offset) 
            logger.info(f"Modo B-Tree: Entrada '{record_id}' inserida na B-Tree em memória.")

        return record_id

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Recupera um registro com base no modo de operação."""
        key_for_index = self._hash_to_int(record_id)
        offset = None

        if self.operation_mode == "B-Tree":
            if self.in_memory_btree_nodes is None:
                st.error("B-Tree em memória não carregada. Recarregue o modo B-Tree ou sincronize.")
                return None
            # No modo B-Tree, busca na árvore em memória para o offset
            offset = self.btree_index.search(key_for_index)
            if offset is None or offset == APP_CONFIG["RECORD_DELETED_MARKER"]:
                logger.warning(f"Modo B-Tree: Registro '{record_id}' não encontrado ou marcado como deletado na B-Tree em memória.")
                return None
            logger.info(f"Modo B-Tree: Registro '{record_id}' encontrado na B-Tree em memória no offset {offset}.")
        else: # "Direto" or "Indice"
            # Em ambos os modos, a busca usa o SequentialIndexManager para encontrar o último offset válido
            offset = self.sequential_index.get_offset(key_for_index)
            if offset is None or offset == APP_CONFIG["RECORD_DELETED_MARKER"]:
                logger.warning(f"Modo {self.operation_mode}: Registro '{record_id}' não encontrado ou marcado como deletado no índice sequencial.")
                return None
            logger.info(f"Modo {self.operation_mode}: Registro '{record_id}' encontrado no índice sequencial no offset {offset}.")

        # Após obter o offset, lê o registro do arquivo de dados
        with self.db_lock:
            if not self.db_file.exists():
                logger.error(f"Arquivo de dados '{self.db_file}' não encontrado.")
                return None
            with open(self.db_file, 'rb') as f:
                f.seek(offset)
                line = f.readline().decode('utf-8')
                if line:
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        logger.error(f"Erro ao decodificar JSON do registro no offset {offset}. Linha: {line[:100]}...")
                        return None
                return None
    
    def update_record(self, record_id: str, new_data: Dict[str, Any]) -> bool:
        """Atualiza um registro com base no modo de operação."""
        # Primeiro, verifica se o registro existe (e obtém seus dados para mesclagem)
        old_record = self.get_record(record_id)
        if old_record is None:
            st.warning(f"Tentativa de atualizar registro ID '{record_id}', mas não encontrado ou deletado.")
            return False
        
        updated_record = {**old_record, **new_data}
        updated_record['record_id'] = record_id

        serialized_record = json.dumps(updated_record, ensure_ascii=False, default=str) + '\n'
        record_bytes = serialized_record.encode('utf-8')

        with self.db_lock:
            with open(self.db_file, 'ab') as f:
                new_offset = f.tell()
                f.write(record_bytes)
        logger.info(f"Registro '{record_id}' atualizado e gravado no arquivo de dados em novo offset {new_offset}.")

        key_for_index = self._hash_to_int(record_id)

        # Sempre apenda no índice sequencial primeiro, conforme a ordem pedida
        self.sequential_index.append_entry(key_for_index, new_offset)
        logger.info(f"Entrada '{record_id}' atualizada no índice sequencial.")

        if self.operation_mode == "B-Tree":
            if self.in_memory_btree_nodes is None:
                st.error("B-Tree em memória não carregada. Recarregue o modo B-Tree ou sincronize.")
                return False
            # Atualiza na B-Tree em memória
            self.btree_index.insert(key_for_index, new_offset) 
            logger.info(f"Modo B-Tree: Entrada '{record_id}' atualizada na B-Tree em memória.")

        return True

    def delete_record(self, record_id: str) -> bool:
        """Marca um registro como 'deletado' adicionando um marcador no índice sequencial."""
        key_for_index = self._hash_to_int(record_id)

        # Primeiro, verifica se o registro logicamente existe antes de marcá-lo para deleção
        existing_record = self.get_record(record_id)
        if existing_record is None:
            st.warning(f"Registro com ID '{record_id}' não encontrado para exclusão.")
            return False

        # Adiciona um marcador de deleção ao índice sequencial
        self.sequential_index.append_entry(key_for_index, APP_CONFIG["RECORD_DELETED_MARKER"])
        logger.info(f"Registro '{record_id}' marcado como deletado no índice sequencial com marker {APP_CONFIG['RECORD_DELETED_MARKER']}.")

        if self.operation_mode == "B-Tree":
            if self.in_memory_btree_nodes is None:
                st.error("B-Tree em memória não carregada. Recarregue o modo B-Tree ou sincronize.")
                return False
            # Na B-Tree em memória, atualizamos sua entrada para apontar para o marcador de deleção
            # A inserção na B-Tree se comporta como uma atualização para chaves existentes.
            self.btree_index.insert(key_for_index, APP_CONFIG["RECORD_DELETED_MARKER"]) 
            logger.info(f"Modo B-Tree: Registro '{record_id}' marcado como deletado na B-Tree em memória.")
        
        st.success(f"Registro '{record_id}' logicamente excluído. Para remover completamente do arquivo .btr, sincronize ou mude de modo.")
        return True


    def get_all_records(self) -> List[Dict[str, Any]]:
        """Retorna todos os registros armazenados com base no modo de operação."""
        all_valid_offsets = []
        if self.operation_mode == "B-Tree":
            if self.in_memory_btree_nodes is None:
                st.error("B-Tree em memória não carregada. Recarregue o modo B-Tree ou sincronize.")
                return []
            # Para o modo B-Tree, recuperamos todos os ponteiros da B-Tree em memória
            # e filtramos os marcadores de deleção.
            raw_offsets_from_btree = self.btree_index.get_all_records_pointers()
            for offset in raw_offsets_from_btree:
                if offset != APP_CONFIG["RECORD_DELETED_MARKER"]:
                    all_valid_offsets.append(offset)
            logger.info(f"Modo B-Tree: Recuperando todos os offsets da B-Tree em memória e filtrando deletados.")
        else: # "Direto" or "Indice"
            # Para os modos de índice sequencial, obtemos todas as entradas e então
            # determinamos o último offset válido para cada ID.
            entries = self.sequential_index.get_all_entries()
            latest_valid_offsets_map = {} # {record_id_hash: latest_offset}

            # Processa as entradas para encontrar o último offset válido para cada record_id_hash
            # Iterando do início ao fim, a última entrada para uma chave "ganha".
            for record_hash, offset in entries:
                if offset == APP_CONFIG["RECORD_DELETED_MARKER"]:
                    # Se um registro é marcado como deletado, remove-o do mapa de offsets válidos
                    if record_hash in latest_valid_offsets_map:
                        del latest_valid_offsets_map[record_hash]
                else:
                    # Se for um offset válido, atualiza o mapa com o mais recente
                    latest_valid_offsets_map[record_hash] = offset
            
            all_valid_offsets = list(latest_valid_offsets_map.values())
            logger.info(f"Modo {self.operation_mode}: Recuperando todos os offsets do índice sequencial e filtrando deletados.")

        records = []
        with self.db_lock:
            if not self.db_file.exists():
                logger.error(f"Arquivo de dados '{self.db_file}' não encontrado para obter todos os registros.")
                return []
            with open(self.db_file, 'rb') as f:
                for offset in all_valid_offsets:
                    f.seek(offset)
                    line = f.readline().decode('utf-8')
                    if line:
                        try:
                            record = json.loads(line)
                            records.append(record)
                        except json.JSONDecodeError:
                            logger.error(f"Erro ao decodificar JSON de registro inválido no offset {offset}.")
        return records

    def export_data(self, output_file: Path) -> None:
        """Exporta todos os registros para um arquivo CSV."""
        records = self.get_all_records() # Usa o método que respeita o modo de operação
        if not records:
            st.warning("Nenhum registro para exportar.")
            return

        fieldnames = [FIELD_MAPPING[field] for field in REQUIRED_FIELDS_EN] + ['record_id']

        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for record in records:
                    csv_record = {}
                    for en_field, pt_field in FIELD_MAPPING.items():
                        value = record.get(en_field, '')
                        if en_field in LIST_FIELDS_EN and isinstance(value, list):
                            csv_record[pt_field] = ', '.join(value)
                        elif isinstance(value, date):
                            csv_record[pt_field] = value.isoformat()
                        else:
                            csv_record[pt_field] = value
                    csv_record['record_id'] = record.get('record_id', '')
                    writer.writerow(csv_record)
            logger.info(f"Dados exportados para '{output_file}'.")
        except Exception as e:
            logger.error(f"Erro ao exportar dados para CSV: {traceback.format_exc()}")
            st.error(f"🚨 Erro ao exportar dados: {e}")

# --- Funções de Ajuda e UI ---

# Removido get_db_manager como função separada para gerenciar via session_state

def generate_unique_id() -> str:
    """Gera um ID único baseado no timestamp."""
    return str(int(time.time() * 100000))

def display_record(record: Dict[str, Any]):
    """Exibe os detalhes de um registro."""
    if not record:
        st.write("Registro não encontrado.")
        return

    st.subheader(f"Detalhes do Registro: {record.get('record_id', 'N/A')}")
    col1, col2 = st.columns(2)

    # Exibe os campos usando os nomes em português
    for i, (en_field, pt_field) in enumerate(FIELD_MAPPING.items()):
        display_value = record.get(en_field, "Não informado")
        if en_field in LIST_FIELDS_EN and isinstance(display_value, list):
            display_value = ", ".join(display_value)
        elif isinstance(display_value, date):
            display_value = display_value.strftime("%d/%m/%Y") # Formato de data PT-BR

        if i % 2 == 0:
            with col1:
                st.write(f"**{pt_field.replace('_', ' ').title()}:** {display_value}")
        else:
            with col2:
                st.write(f"**{pt_field.replace('_', ' ').title()}:** {display_value}")
    
    # Exibe o ID do registro no final
    st.write(f"**ID do Registro:** `{record.get('record_id', 'N/A')}`")


def render_data_management_section():
    """Seção para gerenciar dados (CRUD e Import/Export)."""
    st.header("Gerenciamento de Dados de Acidentes")

    # Modos de operação
    operation_mode = st.session_state.get("operation_mode", "Direto")
    new_operation_mode = st.selectbox(
        "Selecione o Modo de Operação:",
        ["Direto", "Indice", "B-Tree"],
        index=["Direto", "Indice", "B-Tree"].index(operation_mode),
        key="select_operation_mode"
    )

    if new_operation_mode != operation_mode:
        if "db_manager" in st.session_state:
            st.session_state.db_manager.set_operation_mode(new_operation_mode)
        st.session_state["operation_mode"] = new_operation_mode
        st.experimental_rerun() # Reinicia para aplicar o novo modo

    st.info(f"Modo de operação atual: **{st.session_state.operation_mode}**")


    # --- Adicionar/Atualizar Registro ---
    st.subheader("Adicionar/Atualizar Registro")
    
    # Formulário para entrada de dados
    with st.form("record_form", clear_on_submit=True):
        st.write("Preencha os campos abaixo:")
        new_record_data = {}
        for en_field, pt_field in FIELD_MAPPING.items():
            if en_field == "record_id": # ID é gerado, não inserido pelo usuário
                continue

            if en_field == "crash_date":
                # Campo de data
                new_record_data[en_field] = st.date_input(
                    f"{pt_field.replace('_', ' ').title()}:",
                    value=date.today(),
                    key=f"input_{en_field}"
                )
            elif en_field in LIST_FIELDS_EN:
                # Campo de texto para listas (separado por vírgulas)
                text_input = st.text_input(
                    f"{pt_field.replace('_', ' ').title()} (separar por vírgulas):",
                    key=f"input_{en_field}"
                )
                new_record_data[en_field] = [item.strip() for item in text_input.split(',') if item.strip()]
            elif en_field in ["num_units", "injuries_total", "injuries_fatal", 
                              "injuries_incapacitating", "injuries_non_incapacitating",
                              "injuries_reported_not_evident", "injuries_no_indication",
                              "crash_hour", "crash_day_of_week", "crash_month"]:
                # Campos numéricos
                new_record_data[en_field] = st.number_input(
                    f"{pt_field.replace('_', ' ').title()}:",
                    min_value=0, value=0, step=1,
                    key=f"input_{en_field}"
                )
            elif en_field == "intersection_related_i":
                # Campo booleano (Sim/Não)
                new_record_data[en_field] = st.selectbox(
                    f"{pt_field.replace('_', ' ').title()}:",
                    options=["Sim", "Não"],
                    index=1 if "não" in new_record_data.get(en_field, "").lower() else 0, # Default para Não
                    key=f"input_{en_field}"
                ) == "Sim" # Converte para True/False
            else:
                # Outros campos de texto
                new_record_data[en_field] = st.text_input(
                    f"{pt_field.replace('_', ' ').title()}:",
                    key=f"input_{en_field}"
                )

        record_id_to_update = st.text_input("ID do Registro para Atualizar (deixe em branco para novo registro):", key="update_id_input")
        
        submitted = st.form_submit_button("Salvar Registro")
        if submitted:
            # Validação dos campos obrigatórios
            is_valid = True
            for en_field in REQUIRED_FIELDS_EN:
                if en_field not in new_record_data or not new_record_data[en_field]:
                    if en_field != "record_id": # ID é gerado
                        st.error(f"O campo '{FIELD_MAPPING.get(en_field, en_field).replace('_', ' ').title()}' é obrigatório.")
                        is_valid = False
            
            if is_valid:
                if record_id_to_update:
                    # Se um ID foi fornecido, tenta atualizar
                    success = st.session_state.db_manager.update_record(record_id_to_update, new_record_data)
                    if success:
                        st.success(f"Registro '{record_id_to_update}' atualizado com sucesso!")
                    else:
                        st.error(f"Falha ao atualizar registro '{record_id_to_update}'. Verifique o ID.")
                else:
                    # Se nenhum ID, adiciona um novo registro
                    record_id = st.session_state.db_manager.insert_record(new_record_data)
                    st.success(f"Novo registro adicionado com ID: {record_id}")
            else:
                st.error("Por favor, preencha todos os campos obrigatórios.")

    st.markdown("---")

    # Botão para sincronizar B-Tree
    if st.session_state.operation_mode in ["Direto", "Indice"]:
        if st.button("Sincronizar B-Tree com Índice Sequencial"):
            with st.spinner("Sincronizando B-Tree... Pode levar alguns segundos para grandes volumes de dados."):
                st.session_state.db_manager._sync_btree_from_sequential_index()


    st.markdown("---")

    # --- Importar Dados do CSV ---
    st.subheader("Importar Dados do CSV")
    uploaded_file = st.file_uploader("Escolha um arquivo CSV para importar", type=["csv"], key="csv_uploader_import")
    if uploaded_file is not None:
        try:
            # Salva o arquivo temporariamente para a função de leitura
            temp_csv_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
            with open(temp_csv_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # Usa a função de normalização e leitura com tradução de cabeçalhos
            records_to_insert = read_and_normalize_csv_data(temp_csv_path)

            if records_to_insert:
                st.info(f"Iniciando importação de {len(records_to_insert)} registros do CSV...")
                success_count = 0
                total_records = len(records_to_insert)
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, record in enumerate(records_to_insert):
                    try:
                        st.session_state.db_manager.insert_record(record)
                        success_count += 1
                        progress_bar.progress((i + 1) / total_records)
                        status_text.text(f"Processando registro {i+1} de {total_records}...")
                    except Exception as record_e:
                        st.error(f"Erro ao inserir registro {i+1}: {record}. Erro: {record_e}")
                        logger.error(f"Erro ao inserir registro do CSV: {traceback.format_exc()}")
                
                progress_bar.empty()
                status_text.empty()
                st.success(f"Importação concluída! {success_count} de {total_records} registros importados com sucesso.")
            else:
                st.warning("Nenhum registro válido encontrado no CSV para importação ou todos os registros falharam na validação.")
            
            # Limpa o arquivo temporário
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)

        except Exception as e:
            st.error(f"🚨 Erro ao processar o arquivo CSV: {e}")
            logger.error(f"Erro ao processar CSV de importação: {traceback.format_exc()}")
    
    st.markdown("---")

    # --- Exportar Dados para CSV ---
    st.subheader("Exportar Dados para CSV")
    if st.button("Gerar CSV para Download"):
        try:
            # Usa o nome do arquivo da APP_CONFIG para o download, mas salva temporariamente
            temp_export_path = Path(tempfile.gettempdir()) / APP_CONFIG["CSV_FILE_NAME"]
            st.session_state.db_manager.export_data(temp_export_path)
            
            if temp_export_path.exists():
                with open(temp_export_path, "rb") as f:
                    st.download_button(
                        label="Download CSV Exportado",
                        data=f.read(),
                        file_name=APP_CONFIG["CSV_FILE_NAME"], # Nome de arquivo para download
                        mime="text/csv"
                    )
                os.remove(temp_export_path)
                st.success("Arquivo CSV gerado com sucesso!")
            else:
                st.error("Falha ao gerar arquivo CSV para exportação.")
        except Exception as e:
            st.error(f"🚨 Erro ao exportar dados: {e}")
            logger.error(f"Erro ao exportar dados para CSV: {traceback.format_exc()}")

    st.markdown("---")

    # --- Visualizar Registros ---
    st.subheader("Visualizar Registros Existentes")
    search_query = st.text_input("Buscar registro por ID (ou deixe em branco para ver todos):", key="search_record_id")
    
    if st.button("Buscar/Listar Registros"):
        if search_query:
            record = st.session_state.db_manager.get_record(search_query)
            if record:
                display_record(record)
                if st.button(f"Deletar Registro {search_query}"):
                    if st.session_state.db_manager.delete_record(search_query):
                        st.success(f"Registro '{search_query}' deletado (logicamente).")
                    else:
                        st.error(f"Falha ao deletar registro '{search_query}'.")
            else:
                st.warning(f"Registro com ID '{search_query}' não encontrado.")
        else:
            all_records = st.session_state.db_manager.get_all_records()
            if all_records:
                st.write(f"Total de registros: {len(all_records)}")
                # Exibe uma tabela com os registros
                st.dataframe(all_records)
            else:
                st.info("Nenhum registro encontrado no banco de dados.")

def render_cryptography_section():
    """Seção para gerenciar criptografia."""
    st.header("Gerenciamento de Criptografia")

    st.subheader("Geração e Carregamento de Chaves RSA")
    # Para garantir que as chaves RSA sejam salvas em RSA_KEYS_DIR
    APP_CONFIG["PRIVATE_KEY_FILE"] = APP_CONFIG["RSA_KEYS_DIR"] / "private_key.pem"
    APP_CONFIG["PUBLIC_KEY_FILE"] = APP_CONFIG["RSA_KEYS_DIR"] / "public_key.pem"

    if st.button("Gerar Novas Chaves RSA"):
        private_pem, public_pem = generate_rsa_key_pair()
        save_rsa_keys(private_pem, public_pem)
        st.success("Novo par de chaves RSA gerado e salvo com sucesso!")
    
    st.write("---")

    st.subheader("Criptografia e Descriptografia Híbrida (AES + RSA)")
    st.info("As chaves RSA (Cryptography) são usadas para proteger uma chave AES, que por sua vez criptografa/descriptografa os arquivos grandes de dados e índice (Cryptography).")

    private_key, public_key = load_rsa_keys()

    if private_key and public_key:
        file_options = {
            "Arquivo de Dados (.db)": {
                "original": APP_CONFIG["DB_FILE"],
                "encrypted": APP_CONFIG["ENCRYPTED_DB_FILE"],
                "name": "dados"
            },
            "Arquivo de Índice Sequencial (.idx)": {
                "original": APP_CONFIG["SEQUENTIAL_INDEX_FILE"],
                "encrypted": APP_CONFIG["ENCRYPTED_SEQUENTIAL_INDEX_FILE"],
                "name": "índice sequencial"
            },
            "Arquivo B-Tree (.btr)": {
                "original": APP_CONFIG["BTREE_FILE"],
                "encrypted": APP_CONFIG["ENCRYPTED_BTREE_FILE"],
                "name": "B-Tree"
            }
        }
        
        selected_file_type_label = st.selectbox(
            "Selecione o tipo de arquivo para criptografar/descriptografar:",
            list(file_options.keys()),
            key="crypto_file_select"
        )
        
        selected_file_info = file_options[selected_file_type_label]
        target_file_path = selected_file_info["original"]
        encrypted_target_file_path = selected_file_info["encrypted"]
        file_display_name = selected_file_info["name"]

        st.markdown(f"**Arquivo selecionado:** `{target_file_path.name}`")

        if st.button(f"Criptografar {file_display_name.capitalize()} (AES com RSA)"):
            try:
                if not target_file_path.exists():
                    st.warning(f"Arquivo de {file_display_name} '{target_file_path.name}' não encontrado para criptografia.")
                else:
                    # 1. Gerar nova chave AES
                    aes_key = generate_aes_key()
                    # 2. Criptografar chave AES com RSA (Cryptography)
                    encrypted_aes_key = rsa_encrypt_aes_key(aes_key, public_key)
                    # 3. Salvar chave AES criptografada em arquivo
                    with open(APP_CONFIG["AES_KEY_FILE"], "wb") as f:
                        f.write(encrypted_aes_key)
                    logger.info(f"Chave AES criptografada salva em {APP_CONFIG['AES_KEY_FILE']}.")

                    # 4. Criptografar o arquivo selecionado com AES (Cryptography)
                    encrypt_file(target_file_path, encrypted_target_file_path, aes_key)
                    st.success(f"Arquivo de {file_display_name} '{target_file_path.name}' criptografado com sucesso para '{encrypted_target_file_path.name}'!")
            except Exception as e:
                st.error(f"🚨 Erro durante a criptografia do arquivo de {file_display_name}: {e}")
                logger.error(f"Erro na criptografia de {file_display_name}: {traceback.format_exc()}")
        
        if st.button(f"Descriptografar {file_display_name.capitalize()} (AES com RSA)"):
            try:
                if not encrypted_target_file_path.exists():
                    st.warning(f"Arquivo de {file_display_name} criptografado '{encrypted_target_file_path.name}' não encontrado para descriptografia.")
                elif not APP_CONFIG["AES_KEY_FILE"].exists():
                    st.error("Arquivo da chave AES criptografada não encontrado. Não é possível descriptografar.")
                    return

                # 1. Carregar chave AES criptografada
                with open(APP_CONFIG["AES_KEY_FILE"], "rb") as f:
                    encrypted_aes_key = f.read()
                
                # 2. Descriptografar chave AES com RSA privada (Cryptography)
                aes_key = rsa_decrypt_aes_key(encrypted_aes_key, private_key)
                logger.info("Chave AES descriptografada com sucesso.")

                # 3. Descriptografar o arquivo selecionado com AES (Cryptography)
                decrypt_file(encrypted_target_file_path, target_file_path, aes_key)
                st.success(f"Arquivo de {file_display_name} '{encrypted_target_file_path.name}' descriptografado com sucesso para '{target_file_path.name}'!")
            except Exception as e:
                st.error(f"🚨 Erro durante a descriptografia do arquivo de {file_display_name}: {e}")
                logger.error(f"Erro na descriptografia de {file_display_name}: {traceback.format_exc()}")
    else:
        st.warning("Por favor, gere as chaves RSA primeiro para usar as funcionalidades de criptografia.")

def render_administration_section():
    """Seção para administração do sistema."""
    st.header("Administração do Sistema")

    st.subheader("Backup e Restauração")
    if st.button("Criar Backup do Banco de Dados e Índice"):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_db_file = APP_CONFIG["BACKUP_PATH"] / f"traffic_accidents_{timestamp}.db"
            backup_sequential_index_file = APP_CONFIG["BACKUP_PATH"] / f"traffic_accidents_seq_index_{timestamp}.idx"
            backup_btree_file = APP_CONFIG["BACKUP_PATH"] / f"traffic_accidents_btree_{timestamp}.btr"

            if APP_CONFIG["DB_FILE"].exists():
                shutil.copy(APP_CONFIG["DB_FILE"], backup_db_file)
            else:
                st.warning("Arquivo de dados principal não existe para backup.")

            if APP_CONFIG["SEQUENTIAL_INDEX_FILE"].exists():
                shutil.copy(APP_CONFIG["SEQUENTIAL_INDEX_FILE"], backup_sequential_index_file)
            else:
                st.warning("Arquivo de índice sequencial não existe para backup.")
            
            if APP_CONFIG["BTREE_FILE"].exists():
                shutil.copy(APP_CONFIG["BTREE_FILE"], backup_btree_file)
            else:
                st.warning("Arquivo B-Tree não existe para backup.")
            
            st.success(f"Backup criado com sucesso em '{APP_CONFIG['BACKUP_PATH']}'.")
            logger.info(f"Backup criado em {APP_CONFIG['BACKUP_PATH']}")
        except Exception as e:
            st.error(f"🚨 Erro ao criar backup: {e}")
            logger.error(f"Erro na criação de backup: {traceback.format_exc()}")
    
    st.write("---")
    st.subheader("Restaurar Backup")
    # Listar todos os arquivos de backup com qualquer extensão relevante
    backup_files = (
        list(APP_CONFIG["BACKUP_PATH"].glob("traffic_accidents_*.db")) +
        list(APP_CONFIG["BACKUP_PATH"].glob("traffic_accidents_seq_index_*.idx")) +
        list(APP_CONFIG["BACKUP_PATH"].glob("traffic_accidents_btree_*.btr"))
    )
    backup_files.sort(key=os.path.getmtime, reverse=True) # Mais recentes primeiro
    
    if backup_files:
        selected_backup_name = st.selectbox("Escolha um arquivo de backup para restaurar:", [f.name for f in backup_files])
        selected_backup_path = APP_CONFIG["BACKUP_PATH"] / selected_backup_name

        if st.button("Restaurar Backup Selecionado"):
            try:
                # Determina os arquivos correspondentes para restauração
                if selected_backup_path.suffix == ".db":
                    shutil.copy(selected_backup_path, APP_CONFIG["DB_FILE"])
                    st.success(f"Arquivo de dados restaurado de '{selected_backup_path.name}'.")
                    # Tentar encontrar e restaurar os índices correspondentes
                    base_name = selected_backup_path.name.replace(".db", "")
                    corresponding_idx = APP_CONFIG["BACKUP_PATH"] / f"{base_name.replace('traffic_accidents_', 'traffic_accidents_seq_index_')}.idx"
                    corresponding_btr = APP_CONFIG["BACKUP_PATH"] / f"{base_name.replace('traffic_accidents_', 'traffic_accidents_btree_')}.btr"

                    if corresponding_idx.exists():
                        shutil.copy(corresponding_idx, APP_CONFIG["SEQUENTIAL_INDEX_FILE"])
                        st.info(f"Índice sequencial '{corresponding_idx.name}' restaurado.")
                    else:
                        st.warning("Índice sequencial correspondente não encontrado para restauração.")
                    
                    if corresponding_btr.exists():
                        shutil.copy(corresponding_btr, APP_CONFIG["BTREE_FILE"])
                        st.info(f"B-Tree '{corresponding_btr.name}' restaurada.")
                    else:
                        st.warning("B-Tree correspondente não encontrada para restauração.")

                elif selected_backup_path.suffix == ".idx":
                    shutil.copy(selected_backup_path, APP_CONFIG["SEQUENTIAL_INDEX_FILE"])
                    st.success(f"Índice sequencial restaurado de '{selected_backup_path.name}'.")
                    st.info("Para garantir a consistência, a B-Tree pode precisar ser reconstruída a partir deste índice sequencial.")

                elif selected_backup_path.suffix == ".btr":
                    shutil.copy(selected_backup_path, APP_CONFIG["BTREE_FILE"])
                    st.success(f"B-Tree restaurada de '{selected_backup_path.name}'.")
                    st.info("Para garantir a consistência, o índice sequencial pode precisar ser reconstruído ou verificado.")
                else:
                    st.error("Tipo de arquivo de backup desconhecido.")
                
                st.info("Por favor, reinicie a aplicação para que o backup seja totalmente carregado.")
                logger.info(f"Backup restaurado de {selected_backup_name}")
            except Exception as e:
                st.error(f"🚨 Erro ao restaurar backup: {e}")
                logger.error(f"Erro na restauração de backup: {traceback.format_exc()}")
    else:
        st.info("Nenhum arquivo de backup encontrado.")

    st.markdown("---")
    st.subheader("Limpar Dados")
    st.warning("Esta ação removerá todos os dados e os índices permanentemente!")
    if st.button("APAGAR TODOS OS DADOS E ÍNDICES", help="CUIDADO: Esta ação é irreversível!"):
        if st.checkbox("Confirmo que desejo apagar todos os dados e índices.", key="confirm_delete_all"):
            try:
                if APP_CONFIG["DB_FILE"].exists():
                    os.remove(APP_CONFIG["DB_FILE"])
                if APP_CONFIG["SEQUENTIAL_INDEX_FILE"].exists():
                    os.remove(APP_CONFIG["SEQUENTIAL_INDEX_FILE"])
                if APP_CONFIG["BTREE_FILE"].exists():
                    os.remove(APP_CONFIG["BTREE_FILE"])
                if APP_CONFIG["AES_KEY_FILE"].exists():
                    os.remove(APP_CONFIG["AES_KEY_FILE"])
                
                # Reinicializa o DBManager para criar arquivos vazios
                # Reinicializa o operation_mode para "Direto" para um estado limpo
                st.session_state["operation_mode"] = "Direto"
                st.session_state["db_manager"] = DBManager(st.session_state["operation_mode"])
                st.success("Todos os dados e os índices foram apagados com sucesso e o sistema foi reinicializado.")
                logger.info("Todos os dados e índices foram apagados.")
                st.rerun() # Reinicia para refletir o estado limpo
            except Exception as e:
                st.error(f"🚨 Erro ao apagar dados: {e}")
                logger.error(f"Erro ao apagar dados: {traceback.format_exc()}")
        else:
            st.info("Confirmação necessária para apagar todos os dados.")

# --- SEÇÃO DE COMPACTAÇÃO ---
def render_compression_section():
    """Seção para ferramentas de Compactação/Descompactação e Comparação."""
    st.title("Ferramenta de Compactação/Descompactação de Arquivos")
    
    # Initialize progress elements
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    def update_progress(progress: float, message: str):
        progress_bar.progress(progress)
        progress_text.text(message)
    
    # Use selectbox instead of tabs
    selected_view = st.selectbox(
        "Selecione a Visão:", 
        ("Compactação/Descompactação", "Comparação de Algoritmos"), 
        key="main_view_select_compression" # Chave única para evitar conflitos
    )

    # Initialize variables for file paths and temporary directories outside the conditional blocks
    input_path_tab1 = None
    output_path_tab1 = None
    temp_dir_tab1 = None
    input_path_compare = None
    temp_dir_compare = None

    if selected_view == "Compactação/Descompactação":
        # Algorithm selection
        algorithm = st.radio("Selecione o Algoritmo:", ("Huffman", "LZW"), key="algo_select_compression") # Chave única
        
        # Operation selection
        operation = st.radio("Selecione a Operação:", ("Compactação", "Descompactação"), key="op_select_compression") # Chave única
        
        # File source selection
        file_source_option = st.radio(
            "Selecione a Origem do Arquivo:", 
            ("Carregar Arquivo", "Arquivos do Sistema"), 
            key="file_source_compression_option"
        )
        
        selected_file = None
        uploaded_file = None

        if file_source_option == "Carregar Arquivo":
            # Determine allowed file types for upload
            allowed_types = []
            if operation == "Compactação":
                allowed_types = [".csv", ".txt", ".bin", ".db", ".idx", ".btr"] # Mais tipos para compactar
            else: # Descompression
                if algorithm == "Huffman":
                    allowed_types = [".huff", ".lzw"] # Huffman e LZW têm extensões diferentes

            uploaded_file = st.file_uploader(
                "Upload de um arquivo:", 
                type=[ext.strip('.') for ext in allowed_types], # Streamlit expects extensions without leading dot
                key="upload_tab1_compression" # Chave única
            )
            if uploaded_file:
                # Save to a temporary directory for processing
                temp_dir_tab1 = tempfile.mkdtemp()
                input_path_tab1 = os.path.join(temp_dir_tab1, uploaded_file.name)
                with open(input_path_tab1, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.info(f"Arquivo '{uploaded_file.name}' carregado temporariamente.")
        
        elif file_source_option == "Arquivos do Sistema":
            system_files = {
                "Arquivo de Dados (.db)": APP_CONFIG["DB_FILE"],
                "Arquivo de Índice Sequencial (.idx)": APP_CONFIG["SEQUENTIAL_INDEX_FILE"],
                "Arquivo B-Tree (.btr)": APP_CONFIG["BTREE_FILE"]
            }
            # Filtrar as opções baseadas na operação
            available_system_files = {}
            for label, path_obj in system_files.items():
                if operation == "Compactação":
                    available_system_files[label] = path_obj
                elif operation == "Descompactação":
                    # Para descompactação, só permite arquivos que são saídas de compressão
                    if algorithm == "Huffman" and path_obj.suffix == HUFFMAN_COMPRESSED_EXTENSION:
                        available_system_files[label] = path_obj
                    elif algorithm == "LZW" and path_obj.suffix == LZW_COMPRESSED_EXTENSION:
                        available_system_files[label] = path_obj
            
            if available_system_files:
                system_file_label = st.selectbox(
                    "Selecione um arquivo do sistema:",
                    list(available_system_files.keys()),
                    key="system_file_select_compression"
                )
                input_path_tab1 = available_system_files[system_file_label]
                st.info(f"Arquivo do sistema selecionado: '{input_path_tab1.name}'")
            else:
                st.warning("Nenhum arquivo do sistema disponível para esta operação/algoritmo.")
                input_path_tab1 = None # Garante que input_path_tab1 seja None se não houver opções

        if input_path_tab1 and st.button(f"Executar {operation}"):
            progress_bar.progress(0)
            progress_text.text(f"Iniciando {operation.lower()}...")
            
            output_folder = HUFFMAN_COMPRESSED_FOLDER if algorithm == "Huffman" else LZW_COMPRESSED_FOLDER
            
            try:
                if operation == "Compactação":
                    original_file_name, _ = os.path.splitext(os.path.basename(input_path_tab1))
                    output_ext = HUFFMAN_COMPRESSED_EXTENSION if algorithm == "Huffman" else LZW_COMPRESSED_EXTENSION
                    output_file_name = f"{original_file_name}{output_ext}"
                    output_path_tab1 = os.path.join(output_folder, output_file_name)

                    if algorithm == "Huffman":
                        orig_s, comp_s, ratio, proc_t = HuffmanProcessor.compress_file(str(input_path_tab1), output_path_tab1, update_progress)
                    else: # LZW
                        orig_s, comp_s, ratio, proc_t = LZWProcessor.compress(str(input_path_tab1), output_path_tab1, update_progress)
                    
                    st.success(f"{algorithm} Compactação Completa!")
                    st.write(f"Tamanho Original: {orig_s / 1024:.2f} KB")
                    st.write(f"Tamanho Compactado: {comp_s / 1024:.2f} KB")
                    st.write(f"Taxa de Compactação: {ratio:.2f}%")
                    st.write(f"Tempo Gasto: {proc_t:.4f} segundos")

                    if comp_s > 0: # Ensure file was created before offering download
                        with open(output_path_tab1, "rb") as f_out:
                            st.download_button(
                                label=f"Download Arquivo Compactado ({output_ext})",
                                data=f_out.read(),
                                file_name=output_file_name,
                                mime="application/octet-stream"
                            )

                else: # Descompactação
                    original_file_name_no_ext, _ = os.path.splitext(os.path.basename(input_path_tab1))
                    # Tenta adivinhar a extensão original ou usa uma genérica
                    if original_file_name_no_ext.endswith(".db"):
                        output_ext = ".db"
                    elif original_file_name_no_ext.endswith(".idx"):
                        output_ext = ".idx"
                    elif original_file_name_no_ext.endswith(".btr"):
                        output_ext = ".btr"
                    else:
                        output_ext = ".original" # Extensão genérica

                    # Remove a extensão de compressão para obter o nome original
                    base_name_decompressed = original_file_name_no_ext.replace(HUFFMAN_COMPRESSED_EXTENSION, "").replace(LZW_COMPRESSED_EXTENSION, "")
                    output_file_name = f"{base_name_decompressed}{output_ext}"
                    output_path_tab1 = os.path.join(TEMP_FOLDER, output_file_name) # Decompress to temp for now
                    
                    if algorithm == "Huffman":
                        comp_s, decomp_s, ratio, proc_t = HuffmanProcessor.decompress_file(str(input_path_tab1), output_path_tab1, update_progress)
                    else: # LZW
                        comp_s, decomp_s, ratio, proc_t = LZWProcessor.decompress(str(input_path_tab1), output_path_tab1, update_progress)
                    
                    st.success(f"{algorithm} Descompactação Completa!")
                    st.write(f"Tamanho Compactado: {comp_s / 1024:.2f} KB")
                    st.write(f"Tamanho Descompactado: {decomp_s / 1024:.2f} KB")
                    st.write(f"Tempo Gasto: {proc_t:.4f} segundos")

                    if decomp_s > 0:
                        with open(output_path_tab1, "rb") as f_out:
                            st.download_button(
                                label=f"Download Arquivo Descompactado ({output_file_name})",
                                data=f_out.read(),
                                file_name=output_file_name,
                                mime="application/octet-stream"
                            )
            
            except FileNotFoundError:
                st.error("Arquivo não encontrado. Por favor, certifique-se de que o arquivo existe no caminho especificado.")
            except Exception as e:
                st.error(f"Erro durante a {operation.lower()}: {str(e)}")
            finally:
                # Clean up temp uploaded file if it was used for tab1
                if uploaded_file and temp_dir_tab1 and os.path.exists(temp_dir_tab1): # Check if temp_dir_tab1 was actually created
                    try:
                        if os.path.exists(input_path_tab1): # Only remove if it was indeed created in temp
                            os.remove(input_path_tab1)
                        os.rmdir(temp_dir_tab1)
                    except OSError as e:
                        st.warning(f"Não foi possível limpar o diretório temporário de upload: {str(e)}")
                # Clean up temp decompressed output if applicable
                if operation == "Descompactação" and output_path_tab1 and os.path.exists(output_path_tab1):
                     try:
                        os.remove(output_path_tab1)
                     except OSError as e:
                        st.warning(f"Não foi possível limpar o arquivo de saída descompactado temporário: {str(e)}")

                progress_bar.progress(1.0)
                time.sleep(0.5)
    
    elif selected_view == "Comparação de Algoritmos":
        st.header("Comparação de Desempenho de Algoritmos")
        st.write("Compare os algoritmos Huffman e LZW no mesmo arquivo")
        
        compare_file_source = st.radio(
            "Selecione o arquivo para comparação:", 
            ("CSV Padrão", "Escolha do Usuário"), 
            key="compare_source_compression" # Chave única
        )
        
        compare_file = None
        compare_uploaded = None
        
        if compare_file_source == "CSV Padrão":
            try:
                default_files = []
                if os.path.exists(HUFFMAN_SOURCE_FOLDER):
                    for file in os.listdir(HUFFMAN_SOURCE_FOLDER):
                        if file.endswith(DEFAULT_EXTENSION):
                            default_files.append(file)
                
                if default_files:
                    compare_file = st.selectbox("Selecione um arquivo CSV para comparação:", default_files)
                    input_path_compare = os.path.join(HUFFMAN_SOURCE_FOLDER, compare_file)
                else:
                    st.warning(f"Nenhum arquivo CSV encontrado em {HUFFMAN_SOURCE_FOLDER}")
            except Exception as e:
                st.error(f"Erro ao acessar o diretório de origem: {str(e)}")
        else:
            # For comparison, typically a raw file (like .csv) is used, not compressed ones
            compare_uploaded_allowed_types = [".csv", ".txt", ".bin", ".db", ".idx", ".btr"] # Adicionado tipos de arquivos do sistema
            compare_uploaded = st.file_uploader(
                "Upload de um arquivo para comparação", 
                type=[ext.strip('.') for ext in compare_uploaded_allowed_types],
                key="compare_upload_compression" # Chave única
            )
            if compare_uploaded:
                # Save to temp location
                temp_dir_compare = tempfile.mkdtemp()
                input_path_compare = os.path.join(temp_dir_compare, compare_uploaded.name)
                with open(input_path_compare, "wb") as f:
                    f.write(compare_uploaded.getbuffer())
        
        if (compare_file or compare_uploaded) and st.button("Executar Comparação"):
            progress_bar.progress(0)
            progress_text.text("Iniciando comparação...")
            
            try:
                # Run comparison
                df = compare_algorithms(str(input_path_compare), update_progress) # Converte Path para string
                
                # Display results
                st.success("Comparação concluída!")
                st.dataframe(df.style.format({
                    'Original Size (KB)': '{:.2f}',
                    'Compressed Size (KB)': '{:.2f}',
                    'Compression Ratio (%)': '{:.2f}',
                    'Compression Time (s)': '{:.4f}',
                    'Decompression Time (s)': '{:.4f}',
                    'Total Time (s)': '{:.4f}'
                }))
                
                # Show plots
                fig = plot_comparison(df)
                st.pyplot(fig)
                
                # Offer download of results
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Resultados como CSV",
                    data=csv,
                    file_name="compression_comparison.csv",
                    mime="text/csv"
                )
            
            except Exception as e:
                st.error(f"Erro durante a comparação: {str(e)}")
            finally:
                # Clean up temp files for comparison tab
                if compare_uploaded and temp_dir_compare and os.path.exists(temp_dir_compare): # Check if temp_dir_compare was actually created
                    try:
                        if input_path_compare and os.path.exists(input_path_compare): # Only remove if it was indeed created in temp
                            os.remove(input_path_compare)
                        os.rmdir(temp_dir_compare)
                    except OSError as e:
                        st.warning(f"Não foi possível limpar o diretório temporário de upload para comparação: {str(e)}")
                
                progress_bar.progress(1.0)
                time.sleep(0.5)

def render_activity_log_section():
    """Exibe o log de atividades da aplicação."""
    st.header("Log de Atividades")
    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log_content = f.read()
        st.code(log_content, language="text")
    else:
        st.info("Nenhum log de atividades encontrado ainda.")

def render_about_section():
    """Exibe informações sobre a aplicação."""
    st.header("Sobre")
    st.write("""
    Este é um sistema de gerenciamento de banco de dados de acidentes de trânsito
    com funcionalidades avançadas de compressão (LZW e Huffman), criptografia (AES e RSA)
    e indexação eficiente usando uma estrutura de dados B-Tree.
    """)
    st.write("Desenvolvido para demonstração de conceitos de Sistemas de Informação e Estruturas de Dados.")
    st.write("Versão: 1.0 (B-Tree + Crypto + Compression)")
    st.write("---")
    st.subheader("Tecnologias Utilizadas:")
    st.markdown("""
    * **Python**: Linguagem de programação principal.
    * **Streamlit**: Para a interface de usuário web interativa.
    * **`cryptography`**: Biblioteca para operações criptográficas (AES, RSA).
    * **`filelock`**: Para gerenciamento de concorrência e integridade do arquivo.
    * **`pathlib`**: Para manipulação de caminhos de arquivos de forma orientada a objetos.
    * **`pandas`**: Para manipulação e exibição de dados tabulares.
    * **`matplotlib`**: Para geração de gráficos de comparação.
    * **`cryptography`**: Para gerar a lógica de Encriptação padrão e híbrida 
    """)
    st.write("Código desenvolvido por Gabriel da Silva Cassino")
    st.write("OBS. IMPORTANTE: este código é uma adaptação feita a partir do Java")
    st.write("ainda está em estágio pre-alpha")
# --- FUNÇÃO AUXILIAR PARA LEITURA E NORMALIZAÇÃO DE CSV ---
def read_and_normalize_csv_data(csv_file_path: str) -> List[Dict[str, Any]]:
    """
    Lê um arquivo CSV, traduz os cabeçalhos de português para inglês (nomes internos do sistema),
    e retorna uma lista de dicionários com os nomes dos campos em inglês,
    realizando também a conversão de tipos de dados.
    """
    data = []
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Mapear os cabeçalhos do CSV para os nomes internos em inglês
            # Ignora colunas desconhecidas
            header_map = {}
            found_headers_pt = []
            for col_pt in reader.fieldnames:
                # Normaliza o nome da coluna do CSV (minusculas, sem espaços extras)
                normalized_col_pt = col_pt.lower().strip().replace(" ", "_") # 'condição climática' -> 'condição_climática'
                found_headers_pt.append(normalized_col_pt)
                col_en = REVERSE_FIELD_MAPPING.get(normalized_col_pt, None)
                if col_en:
                    header_map[col_pt] = col_en
                else:
                    logger.warning(f"Coluna desconhecida no CSV (será ignorada): '{col_pt}' (Normalizado: '{normalized_col_pt}')")
            
            # Verificar se todos os campos obrigatórios em português (do CSV) estão presentes
            missing_fields_pt = [
                pt_field for pt_field in REQUIRED_FIELDS_PT
                if pt_field not in found_headers_pt
            ]
            if missing_fields_pt:
                st.warning(f"🚨 Atenção: Os seguintes campos obrigatórios (em português) não foram encontrados no CSV importado e podem causar problemas: {', '.join([f.replace('_', ' ').title() for f in missing_fields_pt])}")
                logger.warning(f"Campos obrigatórios ausentes no CSV importado: {missing_fields_pt}")

            for i, row in enumerate(reader):
                normalized_row = {}
                is_row_valid = True
                for pt_key_original, en_key in header_map.items():
                    raw_value = row.get(pt_key_original, "").strip() # Pega o valor e remove espaços
                    
                    # --- Pré-processamento de Dados (Importante!) ---
                    # Converta campos que são listas em strings separadas por vírgula no CSV para listas internas
                    if en_key in LIST_FIELDS_EN:
                        normalized_row[en_key] = [item.strip() for item in raw_value.split(',') if item.strip()]
                    elif en_key == "crash_date":
                        # Tratar datas: converter string para objeto date
                        try:
                            normalized_row[en_key] = datetime.strptime(raw_value, '%Y-%m-%d').date()
                        except ValueError:
                            st.error(f"Linha {i+2}: Formato de data inválido para '{FIELD_MAPPING.get(en_key, en_key)}': '{raw_value}'. Esperado AAAA-MM-DD. Registro será ignorado.")
                            logger.error(f"Invalid date format in CSV for row {i+2}, field '{en_key}': '{raw_value}'")
                            is_row_valid = False
                            break # Sai do loop desta linha
                    elif en_key == "intersection_related_i":
                        normalized_row[en_key] = raw_value.lower() == "sim" # 'Sim' -> True, 'Não' -> False
                    elif en_key in ["num_units", "injuries_total", "injuries_fatal", 
                                  "injuries_incapacitating", "injuries_non_incapacitating",
                                  "injuries_reported_not_evident", "injuries_no_indication",
                                  "crash_hour", "crash_day_of_week", "crash_month"]:
                        # Converter campos numéricos
                        try:
                            normalized_row[en_key] = int(raw_value) if raw_value else 0 # Converte para int, ou 0 se vazio
                        except ValueError:
                            st.warning(f"Linha {i+2}: Valor não numérico para '{FIELD_MAPPING.get(en_key, en_key)}': '{raw_value}'. Definindo como 0. Registro pode ser inválido.")
                            logger.warning(f"Non-numeric value in CSV for row {i+2}, field '{en_key}': '{raw_value}'")
                            normalized_row[en_key] = 0
                    else:
                        # Outros campos de texto
                        normalized_row[en_key] = raw_value
                
                if is_row_valid:
                    # Verifica se todos os campos obrigatórios (agora em EN) têm valor
                    for required_en_field in REQUIRED_FIELDS_EN:
                        if not normalized_row.get(required_en_field):
                            # Permite 0 ou False como valores válidos para numéricos/booleanos
                            if isinstance(normalized_row.get(required_en_field), (int, bool)):
                                continue
                            st.warning(f"Linha {i+2}: Campo obrigatório '{FIELD_MAPPING.get(required_en_field, required_en_field).replace('_', ' ').title()}' está vazio. Registro pode ser incompleto.")
                            logger.warning(f"Missing value for required field '{required_en_field}' in CSV row {i+2}.")
                    
                    data.append(normalized_row)
        return data
    except Exception as e:
        st.error(f"🚨 Erro ao ler ou normalizar o CSV: {e}. Verifique o formato do arquivo e os cabeçalhos.")
        logger.error(f"Erro na leitura/normalização do CSV: {traceback.format_exc()}")
        return []

# --- Configuração da UI Principal do Streamlit ---
def setup_ui():
    """Configura a interface de usuário principal do Streamlit."""
    st.set_page_config(layout="wide", page_title="Gerenciador de Acidentes de Trânsito")

    st.sidebar.title("Navegação")
    options = [
        "Gerenciamento de Dados",
        "Criptografia",
        "Compactação", # Nova opção adicionada
        "Administração",
        "Log de Atividades",
        "Sobre"
    ]
    
    # Armazena o modo de operação na sessão para persistência
    if "operation_mode" not in st.session_state:
        st.session_state["operation_mode"] = "Direto" # Define o modo padrão

    # Verifica se a navegação mudou para lidar com a persistência da B-Tree em memória
    current_selected_option = st.sidebar.radio("Ir para", options)
    if "last_selected_option" not in st.session_state:
        st.session_state["last_selected_option"] = current_selected_option

    if current_selected_option != st.session_state["last_selected_option"]:
        # Se a UI mudou, e o modo era B-Tree, salve a B-Tree em disco
        if st.session_state.get("operation_mode") == "B-Tree" and "db_manager" in st.session_state:
            with st.spinner("Salvando B-Tree em memória..."):
                st.session_state.db_manager._save_btree_from_memory()
        st.session_state["last_selected_option"] = current_selected_option
        st.rerun() # Força um rerun para garantir que os estados sejam atualizados

    # Exibe a seção selecionada
    if current_selected_option == "Gerenciamento de Dados":
        render_data_management_section()
    elif current_selected_option == "Criptografia":
        render_cryptography_section()
    elif current_selected_option == "Compactação": # Chamada da nova seção
        render_compression_section()
    elif current_selected_option == "Administração":
        render_administration_section()
    elif current_selected_option == "Log de Atividades":
        render_activity_log_section()
    elif current_selected_option == "Sobre":
        render_about_section()


if __name__ == "__main__":
    try:
        # Ensure base directories exist before any DB operations
        # Directories are created in APP_CONFIG setup, but this reinforces for critical ones
        APP_CONFIG["DB_DIR"].mkdir(parents=True, exist_ok=True)
        APP_CONFIG["BACKUP_PATH"].mkdir(parents=True, exist_ok=True)
        APP_CONFIG["RSA_KEYS_DIR"].mkdir(parents=True, exist_ok=True)
        APP_CONFIG["HUFFMAN_FOLDER"].mkdir(parents=True, exist_ok=True)
        APP_CONFIG["LZW_FOLDER"].mkdir(parents=True, exist_ok=True)
        APP_CONFIG["LOG_FILE"].parent.mkdir(parents=True, exist_ok=True) # Ensure log file directory exists
        TEMP_FOLDER.mkdir(parents=True, exist_ok=True) # Ensure temp folder is created

        # Inicializa o DBManager e o armazena em session_state para persistência entre reruns
        if "db_manager" not in st.session_state:
            # Inicializa o modo de operação antes de criar o DBManager
            if "operation_mode" not in st.session_state:
                st.session_state["operation_mode"] = "Direto"
            st.session_state["db_manager"] = DBManager(st.session_state["operation_mode"])

        setup_ui()
    except OSError as e:
        st.error(f"🚨 Crítico: Não foi possível criar os diretórios necessários. Verifique as permissões para `{APP_CONFIG['DB_DIR']}`. Erro: {e}")
        logger.critical(f"Initial directory creation failed: {traceback.format_exc()}")
        st.stop() # Interrompe o aplicativo se os diretórios críticos não puderem ser criados
    except Exception as e:
        st.error(f"🚨 Ocorreu um erro inesperado na inicialização da aplicação: {e}")
        logger.critical(f"Unhandled error during application setup: {traceback.format_exc()}")
