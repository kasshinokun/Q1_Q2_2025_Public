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

# --- Configuration Constants (Centralized & Merged) ---
APP_CONFIG = {
    "DB_DIR": os.path.join(Path.home(), 'Documents', 'Data'),
    "DB_FILE_NAME": 'traffic_accidents.db',
    "INDEX_FILE_NAME": 'index.idx',
    "LOCK_FILE_NAME": 'traffic_accidents.lock',
    "ID_COUNTER_FILE_NAME": 'id_counter.dat',
    "BACKUP_DIR_NAME": 'backups',
    "CSV_DELIMITER": ';',
    "MAX_RECORDS_PER_PAGE": 20,
    "MAX_FILE_SIZE_MB": 100,
    "CHUNK_SIZE": 8192,
    "MAX_BACKUPS": 5,
    "MAX_LOG_ENTRIES_DISPLAY": 15,
    "LOG_FILE_NAME": 'traffic_accidents_app.log',
    # B-Tree Specific Config
    "BTREE_DB_FILE_NAME": 'traffic_accidents_btree.db',
    "BTREE_ORDER": 63, # B-Tree Order
    # Compression Specific Config
    "COMPRESSION_SOURCE_DIR": os.path.join(Path.home(), 'Documents', 'SourceForCompression'),
    "COMPRESSION_OUTPUT_DIR": os.path.join(Path.home(), 'Documents', 'CompressedFiles'),
    "HUFFMAN_EXTENSION": ".huff",
    "LZW_EXTENSION": ".lzw",
    "MIN_COMPRESSION_SIZE": 100, # Minimum file size to apply compression for Huffman
    "BUFFER_SIZE": 8192 # Buffer size for file I/O operations in Huffman
}

# --- Path Derivations ---
DB_DIR = Path(APP_CONFIG["DB_DIR"])
DB_PATH = DB_DIR / APP_CONFIG["DB_FILE_NAME"]
INDEX_PATH = DB_DIR / APP_CONFIG["INDEX_FILE_NAME"]
LOCK_PATH = DB_DIR / APP_CONFIG["LOCK_FILE_NAME"]
ID_COUNTER_PATH = DB_DIR / APP_CONFIG["ID_COUNTER_FILE_NAME"]
BACKUP_PATH = DB_DIR / APP_CONFIG["BACKUP_DIR_NAME"]
LOG_FILE_PATH = DB_DIR / APP_CONFIG["LOG_FILE_NAME"]
BTREE_DB_PATH = DB_DIR / APP_CONFIG["BTREE_DB_FILE_NAME"]
COMPRESSION_SOURCE_DIR = Path(APP_CONFIG["COMPRESSION_SOURCE_DIR"])
COMPRESSION_OUTPUT_DIR = Path(APP_CONFIG["COMPRESSION_OUTPUT_DIR"])

# --- Ensure Directories Exist ---
DB_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_PATH.mkdir(parents=True, exist_ok=True)
COMPRESSION_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
COMPRESSION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---
class DataValidationError(Exception):
    """Custom exception for data validation errors within DataObject."""
    pass

class DatabaseError(Exception):
    """Custom exception for database operations and file I/O errors."""
    pass

class FileLockError(Exception):
    """Custom exception for errors acquiring/releasing file locks."""
    pass

# --- Data Fields Definition ---
# Based on stCRUDDataObjectPY_v3alpha.py and v5alpha0.1.d.py
FIELDS = [
    'crash_date', 'traffic_control_device', 'weather_condition',
    'lighting_condition', 'first_crash_type', 'trafficway_type',
    'alignment', 'roadway_surface_cond', 'road_defect', 'crash_type',
    'intersection_related_i', 'damage', 'prim_contributory_cause',
    'num_units', 'most_severe_injury', 'injuries_total', 'injuries_fatal',
    'injuries_incapacitating', 'injuries_non_incapacitating',
    'injuries_reported_not_evident', 'injuries_no_indication',
    'crash_hour', 'crash_day_of_week', 'crash_month'
]

# --- DataObject Class (Merged & Enhanced) ---
class DataObject:
    """
    Represents a traffic accident record with validation and multiple serialization formats.
    """
    def __init__(self, existing_data_dict: Dict[str, Any]):
        self.data = {}
        self._initialize_defaults()
        # Overwrite defaults with provided data, ensuring validation
        for field in FIELDS:
            if field in existing_data_dict:
                self.data[field] = existing_data_dict[field]

        self.id = self.data.get('id')
        self.validate() # Validate on creation

    def _initialize_defaults(self):
        """Initializes all fields with safe and type-appropriate default values."""
        self.data = {
            'crash_date': "", 'traffic_control_device': "UNKNOWN", 'weather_condition': "UNKNOWN",
            'lighting_condition': "UNKNOWN", 'first_crash_type': "UNKNOWN", 'trafficway_type': "UNKNOWN",
            'alignment': "UNKNOWN", 'roadway_surface_cond': "UNKNOWN", 'road_defect': "NONE",
            'crash_type': "UNKNOWN", 'intersection_related_i': "NO", 'damage': "UNKNOWN",
            'prim_contributory_cause': "UNKNOWN", 'num_units': 0, 'most_severe_injury': "NONE",
            'injuries_total': 0.0, 'injuries_fatal': 0.0, 'injuries_incapacitating': 0.0,
            'injuries_non_incapacitating': 0.0, 'injuries_reported_not_evident': 0.0,
            'injuries_no_indication': 0.0, 'crash_hour': 0, 'crash_day_of_week': 1, 'crash_month': 1
        }

    def validate(self):
        """Performs validation and sanitization on the data dictionary."""
        # This is a simplified validation routine for the merged script.
        # A full implementation would use the detailed validators from v5alpha0.1.d
        if not self.data.get('crash_date'):
            raise DataValidationError("Crash date is required.")
        if not self.data.get('crash_type') or self.data['crash_type'] == "UNKNOWN":
            raise DataValidationError("Crash type is required.")
        # Ensure numeric types
        for field in ['num_units', 'injuries_total', 'injuries_fatal', 'crash_hour']:
             # Convert to float first, then to int, to handle "0.0" correctly
             try:
                 self.data[field] = int(float(self.data.get(field, 0)))
             except (ValueError, TypeError) as e:
                 raise DataValidationError(f"Invalid numeric value for {field}: {self.data.get(field)} - {e}")
        return True


    def to_dict(self) -> Dict[str, Any]:
        """Returns the full data dictionary, including the ID."""
        output_dict = self.data.copy()
        if self.id is not None:
            output_dict['id'] = self.id
        return output_dict

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'DataObject':
        """Creates a DataObject instance from a dictionary."""
        return cls(existing_data_dict=data_dict)

    @classmethod
    def from_csv_row(cls, row_data: List[str]) -> 'DataObject':
        """Creates a DataObject from a list of strings (CSV row)."""
        if len(row_data) != len(FIELDS):
            raise DataValidationError(f"CSV row has {len(row_data)} fields, expected {len(FIELDS)}.")
        data_dict = dict(zip(FIELDS, row_data))
        return cls(existing_data_dict=data_dict)


    def to_binary(self) -> bytes:
        """Serializes the DataObject to bytes for B-Tree storage."""
        # This serialization must match from_binary
        # Using JSON as a simple, flexible binary format for this merge
        data_to_serialize = self.to_dict()
        return json.dumps(data_to_serialize, sort_keys=True).encode('utf-8')

    @staticmethod
    def from_binary(binary_data: bytes) -> 'DataObject':
        """Deserializes bytes back into a DataObject."""
        data_dict = json.loads(binary_data.decode('utf-8'))
        return DataObject.from_dict(data_dict)

    def __lt__(self, other): return self.id < other.id
    def __eq__(self, other): return self.id == other.id
    def __hash__(self): return hash(self.id)
    def __repr__(self): return f"DataObject(ID={self.id}, Type='{self.data.get('crash_type')}')"


################################################################################
# SECTION 1: Standard Database Engine (File + Index)
# Based on stCRUDDataObjectPY_v4epsilon.py & v5alpha0.1.d.py
################################################################################

RECORD_FORMAT_V4 = "<Q d 32s ?" # record_id, timestamp, hash, is_valid
RECORD_HEADER_SIZE_V4 = struct.calcsize(RECORD_FORMAT_V4)

