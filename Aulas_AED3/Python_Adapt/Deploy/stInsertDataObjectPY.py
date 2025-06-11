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

# --- Cryptography Imports from pycryptonew.py ---
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey # Removed DecryptionError

# --- Custom Exceptions ---
class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass

class RecordNotFoundError(DatabaseError):
    """Custom exception for when a record is not found."""
    pass

class DataValidationError(ValueError):
    """Custom exception for data validation errors."""
    pass

class EncryptionError(Exception):
    """Custom exception for encryption/decryption errors."""
    pass

# --- Configuration Constants (Centralized - from v4epsilon & v6zeta merged) ---
APP_CONFIG = {
    "DB_DIR": Path.home() / 'Documents' / 'Data',  # Using Pathlib
    "DB_FILE_NAME": 'traffic_accidents.db',
    "INDEX_FILE_NAME": 'traffic_accidents.idx',
    "ID_COUNTER_FILE_NAME": 'id_counter.txt',
    "RSA_KEYS_DIR": Path.home() / 'Documents' / 'Data' / 'rsa_keys',
    "LOG_FILE_NAME": 'app_activity.log',
    "BACKUP_DIR_NAME": 'backups',
    "HUFFMAN_FOLDER_NAME": 'huffman_compressed',
    "LZW_FOLDER_NAME": 'lzw_compressed',
    "COMPACTION_THRESHOLD_PERCENT": 20, # Percentage of deleted records to trigger compaction
    "LOCK_TIMEOUT": 10, # Seconds to wait for a file lock
    "CSV_DELIMITER": ';', # Changed from comma in v6zeta to semicolon from v4epsilon
    "MAX_RECORDS_PER_PAGE": 20, # From v6zeta
    "MAX_FILE_SIZE_MB": 100, # Max CSV file size for import - From v6zeta
    "CHUNK_SIZE": 4096, # For file operations like import/export, encryption/decryption
    "DEFAULT_ENCODING": "utf-8" # Explicit encoding for file operations
}

