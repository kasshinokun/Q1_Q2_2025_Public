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

# --- Configuração de Pastas ---
BASE_DIR = Path(__file__).parent # Diretório onde o app_v7d.py está
DATA_ROOT_DIR = BASE_DIR / "app_data" # Nova pasta raiz para todos os dados
DB_FILE_PATH = DATA_ROOT_DIR / "traffic_accidents.db" # Arquivo principal do DB
ENCRYPT_FOLDER = DATA_ROOT_DIR / "Encrypt"
COMPRESSED_FOLDER = DATA_ROOT_DIR / "Compress"
TEMP_FOLDER = DATA_ROOT_DIR / "Temp"

# Garante que as pastas existam
DATA_ROOT_DIR.mkdir(parents=True, exist_ok=True)
ENCRYPT_FOLDER.mkdir(parents=True, exist_ok=True)
COMPRESSED_FOLDER.mkdir(parents=True, exist_ok=True)
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

# Configure logging
LOG_FILE = DATA_ROOT_DIR / 'traffic_accidents.log' # Log na nova pasta de dados
logging.basicConfig(
    level=logging.INFO, # Pode ser alterado para logging.DEBUG para mais detalhes
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE), # Log para arquivo
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

# Opções de dropdown para alguns campos (Proveniente de app_v6.py para o exemplo)
TRAFFIC_CONTROL_DEVICE_OPTIONS = [
    'SINAL DE TRÂNSITO',
    'SEM CONTROLES',
    'SINAL DE PARE/LUMINOSO',
    'DESCONHECIDO',
    'OUTRO',
    'PLACA DE PASSAGEM DE PEDESTRES',
    'OUTRA PLACA DE ALERTA',
    'DIREÇÃO DE PREFERÊNCIA',
    'SINAL DE CONTROLE PISCANTE',
    'MARCAÇÃO DE USO DE FAIXA',
    'OUTRA PLACA REGISTRADA',
    'DELINEADORES',
    'ZONA ESCOLAR',
    'POLÍCIA/SINALIZADOR',
    'PROIBIDO ULTRAPASSAR',
    'PLACA DE PASSAGEM DE TREM',
    'PORTÃO DE CRUZAMENTO FERROVIÁRIO',
    'PLACA DE TRAVESSIA DE BICICLETAS',
    'OUTRO CRUZAMENTO FERROVIÁRIO'
]
WEATHER_CONDITION_OPTIONS = ['CLARO',
    'CHUVA',
    'NEVE',
    'NUBLADO/CLARO',
    'DESCONHECIDO',
    'NEBLINA/FUMAÇA/NEBLINA',
    'VENTO E NEVE',
    'CHUVA/GAROA CONGELANTE',
    'OUTRO',
    'GRANHO/GRANIZO',
    'VENTO CRUZADO FORTE',
    'VENTO DE AREIA, SOLO, SUJEIRA'
]
LIGHTING_CONDITION_OPTIONS = [ 
    'LUZ DO DIA',
    'ESCURO, ESTRADA ILUMINADA',
    'CREPÚSCULO',
    'ESCURO',
    'DESCONHECIDO',
    'AMANHECER'
]
FIRST_CRASH_TYPE_OPTIONS = [
    ' GIRO ',
    'TRASEIRA PARA TRÁS',
    'ÂNGULO',
    'OBJETO FIXO',
    'TRASEIRA PARA FRENTE',
    'DESLIZAMENTO LATERAL NA MESMA DIREÇÃO',
    'DESLIZAMENTO LATERAL NA DIREÇÃO OPOSTA',
    'CICLISTA',
    'PEDESTRE',
    'DE FRENTE',
    'VEÍCULO MOTORIZADO ESTACIONADO',
    'NÃO COLISÃO COM OUTRO',
    'VIRADO',
    'OUTRO OBJETO',
    'TRASEIRA PARA LADO',
    'ANIMAL',
    'TREM',
    'TRASEIRA PARA TRASEIRA '
]
TRAFFICWAY_TYPE_OPTIONS=[
    'NÃO DIVIDIDO',
    'QUADRUPLICADA ',
    'INTERSEÇÃO EM T',
    'DIVIDIDO - COM MEDIANA (NÃO ELEVADO)  ',
    'OUTRO',
    'INTERSEÇÃO DESCONHECIDA TSPE',
    'MÃO ÚNICA ',
    'RAMPA',
    'ROTA DE TRÁFEGO',
    'CINCO PONTOS OU MAIS ',
    'DIVIDIDO - COM BARREIRA MEDIANA',
    'DESCONHECIDO',
    'BECO',
    'FAIXA DE CONVERSÃO CENTRAL',
    'INTERSEÇÃO EM L',
    'ENTRADA DE CARROS',
    'INTERSEÇÃO EM S',
    'ESTACIONAMENTO',
    'ROTATÓRIA',
    'NÃO INFORMADO'
]
ALIGNMENT_OPTIONS=[
    'EM LINHA RETA E NIVELADA',
    'CURVA E NIVELADA',
    'EM LINHA RETA EM TOPO DE COLINA',
    'EM LINHA RETA EM DECLIVE',
    'CURVA EM DECLIVE',
    'CURVA EM TOPO DE COLINA'
]
ROADWAY_SURFACE_COND_OPTIONS=[
    'DESCONHECIDO',
    'SECO',
    'MOLHADO',
    'NEVE OU GELO',
    'GELO',
    'OUTRO',
    'AREIA, LAMA, SUJEIRA'
]
ROAD_DEFECT_OPTIONS=[
    'DESCONHECIDO',
    'SEM DEFEITOS',
    'OUTRO',
    'DEFEITO PRÓXIMO A ESTRADA',
    'SUPERFÍCIE DESGASTADA',
    'ENTULHOS NA ESTRADA',
    'SULCOS, BURACOS'
]
CRASH_TYPE_OPTIONS = [
    'SEM FERIMENTOS / DIRIGIR AFASTADO',
    'LESÃO E/OU REBOQUE DEVIDO A ACIDENTE',
    'COLISÃO FRONTAL',
    'COLISÃO TRASEIRA',
    'SAíDA DE PISTA',
    'COLISÃO LATERAL',
    'NÃO COLISÃO',
    'UNKNOWN',
    'COLISÃO',
]
INTERSECTION_RELATED_OPTIONS = [
    'Y',
    'S', 
    'N'
]
DAMAGE_OPTIONS = [
    '$501 - $1,500',
    'ACIMA DE $1,500',
    '$500 OU MENOS'
]
PRIM_CONTRIBUTORY_CAUSE_OPTIONS=[
    'INCAPAZ DE DETERMINAR',
    'GIRO INCORRETO/SEM SINAL ',
    'SEGUIR MUITO DE PERTO',
    'HABILIDADES/CONHECIMENTO/EXPERIÊNCIA DE CONDUÇÃO',
    'MANOBRA DE RÉ INADEQUADA',
    ' FALHAR EM DAR A DIREITA DE PASSAGEM',
    'ULTRAPASSAR/ULTRAPASSAR INADEQUADAMENTE',
    'CURVATURA IRREGULAR/SEM SINAL',
    'DIRIGIR NO LADO ERRADO/ERRADO',
    'USO INADEQUADO DA FAIXA',
    'NÃO APLICÁVEL',
    'NÃO REDUZIR A VELOCIDADE PARA EVITAR ACIDENTE',
    'DESCONSIDERAR SINAL DE TRÂNSITOS',
    'CLIMA',
    'DESCONSIDERAR  SINAL DE PARE',
    'EQUIPAMENTO - CONDIÇÕES DO VEÍCULO ',
    'OPERAR O VEÍCULO DE FORMA ERRÁTICA, IMPRUDENTE, DESCUIDADA, NEGLIGENTE OU AGRESSIVA',
    'NÃO CUMPRIMENTO DA DIREÇÃO DE PREFERÊNCIA DE DIREITO DE PASSAGEM',
    'DESCONSIDERAR OUTRO TRAFFIC SIGNS',
    'CONVERSÃO À DIREITA NO VERMELHO',
    'VISÃO OBSTRUÍDA (SINAIS, GALHOS DE ÁRVORES, PRÉDIOS, ETC.)',
    'AÇÃO EVASIVA DEVIDO A ANIMAL, OBJETO, NÃO MOTORISTA',
    'SOB A INFLUÊNCIA DE ÁLCOOL/DROGAS (USADO QUANDO A PRISÃO FOI EFETUADA)',
    'DISTRAÇÃO - DE FORA DO VEÍCULO',
    'EXCEDENDO A VELOCIDADE SEGURA PARA AS CONDIÇÕES',
    'DESRESPEITANDO AS MARCAÇÕES DA RUA',
    'DEFEITOS DE ENGENHARIA/SUPERFÍCIE/MARCAÇÃO DE RODOVIAS',
    'CONDIÇÕES FÍSICAS DO MOTORISTA',
    'DISTRAÇÃO - DE DENTRO DO VEÍCULO',
    'EXCEDENDO O LIMITE DE VELOCIDADE AUTORIZADO',
    'CONSTRUÇÃO/MANUTENÇÃO DE ESTRADAS',
    'DISTRAÇÃO - OUTRO DISPOSITIVO ELETRÔNICO (DISPOSITIVO DE NAVEGAÇÃO, DVD PLAYER, ETC.)',
    'ANIMAL',
    'TINHA INGERIDO BEBIDA (USO NÃO REALIZADO QUANDO A PRISÃO FOI FEITA)',
    'BICICLETA AVANÇA LEGAL NO SINAL VERMELHO',
    'USO DE CELULAR SUPERIOR A MENSAGENS DE TEXTO',
    'RELACIONADO AO PONTO DE ÔNIBUS',
    'MENSAGEM DE TEXTO',
    'FAIXAS DE PEDESTRES OBSTRUÍDAS',
    'DESCONSIDERAR SIELD SIGN',
    'MOTOCICLETA AVANÇA LEGAL NO SINAL VERMELHO',
    'DESCONSIDERAR O SINAL DE DIREÇÃO DE PREFERÊNCIA',
    'PASSANDO POR ÔNIBUS ESCOLAR PARADO'
]
MOST_SEVERE_INJURY_OPTIONS = [
    'SEM INDICAÇÃO DE LESÃO  ',
    'LESÃO NÃO-INCAPACITANTE  ',
    'LESÃO INCAPACITANTE  ',
    'RELATADO, NÃO EVIDENTE ',
    'FATAL'
]

