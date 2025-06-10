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
import getpass # Import for password input (used in crypto operations)

# --- Cryptography Imports from pycryptonew.py ---
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traffic_accidents.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Configuration Constants (Centralized - from v4epsilon) ---
APP_CONFIG = {
    "DB_DIR": os.path.join(Path.home(), 'Documents', 'Data'),
    "DB_FILE_NAME": 'traffic_accidents.db',
    "INDEX_FILE_NAME": 'index.idx',
    "LOCK_FILE_NAME": 'traffic_accidents.lock',
    "ID_COUNTER_FILE_NAME": 'id_counter.dat', # New file for auto-increment ID
    "BACKUP_DIR_NAME": 'backups',
    "CSV_DELIMITER": ';',
    "MAX_RECORDS_PER_PAGE": 20,
    "MAX_FILE_SIZE_MB": 100,
    "CHUNK_SIZE": 4096,
    "MAX_BACKUPS": 5,
    "MAX_LOG_ENTRIES_DISPLAY": 10,
    "LOG_FILE_NAME": 'traffic_accidents.log',
    "BTREE_DB_FILE_NAME": 'traffic_accidents_btree.btr', # B-Tree data file
    "BTREE_PAGE_SIZE": 4096, # Bytes per page in B-Tree
    "BTREE_MIN_DEGREE": 3, # Minimum degree (t) for B-Tree (t >= 2)
    "RSA_KEYS_DIR": os.path.join(Path.home(), 'Documents', 'Data', 'crypto_keys'), # Directory for RSA keys
    "RSA_PUBLIC_KEY_FILE": 'public.pem',
    "RSA_PRIVATE_KEY_FILE": 'private.pem'
}

# Derived paths
DB_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["DB_FILE_NAME"])
INDEX_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["INDEX_FILE_NAME"])
LOCK_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOCK_FILE_NAME"])
ID_COUNTER_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["ID_COUNTER_FILE_NAME"])
BACKUP_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["BACKUP_DIR_NAME"])
LOG_FILE_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOG_FILE_NAME"])
BTREE_DB_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["BTREE_DB_FILE_NAME"])
RSA_PUBLIC_KEY_PATH = os.path.join(APP_CONFIG["RSA_KEYS_DIR"], APP_CONFIG["RSA_PUBLIC_KEY_FILE"])
RSA_PRIVATE_KEY_PATH = os.path.join(APP_CONFIG["RSA_KEYS_DIR"], APP_CONFIG["RSA_PRIVATE_KEY_FILE"])


# Ensure directories exist
Path(APP_CONFIG["DB_DIR"]).mkdir(parents=True, exist_ok=True)
Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
Path(APP_CONFIG["RSA_KEYS_DIR"]).mkdir(parents=True, exist_ok=True)


# --- DataObject Definition (from v5alpha0.1.d.py) ---
class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

