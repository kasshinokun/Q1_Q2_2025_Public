import base64
import fnmatch
import locale
from queue import Full
import tempfile
import shutil
# Removed 'requests' as it was causing an error and wasn't used
import streamlit as st
import os
import re
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
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import platform
import sys
from enum import Enum, auto
# --- Cryptography Imports (for RSA and AES) ---
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag as CryptoInvalidTag # Renomeado para evitar conflito

# Configure logging
logging.basicConfig(
    level=logging.INFO, # Pode ser alterado para logging.DEBUG para mais detalhes
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Log para o console
    ]
)
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---
class DataValidationError(ValueError):
    """Exceção personalizada para erros de validação de dados."""
    pass

class DatabaseError(Exception):
    """Exceção personalizada para erros relacionados ao banco de dados."""
    pass

# --- Definição dos Campos de Dados ---
# Define todos os campos para o DataObject, seus tipos esperados e regras de validação básicas.
# Nota: 'crash_hour', 'crash_day_of_week', 'crash_month' NÃO estão aqui porque são *derivados* da 'crash_date'
# e não são campos de entrada diretos para o DataObject.
FIELDS = [
    # (nome_do_campo, tipo_esperado, valor_padrao, eh_obrigatorio)
    ('crash_date', str, '01/01/2020 00:00:00 AM', True),
    ('traffic_control_device', str, 'UNKNOWN', False),
    ('weather_condition', str, 'UNKNOWN', False),
    ('lighting_condition', str, 'UNKNOWN', False),
    ('first_crash_type', str, 'UNKNOWN', False),
    ('trafficway_type', str, 'UNKNOWN', False),
    ('alignment', str, 'UNKNOWN', False),
    ('roadway_surface_cond', str, 'UNKNOWN', False),
    ('road_defect', str, 'UNKNOWN', False),
    ('crash_type', str, 'UNKNOWN', False),
    ('intersection_related_i', str, 'UNKNOWN', False), # 'Y' ou 'N'
    ('damage', str, 'UNKNOWN', False),
    ('prim_contributory_cause', str, 'UNKNOWN', False),
    ('num_units', int, 0, False),
    ('most_severe_injury', str, 'NONE', False),
    ('injuries_total', int, 0, False),
    ('injuries_fatal', int, 0, False),
    ('injuries_incapacitating', int, 0, False),
    ('injuries_non_incapacitating', int, 0, False),
    ('injuries_reported_not_evident', int, 0, False),
    ('injuries_no_indication', int, 0, False),
]

# Mapeamento de nomes de campos para português brasileiro para __repr__ e UI
FIELD_NAMES_PT = {
    'crash_date': 'Data do Acidente (MM/DD/AAAA HH:MM:SS AM/PM)',
    'crash_hour': 'Hora do Acidente (0-23)',
    'crash_day_of_week': 'Dia da Semana do Acidente (1=Seg, 7=Dom)',
    'crash_month': 'Mês do Acidente (1-12)',
    'traffic_control_device': 'Dispositivo de Controle de Tráfego',
    'weather_condition': 'Condição Climática',
    'lighting_condition': 'Condição de Iluminação',
    'first_crash_type': 'Primeiro Tipo de Colisão',
    'trafficway_type': 'Tipo de Via',
    'alignment': 'Alinhamento',
    'roadway_surface_cond': 'Condição da Superfície da Via',
    'road_defect': 'Defeito na Via',
    'crash_type': 'Tipo de Acidente',
    'intersection_related_i': 'Relacionado a Interseção (Y/N)',
    'damage': 'Dano',
    'prim_contributory_cause': 'Causa Contributiva Primária',
    'num_units': 'Número de Unidades',
    'most_severe_injury': 'Lesão Mais Grave',
    'injuries_total': 'Total de Lesões',
    'injuries_fatal': 'Lesões Fatais',
    'injuries_incapacitating': 'Lesões Incapacitantes',
    'injuries_non_incapacitating': 'Lesões Não Incapacitantes',
    'injuries_reported_not_evident': 'Lesões Reportadas Não Evidentes',
    'injuries_no_indication': 'Sem Indicação de Lesões',
    'id': 'ID do Registro'
}

# Mapeamento de headers em português para os nomes de campo em inglês do DataObject
PORTUGUESE_TO_ENGLISH_HEADERS = {
    'crash_date': 'crash_date',
    'dispositivo_de_controle_de_tráfego': 'traffic_control_device',
    'condição_climática': 'weather_condition',
    'condição_de_iluminação': 'lighting_condition',
    'primeiro_tipo_de_acidente': 'first_crash_type',
    'tipo_de_pista_de_tráfego': 'trafficway_type',
    'alinhamento': 'alignment',
    'superfície_da_estrada': 'roadway_surface_cond',
    'defeito_da_estrada': 'road_defect',
    'tipo_de_acidente': 'crash_type',
    'relacionado_à_interseção': 'intersection_related_i',
    'dano': 'damage',
    'causa_contributiva_primária': 'prim_contributory_cause',
    'num_unidades': 'num_units',
    'most_severe_injury': 'most_severe_injury',
    'injuries_total': 'injuries_total',
    'injuries_fatal': 'injuries_fatal',
    'injuries_incapacitating': 'injuries_incapacitating',
    'injuries_non_incapacitating': 'injuries_non_incapacitating',
    'injuries_reported_not_evident': 'injuries_reported_not_evident',
    'injuries_no_indication': 'injuries_no_indication',
    # Campos que podem estar no CSV mas são *derivados* no DataObject, e, portanto, serão ignorados do input data_dict
    'hora_acidente': 'crash_hour',
    'dia_semana_acidente': 'crash_day_of_week',
    'mes_acidente': 'crash_month'
}

# Opções de dropdown para alguns campos (simplificado do app_v6.py para o exemplo)
TRAFFIC_CONTROL_DEVICE_OPTIONS = ['SINAL DE TRAFEGO', 'SINAL DE PARE', 'NENHUM', 'SEM SINALIZACAO', 'UNKNOWN']
WEATHER_CONDITION_OPTIONS = ['CEU LIMPO', 'CHUVA', 'NEVE', 'NUBLADO', 'FOG', 'UNKNOWN']
LIGHTING_CONDITION_OPTIONS = ['DIA CLARO', 'CREPUSCULO', 'NOITE', 'UNKNOWN']
CRASH_TYPE_OPTIONS = ['COLISAO FRONTAL', 'COLISAO TRASEIRA', 'SAIDA DE PISTA', 'COLISAO LATERAL', 'NAO COLISAO', 'UNKNOWN', 'COLISAO']
INTERSECTION_RELATED_OPTIONS = ['Y', 'N', 'UNKNOWN']
DAMAGE_OPTIONS = ['MINIMO', 'MAIOR', 'SUBSTANCIAL', 'MENOR', 'NENHUM', 'UNKNOWN']
MOST_SEVERE_INJURY_OPTIONS = ['NENHUMA', 'LESÃO INCAPACITANTE', 'LESÃO FATAL', 'UNKNOWN']

