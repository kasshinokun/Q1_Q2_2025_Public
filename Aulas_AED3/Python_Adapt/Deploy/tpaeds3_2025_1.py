import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union, Callable, Iterator
import os
import struct
import threading
import hashlib
import json
import traceback
from datetime import datetime, date, time
from enum import Enum, auto
import re
import logging

# --- Configurações Iniciais e Logging (do DataObject_3.py) ---
DOCUMENTS_PATH = Path.home() / "DataDB"
DATA_FOLDER = DOCUMENTS_PATH / "Data"
LOG_FILE = DATA_FOLDER / 'traffic_accidents.log'

VALID_DATE_FORMATS = ('%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y',
                      '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y',
                      '%Y-%m-%d %I:%M:%S',
                      '%m-%d-%Y %I:%M:%S',
                      '%d-%m-%Y %I:%M:%S',
                      '%Y/%m/%d %I:%M:%S',
                      '%m/%d/%Y %I:%M:%S',
                      '%d/%m/%Y %I:%M:%S',
                      '%Y-%m-%d %I:%M:%S %p',
                      '%m-%d-%Y %I:%M:%S %p',
                      '%d-%m-%Y %I:%M:%S %p',
                      '%Y/%m/%d %I:%M:%S %p',
                      '%m/%d/%Y %I:%M:%S %p',
                      '%d/%m/%Y %I:%M:%S %p',
                      '%m/%d/%Y %I:%M:%S %p')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Enumerações e Definições de Campo (do DataObject_3.py) ---
class FieldType(Enum):
    STRING = auto()
    DATE = auto()
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    ENUM = auto()
    MULTI_ENUM = auto()

FIELD_DEFINITIONS = {
    'crash_date': {'type': FieldType.DATE, 'required': True},
    'default_datetime': {'type': FieldType.DATE, 'required': True, 'default': datetime.now().strftime('%m-%d-%Y %I:%M:%S %p')},
    'traffic_control_device': {'type': FieldType.ENUM, 'required': True, 'default': 'UNKNOWN', 'options': [
                    "TRAFFIC SIGNAL", "NO CONTROLS", "STOP SIGN/FLASHER", "UNKNOWN", "OTHER",
                    "PEDESTRIAN CROSSING SIGN", "OTHER WARNING SIGN", "YIELD", "FLASHING CONTROL SIGNAL",
                    "LANE USE MARKING", "OTHER REG. SIGN", "DELINEATORS", "SCHOOL ZONE",
                    "POLICE/FLAGMAN", "NO PASSING", "RR CROSSING SIGN", "RAILROAD CROSSING GATE",
                    "BICYCLE CROSSING SIGN", "OTHER RAILROAD CROSSING"]},
    'weather_condition': {'type': FieldType.ENUM, 'required': True, 'default': 'CLEAR', 'options': [
                    "CLEAR", "RAIN", "SNOW", "CLOUDY/OVERCAST", "UNKNOWN", "FOG/SMOKE/HAZE",
                    "BLOWING SNOW", "FREEZING RAIN/DRIZZLE", "OTHER", "SLEET/HAIL",
                    "SEVERE CROSS WIND GATE", "BLOWING SAND, SOIL, DIRT"]},
    'lighting_condition': {'type': FieldType.MULTI_ENUM, 'required': True, 'default': 'DAYLIGHT', 'options': ["DAYLIGHT", "DARKNESS, LIGHTED ROAD", "DUSK", "DARKNESS", "UNKNOWN", "DAWN"]},
    'first_crash_type': {'type': FieldType.ENUM, 'required': True, 'default': 'REAR END', 'options': [
                    "TURNING", "REAR END", "ANGLE", "FIXED OBJECT", "REAR TO FRONT",
                    "SIDESWIPE SAME DIRECTION", "SIDESWIPE OPPOSITE DIRECTION", "PEDALCYCLIST",
                    "PEDESTRIAN", "HEAD ON", "PARKED MOTOR VEHICLE", "OTHER NONCOLLISION",
                    "OVERTURNED", "OTHER OBJECT", "REAR TO SIDE", "ANIMAL", "TRAIN", "REAR TO REAR"]},
    'trafficway_type': {'type': FieldType.ENUM, 'required': True, 'default': 'NOT DIVIDED', 'options': [
                    "NOT DIVIDED", "FOUR WAY", "T-INTERSECTION", "DIVIDED - W/MEDIAN (NOT RAISED)",
                    "OTHER", "UNKNOWN INTERSECTION TYPE", "ONE-WAY", "RAMP", "TRAFFIC ROUTE",
                    "FIVE POINT, OR MORE", "DIVIDED - W/MEDIAN BARRIER", "UNKNOWN", "ALLEY",
                    "CENTER TURN LANE", "L-INTERSECTION", "DRIVEWAY", "Y-INTERSECTION",
                    "PARKING LOT", "ROUNDABOUT", "NOT REPORTED"]},
    'alignment': {'type': FieldType.ENUM, 'required': True, 'default': 'STRAIGHT AND LEVEL', 'options': ["STRAIGHT AND LEVEL", "CURVE, LEVEL", "STRAIGHT ON HILLCREST", "STRAIGHT ON GRADE", "CURVE ON GRADE", "CURVE ON HILLCREST"]},
    'roadway_surface_cond': {'type': FieldType.ENUM, 'required': True, 'default': 'DRY', 'options': ["UNKNOWN", "DRY", "WET", "SNOW OR SLUSH", "ICE", "OTHER", "SAND, MUD, DIRT"]},
    'road_defect': {'type': FieldType.ENUM, 'required': True, 'default': 'NO DEFECTS', 'options': ["UNKNOWN", "NO DEFECTS", "OTHER", "SHOULDER DEFECT", "WORN SURFACE", "DEBRIS ON ROADWAY", "RUT, HOLES"]},
    'crash_type': {'type': FieldType.MULTI_ENUM, 'required': True, 'default': 'NO INJURY / DRIVE AWAY', 'options': ['NO INJURY / DRIVE AWAY', 'INJURY', 'FATAL', 'PROPERTY DAMAGE', "INJURY AND TOW DUE TO CRASH / INJURY OR TOW DUE TO CRASH"]},
    'intersection_related_i': {'type': FieldType.BOOLEAN, 'default': False},
    'damage': {'type': FieldType.ENUM, 'required': True, 'default': '$500 OR LESS', 'options': ["$501 - $1,500", "OVER $1,500", "$500 OR LESS"]},
    'prim_contributory_cause': {'type': FieldType.ENUM, 'required': True, 'default': 'UNABLE TO DETERMINE', 'options': [
                    "UNABLE TO DETERMINE", "IMPROPER TURNING/NO SIGNAL", "FOLLOWING TOO CLOSELY",
                    "DRIVING SKILLS/KNOWLEDGE/EXPERIENCE", "IMPROPER BACKING", "FAILING TO YIELD RIGHT-OF-WAY",
                    "IMPROPER OVERTAKING/PASSING", "DRIVING ON WRONG SIDE/WRONG WAY", "IMPROPER LANE USAGE",
                    "NOT APPLICABLE", "FAILING TO REDUCE SPEED TO AVOID CRASH", "DISREGARDING TRAFFIC SIGNALS",
                    "WEATHER", "DISREGARDING STOP SIGN", "EQUIPMENT - VEHICLE CONDITION",
                    "OPERATING VEHICLE IN ERRATIC, RECKLESS, CARELESS, NEGLIGENT OR AGGRESSIVE MANNER",
                    "DISREGARDING OTHER TRAFFIC SIGNS", "TURNING RIGHT ON RED",
                    "VISION OBSCURED (SIGNS, TREE LIMBS, BUILDINGS, ETC.)",
                    "EVASIVE ACTION DUE TO ANIMAL, OBJECT, NONMOTORIST",
                    "UNDER THE INFLUENCE OF ALCOHOL/DRUGS (USE WHEN ARREST IS EFFECTED)",
                    "DISTRACTION - FROM OUTSIDE VEHICLE", "EXCEEDING SAFE SPEED FOR CONDITIONS",
                    "DISREGARDING ROAD MARKINGS", "ROAD ENGINEERING/SURFACE/MARKING DEFECTS",
                    "PHYSICAL CONDITION OF DRIVER", "DISTRACTION - FROM INSIDE VEHICLE",
                    "EXCEEDING AUTHORIZED SPEED LIMIT", "ROAD CONSTRUCTION/MAINTENANCE",
                    "DISTRACTION - OTHER ELECTRONIC DEVICE (NAVIGATION DEVICE, DVD PLAYER, ETC.)",
                    "ANIMAL", "HAD BEEN DRINKING (USE WHEN ARREST IS NOT MADE)",
                    "BICYCLE ADVANCING LEGALLY ON RED LIGHT", "CELL PHONE USE OTHER THAN TEXTING",
                    "RELATED TO BUS STOP", "TEXTING", "OBSTRUCTED CROSSWALKS", "DISREGARDING YIELD SIGN",
                    "MOTORCYCLE ADVANCING LEGALLY ON RED LIGHT", "PASSING STOPPED SCHOOL BUS"]},
    'num_units': {'type': FieldType.INTEGER, 'default': 1, 'min': 0, 'max': 999},
    'most_severe_injury': {'type': FieldType.MULTI_ENUM, 'default': 'NO INDICATION OF INJURY', 'options': ["NO INDICATION OF INJURY", "NONINCAPACITATING INJURY", "INCAPACITATING INJURY", "REPORTED, NOT EVIDENT", "FATAL"]},
    'injuries_total': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_fatal': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_incapacitating': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_non_incapacitating': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_reported_not_evident': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_no_indication': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'crash_hour': {'type': FieldType.INTEGER, 'default': 0, 'min': 0, 'max': 23},
    'crash_day_of_week': {'type': FieldType.INTEGER, 'default': 1, 'min': 1, 'max': 7},
    'crash_month': {'type': FieldType.INTEGER, 'default': 1, 'min': 1, 'max': 12}
}

FIELDS = list(FIELD_DEFINITIONS.keys())

# --- Exceções Personalizadas (do DataObject_3.py) ---
class DataValidationError(Exception):
    """Exceção personalizada para erros de validação de dados."""
    pass

class DatabaseError(Exception):
    """Exceção personalizada para operações de banco de dados."""
    pass

class LockAcquisitionError(Exception):
    """Exceção personalizada para falhas na aquisição de bloqueio."""
    pass

class FileLockError(Exception):
    """Exceção personalizada para operações de backup."""
    pass

class RecordNotFoundError(Exception):
    """Exceção personalizada quando um registro não é encontrado."""
    pass

class RecordExistsError(Exception):
    """Exceção personalizada quando um registro com o mesmo ID já existe."""
    pass

class BackupError(Exception):
    """Exceção personalizada para operações de backup."""
    pass

