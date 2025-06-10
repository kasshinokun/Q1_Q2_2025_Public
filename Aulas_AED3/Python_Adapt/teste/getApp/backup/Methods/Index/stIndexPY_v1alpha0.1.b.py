# -*- coding: utf-8 -*-
"""
Gerenciador de Banco de Dados de Acidentes de Trânsito Aprimorado

Este script é uma fusão e melhoria de múltiplos arquivos Python:
- stCRUDDataObjectPY_v3alpha.py (Base da UI)
- stCRUDDataObjectPY_v4epsilon.py (Configuração e Indexação)
- stCRUDDataObjectPY_v5alpha0.1.e.py (DataObject e Classe DB Robusta)
- stCRUDDataObjectPY_v5alpha0.2.a.py (Implementação da Árvore B - Placeholder)
- stHuffman_v5.py (Compressão Huffman - Placeholder)
- stLZWPY_v4.py (Compressão LZW - Placeholder)
- AES_RSA.py / pycryptonew.py (Funções de Criptografia)

O resultado é uma aplicação Streamlit completa e rica em recursos que oferece:
- Escolha entre um banco de dados padrão baseado em arquivo/índice e um motor baseado em B-Tree (placeholder).
- Um DataObject robusto com validação extensiva.
- Funcionalidade CRUD completa (Criar, Ler, Atualizar, Deletar).
- Importação/exportação em massa via CSV.
- Capacidades de backup e restauração do banco de dados.
- Utilitários integrados de compressão/descompressão de arquivos (Huffman & LZW - Placeholder).
- Funções de criptografia/descriptografia híbrida (AES + RSA).
- Um log de atividades e funções administrativas.
- Interface de usuário aprimorada com navegação por selectbox, ícones e CSS personalizado.
"""

import streamlit as st
import os
import filelock
import logging
import traceback
from datetime import datetime, date
from collections import OrderedDict, Counter, deque
import re
import getpass # Para entrada de senha (apesar de não funcionar diretamente no Streamlit, mantido por contexto)
from pathlib import Path
from typing import List, Dict, Optional, Union, Callable, Any, Iterator, Tuple
import shutil
import tempfile
import math
import heapq
import io
import csv
import struct
import json
import hashlib
import time

# --- Criptografia Imports (adaptado de pycryptonew.py) ---
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False # Define como False se a biblioteca não estiver instalada

# --- Constantes de Configuração (Centralizadas) ---
APP_CONFIG = {
    "DB_DIR": os.path.join(Path.home(), 'Documents', 'Data'),
    "DB_FILE_NAME": 'traffic_accidents.db',
    "BTREE_DB_FILE_NAME": 'traffic_accidents_btree.db', # Nome do arquivo de dados da B-Tree
    "INDEX_FILE_NAME": 'index.idx',
    "LOCK_FILE_NAME": 'traffic_accidents.lock',
    "ID_COUNTER_FILE_NAME": 'id_counter.dat', # Arquivo para ID auto-incremento
    "BACKUP_DIR_NAME": 'backups',
    "CSV_DELIMITER": ';',
    "MAX_RECORDS_PER_PAGE": 20,
    "MAX_FILE_SIZE_MB": 100, # Tamanho máximo do arquivo CSV para importação
    "CHUNK_SIZE": 4096,     # Tamanho do chunk para operações de arquivo
    "MAX_BACKUPS": 5,       # Número máximo de backups a manter
    "MAX_LOG_ENTRIES_DISPLAY": 10, # Número de entradas de log a exibir
    "LOG_FILE_NAME": 'traffic_accidents.log',
    "HUFFMAN_FOLDER_NAME": "Huffman",
    "LZW_FOLDER_NAME": "LZW",
    "RSA_KEYS_DIR_NAME": "rsa_keys",
    "COMPRESSED_DB_EXTENSION": ".comp", # Extensão para arquivos de DB compactados
    "ENCRYPTED_DB_EXTENSION": ".enc",   # Extensão para arquivos de DB criptografados
    "BTREE_PAGE_SIZE": 4096, # Tamanho da página em bytes para a B-Tree
    "BTREE_MIN_DEGREE": 3,   # Grau mínimo (t) para a B-Tree (t >= 2)
    "HUFFMAN_COMPRESSED_EXTENSION": ".huff",
    "LZW_COMPRESSED_EXTENSION": ".lzw",
}

# --- Caminhos Derivados ---
DB_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["DB_FILE_NAME"])
BTREE_DB_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["BTREE_DB_FILE_NAME"])
INDEX_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["INDEX_FILE_NAME"])
LOCK_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOCK_FILE_NAME"])
ID_COUNTER_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["ID_COUNTER_FILE_NAME"])
BACKUP_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["BACKUP_DIR_NAME"])
LOG_FILE_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOG_FILE_NAME"])
HUFFMAN_FOLDER = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["HUFFMAN_FOLDER_NAME"])
LZW_FOLDER = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LZW_FOLDER_NAME"])
RSA_KEYS_DIR = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["RSA_KEYS_DIR_NAME"])

# Caminhos das Chaves RSA
RSA_PUBLIC_KEY_PATH = os.path.join(RSA_KEYS_DIR, "public_key.pem")
RSA_PRIVATE_KEY_PATH = os.path.join(RSA_KEYS_DIR, "private_key.pem")