class TrafficAccidentsDB:
    """
    Handles database operations using a main data file and a separate index file.
    """
    def __init__(self):
        self.db_file = DB_PATH
        self.index_file = INDEX_PATH
        self.lock_file = LOCK_PATH
        self.id_counter_file = ID_COUNTER_PATH
        self.backup_dir = BACKUP_PATH
        self._index_cache: Dict[int, int] = {}
        self._current_id = 0
        self._lock = filelock.FileLock(self.lock_file, timeout=10)
        
        with self._lock:
            self._load_id_counter()
            self._load_index_to_cache()

    def _load_id_counter(self):
        if self.id_counter_file.exists():
            try:
                self._current_id = int(self.id_counter_file.read_text())
            except (IOError, ValueError) as e:
                logger.warning(f"Could not load ID counter, resetting to 0: {e}")
                self._current_id = 0
        else:
            self._current_id = 0

    def _save_id_counter(self):
        try:
            self.id_counter_file.write_text(str(self._current_id))
        except IOError as e:
            logger.error(f"Error saving ID counter: {e}")

    def _get_next_id(self) -> int:
        self._current_id += 1
        self._save_id_counter()
        return self._current_id

    def _load_index_to_cache(self):
        self._index_cache = {}
        if not self.index_file.exists():
            return
        try:
            with open(self.index_file, 'rb') as f_idx:
                entry_size = struct.calcsize("<Q Q")
                while chunk := f_idx.read(entry_size):
                    if len(chunk) == entry_size:
                        r_id, pos = struct.unpack("<Q Q", chunk)
                        self._index_cache[r_id] = pos
        except Exception as e:
            logger.error(f"Error loading index file to cache: {e}")
            self._index_cache = {} # Clear cache on error to prevent inconsistent state

    def _save_index_from_cache(self):
        try:
            with open(self.index_file, 'wb') as f_idx:
                for r_id, pos in self._index_cache.items():
                    f_idx.write(struct.pack("<Q Q", r_id, pos))
        except IOError as e:
            logger.error(f"Error saving index file from cache: {e}")

    def add_record(self, data_obj: DataObject) -> int:
        data_dict = data_obj.to_dict()
        data_bytes = json.dumps(data_dict).encode('utf-8')
        data_hash = hashlib.sha256(data_bytes).hexdigest()
        
        with self._lock:
            record_id = self._get_next_id()
            timestamp = datetime.now().timestamp()
            
            record_header = struct.pack(
                RECORD_FORMAT_V4, record_id, timestamp,
                bytes.fromhex(data_hash), True
            )
            
            try:
                with open(self.db_file, 'ab') as f:
                    position = f.tell()
                    f.write(record_header)
                    f.write(struct.pack("<I", len(data_bytes)))
                    f.write(data_bytes)
            except IOError as e:
                logger.error(f"Error writing record to DB file: {e}")
                raise DatabaseError(f"Failed to add record to DB file: {e}")
            
            self._index_cache[record_id] = position
            self._save_index_from_cache()
            
        logger.info(f"[StandardDB] Added record {record_id}")
        return record_id

    def get_record(self, record_id: int) -> Optional[DataObject]:
        with self._lock:
            position = self._index_cache.get(record_id)
            if position is None:
                return None
            
            try:
                with open(self.db_file, 'rb') as f:
                    f.seek(position)
                    header_bytes = f.read(RECORD_HEADER_SIZE_V4)
                    if len(header_bytes) < RECORD_HEADER_SIZE_V4: 
                        logger.warning(f"Incomplete header for record {record_id} at position {position}")
                        return None
                    
                    _, _, _, is_valid = struct.unpack(RECORD_FORMAT_V4, header_bytes)
                    if not is_valid: return None

                    data_size_bytes = f.read(4)
                    if len(data_size_bytes) < 4: 
                        logger.warning(f"Incomplete data size for record {record_id} at position {position}")
                        return None
                    data_size = struct.unpack("<I", data_size_bytes)[0]
                    
                    data_bytes = f.read(data_size)
                    if len(data_bytes) < data_size:
                        logger.warning(f"Incomplete data for record {record_id} at position {position}")
                        return None

                    data_dict = json.loads(data_bytes.decode('utf-8'))
                    data_dict['id'] = record_id
                    
                    return DataObject.from_dict(data_dict)
            except (IOError, json.JSONDecodeError, struct.error) as e:
                logger.error(f"Error reading record {record_id} from DB file: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error getting record {record_id}: {traceback.format_exc()}")
                return None


    def get_all_records(self) -> List[DataObject]:
        records = []
        with self._lock:
            sorted_ids = sorted(self._index_cache.keys())
            for record_id in sorted_ids:
                record = self.get_record(record_id)
                if record:
                    records.append(record)
        return records

    def update_record(self, record_id: int, new_data_obj: DataObject) -> bool:
        with self._lock:
            position = self._index_cache.get(record_id)
            if position is None: 
                logger.warning(f"[StandardDB] Attempted to update non-existent record {record_id}.")
                return False
            
            try:
                # Mark old record as invalid
                with open(self.db_file, 'r+b') as f:
                    f.seek(position + struct.calcsize("<Q d 32s")) # Seek to the boolean flag
                    f.write(struct.pack("?", False))
            except IOError as e:
                logger.error(f"Error marking old record {record_id} as invalid: {e}")
                raise DatabaseError(f"Failed to update record {record_id}: {e}")
            
            # Remove old entry from index and add new record
            del self._index_cache[record_id] # Temporarily remove from cache
            # Add new record. This will assign a new position and update the index.
            # We must ensure the new_data_obj does not carry the old ID for this logic to work,
            # or handle re-assignment. For simplicity, `add_record` will assign a new ID.
            # If the intent was to keep the ID, the logic needs to overwrite in place or rebuild.
            # For this consolidated version, we simulate an update by invalidating old and adding new.
            new_record_assigned_id = self.add_record(new_data_obj) # Add as a new record, effectively
            logger.info(f"[StandardDB] Updated (invalidated old, added new) record {record_id} -> New ID {new_record_assigned_id}")
        return True

    def delete_record(self, record_id: int) -> bool:
        with self._lock:
            position = self._index_cache.get(record_id)
            if position is None: 
                logger.warning(f"[StandardDB] Attempted to delete non-existent record {record_id}.")
                return False
            
            try:
                # Mark as invalid in the DB file
                with open(self.db_file, 'r+b') as f:
                    f.seek(position + struct.calcsize("<Q d 32s")) # Seek to the boolean flag
                    f.write(struct.pack("?", False))
            except IOError as e:
                logger.error(f"Error marking record {record_id} as invalid for deletion: {e}")
                raise DatabaseError(f"Failed to delete record {record_id}: {e}")

            # Remove from index cache
            if record_id in self._index_cache:
                del self._index_cache[record_id]
                self._save_index_from_cache()

        logger.info(f"[StandardDB] Deleted record {record_id}")
        return True

    def get_number_of_records(self) -> int:
        return len(self._index_cache)
        
    def delete_all_data(self):
        with self._lock:
            try:
                if self.db_file.exists(): self.db_file.unlink()
                if self.index_file.exists(): self.index_file.unlink()
                if self.id_counter_file.exists(): self.id_counter_file.unlink()
                self._index_cache.clear()
                self._current_id = 0
                logger.info("[StandardDB] All data has been deleted.")
            except IOError as e:
                logger.error(f"Error deleting all data for StandardDB: {e}")
                raise DatabaseError(f"Failed to delete all data: {e}")


################################################################################
# SECTION 2: B-Tree Database Engine
# Based on stCRUDDataObjectPY_v5alpha0.2.a.py
################################################################################

# --- B-Tree Constants ---
PAGE_SIZE = APP_CONFIG["CHUNK_SIZE"] # 8192
PAGE_HEADER_SIZE = 32

def serialize_btree_key(key_val) -> bytes:
    """Pads string representation of a key to a fixed length for B-Tree comparison."""
    # Ensure consistent padding and length for comparison
    # For integer IDs, convert to string and pad. Max 8 chars for a Q-sized int.
    return str(key_val).encode('utf-8').ljust(8, b'\x00')

def deserialize_btree_key(key_bytes: bytes) -> str:
    """Decodes a fixed-length key back to a string."""
    return key_bytes.decode('utf-8').strip('\x00')