class DataObject:
    """
    Represents a single record of traffic accident data.
    Includes validation logic for each field.
    """
    REQUIRED_FIELDS = [
        "id", "data", "hora", "uf", "br", "km", "municipio",
        "causa_acidente", "tipo_acidente", "classificacao_acidente",
        "fase_dia", "condicao_metereologica", "tipo_pista", "tracado_via",
        "uso_solo", "pessoas", "mortos", "feridos_leves", "feridos_graves",
        "ilesos", "ignorados", "feridos", "veiculos"
    ]

    FIELD_TYPES = {
        "id": int, "data": str, "hora": str, "uf": str, "br": int, "km": float,
        "municipio": str, "causa_acidente": str, "tipo_acidente": str,
        "classificacao_acidente": str, "fase_dia": str,
        "condicao_metereologica": str, "tipo_pista": str, "tracado_via": str,
        "uso_solo": str, "pessoas": int, "mortos": int, "feridos_leves": int,
        "feridos_graves": int, "ilesos": int, "ignorados": int, "feridos": int,
        "veiculos": int
    }

    # Data validation rules
    VALIDATION_RULES = {
        "id": lambda x: x >= 0,
        "data": lambda x: re.match(r"^\d{2}/\d{2}/\d{4}$", x) is not None,
        "hora": lambda x: re.match(r"^\d{2}h\d{2}$", x) is not None,
        "uf": lambda x: len(x) == 2 and x.isalpha() and x.isupper(),
        "br": lambda x: x >= 0,
        "km": lambda x: x >= 0.0,
        "pessoas": lambda x: x >= 0,
        "mortos": lambda x: x >= 0,
        "feridos_leves": lambda x: x >= 0,
        "feridos_graves": lambda x: x >= 0,
        "ilesos": lambda x: x >= 0,
        "ignorados": lambda x: x >= 0,
        "feridos": lambda x: x >= 0,
        "veiculos": lambda x: x >= 0,
        "classificacao_acidente": lambda x: x in ["Sem Vítimas", "Com Vítimas Feridas", "Com Vítimas Fatais"],
        "fase_dia": lambda x: x in ["Plena Noite", "Amanhecer", "Pleno Dia", "Anoitecer"],
        "condicao_metereologica": lambda x: x in ["Ceu Claro", "Chuva", "Garoa/Chuvisco", "Nevoa/Neblina", "Vento", "Granizo", "Ceu Nublado", "Sol", "Ignorada"],
        "tipo_pista": lambda x: x in ["Dupla", "Simples", "Múltipla", "Múltiplas pistas"], # Added "Múltiplas pistas"
        "tracado_via": lambda x: x in ["Reta", "Curva", "Interseção", "Retorno", "Desvio", "Viaduto", "Ponte", "Túnel", "Rotatória"],
        "uso_solo": lambda x: x in ["Rural", "Urbano"]
    }

    def __init__(self, **kwargs):
        self.data = {}
        for field in self.REQUIRED_FIELDS:
            value = kwargs.get(field)
            if value is None:
                raise DataValidationError(f"Missing required field: {field}")
            
            # Type conversion
            try:
                if field in self.FIELD_TYPES:
                    value = self.FIELD_TYPES[field](value)
            except ValueError:
                raise DataValidationError(f"Invalid type for field '{field}': expected {self.FIELD_TYPES[field].__name__}, got '{value}'")
            
            # Specific validation for certain fields
            if field in self.VALIDATION_RULES and not self.VALIDATION_RULES[field](value):
                raise DataValidationError(f"Invalid value for field '{field}': {value}")
            
            self.data[field] = value

    def __getattr__(self, name):
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name == 'data': # Allow setting the internal dictionary directly
            super().__setattr__(name, value)
            return

        if name in self.REQUIRED_FIELDS:
            # Type conversion
            try:
                if name in self.FIELD_TYPES:
                    value = self.FIELD_TYPES[name](value)
            except ValueError:
                raise DataValidationError(f"Invalid type for field '{name}': expected {self.FIELD_TYPES[name].__name__}, got '{value}'")
            
            # Specific validation
            if name in self.VALIDATION_RULES and not self.VALIDATION_RULES[name](value):
                raise DataValidationError(f"Invalid value for field '{name}': {value}")
            
            self.data[name] = value
        else:
            # Allow setting other attributes directly if not part of data fields
            super().__setattr__(name, value)

    def to_dict(self) -> Dict[str, Any]:
        return self.data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)

    @classmethod
    def from_csv_row(cls, row: List[str]):
        """
        Creates a DataObject from a list of strings (CSV row).
        Assumes the order of fields in the CSV row matches REQUIRED_FIELDS.
        """
        if len(row) != len(cls.REQUIRED_FIELDS):
            raise DataValidationError(f"CSV row has {len(row)} fields, expected {len(cls.REQUIRED_FIELDS)}")
        
        kwargs = {}
        for i, field_name in enumerate(cls.REQUIRED_FIELDS):
            kwargs[field_name] = row[i].strip()
        
        # Special handling for 'data' and 'hora' if they come from CSV and need reformatting
        if 'data' in kwargs:
            # Example: '2015-01-01' to 'DD/MM/YYYY' or just ensure format
            if '-' in kwargs['data']:
                try:
                    d = datetime.strptime(kwargs['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                    kwargs['data'] = d
                except ValueError:
                    pass # Let validation rule catch if not in expected format
        if 'hora' in kwargs:
            # Example: '08:00:00' to '08h00'
            if ':' in kwargs['hora']:
                try:
                    h = datetime.strptime(kwargs['hora'], '%H:%M:%S').strftime('%Hh%M')
                    kwargs['hora'] = h
                except ValueError:
                    pass # Let validation rule catch if not in expected format

        return cls(**kwargs)

    def to_csv_row(self) -> List[str]:
        """
        Converts the DataObject to a list of strings for CSV export,
        maintaining the order of REQUIRED_FIELDS.
        """
        row_data = []
        for field in self.REQUIRED_FIELDS:
            value = self.data.get(field)
            # Convert non-string types to string for CSV
            row_data.append(str(value) if value is not None else '')
        return row_data

    def to_binary(self) -> bytes:
        """Serializes the DataObject into a compact binary format."""
        # Simple JSON serialization for now, could be optimized for space
        # by using fixed-size fields or specific binary packers.
        return json.dumps(self.data, ensure_ascii=False).encode('utf-8')

    @classmethod
    def from_binary(cls, binary_data: bytes):
        """Deserializes a DataObject from binary data."""
        return cls.from_dict(json.loads(binary_data.decode('utf-8')))


# --- TrafficAccidentsDB Class (from v5alpha0.1.d.py) ---
class TrafficAccidentsDB:
    def __init__(self, db_file: str, index_file: str, id_counter_file: str, lock_file: str):
        self.db_file = db_file
        self.index_file = index_file
        self.id_counter_file = id_counter_file
        self.lock_file = lock_file
        self.index: Dict[int, Tuple[int, int]] = {}  # {id: (offset, length)}
        self.id_counter = self._load_id_counter()
        self._load_index()

    def _acquire_lock(self):
        """Acquires a file lock to ensure exclusive access."""
        self.lock = filelock.FileLock(self.lock_file, timeout=10)
        try:
            self.lock.acquire()
            logger.debug(f"Lock acquired for {self.db_file}")
        except filelock.Timeout:
            logger.error(f"Failed to acquire lock for {self.db_file}. Another process might be using it.")
            st.error("Não foi possível acessar o banco de dados. Ele pode estar em uso por outra sessão.")
            raise

    def _release_lock(self):
        """Releases the file lock."""
        if hasattr(self, 'lock') and self.lock.is_locked:
            self.lock.release()
            logger.debug(f"Lock released for {self.db_file}")

    def _load_id_counter(self) -> int:
        """Loads the last used ID from a file, or starts from 1."""
        if os.path.exists(self.id_counter_file):
            try:
                with open(self.id_counter_file, 'r') as f:
                    return int(f.read().strip())
            except (ValueError, IOError) as e:
                logger.warning(f"Could not load ID counter, starting from 1. Error: {e}")
        return 1

    def _save_id_counter(self):
        """Saves the current ID counter to a file."""
        with open(self.id_counter_file, 'w') as f:
            f.write(str(self.id_counter))

    def _load_index(self):
        """Loads the index from disk."""
        if os.path.exists(self.index_file):
            try:
                # The index is assumed to be JSON for simplicity with DataObject
                with open(self.index_file, 'r') as f:
                    # Convert keys back to int if necessary, as JSON keys are strings
                    temp_index = json.load(f)
                    self.index = {int(k): tuple(v) for k, v in temp_index.items()}
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load index, initializing empty. Error: {e}")
                self.index = {}
        else:
            self.index = {}

    def _save_index(self):
        """Saves the index to disk."""
        # Convert tuple values to list for JSON serialization
        serializable_index = {str(k): list(v) for k, v in self.index.items()}
        with open(self.index_file, 'w') as f:
            json.dump(serializable_index, f)

    def add_record(self, data_obj: DataObject) -> int:
        """Adds a new record to the database."""
        self._acquire_lock()
        try:
            if data_obj.id is None or data_obj.id == 0:
                data_obj.id = self.id_counter
            
            if data_obj.id in self.index:
                # If ID exists, it's an update, not an add.
                # In this simplified add_record, we assume new IDs.
                # For real update logic, a separate update_record method is better.
                logger.warning(f"Record with ID {data_obj.id} already exists. Use update_record for updates.")
                return 0 # Indicate failure or that it was an update
            
            binary_data = data_obj.to_binary()
            
            with open(self.db_file, 'ab') as f:
                offset = f.tell()
                # Store length before data for easy reading
                f.write(struct.pack('>I', len(binary_data)))
                f.write(binary_data)
                length = f.tell() - offset
            
            self.index[data_obj.id] = (offset, length)
            self.id_counter += 1
            
            self._save_index()
            self._save_id_counter()
            logger.info(f"Record {data_obj.id} added successfully.")
            return data_obj.id
        except Exception as e:
            logger.error(f"Error adding record: {e}", exc_info=True)
            st.error(f"Erro ao adicionar registro: {e}")
            return 0
        finally:
            self._release_lock()

    def get_record(self, record_id: int) -> Optional[DataObject]:
        """Retrieves a record by its ID."""
        self._acquire_lock()
        try:
            if record_id not in self.index:
                logger.warning(f"Record with ID {record_id} not found.")
                return None
            
            offset, length = self.index[record_id]
            
            with open(self.db_file, 'rb') as f:
                f.seek(offset)
                # Read length of the data block, then the data itself
                # This assumes the length was stored at the beginning of the block
                # The length here is the full length including the 4 bytes for length prefix
                # The actual data length is length - 4
                
                # Check if the remaining file size is less than expected length
                current_pos = f.tell()
                f.seek(0, os.SEEK_END)
                file_end = f.tell()
                f.seek(current_pos) # Go back to original position

                # Re-read the actual length from the file, not from index (index has block length)
                # The index stores (offset, full_block_length_with_prefix)
                # So we read the prefix 'I' (4 bytes) and then the actual data_len
                read_len_prefix = f.read(4)
                if len(read_len_prefix) < 4:
                    logger.error(f"Corrupted record at ID {record_id}: unable to read length prefix.")
                    return None
                data_len = struct.unpack('>I', read_len_prefix)[0]
                
                binary_data = f.read(data_len)

                if len(binary_data) < data_len:
                    logger.error(f"Corrupted record at ID {record_id}: expected {data_len} bytes, got {len(binary_data)}.")
                    return None
            
            return DataObject.from_binary(binary_data)
        except Exception as e:
            logger.error(f"Error getting record {record_id}: {e}", exc_info=True)
            st.error(f"Erro ao buscar registro {record_id}: {e}")
            return None
        finally:
            self._release_lock()

    def update_record(self, data_obj: DataObject) -> bool:
        """Updates an existing record. This involves rewriting the entire DB if size changes."""
        self._acquire_lock()
        try:
            if data_obj.id not in self.index:
                logger.warning(f"Record with ID {data_obj.id} not found for update.")
                st.warning(f"Registro com ID {data_obj.id} não encontrado para atualização.")
                return False
            
            old_offset, old_full_length = self.index[data_obj.id]
            new_binary_data = data_obj.to_binary()
            new_full_length = len(new_binary_data) + 4 # +4 for the length prefix

            # This is a simplification. A real production system would use free lists
            # or a log-structured approach for updates to avoid rewriting the whole DB.
            # For this example, we'll implement a full rewrite for simplicity if size changes.

            # Attempt to overwrite in place if new record fits
            if new_full_length <= old_full_length:
                with open(self.db_file, 'r+b') as f:
                    f.seek(old_offset)
                    f.write(struct.pack('>I', len(new_binary_data))) # Write new length
                    f.write(new_binary_data)
                    # Pad with zeros if new data is smaller than old data
                    if new_full_length < old_full_length:
                        f.write(b'\0' * (old_full_length - new_full_length))
                logger.info(f"Record {data_obj.id} updated in-place.")
                return True
            else:
                # If new data is larger, append to end and update index, then compact later
                logger.warning(f"Record {data_obj.id} new size ({new_full_length}) > old size ({old_full_length}). Appending new data and marking old as stale.")
                
                # Append new data to the end
                with open(self.db_file, 'ab') as f:
                    new_offset = f.tell()
                    f.write(struct.pack('>I', len(new_binary_data)))
                    f.write(new_binary_data)
                
                self.index[data_obj.id] = (new_offset, new_full_length) # Update index to new location
                self._save_index()
                logger.info(f"Record {data_obj.id} updated by appending. Old record at {old_offset} is now stale.")
                st.warning("O registro foi atualizado (nova versão adicionada). Recomenda-se compactar o DB.")
                return True

        except Exception as e:
            logger.error(f"Error updating record {data_obj.id}: {e}", exc_info=True)
            st.error(f"Erro ao atualizar registro {data_obj.id}: {e}")
            return False
        finally:
            self._release_lock()

    def delete_record(self, record_id: int) -> bool:
        """Deletes a record by marking it as stale. Requires compaction to reclaim space."""
        self._acquire_lock()
        try:
            if record_id not in self.index:
                logger.warning(f"Record with ID {record_id} not found for deletion.")
                st.warning(f"Registro com ID {record_id} não encontrado para exclusão.")
                return False
            
            del self.index[record_id]
            self._save_index()
            logger.info(f"Record {record_id} marked for deletion (removed from index).")
            st.info(f"Registro {record_id} excluído (marcado para remoção física na compactação).")
            return True
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {e}", exc_info=True)
            st.error(f"Erro ao excluir registro {record_id}: {e}")
            return False
        finally:
            self._release_lock()

    def list_records(self, page: int = 1, records_per_page: int = APP_CONFIG["MAX_RECORDS_PER_PAGE"]) -> List[DataObject]:
        """Lists records with pagination."""
        all_ids = sorted(self.index.keys())
        start_index = (page - 1) * records_per_page
        end_index = start_index + records_per_page
        
        records = []
        for record_id in all_ids[start_index:end_index]:
            record = self.get_record(record_id)
            if record: # Ensure record is not None (e.g., due to corruption)
                records.append(record)
        return records

    def count_records(self) -> int:
        """Returns the total number of active records."""
        return len(self.index)

    def compact_db(self):
        """Rewrites the database file, removing stale records."""
        self._acquire_lock()
        st.info("Iniciando compactação do banco de dados...")
        logger.info("Starting database compaction.")
        
        temp_db_file = self.db_file + ".tmp"
        new_index: Dict[int, Tuple[int, int]] = {}
        
        try:
            with open(self.db_file, 'rb') as src_f, open(temp_db_file, 'wb') as dest_f:
                for record_id in sorted(self.index.keys()):
                    # Use get_record to read the actual data, ensuring it's valid
                    data_obj = self.get_record(record_id)
                    if data_obj:
                        binary_data = data_obj.to_binary()
                        offset = dest_f.tell()
                        dest_f.write(struct.pack('>I', len(binary_data)))
                        dest_f.write(binary_data)
                        length = dest_f.tell() - offset
                        new_index[record_id] = (offset, length)
                    else:
                        logger.warning(f"Skipping corrupted or missing record {record_id} during compaction.")
            
            # Replace old files with new ones
            os.replace(temp_db_file, self.db_file)
            self.index = new_index
            self._save_index()
            
            st.success("Compactação do banco de dados concluída com sucesso!")
            logger.info("Database compaction completed successfully.")
        except Exception as e:
            st.error(f"Erro durante a compactação do banco de dados: {e}")
            logger.error(f"Error during database compaction: {e}", exc_info=True)
            # Clean up temp file if error occurs
            if os.path.exists(temp_db_file):
                os.remove(temp_db_file)
        finally:
            self._release_lock()

    def backup_db(self):
        """Creates a timestamped backup of the database and index files."""
        self._acquire_lock()
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_db_path = os.path.join(BACKUP_PATH, f"{APP_CONFIG['DB_FILE_NAME']}_{timestamp}.bak")
            backup_index_path = os.path.join(BACKUP_PATH, f"{APP_CONFIG['INDEX_FILE_NAME']}_{timestamp}.bak")
            backup_id_counter_path = os.path.join(BACKUP_PATH, f"{APP_CONFIG['ID_COUNTER_FILE_NAME']}_{timestamp}.bak")
            
            shutil.copy2(self.db_file, backup_db_path)
            shutil.copy2(self.index_file, backup_index_path)
            shutil.copy2(self.id_counter_file, backup_id_counter_path)
            
            st.success(f"Backup criado em: {BACKUP_PATH}")
            logger.info(f"Backup created at: {BACKUP_PATH} with timestamp {timestamp}")

            # Clean up old backups
            self._clean_old_backups()
            return True
        except Exception as e:
            st.error(f"Erro ao criar backup: {e}")
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return False
        finally:
            self._release_lock()

    def _clean_old_backups(self):
        """Removes oldest backups if their count exceeds MAX_BACKUPS."""
        backup_files = sorted(Path(BACKUP_PATH).glob(f"{APP_CONFIG['DB_FILE_NAME']}_*.bak"), key=os.path.getmtime)
        if len(backup_files) > APP_CONFIG["MAX_BACKUPS"]:
            for i in range(len(backup_files) - APP_CONFIG["MAX_BACKUPS"]):
                file_to_remove_db = backup_files[i]
                
                # Derive corresponding index and id_counter backup files
                timestamp_str = file_to_remove_db.name.split('_')[-1].split('.')[0]
                file_to_remove_index = Path(BACKUP_PATH) / f"{APP_CONFIG['INDEX_FILE_NAME']}_{timestamp_str}.bak"
                file_to_remove_id_counter = Path(BACKUP_PATH) / f"{APP_CONFIG['ID_COUNTER_FILE_NAME']}_{timestamp_str}.bak"

                try:
                    os.remove(file_to_remove_db)
                    if file_to_remove_index.exists():
                        os.remove(file_to_remove_index)
                    if file_to_remove_id_counter.exists():
                        os.remove(file_to_remove_id_counter)
                    logger.info(f"Removed old backup: {file_to_remove_db.name}")
                except Exception as e:
                    logger.warning(f"Could not remove old backup {file_to_remove_db.name}: {e}")

    def restore_db(self, backup_db_file: str):
        """Restores the database and index from a selected backup."""
        self._acquire_lock()
        try:
            # Derive corresponding index and id_counter backup files
            timestamp_str = backup_db_file.name.split('_')[-1].split('.')[0]
            backup_index_file = Path(BACKUP_PATH) / f"{APP_CONFIG['INDEX_FILE_NAME']}_{timestamp_str}.bak"
            backup_id_counter_file = Path(BACKUP_PATH) / f"{APP_CONFIG['ID_COUNTER_FILE_NAME']}_{timestamp_str}.bak"

            if not backup_db_file.exists() or not backup_index_file.exists() or not backup_id_counter_file.exists():
                st.error("Arquivos de backup incompletos ou não encontrados!")
                logger.error(f"Incomplete backup set for {backup_db_file.name}")
                return False

            # Close current DB connections/release locks if necessary before overwriting
            self._save_index() # Ensure current index is saved before potential overwrite
            self._save_id_counter() # Ensure current ID counter is saved

            shutil.copy2(backup_db_file, self.db_file)
            shutil.copy2(backup_index_file, self.index_file)
            shutil.copy2(backup_id_counter_file, self.id_counter_file)
            
            # Reload the DB state after restore
            self.id_counter = self._load_id_counter()
            self._load_index()
            
            st.success(f"Banco de dados restaurado de: {backup_db_file.name}")
            logger.info(f"Database restored from: {backup_db_file.name}")
            return True
        except Exception as e:
            st.error(f"Erro ao restaurar backup: {e}")
            logger.error(f"Error restoring backup: {e}", exc_info=True)
            return False
        finally:
            self._release_lock()


# --- B-Tree Implementation (from v5alpha0.2.a.py) ---

PAGE_SIZE = APP_CONFIG["BTREE_PAGE_SIZE"] # Bytes per page
T = APP_CONFIG["BTREE_MIN_DEGREE"]       # Minimum degree (t)
MAX_KEYS = 2 * T - 1                    # Maximum keys per node
MIN_KEYS = T - 1                        # Minimum keys per node

class BTreeNode:
    def __init__(self, is_leaf=False):
        self.keys = []      # List of (key, data_offset) tuples
        self.children = []  # List of child page IDs
        self.is_leaf = is_leaf
        self.page_id = None # Assigned by Pager
        self.n = 0          # Current number of keys

    def to_binary(self) -> bytes:
        """Serializes the node into a fixed-size binary page."""
        # Format: is_leaf (1 byte), n (1 byte), keys_and_offsets, children_pointers
        # Each key-value pair: (int key, int data_offset)
        # Each child pointer: (int page_id)

        # Buffer for the page
        buffer = bytearray(PAGE_SIZE)
        offset = 0

        # is_leaf (1 byte)
        buffer[offset] = 1 if self.is_leaf else 0
        offset += 1

        # n (number of keys, 1 byte)
        buffer[offset] = self.n
        offset += 1
        
        # Write keys and data offsets
        key_offset_format = '>Ii' # Unsigned int for key (ID), signed int for offset
        key_offset_size = struct.calcsize(key_offset_format)

        for i in range(self.n):
            key, data_offset = self.keys[i]
            struct.pack_into(key_offset_format, buffer, offset, key, data_offset)
            offset += key_offset_size
        
        # Fill remaining key/offset slots with zeros
        for _ in range(self.n, MAX_KEYS):
            struct.pack_into(key_offset_format, buffer, offset, 0, 0) # Dummy zeros
            offset += key_offset_size

        # Write children pointers
        child_ptr_format = '>i' # Signed int for page ID (-1 for None)
        child_ptr_size = struct.calcsize(child_ptr_format)
        
        num_children = self.n + 1 if not self.is_leaf else 0

        for i in range(num_children):
            child_page_id = self.children[i] if not self.is_leaf else -1
            struct.pack_into(child_ptr_format, buffer, offset, child_page_id)
            offset += child_ptr_size
        
        # Fill remaining child slots with zeros
        for _ in range(num_children, MAX_KEYS + 1):
            struct.pack_into(child_ptr_format, buffer, offset, -1) # Dummy -1 (invalid page ID)
            offset += child_ptr_size

        if offset > PAGE_SIZE:
            logger.error(f"Node serialization exceeded PAGE_SIZE: {offset} > {PAGE_SIZE}")
            raise ValueError("Node serialization exceeded PAGE_SIZE")

        return bytes(buffer)

    @classmethod
    def from_binary(cls, binary_data: bytes):
        """Deserializes a node from binary data."""
        node = cls()
        offset = 0

        # is_leaf (1 byte)
        node.is_leaf = bool(binary_data[offset])
        offset += 1

        # n (number of keys, 1 byte)
        node.n = binary_data[offset]
        offset += 1

        # Read keys and data offsets
        key_offset_format = '>Ii'
        key_offset_size = struct.calcsize(key_offset_format)
        
        node.keys = []
        for _ in range(MAX_KEYS): # Read all slots
            key, data_offset = struct.unpack_from(key_offset_format, binary_data, offset)
            if len(node.keys) < node.n: # Only add if within actual 'n' count
                node.keys.append((key, data_offset))
            offset += key_offset_size
        
        # Read children pointers
        child_ptr_format = '>i'
        child_ptr_size = struct.calcsize(child_ptr_format)

        node.children = []
        num_children = node.n + 1 if not node.is_leaf else 0
        for _ in range(MAX_KEYS + 1): # Read all slots
            child_page_id = struct.unpack_from(child_ptr_format, binary_data, offset)[0]
            if len(node.children) < num_children: # Only add if within actual child count
                if child_page_id != -1: # -1 indicates an empty slot
                    node.children.append(child_page_id)
            offset += child_ptr_size
        
        return node

class Pager:
    def __init__(self, db_file_path: str):
        self.db_file_path = db_file_path
        self.file = open(db_file_path, 'r+b' if os.path.exists(db_file_path) else 'w+b')
        self.file.seek(0, os.SEEK_END)
        self.num_pages = self.file.tell() // PAGE_SIZE
        self.page_cache = {} # Simple in-memory cache for pages

    def get_new_page_id(self) -> int:
        """Returns a new unique page ID."""
        new_page_id = self.num_pages
        self.num_pages += 1
        return new_page_id

    def read_page(self, page_id: int) -> BTreeNode:
        """Reads a page from disk or cache."""
        if page_id in self.page_cache:
            return self.page_cache[page_id]
        
        if page_id < 0 or page_id >= self.num_pages:
            logger.error(f"Attempted to read invalid page ID: {page_id}")
            raise ValueError(f"Invalid page ID: {page_id}")

        self.file.seek(page_id * PAGE_SIZE)
        binary_data = self.file.read(PAGE_SIZE)
        if len(binary_data) < PAGE_SIZE:
            logger.error(f"Corrupted page {page_id}: read only {len(binary_data)} of {PAGE_SIZE} bytes.")
            raise IOError(f"Corrupted page {page_id}")
        
        node = BTreeNode.from_binary(binary_data)
        node.page_id = page_id
        self.page_cache[page_id] = node
        return node

    def write_page(self, node: BTreeNode):
        """Writes a page to disk."""
        if node.page_id is None:
            raise ValueError("Node must have a page_id to be written.")
        
        self.file.seek(node.page_id * PAGE_SIZE)
        binary_data = node.to_binary()
        self.file.write(binary_data)
        self.file.flush() # Ensure data is written to disk
        self.page_cache[node.page_id] = node # Update cache

    def flush_all(self):
        """Ensures all cached pages are written to disk."""
        for node in self.page_cache.values():
            if node.page_id is not None:
                self.write_page(node)
        self.file.flush()

    def close(self):
        """Closes the underlying file."""
        self.flush_all()
        self.file.close()

class TrafficAccidentsTree:
    def __init__(self, db_file_name: str):
        self.db_file_path = os.path.join(APP_CONFIG["DB_DIR"], db_file_name)
        self.order = APP_CONFIG["BTREE_MIN_DEGREE"] # This is 't', the minimum degree
        self.t = self.order
        self.pager = Pager(self.db_file_path)

        if self.pager.num_pages == 0:
            # Create a new root node if the database is empty
            self.root = self._create_node(is_leaf=True)
            self.root.page_id = self.pager.get_new_page_id()
            self.pager.write_page(self.root)
            self.root_page_id = self.root.page_id
            logger.info(f"New B-Tree database created at {self.db_file_path}")
        else:
            # Load the root node (assumed to be page 0 for simplicity)
            self.root_page_id = 0 # Assume root is always page 0
            self.root = self.pager.read_page(self.root_page_id)
            logger.info(f"Existing B-Tree database loaded from {self.db_file_path}")

    def _create_node(self, is_leaf: bool) -> BTreeNode:
        """Helper to create a new node."""
        node = BTreeNode(is_leaf=is_leaf)
        node.page_id = self.pager.get_new_page_id() # Assign a new page ID
        return node

    def insert(self, key: int, data_offset: int):
        """Inserts a new key-value pair into the B-tree."""
        root = self.pager.read_page(self.root_page_id)
        if root.n == (2 * self.t - 1):
            s = self._create_node() # New root
            s.page_id = self.pager.get_new_page_id()
            s.children.append(root.page_id)
            s.n = 0
            self._split_child(s, 0, root)
            self.root_page_id = s.page_id # Update root page ID
            self.root = s # Update in-memory root reference
        self._insert_non_full(self.pager.read_page(self.root_page_id), key, data_offset)
        self.pager.flush_all() # Ensure all changes are written

    def _insert_non_full(self, x: BTreeNode, key: int, data_offset: int):
        """Helper for inserting into a non-full node."""
        i = x.n - 1
        if x.is_leaf:
            x.keys.append(None) # Make space
            while i >= 0 and key < x.keys[i][0]:
                x.keys[i + 1] = x.keys[i]
                i -= 1
            x.keys[i + 1] = (key, data_offset)
            x.n += 1
            self.pager.write_page(x)
        else:
            while i >= 0 and key < x.keys[i][0]:
                i -= 1
            i += 1
            child = self.pager.read_page(x.children[i])
            if child.n == (2 * self.t - 1):
                self._split_child(x, i, child)
                if key > x.keys[i][0]:
                    i += 1
            self._insert_non_full(self.pager.read_page(x.children[i]), key, data_offset)

    def _split_child(self, x: BTreeNode, i: int, y: BTreeNode):
        """Splits a child node y of x."""
        z = self._create_node(is_leaf=y.is_leaf)
        z.n = self.t - 1
        
        # Copy keys and children from y to z
        z.keys = y.keys[self.t: (2 * self.t - 1)]
        if not y.is_leaf:
            z.children = y.children[self.t: (2 * self.t)]
        
        y.n = self.t - 1 # y now has t-1 keys

        # Make space for new child and key in x
        x.children.insert(i + 1, z.page_id) # Insert z's page_id into x's children
        x.keys.insert(i, y.keys[self.t - 1]) # Insert median key from y into x
        x.n += 1

        # Remove moved key and children from y
        y.keys = y.keys[0:self.t - 1]
        if not y.is_leaf:
            y.children = y.children[0:self.t]

        # Write the modified nodes to disk
        self.pager.write_page(y)
        self.pager.write_page(z)
        self.pager.write_page(x)

    def search(self, key: int) -> Optional[int]:
        """Searches for a key and returns its data offset."""
        return self._search_node(self.pager.read_page(self.root_page_id), key)

    def _search_node(self, x: BTreeNode, key: int) -> Optional[int]:
        """Helper for searching within a node."""
        i = 0
        while i < x.n and key > x.keys[i][0]:
            i += 1
        
        if i < x.n and key == x.keys[i][0]:
            return x.keys[i][1] # Return data offset
        elif x.is_leaf:
            return None
        else:
            return self._search_node(self.pager.read_page(x.children[i]), key)

    def delete(self, key: int) -> bool:
        """Deletes a key from the B-tree."""
        root = self.pager.read_page(self.root_page_id)
        found = self._delete_from_node(root, key)
        
        if root.n == 0 and not root.is_leaf:
            # If root becomes empty and has children, new root is its only child
            self.root_page_id = root.children[0]
            self.root = self.pager.read_page(self.root_page_id) # Update in-memory root
            # The old root page might be reclaimable if we implement a free list
        
        self.pager.flush_all() # Ensure all changes are written
        return found

    def _delete_from_node(self, x: BTreeNode, key: int) -> bool:
        """Helper for deleting a key from a node."""
        i = 0
        while i < x.n and key > x.keys[i][0]:
            i += 1

        # Case 1: Key is found in node x
        if i < x.n and key == x.keys[i][0]:
            if x.is_leaf:
                x.keys.pop(i)
                x.n -= 1
                self.pager.write_page(x)
                return True
            else:
                # Key is in internal node, replace with predecessor/successor
                # (Simplified: just removing, full delete is complex)
                # This needs full CLRS delete algorithm implementation for robustness
                # For now, this is a placeholder/simplified delete.
                # A full delete would ensure node properties (min_keys) are maintained
                # by borrowing/merging children.
                logger.warning(f"Complex B-Tree delete for internal node ({key}) not fully implemented. Consider re-building for robust deletion.")
                return False # Indicate not fully handled
        # Case 2: Key is not in node x, recurse to child
        else:
            if x.is_leaf:
                return False # Key not found
            
            child_node = self.pager.read_page(x.children[i])

            # Ensure child has enough keys for deletion (at least t keys)
            if child_node.n < self.t:
                # Perform borrow or merge operation
                if i > 0 and self.pager.read_page(x.children[i-1]).n >= self.t:
                    self._borrow_from_prev(x, i, child_node)
                elif i < x.n and self.pager.read_page(x.children[i+1]).n >= self.t:
                    self._borrow_from_next(x, i, child_node)
                else:
                    # Merge with sibling
                    if i < x.n: # Merge with right sibling
                        self._merge_children(x, i, child_node, self.pager.read_page(x.children[i+1]))
                    else: # Merge with left sibling
                        self._merge_children(x, i-1, self.pager.read_page(x.children[i-1]), child_node)
            
            # After ensuring child has enough keys, recurse
            return self._delete_from_node(self.pager.read_page(x.children[i]), key)


    # NOTE: The full delete algorithm for B-Trees (especially borrowing and merging)
    # is quite complex and beyond the scope of a simplified example.
    # The current `_delete_from_node` above is a simplified version.
    # For a robust B-Tree, these helper methods (_borrow_from_prev, _borrow_from_next, _merge_children)
    # would need to be fully implemented according to CLRS or similar algorithm.
    # Without them, deletion might not maintain B-tree properties correctly or reclaim space.
    # For now, I'm just leaving warnings.

    def _borrow_from_prev(self, parent_node: BTreeNode, child_idx: int, current_child: BTreeNode):
        """Borrows a key from the left sibling."""
        left_sibling = self.pager.read_page(parent_node.children[child_idx - 1])
        
        # Move key from parent to current_child
        current_child.keys.insert(0, parent_node.keys[child_idx - 1])
        current_child.n += 1

        # Move child from left_sibling to current_child
        if not left_sibling.is_leaf:
            current_child.children.insert(0, left_sibling.children.pop())
        
        # Move key from left_sibling to parent
        parent_node.keys[child_idx - 1] = left_sibling.keys.pop()
        left_sibling.n -= 1

        self.pager.write_page(parent_node)
        self.pager.write_page(left_sibling)
        self.pager.write_page(current_child)

    def _borrow_from_next(self, parent_node: BTreeNode, child_idx: int, current_child: BTreeNode):
        """Borrows a key from the right sibling."""
        right_sibling = self.pager.read_page(parent_node.children[child_idx + 1])
        
        # Move key from parent to current_child
        current_child.keys.append(parent_node.keys[child_idx])
        current_child.n += 1

        # Move child from right_sibling to current_child
        if not right_sibling.is_leaf:
            current_child.children.append(right_sibling.children.pop(0))
        
        # Move key from right_sibling to parent
        parent_node.keys[child_idx] = right_sibling.keys.pop(0)
        right_sibling.n -= 1

        self.pager.write_page(parent_node)
        self.pager.write_page(right_sibling)
        self.pager.write_page(current_child)

    def _merge_children(self, parent_node: BTreeNode, child_idx: int, left_child: BTreeNode, right_child: BTreeNode):
        """Merges two children and pulls a key from the parent."""
        # Pull key from parent down to left_child
        left_child.keys.append(parent_node.keys.pop(child_idx))
        parent_node.n -= 1

        # Append right_child's keys and children to left_child
        left_child.keys.extend(right_child.keys)
        left_child.n += right_child.n + 1 # +1 for the key pulled from parent
        if not left_child.is_leaf:
            left_child.children.extend(right_child.children)
        
        # Remove right_child from parent's children
        parent_node.children.pop(child_idx + 1)

        # Write updated nodes
        self.pager.write_page(parent_node)
        self.pager.write_page(left_child)
        # Note: right_child's page can now be considered free (for a free list implementation)


# --- Compression Utilities (from stHuffman_v5.py & stLZWPY_v4.py) ---

# Huffman Constants
HUFFMAN_FOLDER = os.path.join(APP_CONFIG["DB_DIR"], "Huffman")
COMPRESSED_EXTENSION_HUFF = ".huff"
Path(HUFFMAN_FOLDER).mkdir(parents=True, exist_ok=True)

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
    def generate_tree(data: bytes, progress_callback=None) -> Optional[Node]:
        """Optimized tree generation with progress tracking"""
        if not data:
            return None
            
        if len(data) == 1:
            return Node(data, 1)  # Handle single-byte case

        frequency = Counter(data)
        heap = [Node(bytes([char_code]), freq) for char_code, freq in frequency.items()]
        heapq.heapify(heap)

        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            merged = Node(None, left.freq + right.freq, left, right)
            heapq.heappush(heap, merged)
        
        return heapq.heappop(heap)

    @staticmethod
    def generate_codes(node: Node, current_code: str = "", codes: Dict[bytes, str] = {}) -> Dict[bytes, str]:
        if node.char is not None:
            codes[node.char] = current_code
            return codes
        if node.left:
            HuffmanProcessor.generate_codes(node.left, current_code + "0", codes)
        if node.right:
            HuffmanProcessor.generate_codes(node.right, current_code + "1", codes)
        return codes

    @staticmethod
    def _pad_encoded_text(encoded_text: str) -> Tuple[bytes, int]:
        """Pads the encoded text and converts to bytes."""
        extra_padding = 8 - len(encoded_text) % 8
        for i in range(extra_padding):
            encoded_text += "0"
        
        padded_info = "{0:08b}".format(extra_padding)
        encoded_text = padded_info + encoded_text
        
        byte_array = bytearray()
        for i in range(0, len(encoded_text), 8):
            byte_array.append(int(encoded_text[i:i+8], 2))
        
        return bytes(byte_array), extra_padding

    @staticmethod
    def _remove_padding(padded_encoded_text: bytes) -> str:
        """Removes padding from the encoded text."""
        padded_info = bin(padded_encoded_text[0])[2:].rjust(8, '0')
        extra_padding = int(padded_info, 2)
        
        encoded_text = "".join([bin(byte)[2:].rjust(8, '0') for byte in padded_encoded_text])
        
        return encoded_text[8:-extra_padding] if extra_padding != 0 else encoded_text[8:]

    @staticmethod
    def _decode_text(encoded_text: str, huffman_tree: Node) -> bytes:
        """Decodes the text using the Huffman tree."""
        current_node = huffman_tree
        decoded_text = bytearray()
        
        for bit in encoded_text:
            if bit == '0':
                current_node = current_node.left
            else:
                current_node = current_node.right
            
            if current_node.char is not None:
                decoded_text.extend(current_node.char)
                current_node = huffman_tree
        
        return bytes(decoded_text)

    @staticmethod
    def _serialize_tree(node: Node) -> bytes:
        """Serializes the Huffman tree for storage."""
        if node.char is not None:
            return b'1' + node.char
        return b'0' + HuffmanProcessor._serialize_tree(node.left) + HuffmanProcessor._serialize_tree(node.right)

    @staticmethod
    def _deserialize_tree(data_stream: io.BytesIO) -> Node:
        """Deserializes the Huffman tree from a byte stream."""
        bit = data_stream.read(1)
        if bit == b'1':
            char = data_stream.read(1)
            return Node(char, 0)
        left = HuffmanProcessor._deserialize_tree(data_stream)
        right = HuffmanProcessor._deserialize_tree(data_stream)
        return Node(None, 0, left, right)

    @staticmethod
    def compress_file(input_path: str, output_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[int, int, float, float]:
        start_time = time.time()
        try:
            with open(input_path, 'rb') as file:
                data = file.read()
            
            initial_size = len(data)
            if initial_size == 0:
                raise ValueError("Input file is empty. Cannot compress.")

            tree = HuffmanProcessor.generate_tree(data)
            codes = HuffmanProcessor.generate_codes(tree)
            
            encoded_text = "".join([codes[bytes([byte])] for byte in data])
            padded_encoded_text, _ = HuffmanProcessor._pad_encoded_text(encoded_text)
            
            serialized_tree = HuffmanProcessor._serialize_tree(tree)
            
            with open(output_path, 'wb') as output_file:
                # Write tree length (4 bytes)
                output_file.write(struct.pack('>I', len(serialized_tree)))
                # Write serialized tree
                output_file.write(serialized_tree)
                # Write padded encoded text
                output_file.write(padded_encoded_text)

            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / initial_size) * 100 if initial_size > 0 else 0
            process_time = time.time() - start_time
            
            if progress_callback:
                progress_callback(1.0)
            return compressed_size, initial_size, compression_ratio, process_time
        except Exception as e:
            logger.error(f"Error during Huffman compression of {input_path}: {traceback.format_exc()}")
            raise e

    @staticmethod
    def decompress_file(input_path: str, output_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[int, int, float, float]:
        start_time = time.time()
        try:
            with open(input_path, 'rb') as file:
                # Read tree length (4 bytes)
                tree_len_bytes = file.read(4)
                if len(tree_len_bytes) < 4:
                    raise ValueError("Corrupted compressed file: missing tree length.")
                tree_len = struct.unpack('>I', tree_len_bytes)[0]
                
                # Read serialized tree
                serialized_tree_data = file.read(tree_len)
                if len(serialized_tree_data) < tree_len:
                    raise ValueError("Corrupted compressed file: incomplete tree data.")
                huffman_tree = HuffmanProcessor._deserialize_tree(io.BytesIO(serialized_tree_data))
                
                # Read padded encoded text
                padded_encoded_text = file.read()

            compressed_size = len(tree_len_bytes) + len(serialized_tree_data) + len(padded_encoded_text) # Get actual size read

            encoded_text = HuffmanProcessor._remove_padding(padded_encoded_text)
            decoded_text = HuffmanProcessor._decode_text(encoded_text, huffman_tree)

            with open(output_path, 'wb') as output_file:
                output_file.write(decoded_text)
            
            decompressed_size = len(decoded_text)
            compression_ratio = (1 - compressed_size / decompressed_size) * 100 if decompressed_size > 0 else 0
            process_time = time.time() - start_time

            if progress_callback:
                progress_callback(1.0)
            return compressed_size, decompressed_size, compression_ratio, process_time
        except Exception as e:
            logger.error(f"Error during Huffman decompression of {input_path}: {traceback.format_exc()}")
            raise e

# LZW Constants
LZW_FOLDER = os.path.join(APP_CONFIG["DB_DIR"], "LZW")
COMPRESSED_EXTENSION_LZW = ".lzw"
Path(LZW_FOLDER).mkdir(parents=True, exist_ok=True)

class LZWProcessor:
    @staticmethod
    def compress(input_file_path, output_file_path, progress_callback=None):
        start_time = time.time()
        
        try:
            with open(input_file_path, 'rb') as f:
                data = f.read()
            
            initial_size = len(data)
            if initial_size == 0:
                raise ValueError("Input file is empty. Cannot compress.")

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
                    if next_code <= 4095: # Max code for 12 bits
                        dictionary[wc] = next_code
                        next_code += 1
                        if next_code > max_code: # Expand bits if dictionary is full
                            bits += 1
                            max_code = 2**bits - 1
                    w = c
                
                processed_bytes += 1
                if progress_callback:
                    progress_callback(processed_bytes / total_bytes)
            
            if w:
                compressed_data.append(dictionary[w])

            # Write compressed data as variable-length codes
            with open(output_file_path, 'wb') as f:
                current_bits = 0
                current_value = 0
                for code in compressed_data:
                    # Determine bits required for current code
                    code_bits = (code).bit_length()
                    if code_bits == 0: # Handle code 0 explicitly if it's the only one
                        code_bits = 1
                    
                    # Ensure minimum bits is always at least 9 as per LZW common practice
                    # and expand as dictionary grows
                    needed_bits = max(9, (next_code -1).bit_length() if next_code > 0 else 9)

                    current_value = (current_value << needed_bits) | code
                    current_bits += needed_bits
                    
                    while current_bits >= 8:
                        f.write(struct.pack('>B', (current_value >> (current_bits - 8)) & 0xFF))
                        current_bits -= 8
                
                # Write any remaining bits
                if current_bits > 0:
                    f.write(struct.pack('>B', (current_value << (8 - current_bits)) & 0xFF))

            compressed_size = os.path.getsize(output_file_path)
            compression_ratio = (1 - compressed_size / initial_size) * 100 if initial_size > 0 else 0
            process_time = time.time() - start_time

            if progress_callback:
                progress_callback(1.0)
            return compressed_size, initial_size, compression_ratio, process_time
        except Exception as e:
            logger.error(f"Error during LZW compression of {input_file_path}: {traceback.format_exc()}")
            raise e

    @staticmethod
    def decompress(input_file_path, output_file_path, progress_callback=None):
        start_time = time.time()
        
        try:
            with open(input_file_path, 'rb') as f:
                compressed_bytes = f.read()
            
            compressed_size = len(compressed_bytes)
            if compressed_size == 0:
                raise ValueError("Input file is empty. Cannot decompress.")

            dictionary = {i: bytes([i]) for i in range(256)}
            next_code = 256
            
            result = bytearray()
            w = bytes()
            
            # Read bits from the compressed data
            bit_buffer = deque()
            
            def read_bits(num_bits):
                while len(bit_buffer) < num_bits:
                    if not compressed_bytes:
                        raise EOFError("Unexpected end of compressed data stream.")
                    next_byte = compressed_bytes.pop(0) if isinstance(compressed_bytes, list) else compressed_bytes[0]
                    if isinstance(compressed_bytes, (bytes, bytearray)):
                         compressed_bytes = compressed_bytes[1:] # Consume byte
                    bit_buffer.extend(bin(next_byte)[2:].rjust(8, '0'))
                
                bits = "".join([bit_buffer.popleft() for _ in range(num_bits)])
                return int(bits, 2)

            total_bits_read = 0
            
            # Initial bits is 9
            bits = 9
            max_code = 2**bits - 1

            # Read first code
            try:
                k = read_bits(bits)
                result.extend(dictionary[k])
                w = dictionary[k]
                total_bits_read += bits
            except EOFError:
                # Empty file or very short compressed data not containing a full first code
                return 0, 0, 0, 0 # Return zeros as no data was processed

            # Loop for remaining codes
            while True:
                try:
                    # Dynamically determine bits needed for the next code
                    needed_bits = (next_code - 1).bit_length() if next_code > 256 else 9
                    if needed_bits < 9: # Always at least 9 bits
                        needed_bits = 9

                    k = read_bits(needed_bits)
                    total_bits_read += needed_bits

                except EOFError:
                    break # End of file

                if k in dictionary:
                    entry = dictionary[k]
                elif k == next_code:
                    entry = w + bytes([w[0]])
                else:
                    raise ValueError(f"Bad compressed code {k}")
                
                result.extend(entry)
                
                if next_code <= 4095: # Max code for 12 bits
                    dictionary[next_code] = w + bytes([entry[0]])
                    next_code += 1
                    if next_code > max_code:
                        bits += 1
                        max_code = 2**bits - 1
                w = entry
                
                if progress_callback:
                    # Estimate progress based on bits read
                    estimated_total_bits = compressed_size * 8
                    progress_callback(total_bits_read / estimated_total_bits)

            decompressed_size = len(result)
            compression_ratio = (1 - compressed_size / decompressed_size) * 100 if decompressed_size > 0 else 0
            process_time = time.time() - start_time

            with open(output_file_path, 'wb') as f:
                f.write(result)
            
            if progress_callback:
                progress_callback(1.0)
            return compressed_size, decompressed_size, compression_ratio, process_time
        except Exception as e:
            logger.error(f"Error during LZW decompression of {input_file_path}: {traceback.format_exc()}")
            raise e


# --- Cryptography Handler (from pycryptonew.py) ---
# This class contains the logic for AES and RSA encryption/decryption using cryptography library.
# The Blowfish functions are placeholders.

class CryptographyHandler:
    @staticmethod
    def blowfish_encrypt_file():
        input_file = st.text_input("Caminho do arquivo de entrada para Blowfish (criptografar):").strip()
        output_file = st.text_input("Caminho do arquivo de saída para Blowfish (criptografado):").strip()
        password = st.text_input("Senha para Blowfish (criptografar):", type="password").strip() # getpass doesn't work in Streamlit

        if st.button("Criptografar com Blowfish"):
            if not input_file or not output_file or not password:
                st.error("Por favor, preencha todos os campos para Blowfish.")
                return False
            if not os.path.exists(input_file):
                st.error("Arquivo de entrada não encontrado!")
                return False
            
            try:
                # This relies on the external Blowfish implementation
                encrypt_file(input_file, output_file, password)
                st.success("Criptografia Blowfish concluída com sucesso!")
                return True
            except NotImplementedError:
                st.error("Erro: A implementação do Blowfish não está disponível.")
                return False
            except Exception as e:
                st.error(f"Erro na criptografia Blowfish: {e}")
                logger.error(f"Erro na criptografia Blowfish: {traceback.format_exc()}")
                return False
        return False

    @staticmethod
    def blowfish_decrypt_file():
        input_file = st.text_input("Caminho do arquivo de entrada para Blowfish (descriptografar):").strip()
        output_file = st.text_input("Caminho do arquivo de saída para Blowfish (descriptografado):").strip()
        password = st.text_input("Senha para Blowfish (descriptografar):", type="password").strip()

        if st.button("Descriptografar com Blowfish"):
            if not input_file or not output_file or not password:
                st.error("Por favor, preencha todos os campos para Blowfish.")
                return False
            if not os.path.exists(input_file):
                st.error("Arquivo de entrada não encontrado!")
                return False
            
            try:
                # This relies on the external Blowfish implementation
                decrypt_file(input_file, output_file, password)
                st.success("Descriptografia Blowfish concluída com sucesso!")
                return True
            except NotImplementedError:
                st.error("Erro: A implementação do Blowfish não está disponível.")
                return False
            except Exception as e:
                st.error(f"Erro na descriptografia Blowfish: {e}")
                logger.error(f"Erro na descriptografia Blowfish: {traceback.format_exc()}")
                return False
        return False

    @staticmethod
    def generate_rsa_keys():
        st.subheader("Gerar Chaves RSA")
        st.write(f"As chaves serão salvas em: `{APP_CONFIG['RSA_KEYS_DIR']}`")
        
        if st.button("Gerar Novas Chaves RSA"):
            try:
                # Ensure directory exists
                Path(APP_CONFIG["RSA_KEYS_DIR"]).mkdir(parents=True, exist_ok=True)

                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
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
                
                with open(RSA_PRIVATE_KEY_PATH, "wb") as f:
                    f.write(private_pem)
                
                with open(RSA_PUBLIC_KEY_PATH, "wb") as f:
                    f.write(public_pem)
                
                st.success(f"Chaves RSA geradas e salvas em {APP_CONFIG['RSA_KEYS_DIR']}/")
                logger.info("Chaves RSA geradas com sucesso.")
            except Exception as e:
                st.error(f"Erro ao gerar chaves RSA: {e}")
                logger.error(f"Erro ao gerar chaves RSA: {traceback.format_exc()}")

    @staticmethod
    def hybrid_encrypt_file(input_file_path: str, output_file_path: str, public_key_path: str):
        """Encrypts a file using AES with RSA key encryption."""
        try:
            if not os.path.exists(input_file_path):
                raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_file_path}")
            if not os.path.exists(public_key_path):
                raise FileNotFoundError(f"Arquivo de chave pública não encontrado: {public_key_path}")

            aes_key = os.urandom(32)  # 256-bit AES key
            iv = os.urandom(16)      # 128-bit IV for AES CBC
            
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            
            with open(input_file_path, 'rb') as f:
                plaintext = f.read()
            
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(plaintext) + padder.finalize()
            
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            with open(public_key_path, 'rb') as f:
                public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            
            enc_aes_key = public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            with open(output_file_path, 'wb') as f:
                f.write(struct.pack('>I', len(enc_aes_key))) # Length of encrypted AES key
                f.write(enc_aes_key)
                f.write(iv)
                f.write(ciphertext)
            
            return True
        except Exception as e:
            st.error(f"Erro na criptografia híbrida: {e}")
            logger.error(f"Erro na criptografia híbrida de {input_file_path}: {traceback.format_exc()}")
            return False

    @staticmethod
    def hybrid_decrypt_file(input_file_path: str, output_file_path: str, private_key_path: str, password: Optional[str] = None):
        """Decrypts a file using AES with RSA key decryption."""
        try:
            if not os.path.exists(input_file_path):
                raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_file_path}")
            if not os.path.exists(private_key_path):
                raise FileNotFoundError(f"Arquivo de chave privada não encontrado: {private_key_path}")

            with open(input_file_path, 'rb') as f:
                key_len = struct.unpack('>I', f.read(4))[0]
                enc_aes_key = f.read(key_len)
                iv = f.read(16)
                ciphertext = f.read()
            
            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=password.encode('utf-8') if password else None,
                    backend=default_backend()
                )
            
            aes_key = private_key.decrypt(
                enc_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
            
            with open(output_file_path, 'wb') as f:
                f.write(decrypted_data)
            
            return True
        except Exception as e:
            st.error(f"Erro na descriptografia híbrida: {e}")
            logger.error(f"Erro na descriptografia híbrida de {input_file_path}: {traceback.format_exc()}")
            return False


# --- Streamlit UI Setup ---
def setup_ui():
    if 'db_type' not in st.session_state:
        st.session_state.db_type = "Standard" # Default to Standard DB

    if 'db' not in st.session_state:
        st.session_state.db = TrafficAccidentsDB(DB_PATH, INDEX_PATH, ID_COUNTER_PATH, LOCK_PATH)
    
    if 'btree_db' not in st.session_state:
        st.session_state.btree_db = TrafficAccidentsTree(APP_CONFIG["BTREE_DB_FILE_NAME"])
    
    st.sidebar.title("Opções do Banco de Dados")
    db_choice = st.sidebar.radio("Escolha o tipo de Banco de Dados:", ("Standard (Arquivo)", "B-Tree (Em Disco)"))
    st.session_state.db_type = db_choice

    if st.sidebar.button("Fazer Backup DB"):
        if st.session_state.db.backup_db():
            st.sidebar.success("Backup do DB padrão criado!")
        else:
            st.sidebar.error("Falha ao criar backup do DB padrão.")

    st.sidebar.subheader("Restaurar Backup DB")
    backup_files = list(Path(BACKUP_PATH).glob(f"{APP_CONFIG['DB_FILE_NAME']}_*.bak"))
    backup_files_sorted = sorted(backup_files, key=os.path.getmtime, reverse=True)
    backup_options = [f.name for f in backup_files_sorted]
    
    if backup_options:
        selected_backup = st.sidebar.selectbox("Selecione o backup para restaurar:", backup_options)
        if st.sidebar.button("Restaurar DB Selecionado"):
            if st.session_state.db.restore_db(Path(BACKUP_PATH) / selected_backup):
                st.sidebar.success(f"DB restaurado de {selected_backup}")
                st.experimental_rerun()
            else:
                st.sidebar.error(f"Falha ao restaurar DB de {selected_backup}")
    else:
        st.sidebar.info("Nenhum backup disponível.")

    st.title("Sistema de Gerenciamento de Acidentes de Trânsito")

    tab_overview, tab_crud, tab_import_export, tab_search_index, tab_compression, tab_admin, tab_crypto = st.tabs([
        "Visão Geral", "CRUD de Registros", "Importar/Exportar CSV", "Busca e Indexação",
        "Compactação", "Administração", "Criptografia"
    ])

    with tab_overview:
        show_overview_tab()
    with tab_crud:
        show_crud_tab()
    with tab_import_export:
        show_import_export_tab()
    with tab_search_index:
        show_search_index_tab()
    with tab_compression:
        show_compression_tab()
    with tab_admin:
        show_admin_tab()
    with tab_crypto:
        show_crypto_tab() # New tab for crypto operations

def show_overview_tab():
    st.header("Visão Geral do Banco de Dados")
    st.write(f"Você está usando o tipo de DB: **{st.session_state.db_type}**")

    current_db = st.session_state.db if st.session_state.db_type == "Standard (Arquivo)" else st.session_state.btree_db

    if st.session_state.db_type == "Standard (Arquivo)":
        st.write(f"Caminho do arquivo DB padrão: `{DB_PATH}`")
        st.write(f"Caminho do arquivo de índice: `{INDEX_PATH}`")
        st.write(f"Caminho do contador de IDs: `{ID_COUNTER_PATH}`")
        st.write(f"Caminho do arquivo de lock: `{LOCK_PATH}`")
    else: # B-Tree
        st.write(f"Caminho do arquivo DB B-Tree: `{BTREE_DB_PATH}`")
        st.write(f"Tamanho da Página B-Tree: {APP_CONFIG['BTREE_PAGE_SIZE']} bytes")
        st.write(f"Grau Mínimo (t) da B-Tree: {APP_CONFIG['BTREE_MIN_DEGREE']}")

    total_records = current_db.count_records()
    st.metric("Total de Registros", total_records)

    st.subheader("Informações do Sistema")
    st.info(f"Diretório Base do DB: `{APP_CONFIG['DB_DIR']}`")
    st.info(f"Diretório de Backups: `{BACKUP_PATH}`")
    st.info(f"Arquivo de Log: `{LOG_FILE_PATH}`")
    st.info(f"Diretório de Chaves RSA: `{APP_CONFIG['RSA_KEYS_DIR']}`")


def show_crud_tab():
    st.header("Operações CRUD de Registros")
    
    current_db = st.session_state.db if st.session_state.db_type == "Standard (Arquivo)" else st.session_state.btree_db

    operation = st.radio("Selecione a Operação:", ("Adicionar", "Buscar", "Atualizar", "Excluir"))

    if operation == "Adicionar":
        st.subheader("Adicionar Novo Registro")
        with st.form("add_record_form"):
            new_data = {}
            # Use fixed fields for input for simplicity in Streamlit
            new_data["id"] = st.number_input("ID (deixe 0 para auto-incrementar):", min_value=0, value=0, format="%d")
            new_data["data"] = st.text_input("Data (DD/MM/YYYY):", "01/01/2023")
            new_data["hora"] = st.text_input("Hora (HHhMM):", "10h30")
            new_data["uf"] = st.text_input("UF (ex: MG):", "MG").upper()
            new_data["br"] = st.number_input("BR:", min_value=0, value=101)
            new_data["km"] = st.number_input("KM:", min_value=0.0, value=0.0, format="%.2f")
            new_data["municipio"] = st.text_input("Município:", "BELO HORIZONTE").upper()
            new_data["causa_acidente"] = st.text_input("Causa do Acidente:", "Falta de Atenção")
            new_data["tipo_acidente"] = st.text_input("Tipo de Acidente:", "Colisão Traseira")
            new_data["classificacao_acidente"] = st.selectbox("Classificação do Acidente:", DataObject.VALIDATION_RULES["classificacao_acidente"].__annotations__['return'] if isinstance(DataObject.VALIDATION_RULES["classificacao_acidente"], type) else ["Sem Vítimas", "Com Vítimas Feridas", "Com Vítimas Fatais"])
            new_data["fase_dia"] = st.selectbox("Fase do Dia:", ["Plena Noite", "Amanhecer", "Pleno Dia", "Anoitecer"])
            new_data["condicao_metereologica"] = st.selectbox("Condição Meteorológica:", ["Ceu Claro", "Chuva", "Garoa/Chuvisco", "Nevoa/Neblina", "Vento", "Granizo", "Ceu Nublado", "Sol", "Ignorada"])
            new_data["tipo_pista"] = st.selectbox("Tipo de Pista:", ["Dupla", "Simples", "Múltipla", "Múltiplas pistas"])
            new_data["tracado_via"] = st.selectbox("Traçado da Via:", ["Reta", "Curva", "Interseção", "Retorno", "Desvio", "Viaduto", "Ponte", "Túnel", "Rotatória"])
            new_data["uso_solo"] = st.selectbox("Uso do Solo:", ["Rural", "Urbano"])
            new_data["pessoas"] = st.number_input("Pessoas Envolvidas:", min_value=0, value=0)
            new_data["mortos"] = st.number_input("Mortos:", min_value=0, value=0)
            new_data["feridos_leves"] = st.number_input("Feridos Leves:", min_value=0, value=0)
            new_data["feridos_graves"] = st.number_input("Feridos Graves:", min_value=0, value=0)
            new_data["ilesos"] = st.number_input("Ilesos:", min_value=0, value=0)
            new_data["ignorados"] = st.number_input("Ignorados:", min_value=0, value=0)
            new_data["feridos"] = st.number_input("Feridos (Total):", min_value=0, value=0)
            new_data["veiculos"] = st.number_input("Veículos Envolvidos:", min_value=0, value=0)
            
            submitted = st.form_submit_button("Adicionar Registro")
            if submitted:
                try:
                    data_obj = DataObject(**new_data)
                    record_id = current_db.add_record(data_obj)
                    if record_id:
                        st.success(f"Registro adicionado com sucesso! ID: {record_id}")
                        logger.info(f"Record {record_id} added via UI.")
                        st.experimental_rerun()
                    else:
                        st.error("Falha ao adicionar registro.")
                except DataValidationError as e:
                    st.error(f"Erro de validação: {e}")
                    logger.error(f"Validation error adding record: {e}")
                except Exception as e:
                    st.error(f"Erro inesperado: {e}")
                    logger.error(f"Unexpected error adding record: {traceback.format_exc()}")

    elif operation == "Buscar":
        st.subheader("Buscar Registro por ID")
        search_id = st.number_input("ID do Registro para Buscar:", min_value=1, format="%d")
        if st.button("Buscar Registro"):
            record = current_db.get_record(search_id)
            if record:
                st.json(record.to_dict())
            else:
                st.warning(f"Registro com ID {search_id} não encontrado.")

    elif operation == "Atualizar":
        st.subheader("Atualizar Registro Existente")
        update_id = st.number_input("ID do Registro para Atualizar:", min_value=1, format="%d")
        
        existing_record = None
        if update_id:
            existing_record = current_db.get_record(update_id)
            if not existing_record:
                st.info("Insira um ID e clique em 'Carregar Registro' para preencher os campos.")

        if st.button("Carregar Registro"):
            if existing_record:
                st.session_state[f'update_form_data_{update_id}'] = existing_record.to_dict()
                st.success(f"Registro {update_id} carregado para edição.")
            else:
                st.warning(f"Registro com ID {update_id} não encontrado.")

        if existing_record or (f'update_form_data_{update_id}' in st.session_state and st.session_state[f'update_form_data_{update_id}']['id'] == update_id):
            current_data = st.session_state.get(f'update_form_data_{update_id}', existing_record.to_dict() if existing_record else {})
            
            with st.form("update_record_form"):
                updated_data = {}
                # Populate fields with current_data
                for field in DataObject.REQUIRED_FIELDS:
                    if field == "id": # ID is not editable
                        st.text_input("ID:", value=current_data.get(field, ''), disabled=True, key=f"update_{field}")
                        updated_data[field] = current_data.get(field)
                    elif field == "classificacao_acidente":
                        updated_data[field] = st.selectbox("Classificação do Acidente:", ["Sem Vítimas", "Com Vítimas Feridas", "Com Vítimas Fatais"], index=["Sem Vítimas", "Com Vítimas Feridas", "Com Vítimas Fatais"].index(current_data.get(field, "Sem Vítimas")), key=f"update_{field}")
                    elif field == "fase_dia":
                        updated_data[field] = st.selectbox("Fase do Dia:", ["Plena Noite", "Amanhecer", "Pleno Dia", "Anoitecer"], index=["Plena Noite", "Amanhecer", "Pleno Dia", "Anoitecer"].index(current_data.get(field, "Pleno Dia")), key=f"update_{field}")
                    elif field == "condicao_metereologica":
                        options = ["Ceu Claro", "Chuva", "Garoa/Chuvisco", "Nevoa/Neblina", "Vento", "Granizo", "Ceu Nublado", "Sol", "Ignorada"]
                        updated_data[field] = st.selectbox("Condição Meteorológica:", options, index=options.index(current_data.get(field, "Ceu Claro")), key=f"update_{field}")
                    elif field == "tipo_pista":
                        options = ["Dupla", "Simples", "Múltipla", "Múltiplas pistas"]
                        updated_data[field] = st.selectbox("Tipo de Pista:", options, index=options.index(current_data.get(field, "Simples")), key=f"update_{field}")
                    elif field == "tracado_via":
                        options = ["Reta", "Curva", "Interseção", "Retorno", "Desvio", "Viaduto", "Ponte", "Túnel", "Rotatória"]
                        updated_data[field] = st.selectbox("Traçado da Via:", options, index=options.index(current_data.get(field, "Reta")), key=f"update_{field}")
                    elif field == "uso_solo":
                        options = ["Rural", "Urbano"]
                        updated_data[field] = st.selectbox("Uso do Solo:", options, index=options.index(current_data.get(field, "Rural")), key=f"update_{field}")
                    elif field == "br":
                        updated_data[field] = st.number_input("BR:", min_value=0, value=current_data.get(field, 0), key=f"update_{field}")
                    elif field == "km":
                        updated_data[field] = st.number_input("KM:", min_value=0.0, value=float(current_data.get(field, 0.0)), format="%.2f", key=f"update_{field}")
                    elif DataObject.FIELD_TYPES[field] == int:
                        updated_data[field] = st.number_input(f"{field.replace('_', ' ').title()}:", min_value=0, value=current_data.get(field, 0), key=f"update_{field}")
                    else:
                        updated_data[field] = st.text_input(f"{field.replace('_', ' ').title()}:", value=str(current_data.get(field, '')), key=f"update_{field}")
                
                update_submitted = st.form_submit_button("Atualizar Registro")
                if update_submitted:
                    try:
                        updated_data_obj = DataObject(**updated_data)
                        if current_db.update_record(updated_data_obj):
                            st.success(f"Registro {update_id} atualizado com sucesso!")
                            logger.info(f"Record {update_id} updated via UI.")
                            if f'update_form_data_{update_id}' in st.session_state:
                                del st.session_state[f'update_form_data_{update_id}'] # Clear form data
                            st.experimental_rerun()
                        else:
                            st.error("Falha ao atualizar registro.")
                    except DataValidationError as e:
                        st.error(f"Erro de validação: {e}")
                        logger.error(f"Validation error updating record {update_id}: {e}")
                    except Exception as e:
                        st.error(f"Erro inesperado: {e}")
                        logger.error(f"Unexpected error updating record {update_id}: {traceback.format_exc()}")
        
    elif operation == "Excluir":
        st.subheader("Excluir Registro por ID")
        delete_id = st.number_input("ID do Registro para Excluir:", min_value=1, format="%d")
        if st.button("Excluir Registro"):
            if current_db.delete_record(delete_id):
                st.success(f"Registro {delete_id} excluído com sucesso (marcado para remoção física na compactação).")
                logger.info(f"Record {delete_id} deleted via UI.")
                st.experimental_rerun()
            else:
                st.error(f"Falha ao excluir registro {delete_id}.")

    st.subheader("Listar Todos os Registros")
    total_records = current_db.count_records()
    if total_records == 0:
        st.info("Nenhum registro encontrado no banco de dados.")
    else:
        pages = math.ceil(total_records / APP_CONFIG["MAX_RECORDS_PER_PAGE"])
        current_page = st.number_input(f"Página (1-{pages}):", min_value=1, max_value=pages, value=1 if pages > 0 else 0)
        
        if current_page > 0: # Only list if there's at least one page
            records = current_db.list_records(current_page, APP_CONFIG["MAX_RECORDS_PER_PAGE"])
            
            # Convert list of DataObject to list of dicts for display
            records_data = [record.to_dict() for record in records]
            
            st.dataframe(records_data, use_container_width=True)

def show_import_export_tab():
    st.header("Importar/Exportar Dados CSV")

    current_db = st.session_state.db if st.session_state.db_type == "Standard (Arquivo)" else st.session_state.btree_db

    st.subheader("Importar CSV")
    uploaded_file = st.file_uploader("Escolha um arquivo CSV para importar", type="csv")
    if uploaded_file is not None:
        if st.button("Iniciar Importação"):
            try:
                # Use tempfile to handle the uploaded file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                with st.spinner("Importando registros do CSV..."):
                    imported_count = 0
                    with open(tmp_path, 'r', encoding='utf-8') as csvfile:
                         reader = csv.reader(csvfile, delimiter=APP_CONFIG["CSV_DELIMITER"])
                         next(reader) # Skip header
                         for row in reader:
                             try:
                                 data_obj = DataObject.from_csv_row(row)
                                 current_db.add_record(data_obj) # Use current_db
                                 imported_count +=1
                             except DataValidationError as e:
                                 logger.warning(f"Skipping invalid CSV row: {row} - Error: {e}")
                    st.success(f"Importação completa! Adicionados {imported_count} novos registros.")

            except Exception as e:
                st.error(f"Ocorreu um erro durante a importação do CSV: {e}")
                logger.error(f"Importação CSV falhou: {traceback.format_exc()}")
            finally:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    st.subheader("Exportar CSV")
    if st.button("Exportar Todos os Registros para CSV"):
        try:
            all_records = []
            # For standard DB, iterate through index
            if st.session_state.db_type == "Standard (Arquivo)":
                for record_id in sorted(st.session_state.db.index.keys()):
                    record = st.session_state.db.get_record(record_id)
                    if record:
                        all_records.append(record)
            # For B-Tree, iterate through a search of all keys (needs a proper B-Tree iterator)
            # For simplicity for B-Tree, we'll retrieve all by ID if possible, or just skip
            # A full B-Tree implementation would need an in-order traversal for efficient export.
            else: # B-Tree
                st.warning("Exportação para B-Tree irá buscar registros um por um. Pode ser lento para muitos registros.")
                # This is an inefficient way to get all records from B-Tree.
                # A proper B-Tree would have an iterator for ordered traversal.
                # For demonstration, we'll try to get all IDs if they are sequential.
                # Or a simple approach: if you know min/max ID, iterate.
                # Given current B-Tree, there's no easy way to get all without knowing keys.
                # For now, let's assume the B-Tree only stores what's in traffic_accidents.db
                # and you might want to export the original data, not just what's in B-Tree.
                # If the B-Tree is the *sole* source of truth, this needs to be implemented.
                # For this combined file, let's make it fetch from the original DB for export for now.
                # TODO: Implement a proper B-Tree traversal for export.
                
                # For now, let's iterate through the IDs in the index if the B-Tree is used for index only
                # if current_db.db_file_path == BTREE_DB_PATH: # If it's the B-Tree
                #     all_ids_in_btree = [] # How to get all keys from B-Tree without traversal?
                #     # This is a major gap. Assuming a separate iteration or temporary standard DB.
                #     st.error("Exportação completa de dados da B-Tree não totalmente implementada ainda.")
                #     return
                
                # Fallback: if using B-Tree, but want to export original DB for testing, use standard DB
                # This is a conceptual divergence. The user's original problem implies two DBs.
                # For export, we'll use the *currently selected* DB type.
                # For B-Tree, current_db.list_records will attempt to list.
                all_records = []
                # Attempt to get all records by iterating through pages in the selected DB
                num_pages = math.ceil(current_db.count_records() / APP_CONFIG["MAX_RECORDS_PER_PAGE"])
                for page_num in range(1, num_pages + 1):
                    all_records.extend(current_db.list_records(page_num, APP_CONFIG["MAX_RECORDS_PER_PAGE"]))

            if not all_records:
                st.info("Nenhum registro para exportar.")
                return

            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer, delimiter=APP_CONFIG["CSV_DELIMITER"])
            
            # Write header
            csv_writer.writerow(DataObject.REQUIRED_FIELDS)
            
            # Write data rows
            for record in all_records:
                csv_writer.writerow(record.to_csv_row())
            
            st.download_button(
                label="Download CSV",
                data=csv_buffer.getvalue().encode('utf-8'),
                file_name="traffic_accidents_export.csv",
                mime="text/csv"
            )
            st.success("Dados exportados para CSV com sucesso!")
        except Exception as e:
            st.error(f"Erro ao exportar CSV: {e}")
            logger.error(f"Erro ao exportar CSV: {traceback.format_exc()}")


