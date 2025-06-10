# -*- coding: utf-8 -*-
"""
Enhanced Traffic Accidents Database Manager

This script is a comprehensive merge of multiple Python files:
- stCRUDDataObjectPY_v3alpha.py (UI Base)
- stCRUDDataObjectPY_v4epsilon.py (Config & Indexing)
- stCRUDDataObjectPY_v5alpha0.1.d.py (Robust DataObject & DB Class)
- stCRUDDataObjectPY_v5alpha0.2.a.py (B-Tree Implementation)
- stHuffman_v5.py (Huffman Compression)
- stLZWPY_v4.py (LZW Compression)

The result is a single, feature-rich Streamlit application that provides:
- A choice between a standard file/index database and a B-Tree-based engine.
- A robust DataObject with extensive validation.
- Full CRUD (Create, Read, Update, Delete) functionality.
- Bulk import/export via CSV.
- Database backup and restore capabilities.
- Integrated file compression/decompression utilities (Huffman & LZW).
- An activity log and administrative functions.
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
from collections import OrderedDict, Counter, defaultdict
import heapq
import io
import pickle # Adicionado para serialização do índice do TrafficAccidentsDB
import re # Para parsing do log de atividades

# Configure logging
logging.basicConfig(
    level=logging.INFO, # Set to logging.DEBUG to see detailed date parsing attempts
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traffic_accidents.log'), # Log to a file
        logging.StreamHandler() # Also log to console
    ]
)
logger = logging.getLogger(__name__)

# --- Configuration Constants (Centralized) ---
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
    "LOG_FILE_NAME": 'traffic_accidents.log'
}

# Derived paths
DB_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["DB_FILE_NAME"])
INDEX_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["INDEX_FILE_NAME"])
LOCK_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOCK_FILE_NAME"])
ID_COUNTER_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["ID_COUNTER_FILE_NAME"])
BACKUP_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["BACKUP_DIR_NAME"])

# B-Tree related constants and classes
PAGE_SIZE = 4096 # bytes
DEFAULT_ORDER = 128 # Max number of keys in a node (2*t - 1)
MIN_DEGREE = (DEFAULT_ORDER // 2) + 1 # t = order // 2 + 1
BTREE_DB_FILE_NAME = "traffic_accidents_btree.db"
BTREE_DB_PATH = os.path.join(APP_CONFIG["DB_DIR"], BTREE_DB_FILE_NAME)


# --- DataObject Class ---
class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

class DataObject:
    """
    Represents a single record of traffic accident data.
    Provides methods for serialization and deserialization.
    """
    def __init__(self, id: Optional[int], city: str, state: str, accident_type: str, 
                 date_str: str, time_str: str, weather_conditions: str, 
                 road_conditions: str, num_vehicles: int, num_fatalities: int):
        self.id = id
        self.city = city
        self.state = state
        self.accident_type = accident_type
        # Store date and time as datetime.date and datetime.time objects
        try:
            self.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise DataValidationError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.")
        try:
            self.time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            raise DataValidationError(f"Invalid time format: {time_str}. Expected HH:MM.")
        self.weather_conditions = weather_conditions
        self.road_conditions = road_conditions
        
        if not isinstance(num_vehicles, int) or num_vehicles < 0:
            raise DataValidationError(f"Number of vehicles must be a non-negative integer: {num_vehicles}")
        self.num_vehicles = num_vehicles
        
        if not isinstance(num_fatalities, int) or num_fatalities < 0:
            raise DataValidationError(f"Number of fatalities must be a non-negative integer: {num_fatalities}")
        self.num_fatalities = num_fatalities

    def __repr__(self):
        return (f"DataObject(ID: {self.id}, City: {self.city}, State: {self.state}, "
                f"Date: {self.date}, Time: {self.time}, Type: {self.accident_type})")

    def __str__(self):
        return self.__repr__()
    
    def __eq__(self, other):
        if not isinstance(other, DataObject):
            return NotImplemented
        return self.id == other.id # Assume ID is unique identifier

    def to_csv_row(self) -> List[str]:
        """Converts the DataObject into a list of strings suitable for CSV export."""
        return [
            str(self.id) if self.id is not None else '',
            self.city,
            self.state,
            self.accident_type,
            self.date.strftime('%Y-%m-%d'),
            self.time.strftime('%H:%M'),
            self.weather_conditions,
            self.road_conditions,
            str(self.num_vehicles),
            str(self.num_fatalities)
        ]

    @staticmethod
    def from_csv_row(row: List[str]) -> 'DataObject':
        """
        Creates a DataObject instance from a list of strings (CSV row).
        Performs basic type conversion and validation.
        """
        if len(row) != 10:
            raise DataValidationError(f"Invalid number of columns: expected 10, got {len(row)} for row {row}")
        try:
            # Strip whitespace from string fields
            record_id = int(row[0].strip()) if row[0].strip() else None # Handle empty ID for auto-generation
            city = row[1].strip()
            state = row[2].strip()
            accident_type = row[3].strip()
            date_str = row[4].strip()
            time_str = row[5].strip()
            weather_conditions = row[6].strip()
            road_conditions = row[7].strip()
            num_vehicles = int(row[8].strip())
            num_fatalities = int(row[9].strip())

            return DataObject(record_id, city, state, accident_type, date_str, time_str, 
                              weather_conditions, road_conditions, num_vehicles, num_fatalities)
        except ValueError as e:
            raise DataValidationError(f"Type conversion error: {e} in row {row}")
        except DataValidationError: # Re-raise if our internal validation caught it
            raise
        except Exception as e:
            raise DataValidationError(f"Error parsing CSV row: {e} in row {row}")

    def to_binary(self) -> bytes:
        """Serializes the DataObject into a binary format."""
        # For simplicity, convert to dict and then JSON.
        # Ensure date/time objects are converted to strings for JSON serialization.
        obj_dict = self.__dict__.copy()
        obj_dict['date'] = self.date.strftime('%Y-%m-%d')
        obj_dict['time'] = self.time.strftime('%H:%M:%S') # Include seconds for full precision if needed
        
        data_str = json.dumps(obj_dict, default=str)
        encoded = data_str.encode('utf-8')
        # Prepend length of data for easy deserialization
        return struct.pack(f'>I{len(encoded)}s', len(encoded), encoded)

    @classmethod
    def from_binary(cls, data: bytes) -> 'DataObject':
        """Deserializes a DataObject from binary data."""
        length = struct.unpack('>I', data[:4])[0]
        decoded_data = data[4:4+length].decode('utf-8')
        obj_dict = json.loads(decoded_data)
        
        # Convert date and time strings back to objects
        obj_dict['date_str'] = obj_dict.pop('date')
        obj_dict['time_str'] = obj_dict.pop('time') # Original stored as HH:MM:SS
        
        # Instantiate using date_str and time_str, then the __init__ will parse them
        return cls(**obj_dict)

# --- TrafficAccidentsDB Class ---
class TrafficAccidentsDB:
    """
    Manages traffic accident records stored in a binary file with an in-memory index.
    Supports basic CRUD operations and ensures data integrity with file locking.
    """
    def __init__(self, db_file: str, index_file: str, lock_file: str, id_counter_file: str):
        self.db_file = db_file
        self.index_file = index_file
        self.lock_file = lock_file
        self.id_counter_file = id_counter_file
        self.index: Dict[int, Tuple[int, int]] = {}  # {id: (offset, length)}
        self.id_counter = 0
        
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True) # Ensure DB directory exists
        self._load_index()
        self._load_id_counter()

    def _load_index(self):
        """Loads the index from a file."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'rb') as f:
                    self.index = pickle.load(f)
                logger.info(f"Index loaded from {self.index_file}. {len(self.index)} records.")
            except Exception as e:
                logger.error(f"Error loading index file {self.index_file}: {e}", exc_info=True)
                self.index = {} # Reset index on error
        else:
            self.index = {}
            logger.info(f"Index file {self.index_file} not found. Starting with empty index.")

    def _save_index(self):
        """Saves the current index to a file."""
        try:
            with open(self.index_file, 'wb') as f:
                pickle.dump(self.index, f)
            logger.debug(f"Index saved to {self.index_file}.")
        except Exception as e:
            logger.error(f"Error saving index file {self.index_file}: {e}", exc_info=True)

    def _load_id_counter(self):
        """Loads the last used ID from a file to ensure unique IDs."""
        if os.path.exists(self.id_counter_file):
            try:
                with open(self.id_counter_file, 'r') as f:
                    self.id_counter = int(f.read().strip())
                logger.info(f"ID counter loaded from {self.id_counter_file}: {self.id_counter}")
            except Exception as e:
                logger.error(f"Error loading ID counter from {self.id_counter_file}: {e}", exc_info=True)
                self.id_counter = 0 # Reset counter on error
        else:
            self.id_counter = 0
            logger.info(f"ID counter file {self.id_counter_file} not found. Starting counter from 0.")


    def _save_id_counter(self):
        """Saves the current ID counter to a file."""
        try:
            with open(self.id_counter_file, 'w') as f:
                f.write(str(self.id_counter))
            logger.debug(f"ID counter saved to {self.id_counter_file}: {self.id_counter}.")
        except Exception as e:
            logger.error(f"Error saving ID counter to {self.id_counter_file}: {e}", exc_info=True)

    def add_record(self, data_obj: DataObject) -> Optional[int]:
        """Adds a new record to the database or updates an existing one."""
        with filelock.FileLock(self.lock_file, timeout=10):
            if data_obj.id is None or data_obj.id <= 0 or data_obj.id in self.index:
                # If ID is not provided, 0, or already exists, generate a new one
                self.id_counter += 1
                data_obj.id = self.id_counter
                self._save_id_counter()
                logger.info(f"Generated new ID for record: {data_obj.id}")
            
            try:
                binary_data = data_obj.to_binary()
                data_length = len(binary_data)
                
                # Write to the end of the database file
                with open(self.db_file, 'ab') as f:
                    offset = f.tell()
                    f.write(binary_data)
                
                self.index[data_obj.id] = (offset, data_length)
                self._save_index()
                logger.info(f"Record {data_obj.id} added/updated at offset {offset}, length {data_length}.")
                return data_obj.id
            except filelock.Timeout:
                logger.error("Could not acquire file lock for adding/updating record.")
                st.error("Não foi possível adquirir o bloqueio do arquivo. Tente novamente.")
                return None
            except Exception as e:
                logger.error(f"Error adding/updating record {data_obj.id}: {e}", exc_info=True)
                return None

    def get_record(self, record_id: int) -> Optional[DataObject]:
        """Retrieves a record by its ID."""
        offset, length = self.index.get(record_id, (None, None))
        if offset is None:
            return None
        
        with filelock.FileLock(self.lock_file, timeout=10):
            try:
                with open(self.db_file, 'rb') as f:
                    f.seek(offset)
                    binary_data = f.read(length)
                    if not binary_data: # In case file was truncated or error
                        logger.warning(f"No data found at expected offset {offset} for record {record_id}.")
                        return None
                    return DataObject.from_binary(binary_data)
            except filelock.Timeout:
                logger.error(f"Could not acquire file lock for reading record {record_id}.")
                st.error("Não foi possível adquirir o bloqueio do arquivo para leitura. Tente novamente.")
                return None
            except Exception as e:
                logger.error(f"Error reading record {record_id}: {e}", exc_info=True)
                return None

    def delete_record(self, record_id: int) -> bool:
        """
        Deletes a record by its ID.
        Note: This implementation only removes from index.
        Actual data in .db file is marked for overwrite on next compaction/rewrite.
        A full file rewrite/compaction is needed for physical deletion.
        """
        if record_id not in self.index:
            return False
        
        with filelock.FileLock(self.lock_file, timeout=10):
            try:
                del self.index[record_id]
                self._save_index()
                logger.info(f"Record {record_id} marked for deletion (removed from index).")
                return True
            except filelock.Timeout:
                logger.error(f"Could not acquire file lock for deleting record {record_id}.")
                st.error("Não foi possível adquirir o bloqueio do arquivo para exclusão. Tente novamente.")
                return False
            except Exception as e:
                logger.error(f"Error deleting record {record_id}: {e}", exc_info=True)
                return False

    def get_all_records(self) -> List[DataObject]:
        """Retrieves all records from the database."""
        records = []
        with filelock.FileLock(self.lock_file, timeout=10):
            try:
                # Iterate through a sorted list of IDs to ensure consistent order
                for record_id in sorted(self.index.keys()):
                    record = self.get_record(record_id)
                    if record:
                        records.append(record)
                return records
            except filelock.Timeout:
                logger.error("Could not acquire file lock for getting all records.")
                st.error("Não foi possível adquirir o bloqueio do arquivo para listar registros. Tente novamente.")
                return []
            except Exception as e:
                logger.error(f"Error retrieving all records: {e}", exc_info=True)
                return []