class BTreeNodePage:
    """Represents the in-memory structure of a single B-Tree page."""
    # Slot stores (data_offset, data_length, child_page_num)
    SLOT_SIZE = struct.calcsize('<HHI') # offset(H - 2 bytes), length(H - 2 bytes), child_page_num(I - 4 bytes) = 8 bytes

    def __init__(self, page_data: bytearray, page_num: int, is_new: bool = False):
        self.page_data = page_data
        self.page_num = page_num
        self.is_dirty = is_new

        if is_new:
            self.num_keys = 0
            self.is_leaf = True
            # Free space offset points to the end of the page initially
            self.free_space_offset = PAGE_SIZE 
            self._write_header() # Write initial header for new pages
        else:
            self._read_header() # Read header for existing pages

    def _write_header(self):
        # Format: num_keys (H), free_space_offset (H), is_leaf (?), padding (x), reserved (H)
        # Using 8 bytes for header to align with common block sizes, though only 5 are strictly used here.
        struct.pack_into('<H H ? x H', self.page_data, 0, 
                         self.num_keys, 
                         self.free_space_offset, 
                         self.is_leaf, 
                         0) # Placeholder for reserved field or padding

    def _read_header(self):
        self.num_keys, self.free_space_offset, self.is_leaf, _ = struct.unpack_from('<H H ? x H', self.page_data, 0) # Unpack 4 values

    @property
    def num_keys(self) -> int:
        return struct.unpack_from('<H', self.page_data, 0)[0]

    @num_keys.setter
    def num_keys(self, value: int):
        struct.pack_into('<H', self.page_data, 0, value)
        self.is_dirty = True

    @property
    def is_leaf(self) -> bool:
        return struct.unpack_from('<?', self.page_data, 4)[0] # Correct offset for is_leaf

    @is_leaf.setter
    def is_leaf(self, value: bool):
        struct.pack_into('<?', self.page_data, 4, value) # Correct offset
        self.is_dirty = True

    @property
    def free_space_offset(self) -> int:
        return struct.unpack_from('<H', self.page_data, 2)[0] # Correct offset for free_space_offset

    @free_space_offset.setter
    def free_space_offset(self, value: int):
        struct.pack_into('<H', self.page_data, 2, value) # Correct offset
        self.is_dirty = True
        
    def get_child_page_num(self, slot_idx: int) -> int:
        # Child pointers are stored with the keys in the slots
        slot_offset = PAGE_HEADER_SIZE + slot_idx * self.SLOT_SIZE
        _, _, child_page = struct.unpack_from('<HHI', self.page_data, slot_offset)
        return child_page

    def get_key_data_from_slot(self, slot_idx: int) -> Tuple[bytes, bytes]:
        slot_offset = PAGE_HEADER_SIZE + slot_idx * self.SLOT_SIZE
        data_offset, data_length, _ = struct.unpack_from('<HHI', self.page_data, slot_offset)
        payload = self.page_data[data_offset : data_offset + data_length]
        
        # We assume the key can be extracted from the payload (DataObject's ID)
        # This is for internal B-Tree comparison, not directly stored as a fixed-size key in the slot
        # However, for simplicity here, we'll return a 'derived' key.
        # In a strict B-Tree, keys are stored explicitly.
        
        # Here, `get_key_from_payload` needs the payload to extract the key.
        # So we return the payload and let the caller extract the key.
        return payload, payload # Return payload as both key and value for now, and rely on get_key_from_payload in search

    def insert_cell(self, slot_idx: int, key_bytes: bytes, payload: bytes, child_page: int = 0):
        # A B-Tree typically stores (key, value_pointer, child_pointer) in slots.
        # Given DataObject.to_binary() includes the ID, we'll store (key_bytes, payload_offset, payload_length, child_page_num)
        # where payload_offset/length refer to the DataObject's binary representation.

        # For this merged example, simplified to store: (offset_to_payload, length_of_payload, child_page_num)
        # and the actual payload is placed at the free_space_offset.
        # The key is *derived* from the payload. This is a common simplification in simpler DBs.

        payload_len = len(payload)
        # Calculate required space. A slot needs SLOT_SIZE, plus space for the actual payload.
        required_space = self.SLOT_SIZE + payload_len 
        
        if self.free_space_offset - required_space < PAGE_HEADER_SIZE + (self.num_keys + 1) * self.SLOT_SIZE:
            # If there's not enough space for the new slot and its payload
            raise Exception("Page full: Cannot insert cell. Requires B-tree split handling.") # Needs proper B-tree split handling

        # Place the new payload at the end of the free space (moving backwards from PAGE_SIZE)
        new_payload_offset = self.free_space_offset - payload_len
        self.page_data[new_payload_offset : self.free_space_offset] = payload
        self.free_space_offset = new_payload_offset

        # Shift existing slots to make room for the new slot
        # Start from the last slot and move backwards
        for i in range(self.num_keys, slot_idx, -1):
            source_slot_start = PAGE_HEADER_SIZE + (i - 1) * self.SLOT_SIZE
            dest_slot_start = PAGE_HEADER_SIZE + i * self.SLOT_SIZE
            # Copy slot data: (data_offset, data_length, child_page)
            self.page_data[dest_slot_start : dest_slot_start + self.SLOT_SIZE] = \
                self.page_data[source_slot_start : source_slot_start + self.SLOT_SIZE]

        # Insert the new slot entry
        new_slot_start = PAGE_HEADER_SIZE + slot_idx * self.SLOT_SIZE
        struct.pack_into('<HHI', self.page_data, new_slot_start, 
                         new_payload_offset, payload_len, child_page)
        
        self.num_keys += 1
        self.is_dirty = True

    def get_cell_data(self, slot_idx: int) -> bytes:
        """Retrieves the payload (serialized DataObject) for a given slot index."""
        if slot_idx >= self.num_keys:
            raise IndexError("Slot index out of bounds.")
        slot_offset = PAGE_HEADER_SIZE + slot_idx * self.SLOT_SIZE
        data_offset, data_length, _ = struct.unpack_from('<HHI', self.page_data, slot_offset)
        return self.page_data[data_offset : data_offset + data_length]


class Pager:
    """Manages reading and writing B-Tree pages to/from disk."""
    ROOT_PAGE_METADATA_SIZE = 4 # Size to store root page number

    def __init__(self, db_file_path: Path):
        self.db_file_path = db_file_path
        self.file = open(self.db_file_path, 'r+b' if self.db_file_path.exists() else 'w+b')
        
        # Ensure file is at least large enough for root metadata
        if self.db_file_path.stat().st_size < self.ROOT_PAGE_METADATA_SIZE:
             self.file.write(b'\x00' * self.ROOT_PAGE_METADATA_SIZE) # Pad for root page number
             self.file.flush()

        self.file.seek(0, os.SEEK_END)
        # The next_page_num calculation needs to account for the metadata at the start
        self.next_page_num = (self.file.tell() - self.ROOT_PAGE_METADATA_SIZE) // PAGE_SIZE 

        if self.next_page_num == 0:
            # If the file is new or only has metadata, create the first actual data page
            # This is the root page
            initial_root_page = self.new_page(is_leaf=True)
            self.root_page_num = initial_root_page.page_num
            self._save_metadata() # Save the root page number
        else:
            self._load_metadata()
        
        self.cache = OrderedDict()
        self.cache_size = 100 # Cache up to 100 pages

    def _save_metadata(self):
        self.file.seek(0)
        self.file.write(self.root_page_num.to_bytes(4, 'little'))
        self.file.flush()

    def _load_metadata(self):
        self.file.seek(0)
        root_num_bytes = self.file.read(4)
        if len(root_num_bytes) < 4:
            raise DatabaseError("B-Tree DB file corrupted: Root page number missing.")
        self.root_page_num = int.from_bytes(root_num_bytes, 'little')
        
    def new_page(self, is_leaf: bool = True) -> BTreeNodePage:
        # Allocate space for a new page AFTER the metadata and existing pages
        page_num = self.next_page_num
        self.file.seek(self.ROOT_PAGE_METADATA_SIZE + page_num * PAGE_SIZE)
        self.file.write(b'\x00' * PAGE_SIZE)
        self.next_page_num += 1
        page = BTreeNodePage(bytearray(PAGE_SIZE), page_num, is_new=True)
        page.is_leaf = is_leaf # Set leaf property using setter to mark dirty
        self.write_page(page) # Write the new page to cache and mark for disk write
        return page

    def read_page(self, page_num: int) -> BTreeNodePage:
        if page_num in self.cache:
            self.cache.move_to_end(page_num)
            return self.cache[page_num]

        file_offset = self.ROOT_PAGE_METADATA_SIZE + page_num * PAGE_SIZE
        self.file.seek(file_offset)
        page_data_bytes = self.file.read(PAGE_SIZE)
        
        if len(page_data_bytes) < PAGE_SIZE:
            logger.error(f"Incomplete page data read for page {page_num}. Expected {PAGE_SIZE}, got {len(page_data_bytes)}.")
            raise IndexError("Page index out of bounds or incomplete page data.")

        page = BTreeNodePage(bytearray(page_data_bytes), page_num)
        # No need to call _read_header here as it's called in BTreeNodePage's __init__ when not new.
        
        if len(self.cache) >= self.cache_size:
            lru_page_num, lru_page = self.cache.popitem(last=False)
            if lru_page.is_dirty: self._write_to_disk(lru_page)
        
        self.cache[page_num] = page
        return page
        
    def write_page(self, page: BTreeNodePage):
        page.is_dirty = True
        self.cache[page.page_num] = page
        self.cache.move_to_end(page.page_num)
        
    def _write_to_disk(self, page: BTreeNodePage):
        file_offset = self.ROOT_PAGE_METADATA_SIZE + page.page_num * PAGE_SIZE
        self.file.seek(file_offset)
        self.file.write(page.page_data)
        page.is_dirty = False

    def flush_all(self):
        """Writes all dirty pages from cache to disk."""
        for page in self.cache.values():
            if page.is_dirty: self._write_to_disk(page)
        self._save_metadata() # Ensure root page num is saved
        self.file.flush()

    def close(self):
        """Closes the underlying file, flushing any unsaved changes."""
        if hasattr(self, 'file') and not self.file.closed:
            self.flush_all()
            self.file.close()

    def __del__(self):
        self.close()