def show_search_index_tab():
    st.header("Busca e Indexação")
    
    current_db = st.session_state.db if st.session_state.db_type == "Standard (Arquivo)" else st.session_state.btree_db

    search_id = st.number_input("ID do Registro para Buscar:", min_value=1, format="%d", key="search_index_id")
    if st.button("Buscar no Índice"):
        start_time = time.time()
        record = current_db.get_record(search_id) # This uses the internal index/B-Tree
        end_time = time.time()
        
        if record:
            st.success(f"Registro encontrado! Tempo de busca: {end_time - start_time:.6f} segundos")
            st.json(record.to_dict())
        else:
            st.warning(f"Registro com ID {search_id} não encontrado no índice.")
            st.info(f"Tempo de busca: {end_time - start_time:.6f} segundos")

    st.subheader("Estatísticas do Índice")
    if st.session_state.db_type == "Standard (Arquivo)":
        st.write(f"Número de entradas no índice: {len(st.session_state.db.index)}")
        index_size_bytes = os.path.getsize(INDEX_PATH) if os.path.exists(INDEX_PATH) else 0
        st.write(f"Tamanho do arquivo de índice: {index_size_bytes / 1024:.2f} KB")
    else: # B-Tree
        st.write(f"Caminho do arquivo DB B-Tree: `{BTREE_DB_PATH}`")
        st.write(f"Número de páginas na B-Tree: {st.session_state.btree_db.pager.num_pages}")
        st.write(f"Ordem da B-Tree (t): {st.session_state.btree_db.t}")
        btree_file_size = os.path.getsize(BTREE_DB_PATH) if os.path.exists(BTREE_DB_PATH) else 0
        st.write(f"Tamanho do arquivo da B-Tree: {btree_file_size / 1024:.2f} KB")
        # Option to clear B-Tree DB for testing
        if st.button("Limpar Banco de Dados B-Tree"):
            if os.path.exists(BTREE_DB_PATH):
                try:
                    st.session_state.btree_db.pager.flush_all()
                    st.session_state.btree_db.pager.file.close()
                    os.remove(BTREE_DB_PATH)
                    # Re-initialize the B-Tree instance
                    st.session_state.btree_db = TrafficAccidentsTree(APP_CONFIG["BTREE_DB_FILE_NAME"]) 
                    st.success("Banco de dados B-Tree limpo e reiniciado.")
                    logger.info("B-Tree database cleared.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao limpar banco de dados B-Tree: {e}")
                    logger.error(f"Error cleaning B-Tree DB: {traceback.format_exc()}")
            else:
                st.info("O arquivo do banco de dados B-Tree não existe para ser limpo.")


