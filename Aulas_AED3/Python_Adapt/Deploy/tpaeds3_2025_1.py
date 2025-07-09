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
    'id': 'ID do Registro',
    'is_active': 'Registro Ativo' # Adicionado para a exclusão lógica
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
        self._data['is_active'] = 1 # Novo campo para exclusão lógica: 1 = ativo, 0 = inativo

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
        # Se 'is_active' for passado no data_dict, armazena-o, caso contrário, usa o padrão (1)
        if 'is_active' in data_dict:
            self._data['is_active'] = int(data_dict['is_active'])


    # Removido from_csv_row, pois o parsing agora será feito em process_csv_to_db

    def to_map(self) -> Dict[str, Any]:
        """
        Converte a instância de DataObject para um dicionário (mapa),
        incluindo o 'id' se presente e os campos derivados.
        Inclui o campo 'is_active'.
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
        # Permite definir o atributo 'id' e os campos derivados, e 'is_active'
        if name in ['id', 'crash_hour', 'crash_day_of_week', 'crash_month', 'is_active']:
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

            # Validação para is_active
            if not isinstance(self._data.get('is_active'), int) or self._data['is_active'] not in [0, 1]:
                raise DataValidationError("Campo 'is_active' deve ser 0 ou 1.")

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
        """
        status = "Ativo" if self.is_active == 1 else "Inativo (Deletado)"
        return (f"Acidente em {self.crash_date} - Tipo: {self.crash_type} - "
                f"Lesões Totais: {self.injuries_total} - Status: {status}")

    def __repr__(self):
        """
        Retorna uma representação de string detalhada para depuração,
        exibindo todos os campos em português brasileiro.
        """
        details = []
        all_fields = [f[0] for f in FIELDS] + ['id', 'crash_hour', 'crash_day_of_week', 'crash_month', 'is_active']
        for field_name in all_fields:
            if field_name in self._data:
                pt_name = FIELD_NAMES_PT.get(field_name, field_name)
                value = getattr(self, field_name)
                details.append(f"{pt_name}='{value}'")

        return f"DataObject({', '.join(details)})"


# --- Nova Classe: TrafficAccidentDB ---