class DataObject:
    """
    Representa um registro de acidente de trânsito, otimizado para validação e serialização,
    adaptado para ser usado em app_v6.py e compatível com datamanager_v1.py.
    Inclui métodos __str__ e __repr__ aprimorados.
    """
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """
        Inicializa uma nova instância de DataObject.
        Pode ser inicializada a partir de um dicionário.

        Args:
            data (Optional[Dict[str, Any]]): Um dicionário contendo os dados do acidente.
        """
        self._data = {}
        self._initialize_defaults()
        if data:
            self._initialize_from_dict(data)

    def _initialize_defaults(self):
        """Define valores padrão para todos os campos."""
        for field_name, field_type, default_value, _ in FIELDS:
            self._data[field_name] = default_value
        # Inicializa campos derivados que não estão em FIELDS mas são gerados
        self._data['crash_hour'] = 0
        self._data['crash_day_of_week'] = 0
        self._data['crash_month'] = 0

    def _initialize_from_dict(self, data_dict: Dict[str, Any]):
        """Popula os campos a partir de um dicionário, realizando conversão básica."""
        for field_name, field_type, _, _ in FIELDS:
            if field_name in data_dict:
                value = data_dict[field_name]
                try:
                    if field_type == int:
                        self._data[field_name] = int(float(value)) if isinstance(value, str) and '.' in value else int(value)
                    elif field_type == float:
                        self._data[field_name] = float(value)
                    else:
                        self._data[field_name] = str(value).strip()
                except (ValueError, TypeError):
                    logger.warning(f"Erro de conversão de tipo para o campo '{field_name}'. Valor: '{value}'. Usando valor padrão.")
                    default_value_for_field = next((f[2] for f in FIELDS if f[0] == field_name), None)
                    self._data[field_name] = default_value_for_field
            # Se o campo não estiver no data_dict, ele manterá o valor padrão inicializado.
        
        # Se 'id' for passado no data_dict, armazena-o
        if 'id' in data_dict:
            self._data['id'] = data_dict['id']


    # Removido from_csv_row, pois o parsing agora será feito em process_csv_to_db

    def to_map(self) -> Dict[str, Any]:
        """
        Converte a instância de DataObject para um dicionário (mapa),
        incluindo o 'id' se presente e os campos derivados.
        """
        data_map = self._data.copy()
        return data_map

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any):
        if name == "_data":
            super().__setattr__(name, value)
            return

        for field_name, field_type, _, _ in FIELDS:
            if field_name == name:
                try:
                    if field_name == 'crash_date':
                        self._data[field_name] = str(value)
                    elif field_type == int:
                        self._data[field_name] = int(value)
                    elif field_type == float:
                        self._data[field_name] = float(value)
                    elif field_type == str:
                        self._data[field_name] = str(value)
                    else:
                        self._data[field_name] = value
                except (ValueError, TypeError):
                    raise DataValidationError(f"Valor '{value}' inválido para o campo '{field_name}'. Esperado: {field_type.__name__}.")
                return
        # Permite definir o atributo 'id' e os campos derivados mesmo que não estejam em FIELDS
        if name in ['id', 'crash_hour', 'crash_day_of_week', 'crash_month']:
            self._data[name] = value
            return

        super().__setattr__(name, value)

    @property
    def crash_datetime(self) -> Optional[datetime]:
        """Retorna a data e hora do acidente como um objeto datetime."""
        try:
            return datetime.strptime(self.crash_date, '%m/%d/%Y %I:%M:%S %p')
        except ValueError:
            try:
                return datetime.strptime(self.crash_date, '%m/%d/%Y %I:%M %p')
            except (ValueError, TypeError):
                logger.warning(f"Não foi possível parsear 'crash_date' ('{self.crash_date}') para datetime. Formato inválido.")
                return None

    @crash_datetime.setter
    def crash_datetime(self, dt: datetime):
        """Define a data e hora do acidente a partir de um objeto datetime."""
        self.crash_date = dt.strftime('%m/%d/%Y %I:%M:%S %p')

    def validate(self) -> bool:
        """
        Realiza uma validação abrangente dos dados do DataObject.
        """
        try:
            for field_name, field_type, _, is_required in FIELDS:
                value = self._data.get(field_name)

                if is_required and (value is None or (isinstance(value, str) and not value.strip() and field_name != 'intersection_related_i')):
                    raise DataValidationError(f"Campo obrigatório '{field_name}' está vazio.")

                if value is not None and not (isinstance(value, str) and not value.strip()):
                    if field_type == int and not isinstance(value, int):
                         raise DataValidationError(f"Campo '{field_name}' deve ser um inteiro. Valor: {value}.")
                    if field_type == float and not isinstance(value, float):
                         raise DataValidationError(f"Campo '{field_name}' deve ser um float. Valor: {value}.")
                    if field_type == str and not isinstance(value, str):
                         raise DataValidationError(f"Campo '{field_name}' deve ser uma string. Valor: {value}.")

            c_datetime = self.crash_datetime
            if c_datetime is None:
                raise DataValidationError(f"Formato de data/hora inválido para 'crash_date' ('{self.crash_date}'). Esperado MM/DD/YYYY HH:MM:SS AM/PM ou MM/DD/YYYY HH:MM AM/PM.")
            
            # Atualiza os campos derivados com base na data do acidente
            self._data['crash_hour'] = c_datetime.hour
            self._data['crash_day_of_week'] = c_datetime.isoweekday()
            self._data['crash_month'] = c_datetime.month

            if not (0 <= self.crash_hour <= 23):
                raise DataValidationError("Hora do acidente fora do intervalo válido (0-23).")
            if not (1 <= self.crash_day_of_week <= 7):
                raise DataValidationError("Dia da semana do acidente fora do intervalo válido (1-7).")
            if not (1 <= self.crash_month <= 12):
                raise DataValidationError("Mês do acidente fora do intervalo válido (1-12).")

            if self.intersection_related_i.upper() not in ['Y', 'N', 'UNKNOWN', '']:
                raise DataValidationError(f"Valor inválido para 'intersection_related_i': '{self.intersection_related_i}'. Esperado 'Y', 'N', 'UNKNOWN' ou vazio.")

            reported_injuries = (
                self.injuries_fatal + self.injuries_incapacitating +
                self.injuries_non_incapacitating + self.injuries_reported_not_evident +
                self.injuries_no_indication
            )
            if self.injuries_total < reported_injuries and self.injuries_total > 0:
                logger.warning(
                    f"Total de lesões ({self.injuries_total}) é menor que a soma das lesões específicas ({reported_injuries})."
                    f" ID do registro (data+hora): {self.crash_date}"
                )

            return True
        except DataValidationError as e:
            logger.warning(f"Falha na validação do DataObject: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado durante a validação do DataObject: {traceback.format_exc()}")
            return False

    def __str__(self):
        """
        Retorna uma representação de string concisa e amigável ao usuário.
        Adaptado do app_v6.py para português.
        """
        return (f"Acidente em {self.crash_date} - Tipo: {self.crash_type} - "
                f"Lesões Totais: {self.injuries_total}")

    def __repr__(self):
        """
        Retorna uma representação de string detalhada para depuração,
        exibindo todos os campos em português brasileiro.
        """
        details = []
        all_fields = [f[0] for f in FIELDS] + ['id', 'crash_hour', 'crash_day_of_week', 'crash_month']
        for field_name in all_fields:
            if field_name in self._data:
                pt_name = FIELD_NAMES_PT.get(field_name, field_name)
                value = getattr(self, field_name)
                details.append(f"{pt_name}='{value}'")

        return f"DataObject({', '.join(details)})"