def show_compression_tab():
    st.header("Compactação de Arquivos")

    compression_type = st.radio("Selecione o Algoritmo de Compactação:", ("Huffman", "LZW"))

    st.subheader("Compactar Arquivo")
    uploaded_file_compress = st.file_uploader("Escolha um arquivo para compactar", type=None, key="compress_upload")
    
    if uploaded_file_compress is not None:
        input_path_temp = os.path.join(tempfile.gettempdir(), uploaded_file_compress.name)
        with open(input_path_temp, "wb") as f:
            f.write(uploaded_file_compress.getbuffer())

        output_dir = HUFFMAN_FOLDER if compression_type == "Huffman" else LZW_FOLDER
        output_filename = uploaded_file_compress.name + (COMPRESSED_EXTENSION_HUFF if compression_type == "Huffman" else COMPRESSED_EXTENSION_LZW)
        output_path = os.path.join(output_dir, output_filename)

        if st.button(f"Compactar com {compression_type}"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(p):
                progress_bar.progress(p)
                status_text.text(f"Progresso: {p*100:.1f}%")

            try:
                if compression_type == "Huffman":
                    compressed_size, original_size, compression_ratio, process_time = HuffmanProcessor.compress_file(input_path_temp, output_path, update_progress)
                else: # LZW
                    compressed_size, original_size, compression_ratio, process_time = LZWProcessor.compress(input_path_temp, output_path, update_progress)
                
                st.success(f"Arquivo compactado com sucesso em: `{output_path}`")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tamanho Original", f"{original_size:,} bytes")
                    st.metric("Taxa de Compactação", f"{compression_ratio:.2f}%")
                with col2:
                    st.metric("Tamanho Compactado", f"{compressed_size:,} bytes")
                    st.metric("Tempo de Processamento", f"{process_time:.4f} seg")
                logger.info(f"File {uploaded_file_compress.name} compressed with {compression_type}. Ratio: {compression_ratio:.2f}%")
            except Exception as e:
                st.error(f"Erro durante a compactação: {e}")
                logger.error(f"Compression failed: {traceback.format_exc()}")
            finally:
                os.unlink(input_path_temp) # Clean up temp file
                progress_bar.empty()
                status_text.empty()

    st.subheader("Descompactar Arquivo")
    
    # List available compressed files in respective folders
    huff_files = [f.name for f in Path(HUFFMAN_FOLDER).glob(f"*{COMPRESSED_EXTENSION_HUFF}")]
    lzw_files = [f.name for f in Path(LZW_FOLDER).glob(f"*{COMPRESSED_EXTENSION_LZW}")]
    
    available_files = []
    if compression_type == "Huffman":
        available_files = huff_files
    else:
        available_files = lzw_files

    if not available_files:
        st.info(f"Nenhum arquivo compactado ({compression_type}) encontrado no diretório: {HUFFMAN_FOLDER if compression_type == 'Huffman' else LZW_FOLDER}")
    else:
        selected_file_decompress = st.selectbox(f"Selecione um arquivo {compression_type} para descompactar:", available_files, key="decompress_select")
        
        if selected_file_decompress and st.button(f"Descompactar com {compression_type}"):
            input_path_decompress = os.path.join(HUFFMAN_FOLDER if compression_type == "Huffman" else LZW_FOLDER, selected_file_decompress)
            
            output_filename = selected_file_decompress.replace(COMPRESSED_EXTENSION_HUFF if compression_type == "Huffman" else COMPRESSED_EXTENSION_LZW, "")
            output_path_decompress = os.path.join(output_dir, "decompressed_" + output_filename) # Add prefix to avoid overwrite

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(p):
                progress_bar.progress(p)
                status_text.text(f"Progresso: {p*100:.1f}%")

            try:
                if compression_type == "Huffman":
                    compressed_size, decompressed_size, compression_ratio, process_time = HuffmanProcessor.decompress_file(input_path_decompress, output_path_decompress, update_progress)
                else: # LZW
                    compressed_size, decompressed_size, compression_ratio, process_time = LZWProcessor.decompress(input_path_decompress, output_path_decompress, update_progress)
                
                st.success(f"Arquivo descompactado com sucesso em: `{output_path_decompress}`")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tamanho Compactado", f"{compressed_size:,} bytes")
                    st.metric("Taxa de Compactação", f"{compression_ratio:.2f}%")
                with col2:
                    st.metric("Tamanho Descompactado", f"{decompressed_size:,} bytes")
                    st.metric("Tempo de Processamento", f"{process_time:.4f} seg")
                logger.info(f"File {selected_file_decompress} decompressed with {compression_type}. Ratio: {compression_ratio:.2f}%")
            except Exception as e:
                st.error(f"Erro durante a descompactação: {e}")
                logger.error(f"Decompression failed: {traceback.format_exc()}")
            finally:
                progress_bar.empty()
                status_text.empty()

def show_admin_tab():
    st.header("Funções Administrativas")

    st.subheader("Log de Atividades")
    if os.path.exists(APP_CONFIG["LOG_FILE_NAME"]):
        with open(APP_CONFIG["LOG_FILE_NAME"], "r", encoding="utf-8") as f:
            log_content = f.readlines()
        
        display_entries = []
        for line in reversed(log_content): # Show most recent first
            try:
                # Basic parsing to highlight info/warning/error
                match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.*?) - (INFO|WARNING|ERROR|CRITICAL) - (.*)", line)
                if match:
                    timestamp_str, name, log_level, message = match.groups()
                    if log_level == "ERROR" or log_level == "CRITICAL":
                        display_entries.append(f"🚨 **`{timestamp_str}`** `{log_level}` `{message}`")
                    elif log_level == "WARNING":
                        display_entries.append(f"⚠️ **`{timestamp_str}`** `{log_level}` `{message}`")
                    else:
                        display_entries.append(f"ℹ️ **`{timestamp_str}`** `{log_level}` `{message}`")

                    if len(display_entries) >= APP_CONFIG["MAX_LOG_ENTRIES_DISPLAY"]:
                        break
            except Exception as e:
                logger.warning(f"Failed to parse log line for registry: {line.strip()} - {e}")
                continue
        
        if display_entries:
            for entry in display_entries:
                st.markdown(entry, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Nenhum registro recente de atividade relevante encontrado no log.")
    else:
        st.info("ℹ️ Arquivo de log de atividades não encontrado.")

    st.subheader("Limpar Banco de Dados")
    st.warning("Esta ação removerá *TODOS* os registros do banco de dados e do índice. CUIDADO!")
    confirm_clear = st.checkbox("Sim, eu entendo que esta ação é irreversível e desejo limpar o DB.")
    if confirm_clear and st.button("Limpar DB Agora"):
        try:
            # Clear standard DB
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            if os.path.exists(INDEX_PATH):
                os.remove(INDEX_PATH)
            if os.path.exists(ID_COUNTER_PATH):
                os.remove(ID_COUNTER_PATH)
            st.session_state.db = TrafficAccidentsDB(DB_PATH, INDEX_PATH, ID_COUNTER_PATH, LOCK_PATH) # Re-initialize
            
            # Clear B-Tree DB
            if os.path.exists(BTREE_DB_PATH):
                st.session_state.btree_db.pager.flush_all()
                st.session_state.btree_db.pager.file.close()
                os.remove(BTREE_DB_PATH)
                st.session_state.btree_db = TrafficAccidentsTree(APP_CONFIG["BTREE_DB_FILE_NAME"]) # Re-initialize
            
            st.success("Banco de dados principal e B-Tree limpos com sucesso!")
            logger.info("All databases cleared via admin UI.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao limpar o banco de dados: {e}")
            logger.error(f"Error clearing databases: {traceback.format_exc()}")

    st.subheader("Compactar Banco de Dados (Standard)")
    st.info("A compactação remove registros 'excluídos' ou 'stale' fisicamente do arquivo de dados, recuperando espaço.")
    if st.button("Executar Compactação Agora"):
        st.session_state.db.compact_db()
        st.experimental_rerun()

def show_crypto_tab():
    st.header("Operações de Criptografia")

    CryptographyHandler.generate_rsa_keys()

    st.subheader("Criptografar/Descriptografar Arquivos do Banco de Dados (AES + RSA)")
    st.info(f"As chaves RSA (pública e privada) devem estar em: `{APP_CONFIG['RSA_KEYS_DIR']}`")

    operation = st.radio("Selecione a Operação:", ("Criptografar", "Descriptografar"), key="crypto_op_choice")

    file_type = st.selectbox("Escolha o tipo de arquivo:",
                             ("Banco de Dados Padrão (.db)", "Índice Padrão (.idx)", "Banco de Dados B-Tree (.btr)"))

    target_file = ""
    if file_type == "Banco de Dados Padrão (.db)":
        target_file = DB_PATH
    elif file_type == "Índice Padrão (.idx)":
        target_file = INDEX_PATH
    elif file_type == "Banco de Dados B-Tree (.btr)":
        target_file = BTREE_DB_PATH
    
    st.write(f"Arquivo alvo: `{target_file}`")

    if operation == "Criptografar":
        output_encrypted_file = st.text_input("Nome do arquivo de saída criptografado (ex: data.db.enc):", f"{os.path.basename(target_file)}.enc")
        if st.button(f"Criptografar {file_type}"):
            if CryptographyHandler.hybrid_encrypt_file(target_file, os.path.join(APP_CONFIG["DB_DIR"], output_encrypted_file), RSA_PUBLIC_KEY_PATH):
                st.success(f"{file_type} criptografado com sucesso para `{output_encrypted_file}`!")
                logger.info(f"{file_type} encrypted to {output_encrypted_file}")
            else:
                st.error(f"Falha ao criptografar {file_type}.")

    elif operation == "Descriptografar":
        input_encrypted_file = st.text_input("Caminho do arquivo criptografado para descriptografar:", f"{os.path.basename(target_file)}.enc")
        output_decrypted_file = st.text_input("Nome do arquivo de saída descriptografado (ex: data.db.dec):", f"{os.path.basename(target_file)}.dec")
        private_key_password = st.text_input("Senha da Chave Privada (se houver):", type="password", key="private_key_pass")

        if st.button(f"Descriptografar {file_type}"):
            full_input_path = os.path.join(APP_CONFIG["DB_DIR"], input_encrypted_file)
            full_output_path = os.path.join(APP_CONFIG["DB_DIR"], output_decrypted_file)

            if CryptographyHandler.hybrid_decrypt_file(full_input_path, full_output_path, RSA_PRIVATE_KEY_PATH, private_key_password):
                st.success(f"{file_type} descriptografado com sucesso para `{output_decrypted_file}`!")
                logger.info(f"{file_type} decrypted to {output_decrypted_file}")
            else:
                st.error(f"Falha ao descriptografar {file_type}.")
    
    st.subheader("Criptografia/Descriptografia Blowfish (Placeholder)")
    st.info("As funções Blowfish são apenas placeholders e não possuem uma implementação completa aqui.")
    CryptographyHandler.blowfish_encrypt_file()
    CryptographyHandler.blowfish_decrypt_file()


# --- Main Application Entry Point ---
if __name__ == "__main__":
    try:
        # Ensure base directories exist
        Path(APP_CONFIG["DB_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
        Path(APP_CONFIG["RSA_KEYS_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(HUFFMAN_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(LZW_FOLDER).mkdir(parents=True, exist_ok=True)

        setup_ui()
    except Exception as e:
        st.error(f"A critical error occurred in the application: {e}")
        logger.critical(f"Unhandled exception in main app entry point: {traceback.format_exc()}")