# --- Classe DataObject (do DataObject_3.py) ---
class DataObject:
    """
    Representa um registro de acidente de trânsito com validação e serialização aprimoradas.
    Pode ser inicializado a partir de uma lista de dados (ex: CSV) ou um dicionário.
    """
    
    def __init__(self, row_data: Optional[List[str]] = None, initial_data: Optional[Dict[str, Any]] = None):
        self._initialize_defaults()
        
        if row_data is not None:
            try:
                self._initialize_from_row(row_data)
            except Exception as e:
                logger.error(f"Erro ao inicializar DataObject a partir de row_data: {str(e)}\n{traceback.format_exc()}")
                raise DataValidationError(f"Dados inválidos de row_data: {str(e)}")
        elif initial_data is not None:
            try:
                self._initialize_from_dict(initial_data)
            except Exception as e:
                logger.error(f"Erro ao inicializar DataObject a partir de dicionário: {str(e)}\n{traceback.format_exc()}")
                raise DataValidationError(f"Dados inválidos de dicionário: {str(e)}")

    def _initialize_defaults(self):
        """Inicializa todos os campos com valores padrão apropriados para o tipo."""
        for field, definition in FIELD_DEFINITIONS.items():
            setattr(self, field, definition.get('default', None))
            if definition['type'] == FieldType.MULTI_ENUM and isinstance(getattr(self, field), str):
                setattr(self, field, [getattr(self, field)])

    def _initialize_from_row(self, row_data: List[str]):
        """
        Inicializa o objeto a partir de dados de linha CSV com conversão e validação de tipo aprimoradas.
        Lida com a derivação de 'crash_date' a partir de 'default_datetime'.
        """
        if len(row_data) != len(FIELDS):
            raise DataValidationError(f"Esperado {len(FIELDS)} campos, obtido {len(row_data)}")
        
        processed_data = [value.strip() if value and value.strip() else None for value in row_data]
        
        temp_data_storage = {}

        try:
            if 'default_datetime' in FIELDS:
                default_datetime_index = FIELDS.index('default_datetime')
                if default_datetime_index < len(processed_data) and processed_data[default_datetime_index] is not None:
                    value = processed_data[default_datetime_index]
                    try:
                        validated_date = self._validate_date(value)
                        temp_data_storage['default_datetime'] = validated_date
                        
                        crash_date_index = FIELDS.index('crash_date')
                        if crash_date_index >= len(processed_data) or processed_data[crash_date_index] is None:
                            try:
                                dt_obj = datetime.strptime(validated_date, '%Y-%m-%d')
                                temp_data_storage['crash_date'] = dt_obj.strftime('%Y-%m-%d')
                            except ValueError as e:
                                logger.error(f"Erro ao analisar default_datetime para derivação de crash_date: {e}")
                                raise DataValidationError(f"Erro ao derivar crash_date de default_datetime: {e}")
                        else:
                            temp_data_storage['crash_date'] = self._validate_date(processed_data[crash_date_index])

                    except DataValidationError as e:
                        logger.error(f"Erro ao processar default_datetime: {e}")
                        raise
                    except Exception as e:
                        logger.error(f"Erro inesperado ao processar default_datetime: {e}")
                        raise DataValidationError(f"Valor inválido para default_datetime: {e}")
                else:
                    default_val = FIELD_DEFINITIONS['default_datetime'].get('default')
                    temp_data_storage['default_datetime'] = default_val
                    
                    crash_date_index = FIELDS.index('crash_date')
                    if crash_date_index >= len(processed_data) or processed_data[crash_date_index] is None:
                         if default_val:
                            try:
                                parsed_dt = None
                                for fmt in VALID_DATE_FORMATS:
                                    try:
                                        parsed_dt = datetime.strptime(default_val, fmt)
                                        break
                                    except ValueError:
                                        continue
                                if parsed_dt:
                                    temp_data_storage['crash_date'] = parsed_dt.strftime('%Y-%m-%d')
                                else:
                                    logger.warning(f"Não foi possível analisar o valor padrão de default_datetime '{default_val}'. crash_date não será derivado.")
                            except Exception as e:
                                logger.error(f"Erro ao analisar o padrão de default_datetime para derivação de crash_date: {e}")
                                pass
            
            for i, field in enumerate(FIELDS):
                if field == 'crash_date' and 'crash_date' in temp_data_storage:
                    continue
                if field == 'default_datetime' and 'default_datetime' in temp_data_storage:
                    continue

                value = processed_data[i]
                definition = FIELD_DEFINITIONS[field]
                
                try:
                    if value is None and definition.get('required', False):
                        raise DataValidationError(f"Campo obrigatório {field} está faltando")
                    
                    if value is None:
                        temp_data_storage[field] = definition.get('default', None)
                        if definition['type'] == FieldType.MULTI_ENUM and isinstance(temp_data_storage[field], str):
                            setattr(self, field, [getattr(self, field)])
                        continue  
                    
                    if definition['type'] == FieldType.DATE:
                        temp_data_storage[field] = self._validate_date(value)
                    elif definition['type'] == FieldType.STRING:
                        temp_data_storage[field] = self._validate_string(value, field)
                    elif definition['type'] == FieldType.BOOLEAN:
                        temp_data_storage[field] = self._validate_boolean(value)
                    elif definition['type'] == FieldType.INTEGER:
                        temp_data_storage[field] = self._validate_integer(value, field, 
                                                                   definition.get('min'), 
                                                                   definition.get('max'))
                    elif definition['type'] == FieldType.FLOAT:
                        temp_data_storage[field] = self._validate_float(value, field, 
                                                                definition.get('min'))
                    elif definition['type'] == FieldType.ENUM:
                        options = definition.get('options', [])
                        if value not in options:
                            raise DataValidationError(f"Campo '{field}' deve ser um de {options} (atual: {value})")
                        temp_data_storage[field] = value
                    elif definition['type'] == FieldType.MULTI_ENUM:
                        options = definition.get('options', [])
                        parsed_list = self._parse_multi_enum_string(value, options)
                        if not parsed_list and definition.get('required', False):
                             raise DataValidationError(f"Campo MULTI_ENUM obrigatório {field} está vazio ou inválido.")
                        temp_data_storage[field] = parsed_list

                except DataValidationError as e:
                    logger.warning(f"Erro de validação para o campo {field}: {str(e)}")
                    raise
                except Exception as e:
                    logger.error(f"Erro inesperado ao processar o campo {field}: {str(e)}")
                    raise DataValidationError(f"Valor inválido para {field}: {str(e)}")
            
            for field in FIELDS:
                setattr(self, field, temp_data_storage.get(field))

            if not self.validate():
                raise DataValidationError("DataObject falhou na validação final após a inicialização do campo.")

        except Exception as e:
            logger.error(f"Erro de validação na inicialização do campo: {str(e)}\n{traceback.format_exc()}")
            raise DataValidationError(f"Validação do campo falhou: {str(e)}")

    def _initialize_from_dict(self, data_dict: Dict[str, Any]):
        """
        Inicializa o objeto a partir de um dicionário, tipicamente de desserialização ou dados de formulário.
        Lida com a derivação de 'crash_date' a partir de 'default_datetime'.
        """
        processed_data = {}

        if 'default_datetime' in data_dict:
            value = data_dict['default_datetime']
            if isinstance(value, date):
                processed_data['default_datetime'] = value.strftime('%Y-%m-%d')
            elif isinstance(value, str) and value:
                processed_data['default_datetime'] = self._validate_date(value)
            elif FIELD_DEFINITIONS['default_datetime'].get('required', False):
                raise DataValidationError(f"Campo obrigatório 'default_datetime' está faltando")
            else:
                processed_data['default_datetime'] = FIELD_DEFINITIONS['default_datetime'].get('default')

            if 'crash_date' not in data_dict or data_dict['crash_date'] is None:
                if processed_data.get('default_datetime'):
                    try:
                        dt_obj = datetime.strptime(processed_data['default_datetime'], '%Y-%m-%d')
                        processed_data['crash_date'] = dt_obj.strftime('%Y-%m-%d')
                    except ValueError as e:
                        logger.error(f"Erro ao analisar default_datetime para derivação de crash_date: {e}")
                        raise DataValidationError(f"Erro ao derivar crash_date de default_datetime: {e}")
            else:
                processed_data['crash_date'] = self._validate_date(data_dict['crash_date'])
        elif FIELD_DEFINITIONS['default_datetime'].get('required', False):
            raise DataValidationError(f"Campo obrigatório 'default_datetime' está faltando")
        else:
            default_val = FIELD_DEFINITIONS['default_datetime'].get('default')
            processed_data['default_datetime'] = default_val
            
            if 'crash_date' not in data_dict or data_dict['crash_date'] is None:
                if default_val:
                    try:
                        parsed_dt = None
                        for fmt in VALID_DATE_FORMATS:
                            try:
                                parsed_dt = datetime.strptime(default_val, fmt)
                                break
                            except ValueError:
                                continue
                        if parsed_dt:
                            processed_data['crash_date'] = parsed_dt.strftime('%Y-%m-%d')
                        else:
                            logger.warning(f"Não foi possível analisar o valor padrão de default_datetime '{default_val}'. crash_date não será derivado.")
                    except Exception as e:
                        logger.error(f"Erro ao analisar o padrão de default_datetime para derivação de crash_date: {e}")
                        pass
            else:
                processed_data['crash_date'] = self._validate_date(data_dict['crash_date'])


        for field, definition in FIELD_DEFINITIONS.items():
            if field in ['crash_date', 'default_datetime']:
                continue

            value = data_dict.get(field)
            
            if definition['type'] == FieldType.BOOLEAN:
                if value in (True, 'Y', 'true', '1'):
                    processed_data[field] = True
                elif value in (False, 'N', 'false', '0'):
                    processed_data[field] = False
                else:
                    processed_data[field] = definition.get('default', False)

            elif definition['type'] == FieldType.ENUM:
                options = definition.get('options', [])
                if value is not None and value not in options:
                    raise DataValidationError(f"Campo '{field}' deve ser um de {options} (atual: {value})")
                elif value is None:
                    processed_data[field] = definition.get('default')
                else:
                    processed_data[field] = value
            
            elif definition['type'] == FieldType.MULTI_ENUM:
                options = definition.get('options', [])
                if isinstance(value, str):
                    processed_data[field] = self._parse_multi_enum_string(value, options)
                elif isinstance(value, list):
                    for item in value:
                        if item not in options:
                            raise DataValidationError(f"Opção de enum inválida '{item}' no campo '{field}'. Deve ser um de {options}")
                    processed_data[field] = value
                elif value is None:
                    processed_data[field] = [definition.get('default')] if definition.get('default') else []
                else:
                    raise DataValidationError(f"Campo '{field}' deve ser uma string ou lista de strings para MULTI_ENUM.")
                
                if not processed_data[field] and definition.get('required', False):
                    raise DataValidationError(f"Campo MULTI_ENUM obrigatório {field} está vazio ou inválido.")
            
            else:
                if value is None and definition.get('required', False):
                    raise DataValidationError(f"Campo obrigatório {field} está faltando")
                
                if value is not None:
                    if definition['type'] == FieldType.INTEGER:
                        processed_data[field] = self._validate_integer(str(value), field, definition.get('min'), definition.get('max'))
                    elif definition['type'] == FieldType.FLOAT:
                        processed_data[field] = self._validate_float(str(value), field, definition.get('min'))
                    elif definition['type'] == FieldType.STRING:
                        processed_data[field] = self._validate_string(str(value), field)
                    elif definition['type'] == FieldType.DATE:
                        processed_data[field] = self._validate_date(value)
                else:
                    processed_data[field] = definition.get('default')
        
        for field in FIELDS:
            setattr(self, field, processed_data.get(field))

        if not self.validate():
            raise DataValidationError("DataObject inicializado a partir do dicionário falhou na validação final.")

    @staticmethod
    def _parse_multi_enum_string(value_str: str, options: List[str]) -> List[str]:
        """Analisa uma string contendo múltiplos valores de enum (separados por vírgula ou barra) em uma lista."""
        if not value_str:
            return []
        
        normalized_value_str = value_str.replace('/', ',')
        
        parts = [p.strip() for p in normalized_value_str.split(',') if p.strip()]
        
        valid_parts = []
        for part in parts:
            if part in options:
                valid_parts.append(part)
            else:
                raise DataValidationError(f"Opção de enum inválida '{part}'. Deve ser uma de {options}")
        return valid_parts

    @staticmethod
    def _validate_date(date_str: str) -> str:
        """Valida e padroniza o formato da data com verificações aprimoradas."""
        date_str = str(date_str).strip()
        if not date_str:
            return ""
        
        for fmt in VALID_DATE_FORMATS:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.date() > date.today():
                    raise DataValidationError("A data não pode estar no futuro")
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        raise DataValidationError(f"Formato de data inválido. Esperado um de: {', '.join(VALID_DATE_FORMATS)}")

    @staticmethod
    def _validate_string(value: str, field_name: str) -> str:
        """Valida campos de string com sanitização."""
        value = str(value).strip()
        if not value:
            return FIELD_DEFINITIONS[field_name].get('default', '')
        
        value = re.sub(r'[;\n\r\t]', ' ', value)
        return value[:255]

    @staticmethod
    def _validate_boolean(value: str) -> bool:
        """Valida campos booleanos."""
        value = str(value).strip().lower()
        return value in ('yes', 'y', 'true', '1', 't')

    @staticmethod
    def _validate_integer(value: str, field_name: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Valida campos inteiros com verificação de intervalo."""
        try:
            num = int(float(value)) if value is not None and value != '' else FIELD_DEFINITIONS[field_name].get('default', 0)
            
            if min_val is not None and num < min_val:
                raise DataValidationError(f"O valor deve ser ≥ {min_val}")
            if max_val is not None and num > max_val:
                raise DataValidationError(f"O valor deve ser ≤ {max_val}")
            
            return num
        except (ValueError, TypeError):
            raise DataValidationError("Valor inteiro inválido")

    @staticmethod
    def _validate_float(value: str, field_name: str, min_val: Optional[float] = None) -> float:
        """Valida campos float com verificação de intervalo."""
        try:
            num = float(value) if value is not None and value != '' else FIELD_DEFINITIONS[field_name].get('default', 0.0)
            
            if min_val is not None and num < min_val:
                raise DataValidationError(f"O valor deve ser ≥ {min_val}")
            
            return round(num, 2)
        except (ValueError, TypeError):
            raise DataValidationError("Valor numérico inválido")

    def to_bytes(self) -> bytes:
        """Serializa o objeto para bytes usando JSON com tratamento de erros."""
        try:
            data_dict = {attr: getattr(self, attr) for attr in FIELDS}
            for key, value in data_dict.items():
                if isinstance(value, date):
                    data_dict[key] = value.isoformat()
                elif FIELD_DEFINITIONS[key]['type'] == FieldType.MULTI_ENUM and isinstance(value, list):
                    data_dict[key] = ",".join(value)
            return json.dumps(data_dict, sort_keys=True).encode('utf-8')
        except Exception as e:
            logger.error(f"Erro de serialização: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Falha ao serializar o registro")

    @classmethod
    def from_bytes(cls, byte_data: bytes) -> 'DataObject':
        """Desserializa o objeto de bytes com tratamento de erros abrangente."""
        try:
            if not byte_data:
                raise ValueError("Dados em bytes vazios")
                
            data_dict = json.loads(byte_data.decode('utf-8'))
            obj = cls(initial_data=data_dict)
            
            if not obj.validate():
                raise DataValidationError("Objeto desserializado falhou na validação")
            
            return obj
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Erro de decodificação JSON: {str(e)}")
            raise DatabaseError("Formato de dados inválido")
        except Exception as e:
            logger.error(f"Erro de desserialização: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Falha ao desserializar o registro")

    def validate(self) -> bool:
        """Validação abrangente dos campos do objeto."""
        try:
            for field, definition in FIELD_DEFINITIONS.items():
                value = getattr(self, field)
                
                if definition.get('required', False):
                    if value is None or (isinstance(value, str) and not value) or \
                       (isinstance(value, list) and not value):
                        raise DataValidationError(f"Campo obrigatório '{field}' está vazio ou faltando")
                
                if value is None:
                    continue
                
                if definition['type'] == FieldType.INTEGER:
                    if not isinstance(value, int):
                        raise DataValidationError(f"Campo '{field}' deve ser um inteiro (atual: {type(value).__name__})")
                    if 'min' in definition and value < definition['min']:
                        raise DataValidationError(f"Campo '{field}' deve ser ≥ {definition['min']} (atual: {value})")
                    if 'max' in definition and value > definition['max']:
                        raise DataValidationError(f"Campo '{field}' deve ser ≤ {definition['max']} (atual: {value})")
                
                elif definition['type'] == FieldType.FLOAT:
                    if not isinstance(value, (int, float)):
                        raise DataValidationError(f"Campo '{field}' deve ser um número (atual: {type(value).__name__})")
                    if 'min' in definition and value < definition['min']:
                        raise DataValidationError(f"Campo '{field}' deve ser ≥ {definition['min']} (atual: {value})")
                
                elif definition['type'] == FieldType.DATE:
                    try:
                        parsed_dt = None
                        for fmt in VALID_DATE_FORMATS:
                            try:
                                parsed_dt = datetime.strptime(value, fmt)
                                break
                            except ValueError:
                                continue
                        if parsed_dt is None:
                            raise ValueError
                    except ValueError:
                        raise DataValidationError(f"Campo '{field}' deve ser uma data válida em um dos formatos {VALID_DATE_FORMATS} (atual: {value})")
                
                elif definition['type'] == FieldType.BOOLEAN:
                    if not isinstance(value, bool):
                        raise DataValidationError(f"Campo '{field}' deve ser um booleano (atual: {type(value).__name__})")
                
                elif definition['type'] == FieldType.STRING:
                    if not isinstance(value, str):
                        raise DataValidationError(f"Campo '{field}' deve ser uma string (atual: {type(value).__name__})")
                
                elif definition['type'] == FieldType.ENUM:
                    if not isinstance(value, str):
                        raise DataValidationError(f"Campo '{field}' deve ser uma string (atual: {type(value).__name__})")
                    options = definition.get('options', [])
                    if value not in options:
                        raise DataValidationError(f"Campo '{field}' deve ser um de {options} (atual: {value})")
                
                elif definition['type'] == FieldType.MULTI_ENUM:
                    if not isinstance(value, list):
                        raise DataValidationError(f"Campo '{field}' deve ser uma lista (atual: {type(value).__name__})")
                    options = definition.get('options', [])
                    for item in value:
                        if not isinstance(item, str):
                            raise DataValidationError(f"Itens no campo '{field}' devem ser strings (atual: {type(item).__name__})")
                        if item not in options:
                            raise DataValidationError(f"Opção de enum inválida '{item}' no campo '{field}'. Deve ser uma de {options}")

            return True
        except DataValidationError as e:
            logger.warning(f"Validação falhou para DataObject: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro de validação inesperado para DataObject: {str(e)}\n{traceback.format_exc()}")
            return False
        
    def __str__(self) -> str:
        """Representação legível do objeto."""
        lighting_cond_str = ", ".join(self.lighting_condition) if isinstance(self.lighting_condition, list) else str(self.lighting_condition)
        crash_type_str = ", ".join(self.crash_type) if isinstance(self.crash_type, list) else str(self.crash_type)
        most_severe_injury_str = ", ".join(self.most_severe_injury) if isinstance(self.most_severe_injury, list) else str(self.most_severe_injury)

        return (
            f"DataObject(crash_date='{self.crash_date}', "
            f"default_datetime='{self.default_datetime}', "
            f"traffic_control_device='{self.traffic_control_device}', "
            f"weather_condition='{self.weather_condition}', "
            f"lighting_condition='{lighting_cond_str}', "
            f"first_crash_type='{self.first_crash_type}', "
            f"num_units={self.num_units}, "
            f"crash_hour={self.crash_hour})"
        )

    def __repr__(self) -> str:
        """Representação oficial em string do objeto."""
        lighting_cond_repr = f"'{', '.join(self.lighting_condition)}'" if isinstance(self.lighting_condition, list) else repr(self.lighting_condition)
        crash_type_repr = f"'{', '.join(self.crash_type)}'" if isinstance(self.crash_type, list) else repr(self.crash_type)
        most_severe_injury_repr = f"'{', '.join(self.most_severe_injury)}'" if isinstance(self.most_severe_injury, list) else repr(self.most_severe_injury)

        return (
            f"DataObject(\n"
            f"  crash_date='{self.crash_date}',\n"
            f"  default_datetime='{self.default_datetime}',\n"
            f"  traffic_control_device='{self.traffic_control_device}',\n"
            f"  weather_condition='{self.weather_condition}',\n"
            f"  lighting_condition={lighting_cond_repr},\n"
            f"  first_crash_type='{self.first_crash_type}',\n"
            f"  trafficway_type='{self.trafficway_type}',\n"
            f"  alignment='{self.alignment}',\n"
            f"  roadway_surface_cond='{self.roadway_surface_cond}',\n"
            f"  road_defect='{self.road_defect}',\n"
            f"  crash_type={crash_type_repr},\n"
            f"  intersection_related_i={self.intersection_related_i},\n"
            f"  damage='{self.damage}',\n"
            f"  prim_contributory_cause='{self.prim_contributory_cause}',\n"
            f"  num_units={self.num_units},\n"
            f"  most_severe_injury={most_severe_injury_repr},\n"
            f"  injuries_total={self.injuries_total},\n"
            f"  injuries_fatal={self.injuries_fatal},\n"
            f"  injuries_incapacitating={self.injuries_incapacitating},\n"
            f"  injuries_non_incapacitating={self.injuries_non_incapacitating},\n"
            f"  injuries_reported_not_evident={self.injuries_reported_not_evident},\n"
            f"  injuries_no_indication={self.injuries_no_indication},\n"
            f"  crash_hour={self.crash_hour},\n"
            f"  crash_day_of_week={self.crash_day_of_week},\n"
            f"  crash_month={self.crash_month}\n"
            f")"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto para uma representação de dicionário."""
        data_dict = {
            'crash_date': self.crash_date,
            'default_datetime': self.default_datetime,
            'traffic_control_device': self.traffic_control_device,
            'weather_condition': self.weather_condition,
            'lighting_condition': self.lighting_condition,
            'first_crash_type': self.first_crash_type,
            'trafficway_type': self.trafficway_type,
            'alignment': self.alignment,
            'roadway_surface_cond': self.roadway_surface_cond,
            'road_defect': self.road_defect,
            'crash_type': self.crash_type,
            'intersection_related_i': self.intersection_related_i,
            'damage': self.damage,
            'prim_contributory_cause': self.prim_contributory_cause,
            'num_units': self.num_units,
            'most_severe_injury': self.most_severe_injury,
            'injuries_total': self.injuries_total,
            'injuries_fatal': self.injuries_fatal,
            'injuries_incapacitating': self.injuries_incapacitating,
            'injuries_non_incapacitating': self.injuries_non_incapacitating,
            'injuries_reported_not_evident': self.injuries_reported_not_evident,
            'injuries_no_indication': self.injuries_no_indication,
            'crash_hour': self.crash_hour,
            'crash_day_of_week': self.crash_day_of_week,
            'crash_month': self.crash_month
        }
        for field in ['lighting_condition', 'crash_type', 'most_severe_injury']:
            if FIELD_DEFINITIONS[field]['type'] == FieldType.MULTI_ENUM and isinstance(data_dict[field], list):
                data_dict[field] = ",".join(data_dict[field])

        return data_dict

    @staticmethod
    def validate_dict(data: Dict[str, Any]) -> bool:
        """Valida se um dicionário contém todos os campos obrigatórios com os tipos corretos."""
        required_fields = {
            'crash_date': str, 'default_datetime': str, 'traffic_control_device': str,
            'weather_condition': str, 'lighting_condition': (str, list),
            'first_crash_type': str, 'trafficway_type': str, 'alignment': str,
            'roadway_surface_cond': str, 'road_defect': str, 'crash_type': (str, list),
            'intersection_related_i': bool, 'damage': str, 'prim_contributory_cause': str,
            'num_units': int, 'most_severe_injury': (str, list),
            'injuries_total': (float, int), 'injuries_fatal': (float, int),
            'injuries_incapacitating': (float, int), 'injuries_non_incapacitating': (float, int),
            'injuries_reported_not_evident': (float, int), 'injuries_no_indication': (float, int),
            'crash_hour': int, 'crash_day_of_week': int, 'crash_month': int
        }

        if not all(field in data for field in required_fields):
            logger.warning(f"Campos obrigatórios faltando: {set(required_fields.keys()) - set(data.keys())}")
            return False

        for field, expected_type in required_fields.items():
            value = data[field]
            
            if isinstance(expected_type, tuple):
                if not isinstance(value, expected_type):
                    logger.warning(f"Campo '{field}' tem tipo incorreto. Esperado um de {expected_type}, obtido {type(value)}")
                    return False
            else:
                if not isinstance(value, expected_type):
                    logger.warning(f"Campo '{field}' tem tipo incorreto. Esperado {expected_type}, obtido {type(value)}")
                    return False
            
            if field in FIELD_DEFINITIONS and FIELD_DEFINITIONS[field]['type'] == FieldType.ENUM:
                options = FIELD_DEFINITIONS[field].get('options', [])
                if value not in options:
                    logger.warning(f"Campo '{field}' tem valor de enum inválido. Esperado um de {options}, obtido '{value}'")
                    return False
            
            elif field in FIELD_DEFINITIONS and FIELD_DEFINITIONS[field]['type'] == FieldType.MULTI_ENUM:
                options = FIELD_DEFINITIONS[field].get('options', [])
                if isinstance(value, str):
                    try:
                        parsed_list = DataObject._parse_multi_enum_string(value, options)
                    except DataValidationError as e:
                        logger.warning(f"Erro de validação para campo MULTI_ENUM '{field}': {str(e)}")
                        return False
                elif isinstance(value, list):
                    for item in value:
                        if not isinstance(item, str) or item not in options:
                            logger.warning(f"Campo '{field}' contém item inválido '{item}'. Esperado string de {options}.")
                            return False
                else:
                    logger.warning(f"Campo '{field}' tem tipo incorreto para MULTI_ENUM. Esperado string ou lista, obtido {type(value)}")
                    return False

        date_fields = ['crash_date', 'default_datetime']
        for field in date_fields:
            if field in data and isinstance(data[field], str):
                try:
                    parsed = False
                    for fmt in VALID_DATE_FORMATS:
                        try:
                            datetime.strptime(data[field], fmt)
                            parsed = True
                            break
                        except ValueError:
                            continue
                    if not parsed:
                        logger.warning(f"Campo '{field}' tem formato de data inválido: '{data[field]}'. Esperado um de: {', '.join(VALID_DATE_FORMATS)}")
                        return False
                except (TypeError, AttributeError):
                    logger.warning(f"Campo '{field}' não é uma string para validação de data: {type(data[field])}")
                    return False
            elif field in data and data[field] is not None:
                logger.warning(f"Campo '{field}' não é uma string para validação de data: {type(data[field])}")
                return False

        return True

# --- Constantes de Estrutura de Arquivo (do DataObject_3.py) ---
DB_HEADER_FORMAT = '>I'
DB_HEADER_SIZE_BYTES = struct.calcsize(DB_HEADER_FORMAT)

RECORD_ID_FORMAT = '>I'
VALIDATOR_FORMAT = '?'
DICT_SIZE_FORMAT = '>I'

RECORD_METADATA_SIZE_BYTES = struct.calcsize(RECORD_ID_FORMAT) + \
                             struct.calcsize(VALIDATOR_FORMAT) + \
                             struct.calcsize(DICT_SIZE_FORMAT)

INDEX_HEADER_FORMAT = '>I'
INDEX_HEADER_SIZE_BYTES = struct.calcsize(INDEX_HEADER_FORMAT)

INDEX_ENTRY_ID_FORMAT = '>I'
INDEX_RECORD_ID_FORMAT = '>I'
INDEX_VALIDATOR_FORMAT = '?'
CHECKSUM_FORMAT = '8s'
OFFSET_FORMAT = '>Q'

# CORREÇÃO: Definindo a string de formato diretamente para evitar potenciais problemas de concatenação
INDEX_ENTRY_FORMAT_STRING = ">II?8sQ"
INDEX_ENTRY_SIZE_BYTES = struct.calcsize(INDEX_ENTRY_FORMAT_STRING)

# --- Classe IndexDB (do DataObject_3.py) ---
class IndexDB:
    """
    Gerencia um arquivo de índice (.idx) para registros TrafficAccidentsDB.
    O índice armazena [index_entry_id][record_id][is_valid][checksum][offset].
    Ele mantém um mapa na memória da última posição válida e checksum para cada record_id.
    """
    def __init__(self, index_file_name: str = "traffic_accidents.idx"):
        self.index_path = DATA_FOLDER / index_file_name
        self._next_index_entry_id = 1
        self._lock = threading.Lock()
        self._index_map: Dict[int, Dict[str, Any]] = {}

        self._initialize_index_file()

    def _initialize_index_file(self):
        """Inicializa o arquivo de índice."""
        with self._lock:
            if not self.index_path.parent.exists():
                self.index_path.parent.mkdir(parents=True)

            if not self.index_path.exists() or os.path.getsize(self.index_path) == 0:
                logger.info(f"Arquivo de índice '{self.index_path}' não encontrado ou vazio. Inicializando novo índice.")
                self._next_index_entry_id = 1
                self._write_header()
            else:
                self._read_header_and_load_map()

    def _read_header_and_load_map(self):
        """Lê o cabeçalho e carrega todas as entradas de índice no mapa em memória."""
        self._index_map = {}
        self._next_index_entry_id = 1

        try:
            with open(self.index_path, 'rb') as f:
                header_bytes = f.read(INDEX_HEADER_SIZE_BYTES)
                if len(header_bytes) < INDEX_HEADER_SIZE_BYTES:
                    logger.warning(f"Cabeçalho do índice incompleto em '{self.index_path}'. Reiniciando índice.")
                    return

                self._next_index_entry_id = struct.unpack(INDEX_HEADER_FORMAT, header_bytes)[0]
                
                max_index_entry_id_in_file = 0
                
                while True:
                    entry_bytes = f.read(INDEX_ENTRY_SIZE_BYTES)
                    if not entry_bytes:
                        break
                    if len(entry_bytes) < INDEX_ENTRY_SIZE_BYTES:
                        logger.warning(f"Entrada de índice incompleta encontrada no byte {f.tell() - len(entry_bytes)}. O índice pode estar corrompido. Interrompendo a leitura.")
                        break

                    try:
                        index_entry_id, record_id, is_valid, checksum_bytes, offset = struct.unpack(INDEX_ENTRY_FORMAT_STRING, entry_bytes)
                        
                        max_index_entry_id_in_file = max(max_index_entry_id_in_file, index_entry_id)

                        if is_valid:
                            self._index_map[record_id] = {
                                'index_entry_id': index_entry_id,
                                'offset': offset,
                                'checksum': checksum_bytes.decode('ascii')
                            }
                        else:
                            if record_id in self._index_map and self._index_map[record_id]['index_entry_id'] == index_entry_id:
                                del self._index_map[record_id]
                                
                    except struct.error as e:
                        logger.error(f"Erro ao desempacotar entrada de índice no offset {f.tell() - INDEX_ENTRY_SIZE_BYTES}: {e}. Pulando entrada corrompida.")
                        break
                
                self._next_index_entry_id = max(self._next_index_entry_id, max_index_entry_id_in_file + 1)
                
                logger.info(f"Índice carregado. Registros válidos no mapa: {len(self._index_map)}, Próximo ID de entrada do índice: {self._next_index_entry_id}")

        except FileNotFoundError:
            logger.error(f"Tentativa de ler o índice de um arquivo não existente: {self.index_path}.")
            self._next_index_entry_id = 1
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado ao carregar o índice: {e}\n{traceback.format_exc()}")
            self._next_index_entry_id = 1
            self._write_header()

    def _write_header(self):
        """Escreve o cabeçalho no início do arquivo de índice."""
        header_data = struct.pack(INDEX_HEADER_FORMAT, self._next_index_entry_id)
        with open(self.index_path, 'r+b' if self.index_path.exists() else 'wb') as f:
            f.seek(0)
            f.write(header_data)
            f.flush()

    def add_entry(self, record_id: int, offset: int, data_bytes: bytes):
        """
        Adiciona uma nova entrada de índice para um registro.
        Isso atualiza o mapa em memória e anexa ao arquivo de índice.
        """
        with self._lock:
            self._read_header_and_load_map()

            index_entry_id = self._next_index_entry_id
            checksum = hashlib.md5(data_bytes).hexdigest()[:8]

            entry_data = struct.pack(INDEX_ENTRY_FORMAT_STRING,
                                     index_entry_id,
                                     record_id,
                                     True,
                                     checksum.encode('ascii'),
                                     offset)
            
            with open(self.index_path, 'ab') as f:
                f.write(entry_data)
                f.flush()

            self._index_map[record_id] = {
                'index_entry_id': index_entry_id,
                'offset': offset,
                'checksum': checksum
            }

            self._next_index_entry_id += 1
            self._write_header()

            logger.info(f"Entrada de índice para record_id {record_id} (index_entry_id {index_entry_id}) adicionada no offset {offset}.")

    def get_offset_and_checksum(self, record_id: int) -> Optional[Tuple[int, str]]:
        """
        Recupera o offset e o checksum para um dado record_id do índice.
        Retorna (offset, checksum_string) se encontrado, caso contrário None.
        """
        with self._lock:
            self._read_header_and_load_map()
            entry = self._index_map.get(record_id)
            if entry:
                logger.info(f"Entrada de índice encontrada para record_id {record_id}: offset={entry['offset']}, checksum={entry['checksum']}.")
                return entry['offset'], entry['checksum']
            logger.warning(f"Nenhuma entrada de índice válida encontrada para record_id {record_id}.")
            return None

    def delete_entry(self, record_id: int):
        """
        Marca uma entrada de índice como inválida anexando uma nova entrada inválida para o record_id.
        Esta é uma exclusão lógica do ponto de vista do índice.
        """
        with self._lock:
            self._read_header_and_load_map()

            if record_id not in self._index_map:
                logger.warning(f"Tentativa de excluir entrada de índice para record_id {record_id}, mas ela não existe no mapa de índice (ou já foi invalidada).")
                return

            index_entry_id = self._next_index_entry_id
            last_known_info = self._index_map[record_id]
            checksum = last_known_info['checksum']
            offset = last_known_info['offset']

            entry_data = struct.pack(INDEX_ENTRY_FORMAT_STRING,
                                     index_entry_id,
                                     record_id,
                                     False,
                                     checksum.encode('ascii'),
                                     offset)
            
            with open(self.index_path, 'ab') as f:
                f.write(entry_data)
                f.flush()

            del self._index_map[record_id]

            self._next_index_entry_id += 1
            self._write_header()

            logger.info(f"Entrada de índice para record_id {record_id} marcada como excluída (index_entry_id {index_entry_id}).")

# --- Classe TrafficAccidentsDB (do DataObject_3.py) ---
class TrafficAccidentsDB:
    """
    Gerencia o salvamento e carregamento de instâncias DataObject de/para um arquivo de banco de dados binário.
    """
    def __init__(self, db_file_name: str = "traffic_accidents.db", index_db: Optional['IndexDB'] = None):
        self.db_path = DATA_FOLDER / db_file_name
        self._next_record_id = 1
        self._lock = threading.Lock()
        self.index_db = index_db

        self._initialize_db_file()

    def _initialize_db_file(self):
        """Inicializa o arquivo do banco de dados."""
        with self._lock:
            if not self.db_path.parent.exists():
                self.db_path.parent.mkdir(parents=True)

            if not self.db_path.exists() or os.path.getsize(self.db_path) == 0:
                logger.info(f"Arquivo do banco de dados '{self.db_path}' não encontrado ou vazio. Inicializando novo banco de dados.")
                self._next_record_id = 1
                self._write_header()
            else:
                self._read_header()

    def _read_header(self):
        """Lê o cabeçalho do início do arquivo do banco de dados."""
        try:
            with open(self.db_path, 'rb') as f:
                header_bytes = f.read(DB_HEADER_SIZE_BYTES)
                if len(header_bytes) < DB_HEADER_SIZE_BYTES:
                    logger.warning(f"Cabeçalho do banco de dados incompleto em '{self.db_path}'. Reinicializando.")
                    self._next_record_id = 1
                    return

                self._next_record_id = struct.unpack(DB_HEADER_FORMAT, header_bytes)[0]
                logger.info(f"Cabeçalho do banco de dados lido: next_record_id={self._next_record_id}")
        except FileNotFoundError:
            logger.error(f"Tentativa de ler o cabeçalho de um arquivo não existente: {self.db_path}.")
            self._next_record_id = 1
        except struct.error as e:
            logger.error(f"Erro ao desempacotar o cabeçalho do banco de dados: {e}. O arquivo pode estar corrompido. Reinicializando.")
            self._next_record_id = 1
            self._write_header()

    def _write_header(self):
        """Escreve o cabeçalho no início do arquivo do banco de dados."""
        header_data = struct.pack(DB_HEADER_FORMAT, self._next_record_id)
        with open(self.db_path, 'r+b' if self.db_path.exists() else 'wb') as f:
            f.seek(0)
            f.write(header_data)
            f.flush()

    def save_record(self, data_object: DataObject) -> int:
        """
        Salva uma instância DataObject no arquivo do banco de dados.
        Retorna o ID do registro salvo.
        """
        with self._lock:
            self._read_header()
            
            record_id = self._next_record_id
            
            try:
                data_bytes = data_object.to_bytes()
            except Exception as e:
                logger.error(f"Falha ao serializar DataObject: {e}")
                raise DatabaseError(f"Falha ao serializar DataObject: {e}")

            dict_size = len(data_bytes)
            
            record_metadata = struct.pack(RECORD_ID_FORMAT + VALIDATOR_FORMAT + DICT_SIZE_FORMAT,
                                            record_id, True, dict_size)
            
            with open(self.db_path, 'ab') as f:
                start_offset = f.tell()
                f.write(record_metadata)
                f.write(data_bytes)
                f.flush()

            self._next_record_id += 1
            self._write_header()

            logger.info(f"Registro com ID {record_id} salvo com sucesso no offset {start_offset}.")

            if self.index_db:
                self.index_db.add_entry(record_id, start_offset, data_bytes)

            return record_id

    def load_all_records(self) -> List[DataObject]:
        """Carrega todas as instâncias DataObject válidas do arquivo do banco de dados."""
        records = []
        with self._lock:
            try:
                with open(self.db_path, 'rb') as f:
                    f.seek(DB_HEADER_SIZE_BYTES)

                    while True:
                        metadata_bytes = f.read(RECORD_METADATA_SIZE_BYTES)
                        if not metadata_bytes:
                            break
                        
                        if len(metadata_bytes) < RECORD_METADATA_SIZE_BYTES:
                            logger.warning("Metadados de registro incompletos encontrados durante load_all_records. Possível corrupção de arquivo. Interrompendo a leitura.")
                            break

                        try:
                            rec_id, validator, dict_size = struct.unpack(RECORD_ID_FORMAT + VALIDATOR_FORMAT + DICT_SIZE_FORMAT, metadata_bytes)
                        except struct.error as e:
                            logger.error(f"Erro ao desempacotar metadados de registro: {e}. Pulando registro potencialmente corrompido.")
                            break
                        
                        if not validator:
                            logger.info(f"O registro ID {rec_id} tem validador inválido. Pulando os dados deste registro.")
                            f.seek(dict_size, os.SEEK_CUR)
                            continue

                        data_bytes = f.read(dict_size)
                        if len(data_bytes) < dict_size:
                            logger.warning(f"Dados incompletos para o registro ID {rec_id}. Possível corrupção de arquivo. Interrompendo a leitura.")
                            break
                        
                        try:
                            data_object = DataObject.from_bytes(data_bytes)
                            setattr(data_object, 'record_id', rec_id)
                            records.append(data_object)
                        except (DataValidationError, DatabaseError) as e:
                            logger.error(f"Falha ao desserializar o registro ID {rec_id}: {e}. Pulando.")
                            pass

            except FileNotFoundError:
                logger.error(f"Arquivo do banco de dados não encontrado: {self.db_path}")
            except Exception as e:
                logger.error(f"Ocorreu um erro inesperado ao carregar registros: {e}\n{traceback.format_exc()}")
                raise DatabaseError(f"Erro ao carregar registros: {e}")

        logger.info(f"Carregado {len(records)} registros do banco de dados.")
        return records

    def get_record_by_id(self, target_record_id: int) -> Optional[DataObject]:
        """
        Recupera uma instância DataObject pelo seu ID de registro.
        Tenta usar o índice se disponível; caso contrário, executa uma varredura sequencial.
        """
        with self._lock:
            if self.index_db:
                index_info = self.index_db.get_offset_and_checksum(target_record_id)
                if index_info:
                    offset, expected_checksum = index_info
                    try:
                        with open(self.db_path, 'rb') as f:
                            f.seek(offset)
                            metadata_bytes = f.read(RECORD_METADATA_SIZE_BYTES)
                            if len(metadata_bytes) < RECORD_METADATA_SIZE_BYTES:
                                logger.warning(f"Metadados de registro incompletos no offset {offset} para o registro ID {target_record_id}. O índice pode estar dessincronizado ou o DB corrompido.")
                                pass
                            else:
                                rec_id, validator, dict_size = struct.unpack(RECORD_ID_FORMAT + VALIDATOR_FORMAT + DICT_SIZE_FORMAT, metadata_bytes)
                                
                                if rec_id != target_record_id:
                                    logger.error(f"Incompatibilidade de índice: Esperado record_id {target_record_id} no offset {offset}, mas encontrado {rec_id}. Índice corrompido ou dessincronizado. Voltando à varredura sequencial.")
                                    pass

                                elif not validator:
                                    logger.warning(f"O registro ID {rec_id} no offset {offset} está marcado como inválido no DB. Não é possível recuperá-lo via índice. Voltando à varredura sequencial.")
                                    pass

                                else:
                                    data_bytes = f.read(dict_size)
                                    if len(data_bytes) < dict_size:
                                        logger.warning(f"Dados incompletos para o registro ID {target_record_id} no offset {offset}. Possível corrupção de arquivo. Voltando à varredura sequencial.")
                                        pass
                                    else:
                                        actual_checksum = hashlib.md5(data_bytes).hexdigest()[:8]
                                        if actual_checksum != expected_checksum:
                                            logger.warning(f"Incompatibilidade de checksum para o registro ID {target_record_id}. Esperado {expected_checksum}, obtido {actual_checksum}. Os dados podem estar corrompidos. Voltando à varredura sequencial.")
                                            pass
                                        else:
                                            try:
                                                data_object = DataObject.from_bytes(data_bytes)
                                                setattr(data_object, 'record_id', rec_id)
                                                logger.info(f"Registro ID {target_record_id} encontrado e carregado usando o índice.")
                                                return data_object
                                            except (DataValidationError, DatabaseError) as e:
                                                logger.error(f"Falha ao desserializar o registro ID {target_record_id} do offset {offset}: {e}. Voltando à varredura sequencial.")
                                                pass

                    except FileNotFoundError:
                        logger.error(f"Arquivo do banco de dados não encontrado: {self.db_path}.")
                        pass
                    except Exception as e:
                        logger.error(f"Ocorreu um erro inesperado ao recuperar o registro por ID do índice: {e}\n{traceback.format_exc()}. Voltando à varredura sequencial.")
                        pass
        
        logger.info(f"Executando varredura sequencial para o registro ID {target_record_id}.")
        try:
            with open(self.db_path, 'rb') as f:
                f.seek(DB_HEADER_SIZE_BYTES)

                while True:
                    metadata_start_pos = f.tell()
                    metadata_bytes = f.read(RECORD_METADATA_SIZE_BYTES)
                    if not metadata_bytes:
                        break
                    
                    if len(metadata_bytes) < RECORD_METADATA_SIZE_BYTES:
                        logger.warning("Metadados de registro incompletos durante a varredura sequencial. Possível corrupção de arquivo. Interrompendo a leitura.")
                        break

                    try:
                        rec_id, validator, dict_size = struct.unpack(RECORD_ID_FORMAT + VALIDATOR_FORMAT + DICT_SIZE_FORMAT, metadata_bytes)
                    except struct.error as e:
                        logger.error(f"Erro ao desempacotar metadados de registro durante a varredura sequencial: {e}. Pulando registro potencialmente corrompido.")
                        break
                    
                    if validator and rec_id == target_record_id:
                        data_bytes = f.read(dict_size)
                        if len(data_bytes) < dict_size:
                            logger.warning(f"Dados incompletos para o registro ID {target_record_id} durante a varredura sequencial. Possível corrupção de arquivo.")
                            break
                        
                        try:
                            data_object = DataObject.from_bytes(data_bytes)
                            setattr(data_object, 'record_id', rec_id)
                            logger.info(f"Registro ID {target_record_id} encontrado e carregado via varredura sequencial.")
                            return data_object
                        except (DataValidationError, DatabaseError) as e:
                            logger.error(f"Falha ao desserializar o registro ID {rec_id} durante a varredura sequencial: {e}. Pulando.")
                            pass
                    else:
                        f.seek(dict_size, os.SEEK_CUR)

        except FileNotFoundError:
            logger.error(f"Arquivo do banco de dados não encontrado: {self.db_path}")
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado durante a varredura sequencial: {e}\n{traceback.format_exc()}")
            raise DatabaseError(f"Erro durante a varredura sequencial: {e}")
        
        logger.warning(f"Registro com ID {target_record_id} não encontrado.")
        return None

    def delete_record_logical(self, record_id: int) -> bool:
        """
        Executa uma exclusão lógica de um registro marcando seu byte validador como False no arquivo .db.
        Se um IndexDB estiver associado, ele também excluirá a entrada do índice.
        Retorna True se bem-sucedido, False caso contrário.
        """
        with self._lock:
            bytes_to_write_validator_false = struct.pack(VALIDATOR_FORMAT, False)

            try:
                with open(self.db_path, 'r+b') as f:
                    f.seek(DB_HEADER_SIZE_BYTES)

                    while True:
                        metadata_start_pos = f.tell()
                        metadata_bytes = f.read(RECORD_METADATA_SIZE_BYTES)
                        if not metadata_bytes:
                            break
                        
                        if len(metadata_bytes) < RECORD_METADATA_SIZE_BYTES:
                            logger.warning("Metadados de registro incompletos durante a varredura de exclusão lógica. Possível corrupção de arquivo. Interrompendo.")
                            break

                        try:
                            rec_id, validator, dict_size = struct.unpack(RECORD_ID_FORMAT + VALIDATOR_FORMAT + DICT_SIZE_FORMAT, metadata_bytes)
                        except struct.error as e:
                            logger.error(f"Erro ao desempacotar metadados de registro durante a exclusão lógica: {e}. Pulando entrada corrompida.")
                            break

                        if rec_id == record_id and validator:
                            validator_byte_pos = metadata_start_pos + struct.calcsize(RECORD_ID_FORMAT)
                            f.seek(validator_byte_pos)
                            f.write(bytes_to_write_validator_false)
                            f.flush()

                            logger.info(f"Registro ID {record_id} logicamente excluído no arquivo DB.")
                            
                            if self.index_db:
                                self.index_db.delete_entry(record_id)
                            
                            return True

                        else:
                            f.seek(dict_size, os.SEEK_CUR)

            except FileNotFoundError:
                logger.error(f"Arquivo do banco de dados não encontrado: {self.db_path}")
                return False
            except Exception as e:
                logger.error(f"Ocorreu um erro inesperado durante a exclusão lógica: {e}\n{traceback.format_exc()}")
                raise DatabaseError(f"Erro durante a exclusão lógica: {e}")
            
            logger.warning(f"Registro com ID {record_id} não encontrado ou já excluído.")
            return False

    def update_record(self, record_id: int, updated_data_object: DataObject) -> bool:
        """
        Atualiza um registro existente no arquivo .db.
        Retorna True se a atualização for bem-sucedida, False caso contrário.
        """
        with self._lock:
            original_record_offset = -1
            original_dict_size = -1
            original_validator_pos = -1

            try:
                with open(self.db_path, 'r+b') as f:
                    f.seek(DB_HEADER_SIZE_BYTES)
                    while True:
                        current_pos = f.tell()
                        metadata_bytes = f.read(RECORD_METADATA_SIZE_BYTES)
                        if not metadata_bytes:
                            break
                        
                        if len(metadata_bytes) < RECORD_METADATA_SIZE_BYTES:
                            logger.warning(f"Metadados de registro incompletos durante a busca para atualização. Possível corrupção de arquivo.")
                            break

                        rec_id, validator, dict_size = struct.unpack(RECORD_ID_FORMAT + VALIDATOR_FORMAT + DICT_SIZE_FORMAT, metadata_bytes)

                        if rec_id == record_id and validator:
                            original_record_offset = current_pos
                            original_dict_size = dict_size
                            original_validator_pos = current_pos + struct.calcsize(RECORD_ID_FORMAT)
                            logger.info(f"Registro ID {record_id} encontrado no offset {original_record_offset} para atualização.")
                            break
                        else:
                            f.seek(dict_size, os.SEEK_CUR)

                if original_record_offset == -1:
                    logger.warning(f"Registro com ID {record_id} não encontrado para atualização ou já logicamente excluído.")
                    return False

                updated_data_bytes = updated_data_object.to_bytes()
                new_dict_size = len(updated_data_bytes)

                if new_dict_size <= original_dict_size:
                    logger.info(f"Atualizando registro ID {record_id} in-place (novo tamanho {new_dict_size} <= original {original_dict_size}).")
                    with open(self.db_path, 'r+b') as f:
                        f.seek(original_record_offset + RECORD_METADATA_SIZE_BYTES)
                        f.write(updated_data_bytes)
                        
                        padding_needed = original_dict_size - new_dict_size
                        if padding_needed > 0:
                            f.write(b'\0' * padding_needed)
                        f.flush()
                    logger.info(f"Registro ID {record_id} atualizado in-place com sucesso.")
                    return True
                else:
                    logger.info(f"Novo tamanho ({new_dict_size}) > original ({original_dict_size}). Realizando exclusão lógica e anexação.")
                    
                    with open(self.db_path, 'r+b') as f:
                        f.seek(original_validator_pos)
                        f.write(struct.pack(VALIDATOR_FORMAT, False))
                        f.flush()
                    logger.info(f"Registro original ID {record_id} marcado como logicamente excluído.")

                    new_record_metadata = struct.pack(RECORD_ID_FORMAT + VALIDATOR_FORMAT + DICT_SIZE_FORMAT,
                                                      record_id, True, new_dict_size)
                    with open(self.db_path, 'ab') as f:
                        new_start_offset = f.tell()
                        f.write(new_record_metadata)
                        f.write(updated_data_bytes)
                        f.flush()
                    logger.info(f"Registro ID {record_id} reescrito no novo offset {new_start_offset}.")

                    if self.index_db:
                        self.index_db.add_entry(record_id, new_start_offset, updated_data_bytes)
                        logger.info(f"Índice atualizado para o registro ID {record_id}.")

                    return True

            except FileNotFoundError:
                logger.error(f"Arquivo do banco de dados não encontrado: {self.db_path}")
                return False
            except Exception as e:
                logger.error(f"Ocorreu um erro inesperado durante a atualização do registro: {e}\n{traceback.format_exc()}")
                raise DatabaseError(f"Erro ao atualizar o registro: {e}")

    def import_from_csv(self, csv_file_path: Union[str, Path], has_header: bool = True) -> int:
        """
        Lê dados de um arquivo CSV, valida cada linha e salva-os como DataObjects no DB.
        """
        csv_file = Path(csv_file_path)
        if not csv_file.exists():
            logger.error(f"Arquivo CSV não encontrado: {csv_file_path}")
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_file_path}")

        imported_count = 0
        with self._lock:
            with open(csv_file, 'r', encoding='utf-8') as f:
                if has_header:
                    next(f)

                for line_num, line in enumerate(f, 1 + (1 if has_header else 0)):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        row_data = line.split(';')
                        data_obj = DataObject(row_data=row_data)
                        
                        self.save_record(data_obj)
                        imported_count += 1
                        logger.debug(f"Linha {line_num}: Registro importado com sucesso (ID: {self._next_record_id - 1}).")
                    except DataValidationError as e:
                        logger.error(f"Linha {line_num}: Erro de validação: {e}. Linha: '{line}'")
                    except Exception as e:
                        logger.error(f"Linha {line_num}: Erro inesperado ao importar: {e}\n{traceback.format_exc()}. Linha: '{line}'")

        logger.info(f"Importação CSV concluída. Total de registros importados com sucesso: {imported_count}.")
        return imported_count

    def export_to_csv(self, csv_file_path: Union[str, Path], include_header: bool = True) -> int:
        """
        Exporta todos os registros válidos do banco de dados para um arquivo CSV.
        """
        csv_file = Path(csv_file_path)
        exported_count = 0

        with self._lock:
            try:
                with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                    if include_header:
                        f.write(';'.join(FIELDS) + '\n')

                    records_to_export = self.load_all_records()

                    for record in records_to_export:
                        record_dict = record.to_dict()
                        csv_line_parts = []
                        for field_name in FIELDS:
                            value = record_dict.get(field_name, '')
                            csv_line_parts.append(str(value) if value is not None else '')
                        
                        f.write(';'.join(csv_line_parts) + '\n')
                        exported_count += 1
                
                logger.info(f"Exportação CSV concluída. Total de registros exportados com sucesso: {exported_count} para '{csv_file_path}'.")
                return exported_count

            except FileNotFoundError:
                logger.error(f"Não foi possível criar o arquivo CSV: {csv_file_path}. Caminho inválido ou permissão negada.")
                raise DatabaseError(f"Não foi possível criar o arquivo CSV: {csv_file_path}")
            except Exception as e:
                logger.error(f"Ocorreu um erro inesperado durante a exportação para CSV: {e}\n{traceback.format_exc()}")
                raise DatabaseError(f"Erro ao exportar registros para CSV: {e}")