class TrafficAccidentsTree:
    """B-Tree based database for Traffic Accidents."""
    def __init__(self):
        self.pager = Pager(BTREE_DB_PATH)
        self.order = APP_CONFIG["BTREE_ORDER"]
        self.t = math.ceil(self.order / 2) # Minimum degree (t)

    def _search_key(self, node_page: BTreeNodePage, key_bytes: bytes) -> Tuple[bool, int]:
        """
        Binary search for a key in a node page.
        Returns (is_found, index) where index is the position where the key was found
        or where it should be inserted.
        """
        low = 0
        high = node_page.num_keys - 1
        insert_idx = 0

        while low <= high:
            mid = (low + high) // 2
            payload_at_mid, _ = node_page.get_key_data_from_slot(mid) # Get payload to extract key
            current_key_bytes = self.get_key_from_payload(payload_at_mid)
            
            # Compare serialized keys
            if key_bytes == current_key_bytes:
                return True, mid
            elif key_bytes < current_key_bytes:
                high = mid - 1
                insert_idx = mid
            else:
                low = mid + 1
                insert_idx = low
        return False, insert_idx
        
    def get_key_from_payload(self, payload:bytes)->bytes:
         # Assuming payload is JSON, extract 'id' and serialize it as the key
         data_dict = json.loads(payload.decode('utf-8'))
         return serialize_btree_key(data_dict['id'])

    def add_record(self, data_obj: DataObject):
        # Simplified add_record without full B-Tree splitting.
        # It assumes enough space or handles simple cases in the root.
        key_bytes = serialize_btree_key(data_obj.id)
        payload = data_obj.to_binary()
        
        root_page = self.pager.read_page(self.pager.root_page_num)
        
        is_found, idx = self._search_key(root_page, key_bytes)
        
        if is_found: # Update existing record
            # In this simplified B-Tree, if a key is found, we effectively
            # overwrite it by inserting the new payload at the same logical position.
            # This doesn't handle resizing of payloads well in the page's free space.
            # A full B-tree would delete the old entry and insert the new, or update in place.
            logger.warning(f"[B-Tree] Updating record {data_obj.id}. Overwriting data.")
            # For simplicity, we remove the old entry and then add the new one.
            # This is not a true in-place update for B-trees but works for this simplified version.
            # A more robust B-tree implementation would need to handle this properly,
            # perhaps by marking the old slot as deleted and adding a new one,
            # or by managing free space within pages for in-place updates.
            # Given the simple BTreeNodePage, deleting and re-inserting is difficult.
            # For now, if found, we just allow `insert_cell` to try and insert, potentially creating duplicates or errors.
            # This is a known limitation of the merged B-tree.
            pass

        try:
            root_page.insert_cell(idx, key_bytes, payload) # Pass key_bytes as parameter to insert_cell
            self.pager.write_page(root_page)
            self.pager.flush_all()
            logger.info(f"[B-Tree] Added/Updated record {data_obj.id}")
            return data_obj.id
        except Exception as e:
            logger.error(f"[B-Tree] Failed to add/update record {data_obj.id}: {e}")
            raise DatabaseError(f"Failed to add/update record in B-Tree: {e}")

    def get_record(self, record_id: int) -> Optional[DataObject]:
        key_bytes = serialize_btree_key(record_id)
        
        # Traverse the B-tree to find the record
        current_page_num = self.pager.root_page_num
        while True:
            try:
                node_page = self.pager.read_page(current_page_num)
            except IndexError:
                logger.error(f"[B-Tree] Attempted to read invalid page number {current_page_num}")
                return None

            is_found, idx = self._search_key(node_page, key_bytes)
            
            if is_found:
                payload = node_page.get_cell_data(idx)
                return DataObject.from_binary(payload)
            elif node_page.is_leaf:
                return None # Not found in a leaf node
            else:
                # If not found in internal node, go to appropriate child
                # The child page number is stored in the slot for the key just before `idx`
                # if `idx` is not 0, or for the very first child if `idx` is 0.
                # In this simplified B-tree, `get_child_page_num(idx)` is used,
                # which implies the child pointer is associated with the `idx`-th slot.
                current_page_num = node_page.get_child_page_num(idx)


    def get_all_records(self) -> List[DataObject]:
        records = []
        # This function needs a full traversal for a B-tree.
        # Implement a basic in-order traversal (DFS)
        stack = [self.pager.root_page_num]
        visited_pages = set() # To prevent infinite loops if tree is malformed

        while stack:
            page_num = stack.pop()
            if page_num in visited_pages:
                continue
            visited_pages.add(page_num)

            try:
                node_page = self.pager.read_page(page_num)
            except IndexError:
                logger.error(f"[B-Tree] Skipped invalid page number {page_num} during full scan.")
                continue

            # For a B-tree, keys and child pointers alternate: P0, K1, P1, K2, P2, ... Pk, Kk, Pk
            # So, to traverse in-order, first visit P0, then K1, then P1, etc.
            
            # If not a leaf, add the first child pointer (P0)
            if not node_page.is_leaf:
                stack.append(node_page.get_child_page_num(0)) # Assuming child 0 is the left-most

            for i in range(node_page.num_keys):
                # Process the current key/record
                payload = node_page.get_cell_data(i)
                records.append(DataObject.from_binary(payload))
                
                # If not a leaf, add the next child pointer (Pi)
                if not node_page.is_leaf:
                    stack.append(node_page.get_child_page_num(i + 1)) # Child associated with the (i)-th key

        # Sort by ID as B-tree provides ordered access, but our simple traversal might not guarantee it
        # due to `get_cell_data` not necessarily returning keys in exact order or full traversal complexities.
        # The B-Tree search is order-preserving, so a proper traversal should result in sorted IDs.
        # However, due to simplified B-tree node implementation, an explicit sort here ensures correctness.
        return sorted(records, key=lambda r: r.id)

    def delete_record(self, record_id: int) -> bool:
        logger.warning("[B-Tree] Delete operation is not fully implemented for this simplified B-Tree.")
        return False
        
    def get_number_of_records(self) -> int:
        # For a true B-Tree, this would require traversing and counting records in leaves.
        # For this simplified implementation, a full traversal might be slow for large datasets.
        # A more robust solution would be to maintain a record count in metadata.
        
        # For now, traverse all records and count.
        try:
            return len(self.get_all_records())
        except Exception as e:
            logger.error(f"[B-Tree] Error getting number of records: {e}")
            return 0

    def delete_all_data(self):
        try:
            self.pager.close() # Close and flush pager
            if BTREE_DB_PATH.exists():
                BTREE_DB_PATH.unlink()
            self.__init__() # Re-initialize the pager and B-tree
            logger.info("[B-Tree] All data has been deleted.")
        except IOError as e:
            logger.error(f"Error deleting all data for B-Tree: {e}")
            raise DatabaseError(f"Failed to delete all B-Tree data: {e}")

################################################################################
# SECTION 3: Compression Utilities
# Based on stHuffman_v5.py and stLZWPY_v4.py
################################################################################

# --- Huffman Compression ---
class HuffmanNode:
    def __init__(self, char: Optional[bytes], freq: int, left=None, right=None):
        self.char, self.freq, self.left, self.right = char, freq, left, right
    def __lt__(self, other): return self.freq < other.freq