# --- Definição dos Campos de Dados ---
# Define todos os campos para o DataObject, seus tipos esperados e regras de validação básicas.
# Nota: 'crash_hour', 'crash_day_of_week', 'crash_month' NÃO estão aqui porque são *derivados* da 'crash_date'
# e não são campos de entrada diretos para o DataObject.
FIELDS = [
    # (nome_do_campo, tipo_esperado, valor_padrao, eh_obrigatorio)
    ('crash_date', str, '01/01/2020 00:00:00 AM', True),
    ('traffic_control_device', str, TRAFFIC_CONTROL_DEVICE_OPTIONS[0], False),
    ('weather_condition', str, WEATHER_CONDITION_OPTIONS[0], False),
    ('lighting_condition', str, LIGHTING_CONDITION_OPTIONS[0], False),
    ('first_crash_type', str, FIRST_CRASH_TYPE_OPTIONS[0], False),
    ('trafficway_type', str, TRAFFICWAY_TYPE_OPTIONS[0], False),
    ('alignment', str, ALIGNMENT_OPTIONS[0], False),
    ('roadway_surface_cond', str, ROADWAY_SURFACE_COND_OPTIONS[0], False),
    ('road_defect', str, ROAD_DEFECT_OPTIONS[0], False),
    ('crash_type', str,CRASH_TYPE_OPTIONS[0], False),
    ('intersection_related_i', str,INTERSECTION_RELATED_OPTIONS[0], False), # 'Y' ou 'N'
    ('damage', str,DAMAGE_OPTIONS[0], False),
    ('prim_contributory_cause', str,PRIM_CONTRIBUTORY_CAUSE_OPTIONS[0], False),
    ('num_units', int, 0, False),
    ('most_severe_injury', str,MOST_SEVERE_INJURY_OPTIONS[0], False),
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
    'intersection_related_i': 'Relacionado a Interseção I (Y/N)',
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
    'data_acidente': 'crash_date',
    'dispositivo_de_controle_de_trafego': 'traffic_control_device',
    'condicao_climatica': 'weather_condition',
    'condicao_de_iluminacao': 'lighting_condition',
    'primeiro_tipo_de_acidente': 'first_crash_type',
    'tipo_de_pista_de_trafego': 'trafficway_type',
    'alinhamento': 'alignment',
    'superficie_da_estrada': 'roadway_surface_cond',
    'defeito_da_estrada': 'road_defect',
    'tipo_de_acidente': 'crash_type',
    'relacionado_a_intersecao_i': 'intersection_related_i',
    'dano': 'damage',
    'causa_contributiva_primaria': 'prim_contributory_cause',
    'num_unidades': 'num_units',
    'ferimento_mais_severo': 'most_severe_injury',
    'ferimentos_total': 'injuries_total',
    'ferimentos_fatais': 'injuries_fatal',
    'ferimentos_incapacitantes': 'injuries_incapacitating',
    'ferimentos_nao_incapacitantes': 'injuries_non_incapacitating',
    'ferimentos_reportado_nao_evidente': 'injuries_reported_not_evident',
    'ferimentos_sem_indicacao': 'injuries_no_indication',
    # Campos que podem estar no CSV mas são *derivados* no DataObject, e, portanto, serão ignorados do input data_dict
    'hora_acidente': 'crash_hour',
    'dia_semana_acidente': 'crash_day_of_week',
    'mes_acidente': 'crash_month'
}



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

    def __init__(self, db_file_path: Path): # Alterado para Path
        self.db_file_path = db_file_path
        self._initialize_db_header()

    def _initialize_db_header(self):
        """
        Inicializa o arquivo DB com um cabeçalho, se ele não existir ou estiver vazio.
        """
        if not self.db_file_path.exists() or self.db_file_path.stat().st_size < self.DB_HEADER_SIZE:
            try:
                with filelock.FileLock(str(self.db_file_path) + ".lock"): # Usar str() para filelock
                    self.db_file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.db_file_path, "r+b" if self.db_file_path.exists() else "w+b") as f:
                        f.seek(0)
                        if self.db_file_path.stat().st_size < self.DB_HEADER_SIZE:
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
            with filelock.FileLock(str(self.db_file_path) + ".lock"):
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
            with filelock.FileLock(str(self.db_file_path) + ".lock"):
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
            with filelock.FileLock(str(self.db_file_path) + ".lock"):
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
            with filelock.FileLock(str(self.db_file_path) + ".lock"):
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
            with filelock.FileLock(str(self.db_file_path) + ".lock"):
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
            with filelock.FileLock(str(self.db_file_path) + ".lock"):
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
            # Use csv.reader para lidar com o delimitador e as aspas
            csv_reader = csv.reader(csv_file_buffer, delimiter=';')
            
            # Lê o cabeçalho e remove espaços em branco
            header = [h.strip() for h in next(csv_reader)]

            # Determina o tipo de cabeçalho e cria um mapeamento de coluna para campo do DataObject
            column_to_field_map = {}
            expected_english_fields = [f[0] for f in FIELDS] # Nomes dos campos esperados em inglês
            
            is_portuguese_header = False
            for col_name_csv in header:
                # Tenta mapear para português (case-insensitive)
                if col_name_csv.lower() in PORTUGUESE_TO_ENGLISH_HEADERS:
                    mapped_field = PORTUGUESE_TO_ENGLISH_HEADERS[col_name_csv.lower()]
                    column_to_field_map[col_name_csv] = mapped_field
                    if col_name_csv.lower() != mapped_field.lower(): # Verifica se houve tradução
                        is_portuguese_header = True
                elif col_name_csv in expected_english_fields: # Se já for inglês
                    column_to_field_map[col_name_csv] = col_name_csv
                # Colunas não reconhecidas serão ignoradas

            if not column_to_field_map:
                st.error("Nenhum cabeçalho reconhecível encontrado no arquivo CSV. Verifique se os cabeçalhos estão em português ou inglês e correspondem aos campos esperados.")
                # Retorna o número de linhas restantes como inválidas, já que não podemos processá-las
                return 0, len(list(csv_reader))

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
                return 0, len(list(csv_reader))

            # Mapeamento de índices de coluna para nomes de campo do DataObject
            field_index_map = {col_name_csv: idx for idx, col_name_csv in enumerate(header)}

            for i, row in enumerate(csv_reader):
                logger.info(f"Processando linha {i+1}: {row}")
                if len(row) != len(header):
                    st.warning(f"Linha {i+1} tem número de colunas inconsistente ({len(row)} vs {len(header)}). Pulando esta linha.")
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
                            st.error(f"Falha ao escrever registro da linha {i+1} no DB (ID gerado: {data_obj.id if hasattr(data_obj, 'id') else 'N/A'}): {row}")
                    else:
                        invalid_count += 1
                        st.warning(f"Linha {i+1} inválida, não adicionada ao DB. Verifique logs para detalhes: {row}")
                except DataValidationError as e:
                    invalid_count += 1
                    st.error(f"Erro de validação na linha {i+1}: {e} - Dados: {row}")
                except Exception as e:
                    invalid_count += 1
                    st.error(f"Erro inesperado ao processar linha {i+1}: {traceback.format_exc()} - Dados: {row}")
        except Exception as e:
            st.error(f"Erro ao ler arquivo CSV: {traceback.format_exc()}")
            logger.error(f"Erro fatal ao processar CSV: {traceback.format_exc()}")

        st.success(f"Processamento concluído. Registros válidos escritos no DB: {processed_count}. Registros inválidos/erros: {invalid_count}.")
        logger.info(f"Processamento CSV concluído. Registros válidos escritos no DB: {processed_count}. Registros inválidos/erros: {invalid_count}.")
        return processed_count, invalid_count