class TrafficAccidentDB:
    """
    Gerencia as operações de CRUD para registros de acidentes de trânsito
    em um arquivo binário, incluindo funcionalidade de exclusão lógica e
    importação/exportação de CSV.
    """
    DB_HEADER_SIZE = 4 # Tamanho do cabeçalho principal que armazena o último ID
    RECORD_INNER_HEADER_FORMAT = '<I B I'
    RECORD_INNER_HEADER_SIZE = struct.calcsize(RECORD_INNER_HEADER_FORMAT)
    CHECKSUM_SIZE = 32 # SHA256 é 32 bytes

    def __init__(self, db_file_path: str = "data_objects.db"):
        self.db_file_path = db_file_path
        self._initialize_db_header()

    def _initialize_db_header(self):
        """
        Inicializa o arquivo DB com um cabeçalho, se ele não existir ou estiver vazio.
        """
        if not os.path.exists(self.db_file_path) or os.path.getsize(self.db_file_path) < self.DB_HEADER_SIZE:
            try:
                with filelock.FileLock(self.db_file_path + ".lock"):
                    Path(self.db_file_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(self.db_file_path, "r+b" if os.path.exists(self.db_file_path) else "w+b") as f:
                        f.seek(0)
                        if os.path.getsize(self.db_file_path) < self.DB_HEADER_SIZE:
                            f.write(struct.pack('<I', 0))
                        logger.info(f"Arquivo DB '{self.db_file_path}' inicializado com cabeçalho ID 0.")
            except Exception as e:
                logger.error(f"Erro ao inicializar o cabeçalho do arquivo DB: {e}")

    def _read_last_id_from_header(self) -> int:
        """
        Lê o último ID do cabeçalho do arquivo DB.
        """
        self._initialize_db_header()

        last_id = 0
        try:
            with filelock.FileLock(self.db_file_path + ".lock"):
                with open(self.db_file_path, "rb") as f:
                    f.seek(0)
                    header_bytes = f.read(self.DB_HEADER_SIZE)
                    if len(header_bytes) == self.DB_HEADER_SIZE:
                        last_id = struct.unpack('<I', header_bytes)[0]
                    else:
                        logger.warning("Cabeçalho do DB incompleto. Re-inicializando.")
                        self._initialize_db_header()
                        last_id = 0
        except Exception as e:
            logger.error(f"Erro ao ler último ID do cabeçalho do DB: {e}")
            last_id = 0
        return last_id

    def _update_last_id_in_header(self, new_id: int):
        """
        Atualiza o último ID no cabeçalho do arquivo DB.
        """
        try:
            with filelock.FileLock(self.db_file_path + ".lock"):
                with open(self.db_file_path, "r+b") as f:
                    f.seek(0)
                    f.write(struct.pack('<I', new_id))
                logger.info(f"Cabeçalho do DB atualizado com ID: {new_id}")
        except Exception as e:
            logger.error(f"Erro ao atualizar ID no cabeçalho do DB: {e}")

    def write_data_object(self, data_object: DataObject) -> bool:
        """
        Serializa um DataObject e o escreve no arquivo DB com o formato especificado.
        """
        self._initialize_db_header()

        current_last_id = self._read_last_id_from_header()
        record_id = current_last_id + 1
        logger.info(f"Gerando registro com ID: {record_id}")

        data_object.id = record_id # Atribui o ID ao DataObject
        data_object.is_active = 1 # Garante que o registro é marcado como ativo ao ser escrito

        data_map = data_object.to_map()
        # Garante que o ID esteja no mapa antes da serialização
        if 'id' not in data_map:
             data_map['id'] = record_id
        if 'is_active' not in data_map:
            data_map['is_active'] = 1

        json_data = json.dumps(data_map, ensure_ascii=False)
        byte_vector = json_data.encode('utf-8')

        sha256_checksum = hashlib.sha256(byte_vector).digest()

        # boolean_validator agora representa o status is_active do DataObject
        is_active_status = data_object.is_active
        total_data_size_with_checksum = len(byte_vector) + len(sha256_checksum)

        record_inner_header = struct.pack(self.RECORD_INNER_HEADER_FORMAT, record_id, is_active_status, total_data_size_with_checksum)

        full_record_data = record_inner_header + sha256_checksum + byte_vector

        try:
            with filelock.FileLock(self.db_file_path + ".lock"):
                with open(self.db_file_path, "ab") as f:
                    f.write(full_record_data)
                self._update_last_id_in_header(record_id)
            logger.info(f"Registro ID {record_id} salvo com sucesso em {self.db_file_path}")
            return True # Retorna True em caso de sucesso
        except Exception as e:
            logger.error(f"Erro ao salvar registro ID {record_id} em {self.db_file_path}: {e}")
            return False # Retorna False em caso de falha

    def read_all_data_objects(self) -> List[Dict[str, Any]]:
        """
        Lê todos os registros DataObject do arquivo DB que estão ativos.
        Retorna uma lista de dicionários, onde cada dicionário representa um DataObject.
        """
        self._initialize_db_header() # Garante que o cabeçalho exista

        records = []
        try:
            with filelock.FileLock(self.db_file_path + ".lock"):
                with open(self.db_file_path, "rb") as f:
                    f.seek(self.DB_HEADER_SIZE) # Pula o cabeçalho principal
                    while True:
                        # Tenta ler o cabeçalho interno do registro (ID, is_active, total_data_size_with_checksum)
                        record_header_bytes = f.read(self.RECORD_INNER_HEADER_SIZE)
                        if not record_header_bytes:
                            break # Fim do arquivo

                        record_id, is_active, total_data_size_with_checksum = struct.unpack(self.RECORD_INNER_HEADER_FORMAT, record_header_bytes)

                        # Posição atual para ler o checksum e os dados
                        current_record_data_start_pos = f.tell()

                        # Lê o SHA-256 checksum (32 bytes)
                        sha256_checksum_read = f.read(self.CHECKSUM_SIZE)
                        if len(sha256_checksum_read) < self.CHECKSUM_SIZE:
                            logger.error(f"EOF inesperado ao ler checksum para o registro ID {record_id}.")
                            break

                        # Lê o vetor de bytes (dados JSON)
                        byte_vector_len = total_data_size_with_checksum - self.CHECKSUM_SIZE
                        byte_vector_read = f.read(byte_vector_len)
                        if len(byte_vector_read) < byte_vector_len:
                            logger.error(f"EOF inesperado ao ler dados para o registro ID {record_id}.")
                            break

                        # **AQUI É A MUDANÇA PARA EXCLUSÃO LÓGICA:**
                        # Apenas processa registros que estão ativos (is_active == 1)
                        if is_active == 1:
                            # Valida checksum
                            calculated_checksum = hashlib.sha256(byte_vector_read).digest()
                            if calculated_checksum != sha256_checksum_read:
                                logger.warning(f"Erro de integridade no registro ID {record_id}: Checksum inválido. Pulando.")
                                continue # Pula o registro corrompido

                            # Decodifica e carrega JSON
                            try:
                                json_data_str = byte_vector_read.decode('utf-8')
                                data_map = json.loads(json_data_str)
                                data_map['is_active'] = is_active # Adiciona o status is_active ao mapa retornado
                                records.append(data_map)
                            except json.JSONDecodeError as je:
                                logger.error(f"Erro de decodificação JSON no registro ID {record_id}: {je}. Dados corrompidos. Pulando.")
                            except Exception as ex:
                                logger.error(f"Erro desconhecido ao processar registro ID {record_id}: {ex}. Pulando.")
                        else:
                            logger.info(f"Registro ID {record_id} está logicamente deletado. Pulando.")
            
        except FileNotFoundError:
            logger.info(f"Arquivo DB '{self.db_file_path}' não encontrado. Retornando lista vazia.")
        except Exception as e:
            logger.error(f"Erro ao abrir ou ler arquivo DB '{self.db_file_path}': {e}")
        return records

    def read_record_by_id(self, record_id: int, include_inactive: bool = False) -> Optional[Dict[str, Any]]:
        """
        Busca um registro DataObject específico pelo ID no arquivo DB.
        Por padrão, retorna apenas registros ativos. Use include_inactive=True para incluir inativos.
        """
        self._initialize_db_header()

        try:
            with filelock.FileLock(self.db_file_path + ".lock"):
                with open(self.db_file_path, "rb") as f:
                    f.seek(self.DB_HEADER_SIZE) # Pula o cabeçalho principal
                    while True:
                        current_record_start_pos = f.tell() # Salva a posição atual para cálculo de offset
                        record_header_bytes = f.read(self.RECORD_INNER_HEADER_SIZE)
                        if not record_header_bytes:
                            break

                        rec_id, is_active, total_data_size_with_checksum = struct.unpack(self.RECORD_INNER_HEADER_FORMAT, record_header_bytes)

                        # Calcula a posição para o próximo registro
                        next_record_pos = current_record_start_pos + self.RECORD_INNER_HEADER_SIZE + total_data_size_with_checksum

                        if rec_id == record_id:
                            # Se o ID corresponder, lê o checksum e os dados
                            f.seek(current_record_start_pos + self.RECORD_INNER_HEADER_SIZE) # Volta para ler o checksum
                            sha256_checksum_read = f.read(self.CHECKSUM_SIZE)
                            byte_vector_len = total_data_size_with_checksum - self.CHECKSUM_SIZE
                            byte_vector_read = f.read(byte_vector_len)

                            if is_active == 0 and not include_inactive:
                                logger.info(f"Registro ID {record_id} encontrado, mas está inativo e não foi solicitado (include_inactive=False).")
                                return None # Não retorna registros inativos por padrão

                            calculated_checksum = hashlib.sha256(byte_vector_read).digest()
                            if calculated_checksum != sha256_checksum_read:
                                logger.warning(f"Erro de integridade no registro ID {rec_id}: Checksum inválido.")
                                return None
                            
                            try:
                                json_data_str = byte_vector_read.decode('utf-8')
                                data_map = json.loads(json_data_str)
                                data_map['is_active'] = is_active # Adiciona o status is_active ao mapa
                                return data_map
                            except json.JSONDecodeError:
                                logger.error(f"Erro de decodificação JSON para o registro ID {rec_id}.")
                                return None
                        else:
                            # Se não for o ID buscado, avança para o próximo registro
                            f.seek(next_record_pos) # Pula para o início do próximo registro
                            continue
        except FileNotFoundError:
            logger.info(f"Arquivo DB '{self.db_file_path}' não encontrado.")
        except Exception as e:
            logger.error(f"Erro ao buscar registro ID {record_id} no DB: {e}")
        return None


    def delete_record_by_id(self, record_id: int) -> bool:
        """
        Realiza a exclusão lógica de um registro no DB pelo seu ID,
        alterando o campo 'is_active' para 0.
        """
        self._initialize_db_header()

        found_and_marked_for_deletion = False

        try:
            with filelock.FileLock(self.db_file_path + ".lock"):
                with open(self.db_file_path, "r+b") as f:
                    f.seek(self.DB_HEADER_SIZE) # Pula o cabeçalho principal
                    while True:
                        current_record_start_pos = f.tell() # Posição de início do registro
                        
                        record_header_bytes = f.read(self.RECORD_INNER_HEADER_SIZE)
                        if not record_header_bytes:
                            break # Fim do arquivo

                        rec_id, is_active, total_data_size_with_checksum = struct.unpack(self.RECORD_INNER_HEADER_FORMAT, record_header_bytes)

                        # Calcula a posição para o próximo registro
                        next_record_pos = current_record_start_pos + self.RECORD_INNER_HEADER_SIZE + total_data_size_with_checksum

                        if rec_id == record_id:
                            if is_active == 0:
                                logger.info(f"Registro ID {record_id} já está logicamente deletado.")
                                return True # Já está deletado, consideramos sucesso
                            
                            # Move o ponteiro de volta para a posição do boolean_validator
                            # O boolean_validator (is_active) está no offset 4 (depois do ID de 4 bytes)
                            f.seek(current_record_start_pos + struct.calcsize('<I')) # Pula o ID (4 bytes)
                            
                            # Escreve 0 para marcar como inativo
                            f.write(struct.pack('<B', 0)) 
                            logger.info(f"Registro ID {record_id} marcado como logicamente deletado.")
                            found_and_marked_for_deletion = True
                            break # Encontrou e atualizou, pode sair
                        
                        # Se não for o ID buscado, avança para o próximo registro
                        f.seek(next_record_pos)

            if found_and_marked_for_deletion:
                return True
            else:
                logger.info(f"Registro ID {record_id} não encontrado para exclusão lógica.")
                return False

        except FileNotFoundError:
            logger.info(f"Arquivo DB '{self.db_file_path}' não encontrado para exclusão lógica.")
            return False
        except Exception as e:
            logger.error(f"Erro ao realizar exclusão lógica para o registro ID {record_id}: {traceback.format_exc()}")
            return False

    def process_csv_to_db(self, csv_file_buffer: io.StringIO) -> Tuple[int, int]:
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
                if col_name_csv.lower() in PORTUGUESE_TO_ENGLISH_HEADERS: # Convert to lower for robust matching
                    mapped_field = PORTUGUESE_TO_ENGLISH_HEADERS[col_name_csv.lower()]
                    column_to_field_map[col_name_csv] = mapped_field
                    if col_name_csv.lower() != mapped_field.lower(): # Check if translation occurred
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
                        if self.write_data_object(data_obj): # Chama o método da instância
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

# --- Funções de UI (Streamlit) e Lógica de Negócio que usarão a nova classe ---

class Functions: # Renomeada para evitar conflito com a classe TrafficAccidentDB
    """
    Uma coleção de métodos utilitários para lidar com várias tarefas,
    incluindo criptografia, hashing, leitura/escrita de banco de dados
    e funcionalidades de UI/UX para Streamlit.
    """
    
    # Instância da classe de banco de dados
    _db_manager = TrafficAccidentDB(db_file_path="data_objects.db") # Instancia a classe aqui
    
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
    def _get_db_modified_time(): # db_file_path agora é acessado via _db_manager
        """Obtém a última vez que o arquivo DB foi modificado."""
        db_file_path = Functions._db_manager.db_file_path
        if os.path.exists(db_file_path):
            return os.path.getmtime(db_file_path)
        return 0

    @staticmethod
    def load_data_from_db(force_reload: bool = False) -> pd.DataFrame:
        """
        Carrega dados do banco de dados para um DataFrame, usando cache.
        Apenas registros ativos são carregados por padrão.
        """
        current_modified_time = Functions._get_db_modified_time()

        if not force_reload and Functions._db_cache is not None and \
           Functions._last_db_modified_time == current_modified_time:
            logger.info("Carregando dados do DB do cache.")
            return Functions._db_cache
        
        logger.info(f"Carregando todos os registros ATIVOS do DB: {Functions._db_manager.db_file_path}")
        # Chama o método da instância de TrafficAccidentDB
        records_as_dicts = Functions._db_manager.read_all_data_objects() 

        if records_as_dicts:
            df = pd.DataFrame(records_as_dicts)
            # Reordenar colunas para corresponder a FIELDS, adicionando 'id' e 'is_active' no início
            # e incluindo os campos derivados que agora fazem parte do to_map()
            ordered_columns_english = ['id', 'is_active'] + [f[0] for f in FIELDS] + ['crash_hour', 'crash_day_of_week', 'crash_month']
            # Filtra colunas que realmente existem no DataFrame
            df = df[[col for col in ordered_columns_english if col in df.columns]]
            
            # Traduzir nomes das colunas para português
            df = df.rename(columns=FIELD_NAMES_PT)
        else:
            # Cria um DataFrame vazio com as colunas em português
            # Garante que todas as colunas possíveis (id + is_active + FIELDS + derivados) estejam no DF vazio
            all_possible_fields = ['id', 'is_active'] + [f[0] for f in FIELDS] + ['crash_hour', 'crash_day_of_week', 'crash_month']
            columns_pt = [FIELD_NAMES_PT.get(f, f) for f in all_possible_fields]
            df = pd.DataFrame(columns=columns_pt)
            logger.info("Nenhum registro ativo encontrado no DB. DataFrame vazio criado.")

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
            # Ao adicionar, garantimos que is_active é 1 (ativo)
            data_obj.is_active = 1 
            if data_obj.validate():
                # Chama o método da instância de TrafficAccidentDB
                success = Functions._db_manager.write_data_object(data_obj)
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
    def search_records_by_id(record_id: int, include_inactive: bool = False) -> Optional[pd.DataFrame]:
        """
        Busca um registro pelo ID e retorna como DataFrame.
        A busca retornará apenas registros ativos por padrão.
        """
        # Chama o método da instância de TrafficAccidentDB
        record_map = Functions._db_manager.read_record_by_id(record_id, include_inactive=include_inactive) 
        if record_map:
            df = pd.DataFrame([record_map])
            df = df.rename(columns=FIELD_NAMES_PT)
            return df
        return None

    @staticmethod
    def delete_record_by_id(record_id: int) -> bool:
        """
        Deleta (logicamente) um registro pelo ID.
        """
        # Chama o método da instância de TrafficAccidentDB
        success = Functions._db_manager.delete_record_by_id(record_id)
        if success:
            st.success(f"Registro ID {record_id} deletado (logicamente) com sucesso!")
            Functions.load_data_from_db(force_reload=True) # Invalida cache
        else:
            st.error(f"Não foi possível deletar o registro ID {record_id} (logicamente). Verifique se o ID existe e está ativo, ou consulte os logs.")
        return success
    
    @staticmethod
    def upload_csv_to_db(uploaded_file):
        """Processa um arquivo CSV carregado e o insere no DB."""
        if uploaded_file is not None:
            string_io = io.StringIO(uploaded_file.getvalue().decode("latin-1"))
            # Chama o método da instância de TrafficAccidentDB
            processed, invalid = Functions._db_manager.process_csv_to_db(string_io)
            if processed > 0:
                st.success(f"CSV processado! {processed} registros válidos adicionados. {invalid} registros inválidos/erros.")
                Functions.load_data_from_db(force_reload=True) # Recarrega dados após upload
            elif invalid > 0:
                st.warning(f"Nenhum registro válido do CSV foi adicionado. {invalid} registros inválidos/erros. Verifique o formato do arquivo.")
            else:
                st.info("O arquivo CSV está vazio ou não contém dados válidos.")

    # --- Placeholder Methods for app_v6.py Integration ---
    # These methods would contain the actual logic from app_v6.py
    # and are prefixed with 'v6_' to avoid potential naming conflicts.

    @staticmethod
    def v6_run_step_2_logic():
        """Placeholder for the logic of 'Etapa 2' from app_v6.py."""
        st.write("Executando lógica da Etapa 2...")
        # Adicione aqui o código real da Etapa 2 do app_v6.py
        # Ex: processamento de dados, cálculos, etc.
        st.success("Lógica da Etapa 2 concluída (placeholder).")

    @staticmethod
    def v6_run_step_3_logic():
        """Placeholder for the logic of 'Etapa 3' from app_v6.py."""
        st.write("Executando lógica da Etapa 3...")
        # Adicione aqui o código real da Etapa 3 do app_v6.py
        # Ex: análise de dados, geração de relatórios, etc.
        st.success("Lógica da Etapa 3 concluída (placeholder).")

    @staticmethod
    def v6_run_step_4_logic():
        """Placeholder for the logic of 'Etapa 4' from app_v6.py."""
        st.write("Executando lógica da Etapa 4...")
        # Adicione aqui o código real da Etapa 4 do app_v6.py
        # Ex: visualizações avançadas, machine learning, etc.
        st.success("Lógica da Etapa 4 concluída (placeholder).")

    @staticmethod
    def v6_display_system_admin():
        """Placeholder for the 'Administração do Sistema' content from app_v6.py."""
        st.write("Conteúdo da Administração do Sistema (placeholder).")
        st.info("Esta seção conteria ferramentas para gerenciar o sistema, como backup/restauração do DB, gerenciamento de usuários (se aplicável), etc.")
        # Adicione aqui o código real da Administração do Sistema do app_v6.py

    @staticmethod
    def check_time_input(date_accident, hour_accident):
        """
        Verifica e ajusta a hora do acidente se necessário.
        Esta função é um placeholder e deve ser substituída pela lógica real do app_v6.py.
        """
        # Exemplo de lógica placeholder:
        # Se a data for hoje e a hora for futura, ajusta para a hora atual.
        current_datetime = datetime.now()
        if date_accident == current_datetime.date() and hour_accident > current_datetime.time():
            st.warning("A hora do acidente não pode ser no futuro. Ajustando para a hora atual.")
            return current_datetime.time()
        return hour_accident

    @staticmethod
    def get_string_from_boolean(value: Union[str, bool, int]) -> str:
        """
        Converte valores booleanos/inteiros para strings 'SIM' ou 'NÃO'.
        Esta função é um placeholder e deve ser substituída pela lógica real do app_v6.py.
        """
        if isinstance(value, str):
            if value.upper() == 'Y':
                return 'SIM'
            elif value.upper() == 'N':
                return 'NÃO'
            return value # Retorna o próprio valor se não for 'Y'/'N'
        elif isinstance(value, (bool, int)):
            return 'SIM' if bool(value) else 'NÃO'
        return str(value)


# ===================================================== STREAMLIT UI =====================================================
# Proveniente de app_v6.py
def add_record_v6(add_registry,save_settings):
    if add_registry=="Manual":
        st.subheader("➕ Inserir Novo Registro")
        st.subheader("🚗 Detalhes do Registro de Acidente")
        st.subheader("Detalhes Iniciais")
        try:
            locale.setlocale(locale.LC_ALL, '') # Define a localidade para a do sistema
        except locale.Error:
            # Caso não consiga definir a localidade, use um fallback
            print("Não foi possível definir a localidade do sistema. Usando 'en_US' como fallback.")
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') # Exemplo de fallback para inglês

        # Pega o código do idioma principal (ex: 'pt' para português)
        # Isso é uma simplificação, pois a localidade pode ser mais complexa
        idioma_sistema = locale.getdefaultlocale()[0] # Ex: ('pt_BR', 'UTF-8') -> 'pt_BR'

        # Gera o if ternário para o formato
        formato_data = "DD/MM/YYYY" if idioma_sistema and idioma_sistema.startswith('pt') else "MM/DD/YYYY"

        cols0 = st.columns(2)
        jan_1 = date(2020, 1, 1)
        with cols0[0]:
            date_accident=st.date_input("Dia do Acidente",
                        value="today", # Usar datetime.date.today() é o ideal
                        min_value=jan_1,
                        max_value="today", # Usar datetime.date.today() é o ideal
                        format=formato_data, # Aqui aplicamos o formato determinado pelo if ternário
            )
            hour_accident=st.time_input(
                "Hora do Acidente",
                step=timedelta(minutes=15), # Opcional: define o passo para minutos
                
            )
            #hour_accident=Functions.check_time_input(date_accident,hour_accident) 
        default_timestamp_string=datetime.strptime(date_accident.strftime("%m-%d-%Y")+" "+hour_accident.strftime("%I:%M:%S %p"), "%m-%d-%Y %I:%M:%S %p")
        with cols0[1]:
            hour_accident=Functions.check_time_input(date_accident,hour_accident) 
            st.write(f"Timestamp a ser salvo: {default_timestamp_string}")
            st.write(f"  Hora do Acidente: {hour_accident.hour}")
            st.write(f"  Dia da Semana do Acidente: {date_accident.isoweekday()+1}")
            st.write(f"  Mês do Acidente: {date_accident.month}")

        num_units = st.number_input(
            "Número de Unidades Envolvidas",
            min_value=0, max_value=999, value=0, step=1,
            key="num_units"
        )
        st.subheader("Demais Detalhes")
        cols1 = st.columns(3)
        with cols1[0]:
            crash_type = st.text_input(
                "Tipo de Acidente", key="crash_type" 
            )
            traffic_control_device = st.selectbox(
                "Dispositivo de Controle de Tráfego",
                ["DESCONHECIDO", "SINAL DE TRÁFEGO", "PLACA DE PARE", "PLACA DE RENDIMENTO", "NENHUM", "OUTRO"], 
                index=0,
                key="tcd"
            )
            weather_condition = st.selectbox(
                "Condição Climática",
                ["DESCONHECIDO", "LIMPO", "CHUVA", "NEVE", "NEBLINA", "VENTOS FORTES", "GEADA", "OUTRO"], 
                index=0,
                key="weather"
            )
            lighting_condition = st.selectbox(
                "Condição de Iluminação", 
                ["DESCONHECIDO", "LUZ DO DIA", "ESCURIDÃO - ILUMINADO", "ESCURIDÃO - NÃO ILUMINADO", "CREPÚSCULO/AMANHECER"], 
                index=0,
                key="lighting"
            )
        with cols1[1]:
            first_crash_type = st.text_input("Primeiro Tipo de Acidente (Específico)", key="first_crash_type") 
            trafficway_type = st.text_input("Tipo de Via", key="trafficway_type") 
            alignment = st.text_input("Alinhamento", key="alignment")
            roadway_surface_cond = st.selectbox(
                "Condição da Superfície da Via", 
                ["DESCONHECIDO", "SECO", "MOLHADO", "NEVE/GELO", "AREIA/LAMA/SUJEIRA/ÓLEO"], 
                index=0,
                key="surface_condition"
            )
        with cols1[2]:
            road_defect = st.selectbox(
                "Defeito na Via", 
                ["NENHUM", "BURACOS", "DEFEITO NO ACOSTAMENTO", "DETRITOS NA VIA", "OUTRO"],
                index=0,
                key="road_defect"
            )
            intersection_related_i = st.selectbox(
                "Relacionado à Interseção?", 
                ["NÃO", "SIM"],
                index=0,
                key="intersection_related"
            )
            damage = st.text_input("Descrição do Dano",  key="damage")
            prim_contributory_cause = st.text_input("Causa Contributiva Primária", key="prim_cause")
            most_severe_injury = st.selectbox(
                "Lesão Mais Severa",
                ["NENHUMA", "FATAL", "INCAPACITANTE", "NÃO-INCAPACITANTE", "RELATADA, NÃO EVIDENTE"],
                index=0,
                key="most_severe_injury"
            )

        st.subheader("Ferimentos - Detalhamento")
        inj_cols = st.columns(3)
        with inj_cols[0]:
            injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0,  step=0.1, key="injuries_fatal")
            injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0, step=0.1, key="injuries_incapacitating")
        with inj_cols[1]:
            injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0, key="injuries_non_incapacitating")
            injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0, step=0.1, key="injuries_reported_not_evident")
        with inj_cols[2]:
            injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0, step=0.1, key="injuries_no_indication")
            injuries_total = st.number_input(
                            "Total Injuries",
                            min_value=0.0, step=0.1,
                            key="injuries_total"
                        )
        submitted = st.button("💾 Salvar Registro" if save_settings =="Etapa 1" else "💾 Salvar Registro e Atualizar Índice", use_container_width=True)
    if add_registry=="Arquivo CSV":
        st.write("Arquivo CSV")