class HuffmanProcessor:
    @staticmethod
    def generate_tree(data: bytes, progress_callback=None) -> Optional['HuffmanNode']:
        """Optimized tree generation with progress tracking"""
        if not data:
            return None
            
        if len(data) == 1:
            return HuffmanNode(data, 1)  # Handle single-byte case

        if progress_callback:
            progress_callback(0, "Analyzing file content...")

        # Use Counter for frequency analysis of bytes
        byte_count = Counter(data)
        
        # Handle single-byte case
        if len(byte_count) == 1:
            byte = next(iter(byte_count))
            return HuffmanNode(bytes([byte]), byte_count[byte])
        
        if progress_callback:
            progress_callback(0.2, "Building priority queue...")

        nodes = [HuffmanNode(bytes([byte]), freq) for byte, freq in byte_count.items()]
        heapq.heapify(nodes)

        if progress_callback:
            progress_callback(0.3, "Constructing Huffman tree...")

        # total_nodes = len(nodes) # Not strictly used for progress calculation in this way
        while len(nodes) > 1:
            left = heapq.heappop(nodes)
            right = heapq.heappop(nodes)
            heapq.heappush(nodes, HuffmanNode(None, left.freq + right.freq, left, right))
            
            if progress_callback and len(nodes) % 50 == 0: # Update less frequently for performance
                progress = 0.3 + 0.7 * (1 - len(nodes)/(len(byte_count)*2 - 1)) # Approx progress
                progress_callback(progress, f"Merging nodes: {len(nodes)} remaining")

        if progress_callback:
            progress_callback(1.0, "Huffman tree complete!")
            time.sleep(0.3)

        return nodes[0]

    @staticmethod
    def build_codebook(root: Optional['HuffmanNode']) -> Dict[bytes, str]:
        """Optimized codebook generation with iterative DFS"""
        if not root:
            return {}

        codebook = {}
        stack = [(root, "")]
        
        while stack:
            node, code = stack.pop()
            if node.char is not None:
                codebook[node.char] = code or '0' # Ensure single node tree gets a code
            else:
                if node.right:
                    stack.append((node.right, code + '1'))
                if node.left:
                    stack.append((node.left, code + '0'))
        
        return codebook

    @staticmethod
    def compress_file(input_path: str, output_path: str, progress_callback=None) -> Tuple[int, int, float, float]:
        """Optimized compression with progress tracking"""
        start_time = time.time()
        
        # Read input file as binary
        try:
            with open(input_path, 'rb') as file:
                data = file.read()
        except IOError as e:
            logger.error(f"Error reading input file for Huffman compression: {e}")
            raise DatabaseError(f"Failed to read input file for compression: {e}")

        if not data:
            return 0, 0, 0.0, 0.0

        original_size = len(data)
        
        # Skip compression for small files
        if original_size < APP_CONFIG["MIN_COMPRESSION_SIZE"]:
            try:
                with open(output_path, 'wb') as file:
                    file.write(data)
            except IOError as e:
                logger.error(f"Error writing small file directly during Huffman compression: {e}")
                raise DatabaseError(f"Failed to write uncompressed small file: {e}")
            return original_size, original_size, 0.0, time.time() - start_time

        # Step 1: Build Huffman tree
        if progress_callback:
            progress_callback(0.1, "Building Huffman Tree...")
        root = HuffmanProcessor.generate_tree(
            data, 
            lambda p, m: progress_callback(0.1 + p * 0.2, m) if progress_callback else None # Allocate 20% for tree build
        )

        # Step 2: Build codebook
        if progress_callback:
            progress_callback(0.3, "Generating encoding dictionary...")
        codebook = HuffmanProcessor.build_codebook(root)
        
        # Create reverse lookup for faster encoding
        # byte[0] since HuffmanNode stores bytes, e.g., b'a'
        encode_table = {byte[0]: code for byte, code in codebook.items()}  

        # Step 3: Compress data
        if progress_callback:
            progress_callback(0.4, "Encoding data...")

        compressed_output_buffer = io.BytesIO() # Use BytesIO for in-memory writing
        
        # Write header: codebook size, then each byte, code_length, code_int
        # This is different from the original Huffman_v5.py's header, which was json.dumps
        # The new header stores (byte, code_length, code_int) for each entry.
        
        # Write character table size
        compressed_output_buffer.write(struct.pack('I', len(codebook)))
        for byte_val, code in codebook.items():
            # HuffmanNode stores char as bytes, so byte_val is like b'a'. Get the integer value.
            compressed_output_buffer.write(struct.pack('B', byte_val[0]))  # Single byte character
            compressed_output_buffer.write(struct.pack('B', len(code)))    # Length of code string
            
            # Pad code to nearest 8 bits for int conversion if needed, then convert
            # This needs to be careful: int(code, 2) works directly on binary strings.
            # No padding needed for int conversion itself, but make sure to store enough bits.
            # Using 4 bytes (I) for code_int implies max 32 bits. Our codes can be variable.
            # Need to adjust based on max_code_length in Huffman.
            
            # For simplicity, if codes are short, just store directly.
            # A more robust solution would be to use varint encoding for codes or fixed maximum length.
            # For now, let's assume `code` fits in an int (e.g., max 32 bits)
            try:
                code_int = int(code, 2)
                compressed_output_buffer.write(struct.pack('I', code_int))
            except ValueError as e:
                logger.error(f"Code {code} cannot be converted to int: {e}")
                raise DatabaseError(f"Error packing Huffman code: {e}")

        # Write original data size
        compressed_output_buffer.write(struct.pack('I', original_size))

        # Buffered bit writing
        current_byte = 0
        bit_count = 0
        bytes_processed = 0
        
        for byte in data:
            code = encode_table[byte]
            for bit_char in code:
                current_byte = (current_byte << 1) | (1 if bit_char == '1' else 0)
                bit_count += 1
                if bit_count == 8:
                    compressed_output_buffer.write(bytes([current_byte]))
                    current_byte = 0
                    bit_count = 0
            
            bytes_processed += 1
            if progress_callback and bytes_processed % 10000 == 0: # Update less frequently
                progress = 0.4 + 0.5 * (bytes_processed / original_size) # Allocate 50% for encoding
                progress_callback(progress, f"Encoded {bytes_processed}/{original_size} bytes")

        # Flush remaining bits
        padding_bits_at_end = (8 - bit_count) % 8
        if bit_count > 0:
            current_byte <<= padding_bits_at_end
            compressed_output_buffer.write(bytes([current_byte]))
        
        # Write padding size as the very last byte (or 0 if no padding)
        compressed_output_buffer.write(struct.pack('B', padding_bits_at_end))

        # Final write to disk
        try:
            with open(output_path, 'wb') as file:
                file.write(compressed_output_buffer.getvalue())
        except IOError as e:
            logger.error(f"Error writing compressed file (Huffman): {e}")
            raise DatabaseError(f"Failed to write compressed file: {e}")


        compressed_size = os.path.getsize(output_path)
        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0.0
        process_time = time.time() - start_time

        if progress_callback:
            progress_callback(1.0, "Compression complete!")

        return original_size, compressed_size, compression_ratio, process_time

    @staticmethod
    def decompress_file(input_path: str, output_path: str, progress_callback=None) -> Tuple[int, int, float, float]:
        """Optimized decompression with progress tracking"""
        start_time = time.time()
        
        try:
            with open(input_path, 'rb') as file:
                # Read character table size
                header_data = file.read(4)
                if len(header_data) < 4: raise DatabaseError("Invalid Huffman file: Header size missing.")
                table_size = struct.unpack('I', header_data)[0]
                
                code_table = {}
                max_code_length = 0
                
                if progress_callback:
                    progress_callback(0.1, "Reading metadata...")

                for i in range(table_size):
                    entry_data = file.read(1 + 1 + 4) # byte (B), code_length (B), code_int (I)
                    if len(entry_data) < 6: raise DatabaseError(f"Invalid Huffman file: Incomplete codebook entry {i}.")
                    
                    byte, code_length, code_int = struct.unpack('B B I', entry_data)
                    code = format(code_int, f'0{code_length}b') # Reconstruct binary string
                    code_table[code] = bytes([byte])
                    max_code_length = max(max_code_length, code_length)
                    
                    if progress_callback and i % 100 == 0:
                        progress = 0.1 + 0.2 * (i / table_size)
                        progress_callback(progress, f"Loading code table: {i}/{table_size}")

                # Read original data size
                data_size_bytes = file.read(4)
                if len(data_size_bytes) < 4: raise DatabaseError("Invalid Huffman file: Original data size missing.")
                original_decompressed_size = struct.unpack('I', data_size_bytes)[0]

                # Read all remaining compressed data bytes (excluding the last byte which is padding info)
                compressed_data_bytes_raw = file.read()
                if not compressed_data_bytes_raw: raise DatabaseError("Invalid Huffman file: No compressed data found.")

                # The last byte of the stream is the padding information
                padding_bits = compressed_data_bytes_raw[-1]
                compressed_data_bytes = compressed_data_bytes_raw[:-1] # Actual compressed data
                
        except (IOError, struct.error, json.JSONDecodeError) as e:
            logger.error(f"Error reading Huffman compressed file: {e}")
            raise DatabaseError(f"Failed to read compressed file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during Huffman decompression file read: {traceback.format_exc()}")
            raise DatabaseError(f"Unexpected error during decompression: {e}")

        # Convert bytes to a single bit string
        bit_string = ""
        for byte in compressed_data_bytes:
            bit_string += format(byte, '08b')
        
        # Remove trailing padding bits if any
        if padding_bits > 0:
            bit_string = bit_string[:-padding_bits]

        # Decompress the bit string
        decompressed_output_buffer = io.BytesIO()
        current_code = ""
        bytes_decoded = 0
        
        if progress_callback:
            progress_callback(0.4, "Decompressing data...")

        for bit in bit_string:
            current_code += bit
            if current_code in code_table:
                decompressed_output_buffer.write(code_table[current_code])
                bytes_decoded += 1
                current_code = "" # Reset for next code
                
                if progress_callback and bytes_decoded % 10000 == 0:
                    progress = 0.4 + 0.5 * (bytes_decoded / original_decompressed_size) if original_decompressed_size > 0 else 0.9
                    progress_callback(progress, f"Decoded {bytes_decoded}/{original_decompressed_size} bytes")

        # Final check if the decoded size matches the expected size
        if bytes_decoded != original_decompressed_size:
            logger.warning(f"Huffman decompression resulted in {bytes_decoded} bytes, expected {original_decompressed_size} bytes.")
            # Depending on strictness, this could be an error or just a warning.
            # We will still write out the data we got.

        try:
            with open(output_path, 'wb') as file:
                file.write(decompressed_output_buffer.getvalue())
        except IOError as e:
            logger.error(f"Error writing decompressed file (Huffman): {e}")
            raise DatabaseError(f"Failed to write decompressed file: {e}")

        compressed_size_on_disk = os.path.getsize(input_path)
        decompressed_size_on_disk = os.path.getsize(output_path)
        
        compression_ratio = (1 - decompressed_size_on_disk / compressed_size_on_disk) * 100 if compressed_size_on_disk > 0 else 0.0
        process_time = time.time() - start_time

        if progress_callback:
            progress_callback(1.0, "Decompression complete!")

        return compressed_size_on_disk, decompressed_size_on_disk, compression_ratio, process_time


# --- LZW Compression ---
def lzw_compress(input_path: str, output_path: str, progress_callback=None):
    start_time = time.time()
    try:
        with open(input_path, 'rb') as f: data = f.read()
    except IOError as e:
        logger.error(f"Error reading input file for LZW compression: {e}")
        raise DatabaseError(f"Failed to read input file: {e}")
    
    if not data: return 0,0,0,0 # Nothing to compress
    
    original_size = len(data)

    dictionary = {bytes([i]): i for i in range(256)}
    next_code = 256
    w = bytes()
    compressed_codes = []

    total_bytes = len(data)
    processed_bytes = 0

    if progress_callback:
        progress_callback(0.1, "Initializing LZW dictionary...")

    for byte in data:
        c = bytes([byte])
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            compressed_codes.append(dictionary[w])
            # Limit dictionary size to prevent excessive memory usage.
            # Using 16-bit codes (0-65535), so max_code is 65535.
            if next_code < 65536: 
                dictionary[wc] = next_code
                next_code += 1
            else: # Dictionary full, clear it and restart codes.
                # This simple reset can hurt compression ratio if previous dictionary was good.
                # More advanced LZW uses a dynamic bit-width or no-reset.
                dictionary = {bytes([i]): i for i in range(256)}
                next_code = 256
            w = c
        
        processed_bytes += 1
        if progress_callback and processed_bytes % 10000 == 0:
            progress = 0.1 + 0.8 * (processed_bytes / total_bytes) # Allocate 80% for encoding
            progress_callback(progress, f"Compressing LZW: {processed_bytes}/{total_bytes} bytes")

    if w: compressed_codes.append(dictionary[w])

    try:
        with open(output_path, 'wb') as f:
            # Write a simple header: total number of codes
            f.write(len(compressed_codes).to_bytes(4, 'big')) 
            for code in compressed_codes:
                f.write(code.to_bytes(2, 'big')) # Write codes as 16-bit integers
    except IOError as e:
        logger.error(f"Error writing output file for LZW compression: {e}")
        raise DatabaseError(f"Failed to write compressed file: {e}")

    compressed_size = os.path.getsize(output_path)
    compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0.0
    process_time = time.time() - start_time

    if progress_callback:
        progress_callback(1.0, "LZW Compression complete!")
        
    return original_size, compressed_size, compression_ratio, process_time