# --- Constantes e Funções Auxiliares de apendice_v1.py ---
BUFFER_SIZE = 65536
DEFAULT_EXTENSION = ".csv"
HUFFMAN_COMPRESSED_EXTENSION = ".huff"
LZW_COMPRESSED_EXTENSION = ".lzw"
MIN_COMPRESSION_SIZE = 100
MAX_FILE_SIZE_MB = 100
CHUNK_SIZE = 4096
MAX_BACKUPS = 5
MAX_LOG_ENTRIES_DISPLAY = 10

# Blowfish constants
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

# Helper functions from apendice_v1.py
def count_file(input_file_path, extension, folder):
    prefix = Path(input_file_path).name
    contador = 1
    for nome_arquivo in os.listdir(folder):
        # Ajuste para garantir que o prefixo corresponda ao nome base do arquivo
        # e não inclua extensões anteriores ou versões
        base_name_no_ext = Path(prefix).stem
        if fnmatch.fnmatch(nome_arquivo, f"{base_name_no_ext}*{extension}"):
            contador = contador + 1
    return contador

def get_original(file_name: str, old_extension: str) -> str:
    # Remove a extensão de compressão/criptografia e a parte _versionX
    # Ex: "original_file_version2.enc.aes_rsa" -> "original_file"
    # Ex: "original_file_version2.huff" -> "original_file"
    
    # Primeiro, remove a extensão final (ex: .enc.aes_rsa ou .huff)
    name_without_final_ext, _ = os.path.splitext(file_name)
    
    # Se a extensão original foi parte de um nome de arquivo composto (ex: .csv.huff),
    # então o name_without_final_ext ainda pode ter a extensão original.
    # Ex: "meu_arquivo.csv.huff" -> "meu_arquivo.csv"
    # Precisamos remover a extensão original se ela estiver presente e for a que estamos procurando.
    if name_without_final_ext.endswith(old_extension):
        name_without_final_ext = name_without_final_ext[:-len(old_extension)]

    # Agora, remove a parte "_versionX" se existir
    regex_pattern_dynamic_version = r'_version\d+$'
    match = re.search(regex_pattern_dynamic_version, name_without_final_ext)
    if match:
        return name_without_final_ext[:match.start()]
    else:
        return name_without_final_ext


# Huffman Implementation (from apendice_v1.py)
class Node:
    __slots__ = ['char', 'freq', 'left', 'right']
    
    def __init__(self, char: Optional[bytes], freq: int, 
                 left: Optional['Node'] = None, 
                 right: Optional['Node'] = None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other: 'Node'):
        return self.freq < other.freq