# Derive full paths
APP_CONFIG["DB_PATH"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["DB_FILE_NAME"]
APP_CONFIG["INDEX_PATH"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["INDEX_FILE_NAME"]
APP_CONFIG["ID_COUNTER_PATH"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["ID_COUNTER_FILE_NAME"]
APP_CONFIG["LOG_FILE_PATH"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["LOG_FILE_NAME"]
APP_CONFIG["BACKUP_PATH"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["BACKUP_DIR_NAME"]
APP_CONFIG["HUFFMAN_FOLDER"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["HUFFMAN_FOLDER_NAME"]
APP_CONFIG["LZW_FOLDER"] = APP_CONFIG["DB_DIR"] / APP_CONFIG["LZW_FOLDER_NAME"]

# RSA Key Paths
APP_CONFIG["PUBLIC_KEY_PATH"] = APP_CONFIG["RSA_KEYS_DIR"] / 'public_key.pem'
APP_CONFIG["PRIVATE_KEY_PATH"] = APP_CONFIG["RSA_KEYS_DIR"] / 'private_key.pem'

# --- Logging Setup ---
# Ensure log directory exists
APP_CONFIG["DB_DIR"].mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Default to DEBUG, can be changed

# Create formatters
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Console Handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO) # Default console level to INFO
ch.setFormatter(formatter)
logger.addHandler(ch)

# File Handler with rotation
try:
    # Use RotatingFileHandler to manage log file size and rotation
    # Max 5MB per file, keep 3 backup files
    fh = RotatingFileHandler(APP_CONFIG["LOG_FILE_PATH"], maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
except (IOError, PermissionError) as e:
    logger.error(f"Failed to set up file logging to {APP_CONFIG['LOG_FILE_PATH']}: {e}. Continuing with console logging only.")
    logger.critical("CRITICAL: File logging could not be initialized due to permissions or path issues. Check file system permissions.")

# --- DataObject Class (Refactored from DataObject_Class.py) ---
class DataObject:
    """
    Representa um único registro de acidente de trânsito, espelhando a estrutura do DataObject Java.
    Inclui lógica de validação e conversão para entradas do Streamlit.
    """
    REQUIRED_FIELDS = [
        "crash_date", "traffic_control_device", "weather_condition", "lighting_condition",
        "first_crash_type", "trafficway_type", "alignment", "roadway_surface_cond",
        "road_defect", "crash_type", "intersection_related_i", "damage",
        "prim_contributory_cause", "num_units", "most_severe_injury", "injuries_total",
        "injuries_fatal", "injuries_incapacitating", "injuries_non_incapacitating",
        "injuries_reported_not_evident", "injuries_no_indication", "crash_hour",
        "crash_day_of_week", "crash_month"
    ]
    
    # Fields that should be treated as lists internally, joined to string on output
    LIST_FIELDS = ["lighting_condition", "crash_type", "most_severe_injury"]

    def __init__(self, data: Dict[str, Any]):
        self._data = self._validate_and_clean_data(data)
        self.deleted = data.get("deleted", False) # Added for soft deletion compatibility

    def _split_string_to_list(self, text: Union[str, List[str], None]) -> List[str]:
        """
        Receives a string, list of strings, or None and returns it as a cleaned list of strings.
        If the string contains ',' or '/', it performs a split.
        """
        if isinstance(text, list):
            # Already a list, clean existing items
            return [item.strip() for item in text if item is not None and item.strip()]
        elif isinstance(text, str):
            text = text.strip()
            if not text:
                return []
            
            # Replace '/' with ',' to standardize splitting
            normalized_text = text.replace('/', ',')
            
            if ',' in normalized_text:
                return [item.strip() for item in normalized_text.split(',') if item.strip()]
            else:
                return [text] # Return as a list with a single item
        return [] # Return empty list for None or other non-string/list types

    def _join_list_to_string(self, data_list: Union[List[str], str, None]) -> str:
        """
        Receives a list of strings (or a single string/None) and returns it as a single string.
        If the list contains more than one item, it joins them with " , ".
        """
        if isinstance(data_list, str):
            return data_list.strip() # Already a string, just clean
        elif isinstance(data_list, list):
            cleaned_list = [item.strip() for item in data_list if item is not None and item.strip()]
            if not cleaned_list:
                return ""
            return " , ".join(cleaned_list)
        return "" # Return empty string for None or other non-list types

    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e limpa os dados de entrada, aplicando tipos e restrições
        baseados nos atributos do DataObject Java.
        """
        cleaned_data = {}
        
        # Define expected fields and their validation/conversion logic
        fields = {
            "id_registro": (int, lambda x: int(x) if x is not None and str(x).isdigit() else None),
            "crash_date": (str, lambda x: str(x).strip() if x is not None else ""),
            "data_local": (str, lambda x: str(x).strip() if x is not None else ""),
            "crash_hour": (int, lambda x: int(x) if x is not None and str(x).isdigit() else None),
            "crash_day_of_week": (int, lambda x: int(x) if x is not None and str(x).isdigit() else None),
            "crash_month": (int, lambda x: int(x) if x is not None and str(x).isdigit() else None),
            "injuries_total": (float, lambda x: float(x) if x is not None and (isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit()) else 0.0),
            "injuries_fatal": (float, lambda x: float(x) if x is not None and (isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit()) else 0.0),
            "injuries_incapacitating": (float, lambda x: float(x) if x is not None and (isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit()) else 0.0),
            "injuries_non_incapacitating": (float, lambda x: float(x) if x is not None and (isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit()) else 0.0),
            "injuries_reported_not_evident": (float, lambda x: float(x) if x is not None and (isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit()) else 0.0),
            "injuries_no_indication": (float, lambda x: float(x) if x is not None and (isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit()) else 0.0),
            "num_units": (int, lambda x: int(x) if x is not None and str(x).isdigit() else 0),
            "traffic_control_device": (str, lambda x: str(x).strip() if x is not None else ""),
            "weather_condition": (str, lambda x: str(x).strip() if x is not None else ""),
            # These are now List[str] fields internally
            "lighting_condition": (list, self._split_string_to_list),
            "first_crash_type": (str, lambda x: str(x).strip() if x is not None else ""),
            "trafficway_type": (str, lambda x: str(x).strip() if x is not None else ""),
            "alignment": (str, lambda x: str(x).strip() if x is not None else ""),
            "roadway_surface_cond": (str, lambda x: str(x).strip() if x is not None else ""),
            "road_defect": (str, lambda x: str(x).strip() if x is not None else ""),
            # This is now List[str] field internally
            "crash_type": (list, self._split_string_to_list),
            "intersection_related_i": (str, lambda x: str(x).strip() if x is not None else ""),
            "damage": (str, lambda x: str(x).strip() if x is not None else ""),
            "prim_contributory_cause": (str, lambda x: str(x).strip() if x is not None else ""),
            # This is now List[str] field internally
            "most_severe_injury": (list, self._split_string_to_list),
            "deleted": (bool, lambda x: bool(x) if x is not None else False),
        }

        for key, (expected_type, converter) in fields.items():
            value = data.get(key)
            try:
                cleaned_value = converter(value)
                if cleaned_value is not None:
                    # Specific validation for crash_date and data_local (assuming date strings)
                    if key == "crash_date" and cleaned_value:
                        try:
                            if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned_value): #YYYY-MM-DD
                                datetime.strptime(cleaned_value, "%Y-%m-%d").date()
                            elif re.match(r"^\d{2}/\d{2}/\d{4}$", cleaned_value): # DD/MM/YYYY
                                datetime.strptime(cleaned_value, "%d/%m/%Y").date()
                            else:
                                raise ValueError("Invalid date format")
                        except ValueError:
                            raise DataValidationError(f"Invalid date format for '{key}': {value}. Expected YYYY-MM-DD or DD/MM/YYYY.")
                    if key == "data_local" and cleaned_value:
                         try:
                            if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned_value): #YYYY-MM-DD
                                datetime.strptime(cleaned_value, "%Y-%m-%d").date()
                            elif re.match(r"^\d{2}/\d{2}/\d{4}$", cleaned_value): # DD/MM/YYYY
                                datetime.strptime(cleaned_value, "%d/%m/%Y").date()
                            else:
                                raise ValueError("Invalid date format")
                         except ValueError:
                            raise DataValidationError(f"Invalid date format for '{key}': {value}. Expected YYYY-MM-DD or DD/MM/YYYY.")
                    
                    # Type checking, with special handling for LIST_FIELDS
                    if key in self.LIST_FIELDS:
                        if not isinstance(cleaned_value, list):
                            raise DataValidationError(f"Type mismatch for field '{key}'. Expected list, got {type(cleaned_value)} from '{value}'.")
                    elif not isinstance(cleaned_value, expected_type) and cleaned_value is not None:
                        # Attempt to cast if types don't match after conversion, but not for None
                        if expected_type is int and isinstance(cleaned_value, float):
                            cleaned_value = int(cleaned_value)
                        elif expected_type is float and isinstance(cleaned_value, int):
                            cleaned_value = float(cleaned_value)
                        elif expected_type is bool and isinstance(cleaned_value, str):
                            cleaned_value = cleaned_value.lower() == 'true'
                        else:
                            raise DataValidationError(f"Type mismatch for field '{key}'. Expected {expected_type}, got {type(cleaned_value)} from '{value}'.")
                cleaned_data[key] = cleaned_value
            except (ValueError, TypeError) as e:
                raise DataValidationError(f"Failed to convert or validate field '{key}' with value '{value}': {e}")
        
        # Ensure all REQUIRED_FIELDS are present and valid
        for field in self.REQUIRED_FIELDS:
            if field not in cleaned_data or cleaned_data[field] is None or \
               (isinstance(cleaned_data[field], str) and not cleaned_data[field].strip()) or \
               (isinstance(cleaned_data[field], list) and not cleaned_data[field]): # Ensure lists are not empty for required fields
                raise DataValidationError(f"Missing or invalid required field: {field}")
        
        return cleaned_data

    # Properties for data access (using the _data dictionary)
    @property
    def id_registro(self) -> int:
        return self._data.get("id_registro")

    @id_registro.setter
    def id_registro(self, value: int):
        self._data["id_registro"] = value

    @property
    def crash_date(self) -> str:
        return self._data.get("crash_date")

    @crash_date.setter
    def crash_date(self, value: str):
        self._data["crash_date"] = value

    @property
    def data_local(self) -> str:
        return self._data.get("data_local")

    @data_local.setter
    def data_local(self, value: str):
        self._data["data_local"] = value

    @property
    def crash_hour(self) -> int:
        return self._data.get("crash_hour")

    @crash_hour.setter
    def crash_hour(self, value: int):
        self._data["crash_hour"] = value

    @property
    def crash_day_of_week(self) -> int:
        return self._data.get("crash_day_of_week")

    @crash_day_of_week.setter
    def crash_day_of_week(self, value: int):
        self._data["crash_day_of_week"] = value

    @property
    def crash_month(self) -> int:
        return self._data.get("crash_month")

    @crash_month.setter
    def crash_month(self, value: int):
        self._data["crash_month"] = value

    @property
    def injuries_total(self) -> float:
        return self._data.get("injuries_total")

    @injuries_total.setter
    def injuries_total(self, value: float):
        self._data["injuries_total"] = value

    @property
    def injuries_fatal(self) -> float:
        return self._data.get("injuries_fatal")

    @injuries_fatal.setter
    def injuries_fatal(self, value: float):
        self._data["injuries_fatal"] = value

    @property
    def injuries_incapacitating(self) -> float:
        return self._data.get("injuries_incapacitating")

    @injuries_incapacitating.setter
    def injuries_incapacitating(self, value: float):
        self._data["injuries_incapacitating"] = value

    @property
    def injuries_non_incapacitating(self) -> float:
        return self._data.get("injuries_non_incapacitating")

    @injuries_non_incapacitating.setter
    def injuries_non_incapacitating(self, value: float):
        self._data["injuries_non_incapacitating"] = value

    @property
    def injuries_reported_not_evident(self) -> float:
        return self._data.get("injuries_reported_not_evident")

    @injuries_reported_not_evident.setter
    def injuries_reported_not_evident(self, value: float):
        self._data["injuries_reported_not_evident"] = value

    @property
    def injuries_no_indication(self) -> float:
        return self._data.get("injuries_no_indication")

    @injuries_no_indication.setter
    def injuries_no_indication(self, value: float):
        self._data["injuries_no_indication"] = value

    @property
    def num_units(self) -> int:
        return self._data.get("num_units")

    @num_units.setter
    def num_units(self, value: int):
        self._data["num_units"] = value

    @property
    def traffic_control_device(self) -> str:
        return self._data.get("traffic_control_device")

    @traffic_control_device.setter
    def traffic_control_device(self, value: str):
        self._data["traffic_control_device"] = value

    @property
    def weather_condition(self) -> str:
        return self._data.get("weather_condition")

    @weather_condition.setter
    def weather_condition(self, value: str):
        self._data["weather_condition"] = value

    @property
    def lighting_condition(self) -> List[str]:
        # Always return as a list internally
        return self._data.get("lighting_condition", [])

    @lighting_condition.setter
    def lighting_condition(self, value: Union[str, List[str]]):
        # Ensure input is converted to a list via helper function
        self._data["lighting_condition"] = self._split_string_to_list(value)
    
    @property
    def first_crash_type(self) -> str:
        return self._data.get("first_crash_type")

    @first_crash_type.setter
    def first_crash_type(self, value: str):
        self._data["first_crash_type"] = value

    @property
    def trafficway_type(self) -> str:
        return self._data.get("trafficway_type")

    @trafficway_type.setter
    def trafficway_type(self, value: str):
        self._data["trafficway_type"] = value

    @property
    def alignment(self) -> str:
        return self._data.get("alignment")

    @alignment.setter
    def alignment(self, value: str):
        self._data["alignment"] = value

    @property
    def roadway_surface_cond(self) -> str:
        return self._data.get("roadway_surface_cond")

    @roadway_surface_cond.setter
    def roadway_surface_cond(self, value: str):
        self._data["roadway_surface_cond"] = value

    @property
    def road_defect(self) -> str:
        return self._data.get("road_defect")

    @road_defect.setter
    def road_defect(self, value: str):
        self._data["road_defect"] = value
        
    @property
    def crash_type(self) -> List[str]:
        # Always return as a list internally
        return self._data.get("crash_type", [])

    @crash_type.setter
    def crash_type(self, value: Union[str, List[str]]):
        # Ensure input is converted to a list via helper function
        self._data["crash_type"] = self._split_string_to_list(value)

    @property
    def intersection_related_i(self) -> str:
        return self._data.get("intersection_related_i")

    @intersection_related_i.setter
    def intersection_related_i(self, value: str):
        self._data["intersection_related_i"] = value

    @property
    def damage(self) -> str:
        return self._data.get("damage")

    @damage.setter
    def damage(self, value: str):
        self._data["damage"] = value

    @property
    def prim_contributory_cause(self) -> str:
        return self._data.get("prim_contributory_cause")

    @prim_contributory_cause.setter
    def prim_contributory_cause(self, value: str):
        self._data["prim_contributory_cause"] = value
        
    @property
    def most_severe_injury(self) -> List[str]:
        # Always return as a list internally
        return self._data.get("most_severe_injury", [])

    @most_severe_injury.setter
    def most_severe_injury(self, value: Union[str, List[str]]):
        # Ensure input is converted to a list via helper function
        self._data["most_severe_injury"] = self._split_string_to_list(value)

    @property
    def id(self) -> Optional[int]:
        # Map 'id' attribute used by DBManager to 'id_registro' in _data
        return self._data.get("id_registro") 

    @id.setter
    def id(self, value: Optional[int]):
        # Map 'id' attribute used by DBManager to 'id_registro' in _data
        self._data["id_registro"] = value

    def to_dict(self, include_deleted: bool = False) -> Dict[str, Any]:
        data = {}
        
        # Manually add properties that are not in REQUIRED_FIELDS but should be in dict
        all_props = [
            "id_registro", "crash_date", "data_local", "crash_hour", "crash_day_of_week",
            "crash_month", "injuries_total", "injuries_fatal", "injuries_incapacitating",
            "injuries_non_incapacitating", "injuries_reported_not_evident", "injuries_no_indication",
            "num_units", "traffic_control_device", "weather_condition", "lighting_condition",
            "first_crash_type", "trafficway_type", "alignment", "roadway_surface_cond",
            "road_defect", "crash_type", "intersection_related_i", "damage",
            "prim_contributory_cause", "most_severe_injury"
        ]

        for prop_name in all_props:
            if hasattr(self, prop_name):
                value = getattr(self, prop_name)
                # Apply _join_list_to_string for LIST_FIELDS when converting to dict
                if prop_name in self.LIST_FIELDS:
                    data[prop_name] = self._join_list_to_string(value)
                else:
                    data[prop_name] = value
        
        # Ensure 'id' is mapped from 'id_registro' for external use (e.g., DBManager, CSV)
        if 'id_registro' in data:
            data['id'] = data.pop('id_registro')
        elif hasattr(self, 'id_registro') and self.id_registro is not None:
             data['id'] = self.id_registro # Fallback if not already in data

        if include_deleted:
            data['deleted'] = self.deleted
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        # The new DataObject constructor expects a single 'data' dictionary.
        # The old DataObject.from_dict used **data, which passed individual keys.
        # We need to adapt the incoming dictionary to the new DataObject's constructor.
        cleaned_data = {k: v for k, v in data.items()}
        # If 'id' is present, map it to 'id_registro' for the new DataObject's internal use.
        # The new DataObject's __init__ will then correctly process 'id_registro'.
        if 'id' in cleaned_data:
            cleaned_data['id_registro'] = cleaned_data.pop('id')
        return cls(cleaned_data)


# --- DBManager Class (from v4epsilon) ---
class DBManager:
    def __init__(self, db_path: Path, index_path: Path, id_counter_path: Path, lock_timeout: int = 10):
        self.db_path = db_path
        self.index_path = index_path
        self.id_counter_path = id_counter_path
        self.lock_timeout = lock_timeout
        self._ensure_db_files()
        self.current_id = self._load_id_counter()

    def _ensure_db_files(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            with open(self.db_path, 'wb') as f:
                pass # Create empty binary file
        if not self.index_path.exists():
            with open(self.index_path, 'w', encoding=APP_CONFIG["DEFAULT_ENCODING"]) as f:
                json.dump({}, f) # Create empty JSON index
        if not self.id_counter_path.exists():
            with open(self.id_counter_path, 'w', encoding=APP_CONFIG["DEFAULT_ENCODING"]) as f:
                f.write('1') # Initialize ID counter to 1

    def _load_id_counter(self) -> int:
        try:
            with filelock.FileLock(f"{self.id_counter_path}.lock", timeout=self.lock_timeout):
                with open(self.id_counter_path, 'r', encoding=APP_CONFIG["DEFAULT_ENCODING"]) as f:
                    return int(f.read().strip())
        except (IOError, ValueError) as e:
            logger.error(f"Error loading ID counter from {self.id_counter_path}: {e}")
            raise DatabaseError(f"Falha ao carregar contador de IDs. Erro: {e}")

    def _save_id_counter(self, new_id: int):
        try:
            with filelock.FileLock(f"{self.id_counter_path}.lock", timeout=self.lock_timeout):
                with open(self.id_counter_path, 'w', encoding=APP_CONFIG["DEFAULT_ENCODING"]) as f:
                    f.write(str(new_id))
        except IOError as e:
            logger.error(f"Error saving ID counter to {self.id_counter_path}: {e}")
            raise DatabaseError(f"Falha ao salvar contador de IDs. Erro: {e}")

    def _load_index(self) -> Dict[str, Dict[str, Union[int, bool]]]:
        try:
            with filelock.FileLock(f"{self.index_path}.lock", timeout=self.lock_timeout):
                with open(self.index_path, 'r', encoding=APP_CONFIG["DEFAULT_ENCODING"]) as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Index file {self.index_path} not found or corrupted, creating new. Error: {e}")
            return {}
        except (IOError, PermissionError) as e:
            logger.error(f"Error loading index from {self.index_path}: {e}")
            raise DatabaseError(f"Falha ao carregar o índice. Erro: {e}")

    def _save_index(self, index: Dict[str, Dict[str, Union[int, bool]]]):
        try:
            with filelock.FileLock(f"{self.index_path}.lock", timeout=self.lock_timeout):
                with open(self.index_path, 'w', encoding=APP_CONFIG["DEFAULT_ENCODING"]) as f:
                    json.dump(index, f, indent=4)
        except IOError as e:
            logger.error(f"Error saving index to {self.index_path}: {e}")
            raise DatabaseError(f"Falha ao salvar o índice. Erro: {e}")

    def write_record(self, data_obj: DataObject) -> int:
        record_id = self.current_id
        data_obj.id_registro = record_id # Use the new property for id
        data_obj.deleted = False

        record_data = json.dumps(data_obj.to_dict(include_deleted=True), ensure_ascii=False) + '\n'
        record_bytes = record_data.encode(APP_CONFIG["DEFAULT_ENCODING"])
        record_size = len(record_bytes)

        try:
            with filelock.FileLock(f"{self.db_path}.lock", timeout=self.lock_timeout):
                with open(self.db_path, 'ab') as f: # Open in append binary mode
                    offset = f.tell()
                    f.write(record_bytes)

                index = self._load_index()
                index[str(record_id)] = {"offset": offset, "size": record_size, "deleted": False}
                self._save_index(index)

                self.current_id += 1
                self._save_id_counter(self.current_id)
                logger.info(f"Record {record_id} added at offset {offset}.")
                return record_id
        except filelock.Timeout:
            raise DatabaseError(f"Timeout acquiring database lock. Please try again.")
        except IOError as e:
            logger.error(f"Failed to write record {record_id} to DB file: {e}")
            raise DatabaseError(f"Falha ao escrever registro no banco de dados. Erro: {e}")

    def get_record(self, record_id: int) -> Optional[DataObject]:
        index = self._load_index()
        record_info = index.get(str(record_id))

        if not record_info or record_info.get("deleted"):
            logger.info(f"Record {record_id} not found or marked as deleted.")
            return None

        offset = record_info["offset"]
        size = record_info["size"]

        try:
            with filelock.FileLock(f"{self.db_path}.lock", timeout=self.lock_timeout):
                with open(self.db_path, 'rb') as f:
                    f.seek(offset)
                    record_bytes = f.read(size)
                record_data = record_bytes.decode(APP_CONFIG["DEFAULT_ENCODING"])
                data_dict = json.loads(record_data)
                return DataObject.from_dict(data_dict) # This now correctly calls the new from_dict
        except filelock.Timeout:
            raise DatabaseError(f"Timeout acquiring database lock. Please try again.")
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to read or parse record {record_id} from DB file: {e}")
            raise DatabaseError(f"Falha ao ler ou processar registro {record_id}. Erro: {e}")

    def update_record(self, updated_data_obj: DataObject) -> bool:
        # The new DataObject uses id_registro, which is mapped to id property
        if updated_data_obj.id is None: # Use the id property
            raise DataValidationError("Record ID is required for update.")

        index = self._load_index()
        record_info = index.get(str(updated_data_obj.id)) # Use the id property

        if not record_info or record_info.get("deleted"):
            raise RecordNotFoundError(f"Record with ID {updated_data_obj.id} not found or already deleted for update.")

        # Mark old record as deleted in index
        index[str(updated_data_obj.id)]["deleted"] = True # Use the id property
        self._save_index(index)
        logger.info(f"Record {updated_data_obj.id} marked as deleted for update.")

        # Write new version of the record
        new_id = self.write_record(updated_data_obj)
        logger.info(f"Record {updated_data_obj.id} updated to new record with ID {new_id}.")
        return True

    def delete_record(self, record_id: int) -> bool:
        index = self._load_index()
        record_info = index.get(str(record_id))

        if not record_info or record_info.get("deleted"):
            logger.info(f"Record {record_id} already deleted or not found.")
            return False

        # Mark record as deleted in index
        index[str(record_id)]["deleted"] = True
        self._save_index(index)
        logger.info(f"Record {record_id} marked as deleted.")
        return True

    def get_all_records(self, include_deleted: bool = False) -> List[DataObject]:
        records = []
        index = self._load_index()
        try:
            with filelock.FileLock(f"{self.db_path}.lock", timeout=self.lock_timeout):
                with open(self.db_path, 'rb') as f:
                    for record_id_str, info in index.items():
                        if not include_deleted and info.get("deleted"):
                            continue
                        try:
                            f.seek(info["offset"])
                            record_bytes = f.read(info["size"])
                            record_data = record_bytes.decode(APP_CONFIG["DEFAULT_ENCODING"])
                            data_dict = json.loads(record_data)
                            records.append(DataObject.from_dict(data_dict))
                        except (IOError, json.JSONDecodeError) as e:
                            logger.error(f"Error reading record {record_id_str} during get_all_records: {e}")
                            # Optionally, mark this record as corrupted in index or skip
                            continue
        except filelock.Timeout:
            raise DatabaseError(f"Timeout acquiring database lock during get_all_records. Please try again.")
        except IOError as e:
            logger.error(f"Failed to access DB file during get_all_records: {e}")
            raise DatabaseError(f"Falha ao acessar o banco de dados. Erro: {e}")
        return records

    def count_records(self) -> Tuple[int, int]:
        index = self._load_index()
        total = len(index)
        deleted = sum(1 for info in index.values() if info.get("deleted"))
        return total, deleted

    def compact_db(self, progress_callback: Optional[Callable[[float], None]] = None):
        total_records, deleted_records = self.count_records()
        if total_records == 0 or deleted_records == 0:
            logger.info("No records to compact or no deleted records found.")
            if progress_callback: progress_callback(1.0)
            return

        percentage_deleted = (deleted_records / total_records) * 100
        if percentage_deleted < APP_CONFIG["COMPACTION_THRESHOLD_PERCENT"]:
            logger.info(f"Deleted records ({percentage_deleted:.2f}%) below threshold ({APP_CONFIG['COMPACTION_THRESHOLD_PERCENT']}%). Skipping compaction.")
            if progress_callback: progress_callback(1.0)
            return

        logger.info(f"Starting database compaction. Deleted records: {deleted_records}/{total_records} ({percentage_deleted:.2f}%).")
        temp_db_path = self.db_path.with_suffix('.db.tmp')
        new_index = {}
        offset = 0
        records_processed = 0

        all_records = self.get_all_records(include_deleted=True)
        total_non_deleted = sum(1 for rec in all_records if not rec.deleted)

        try:
            with filelock.FileLock(f"{self.db_path}.lock", timeout=self.lock_timeout):
                with open(temp_db_path, 'wb') as temp_f:
                    for record_obj in all_records:
                        if not record_obj.deleted:
                            # Use id_registro for index consistency
                            record_data = json.dumps(record_obj.to_dict(include_deleted=True), ensure_ascii=False) + '\n'
                            record_bytes = record_data.encode(APP_CONFIG["DEFAULT_ENCODING"])
                            record_size = len(record_bytes)

                            temp_f.write(record_bytes)
                            new_index[str(record_obj.id)] = {"offset": offset, "size": record_size, "deleted": False} # Use record_obj.id which maps to id_registro
                            offset += record_size
                            records_processed += 1

                            if progress_callback and total_non_deleted > 0:
                                progress = records_processed / total_non_deleted
                                progress_callback(progress)

                # Atomically replace old files with new ones
                shutil.move(temp_db_path, self.db_path)
                self._save_index(new_index) # Save the new index
                logger.info("Database compaction completed successfully.")
                if progress_callback: progress_callback(1.0)

        except filelock.Timeout:
            logger.error("Timeout during database compaction. Compaction aborted.")
            st.error("Erro: Tempo limite excedido ao tentar compactar o banco de dados. Tente novamente.")
            if temp_db_path.exists():
                os.remove(temp_db_path)
            raise DatabaseError("Compaction timeout.")
        except (IOError, OSError) as e:
            logger.error(f"Error during database compaction: {e}")
            st.error(f"Erro ao compactar o banco de dados: {e}")
            if temp_db_path.exists():
                os.remove(temp_db_path)
            raise DatabaseError(f"Falha na compactação do banco de dados. Erro: {e}")

    def search_records(self, field: str, query: str) -> List[DataObject]:
        found_records = []
        all_records = self.get_all_records() # Get only non-deleted records
        query_lower = query.lower()

        for record in all_records:
            record_dict = record.to_dict(include_deleted=True) # Get the dictionary representation including potentially original list values
            # Need to get the raw internal list value for proper search on LIST_FIELDS
            internal_value = record._data.get(field) # Access the internal _data dict directly for true list content

            if field in record_dict:
                if field in DataObject.LIST_FIELDS and isinstance(internal_value, list):
                    # Search within list items
                    if any(query_lower in str(item).lower() for item in internal_value):
                        found_records.append(record)
                else:
                    value = record_dict[field] # Use the string representation for other fields
                    if isinstance(value, str) and query_lower in value.lower():
                        found_records.append(record)
                    elif isinstance(value, (int, float)):
                        # Handle exact match for numeric types
                        try:
                            if float(query) == float(value):
                                found_records.append(record)
                        except ValueError:
                            pass # Query is not a valid number, skip numeric comparison
                    elif isinstance(value, date) and query_lower in value.isoformat().lower():
                        found_records.append(record)
        return found_records


    def export_to_csv(self, file_path: Path, progress_callback: Optional[Callable[[float], None]] = None):
        all_records = self.get_all_records()
        if not all_records:
            logger.info("No records to export to CSV.")
            if progress_callback: progress_callback(1.0)
            return

        # Dynamically determine all possible fields from the first record's to_dict
        # This ensures all fields, including those unique to specific records, are included
        # and correctly mapped from the new DataObject's internal structure.
        first_record_dict = all_records[0].to_dict(include_deleted=True)
        fieldnames = sorted(list(first_record_dict.keys()))
        
        # Define a desired order for critical fields, if they exist in the new structure
        # The new DataObject has different field names, so this list needs to be updated.
        ordered_fieldnames_priority = [
            "id", "crash_date", "data_local", "crash_hour", "crash_day_of_week", "crash_month",
            "injuries_total", "injuries_fatal", "injuries_incapacitating",
            "injuries_non_incapacitating", "injuries_reported_not_evident", "injuries_no_indication",
            "num_units", "traffic_control_device", "weather_condition", "lighting_condition",
            "first_crash_type", "trafficway_type", "alignment", "roadway_surface_cond",
            "road_defect", "crash_type", "intersection_related_i", "damage",
            "prim_contributory_cause", "most_severe_injury"
        ]
        
        ordered_fieldnames = []
        for field in ordered_fieldnames_priority:
            if field in fieldnames and field not in ordered_fieldnames:
                ordered_fieldnames.append(field)
        
        # Add any remaining fields that were not in the priority list
        for field in fieldnames:
            if field not in ordered_fieldnames:
                ordered_fieldnames.append(field)

        # Remove 'deleted' if it's not strictly necessary for export
        if 'deleted' in ordered_fieldnames:
            ordered_fieldnames.remove('deleted')

        try:
            with open(file_path, 'w', newline='', encoding=APP_CONFIG["DEFAULT_ENCODING"]) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=ordered_fieldnames, delimiter=APP_CONFIG["CSV_DELIMITER"])
                writer.writeheader()
                for i, record in enumerate(all_records):
                    # Use to_dict without include_deleted for export, which will handle joining LIST_FIELDS
                    row_to_write = record.to_dict(include_deleted=False) 
                    writer.writerow(row_to_write)
                    if progress_callback:
                        progress_callback((i + 1) / len(all_records))
            logger.info(f"Exported {len(all_records)} records to {file_path}")
            if progress_callback: progress_callback(1.0)
            return True
        except IOError as e:
            logger.error(f"Error exporting to CSV {file_path}: {e}")
            raise DatabaseError(f"Falha ao exportar para CSV. Erro: {e}")

    def import_from_csv(self, file_buffer: io.BytesIO, overwrite_existing: bool = False, progress_callback: Optional[Callable[[float], None]] = None):
        temp_file_path = None
        try:
            # Write buffer to a temporary file to allow csv.DictReader to work properly
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp_file:
                tmp_file.write(file_buffer.read())
                temp_file_path = Path(tmp_file.name)

            imported_count = 0
            skipped_count = 0
            errors = []
            
            with open(temp_file_path, 'r', encoding=APP_CONFIG["DEFAULT_ENCODING"]) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=APP_CONFIG["CSV_DELIMITER"])
                rows = list(reader) # Read all rows into memory to get total count for progress
                total_rows = len(rows)

                if not reader.fieldnames:
                    raise DataValidationError("CSV file is empty or missing headers.")

                for i, row in enumerate(rows):
                    row_data = {k.strip(): v.strip() for k, v in row.items()}
                    record_id = row_data.get("id") # Keep this as 'id' from CSV for lookup

                    existing_record = None
                    if record_id:
                        try:
                            existing_record = self.get_record(int(record_id))
                        except (ValueError, DatabaseError):
                            # ID from CSV might not be an int, or DB error
                            pass

                    if existing_record:
                        if overwrite_existing:
                            try:
                                # Mark existing record as deleted and add new
                                self.delete_record(int(record_id))
                                # Pass row_data directly to the new DataObject constructor
                                # DataObject's constructor will handle splitting LIST_FIELDS
                                new_record_obj = DataObject(row_data) 
                                self.write_record(new_record_obj)
                                imported_count += 1
                                logger.info(f"Record ID {record_id} overwritten from CSV.")
                            except (DataValidationError, DatabaseError, Exception) as e:
                                errors.append(f"Row {i+2} (ID: {record_id}) - Overwrite failed: {e}")
                                logger.warning(f"Failed to overwrite record {record_id} from CSV: {e}")
                                skipped_count += 1
                        else:
                            skipped_count += 1
                            logger.info(f"Skipping existing record ID {record_id} (overwrite not enabled).")
                            errors.append(f"Row {i+2} (ID: {record_id}) - Skipped (record exists, overwrite not enabled).")
                    else:
                        try:
                            # Create new DataObject, let write_record assign new ID
                            # DataObject's constructor will handle splitting LIST_FIELDS
                            new_record_obj = DataObject(row_data) 
                            self.write_record(new_record_obj)
                            imported_count += 1
                        except (DataValidationError, DatabaseError, Exception) as e:
                            errors.append(f"Row {i+2} (ID: {record_id if record_id else 'N/A'}) - Import failed: {e}")
                            logger.warning(f"Failed to import row {i+2} from CSV: {e}")
                            skipped_count += 1
                    if progress_callback:
                        progress_callback((i + 1) / total_rows)
                if progress_callback: progress_callback(1.0)
                return imported_count, skipped_count, errors
        except (IOError, UnicodeDecodeError) as e:
            logger.error(f"Error reading CSV file {temp_file_path}: {e}")
            raise DatabaseError(f"Falha ao ler o arquivo CSV. Verifique o formato e a codificação. Erro: {e}")
        except csv.Error as e:
            logger.error(f"CSV parsing error: {e}")
            raise DatabaseError(f"Erro de análise CSV: {e}. Verifique o delimitador e o formato.")
        finally:
            if temp_file_path and temp_file_path.exists():
                os.remove(temp_file_path)

# --- BTreeDBManager (Placeholder - Inherits from DBManager for now) ---
class BTreeDBManager(DBManager):
    def __init__(self, db_path: Path, index_path: Path, id_counter_path: Path, lock_timeout: int = 10):
        super().__init__(db_path, index_path, id_counter_path, lock_timeout)
        logger.info("BTreeDBManager initialized. Currently using flat-file DBManager implementation as placeholder.")
    # TODO: Implement actual B-Tree indexing logic here
    # This would involve managing B-Tree nodes on disk,
    # and modifying write_record, get_record, update_record, delete_record
    # to interact with the B-Tree structure instead of the simple JSON index.

# --- Cryptography Utilities ---
class CryptographyHandler:
    def __init__(self, public_key_path: Path, private_key_path: Path):
        self.public_key_path = public_key_path
        self.private_key_path = private_key_path
        self._ensure_key_dir()

    def _ensure_key_dir(self):
        self.public_key_path.parent.mkdir(parents=True, exist_ok=True)

    def generate_rsa_keys(self, password: Optional[str] = None):
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()

            # Serialize private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption() if password is None else serialization.BestAvailableEncryption(password.encode(APP_CONFIG["DEFAULT_ENCODING"]))
            )

            # Serialize public key
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            with open(self.private_key_path, "wb") as f:
                f.write(private_pem)
            with open(self.public_key_path, "wb") as f:
                f.write(public_pem)
            logger.info(f"RSA keys generated and saved to {self.private_key_path} and {self.public_key_path}")
        except Exception as e:
            logger.error(f"Error generating RSA keys: {traceback.format_exc()}")
            raise EncryptionError(f"Falha ao gerar chaves RSA: {e}")

    def _load_public_key(self):
        try:
            with open(self.public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            return public_key
        except (FileNotFoundError, ValueError) as e:
            raise EncryptionError(f"Falha ao carregar chave pública. Verifique o caminho e formato. Erro: {e}")

    def _load_private_key(self, password: Optional[str] = None):
        try:
            with open(self.private_key_path, "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=password.encode(APP_CONFIG["DEFAULT_ENCODING"]) if password else None,
                    backend=default_backend()
                )
            return private_key
        except (FileNotFoundError, ValueError, InvalidKey) as e: # Catch InvalidKey specifically for wrong password/corrupted key
            raise EncryptionError(f"Falha ao carregar chave privada. Verifique o caminho, formato ou senha. Erro: {e}")

    def encrypt_file_hybrid(self, input_file_path: Path, output_file_path: Path, progress_callback: Optional[Callable[[float], None]] = None):
        public_key = self._load_public_key()
        aes_key = os.urandom(32) # AES256 key
        iv = os.urandom(16) # AES CBC IV
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Encrypt AES key with RSA public key
        encrypted_aes_key = public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        try:
            file_size = input_file_path.stat().st_size
            bytes_processed = 0
            with open(input_file_path, 'rb') as infile, open(output_file_path, 'wb') as outfile:
                # Write encrypted AES key length, IV length, encrypted AES key, and IV
                outfile.write(len(encrypted_aes_key).to_bytes(4, 'big'))
                outfile.write(len(iv).to_bytes(4, 'big'))
                outfile.write(encrypted_aes_key)
                outfile.write(iv)

                while True:
                    chunk = infile.read(APP_CONFIG["CHUNK_SIZE"])
                    if not chunk:
                        break
                    encrypted_chunk = encryptor.update(chunk)
                    outfile.write(encrypted_chunk)
                    bytes_processed += len(chunk)
                    if progress_callback:
                        progress_callback(bytes_processed / file_size)

                # Finalize encryption
                outfile.write(encryptor.finalize())
            logger.info(f"File '{input_file_path}' encrypted to '{output_file_path}'.")
            if progress_callback: progress_callback(1.0)
        except Exception as e:
            logger.error(f"Error encrypting file {input_file_path}: {traceback.format_exc()}")
            raise EncryptionError(f"Falha ao criptografar o arquivo {input_file_path.name}. Erro: {e}")
        finally:
            if progress_callback: progress_callback(1.0)

    def decrypt_file_hybrid(self, input_file_path: Path, output_file_path: Path, password: Optional[str] = None, progress_callback: Optional[Callable[[float], None]] = None):
        private_key = self._load_private_key(password)

        try:
            with open(input_file_path, 'rb') as infile:
                encrypted_aes_key_len = int.from_bytes(infile.read(4), 'big')
                iv_len = int.from_bytes(infile.read(4), 'big')
                encrypted_aes_key = infile.read(encrypted_aes_key_len)
                iv = infile.read(iv_len)

                # Decrypt AES key with RSA private key
                aes_key = private_key.decrypt(
                    encrypted_aes_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

                cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
                decryptor = cipher.decryptor()

                file_size = input_file_path.stat().st_size
                # Adjust total_size for progress bar calculation
                # Subtract header size (4 bytes for encrypted_aes_key_len + 4 for iv_len + encrypted_aes_key_len + iv_len)
                data_start_offset = 4 + 4 + encrypted_aes_key_len + iv_len
                bytes_processed = 0

                with open(output_file_path, 'wb') as outfile:
                    infile.seek(data_start_offset) # Ensure we start reading from the actual encrypted data
                    while True:
                        chunk = infile.read(APP_CONFIG["CHUNK_SIZE"])
                        if not chunk:
                            break
                        decrypted_chunk = decryptor.update(chunk)
                        outfile.write(decrypted_chunk)
                        bytes_processed += len(chunk)
                        if progress_callback:
                            # Calculate progress based on actual encrypted data size, not total file size
                            progress = bytes_processed / (file_size - data_start_offset)
                            progress_callback(progress)

                    outfile.write(decryptor.finalize())
            logger.info(f"File '{input_file_path}' decrypted to '{output_file_path}'.")
            if progress_callback: progress_callback(1.0)
        except InvalidKey as e:
            logger.error(f"Incorrect password or corrupted private key for {input_file_path}: {e}")
            raise EncryptionError("Senha incorreta ou chave privada corrompida. Tente novamente.")
        except Exception as e:
            logger.error(f"Error decrypting file {input_file_path}: {traceback.format_exc()}")
            raise EncryptionError(f"Falha ao descriptografar o arquivo {input_file_path.name}. Erro: {e}")
        finally:
            if progress_callback: progress_callback(1.0)

# --- Compression Utilities (LZW and Huffman) ---
class LZWCompressor:
    # LZW implementation from previous versions, kept for completeness
    # Ensure it works with bytes for compression
    def compress(self, uncompressed_data: bytes) -> bytes:
        """Compress a string to a list of output symbols."""
        # Build the dictionary.
        dictionary_size = 256
        dictionary = {bytes([i]): i for i in range(dictionary_size)}
        
        w = b""
        result = bytearray()
        for c_byte in uncompressed_data:
            c = bytes([c_byte])
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                result.extend(dictionary[w].to_bytes(2, 'big')) # Use 2 bytes for codes
                # Add wc to the dictionary.
                if dictionary_size < 65536: # Limit dictionary size to 2^16
                    dictionary[wc] = dictionary_size
                    dictionary_size += 1
                w = c
        # Output the code for w.
        if w:
            result.extend(dictionary[w].to_bytes(2, 'big'))
        return bytes(result)

    def decompress(self, compressed_data: bytes) -> bytes:
        """Decompress a list of output kwcodes to a string."""
        # Build the dictionary.
        dictionary_size = 256
        dictionary = {i: bytes([i]) for i in range(dictionary_size)}

        # Use a deque for efficient popping from the left
        compressed_codes = deque()
        for i in range(0, len(compressed_data), 2):
            compressed_codes.append(int.from_bytes(compressed_data[i:i+2], 'big'))

        if not compressed_codes:
            return b""

        w = dictionary[compressed_codes.popleft()]
        result = bytearray(w)
        for k in compressed_codes:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dictionary_size:
                entry = w + bytes([w[0]])
            else:
                raise ValueError('Bad compressed k: %d' % k)
            result.extend(entry)

            # Add w+entry[0] to the dictionary.
            if dictionary_size < 65536:
                dictionary[dictionary_size] = w + bytes([entry[0]])
                dictionary_size += 1
            w = entry
        return bytes(result)

class HuffmanCompressor:
    # Huffman implementation from previous versions, kept for completeness
    # Ensure it works with bytes
    class Node:
        def __init__(self, char, freq):
            self.char = char
            self.freq = freq
            self.left = None
            self.right = None

        def __lt__(self, other):
            return self.freq < other.freq

    def build_huffman_tree(self, data: bytes):
        frequency = defaultdict(int)
        for byte_char in data:
            frequency[byte_char] += 1

        priority_queue = [self.Node(char, freq) for char, freq in frequency.items()]
        heapq.heapify(priority_queue)

        while len(priority_queue) > 1:
            left = heapq.heappop(priority_queue)
            right = heapq.heappop(priority_queue)
            merged = self.Node(None, left.freq + right.freq)
            merged.left = left
            merged.right = right
            heapq.heappush(priority_queue, merged)
        
        return priority_queue[0] if priority_queue else None

    def build_codes(self, node, current_code: str, codes: Dict[int, str]):
        if node is None:
            return
        if node.char is not None:
            codes[node.char] = current_code if current_code else "0" # Handle single character case
            return

        self.build_codes(node.left, current_code + "0", codes)
        self.build_codes(node.right, current_code + "1", codes)

    def bytes_to_bits(self, byte_data: bytes) -> str:
        return ''.join(format(byte, '08b') for byte in byte_data)

    def bits_to_bytes(self, bit_string: str) -> bytes:
        # Pad with zeros to make length a multiple of 8
        padding_needed = 8 - (len(bit_string) % 8)
        if padding_needed == 8: # If already a multiple of 8, no padding needed
            padding_needed = 0
        padded_bit_string = bit_string + '0' * padding_needed
        
        byte_array = bytearray()
        for i in range(0, len(padded_bit_string), 8):
            byte_array.append(int(padded_bit_string[i:i+8], 2))
        return bytes(byte_array), padding_needed


    def compress(self, data: bytes) -> Tuple[bytes, Dict[int, str], int]:
        if not data:
            return b"", {}, 0
        root = self.build_huffman_tree(data)
        codes = {}
        self.build_codes(root, "", codes)

        encoded_bits = "".join(codes[byte_char] for byte_char in data)
        compressed_bytes, padding_info = self.bits_to_bytes(encoded_bits)
        
        # Convert codes dictionary keys back to strings for JSON serialization
        # And convert values to string if they are not already
        serializable_codes = {str(k): v for k, v in codes.items()}
        return compressed_bytes, serializable_codes, padding_info

    def decompress(self, compressed_bytes: bytes, codes: Dict[str, str], padding_info: int) -> bytes:
        if not compressed_bytes:
            return b""

        # Reconstruct codes with integer keys
        huffman_codes = {int(k): v for k, v in codes.items()}
        # Create a reverse lookup for decompression
        reverse_huffman_codes = {v: k for k, v in huffman_codes.items()}

        # Convert compressed bytes to bit string
        bit_string = "".join(format(byte, '08b') for byte in compressed_bytes)
        
        # Remove padding
        if padding_info > 0:
            bit_string = bit_string[:-padding_info]

        current_code = ""
        decompressed_bytes = bytearray()
        for bit in bit_string:
            current_code += bit
            if current_code in reverse_huffman_codes:
                decompressed_bytes.append(reverse_huffman_codes[current_code])
                current_code = ""
        
        return bytes(decompressed_bytes)


class CompressionManager:
    def __init__(self, db_manager: DBManager, lzw_folder: Path, huffman_folder: Path):
        self.db_manager = db_manager
        self.lzw_folder = lzw_folder
        self.huffman_folder = huffman_folder
        self.lzw_compressor = LZWCompressor()
        self.huffman_compressor = HuffmanCompressor()
        self._ensure_compression_dirs()

    def _ensure_compression_dirs(self):
        self.lzw_folder.mkdir(parents=True, exist_ok=True)
        self.huffman_folder.mkdir(parents=True, exist_ok=True)

    def _get_db_content_for_compression(self) -> bytes:
        """Reads the raw content of the database file."""
        try:
            with filelock.FileLock(f"{self.db_manager.db_path}.lock", timeout=self.db_manager.lock_timeout):
                with open(self.db_manager.db_path, 'rb') as f:
                    return f.read()
        except filelock.Timeout:
            raise DatabaseError("Timeout acquiring DB lock for compression.")
        except IOError as e:
            raise DatabaseError(f"Error reading DB file for compression: {e}")

    def _write_compressed_data(self, file_path: Path, compressed_data: bytes, metadata: Dict[str, Any]):
        try:
            with open(file_path, 'wb') as f:
                f.write(json.dumps(metadata).encode(APP_CONFIG["DEFAULT_ENCODING"]) + b'\n')
                f.write(compressed_data)
        except IOError as e:
            raise DatabaseError(f"Error writing compressed file {file_path}: {e}")

    def _read_compressed_data(self, file_path: Path) -> Tuple[bytes, Dict[str, Any]]:
        try:
            with open(file_path, 'rb') as f:
                header_bytes = f.readline()
                metadata = json.loads(header_bytes.strip().decode(APP_CONFIG["DEFAULT_ENCODING"]))
                compressed_data = f.read()
                return compressed_data, metadata
        except (IOError, json.JSONDecodeError) as e:
            raise DatabaseError(f"Error reading compressed file or metadata {file_path}: {e}")

    def compress_db_lzw(self, output_file_name: str, progress_callback: Optional[Callable[[float], None]] = None):
        logger.info("Starting LZW compression of the database.")
        raw_db_content = self._get_db_content_for_compression()
        
        try:
            compressed_content = self.lzw_compressor.compress(raw_db_content)
            output_path = self.lzw_folder / output_file_name
            metadata = {
                "original_size": len(raw_db_content),
                "compressed_size": len(compressed_content),
                "compression_type": "LZW",
                "timestamp": datetime.now().isoformat()
            }
            self._write_compressed_data(output_path, compressed_content, metadata)
            logger.info(f"LZW compression successful. Original: {len(raw_db_content)} bytes, Compressed: {len(compressed_content)} bytes. Saved to {output_path}")
            if progress_callback: progress_callback(1.0)
            return output_path, metadata
        except Exception as e:
            logger.error(f"LZW compression failed: {traceback.format_exc()}")
            raise DatabaseError(f"Falha na compressão LZW: {e}")

    def decompress_db_lzw(self, input_file_name: str, output_file_path: Path, progress_callback: Optional[Callable[[float], None]] = None):
        logger.info("Starting LZW decompression of the database.")
        input_path = self.lzw_folder / input_file_name
        compressed_content, metadata = self._read_compressed_data(input_path)
        
        try:
            decompressed_content = self.lzw_compressor.decompress(compressed_content)
            with open(output_file_path, 'wb') as f:
                f.write(decompressed_content)
            logger.info(f"LZW decompression successful. Decompressed size: {len(decompressed_content)} bytes. Saved to {output_file_path}")
            if progress_callback: progress_callback(1.0)
            return output_file_path
        except Exception as e:
            logger.error(f"LZW decompression failed: {traceback.format_exc()}")
            raise DatabaseError(f"Falha na descompressão LZW: {e}")

    def compress_db_huffman(self, output_file_name: str, progress_callback: Optional[Callable[[float], None]] = None):
        logger.info("Starting Huffman compression of the database.")
        raw_db_content = self._get_db_content_for_compression()

        try:
            compressed_content, codes, padding_info = self.huffman_compressor.compress(raw_db_content)
            output_path = self.huffman_folder / output_file_name
            metadata = {
                "original_size": len(raw_db_content),
                "compressed_size": len(compressed_content),
                "compression_type": "Huffman",
                "timestamp": datetime.now().isoformat(),
                "huffman_codes": codes, # Store codes to decompress
                "padding_info": padding_info # Store padding info
            }
            self._write_compressed_data(output_path, compressed_content, metadata)
            logger.info(f"Huffman compression successful. Original: {len(raw_db_content)} bytes, Compressed: {len(compressed_content)} bytes. Saved to {output_path}")
            if progress_callback: progress_callback(1.0)
            return output_path, metadata
        except Exception as e:
            logger.error(f"Huffman compression failed: {traceback.format_exc()}")
            raise DatabaseError(f"Falha na compressão Huffman: {e}")

    def decompress_db_huffman(self, input_file_name: str, output_file_path: Path, progress_callback: Optional[Callable[[float], None]] = None):
        logger.info("Starting Huffman decompression of the database.")
        input_path = self.huffman_folder / input_file_name
        compressed_content, metadata = self._read_compressed_data(input_path)
        
        try:
            codes = metadata.get("huffman_codes")
            padding_info = metadata.get("padding_info", 0)
            if not codes:
                raise ValueError("Huffman codes not found in metadata.")
            
            decompressed_content = self.huffman_compressor.decompress(compressed_content, codes, padding_info)
            with open(output_file_path, 'wb') as f:
                f.write(decompressed_content)
            logger.info(f"Huffman decompression successful. Decompressed size: {len(decompressed_content)} bytes. Saved to {output_file_path}")
            if progress_callback: progress_callback(1.0)
            return output_file_path
        except Exception as e:
            logger.error(f"Huffman decompression failed: {traceback.format_exc()}")
            raise DatabaseError(f"Falha na descompressão Huffman: {e}")


# --- Streamlit UI Functions (Moved from main to organize) ---
# These functions will be called by setup_ui in the main block

db_manager = BTreeDBManager(
    db_path=APP_CONFIG["DB_PATH"],
    index_path=APP_CONFIG["INDEX_PATH"],
    id_counter_path=APP_CONFIG["ID_COUNTER_PATH"],
    lock_timeout=APP_CONFIG["LOCK_TIMEOUT"]
)
crypto_handler = CryptographyHandler(
    public_key_path=APP_CONFIG["PUBLIC_KEY_PATH"],
    private_key_path=APP_CONFIG["PRIVATE_KEY_PATH"]
)
compression_manager = CompressionManager(
    db_manager=db_manager,
    lzw_folder=APP_CONFIG["LZW_FOLDER"],
    huffman_folder=APP_CONFIG["HUFFMAN_FOLDER"]
)

def render_home_section():
    st.header("🏠 Bem-vindo ao Gerenciador de Acidentes de Trânsito")
    st.write("""
        Esta aplicação permite gerenciar um banco de dados de acidentes de trânsito.
        Você pode adicionar, visualizar, atualizar, excluir e buscar registros.
        Funcionalidades avançadas incluem compressão e criptografia dos dados.
    """)
    st.info("Utilize as abas acima para navegar pelas funcionalidades.")

def render_add_record_section():
    st.header("➕ Adicionar Novo Registro")
    with st.form("add_record_form"):
        st.subheader("Detalhes do Acidente")
        # Update input fields to match new DataObject's REQUIRED_FIELDS and other properties
        # For simplicity, let's use text input for all string fields and number input for numeric
        # You might want to use st.date_input, st.time_input etc. for better UX

        # Using text_input for all fields for now to allow for flexible data entry
        # and rely on DataObject's internal validation.
        input_data = {}
        # Get all properties from DataObject dynamically, excluding the removed fields
        all_data_object_properties = [
            "crash_date", "traffic_control_device", "weather_condition", "lighting_condition",
            "first_crash_type", "trafficway_type", "alignment", "roadway_surface_cond",
            "road_defect", "crash_type", "intersection_related_i", "damage",
            "prim_contributory_cause", "num_units", "most_severe_injury", "injuries_total",
            "injuries_fatal", "injuries_incapacitating", "injuries_non_incapacitating",
            "injuries_reported_not_evident", "injuries_no_indication", "crash_hour",
            "crash_day_of_week", "crash_month", "data_local"
        ]

        for field in all_data_object_properties:
            label = f"*{field.replace('_', ' ').title()}*" if field in DataObject.REQUIRED_FIELDS else f"{field.replace('_', ' ').title()}"
            if field in ["injuries_total", "injuries_fatal", "injuries_incapacitating", 
                         "injuries_non_incapacitating", "injuries_reported_not_evident", 
                         "injuries_no_indication", "num_units", "crash_hour", 
                         "crash_day_of_week", "crash_month"]:
                input_data[field] = st.number_input(label, value=0, format="%d", key=f"add_{field}_num")
            else:
                # For LIST_FIELDS, prompt for comma/slash separated string
                if field in DataObject.LIST_FIELDS:
                    st.markdown(f"**{label}** (separar por vírgula ou barra '/'):")
                input_data[field] = st.text_input(label, key=f"add_{field}")


        submitted = st.form_submit_button("Adicionar Registro")
        if submitted:
            try:
                # The DataObject constructor now expects a dictionary
                new_data_obj = DataObject(input_data)
                record_id = db_manager.write_record(new_data_obj)
                st.success(f"Registro adicionado com sucesso! ID: **{record_id}**")
                logger.info(f"New record added with ID: {record_id}")
            except DataValidationError as e:
                st.error(f"Erro de validação: {e}")
                logger.warning(f"Data validation error on add: {e}")
            except DatabaseError as e:
                st.error(f"Erro no banco de dados: {e}")
                logger.error(f"Database error on add: {e}")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado: {e}")
                logger.critical(f"Unexpected error on add: {traceback.format_exc()}")

def render_view_records_section():
    st.header("📊 Visualizar Registros")
    
    # Pagination
    total_records, deleted_records = db_manager.count_records()
    st.info(f"Total de registros: {total_records} (Excluídos: {deleted_records})")

    records_per_page = st.slider("Registros por página", 10, 100, APP_CONFIG["MAX_RECORDS_PER_PAGE"])
    
    all_records = db_manager.get_all_records()
    non_deleted_records = [rec for rec in all_records if not rec.deleted]
    total_non_deleted = len(non_deleted_records)

    num_pages = math.ceil(total_non_deleted / records_per_page)
    current_page = st.number_input("Página", 1, num_pages if num_pages > 0 else 1, 1)

    start_idx = (current_page - 1) * records_per_page
    end_idx = start_idx + records_per_page
    records_to_display = non_deleted_records[start_idx:end_idx]

    if records_to_display:
        st.subheader(f"Registros (Página {current_page}/{num_pages})")
        
        # Convert DataObject list to list of dictionaries for Streamlit table
        display_data = []
        for record in records_to_display:
            # .to_dict() already handles joining LIST_FIELDS to strings
            display_data.append(record.to_dict()) 
        
        st.dataframe(display_data)

        # Download CSV
        csv_buffer = io.BytesIO()
        try:
            # Create a temporary path for the export function, then read its content
            temp_csv_path = Path(tempfile.gettempdir()) / "exported_traffic_accidents.csv"
            db_manager.export_to_csv(temp_csv_path)
            with open(temp_csv_path, 'rb') as f:
                csv_buffer.write(f.read())
            st.download_button(
                label="Download Dados em CSV",
                data=csv_buffer.getvalue(),
                file_name="traffic_accidents.csv",
                mime="text/csv",
                help="Baixa todos os registros não excluídos como um arquivo CSV."
            )
            os.remove(temp_csv_path) # Clean up temp file
        except Exception as e:
            st.error(f"Erro ao preparar CSV para download: {e}")
            logger.error(f"Error preparing CSV for download: {traceback.format_exc()}")

    else:
        st.info("Nenhum registro para exibir.")

def render_search_update_delete_section():
    st.header("🔍 Buscar, ✏️ Atualizar e 🗑️ Excluir Registros")

    search_id = st.number_input("Buscar registro por ID", min_value=1, format="%d")
    
    col1, col2 = st.columns(2)
    with col1:
        search_button = st.button("Buscar")
    with col2:
        clear_button = st.button("Limpar Busca")

    if 'found_record' not in st.session_state:
        st.session_state.found_record = None
    if 'record_id_to_update' not in st.session_state:
        st.session_state.record_id_to_update = None

    if search_button:
        if search_id:
            record = db_manager.get_record(search_id)
            if record:
                # When displaying for update, we need the raw list values for LIST_FIELDS
                # The DataObject._data dict holds these
                display_dict = record._data.copy()
                # Ensure 'id' is set for display purposes (even if stored as 'id_registro')
                display_dict['id'] = record.id_registro

                # For LIST_FIELDS, convert the list back to a comma-separated string for display in text_input
                for field in DataObject.LIST_FIELDS:
                    if field in display_dict and isinstance(display_dict[field], list):
                        display_dict[field] = record._join_list_to_string(display_dict[field])


                st.session_state.found_record = display_dict
                st.session_state.record_id_to_update = search_id
                st.success(f"Registro ID {search_id} encontrado.")
                logger.info(f"Record {search_id} found for display.")
            else:
                st.error(f"Registro com ID {search_id} não encontrado ou foi excluído.")
                st.session_state.found_record = None
                st.session_state.record_id_to_update = None
        else:
            st.warning("Por favor, insira um ID para buscar.")
    
    if clear_button:
        st.session_state.found_record = None
        st.session_state.record_id_to_update = None
        st.experimental_rerun() # Clear inputs by rerunning

    if st.session_state.found_record:
        st.subheader(f"Detalhes do Registro ID: {st.session_state.record_id_to_update}")
        
        # Display current data and allow editing
        updated_data = {}
        # Get all properties from DataObject dynamically, excluding the removed fields
        all_data_object_properties = [
            "id_registro", "crash_date", "data_local", "crash_hour", "crash_day_of_week",
            "crash_month", "injuries_total", "injuries_fatal", "injuries_incapacitating",
            "injuries_non_incapacitating", "injuries_reported_not_evident", "injuries_no_indication",
            "num_units", "traffic_control_device", "weather_condition", "lighting_condition",
            "first_crash_type", "trafficway_type", "alignment", "roadway_surface_cond",
            "road_defect", "crash_type", "intersection_related_i", "damage",
            "prim_contributory_cause", "most_severe_injury"
        ]

        for field in all_data_object_properties:
            # Get the value from the found_record dictionary (which already converted lists to strings for display)
            current_value = st.session_state.found_record.get(field, "")
            
            # Special handling for 'id' to be displayed but not editable
            if field == "id" or field == "id_registro":
                st.text_input(f"ID do Registro", value=str(current_value), disabled=True, key=f"edit_{field}")
                updated_data[field] = current_value # Keep the original ID
            elif field in ["injuries_total", "injuries_fatal", "injuries_incapacitating", 
                         "injuries_non_incapacitating", "injuries_reported_not_evident", 
                         "injuries_no_indication", "num_units", "crash_hour", 
                         "crash_day_of_week", "crash_month"]:
                # Cast to correct type if it's currently a string for number_input
                default_val = current_value if isinstance(current_value, (int, float)) else (0 if field in ["num_units", "crash_hour", "crash_day_of_week", "crash_month"] else 0.0)
                if isinstance(current_value, str) and current_value.replace('.', '', 1).isdigit():
                    default_val = int(current_value) if field in ["num_units", "crash_hour", "crash_day_of_week", "crash_month"] else float(current_value)
                
                updated_data[field] = st.number_input(
                    f"{field.replace('_', ' ').title()}", 
                    value=default_val, 
                    format="%d" if field in ["num_units", "crash_hour", "crash_day_of_week", "crash_month"] else "%.6f", 
                    key=f"edit_{field}_num"
                )
            else:
                # For LIST_FIELDS, display as string, will be split on DataObject init
                if field in DataObject.LIST_FIELDS:
                    st.markdown(f"**{field.replace('_', ' ').title()}** (separar por vírgula ou barra '/'):")
                updated_data[field] = st.text_input(f"{field.replace('_', ' ').title()}", value=str(current_value), key=f"edit_{field}")


        col_upd, col_del = st.columns(2)
        with col_upd:
            update_button = st.button("Atualizar Registro")
        with col_del:
            delete_button = st.button("Excluir Registro", help="Exclusão lógica do registro.")

        if update_button:
            try:
                # Ensure the 'id' (which maps to 'id_registro') is passed correctly to the new DataObject
                updated_data['id'] = st.session_state.record_id_to_update
                
                # The DataObject constructor will now automatically handle the string-to-list conversion
                # for the LIST_FIELDS based on the input from text_input
                updated_data_obj = DataObject(updated_data) 
                
                # Assign the original ID to the id_registro property for update logic
                updated_data_obj.id_registro = st.session_state.record_id_to_update

                if db_manager.update_record(updated_data_obj):
                    st.success(f"Registro ID {st.session_state.record_id_to_update} atualizado com sucesso!")
                    logger.info(f"Record {st.session_state.record_id_to_update} updated.")
                    st.session_state.found_record = None # Clear form after update
                    st.session_state.record_id_to_update = None
                    st.experimental_rerun()
                else:
                    st.error("Falha ao atualizar o registro.")
            except DataValidationError as e:
                st.error(f"Erro de validação ao atualizar: {e}")
                logger.warning(f"Data validation error on update: {e}")
            except RecordNotFoundError as e:
                st.error(f"Erro: {e}")
                logger.warning(f"Record not found for update: {e}")
            except DatabaseError as e:
                st.error(f"Erro no banco de dados ao atualizar: {e}")
                logger.error(f"Database error on update: {e}")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado ao atualizar: {e}")
                logger.critical(f"Unexpected error on update: {traceback.format_exc()}")

        if delete_button:
            if st.session_state.record_id_to_update:
                if st.warning(f"Tem certeza que deseja excluir o registro ID {st.session_state.record_id_to_update}?"):
                    if st.button("Confirmar Exclusão"):
                        try:
                            if db_manager.delete_record(st.session_state.record_id_to_update):
                                st.success(f"Registro ID {st.session_state.record_id_to_update} excluído com sucesso (lógica)!")
                                logger.info(f"Record {st.session_state.record_id_to_update} soft deleted.")
                                st.session_state.found_record = None # Clear form after delete
                                st.session_state.record_id_to_update = None
                                st.experimental_rerun()
                            else:
                                st.error("Falha ao excluir o registro.")
                        except DatabaseError as e:
                            st.error(f"Erro no banco de dados ao excluir: {e}")
                            logger.error(f"Database error on delete: {e}")
                        except Exception as e:
                            st.error(f"Ocorreu um erro inesperado ao excluir: {e}")
                            logger.critical(f"Unexpected error on delete: {traceback.format_exc()}")
            else:
                st.warning("Nenhum registro selecionado para exclusão.")

    st.subheader("Busca Avançada por Campo")
    # Updated search_field options to exclude removed fields
    search_field = st.selectbox("Selecione o campo para buscar", 
                                 options=sorted(list(set(DataObject.REQUIRED_FIELDS + [
                                     "id", "id_registro", "data_local"
                                 ]))),
                                 key="search_field_adv")
    search_query = st.text_input(f"Valor a buscar em '{search_field}'", key="search_query_adv")
    
    if st.button("Buscar por Campo"):
        if search_field and search_query:
            try:
                results = db_manager.search_records(search_field, search_query)
                if results:
                    st.subheader(f"Resultados da Busca para '{search_query}' em '{search_field}'")
                    display_results = [r.to_dict() for r in results] # .to_dict() will join LIST_FIELDS
                    st.dataframe(display_results)
                    st.success(f"Encontrados {len(results)} registros.")
                    logger.info(f"Search for '{search_query}' in '{search_field}' returned {len(results)} results.")
                else:
                    st.info("Nenhum registro encontrado com os critérios de busca.")
                    logger.info(f"Search for '{search_query}' in '{search_field}' returned no results.")
            except DatabaseError as e:
                st.error(f"Erro no banco de dados durante a busca: {e}")
                logger.error(f"Database error on advanced search: {e}")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado durante a busca: {e}")
                logger.critical(f"Unexpected error on advanced search: {traceback.format_exc()}")
        else:
            st.warning("Por favor, selecione um campo e insira um valor para buscar.")

def render_db_operations_section():
    st.header("🛠️ Operações do Banco de Dados")

    st.subheader("Importar Dados do CSV")
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=["csv"])
    overwrite_existing = st.checkbox("Sobrescrever registros existentes (se IDs corresponderem)", value=False)
    
    if uploaded_file is not None:
        if st.button("Importar CSV"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def import_progress(p):
                progress_bar.progress(p)
                status_text.text(f"Importando... {int(p*100)}%")

            try:
                file_buffer = io.BytesIO(uploaded_file.getvalue())
                imported_count, skipped_count, errors = db_manager.import_from_csv(
                    file_buffer, 
                    overwrite_existing=overwrite_existing, 
                    progress_callback=import_progress
                )
                st.success(f"Importação concluída. Importados: {imported_count}, Ignorados: {skipped_count}")
                if errors:
                    st.warning("Erros durante a importação:")
                    for error in errors:
                        st.code(error)
                logger.info(f"CSV import finished. Imported: {imported_count}, Skipped: {skipped_count}, Errors: {len(errors)}")
            except (DataValidationError, DatabaseError) as e:
                st.error(f"Erro na importação do CSV: {e}")
                logger.error(f"CSV import error: {traceback.format_exc()}")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado na importação: {e}")
                logger.critical(f"Unexpected error on CSV import: {traceback.format_exc()}")
            finally:
                progress_bar.empty()
                status_text.empty()

    st.subheader("Compactar Banco de Dados")
    st.info(f"A compactação remove fisicamente os registros logicamente excluídos. Isso é recomendado quando a porcentagem de registros excluídos atinge {APP_CONFIG['COMPACTION_THRESHOLD_PERCENT']}%.")
    total, deleted = db_manager.count_records()
    if total > 0:
        percent_deleted = (deleted / total) * 100
        st.write(f"Atualmente, {deleted} de {total} registros estão excluídos ({percent_deleted:.2f}%).")
    else:
        st.write("Banco de dados vazio.")

    if st.button("Executar Compactação"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        def compaction_progress(p):
            progress_bar.progress(p)
            status_text.text(f"Compactando... {int(p*100)}%")

        try:
            db_manager.compact_db(progress_callback=compaction_progress)
            st.success("Compactação do banco de dados concluída!")
            logger.info("Database compaction initiated and finished successfully.")
        except DatabaseError as e:
            st.error(f"Erro durante a compactação: {e}")
            logger.error(f"Database compaction error: {traceback.format_exc()}")
        finally:
            progress_bar.empty()
            status_text.empty()
            st.experimental_rerun() # Refresh stats

    st.subheader("Resetar Banco de Dados")
    if st.button("Resetar Tudo (Cuidado!)"):
        if st.warning("Esta ação é irreversível e excluirá TODOS os dados e o índice. Deseja continuar?"):
            if st.button("SIM, EXCLUIR TUDO PERMANENTEMENTE"):
                try:
                    with filelock.FileLock(f"{APP_CONFIG['DB_PATH']}.lock", timeout=APP_CONFIG["LOCK_TIMEOUT"]):
                        if APP_CONFIG["DB_PATH"].exists():
                            os.remove(APP_CONFIG["DB_PATH"])
                        if APP_CONFIG["INDEX_PATH"].exists():
                            os.remove(APP_CONFIG["INDEX_PATH"])
                        if APP_CONFIG["ID_COUNTER_PATH"].exists():
                            os.remove(APP_CONFIG["ID_COUNTER_PATH"])
                        # Reinitialize DBManager to recreate empty files and counter
                        db_manager.__init__(
                            db_path=APP_CONFIG["DB_PATH"],
                            index_path=APP_CONFIG["INDEX_PATH"],
                            id_counter_path=APP_CONFIG["ID_COUNTER_PATH"],
                            lock_timeout=APP_CONFIG["LOCK_TIMEOUT"]
                        )
                        st.success("Banco de dados, índice e contador de IDs foram resetados.")
                        logger.warning("All database files and index reset by user.")
                        st.experimental_rerun()
                except filelock.Timeout:
                    st.error("Timeout ao tentar obter o bloqueio para resetar o banco de dados. Tente novamente.")
                    logger.error("Timeout on DB reset lock.")
                except Exception as e:
                    st.error(f"Erro ao resetar o banco de dados: {e}")
                    logger.critical(f"Unexpected error on reset: {traceback.format_exc()}")

def render_compression_section():
    st.header("🗜️ Compressão de Dados")
    st.info("Comprima o banco de dados usando algoritmos LZW ou Huffman para economizar espaço.")

    compression_option = st.selectbox("Escolha o Algoritmo de Compressão", ["Nenhum", "LZW", "Huffman"])
    
    if compression_option == "LZW":
        st.subheader("Compressão/Descompressão LZW")
        lzw_output_name = st.text_input("Nome do arquivo LZW de saída (ex: db_compressed.lzw)", "traffic_accidents.lzw")
        if st.button("Comprimir DB (LZW)"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                output_path, metadata = compression_manager.compress_db_lzw(lzw_output_name, progress_callback=lambda p: (progress_bar.progress(p), status_text.text(f"Comprimindo... {int(p*100)}%")))
                st.success(f"Banco de dados compactado com LZW para: {output_path.name}")
                st.json(metadata)
            except DatabaseError as e:
                st.error(f"Erro na compressão LZW: {e}")
            finally:
                progress_bar.empty()
                status_text.empty()
        
        lzw_decompress_name = st.text_input("Nome do arquivo LZW para descomprimir (ex: db_compressed.lzw)", "traffic_accidents.lzw", key="decompress_lzw_name")
        if st.button("Descomprimir LZW para DB Original"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                # Decompress directly to the original DB path
                output_path = compression_manager.decompress_db_lzw(lzw_decompress_name, APP_CONFIG["DB_PATH"], progress_callback=lambda p: (progress_bar.progress(p), status_text.text(f"Descomprimindo... {int(p*100)}%")))
                st.success(f"Arquivo LZW descomprimido para o banco de dados original: {output_path.name}. **Lembre-se de que isso sobrescreve o DB existente.**")
                # After decompression, force re-load index and counter if needed
                db_manager._ensure_db_files()
                db_manager.current_id = db_manager._load_id_counter()
            except DatabaseError as e:
                st.error(f"Erro na descompressão LZW: {e}")
            finally:
                progress_bar.empty()
                status_text.empty()

    elif compression_option == "Huffman":
        st.subheader("Compressão/Descompressão Huffman")
        huffman_output_name = st.text_input("Nome do arquivo Huffman de saída (ex: db_compressed.huf)", "traffic_accidents.huf")
        if st.button("Comprimir DB (Huffman)"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                output_path, metadata = compression_manager.compress_db_huffman(huffman_output_name, progress_callback=lambda p: (progress_bar.progress(p), status_text.text(f"Comprimindo... {int(p*100)}%")))
                st.success(f"Banco de dados compactado com Huffman para: {output_path.name}")
                st.json(metadata)
            except DatabaseError as e:
                st.error(f"Erro na compressão Huffman: {e}")
            finally:
                progress_bar.empty()
                status_text.empty()
        
        huffman_decompress_name = st.text_input("Nome do arquivo Huffman para descomprimir (ex: db_compressed.huf)", "traffic_accidents.huf", key="decompress_huffman_name")
        if st.button("Descomprimir Huffman para DB Original"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                # Decompress directly to the original DB path
                output_path = compression_manager.decompress_db_huffman(huffman_decompress_name, APP_CONFIG["DB_PATH"], progress_callback=lambda p: (progress_bar.progress(p), status_text.text(f"Descomprimindo... {int(p*100)}%")))
                st.success(f"Arquivo Huffman descomprimido para o banco de dados original: {output_path.name}. **Lembre-se de que isso sobrescreve o DB existente.**")
                # After decompression, force re-load index and counter if needed
                db_manager._ensure_db_files()
                db_manager.current_id = db_manager._load_id_counter()
            except DatabaseError as e:
                st.error(f"Erro na descompressão Huffman: {e}")
            finally:
                progress_bar.empty()
                status_text.empty()

def render_cryptography_section():
    st.header("🔒 Criptografia de Dados")
    st.info("Criptografe e descriptografe o banco de dados usando AES/RSA.")

    st.subheader("Gerar Chaves RSA")
    st.write("As chaves RSA são usadas para criptografar/descriptografar a chave AES de forma segura.")
    password = st.text_input("Senha para proteger a chave privada (opcional)", type="password", key="rsa_password")
    if st.button("Gerar Novas Chaves RSA"):
        try:
            crypto_handler.generate_rsa_keys(password if password else None)
            st.success("Chaves RSA geradas e salvas com sucesso!")
        except EncryptionError as e:
            st.error(f"Erro ao gerar chaves RSA: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao gerar chaves RSA: {e}")
            logger.critical(f"Unexpected error on RSA key generation: {traceback.format_exc()}")

    st.subheader("Criptografar Banco de Dados")
    encrypt_output_name = st.text_input("Nome do arquivo criptografado de saída (ex: traffic_accidents.enc)", "traffic_accidents.enc")
    if st.button("Criptografar DB"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        try:
            output_path = APP_CONFIG["DB_DIR"] / encrypt_output_name
            crypto_handler.encrypt_file_hybrid(
                input_file_path=APP_CONFIG["DB_PATH"],
                output_file_path=output_path,
                progress_callback=lambda p: (progress_bar.progress(p), status_text.text(f"Criptografando... {int(p*100)}%"))
            )
            st.success(f"Banco de dados criptografado para: {output_path.name}")
        except EncryptionError as e:
            st.error(f"Erro na criptografia: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado na criptografia: {e}")
            logger.critical(f"Unexpected error on encryption: {traceback.format_exc()}")
        finally:
            progress_bar.empty()
            status_text.empty()

    st.subheader("Descriptografar Banco de Dados")
    decrypt_input_name = st.text_input("Nome do arquivo criptografado para descriptografar (ex: traffic_accidents.enc)", "traffic_accidents.enc", key="decrypt_input_name")
    decrypt_password = st.text_input("Senha da chave privada (se usada)", type="password", key="decrypt_password")
    if st.button("Descriptografar DB para Original"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        try:
            input_path = APP_CONFIG["DB_DIR"] / decrypt_input_name
            # Decrypt directly to the original DB path
            crypto_handler.decrypt_file_hybrid(
                input_file_path=input_path,
                output_file_path=APP_CONFIG["DB_PATH"],
                password=decrypt_password if decrypt_password else None,
                progress_callback=lambda p: (progress_bar.progress(p), status_text.text(f"Descriptografando... {int(p*100)}%"))
            )
            st.success(f"Arquivo criptografado descomprimido para o banco de dados original: {APP_CONFIG['DB_PATH'].name}. **Lembre-se de que isso sobrescreve o DB existente.**")
            # After decryption, force re-load index and counter if needed
            db_manager._ensure_db_files()
            db_manager.current_id = db_manager._load_id_counter()
        except EncryptionError as e:
            st.error(f"Erro na descriptografia: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado na descriptografia: {e}")
            logger.critical(f"Unexpected error on decryption: {traceback.format_exc()}")
        finally:
            progress_bar.empty()
            status_text.empty()

def render_administration_section():
    st.header("⚙️ Administração")

    st.subheader("Logs da Aplicação")
    log_file_path = APP_CONFIG["LOG_FILE_PATH"]
    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding=APP_CONFIG["DEFAULT_ENCODING"]) as f:
                log_content = f.read()
            st.text_area("Conteúdo do Log", log_content, height=300)
            st.download_button(
                label="Download Log",
                data=log_content,
                file_name="app_activity.log",
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"Erro ao ler o arquivo de log: {e}")
            logger.error(f"Error reading log file: {traceback.format_exc()}")
    else:
        st.info("Arquivo de log não encontrado.")
    
    st.subheader("Backup do Banco de Dados")
    backup_file_name = st.text_input("Nome do arquivo de backup (ex: db_backup.zip)", f"traffic_accidents_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip")
    if st.button("Criar Backup"):
        try:
            backup_path = APP_CONFIG["BACKUP_PATH"] / backup_file_name
            # Create a zip archive of DB and index files
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if APP_CONFIG["DB_PATH"].exists():
                    zipf.write(APP_CONFIG["DB_PATH"], arcname=APP_CONFIG["DB_FILE_NAME"])
                if APP_CONFIG["INDEX_PATH"].exists():
                    zipf.write(APP_CONFIG["INDEX_PATH"], arcname=APP_CONFIG["INDEX_FILE_NAME"])
                if APP_CONFIG["ID_COUNTER_PATH"].exists():
                    zipf.write(APP_CONFIG["ID_COUNTER_PATH"], arcname=APP_CONFIG["ID_COUNTER_FILE_NAME"])
            st.success(f"Backup criado com sucesso em: {backup_path}")
            logger.info(f"Database backup created at {backup_path}")
        except Exception as e:
            st.error(f"Erro ao criar backup: {e}")
            logger.critical(f"Error creating backup: {traceback.format_exc()}")
            
    st.subheader("Restaurar Backup")
    uploaded_backup = st.file_uploader("Escolha um arquivo de backup (.zip)", type=["zip"])
    if uploaded_backup is not None:
        if st.button("Restaurar Backup"):
            try:
                with tempfile.TemporaryDirectory() as tempdir:
                    temp_backup_path = Path(tempdir) / uploaded_backup.name
                    with open(temp_backup_path, "wb") as f:
                        f.write(uploaded_backup.getvalue())

                    with zipfile.ZipFile(temp_backup_path, 'r') as zip_ref:
                        # Extract only DB-related files
                        for member in zip_ref.namelist():
                            if member in [APP_CONFIG["DB_FILE_NAME"], APP_CONFIG["INDEX_FILE_NAME"], APP_CONFIG["ID_COUNTER_FILE_NAME"]]:
                                dest_path = APP_CONFIG["DB_DIR"] / member
                                with open(dest_path, "wb") as outfile:
                                    outfile.write(zip_ref.read(member))
                
                # Reinitialize DBManager to load the restored data
                db_manager.__init__(
                    db_path=APP_CONFIG["DB_PATH"],
                    index_path=APP_CONFIG["INDEX_PATH"],
                    id_counter_path=APP_CONFIG["ID_COUNTER_PATH"],
                    lock_timeout=APP_CONFIG["LOCK_TIMEOUT"]
                )
                st.success("Backup restaurado com sucesso!")
                logger.warning(f"Database restored from backup: {uploaded_backup.name}")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao restaurar backup: {e}")
                logger.critical(f"Error restoring backup: {traceback.format_exc()}")

def render_activity_log_section():
    st.header("📝 Log de Atividades")
    st.write("Visualize o histórico de operações da aplicação.")

    log_file_path = APP_CONFIG["LOG_FILE_PATH"]
    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding=APP_CONFIG["DEFAULT_ENCODING"]) as f:
                log_content = f.read()
            st.text_area("Conteúdo Completo do Log", log_content, height=500, key="full_activity_log")
            st.download_button(
                label="Baixar Log de Atividades",
                data=log_content,
                file_name="full_app_activity.log",
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"Não foi possível ler o arquivo de log: {e}")
            logger.error(f"Failed to read activity log file: {traceback.format_exc()}")
    else:
        st.info("Arquivo de log de atividades não encontrado.")

def render_about_section():
    st.header("ℹ️ Sobre")
    st.write("""
        **Gerenciador de Acidentes de Trânsito**
        
        Esta aplicação foi desenvolvida para gerenciar registros de acidentes de trânsito,
        oferecendo funcionalidades de CRUD (Criar, Ler, Atualizar, Excluir) e recursos avançados como:
        
        - **Armazenamento Persistente:** Dados salvos em arquivos binários com um índice JSON.
        - **B-Tree Index (Em desenvolvimento):** Planejado para otimizar a busca e manipulação de registros.
        - **Compressão de Dados:** Suporte a algoritmos LZW e Huffman para reduzir o tamanho do banco de dados.
        - **Criptografia Híbrida:** Utiliza AES para criptografia de dados e RSA para proteção da chave AES.
        - **Logs de Atividade:** Mantém um registro detalhado das operações da aplicação.
        - **Backup e Restauração:** Funcionalidades para proteger seus dados.
        
        **Versão:** 1.0 Alpha (Baseado em `stCRUDDataObjectPY_v4epsilon.py` e `stCRUDDataObjectPY_v3alpha.py` com adição de B-Tree, compressão e criptografia.)
        
        **Desenvolvido por:** Seu Nome/Equipe (Ex: Gemini Advanced)
        
        **Tecnologias:** Streamlit, Python, `pathlib`, `filelock`, `cryptography`, `zipfile`.
        
        ---
        
        **Aviso:** Esta é uma versão de demonstração/protótipo. Recomenda-se cautela ao lidar com dados sensíveis e sempre fazer backups.
    """)

# --- Main Application Entry Point ---
import zipfile # Import zipfile here as it's used in administration section

def setup_ui():
    st.set_page_config(layout="wide", page_title="Traffic Accidents DB Manager")
    st.title("Traffic Accidents Database Manager 🚧")

    selected_option = st.sidebar.selectbox(
    "Selecione uma opção:",
    [
        "Home", "Adicionar Registro", "Visualizar Registros",
        "Buscar/Atualizar/Excluir", "Operações DB", "Compressão",
        "Criptografia", "Administração", "Log de Atividades", "Sobre"
    ]
    )

    if selected_option == "Home":
        render_home_section()
    elif selected_option == "Adicionar Registro":
        render_add_record_section()
    elif selected_option == "Visualizar Registros":
        render_view_records_section()
    elif selected_option == "Buscar/Atualizar/Excluir":
        render_search_update_delete_section()
    elif selected_option == "Operações DB":
        render_db_operations_section()
    elif selected_option == "Compressão":
        render_compression_section()
    elif selected_option == "Criptografia":
        render_cryptography_section()
    elif selected_option == "Administração":
        render_administration_section()
    elif selected_option == "Log de Atividades":
        render_activity_log_section()
    elif selected_option == "Sobre":
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

        setup_ui()
    except OSError as e:
        st.error(f"🚨 Crítico: Não foi possível criar os diretórios necessários. Verifique as permissões para `{APP_CONFIG['DB_DIR']}`. Erro: {e}")
        logger.critical(f"Initial directory creation failed: {traceback.format_exc()}")
        st.stop() # Interrompe o aplicativo se os diretórios críticos não puderem ser criados
    except Exception as e:
        st.error(f"🚨 Ocorreu um erro crítico na inicialização da aplicação: {e}")
        logger.critical(f"Critical application startup error: {traceback.format_exc()}")
        st.stop() # Interrompe o aplicativo em caso de erro crítico