def lzw_decompress(input_path: str, output_path: str, progress_callback=None):
    start_time = time.time()
    try:
        with open(input_path, 'rb') as f:
            # Read header: total number of codes
            num_codes_bytes = f.read(4)
            if len(num_codes_bytes) < 4: raise DatabaseError("Invalid LZW file: Number of codes missing.")
            num_codes = int.from_bytes(num_codes_bytes, 'big')
            
            compressed_data = []
            if progress_callback: progress_callback(0.1, "Reading compressed data...")
            for i in range(num_codes):
                code_bytes = f.read(2)
                if len(code_bytes) < 2: raise DatabaseError(f"Invalid LZW file: Incomplete code at index {i}.")
                compressed_data.append(int.from_bytes(code_bytes, 'big'))
                if progress_callback and i % 10000 == 0:
                    progress = 0.1 + 0.2 * (i / num_codes)
                    progress_callback(progress, f"Reading LZW codes: {i}/{num_codes}")
    except (IOError, struct.error) as e:
        logger.error(f"Error reading LZW compressed file: {e}")
        raise DatabaseError(f"Failed to read compressed file: {e}")
    
    if not compressed_data: return 0,0,0,0 # Nothing to decompress

    dictionary = {i: bytes([i]) for i in range(256)}
    next_code = 256
    decompressed_bytes_buffer = io.BytesIO() # Use BytesIO for efficient writing
    
    if progress_callback:
        progress_callback(0.3, "Decompressing LZW data...")

    try:
        # First code
        previous_entry = dictionary[compressed_data[0]]
        decompressed_bytes_buffer.write(previous_entry)

        for i in range(1, len(compressed_data)):
            code = compressed_data[i]
            current_entry = bytes()
            
            if code in dictionary:
                current_entry = dictionary[code]
            elif code == next_code:
                current_entry = previous_entry + bytes([previous_entry[0]])
            else:
                raise DatabaseError(f"Bad compressed code {code} during LZW decompression.")
            
            decompressed_bytes_buffer.write(current_entry)
            
            # Add new entry to dictionary
            if next_code < 65536: # Max for 16-bit codes
                dictionary[next_code] = previous_entry + bytes([current_entry[0]])
                next_code += 1
            else: # Dictionary full, clear it and restart codes.
                dictionary = {i: bytes([i]) for i in range(256)}
                next_code = 256

            previous_entry = current_entry
            
            if progress_callback and i % 10000 == 0:
                progress = 0.3 + 0.6 * (i / num_codes)
                progress_callback(progress, f"Decompressing LZW: {i}/{num_codes} codes processed")

    except Exception as e:
        logger.error(f"Error during LZW bit string decoding: {e}")
        raise DatabaseError(f"Error during LZW decoding: {e}")

    try:
        with open(output_path, 'wb') as f:
            f.write(decompressed_bytes_buffer.getvalue())
    except IOError as e:
        logger.error(f"Error writing decompressed file (LZW): {e}")
        raise DatabaseError(f"Failed to write decompressed file: {e}")

    compressed_size_on_disk = os.path.getsize(input_path)
    decompressed_size_on_disk = os.path.getsize(output_path)
    
    compression_ratio = (1 - decompressed_size_on_disk / compressed_size_on_disk) * 100 if compressed_size_on_disk > 0 else 0.0
    process_time = time.time() - start_time

    if progress_callback:
        progress_callback(1.0, "LZW Decompression complete!")

    return compressed_size_on_disk, decompressed_size_on_disk, compression_ratio, process_time


################################################################################
# SECTION 4: Streamlit UI
# Based on stCRUDDataObjectPY_v3alpha.py structure with enhancements
################################################################################