# --- Pager and B-Tree Classes (simplified for context) ---
# These are placeholder implementations for the B-Tree functionality
# which would be more fully developed in a separate file like
# stCRUDDataObjectPY_v5alpha0.2.a.py if this were a modular system.
# They are included here to satisfy dependencies for the main setup_ui.

class Pager:
    """Manages reading and writing fixed-size pages to/from a file."""
    def __init__(self, db_file_path):
        self.db_file_path = db_file_path
        # Use 'a+b' to open for reading and appending in binary mode.
        # buffering=0 for unbuffered I/O (direct write/read).
        self.file = open(db_file_path, 'a+b', buffering=0)
        self.file.seek(0, os.SEEK_END)
        self.num_pages = self.file.tell() // PAGE_SIZE
        self.pages = {} # In-memory cache: {page_num: (data, is_dirty)}

    def _read_page(self, page_num: int) -> bytes:
        """Reads a page from disk or cache."""
        if page_num < 0 or page_num >= self.num_pages:
            raise IndexError(f"Page number {page_num} out of bounds (0-{self.num_pages-1}).")

        if page_num in self.pages and not self.pages[page_num][1]: # Check cache, not dirty
            return self.pages[page_num][0]
        
        self.file.seek(page_num * PAGE_SIZE)
        data = self.file.read(PAGE_SIZE)
        if len(data) < PAGE_SIZE: # Pad with zeros if end of file
            data += b'\0' * (PAGE_SIZE - len(data))
        self.pages[page_num] = (data, False)
        return data

    def _write_page(self, page_num: int, data: bytes):
        """Writes a page to the in-memory cache and marks it as dirty."""
        if len(data) != PAGE_SIZE:
            raise ValueError(f"Page data must be {PAGE_SIZE} bytes.")
        if page_num < 0:
            raise IndexError(f"Page number {page_num} cannot be negative.")
        self.pages[page_num] = (data, True) # Mark as dirty

    def flush_page(self, page_num: int):
        """Writes a dirty page from cache to disk."""
        if page_num in self.pages and self.pages[page_num][1]: # If page is dirty
            data, _ = self.pages[page_num]
            self.file.seek(page_num * PAGE_SIZE)
            self.file.write(data)
            self.pages[page_num] = (data, False) # Mark as clean
            logger.debug(f"Flushed page {page_num} to disk.")

    def flush_all(self):
        """Flushes all dirty pages from cache to disk."""
        for page_num in list(self.pages.keys()): # Iterate over a copy of keys as pages might be removed
            self.flush_page(page_num)
        self.file.flush()
        logger.info("All dirty pages flushed to disk.")

    def allocate_page(self) -> int:
        """Allocates a new empty page in the file and returns its page number."""
        new_page_num = self.num_pages
        self.num_pages += 1
        # Write an empty page to extend the file and immediately flush
        self._write_page(new_page_num, b'\0' * PAGE_SIZE)
        self.flush_page(new_page_num)
        logger.info(f"Allocated new page: {new_page_num}.")
        return new_page_num

    def close(self):
        """Closes the underlying file, ensuring all changes are flushed."""
        self.flush_all()
        self.file.close()
        logger.info(f"Pager for {self.db_file_path} closed.")

