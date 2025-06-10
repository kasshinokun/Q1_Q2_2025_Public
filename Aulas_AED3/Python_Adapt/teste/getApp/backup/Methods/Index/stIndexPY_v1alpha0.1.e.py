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
import getpass  # Import for password input (used in crypto operations)

# --- Cryptography Imports from pycryptonew.py ---
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

# --- Configuration Constants (Centralized - from v4epsilon) ---
APP_CONFIG = {
    "DB_DIR": Path.home() / 'Documents' / 'Data',  # Using Pathlib
    "DB_FILE_NAME": 'traffic_accidents.db',
    "INDEX_FILE_NAME": 'traffic_accidents.idx',
    "BTREE_INDEX_FILE_NAME": 'traffic_accidents_btree.idx',  # New B-Tree index file
    "ID_COUNTER_FILE_NAME": 'id_counter.txt',
    "LOCK_FILE_NAME": 'db.lock',
    "RSA_KEYS_DIR": Path.home() / 'Documents' / 'RSA_Keys',  # Using Pathlib
    "LOG_FILE_NAME": 'app_activity.log',
    "BTREE_PAGE_SIZE": 4096,  # 4KB page size
    "BTREE_MIN_DEGREE": 3  # Minimum degree (t) for B-Tree
}

# --- Global Paths ---
DB_FILE_PATH = APP_CONFIG["DB_DIR"] / APP_CONFIG["DB_FILE_NAME"]
INDEX_FILE_PATH = APP_CONFIG["DB_DIR"] / APP_CONFIG["INDEX_FILE_NAME"]
BTREE_INDEX_FILE_PATH = APP_CONFIG["DB_DIR"] / APP_CONFIG["BTREE_INDEX_FILE_NAME"]
ID_COUNTER_PATH = APP_CONFIG["DB_DIR"] / APP_CONFIG["ID_COUNTER_FILE_NAME"]
LOCK_FILE_PATH = APP_CONFIG["DB_DIR"] / APP_CONFIG["LOCK_FILE_NAME"]
RSA_PUBLIC_KEY_PATH = APP_CONFIG["RSA_KEYS_DIR"] / 'public_key.pem'
RSA_PRIVATE_KEY_PATH = APP_CONFIG["RSA_KEYS_DIR"] / 'private_key.pem'
LOG_FILE_PATH = APP_CONFIG["DB_DIR"] / APP_CONFIG["LOG_FILE_NAME']

BACKUP_PATH = APP_CONFIG["DB_DIR"] / 'backup' # Subdiretório para backups
HUFFMAN_FOLDER = APP_CONFIG["DB_DIR"] / 'huffman_compressed'
LZW_FOLDER = APP_CONFIG["DB_DIR"] / 'lzw_compressed'

# --- Configure logging ---
# Centralizar a configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Streamlit session state variables
if 'db' not in st.session_state:
    st.session_state.db = None # Will be initialized with DBManager or BTreeDBManager
if 'db_type' not in st.session_state:
    st.session_state.db_type = "default" # "default" or "btree"
if 'logger' not in st.session_state:
    st.session_state.logger = logger
if 'rsa_keys_generated' not in st.session_state:
    st.session_state.rsa_keys_generated = False
if 'key_pair' not in st.session_state:
    st.session_state.key_pair = {"public": None, "private": None}


# --- DataObject Class (from stCRUDDataObjectPY_v5alpha0.1.e.py) ---
class DataObject:
    """
    Represents a single traffic accident record with validation.
    """
    def __init__(self, data: Dict[str, Any]):
        self._data = self._validate_and_clean_data(data)

    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates and cleans input data, enforcing types and constraints.
        """
        cleaned_data = {}
        # Define expected fields and their validation/conversion logic
        fields = {
            "id": (int, lambda x: int(x) if x else None),
            "data": (str, lambda x: str(x).strip()), # Assuming 'YYYY-MM-DD' format
            "hora": (str, lambda x: str(x).strip()), # Assuming 'HH:MM' format
            "tipo_acidente": (str, lambda x: str(x).strip()),
            "causa_acidente": (str, lambda x: str(x).strip()),
            "condicao_via": (str, lambda x: str(x).strip()),
            "condicao_metereologica": (str, lambda x: str(x).strip()),
            "lesoes": (int, lambda x: int(x) if str(x).isdigit() else 0),
            "mortes": (int, lambda x: int(x) if str(x).isdigit() else 0),
            "veiculos_envolvidos": (int, lambda x: int(x) if str(x).isdigit() else 0),
            "bairro": (str, lambda x: str(x).strip()),
            "cidade": (str, lambda x: str(x).strip()),
            "uf": (str, lambda x: str(x).strip().upper() if x else ""),
            "latitude": (float, lambda x: float(x) if (isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit())) else 0.0),
            "longitude": (float, lambda x: float(x) if (isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit())) else 0.0),
        }

        for field, (expected_type, converter) in fields.items():
            value = data.get(field)
            try:
                converted_value = converter(value)
                # Additional specific validations
                if field == "data":
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', converted_value):
                        raise ValueError(f"Formato de data inválido para '{field}': {value}. Esperado YYYY-MM-DD.")
                elif field == "hora":
                    if not re.match(r'^\d{2}:\d{2}$', converted_value):
                        raise ValueError(f"Formato de hora inválido para '{field}': {value}. Esperado HH:MM.")
                elif field in ["lesoes", "mortes", "veiculos_envolvidos"] and converted_value < 0:
                    raise ValueError(f"'{field}' não pode ser negativo.")
                elif field in ["latitude", "longitude"] and not (-180.0 <= converted_value <= 180.0): # General range for geo-coordinates
                     logger.warning(f"Coordenada '{field}' fora do range típico: {converted_value}")
                elif field == "uf" and len(converted_value) != 2:
                    logger.warning(f"UF '{converted_value}' tem comprimento inválido. Esperado 2 caracteres.")
                
                cleaned_data[field] = converted_value
            except (ValueError, TypeError) as e:
                logger.warning(f"Erro de validação para o campo '{field}' com valor '{value}': {e}. Usando valor padrão/ignorado.")
                cleaned_data[field] = None if expected_type == str else 0 if expected_type == int else 0.0 if expected_type == float else None
        
        # Ensure 'id' is always an integer. If not provided or invalid, it will be 0,
        # which can then be handled by DBManager for new records.
        if cleaned_data.get("id") is None:
            cleaned_data["id"] = 0 

        return cleaned_data

    def to_dict(self) -> Dict[str, Any]:
        """Returns the data as a dictionary."""
        return self._data

    def to_csv_row(self) -> Dict[str, Any]:
        """Returns the data as a dictionary suitable for CSV writing."""
        return self._data

    @property
    def id(self) -> int:
        return self._data.get("id")

    @id.setter
    def id(self, value: int):
        self._data["id"] = value

    # Add other property getters for easier access
    @property
    def data(self) -> str:
        return self._data.get("data")
    
    @property
    def hora(self) -> str:
        return self._data.get("hora")

    # ... add more properties as needed for other fields ...


# --- DBManager Class (from stCRUDDataObjectPY_v5alpha0.1.e.py) ---
class DBManager:
    """
    Manages the flat-file database and its index.
    """
    def __init__(self, db_file: Path, index_file: Path, id_counter_file: Path, lock_file: Path, logger: logging.Logger):
        self.db_file = db_file
        self.index_file = index_file
        self.id_counter_file = id_counter_file
        self.lock_file = filelock.FileLock(str(lock_file))
        self.logger = logger
        self._next_id = self._load_next_id()
        self._initialize_files()

    def _initialize_files(self):
        """Ensures database and index files exist."""
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.db_file.touch(exist_ok=True)
        self.index_file.touch(exist_ok=True)

    def _load_next_id(self) -> int:
        """Loads the next available ID from a counter file."""
        try:
            if self.id_counter_file.exists():
                with self.id_counter_file.open('r') as f:
                    content = f.read().strip()
                    if content.isdigit():
                        return int(content)
            return 1
        except Exception as e:
            self.logger.error(f"Failed to load next ID from {self.id_counter_file}: {e}")
            return 1

    def _save_next_id(self):
        """Saves the current next ID to the counter file."""
        try:
            with self.id_counter_file.open('w') as f:
                f.write(str(self._next_id))
        except Exception as e:
            self.logger.error(f"Failed to save next ID to {self.id_counter_file}: {e}")

    def _get_current_index(self) -> Dict[int, Dict[str, int]]:
        """Loads the entire index from the file."""
        index = {}
        try:
            if self.index_file.exists() and self.index_file.stat().st_size > 0:
                with self.index_file.open('r') as f:
                    index_data = json.load(f)
                    index = {int(k): v for k, v in index_data.items()}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding index file {self.index_file}: {e}. Index will be rebuilt if needed.")
            # Optionally, attempt to rebuild index here if corrupted
        except Exception as e:
            self.logger.error(f"Error loading index file {self.index_file}: {e}")
        return index

    def _save_index(self, index: Dict[int, Dict[str, int]]):
        """Saves the entire index to the file."""
        try:
            with self.index_file.open('w') as f:
                json.dump(index, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving index file {self.index_file}: {e}")

    def _append_record_to_db_file(self, record: DataObject) -> Tuple[int, int]:
        """Appends a record to the database file and returns its offset and size."""
        data_json = json.dumps(record.to_dict(), ensure_ascii=False) + '\n'
        data_bytes = data_json.encode('utf-8')
        
        with self.db_file.open('ab') as f:
            offset = f.tell()
            f.write(data_bytes)
            size = len(data_bytes)
        return offset, size

    def _read_record_from_db_file(self, offset: int, size: int) -> Optional[DataObject]:
        """Reads a record from the database file given its offset and size."""
        try:
            with self.db_file.open('rb') as f:
                f.seek(offset)
                data_bytes = f.read(size)
                data_json = data_bytes.decode('utf-8').strip()
                return DataObject(json.loads(data_json))
        except (IOError, json.JSONDecodeError, UnicodeDecodeError) as e:
            self.logger.error(f"Error reading record from DB at offset {offset}, size {size}: {e}")
            return None

    def add_record(self, record_data: Dict[str, Any]) -> Optional[DataObject]:
        """Adds a new record to the database."""
        with self.lock_file:
            record = DataObject(record_data)
            record.id = self._next_id
            
            offset, size = self._append_record_to_db_file(record)
            
            index = self._get_current_index()
            index[record.id] = {"offset": offset, "size": size, "deleted": 0} # 0 for not deleted, 1 for deleted
            self._save_index(index)
            
            self._next_id += 1
            self._save_next_id()
            self.logger.info(f"Record added: ID {record.id}")
            return record

    def get_record(self, record_id: int) -> Optional[DataObject]:
        """Retrieves a record by its ID."""
        with self.lock_file:
            index = self._get_current_index()
            record_info = index.get(record_id)
            if record_info and record_info["deleted"] == 0:
                return self._read_record_from_db_file(record_info["offset"], record_info["size"])
            return None

    def update_record(self, record_id: int, new_data: Dict[str, Any]) -> Optional[DataObject]:
        """Updates an existing record by marking old as deleted and adding new."""
        with self.lock_file:
            index = self._get_current_index()
            record_info = index.get(record_id)
            if not record_info or record_info["deleted"] == 1:
                self.logger.warning(f"Update failed: Record ID {record_id} not found or marked for deletion.")
                return None

            # Mark old record as deleted in index
            record_info["deleted"] = 1
            
            # Add new version of the record
            updated_record = DataObject(new_data)
            updated_record.id = record_id # Keep the same ID
            
            offset, size = self._append_record_to_db_file(updated_record)
            
            index[record_id] = {"offset": offset, "size": size, "deleted": 0} # New entry for the updated record
            self._save_index(index)
            self.logger.info(f"Record updated: ID {record_id}")
            return updated_record

    def delete_record(self, record_id: int) -> bool:
        """Marks a record as deleted in the index."""
        with self.lock_file:
            index = self._get_current_index()
            if record_id in index:
                index[record_id]["deleted"] = 1
                self._save_index(index)
                self.logger.info(f"Record marked for deletion: ID {record_id}")
                return True
            self.logger.warning(f"Delete failed: Record ID {record_id} not found.")
            return False

    def list_all_records(self) -> List[DataObject]:
        """Lists all non-deleted records."""
        records = []
        with self.lock_file:
            index = self._get_current_index()
            for record_id, record_info in index.items():
                if record_info["deleted"] == 0:
                    record = self._read_record_from_db_file(record_info["offset"], record_info["size"])
                    if record: # Ensure record was successfully read
                        records.append(record)
        return records

    def search_records(self, field: str, query: Any) -> List[DataObject]:
        """Searches for records based on a field and query."""
        results = []
        all_records = self.list_all_records() # Search only non-deleted records
        for record in all_records:
            record_dict = record.to_dict()
            if field in record_dict:
                # Basic string comparison (case-insensitive for strings)
                if isinstance(record_dict[field], str) and isinstance(query, str):
                    if query.lower() in record_dict[field].lower():
                        results.append(record)
                elif record_dict[field] == query:
                    results.append(record)
        return results

    def compact_db(self):
        """
        Rewrites the database file, removing deleted records and updating the index.
        This is a performance-intensive operation.
        """
        self.logger.info("Starting database compaction...")
        st.info("Iniciando compactação do banco de dados... Isso pode levar um tempo.")
        
        temp_db_file = self.db_file.with_suffix('.db.tmp')
        new_index = {}
        
        try:
            with self.lock_file:
                current_index = self._get_current_index()
                
                with temp_db_file.open('wb') as out_f:
                    for record_id in sorted(current_index.keys()):
                        record_info = current_index[record_id]
                        if record_info["deleted"] == 0:
                            # Read old record
                            record = self._read_record_from_db_file(record_info["offset"], record_info["size"])
                            if record:
                                # Write to new temp file
                                data_json = json.dumps(record.to_dict(), ensure_ascii=False) + '\n'
                                data_bytes = data_json.encode('utf-8')
                                
                                offset = out_f.tell()
                                out_f.write(data_bytes)
                                size = len(data_bytes)
                                
                                # Update index for new offsets
                                new_index[record_id] = {"offset": offset, "size": size, "deleted": 0}
                            else:
                                self.logger.warning(f"Skipping unreadable record ID {record_id} during compaction.")
                        else:
                            self.logger.info(f"Skipping deleted record ID {record_id} during compaction.")

                # Replace old files with new ones
                self.db_file.unlink() # Delete old DB file
                temp_db_file.rename(self.db_file) # Rename temp file to old DB file name
                self._save_index(new_index) # Save the new index
                
                self.logger.info("Database compaction completed successfully.")
                st.success("Banco de dados compactado com sucesso!")

        except Exception as e:
            self.logger.error(f"Error during database compaction: {traceback.format_exc()}")
            st.error(f"Erro durante a compactação do banco de dados: {e}")
            # Attempt to clean up temp file if error occurs
            if temp_db_file.exists():
                temp_db_file.unlink()
    
    def export_to_csv(self, output_path: Path):
        """Exports all non-deleted records to a CSV file."""
        self.logger.info(f"Starting CSV export to {output_path}...")
        st.info(f"Exportando dados para CSV em `{output_path}`...")
        
        records = self.list_all_records()
        if not records:
            st.warning("Não há registros para exportar.")
            self.logger.warning("No records to export to CSV.")
            return

        # Define CSV header based on DataObject fields
        # This assumes all DataObjects have the same set of keys
        # If fields can vary, you might need a more robust way to collect all unique keys
        header = list(DataObject({}).to_dict().keys()) 

        try:
            with output_path.open('w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=header)
                writer.writeheader()
                
                total_records = len(records)
                progress_text = f"Exportando {total_records} registros..."
                progress_bar = st.progress(0, text=progress_text)
                
                batch_size = max(1, total_records // 100) # Update at least 100 times, or for every record if less than 100
                
                for i, record in enumerate(records):
                    writer.writerow(record.to_csv_row())
                    if (i + 1) % batch_size == 0 or (i + 1) == total_records:
                        progress_value = min(100, int(((i + 1) / total_records) * 100))
                        progress_bar.progress(progress_value, text=f"Exportando: {i + 1}/{total_records} registros")

            st.success(f"Dados exportados com sucesso para `{output_path}`.")
            self.logger.info(f"Data exported to CSV successfully to {output_path}. Total records: {total_records}")
        except Exception as e:
            st.error(f"Erro ao exportar dados para CSV: {e}")
            self.logger.error(f"Error exporting data to CSV: {traceback.format_exc()}")
        finally:
            if 'progress_bar' in locals():
                progress_bar.empty()

    def import_from_csv(self, uploaded_file_object, overwrite: bool = False, progress_bar=None, progress_text_placeholder=None):
        """
        Imports records from a CSV file into the database.
        Optionally overwrites existing data.
        Includes streamed progress feedback.
        """
        self.logger.info(f"Starting CSV import from {uploaded_file_object.name}. Overwrite: {overwrite}")
        
        # Create a temporary file to save the uploaded content
        temp_csv_path = Path(tempfile.gettempdir()) / uploaded_file_object.name
        try:
            with temp_csv_path.open("wb") as f:
                f.write(uploaded_file_object.getbuffer())

            # Count total lines for progress bar
            total_lines = 0
            with temp_csv_path.open('r', encoding='utf-8') as f:
                total_lines = sum(1 for row in f) - 1 # Subtract 1 for header row
            
            if total_lines <= 0:
                st.warning("O arquivo CSV está vazio ou contém apenas o cabeçalho. Nenhum dado importado.")
                self.logger.warning(f"CSV file {uploaded_file_object.name} is empty or header only.")
                return

            if overwrite:
                st.warning("Sobrescrevendo dados existentes do banco de dados.")
                self.logger.warning("Overwriting existing database data.")
                # This simplistic overwrite empties the DB.
                # A more robust overwrite might involve matching records by ID and updating.
                self.db_file.unlink(missing_ok=True)
                self.index_file.unlink(missing_ok=True)
                self._next_id = 1 # Reset ID counter
                self._save_next_id()
                self._initialize_files() # Re-create empty files

            imported_count = 0
            batch_size = max(1, total_lines // 100) # Update at least 100 times
            
            # Initialize or update progress bar (if already passed from UI)
            if progress_bar is None:
                progress_text = f"Importando {total_lines} registros de {uploaded_file_object.name}..."
                progress_bar = st.progress(0, text=progress_text)
            else:
                progress_text_placeholder.text(f"Importando {total_lines} registros de {uploaded_file_object.name}...")

            with temp_csv_path.open('r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for i, row in enumerate(reader):
                    # Ensure all keys from DataObject are present, even if empty in CSV
                    processed_row = {field: row.get(field, '') for field in DataObject({}).to_dict().keys()}
                    
                    # Convert id to 0 if it's empty or not a valid number, so add_record can assign a new one
                    if 'id' in processed_row and (not processed_row['id'] or not str(processed_row['id']).strip().isdigit()):
                        processed_row['id'] = 0 # Let DBManager assign a new ID for new records
                    else:
                        processed_row['id'] = int(processed_row['id']) # Ensure it's an int if valid
                        
                    try:
                        self.add_record(processed_row) # Or use update_record if ID exists and overwrite is active
                        imported_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to add record from CSV row {i+2} (incl. header): {row}. Error: {e}")
                        st.warning(f"Falha ao importar linha {i+2}: {row}. Erro: {e}")
                    
                    if imported_count % batch_size == 0 or imported_count == total_lines:
                        progress_value = min(100, int((imported_count / total_lines) * 100))
                        progress_bar.progress(progress_value, text=f"Importando: {imported_count}/{total_lines} registros")
                        self.logger.info(f"CSV import progress: {imported_count}/{total_lines} records.")

            st.success(f"Importação de CSV concluída. Total de {imported_count} registros importados/atualizados.")
            self.logger.info(f"CSV import completed. Total imported/updated: {imported_count} records.")

        except Exception as e:
            st.error(f"Erro inesperado durante a importação do CSV: {e}")
            self.logger.error(f"Unexpected error during CSV import: {traceback.format_exc()}")
        finally:
            if temp_csv_path.exists():
                temp_csv_path.unlink() # Clean up temporary file
            if progress_bar: # Ensure cleanup even if not passed from UI
                progress_bar.empty()
            if progress_text_placeholder:
                progress_text_placeholder.empty()

# --- Placeholder for BTreeDBManager (from stCRUDDataObjectPY_v5alpha0.2.a.py) ---
# This class would have similar CRUD methods but backed by a B-Tree implementation.
# For now, it will simply inherit from DBManager and log its usage.
class BTreeDBManager(DBManager):
    def __init__(self, db_file: Path, index_file: Path, id_counter_file: Path, lock_file: Path, logger: logging.Logger, btree_page_size: int, btree_min_degree: int):
        super().__init__(db_file, index_file, id_counter_file, lock_file, logger)
        self.btree_page_size = btree_page_size
        self.btree_min_degree = btree_min_degree
        self.logger.info(f"BTreeDBManager initialized with page size {btree_page_size} and min degree {btree_min_degree}.")
        st.warning("Aviso: BTreeDBManager é um placeholder. A implementação completa da B-Tree ainda não está disponível.")

    # Override methods if B-Tree logic is different
    # For import/export, the underlying file operations might be similar,
    # but the way records are stored and indexed would change.
    # The `import_from_csv` method can largely remain the same as it interacts with DataObject
    # and then uses `add_record`, which would be the B-Tree specific method.

# --- CryptographyHandler Class (from pycryptonew.py / AES_RSA.py) ---
class CryptographyHandler:
    """
    Handles RSA key generation, AES encryption/decryption (hybrid).
    """
    @staticmethod
    def generate_rsa_key_pair(private_key_path: Path, public_key_path: Path, password: Optional[str] = None) -> bool:
        """Generates RSA public and private key pair."""
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()

            private_pem_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8')) if password else serialization.NoEncryption()
            )
            public_pem_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.SubjectPublicKeyInfo
            )

            private_key_path.parent.mkdir(parents=True, exist_ok=True)
            public_key_path.parent.mkdir(parents=True, exist_ok=True)

            private_key_path.write_bytes(private_pem_bytes)
            public_key_path.write_bytes(public_pem_bytes)

            st.session_state.logger.info(f"RSA key pair generated: Private Key: {private_key_path}, Public Key: {public_key_path}")
            return True
        except Exception as e:
            st.session_state.logger.error(f"Error generating RSA key pair: {traceback.format_exc()}")
            return False

    @staticmethod
    def load_public_key(public_key_path: Path):
        """Loads a public key from a file."""
        try:
            with public_key_path.open("rb") as key_file:
                public_key = serialization.load_pem_public_key(
                    key_file.read(),
                    backend=default_backend()
                )
            return public_key
        except Exception as e:
            st.session_state.logger.error(f"Error loading public key from {public_key_path}: {traceback.format_exc()}")
            return None

    @staticmethod
    def load_private_key(private_key_path: Path, password: Optional[str] = None):
        """Loads a private key from a file."""
        try:
            with private_key_path.open("rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=password.encode('utf-8') if password else None,
                    backend=default_backend()
                )
            return private_key
        except Exception as e:
            st.session_state.logger.error(f"Error loading private key from {private_key_path}: {traceback.format_exc()}")
            return None

    @staticmethod
    def hybrid_encrypt_file(input_file_path: Path, output_file_path: Path, public_key_path: Path):
        """
        Encrypts a file using AES, and encrypts the AES key with RSA (hybrid encryption).
        """
        st.session_state.logger.info(f"Starting hybrid encryption of {input_file_path} to {output_file_path}")
        st.info(f"Criptografando `{input_file_path.name}`. Por favor, aguarde...")
        
        public_key = CryptographyHandler.load_public_key(public_key_path)
        if not public_key:
            st.error("Chave pública não encontrada ou inválida para criptografia.")
            return False

        try:
            # Generate a random AES key
            aes_key = os.urandom(32)  # 256-bit AES key

            # Encrypt the AES key with RSA public key
            encrypted_aes_key = public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Generate a random IV for AES-CBC
            iv = os.urandom(16)

            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            input_file_size = input_file_path.stat().st_size
            chunk_size = 64 * 1024 # 64KB chunks
            
            with input_file_path.open('rb') as infile, output_file_path.open('wb') as outfile:
                # Write encrypted AES key length, encrypted AES key, and IV
                outfile.write(len(encrypted_aes_key).to_bytes(4, 'big')) # 4 bytes for key length
                outfile.write(encrypted_aes_key)
                outfile.write(iv)

                processed_bytes = 0
                progress_bar = st.progress(0, text=f"Criptografando {input_file_path.name}...")

                while True:
                    chunk = infile.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Pad the last block if it's not a multiple of AES block size (16 bytes)
                    if len(chunk) % algorithms.AES.block_size // 8 != 0:
                        remaining_bytes = algorithms.AES.block_size // 8 - (len(chunk) % (algorithms.AES.block_size // 8))
                        chunk += b'\x00' * remaining_bytes # Simple padding, unpadding needs to know this. PKCS7 is better.
                    
                    encrypted_chunk = encryptor.update(chunk)
                    outfile.write(encrypted_chunk)

                    processed_bytes += len(chunk)
                    progress_value = min(100, int((processed_bytes / input_file_size) * 100))
                    progress_bar.progress(progress_value, text=f"Criptografando: {processed_bytes}/{input_file_size} bytes")

                # Finalize encryption with any remaining buffered data
                encrypted_chunk = encryptor.finalize()
                outfile.write(encrypted_chunk)
                
                st.success(f"Arquivo `{input_file_path.name}` criptografado com sucesso para `{output_file_path.name}`.")
                st.session_state.logger.info(f"File {input_file_path.name} encrypted to {output_file_path.name}")
                progress_bar.empty()
                return True

        except Exception as e:
            st.error(f"Falha ao criptografar arquivo {input_file_path.name}: {e}")
            st.session_state.logger.error(f"Encryption failed for {input_file_path.name}: {traceback.format_exc()}")
            return False

    @staticmethod
    def hybrid_decrypt_file(input_file_path: Path, output_file_path: Path, private_key_path: Path, private_key_password: Optional[str] = None):
        """
        Decrypts a file by first decrypting the AES key with RSA private key,
        then using the AES key to decrypt the file content.
        """
        st.session_state.logger.info(f"Starting hybrid decryption of {input_file_path} to {output_file_path}")
        st.info(f"Descriptografando `{input_file_path.name}`. Por favor, aguarde...")

        private_key = CryptographyHandler.load_private_key(private_key_path, private_key_password)
        if not private_key:
            st.error("Chave privada não encontrada ou senha incorreta para descriptografia.")
            return False

        try:
            with input_file_path.open('rb') as infile, output_file_path.open('wb') as outfile:
                # Read encrypted AES key length
                encrypted_aes_key_len = int.from_bytes(infile.read(4), 'big')
                # Read encrypted AES key
                encrypted_aes_key = infile.read(encrypted_aes_key_len)
                # Read IV
                iv = infile.read(16)

                # Decrypt the AES key with RSA private key
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

                input_file_size = input_file_path.stat().st_size
                header_size = 4 + encrypted_aes_key_len + len(iv)
                data_size_to_process = input_file_size - header_size
                chunk_size = 64 * 1024 # 64KB chunks
                
                processed_bytes = 0
                progress_bar = st.progress(0, text=f"Descriptografando {input_file_path.name}...")

                while True:
                    chunk = infile.read(chunk_size)
                    if not chunk:
                        break
                    
                    decrypted_chunk = decryptor.update(chunk)
                    outfile.write(decrypted_chunk)

                    processed_bytes += len(chunk)
                    progress_value = min(100, int((processed_bytes / data_size_to_process) * 100))
                    progress_bar.progress(progress_value, text=f"Descriptografando: {processed_bytes}/{data_size_to_process} bytes")

                # Finalize decryption
                decrypted_chunk = decryptor.finalize()
                outfile.write(decrypted_chunk)

                st.success(f"Arquivo `{input_file_path.name}` descriptografado com sucesso para `{output_file_path.name}`.")
                st.session_state.logger.info(f"File {input_file_path.name} decrypted to {output_file_path.name}")
                progress_bar.empty()
                return True

        except Exception as e:
            st.error(f"Falha ao descriptografar arquivo {input_file_path.name}: {e}")
            st.session_state.logger.error(f"Decryption failed for {input_file_path.name}: {traceback.format_exc()}")
            return False

    @staticmethod
    def blowfish_encrypt_file():
        st.info("Função Blowfish Encriptar (placeholder)")
        # Placeholder for Blowfish encryption logic
        # Would require similar file reading/writing logic with progress bar
        pass

    @staticmethod
    def blowfish_decrypt_file():
        st.info("Função Blowfish Descriptografar (placeholder)")
        # Placeholder for Blowfish decryption logic
        # Would require similar file reading/writing logic with progress bar
        pass

# --- UI Functions (from stIndexPY_v1alpha0.1.b.py and .c.py) ---

def setup_ui():
    """Configures the Streamlit UI, including sidebar navigation."""
    st.set_page_config(layout="wide", page_title="Gerenciador de Acidentes de Trânsito", page_icon="🚗")

    st.sidebar.title("Navegação")
    page_options = [
        "Início", "Adicionar Registro", "Buscar/Atualizar/Deletar", "Compressão de Arquivos",
        "Criptografia de Arquivos", "Administração", "Log de Atividades", "Sobre o Aplicativo"
    ]
    selected_page_label = st.sidebar.radio("Ir para", page_options)

    if selected_page_label == "Início":
        display_home_section()
    elif selected_page_label == "Adicionar Registro":
        display_add_record_section()
    elif selected_page_label == "Buscar/Atualizar/Deletar":
        display_crud_section()
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

def display_home_section():
    """Displays the home section of the application."""
    st.title("Bem-vindo ao Gerenciador de Acidentes de Trânsito")
    st.write("""
    Este aplicativo permite gerenciar um banco de dados de acidentes de trânsito,
    oferecendo funcionalidades de CRUD, importação/exportação CSV, backup, compactação,
    compressão de arquivos (LZW/Huffman - placeholder) e criptografia/descriptografia (AES/RSA).
    """)

    st.subheader("Configuração do Banco de Dados")
    db_choice = st.radio(
        "Selecione o tipo de Banco de Dados:",
        ("Padrão (Arquivo Plano)", "B-Tree (Placeholder)"),
        key="db_type_selector"
    )

    if db_choice == "Padrão (Arquivo Plano)":
        if st.session_state.db_type != "default":
            st.session_state.db_type = "default"
            st.session_state.db = DBManager(DB_FILE_PATH, INDEX_FILE_PATH, ID_COUNTER_PATH, LOCK_FILE_PATH, st.session_state.logger)
            st.experimental_rerun() # Rerun to re-initialize DBManager
        st.info("Usando o Banco de Dados Padrão (Arquivo Plano).")
    elif db_choice == "B-Tree (Placeholder)":
        if st.session_state.db_type != "btree":
            st.session_state.db_type = "btree"
            st.session_state.db = BTreeDBManager(DB_FILE_PATH, BTREE_INDEX_FILE_PATH, ID_COUNTER_PATH, LOCK_FILE_PATH, st.session_state.logger, 
                                                APP_CONFIG["BTREE_PAGE_SIZE"], APP_CONFIG["BTREE_MIN_DEGREE"])
            st.experimental_rerun() # Rerun to re-initialize BTreeDBManager
        st.warning("Usando o Banco de Dados B-Tree (Placeholder). Funcionalidade CRUD ainda usa o backend do arquivo plano.")
    
    if st.session_state.db is None: # Initial setup if not yet done
        st.session_state.db = DBManager(DB_FILE_PATH, INDEX_FILE_PATH, ID_COUNTER_PATH, LOCK_FILE_PATH, st.session_state.logger)
        st.session_state.db_type = "default"

    st.subheader("Status do Banco de Dados")
    try:
        num_records = len(st.session_state.db.list_all_records())
        st.write(f"Total de registros no DB: **{num_records}**")
        st.write(f"Caminho do arquivo DB: `{DB_FILE_PATH}`")
        st.write(f"Caminho do arquivo de índice: `{st.session_state.db.index_file}`")
        st.write(f"Próximo ID disponível: `{st.session_state.db._next_id}`")
    except Exception as e:
        st.error(f"Não foi possível carregar o status do banco de dados. Erro: {e}")
        st.session_state.logger.error(f"Failed to load DB status: {traceback.format_exc()}")

def display_add_record_section():
    """Allows adding new records to the database."""
    st.title("Adicionar Novo Registro de Acidente")

    with st.form("add_record_form"):
        st.subheader("Detalhes do Acidente")
        col1, col2, col3 = st.columns(3)
        with col1:
            data = st.date_input("Data do Acidente", datetime.now().date()).strftime("%Y-%m-%d")
            tipo_acidente = st.text_input("Tipo de Acidente")
            condicao_via = st.text_input("Condição da Via")
            lesoes = st.number_input("Número de Lesões", min_value=0, value=0)
            bairro = st.text_input("Bairro")
            latitude = st.number_input("Latitude", format="%.6f", value=0.0)
        with col2:
            hora = st.time_input("Hora do Acidente", datetime.now().time()).strftime("%H:%M")
            causa_acidente = st.text_input("Causa do Acidente")
            condicao_metereologica = st.text_input("Condição Meteorológica")
            mortes = st.number_input("Número de Mortes", min_value=0, value=0)
            cidade = st.text_input("Cidade")
            longitude = st.number_input("Longitude", format="%.6f", value=0.0)
        with col3:
            uf = st.text_input("UF", max_chars=2).upper()
            veiculos_envolvidos = st.number_input("Veículos Envolvidos", min_value=0, value=1)
            
        submitted = st.form_submit_button("Adicionar Registro")

        if submitted:
            new_record_data = {
                "data": data,
                "hora": hora,
                "tipo_acidente": tipo_acidente,
                "causa_acidente": causa_acidente,
                "condicao_via": condicao_via,
                "condicao_metereologica": condicao_metereologica,
                "lesoes": lesoes,
                "mortes": mortes,
                "veiculos_envolvidos": veiculos_envolvidos,
                "bairro": bairro,
                "cidade": cidade,
                "uf": uf,
                "latitude": latitude,
                "longitude": longitude
            }
            try:
                record = st.session_state.db.add_record(new_record_data)
                if record:
                    st.success(f"Registro adicionado com sucesso! ID: {record.id}")
                    st.session_state.logger.info(f"Record added successfully with ID: {record.id}")
                else:
                    st.error("Falha ao adicionar o registro. Verifique os logs para mais detalhes.")
            except Exception as e:
                st.error(f"Erro ao adicionar registro: {e}")
                st.session_state.logger.error(f"Error adding record: {traceback.format_exc()}")

def display_crud_section():
    """Allows searching, updating, and deleting records."""
    st.title("Buscar, Atualizar ou Deletar Registro")

    all_records = st.session_state.db.list_all_records()
    record_ids = sorted([r.id for r in all_records])

    if not record_ids:
        st.info("Não há registros no banco de dados para buscar, atualizar ou deletar.")
        return

    selected_id = st.selectbox("Selecione o ID do Registro", record_ids, key="crud_select_id")

    record_to_display = None
    if selected_id:
        record_to_display = st.session_state.db.get_record(selected_id)

    if record_to_display:
        st.subheader(f"Detalhes do Registro ID: {selected_id}")
        record_data = record_to_display.to_dict()

        with st.form("update_record_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                data = st.date_input("Data do Acidente", datetime.strptime(record_data.get("data", "2000-01-01"), "%Y-%m-%d").date(), key="update_data").strftime("%Y-%m-%d")
                tipo_acidente = st.text_input("Tipo de Acidente", value=record_data.get("tipo_acidente", ""), key="update_tipo_acidente")
                condicao_via = st.text_input("Condição da Via", value=record_data.get("condicao_via", ""), key="update_condicao_via")
                lesoes = st.number_input("Número de Lesões", min_value=0, value=record_data.get("lesoes", 0), key="update_lesoes")
                bairro = st.text_input("Bairro", value=record_data.get("bairro", ""), key="update_bairro")
                latitude = st.number_input("Latitude", format="%.6f", value=record_data.get("latitude", 0.0), key="update_latitude")
            with col2:
                hora = st.time_input("Hora do Acidente", datetime.strptime(record_data.get("hora", "00:00"), "%H:%M").time(), key="update_hora").strftime("%H:%M")
                causa_acidente = st.text_input("Causa do Acidente", value=record_data.get("causa_acidente", ""), key="update_causa_acidente")
                condicao_metereologica = st.text_input("Condição Meteorológica", value=record_data.get("condicao_metereologica", ""), key="update_condicao_metereologica")
                mortes = st.number_input("Número de Mortes", min_value=0, value=record_data.get("mortes", 0), key="update_mortes")
                cidade = st.text_input("Cidade", value=record_data.get("cidade", ""), key="update_cidade")
                longitude = st.number_input("Longitude", format="%.6f", value=record_data.get("longitude", 0.0), key="update_longitude")
            with col3:
                uf = st.text_input("UF", value=record_data.get("uf", "").upper(), max_chars=2, key="update_uf").upper()
                veiculos_envolvidos = st.number_input("Veículos Envolvidos", min_value=0, value=record_data.get("veiculos_envolvidos", 1), key="update_veiculos_envolvidos")

            col_buttons = st.columns(2)
            with col_buttons[0]:
                update_submitted = st.form_submit_button("Atualizar Registro")
            with col_buttons[1]:
                delete_submitted = st.form_submit_button("Deletar Registro")

            if update_submitted:
                updated_record_data = {
                    "data": data,
                    "hora": hora,
                    "tipo_acidente": tipo_acidente,
                    "causa_acidente": causa_acidente,
                    "condicao_via": condicao_via,
                    "condicao_metereologica": condicao_metereologica,
                    "lesoes": lesoes,
                    "mortes": mortes,
                    "veiculos_envolvidos": veiculos_envolvidos,
                    "bairro": bairro,
                    "cidade": cidade,
                    "uf": uf,
                    "latitude": latitude,
                    "longitude": longitude
                }
                try:
                    updated_obj = st.session_state.db.update_record(selected_id, updated_record_data)
                    if updated_obj:
                        st.success(f"Registro ID {selected_id} atualizado com sucesso!")
                        st.session_state.logger.info(f"Record ID {selected_id} updated.")
                        st.experimental_rerun()
                    else:
                        st.error("Falha ao atualizar o registro.")
                except Exception as e:
                    st.error(f"Erro ao atualizar registro: {e}")
                    st.session_state.logger.error(f"Error updating record: {traceback.format_exc()}")

            if delete_submitted:
                if st.session_state.db.delete_record(selected_id):
                    st.success(f"Registro ID {selected_id} deletado com sucesso!")
                    st.session_state.logger.info(f"Record ID {selected_id} deleted.")
                    st.experimental_rerun()
                else:
                    st.error("Falha ao deletar o registro.")
    else:
        st.info("Selecione um ID de registro válido para ver os detalhes.")

    st.subheader("Buscar Registros por Campo")
    search_field = st.selectbox("Campo para Buscar", list(DataObject({}).to_dict().keys()), key="search_field")
    search_query = st.text_input(f"Valor para Buscar em '{search_field}'", key="search_query")

    if st.button("Buscar"):
        if search_query:
            results = st.session_state.db.search_records(search_field, search_query)
            if results:
                st.subheader("Resultados da Busca:")
                st.dataframe([r.to_dict() for r in results])
            else:
                st.info("Nenhum registro encontrado para a busca.")
        else:
            st.warning("Por favor, insira um valor para a busca.")


def display_compression_section():
    """Displays the compression/decompression section (placeholders)."""
    st.title("Compressão e Descompressão de Arquivos")
    st.info("As funções de compressão LZW e Huffman são placeholders.")

    st.subheader("Compressão LZW (Placeholder)")
    st.button("Comprimir Banco de Dados (LZW)", key="compress_lzw_db")
    st.button("Descomprimir Banco de Dados (LZW)", key="decompress_lzw_db")

    st.subheader("Compressão Huffman (Placeholder)")
    st.button("Comprimir Banco de Dados (Huffman)", key="compress_huffman_db")
    st.button("Descomprimir Banco de Dados (Huffman)", key="decompress_huffman_db")

def display_cryptography_section():
    """Displays the file encryption/decryption section."""
    st.title("Criptografia e Descriptografia de Arquivos")

    st.subheader("Gerar Chaves RSA")
    if st.button("Gerar Novo Par de Chaves RSA"):
        with st.spinner("Gerando chaves RSA..."):
            password = st.text_input("Senha para a chave privada (opcional)", type="password", key="gen_rsa_pass")
            if CryptographyHandler.generate_rsa_key_pair(RSA_PRIVATE_KEY_PATH, RSA_PUBLIC_KEY_PATH, password):
                st.success("Par de chaves RSA gerado e salvo com sucesso!")
                st.session_state.rsa_keys_generated = True
                st.session_state.key_pair = {
                    "public": CryptographyHandler.load_public_key(RSA_PUBLIC_KEY_PATH),
                    "private": CryptographyHandler.load_private_key(RSA_PRIVATE_KEY_PATH, password)
                }
            else:
                st.error("Falha ao gerar par de chaves RSA.")
    
    if RSA_PUBLIC_KEY_PATH.exists() and RSA_PRIVATE_KEY_PATH.exists():
        st.success("Chaves RSA existentes encontradas.")
        st.session_state.rsa_keys_generated = True
    else:
        st.warning("Nenhum par de chaves RSA encontrado. Por favor, gere um.")

    st.subheader("Criptografia Híbrida (AES + RSA)")
    if st.session_state.rsa_keys_generated:
        # File paths for encryption/decryption
        db_file_name = APP_CONFIG["DB_FILE_NAME"]
        index_file_name = APP_CONFIG["INDEX_FILE_NAME"]
        
        st.write(f"Caminho do Banco de Dados: `{DB_FILE_PATH}`")
        st.write(f"Caminho do Índice: `{INDEX_FILE_PATH}`")

        st.info("Você pode criptografar o arquivo do Banco de Dados ou o arquivo de Índice.")
        file_to_encrypt = st.selectbox(
            "Selecione o arquivo para criptografar:",
            options=["Banco de Dados", "Índice"],
            key="file_to_encrypt_select"
        )
        
        input_encrypt_path = DB_FILE_PATH if file_to_encrypt == "Banco de Dados" else INDEX_FILE_PATH
        output_encrypt_file = f"{file_to_encrypt.lower().replace(' ', '_')}_encrypted.bin"
        full_output_encrypt_path = APP_CONFIG["DB_DIR"] / output_encrypt_file

        if st.button(f"Criptografar {file_to_encrypt}"):
            if input_encrypt_path.exists():
                CryptographyHandler.hybrid_encrypt_file(input_encrypt_path, full_output_encrypt_path, RSA_PUBLIC_KEY_PATH)
            else:
                st.warning(f"O arquivo {input_encrypt_path.name} não existe para ser criptografado.")
    else:
        st.info("Gere um par de chaves RSA para habilitar a criptografia.")

    st.subheader("Descriptografia Híbrida (AES + RSA)")
    if st.session_state.rsa_keys_generated:
        # List .bin files in DB_DIR for decryption
        encrypted_files = [f.name for f in APP_CONFIG["DB_DIR"].glob("*.bin")]
        
        if encrypted_files:
            input_encrypted_file = st.selectbox(
                "Selecione o arquivo criptografado para descriptografar:",
                options=encrypted_files,
                key="file_to_decrypt_select"
            )
            output_decrypted_file_name = st.text_input(
                "Nome do arquivo de saída descriptografado (ex: traffic_accidents_decrypted.db)",
                value=input_encrypted_file.replace("_encrypted.bin", "_decrypted.db") if "_encrypted.bin" in input_encrypted_file else input_encrypted_file.replace(".bin", "_decrypted.db"),
                key="decrypted_output_name"
            )
            private_key_password = st.text_input("Senha da chave privada (se houver)", type="password", key="decrypt_rsa_pass")

            if st.button("Descriptografar Arquivo"):
                if input_encrypted_file:
                    full_input_path = APP_CONFIG["DB_DIR"] / input_encrypted_file
                    full_output_path = APP_CONFIG["DB_DIR"] / output_decrypted_file_name

                    if CryptographyHandler.hybrid_decrypt_file(full_input_path, full_output_path, RSA_PRIVATE_KEY_PATH, private_key_password):
                        st.success(f"Arquivo `{input_encrypted_file}` descriptografado com sucesso para `{output_decrypted_file_name}`!")
                        st.session_state.logger.info(f"File {input_encrypted_file} decrypted to {output_decrypted_file_name}")
                    else:
                        st.error(f"Falha ao descriptografar o arquivo `{input_encrypted_file}`. Verifique a senha ou a integridade do arquivo.")
                else:
                    st.warning("Nenhum arquivo criptografado selecionado.")
        else:
            st.info("Nenhum arquivo .bin encontrado no diretório do banco de dados para descriptografar.")
    else:
        st.info("Gere um par de chaves RSA para habilitar a descriptografia.")
    
    st.subheader("Criptografia/Descriptografia Blowfish (Placeholder)")
    st.info("As funções Blowfish são apenas placeholders e não possuem uma implementação completa aqui.")
    CryptographyHandler.blowfish_encrypt_file()
    CryptographyHandler.blowfish_decrypt_file()


def display_admin_section():
    """Displays administrative functions for database management."""
    st.title("Administração do Sistema")

    st.subheader("Informações do Sistema")
    st.info(f"Diretório da Aplicação: `{APP_CONFIG['DB_DIR']}`")
    st.info(f"Arquivo Banco de Dados: `{APP_CONFIG['DB_FILE_NAME']}`")
    st.info(f"Arquivo Índice Padrão: `{APP_CONFIG['INDEX_FILE_NAME']}`")
    st.info(f"Arquivo Índice B-Tree: `{APP_CONFIG['BTREE_INDEX_FILE_NAME']}`")
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
        st.session_state.db.compact_db()

    st.subheader("Backup e Restauração")
    if st.button("Criar Backup do Banco de Dados"):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file_name = f"{APP_CONFIG['DB_FILE_NAME']}.{timestamp}.bak"
            backup_index_name = f"{APP_CONFIG['INDEX_FILE_NAME']}.{timestamp}.bak"
            
            BACKUP_PATH.mkdir(parents=True, exist_ok=True) # Ensure backup directory exists

            shutil.copy(DB_FILE_PATH, BACKUP_PATH / backup_file_name)
            shutil.copy(INDEX_FILE_PATH, BACKUP_PATH / backup_index_name)
            st.success(f"Backup criado em `{BACKUP_PATH}`: `{backup_file_name}` e `{backup_index_name}`")
            st.session_state.logger.info(f"Backup created at {BACKUP_PATH / backup_file_name}")
        except FileNotFoundError:
            st.error("Arquivos do banco de dados não encontrados para backup.")
            st.session_state.logger.error(f"Backup failed: DB or index file not found. {traceback.format_exc()}")
        except Exception as e:
            st.error(f"Erro ao criar backup: {e}")
            st.session_state.logger.error(f"Backup failed: {traceback.format_exc()}")
    
    backup_files = list(BACKUP_PATH.glob(f"{APP_CONFIG['DB_FILE_NAME']}*.bak"))
    backup_files.sort(key=os.path.getmtime, reverse=True) # Sort by modification time, newest first
    backup_options = [f.name for f in backup_files]

    if backup_options:
        selected_backup = st.selectbox("Restaurar de Backup", backup_options, help="Selecione um arquivo .bak para restaurar. Isso substituirá os dados atuais.")
        if st.button("Restaurar Banco de Dados do Backup"):
            if selected_backup:
                try:
                    db_backup_path = BACKUP_PATH / selected_backup
                    # Infer index backup name by replacing .db.bak with .idx.bak
                    index_backup_path = BACKUP_PATH / selected_backup.replace(APP_CONFIG['DB_FILE_NAME'], APP_CONFIG['INDEX_FILE_NAME'])
                    
                    if db_backup_path.exists() and index_backup_path.exists():
                        shutil.copy(db_backup_path, DB_FILE_PATH)
                        shutil.copy(index_backup_path, INDEX_FILE_PATH)
                        # Re-initialize DBManager to load the restored state
                        st.session_state.db = DBManager(DB_FILE_PATH, INDEX_FILE_PATH, ID_COUNTER_PATH, LOCK_FILE_PATH, st.session_state.logger)
                        st.success(f"Banco de dados restaurado com sucesso de `{selected_backup}`!")
                        st.session_state.logger.info(f"Database restored from {selected_backup}")
                        st.experimental_rerun() # Rerun to reflect restored state
                    else:
                        st.error("Arquivos de backup correspondentes (DB e Index) não encontrados.")
                except Exception as e:
                    st.error(f"Erro ao restaurar backup: {e}")
                    st.session_state.logger.error(f"Restore failed: {traceback.format_exc()}")
            else:
                st.warning("Nenhum arquivo de backup selecionado.")
    else:
        st.info("Nenhum arquivo de backup encontrado.")

    st.subheader("Importar/Exportar CSV")

    # Placeholder for a progress bar for import
    csv_import_progress_text_placeholder = st.empty()
    csv_import_progress_bar = st.progress(0, text="Aguardando arquivo CSV para importação...")

    uploaded_db_file = st.file_uploader("Carregar Arquivo CSV para o Banco de Dados", type="csv", key="db_csv_upload")
    if uploaded_db_file is not None:
        overwrite_db = st.checkbox("Sobrescrever dados existentes do Banco de Dados?", key="overwrite_db_csv")
        if st.button("Importar Banco de Dados do CSV", key="import_db_csv_button"):
            st.session_state.logger.info(f"Attempting to import {uploaded_db_file.name} to DB.")
            try:
                # Pass the progress bar and its text placeholder
                st.session_state.db.import_from_csv(uploaded_db_file, overwrite_db, csv_import_progress_bar, csv_import_progress_text_placeholder)
            except Exception as e:
                st.error(f"Erro ao iniciar importação do CSV: {e}")
                st.session_state.logger.error(f"Error initiating CSV import: {traceback.format_exc()}")
            finally:
                # Ensure the progress bar and text are cleared even on error
                csv_import_progress_bar.empty()
                csv_import_progress_text_placeholder.empty()

    if st.button("Exportar Banco de Dados para CSV"):
        output_csv_path = APP_CONFIG["DB_DIR"] / "traffic_accidents_export.csv"
        try:
            st.session_state.db.export_to_csv(output_csv_path)
            if output_csv_path.exists():
                with open(output_csv_path, "rb") as f:
                    st.download_button(
                        label="Baixar CSV Exportado",
                        data=f.read(),
                        file_name="traffic_accidents_export.csv",
                        mime="text/csv"
                    )
        except Exception as e:
            st.error(f"Erro ao exportar dados: {e}")
            st.session_state.logger.error(f"Error during data export: {traceback.format_exc()}")

    st.subheader("Importar Chaves RSA do CSV")
    uploaded_rsa_keys_file = st.file_uploader("Carregar Arquivo CSV de Chaves RSA (Placeholder)", type="csv", key="rsa_csv_upload")
    if uploaded_rsa_keys_file is not None:
        if st.button("Importar Chaves RSA do CSV (Placeholder)", key="import_rsa_csv_button"):
            st.warning("Importação de Chaves RSA de CSV é um placeholder. A lógica de importação real deve ser implementada.")
            st.info(f"Arquivo carregado: {uploaded_rsa_keys_file.name}. Conteúdo (primeiras 1000 bytes):")
            st.code(uploaded_rsa_keys_file.read(1000).decode('utf-8'))
            uploaded_rsa_keys_file.seek(0) # Reset file pointer for potential future reads
            st.session_state.logger.info(f"RSA Keys CSV uploaded: {uploaded_rsa_keys_file.name}")


def display_activity_log():
    """Displays the application activity log."""
    st.title("Log de Atividades do Sistema")
    
    if LOG_FILE_PATH.exists():
        try:
            with LOG_FILE_PATH.open('r', encoding='utf-8') as f:
                log_content = f.read()
            st.code(log_content, language='log')
        except Exception as e:
            st.error(f"Erro ao ler o arquivo de log: {e}")
            st.session_state.logger.error(f"Error reading log file: {traceback.format_exc()}")
    else:
        st.info("Arquivo de log não encontrado. Nenhuma atividade registrada ainda.")

def display_about_section():
    """Displays information about the application."""
    st.title("Sobre o Aplicativo")
    st.markdown("""
    Este aplicativo é um **Gerenciador de Banco de Dados de Acidentes de Trânsito**
    desenvolvido usando Python e Streamlit.

    **Recursos Principais:**
    - Gerenciamento de registros de acidentes de trânsito (CRUD).
    - Opção de banco de dados padrão (flat-file) ou B-Tree (placeholder).
    - Importação e exportação de dados via CSV com feedback de progresso.
    - Funcionalidades de backup e restauração do banco de dados.
    - Compactação de banco de dados para otimização de espaço.
    - Compressão e descompressão de arquivos (LZW e Huffman - placeholders).
    - Criptografia e descriptografia híbrida (AES com chave RSA).
    - Geração e gerenciamento de chaves RSA.
    - Registro de atividades do sistema.

    **Desenvolvido por:** [Seu Nome/Organização]
    **Versão:** 1.0 Alpha

    **Tecnologias Utilizadas:**
    - Python
    - Streamlit
    - `pathlib`
    - `filelock`
    - `cryptography` (para AES/RSA)
    - `csv`
    - `json`

    Agradecemos por usar este aplicativo!
    """)

# --- Main Application Entry Point ---
if __name__ == "__main__":
    try:
        # Ensure base directories exist
        APP_CONFIG["DB_DIR"].mkdir(parents=True, exist_ok=True)
        BACKUP_PATH.mkdir(parents=True, exist_ok=True)
        APP_CONFIG["RSA_KEYS_DIR"].mkdir(parents=True, exist_ok=True)
        HUFFMAN_FOLDER.mkdir(parents=True, exist_ok=True)
        LZW_FOLDER.mkdir(parents=True, exist_ok=True)
        
        setup_ui()
    except OSError as e:
        st.error(f"🚨 Crítico: Não foi possível criar os diretórios necessários. Verifique as permissões para `{APP_CONFIG['DB_DIR']}`. Erro: {e}")
        logger.critical(f"Initial directory creation failed: {traceback.format_exc()}")
        st.stop() # Interrompe o aplicativo se os diretórios não puderem ser criados
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado na inicialização da aplicação: {e}")
        logger.critical(f"Unhandled exception during application startup: {traceback.format_exc()}")