# --- Função de Formulário (do form.py) ---
def accident_record_form(
    initial_data: Optional[Dict[str, Any]] = None,
    submit_label: str = "💾 Salvar Registro",
    key_prefix: str = "form",
    disabled_fields: Optional[List[str]] = None
):
    """
    Fornece um formulário para usuários adicionarem ou editarem um registro de acidente.
    Inclui validação de entrada e feedback claro.
    """
    if disabled_fields is None:
        disabled_fields = []
    
    # Adicionando esta verificação para garantir que initial_data seja sempre um dicionário.
    if initial_data is None:
        initial_data = {}

    submitted_data = None
    submitted = False

    def is_disabled(field_name):
        return field_name in disabled_fields

    with st.form(f"{key_prefix}_record_form", clear_on_submit=True if initial_data is None else False):
        st.subheader("Detalhes do Acidente Obrigatórios (*)")
        cols_req = st.columns(2)

        default_crash_date = initial_data.get('crash_date', date.today().isoformat())
        if isinstance(default_crash_date, str):
            try:
                default_crash_date = datetime.strptime(default_crash_date, '%Y-%m-%d').date()
            except ValueError:
                default_crash_date = date.today()

        default_crash_time = initial_data.get('default_datetime', datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'))
        if isinstance(default_crash_time, str):
            try:
                time_str_match = re.search(r'(\d{2}:\d{2}:\d{2} (?:AM|PM))', default_crash_time)
                if time_str_match:
                    default_crash_time = datetime.strptime(time_str_match.group(1), '%I:%M:%S %p').time()
                else:
                    default_crash_time = datetime.now().time()
            except ValueError:
                default_crash_time = datetime.now().time()
        elif isinstance(default_crash_time, datetime):
            default_crash_time = default_crash_time.time()
        else:
            default_crash_time = datetime.now().time()


        with cols_req[0]:
            crash_date = st.date_input(
                "Data do Acidente*",
                value=default_crash_date,
                help="Data do acidente (YYYY-MM-DD)",
                key=f"{key_prefix}_crash_date",
                disabled=is_disabled('crash_date')
            )
            crash_time = st.time_input(
                "Hora do Acidente*",
                value=default_crash_time,
                help="Hora do acidente (HH:MM AM/PM)",
                key=f"{key_prefix}_crash_time_only",
                disabled=is_disabled('default_datetime')
            )
            
        with cols_req[1]:
            num_units = st.number_input(
                "Número de Unidades Envolvidas*",
                min_value=0,
                max_value=999,
                value=initial_data.get('num_units', 1),
                step=1,
                help="Número total de veículos/unidades envolvidos no acidente.",
                key=f"{key_prefix}_num_units",
                disabled=is_disabled('num_units')
            )
            crash_type_options = ["NO INJURY / DRIVE AWAY", "INJURY AND / OR TOW DUE TO CRASH"]
            default_crash_type = initial_data.get('crash_type')
            if isinstance(default_crash_type, list) and default_crash_type:
                default_crash_type = default_crash_type[0]
            elif default_crash_type not in crash_type_options:
                default_crash_type = crash_type_options[0]
            crash_type_index = crash_type_options.index(default_crash_type) if default_crash_type in crash_type_options else 0


            crash_type = st.selectbox(
                "Tipo de Acidente*",
                crash_type_options,
                index=crash_type_index,
                help="Tipo principal de colisão (ex: Traseira, Frontal, Lateral, Capotamento)",
                key=f"{key_prefix}_crash_type",
                disabled=is_disabled('crash_type')
            )            
            injuries_total = st.number_input(
                "Total de Feridos*",
                min_value=0.0,
                value=float(initial_data.get('injuries_total', 0.0)),
                step=1.0,
                help="Contagem total de todas as lesões (fatais, incapacitantes, etc.).",
                key=f"{key_prefix}_injuries_total",
                disabled=is_disabled('injuries_total')
            )

        st.subheader("Detalhes Opcionais")
        cols1 = st.columns(3)
        with cols1[0]:
            traffic_control_device_options = [
                "TRAFFIC SIGNAL", "NO CONTROLS", "STOP SIGN/FLASHER", "UNKNOWN", "OTHER",
                "PEDESTRIAN CROSSING SIGN", "OTHER WARNING SIGN", "YIELD", "FLASHING CONTROL SIGNAL",
                "LANE USE MARKING", "OTHER REG. SIGN", "DELINEATORS", "SCHOOL ZONE",
                "POLICE/FLAGMAN", "NO PASSING", "RR CROSSING SIGN", "RAILROAD CROSSING GATE",
                "BICYCLE CROSSING SIGN", "OTHER RAILROAD CROSSING",
            ]
            default_tcd = initial_data.get('traffic_control_device')
            tcd_index = traffic_control_device_options.index(default_tcd) if default_tcd in traffic_control_device_options else 0
            traffic_control_device = st.selectbox(
                "Dispositivo de Controle de Tráfego",
                traffic_control_device_options,
                index=tcd_index,
                key=f"{key_prefix}_tcd",
                disabled=is_disabled('traffic_control_device')
            )
            
            weather_condition_options = [
                "CLEAR", "RAIN", "SNOW", "CLOUDY/OVERCAST", "UNKNOWN", "FOG/SMOKE/HAZE",
                "BLOWING SNOW", "FREEZING RAIN/DRIZZLE", "OTHER", "SLEET/HAIL",
                "SEVERE CROSS WIND GATE", "BLOWING SAND, SOIL, DIRT",
            ]
            default_weather = initial_data.get('weather_condition')
            weather_index = weather_condition_options.index(default_weather) if default_weather in weather_condition_options else 0
            weather_condition = st.selectbox(
                "Condição Climática",
                weather_condition_options,
                index=weather_index,
                key=f"{key_prefix}_weather",
                disabled=is_disabled('weather_condition')
            )
            
            lighting_condition_options = ["DAYLIGHT", "DARKNESS, LIGHTED ROAD", "DUSK", "DARKNESS", "UNKNOWN", "DAWN"]
            default_lighting = initial_data.get('lighting_condition')
            if isinstance(default_lighting, list) and default_lighting:
                default_lighting = default_lighting[0]
            elif default_lighting not in lighting_condition_options:
                default_lighting = lighting_condition_options[0]
            lighting_index = lighting_condition_options.index(default_lighting) if default_lighting in lighting_condition_options else 0

            lighting_condition = st.selectbox(
                "Condição de Iluminação",
                lighting_condition_options,
                index=lighting_index,
                key=f"{key_prefix}_lighting",
                disabled=is_disabled('lighting_condition')
            )
        with cols1[1]:
            first_crash_type_options = [
                "TURNING", "REAR END", "ANGLE", "FIXED OBJECT", "REAR TO FRONT",
                "SIDESWIPE SAME DIRECTION", "SIDESWIPE OPPOSITE DIRECTION", "PEDALCYCLIST",
                "PEDESTRIAN", "HEAD ON", "PARKED MOTOR VEHICLE", "OTHER NONCOLLISION",
                "OVERTURNED", "OTHER OBJECT", "REAR TO SIDE", "ANIMAL", "TRAIN", "REAR TO REAR",
            ]
            default_first_crash_type = initial_data.get('first_crash_type')
            first_crash_type_index = first_crash_type_options.index(default_first_crash_type) if default_first_crash_type in first_crash_type_options else 0
            first_crash_type = st.selectbox(
                "Primeiro Tipo de Acidente (Específico)",
                options=first_crash_type_options,
                index=first_crash_type_index,
                help="Ponto de primeiro contato mais específico, se conhecido.",
                key=f"{key_prefix}_first_crash_type",
                disabled=is_disabled('first_crash_type')
            )
            
            trafficway_type_options = [
                "NOT DIVIDED", "FOUR WAY", "T-INTERSECTION", "DIVIDED - W/MEDIAN (NOT RAISED)",
                "OTHER", "UNKNOWN INTERSECTION TYPE", "ONE-WAY", "RAMP", "TRAFFIC ROUTE",
                "FIVE POINT, OR MORE", "DIVIDED - W/MEDIAN BARRIER", "UNKNOWN", "ALLEY",
                "CENTER TURN LANE", "L-INTERSECTION", "DRIVEWAY", "Y-INTERSECTION",
                "PARKING LOT", "ROUNDABOUT", "NOT REPORTED",
            ]
            default_trafficway_type = initial_data.get('trafficway_type')
            trafficway_type_index = trafficway_type_options.index(default_trafficway_type) if default_trafficway_type in trafficway_type_options else 0
            trafficway_type = st.selectbox(
                "Tipo de Via",
                trafficway_type_options,
                index=trafficway_type_index,
                help="Tipo de via (ex: INTERSTATE, LOCAL STREET, ALLEY)",
                key=f"{key_prefix}_trafficway_type",
                disabled=is_disabled('trafficway_type')
            )
            
            alignment_options = ["STRAIGHT AND LEVEL", "CURVE, LEVEL", "STRAIGHT ON HILLCREST", "STRAIGHT ON GRADE", "CURVE ON GRADE", "CURVE ON HILLCREST"]
            default_alignment = initial_data.get('alignment')
            alignment_index = alignment_options.index(default_alignment) if default_alignment in alignment_options else 0
            alignment = st.selectbox(
                "Alinhamento",
                alignment_options,
                index=alignment_index,
                help="Alinhamento da via (ex: STRAIGHT AND LEVEL, CURVE ON GRADE)",
                key=f"{key_prefix}_alignment",
                disabled=is_disabled('alignment')
            )
            
            roadway_surface_cond_options = ["UNKNOWN", "DRY", "WET", "SNOW OR SLUSH", "ICE", "OTHER", "SAND, MUD, DIRT"]
            default_roadway_surface_cond = initial_data.get('roadway_surface_cond')
            roadway_surface_cond_index = roadway_surface_cond_options.index(default_roadway_surface_cond) if default_roadway_surface_cond in roadway_surface_cond_options else 0
            roadway_surface_cond = st.selectbox(
                "Condição da Superfície da Via",
                roadway_surface_cond_options,
                index=roadway_surface_cond_index,
                key=f"{key_prefix}_surface_cond",
                disabled=is_disabled('roadway_surface_cond')
            )
        with cols1[2]:
            road_defect_options = ["UNKNOWN", "NO DEFECTS", "OTHER", "SHOULDER DEFECT", "WORN SURFACE", "DEBRIS ON ROADWAY", "RUT, HOLES"]
            default_road_defect = initial_data.get('road_defect')
            road_defect_index = road_defect_options.index(default_road_defect) if default_road_defect in road_defect_options else 0
            road_defect = st.selectbox(
                "Defeito na Via",
                road_defect_options,
                index=road_defect_index,
                key=f"{key_prefix}_road_defect",
                disabled=is_disabled('road_defect')
            )
            
            intersection_related_i_options = ["NO", "YES"]
            default_intersection_related_i = "YES" if initial_data.get('intersection_related_i', False) else "NO"
            intersection_related_i_index = intersection_related_i_options.index(default_intersection_related_i) if default_intersection_related_i in intersection_related_i_options else 0
            intersection_related_i = st.selectbox(
                "Relacionado à Interseção?",
                intersection_related_i_options,
                index=intersection_related_i_index,
                key=f"{key_prefix}_intersection_related",
                disabled=is_disabled('intersection_related_i')
            )
            
            damage_options = ["$501 - $1,500", "OVER $1,500", "$500 OR LESS"]
            default_damage = initial_data.get('damage')
            damage_index = damage_options.index(default_damage) if default_damage in damage_options else 0
            damage = st.selectbox(
                "Descrição do Dano",
                damage_options,
                help="Breve descrição dos danos à propriedade.",
                index=damage_index,
                key=f"{key_prefix}_damage",
                disabled=is_disabled('damage')
            )
            
            prim_contributory_cause_options = [
                "UNABLE TO DETERMINE", "IMPROPER TURNING/NO SIGNAL", "FOLLOWING TOO CLOSELY",
                "DRIVING SKILLS/KNOWLEDGE/EXPERIENCE", "IMPROPER BACKING", "FAILING TO YIELD RIGHT-OF-WAY",
                "IMPROPER OVERTAKING/PASSING", "DRIVING ON WRONG SIDE/WRONG WAY", "IMPROPER LANE USAGE",
                "NOT APPLICABLE", "FAILING TO REDUCE SPEED TO AVOID CRASH", "DISREGARDING TRAFFIC SIGNALS",
                "WEATHER", "DISREGARDING STOP SIGN", "EQUIPMENT - VEHICLE CONDITION",
                "OPERATING VEHICLE IN ERRATIC, RECKLESS, CARELESS, NEGLIGENT OR AGGRESSIVE MANNER",
                "DISREGARDING OTHER TRAFFIC SIGNS", "TURNING RIGHT ON RED",
                "VISION OBSCURED (SIGNS, TREE LIMBS, BUILDINGS, ETC.)",
                "EVASIVE ACTION DUE TO ANIMAL, OBJECT, NONMOTORIST",
                "UNDER THE INFLUENCE OF ALCOHOL/DRUGS (USE WHEN ARREST IS EFFECTED)",
                "DISTRACTION - FROM OUTSIDE VEHICLE", "EXCEEDING SAFE SPEED FOR CONDITIONS",
                "DISREGARDING ROAD MARKINGS", "ROAD ENGINEERING/SURFACE/MARKING DEFECTS",
                "PHYSICAL CONDITION OF DRIVER", "DISTRACTION - FROM INSIDE VEHICLE",
                "EXCEEDING AUTHORIZED SPEED LIMIT", "ROAD CONSTRUCTION/MAINTENANCE",
                "DISTRACTION - OTHER ELECTRONIC DEVICE (NAVIGATION DEVICE, DVD PLAYER, ETC.)",
                "ANIMAL", "HAD BEEN DRINKING (USE WHEN ARREST IS NOT MADE)",
                "BICYCLE ADVANCING LEGALLY ON RED LIGHT", "CELL PHONE USE OTHER THAN TEXTING",
                "RELATED TO BUS STOP", "TEXTING", "OBSTRUCTED CROSSWALKS", "DISREGARDING YIELD SIGN",
                "MOTORCYCLE ADVANCING LEGALLY ON RED LIGHT", "PASSING STOPPED SCHOOL BUS",
            ]
            default_prim_contributory_cause = initial_data.get('prim_contributory_cause')
            prim_contributory_cause_index = prim_contributory_cause_options.index(default_prim_contributory_cause) if default_prim_contributory_cause in prim_contributory_cause_options else 0
            prim_contributory_cause = st.selectbox(
                "Principal Causa Contributiva",
                prim_contributory_cause_options,
                help="Principal fator que contribuiu para o acidente (ex: VELOCIDADE INSEGURA, NÃO CUMPRIU O RENDIMENTO)",
                index=prim_contributory_cause_index,
                key=f"{key_prefix}_prim_cause",
                disabled=is_disabled('prim_contributory_cause')
            )
            
            most_severe_injury_options = ["NO INDICATION OF INJURY", "NONINCAPACITATING INJURY", "INCAPACITATING INJURY", "REPORTED, NOT EVIDENT", "FATAL"]
            default_most_severe_injury = initial_data.get('most_severe_injury')
            if isinstance(default_most_severe_injury, list) and default_most_severe_injury:
                default_most_severe_injury = default_most_severe_injury[0]
            elif default_most_severe_injury not in most_severe_injury_options:
                default_most_severe_injury = most_severe_injury_options[0]
            most_severe_injury_index = most_severe_injury_options.index(default_most_severe_injury) if default_most_severe_injury in most_severe_injury_options else 0

            most_severe_injury = st.selectbox(
                "Lesão Mais Grave",
                most_severe_injury_options,
                index=most_severe_injury_index,
                key=f"{key_prefix}_most_severe_injury",
                disabled=is_disabled('most_severe_injury')
            )

        st.subheader("Detalhes de Lesões & Dados Temporais")
        inj_cols = st.columns(3)
        with inj_cols[0]:
            injuries_fatal = st.number_input(
                "Lesões Fatais",
                min_value=0.0,
                value=float(initial_data.get('injuries_fatal', 0.0)),
                step=1.0,
                key=f"{key_prefix}_injuries_fatal",
                disabled=is_disabled('injuries_fatal')
            )
            injuries_incapacitating = st.number_input(
                "Lesões Incapacitantes",
                min_value=0.0,
                value=float(initial_data.get('injuries_incapacitating', 0.0)),
                step=1.0,
                key=f"{key_prefix}_injuries_incapacitating",
                disabled=is_disabled('injuries_incapacitating')
            )
        with inj_cols[1]:
            injuries_non_incapacitating = st.number_input(
                "Lesões Não Incapacitantes",
                min_value=0.0,
                value=float(initial_data.get('injuries_non_incapacitating', 0.0)),
                step=1.0,
                key=f"{key_prefix}_injuries_non_incapacitating",
                disabled=is_disabled('injuries_non_incapacitating')
            )
            injuries_reported_not_evident = st.number_input(
                "Lesões Reportadas Não Evidentes",
                min_value=0.0,
                value=float(initial_data.get('injuries_reported_not_evident', 0.0)),
                step=1.0,
                key=f"{key_prefix}_injuries_reported_not_evident",
                disabled=is_disabled('injuries_reported_not_evident')
            )
        with inj_cols[2]:
            injuries_no_indication = st.number_input(
                "Lesões Sem Indicação",
                min_value=0.0,
                value=float(initial_data.get('injuries_no_indication', 0.0)),
                step=1.0,
                key=f"{key_prefix}_injuries_no_indication",
                disabled=is_disabled('injuries_no_indication')
            )

        temp_cols = st.columns(3)
        with temp_cols[0]:
            default_hour = initial_data.get('crash_hour', 0)
            crash_hour = st.slider(
                "Hora do Acidente (0-23)",
                0, 23,
                value=int(default_hour),
                key=f"{key_prefix}_crash_hour",
                disabled=is_disabled('crash_hour')
            )
        with temp_cols[1]:
            default_day_of_week = initial_data.get('crash_day_of_week', 1)
            crash_day_of_week = st.slider(
                "Dia da Semana (1=Segunda, 7=Domingo)",
                1, 7,
                value=int(default_day_of_week),
                key=f"{key_prefix}_crash_day_of_week",
                disabled=is_disabled('crash_day_of_week')
            )
        with temp_cols[2]:
            default_month = initial_data.get('crash_month', 1)
            crash_month = st.slider(
                "Mês (1-12)",
                1, 12,
                value=int(default_month),
                key=f"{key_prefix}_crash_month",
                disabled=is_disabled('crash_month')
            )

        submitted = st.form_submit_button(submit_label, use_container_width=True)

        if submitted:
            full_datetime_str = f"{crash_date.isoformat()} {crash_time.strftime('%I:%M:%S %p')}"
            
            submitted_data = {
                'crash_date': crash_date.isoformat(),
                'default_datetime': full_datetime_str,
                'traffic_control_device': traffic_control_device,
                'weather_condition': weather_condition,
                'lighting_condition': [lighting_condition],
                'first_crash_type': first_crash_type,
                'trafficway_type': trafficway_type,
                'alignment': alignment,
                'roadway_surface_cond': roadway_surface_cond,
                'road_defect': road_defect,
                'crash_type': [crash_type],
                'intersection_related_i': True if intersection_related_i == "YES" else False,
                'damage': damage,
                'prim_contributory_cause': prim_contributory_cause,
                'num_units': num_units,
                'most_severe_injury': [most_severe_injury],
                'injuries_total': injuries_total,
                'injuries_fatal': injuries_fatal,
                'injuries_incapacitating': injuries_incapacitating,
                'injuries_non_incapacitating': injuries_non_incapacitating,
                'injuries_reported_not_evident': injuries_reported_not_evident,
                'injuries_no_indication': injuries_no_indication,
                'crash_hour': crash_hour,
                'crash_day_of_week': crash_day_of_week,
                'crash_month': crash_month
            }
            return submitted_data, True
    return None, False

# --- Inicialização do Banco de Dados (do streamlit_app.py) ---
DATA_FOLDER.mkdir(parents=True, exist_ok=True)

@st.cache_resource
def get_database_instances():
    index_db_instance = IndexDB()
    traffic_db_instance = TrafficAccidentsDB(index_db=index_db_instance)
    return traffic_db_instance, index_db_instance

db, index_db = get_database_instances()

# --- Gerenciamento de Estado da Aplicação Streamlit (do streamlit_app.py) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'view_records'
if 'record_to_edit_id' not in st.session_state:
    st.session_state.record_to_edit_id = None
if 'record_to_delete_id' not in st.session_state:
    st.session_state.record_to_delete_id = None
if 'records_per_page' not in st.session_state:
    st.session_state.records_per_page = 20
if 'current_pagination_page' not in st.session_state:
    st.session_state.current_pagination_page = 1
if 'found_record' not in st.session_state:
    st.session_state.found_record = None
if 'last_searched_id' not in st.session_state:
    st.session_state.last_searched_id = None

# --- Funções de Navegação (do streamlit_app.py) ---
def navigate_to(page_name: str, record_id: Optional[int] = None):
    st.session_state.current_page = page_name
    if page_name in ['update_record', 'delete_record']:
        st.session_state.record_to_edit_id = record_id
        st.session_state.record_to_delete_id = record_id
    else:
        st.session_state.record_to_edit_id = None
        st.session_state.record_to_delete_id = None
        st.session_state.found_record = None
        st.session_state.last_searched_id = None
    st.rerun()

# --- Funções Auxiliares para Exibição de Registros (do streamlit_app.py) ---
def display_record_details(record: DataObject, expander_title_prefix: str = "Detalhes do Registro"):
    """Exibe os detalhes de um DataObject dentro de um st.expander."""
    record_dict = record.to_dict()
    record_id_for_display = getattr(record, 'record_id', 'N/A')

    if 'crash_date' in record_dict and isinstance(record_dict['crash_date'], str):
        try:
            record_dict['crash_date'] = datetime.strptime(record_dict['crash_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError:
            pass

    if 'default_datetime' in record_dict and isinstance(record_dict['default_datetime'], str):
        try:
            dt_obj = datetime.strptime(record_dict['default_datetime'].split('.')[0], '%Y-%m-%d %I:%M:%S %p')
            record_dict['default_datetime'] = dt_obj.strftime('%d/%m/%Y %I:%M:%S %p')
        except ValueError:
            try:
                dt_obj = datetime.strptime(record_dict['default_datetime'], '%Y-%m-%d')
                record_dict['default_datetime'] = dt_obj.strftime('%d/%m/%Y') + " (Apenas Data)"
            except ValueError:
                pass

    with st.expander(f"{expander_title_prefix} - ID: {record_id_for_display} - Data: {record_dict.get('crash_date', 'N/A')}"):
        df_data = []
        for field in FIELDS:
            value = record_dict.get(field)
            if FIELD_DEFINITIONS[field]['type'] == FieldType.BOOLEAN:
                value = "Sim" if value else "Não"
            elif FIELD_DEFINITIONS[field]['type'] == FieldType.MULTI_ENUM and isinstance(value, list):
                value = ", ".join(value)
            
            if field.startswith('injuries_') and isinstance(value, (float, int)):
                value = f"{float(value):.2f}"

            df_data.append({"Campo": field.replace('_', ' ').title(), "Valor": value})
        
        st.table(pd.DataFrame(df_data))

# --- Telas da Aplicação (do streamlit_app.py) ---

def view_records_screen():
    """Exibe todos os registros válidos com paginação e expansores."""
    st.title("📊 Visualizar Registros de Acidentes")

    records = db.load_all_records()
    total_records = len(records)

    if not records:
        st.info("Nenhum registro encontrado no banco de dados.")
        return

    st.sidebar.header("Opções de Visualização")
    st.session_state.records_per_page = st.sidebar.selectbox(
        "Registros por Página", [20, 50, 100],
        index=[20, 50, 100].index(st.session_state.records_per_page) if st.session_state.records_per_page in [20, 50, 100] else 0,
        key="rpp_view"
    )

    total_pages = (total_records + st.session_state.records_per_page - 1) // st.session_state.records_per_page

    st.session_state.current_pagination_page = st.sidebar.number_input(
        "Página Atual",
        min_value=1,
        max_value=total_pages if total_pages > 0 else 1,
        value=st.session_state.current_pagination_page if st.session_state.current_pagination_page <= total_pages else 1,
        key="page_num_view"
    )

    start_idx = (st.session_state.current_pagination_page - 1) * st.session_state.records_per_page
    end_idx = start_idx + st.session_state.records_per_page
    paginated_records = records[start_idx:end_idx]

    st.write(f"Exibindo registros {start_idx + 1} a {min(end_idx, total_records)} de {total_records}")

    for record in paginated_records:
        display_record_details(record, expander_title_prefix=f"Detalhes do Registro")

def add_record_screen():
    """Tela para inserção de novos registros."""
    st.title("➕ Inserir Novo Registro")
    st.write("Preencha o formulário abaixo para adicionar um novo registro de acidente.")

    submitted_data, submitted = accident_record_form(key_prefix="add")

    if submitted:
        try:
            new_data_object = DataObject(initial_data=submitted_data)
            record_id = db.save_record(new_data_object)
            st.success(f"Registro adicionado com sucesso! ID: {record_id}")
        except DataValidationError as e:
            st.error(f"Erro de validação ao adicionar registro: {e}")
        except DatabaseError as e:
            st.error(f"Erro no banco de dados ao adicionar registro: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")
            st.exception(e)


def search_record_screen():
    """Tela para pesquisar, visualizar, editar ou excluir um registro por ID."""
    st.title("🔍 Pesquisar Registro por ID")
    search_id_input = st.number_input(
        "Digite o ID do Registro:",
        min_value=1,
        value=st.session_state.last_searched_id if st.session_state.last_searched_id else 1,
        step=1,
        key="search_id_input"
    )
    
    col_search_btns = st.columns(2)
    with col_search_btns[0]:
        if st.button("🔎 Pesquisar", key="search_button"):
            st.session_state.found_record = db.get_record_by_id(search_id_input)
            st.session_state.last_searched_id = search_id_input
            if not st.session_state.found_record:
                st.warning(f"Registro com ID {st.session_state.last_searched_id} não encontrado ou foi logicamente excluído.")
                st.session_state.found_record = None
    
    if st.session_state.get('found_record'):
        st.success(f"Registro ID {st.session_state.last_searched_id} encontrado!")
        display_record_details(st.session_state.found_record, expander_title_prefix=f"Detalhes do Registro")

        st.subheader("Ações:")
        action_cols = st.columns(2)
        with action_cols[0]:
            if st.button("✏️ Editar Registro", key="edit_record_button"):
                navigate_to('update_record', st.session_state.last_searched_id)
        with action_cols[1]:
            if st.button("🗑️ Excluir Registro", key="delete_record_button"):
                navigate_to('delete_record', st.session_state.last_searched_id)


def update_record_screen():
    """Tela para atualizar um registro existente."""
    st.title("🔄 Atualizar Registro")
    
    record_id = st.session_state.record_to_edit_id
    if record_id is None:
        st.warning("Nenhum ID de registro especificado para atualização. Por favor, pesquise um registro primeiro.")
        if st.button("Voltar para Pesquisa", key="back_to_search_from_update"):
            navigate_to('search_record')
        return

    st.info(f"Editando registro com ID: {record_id}")
    
    current_record = db.get_record_by_id(record_id)

    if current_record:
        initial_data_for_form = current_record.to_dict()
        
        with st.expander(f"Registro Atual (ID: {record_id})"):
             df_data = []
             for field_name in FIELDS:
                 value = initial_data_for_form.get(field_name)
                 if FIELD_DEFINITIONS[field_name]['type'] == FieldType.BOOLEAN:
                     value = "Sim" if value else "Não"
                 elif FIELD_DEFINITIONS[field_name]['type'] == FieldType.MULTI_ENUM and isinstance(value, list):
                     value = ", ".join(value)
                 
                 if field_name.startswith('injuries_') and isinstance(value, (float, int)):
                     value = f"{float(value):.2f}"

                 df_data.append({"Campo": field_name.replace('_', ' ').title(), "Valor": value})
             st.table(pd.DataFrame(df_data))


        submitted_data, submitted = accident_record_form(
            initial_data=initial_data_for_form,
            submit_label=f"🔄 Atualizar Registro ID {record_id}",
            key_prefix="update"
        )

        if submitted:
            try:
                updated_data_object = DataObject(initial_data=submitted_data)
                success = db.update_record(record_id, updated_data_object)
                if success:
                    st.success(f"Registro ID {record_id} atualizado com sucesso!")
                    st.session_state.record_to_edit_id = None
                    st.session_state.found_record = None
                    st.session_state.last_searched_id = None
                    if st.button("Voltar para Pesquisa", key="post_update_back_to_search"):
                        navigate_to('search_record')
                else:
                    st.error(f"Falha ao atualizar o registro ID {record_id}.")
            except DataValidationError as e:
                st.error(f"Erro de validação ao atualizar registro: {e}")
            except DatabaseError as e:
                st.error(f"Erro no banco de dados ao atualizar registro: {e}")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado: {e}")
                st.exception(e)
    else:
        st.warning(f"Registro com ID {record_id} não encontrado ou já foi excluído. Não é possível atualizar.")
        if st.button("Voltar para Pesquisa", key="no_record_update_back_to_search"):
            navigate_to('search_record')


def delete_record_screen():
    """Tela para exclusão lógica de um registro."""
    st.title("🗑️ Excluir Registro")

    record_id = st.session_state.record_to_delete_id
    if record_id == None:
        st.warning("Nenhum ID de registro especificado para exclusão. Por favor, pesquise um registro primeiro.")
        if st.button("Voltar para Pesquisa", key="back_to_search_from_delete"):
            navigate_to('search_record')
        return

    st.info(f"Você está prestes a excluir o registro com ID: {record_id}")
    
    record_to_delete = db.get_record_by_id(record_id)

    if record_to_delete:
        st.subheader("Prévia do Registro a Ser Excluído:")
        display_record_details(record_to_delete, expander_title_prefix=f"Registro ID {record_id} (Prévia)")
        
        st.warning("Atenção: Esta ação é irreversível (exclusão lógica).")
        
        col_delete_btns = st.columns(2)
        with col_delete_btns[0]:
            if st.button(f"✅ Confirmar Exclusão do ID {record_id}", key="confirm_delete_button"):
                try:
                    success = db.delete_record_logical(record_id)
                    if success:
                        st.success(f"Registro ID {record_id} excluído logicamente com sucesso!")
                        st.session_state.record_to_delete_id = None
                        st.session_state.found_record = None
                        st.session_state.last_searched_id = None
                        if st.button("Voltar para Pesquisa", key="post_delete_back_to_search"):
                            navigate_to('search_record')
                    else:
                        st.error(f"Falha ao excluir o registro ID {record_id}.")
                except DatabaseError as e:
                    st.error(f"Erro no banco de dados ao excluir registro: {e}")
                except Exception as e:
                    st.error(f"Ocorreu um erro inesperado: {e}")
                    st.exception(e)
        with col_delete_btns[1]:
            if st.button("❌ Cancelar Exclusão", key="cancel_delete_button"):
                st.info("Exclusão cancelada.")
                st.session_state.record_to_delete_id = None
                navigate_to('search_record')
    else:
        st.warning(f"Registro com ID {record_id} não encontrado ou já foi excluído. Nenhuma ação necessária.")
        if st.button("Voltar para Pesquisa", key="no_record_delete_back_to_search"):
            navigate_to('search_record')


def management_screen():
    """Tela para importação e exportação de dados CSV."""
    st.title("🗃️ Gestão de Dados (CSV)")

    st.subheader("📥 Importar Dados de CSV")
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv", key="csv_uploader")

    if uploaded_file is not None:
        try:
            temp_csv_path = DATA_FOLDER / "temp_upload.csv"
            with open(temp_csv_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            has_header = st.checkbox("O CSV contém cabeçalho?", value=True, key="csv_header_checkbox")
            
            if st.button("Importar CSV", key="import_csv_button"):
                with st.spinner("Importando dados..."):
                    imported_count = db.import_from_csv(temp_csv_path, has_header=has_header)
                    st.success(f"{imported_count} registros importados com sucesso do CSV!")
                os.remove(temp_csv_path)
        except Exception as e:
            st.error(f"Erro ao processar o arquivo CSV: {e}")
            st.exception(e)

    st.subheader("📤 Exportar Registros Válidos para CSV")
    if st.button("Exportar para CSV", key="export_csv_button"):
        try:
            export_path = DATA_FOLDER / "exported_traffic_accidents.csv"
            with st.spinner("Exportando dados..."):
                exported_count = db.export_to_csv(export_path, include_header=True)
                
            with open(export_path, "rb") as f:
                st.download_button(
                    label=f"Download CSV ({exported_count} registros)",
                    data=f.read(),
                    file_name="exported_traffic_accidents.csv",
                    mime="text/csv",
                    key="download_exported_csv"
                )
            st.success(f"{exported_count} registros exportados para '{export_path}'. Clique no botão acima para baixar.")
        except Exception as e:
            st.error(f"Erro ao exportar dados para CSV: {e}")
            st.exception(e)


# --- Barra Lateral de Navegação Principal ---
st.sidebar.title("Opções")
st.sidebar.button("📊 Visualizar Registros", on_click=navigate_to, args=('view_records',), use_container_width=True)
st.sidebar.button("➕ Inserir Novo Registro", on_click=navigate_to, args=('add_record',), use_container_width=True)
st.sidebar.button("🔍 Pesquisar Registro", on_click=navigate_to, args=('search_record',), use_container_width=True)
st.sidebar.button("🗃️ Gestão de Dados", on_click=navigate_to, args=('management',), use_container_width=True)

# --- Renderiza a Tela Atual com base no estado da sessão ---
if st.session_state.current_page == 'view_records':
    view_records_screen()
elif st.session_state.current_page == 'add_record':
    add_record_screen()
elif st.session_state.current_page == 'search_record':
    search_record_screen()
elif st.session_state.current_page == 'update_record':
    update_record_screen()
elif st.session_state.current_page == 'delete_record':
    delete_record_screen()
elif st.session_state.current_page == 'management':
    management_screen()