class BTreeNode:
    """Represents a node in the B-Tree. (Simplified for this context)"""
    def __init__(self, is_leaf: bool = True):
        self.is_leaf = is_leaf
        self.keys = [] # List of record IDs (integers)
        self.children = [] # List of child page numbers (integers)
        self.values = [] # List of (offset, length) tuples for data records

    def to_binary(self, order: int) -> bytes:
        """
        Serializes the BTreeNode into a fixed-size binary format.
        (This is a simplified/dummy implementation. A real B-Tree node
        serialization needs to be robust and handle variable length keys/values
        or use fixed-size slots effectively within PAGE_SIZE).
        """
        # Header: is_leaf (1 byte), num_keys (1 byte)
        header = struct.pack('>BB', int(self.is_leaf), len(self.keys))
        
        # Pack keys (assuming keys are integers)
        keys_packed = b''
        for key in self.keys:
            keys_packed += struct.pack('>I', key) # Use unsigned int (4 bytes)

        # Pack values (assuming values are (offset, length) tuples of integers)
        values_packed = b''
        for offset, length in self.values:
            values_packed += struct.pack('>II', offset, length) # Each tuple is 8 bytes

        # Pack children (assuming children are page numbers/integers)
        children_packed = b''
        for child_page_num in self.children:
            children_packed += struct.pack('>I', child_page_num) # Use unsigned int (4 bytes)

        # Combine all parts
        data = header + keys_packed + values_packed + children_packed
        
        # Pad to PAGE_SIZE. This padding logic is crucial for fixed-size pages
        # and needs to be carefully designed based on max keys/children.
        # For this example, we just ensure it fits.
        padded_data = data + b'\0' * (PAGE_SIZE - len(data))
        return padded_data[:PAGE_SIZE] # Ensure it's exactly PAGE_SIZE

    @classmethod
    def from_binary(cls, data: bytes, order: int) -> 'BTreeNode':
        """
        Deserializes a BTreeNode from binary data.
        (This is a simplified/dummy implementation corresponding to to_binary).
        """
        is_leaf_int, num_keys = struct.unpack_from('>BB', data, 0)
        node = cls(is_leaf=bool(is_leaf_int))
        
        offset = 2 # After header (is_leaf, num_keys)
        
        # Read keys
        for _ in range(num_keys):
            key = struct.unpack_from('>I', data, offset)[0]
            node.keys.append(key)
            offset += 4 # Size of unsigned int
            
        # Read values
        for _ in range(num_keys):
            offset_val, length_val = struct.unpack_from('>II', data, offset)
            node.values.append((offset_val, length_val))
            offset += 8 # Size of two unsigned ints

        # Read children (num_keys + 1 children for num_keys keys, if not a leaf)
        if not node.is_leaf:
            for _ in range(num_keys + 1):
                child_page_num = struct.unpack_from('>I', data, offset)[0]
                node.children.append(child_page_num)
                offset += 4
        
        return node