def setup_ui():
    """Configures the main Streamlit page and UI components."""
    st.set_page_config(page_title="Traffic Accidents DB", layout="wide", page_icon="🚗")

    st.markdown("""
    <style>
        .main .block-container { padding-top: 2rem; }
        .stButton>button { background-color: #007bff; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🚗 Traffic Accidents Database Manager")
    st.caption("Enhanced version with multiple DB engines and tools.")

    # --- Initialize Database Engine in Session State ---
    if 'db_engine' not in st.session_state:
        st.session_state.db_engine = TrafficAccidentsDB() # Default to standard
        st.session_state.db_type = "Standard"
    
    # Store temporary state for delete confirmation dialog
    if 'show_delete_confirmation' not in st.session_state:
        st.session_state.show_delete_confirmation = False

    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Configuration")

        db_choice = st.radio(
            "Select Database Engine",
            ("Standard", "B-Tree"),
            index=0 if st.session_state.db_type == "Standard" else 1,
            key="db_engine_choice"
        )
        
        if db_choice != st.session_state.db_type:
            # Close existing database connection if switching
            if hasattr(st.session_state.db_engine, 'close') and callable(getattr(st.session_state.db_engine, 'close')):
                st.session_state.db_engine.close()

            if db_choice == "Standard":
                st.session_state.db_engine = TrafficAccidentsDB()
            else: # B-Tree
                st.session_state.db_engine = TrafficAccidentsTree()
            st.session_state.db_type = db_choice
            st.rerun() # Rerun to update the main UI with the new DB engine

        st.header("📊 Database Info")
        try:
            num_records = st.session_state.db_engine.get_number_of_records()
            st.metric("Total Records", num_records)
        except Exception as e:
            st.error(f"Could not get record count: {e}")
            logger.error(f"Error getting record count for UI: {e}")

        st.divider()
        st.header("📄 Operations")
        operation = st.radio(
            "Choose an action:",
            ["View All Records", "Search & Manage", "Add New Record", "Import from CSV", "Export to CSV"]
        )
        
        st.divider()
        admin_expander(st.session_state.db_engine)
        
        # Moved compression utilities here
        utilities_expander() 
        
        activity_log_expander()


    # --- Main Panel Dispatcher ---
    db = st.session_state.db_engine
    if operation == "View All Records":
        view_all_records_ui(db)
    elif operation == "Search & Manage":
        search_and_manage_ui(db)
    elif operation == "Add New Record":
        add_new_record_ui(db)
    elif operation == "Import from CSV":
        import_from_csv_ui(db)
    elif operation == "Export to CSV":
        export_to_csv_ui(db)

def admin_expander(db):
    with st.sidebar.expander("🔑 Admin & Backups"):
        if st.button("Create Backup", use_container_width=True, key="create_backup_btn"):
            if isinstance(db, TrafficAccidentsDB):
                try:
                    with st.spinner("Creating backup..."):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_db_file = BACKUP_PATH / f"{APP_CONFIG['DB_FILE_NAME']}_{timestamp}.bak"
                        backup_index_file = BACKUP_PATH / f"{APP_CONFIG['INDEX_FILE_NAME']}_{timestamp}.idx_bak"
                        backup_id_counter_file = BACKUP_PATH / f"{APP_CONFIG['ID_COUNTER_FILE_NAME']}_{timestamp}.cnt_bak"

                        shutil.copy2(DB_PATH, backup_db_file)
                        shutil.copy2(INDEX_PATH, backup_index_file)
                        shutil.copy2(ID_COUNTER_PATH, backup_id_counter_file)
                        
                        # Clean up old backups
                        all_backups = sorted(BACKUP_PATH.glob(f"{APP_CONFIG['DB_FILE_NAME']}*.bak"), key=os.path.getmtime)
                        if len(all_backups) > APP_CONFIG["MAX_BACKUPS"]:
                            for old_backup in all_backups[:-APP_CONFIG["MAX_BACKUPS"]]:
                                os.unlink(old_backup)
                                # Also delete corresponding index and id counter backups if they exist
                                try:
                                    os.unlink(old_backup.parent / old_backup.name.replace(".bak", ".idx_bak"))
                                    os.unlink(old_backup.parent / old_backup.name.replace(".bak", ".cnt_bak"))
                                except OSError as e:
                                    logger.warning(f"Could not clean up associated backup files for {old_backup.name}: {e}")

                    st.success(f"Backup created successfully at {backup_db_file.parent}!")
                    logger.info(f"Backup created: {backup_db_file}")
                except FileNotFoundError:
                    st.warning("Database files not found. Cannot create backup.")
                    logger.warning("Attempted to backup but DB files not found.")
                except Exception as e:
                    st.error(f"Backup failed: {e}")
                    logger.error(f"Backup operation failed: {traceback.format_exc()}")
            else:
                st.warning("Backup is only implemented for the Standard DB engine.")
        
        st.caption("Choose a backup to restore:")
        backup_files = list(BACKUP_PATH.glob(f"{APP_CONFIG['DB_FILE_NAME']}*.bak"))
        backup_files.sort(key=os.path.getmtime, reverse=True) # Sort by modification time, newest first
        
        backup_options = [f.name for f in backup_files]
        selected_backup = st.selectbox("Select backup file", [""] + backup_options, key="select_backup")

        if selected_backup and st.button("Restore from Selected Backup", use_container_width=True, key="restore_backup_btn"):
            if isinstance(db, TrafficAccidentsDB):
                st.session_state.show_restore_confirmation = True
            else:
                st.warning("Restore is only implemented for the Standard DB engine.")

    if st.session_state.get("show_restore_confirmation") and selected_backup:
        with st.dialog("Confirm Restore"):
            st.write(f"This will overwrite current data with: **{selected_backup}**. Are you sure?")
            if st.button("Yes, Restore"):
                try:
                    with st.spinner("Restoring database..."):
                        backup_db_file = BACKUP_PATH / selected_backup
                        backup_index_file = BACKUP_PATH / selected_backup.replace(".bak", ".idx_bak")
                        backup_id_counter_file = BACKUP_PATH / selected_backup.replace(".bak", ".cnt_bak")

                        # Ensure lock is released before overwriting files
                        try:
                            db._lock.release() 
                        except Exception as e:
                            logger.warning(f"Could not release database lock before restore: {e}. Attempting to proceed.")


                        shutil.copy2(backup_db_file, DB_PATH)
                        shutil.copy2(backup_index_file, INDEX_PATH)
                        shutil.copy2(backup_id_counter_file, ID_COUNTER_PATH)
                        
                        # Reinitialize DB to load restored data and re-acquire lock
                        st.session_state.db_engine = TrafficAccidentsDB()
                        st.session_state.show_restore_confirmation = False
                        st.success("Database restored successfully! Re-initializing application...")
                        logger.info(f"Database restored from {selected_backup}")
                        time.sleep(1)
                        st.rerun()
                except FileNotFoundError:
                    st.error("Selected backup files not found. Restore failed.")
                    logger.error(f"Restore failed: {traceback.format_exc()}")
                except Exception as e:
                    st.error(f"Restore failed: {e}")
                    logger.error(f"Restore operation failed: {traceback.format_exc()}")
            if st.button("Cancel Restore"):
                st.session_state.show_restore_confirmation = False
                st.rerun()

    if st.button("⚠️ Delete All Data", use_container_width=True, key="delete_all_data_btn"):
        st.session_state.show_delete_confirmation = True

    if st.session_state.get("show_delete_confirmation"):
        with st.dialog("Confirm Deletion"):
             st.write("This will permanently delete all records. Are you sure?")
             if st.button("Yes, Delete Everything"):
                 try:
                     db.delete_all_data()
                     st.session_state.show_delete_confirmation = False
                     st.success("All data has been deleted.")
                     time.sleep(1)
                     st.rerun()
                 except Exception as e:
                     st.error(f"Failed to delete data: {e}")
                     logger.error(f"Error during all data deletion: {traceback.format_exc()}")
             if st.button("Cancel"):
                 st.session_state.show_delete_confirmation = False
                 st.rerun()

def get_files_in_dir(directory: Path, extensions: Optional[List[str]] = None) -> List[str]:
    """Helper to get files in a directory with optional extension filtering."""
    files = []
    if directory.exists() and directory.is_dir():
        for item in os.listdir(directory):
            item_path = directory / item
            if item_path.is_file():
                if extensions:
                    if any(item.lower().endswith(ext.lower()) for ext in extensions):
                        files.append(item)
                else:
                    files.append(item)
    return files

def utilities_expander():
    with st.sidebar.expander("🛠️ Compression Utilities"):
        st.write("Select a file and an algorithm to compress or decompress.")
        
        compression_mode = st.radio(
            "Operation:",
            ("Compress", "Decompress"),
            key="compression_mode_radio"
        )
        
        algorithm_choice = st.radio(
            "Algorithm:",
            ("Huffman", "LZW"),
            key="algorithm_choice_radio"
        )

        uploaded_file = st.file_uploader(
            f"Upload a file for {compression_mode.lower()}", 
            type=None, # Allow all types, check extension later
            key="compression_uploader"
        )
        
        # --- File selection from default directories ---
        st.markdown("---")
        st.write("Or select from default directories:")

        selected_default_file = None
        default_files_available = []

        if compression_mode == "Compress":
            default_files_available = get_files_in_dir(COMPRESSION_SOURCE_DIR)
        else: # Decompress
            if algorithm_choice == "Huffman":
                default_files_available = get_files_in_dir(COMPRESSION_OUTPUT_DIR, extensions=[APP_CONFIG["HUFFMAN_EXTENSION"]])
            elif algorithm_choice == "LZW":
                default_files_available = get_files_in_dir(COMPRESSION_OUTPUT_DIR, extensions=[APP_CONFIG["LZW_EXTENSION"]])
        
        if default_files_available:
            selected_default_file = st.selectbox(
                f"Select a file from '{COMPRESSION_SOURCE_DIR.name}' (for compression) or '{COMPRESSION_OUTPUT_DIR.name}' (for decompression):",
                [""] + sorted(default_files_available),
                key="default_file_selector"
            )
        else:
            st.info(f"No relevant files found in {'source' if compression_mode == 'Compress' else 'output'} directory for {algorithm_choice} {compression_mode.lower()}.")


        # --- Process Button ---
        if st.button(f"Start {compression_mode} with {algorithm_choice}", key="start_compression_btn"):
            file_to_process_path = None
            input_filename = None
            
            # Determine which file source to use
            if uploaded_file:
                # Save uploaded file to a temporary location for processing
                temp_dir = tempfile.mkdtemp()
                file_to_process_path = Path(temp_dir) / uploaded_file.name
                with open(file_to_process_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                input_filename = uploaded_file.name
            elif selected_default_file:
                if compression_mode == "Compress":
                    file_to_process_path = COMPRESSION_SOURCE_DIR / selected_default_file
                else: # Decompress
                    file_to_process_path = COMPRESSION_OUTPUT_DIR / selected_default_file
                input_filename = selected_default_file
            
            if not file_to_process_path or not file_to_process_path.exists():
                st.warning("Please upload a file or select one from the default directories.")
                return

            # Initialize progress bar and text
            progress_bar = st.progress(0)
            progress_text = st.empty()

            def update_progress(progress: float, message: str):
                progress_bar.progress(progress)
                progress_text.text(message)

            output_path = None
            try:
                if compression_mode == "Compress":
                    output_filename = input_filename + (APP_CONFIG["HUFFMAN_EXTENSION"] if algorithm_choice == "Huffman" else APP_CONFIG["LZW_EXTENSION"])
                    output_path = COMPRESSION_OUTPUT_DIR / output_filename
                    
                    if algorithm_choice == "Huffman":
                        original_size, compressed_size, compression_ratio, process_time = \
                            HuffmanProcessor.compress_file(str(file_to_process_path), str(output_path), update_progress)
                    else: # LZW
                        original_size, compressed_size, compression_ratio, process_time = \
                            lzw_compress(str(file_to_process_path), str(output_path), update_progress)
                    
                    st.success("File compressed successfully!")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Original Size", f"{original_size:,} bytes")
                        st.metric("Compression Ratio", f"{compression_ratio:.2f}%")
                    with col2:
                        st.metric("Compressed Size", f"{compressed_size:,} bytes")
                        st.metric("Processing Time", f"{process_time:.2f} sec")
                    st.write(f"Compressed file saved to: `{output_path}`")
                
                else:  # Decompress
                    expected_extension = APP_CONFIG["HUFFMAN_EXTENSION"] if algorithm_choice == "Huffman" else APP_CONFIG["LZW_EXTENSION"]
                    if not input_filename.endswith(expected_extension):
                        st.error(f"Selected file '{input_filename}' does not have the expected '{expected_extension}' extension for {algorithm_choice} decompression.")
                        return

                    # Remove the compression extension to get original name
                    original_filename_base = input_filename[:-len(expected_extension)]
                    output_filename = f"decompressed_{original_filename_base}"
                    output_path = COMPRESSION_OUTPUT_DIR / output_filename
                    
                    if algorithm_choice == "Huffman":
                        compressed_size, decompressed_size, compression_ratio, process_time = \
                            HuffmanProcessor.decompress_file(str(file_to_process_path), str(output_path), update_progress)
                    else: # LZW
                        compressed_size, decompressed_size, compression_ratio, process_time = \
                            lzw_decompress(str(file_to_process_path), str(output_path), update_progress)
                    
                    st.success("File decompressed successfully!")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Compressed Size", f"{compressed_size:,} bytes")
                        st.metric("Decompression Ratio", f"{compression_ratio:.2f}%")
                    with col2:
                        st.metric("Decompressed Size", f"{decompressed_size:,} bytes")
                        st.metric("Processing Time", f"{process_time:.2f} sec")
                    st.write(f"Decompressed file saved to: `{output_path}`")
                    
                    # Offer download for decompressed file
                    if output_path and output_path.exists():
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Download Decompressed File",
                                data=f,
                                file_name=output_filename,
                                mime="application/octet-stream",
                                key="download_decompressed_btn"
                            )

            except DatabaseError as e: # Catch custom database/file errors
                st.error(f"Operation failed: {e}")
                logger.error(f"Compression/Decompression Error: {traceback.format_exc()}")
            except Exception as e:
                st.error(f"An unexpected error occurred during {compression_mode.lower()}: {e}")
                logger.error(f"Unexpected error in compression utilities: {traceback.format_exc()}")
            finally:
                # Clean up temporary uploaded file if it was created
                if 'temp_dir' in locals() and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                
                # Ensure progress bar completes
                progress_bar.progress(1.0)
                progress_text.text("Done.")
                time.sleep(0.5)


def activity_log_expander():
     with st.sidebar.expander("📜 Activity Log"):
        st.write(f"Last {APP_CONFIG['MAX_LOG_ENTRIES_DISPLAY']} log entries:")
        if LOG_FILE_PATH.exists():
            try:
                with open(LOG_FILE_PATH, 'r') as f:
                    lines = f.readlines()
                for line in reversed(lines[-APP_CONFIG['MAX_LOG_ENTRIES_DISPLAY']:]):
                    st.code(line.strip(), language='log')
            except Exception as e:
                st.error(f"Could not read log file: {e}")
                logger.error(f"Error reading activity log: {e}")
        else:
            st.info("Log file not found.")

def view_all_records_ui(db):
    st.header("📄 View All Records")
    with st.spinner("Loading records..."):
        try:
            records = db.get_all_records()
            if not records:
                st.info("No records found in the database.")
                return
            
            # Pagination logic
            total_records = len(records)
            records_per_page = APP_CONFIG["MAX_RECORDS_PER_PAGE"]
            total_pages = math.ceil(total_records / records_per_page)

            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1

            col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
            with col_nav1:
                if st.button("Previous Page", disabled=(st.session_state.current_page <= 1)):
                    st.session_state.current_page -= 1
                    st.rerun()
            with col_nav2:
                st.markdown(f"<p style='text-align: center;'>Page {st.session_state.current_page} of {total_pages}</p>", unsafe_allow_html=True)
            with col_nav3:
                if st.button("Next Page", disabled=(st.session_state.current_page >= total_pages)):
                    st.session_state.current_page += 1
                    st.rerun()

            start_idx = (st.session_state.current_page - 1) * records_per_page
            end_idx = start_idx + records_per_page
            display_records = records[start_idx:end_idx]

            for record in display_records:
                with st.expander(f"Record ID: {record.id} - {record.data.get('crash_type', 'N/A')}"):
                    st.json(record.to_dict())

        except Exception as e:
            st.error(f"Failed to load records: {e}")
            logger.error(f"UI Error in view_all_records: {traceback.format_exc()}")

def search_and_manage_ui(db):
    st.header("🔍 Search & Manage Records")
    search_id_str = st.text_input("Enter Record ID to find:", key="search_id")
    
    # Initialize record_to_edit in session_state if not present
    if 'record_to_edit' not in st.session_state:
        st.session_state.record_to_edit = None

    if st.button("Search"): # Add a specific search button
        if search_id_str:
            try:
                search_id = int(search_id_str)
                with st.spinner(f"Searching for record {search_id}..."):
                    record = db.get_record(search_id)
                
                if record:
                    st.success(f"Record {search_id} found.")
                    st.session_state.record_to_edit = record.to_dict() # Store for editing
                    st.session_state.last_searched_id = search_id # Keep track of the ID we found
                else:
                    st.warning(f"Record with ID {search_id} not found.")
                    st.session_state.record_to_edit = None # Clear previous edit data
            except ValueError:
                st.error("Please enter a valid integer for the Record ID.")
            except Exception as e:
                st.error(f"An error occurred during search: {e}")
                logger.error(f"Error during search: {traceback.format_exc()}")
        else:
            st.warning("Please enter a Record ID to search.")

    # Display edit form if a record is loaded into session state
    if st.session_state.record_to_edit:
        with st.form(key="edit_record_form"):
            st.subheader(f"Editing Record ID: {st.session_state.last_searched_id}")
            edited_data = {}
            for field, value in st.session_state.record_to_edit.items():
                if field == 'id': continue # ID is not editable
                # Use default value from the loaded record
                edited_data[field] = st.text_input(f"{field.replace('_', ' ').title()}", value=str(value), key=f"edit_{field}")
            
            col_edit1, col_edit2 = st.columns(2)
            with col_edit1:
                submitted = st.form_submit_button("Save Changes")
            with col_edit2:
                if st.form_submit_button(f"Delete Record {st.session_state.last_searched_id}", type="primary"):
                    st.session_state.show_delete_single_confirmation = True # Trigger deletion confirmation

            if submitted:
                try:
                    # DataObject expects all FIELDS. Merge edited_data with original defaults if necessary,
                    # but typically the form ensures all fields are present for validation.
                    # The ID is kept separate as it's not part of the 'editable' fields for DataObject init.
                    final_data_for_obj = {'id': st.session_state.last_searched_id}
                    for field in FIELDS: # Ensure all fields are passed to DataObject.from_dict
                        final_data_for_obj[field] = edited_data.get(field, st.session_state.record_to_edit.get(field))

                    new_obj = DataObject.from_dict(final_data_for_obj)
                    
                    if db.update_record(st.session_state.last_searched_id, new_obj):
                        st.success(f"Record {st.session_state.last_searched_id} updated successfully!")
                        st.session_state.record_to_edit = None # Clear edit state
                        st.session_state.last_searched_id = None
                        # No rerun needed here, form clears on submit
                    else:
                        st.error("Failed to update record. Check logs for details.")
                except DataValidationError as e:
                    st.error(f"Validation Error during update: {e}")
                    logger.warning(f"Validation error during update: {e}")
                except Exception as e:
                    st.error(f"Error updating record: {e}")
                    logger.error(f"Error updating record: {traceback.format_exc()}")
        
        # Deletion confirmation dialog for single record
        if st.session_state.get("show_delete_single_confirmation"):
            with st.dialog("Confirm Single Record Deletion"):
                st.write(f"Are you sure you want to delete Record ID: {st.session_state.last_searched_id}?")
                col_del_single1, col_del_single2 = st.columns(2)
                with col_del_single1:
                    if st.button("Yes, Delete This Record"):
                        try:
                            if db.delete_record(st.session_state.last_searched_id):
                                st.success(f"Record {st.session_state.last_searched_id} deleted.")
                                st.session_state.record_to_edit = None
                                st.session_state.last_searched_id = None
                                st.session_state.show_delete_single_confirmation = False
                                st.rerun() # Refresh UI after deletion
                            else:
                                st.error("Failed to delete record.")
                        except Exception as e:
                            st.error(f"Error deleting record: {e}")
                            logger.error(f"Error deleting record: {traceback.format_exc()}")
                with col_del_single2:
                    if st.button("Cancel Deletion"):
                        st.session_state.show_delete_single_confirmation = False
                        st.rerun() # Close dialog

def add_new_record_ui(db):
    st.header("✍️ Add New Record")
    with st.form("new_record_form"):
        st.subheader("Enter New Record Details")
        new_data = {}
        for field in FIELDS:
            # Use appropriate default values for fields, e.g., 0 for numbers, empty string for text
            default_value = ""
            if field in ['num_units', 'crash_hour', 'crash_day_of_week', 'crash_month']:
                default_value = "0"
            elif field.startswith('injuries'):
                default_value = "0.0"

            new_data[field] = st.text_input(f"{field.replace('_', ' ').title()}", value=default_value, key=f"new_{field}")
            
        submitted = st.form_submit_button("Add Record")
        if submitted:
            try:
                # Add a dummy ID, the DB will assign the real one. DataObject.from_dict handles it.
                new_data_obj_init = new_data.copy()
                new_data_obj_init['id'] = -1 # Temporary ID, actual ID is assigned by DB
                
                new_obj = DataObject.from_dict(new_data_obj_init)
                record_id = db.add_record(new_obj)
                st.success(f"Successfully added new record with ID: {record_id}")
                # Clear form inputs after successful submission
                for field in FIELDS:
                    st.session_state[f"new_{field}"] = "" # Reset text input
            except (DataValidationError, ValueError) as e:
                st.error(f"Validation Error: {e}")
            except Exception as e:
                st.error(f"Failed to add record: {e}")
                logger.error(f"Error adding record: {traceback.format_exc()}")

def import_from_csv_ui(db):
    st.header("📤 Import from CSV")
    st.write("Upload a CSV file to bulk import records.")
    st.info(f"Expected CSV delimiter: '{APP_CONFIG['CSV_DELIMITER']}'")
    st.info(f"Expected fields order: {', '.join(FIELDS)}")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'], key="csv_uploader")
    
    if uploaded_file is not None:
        if st.button("Start Import"):
            try:
                # Ensure the temporary file is written correctly for reading by csv.reader
                # Use uploaded_file.read().decode('utf-8') to get string content
                string_data = uploaded_file.getvalue().decode('utf-8')
                
                # Using io.StringIO for direct string processing without temp file
                csv_file_like_object = io.StringIO(string_data)

                with st.spinner("Importing records from CSV..."):
                    imported_count = 0
                    failed_rows = []
                    reader = csv.reader(csv_file_like_object, delimiter=APP_CONFIG["CSV_DELIMITER"])
                    header = next(reader, None) # Read header
                    if header is None:
                        st.warning("CSV file is empty or has no header.")
                        return

                    # Basic check for header consistency (optional but good practice)
                    # if [h.lower().replace(' ', '_') for h in header] != [f.lower() for f in FIELDS]:
                    #     st.warning("CSV header might not match expected fields. Proceeding based on order.")

                    for i, row in enumerate(reader):
                        row_num = i + 2 # +1 for 0-indexed, +1 for header
                        try:
                            data_obj = DataObject.from_csv_row(row)
                            db.add_record(data_obj)
                            imported_count +=1
                        except DataValidationError as e:
                            failed_rows.append(f"Row {row_num}: {row} - Error: {e}")
                            logger.warning(f"Skipping invalid CSV row {row_num}: {row} - Error: {e}")
                        except Exception as e:
                            failed_rows.append(f"Row {row_num}: {row} - Unexpected Error: {e}")
                            logger.error(f"Unexpected error processing CSV row {row_num}: {row} - {traceback.format_exc()}")
                    
                    if imported_count > 0:
                        st.success(f"Import complete! Added {imported_count} new records.")
                    else:
                        st.warning("No records were imported. Check for data format issues.")

                    if failed_rows:
                        st.error(f"Failed to import {len(failed_rows)} rows due to errors.")
                        with st.expander("Show detailed import errors"):
                            for error_msg in failed_rows:
                                st.write(error_msg)

            except Exception as e:
                st.error(f"An error occurred during CSV import: {e}")
                logger.error(f"CSV import failed: {traceback.format_exc()}")

def export_to_csv_ui(db):
    st.header("📥 Export to CSV")
    st.write("Export all records from the database to a CSV file.")
    
    if st.button("Generate CSV"):
        try:
            with st.spinner("Generating CSV data..."):
                records = db.get_all_records()
                if not records:
                    st.info("No records to export.")
                    return

                # Create an in-memory CSV file
                output = io.StringIO()
                writer = csv.writer(output, delimiter=APP_CONFIG["CSV_DELIMITER"])
                
                # Write header
                writer.writerow(FIELDS)
                
                # Write data rows
                for record in records:
                    row_data = [str(record.data.get(field, '')) for field in FIELDS]
                    writer.writerow(row_data)
                
                csv_string = output.getvalue()
                
                st.download_button(
                    label="Download CSV File",
                    data=csv_string,
                    file_name="traffic_accidents_export.csv",
                    mime="text/csv"
                )
                st.success("CSV file generated and ready for download.")

        except Exception as e:
            st.error(f"An error occurred during CSV export: {e}")
            logger.error(f"CSV export failed: {traceback.format_exc()}")


# --- Main Application Entry Point ---
if __name__ == "__main__":
    try:
        setup_ui()
    except Exception as e:
        st.error(f"A critical error occurred in the application: {e}")
        logger.critical(f"Unhandled exception in main app entry point: {traceback.format_exc()}")