class HuffmanProcessor:
    @staticmethod
    def generate_tree(data: bytes, progress_callback: Optional[Callable[[float, str], None]] = None) -> Optional[Node]:
        if not data:
            return None
            
        if len(data) == 1:
            return Node(data, 1)

        if progress_callback:
            progress_callback(0, "Analisando conteúdo do arquivo...")

        byte_count = Counter(data)
        
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
        start_time = time.time()
        
        with open(input_path, 'rb') as file:
            data = file.read()

        if not data:
            return 0, 0, 0.0, 0.0

        original_size = len(data)
        
        if original_size < MIN_COMPRESSION_SIZE:
            with open(output_path, 'wb') as file:
                file.write(data)
            return original_size, original_size, 0.0, time.time() - start_time

        if progress_callback:
            progress_callback(0, "Construindo Árvore de Huffman...")
        root = HuffmanProcessor.generate_tree(
            data, 
            lambda p, m: progress_callback(p * 0.3, f"Huffman: {m}") if progress_callback else None
        )

        if progress_callback:
            progress_callback(0.3, "Gerando dicionário de codificação...")
        codebook = HuffmanProcessor.build_codebook(root)
        encode_table = {byte[0]: code for byte, code in codebook.items()}

        if progress_callback:
            progress_callback(0.4, "Comprimindo dados...")

        with open(output_path, 'wb') as file:
            file.write(struct.pack('I', len(codebook)))
            for byte, code in codebook.items():
                file.write(struct.pack('B', byte[0]))
                file.write(struct.pack('B', len(code)))
                # Convert binary string to int, then pack. Handle empty code for single char input
                file.write(struct.pack('I', int(code, 2) if code else 0)) 

            file.write(struct.pack('I', original_size))

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

            if bit_count > 0:
                current_byte <<= (8 - bit_count)
                buffer.append(current_byte)
            
            if buffer:
                file.write(buffer)
            
            # Write padding bits info
            file.write(struct.pack('B', (8 - bit_count) % 8))

        compressed_size = os.path.getsize(output_path)
        compression_ratio = (original_size - compressed_size) / original_size * 100
        process_time = time.time() - start_time

        if progress_callback:
            progress_callback(1.0, "Compressão completa!")

        return original_size, compressed_size, compression_ratio, process_time

    @staticmethod
    def decompress_file(input_path: str, output_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[int, int, float, float]:
        start_time = time.time()
        
        with open(input_path, 'rb') as file:
            table_size = struct.unpack('I', file.read(4))[0]
            code_table = {}
            max_code_length = 0
            
            if progress_callback:
                progress_callback(0.1, "Lendo metadados...")

            for i in range(table_size):
                byte = struct.unpack('B', file.read(1))[0]
                code_length = struct.unpack('B', file.read(1))[0]
                code_int = struct.unpack('I', file.read(4))[0]
                # Reconstruct binary string from int and length
                code = format(code_int, f'0{code_length}b') 
                code_table[code] = bytes([byte])
                max_code_length = max(max_code_length, code_length)
                
                if progress_callback and i % 100 == 0:
                    progress = 0.1 + 0.2 * (i / table_size)
                    progress_callback(progress, f"Carregando tabela de códigos: {i}/{table_size}")

            original_data_size = struct.unpack('I', file.read(4))[0] # Changed from data_size to original_data_size for clarity
            
            # Read all remaining bytes for compressed data
            compressed_data_raw = file.read()
            
            # The last byte of the raw compressed data contains the padding bits
            padding_bits = compressed_data_raw[-1]
            compressed_data_bytes = compressed_data_raw[:-1] # Actual compressed data without padding info

            total_compressed_bits = len(compressed_data_bytes) * 8 - padding_bits
            
            if progress_callback:
                progress_callback(0.3, "Preparando para decodificar...")

            result = io.BytesIO()
            current_bits = ""
            bytes_decoded = 0
            bits_processed = 0

            for byte_val in compressed_data_bytes:
                bits_in_byte = format(byte_val, '08b')
                for bit in bits_in_byte:
                    if bits_processed < total_compressed_bits: # Only process actual data bits
                        current_bits += bit
                        bits_processed += 1
                        
                        # Try to match prefixes
                        found_match = False
                        # Iterate from longest possible code to shortest
                        for length in range(1, min(len(current_bits), max_code_length) + 1):
                            prefix = current_bits[:length]
                            if prefix in code_table:
                                result.write(code_table[prefix])
                                bytes_decoded += 1
                                current_bits = current_bits[length:]
                                found_match = True
                                break # Found a match, move to next bits
                        
                        # If no match found for any prefix, it's an error or incomplete data
                        # This scenario should ideally not happen with a valid Huffman stream
                        if not found_match and current_bits:
                            # This part might need more robust error handling if data is truly corrupted
                            # For now, we'll just log and try to continue or break
                            logger.warning(f"No Huffman code match for prefix: {current_bits}. Data might be corrupted.")
                            # Consider breaking or raising an error here if strictness is needed
                            # For now, let's just continue and hope for recovery or end of stream
                            pass # Keep processing if possible, or break if it's clearly stuck

                    if bytes_decoded >= original_data_size: # Stop if we've decoded enough bytes
                        break
                if bytes_decoded >= original_data_size: # Stop if we've decoded enough bytes
                    break
                if progress_callback and bytes_decoded % 1000 == 0:
                    progress = 0.3 + 0.7 * (bytes_decoded / original_data_size)
                    progress_callback(progress, f"Decodificados {bytes_decoded}/{original_data_size} bytes")

        with open(output_path, 'wb') as file:
            final_decoded_data = result.getvalue()
            # Ensure we only write up to the original size, in case of extra padding bits leading to extra bytes
            file.write(final_decoded_data[:original_data_size])

        compressed_size = os.path.getsize(input_path)
        decompressed_size = os.path.getsize(output_path)
        compression_ratio = (compressed_size - decompressed_size) / compressed_size * 100
        process_time = time.time() - start_time

        if progress_callback:
            progress_callback(1.0, "Descompressão completa!")

        return compressed_size, decompressed_size, compression_ratio, process_time

# LZW Implementation (from apendice_v1.py)
class LZWProcessor:
    @staticmethod
    def compress(input_file_path: str, output_file_path: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[int, int, float, float]:
        start_time = time.time()
        
        try:
            with open(input_file_path, 'rb') as f:
                data = f.read()
            
            original_size = len(data)
            if not data:
                return 0, 0, 0.0, 0.0

            dictionary = {bytes([i]): i for i in range(256)}
            next_code = 256
            compressed_data = []
            w = bytes()
            
            total_bytes = len(data)
            processed_bytes = 0
            bits = 9
            max_code = 2**bits - 1
            
            for byte in data:
                c = bytes([byte])
                wc = w + c
                if wc in dictionary:
                    w = wc
                else:
                    compressed_data.append(dictionary[w])
                    if next_code <= 2**24 - 1: # Limite para evitar estouro de memória ou códigos muito longos
                        dictionary[wc] = next_code
                        next_code += 1
                    if next_code > max_code and bits < 24: # Aumenta bits até 24
                        bits += 1
                        max_code = 2**bits - 1
                    w = c
                
                processed_bytes += 1
                if progress_callback and processed_bytes % 1000 == 0:
                    progress = processed_bytes / total_bytes
                    progress_callback(progress, f"Comprimindo... {processed_bytes}/{total_bytes} bytes processados")
            
            if w:
                compressed_data.append(dictionary[w])
            
            with open(output_file_path, 'wb') as f:
                f.write(len(compressed_data).to_bytes(4, byteorder='big')) # Número de códigos
                f.write(initial_bits.to_bytes(1, byteorder='big')) # Salva o número inicial de bits (9)
                
                buffer = 0
                buffer_length = 0
                
                for code in compressed_data:
                    # Calcula o número de bits necessários para o código atual
                    # Deve ser baseado no `next_code` atual do dicionário no momento da COMPRESSÃO
                    # NOTA: Esta lógica pode ser complexa. Para LZW, o tamanho do código pode variar.
                    # A implementação original do apendice_v1.py tinha um bug aqui.
                    # Uma abordagem mais robusta seria recalcular `bits` para cada `code` baseado no `next_code`
                    # no momento em que o código foi gerado durante a compressão, ou usar um tamanho fixo por bloco.
                    # Para simplificar e manter a compatibilidade com a descompressão do apendice_v1.py,
                    # vou usar o `bits` que cresceu durante a compressão.
                    
                    # A lógica do apendice_v1.py para current_code_bits parece ser um erro.
                    # O número de bits para codificar um símbolo deve ser o `bits` atual do dicionário.
                    current_code_bits = bits # Usa o 'bits' atual que foi ajustado
                    if code >= (1 << current_code_bits): # Se o código excede o tamanho atual de bits, aumenta
                        current_code_bits = (code.bit_length() + 7) // 8 * 8 # Arredonda para o próximo byte
                        if current_code_bits < 9: current_code_bits = 9 # Minimo de 9 bits
                        if current_code_bits > 24: current_code_bits = 24 # Maximo de 24 bits

                    buffer = (buffer << current_code_bits) | code
                    buffer_length += current_code_bits
                    
                    while buffer_length >= 8:
                        byte = (buffer >> (buffer_length - 8)) & 0xFF
                        f.write(bytes([byte]))
                        buffer_length -= 8
                        buffer = buffer & ((1 << buffer_length) - 1)
                
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
        start_time = time.time()
        
        try:
            with open(input_file_path, 'rb') as f:
                num_codes_expected = int.from_bytes(f.read(4), byteorder='big')
                initial_bits = int.from_bytes(f.read(1), byteorder='big')
                compressed_bytes = f.read()
            
            compressed_size = os.path.getsize(input_file_path)
            dictionary = {i: bytes([i]) for i in range(256)}
            next_code = 256
            decompressed_data = bytearray()
            buffer = 0
            buffer_length = 0
            byte_pos = 0
            codes = []
            current_bits = initial_bits # Começa com 9 bits
            
            # Lendo os códigos do arquivo
            while byte_pos < len(compressed_bytes):
                # Preenche o buffer
                while buffer_length < current_bits and byte_pos < len(compressed_bytes):
                    buffer = (buffer << 8) | compressed_bytes[byte_pos]
                    byte_pos += 1
                    buffer_length += 8
                
                # Se ainda não há bits suficientes para ler um código completo, sai
                if buffer_length < current_bits:
                    break
                
                # Extrai o código
                code = (buffer >> (buffer_length - current_bits)) & ((1 << current_bits) - 1)
                codes.append(code)
                buffer_length -= current_bits
                
                # Atualiza current_bits se o dicionário cresceu
                if next_code >= (1 << current_bits) and current_bits < 24:
                    current_bits += 1
                
                # Adiciona nova entrada ao dicionário (placeholder, será preenchido depois)
                if next_code <= 2**24 -1: # Evita que o dicionário cresça indefinidamente
                    dictionary[next_code] = None # Placeholder
                    next_code += 1

                if progress_callback and len(codes) % 1000 == 0:
                    progress = len(codes) / num_codes_expected
                    progress_callback(progress * 0.5, f"Lendo dados comprimidos... {len(codes)}/{num_codes_expected} códigos processados")
            
            if len(codes) != num_codes_expected:
                logger.warning(f"Número de códigos lidos ({len(codes)}) difere do esperado ({num_codes_expected}). Tentando continuar.")
            
            # Reset dictionary for actual decompression logic
            dictionary = {i: bytes([i]) for i in range(256)}
            next_code = 256
            
            if not codes:
                raise ValueError("Nenhum código para descomprimir.")

            w = dictionary[codes[0]]
            decompressed_data.extend(w)
            
            for code in codes[1:]:
                # Atualiza current_bits para o próximo ciclo de dicionário
                # Isso é crucial para que o decodificador saiba quantos bits ler para o próximo código
                if next_code >= (1 << current_bits) and current_bits < 24:
                    current_bits += 1
                
                if code in dictionary:
                    entry = dictionary[code]
                elif code == next_code: # Regra especial para LZW
                    entry = w + w[:1]
                else:
                    raise ValueError(f"Código comprimido inválido ou fora de ordem: {code}")
                
                decompressed_data.extend(entry)
                
                # Adiciona a nova sequência ao dicionário
                if next_code <= 2**24 - 1: # Limite para o dicionário
                    dictionary[next_code] = w + entry[:1]
                    next_code += 1
                w = entry
                
                if progress_callback and len(decompressed_data) % 100000 == 0:
                    progress = 0.5 + (len(decompressed_data) / (num_codes_expected * 3)) # Estimativa de progresso
                    progress_callback(progress, f"Descomprimindo... {len(decompressed_data)//1024}KB processados")

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

# Blowfish Implementation (from apendice_v1.py)
class Blowfish:
    def __init__(self, key):
        self.P = list(P_INIT)
        self.S = [list(s_arr) for s_arr in S_INIT]

        key_bytes = key
        key_len = len(key_bytes)
        
        j = 0
        for i in range(18):
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
            L, R = R, L
        R ^= self.P[16]
        L ^= self.P[17]
        return L, R

    def _decrypt_block(self, L, R):
        for i in range(17, 1, -1):
            L ^= self.P[i]
            R ^= self._feistel(L)
            L, R = R, L
        R ^= self.P[1]
        L ^= self.P[0]
        return L, R

    def encrypt(self, data):
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
        
        if not decrypted_data:
            raise ValueError("Dados descriptografados vazios. Senha incorreta ou arquivo corrompido?")

        padding_len = decrypted_data[-1]
        if padding_len > 8 or padding_len == 0:
            raise ValueError("Padding incorreto ou dados corrompidos. Senha incorreta ou arquivo não Blowfish?")
        
        # Validate padding bytes
        if not all(byte == padding_len for byte in decrypted_data[-padding_len:]):
             raise ValueError("Integridade do padding violada. Senha incorreta ou arquivo corrompido.")

        return decrypted_data[:-padding_len]

# RSA and AES Hybrid Implementation (from apendice_v1.py)
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
    def generate_sample():
        test_file = ENCRYPT_FOLDER / "test_document.txt"
        if not test_file.exists():
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("This is a test document for encryption and decryption. " * 100)
    
    @staticmethod
    def hybrid_encrypt_file(input_file: str, public_key_file: str, output_file: str):
        with open(input_file, 'rb') as f:
            plaintext = f.read()

        with open(public_key_file, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
        
        session_key = os.urandom(32)
        encrypted_session_key = public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(session_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        tag = encryptor.tag

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
                password=None,
                backend=default_backend()
            )
        
        with open(input_file, 'rb') as f:
            rsa_key_size_bytes = private_key.key_size // 8
            encrypted_session_key = f.read(rsa_key_size_bytes)
            iv = f.read(16)
            tag = f.read(16)
            ciphertext = f.read()
        
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

# --- Funções de UI (Streamlit) e Lógica de Negócio que usarão a nova classe ---

class Functions: # Renomeada para evitar conflito com a classe TrafficAccidentDB
    """
    Uma coleção de métodos utilitários para lidar com várias tarefas,
    incluindo criptografia, hashing, leitura/escrita de banco de dados
    e funcionalidades de UI/UX para Streamlit.
    """
    
    # Instância da classe de banco de dados
    _db_manager = TrafficAccidentDB(db_file_path=DB_FILE_PATH) # Instancia a classe aqui
    
    # --- Configurações de Criptografia e Chaves ---
    _private_key = None
    _public_key = None
    _aes_key = None
    _cipher = None
    _aes_key_path = ENCRYPT_FOLDER / "aes_key.bin" # Caminho ajustado
    _public_key_path = ENCRYPT_FOLDER / "public_key.pem" # Caminho ajustado
    _private_key_path = ENCRYPT_FOLDER / "private_key.pem" # Caminho ajustado
    
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
        if db_file_path.exists():
            return db_file_path.stat().st_mtime
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
            # Tenta decodificar como UTF-8, com fallback para latin-1
            try:
                # Decodifica o arquivo como UTF-8
                string_io = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
                st.info("Arquivo CSV decodificado como UTF-8.")
            except UnicodeDecodeError:
                # Se falhar, tenta decodificar como latin-1 e avisa o usuário
                st.warning("Falha ao decodificar CSV como UTF-8. Tentando decodificar como ISO-8859-1 (Latin-1).")
                string_io = io.StringIO(uploaded_file.getvalue().decode("iso-8859-1"))
            except Exception as e:
                st.error(f"Erro inesperado ao decodificar o arquivo CSV: {e}")
                return

            # Chama o método da instância de TrafficAccidentDB
            processed, invalid = Functions._db_manager.process_csv_to_db(string_io)
            if processed > 0:
                st.success(f"CSV processado! {processed} registros válidos adicionados. {invalid} registros inválidos/erros.")
                Functions.load_data_from_db(force_reload=True) # Recarrega dados após upload
            elif invalid > 0:
                st.warning(f"Nenhum registro válido do CSV foi adicionado. {invalid} registros inválidos/erros. Verifique o formato do arquivo.")
            else:
                st.info("O arquivo CSV está vazio ou não contém dados válidos.")

    # --- Funções de Criptografia e Compressão (Adaptadas de apendice_v1.py) ---

    @staticmethod
    def derive_key_pbkdf2(password: bytes, salt: bytes, dk_len: int = 16, iterations: int = 10000) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=dk_len,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(password)

    @staticmethod
    def blowfish_encrypt_file_func(input_file: str, output_file: str, password: str):
        salt = os.urandom(16)
        key = Functions.derive_key_pbkdf2(password.encode(), salt, dk_len=32)
        cipher = Blowfish(key)
        with open(input_file, 'rb') as f:
            plaintext = f.read()
        ciphertext = cipher.encrypt(plaintext)
        with open(output_file, 'wb') as f:
            f.write(salt)
            f.write(ciphertext)

    @staticmethod
    def blowfish_decrypt_file_func(input_file: str, output_file: str, password: str):
        with open(input_file, 'rb') as f:
            salt = f.read(16)
            ciphertext = f.read()
        key = Functions.derive_key_pbkdf2(password.encode(), salt, dk_len=32)
        cipher = Blowfish(key)
        try:
            plaintext = cipher.decrypt(ciphertext)
        except ValueError as e:
            raise ValueError(f"Erro ao descriptografar: {e}")
        with open(output_file, 'wb') as f:
            f.write(plaintext)

    # --- Placeholder Methods for app_v6.py Integration (mantidos para compatibilidade com outros módulos) ---
    # Estes métodos devem ser preenchidos com a lógica real do app_v6.py se necessário
    # ou removidos se não forem mais utilizados.

    @staticmethod
    def v6_run_step_2_logic():
        """Placeholder for the logic of 'Etapa 2' from app_v6.py."""
        st.write("Executando lógica da Etapa 2...")
        st.success("Lógica da Etapa 2 concluída (placeholder).")

    @staticmethod
    def v6_run_step_3_logic():
        """Placeholder for the logic of 'Etapa 3' from app_v6.py."""
        st.write("Executando lógica da Etapa 3...")
        st.success("Lógica da Etapa 3 concluída (placeholder).")

    @staticmethod
    def v6_run_step_4_logic():
        """Placeholder for the logic of 'Etapa 4' from app_v6.py."""
        st.write("Executando lógica da Etapa 4...")
        st.success("Lógica da Etapa 4 concluída (placeholder).")

    @staticmethod
    def v6_display_system_admin():
        """Placeholder for the 'Administração do Sistema' content from app_v6.py."""
        st.write("Conteúdo da Administração do Sistema (placeholder).")
        st.info("Esta seção conteria ferramentas para gerenciar o sistema, como backup/restauração do DB, gerenciamento de usuários (se aplicável), etc.")

    @staticmethod
    def check_time_input(date_accident, hour_accident):
        """
        Verifica e ajusta a hora do acidente se necessário.
        Esta função é um placeholder e deve ser substituída pela lógica real do app_v6.py.
        """
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

# UI Functions (from apendice_v1.py, adapted for new folder structure)
def show_compression_ui():
    st.title("Ferramenta de Compressão/Descompressão de Arquivos")
    
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    def update_progress(progress: float, message: str):
        progress_bar.progress(progress)
        progress_text.text(message)
    
    selected_view = st.selectbox(
        "Selecionar Visualização:", 
        ("Compressão/Descompressão", "Comparação de Algoritmos"), 
        key="main_view_select_comp" # Adicionado sufixo para evitar conflito de key
    )

    if selected_view == "Compressão/Descompressão":
        algorithm = st.radio("Selecionar Algoritmo:", ("Huffman", "LZW"), key="algo_select_comp") # Adicionado sufixo
        operation = st.radio("Selecionar Operação:", ("Compressão", "Descompressão"), key="op_select_comp") # Adicionado sufixo
        allowed_types = []
        if operation == "Compressão":
            allowed_types = [".lzw", ".huff", ".csv", ".db", ".idx", ".btr"]
        else:
            if algorithm == "Huffman":
                allowed_types = [".huff"]
            elif algorithm == "LZW":
                allowed_types = [".lzw"]
        
        file_source = st.radio(
            "Selecionar Origem do Arquivo:", 
            ("Padrão", "Escolha do Usuário"), 
            key="comp_file_source" # Adicionado sufixo
        )
        
        input_path = None
        uploaded_file = None
        temp_dir_upload = None

        if file_source == "Padrão":
            source_folder = DATA_ROOT_DIR if operation == "Compressão" else COMPRESSED_FOLDER
            default_files = []
            if source_folder.exists():
                for file_name in os.listdir(source_folder):
                    file_ext = os.path.splitext(file_name)[1]
                    # Verifica se o arquivo é o DB principal ou um arquivo com extensão permitida
                    if (operation == "Compressão" and (file_name == DB_FILE_PATH.name or file_ext in allowed_types)) or \
                       (operation == "Descompressão" and file_ext in allowed_types):
                        default_files.append(file_name)
            if default_files:
                selected_file = st.selectbox(f"Selecione um arquivo de {source_folder}:", default_files)
                input_path = str(source_folder / selected_file) # Converte Path para str
            else:
                st.warning(f"Nenhum arquivo {', '.join(allowed_types)} encontrado em {source_folder}")
        else:
            uploaded_file = st.file_uploader(
                "Carregar um arquivo:", 
                type=[ext.strip('.') for ext in allowed_types],
                key="upload_comp_tab1" # Adicionado sufixo
            )
            if uploaded_file:
                temp_dir_upload = tempfile.mkdtemp(dir=TEMP_FOLDER) # Cria temp dir dentro de TEMP_FOLDER
                input_path = os.path.join(temp_dir_upload, uploaded_file.name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.info(f"Arquivo '{uploaded_file.name}' carregado temporariamente.")

        if input_path and st.button(f"Executar {operation}", key="execute_comp_btn"): # Adicionado sufixo
            progress_bar.progress(0)
            progress_text.text(f"Iniciando {operation.lower()}...")
            output_folder = COMPRESSED_FOLDER
            
            try:
                if operation == "Compressão":
                    original_file_name = Path(input_path).name
                    output_ext = HUFFMAN_COMPRESSED_EXTENSION if algorithm == "Huffman" else LZW_COMPRESSED_EXTENSION
                    # Ajuste para o nome do arquivo de saída, considerando o nome original sem a extensão padrão
                    base_name_no_original_ext = Path(original_file_name).stem if original_file_name.endswith(DEFAULT_EXTENSION) else Path(original_file_name).name
                    output_file_name = f"{base_name_no_original_ext}_version{count_file(input_path, output_ext, output_folder)}{output_ext}"
                    output_path = str(output_folder / output_file_name) # Converte Path para str

                    if algorithm == "Huffman":
                        orig_s, comp_s, ratio, proc_t = HuffmanProcessor.compress_file(input_path, output_path, update_progress)
                    else:
                        orig_s, comp_s, ratio, proc_t = LZWProcessor.compress(input_path, output_path, update_progress)
                    
                    st.success(f"Compressão {algorithm} Concluída!")
                    st.write(f"Tamanho Original: {orig_s / 1024:.2f} KB")
                    st.write(f"Tamanho Comprimido: {comp_s / 1024:.2f} KB")
                    st.write(f"Taxa de Compressão: {ratio:.2f}%")
                    st.write(f"Tempo Gasto: {proc_t:.4f} segundos")

                    if comp_s > 0:
                        with open(output_path, "rb") as f_out:
                            st.download_button(
                                label=f"Baixar Arquivo Comprimido ({output_ext})",
                                data=f_out.read(),
                                file_name=output_file_name,
                                mime="application/octet-stream"
                            )

                else: # Descompressão
                    original_file_name = Path(input_path).name
                    output_ext_from_algo = HUFFMAN_COMPRESSED_EXTENSION if algorithm == "Huffman" else LZW_COMPRESSED_EXTENSION
                    
                    # Tenta inferir o nome original do arquivo descomprimido
                    # Ex: "meu_arquivo_version1.huff" -> "meu_arquivo" ou "meu_arquivo.csv"
                    base_name_for_decompression = get_original(original_file_name, output_ext_from_algo)
                    
                    # Adiciona a extensão padrão se não houver uma. Isso é uma heurística.
                    if not Path(base_name_for_decompression).suffix:
                        base_name_for_decompression += DEFAULT_EXTENSION

                    output_file_name = base_name_for_decompression
                    output_path = str(TEMP_FOLDER / output_file_name) # Converte Path para str
                    
                    if algorithm == "Huffman":
                        comp_s, decomp_s, ratio, proc_t = HuffmanProcessor.decompress_file(input_path, output_path, update_progress)
                    else:
                        comp_s, decomp_s, ratio, proc_t = LZWProcessor.decompress(input_path, output_path, update_progress)
                    
                    st.success(f"Descompressão {algorithm} Concluída!")
                    st.write(f"Tamanho Comprimido: {comp_s / 1024:.2f} KB")
                    st.write(f"Tamanho Descomprimido: {decomp_s / 1024:.2f} KB")
                    st.write(f"Tempo Gasto: {proc_t:.4f} segundos")

                    if decomp_s > 0:
                        with open(output_path, "rb") as f_out:
                            st.download_button(
                                label=f"Baixar Arquivo Descomprimido ({output_file_name})",
                                data=f_out.read(),
                                file_name=output_file_name,
                                mime="application/octet-stream"
                            )
            
            except FileNotFoundError:
                st.error("Arquivo não encontrado. Por favor, certifique-se de que o arquivo existe no caminho especificado.")
            except Exception as e:
                st.error(f"Erro durante {operation.lower()}: {str(e)}\n{traceback.format_exc()}")
            finally:
                if temp_dir_upload and Path(temp_dir_upload).exists():
                    try:
                        shutil.rmtree(temp_dir_upload) # Remove o diretório temporário e seu conteúdo
                    except OSError as e:
                        st.warning(f"Não foi possível limpar o diretório temporário: {e}")
                # Limpa arquivos temporários de saída da descompressão se existirem
                if 'output_path' in locals() and Path(output_path).exists() and Path(output_path).parent == TEMP_FOLDER:
                     try:
                         os.remove(output_path)
                     except OSError as e:
                         logger.warning(f"Não foi possível remover o arquivo temporário de saída: {e}")

                progress_bar.progress(1.0)
                time.sleep(0.5)

    elif selected_view == "Comparação de Algoritmos":
        st.header("Comparação de Desempenho de Algoritmos")
        compare_file_source = st.radio(
            "Selecione o arquivo para comparação:", 
            ("CSV Padrão", "Escolha do Usuário"), 
            key="compare_source_comp" # Adicionado sufixo
        )
        
        compare_file = None
        compare_uploaded = None
        temp_dir_compare = None
        input_path = None # Inicializa input_path

        if compare_file_source == "CSV Padrão":
            default_files = []
            if DATA_ROOT_DIR.exists():
                for file_name in os.listdir(DATA_ROOT_DIR):
                    if file_name.endswith(DEFAULT_EXTENSION):
                        default_files.append(file_name)
            if default_files:
                compare_file = st.selectbox("Selecione um arquivo CSV para comparação:", default_files)
                input_path = str(DATA_ROOT_DIR / compare_file) # Converte Path para str
            else:
                st.warning(f"Nenhum arquivo CSV encontrado em {DATA_ROOT_DIR}")
        else:
            compare_uploaded = st.file_uploader(
                "Carregar um arquivo para comparação", 
                type=["lzw", "huff", "csv", "db", "idx", "btr"],
                key="compare_upload_comp" # Adicionado sufixo
            )
            if compare_uploaded:
                temp_dir_compare = tempfile.mkdtemp(dir=TEMP_FOLDER) # Cria temp dir dentro de TEMP_FOLDER
                input_path = os.path.join(temp_dir_compare, compare_uploaded.name)
                with open(input_path, "wb") as f:
                    f.write(compare_uploaded.getbuffer())
        
        if input_path and st.button("Executar Comparação", key="execute_compare_btn"): # Adicionado sufixo
            progress_bar.progress(0)
            progress_text.text("Iniciando comparação...")
            
            try:
                huffman_output = str(TEMP_FOLDER / "temp_huffman.huff")
                lzw_output = str(TEMP_FOLDER / "temp_lzw.lzw")
                huffman_decompressed_output = str(TEMP_FOLDER / (Path(input_path).stem + ".huffout"))
                lzw_decompressed_output = str(TEMP_FOLDER / (Path(input_path).stem + ".lzwout"))

                progress_text.text( "Testando compressão Huffman...")
                huff_compress = HuffmanProcessor.compress_file(input_path, huffman_output, 
                    lambda p, m: update_progress(p * 0.3, f"Huffman: {m}"))
                
                progress_text.text("Testando descompressão Huffman...")
                huff_decompress = HuffmanProcessor.decompress_file(huffman_output, huffman_decompressed_output, 
                    lambda p, m: update_progress(0.4 + p * 0.2, f"Huffman: {m}"))
                
                progress_text.text("Testando compressão LZW...")
                lzw_compress = LZWProcessor.compress(input_path, lzw_output, 
                    lambda p, m: update_progress(0.6 + p * 0.2, f"LZW: {m}"))
                
                progress_text.text( "Testando descompressão LZW...")
                lzw_decompress = LZWProcessor.decompress(lzw_output, lzw_decompressed_output, 
                    lambda p, m: update_progress(0.8 + p * 0.2, f"LZW: {m}"))
                
                results = []
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
                
                df = pd.DataFrame(results)
                st.success("Comparação concluída!")
                st.dataframe(df.style.format({
                    'Original Size (KB)': '{:.2f}',
                    'Compressed Size (KB)': '{:.2f}',
                    'Compression Ratio (%)': '{:.2f}',
                    'Compression Time (s)': '{:.4f}',
                    'Decompression Time (s)': '{:.4f}',
                    'Total Time (s)': '{:.4f}'
                }))
                
                fig, axes = plt.subplots(2, 2, figsize=(15, 10))
                df.plot.bar(x='Algorithm', y='Compression Ratio (%)', ax=axes[0,0], title='Comparação de Taxa de Compressão', legend=False)
                axes[0,0].set_ylabel('Taxa (%)')
                df.plot.bar(x='Algorithm', y='Compression Time (s)', ax=axes[0,1], title='Comparação de Tempo de Compressão', legend=False)
                axes[0,1].set_ylabel('Tempo (s)')
                df.plot.bar(x='Algorithm', y='Decompression Time (s)', ax=axes[1,0], title='Comparação de Tempo de Descompressão', legend=False)
                axes[1,0].set_ylabel('Tempo (s)')
                df.plot.bar(x='Algorithm', y='Total Time (s)', ax=axes[1,1], title='Comparação de Tempo Total de Processamento', legend=False)
                axes[1,1].set_ylabel('Tempo (s)')
                plt.tight_layout()
                st.pyplot(fig)
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Baixar Resultados como CSV",
                    data=csv,
                    file_name="compression_comparison.csv",
                    mime="text/csv"
                )
            
            except Exception as e:
                st.error(f"Erro durante a comparação: {str(e)}\n{traceback.format_exc()}")
            finally:
                if temp_dir_compare and Path(temp_dir_compare).exists():
                    try:
                        shutil.rmtree(temp_dir_compare) # Remove o diretório temporário e seu conteúdo
                    except OSError as e:
                        st.warning(f"Não foi possível limpar o diretório temporário: {e}")
                # Limpa arquivos temporários de saída da comparação se existirem
                for temp_file in [huffman_output, lzw_output, huffman_decompressed_output, lzw_decompressed_output]:
                    if 'temp_file' in locals() and Path(temp_file).exists():
                        try:
                            os.remove(temp_file)
                        except OSError as e:
                            logger.warning(f"Não foi possível remover o arquivo temporário: {e}")
                progress_bar.progress(1.0)
                time.sleep(0.5)

def show_encryption_ui():
    st.title("Ferramenta de Criptografia de Arquivos")
    CryptographyHandler.generate_sample() # Garante que o arquivo de teste exista

    operations = [
        "Blowfish Criptografar",
        "Blowfish Descriptografar",
        "Gerar Chaves RSA",
        "Híbrida (AES + RSA) Criptografar",
        "Híbrida (AES + RSA) Descriptografar"
    ]
    
    selected_operation = st.selectbox("Selecione a Operação de Criptografia", operations, key="crypto_op_select") # Adicionado sufixo

    input_file_path = None
    public_key_file_path = None
    private_key_file_path = None
    temp_dir_upload = None
    temp_dir_pk_upload = None # Para chaves públicas/privadas carregadas

    if selected_operation != "Gerar Chaves RSA":
        file_source = st.radio(
            "Selecionar Origem do Arquivo:", 
            ("Padrão", "Escolha do Usuário"), 
            key="crypto_file_source_enc" # Adicionado sufixo
        )
        
        if file_source == "Padrão":
            default_files_options = {}
            if selected_operation in ["Blowfish Criptografar", "Híbrida (AES + RSA) Criptografar"]:
                # Adiciona o arquivo de teste e os arquivos do DB_FILE_PATH
                if (ENCRYPT_FOLDER / "test_document.txt").exists():
                    default_files_options["test_document.txt"] = str(ENCRYPT_FOLDER / "test_document.txt")
                if DB_FILE_PATH.exists():
                    default_files_options["Arquivo de Dados (.db)"] = str(DB_FILE_PATH)
                # Adicione aqui outros arquivos padrão se houver (ex: índices)
            elif selected_operation == "Blowfish Descriptografar":
                for file_name in os.listdir(ENCRYPT_FOLDER):
                    if file_name.endswith(".enc.bf"):
                        default_files_options[file_name] = str(ENCRYPT_FOLDER / file_name)
            elif selected_operation == "Híbrida (AES + RSA) Descriptografar":
                for file_name in os.listdir(ENCRYPT_FOLDER):
                    if file_name.endswith(".enc.aes_rsa"):
                        default_files_options[file_name] = str(ENCRYPT_FOLDER / file_name)
            
            if default_files_options:
                selected_file_name = st.selectbox(f"Selecione um arquivo:", list(default_files_options.keys()), key="selected_file_crypto") # Adicionado sufixo
                input_file_path = default_files_options[selected_file_name]
            else:
                st.warning(f"Nenhum arquivo padrão encontrado para '{selected_operation}'.")
        else:
            allowed_types = []
            if selected_operation in ["Blowfish Criptografar", "Híbrida (AES + RSA) Criptografar"]:
                allowed_types = ["txt", "csv", "db", "idx", "btr"] # Tipos comuns para criptografar
            elif selected_operation == "Blowfish Descriptografar":
                allowed_types = ["bf"]
            elif selected_operation == "Híbrida (AES + RSA) Descriptografar":
                allowed_types = ["aes_rsa"]
            
            uploaded_file = st.file_uploader(
                "Carregar um arquivo:", 
                type=allowed_types if allowed_types else None,
                key="upload_crypto_main_file" # Adicionado sufixo
            )
            if uploaded_file:
                temp_dir_upload = tempfile.mkdtemp(dir=TEMP_FOLDER) # Cria temp dir dentro de TEMP_FOLDER
                input_file_path = os.path.join(temp_dir_upload, uploaded_file.name)
                with open(input_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.info(f"Arquivo '{uploaded_file.name}' carregado temporariamente.")

    if selected_operation == "Blowfish Criptografar":
        st.header("Criptografia Blowfish")
        output_filename = st.text_input("Nome do arquivo de saída", 
                                        value=f"{Path(input_file_path).stem}_version{count_file(input_file_path, '.enc.bf', ENCRYPT_FOLDER)}.enc.bf" if input_file_path else "", 
                                        key="blowfish_output_enc")
        password = st.text_input("Senha para Blowfish", type="password", key="blowfish_password_enc")

        if st.button("Criptografar com Blowfish", key="btn_blowfish_enc"):
            if input_file_path and output_filename and password:
                output_path = str(ENCRYPT_FOLDER / output_filename) # Converte Path para str
                try:
                    Functions.blowfish_encrypt_file_func(input_file_path, output_path, password) # Chama o método da classe Functions
                    st.success(f"Arquivo criptografado com sucesso em '{output_path}'!")
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Baixar Arquivo Criptografado",
                            data=f.read(),
                            file_name=output_filename,
                            mime="application/octet-stream"
                        )
                except Exception as e:
                    st.error(f"Erro na criptografia Blowfish: {e}\n{traceback.format_exc()}")
                finally:
                    if temp_dir_upload and Path(temp_dir_upload).exists():
                        try:
                            shutil.rmtree(temp_dir_upload)
                        except OSError as e:
                            st.warning(f"Não foi possível limpar o diretório temporário: {e}")
            else:
                st.warning("Por favor, selecione um arquivo de entrada, forneça um nome de saída e uma senha.")

    elif selected_operation == "Blowfish Descriptografar":
        st.header("Descriptografia Blowfish")
        # Tenta inferir o nome original do arquivo descomprimido
        default_output_name_dec = ""
        if input_file_path:
            # Remove a extensão .enc.bf
            base_name_no_enc = Path(input_file_path).stem
            # Tenta remover _versionX
            default_output_name_dec = get_original(base_name_no_enc, ".enc") # .enc é a extensão que Blowfish usa no apendice_v1
            if not Path(default_output_name_dec).suffix: # Se não tiver sufixo, adiciona .txt como padrão
                default_output_name_dec += ".txt"

        output_filename = st.text_input("Nome do arquivo de saída", 
                                        value=default_output_name_dec, 
                                        key="blowfish_output_dec")
        password = st.text_input("Senha para Blowfish", type="password", key="blowfish_password_dec")

        if st.button("Descriptografar com Blowfish", key="btn_blowfish_dec"):
            if input_file_path and output_filename and password:
                with tempfile.TemporaryDirectory(dir=TEMP_FOLDER) as temp_dir_output: # Cria temp dir dentro de TEMP_FOLDER
                    output_path = os.path.join(temp_dir_output, output_filename)
                    try:
                        Functions.blowfish_decrypt_file_func(input_file_path, output_path, password) # Chama o método da classe Functions
                        st.success(f"Arquivo descriptografado com sucesso em '{output_filename}'!")
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Baixar Arquivo Descriptografado",
                                data=f.read(),
                                file_name=output_filename,
                                mime="application/octet-stream"
                            )
                    except Exception as e:
                        st.error(f"Erro na descriptografia Blowfish: {e}\n{traceback.format_exc()}")
                    finally:
                        if temp_dir_upload and Path(temp_dir_upload).exists():
                            try:
                                shutil.rmtree(temp_dir_upload)
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
                st.success(f"Chaves RSA geradas com sucesso e salvas em '{ENCRYPT_FOLDER}'")
                with open(public_key_path, "rb") as f:
                    st.download_button(
                        label="Baixar Chave Pública",
                        data=f.read(),
                        file_name=os.path.basename(public_key_path),
                        mime="application/x-pem-file"
                    )
                with open(private_key_path, "rb") as f:
                    st.download_button(
                        label="Baixar Chave Privada",
                        data=f.read(),
                        file_name=os.path.basename(private_key_path),
                        mime="application/x-pem-file"
                    )
            except Exception as e:
                st.error(f"Erro ao gerar chaves RSA: {e}\n{traceback.format_exc()}")

    elif selected_operation == "Híbrida (AES + RSA) Criptografar":
        st.header("Criptografia Híbrida (AES + RSA)")
        st.subheader("Seleção da Chave Pública")
        key_file_source_enc = st.radio("Origem da Chave Pública:", ("Padrão", "Escolha do Usuário"), key="pk_source_enc")
        
        if key_file_source_enc == "Padrão":
            default_pk_files = {}
            for file_name in os.listdir(ENCRYPT_FOLDER):
                if file_name.endswith(".pem") and "public" in file_name:
                    default_pk_files[file_name] = str(ENCRYPT_FOLDER / file_name)
            if default_pk_files:
                selected_pk_name = st.selectbox("Selecione uma Chave Pública:", list(default_pk_files.keys()), key="selected_pk_enc") # Adicionado sufixo
                public_key_file_path = default_pk_files[selected_pk_name]
            else:
                st.warning("Nenhuma chave pública encontrada na pasta de criptografia.")
        else:
            uploaded_pk_file = st.file_uploader("Carregar chave pública (.pem)", type=["pem"], key="upload_pk_enc_file") # Adicionado sufixo
            if uploaded_pk_file:
                temp_dir_pk_upload = tempfile.mkdtemp(dir=TEMP_FOLDER) # Cria temp dir dentro de TEMP_FOLDER
                public_key_file_path = os.path.join(temp_dir_pk_upload, uploaded_pk_file.name)
                with open(public_key_file_path, "wb") as f:
                    f.write(uploaded_pk_file.getbuffer())
                st.info(f"Chave pública '{uploaded_pk_file.name}' carregada temporariamente.")

        default_output_name = ""
        if input_file_path:
            base_name = Path(input_file_path).stem # Pega o nome base sem a extensão
            default_output_name = f"{base_name}_version{count_file(input_file_path, '.enc.aes_rsa', ENCRYPT_FOLDER)}.enc.aes_rsa"
        output_filename = st.text_input("Nome do arquivo de saída", 
                                        value=default_output_name, 
                                        key="hybrid_output_enc")

        if st.button("Criptografar Híbrido", key="btn_hybrid_enc"):
            if input_file_path and public_key_file_path and output_filename:
                output_path = str(ENCRYPT_FOLDER / output_filename) # Converte Path para str
                try:
                    CryptographyHandler.hybrid_encrypt_file(input_file_path, public_key_file_path, output_path)
                    st.success(f"Arquivo criptografado hibridamente com sucesso em '{output_path}'!")
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Baixar Arquivo Híbrido Criptografado",
                            data=f.read(),
                            file_name=output_filename,
                            mime="application/octet-stream"
                        )
                except Exception as e:
                    st.error(f"Erro na criptografia híbrida: {e}\n{traceback.format_exc()}")
                finally:
                    if temp_dir_upload and Path(temp_dir_upload).exists():
                        try:
                            shutil.rmtree(temp_dir_upload)
                        except OSError as e:
                            st.warning(f"Não foi possível limpar o diretório temporário do arquivo de entrada: {e}")
                    if temp_dir_pk_upload and Path(temp_dir_pk_upload).exists():
                        try:
                            shutil.rmtree(temp_dir_pk_upload)
                        except OSError as e:
                            st.warning(f"Não foi possível limpar o diretório temporário da chave pública: {e}")
            else:
                st.warning("Por favor, selecione um arquivo de entrada, uma chave pública e forneça um nome de saída.")

    elif selected_operation == "Híbrida (AES + RSA) Descriptografar":
        st.header("Descriptografia Híbrida (AES + RSA)")
        st.subheader("Seleção da Chave Privada")
        key_file_source_dec = st.radio("Origem da Chave Privada:", ("Padrão", "Escolha do Usuário"), key="pk_source_dec")
        
        if key_file_source_dec == "Padrão":
            default_pr_files = {}
            for file_name in os.listdir(ENCRYPT_FOLDER):
                if file_name.endswith(".pem") and "private" in file_name:
                    default_pr_files[file_name] = str(ENCRYPT_FOLDER / file_name)
            if default_pr_files:
                selected_pr_name = st.selectbox("Selecione uma Chave Privada:", list(default_pr_files.keys()), key="selected_pr_dec") # Adicionado sufixo
                private_key_file_path = default_pr_files[selected_pr_name]
            else:
                st.warning("Nenhuma chave privada encontrada na pasta de criptografia.")
        else:
            uploaded_pr_file = st.file_uploader("Carregar chave privada (.pem)", type=["pem"], key="upload_pr_dec_file") # Adicionado sufixo
            if uploaded_pr_file:
                temp_dir_pr_upload = tempfile.mkdtemp(dir=TEMP_FOLDER) # Cria temp dir dentro de TEMP_FOLDER
                private_key_file_path = os.path.join(temp_dir_pr_upload, uploaded_pr_file.name)
                with open(private_key_file_path, "wb") as f:
                    f.write(uploaded_pr_file.getbuffer())
                st.info(f"Chave privada '{uploaded_pr_file.name}' carregada temporariamente.")

        default_output_name = ""
        if input_file_path:
            # Remove a extensão .enc.aes_rsa
            base_name_no_enc = Path(input_file_path).stem
            # Tenta remover _versionX
            default_output_name = get_original(base_name_no_enc, ".enc") # .enc é a extensão que AES+RSA usa no apendice_v1
            if not Path(default_output_name).suffix: # Se não tiver sufixo, adiciona .txt como padrão
                default_output_name += ".txt"
        
        output_filename = st.text_input("Nome do arquivo de saída", 
                                        value=default_output_name, 
                                        key="hybrid_output_dec")

        if st.button("Descriptografar Híbrido", key="btn_hybrid_dec"):
            if input_file_path and private_key_file_path and output_filename:
                with tempfile.TemporaryDirectory(dir=TEMP_FOLDER) as temp_dir_output: # Cria temp dir dentro de TEMP_FOLDER
                    output_path = os.path.join(temp_dir_output, output_filename)
                    try:
                        CryptographyHandler.hybrid_decrypt_file(input_file_path, private_key_file_path, output_path)
                        st.success(f"Arquivo descriptografado com sucesso!")
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Baixar Arquivo Descriptografado",
                                data=f.read(),
                                file_name=output_filename,
                                mime="application/octet-stream"
                            )
                    except Exception as e:
                        st.error(f"Erro na descriptografia híbrida: {e}\n{traceback.format_exc()}")
                    finally:
                        if temp_dir_upload and Path(temp_dir_upload).exists():
                            try:
                                shutil.rmtree(temp_dir_upload)
                            except OSError as e:
                                st.warning(f"Não foi possível limpar o diretório temporário do arquivo de entrada: {e}")
                        if temp_dir_pr_upload and Path(temp_dir_pr_upload).exists():
                            try:
                                shutil.rmtree(temp_dir_pr_upload)
                            except OSError as e:
                                st.warning(f"Não foi possível limpar o diretório temporário da chave privada: {e}")
            else:
                st.warning("Por favor, selecione um arquivo de entrada, uma chave privada e forneça um nome de saída.")

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
                st.write("Arquivo carregado com sucesso!")
                if st.button("Processar e Adicionar ao Banco de Dados (Etapa 2)"):
                    Functions.upload_csv_to_db(uploaded_csv_file_e2) # Reutiliza a função de upload CSV
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

    # --- Conteúdo da Etapa 3 (Compactação e Criptografia) ---
    elif main_option == "Etapa 3":
        st.header("🔐 Etapa 3: Compactação e Criptografia")
        st.write("Otimize o armazenamento e a segurança dos seus dados aplicando técnicas de compactação e criptografia.")
        st.markdown("---") # Separador visual

        # Novo seletor para escolher entre Compactação e Criptografia
        app_mode_crypto_comp = st.sidebar.selectbox(
            "Selecione a Funcionalidade", 
            ["Compactação", "Criptografia"],
            key="app_mode_crypto_comp_select" # Adicionado sufixo
        )

        if app_mode_crypto_comp == "Compactação":
            show_compression_ui()
        elif app_mode_crypto_comp == "Criptografia":
            show_encryption_ui()

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
                        key="download_aho_corasik"
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
        * **`cryptography`**: Biblioteca robusta para operações criptográficas (AES, RSA).
        * **`filelock`**: Para gerenciamento de concorrência e garantia da integridade do arquivo em operações multi-threaded/multi-processo.
        * **`pathlib`**: Módulo para manipulação de caminhos de arquivos e diretórios de forma orientada a objetos.
        * **`pandas`**: Essencial para manipulação e exibição de dados tabulares (DataFrames).
        * **`hashlib`**: Para geração de checksums (SHA-256) e MD5.
        * **`struct`**: Para empacotar/desempacotar dados binários no formato do banco de dados.
        * **`json`**: Para serialização/desserialização de dados de objetos.
        * **`logging`**: Para registro de informações, avisos e erros.
        * **`datetime`**: Para manipulação de datas e horas.
        * **`io`**: Para lidar com streams de dados de arquivos em memória.
        """)
        st.write("Versão: 1.0_20250708 Alpha 7c")
        st.markdown("---")
        st.info("Agradecemos seu interesse em nossa aplicação!")


if __name__ == "__main__":
    main()