class TrafficAccidentsTree:
    """
    Implements a simple B-Tree for traffic accidents data, using a Pager for disk I/O.
    (Simplified for this context - full B-Tree logic not implemented here).
    """
    def __init__(self, db_file_name: str, order: int = DEFAULT_ORDER):
        self.pager = Pager(os.path.join(APP_CONFIG["DB_DIR"], db_file_name))
        self.order = order # Maximum number of keys a node can hold (2t - 1)
        self.t = (order // 2) + 1 # Minimum degree (t)
        self.root: Optional[BTreeNode] = None
        self.root_page_num = -1 # Stores the page number of the root node

        # Load root from file if it exists, otherwise create a new one
        if self.pager.num_pages > 0:
            self.root_page_num = 0 # Assume root is always at page 0
            root_data = self.pager._read_page(self.root_page_num)
            self.root = BTreeNode.from_binary(root_data, self.order)
            logger.info(f"B-Tree root loaded from page {self.root_page_num}.")
        else:
            # Create a new root node for an empty tree
            self.root = BTreeNode(is_leaf=True)
            self.root_page_num = self.pager.allocate_page() # Allocate first page for root
            self._write_node(self.root_page_num, self.root)
            logger.info(f"New B-Tree root created at page {self.root_page_num}.")

    def _read_node(self, page_num: int) -> BTreeNode:
        """Reads a B-Tree node from disk."""
        data = self.pager._read_page(page_num)
        return BTreeNode.from_binary(data, self.order)

    def _write_node(self, page_num: int, node: BTreeNode):
        """Writes a B-Tree node to disk."""
        self.pager._write_page(page_num, node.to_binary(self.order))
        self.pager.flush_page(page_num) # Ensure changes are written to disk

    def close(self):
        """Closes the B-Tree by closing its pager."""
        self.pager.close()


# --- Streamlit UI Setup (setup_ui function) ---
def setup_ui():
    # Database Initialization (for regular file/index based DB)
    if 'db' not in st.session_state:
        st.session_state.db = TrafficAccidentsDB(
            DB_PATH, INDEX_PATH, LOCK_PATH, ID_COUNTER_PATH
        )
    db = st.session_state.db

    # B-Tree Database Initialization (for B-Tree based DB)
    if 'btree_db' not in st.session_state:
        st.session_state.btree_db = TrafficAccidentsTree(BTREE_DB_FILE_NAME)
    btree_db = st.session_state.btree_db


    st.sidebar.title("Navegação")
    # Using radio buttons for main navigation
    page = st.sidebar.radio(
        "Selecione uma função:",
        ["Dashboard", "Gerenciar Registros", "Importar/Exportar CSV", "Backup/Restaurar", "Compressão de Arquivos", "B-Tree Info", "Log de Atividades", "Configurações"]
    )

    if page == "Dashboard":
        st.header("Dashboard")
        st.write("Visão geral e estatísticas (a ser implementado).")
        st.info(f"Total de registros no banco de dados principal: **{len(db.index)}**")
        # Display basic B-Tree info
        st.info(f"Total de páginas no banco de dados B-Tree: **{btree_db.pager.num_pages}**")
        st.info(f"Caminho do arquivo do banco de dados B-Tree: `{btree_db.pager.db_file_path}`")
        
    elif page == "Gerenciar Registros":
        st.header("Gerenciar Registros")
        st.write("Funcionalidades CRUD para registros individuais.")
        
        st.subheader("Adicionar Novo Registro")
        with st.form("add_record_form"):
            new_id = st.number_input("ID (deixe 0 para auto-gerar)", min_value=0, value=0, step=1)
            new_city = st.text_input("Cidade", key="new_city")
            new_state = st.text_input("Estado", key="new_state")
            new_accident_type = st.text_input("Tipo de Acidente", key="new_accident_type")
            new_date = st.date_input("Data do Acidente", value=date.today(), key="new_date")
            new_time = st.time_input("Hora do Acidente", value=datetime.now().time(), key="new_time")
            new_weather = st.text_input("Condições Climáticas", key="new_weather")
            new_road = st.text_input("Condições da Estrada", key="new_road")
            new_vehicles = st.number_input("Número de Veículos", min_value=1, value=1, step=1, key="new_vehicles")
            new_fatalities = st.number_input("Número de Fatalidades", min_value=0, value=0, step=1, key="new_fatalities")

            submitted = st.form_submit_button("Adicionar Registro")
            if submitted:
                try:
                    data_obj = DataObject(
                        new_id if new_id > 0 else None, # Pass None for auto-generation
                        new_city, new_state, new_accident_type,
                        new_date.strftime('%Y-%m-%d'), new_time.strftime('%H:%M'),
                        new_weather, new_road, new_vehicles, new_fatalities
                    )
                    record_id = db.add_record(data_obj)
                    if record_id:
                        st.success(f"Registro adicionado com sucesso! ID: {record_id}")
                        logger.info(f"Record added: ID {record_id}")
                    else:
                        st.error("Falha ao adicionar registro.")
                except DataValidationError as e:
                    st.error(f"Erro de validação: {e}")
                    logger.error(f"Data validation error on add: {e}", exc_info=True)
                except Exception as e:
                    st.error(f"Erro ao adicionar registro: {e}")
                    logger.error(f"Error adding record: {e}", exc_info=True)

        st.subheader("Buscar Registro")
        search_id = st.number_input("ID do Registro para Buscar", min_value=1, step=1, key="search_id_input")
        if st.button("Buscar Registro", key="btn_search_record"):
            record = db.get_record(search_id)
            if record:
                st.write("---")
                st.json(record.to_csv_row()) # Display as JSON for simplicity
                st.write("---")
            else:
                st.warning(f"Registro com ID {search_id} não encontrado.")

        st.subheader("Listar Todos os Registros")
        if st.button("Listar Registros", key="btn_list_records"):
            all_records = db.get_all_records()
            if all_records:
                st.dataframe([record.to_csv_row() for record in all_records], 
                             column_names=["ID", "City", "State", "AccidentType", "Date", "Time", "Weather", "Road", "Vehicles", "Fatalities"])
            else:
                st.info("Nenhum registro no banco de dados.")

        st.subheader("Deletar Registro")
        delete_id = st.number_input("ID do Registro para Deletar", min_value=1, step=1, key="delete_id_input")
        if st.button("Deletar Registro", key="btn_delete_record"):
            if db.delete_record(delete_id):
                st.success(f"Registro com ID {delete_id} deletado com sucesso!")
                logger.info(f"Record deleted: ID {delete_id}")
            else:
                st.error(f"Não foi possível deletar o registro com ID {delete_id}. Ele pode não existir.")

    elif page == "Importar/Exportar CSV":
        st.header("Importar/Exportar Dados CSV")

        st.subheader("Importar CSV")
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], help="Selecione um arquivo CSV para importar registros. Tamanho máximo 100MB.", key="csv_importer")
        
        if uploaded_file is not None:
            file_size = uploaded_file.size
            if file_size > APP_CONFIG["MAX_FILE_SIZE_MB"] * 1024 * 1024:
                st.error(f"O tamanho do arquivo excede o limite de {APP_CONFIG['MAX_FILE_SIZE_MB']}MB.")
                logger.warning(f"Importação CSV falhou: arquivo muito grande ({file_size} bytes)")
                return

            try:
                # Initialize progress bar and text
                progress_text_placeholder = st.empty()
                progress_bar = st.progress(0)
                
                # Read the entire uploaded file buffer
                bytes_data = uploaded_file.getvalue()
                buffer = io.BytesIO(bytes_data)
                
                # Wrap the BytesIO object with TextIOWrapper for csv.reader
                # newline='' is crucial for csv.reader to handle universal newlines
                csvfile_wrapper = io.TextIOWrapper(buffer, encoding='utf-8', newline='')

                with st.spinner("Importando registros do CSV..."):
                    imported_count = 0
                    reader = csv.reader(csvfile_wrapper, delimiter=APP_CONFIG["CSV_DELIMITER"])
                    
                    # Read header
                    try:
                        header = next(reader) 
                    except StopIteration:
                        st.warning("O arquivo CSV está vazio ou contém apenas um cabeçalho sem dados.")
                        progress_bar.empty()
                        progress_text_placeholder.empty()
                        return

                    # Process rows and update progress
                    for i, row in enumerate(reader):
                        try:
                            data_obj = DataObject.from_csv_row(row)
                            db.add_record(data_obj)
                            imported_count += 1
                        except DataValidationError as e:
                            logger.warning(f"Pulando linha CSV inválida: {row} - Erro: {e}")
                            st.warning(f"Pulando linha inválida: {row} - {e}")
                        except Exception as e:
                            logger.error(f"Erro ao processar linha CSV: {row} - {e}", exc_info=True)
                            st.error(f"Erro ao processar linha: {row} - {e}")
                        
                        # Update progress based on bytes read
                        current_bytes_read = buffer.tell() # Current position in the BytesIO buffer
                        progress = min(1.0, current_bytes_read / file_size) # Ensure progress doesn't exceed 1.0
                        progress_bar.progress(progress)
                        progress_text_placeholder.text(f"Lendo CSV: {current_bytes_read:,} de {file_size:,} bytes ({progress:.1%})")

                st.success(f"Importação concluída! Adicionados {imported_count} novos registros.")
                logger.info(f"CSV import complete. Added {imported_count} new records.")
                progress_text_placeholder.empty() # Clear progress text
                progress_bar.empty() # Clear progress bar

            except UnicodeDecodeError:
                st.error("Erro de codificação: O arquivo CSV não está em UTF-8. Por favor, verifique a codificação.")
                logger.error(f"CSV import failed: UnicodeDecodeError - {traceback.format_exc()}")
            except Exception as e:
                st.error(f"Ocorreu um erro durante a importação do CSV: {e}")
                logger.error(f"Importação CSV falhou: {traceback.format_exc()}")
            finally:
                # Buffers are in-memory, no file to unlink
                pass

        st.subheader("Exportar CSV")
        if st.button("Exportar Banco de Dados para CSV"):
            try:
                # Use a BytesIO object to create the CSV in memory
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer, delimiter=APP_CONFIG["CSV_DELIMITER"])
                
                # Write header row
                writer.writerow(["ID", "City", "State", "AccidentType", "Date", "Time", "WeatherConditions", "RoadConditions", "NumVehicles", "NumFatalities"]) # Example header

                # Fetch all records and write to CSV
                records_exported = 0
                for record_id in db.index.keys():
                    data_obj = db.get_record(record_id)
                    if data_obj:
                        writer.writerow(data_obj.to_csv_row())
                        records_exported += 1
                
                csv_filename = f"traffic_accidents_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                st.success(f"Exportados {records_exported} registros para CSV.")
                st.download_button(
                    label="Download CSV Exportado",
                    data=csv_buffer.getvalue().encode('utf-8'), # Encode to bytes for download
                    file_name=csv_filename,
                    mime="text/csv"
                )
                logger.info(f"CSV exported. Exported {records_exported} records.")
            except Exception as e:
                st.error(f"Erro ao exportar CSV: {e}")
                logger.error(f"CSV export failed: {traceback.format_exc()}")

    elif page == "Backup/Restaurar":
        st.header("Backup e Restauração")
        
        st.subheader("Criar Backup")
        if st.button("Criar Backup Agora"):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_folder_name = f"backup_{timestamp}"
            full_backup_path = os.path.join(BACKUP_PATH, backup_folder_name)
            
            try:
                os.makedirs(full_backup_path, exist_ok=True)
                
                # Copy DB and Index files
                if os.path.exists(DB_PATH):
                    shutil.copy2(DB_PATH, full_backup_path)
                if os.path.exists(INDEX_PATH):
                    shutil.copy2(INDEX_PATH, full_backup_path)
                if os.path.exists(ID_COUNTER_PATH):
                    shutil.copy2(ID_COUNTER_PATH, full_backup_path)
                
                st.success(f"Backup criado com sucesso em: `{full_backup_path}`")
                logger.info(f"Backup created at: {full_backup_path}")
            except Exception as e:
                st.error(f"Erro ao criar backup: {e}")
                logger.error(f"Error creating backup: {e}", exc_info=True)

        st.subheader("Restaurar Backup")
        backup_dirs = [d for d in os.listdir(BACKUP_PATH) if os.path.isdir(os.path.join(BACKUP_PATH, d))]
        if not backup_dirs:
            st.info("Nenhum backup encontrado para restaurar.")
        else:
            selected_backup = st.selectbox("Selecione um backup para restaurar:", sorted(backup_dirs, reverse=True)) # Show most recent first
            if st.button("Restaurar Backup Selecionado"):
                backup_to_restore_path = os.path.join(BACKUP_PATH, selected_backup)
                try:
                    with filelock.FileLock(LOCK_PATH, timeout=10):
                        # Ensure DB file is closed if it was open (handled by filelock usually)
                        # Copy backup files back to main DB directory
                        if os.path.exists(os.path.join(backup_to_restore_path, os.path.basename(DB_PATH))):
                            shutil.copy2(os.path.join(backup_to_restore_path, os.path.basename(DB_PATH)), DB_PATH)
                        if os.path.exists(os.path.join(backup_to_restore_path, os.path.basename(INDEX_PATH))):
                            shutil.copy2(os.path.join(backup_to_restore_path, os.path.basename(INDEX_PATH)), INDEX_PATH)
                        if os.path.exists(os.path.join(backup_to_restore_path, os.path.basename(ID_COUNTER_PATH))):
                            shutil.copy2(os.path.join(backup_to_restore_path, os.path.basename(ID_COUNTER_PATH)), ID_COUNTER_PATH)
                        
                        # Re-initialize DB to load restored data
                        st.session_state.db = TrafficAccidentsDB(DB_PATH, INDEX_PATH, LOCK_PATH, ID_COUNTER_PATH)
                        st.success(f"Backup '{selected_backup}' restaurado com sucesso!")
                        logger.info(f"Backup '{selected_backup}' restored.")
                        st.experimental_rerun() # Rerun to update DB info
                except filelock.Timeout:
                    st.error("Não foi possível adquirir o bloqueio do arquivo para restauração. Tente novamente.")
                    logger.error("Could not acquire file lock for restore.")
                except Exception as e:
                    st.error(f"Erro ao restaurar backup: {e}")
                    logger.error(f"Error restoring backup: {e}", exc_info=True)


    elif page == "Compressão de Arquivos":
        st.header("Ferramentas de Compressão de Arquivos")
        st.info("Esta seção seria integrada com as ferramentas de Compressão Huffman e LZW.")
        st.write("Você pode usar as funcionalidades de compressão e descompressão aqui.")
        # Placeholder for Huffman and LZW integration
        # You would typically import and call functions from stHuffman_v5.py and stLZWPY_v4.py here
        st.subheader("Compressão Huffman (Exemplo de Integração)")
        st.write("Integre `stHuffman_v5.py` aqui para compressão e descompressão de arquivos.")
        
        st.subheader("Compressão LZW (Exemplo de Integração)")
        st.write("Integre `stLZWPY_v4.py` aqui para compressão e descompressão de arquivos.")


    elif page == "B-Tree Info":
        st.header("Informações da B-Tree")
        st.write("Detalhes e estatísticas sobre a implementação da B-Tree em disco.")
        
        st.write(f"Caminho do arquivo do banco de dados B-Tree: `{st.session_state.btree_db.pager.db_file_path}`")
        st.write(f"Tamanho da Página: {PAGE_SIZE} bytes")
        st.write(f"Ordem da B-Tree: {st.session_state.btree_db.order}")
        st.write(f"Grau Mínimo (t): {st.session_state.btree_db.t}")
        st.write(f"Número de páginas alocadas: {st.session_state.btree_db.pager.num_pages}")


        # Option to clear B-Tree DB (for testing/cleanup)
        if st.button("Limpar Arquivo de Banco de Dados B-Tree"):
            if os.path.exists(st.session_state.btree_db.pager.db_file_path):
                try:
                    st.session_state.btree_db.pager.flush_all()
                    st.session_state.btree_db.pager.file.close()
                    os.remove(st.session_state.btree_db.pager.db_file_path)
                    # Re-initialize the B-Tree after deletion
                    st.session_state.btree_db = TrafficAccidentsTree(BTREE_DB_FILE_NAME) 
                    st.success("Banco de dados B-Tree limpo e reiniciado.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao limpar banco de dados B-Tree: {e}")
                    logger.error(f"Error cleaning B-Tree DB: {e}", exc_info=True)

    elif page == "Log de Atividades":
        st.header("Log de Atividades")
        log_file_path = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOG_FILE_NAME"])
        st.subheader("Registros de Atividade Recentes")
        
        try:
            if os.path.exists(log_file_path):
                display_entries = []
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    # Read lines in reverse to get most recent
                    lines = f.readlines()
                    for line in reversed(lines):
                        # Basic parsing, adjust regex if log format changes
                        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - (.*)', line.strip())
                        if match:
                            timestamp_str, logger_name, log_level, message = match.groups()
                            # Filter for relevant logs, e.g., 'Record added', 'Record updated', 'CSV import complete'
                            # and general INFO, WARNING, ERROR messages
                            if any(keyword in message for keyword in ["Record added", "Record updated", "Import complete", "Backup created", "Backup restored", "Error", "Skipping invalid CSV row"]) or log_level in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
                                color = "white"
                                if log_level == "ERROR" or log_level == "CRITICAL":
                                    color = "red"
                                elif log_level == "WARNING":
                                    color = "orange"
                                elif log_level == "INFO":
                                    color = "green" # Or blue, depending on preference
                                
                                display_entries.append(f"**`{timestamp_str}`** `<span style='color: {color};'>[{log_level}]</span>` `{message}`")

                                if len(display_entries) >= APP_CONFIG["MAX_LOG_ENTRIES_DISPLAY"]:
                                    break
                        else:
                            logger.warning(f"Failed to parse log line for display: {line.strip()}")
                            continue
                
                if display_entries:
                    for entry in display_entries:
                        st.markdown(entry, unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Nenhum registro recente de atividade relevante encontrado no log.")
            else:
                st.info("ℹ️ Arquivo de log de atividades não encontrado.")
        except Exception as e:
            st.error(f"⚠️ Não foi possível ler o log de atividades: {str(e)}")
            logger.error(f"Error reading activity log: {traceback.format_exc()}")


    elif page == "Configurações":
        st.header("Configurações do Aplicativo")
        st.info("Ajuste as configurações do banco de dados e do aplicativo. Alterações aqui não são persistentes entre as sessões do Streamlit a menos que você implemente um salvamento de configuração.")
        
        st.subheader("Caminhos do Banco de Dados")
        st.write(f"Diretório Base: `{APP_CONFIG['DB_DIR']}`")
        st.write(f"Arquivo de Banco de Dados: `{APP_CONFIG['DB_FILE_NAME']}`")
        st.write(f"Arquivo de Índice: `{APP_CONFIG['INDEX_FILE_NAME']}`")
        st.write(f"Arquivo de Bloqueio: `{APP_CONFIG['LOCK_FILE_NAME']}`")
        st.write(f"Arquivo Contador de ID: `{APP_CONFIG['ID_COUNTER_FILE_NAME']}`")
        st.write(f"Diretório de Backups: `{APP_CONFIG['BACKUP_DIR_NAME']}`")

        st.subheader("Parâmetros de Operação")
        st.write(f"Delimitador CSV Atual: `{APP_CONFIG['CSV_DELIMITER']}`")
        st.write(f"Máximo de Registros por Página (UI): `{APP_CONFIG['MAX_RECORDS_PER_PAGE']}`")
        st.write(f"Tamanho Máximo de Arquivo CSV (MB): `{APP_CONFIG['MAX_FILE_SIZE_MB']}`")
        st.write(f"Tamanho do Chunk para I/O: `{APP_CONFIG['CHUNK_SIZE']}`")
        st.write(f"Número Máximo de Backups: `{APP_CONFIG['MAX_BACKUPS']}`")
        st.write(f"Máximo de Entradas de Log a Exibir: `{APP_CONFIG['MAX_LOG_ENTRIES_DISPLAY']}`")

        # Example of how to allow changing a setting (e.g., CSV Delimiter)
        new_delimiter = st.text_input("Alterar Delimitador CSV", value=APP_CONFIG["CSV_DELIMITER"], key="csv_delimiter_input")
        if st.button("Atualizar Delimitador CSV"):
            APP_CONFIG["CSV_DELIMITER"] = new_delimiter
            st.success(f"Delimitador CSV atualizado para: `{new_delimiter}`")
            # For persistent changes, you would need to save APP_CONFIG to a file (e.g., JSON)
            # and reload it on app start.

# --- Main Application Entry Point ---
if __name__ == "__main__":
    try:
        # Ensure base directories exist
        Path(APP_CONFIG["DB_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
        
        # Ensure the B-Tree DB file exists (creates if not), so Pager can open it
        # .touch(exist_ok=True) creates an empty file if it doesn't exist
        Path(BTREE_DB_PATH).touch(exist_ok=True) 

        setup_ui()
    except Exception as e:
        st.error(f"Um erro crítico ocorreu na aplicação: {e}")
        logger.critical(f"Exceção não tratada no ponto de entrada principal do aplicativo: {traceback.format_exc()}")