# --- Funções de Banco de Dados (datamanager_v1.py integrado) ---

DB_FILE_PATH = "data_objects.db"
DB_HEADER_SIZE = 4

def _initialize_db_header(db_file_path: str):
    """
    Inicializa o arquivo DB com um cabeçalho, se ele não existir ou estiver vazio.
    """
    if not os.path.exists(db_file_path) or os.path.getsize(db_file_path) < DB_HEADER_SIZE:
        try:
            with filelock.FileLock(db_file_path + ".lock"):
                Path(db_file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(db_file_path, "r+b" if os.path.exists(db_file_path) else "w+b") as f:
                    f.seek(0)
                    if os.path.getsize(db_file_path) < DB_HEADER_SIZE:
                        f.write(struct.pack('<I', 0))
                    logger.info(f"Arquivo DB '{db_file_path}' inicializado com cabeçalho ID 0.")
        except Exception as e:
            logger.error(f"Erro ao inicializar o cabeçalho do arquivo DB: {e}")

def _read_last_id_from_header(db_file_path: str) -> int:
    """
    Lê o último ID do cabeçalho do arquivo DB.
    """
    _initialize_db_header(db_file_path)

    last_id = 0
    try:
        with filelock.FileLock(db_file_path + ".lock"):
            with open(db_file_path, "rb") as f:
                f.seek(0)
                header_bytes = f.read(DB_HEADER_SIZE)
                if len(header_bytes) == DB_HEADER_SIZE:
                    last_id = struct.unpack('<I', header_bytes)[0]
                else:
                    logger.warning("Cabeçalho do DB incompleto. Re-inicializando.")
                    _initialize_db_header(db_file_path)
                    last_id = 0
    except Exception as e:
        logger.error(f"Erro ao ler último ID do cabeçalho do DB: {e}")
        last_id = 0
    return last_id

def _update_last_id_in_header(db_file_path: str, new_id: int):
    """
    Atualiza o último ID no cabeçalho do arquivo DB.
    """
    try:
        with filelock.FileLock(db_file_path + ".lock"):
            with open(db_file_path, "r+b") as f:
                f.seek(0)
                f.write(struct.pack('<I', new_id))
            logger.info(f"Cabeçalho do DB atualizado com ID: {new_id}")
    except Exception as e:
        logger.error(f"Erro ao atualizar ID no cabeçalho do DB: {e}")

def write_data_object_to_db(data_object: DataObject, db_file_path: str = DB_FILE_PATH):
    """
    Serializa um DataObject e o escreve no arquivo DB com o formato especificado.
    """
    _initialize_db_header(db_file_path)

    current_last_id = _read_last_id_from_header(db_file_path)
    record_id = current_last_id + 1
    logger.info(f"Gerando registro com ID: {record_id}")

    data_object.id = record_id # Atribui o ID ao DataObject

    data_map = data_object.to_map()
    # Garante que o ID esteja no mapa antes da serialização
    if 'id' not in data_map:
         data_map['id'] = record_id

    json_data = json.dumps(data_map, ensure_ascii=False)
    byte_vector = json_data.encode('utf-8')

    sha256_checksum = hashlib.sha256(byte_vector).digest()

    boolean_validator = 1
    total_data_size_with_checksum = len(byte_vector) + len(sha256_checksum)

    record_inner_header = struct.pack('<I B I', record_id, boolean_validator, total_data_size_with_checksum)

    full_record_data = record_inner_header + sha256_checksum + byte_vector

    try:
        with filelock.FileLock(db_file_path + ".lock"):
            with open(db_file_path, "ab") as f:
                f.write(full_record_data)
            _update_last_id_in_header(db_file_path, record_id)
        logger.info(f"Registro ID {record_id} salvo com sucesso em {db_file_path}")
        return True # Retorna True em caso de sucesso
    except Exception as e:
        logger.error(f"Erro ao salvar registro ID {record_id} em {db_file_path}: {e}")
        return False # Retorna False em caso de falha

def read_all_data_objects_from_db(db_file_path: str = DB_FILE_PATH) -> List[Dict[str, Any]]:
    """
    Lê todos os registros DataObject do arquivo DB.
    Retorna uma lista de dicionários, onde cada dicionário representa um DataObject.
    """
    _initialize_db_header(db_file_path) # Garante que o cabeçalho exista

    records = []
    try:
        with filelock.FileLock(db_file_path + ".lock"):
            with open(db_file_path, "rb") as f:
                f.seek(DB_HEADER_SIZE) # Pula o cabeçalho principal
                while True:
                    # Tenta ler o cabeçalho interno do registro (ID, boolean_validator, total_data_size_with_checksum)
                    record_header_bytes = f.read(struct.calcsize('<I B I'))
                    if not record_header_bytes:
                        break # Fim do arquivo

                    record_id, boolean_validator, total_data_size_with_checksum = struct.unpack('<I B I', record_header_bytes)

                    # Lê o SHA-256 checksum (32 bytes)
                    sha256_checksum_read = f.read(32)
                    if len(sha256_checksum_read) < 32:
                        logger.error(f"EOF inesperado ao ler checksum para o registro ID {record_id}.")
                        break

                    # Lê o vetor de bytes (dados JSON)
                    byte_vector_len = total_data_size_with_checksum - 32 # total_data_size_with_checksum já inclui o checksum
                    byte_vector_read = f.read(byte_vector_len)
                    if len(byte_vector_read) < byte_vector_len:
                        logger.error(f"EOF inesperado ao ler dados para o registro ID {record_id}.")
                        break

                    # Valida checksum
                    calculated_checksum = hashlib.sha256(byte_vector_read).digest()
                    if calculated_checksum != sha256_checksum_read:
                        logger.warning(f"Erro de integridade no registro ID {record_id}: Checksum inválido. Pulando.")
                        continue # Pula o registro corrompido

                    # Decodifica e carrega JSON
                    try:
                        json_data_str = byte_vector_read.decode('utf-8')
                        data_map = json.loads(json_data_str)
                        records.append(data_map)
                    except json.JSONDecodeError as je:
                        logger.error(f"Erro de decodificação JSON no registro ID {record_id}: {je}. Dados corrompidos. Pulando.")
                    except Exception as ex:
                        logger.error(f"Erro desconhecido ao processar registro ID {record_id}: {ex}. Pulando.")
        
    except FileNotFoundError:
        logger.info(f"Arquivo DB '{db_file_path}' não encontrado. Retornando lista vazia.")
    except Exception as e:
        logger.error(f"Erro ao abrir ou ler arquivo DB '{db_file_path}': {e}")
    return records

def read_record_by_id_from_db(record_id: int, db_file_path: str = DB_FILE_PATH) -> Optional[Dict[str, Any]]:
    """
    Busca um registro DataObject específico pelo ID no arquivo DB.
    """
    _initialize_db_header(db_file_path)

    try:
        with filelock.FileLock(db_file_path + ".lock"):
            with open(db_file_path, "rb") as f:
                f.seek(DB_HEADER_SIZE) # Pula o cabeçalho principal
                while True:
                    current_pos = f.tell()
                    record_header_bytes = f.read(struct.calcsize('<I B I'))
                    if not record_header_bytes:
                        break

                    rec_id, boolean_validator, total_data_size_with_checksum = struct.unpack('<I B I', record_header_bytes)

                    sha256_checksum_read = f.read(32)
                    byte_vector_len = total_data_size_with_checksum - 32
                    byte_vector_read = f.read(byte_vector_len)

                    if rec_id == record_id:
                        calculated_checksum = hashlib.sha256(byte_vector_read).digest()
                        if calculated_checksum != sha256_checksum_read:
                            logger.warning(f"Erro de integridade no registro ID {rec_id}: Checksum inválido.")
                            return None
                        
                        try:
                            json_data_str = byte_vector_read.decode('utf-8')
                            data_map = json.loads(json_data_str)
                            return data_map
                        except json.JSONDecodeError:
                            logger.error(f"Erro de decodificação JSON para o registro ID {rec_id}.")
                            return None
                    else:
                        # Se não for o ID buscado, avança para o próximo registro
                        continue # Já lemos todos os bytes do registro, então a próxima leitura será do próximo cabeçalho
    except FileNotFoundError:
        logger.info(f"Arquivo DB '{db_file_path}' não encontrado.")
    except Exception as e:
        logger.error(f"Erro ao buscar registro ID {record_id} no DB: {e}")
    return None

def delete_record_by_id_from_db(record_id: int, db_file_path: str = DB_FILE_PATH) -> bool:
    """
    Deleta um registro do DB pelo seu ID, reescrevendo o arquivo.
    ATENÇÃO: Esta é uma operação cara para arquivos grandes.
    """
    _initialize_db_header(db_file_path)

    all_records = []
    found_and_deleted = False

    try:
        with filelock.FileLock(db_file_path + ".lock"):
            # Primeiro, lê todos os registros exceto o que será deletado
            with open(db_file_path, "rb") as f_read:
                f_read.seek(DB_HEADER_SIZE) # Pula o cabeçalho principal
                while True:
                    record_header_bytes = f_read.read(struct.calcsize('<I B I'))
                    if not record_header_bytes:
                        break

                    rec_id, boolean_validator, total_data_size_with_checksum = struct.unpack('<I B I', record_header_bytes)

                    sha256_checksum_read = f_read.read(32)
                    byte_vector_len = total_data_size_with_checksum - 32
                    byte_vector_read = f_read.read(byte_vector_len)

                    if rec_id == record_id:
                        found_and_deleted = True
                        logger.info(f"Registro ID {record_id} encontrado e marcado para exclusão.")
                        continue # Pula este registro na leitura para não incluí-lo na lista
                    
                    # Se não for o registro a ser deletado, adiciona à lista
                    try:
                        json_data_str = byte_vector_read.decode('utf-8')
                        data_map = json.loads(json_data_str)
                        all_records.append(data_map)
                    except json.JSONDecodeError:
                        logger.error(f"Erro de decodificação JSON ao ler registro ID {rec_id} para reescrita. Registro será ignorado.")
                    except Exception as ex:
                        logger.error(f"Erro desconhecido ao ler registro ID {rec_id} para reescrita: {ex}. Registro será ignorado.")
            
            if not found_and_deleted:
                logger.info(f"Registro ID {record_id} não encontrado para exclusão.")
                return False

            # Reescreve o arquivo DB com os registros restantes
            new_last_id = 0
            with open(db_file_path, "wb") as f_write:
                f_write.write(struct.pack('<I', 0)) # Escreve cabeçalho temporário (ID 0)
                for data_map in all_records:
                    # Reatribui IDs sequenciais se necessário, ou usa o ID existente do mapa
                    # Para simplificar, vamos manter o ID original ou reatribuir se houver lacunas
                    # Aqui, a abordagem é reescrever, então os IDs podem ser reindexados ou mantidos.
                    # Vamos manter o ID original de cada registro, mas o 'last_id' do cabeçalho
                    # precisará ser o ID mais alto presente após a reescrita.
                    
                    # Garante que o ID esteja presente no mapa para serialização
                    current_rec_id = data_map.get('id', 0)
                    if current_rec_id > new_last_id:
                        new_last_id = current_rec_id

                    json_data = json.dumps(data_map, ensure_ascii=False)
                    byte_vector = json_data.encode('utf-8')
                    sha256_checksum = hashlib.sha256(byte_vector).digest()
                    boolean_validator = 1
                    total_data_size_with_checksum = len(byte_vector) + len(sha256_checksum)
                    record_inner_header = struct.pack('<I B I', current_rec_id, boolean_validator, total_data_size_with_checksum)
                    full_record_data = record_inner_header + sha256_checksum + byte_vector
                    f_write.write(full_record_data)
            
            # Após reescrita, atualiza o cabeçalho principal com o novo último ID
            _update_last_id_in_header(db_file_path, new_last_id)
            logger.info(f"Registro ID {record_id} deletado e DB reescrito com sucesso.")
            return True

    except FileNotFoundError:
        logger.info(f"Arquivo DB '{db_file_path}' não encontrado para exclusão.")
        return False
    except Exception as e:
        logger.error(f"Erro ao deletar registro ID {record_id} e reescrever DB: {traceback.format_exc()}")
        return False

def process_csv_to_db(csv_file_buffer: io.StringIO, db_filepath: str = DB_FILE_PATH) -> Tuple[int, int]:
    """
    Lê um arquivo CSV de um buffer de string, processa cada linha como um DataObject,
    valida-o e o escreve em um arquivo .db.
    Adapta-se a cabeçalhos em inglês ou português.
    Retorna a contagem de registros processados com sucesso e a contagem de erros.
    """
    processed_count = 0
    invalid_count = 0
    try:
        csv_reader = csv.reader(csv_file_buffer, delimiter=';')
        header = [h.strip() for h in next(csv_reader)] # Remove espaços em branco do cabeçalho

        # Determina o tipo de cabeçalho e cria um mapeamento de coluna para campo do DataObject
        column_to_field_map = {}
        expected_english_fields = [f[0] for f in FIELDS] # Nomes dos campos esperados em inglês
        
        # Primeiro tenta mapear para português, depois para inglês
        is_portuguese_header = False
        for col_name_csv in header:
            if col_name_csv in PORTUGUESE_TO_ENGLISH_HEADERS:
                column_to_field_map[col_name_csv] = PORTUGUESE_TO_ENGLISH_HEADERS[col_name_csv]
                if col_name_csv != PORTUGUESE_TO_ENGLISH_HEADERS[col_name_csv]: # Check if translation occurred
                    is_portuguese_header = True
            elif col_name_csv in expected_english_fields: # Handle if it's already English
                column_to_field_map[col_name_csv] = col_name_csv
            # else: this column is not a recognized field for DataObject, will be ignored

        if not column_to_field_map:
            st.error("Nenhum cabeçalho reconhecível encontrado no arquivo CSV.")
            return 0, len(list(csv_reader)) # All rows will be invalid if header is unknown

        if is_portuguese_header:
            st.info("Detectado cabeçalho em português. Adaptando para importação.")
        else:
            st.info("Detectado cabeçalho em inglês. Prosseguindo com importação.")

        # Valida se os campos *obrigatórios* do DataObject estão presentes no CSV (após o mapeamento)
        missing_required_fields = []
        for field_name, _, _, is_required in FIELDS:
            if is_required and field_name not in column_to_field_map.values():
                missing_required_fields.append(field_name)
        
        if missing_required_fields:
            st.error(f"Campos obrigatórios ausentes no CSV: {', '.join(missing_required_fields)}. Verifique o arquivo.")
            return 0, len(list(csv_reader)) # All rows will be invalid if required fields are missing

        # Mapeamento de índices de coluna para nomes de campo do DataObject
        field_index_map = {col_name_csv: idx for idx, col_name_csv in enumerate(header)}

        for i, row in enumerate(csv_reader):
            logger.info(f"Processando linha {i+1}: {row}")
            if len(row) != len(header):
                st.warning(f"Linha {i+1} tem número de colunas inconsistente ({len(row)} vs {len(header)}). Pulando.")
                invalid_count += 1
                continue

            data_dict = {}
            for col_name_csv, field_name_dataobject in column_to_field_map.items():
                if col_name_csv in field_index_map:
                    col_idx = field_index_map[col_name_csv]
                    # Apenas inclua campos que são diretamente definidos em FIELDS
                    # Campos derivados ('crash_hour', etc.) não são passados via data_dict aqui
                    # Serão gerados pelo DataObject.validate()
                    is_field_direct_input = any(f[0] == field_name_dataobject for f in FIELDS)
                    if is_field_direct_input:
                        data_dict[field_name_dataobject] = row[col_idx].strip()

            try:
                data_obj = DataObject(data_dict)
                if data_obj.validate():
                    if write_data_object_to_db(data_obj, db_filepath):
                        processed_count += 1
                    else:
                        invalid_count += 1 # Contabiliza falha de escrita no DB como inválida
                        st.error(f"Falha ao escrever registro da linha {i+1} no DB: {row}")
                else:
                    invalid_count += 1
                    st.warning(f"Linha {i+1} inválida, não adicionada ao DB. Verifique logs para detalhes.")
            except DataValidationError as e:
                invalid_count += 1
                st.error(f"Erro de validação na linha {i+1}: {e} - Dados: {row}")
            except Exception as e:
                invalid_count += 1
                st.error(f"Erro inesperado ao processar linha {i+1}: {traceback.format_exc()} - Dados: {row}")
    except Exception as e:
        st.error(f"Erro ao ler arquivo CSV: {traceback.format_exc()}")

    st.success(f"Processamento concluído. Registros válidos escritos no DB: {processed_count}. Registros inválidos/erros: {invalid_count}.")
    logger.info(f"Processamento CSV concluído. Registros válidos escritos no DB: {processed_count}. Registros inválidos/erros: {invalid_count}.")
    return processed_count, invalid_count

class Functions:
    """
    Uma coleção de métodos utilitários para lidar com várias tarefas,
    incluindo criptografia, hashing, leitura/escrita de banco de dados
    e funcionalidades de UI/UX para Streamlit.
    """
    
    # --- Configurações de Criptografia e Chaves ---
    _private_key = None
    _public_key = None
    _aes_key = None
    _cipher = None
    _aes_key_path = "aes_key.bin"
    _public_key_path = "public_key.pem"
    _private_key_path = "private_key.pem"
    
    # Adicionando um mecanismo de cache para o banco de dados
    _db_cache = None
    _last_db_modified_time = None
    
    @staticmethod
    def _generate_rsa_key_pair():
        """Gera um par de chaves RSA e salva as chaves."""
        logger.info("Gerando par de chaves RSA...")
        Functions._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        Functions._public_key = Functions._private_key.public_key()
        
        # Salvar chave privada
        with open(Functions._private_key_path, "wb") as f:
            f.write(Functions._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Salvar chave pública
        with open(Functions._public_key_path, "wb") as f:
            f.write(Functions._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
            )
        logger.info("Par de chaves RSA gerado e salvo.")

    @staticmethod
    def _load_rsa_key_pair():
        """Carrega o par de chaves RSA de arquivos."""
        try:
            with open(Functions._private_key_path, "rb") as f:
                Functions._private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
            with open(Functions._public_key_path, "rb") as f:
                Functions._public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            logger.info("Par de chaves RSA carregado com sucesso.")
            return True
        except FileNotFoundError:
            logger.warning("Arquivos de chaves RSA não encontrados.")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar chaves RSA: {e}")
            return False

    @staticmethod
    def _ensure_rsa_keys():
        """Garante que as chaves RSA estejam carregadas ou as gera."""
        if not Functions._private_key or not Functions._public_key:
            if not Functions._load_rsa_key_pair():
                Functions._generate_rsa_key_pair()

    @staticmethod
    def _generate_aes_key():
        """Gera e salva uma chave AES aleatória."""
        logger.info("Gerando chave AES...")
        Functions._aes_key = os.urandom(32)  # 256-bit key
        with open(Functions._aes_key_path, "wb") as f:
            f.write(Functions._aes_key)
        logger.info("Chave AES gerada e salva.")

    @staticmethod
    def _load_aes_key():
        """Carrega a chave AES de um arquivo."""
        try:
            with open(Functions._aes_key_path, "rb") as f:
                Functions._aes_key = f.read()
            logger.info("Chave AES carregada com sucesso.")
            return True
        except FileNotFoundError:
            logger.warning("Arquivo de chave AES não encontrado.")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar chave AES: {e}")
            return False

    @staticmethod
    def _ensure_aes_key():
        """Garante que a chave AES esteja carregada ou a gera."""
        if not Functions._aes_key:
            if not Functions._load_aes_key():
                Functions._generate_aes_key()

    @staticmethod
    def encrypt_with_aes(plaintext: bytes) -> bytes:
        """Criptografa dados usando AES no modo GCM."""
        Functions._ensure_aes_key()
        nonce = os.urandom(16)
        cipher = Cipher(algorithms.AES(Functions._aes_key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return nonce + encryptor.tag + ciphertext

    @staticmethod
    def decrypt_with_aes(ciphertext: bytes) -> Optional[bytes]:
        """Descriptografa dados usando AES no modo GCM."""
        Functions._ensure_aes_key()
        nonce = ciphertext[:16]
        tag = ciphertext[16:32]
        encrypted_data = ciphertext[32:]
        try:
            cipher = Cipher(algorithms.AES(Functions._aes_key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return decryptor.update(encrypted_data) + decryptor.finalize()
        except CryptoInvalidTag:
            logger.error("Erro: Tag de autenticação inválida durante a descriptografia AES.")
            return None
        except Exception as e:
            logger.error(f"Erro durante a descriptografia AES: {e}")
            return None

    @staticmethod
    def encrypt_aes_key_with_rsa() -> Optional[bytes]:
        """Criptografa a chave AES com a chave pública RSA."""
        Functions._ensure_rsa_keys()
        Functions._ensure_aes_key()
        if not Functions._public_key or not Functions._aes_key:
            return None
        
        try:
            encrypted_aes_key = Functions._public_key.encrypt(
                Functions._aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return encrypted_aes_key
        except Exception as e:
            logger.error(f"Erro ao criptografar chave AES com RSA: {e}")
            return None

    @staticmethod
    def decrypt_aes_key_with_rsa(encrypted_aes_key: bytes) -> Optional[bytes]:
        """Descriptografa a chave AES com a chave privada RSA."""
        Functions._ensure_rsa_keys()
        if not Functions._private_key:
            return None
        
        try:
            decrypted_aes_key = Functions._private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            Functions._aes_key = decrypted_aes_key # Atualiza a chave AES interna
            logger.info("Chave AES descriptografada e carregada.")
            return decrypted_aes_key
        except Exception as e:
            logger.error(f"Erro ao descriptografar chave AES com RSA: {e}")
            return None

    @staticmethod
    def generate_sha256_checksum(data: bytes) -> str:
        """Gera o checksum SHA-256 de um dado em bytes."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def generate_md5_checksum(data: bytes) -> str:
        """Gera o checksum MD5 de um dado em bytes."""
        return hashlib.md5(data).hexdigest()
        
    @staticmethod
    def _get_db_modified_time(db_file_path: str = DB_FILE_PATH):
        """Obtém a última vez que o arquivo DB foi modificado."""
        if os.path.exists(db_file_path):
            return os.path.getmtime(db_file_path)
        return 0

    @staticmethod
    def load_data_from_db(db_file_path: str = DB_FILE_PATH, force_reload: bool = False) -> pd.DataFrame:
        """
        Carrega dados do banco de dados para um DataFrame, usando cache.
        """
        current_modified_time = Functions._get_db_modified_time(db_file_path)

        if not force_reload and Functions._db_cache is not None and \
           Functions._last_db_modified_time == current_modified_time:
            logger.info("Carregando dados do DB do cache.")
            return Functions._db_cache
        
        logger.info(f"Carregando todos os registros do DB: {db_file_path}")
        records_as_dicts = read_all_data_objects_from_db(db_file_path)
        
        if records_as_dicts:
            df = pd.DataFrame(records_as_dicts)
            # Reordenar colunas para corresponder a FIELDS, adicionando 'id' no início
            # e incluindo os campos derivados que agora fazem parte do to_map()
            ordered_columns_english = ['id'] + [f[0] for f in FIELDS] + ['crash_hour', 'crash_day_of_week', 'crash_month']
            # Filtra colunas que realmente existem no DataFrame
            df = df[[col for col in ordered_columns_english if col in df.columns]]
            
            # Traduzir nomes das colunas para português
            df = df.rename(columns=FIELD_NAMES_PT)
        else:
            # Cria um DataFrame vazio com as colunas em português
            # Garante que todas as colunas possíveis (id + FIELDS + derivados) estejam no DF vazio
            all_possible_fields = ['id'] + [f[0] for f in FIELDS] + ['crash_hour', 'crash_day_of_week', 'crash_month']
            columns_pt = [FIELD_NAMES_PT.get(f, f) for f in all_possible_fields]
            df = pd.DataFrame(columns=columns_pt)
            logger.info("Nenhum registro encontrado no DB. DataFrame vazio criado.")

        Functions._db_cache = df
        Functions._last_db_modified_time = current_modified_time
        return df

    @staticmethod
    def add_new_entry(entry_data: Dict[str, Any]) -> bool:
        """
        Adiciona um novo registro ao DB a partir de um dicionário de dados.
        """
        try:
            data_obj = DataObject(entry_data)
            if data_obj.validate():
                success = write_data_object_to_db(data_obj)
                if success:
                    st.success("Registro adicionado com sucesso!")
                    Functions.load_data_from_db(force_reload=True) # Invalida cache
                    return True
                else:
                    st.error("Erro ao salvar o registro no banco de dados.")
                    return False
            else:
                st.error("Dados do registro inválidos. Verifique os campos.")
                return False
        except DataValidationError as e:
            st.error(f"Erro de validação: {e}")
            return False
        except Exception as e:
            st.error(f"Erro inesperado ao adicionar registro: {traceback.format_exc()}")
            return False

    @staticmethod
    def search_records_by_id(record_id: int) -> Optional[pd.DataFrame]:
        """
        Busca um registro pelo ID e retorna como DataFrame.
        """
        record_map = read_record_by_id_from_db(record_id)
        if record_map:
            df = pd.DataFrame([record_map])
            df = df.rename(columns=FIELD_NAMES_PT)
            return df
        return None

    @staticmethod
    def delete_record_by_id(record_id: int) -> bool:
        """
        Deleta um registro pelo ID.
        """
        success = delete_record_by_id_from_db(record_id)
        if success:
            st.success(f"Registro ID {record_id} deletado com sucesso!")
            Functions.load_data_from_db(force_reload=True) # Invalida cache
        else:
            st.error(f"Não foi possível deletar o registro ID {record_id}. Verifique se o ID existe ou consulte os logs.")
        return success
    
    @staticmethod
    def upload_csv_to_db(uploaded_file):
        """Processa um arquivo CSV carregado e o insere no DB."""
        if uploaded_file is not None:
            string_io = io.StringIO(uploaded_file.getvalue().decode("latin-1"))
            processed, invalid = process_csv_to_db(string_io)
            if processed > 0:
                st.success(f"CSV processado! {processed} registros válidos adicionados. {invalid} registros inválidos/erros.")
                Functions.load_data_from_db(force_reload=True) # Recarrega dados após upload
            elif invalid > 0:
                st.warning(f"Nenhum registro válido do CSV foi adicionado. {invalid} registros inválidos/erros. Verifique o formato do arquivo.")
            else:
                st.info("O arquivo CSV está vazio ou não contém dados válidos.")

# ===================================================== STREAMLIT UI =====================================================

st.set_page_config(layout="wide", page_title="Sistema de Gerenciamento de Acidentes de Trânsito", page_icon="🚨")

# --- Sidebar ---
st.sidebar.title("Navegação")
# Sidebar navigation options
page = st.sidebar.radio("Ir para", ["Início", "Adicionar Novo Registro", "Visualizar Registros", "Buscar Registros", "Deletar Registros", "Upload CSV", "Sobre"])

st.sidebar.markdown("---")
st.sidebar.subheader("Informações do Sistema")
st.sidebar.write("Versão: 1.0_20250707 Alpha")
st.sidebar.write("Status do DB: Online ✅") # Simplificado

# Garante que as chaves RSA e AES existam ao iniciar o aplicativo
Functions._ensure_rsa_keys()
Functions._ensure_aes_key()

# ===================================================== Main Content Area =====================================================

if page == "Início":
    st.title("Bem-vindo ao Sistema de Gerenciamento de Acidentes de Trânsito")
    st.markdown("""
        Este aplicativo Streamlit foi desenvolvido para gerenciar dados de acidentes de trânsito.
        Ele permite adicionar novos registros, visualizar todos os registros existentes, buscar
        registros por ID, deletar registros e fazer upload de arquivos CSV.

        Utiliza um sistema de armazenamento de dados binário com validação de integridade (checksum SHA-256)
        e um cabeçalho otimizado para o controle de IDs, além de funcionalidades criptográficas (AES e RSA)
        para segurança futura dos dados.
    """)
    st.subheader("Funcionalidades Principais:")
    st.markdown("""
    - **Adicionar Novo Registro**: Insira dados de um novo acidente.
    - **Visualizar Registros**: Veja todos os acidentes registrados em uma tabela interativa.
    - **Buscar Registros**: Encontre um acidente específico pelo seu ID.
    - **Deletar Registros**: Remova um registro de acidente existente.
    - **Upload CSV**: Carregue dados de acidentes em massa a partir de um arquivo CSV.
    - **Criptografia e Hashing**: Gerenciamento interno de chaves AES e RSA para futuras implementações de segurança de dados.
    """)

elif page == "Adicionar Novo Registro":
    st.title("Adicionar Novo Registro de Acidente")

    with st.form("form_add_entry", clear_on_submit=True):
        st.subheader("Detalhes do Acidente")
        
        # Inputs para os campos (usando FIELD_NAMES_PT para os rótulos)
        col1, col2 = st.columns(2)
        
        with col1:
            crash_date_str = st.text_input(FIELD_NAMES_PT['crash_date'], help="Formato: MM/DD/AAAA HH:MM:SS AM/PM", value=datetime.now().strftime('%m/%d/%Y %I:%M:%S %p'))
            # crash_hour, crash_day_of_week, crash_month serão derivados do crash_date na validação
            traffic_control_device = st.selectbox(FIELD_NAMES_PT['traffic_control_device'], TRAFFIC_CONTROL_DEVICE_OPTIONS)
            weather_condition = st.selectbox(FIELD_NAMES_PT['weather_condition'], WEATHER_CONDITION_OPTIONS)
            lighting_condition = st.selectbox(FIELD_NAMES_PT['lighting_condition'], LIGHTING_CONDITION_OPTIONS)
            first_crash_type = st.text_input(FIELD_NAMES_PT['first_crash_type'], value="COLISAO FRONTAL")
            trafficway_type = st.text_input(FIELD_NAMES_PT['trafficway_type'], value="VIA EXPRESSA")
            alignment = st.text_input(FIELD_NAMES_PT['alignment'], value="RETO")
            roadway_surface_cond = st.text_input(FIELD_NAMES_PT['roadway_surface_cond'], value="SECO")
            
        with col2:
            road_defect = st.text_input(FIELD_NAMES_PT['road_defect'], value="NENHUM")
            crash_type = st.selectbox(FIELD_NAMES_PT['crash_type'], CRASH_TYPE_OPTIONS)
            intersection_related_i = st.selectbox(FIELD_NAMES_PT['intersection_related_i'], INTERSECTION_RELATED_OPTIONS)
            damage = st.selectbox(FIELD_NAMES_PT['damage'], DAMAGE_OPTIONS)
            prim_contributory_cause = st.text_input(FIELD_NAMES_PT['prim_contributory_cause'], value="NAO INFORMADO")
            num_units = st.number_input(FIELD_NAMES_PT['num_units'], min_value=0, value=1)
            most_severe_injury = st.selectbox(FIELD_NAMES_PT['most_severe_injury'], MOST_SEVERE_INJURY_OPTIONS)
            injuries_total = st.number_input(FIELD_NAMES_PT['injuries_total'], min_value=0, value=0)
            injuries_fatal = st.number_input(FIELD_NAMES_PT['injuries_fatal'], min_value=0, value=0)
            injuries_incapacitating = st.number_input(FIELD_NAMES_PT['injuries_incapacitating'], min_value=0, value=0)
            injuries_non_incapacitating = st.number_input(FIELD_NAMES_PT['injuries_non_incapacitating'], min_value=0, value=0)
            injuries_reported_not_evident = st.number_input(FIELD_NAMES_PT['injuries_reported_not_evident'], min_value=0, value=0)
            injuries_no_indication = st.number_input(FIELD_NAMES_PT['injuries_no_indication'], min_value=0, value=0)

        submitted = st.form_submit_button("Adicionar Registro")

        if submitted:
            entry_data = {
                'crash_date': crash_date_str,
                'traffic_control_device': traffic_control_device,
                'weather_condition': weather_condition,
                'lighting_condition': lighting_condition,
                'first_crash_type': first_crash_type,
                'trafficway_type': trafficway_type,
                'alignment': alignment,
                'roadway_surface_cond': roadway_surface_cond,
                'road_defect': road_defect,
                'crash_type': crash_type,
                'intersection_related_i': intersection_related_i,
                'damage': damage,
                'prim_contributory_cause': prim_contributory_cause,
                'num_units': num_units,
                'most_severe_injury': most_severe_injury,
                'injuries_total': injuries_total,
                'injuries_fatal': injuries_fatal,
                'injuries_incapacitating': injuries_incapacitating,
                'injuries_non_incapacitating': injuries_non_incapacitating,
                'injuries_reported_not_evident': injuries_reported_not_evident,
                'injuries_no_indication': injuries_no_indication,
            }
            Functions.add_new_entry(entry_data)

elif page == "Visualizar Registros":
    st.title("Visualizar Todos os Registros de Acidentes")

    df = Functions.load_data_from_db()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button(
            label="Baixar Dados como CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="registros_acidentes.csv",
            mime="text/csv",
        )
    else:
        st.info("Nenhum registro encontrado no banco de dados. Adicione novos registros ou faça upload de um CSV.")

elif page == "Buscar Registros":
    st.title("Buscar Registros de Acidentes por ID")

    search_id = st.number_input("Digite o ID do Registro:", min_value=1, value=1, step=1)
    if st.button("Buscar"):
        found_record_df = Functions.search_records_by_id(search_id)
        if found_record_df is not None:
            st.subheader(f"Registro Encontrado (ID: {search_id})")
            st.dataframe(found_record_df, use_container_width=True)
        else:
            st.warning(f"Nenhum registro encontrado com o ID: {search_id}.")

elif page == "Deletar Registros":
    st.title("Deletar Registro de Acidente por ID")

    delete_id = st.number_input("Digite o ID do Registro a ser Deletado:", min_value=1, value=1, step=1)
    if st.button("Deletar Registro"):
        if st.checkbox(f"Confirmar exclusão do registro ID {delete_id}?", key=f"confirm_delete_{delete_id}"):
            Functions.delete_record_by_id(delete_id)
            # A recarga do DataFrame já é feita dentro de Functions.delete_record_by_id
        else:
            st.info("Marque a caixa de confirmação para deletar o registro.")

elif page == "Upload CSV":
    st.title("Upload de Dados de Acidentes via CSV")
    st.markdown("""
        Faça upload de um arquivo CSV contendo dados de acidentes.
        O arquivo CSV deve usar ponto e vírgula (`;`) como delimitador
        e pode ter cabeçalhos em **inglês** ou **português**.

        **Exemplo de cabeçalho em Inglês:**
        `crash_date;traffic_control_device;weather_condition;lighting_condition;first_crash_type;...`

        **Exemplo de cabeçalho em Português:**
        `crash_date;dispositivo_de_controle_de_tráfego;condição_climática;condição_de_iluminação;primeiro_tipo_de_acidente;...`

        A coluna `crash_date` deve estar no formato `MM/DD/AAAA HH:MM:SS AM/PM`.
    """)

    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=["csv"])

    if uploaded_file is not None:
        st.write("Arquivo carregado com sucesso!")
        if st.button("Processar e Adicionar ao Banco de Dados"):
            Functions.upload_csv_to_db(uploaded_file)

elif page == "Sobre":
    st.title("Sobre o Sistema")
    st.markdown("""
        Este é um sistema de demonstração para gerenciamento de dados de acidentes de trânsito.
        Desenvolvido com Python e Streamlit, focado em mostrar a manipulação de dados
        e conceitos de armazenamento binário.
    """)
    st.subheader("Tecnologias Utilizadas")
    st.markdown("""
    - **Python**: Linguagem de programação principal.
    - **Streamlit**: Para a interface de usuário web interativa e ágil.
    - **`cryptography`**: Biblioteca robusta para operações criptográficas (AES, RSA).
    - **`filelock`**: Para gerenciamento de concorrência e garantia da integridade do arquivo em operações multi-threaded/multi-processo.
    - **`pathlib`**: Módulo para manipulação de caminhos de arquivos e diretórios de forma orientada a objetos.
    - **`pandas`**: Essencial para manipulação e exibição de dados tabulares (DataFrames).
    - **`hashlib`**: Para geração de checksums (SHA-256) e MD5.
    - **`struct`**: Para empacotar/desempacotar dados binários no formato do banco de dados.
    - **`json`**: Para serialização/desserialização de dados de objetos.
    - **`logging`**: Para registro de informações, avisos e erros.
    - **`datetime`**: Para manipulação de datas e horas.
    - **`io`**: Para lidar com streams de dados de arquivos em memória.
    """)
    st.write("Versão: 1.0_20250707 Alpha")
    st.markdown("Repositório: [Deploy da Aplicação](https://github.com/kasshinokun/Q1_Q2_2025_Public/tree/main/Aulas_AED3/Python_Adapt/Deploy)")