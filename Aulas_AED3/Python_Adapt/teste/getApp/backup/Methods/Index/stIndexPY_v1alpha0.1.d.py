# -*- coding: utf-8 -*-

"""
Gerenciador de Banco de Dados de Acidentes de Trânsito Aprimorado e Otimizado

Este script é uma fusão e melhoria de múltiplos arquivos Python, integrando:
- stCRUDDataObjectPY_v3alpha.py (Base da UI)
- stCRUDDataObjectPY_v4epsilon.py (Configuração e Indexação)
- stCRUDDataObjectPY_v5alpha0.1.e.py (DataObject e Classe DB Robusta)
- stCRUDDataObjectPY_v5alpha0.2.a.py (Implementação da Árvore B - Placeholder)
- stHuffman_v5.py (Compressão Huffman - Placeholder)
- stLZWPY_v4.py (Compressão LZW - Placeholder)
- AES_RSA.py / pycryptonew.py (Funções de Criptografia)

O resultado é uma aplicação Streamlit completa e rica em recursos que oferece:
- Escolha entre um banco de dados padrão baseado em arquivo/índice e um motor baseado em B-Tree (placeholder).
- Um DataObject robusto com validação extensiva, incluindo tratamento para campos de lista.
- Funcionalidade CRUD completa (Criar, Ler, Atualizar, Deletar).
- Importação/exportação em massa via CSV.
- Capacidades de backup e restauração do banco de dados.
- Utilitários integrados de compressão/descompressão de arquivos (Huffman & LZW - Placeholder).
- Funções de criptografia/descriptografia híbrida (AES + RSA).
- Um log de atividades e funções administrativas.
- Interface de usuário aprimorada com navegação.
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
import getpass # Import para entrada de senha (usado em operações de criptografia)
import pickle # Necessário para serialização/deserialização de DataObject
import copy # Necessário para copiar DataObject antes de serializar

# --- Cryptography Imports from pycryptonew.py (Adaptado) ---
# A biblioteca PyCryptodome é a mais comum para estes módulos
try:
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
    from Crypto.Util.Padding import pad, unpad
    CRYPTOGRAPHY_BACKEND_PYCRYPTODOME = True
except ImportError:
    st.warning("PyCryptodome não encontrado. Criptografia pode não funcionar. Usando cryptography.hazmat fallback.")
    CRYPTOGRAPHY_BACKEND_PYCRYPTODOME = False
    # Fallback para cryptography.hazmat se pycryptodome não estiver disponível
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend


# --- Configuration Constants (Centralized - from v4epsilon) ---
APP_CONFIG = {
    "DB_DIR": os.path.join(Path.home(), 'Documents', 'Data'),
    "DB_FILE_NAME": 'traffic_accidents.db',
    "BTREE_INDEX_FILE_NAME": 'traffic_accidents.idx',
    "ID_COUNTER_FILE_NAME": 'id_counter.dat',
    "LOCK_FILE_NAME": 'db_lock.lock',
    "LOG_FILE_NAME": 'app_activity.log',
    "RSA_KEYS_DIR": os.path.join(Path.home(), 'Documents', 'RSA_Keys'),
    "PUBLIC_KEY_FILE": 'public_key.pem',
    "PRIVATE_KEY_FILE": 'private_key.pem',
    "BTREE_PAGE_SIZE": 4096,  # Em bytes
    "BTREE_MIN_DEGREE": 3,   # t no algoritmo B-tree (2t-1 é o número máx de chaves)
    "MAX_FILE_SIZE_MB": 100, # Limite para arquivos de backup/exportação
    "CHUNK_SIZE": 4096      # Tamanho dos chunks para leitura/escrita
}

BACKUP_PATH = os.path.join(APP_CONFIG["DB_DIR"], 'backups')
LOG_FILE_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOG_FILE_NAME"])
RSA_PUBLIC_KEY_PATH = os.path.join(APP_CONFIG["RSA_KEYS_DIR"], APP_CONFIG["PUBLIC_KEY_FILE"])
RSA_PRIVATE_KEY_PATH = os.path.join(APP_CONFIG["RSA_KEYS_DIR"], APP_CONFIG["PRIVATE_KEY_FILE"])

# --- Logging Configuration (from v4epsilon) ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Remova qualquer handler existente para evitar duplicação
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Streamlit logger (optional, for displaying logs in Streamlit UI)
st_logger = logging.getLogger('streamlit')
st_logger.addHandler(file_handler) # Add to same file as main logger

# --- Global State Management ---
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'db' not in st.session_state:
    st.session_state.db = None # Will hold an instance of DBManager or BTreeManager
if 'encryption_key' not in st.session_state:
    st.session_state.encryption_key = None
if 'db_type' not in st.session_state:
    st.session_state.db_type = "Arquivo/Índice Padrão" # Default DB type

# --- Constantes para o Formato do Arquivo DB (da classe DataObject, ajustadas) ---
DB_HEADER_SIZE = 4
RECORD_METADATA_SIZE = 4 + 1 + 4 # ID (4 bytes), is_valid (1 byte), record_size (4 bytes)

# --- Adaptação do DataObject (versão final da nossa conversa) ---
StringOrStringList = Union[str, List[str]]

class DataObject:
    def __init__(self,
                 crash_date: datetime,
                 traffic_control_device: str,
                 weather_condition: str,
                 lighting_condition: StringOrStringList,
                 first_crash_type: str,
                 trafficway_type: str,
                 alignment: str,
                 roadway_surface_cond: str,
                 road_defect: str,
                 crash_type: StringOrStringList,
                 intersection_related_i: str,
                 damage: str,
                 prim_contributory_cause: str,
                 num_units: int,
                 most_severe_injury: StringOrStringList,
                 injuries_total: float,
                 injuries_fatal: float,
                 injuries_incapacitating: float,
                 injuries_non_incapacitating: float,
                 injuries_reported_not_eviden: float,
                 injuries_no_indication: float,
                 crash_hour: int,
                 crash_day_of_week: int,
                 crash_month: int,
                 id: Optional[int] = None):
        self.crash_date = crash_date
        self.traffic_control_device = traffic_control_device
        self.weather_condition = weather_condition
        self.lighting_condition = lighting_condition
        self.first_crash_type = first_crash_type
        self.trafficway_type = trafficway_type
        self.alignment = alignment
        self.roadway_surface_cond = roadway_surface_cond
        self.road_defect = road_defect
        self.crash_type = crash_type
        self.intersection_related_i = intersection_related_i
        self.damage = damage
        self.prim_contributory_cause = prim_contributory_cause
        self.num_units = num_units
        self.most_severe_injury = most_severe_injury
        self.injuries_total = injuries_total
        self.injuries_fatal = injuries_fatal
        self.injuries_incapacitating = injuries_incapacitating
        self.injuries_non_incapacitating = injuries_non_incapacitating
        self.injuries_reported_not_eviden = injuries_reported_not_eviden
        self.injuries_no_indication = injuries_no_indication
        self.crash_hour = crash_hour
        self.crash_day_of_week = crash_day_of_week
        self.crash_month = crash_month
        self.id = id

    def __repr__(self):
        # A representação de string de listas deve ser explícita
        lighting_condition_repr = repr(self.lighting_condition)
        crash_type_repr = repr(self.crash_type)
        most_severe_injury_repr = repr(self.most_severe_injury)

        return (f"DataObject(id={self.id}, crash_date={self.crash_date!r}, "
                f"traffic_control_device={self.traffic_control_device!r}, "
                f"weather_condition={self.weather_condition!r}, "
                f"lighting_condition={lighting_condition_repr}, "
                f"crash_type={crash_type_repr}, "
                f"most_severe_injury={most_severe_injury_repr}, "
                f"num_units={self.num_units}, "
                f"injuries_total={self.injuries_total})")

    # --- Atributos que devem ter a conversão de string para lista (na leitura) ---
    _LIST_CONVERTIBLE_STRING_FIELDS = {
        "lighting_condition",
        "crash_type",
        "most_severe_injury"
    }

    # --- NOVA FUNÇÃO para transformar lista em string para serialização ---
    @staticmethod
    def _convert_list_to_string_for_serialization(value: StringOrStringList) -> str:
        """
        Converte uma lista de strings em uma única string delimitada por ' , '.
        Se a lista tiver apenas um item, retorna esse item.
        Se já for uma string, retorna a própria string.
        """
        if isinstance(value, list):
            if len(value) > 1:
                return " , ".join(value)
            elif len(value) == 1:
                return value[0]
            else: # Lista vazia
                return ""
        return value # Se já é uma string, retorna como está

    # --- Função auxiliar para processar strings com delimitadores (na leitura) ---
    @staticmethod
    def _process_delimited_string(value: str) -> StringOrStringList:
        """
        Converte uma string em lista de strings se contiver ',' ou '/'.
        Remove espaços em branco e elementos vazios após a divisão.
        """
        if isinstance(value, str):
            if ',' in value:
                return [s.strip() for s in value.split(',') if s.strip()]
            elif '/' in value:
                return [s.strip() for s in value.split('/') if s.strip()]
        return value

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'DataObject':
        _id = data_dict.pop('id', None)
        
        def convert_value(key, value):
            if key == 'crash_date':
                if isinstance(value, str):
                    try:
                        return datetime.strptime(value, "%m/%d/%Y %I:%M:%S %p")
                    except ValueError:
                        raise ValueError(f"Formato de data inválido para 'crash_date': '{value}'")
                elif isinstance(value, datetime):
                    return value
                else:
                    raise TypeError(f"Tipo inválido para 'crash_date': esperado str ou datetime, obteve {type(value)}")
            elif key in ['num_units', 'crash_hour', 'crash_day_of_week', 'crash_month']:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Valor inválido para '{key}': '{value}'. Esperado um número inteiro.")
            # Adaptação para o nome correto do campo injuries_reported_not_eviden
            elif key in ['injuries_total', 'injuries_fatal', 'injuries_incapacitating',
                          'injuries_non_incapacitating', 'injuries_reported_not_eviden',
                          'injuries_no_indication']:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Valor inválido para '{key}': '{value}'. Esperado um número decimal.")
            else:
                if key in DataObject._LIST_CONVERTIBLE_STRING_FIELDS:
                    return DataObject._process_delimited_string(str(value))
                return str(value)

        processed_data = {}
        for key in data_dict:
            try:
                processed_data[key] = convert_value(key, data_dict[key])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Erro ao processar campo '{key}' no dicionário: {e}")

        # Renomeia a chave se vier como 'injuries_reported_not_evident' para 'injuries_reported_not_eviden'
        if 'injuries_reported_not_evident' in processed_data and 'injuries_reported_not_eviden' not in processed_data:
            processed_data['injuries_reported_not_eviden'] = processed_data.pop('injuries_reported_not_evident')

        return cls(id=_id, **processed_data)


    @classmethod
    def from_csv_line(cls, line: str, header: list[str]) -> 'DataObject':
        values = line.strip().split(';')
        if len(values) != len(header):
            raise ValueError(
                f"O número de valores na linha ({len(values)}) não corresponde "
                f"ao número de cabeçalhos ({len(header)}). Linha: '{line}'"
            )

        raw_data_dict = dict(zip(header, values))
        processed_data = {}

        converters = {
            'crash_date': lambda x: datetime.strptime(x, "%m/%d/%Y %I:%M:%S %p"),
            'num_units': int,
            'injuries_total': float,
            'injuries_fatal': float,
            'injuries_incapacitating': float,
            'injuries_non_incapacitating': float,
            'injuries_reported_not_eviden': float, # Nome correto do atributo
            'injuries_no_indication': float,
            'crash_hour': int,
            'crash_day_of_week': int,
            'crash_month': int,
        }

        for key in header:
            value = raw_data_dict.get(key)
            if value is None:
                raise ValueError(f"Campo '{key}' faltando na linha CSV: '{line}'")

            try:
                if key in converters:
                    processed_data[key] = converters[key](value)
                else:
                    if key in DataObject._LIST_CONVERTIBLE_STRING_FIELDS:
                        processed_data[key] = DataObject._process_delimited_string(value)
                    else:
                        processed_data[key] = value
            except ValueError as e:
                raise ValueError(f"Falha na conversão de tipo para '{key}': valor '{value}' inválido. Detalhe: {e}")
            except Exception as e:
                raise Exception(f"Erro inesperado ao processar '{key}' da linha CSV: {e}")

        if not (0 <= processed_data.get('crash_hour', -1) <= 23):
             raise ValueError(f"Hora do acidente inválida: {processed_data.get('crash_hour')}. Deve ser entre 0 e 23.")
        if not (1 <= processed_data.get('crash_day_of_week', -1) <= 7):
             raise ValueError(f"Dia da semana inválido: {processed_data.get('crash_day_of_week')}. Deve ser entre 1 e 7.")
        if not (1 <= processed_data.get('crash_month', -1) <= 12):
             raise ValueError(f"Mês inválido: {processed_data.get('crash_month')}. Deve ser entre 1 e 12.")
        
        return cls(**processed_data)

# --- Mapping para cabeçalho do CSV (Português para Inglês) ---
PORTUGUESE_TO_ENGLISH_HEADER_MAP = {
    "data_do_acidente": "crash_date",
    "dispositivo_de_controle_de_tráfego": "traffic_control_device",
    "condição_climática": "weather_condition",
    "condição_de_iluminação": "lighting_condition",
    "tipo_primeiro_acidente": "first_crash_type",
    "tipo_de_via_de_trânsito": "trafficway_type",
    "alinhamento": "alignment",
    "condição_da_superfície_da_estrada": "roadway_surface_cond",
    "defeito_da_estrada": "road_defect",
    "tipo_do_acidente": "crash_type",
    "i.e. relacionados_ao_interseção": "intersection_related_i",
    "dano": "damage",
    "causa_contributiva_primária": "prim_contributory_cause",
    "n.º_de_unidades": "num_units",
    "ferimento_mais_grave": "most_severe_injury",
    "total_de_ferimentos": "injuries_total",
    "ferimento_fatal": "injuries_fatal",
    "ferimento_incapacitante": "injuries_incapacitating",
    "ferimento_não_incapacitante": "injuries_non_incapacitating",
    "ferimento_relatado_não_evidente": "injuries_reported_not_eviden", # NOME DO ATRIBUTO
    "ferimento_sem_indicação": "injuries_no_indication",
    "hora_do_acidente": "crash_hour",
    "dia_da_semana_do_acidente": "crash_day_of_week",
    "mês_do_acidente": "crash_month"
}

# O cabeçalho em português que será comparado
PORTUGUESE_HEADER_EXPECTED_STR = ";".join(PORTUGUESE_TO_ENGLISH_HEADER_MAP.keys())
PORTUGUESE_HEADER_EXPECTED_LIST = list(PORTUGUESE_TO_ENGLISH_HEADER_MAP.keys())

# O cabeçalho em inglês que a classe DataObject espera
ENGLISH_HEADER_FOR_DATAOBJECT = list(PORTUGUESE_TO_ENGLISH_HEADER_MAP.values())


# --- Classes de Suporte (DBManager, BTreeManager, CryptographyHandler, etc.) ---

class CryptographyHandler:
    @staticmethod
    def generate_rsa_keys(private_key_path: str, public_key_path: str, password: str) -> bool:
        try:
            # Generate RSA key pair
            key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            # Encrypt private key with AES256
            private_pem = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
            )

            public_pem = key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Save keys to files
            Path(private_key_path).parent.mkdir(parents=True, exist_ok=True)
            with open(private_key_path, "wb") as f:
                f.write(private_pem)
            with open(public_key_path, "wb") as f:
                f.write(public_pem)
            
            logger.info(f"RSA keys generated and saved to {private_key_path} and {public_key_path}")
            return True
        except Exception as e:
            logger.error(f"Error generating RSA keys: {traceback.format_exc()}")
            st.error(f"Erro ao gerar chaves RSA: {e}")
            return False

    @staticmethod
    def load_public_key(public_key_path: str):
        try:
            with open(public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
            return public_key
        except Exception as e:
            logger.error(f"Error loading public key: {traceback.format_exc()}")
            st.error(f"Erro ao carregar chave pública: {e}")
            return None

    @staticmethod
    def load_private_key(private_key_path: str, password: str):
        try:
            with open(private_key_path, "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), password.encode('utf-8'), backend=default_backend())
            return private_key
        except Exception as e:
            logger.error(f"Error loading private key: {traceback.format_exc()}")
            st.error(f"Erro ao carregar chave privada. Verifique a senha. Detalhes: {e}")
            return None
    
    @staticmethod
    def hybrid_encrypt_file(input_filepath: str, output_filepath: str, public_key_path: str) -> bool:
        try:
            public_key = CryptographyHandler.load_public_key(public_key_path)
            if not public_key:
                return False

            # Generate a random AES key
            aes_key = os.urandom(32) # 256-bit key

            # Encrypt AES key with RSA public key
            if CRYPTOGRAPHY_BACKEND_PYCRYPTODOME:
                rsa_public_key = RSA.import_key(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
                cipher_rsa = PKCS1_OAEP.new(rsa_public_key)
                encrypted_aes_key = cipher_rsa.encrypt(aes_key)
            else:
                encrypted_aes_key = public_key.encrypt(
                    aes_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

            # Encrypt data with AES
            with open(input_filepath, 'rb') as f:
                plaintext = f.read()

            if CRYPTOGRAPHY_BACKEND_PYCRYPTODOME:
                cipher_aes = AES.new(aes_key, AES.MODE_CBC)
                ciphertext = cipher_aes.encrypt(pad(plaintext, AES.block_size))
                iv = cipher_aes.iv
            else:
                iv = os.urandom(16)
                cipher_aes = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
                encryptor = cipher_aes.encryptor()
                # padding manual, pois cryptography.hazmat não tem pad() nativo como PyCryptodome
                padder = padding.PKCS7(algorithms.AES.block_size).padder()
                padded_plaintext = padder.update(plaintext) + padder.finalize()
                ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

            # Write encrypted AES key, IV, and ciphertext to output file
            with open(output_filepath, 'wb') as f:
                f.write(struct.pack('<I', len(encrypted_aes_key))) # Size of RSA encrypted AES key
                f.write(encrypted_aes_key)
                f.write(struct.pack('<I', len(iv))) # Size of IV
                f.write(iv)
                f.write(ciphertext)
            
            logger.info(f"File '{input_filepath}' encrypted to '{output_filepath}' using hybrid AES/RSA.")
            return True
        except Exception as e:
            logger.error(f"Error encrypting file '{input_filepath}': {traceback.format_exc()}")
            st.error(f"Erro ao criptografar arquivo: {e}")
            return False

    @staticmethod
    def hybrid_decrypt_file(input_filepath: str, output_filepath: str, private_key_path: str, password: str) -> bool:
        try:
            private_key = CryptographyHandler.load_private_key(private_key_path, password)
            if not private_key:
                return False

            with open(input_filepath, 'rb') as f:
                encrypted_aes_key_len = struct.unpack('<I', f.read(4))[0]
                encrypted_aes_key = f.read(encrypted_aes_key_len)
                iv_len = struct.unpack('<I', f.read(4))[0]
                iv = f.read(iv_len)
                ciphertext = f.read()

            # Decrypt AES key with RSA private key
            if CRYPTOGRAPHY_BACKEND_PYCRYPTODOME:
                rsa_private_key = RSA.import_key(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
                cipher_rsa = PKCS1_OAEP.new(rsa_private_key)
                aes_key = cipher_rsa.decrypt(encrypted_aes_key)
            else:
                aes_key = private_key.decrypt(
                    encrypted_aes_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

            # Decrypt data with AES
            if CRYPTOGRAPHY_BACKEND_PYCRYPTODOME:
                cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
                plaintext = unpad(cipher_aes.decrypt(ciphertext), AES.block_size)
            else:
                cipher_aes = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
                decryptor = cipher_aes.decryptor()
                padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
                unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
                plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()


            with open(output_filepath, 'wb') as f:
                f.write(plaintext)
            
            logger.info(f"File '{input_filepath}' decrypted to '{output_filepath}' using hybrid AES/RSA.")
            return True
        except Exception as e:
            logger.error(f"Error decrypting file '{input_filepath}': {traceback.format_exc()}")
            st.error(f"Erro ao descriptografar arquivo: {e}")
            return False

    @staticmethod
    def blowfish_encrypt_file():
        st.warning("Função Blowfish de criptografia é um placeholder e não possui implementação completa.")

    @staticmethod
    def blowfish_decrypt_file():
        st.warning("Função Blowfish de descriptografia é um placeholder e não possui implementação completa.")


class HuffmanCompression:
    @staticmethod
    def build_huffman_tree(data):
        frequency = Counter(data)
        heap = [[weight, [symbol, ""]] for symbol, weight in frequency.items()]
        heapq.heapify(heap)
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
        return sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]), p))

    @staticmethod
    def huffman_compress_file(input_filepath: str, output_filepath: str) -> bool:
        try:
            with open(input_filepath, 'rb') as f:
                data = f.read()

            huffman_tree = HuffmanCompression.build_huffman_tree(data)
            huffman_codes = {symbol: code for symbol, code in huffman_tree}

            # Encode data
            encoded_data = "".join(huffman_codes[byte_val] for byte_val in data)

            # Pad encoded data to be a multiple of 8 bits
            padding_len = 8 - (len(encoded_data) % 8)
            if padding_len == 8: # If already a multiple of 8
                padding_len = 0
            encoded_data += '0' * padding_len # Pad with zeros

            # Convert bit string to byte array
            byte_array = bytearray()
            for i in range(0, len(encoded_data), 8):
                byte_array.append(int(encoded_data[i:i+8], 2))

            # Store header (padding_len, tree_size, tree)
            # Tree format: List of (symbol, code_string)
            tree_json = json.dumps(huffman_tree).encode('utf-8')
            tree_size = len(tree_json)

            with open(output_filepath, 'wb') as f:
                f.write(struct.pack('<I', padding_len))
                f.write(struct.pack('<I', tree_size))
                f.write(tree_json)
                f.write(byte_array)
            
            logger.info(f"File '{input_filepath}' compressed to '{output_filepath}' using Huffman.")
            return True
        except Exception as e:
            logger.error(f"Error compressing file '{input_filepath}' with Huffman: {traceback.format_exc()}")
            st.error(f"Erro ao comprimir arquivo com Huffman: {e}")
            return False

    @staticmethod
    def huffman_decompress_file(input_filepath: str, output_filepath: str) -> bool:
        try:
            with open(input_filepath, 'rb') as f:
                padding_len = struct.unpack('<I', f.read(4))[0]
                tree_size = struct.unpack('<I', f.read(4))[0]
                tree_json = f.read(tree_size).decode('utf-8')
                compressed_bytes = f.read()

            huffman_tree = json.loads(tree_json)
            # Rebuild code -> symbol map
            huffman_codes_reverse = {code: symbol for symbol, code in huffman_tree}

            # Convert bytes back to bit string
            bit_string = "".join(f"{byte:08b}" for byte in compressed_bytes)
            
            # Remove padding
            if padding_len > 0:
                bit_string = bit_string[:-padding_len]

            # Decode data
            decoded_data = bytearray()
            current_code = ""
            for bit in bit_string:
                current_code += bit
                if current_code in huffman_codes_reverse:
                    decoded_data.append(huffman_codes_reverse[current_code])
                    current_code = ""

            with open(output_filepath, 'wb') as f:
                f.write(decoded_data)
            
            logger.info(f"File '{input_filepath}' decompressed to '{output_filepath}' using Huffman.")
            return True
        except Exception as e:
            logger.error(f"Error decompressing file '{input_filepath}' with Huffman: {traceback.format_exc()}")
            st.error(f"Erro ao descomprimir arquivo com Huffman: {e}")
            return False


class LZWCompression:
    @staticmethod
    def lzw_compress_file(input_filepath: str, output_filepath: str) -> bool:
        try:
            with open(input_filepath, 'rb') as f:
                data = f.read()

            dictionary_size = 256
            dictionary = {bytes([i]): i for i in range(dictionary_size)}
            w = b""
            result = []
            for byte in data:
                wc = w + bytes([byte])
                if wc in dictionary:
                    w = wc
                else:
                    result.append(dictionary[w])
                    # Add wc to dictionary.
                    dictionary[wc] = dictionary_size
                    dictionary_size += 1
                    w = bytes([byte])
            if w:
                result.append(dictionary[w])

            # Write compressed data as a list of integers
            # Convert integers to bytes, for simplicity pack as unsigned shorts
            compressed_bytes = struct.pack(f'<{len(result)}H', *result) # H for unsigned short (0 to 65535)

            with open(output_filepath, 'wb') as f:
                f.write(compressed_bytes)
            
            logger.info(f"File '{input_filepath}' compressed to '{output_filepath}' using LZW.")
            return True
        except Exception as e:
            logger.error(f"Error compressing file '{input_filepath}' with LZW: {traceback.format_exc()}")
            st.error(f"Erro ao comprimir arquivo com LZW: {e}")
            return False

    @staticmethod
    def lzw_decompress_file(input_filepath: str, output_filepath: str) -> bool:
        try:
            with open(input_filepath, 'rb') as f:
                compressed_bytes = f.read()

            # Unpack bytes back to list of integers
            # Determine how many unsigned shorts are in the byte string
            num_shorts = len(compressed_bytes) // struct.calcsize('H')
            compressed_data = struct.unpack(f'<{num_shorts}H', compressed_bytes)

            dictionary_size = 256
            dictionary = {i: bytes([i]) for i in range(dictionary_size)}
            
            result = io.BytesIO()
            w = bytes([compressed_data[0]])
            result.write(w)
            
            for k in compressed_data[1:]:
                if k in dictionary:
                    entry = dictionary[k]
                elif k == dictionary_size:
                    entry = w + bytes([w[0]])
                else:
                    raise ValueError('Bad compressed k: %s' % k)
                
                result.write(entry)
                dictionary[dictionary_size] = w + bytes([entry[0]])
                dictionary_size += 1
                w = entry
            
            with open(output_filepath, 'wb') as f:
                f.write(result.getvalue())
            
            logger.info(f"File '{input_filepath}' decompressed to '{output_filepath}' using LZW.")
            return True
        except Exception as e:
            logger.error(f"Error decompressing file '{input_filepath}' with LZW: {traceback.format_exc()}")
            st.error(f"Erro ao descomprimir arquivo com LZW: {e}")
            return False


# --- B-Tree Manager (Placeholder/Basic Implementation) ---
class BTreeNode:
    def __init__(self, t, is_leaf):
        self.t = t  # Minimum degree (t)
        self.keys = []
        self.children = []
        self.is_leaf = is_leaf

    def __repr__(self):
        return f"Node(keys={self.keys}, is_leaf={self.is_leaf})"

class BTreeManager:
    def __init__(self, db_dir, index_file_name, page_size, min_degree):
        self.index_filepath = os.path.join(db_dir, index_file_name)
        self.page_size = page_size
        self.t = min_degree # Minimum degree
        self.root = None # BTreeNode object
        self.next_node_id = 0 # To assign unique IDs to nodes for serialization

        # Load existing tree or create new one
        self._load_tree()

    def _allocate_node_id(self):
        """Assigns a unique ID to a new node for serialization."""
        node_id = self.next_node_id
        self.next_node_id += 1
        return node_id

    def _serialize_node(self, node: BTreeNode) -> bytes:
        """Serializes a BTreeNode to bytes, including its ID."""
        # For simplicity, using pickle for node serialization
        return pickle.dumps(node)

    def _deserialize_node(self, data: bytes) -> BTreeNode:
        """Deserializes bytes back to a BTreeNode."""
        return pickle.loads(data)

    def _load_tree(self):
        """Loads the B-tree from disk."""
        if os.path.exists(self.index_filepath):
            try:
                with open(self.index_filepath, 'rb') as f:
                    # Read tree metadata if any, then the root node
                    # For simple pickle, directly load the root
                    serialized_root_and_next_id = f.read()
                    if serialized_root_and_next_id:
                        root_data, self.next_node_id = pickle.loads(serialized_root_and_next_id)
                        self.root = self._deserialize_node(root_data) # Deserialize root node
                        logger.info(f"B-Tree loaded from {self.index_filepath}. Next Node ID: {self.next_node_id}")
                    else:
                        self._create_new_tree()
            except (EOFError, pickle.UnpicklingError, struct.error) as e:
                logger.error(f"Error loading B-Tree from {self.index_filepath}: {e}. Creating new tree.")
                self._create_new_tree()
            except Exception as e:
                logger.error(f"Unexpected error loading B-Tree: {traceback.format_exc()}")
                self._create_new_tree()
        else:
            self._create_new_tree()

    def _create_new_tree(self):
        """Initializes a new empty B-tree."""
        self.root = BTreeNode(self.t, True)
        self.next_node_id = 0 # Reset node IDs for a new tree
        self.root.id = self._allocate_node_id() # Assign ID to root
        self._save_tree()
        logger.info(f"New B-Tree created at {self.index_filepath}.")

    def _save_tree(self):
        """Saves the B-tree to disk."""
        try:
            # For simplicity, pickle the entire root node and next_node_id
            # In a real implementation, nodes would be saved individually
            # and referenced by their page/block offsets.
            serialized_root = self._serialize_node(self.root)
            with open(self.index_filepath, 'wb') as f:
                pickle.dump((serialized_root, self.next_node_id), f)
            logger.info(f"B-Tree saved to {self.index_filepath}.")
        except Exception as e:
            logger.error(f"Error saving B-Tree to {self.index_filepath}: {traceback.format_exc()}")
            st.error(f"Erro ao salvar árvore B: {e}")

    def insert(self, key: int, value_offset: int):
        """Inserts a key-value (ID-offset) pair into the B-tree."""
        # Placeholder for actual B-tree insert logic
        st.info(f"B-Tree: Inserindo chave {key} com offset {value_offset} (Placeholder)")
        # For this placeholder, we'll just add it to the root's keys/children lists
        # In a real B-tree, this would involve splitting nodes, etc.
        self.root.keys.append((key, value_offset))
        self.root.keys.sort() # Keep sorted for simplicity in placeholder
        self._save_tree()
        logger.info(f"B-Tree: Key {key} inserted (placeholder).")

    def search(self, key: int) -> Optional[int]:
        """Searches for a key and returns its value offset."""
        # Placeholder for actual B-tree search logic
        st.info(f"B-Tree: Buscando chave {key} (Placeholder)")
        for k, offset in self.root.keys:
            if k == key:
                return offset
        return None # Not found
    
    def delete(self, key: int):
        """Deletes a key from the B-tree."""
        # Placeholder for actual B-tree delete logic
        st.info(f"B-Tree: Deletando chave {key} (Placeholder)")
        self.root.keys = [(k, offset) for k, offset in self.root.keys if k != key]
        self._save_tree()
        logger.info(f"B-Tree: Key {key} deleted (placeholder).")

    def update(self, key: int, new_value_offset: int):
        """Updates the value offset for an existing key."""
        # Placeholder for actual B-tree update logic
        st.info(f"B-Tree: Atualizando chave {key} com novo offset {new_value_offset} (Placeholder)")
        found = False
        for i, (k, offset) in enumerate(self.root.keys):
            if k == key:
                self.root.keys[i] = (key, new_value_offset)
                found = True
                break
        if found:
            self._save_tree()
            logger.info(f"B-Tree: Key {key} updated (placeholder).")
        else:
            logger.warning(f"B-Tree: Key {key} not found for update (placeholder).")

    def get_all_keys(self) -> List[int]:
        """Returns all keys in the B-tree."""
        return [k for k, _ in self.root.keys] # Placeholder

    def get_all_records_offsets(self) -> List[Tuple[int, int]]:
        """Returns all (key, offset) pairs."""
        return sorted(self.root.keys) # Placeholder

    def get_total_records(self) -> int:
        return len(self.root.keys) # Placeholder


# --- DBManager (File-based DB with Index) ---
class DBManager:
    def __init__(self, db_filepath: str, index_filepath: str, id_counter_filepath: str, lock_filepath: str):
        self.db_filepath = db_filepath
        self.index_filepath = index_filepath
        self.id_counter_filepath = id_counter_filepath
        self.lock_filepath = lock_filepath
        self.index = self._load_index() # {id: (offset, size)}
        self.next_id = self._load_id_counter()
        self.lock = filelock.FileLock(self.lock_filepath)
        self._ensure_db_header()

    def _ensure_db_header(self):
        """Ensures the DB file has its initial ID counter header."""
        with self.lock:
            with open(self.db_filepath, 'a+b') as f: # Use a+b to create if not exists
                f.seek(0, os.SEEK_END)
                if f.tell() < DB_HEADER_SIZE:
                    f.seek(0)
                    f.write(struct.pack('<I', self.next_id)) # Write initial next_id

    def _load_index(self) -> Dict[int, Tuple[int, int]]:
        """Loads the index from file."""
        if os.path.exists(self.index_filepath):
            try:
                with open(self.index_filepath, 'rb') as f:
                    return pickle.load(f)
            except (EOFError, pickle.UnpicklingError) as e:
                logger.error(f"Error loading index from {self.index_filepath}: {e}. Creating new index.")
                return {}
        return {}

    def _save_index(self):
        """Saves the current index to file."""
        with open(self.index_filepath, 'wb') as f:
            pickle.dump(self.index, f)

    def _load_id_counter(self) -> int:
        """Loads the next available ID from file."""
        if os.path.exists(self.id_counter_filepath):
            try:
                with open(self.id_counter_filepath, 'rb') as f:
                    return struct.unpack('<I', f.read(4))[0]
            except (EOFError, struct.error) as e:
                logger.error(f"Error loading ID counter from {self.id_counter_filepath}: {e}. Starting from 0.")
                return 0
        return 0

    def _save_id_counter(self):
        """Saves the current next ID to file."""
        with open(self.id_counter_filepath, 'wb') as f:
            f.write(struct.pack('<I', self.next_id))

    def _get_next_id(self) -> int:
        """Increments and returns the next ID."""
        with self.lock:
            current_id = self.next_id
            self.next_id += 1
            self._save_id_counter()
            return current_id

    def add_record(self, data_obj: DataObject) -> Optional[int]:
        """Adds a new DataObject record to the DB."""
        with self.lock:
            record_id = self._get_next_id()
            data_obj.id = record_id

            # --- APLICAR LÓGICA DE SERIALIZAÇÃO DE LISTA PARA STRING AQUI ---
            # Cria uma cópia rasa do objeto para modificação antes da serialização.
            data_obj_to_pickle = copy.copy(data_obj) 
            for field_name in DataObject._LIST_CONVERTIBLE_STRING_FIELDS:
                current_value = getattr(data_obj_to_pickle, field_name)
                serialized_value = DataObject._convert_list_to_string_for_serialization(current_value)
                setattr(data_obj_to_pickle, field_name, serialized_value)
            
            pickled_data = pickle.dumps(data_obj_to_pickle)
            # --- FIM DA LÓGICA DE SERIALIZAÇÃO ---
            
            record_size = len(pickled_data)
            is_valid = True

            record_bytes_to_write = struct.pack('<I', data_obj.id) + \
                                    struct.pack('!?', is_valid) + \
                                    struct.pack('<I', record_size) + \
                                    pickled_data

            try:
                with open(self.db_filepath, 'r+b') as f:
                    f.seek(0, os.SEEK_END)
                    offset = f.tell()
                    f.write(record_bytes_to_write)
                
                self.index[record_id] = (offset, record_size)
                self._save_index()
                logger.info(f"Record {record_id} added at offset {offset}.")
                return record_id
            except Exception as e:
                logger.error(f"Error adding record {record_id}: {traceback.format_exc()}")
                return None

    def get_record(self, record_id: int) -> Optional[DataObject]:
        """Retrieves a DataObject record by its ID."""
        with self.lock:
            if record_id not in self.index:
                return None

            offset, size = self.index[record_id]
            try:
                with open(self.db_filepath, 'rb') as f:
                    f.seek(offset + RECORD_METADATA_SIZE) # Skip metadata to get actual pickled data
                    pickled_data = f.read(size)
                    data_obj = pickle.loads(pickled_data)
                    logger.info(f"Record {record_id} retrieved from offset {offset}.")
                    return data_obj
            except Exception as e:
                logger.error(f"Error retrieving record {record_id}: {traceback.format_exc()}")
                return None

    def update_record(self, data_obj: DataObject) -> bool:
        """Updates an existing DataObject record."""
        with self.lock:
            if data_obj.id not in self.index:
                logger.warning(f"Attempted to update non-existent record ID: {data_obj.id}")
                return False

            # Mark old record as invalid
            old_offset, old_size = self.index[data_obj.id]
            try:
                with open(self.db_filepath, 'r+b') as f:
                    f.seek(old_offset + 4) # Move to is_valid byte
                    f.write(struct.pack('!?', False)) # Mark as invalid
                logger.info(f"Record {data_obj.id} at offset {old_offset} marked as invalid.")
            except Exception as e:
                logger.error(f"Error marking old record {data_obj.id} invalid: {traceback.format_exc()}")
                return False

            # Add new version of the record (this creates fragmentation)
            # --- APLICAR LÓGICA DE SERIALIZAÇÃO DE LISTA PARA STRING AQUI ---
            data_obj_to_pickle = copy.copy(data_obj) 
            for field_name in DataObject._LIST_CONVERTIBLE_STRING_FIELDS:
                current_value = getattr(data_obj_to_pickle, field_name)
                serialized_value = DataObject._convert_list_to_string_for_serialization(current_value)
                setattr(data_obj_to_pickle, field_name, serialized_value)

            pickled_data = pickle.dumps(data_obj_to_pickle)
            # --- FIM DA LÓGICA DE SERIALIZAÇÃO ---

            new_record_size = len(pickled_data)
            is_valid = True

            new_record_bytes_to_write = struct.pack('<I', data_obj.id) + \
                                        struct.pack('!?', is_valid) + \
                                        struct.pack('<I', new_record_size) + \
                                        pickled_data

            try:
                with open(self.db_filepath, 'r+b') as f:
                    f.seek(0, os.SEEK_END)
                    new_offset = f.tell()
                    f.write(new_record_bytes_to_write)
                
                self.index[data_obj.id] = (new_offset, new_record_size) # Update index to new offset
                self._save_index()
                logger.info(f"Record {data_obj.id} updated at new offset {new_offset}.")
                return True
            except Exception as e:
                logger.error(f"Error adding updated record {data_obj.id}: {traceback.format_exc()}")
                return False

    def delete_record(self, record_id: int) -> bool:
        """Marks a record as invalid without removing it from the file."""
        with self.lock:
            if record_id not in self.index:
                logger.warning(f"Attempted to delete non-existent record ID: {record_id}")
                return False
            
            offset, size = self.index[record_id]
            try:
                with open(self.db_filepath, 'r+b') as f:
                    f.seek(offset + 4) # Move to is_valid byte
                    f.write(struct.pack('!?', False)) # Mark as invalid
                del self.index[record_id] # Remove from active index
                self._save_index()
                logger.info(f"Record {record_id} marked as invalid and removed from index.")
                return True
            except Exception as e:
                logger.error(f"Error deleting record {record_id}: {traceback.format_exc()}")
                return False
    
    def get_all_records(self) -> Iterator[DataObject]:
        """Iterates over all valid records in the database."""
        with self.lock:
            if not os.path.exists(self.db_filepath):
                return

            try:
                with open(self.db_filepath, 'rb') as f:
                    # Skip header
                    f.seek(DB_HEADER_SIZE)
                    
                    while True:
                        current_offset = f.tell()
                        metadata_bytes = f.read(RECORD_METADATA_SIZE)
                        if not metadata_bytes: # EOF
                            break
                        if len(metadata_bytes) < RECORD_METADATA_SIZE:
                            # Incomplete metadata at end of file
                            logger.warning(f"Incomplete record metadata at offset {current_offset}.")
                            break

                        record_id, is_valid_byte, record_size = struct.unpack('<IBI', metadata_bytes)
                        is_valid = bool(is_valid_byte)

                        pickled_data = f.read(record_size)
                        if len(pickled_data) < record_size:
                            logger.warning(f"Incomplete record data for ID {record_id} at offset {current_offset}. Expected {record_size}, got {len(pickled_data)}.")
                            break # Incomplete record

                        if is_valid and record_id in self.index: # Ensure it's valid and still in current index
                            try:
                                data_obj = pickle.loads(pickled_data)
                                yield data_obj
                            except pickle.UnpicklingError as pe:
                                logger.error(f"Unpickling error for record ID {record_id} at offset {current_offset}: {pe}")
                            except Exception as e:
                                logger.error(f"Error decoding record ID {record_id} at offset {current_offset}: {traceback.format_exc()}")
                        else:
                            # If not valid, just skip over its data
                            pass
            except Exception as e:
                logger.error(f"Error iterating all records: {traceback.format_exc()}")

    def get_total_records(self) -> int:
        """Returns the count of valid records."""
        return len(self.index)

    def compact_db(self):
        """Rewrites the DB file to remove invalid records and optimize space."""
        with self.lock:
            temp_db_filepath = self.db_filepath + ".tmp"
            new_index = {}
            new_next_id = 0 # Will rebuild IDs if necessary, or just assign new offsets

            try:
                with open(self.db_filepath, 'rb') as old_f, \
                     open(temp_db_filepath, 'wb') as new_f:
                    
                    old_f.seek(DB_HEADER_SIZE) # Skip old header

                    # Write new header (will update current_id at the end)
                    new_f.write(struct.pack('<I', new_next_id)) 

                    for data_obj in self.get_all_records(): # Use the iterator to get valid records
                        # Re-pickle to ensure consistency with current DataObject structure
                        # And apply the serialization logic for specific fields
                        data_obj_to_pickle = copy.copy(data_obj) 
                        for field_name in DataObject._LIST_CONVERTIBLE_STRING_FIELDS:
                            current_value = getattr(data_obj_to_pickle, field_name)
                            serialized_value = DataObject._convert_list_to_string_for_serialization(current_value)
                            setattr(data_obj_to_pickle, field_name, serialized_value)

                        pickled_data = pickle.dumps(data_obj_to_pickle)
                        record_size = len(pickled_data)
                        is_valid = True # All records copied to new file are valid

                        # Note: IDs are preserved during compaction, only offsets change
                        record_bytes_to_write = struct.pack('<I', data_obj.id) + \
                                                struct.pack('!?', is_valid) + \
                                                struct.pack('<I', record_size) + \
                                                pickled_data
                        
                        current_offset = new_f.tell()
                        new_f.write(record_bytes_to_write)
                        new_index[data_obj.id] = (current_offset, record_size)
                        new_next_id = max(new_next_id, data_obj.id + 1) # Keep track of max ID

                # Update the ID counter in the new file header
                with open(temp_db_filepath, 'r+b') as new_f:
                    new_f.seek(0)
                    new_f.write(struct.pack('<I', new_next_id))
                
                # Replace old files with new ones
                os.replace(temp_db_filepath, self.db_filepath)
                self.index = new_index
                self.next_id = new_next_id
                self._save_index()
                self._save_id_counter()
                logger.info(f"Database compacted. New record count: {len(self.index)}")
                st.success("Banco de dados compactado com sucesso!")
            except Exception as e:
                logger.error(f"Error during DB compaction: {traceback.format_exc()}")
                st.error(f"Erro durante a compactação do banco de dados: {e}")
                # Clean up temp file if error occurs
                if os.path.exists(temp_db_filepath):
                    os.remove(temp_db_filepath)

# --- App Initialization and UI Setup ---

# Database initialization
def initialize_db():
    if st.session_state.db_type == "Arquivo/Índice Padrão":
        st.session_state.db = DBManager(
            db_filepath=os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["DB_FILE_NAME"]),
            index_filepath=os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["BTREE_INDEX_FILE_NAME"]), # Reusing BTREE_INDEX_FILE_NAME for general index
            id_counter_filepath=os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["ID_COUNTER_FILE_NAME"]),
            lock_filepath=os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOCK_FILE_NAME"])
        )
        logger.info("Standard File/Index DBManager initialized.")
    elif st.session_state.db_type == "Árvore B (Placeholder)":
        st.session_state.db = BTreeManager(
            db_dir=APP_CONFIG["DB_DIR"],
            index_file_name=APP_CONFIG["BTREE_INDEX_FILE_NAME"],
            page_size=APP_CONFIG["BTREE_PAGE_SIZE"],
            min_degree=APP_CONFIG["BTREE_MIN_DEGREE"]
        )
        logger.info("B-Tree Manager (Placeholder) initialized.")
    st.session_state.db_initialized = True
    st.success(f"Banco de dados inicializado como: {st.session_state.db_type}!")
    logger.info(f"Database initialized as {st.session_state.db_type}.")

def setup_ui():
    st.sidebar.title("Navegação")
    page_options = [
        "Início",
        "Gerenciar Registros (CRUD)",
        "Importar/Exportar CSV",
        "Backup/Restauração",
        "Compressão de Arquivos",
        "Criptografia de Arquivos",
        "Administração",
        "Log de Atividades",
        "Sobre o Aplicativo"
    ]
    
    selected_page_label = st.sidebar.radio("Ir para", page_options)

    st.title("Sistema de Gerenciamento de Acidentes de Trânsito")

    # DB Type selection and initialization
    st.sidebar.subheader("Tipo de Banco de Dados")
    db_type_options = ["Arquivo/Índice Padrão", "Árvore B (Placeholder)"]
    current_db_type_selection = st.sidebar.selectbox(
        "Selecione o tipo de DB:",
        options=db_type_options,
        index=db_type_options.index(st.session_state.db_type) if st.session_state.db_type in db_type_options else 0,
        key="db_type_selector"
    )
    if current_db_type_selection != st.session_state.db_type:
        st.session_state.db_type = current_db_type_selection
        st.session_state.db_initialized = False # Force re-initialization
        st.warning(f"Tipo de DB alterado para '{st.session_state.db_type}'. Por favor, inicialize o DB.")

    if not st.session_state.db_initialized or st.session_state.db is None:
        st.sidebar.warning("Banco de dados não inicializado.")
        if st.sidebar.button("Inicializar Banco de Dados"):
            initialize_db()
        else:
            st.info("Por favor, inicialize o banco de dados para prosseguir.")
            st.stop() # Stop execution if DB is not initialized

    # Display content based on selected page
    if selected_page_label == "Início":
        display_home_section()
    elif selected_page_label == "Gerenciar Registros (CRUD)":
        display_crud_section()
    elif selected_page_label == "Importar/Exportar CSV":
        display_csv_import_export_section()
    elif selected_page_label == "Backup/Restauração":
        display_backup_restore_section()
    elif selected_page_label == "Compressão de Arquivos":
        display_compression_section()
    elif selected_page_label == "Criptografia de Arquivos":
        display_cryptography_section()
    elif selected_page_label == "Administração":
        display_admin_section()
    elif selected_page_label == "Log de Atividades":
        display_activity_log()
    elif selected_page_label == "Sobre o Aplicativo":
        display_about_section()


# --- UI Sections (as functions for Streamlit pages) ---

def display_home_section():
    st.header("Bem-vindo!")
    st.write("Este é o seu Sistema de Gerenciamento de Banco de Dados de Acidentes de Trânsito.")
    st.write("Use a barra lateral para navegar pelas funcionalidades.")
    st.markdown("""
        ### Funcionalidades Principais:
        - **Gerenciar Registros (CRUD):** Adicione, visualize, atualize e exclua registros de acidentes.
        - **Importar/Exportar CSV:** Importe dados de um arquivo CSV ou exporte o banco de dados atual para CSV.
        - **Backup/Restauração:** Crie backups do seu banco de dados e restaure-os quando necessário.
        - **Compressão de Arquivos:** Comprima e descomprima seus arquivos de banco de dados (LZW e Huffman - placeholders).
        - **Criptografia de Arquivos:** Criptografe e descriptografe seus arquivos de banco de dados usando criptografia híbrida (AES + RSA).
        - **Administração:** Gerencie configurações e execute tarefas de manutenção.
        - **Log de Atividades:** Visualize as operações recentes do sistema.
    """)
    st.info(f"Banco de Dados atual: **{st.session_state.db_type}**")
    if st.session_state.db_type == "Arquivo/Índice Padrão":
        st.info(f"Total de registros no DB: {st.session_state.db.get_total_records()}")
    elif st.session_state.db_type == "Árvore B (Placeholder)":
        st.info(f"Total de registros na Árvore B (Placeholder): {st.session_state.db.get_total_records()}")


def display_crud_section():
    st.header("Gerenciar Registros")
    st.subheader("Adicionar Novo Registro")

    with st.form("add_record_form"):
        # Helper to format default date/time for input
        default_dt = datetime.now()
        col1, col2, col3 = st.columns(3)
        with col1:
            crash_date_input = st.date_input("Data do Acidente", value=default_dt.date())
        with col2:
            crash_time_input = st.time_input("Hora do Acidente", value=default_dt.time())
        with col3:
            crash_hour = st.number_input("Hora (0-23)", min_value=0, max_value=23, value=default_dt.hour)
            crash_day_of_week = st.number_input("Dia da Semana (1-7)", min_value=1, max_value=7, value=default_dt.isoweekday())
            crash_month = st.number_input("Mês (1-12)", min_value=1, max_value=12, value=default_dt.month)

        # Combine date and time
        full_crash_datetime = datetime.combine(crash_date_input, crash_time_input)

        st.markdown("---")
        st.subheader("Dados do Acidente")
        # Campos que podem ser String ou List[str]
        lighting_condition_input = st.text_input("Condição de Iluminação (separar por ',' ou '/')", "DAYLIGHT")
        crash_type_input = st.text_input("Tipo do Acidente (separar por ',' ou '/')", "PARKING")
        most_severe_injury_input = st.text_input("Ferimento Mais Grave (separar por ',' ou '/')", "NO INDICATION OF INJURY")

        # Campos que são sempre str
        traffic_control_device = st.text_input("Dispositivo de Controle de Tráfego", "NO CONTROLS")
        weather_condition = st.text_input("Condição Climática", "CLEAR")
        first_crash_type = st.text_input("Tipo do Primeiro Acidente", "PEDALCYCLIST")
        trafficway_type = st.text_input("Tipo de Via de Trânsito", "UNKNOWN")
        alignment = st.text_input("Alinhamento", "STRAIGHT AND LEVEL")
        roadway_surface_cond = st.text_input("Condição da Superfície da Estrada", "DRY")
        road_defect = st.text_input("Defeito da Estrada", "NO DEFECTS")
        intersection_related_i = st.text_input("Relacionado à Interseção (Y/N/UNKNOWN)", "N")
        damage = st.text_input("Dano ($)", "$501 - $1,500")
        prim_contributory_cause = st.text_input("Causa Contributiva Primária", "UNABLE TO DETERMINE")
        
        st.markdown("---")
        st.subheader("Informações de Ferimentos e Unidades")
        num_units = st.number_input("Nº de Unidades Envolvidas", min_value=1, value=1)
        injuries_total = st.number_input("Total de Ferimentos", min_value=0.0, value=0.0)
        injuries_fatal = st.number_input("Ferimentos Fatais", min_value=0.0, value=0.0)
        injuries_incapacitating = st.number_input("Ferimentos Incapacitantes", min_value=0.0, value=0.0)
        injuries_non_incapacitating = st.number_input("Ferimentos Não Incapacitantes", min_value=0.0, value=0.0)
        injuries_reported_not_eviden = st.number_input("Ferimentos Relatados Não Evidentes", min_value=0.0, value=0.0)
        injuries_no_indication = st.number_input("Ferimentos Sem Indicação", min_value=0.0, value=0.0)

        submitted = st.form_submit_button("Adicionar Registro")
        if submitted:
            try:
                new_data_obj = DataObject(
                    crash_date=full_crash_datetime,
                    traffic_control_device=traffic_control_device,
                    weather_condition=weather_condition,
                    # Estes campos são processados pela DataObject.from_dict/from_csv_line
                    # A entrada aqui é uma string, e a DataObject cuidará da conversão para lista se houver delimitadores.
                    lighting_condition=lighting_condition_input,
                    first_crash_type=first_crash_type,
                    trafficway_type=trafficway_type,
                    alignment=alignment,
                    roadway_surface_cond=roadway_surface_cond,
                    road_defect=road_defect,
                    crash_type=crash_type_input,
                    intersection_related_i=intersection_related_i,
                    damage=damage,
                    prim_contributory_cause=prim_contributory_cause,
                    num_units=num_units,
                    most_severe_injury=most_severe_injury_input,
                    injuries_total=injuries_total,
                    injuries_fatal=injuries_fatal,
                    injuries_incapacitating=injuries_incapacitating,
                    injuries_non_incapacitating=injuries_non_incapacitating,
                    injuries_reported_not_eviden=injuries_reported_not_eviden,
                    injuries_no_indication=injuries_no_indication,
                    crash_hour=crash_hour,
                    crash_day_of_week=crash_day_of_week,
                    crash_month=crash_month
                )
                
                record_id = st.session_state.db.add_record(new_data_obj)
                if record_id is not None:
                    st.success(f"Registro adicionado com sucesso! ID: {record_id}")
                    logger.info(f"Record {record_id} added successfully.")
                else:
                    st.error("Falha ao adicionar registro.")
            except ValueError as e:
                st.error(f"Erro de validação: {e}")
                logger.error(f"Validation error when adding record: {e}")
            except Exception as e:
                st.error(f"Erro inesperado ao adicionar registro: {e}")
                logger.error(f"Unexpected error when adding record: {traceback.format_exc()}")

    st.subheader("Visualizar e Atualizar Registros")
    record_id_to_view = st.number_input("Digite o ID do Registro para Visualizar/Atualizar", min_value=0, value=0, key="view_update_id_input")
    
    if st.button("Buscar Registro"):
        record = st.session_state.db.get_record(record_id_to_view)
        if record:
            st.session_state.current_record_to_edit = record
            st.success(f"Registro {record_id_to_view} encontrado.")
            logger.info(f"Record {record_id_to_view} found for viewing/editing.")
        else:
            st.error(f"Registro com ID {record_id_to_view} não encontrado.")
            logger.warning(f"Record {record_id_to_view} not found for viewing/editing.")
            st.session_state.current_record_to_edit = None

    if 'current_record_to_edit' in st.session_state and st.session_state.current_record_to_edit is not None:
        record_edit = st.session_state.current_record_to_edit
        st.write(f"### Editando Registro ID: {record_edit.id}")

        with st.form("edit_record_form"):
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                edit_crash_date = st.date_input("Data do Acidente", value=record_edit.crash_date.date(), key="edit_date")
            with col_e2:
                edit_crash_time = st.time_input("Hora do Acidente", value=record_edit.crash_date.time(), key="edit_time")
            with col_e3:
                edit_crash_hour = st.number_input("Hora (0-23)", min_value=0, max_value=23, value=record_edit.crash_hour, key="edit_hour")
                edit_crash_day_of_week = st.number_input("Dia da Semana (1-7)", min_value=1, max_value=7, value=record_edit.crash_day_of_week, key="edit_day")
                edit_crash_month = st.number_input("Mês (1-12)", min_value=1, max_value=12, value=record_edit.crash_month, key="edit_month")
            
            edit_full_crash_datetime = datetime.combine(edit_crash_date, edit_crash_time)

            st.markdown("---")
            st.subheader("Dados do Acidente (Edição)")
            # Para edição, precisamos converter List[str] de volta para string para o text_input
            # E a DataObject.from_dict/from_csv_line cuidará da conversão de volta para lista na atualização
            edit_lighting_condition_val = record_edit.lighting_condition if isinstance(record_edit.lighting_condition, str) else " , ".join(record_edit.lighting_condition)
            edit_crash_type_val = record_edit.crash_type if isinstance(record_edit.crash_type, str) else " , ".join(record_edit.crash_type)
            edit_most_severe_injury_val = record_edit.most_severe_injury if isinstance(record_edit.most_severe_injury, str) else " , ".join(record_edit.most_severe_injury)

            edit_lighting_condition = st.text_input("Condição de Iluminação (separar por ',' ou '/')", edit_lighting_condition_val, key="edit_lighting")
            edit_crash_type = st.text_input("Tipo do Acidente (separar por ',' ou '/')", edit_crash_type_val, key="edit_crash_type")
            edit_most_severe_injury = st.text_input("Ferimento Mais Grave (separar por ',' ou '/')", edit_most_severe_injury_val, key="edit_most_severe")

            edit_traffic_control_device = st.text_input("Dispositivo de Controle de Tráfego", record_edit.traffic_control_device, key="edit_tcd")
            edit_weather_condition = st.text_input("Condição Climática", record_edit.weather_condition, key="edit_wc")
            edit_first_crash_type = st.text_input("Tipo do Primeiro Acidente", record_edit.first_crash_type, key="edit_fct")
            edit_trafficway_type = st.text_input("Tipo de Via de Trânsito", record_edit.trafficway_type, key="edit_tw_type")
            edit_alignment = st.text_input("Alinhamento", record_edit.alignment, key="edit_align")
            edit_roadway_surface_cond = st.text_input("Condição da Superfície da Estrada", record_edit.roadway_surface_cond, key="edit_rsc")
            edit_road_defect = st.text_input("Defeito da Estrada", record_edit.road_defect, key="edit_rd")
            edit_intersection_related_i = st.text_input("Relacionado à Interseção (Y/N/UNKNOWN)", record_edit.intersection_related_i, key="edit_iri")
            edit_damage = st.text_input("Dano ($)", record_edit.damage, key="edit_damage")
            edit_prim_contributory_cause = st.text_input("Causa Contributiva Primária", record_edit.prim_contributory_cause, key="edit_pcc")
            
            st.markdown("---")
            st.subheader("Informações de Ferimentos e Unidades (Edição)")
            edit_num_units = st.number_input("Nº de Unidades Envolvidas", min_value=1, value=record_edit.num_units, key="edit_nu")
            edit_injuries_total = st.number_input("Total de Ferimentos", min_value=0.0, value=record_edit.injuries_total, key="edit_it")
            edit_injuries_fatal = st.number_input("Ferimentos Fatais", min_value=0.0, value=record_edit.injuries_fatal, key="edit_if")
            edit_injuries_incapacitating = st.number_input("Ferimentos Incapacitantes", min_value=0.0, value=record_edit.injuries_incapacitating, key="edit_ii")
            edit_injuries_non_incapacitating = st.number_input("Ferimentos Não Incapacitantes", min_value=0.0, value=record_edit.injuries_non_incapacitating, key="edit_lni")
            edit_injuries_reported_not_eviden = st.number_input("Ferimentos Relatados Não Evidentes", min_value=0.0, value=record_edit.injuries_reported_not_eviden, key="edit_irn")
            edit_injuries_no_indication = st.number_input("Ferimentos Sem Indicação", min_value=0.0, value=record_edit.injuries_no_indication, key="edit_ini")

            update_submitted = st.form_submit_button("Atualizar Registro")

            if update_submitted:
                try:
                    updated_data_obj = DataObject(
                        id=record_edit.id, # Keep the original ID
                        crash_date=edit_full_crash_datetime,
                        traffic_control_device=edit_traffic_control_device,
                        weather_condition=edit_weather_condition,
                        # Estes campos são processados pela DataObject.from_dict/from_csv_line
                        # A entrada aqui é uma string, e a DataObject cuidará da conversão para lista se houver delimitadores.
                        lighting_condition=edit_lighting_condition,
                        first_crash_type=edit_first_crash_type,
                        trafficway_type=edit_trafficway_type,
                        alignment=edit_alignment,
                        roadway_surface_cond=edit_roadway_surface_cond,
                        road_defect=edit_road_defect,
                        crash_type=edit_crash_type,
                        intersection_related_i=edit_intersection_related_i,
                        damage=edit_damage,
                        prim_contributory_cause=edit_prim_contributory_cause,
                        num_units=edit_num_units,
                        most_severe_injury=edit_most_severe_injury,
                        injuries_total=edit_injuries_total,
                        injuries_fatal=edit_injuries_fatal,
                        injuries_incapacitating=edit_injuries_incapacitating,
                        injuries_non_incapacitating=edit_injuries_non_incapacitating,
                        injuries_reported_not_eviden=edit_injuries_reported_not_eviden,
                        injuries_no_indication=edit_injuries_no_indication,
                        crash_hour=edit_crash_hour,
                        crash_day_of_week=edit_crash_day_of_week,
                        crash_month=edit_crash_month
                    )
                    
                    if st.session_state.db.update_record(updated_data_obj):
                        st.success(f"Registro ID {record_edit.id} atualizado com sucesso!")
                        logger.info(f"Record {record_edit.id} updated successfully.")
                        st.session_state.current_record_to_edit = None # Clear form
                    else:
                        st.error(f"Falha ao atualizar registro ID {record_edit.id}.")
                except ValueError as e:
                    st.error(f"Erro de validação ao atualizar registro: {e}")
                    logger.error(f"Validation error when updating record: {e}")
                except Exception as e:
                    st.error(f"Erro inesperado ao atualizar registro: {e}")
                    logger.error(f"Unexpected error when updating record: {traceback.format_exc()}")

    st.subheader("Excluir Registro")
    record_id_to_delete = st.number_input("Digite o ID do Registro para Excluir", min_value=0, value=0, key="delete_id_input")
    if st.button("Excluir Registro"):
        if st.session_state.db.delete_record(record_id_to_delete):
            st.success(f"Registro ID {record_id_to_delete} excluído com sucesso!")
            logger.info(f"Record {record_id_to_delete} deleted successfully.")
        else:
            st.error(f"Falha ao excluir registro ID {record_id_to_delete}.")

    st.subheader("Todos os Registros (Visão Rápida)")
    if st.button("Carregar Todos os Registros"):
        records_to_display = []
        try:
            for record in st.session_state.db.get_all_records():
                # Format specific fields for display to avoid list representation directly
                display_record = record.__dict__.copy()
                for field_name in DataObject._LIST_CONVERTIBLE_STRING_FIELDS:
                    value = getattr(record, field_name)
                    if isinstance(value, list):
                        display_record[field_name] = " , ".join(value)
                records_to_display.append(display_record)
            
            if records_to_display:
                st.dataframe(records_to_display)
                logger.info(f"Displayed {len(records_to_display)} records.")
            else:
                st.info("Nenhum registro encontrado no banco de dados.")
        except Exception as e:
            st.error(f"Erro ao carregar todos os registros: {e}")
            logger.error(f"Error loading all records for display: {traceback.format_exc()}")


def display_csv_import_export_section():
    st.header("Importar/Exportar CSV")

    st.subheader("Importar CSV")
    uploaded_file = st.file_uploader("Escolha um arquivo CSV para importar", type=["csv"])
    if uploaded_file is not None:
        if st.button("Processar Importação"):
            try:
                # Read the CSV content as string
                csv_content = uploaded_file.read().decode('utf-8')
                csv_lines = csv_content.splitlines()

                if not csv_lines:
                    st.warning("O arquivo CSV está vazio.")
                    logger.warning("Attempted to import empty CSV file.")
                    return

                header_line = csv_lines[0]
                provided_header_list = [h.strip() for h in header_line.split(';')]

                if provided_header_list != PORTUGUESE_HEADER_EXPECTED_LIST:
                    st.error(
                        "O cabeçalho do CSV não corresponde ao padrão português esperado.\n"
                        f"Esperado: {';'.join(PORTUGUESE_HEADER_EXPECTED_LIST)}\n"
                        f"Recebido: {header_line}"
                    )
                    logger.error(f"CSV import failed due to header mismatch. Expected: {PORTUGUESE_HEADER_EXPECTED_LIST}, Received: {provided_header_list}")
                    return

                imported_count = 0
                error_count = 0
                for line_num, line in enumerate(csv_lines[1:], start=2): # Skip header
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        # DataObject.from_csv_line espera o cabeçalho em inglês para mapeamento interno
                        data_obj = DataObject.from_csv_line(line, ENGLISH_HEADER_FOR_DATAOBJECT)
                        if st.session_state.db.add_record(data_obj) is not None:
                            imported_count += 1
                        else:
                            error_count += 1
                            logger.error(f"Failed to add record from CSV line {line_num}: {line}")
                    except ValueError as e:
                        error_count += 1
                        st.warning(f"Erro na linha {line_num}: {e} (linha ignorada)")
                        logger.warning(f"Error importing CSV line {line_num}: {line}. Details: {e}")
                    except Exception as e:
                        error_count += 1
                        st.error(f"Erro inesperado na linha {line_num}: {e} (linha ignorada)")
                        logger.error(f"Unexpected error importing CSV line {line_num}: {line}. Details: {traceback.format_exc()}")
                
                st.success(f"Importação concluída! {imported_count} registros adicionados, {error_count} erros.")
                logger.info(f"CSV import finished. Added {imported_count} records, {error_count} errors.")

            except Exception as e:
                st.error(f"Erro ao ler ou processar o arquivo CSV: {e}")
                logger.error(f"Error reading/processing CSV file: {traceback.format_exc()}")


    st.subheader("Exportar CSV")
    if st.button("Exportar Banco de Dados para CSV"):
        try:
            # Prepare data for CSV export
            output = io.StringIO()
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

            # Write header row (Portuguese header)
            writer.writerow(PORTUGUESE_HEADER_EXPECTED_LIST)

            for record in st.session_state.db.get_all_records():
                row_data = []
                for english_col_name in ENGLISH_HEADER_FOR_DATAOBJECT:
                    value = getattr(record, english_col_name)
                    # Convert datetime objects to string format for CSV
                    if isinstance(value, datetime):
                        row_data.append(value.strftime("%m/%d/%Y %I:%M:%S %p"))
                    # Convert list attributes back to string for CSV export
                    elif english_col_name in DataObject._LIST_CONVERTIBLE_STRING_FIELDS and isinstance(value, list):
                        row_data.append(DataObject._convert_list_to_string_for_serialization(value))
                    else:
                        row_data.append(str(value))
                writer.writerow(row_data)
            
            csv_string = output.getvalue()
            st.download_button(
                label="Baixar CSV",
                data=csv_string,
                file_name="traffic_accidents_export.csv",
                mime="text/csv"
            )
            st.success("Dados exportados para CSV com sucesso!")
            logger.info("Database exported to CSV successfully.")
        except Exception as e:
            st.error(f"Erro ao exportar dados para CSV: {e}")
            logger.error(f"Error exporting database to CSV: {traceback.format_exc()}")


def display_backup_restore_section():
    st.header("Backup e Restauração")

    st.subheader("Criar Backup")
    if st.button("Criar Backup Agora"):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_db_file = os.path.join(BACKUP_PATH, f"traffic_accidents_backup_{timestamp}.db")
            backup_index_file = os.path.join(BACKUP_PATH, f"traffic_accidents_index_backup_{timestamp}.idx")
            backup_id_counter_file = os.path.join(BACKUP_PATH, f"id_counter_backup_{timestamp}.dat")

            Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True) # Ensure backup dir exists

            # Copy DB file
            db_original_path = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["DB_FILE_NAME"])
            if os.path.exists(db_original_path):
                shutil.copy2(db_original_path, backup_db_file)
            else:
                st.warning("Arquivo DB principal não encontrado para backup.")

            # Copy Index file (only for standard DB)
            if st.session_state.db_type == "Arquivo/Índice Padrão":
                index_original_path = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["BTREE_INDEX_FILE_NAME"])
                if os.path.exists(index_original_path):
                    shutil.copy2(index_original_path, backup_index_file)
                else:
                    st.warning("Arquivo de índice não encontrado para backup.")
            elif st.session_state.db_type == "Árvore B (Placeholder)":
                # For B-Tree, the index is the main file, so it's already copied above.
                # If there's a separate data file for B-Tree, that would need copying too.
                pass # Placeholder, as BTreeManager uses the main DB file path as its index

            # Copy ID Counter file
            id_counter_original_path = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["ID_COUNTER_FILE_NAME"])
            if os.path.exists(id_counter_original_path):
                shutil.copy2(id_counter_original_path, backup_id_counter_file)
            else:
                st.warning("Arquivo de contador de ID não encontrado para backup.")

            st.success(f"Backup criado com sucesso em: {BACKUP_PATH}")
            logger.info(f"Backup created successfully in {BACKUP_PATH} (DB: {backup_db_file}, Index: {backup_index_file}, ID Counter: {backup_id_counter_file}).")
        except Exception as e:
            st.error(f"Erro ao criar backup: {e}")
            logger.error(f"Error creating backup: {traceback.format_exc()}")

    st.subheader("Restaurar Backup")
    backup_files = [f for f in os.listdir(BACKUP_PATH) if f.endswith('.db')]
    if not backup_files:
        st.info("Nenhum arquivo de backup .db encontrado.")
    else:
        selected_backup_db = st.selectbox("Selecione um arquivo de backup .db para restaurar:", backup_files)
        if selected_backup_db:
            if st.button("Restaurar Backup"):
                try:
                    # Determine corresponding index and ID counter files
                    base_name = selected_backup_db.replace('.db', '')
                    original_db_path = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["DB_FILE_NAME"])
                    original_index_path = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["BTREE_INDEX_FILE_NAME"])
                    original_id_counter_path = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["ID_COUNTER_FILE_NAME"])

                    backup_db_path = os.path.join(BACKUP_PATH, selected_backup_db)
                    backup_index_path = backup_db_path.replace('.db', '.idx') # Assumes idx filename matches
                    backup_id_counter_path = backup_db_path.replace('.db', '.dat') # Assumes dat filename matches

                    # Copy DB file
                    shutil.copy2(backup_db_path, original_db_path)

                    # Copy Index file (only if it exists for the backup, for standard DB)
                    if os.path.exists(backup_index_path) and st.session_state.db_type == "Arquivo/Índice Padrão":
                        shutil.copy2(backup_index_path, original_index_path)
                    elif st.session_state.db_type == "Árvore B (Placeholder)":
                        # For B-Tree, the .db file itself is the index/data structure.
                        pass

                    # Copy ID Counter file
                    if os.path.exists(backup_id_counter_path):
                        shutil.copy2(backup_id_counter_path, original_id_counter_path)
                    
                    st.session_state.db_initialized = False # Force re-initialization of DBManager
                    initialize_db() # Re-initialize DB Manager with restored files

                    st.success(f"Backup '{selected_backup_db}' restaurado com sucesso!")
                    logger.info(f"Backup '{selected_backup_db}' restored successfully.")
                except Exception as e:
                    st.error(f"Erro ao restaurar backup: {e}")
                    logger.error(f"Error restoring backup '{selected_backup_db}': {traceback.format_exc()}")


def display_compression_section():
    st.header("Compressão de Arquivos")
    st.info("As funções LZW e Huffman são implementações básicas de placeholder. "
            "Para grandes arquivos, a performance pode não ser otimizada.")

    st.subheader("Comprimir Arquivo")
    compress_file_type = st.radio("Selecione o tipo de arquivo para comprimir:", ("Banco de Dados", "Índice (Padrão)"))
    compress_algorithm = st.selectbox("Algoritmo de Compressão:", ("LZW", "Huffman"))

    input_file_name = APP_CONFIG["DB_FILE_NAME"] if compress_file_type == "Banco de Dados" else APP_CONFIG["BTREE_INDEX_FILE_NAME"]
    full_input_path = os.path.join(APP_CONFIG["DB_DIR"], input_file_name)
    output_compressed_file = f"{input_file_name}.{compress_algorithm.lower()}"
    full_output_path = os.path.join(APP_CONFIG["DB_DIR"], output_compressed_file)

    if st.button(f"Comprimir {compress_file_type} com {compress_algorithm}"):
        if not os.path.exists(full_input_path):
            st.error(f"Arquivo de entrada não encontrado: `{input_file_name}`")
            logger.warning(f"Compression failed: Input file '{full_input_path}' not found.")
            return

        success = False
        if compress_algorithm == "LZW":
            success = LZWCompression.lzw_compress_file(full_input_path, full_output_path)
        elif compress_algorithm == "Huffman":
            success = HuffmanCompression.huffman_compress_file(full_input_path, full_output_path)
        
        if success:
            st.success(f"{compress_file_type} comprimido com sucesso para `{output_compressed_file}`!")
            logger.info(f"{compress_file_type} compressed to {output_compressed_file} using {compress_algorithm}.")
        else:
            st.error(f"Falha ao comprimir {compress_file_type}.")

    st.subheader("Descomprimir Arquivo")
    decompress_file_type = st.radio("Selecione o tipo de arquivo para descomprimir:", ("Banco de Dados (LZW)", "Banco de Dados (Huffman)", "Índice (LZW)", "Índice (Huffman)"))
    
    input_compressed_file = ""
    output_decompressed_file = ""
    decompression_algorithm = ""

    if "Banco de Dados (LZW)" in decompress_file_type:
        input_compressed_file = f"{APP_CONFIG['DB_FILE_NAME']}.lzw"
        output_decompressed_file = APP_CONFIG['DB_FILE_NAME'].replace('.db', '_decompressed.db')
        decompression_algorithm = "LZW"
    elif "Banco de Dados (Huffman)" in decompress_file_type:
        input_compressed_file = f"{APP_CONFIG['DB_FILE_NAME']}.huffman"
        output_decompressed_file = APP_CONFIG['DB_FILE_NAME'].replace('.db', '_decompressed.db')
        decompression_algorithm = "Huffman"
    elif "Índice (LZW)" in decompress_file_type:
        input_compressed_file = f"{APP_CONFIG['BTREE_INDEX_FILE_NAME']}.lzw"
        output_decompressed_file = APP_CONFIG['BTREE_INDEX_FILE_NAME'].replace('.idx', '_decompressed.idx')
        decompression_algorithm = "LZW"
    elif "Índice (Huffman)" in decompress_file_type:
        input_compressed_file = f"{APP_CONFIG['BTREE_INDEX_FILE_NAME']}.huffman"
        output_decompressed_file = APP_CONFIG['BTREE_INDEX_FILE_NAME'].replace('.idx', '_decompressed.idx')
        decompression_algorithm = "Huffman"

    full_input_path = os.path.join(APP_CONFIG["DB_DIR"], input_compressed_file)
    full_output_path = os.path.join(APP_CONFIG["DB_DIR"], output_decompressed_file)

    if st.button(f"Descomprimir Selecionado"):
        if not os.path.exists(full_input_path):
            st.error(f"Arquivo de entrada comprimido não encontrado: `{input_compressed_file}`")
            logger.warning(f"Decompression failed: Input file '{full_input_path}' not found.")
            return

        success = False
        if decompression_algorithm == "LZW":
            success = LZWCompression.lzw_decompress_file(full_input_path, full_output_path)
        elif decompression_algorithm == "Huffman":
            success = HuffmanCompression.huffman_decompress_file(full_input_path, full_output_path)

        if success:
            st.success(f"Arquivo `{input_compressed_file}` descomprimido com sucesso para `{output_decompressed_file}`!")
            logger.info(f"File '{input_compressed_file}' decompressed to {output_decompressed_file} using {decompression_algorithm}.")
        else:
            st.error(f"Falha ao descomprimir arquivo `{input_compressed_file}`.")


def display_cryptography_section():
    st.header("Criptografia de Arquivos")

    st.subheader("Gerar Chaves RSA")
    st.warning("Gerar novas chaves RSA substituirá quaisquer chaves existentes no diretório de chaves. Guarde a senha em local seguro!")
    rsa_password = st.text_input("Senha para a Chave Privada RSA (min. 8 caracteres)", type="password", key="rsa_gen_pass")
    rsa_password_confirm = st.text_input("Confirme a Senha", type="password", key="rsa_gen_pass_confirm")
    
    if st.button("Gerar Novas Chaves RSA"):
        if rsa_password != rsa_password_confirm:
            st.error("As senhas não coincidem.")
        elif len(rsa_password) < 8:
            st.error("A senha deve ter no mínimo 8 caracteres.")
        else:
            if CryptographyHandler.generate_rsa_keys(RSA_PRIVATE_KEY_PATH, RSA_PUBLIC_KEY_PATH, rsa_password):
                st.success("Chaves RSA geradas e salvas com sucesso!")
                logger.info("New RSA keys generated.")
            else:
                st.error("Falha ao gerar chaves RSA.")


    st.subheader("Criptografia Híbrida (AES + RSA)")
    file_type_encrypt = st.radio("Selecione o tipo de arquivo para criptografar:", ("Banco de Dados", "Índice"), key="encrypt_file_type")
    
    input_file_to_encrypt = APP_CONFIG["DB_FILE_NAME"] if file_type_encrypt == "Banco de Dados" else APP_CONFIG["BTREE_INDEX_FILE_NAME"]
    output_encrypted_file = f"{input_file_to_encrypt}.enc"

    full_input_path = os.path.join(APP_CONFIG["DB_DIR"], input_file_to_encrypt)
    full_output_path = os.path.join(APP_CONFIG["DB_DIR"], output_encrypted_file)

    if st.button(f"Criptografar {file_type_encrypt}"):
        if not os.path.exists(RSA_PUBLIC_KEY_PATH):
            st.error("Chave pública RSA não encontrada. Gere as chaves primeiro.")
            logger.warning("Encryption failed: RSA public key not found.")
        elif not os.path.exists(full_input_path):
            st.error(f"Arquivo de entrada não encontrado: `{input_file_to_encrypt}`")
            logger.warning(f"Encryption failed: Input file '{full_input_path}' not found.")
        else:
            if CryptographyHandler.hybrid_encrypt_file(full_input_path, full_output_path, RSA_PUBLIC_KEY_PATH):
                st.success(f"{file_type_encrypt} criptografado com sucesso para `{output_encrypted_file}`!")
                logger.info(f"{file_type_encrypt} encrypted to {output_encrypted_file}")
            else:
                st.error(f"Falha ao criptografar {file_type_encrypt}.")
    
    st.subheader("Descriptografia Híbrida (AES + RSA)")
    file_type_decrypt = st.radio("Selecione o tipo de arquivo para descriptografar:", ("Banco de Dados", "Índice"), key="decrypt_file_type")
    
    input_encrypted_file = f"{APP_CONFIG['DB_FILE_NAME']}.enc" if file_type_decrypt == "Banco de Dados" else f"{APP_CONFIG['BTREE_INDEX_FILE_NAME']}.enc"
    output_decrypted_file = input_encrypted_file.replace('.enc', '_decrypted.db') if file_type_decrypt == "Banco de Dados" else input_encrypted_file.replace('.enc', '_decrypted.idx')

    private_key_password_decrypt = st.text_input("Senha para a Chave Privada RSA para Descriptografar", type="password", key="rsa_decrypt_pass")

    if st.button(f"Descriptografar {file_type_decrypt}"):
        if not os.path.exists(RSA_PRIVATE_KEY_PATH):
            st.error("Chave privada RSA não encontrada.")
            logger.warning("Decryption failed: RSA private key not found.")
        elif not os.path.exists(os.path.join(APP_CONFIG["DB_DIR"], input_encrypted_file)):
            st.error(f"Arquivo criptografado não encontrado: `{input_encrypted_file}`")
            logger.warning(f"Decryption failed: Encrypted file '{input_encrypted_file}' not found.")
        else:
            full_input_path = os.path.join(APP_CONFIG["DB_DIR"], input_encrypted_file)
            full_output_path = os.path.join(APP_CONFIG["DB_DIR"], output_decrypted_file)

            if CryptographyHandler.hybrid_decrypt_file(full_input_path, full_output_path, RSA_PRIVATE_KEY_PATH, private_key_password_decrypt):
                st.success(f"{file_type_decrypt} descriptografado com sucesso para `{output_decrypted_file}`!")
                logger.info(f"{file_type_decrypt} decrypted to {output_decrypted_file}")
            else:
                st.error(f"Falha ao descriptografar {file_type_decrypt}.")
    
    st.subheader("Criptografia/Descriptografia Blowfish (Placeholder)")
    st.info("As funções Blowfish são apenas placeholders e não possuem uma implementação completa aqui.")
    CryptographyHandler.blowfish_encrypt_file()
    CryptographyHandler.blowfish_decrypt_file()


def display_admin_section():
    st.header("Administração")
    st.info(f"Diretório do Banco de Dados: `{APP_CONFIG['DB_DIR']}`")
    st.info(f"Arquivo Banco de Dados: `{APP_CONFIG['DB_FILE_NAME']}`")
    st.info(f"Arquivo Índice: `{APP_CONFIG['BTREE_INDEX_FILE_NAME']}`")
    st.info(f"Arquivo Contador ID: `{APP_CONFIG['ID_COUNTER_FILE_NAME']}`")
    st.info(f"Arquivo Lock: `{APP_CONFIG['LOCK_FILE_NAME']}`")
    st.info(f"Diretório de Backups: `{BACKUP_PATH}`")
    st.info(f"Arquivo de Log: `{LOG_FILE_PATH}`")
    st.info(f"Diretório de Chaves RSA: `{APP_CONFIG['RSA_KEYS_DIR']}`")
    st.info(f"Tamanho da Página B-Tree: `{APP_CONFIG['BTREE_PAGE_SIZE']}` bytes")
    st.info(f"Grau Mínimo B-Tree (t): `{APP_CONFIG['BTREE_MIN_DEGREE']}`")

    st.subheader("Manutenção do Banco de Dados")
    st.warning("A compactação pode levar um tempo e é recomendada para otimizar o espaço em disco após muitas exclusões/atualizações.")
    if st.button("Compactar Banco de Dados Agora"):
        if st.session_state.db_type == "Arquivo/Índice Padrão":
            st.session_state.db.compact_db()
        else:
            st.warning("A compactação da Árvore B não está implementada nesta versão. Esta função é apenas para o tipo 'Arquivo/Índice Padrão'.")


def display_activity_log():
    st.header("Log de Atividades")
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                log_content = f.read()
            st.text_area("Conteúdo do Log", log_content, height=400)
            if st.button("Limpar Log de Atividades"):
                with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                    f.write("")
                st.success("Log de atividades limpo.")
                logger.info("Activity log cleared via UI.")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler o arquivo de log: {e}")
            logger.error(f"Error reading activity log file: {e}")
    else:
        st.info("O arquivo de log de atividades ainda não existe.")


def display_about_section():
    st.header("Sobre o Aplicativo")
    st.write("Este é um protótipo de sistema de gerenciamento de banco de dados para acidentes de trânsito.")
    st.markdown("""
        **Desenvolvido por:** [Seu Nome/Organização]
        **Versão:** 1.0.0 Alpha
        **Recursos:**
        - Gerenciamento CRUD de registros
        - Importação e exportação de CSV
        - Backup e restauração do banco de dados
        - Compressão de arquivos (LZW, Huffman - placeholders)
        - Criptografia híbrida (AES-256 + RSA-2048)
        - Gerenciamento de log de atividades
        - Suporte a indexação (índice simples ou B-tree - placeholder)

        **Tecnologias Utilizadas:**
        - Python
        - Streamlit para a interface do usuário
        - `pickle` para serialização de objetos
        - `struct` para manipulação de bytes
        - `filelock` para controle de concorrência
        - `cryptography` (ou `PyCryptodome`) para criptografia
        - Implementações básicas de LZW e Huffman
    """)


# --- Main Application Entry Point ---
if __name__ == "__main__":
    try:
        # Ensure base directories exist
        Path(APP_CONFIG["DB_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
        Path(APP_CONFIG["RSA_KEYS_DIR"]).mkdir(parents=True, exist_ok=True)
        # Placeholder for Huffman/LZW specific folders if needed by their implementations
        # Path(HUFFMAN_FOLDER).mkdir(parents=True, exist_ok=True)
        # Path(LZW_FOLDER).mkdir(parents=True, exist_ok=True)
        
        setup_ui()
    except OSError as e:
        st.error(f"🚨 Crítico: Não foi possível criar os diretórios necessários. Verifique as permissões para `{APP_CONFIG['DB_DIR']}`. Erro: {e}")
        logger.critical(f"Initial directory creation failed: {traceback.format_exc()}")
        st.stop() # Interrompe o aplicativo se os diretórios não puderem ser criados
    except Exception as e:
        st.error(f"🚨 Ocorreu um erro inesperado na inicialização: {e}")
        logger.critical(f"Unhandled error during initialization: {traceback.format_exc()}")
        st.stop()