# =====================================================================
def main():
    st.set_page_config(layout="wide", page_title="Sistema de Gerenciamento de Acidentes de Trânsito", page_icon="🚨")

    # --- Sidebar ---
    st.sidebar.title("Navegação Principal")
    # Opções da barra lateral principal
    main_option = st.sidebar.selectbox(
        "Selecione uma Opção",
        ["Início", "Etapa 1", "Etapa 2", "Etapa 3", "Etapa 4", "Administração do Sistema", "Sobre"]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Informações do Sistema")
    st.sidebar.write("Versão: 1.0_20250708 Alpha 7c")
    st.sidebar.write("Status do DB: Online ✅") # Simplificado

    # Garante que as chaves RSA e AES existam ao iniciar o aplicativo
    Functions._ensure_rsa_keys()
    Functions._ensure_aes_key()

    # ===================================================== Main Content Area =====================================================

    if main_option == "Início":
        st.title("Bem-vindo ao Sistema de Gerenciamento de Acidentes de Trânsito")
        st.markdown("""
            Este aplicativo Streamlit foi desenvolvido para gerenciar dados de acidentes de trânsito.
            Ele permite adicionar novos registros, visualizar todos os registros existentes, buscar
            registros por ID, deletar registros e fazer upload de arquivos CSV.

            Utiliza um sistema de armazenamento de dados binário com validação de integridade (checksum SHA-256)
            e um cabeçalho otimizado para o controle de IDs. A funcionalidade de exclusão foi adaptada para ser
            **lógica**, ou seja, os registros não são removidos fisicamente do arquivo, mas são marcados como
            inativos e ignorados nas operações de leitura e busca.
        """)
        st.subheader("Funcionalidades Principais:")
        st.markdown("""
        - **Adicionar Novo Registro**: Insira dados de um novo acidente.
        - **Visualizar Registros**: Veja todos os acidentes registrados (apenas ativos) em uma tabela interativa.
        - **Buscar Registros**: Encontre um acidente específico pelo seu ID (apenas registros ativos por padrão).
        - **Deletar Registros**: Marque um registro como "inativo" (exclusão lógica).
        - **Upload CSV**: Carregue dados de acidentes em massa a partir de um arquivo CSV.
        - **Criptografia e Hashing**: Gerenciamento interno de chaves AES e RSA para futuras implementações de segurança de dados.
        """)

    elif main_option == "Etapa 1":
        st.title("Gerenciamento de Dados de Acidentes (Etapa 1)")
        st.markdown("---")

        # Sub-menu para as funcionalidades de gerenciamento de dados de acidentes
        etapa1_sub_page = st.selectbox(
            "Selecione uma Operação",
            ["Adicionar Novo Registro", "Visualizar Registros", "Buscar Registros", "Deletar Registros", "Upload CSV"]
        )

        if etapa1_sub_page == "Adicionar Novo Registro":
            st.subheader("Adicionar Novo Registro de Acidente")

            with st.form("form_add_entry", clear_on_submit=True):
                st.markdown("##### Detalhes do Acidente")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    crash_date_str = st.text_input(FIELD_NAMES_PT['crash_date'], help="Formato: MM/DD/AAAA HH:MM:SS AM/PM", value=datetime.now().strftime('%m/%d/%Y %I:%M:%S %p'))
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

        elif etapa1_sub_page == "Visualizar Registros":
            st.subheader("Visualizar Todos os Registros de Acidentes (Apenas Ativos)")

            df = Functions.load_data_from_db()

            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button(
                    label="Baixar Dados como CSV",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name="registros_acidentes_ativos.csv",
                    mime="text/csv",
                )
            else:
                st.info("Nenhum registro ativo encontrado no banco de dados. Adicione novos registros ou faça upload de um CSV.")

        elif etapa1_sub_page == "Buscar Registros":
            st.subheader("Buscar Registros de Acidentes por ID")
            st.info("Por padrão, a busca retorna apenas registros ativos.")

            search_id = st.number_input("Digite o ID do Registro:", min_value=1, value=1, step=1)
            
            include_inactive_search = st.checkbox("Incluir registros inativos (logicamente deletados) na busca?")

            if st.button("Buscar"):
                record_df = Functions.search_records_by_id(search_id, include_inactive=include_inactive_search)
                
                if record_df is not None and not record_df.empty:
                    st.subheader(f"Registro Encontrado (ID: {search_id})")
                    st.dataframe(record_df, use_container_width=True)
                else:
                    st.warning(f"Nenhum registro encontrado com o ID: {search_id} (ou está inativo e 'Incluir inativos' não foi selecionado).")

        elif etapa1_sub_page == "Deletar Registros":
            st.subheader("Deletar (Logicamente) Registro de Acidente por ID")
            st.warning("Ao deletar um registro, ele será apenas marcado como 'inativo' e não será exibido nas listagens padrão, mas permanecerá no arquivo do banco de dados.")

            delete_id = st.number_input("Digite o ID do Registro a ser Deletado (Logicamente):", min_value=1, value=1, step=1)
            if st.button("Deletar Registro (Lógicamente)"):
                if st.checkbox(f"Confirmar exclusão lógica do registro ID {delete_id}?", key=f"confirm_delete_{delete_id}"):
                    Functions.delete_record_by_id(delete_id)
                else:
                    st.info("Marque a caixa de confirmação para deletar o registro logicamente.")

        elif etapa1_sub_page == "Upload CSV":
            st.subheader("Upload de Dados de Acidentes via CSV")
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

    # --- Conteúdo da Etapa 2 ---
    elif main_option == "Etapa 2":
        st.header("🗂️ Etapa 2: Gerenciamento de Arquivo de Dados e Índice")
        st.write("Nesta etapa, você pode gerenciar o arquivo de dados juntamente com seus índices para otimização de busca.")
        st.markdown("---") # Separador visual

        st.sidebar.subheader("Opções de Dados e Índice")
        sub_option_etapa2 = st.sidebar.selectbox(
            "Selecione uma Ação",
            ("Carregar dados do CSV", "Carregar arquivo de dados e índice",
             "Inserir um registro", "Editar um registro",
             "Apagar um registro", "Exportar arquivo de dados e índice como CSV"),
            help="Escolha a operação que envolve tanto o arquivo de dados quanto o arquivo de índice."
        )

        st.info(f"Você está em: **Etapa 2** - **{sub_option_etapa2}**")

        if sub_option_etapa2 == "Carregar dados do CSV":
            st.subheader("📤 Carregar Dados de um Arquivo CSV (com Índice)")
            st.write("Importe dados de um CSV e, opcionalmente, construa ou atualize um índice associado.")
            uploaded_csv_file_e2 = st.file_uploader(
                "Arraste e solte seu arquivo CSV aqui ou clique para procurar.",
                type=["csv"], key="csv_e2",
                help="O arquivo CSV será usado para popular o banco de dados e o índice."
            )
            if uploaded_csv_file_e2 is not None:
                st.success(f"Arquivo '{uploaded_csv_file_e2.name}' carregado! (Aguardando lógica de processamento com índice)")
        elif sub_option_etapa2 == "Carregar arquivo de dados e índice":
            st.subheader("📥 Carregar Arquivo de Dados (.db) e Índice (.idx)")
            st.write("Selecione os arquivos de dados e índice para carregar o sistema completo.")
            uploaded_db_file_e2 = st.file_uploader(
                "Selecione o arquivo de dados (.db)",
                type=["db"], key="db_e2",
                help="Arquivo binário de registros."
            )
            uploaded_idx_file_e2 = st.file_uploader(
                "Selecione o arquivo de índice (.idx)",
                type=["idx"], key="idx_e2",
                help="Arquivo com a estrutura de índice para busca rápida."
            )
            if uploaded_db_file_e2 is not None and uploaded_idx_file_e2 is not None:
                st.success(f"Arquivos '{uploaded_db_file_e2.name}' e '{uploaded_idx_file_e2.name}' carregados! (Aguardando lógica de carregamento)")
            elif uploaded_db_file_e2 is not None or uploaded_idx_file_e2 is not None:
                st.warning("Por favor, carregue AMBOS os arquivos (.db e .idx) para esta operação.")
        elif sub_option_etapa2 == "Inserir um registro":
             # Chamada para a função de adicionar registro do app_v6.py
             add_record_v6("Manual",main_option) # Reutilizando a função add_record do app_v6.py
        elif sub_option_etapa2 == "Editar um registro":
            st.subheader("✏️ Editar Registro Existente (com Atualização de Índice)")
            st.write("Modifique um registro e tenha certeza que o índice refletirá as mudanças.")
            record_id_edit_e2 = st.text_input("ID do Registro a Editar", key="e2_edit_id")
            if record_id_edit_e2:
                st.info(f"Buscando registro com ID: **{record_id_edit_e2}**... (Aguardando lógica de busca e edição)")
                with st.form("edit_record_form_e2"):
                    st.write("Atualize os campos:")
                    col1, col2 = st.columns(2)
                    with col1:
                        data_acidente_edit = st.date_input("Data do Acidente", value=date.today(), key="e2_edit_data")
                        gravidade_edit = st.selectbox("Gravidade", ["Leve", "Moderada", "Grave", "Fatal"], index=0, key="e2_edit_gravidade")
                    with col2:
                        localizacao_edit = st.text_input("Localização", value="Exemplo de Localização", key="e2_edit_local")
                        veiculos_envolvidos_edit = st.number_input("Veículos Envolvidos", min_value=1, value=1, key="e2_edit_veiculos")
                    observacoes_edit = st.text_area("Observações", value="Exemplo de observações para edição.", key="e2_edit_obs")
                    edit_submitted_e2 = st.form_submit_button("Atualizar Registro e Índice")
                    if edit_submitted_e2:
                        st.success(f"Registro com ID {record_id_edit_e2} atualizado e índice refeito! (Aguardando lógica de edição)")
        elif sub_option_etapa2 == "Apagar um registro":
            st.subheader("🗑️ Apagar Registro (com Atualização de Índice)")
            st.write("Remova um registro e veja o índice ser ajustado para refletir a exclusão.")
            record_id_delete_e2 = st.text_input("ID do Registro a Apagar", key="e2_delete_id")
            if st.button("Apagar Registro e Atualizar Índice", key="e2_delete_btn"):
                if record_id_delete_e2:
                    st.warning(f"Tentando apagar registro com ID: **{record_id_delete_e2}** e seu índice... (Aguardando lógica de exclusão)")
                    st.success(f"Registro com ID {record_id_delete_e2} e sua entrada no índice apagados! (Aguardando confirmação)")
                else:
                    st.error("Por favor, insira um ID de registro para apagar.")
        elif sub_option_etapa2 == "Exportar arquivo de dados e índice como CSV":
            st.subheader("⬇️ Exportar Dados e Índice para CSV")
            st.write("Esta opção permite exportar os dados brutos e/ou informações do índice para um formato CSV.")
            export_type = st.radio(
                "O que você deseja exportar?",
                ("Apenas Dados", "Apenas Índice", "Ambos (Dados e Índice Relacionados)"),
                help="Escolha o tipo de informação a ser exportada."
            )
            if st.button("Gerar CSV(s) para Download", key="e2_export_btn"):
                with st.spinner(f"Gerando {export_type.lower()} para download..."):
                    time.sleep(2) # Simula processamento
                    # Lógica para gerar CSV de dados e/ou índice
                    if "Dados" in export_type:
                        sample_data_e2 = "coluna1,coluna2,coluna3\nvalorX,valorY,valorZ"
                        st.download_button(
                            label="Baixar Dados CSV",
                            data=sample_data_e2,
                            file_name="dados_acidentes_e2.csv",
                            mime="text/csv",
                            key="download_data_e2"
                        )
                    if "Índice" in export_type:
                        sample_index_e2 = "id_registro,offset,tamanho\n1,0,100\n2,101,120"
                        st.download_button(
                            label="Baixar Índice CSV",
                            data=sample_index_e2,
                            file_name="indice_acidentes_e2.csv",
                            mime="text/csv",
                            key="download_index_e2"
                        )
                    st.success(f"{export_type} pronto(s) para download!")

    # --- Conteúdo da Etapa 3 ---
    elif main_option == "Etapa 3":
        st.header("🔐 Etapa 3: Compactação e Criptografia")
        st.write("Otimize o armazenamento e a segurança dos seus dados aplicando técnicas de compactação e criptografia.")
        st.markdown("---") # Separador visual

        st.sidebar.subheader("Opções de Segurança e Otimização")
        sub_option_etapa3 = st.sidebar.selectbox(
            "Selecione uma Ferramenta",
            ("Compactação", "Criptografia"),
            help="Escolha entre compactar dados para economizar espaço ou criptografá-los para segurança."
        )

        st.info(f"Você está em: **Etapa 3** - **{sub_option_etapa3}**")

        if sub_option_etapa3 == "Compactação":
            st.subheader("📦 Compactação de Arquivos")
            st.write("Reduza o tamanho dos seus arquivos usando diferentes algoritmos de compactação.")
            compact_method = st.selectbox(
                "Método de Compactação",
                ("Huffman", "LZW", "LZ78"),
                help="Selecione o algoritmo de compactação a ser utilizado."
            )
            compact_mode_selection = st.radio(
                "Modo de Operação",
                ("Padrão", "Escolha do Usuário"),
                help="No modo 'Padrão', você compacta arquivos internos do sistema. No modo 'Escolha do Usuário', você seleciona um arquivo local."
            )
            compact_action = st.selectbox(
                "Ação",
                ("Compactar", "Descompactar"),
                help="Escolha entre compactar um arquivo para reduzir seu tamanho ou descompactar para restaurá-lo."
            )

            if compact_mode_selection == "Padrão" and compact_action == "Compactar":
                st.write("Selecione qual componente do sistema você deseja compactar:")
                st.selectbox(
                    "Tipo de Arquivo para Compactar",
                    ("Arquivo de Dados", "Índice", "Árvore B"),
                    help="Escolha o arquivo interno do sistema para compactar."
                )
                if st.button(f"{compact_action} Arquivo (Padrão)"):
                    with st.spinner(f"{compact_action} arquivo padrão com {compact_method}..."):
                        time.sleep(2) # Simula
                        st.success(f"Arquivo padrão {compact_action.lower()} com sucesso usando {compact_method}! (Aguardando lógica)")
            elif compact_mode_selection == "Escolha do Usuário":
                st.write("Carregue seu próprio arquivo para compactar ou descompactar.")
                uploaded_file_compact = st.file_uploader(
                    "Carregar arquivo para processamento",
                    type=["db", "idx", "btr", "huff", "lzw", "lz78", "csv"],
                    help="Arraste e solte arquivos nos formatos .db, .idx, .btr, .huff, .lzw, .lz78 ou .csv."
                )
                if uploaded_file_compact is not None:
                    st.info(f"Arquivo '{uploaded_file_compact.name}' carregado.")
                    if st.button(f"{compact_action} Arquivo", key="compact_user_file_btn"):
                        with st.spinner(f"{compact_action} '{uploaded_file_compact.name}' com {compact_method}..."):
                            time.sleep(3) # Simula
                            st.success(f"Arquivo '{uploaded_file_compact.name}' {compact_action.lower()} com sucesso usando {compact_method}! (Aguardando lógica)")
                            st.download_button(
                                label=f"Baixar Arquivo {compact_action}",
                                data="conteúdo_do_arquivo_processado", # Substituir pelo conteúdo real
                                file_name=f"{Path(uploaded_file_compact.name).stem}_processed.bin", # Nome de arquivo de exemplo
                                mime="application/octet-stream",
                                help="Baixe o arquivo após a operação de compactação/descompactação."
                            )

        elif sub_option_etapa3 == "Criptografia":
            st.subheader("🔒 Criptografia de Arquivos")
            st.write("Proteja seus dados sensíveis aplicando criptografia avançada.")
            crypto_method = st.selectbox(
                "Método de Criptografia",
                ("Gerar Chaves RSA/Blowfish", "Blowfish", "AES-RSA"),
                help="Selecione o algoritmo de criptografia. 'Gerar Chaves' cria novos pares de chaves."
            )
            crypto_mode_selection = st.radio(
                "Modo de Operação",
                ("Padrão", "Escolha do Usuário"),
                help="No modo 'Padrão', você criptografa arquivos internos do sistema. No modo 'Escolha do Usuário', você seleciona um arquivo local e chaves."
            )
            crypto_action = st.selectbox(
                "Ação",
                ("Criptografar", "Descriptografar"),
                help="Escolha entre criptografar um arquivo para protegê-lo ou descriptografá-lo para acessá-lo."
            )

            if crypto_method == "Gerar Chaves RSA/Blowfish":
                st.info("Esta opção irá gerar um novo par de chaves RSA (pública/privada) e uma chave Blowfish.")
                if st.button("Gerar Novas Chaves", help="Isso pode levar alguns instantes."):
                    with st.spinner("Gerando chaves..."):
                        time.sleep(3) # Simula
                        st.success("Chaves geradas com sucesso! (Aguardando lógica de geração)")
                        # No futuro, adicione botões de download para as chaves geradas
                        st.download_button(
                            label="Baixar Chave Pública (RSA)",
                            data="chave_publica_rsa_exemplo",
                            file_name="public_key.pem",
                            mime="application/x-pem-file"
                        )
                        st.download_button(
                            label="Baixar Chave Privada (RSA)",
                            data="chave_privada_rsa_exemplo",
                            file_name="private_key.pem",
                            mime="application/x-pem-file"
                        )
                        st.download_button(
                            label="Baixar Chave Blowfish",
                            data="chave_blowfish_exemplo",
                            file_name="blowfish_key.bin",
                            mime="application/octet-stream"
                        )
            else: # Blowfish ou AES-RSA
                if crypto_mode_selection == "Padrão" and crypto_action == "Criptografar":
                    st.write("Selecione qual componente do sistema você deseja criptografar:")
                    st.selectbox(
                        "Tipo de Arquivo para Criptografar",
                        ("Arquivo de Dados", "Índice", "Árvore B"),
                        help="Escolha o arquivo interno do sistema para criptografar."
                    )
                    if st.button("Autogerar Chaves e Criptografar (Padrão)", help="Utiliza chaves padrão do sistema para criptografia."):
                        with st.spinner(f"Criptografando arquivo padrão com {crypto_method} e chaves autogeradas..."):
                            time.sleep(3) # Simula
                            st.success(f"Arquivo padrão criptografado com sucesso usando {crypto_method}! (Aguardando lógica)")
                elif crypto_mode_selection == "Escolha do Usuário":
                    st.write("Carregue as chaves e o arquivo para criptografar/descriptografar.")
                    st.subheader("🔑 Chave(s) de Criptografia")
                    uploaded_key_file = st.file_uploader(
                        "Carregar arquivo de chave (.pem)",
                        type=["pem", "bin"], # Blowfish key might be .bin
                        help="Para RSA, carregue a chave pública (.pem) para criptografar ou a privada (.pem) para descriptografar. Para Blowfish, a chave binária."
                    )
                    st.subheader("📄 Arquivo a ser Processado")
                    uploaded_file_crypto = st.file_uploader(
                        "Carregar arquivo para processamento",
                        type=["db", "idx", "btr", "enc", "enc_aes", "csv"],
                        help="Selecione o arquivo de dados (.db), índice (.idx), árvore B (.btr), ou arquivos já criptografados (.enc, .enc_aes, .csv)."
                    )
                    if uploaded_key_file is not None and uploaded_file_crypto is not None:
                        st.info(f"Chave '{uploaded_key_file.name}' e arquivo '{uploaded_file_crypto.name}' carregados.")
                        if st.button(f"{crypto_action} Arquivo", key="crypto_user_file_btn"):
                            with st.spinner(f"{crypto_action} '{uploaded_file_crypto.name}' com {crypto_method}..."):
                                time.sleep(3) # Simula
                                st.success(f"Arquivo '{uploaded_file_crypto.name}' {crypto_action.lower()} com sucesso usando {crypto_method}! (Aguardando lógica)")
                                st.download_button(
                                    label=f"Baixar Arquivo {crypto_action}",
                                    data="conteúdo_do_arquivo_processado", # Substituir pelo conteúdo real
                                    file_name=f"{Path(uploaded_file_crypto.name).stem}_processed.bin", # Nome de arquivo de exemplo
                                    mime="application/octet-stream",
                                    help="Baixe o arquivo após a operação de criptografia/descriptografia."
                                )
                    elif uploaded_key_file is not None or uploaded_file_crypto is not None:
                        st.warning("Por favor, carregue a chave e o arquivo a ser processado para continuar.")

    # --- Conteúdo da Etapa 4 ---
    elif main_option == "Etapa 4":
        st.header("🔍 Etapa 4: Casamento Padrão e Busca Avançada")
        st.write("Utilize algoritmos eficientes para buscar padrões em seus dados.")
        st.markdown("---") # Separador visual

        st.sidebar.subheader("Opções de Casamento Padrão")
        sub_option_etapa4 = st.sidebar.selectbox(
            "Selecione uma Ação de Busca",
            ("Gerar sistema de Busca por Aho-Corasik", "Buscar registros por Casamento Padrão"),
            help="Escolha entre construir uma estrutura para busca múltipla de padrões ou realizar uma busca direta."
        )

        st.info(f"Você está em: **Etapa 4** - **{sub_option_etapa4}**")

        if sub_option_etapa4 == "Gerar sistema de Busca por Aho-Corasik":
            st.subheader("⚙️ Gerar Sistema de Busca por Aho-Corasik")
            st.write("Esta função constrói o autômato de Aho-Corasik a partir de um conjunto de padrões, otimizando a busca simultânea de múltiplos termos.")
            st.caption("Escolha a etapa de construção do sistema:")
            st.selectbox(
                "Etapas de Geração",
                ("Etapa 1: Carregar Padrões", "Etapa 2: Construir Autômato"),
                help="Etapa 1: Defina os padrões de busca. Etapa 2: Construa a estrutura de Aho-Corasik."
            )
            if st.button("Gerar sistema de Busca por Aho-Corasik", help="Inicia a construção da estrutura de busca."):
                with st.spinner("Gerando sistema Aho-Corasik..."):
                    time.sleep(3) # Simula
                    st.success("Sistema de Busca por Aho-Corasik gerado com sucesso! (Aguardando lógica)")
                    st.download_button(
                        label="Baixar Sistema Aho-Corasik",
                        data="dados_do_sistema_aho_corasik_serializados", # Substituir
                        file_name="aho_corasik_system.bin",
                        mime="application/octet-stream",
                        help="Baixe o arquivo binário do sistema Aho-Corasik gerado."
                    )
        elif sub_option_etapa4 == "Buscar registros por Casamento Padrão":
            st.subheader("🎯 Buscar Registros por Casamento Padrão")
            st.write("Pesquise registros no banco de dados utilizando algoritmos de casamento de padrão.")
            st.caption("Escolha a etapa da busca:")
            st.selectbox(
                "Etapas da Busca",
                ("Etapa 1: Carregar Dados de Busca", "Etapa 2: Executar Busca"),
                help="Etapa 1: Carregue os dados onde a busca será realizada. Etapa 2: Execute a busca com o padrão definido."
            )
            pattern_to_locate = st.text_input(
                "Digite o padrão a ser localizado",
                help="Insira o texto ou padrão que você deseja encontrar nos registros.",
                placeholder="Ex: 'acidente grave', 'colisão lateral'"
            )
            if st.button("Buscar registros por Casamento Padrão", help="Inicia a busca pelo padrão especificado."):
                if pattern_to_locate:
                    with st.spinner(f"Buscando por '{pattern_to_locate}'..."):
                        time.sleep(4) # Simula
                        st.success(f"Busca por '{pattern_to_locate}' concluída! (Aguardando lógica)")
                        st.subheader("Resultados da Busca:")
                        # Exemplo de exibição de resultados (você preencherá com dados reais)
                        st.dataframe(pd.DataFrame({
                            "ID do Registro": [1, 5, 12],
                            "Localização": ["Rua A, Bairro C", "Rodovia X", "Avenida Y"],
                            "Trecho Encontrado": ["Ocorreu um **acidente grave**.", "Colisão frontal em **acidente grave**.", "**acidente grave** próximo ao semáforo"]
                        }))
                        st.info("Nenhum resultado encontrado para o padrão especificado." if not pattern_to_locate else "Resultados exibidos acima.")
                else:
                    st.error("Por favor, digite um padrão para realizar a busca.")

     # --- Conteúdo da Administração do Sistema ---
    elif main_option == "Administração do Sistema":
        st.header("⚙️ Administração do Sistema")
        st.write("Ferramentas para manutenção e gerenciamento do banco de dados e arquivos do sistema.")
        st.markdown("---")

        st.subheader("📊 Backup e Exportação")
        col_backup, col_export = st.columns(2)
        with col_backup:
            if st.button("Realizar Backup Agora", key="backup_db_button", help="Cria uma cópia de segurança do banco de dados principal."):
                with st.spinner("Realizando backup..."):
                    time.sleep(2) # Simula
                    st.success("Backup do banco de dados realizado com sucesso!")
                    # Lógica real para fazer backup
        with col_export:
            if st.button("Exportar Dados para CSV", key="export_csv_button", help="Exporta todo o conteúdo do banco de dados para um arquivo CSV."):
                with st.spinner("Exportando para CSV..."):
                    time.sleep(2) # Simula
                    sample_data_admin = "col1,col2\nval1,val2\nval3,val4"
                    st.download_button(
                        label="Baixar Dados Exportados",
                        data=sample_data_admin,
                        file_name="dados_completos_backup.csv",
                        mime="text/csv",
                        key="download_admin_csv"
                    )
                    st.success("Dados exportados para CSV com sucesso!")

        st.markdown("---")

        admin_opt=st.selectbox(
            "Selecione o Escopo da Operação",
            ("Etapa 1: Apenas Banco de Dados", "Etapa 2: Banco de Dados e Índices"),
            help="Escolha o nível de arquivos a serem importados ou gerenciados."
        )

        if admin_opt=="Etapa 1: Apenas Banco de Dados":
            st.subheader("⬆️ Importar Banco de Dados (.db)")
            st.write("Faça upload de um arquivo `.db` para restaurar ou substituir o banco de dados principal.")
            uploaded_file_import_db = st.file_uploader(
                "Selecione um arquivo .db para importar",
                type="db", key="import_db_uploader",
                help="Este arquivo substituirá o banco de dados principal atual. Faça um backup antes!"
            )
            if uploaded_file_import_db is not None:
                st.success(f"Arquivo '{uploaded_file_import_db.name}' pronto para importação. (Aguardando ação)")
                if st.button("Confirmar Importação de DB", key="confirm_import_db_btn"):
                    with st.spinner("Importando banco de dados..."):
                        time.sleep(3) # Simula
                        st.success("Banco de dados importado com sucesso!")

            st.markdown("---")
            st.subheader("⚠️ Excluir Banco de Dados Principal")
            st.warning("Esta ação é irreversível e excluirá *permanentemente* o arquivo do banco de dados principal (`traffic_accidents.db`). **Faça um backup antes!**")
            if st.button("Excluir Banco de Dados Principal", key="delete_db_button", help="Cuidado! Esta ação não pode ser desfeita."):
                if st.checkbox("Tenho certeza que quero excluir o banco de dados principal.", key="confirm_delete_db"):
                    with st.spinner("Excluindo banco de dados..."):
                        time.sleep(2) # Simula
                        st.error("Banco de dados principal excluído! (Aguardando lógica de exclusão)")
                        st.info("Recomenda-se reiniciar a aplicação para garantir a integridade.")
                else:
                    st.info("Confirme a exclusão marcando a caixa de seleção.")

        if admin_opt=="Etapa 2: Banco de Dados e Índices":
            st.subheader("⬆️ Importar Arquivos de Índice e Banco de Dados")
            st.write("Faça upload de arquivos `.btr` (Árvore B), `.inv` (Índice Invertido) e `.idx` (Índice Geral) para restaurar os índices do sistema, juntamente com o `.db`.")

            col_idx1, col_idx2, col_idx3 = st.columns(3)
            with col_idx1:
                uploaded_btr_file = st.file_uploader("Selecione Árvore B (.btr)", type=["btr"], key="import_btr_uploader", help="Arquivo da estrutura de Árvore B.")
                if uploaded_btr_file: st.success(f"'{uploaded_btr_file.name}' carregado.")
            with col_idx2:
                uploaded_inv_file = st.file_uploader("Selecione Índice Invertido (.inv)", type=["inv"], key="import_inv_uploader", help="Arquivo do Índice Invertido.")
                if uploaded_inv_file: st.success(f"'{uploaded_inv_file.name}' carregado.")
            with col_idx3:
                uploaded_idx_file = st.file_uploader("Selecione Índice Geral (.idx)", type=["idx"], key="import_idx_uploader", help="Arquivo do Índice Geral.")
                if uploaded_idx_file: st.success(f"'{uploaded_idx_file.name}' carregado.")

            st.subheader("⬆️ Importar Banco de Dados (.db) para Conjunto")
            uploaded_db_file_e2_admin = st.file_uploader(
                "Selecione o arquivo .db para este conjunto",
                type="db", key="import_db2_uploader",
                help="Este é o arquivo de dados associado aos índices que você está importando."
            )
            if uploaded_db_file_e2_admin: st.success(f"'{uploaded_db_file_e2_admin.name}' carregado.")

            if st.button("Confirmar Importação de Banco de Dados e Índices", key="confirm_import_full_btn"):
                if uploaded_btr_file or uploaded_inv_file or uploaded_idx_file or uploaded_db_file_e2_admin:
                    with st.spinner("Importando arquivos..."):
                        time.sleep(3) # Simula
                        st.success("Banco de Dados e Índices importados com sucesso! (Aguardando lógica de restauração)")
                else:
                    st.error("Por favor, carregue pelo menos um arquivo para importar.")

            st.markdown("---")
            st.subheader("⚠️ Excluir Banco de Dados Principal e Índices")
            st.warning("Esta ação é irreversível e excluirá *permanentemente* o banco de dados principal (`traffic_accidents.db`), Árvore B (`.btr`), Índice Invertido (`.inv`) e Índice Geral (`.idx`). **Faça um backup antes!**")
            if st.button("Excluir TUDO (DB e Índices)", key="delete_2db_button", help="Esta é uma exclusão completa. Não há volta!"):
                if st.checkbox("Tenho certeza que quero excluir o banco de dados principal e todos os índices.", key="confirm_delete_full"):
                    with st.spinner("Excluindo banco de dados e índices..."):
                        time.sleep(3) # Simula
                        st.error("Banco de dados principal e todos os índices excluídos! (Aguardando lógica de exclusão)")
                        st.info("Recomenda-se reiniciar a aplicação para garantir a integridade.")
                else:
                    st.info("Confirme a exclusão marcando a caixa de seleção.")
        st.markdown("---")

        st.subheader("📜 Visualização e Exclusão de Arquivos de Log")
        st.write("Acesse os logs do sistema para depuração ou remova-os para liberar espaço.")
        col_log_view, col_log_delete = st.columns(2)
        with col_log_view:
            if st.button("Visualizar Conteúdo do Log", key="view_log_button", help="Exibe os registros de atividades do sistema."):
                st.info("Exibindo conteúdo do log (Simulação)...")
                st.code("2024-07-07 10:30:01 - INFO - Aplicação iniciada.\n2024-07-07 10:35:15 - WARNING - Tentativa de acesso negada.")
                # Lógica real para ler e exibir o log
        with col_log_delete:
            if st.button("Excluir Arquivo de Log", key="delete_log_button", help="Remove o arquivo de log do sistema."):
                if st.checkbox("Confirmar exclusão do arquivo de log", key="confirm_delete_log"):
                    with st.spinner("Excluindo arquivo de log..."):
                        time.sleep(1) # Simula
                        st.success("Arquivo de log excluído com sucesso! (Aguardando lógica)")
                else:
                    st.info("Marque a caixa para confirmar a exclusão do log.")

    # --- Conteúdo da Seção "Sobre" ---
    elif main_option == "Sobre":
        st.header("ℹ️ Sobre este Sistema")
        st.markdown("---")

        st.subheader("Autor")
        st.write("Desenvolvido por: [Gabriel da Silva Cassino](https://github.com/kasshinokun/Q1_Q2_2025_Public/tree/main/Aulas_AED3/Python_Adapt/Deploy)")

        st.subheader("Descrição do Projeto")
        st.write("""
        Este é um sistema de gerenciamento de banco de dados de acidentes de trânsito
        com funcionalidades avançadas de compressão (LZW e Huffman), criptografia (híbrida AES e RSA)
        e indexação eficiente usando uma estrutura de dados B-Tree e Índice Invertido.
        """)
        st.write("""
        Desenvolvido como trabalho prático para a disciplina de **Algoritmos e Estruturas de Dados III**
        da graduação em Engenharia da Computação pela **PUC Minas Coração Eucarístico**.
        """)
        st.write("O programa será reconstruído gradativamente. No repositório da aplicação (link abaixo), existem as prévias iniciais.")
        st.markdown("Link do Repositório: [Deploy da Aplicação](https://github.com/kasshinokun/Q1_Q2_2025_Public/tree/main/Aulas_AED3/Python_Adapt/Deploy)")

        st.subheader("Tecnologias Utilizadas")
        st.markdown("""
        * **Python**: Linguagem de programação principal.
        * **Streamlit**: Para a interface de usuário web interativa e ágil.
        * **`cryptography`**: Biblioteca robusta para operações criptográficas (AES, RSA, Blowfish).
        * **`filelock`**: Para gerenciamento de concorrência e garantia da integridade do arquivo em operações multi-threaded/multi-processo.
        * **`pathlib`**: Módulo para manipulação de caminhos de arquivos e diretórios de forma orientada a objetos.
        * **`pandas`**: Essencial para manipulação e exibição de dados tabulares (DataFrames).
        * **`matplotlib`**: Para geração de gráficos de comparação e visualização de dados (se implementado).
        * **`collections`**: Módulos como `Counter` e `defaultdict` para estruturas de dados eficientes.
        * **`typing`**: Suporte para tipagem estática, melhorando a clareza e manutenibilidade do código.
        * **`concurrent.futures`**: Para gerenciamento de threads e processos, permitindo operações assíncronas.
        * **`threading`**: Para controle de threads de execução.
        """)
        st.write("Versão: 1.0_20250708 Alpha 7c")
        st.markdown("---")
        st.info("Agradecemos seu interesse em nossa aplicação!")


if __name__ == "__main__":
    main()