# --- Configuração de Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CSS Personalizado ---
def apply_custom_css():
    """Injeta estilos CSS personalizados para aprimorar a UI do Streamlit."""
    st.markdown("""
    <style>
    /* Estilo para a barra lateral */
    .st-emotion-cache-1ldf0df { /* Target the sidebar background element */
        background-color: #f0f2f6; /* Light gray background */
        border-right: 1px solid #e0e0e0;
        box-shadow: 2px 0 5px rgba(0,0,0,0.05);
    }

    /* Estilo para o título principal no sidebar */
    .st-emotion-cache-1ldf0df h1 {
        color: #1a1a1a; /* Darker text */
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 20px;
    }

    /* Estilo para o selectbox no sidebar */
    .st-emotion-cache-1ldf0df .stSelectbox {
        margin-bottom: 15px;
    }

    /* Estilo para as opções do selectbox */
    .st-emotion-cache-1ldf0df .stSelectbox > div > div > div {
        background-color: #ffffff; /* White background for options */
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 10px;
        color: #333;
        transition: all 0.2s ease-in-out;
    }
    
    /* Estilo quando uma opção do selectbox é selecionada */
    .st-emotion-cache-1ldf0df .stSelectbox > div > div > div:focus,
    .st-emotion-cache-1ldf0df .stSelectbox > div > div > div:hover {
        border-color: #007bff; /* Highlight color */
        box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
        background-color: #e6f2ff; /* Lighter blue on hover */
    }

    /* Estilo para os headers (h1, h2, h3) no conteúdo principal */
    .st-emotion-cache-h5rpmi h1, .st-emotion-cache-h5rpmi h2, .st-emotion-cache-h5rpmi h3 { /* Adjusted selector for broader applicability */
        color: #0056b3; /* Darker blue for headers */
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    /* Cards para seções */
    .st-emotion-cache-nahz7x { /* Target specific block containers for card effect */
        background-color: #ffffff;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Títulos dentro dos cards */
    .st-emotion-cache-nahz7x h2 {
        color: #007bff;
        margin-top: 0;
    }

    /* Ajustar o padding do main content */
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    /* Estilo para os botões */
    .stButton > button {
        background-color: #007bff;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease, transform 0.1s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .stButton > button:hover {
        background-color: #0056b3;
        transform: translateY(-1px);
    }

    .stButton > button:active {
        transform: translateY(0);
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.15);
    }

    /* Estilo para mensagens de sucesso, erro, info, warning */
    .stSuccess {
        background-color: #d4edda;
        color: #155724;
        border-left: 5px solid #28a745;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .stError {
        background-color: #f8d7da;
        color: #721c24;
        border-left: 5px solid #dc3545;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .stWarning {
        background-color: #fff3cd;
        color: #856404;
        border-left: 5px solid #ffc107;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .stInfo {
        background-color: #d1ecf1;
        color: #0c5460;
        border-left: 5px solid #17a2b8;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Custom Exception for Data Validation ---
class DataValidationError(ValueError):
    """Exceção personalizada para erros de validação de dados."""
    pass

# --- DataObject Class ---
class DataObject:
    """Representa um único registro de dados de acidente de trânsito com validação."""
    # Defina os campos obrigatórios e seus tipos esperados para validação
    REQUIRED_FIELDS = [
        "id", "data_ocorrencia", "uf", "br", "km", "municipio",
        "causa_acidente", "tipo_acidente", "classificacao_acidente",
        "fase_dia", "condicao_metereologica", "tipo_pista", "tracado_via",
        "uso_solo", "pessoas", "mortos", "feridos_leves", "feridos_graves",
        "ilesos", "ignorados", "feridos", "veiculos"
    ]

    FIELD_TYPES = {
        "id": int, "data_ocorrencia": str, "uf": str, "br": str, "km": str,
        "municipio": str, "causa_acidente": str, "tipo_acidente": str,
        "classificacao_acidente": str, "fase_dia": str,
        "condicao_metereologica": str, "tipo_pista": str, "tracado_via": str,
        "uso_solo": str, "pessoas": int, "mortos": int, "feridos_leves": int,
        "feridos_graves": int, "ilesos": int, "ignorados": int, "feridos": int,
        "veiculos": int
    }
    
    # Opções válidas para campos de seleção (combobox/radio buttons)
    VALID_OPTIONS = {
        "classificacao_acidente": ["Sem Vítimas", "Com Vítimas Feridas", "Com Vítimas Fatais"],
        "fase_dia": ["Plena Noite", "Amanhecer", "Pleno Dia", "Anoitecer"],
        "condicao_metereologica": ["Céu Claro", "Chuva", "Garoa/Chuvisco", "Nevoa/Neblina", "Vento", "Granizo", "Céu Nublado", "Sol", "Ignorada"],
        "tipo_pista": ["Dupla", "Simples", "Múltipla", "Múltiplas pistas"],
        "tracado_via": ["Reta", "Curva", "Interseção", "Retorno", "Desvio", "Viaduto", "Ponte", "Túnel", "Rotatória"],
        "uso_solo": ["Rural", "Urbano"]
    }

    def __init__(self, **kwargs):
        self.data = {}
        for field in self.REQUIRED_FIELDS:
            value = kwargs.get(field)
            if value is None:
                # Allow 'id' to be None for new records, it will be assigned by DB
                if field != "id": 
                    raise DataValidationError(f"Campo obrigatório faltando: '{field}'")
            
            # Tenta converter o tipo se não for None e tiver um tipo definido
            if value is not None and field in self.FIELD_TYPES:
                try:
                    if self.FIELD_TYPES[field] == int:
                        value = int(value)
                    elif self.FIELD_TYPES[field] == float:
                        value = float(value)
                    elif self.FIELD_TYPES[field] == str:
                        value = str(value).strip() # Remove espaços em branco para strings
                except ValueError:
                    raise DataValidationError(f"Tipo inválido para o campo '{field}': esperado {self.FIELD_TYPES[field].__name__}, recebido '{value}'")
            
            # Validações específicas
            if field == "data_ocorrencia" and value:
                try:
                    datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    raise DataValidationError(f"Data de ocorrência inválida: {value}. Formato esperado AAAA-MM-DD.")
            
            if field == "uf" and value and (not isinstance(value, str) or len(value) != 2 or not value.isalpha() or not value.isupper()):
                raise DataValidationError(f"UF inválido: {value}. Deve ser uma string de 2 letras maiúsculas.")
            
            if field in ["pessoas", "mortos", "feridos_leves", "feridos_graves", "ilesos", "ignorados", "feridos", "veiculos"] and value is not None:
                if not isinstance(value, int) or value < 0:
                    raise DataValidationError(f"Campo '{field}' inválido: {value}. Esperado um número inteiro não negativo.")
            
            if field in self.VALID_OPTIONS and value and value not in self.VALID_OPTIONS[field]:
                raise DataValidationError(f"Valor inválido para o campo '{field}': {value}. Opções válidas: {', '.join(self.VALID_OPTIONS[field])}")
            
            self.data[field] = value

    def __getattr__(self, name):
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name == 'data': # Permite definir o dicionário interno diretamente
            super().__setattr__(name, value)
            return

        if name in self.REQUIRED_FIELDS:
            # Type conversion and validation logic should ideally be applied here too
            # For simplicity in setter, we directly assign. Full validation is in __init__
            self.data[name] = value
        else:
            super().__setattr__(name, value)

    def to_dict(self) -> Dict[str, Any]:
        return self.data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)

    @staticmethod
    def from_csv_row(row: List[str]):
        """
        Cria um DataObject a partir de uma lista de strings (linha CSV).
        Assume uma ordem específica para as colunas CSV.
        Ajuste os índices e o mapeamento de acordo com a estrutura real do seu CSV.
        """
        # Mapeamento assumido da ordem do CSV para os campos do DataObject
        # Esta ordem deve corresponder EXATAMENTE à ordem das colunas no seu arquivo CSV,
        # após o cabeçalho.
        if len(row) < 21: # Mínimo de campos esperados (excluindo ID)
            raise DataValidationError(f"Linha CSV tem poucos campos: {len(row)}, esperado pelo menos 21.")
            
        kwargs = {
            "data_ocorrencia": row[0],
            "uf": row[1],
            "br": row[2],
            "km": row[3],
            "municipio": row[4],
            "causa_acidente": row[5],
            "tipo_acidente": row[6],
            "classificacao_acidente": row[7],
            "fase_dia": row[8],
            "condicao_metereologica": row[9],
            "tipo_pista": row[10],
            "tracado_via": row[11],
            "uso_solo": row[12],
            "pessoas": row[13],
            "mortos": row[14],
            "feridos_leves": row[15],
            "feridos_graves": row[16],
            "ilesos": row[17],
            "ignorados": row[18],
            "feridos": row[19],
            "veiculos": row[20]
        }
        return DataObject(**kwargs) # O construtor DataObject fará a validação e conversão de tipo

    def to_csv_row(self) -> List[str]:
        """Converte o DataObject para uma lista de strings para exportação CSV."""
        # A ordem aqui deve corresponder à ordem esperada por from_csv_row (excluindo o ID)
        return [
            str(self.data_ocorrencia) if self.data_ocorrencia is not None else '',
            str(self.uf) if self.uf is not None else '',
            str(self.br) if self.br is not None else '',
            str(self.km) if self.km is not None else '',
            str(self.municipio) if self.municipio is not None else '',
            str(self.causa_acidente) if self.causa_acidente is not None else '',
            str(self.tipo_acidente) if self.tipo_acidente is not None else '',
            str(self.classificacao_acidente) if self.classificacao_acidente is not None else '',
            str(self.fase_dia) if self.fase_dia is not None else '',
            str(self.condicao_metereologica) if self.condicao_metereologica is not None else '',
            str(self.tipo_pista) if self.tipo_pista is not None else '',
            str(self.tracado_via) if self.tracado_via is not None else '',
            str(self.uso_solo) if self.uso_solo is not None else '',
            str(self.pessoas) if self.pessoas is not None else '',
            str(self.mortos) if self.mortos is not None else '',
            str(self.feridos_leves) if self.feridos_leves is not None else '',
            str(self.feridos_graves) if self.feridos_graves is not None else '',
            str(self.ilesos) if self.ilesos is not None else '',
            str(self.ignorados) if self.ignorados is not None else '',
            str(self.feridos) if self.feridos is not None else '',
            str(self.veiculos) if self.veiculos is not None else ''
        ]

    def __repr__(self):
        return f"DataObject(id={self.id}, uf='{self.uf}', municipio='{self.municipio}', ...)"

# --- TrafficAccidentsDB Class (Banco de Dados Padrão) ---
class TrafficAccidentsDB:
    """Gerencia registros de acidentes de trânsito usando um arquivo flat e um índice simples em memória."""
    def __init__(self, db_path, index_path, lock_path, id_counter_path):
        self.db_path = db_path
        self.index_path = index_path
        self.lock_path = lock_path
        self.id_counter_path = id_counter_path
        self._next_id = 1
        self.records_index: Dict[int, int] = {} # {id: file_offset}
        self.db_file_size = 0 # Rastreia o tamanho do arquivo para lógica de append-only
        
        # Garante que o diretório exista antes de qualquer operação de arquivo
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._load_id_counter()
        self._rebuild_index() # Sempre reconstrói o índice na inicialização para robustez

    def _get_lock(self):
        """Adquire um bloqueio de arquivo."""
        return filelock.FileLock(self.lock_path, timeout=5)

    def _load_id_counter(self):
        """Carrega o próximo ID disponível de um arquivo dedicado."""
        if os.path.exists(self.id_counter_path):
            try:
                with open(self.id_counter_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self._next_id = int(content) + 1
                    else:
                        self._next_id = 1
            except Exception as e:
                logger.warning(f"Falha ao carregar o contador de IDs de {self.id_counter_path}, redefinindo para 1: {e}")
                self._next_id = 1
        else:
            self._next_id = 1
        logger.info(f"Contador de IDs inicializado para: {self._next_id}")

    def _save_id_counter(self):
        """Salva o contador de IDs atual em um arquivo dedicado."""
        try:
            with self._get_lock(): # Bloqueia durante o salvamento do contador de IDs
                with open(self.id_counter_path, 'w', encoding='utf-8') as f:
                    f.write(str(self._next_id - 1)) # Salva o último ID atribuído
        except Exception as e:
            logger.error(f"Erro ao salvar o contador de IDs em {self.id_counter_path}: {traceback.format_exc()}")

    def _rebuild_index(self):
        """Reconstrói o índice em memória escaneando o arquivo DB."""
        self.records_index = {}
        current_offset = 0
        if not os.path.exists(self.db_path):
            self.db_file_size = 0
            return

        try:
            with open(self.db_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_len = len(line.encode('utf-8')) # Obtém o comprimento real em bytes para o offset
                    if line.strip(): # Processa apenas linhas não vazias
                        try:
                            record_data = json.loads(line.strip())
                            record_id = record_data.get('id')
                            if record_id is not None:
                                self.records_index[record_id] = current_offset
                            else:
                                logger.warning(f"Pulando registro sem ID: {line.strip()}")
                        except json.JSONDecodeError as e:
                            logger.warning(f"Pulando linha JSON malformada no DB: {line.strip()} - Erro: {e}")
                    current_offset += line_len
            self.db_file_size = current_offset
            logger.info(f"Índice reconstruído. {len(self.records_index)} registros indexados. Tamanho do DB: {self.db_file_size} bytes.")
        except Exception as e:
            logger.error(f"Erro ao reconstruir o índice para {self.db_path}: {traceback.format_exc()}")
            self.records_index = {} # Limpa o índice se ocorrer um erro

    def add_record(self, data_obj: DataObject) -> Optional[int]:
        """Adiciona um novo registro ao banco de dados."""
        try:
            with self._get_lock():
                data_obj.id = self._next_id
                record_json = json.dumps(data_obj.to_dict(), ensure_ascii=False) + '\n'
                
                # Anexa ao arquivo
                with open(self.db_path, 'a', encoding='utf-8') as f:
                    file_offset = f.tell() # Obtém o offset atual do arquivo antes de escrever
                    f.write(record_json)
                
                self.records_index[data_obj.id] = file_offset
                self.db_file_size += len(record_json.encode('utf-8'))
                self._next_id += 1
                self._save_id_counter()
                logger.info(f"Registro adicionado: ID {data_obj.id}")
                return data_obj.id
        except Exception as e:
            logger.error(f"Erro ao adicionar registro: {traceback.format_exc()}")
            st.error(f"Erro ao adicionar registro: {e}")
            return None

    def get_record(self, record_id: int) -> Optional[DataObject]:
        """Recupera um registro pelo seu ID usando o índice."""
        offset = self.records_index.get(record_id)
        if offset is None:
            return None # Registro não encontrado no índice

        try:
            with self._get_lock():
                with open(self.db_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(offset)
                    line = f.readline()
                    if line.strip():
                        record_data = json.loads(line.strip())
                        if record_data.get('id') == record_id: # Verifica o ID
                            return DataObject.from_dict(record_data)
                        else:
                            # Este cenário indica um índice corrompido ou um DB compactado sem reconstrução do índice
                            logger.warning(f"Inconsistência de índice para o ID {record_id} no offset {offset}. Reconstruindo o índice.")
                            self._rebuild_index() # Tenta reconstruir o índice
                            # Em seguida, tenta obter o registro novamente
                            offset_after_rebuild = self.records_index.get(record_id)
                            if offset_after_rebuild is not None:
                                f.seek(offset_after_rebuild)
                                line_after_rebuild = f.readline()
                                if line_after_rebuild.strip():
                                    record_data_after_rebuild = json.loads(line_after_rebuild.strip())
                                    if record_data_after_rebuild.get('id') == record_id:
                                        return DataObject.from_dict(record_data_after_rebuild)
            return None # Registro não encontrado após a reconstrução ou ainda inválido
        except Exception as e:
            logger.error(f"Erro ao obter o registro ID {record_id}: {traceback.format_exc()}")
            return None

    def update_record(self, record_id: int, new_data_obj: DataObject) -> bool:
        """
        Atualiza um registro existente. Isso envolve marcar o registro antigo como excluído
        e anexar o novo, depois reconstruir o índice.
        Para simplicidade, esta implementação realiza uma reescrita completa.
        Uma abordagem mais otimizada usaria "mark-and-sweep" com compactação.
        """
        if record_id not in self.records_index:
            logger.warning(f"Tentativa de atualizar registro inexistente: ID {record_id}")
            return False
        
        try:
            # Para simplicidade e robustez, leremos tudo, modificaremos e reescreveremos.
            # Para arquivos grandes, uma estratégia de compactação é necessária.
            all_records = self.get_all_records()
            found = False
            with self._get_lock():
                with open(self.db_path, 'w', encoding='utf-8') as f:
                    for record in all_records:
                        if record.id == record_id:
                            new_data_obj.id = record_id # Garante que o ID seja preservado
                            record_json = json.dumps(new_data_obj.to_dict(), ensure_ascii=False) + '\n'
                            f.write(record_json)
                            found = True
                            logger.info(f"Registro atualizado: ID {record_id}")
                        else:
                            record_json = json.dumps(record.to_dict(), ensure_ascii=False) + '\n'
                            f.write(record_json)
            
            self._rebuild_index() # Reconstrói o índice após a reescrita
            return found
        except Exception as e:
            logger.error(f"Erro ao atualizar o registro ID {record_id}: {traceback.format_exc()}")
            st.error(f"Erro ao atualizar o registro ID {record_id}: {e}")
            return False

    def delete_record(self, record_id: int) -> bool:
        """
        Exclui um registro. Semelhante à atualização, isso atualmente executa uma reescrita completa.
        A compactação é necessária para a verdadeira recuperação de espaço.
        """
        if record_id not in self.records_index:
            logger.warning(f"Tentativa de excluir registro inexistente: ID {record_id}")
            return False
        
        try:
            all_records = self.get_all_records()
            found = False
            new_records = []
            for record in all_records:
                if record.id != record_id:
                    new_records.append(record)
                else:
                    found = True

            with self._get_lock():
                with open(self.db_path, 'w', encoding='utf-8') as f:
                    for record in new_records:
                        record_json = json.dumps(record.to_dict(), ensure_ascii=False) + '\n'
                        f.write(record_json)
            
            self._rebuild_index() # Reconstrói o índice após a reescrita
            if found:
                logger.info(f"Registro excluído: ID {record_id}")
            return found
        except Exception as e:
            logger.error(f"Erro ao excluir o registro ID {record_id}: {traceback.format_exc()}")
            st.error(f"Erro ao excluir o registro ID {record_id}: {e}")
            return False

    def get_all_records(self) -> List[DataObject]:
        """Recupera todos os registros, útil para varreduras completas ou exibição na UI."""
        records = []
        if not os.path.exists(self.db_path):
            return records
        
        try:
            with self._get_lock():
                with open(self.db_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if line.strip():
                            try:
                                record_data = json.loads(line.strip())
                                records.append(DataObject.from_dict(record_data))
                            except json.JSONDecodeError as e:
                                logger.warning(f"Pulando linha JSON malformada durante get_all_records: {line.strip()} - Erro: {e}")
            return records
        except Exception as e:
            logger.error(f"Erro ao obter todos os registros: {traceback.format_exc()}")
            st.error(f"Erro ao obter todos os registros: {e}")
            return []

    def count_records(self) -> int:
        """Retorna o número total de registros ativos com base no índice."""
        return len(self.records_index)

    def list_records(self, page: int = 1, records_per_page: int = APP_CONFIG["MAX_RECORDS_PER_PAGE"]) -> List[DataObject]:
        """Lista registros com paginação."""
        all_ids = sorted(self.records_index.keys())
        start_index = (page - 1) * records_per_page
        end_index = start_index + records_per_page
        
        records = []
        for record_id in all_ids[start_index:end_index]:
            record = self.get_record(record_id)
            if record: # Garante que o registro não seja None (ex: devido a corrupção)
                records.append(record)
        return records

    def compact_db(self):
        """
        Reescreve o arquivo do banco de dados para remover registros excluídos/obsoletos.
        Isso efetivamente recupera espaço.
        """
        st.info("Iniciando compactação do banco de dados (pode demorar para arquivos grandes)...")
        logger.info("Iniciando compactação do banco de dados.")
        
        temp_db_path = self.db_path + ".tmp_compact"
        records_to_keep = self.get_all_records() # Obtém apenas registros válidos e atuais

        try:
            with self._get_lock():
                with open(temp_db_path, 'w', encoding='utf-8') as f_tmp:
                    for record in records_to_keep:
                        record_json = json.dumps(record.to_dict(), ensure_ascii=False) + '\n'
                        f_tmp.write(record_json)
            
            # Substitui o arquivo DB antigo pelo compactado
            os.replace(temp_db_path, self.db_path)
            self._rebuild_index() # Reconstrói o índice para refletir novos offsets
            logger.info("Compactação do banco de dados concluída com sucesso.")
            st.success("Banco de dados compactado com sucesso!")
        except Exception as e:
            logger.error(f"Erro durante a compactação do banco de dados: {traceback.format_exc()}")
            st.error(f"Erro durante a compactação do banco de dados: {e}")
        finally:
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path) # Limpa o arquivo temporário

# --- TrafficAccidentsTree Class (Placeholder for B-Tree DB) ---
class TrafficAccidentsTree:
    """
    Placeholder para a implementação da Árvore B em disco.
    As operações CRUD são simuladas ou retornam mensagens de aviso.
    """
    def __init__(self, db_file_name: str):
        self.db_file_path = os.path.join(APP_CONFIG["DB_DIR"], db_file_name)
        # Dummy attributes for UI display and basic functionality
        self.pager = type('Pager', (object,), {
            'db_file_path': self.db_file_path,
            'file': type('File', (object,), {'close': lambda: None})(), # Mock file object
            'num_pages': 0 # Mock number of pages
        })()
        self.order = APP_CONFIG["BTREE_MIN_DEGREE"] # Or 2 * APP_CONFIG["BTREE_MIN_DEGREE"] - 1
        self.t = APP_CONFIG["BTREE_MIN_DEGREE"]
        
        # Simulação de dados para a UI
        if "btree_records" not in st.session_state:
            st.session_state.btree_records = {} # {id: DataObject}
        if "btree_next_id" not in st.session_state:
            st.session_state.btree_next_id = 1
        
        st.info(f"B-Tree DB inicializado (placeholder): `{self.db_file_path}`")

    def add_record(self, data_obj: DataObject) -> Optional[int]:
        """Simula a adição de um registro na B-Tree."""
        new_id = st.session_state.btree_next_id
        data_obj.id = new_id
        st.session_state.btree_records[new_id] = data_obj
        st.session_state.btree_next_id += 1
        st.warning("B-Tree add_record: Função é um placeholder. Registro adicionado apenas na simulação em memória.")
        logger.info(f"B-Tree placeholder: Simulated add of record ID {data_obj.id}")
        return new_id

    def get_record(self, record_id: int) -> Optional[DataObject]:
        """Simula a busca de um registro na B-Tree."""
        st.warning("B-Tree get_record: Função é um placeholder.")
        logger.info(f"B-Tree placeholder: Simulated search for record ID {record_id}")
        return st.session_state.btree_records.get(record_id)

    def update_record(self, record_id: int, new_data_obj: DataObject) -> bool:
        """Simula a atualização de um registro na B-Tree."""
        if record_id in st.session_state.btree_records:
            new_data_obj.id = record_id
            st.session_state.btree_records[record_id] = new_data_obj
            st.warning("B-Tree update_record: Função é um placeholder. Registro atualizado apenas na simulação em memória.")
            logger.info(f"B-Tree placeholder: Simulated update of record ID {record_id}")
            return True
        st.warning("B-Tree update_record: Função é um placeholder. Registro não encontrado para atualização.")
        return False

    def delete_record(self, record_id: int) -> bool:
        """Simula a exclusão de um registro da B-Tree."""
        if record_id in st.session_state.btree_records:
            del st.session_state.btree_records[record_id]
            st.warning("B-Tree delete_record: Função é um placeholder. Registro excluído apenas na simulação em memória.")
            logger.info(f"B-Tree placeholder: Simulated delete of record ID {record_id}")
            return True
        st.warning("B-Tree delete_record: Função é um placeholder. Registro não encontrado para exclusão.")
        return False

    def get_all_records(self) -> List[DataObject]:
        """Retorna todos os registros simulados da B-Tree."""
        st.warning("B-Tree get_all_records: Função é um placeholder. Retornando dados simulados.")
        return list(st.session_state.btree_records.values())
    
    def count_records(self) -> int:
        """Retorna a contagem de registros simulados da B-Tree."""
        return len(st.session_state.btree_records)

    def list_records(self, page: int = 1, records_per_page: int = APP_CONFIG["MAX_RECORDS_PER_PAGE"]) -> List[DataObject]:
        """Lista registros simulados com paginação para a B-Tree."""
        all_ids = sorted(st.session_state.btree_records.keys())
        start_index = (page - 1) * records_per_page
        end_index = start_index + records_per_page
        
        records = []
        for record_id in all_ids[start_index:end_index]:
            records.append(st.session_state.btree_records[record_id])
        return records

    def get_size(self) -> int:
        """Retorna o tamanho do arquivo da B-Tree (simulado ou real se existir)."""
        if os.path.exists(self.db_file_path):
            return os.path.getsize(self.db_file_path)
        return 0 # Placeholder if file doesn't exist

    def get_num_nodes(self) -> int:
        """Retorna o número de nós na B-Tree (placeholder)."""
        return max(1, len(st.session_state.btree_records) // APP_CONFIG["BTREE_MIN_DEGREE"]) # Simulação
        
    def get_depth(self) -> int:
        """Retorna a profundidade da B-Tree (placeholder)."""
        return max(1, math.ceil(math.log(len(st.session_state.btree_records) + 1, APP_CONFIG["BTREE_MIN_DEGREE"]))) # Simulação

    def clear(self) -> bool:
        """Limpa o arquivo do DB da B-Tree e os dados simulados."""
        try:
            if os.path.exists(self.db_file_path):
                # Tenta fechar o arquivo antes de remover se estiver aberto
                if hasattr(self.pager, 'file') and not self.pager.file.closed:
                    self.pager.file.close()
                os.remove(self.db_file_path)
            st.session_state.btree_records = {} # Limpa os registros simulados
            st.session_state.btree_next_id = 1
            st.success("Banco de dados B-Tree e registros simulados limpos.")
            logger.info("B-Tree DB file and simulated records cleared.")
            return True
        except Exception as e:
            st.error(f"Erro ao limpar B-Tree DB: {e}")
            logger.error(f"Error clearing B-Tree DB: {traceback.format_exc()}")
            return False

# --- Classes de Compressão (Placeholders) ---
class HuffmanProcessor:
    @staticmethod
    def compress_file(input_path: str, output_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[int, int, float, float]:
        st.warning("Huffman compress_file: Implementação de compressão não fornecida. Nenhuma ação realizada.")
        logger.warning("Huffman compress_file called but not implemented.")
        
        # Simular um resultado para a UI
        if os.path.exists(input_path):
            original_size = os.path.getsize(input_path)
            simulated_compressed_size = int(original_size * 0.5) # 50% compression
            with open(output_path, 'wb') as f:
                f.write(b'\x00' * simulated_compressed_size) # Create dummy file
            return simulated_compressed_size, original_size, 50.0, 0.1
        return 0, 0, 0.0, 0.0 # compressed_size, original_size, ratio, time_taken

    @staticmethod
    def decompress_file(input_path: str, output_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[int, int, float, float]:
        st.warning("Huffman decompress_file: Implementação de descompressão não fornecida. Nenhuma ação realizada.")
        logger.warning("Huffman decompress_file called but not implemented.")
        
        # Simular um resultado para a UI
        if os.path.exists(input_path):
            compressed_size = os.path.getsize(input_path)
            simulated_decompressed_size = int(compressed_size * 2.0) # Assume 50% compression, so 2x bigger
            with open(output_path, 'wb') as f:
                f.write(b'\x00' * simulated_decompressed_size) # Create dummy file
            return compressed_size, simulated_decompressed_size, 50.0, 0.1
        return 0, 0, 0.0, 0.0 # compressed_size, decompressed_size, ratio, time_taken

class LZWProcessor:
    @staticmethod
    def compress(input_file_path: str, output_file_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        st.warning("LZW compress: Implementação de compressão não fornecida. Nenhuma ação realizada.")
        logger.warning("LZW compress called but not implemented.")
        
        # Simular sucesso
        if os.path.exists(input_file_path):
            original_size = os.path.getsize(input_file_path)
            simulated_compressed_size = int(original_size * 0.6) # 40% compression
            with open(output_file_path, 'wb') as f:
                f.write(b'\x00' * simulated_compressed_size) # Create dummy file
            return True
        return False

    @staticmethod
    def decompress(input_file_path: str, output_file_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        st.warning("LZW decompress: Implementação de descompressão não fornecida. Nenhuma ação realizada.")
        logger.warning("LZW decompress called but not implemented.")
        
        # Simular sucesso
        if os.path.exists(input_file_path):
            compressed_size = os.path.getsize(input_file_path)
            simulated_decompressed_size = int(compressed_size * 1.66) # Inverse of 40% compression
            with open(output_file_path, 'wb') as f:
                f.write(b'\x00' * simulated_decompressed_size) # Create dummy file
            return True
        return False

# --- Funções da UI ---

def display_record_management_section():
    """Exibe a interface para operações CRUD de registros."""
    st.header("🗃️ Gerenciamento de Registros")
    
    current_db = st.session_state.db if not st.session_state.use_btree else st.session_state.btree_db
    st.info(f"Banco de Dados Ativo: **{'Standard DB' if not st.session_state.use_btree else 'B-Tree DB (Placeholder)'}**")

    # Define os campos comuns para entrada, excluindo ID que é auto-gerado
    common_fields_ui = [
        ("data_ocorrencia", "Data da Ocorrência (AAAA-MM-DD)", "2023-01-15", "text"),
        ("uf", "UF (Ex: MG)", "MG", "text"),
        ("br", "BR", "381", "text"),
        ("km", "KM", "490.5", "text"),
        ("municipio", "Município", "BELO HORIZONTE", "text"),
        ("causa_acidente", "Causa do Acidente", "Falta de Atenção", "text"),
        ("tipo_acidente", "Tipo de Acidente", "Colisão Traseira", "text"),
        ("classificacao_acidente", "Classificação do Acidente", DataObject.VALID_OPTIONS["classificacao_acidente"], "select"),
        ("fase_dia", "Fase do Dia", DataObject.VALID_OPTIONS["fase_dia"], "select"),
        ("condicao_metereologica", "Condição Meteorológica", DataObject.VALID_OPTIONS["condicao_metereologica"], "select"),
        ("tipo_pista", "Tipo de Pista", DataObject.VALID_OPTIONS["tipo_pista"], "select"),
        ("tracado_via", "Traçado da Via", DataObject.VALID_OPTIONS["tracado_via"], "select"),
        ("uso_solo", "Uso do Solo", DataObject.VALID_OPTIONS["uso_solo"], "select"),
        ("pessoas", "Pessoas Envolvidas", 2, "number"),
        ("mortos", "Mortos", 0, "number"),
        ("feridos_leves", "Feridos Leves", 1, "number"),
        ("feridos_graves", "Feridos Graves", 0, "number"),
        ("ilesos", "Ilesos", 1, "number"),
        ("ignorados", "Ignorados", 0, "number"),
        ("feridos", "Total Feridos", 1, "number"),
        ("veiculos", "Veículos Envolvidos", 2, "number")
    ]

    operation = st.radio("Selecione a Operação:", ("Adicionar", "Buscar", "Atualizar", "Excluir"), key="crud_operation")

    if operation == "Adicionar":
        st.subheader("➕ Adicionar Novo Registro")
        with st.form("add_record_form"):
            new_data = {}
            for field, label, default_val, input_type in common_fields_ui:
                if input_type == "number":
                    new_data[field] = st.number_input(label, value=default_val, min_value=0, format="%d", key=f"add_{field}")
                elif input_type == "select":
                    new_data[field] = st.selectbox(label, options=default_val, key=f"add_{field}")
                else: # text
                    new_data[field] = st.text_input(label, value=default_val, key=f"add_{field}")
            
            submitted = st.form_submit_button("Adicionar Registro")
            if submitted:
                try:
                    data_obj = DataObject(**new_data)
                    record_id = current_db.add_record(data_obj)
                    if record_id is not None:
                        st.success(f"Registro adicionado com sucesso! ID: {record_id}")
                        logger.info(f"Record {record_id} added via UI. DB Type: {st.session_state.db_type}")
                        st.experimental_rerun() # Refresh UI
                    else:
                        st.error("Falha ao adicionar registro.")
                except DataValidationError as e:
                    st.error(f"Erro de validação: {e}")
                    logger.error(f"Validation error adding record: {e}")
                except Exception as e:
                    st.error(f"Erro inesperado ao adicionar registro: {e}")
                    logger.error(f"Unexpected error adding record: {traceback.format_exc()}")

    elif operation == "Buscar":
        st.subheader("🔍 Buscar Registro por ID")
        search_id = st.number_input("ID do Registro para Buscar:", min_value=1, format="%d", key="search_id_input")
        if st.button("Buscar Registro"):
            record = current_db.get_record(search_id)
            if record:
                st.success(f"Registro com ID {search_id} encontrado:")
                record_dict = record.to_dict()
                st.json(record_dict)
            else:
                st.warning(f"Registro com ID {search_id} não encontrado.")
                logger.info(f"Record {search_id} not found during search.")

    elif operation == "Atualizar":
        st.subheader("✍️ Atualizar Registro Existente")
        update_id = st.number_input("ID do Registro para Atualizar:", min_value=1, format="%d", key="update_id_input")
        
        existing_record = None
        if update_id:
            existing_record = current_db.get_record(update_id)
            if not existing_record:
                st.info("Insira um ID e clique em 'Carregar Registro' para preencher os campos.")

        if st.button("Carregar Registro", key="load_update_record"):
            if existing_record:
                st.session_state[f'update_form_data_{update_id}'] = existing_record.to_dict()
                st.success(f"Registro {update_id} carregado para edição.")
            else:
                st.warning(f"Registro com ID {update_id} não encontrado.")

        # Display update form if record is loaded or exists in session state
        if existing_record or (f'update_form_data_{update_id}' in st.session_state and st.session_state[f'update_form_data_{update_id}']['id'] == update_id):
            current_data_dict = st.session_state.get(f'update_form_data_{update_id}', existing_record.to_dict() if existing_record else {})
            
            with st.form("update_record_form"):
                updated_data = {}
                for field, label, default_val, input_type in common_fields_ui:
                    current_value = current_data_dict.get(field)
                    if input_type == "number":
                        updated_data[field] = st.number_input(label, value=current_value if current_value is not None else 0, min_value=0, format="%d", key=f"update_{field}")
                    elif input_type == "select":
                        # Find current index for selectbox
                        current_index = 0
                        if current_value in default_val:
                            current_index = default_val.index(current_value)
                        updated_data[field] = st.selectbox(label, options=default_val, index=current_index, key=f"update_{field}")
                    else: # text
                        updated_data[field] = st.text_input(label, value=str(current_value) if current_value is not None else '', key=f"update_{field}")
                
                update_submitted = st.form_submit_button("Atualizar Registro")
                if update_submitted:
                    try:
                        updated_data_obj = DataObject(id=update_id, **updated_data) # Pass ID explicitly for update
                        if current_db.update_record(update_id, updated_data_obj):
                            st.success(f"Registro {update_id} atualizado com sucesso!")
                            logger.info(f"Record {update_id} updated via UI. DB Type: {st.session_state.db_type}")
                            if f'update_form_data_{update_id}' in st.session_state:
                                del st.session_state[f'update_form_data_{update_id}'] # Clear form data
                            st.experimental_rerun()
                        else:
                            st.error(f"Falha ao atualizar registro {update_id}.")
                    except DataValidationError as e:
                        st.error(f"Erro de validação: {e}")
                        logger.error(f"Validation error updating record {update_id}: {e}")
                    except Exception as e:
                        st.error(f"Erro inesperado ao atualizar registro {update_id}: {e}")
                        logger.error(f"Unexpected error updating record {update_id}: {traceback.format_exc()}")
        
    elif operation == "Excluir":
        st.subheader("🗑️ Excluir Registro por ID")
        delete_id = st.number_input("ID do Registro para Excluir:", min_value=1, format="%d", key="delete_id_input")
        if st.button("Excluir Registro"):
            if current_db.delete_record(delete_id):
                st.success(f"Registro {delete_id} excluído com sucesso!")
                logger.info(f"Record {delete_id} deleted via UI. DB Type: {st.session_state.db_type}")
                st.experimental_rerun()
            else:
                st.error(f"Falha ao excluir registro {delete_id}.")

    st.subheader("📋 Todos os Registros")
    total_records = current_db.count_records()
    if total_records == 0:
        st.info("Nenhum registro encontrado no banco de dados.")
    else:
        # Calculate pages and current page
        pages = math.ceil(total_records / APP_CONFIG["MAX_RECORDS_PER_PAGE"])
        current_page = st.number_input(f"Página (1-{pages}):", min_value=1, max_value=pages if pages > 0 else 1, value=st.session_state.get('current_page', 1), key="pagination_input")
        st.session_state.current_page = current_page # Store page in session state

        records = current_db.list_records(current_page, APP_CONFIG["MAX_RECORDS_PER_PAGE"])
        
        # Converte lista de DataObject para lista de dicionários para exibição
        records_data_for_display = [record.to_dict() for record in records]
        
        st.dataframe(records_data_for_display, use_container_width=True)

def display_import_export_section():
    """Exibe a interface para importação e exportação de dados CSV."""
    st.header("📥📤 Importar/Exportar Dados CSV")

    current_db = st.session_state.db if not st.session_state.use_btree else st.session_state.btree_db
    st.info(f"Banco de Dados Ativo: **{'Standard DB' if not st.session_state.use_btree else 'B-Tree DB (Placeholder)'}**")


    st.subheader("⬆️ Importar CSV")
    st.markdown("Faça upload de um arquivo CSV para importar registros para o banco de dados. **O cabeçalho do CSV será ignorado.**")
    st.markdown("As colunas do CSV devem seguir a ordem esperada: `data_ocorrencia`, `uf`, `br`, `km`, `municipio`, `causa_acidente`, `tipo_acidente`, `classificacao_acidente`, `fase_dia`, `condicao_metereologica`, `tipo_pista`, `tracado_via`, `uso_solo`, `pessoas`, `mortos`, `feridos_leves`, `feridos_graves`, `ilesos`, `ignorados`, `feridos`, `veiculos`.")

    uploaded_file = st.file_uploader("Escolha um arquivo CSV para importar", type="csv", key="csv_import_uploader")
    if uploaded_file is not None:
        if st.button("Iniciar Importação CSV"):
            try:
                # Use tempfile para lidar com o arquivo carregado
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                with st.spinner("Importando registros do CSV..."):
                    imported_count = 0
                    skipped_count = 0
                    # Use errors='replace' para lidar com caracteres problemáticos
                    with open(tmp_path, 'r', encoding='utf-8', errors='replace') as csvfile:
                         reader = csv.reader(csvfile, delimiter=APP_CONFIG["CSV_DELIMITER"])
                         next(reader) # Pula o cabeçalho
                         for row_num, row in enumerate(reader, start=2): # Começa da linha 2 (após o cabeçalho)
                             try:
                                 data_obj = DataObject.from_csv_row(row)
                                 current_db.add_record(data_obj)
                                 imported_count +=1
                             except DataValidationError as e:
                                 skipped_count += 1
                                 logger.warning(f"Pulando linha CSV inválida (linha {row_num}): {row} - Erro: {e}")
                                 st.warning(f"⚠️ Linha {row_num} ignorada (validação): {e}")
                             except Exception as e:
                                 skipped_count += 1
                                 logger.error(f"Erro inesperado ao processar linha CSV (linha {row_num}): {row} - Erro: {traceback.format_exc()}")
                                 st.error(f"🚨 Erro inesperado na linha {row_num}: {e}")
                    st.success(f"Importação completa! Adicionados {imported_count} novos registros. {skipped_count} linhas puladas devido a erros.")

            except Exception as e:
                st.error(f"🚨 Ocorreu um erro durante a importação do CSV: {e}")
                logger.error(f"Importação CSV falhou: {traceback.format_exc()}")
            finally:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    st.subheader("⬇️ Exportar CSV")
    if st.button("Exportar Todos os Registros para CSV"):
        try:
            all_records = current_db.get_all_records()
            if not all_records:
                st.info("Nenhum registro para exportar.")
                return

            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer, delimiter=APP_CONFIG["CSV_DELIMITER"])
            
            # Gera dinamicamente o cabeçalho CSV com base nos campos do DataObject
            header = [field for field in DataObject.REQUIRED_FIELDS if field != "id"]
            csv_writer.writerow(header)
            
            # Escreve as linhas de dados
            for record in all_records:
                csv_writer.writerow(record.to_csv_row())
            
            st.download_button(
                label="Baixar CSV Exportado",
                data=csv_buffer.getvalue().encode('utf-8'),
                file_name="traffic_accidents_export.csv",
                mime="text/csv"
            )
            st.success("Dados exportados para CSV com sucesso!")
            logger.info("Dados exportados para CSV.")
        except Exception as e:
            st.error(f"🚨 Erro ao exportar CSV: {e}")
            logger.error(f"Erro ao exportar CSV: {traceback.format_exc()}")

def display_backup_restore_section():
    """Exibe a interface para backup e restauração do banco de dados padrão."""
    st.header("💾 Backup e Restauração do Banco de Dados")

    current_db = st.session_state.db # Backup/Restore é para o DB padrão apenas

    st.subheader("⬆️ Fazer Backup")
    st.markdown(f"Será criado um backup do seu banco de dados principal (`{APP_CONFIG['DB_FILE_NAME']}`) e índice (`{APP_CONFIG['INDEX_FILE_NAME']}`) no diretório `{BACKUP_PATH}`.")
    if st.button("Criar Backup Agora"):
        try:
            Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_db_path = os.path.join(BACKUP_PATH, f"{APP_CONFIG['DB_FILE_NAME']}_{timestamp}.bak")
            backup_index_path = os.path.join(BACKUP_PATH, f"{APP_CONFIG['INDEX_FILE_NAME']}_{timestamp}.bak")
            backup_id_counter_path = os.path.join(BACKUP_PATH, f"{APP_CONFIG['ID_COUNTER_FILE_NAME']}_{timestamp}.bak")
            
            # Garante que o DB e o índice estejam atualizados no disco antes do backup
            current_db.compact_db() # Compacta antes do backup para otimização
            
            shutil.copy2(DB_PATH, backup_db_path)
            shutil.copy2(INDEX_PATH, backup_index_path)
            shutil.copy2(ID_COUNTER_PATH, backup_id_counter_path)
            
            st.success(f"Backup criado em: `{BACKUP_PATH}` com timestamp `{timestamp}`")
            logger.info(f"Backup created at: {BACKUP_PATH} with timestamp {timestamp}")

            # Limpa backups antigos
            backups = sorted(Path(BACKUP_PATH).glob(f"{APP_CONFIG['DB_FILE_NAME']}_*.bak"), key=os.path.getmtime)
            if len(backups) > APP_CONFIG["MAX_BACKUPS"]:
                for i in range(len(backups) - APP_CONFIG["MAX_BACKUPS"]):
                    file_to_remove_db = backups[i]
                    timestamp_str = file_to_remove_db.name.split('_')[-1].split('.')[0]
                    file_to_remove_index = Path(BACKUP_PATH) / f"{APP_CONFIG['INDEX_FILE_NAME']}_{timestamp_str}.bak"
                    file_to_remove_id_counter = Path(BACKUP_PATH) / f"{APP_CONFIG['ID_COUNTER_FILE_NAME']}_{timestamp_str}.bak"

                    try:
                        os.remove(file_to_remove_db)
                        if file_to_remove_index.exists(): os.remove(file_to_remove_index)
                        if file_to_remove_id_counter.exists(): os.remove(file_to_remove_id_counter)
                        logger.info(f"Removido backup antigo: {file_to_remove_db.name}")
                    except Exception as e:
                        logger.warning(f"Não foi possível remover backup antigo {file_to_remove_db.name}: {e}")

            st.experimental_rerun() # Atualiza a lista de backups disponíveis
        except Exception as e:
            st.error(f"🚨 Erro ao criar backup: {e}")
            logger.error(f"Erro ao criar backup: {traceback.format_exc()}")

    st.subheader("⬇️ Restaurar Backup")
    st.markdown(f"Restaure o banco de dados principal e o índice a partir de um backup existente. Isso **sobrescreverá** os dados atuais.")
    backup_files = list(Path(BACKUP_PATH).glob(f"{APP_CONFIG['DB_FILE_NAME']}_*.bak"))
    backup_files_sorted = sorted(backup_files, key=os.path.getmtime, reverse=True)
    backup_options = [f.name for f in backup_files_sorted]
    
    if backup_options:
        selected_backup = st.selectbox("Selecione o backup para restaurar:", backup_options, key="restore_select")
        if st.button("Restaurar DB Selecionado"):
            try:
                backup_db_file_path = Path(BACKUP_PATH) / selected_backup
                # Deriva os arquivos de índice e contador de IDs correspondentes
                timestamp_str = backup_db_file_path.name.split('_')[-1].split('.')[0]
                backup_index_file_path = Path(BACKUP_PATH) / f"{APP_CONFIG['INDEX_FILE_NAME']}_{timestamp_str}.bak"
                backup_id_counter_file_path = Path(BACKUP_PATH) / f"{APP_CONFIG['ID_COUNTER_FILE_NAME']}_{timestamp_str}.bak"

                if not backup_db_file_path.exists() or not backup_index_file_path.exists() or not backup_id_counter_file_path.exists():
                    st.error("🚨 Arquivos de backup incompletos ou não encontrados!")
                    logger.error(f"Conjunto de backup incompleto para {backup_db_file_path.name}")
                    return

                # Copia os arquivos de backup para os arquivos de DB ativos
                shutil.copy2(backup_db_file_path, DB_PATH)
                shutil.copy2(backup_index_file_path, INDEX_PATH)
                shutil.copy2(backup_id_counter_file_path, ID_COUNTER_PATH)
                
                # Recarrega o estado do DB após a restauração
                current_db._rebuild_index()
                current_db._load_id_counter()
                
                st.success(f"Banco de dados restaurado de: `{selected_backup}`")
                logger.info(f"Banco de dados restaurado de: {selected_backup}")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"🚨 Erro ao restaurar backup: {e}")
                logger.error(f"Erro ao restaurar backup: {traceback.format_exc()}")
    else:
        st.info("Nenhum backup disponível no diretório.")

def display_compression_section():
    """Exibe a interface para compactação e descompactação de arquivos (Huffman & LZW)."""
    st.header("🗜️ Compactação de Arquivos")

    st.warning("As funções de compressão Huffman e LZW são **placeholders** e apenas simulam o processo de compressão/descompressão. Nenhuma lógica real de algoritmo está implementada aqui.")

    compression_type = st.radio("Selecione o Algoritmo de Compactação:", ("Huffman", "LZW"), key="compression_algo_select")

    st.subheader("📦 Compactar Arquivo")
    uploaded_file_compress = st.file_uploader("Escolha um arquivo para compactar", type=None, key="compress_upload")
    
    if uploaded_file_compress is not None:
        input_path_temp = os.path.join(tempfile.gettempdir(), uploaded_file_compress.name)
        with open(input_path_temp, "wb") as f:
            f.write(uploaded_file_compress.getbuffer())

        output_dir = HUFFMAN_FOLDER if compression_type == "Huffman" else LZW_FOLDER
        output_extension = APP_CONFIG["HUFFMAN_COMPRESSED_EXTENSION"] if compression_type == "Huffman" else APP_CONFIG["LZW_COMPRESSED_EXTENSION"]
        output_filename = uploaded_file_compress.name + output_extension
        output_path = os.path.join(output_dir, output_filename)

        if st.button(f"Compactar com {compression_type}", key=f"btn_compress_{compression_type}"):
            progress_bar = st.progress(0, text="Iniciando compressão...")
            status_text = st.empty()

            def update_progress(p):
                progress_bar.progress(p, text=f"Progresso: {p*100:.1f}%")

            try:
                if compression_type == "Huffman":
                    compressed_size, original_size, compression_ratio, process_time = HuffmanProcessor.compress_file(input_path_temp, output_path, update_progress)
                else: # LZW
                    # LZWProcessor.compress retorna bool. Simular metrics.
                    success = LZWProcessor.compress(input_path_temp, output_path, update_progress)
                    if success:
                        original_size = os.path.getsize(input_path_temp) if os.path.exists(input_path_temp) else 0
                        compressed_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                        process_time = 0.2 # Simulated
                    else:
                        raise Exception("Falha na compressao LZW.")
                
                st.success(f"Arquivo compactado com sucesso em: `{output_path}`")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tamanho Original", f"{original_size:,} bytes")
                    st.metric("Taxa de Compactação", f"{compression_ratio:.2f}%")
                with col2:
                    st.metric("Tamanho Compactado", f"{compressed_size:,} bytes")
                    st.metric("Tempo de Processamento", f"{process_time:.4f} seg")
                logger.info(f"Arquivo {uploaded_file_compress.name} compactado com {compression_type}. Taxa: {compression_ratio:.2f}%")
            except Exception as e:
                st.error(f"🚨 Erro durante a compactação: {e}")
                logger.error(f"Compressão falhou: {traceback.format_exc()}")
            finally:
                if os.path.exists(input_path_temp):
                    os.unlink(input_path_temp) # Limpa arquivo temporário
                progress_bar.empty()
                status_text.empty()

    st.subheader("🔓 Descompactar Arquivo")
    
    # Lista arquivos compactados disponíveis nas respectivas pastas
    huff_files = [f.name for f in Path(HUFFMAN_FOLDER).glob(f"*{APP_CONFIG['HUFFMAN_COMPRESSED_EXTENSION']}")]
    lzw_files = [f.name for f in Path(LZW_FOLDER).glob(f"*{APP_CONFIG['LZW_COMPRESSED_EXTENSION']}")]
    
    available_files = []
    if compression_type == "Huffman":
        available_files = huff_files
    else:
        available_files = lzw_files

    if not available_files:
        st.info(f"Nenhum arquivo compactado ({compression_type}) encontrado no diretório: `{output_dir}`")
    else:
        selected_file_decompress = st.selectbox(f"Selecione um arquivo {compression_type} para descompactar:", [""] + available_files, key="decompress_select")
        
        if selected_file_decompress and st.button(f"Descompactar com {compression_type}", key=f"btn_decompress_{compression_type}"):
            input_path_decompress = os.path.join(output_dir, selected_file_decompress)
            
            output_extension = APP_CONFIG["HUFFMAN_COMPRESSED_EXTENSION"] if compression_type == "Huffman" else APP_CONFIG["LZW_COMPRESSED_EXTENSION"]
            output_filename = selected_file_decompress.replace(output_extension, "")
            # Adiciona um prefixo para evitar sobrescrever o arquivo original se for o mesmo nome
            output_path_decompress = os.path.join(output_dir, "decompressed_" + output_filename) 

            progress_bar = st.progress(0, text="Iniciando descompressão...")
            status_text = st.empty()

            def update_progress(p):
                progress_bar.progress(p, text=f"Progresso: {p*100:.1f}%")

            try:
                if compression_type == "Huffman":
                    compressed_size, decompressed_size, compression_ratio, process_time = HuffmanProcessor.decompress_file(input_path_decompress, output_path_decompress, update_progress)
                else: # LZW
                    success = LZWProcessor.decompress(input_path_decompress, output_path_decompress, update_progress)
                    if success:
                        compressed_size = os.path.getsize(input_path_decompress) if os.path.exists(input_path_decompress) else 0
                        decompressed_size = os.path.getsize(output_path_decompress) if os.path.exists(output_path_decompress) else 0
                        compression_ratio = (1 - compressed_size / decompressed_size) * 100 if decompressed_size > 0 else 0
                        process_time = 0.2 # Simulated
                    else:
                        raise Exception("Falha na descompressao LZW.")
                
                st.success(f"Arquivo descompactado com sucesso em: `{output_path_decompress}`")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tamanho Compactado", f"{compressed_size:,} bytes")
                    st.metric("Taxa de Compactação", f"{compression_ratio:.2f}%")
                with col2:
                    st.metric("Tamanho Descompactado", f"{decompressed_size:,} bytes")
                    st.metric("Tempo de Processamento", f"{process_time:.4f} seg")
                logger.info(f"Arquivo {selected_file_decompress} descompactado com {compression_type}. Taxa: {compression_ratio:.2f}%")
                
                # Oferecer download do arquivo descompactado
                if os.path.exists(output_path_decompress):
                    with open(output_path_decompress, "rb") as f:
                        st.download_button(
                            label="Download Arquivo Descompactado",
                            data=f.read(),
                            file_name=output_filename,
                            mime="application/octet-stream" # Tipo MIME genérico
                        )

            except Exception as e:
                st.error(f"🚨 Erro durante a descompactação: {e}")
                logger.error(f"Descompressão falhou: {traceback.format_exc()}")
            finally:
                progress_bar.empty()
                status_text.empty()

def display_cryptography_section():
    """Exibe a interface para criptografia e descriptografia de arquivos."""
    st.header("🔒 Criptografia de Arquivos (AES + RSA Híbrido)")
    if not HAS_CRYPTOGRAPHY:
        st.error("A biblioteca 'cryptography' não está instalada. As funções de criptografia AES+RSA não estão disponíveis.")
        st.markdown("Por favor, instale-a executando: `pip install cryptography` no seu terminal.")
        return

    st.info("Esta seção permite gerar chaves RSA e usar criptografia híbrida (AES para dados, RSA para chave AES) em arquivos do banco de dados ou índice.")

    st.subheader("🔑 Gerar Chaves RSA")
    st.markdown(f"Gere um par de chaves RSA (pública e privada) para criptografia híbrida. As chaves serão salvas em: `{RSA_KEYS_DIR}`")
    password_rsa_gen = st.text_input("Senha para a Chave Privada (Opcional):", type="password", key="rsa_gen_pwd")
    if st.button("Gerar Chaves RSA", key="btn_generate_rsa"):
        Path(RSA_KEYS_DIR).mkdir(parents=True, exist_ok=True)
        if CryptographyHandler.generate_rsa_keys(RSA_PUBLIC_KEY_PATH, RSA_PRIVATE_KEY_PATH, password_rsa_gen if password_rsa_gen else None):
            st.success("Chaves RSA geradas com sucesso!")
        else:
            st.error("Falha ao gerar chaves RSA.")

    st.subheader("🔐 Criptografar Arquivo")
    encryption_file_type = st.radio("Tipo de arquivo para criptografar:", ("Banco de Dados", "Índice", "Banco de Dados B-Tree"), key="enc_file_type_radio")
    
    file_to_encrypt_path = ""
    if encryption_file_type == "Banco de Dados":
        file_to_encrypt_path = DB_PATH
    elif encryption_file_type == "Índice":
        file_to_encrypt_path = INDEX_PATH
    elif encryption_file_type == "Banco de Dados B-Tree":
        file_to_encrypt_path = BTREE_DB_PATH

    st.markdown(f"Arquivo alvo: `{file_to_encrypt_path}`")
    output_encrypted_file_name = st.text_input("Nome do arquivo de saída criptografado (ex: dados.db.enc):", f"{os.path.basename(file_to_encrypt_path)}.enc", key="output_enc_name")
    
    if st.button("Criptografar", key="btn_encrypt_file"):
        full_output_path = os.path.join(APP_CONFIG["DB_DIR"], output_encrypted_file_name)

        if not os.path.exists(RSA_PUBLIC_KEY_PATH):
            st.warning("⚠️ Chave pública RSA não encontrada. Gere as chaves primeiro.")
        elif not os.path.exists(file_to_encrypt_path):
            st.warning(f"⚠️ Arquivo '{os.path.basename(file_to_encrypt_path)}' não encontrado para criptografia.")
        else:
            with st.spinner(f"Criptografando {os.path.basename(file_to_encrypt_path)}..."):
                if CryptographyHandler.hybrid_encrypt_file(file_to_encrypt_path, full_output_path, RSA_PUBLIC_KEY_PATH):
                    st.success(f"Arquivo '{os.path.basename(file_to_encrypt_path)}' criptografado com sucesso para `{output_encrypted_file_name}`!")
                    logger.info(f"Arquivo {os.path.basename(file_to_encrypt_path)} criptografado para {output_encrypted_file_name}")
                else:
                    st.error(f"🚨 Falha ao criptografar {os.path.basename(file_to_encrypt_path)}.")

    st.subheader("🔓 Descriptografar Arquivo")
    encrypted_files_in_dir = [f for f in os.listdir(APP_CONFIG["DB_DIR"]) if f.endswith(APP_CONFIG["ENCRYPTED_DB_EXTENSION"])]
    
    if encrypted_files_in_dir:
        input_encrypted_file = st.selectbox("Selecione o arquivo criptografado para descriptografar:", [""] + encrypted_files_in_dir, key="decrypt_select")
        
        # Tenta inferir o nome do arquivo original
        inferred_output_name = input_encrypted_file.replace(APP_CONFIG["ENCRYPTED_DB_EXTENSION"], "") if input_encrypted_file else ""
        output_decrypted_file_name = st.text_input("Nome do arquivo de saída descriptografado:", inferred_output_name, key="output_dec_name")
        private_key_password = st.text_input("Senha da Chave Privada (se houver):", type="password", key="private_key_pass")

        if st.button("Descriptografar", key="btn_decrypt_file"):
            full_input_path = os.path.join(APP_CONFIG["DB_DIR"], input_encrypted_file)
            full_output_path = os.path.join(APP_CONFIG["DB_DIR"], output_decrypted_file_name)

            if not os.path.exists(RSA_PRIVATE_KEY_PATH):
                st.warning("⚠️ Chave privada RSA não encontrada. Gere as chaves ou verifique o caminho.")
            elif not os.path.exists(full_input_path):
                st.warning(f"⚠️ Arquivo criptografado '{input_encrypted_file}' não encontrado.")
            else:
                with st.spinner(f"Descriptografando {input_encrypted_file}..."):
                    if CryptographyHandler.hybrid_decrypt_file(full_input_path, full_output_path, RSA_PRIVATE_KEY_PATH, private_key_password if private_key_password else None):
                        st.success(f"Arquivo '{input_encrypted_file}' descriptografado com sucesso para `{output_decrypted_file_name}`!")
                        logger.info(f"Arquivo {input_encrypted_file} descriptografado para {output_decrypted_file_name}")
                    else:
                        st.error(f"🚨 Falha ao descriptografar {input_encrypted_file}. Verifique a senha ou a integridade do arquivo.")
    else:
        st.info("Nenhum arquivo criptografado (.enc) encontrado no diretório do banco de dados para descriptografar.")

    st.subheader("👻 Criptografia/Descriptografia Blowfish (Placeholder)")
    st.info("As funções Blowfish são apenas **placeholders** para demonstração e podem não funcionar sem uma implementação completa.")
    # Exemplo de chamadas para Blowfish (para manter a UI)
    with st.expander("Demonstrar Blowfish (Apenas Placeholder)"):
        bf_input = st.text_input("Caminho do arquivo de entrada (Blowfish Placeholder):", "arquivo_teste.txt", key="bf_input")
        bf_output = st.text_input("Caminho do arquivo de saída (Blowfish Placeholder):", "arquivo_saida.enc", key="bf_output")
        bf_password = st.text_input("Senha (Blowfish Placeholder):", type="password", key="bf_password")
        col_bf1, col_bf2 = st.columns(2)
        with col_bf1:
            if st.button("Criptografar Blowfish (Placeholder)", key="btn_bf_encrypt"):
                CryptographyHandler.blowfish_encrypt_file(bf_input, bf_output, bf_password)
        with col_bf2:
            if st.button("Descriptografar Blowfish (Placeholder)", key="btn_bf_decrypt"):
                CryptographyHandler.blowfish_decrypt_file(bf_input, bf_output, bf_password)


def display_admin_section():
    """Exibe funções administrativas e o log de atividades do sistema."""
    st.header("⚙️ Funções Administrativas")

    current_db = st.session_state.db if not st.session_state.use_btree else st.session_state.btree_db

    st.subheader("📊 Informações do Sistema e do Banco de Dados")
    st.info(f"Diretório Base: `{APP_CONFIG['DB_DIR']}`")
    st.info(f"Arquivo Banco de Dados (Standard): `{DB_PATH}`")
    if os.path.exists(DB_PATH):
        st.info(f"Tamanho do Standard DB: {os.path.getsize(DB_PATH):,} bytes")
    else:
        st.info("Standard DB: Arquivo não existe.")

    st.info(f"Arquivo Banco de Dados (B-Tree): `{BTREE_DB_PATH}`")
    if os.path.exists(BTREE_DB_PATH):
        st.info(f"Tamanho do B-Tree DB: {os.path.getsize(BTREE_DB_PATH):,} bytes")
    else:
        st.info("B-Tree DB: Arquivo não existe.")

    st.info(f"Arquivo Índice (Standard): `{INDEX_PATH}`")
    if os.path.exists(INDEX_PATH):
        st.info(f"Tamanho do Índice Standard: {os.path.getsize(INDEX_PATH):,} bytes")
    else:
        st.info("Índice Standard: Arquivo não existe.")
    
    st.info(f"Arquivo Contador ID: `{ID_COUNTER_PATH}`")
    st.info(f"Arquivo Lock: `{LOCK_PATH}`")
    st.info(f"Diretório de Backups: `{BACKUP_PATH}`")
    st.info(f"Arquivo de Log: `{LOG_FILE_PATH}`")
    st.info(f"Diretório de Chaves RSA: `{RSA_KEYS_DIR}`")
    st.info(f"Tamanho da Página B-Tree: `{APP_CONFIG['BTREE_PAGE_SIZE']}` bytes")
    st.info(f"Grau Mínimo B-Tree (t): `{APP_CONFIG['BTREE_MIN_DEGREE']}`")

    if st.session_state.use_btree:
        st.subheader("🌳 Status da B-Tree (Placeholder)")
        st.write(f"Tamanho do Arquivo B-Tree: {current_db.get_size():,} bytes")
        st.write(f"Número de Nós (estimado): {current_db.get_num_nodes()}")
        st.write(f"Profundidade da Árvore (estimada): {current_db.get_depth()}")

        if st.button("Limpar Banco de Dados B-Tree (Atenção!)", key="clear_btree_db_btn"):
            if current_db.clear():
                st.success("Banco de Dados B-Tree limpo e reiniciado.")
                st.experimental_rerun()
            else:
                st.error("Erro ao limpar B-Tree DB.")
    else: # Only show compaction for Standard DB
        st.subheader("🧹 Manutenção do Banco de Dados Standard")
        st.warning("A compactação pode levar um tempo e é recomendada para otimizar o espaço em disco após muitas exclusões/atualizações.")
        if st.button("Compactar Banco de Dados Standard Agora", key="compact_standard_db_btn"):
            with st.spinner("Compactando..."):
                current_db.compact_db()
                st.success("Compactação concluída.")
                st.experimental_rerun()
        st.subheader("💥 Limpar TODOS os Dados do Standard DB (Extremamente perigoso!)")
        st.warning("Esta ação removerá *TODOS* os registros do banco de dados STANDARD e do índice. CUIDADO! Isso não afeta o B-Tree DB.")
        confirm_clear_all_standard = st.checkbox("Sim, eu entendo que esta ação é irreversível e desejo limpar o DB STANDARD.", key="confirm_clear_all_standard")
        if confirm_clear_all_standard and st.button("Limpar Standard DB Agora", key="clear_all_standard_db_btn"):
            try:
                if os.path.exists(DB_PATH): os.remove(DB_PATH)
                if os.path.exists(INDEX_PATH): os.remove(INDEX_PATH)
                if os.path.exists(ID_COUNTER_PATH): os.remove(ID_COUNTER_PATH)
                st.session_state.db = TrafficAccidentsDB(DB_PATH, INDEX_PATH, LOCK_PATH, ID_COUNTER_PATH) # Re-initialize
                st.success("Banco de dados Standard limpo com sucesso!")
                logger.info("Standard database cleared via admin UI.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"🚨 Erro ao limpar o banco de dados Standard: {e}")
                logger.error(f"Error clearing Standard database: {traceback.format_exc()}")


    st.subheader("📜 Log de Atividades do Sistema")
    
    if os.path.exists(LOG_FILE_PATH):
        try:
            # Use filelock para prevenir problemas com escritas/leituras concorrentes
            with filelock.FileLock(LOCK_PATH, timeout=5): 
                # Melhoria: Especifica encoding e tratamento de erros
                with open(LOG_FILE_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.readlines()
            
            display_entries = deque(maxlen=APP_CONFIG["MAX_LOG_ENTRIES_DISPLAY"])
            # Inverte para mostrar as entradas mais recentes primeiro
            for line in reversed(log_content):
                # Regex para analisar linhas de log: "AAAA-MM-DD HH:MM:SS,ms - NomeLogger - NÍVEL - Mensagem"
                match = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([a-zA-Z._]+) - (\w+) - (.*)$", line.strip())
                if match:
                    timestamp_str, logger_name, log_level, message = match.groups()
                    # Filtra ou destaca mensagens de log relevantes
                    if log_level in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
                        color = ""
                        if log_level == "ERROR" or log_level == "CRITICAL":
                            color = "#dc3545" # Vermelho
                        elif log_level == "WARNING":
                            color = "#ffc107" # Amarelo
                        elif log_level == "INFO":
                            color = "#17a2b8" # Azul claro
                        
                        display_entries.appendleft(f"**`{timestamp_str}`** <span style='color: {color}; font-weight: bold;'>{log_level}</span>: `{message}`")
                else:
                    # Fallback para linhas que não correspondem ao regex, exibe como texto puro
                    display_entries.appendleft(f"`{line.strip()}`")

                if len(display_entries) >= APP_CONFIG["MAX_LOG_ENTRIES_DISPLAY"]:
                    break # Para se o número máximo de entradas for atingido

            if display_entries:
                st.markdown("---")
                for entry in display_entries:
                    st.markdown(entry, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Nenhum registro recente de atividade relevante encontrado no log.")
        except Exception as e:
            st.error(f"⚠️ Não foi possível ler o log de atividades: {str(e)}")
            logger.error(f"Erro ao ler o log de atividades: {traceback.format_exc()}")
    else:
        st.info("ℹ️ Arquivo de log de atividades não encontrado.")


def display_about_section():
    """Exibe informações sobre o aplicativo."""
    st.header("ℹ️ Sobre o Aplicativo")
    st.write("""
    Este é um **Sistema Gerenciador de Banco de Dados de Acidentes de Trânsito** aprimorado,
    desenvolvido para oferecer funcionalidades robustas de CRUD (Criar, Ler, Atualizar, Deletar),
    juntamente com recursos avançados de manipulação de dados e segurança.

    ### Características Principais:
    - **Gerenciamento de Registros:** Adicione, visualize, atualize e exclua registros de acidentes de trânsito.
    - **Persistência de Dados:** Armazenamento eficiente de dados em disco.
    - **Indexação B-Tree:** Utiliza uma estrutura de árvore B para buscas e ordenação otimizadas.
      (⚠️ **Nota:** A implementação da B-Tree é um placeholder nesta versão e simula o comportamento básico).
    - **Importação/Exportação CSV:** Facilita a entrada e saída de grandes volumes de dados.
    - **Manutenção do Banco de Dados:** Ferramentas para compactação e backup/restauração.
    - **Compressão de Arquivos:** Suporte a algoritmos Huffman e LZW para otimização de espaço.
      (⚠️ **Nota:** As implementações de compressão são placeholders nesta versão).
    - **Criptografia de Arquivos:** Proteção de dados sensíveis usando criptografia híbrida (AES + RSA).
      (⚠️ **Nota:** A criptografia Blowfish é um placeholder nesta versão).
    - **Log de Atividades:** Monitoramento e registro de operações importantes.

    Este projeto é uma fusão e aprimoramento de diversas etapas de desenvolvimento de software,
    com foco em persistência de dados e otimização.
    """)
    st.markdown("---")
    st.subheader("Tecnologias Utilizadas:")
    st.markdown("""
    - **Python:** Linguagem de programação principal.
    - **Streamlit:** Para a interface de usuário interativa.
    - **`filelock`:** Para garantir acesso seguro e concorrente a arquivos.
    - **`cryptography` (Python package):** Para as operações de criptografia AES/RSA.
    - **Outras bibliotecas Python:** `os`, `csv`, `json`, `hashlib`, `datetime`, `pathlib`, `shutil`, `tempfile`, `math`, `collections`, `heapq`, `io`, `re`.
    """)
    st.markdown("---")
    st.subheader("Versão:")
    st.write("v5.0 alpha")
    st.write("Desenvolvido por [Seu Nome/Equipe]") # Substitua pelo seu nome/equipe


# --- Função Principal de Configuração da UI ---
def setup_ui():
    """Configura a interface de usuário do Streamlit e gerencia a navegação."""
    st.set_page_config(layout="wide", page_title="Gerenciador de Acidentes de Trânsito", page_icon="🚗")
    apply_custom_css() # Aplica o CSS personalizado

    st.sidebar.title("Opções do Aplicativo")
    
    # Inicializa as instâncias de DB e B-Tree apenas uma vez na sessão
    if "db" not in st.session_state:
        st.session_state.db = TrafficAccidentsDB(DB_PATH, INDEX_PATH, LOCK_PATH, ID_COUNTER_PATH)
    
    if "btree_db" not in st.session_state:
        st.session_state.btree_db = TrafficAccidentsTree(APP_CONFIG["BTREE_DB_FILE_NAME"])
    
    # Toggle entre Standard DB e B-Tree DB na sidebar
    db_choice = st.sidebar.radio(
        "Selecione o Tipo de Banco de Dados:",
        ("Standard DB", "B-Tree DB"),
        key="db_type_selector"
    )
    st.session_state.use_btree = (db_choice == "B-Tree DB")

    if st.session_state.use_btree:
        st.sidebar.success("Usando B-Tree DB (Funções CRUD são placeholders)")
    else:
        st.sidebar.success("Usando Standard DB")

    st.sidebar.markdown("---") # Separador visual

    # Opções de navegação principal com ícones/emojis
    page_options = {
        "Gerenciamento de Registros": "🗃️ Gerenciamento de Registros",
        "Importar/Exportar Dados": "📥📤 Importar/Exportar Dados",
        "Backup/Restaurar": "💾 Backup/Restaurar",
        "Compressão de Arquivos": "🗜️ Compressão de Arquivos",
        "Criptografia de Arquivos": "🔒 Criptografia de Arquivos",
        "Administração": "⚙️ Administração",
        "Log de Atividades": "📜 Log de Atividades", # Separado para foco no log
        "Sobre o Aplicativo": "ℹ️ Sobre o Aplicativo"
    }
    
    selected_page_label = st.sidebar.selectbox(
        "Navegue entre as seções:",
        options=list(page_options.keys()),
        format_func=lambda x: page_options[x], # Mostra o label formatado com ícone
        key="main_navigation_selectbox"
    )

    st.markdown("---") # Separador para o conteúdo principal

    # Renderiza o conteúdo da seção selecionada
    if selected_page_label == "Gerenciamento de Registros":
        display_record_management_section()
    elif selected_page_label == "Importar/Exportar Dados":
        display_import_export_section()
    elif selected_page_label == "Backup/Restaurar":
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


# --- Ponto de Entrada Principal da Aplicação ---
if __name__ == "__main__":
    try:
        # Garante que os diretórios base existam antes de qualquer operação de arquivo
        Path(APP_CONFIG["DB_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
        Path(RSA_KEYS_DIR).mkdir(parents=True, exist_ok=True)
        Path(HUFFMAN_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(LZW_FOLDER).mkdir(parents=True, exist_ok=True)
        
        setup_ui()
    except OSError as e:
        st.error(f"🚨 Crítico: Não foi possível criar os diretórios necessários. Verifique as permissões para `{APP_CONFIG['DB_DIR']}`. Erro: {e}")
        logger.critical(f"Initial directory creation failed: {traceback.format_exc()}")
        st.stop() # Interrompe o aplicativo se os diretórios não puderem ser criados
    except Exception as e:
        st.error(f"🚨 Um erro crítico ocorreu na aplicação: {e}")
        logger.critical(f"Exceção não tratada no ponto de entrada principal do aplicativo: {traceback.format_exc()}")

