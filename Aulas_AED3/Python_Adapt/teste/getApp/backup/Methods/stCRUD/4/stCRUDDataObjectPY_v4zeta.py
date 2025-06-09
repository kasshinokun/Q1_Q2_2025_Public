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
from typing import List, Dict, Optional, Union, Callable, Any, Iterator
import tempfile
import traceback

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
ID_COUNTER_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["ID_COUNTER_FILE_NAME"]) # Path for ID counter
BACKUP_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["BACKUP_DIR_NAME"])
LOG_FILE_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOG_FILE_NAME"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Data Structure ---
# record_id (unsigned long long - 8 bytes), timestamp (double), data_hash (32 bytes for hex hash), is_valid (boolean)
RECORD_FORMAT = "<Q d 32s ?"
RECORD_HEADER_SIZE = struct.calcsize(RECORD_FORMAT)

# --- Database Class (with modifications for auto-increment ID and direct file operations) ---
class TrafficAccidentsDB:
    def __init__(self, db_file: str, index_file: str, lock_file: str, id_counter_file: str):
        self.db_file = db_file
        self.index_file = index_file
        self.lock_file = lock_file
        self.id_counter_file = id_counter_file
        self._index_cache: Dict[int, int] = {} # In-memory cache for the index (ID -> Position)
        self._current_id = 0 # Auto-increment ID counter

        self._ensure_db_and_index_dirs()
        self._initialize_db_file()
        self._load_id_counter() # Load the last used ID
        self._load_index_to_cache() # Load index into memory on init

    def _ensure_db_and_index_dirs(self):
        """Ensures the database and index directories exist."""
        try:
            Path(self.db_file).parent.mkdir(parents=True, exist_ok=True)
            Path(self.index_file).parent.mkdir(parents=True, exist_ok=True)
            Path(self.id_counter_file).parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.critical(f"Critical: Cannot create database directories. Error: {e}")
            raise

    def _initialize_db_file(self):
        """Creates the database file if it doesn't exist."""
        if not Path(self.db_file).exists():
            try:
                with open(self.db_file, 'wb') as f:
                    pass  # Create an empty file
                logger.info(f"Database file created: {self.db_file}")
            except IOError as e:
                logger.critical(f"Critical: Cannot create database file {self.db_file}. Error: {e}")
                raise

    def _load_id_counter(self):
        """Loads the last used ID from the counter file."""
        if Path(self.id_counter_file).exists():
            try:
                with filelock.FileLock(self.lock_file, timeout=10):
                    with open(self.id_counter_file, 'r') as f:
                        self._current_id = int(f.read().strip())
                logger.info(f"ID counter loaded: {self._current_id}")
            except (IOError, ValueError) as e:
                logger.error(f"Error loading ID counter from {self.id_counter_file}: {e}. Resetting to 0.")
                self._current_id = 0
            except filelock.Timeout:
                logger.error(f"Could not acquire lock for ID counter file {self.lock_file} to load counter.")
                self._current_id = 0
        else:
            logger.info("ID counter file does not exist. Starting ID from 0.")
            self._current_id = 0
            self._save_id_counter() # Create file with initial 0

    def _save_id_counter(self):
        """Saves the current ID counter to the file."""
        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                with open(self.id_counter_file, 'w') as f:
                    f.write(str(self._current_id))
            logger.info(f"ID counter saved: {self._current_id}")
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for ID counter file {self.lock_file} to save counter.")
            raise
        except IOError as e:
            logger.error(f"Error saving ID counter to {self.id_counter_file}: {e}")
            raise

    def _get_next_id(self) -> int:
        """Increments and returns the next ID."""
        self._current_id += 1
        self._save_id_counter()
        return self._current_id

    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculates SHA256 hash of the data content."""
        data_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

    def _load_index_to_cache(self):
        """Loads the index file into the in-memory cache."""
        self._index_cache = {}
        if not Path(self.index_file).exists():
            logger.info("Index file does not exist. Starting with an empty index cache.")
            return

        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                with open(self.index_file, 'rb') as f_idx:
                    # ID (Q) + Position (Q)
                    entry_size = struct.calcsize("<Q Q") 
                    while True:
                        chunk = f_idx.read(entry_size)
                        if not chunk:
                            break
                        if len(chunk) == entry_size:
                            r_id, pos = struct.unpack("<Q Q", chunk)
                            self._index_cache[r_id] = pos
                        else:
                            logger.warning(f"Incomplete index entry found. Skipping remaining index file during load.")
                            break
            logger.info(f"Index loaded to cache. {len(self._index_cache)} entries.")
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for index file {self.lock_file} to load index cache.")
            self._index_cache = {}
            raise
        except Exception as e:
            logger.error(f"Error loading index file {self.index_file} to cache: {e}")
            self._index_cache = {}
            raise

    def _save_index_from_cache(self):
        """Saves the in-memory index cache to the index file."""
        logger.info("Saving index cache to disk...")
        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                with open(self.index_file, 'wb') as f_idx:
                    for r_id, pos in self._index_cache.items():
                        f_idx.write(struct.pack("<Q Q", r_id, pos))
            logger.info(f"Index cache saved to disk. {len(self._index_cache)} entries.")
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for index file {self.lock_file} to save index cache.")
            raise
        except Exception as e:
            logger.error(f"Error saving index cache to file {self.index_file}: {e}")
            raise

    def _update_index_cache_entry(self, record_id: int, position: int):
        """Updates a single entry in the in-memory index cache and saves it to disk."""
        self._index_cache[record_id] = position
        self._save_index_from_cache()

    def rebuild_index(self):
        """
        Rebuilds the index file from scratch, including only valid records.
        This updates the in-memory cache and then persists it to disk.
        """
        logger.info("Rebuilding index file from DB and updating cache...")
        new_index_data = {}
        max_id_in_db = 0 # Track max ID for counter update
        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                with open(self.db_file, 'rb') as f_db:
                    f_db.seek(0, os.SEEK_END)
                    file_size = f_db.tell()
                    f_db.seek(0, os.SEEK_SET)
                    
                    while f_db.tell() < file_size:
                        start_pos = f_db.tell()
                        header_bytes = f_db.read(RECORD_HEADER_SIZE)
                        if not header_bytes:
                            break

                        if len(header_bytes) < RECORD_HEADER_SIZE:
                            logger.warning(f"Incomplete header at position {start_pos}. Skipping remaining file during index rebuild.")
                            break

                        try:
                            record_id, timestamp_float, data_hash_bytes, is_valid = struct.unpack(RECORD_FORMAT, header_bytes)
                        except struct.error:
                            logger.error(f"Failed to unpack header at position {start_pos}. Corrupted header. Skipping.")
                            # Heuristic: try to skip to next potential record
                            f_db.seek(4 + 1024, os.SEEK_CUR)
                            continue

                        data_size_bytes = f_db.read(4)
                        if len(data_size_bytes) < 4:
                            logger.warning(f"Incomplete data size at position {f_db.tell()}. Skipping remaining file during index rebuild.")
                            break
                        
                        try:
                            data_size = struct.unpack("<I", data_size_bytes)[0]
                        except struct.error:
                            logger.error(f"Failed to unpack data size at position {f_db.tell()}. Corrupted data size. Skipping.")
                            f_db.seek(1024, os.SEEK_CUR)
                            continue

                        f_db.seek(data_size, os.SEEK_CUR) 

                        if is_valid:
                            new_index_data[record_id] = start_pos
                            if record_id > max_id_in_db:
                                max_id_in_db = record_id
                
                self._index_cache = new_index_data
                self._save_index_from_cache()

                # Update ID counter if rebuilt index has a higher max ID
                if max_id_in_db >= self._current_id:
                    self._current_id = max_id_in_db + 1
                    self._save_id_counter()

            logger.info("Index file rebuilt and cache updated successfully.")
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to rebuild index.")
            raise
        except Exception as e:
            logger.error(f"Error rebuilding index: {traceback.format_exc()}")
            raise

    def get_record_position_from_index(self, record_id: int) -> Optional[int]:
        """Retrieves the position of a record from the in-memory index cache."""
        return self._index_cache.get(record_id)

    def _insert_record(self, record_data: Dict[str, Any], record_id: Optional[int] = None, is_valid: bool = True) -> (int, int):
        """
        Internal method to insert a record into the .db file.
        If record_id is None, a new auto-increment ID is generated.
        Returns a tuple of (record_id, position_in_db).
        """
        if record_id is None:
            record_id = self._get_next_id()
        
        timestamp = datetime.now().timestamp()
        data_hash = self._calculate_data_hash(record_data)
        data_bytes = json.dumps(record_data).encode('utf-8')
        data_size = len(data_bytes)

        record_header = struct.pack(
            RECORD_FORMAT,
            record_id,
            timestamp,
            bytes.fromhex(data_hash),
            is_valid
        )

        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                with open(self.db_file, 'ab') as f:
                    current_position = f.tell()
                    f.write(record_header)
                    f.write(struct.pack("<I", data_size))
                    f.write(data_bytes)
            
            logger.info(f"Record {record_id} inserted at position {current_position}.")
            return record_id, current_position
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to insert record.")
            raise
        except IOError as e:
            logger.error(f"IOError inserting record: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inserting record: {traceback.format_exc()}")
            raise

    def insert_data(self, data: Dict[str, Any]) -> int:
        """Public method to insert new accident data."""
        record_id, position = self._insert_record(data, is_valid=True)
        self._update_index_cache_entry(record_id, position)
        return record_id

    def _read_record_at_position(self, position: int) -> Optional[Dict[str, Any]]:
        """Reads a single record from a specific byte position."""
        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                with open(self.db_file, 'rb') as f:
                    f.seek(position)
                    header_bytes = f.read(RECORD_HEADER_SIZE)
                    if not header_bytes or len(header_bytes) < RECORD_HEADER_SIZE:
                        logger.warning(f"Incomplete header at position {position}.")
                        return None
                    
                    record_id, timestamp_float, data_hash_bytes, is_valid = struct.unpack(RECORD_FORMAT, header_bytes)
                    
                    data_size_bytes = f.read(4)
                    if not data_size_bytes or len(data_size_bytes) < 4:
                        logger.warning(f"Incomplete data size at position {f.tell()}.")
                        return None
                    data_size = struct.unpack("<I", data_size_bytes)[0]

                    data_bytes = f.read(data_size)
                    if not data_bytes or len(data_bytes) < data_size:
                        logger.warning(f"Incomplete data at position {f.tell()}. Expected {data_size} bytes, got {len(data_bytes)}.")
                        return None

                    data = json.loads(data_bytes.decode('utf-8'))
                    timestamp = datetime.fromtimestamp(timestamp_float)
                    data_hash = data_hash_bytes.hex()

                    return {
                        "record_id": record_id,
                        "timestamp": timestamp,
                        "data_hash": data_hash,
                        "is_valid": is_valid,
                        "data": data,
                        "position": position
                    }
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to read record at position {position}.")
            return None
        except (IOError, struct.error, json.JSONDecodeError) as e:
            logger.error(f"Data corruption or read error at position {position}: {e}. Record might be unreadable.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading record at position {position}: {traceback.format_exc()}")
            return None

    def get_record_by_id(self, record_id: int, use_index: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single record by its ID.
        If use_index is True (default), uses the index.
        If use_index is False, scans the file directly to find the record (slower).
        """
        if use_index:
            position = self.get_record_position_from_index(record_id)
            if position is None:
                logger.debug(f"Record {record_id} not found in index cache.")
                return None
            
            record = self._read_record_at_position(position)
            if record and record['is_valid'] and record['record_id'] == record_id:
                logger.debug(f"Record {record_id} found via index at position {position}.")
                return record
            elif record and not record['is_valid']:
                logger.info(f"Record {record_id} found in index at position {position} but is marked as invalid.")
            elif record and record['record_id'] != record_id:
                logger.warning(f"Index for {record_id} points to a record with a different ID ({record['record_id']}) at position {position}. Index might be corrupted or outdated.")
            else:
                logger.warning(f"Record {record_id} not found at indexed position {position} or read failed from DB file.")
            
            return None
        else: # Direct file scan (slower, for debug/specific cases)
            logger.info(f"Searching for record ID {record_id} by direct file scan (no index).")
            for record in self.get_all_records(include_invalid=False):
                if record['record_id'] == record_id:
                    logger.info(f"Record {record_id} found by direct file scan at position {record['position']}.")
                    return record
            logger.info(f"Record {record_id} not found by direct file scan.")
            return None

    def get_all_records(self, include_invalid: bool = False) -> Iterator[Dict[str, Any]]:
        """Yields all records from the database, optionally including invalid ones."""
        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                with open(self.db_file, 'rb') as f:
                    f.seek(0, os.SEEK_END)
                    file_size = f.tell()
                    f.seek(0, os.SEEK_SET)

                    while f.tell() < file_size:
                        start_pos = f.tell()
                        header_bytes = f.read(RECORD_HEADER_SIZE)
                        if not header_bytes:
                            break

                        if len(header_bytes) < RECORD_HEADER_SIZE:
                            logger.warning(f"Incomplete header at position {start_pos}. Skipping remaining file.")
                            break

                        try:
                            record_id, timestamp_float, data_hash_bytes, is_valid = struct.unpack(RECORD_FORMAT, header_bytes)
                        except struct.error:
                            logger.error(f"Failed to unpack header at position {start_pos}. Corrupted header. Skipping record.")
                            f.seek(4 + 1024, os.SEEK_CUR)
                            continue
                        
                        data_size_bytes = f.read(4)
                        if not data_size_bytes or len(data_size_bytes) < 4:
                            logger.warning(f"Incomplete data size at position {f.tell()}. Skipping remaining file.")
                            break
                        
                        try:
                            data_size = struct.unpack("<I", data_size_bytes)[0]
                        except struct.error:
                            logger.error(f"Failed to unpack data size at position {f.tell()}. Corrupted data size. Skipping record.")
                            f.seek(1024, os.SEEK_CUR)
                            continue

                        data_bytes = f.read(data_size)
                        if len(data_bytes) < data_size:
                            logger.warning(f"Incomplete data at position {f.tell()}. Expected {data_size} bytes, got {len(data_bytes)}. Skipping record.")
                            break

                        try:
                            data = json.loads(data_bytes.decode('utf-8'))
                        except json.JSONDecodeError:
                            logger.error(f"JSON decode error at position {start_pos}. Skipping record.")
                            continue

                        timestamp = datetime.fromtimestamp(timestamp_float)
                        data_hash = data_hash_bytes.hex()

                        if is_valid or include_invalid:
                            yield {
                                "record_id": record_id,
                                "timestamp": timestamp,
                                "data_hash": data_hash,
                                "is_valid": is_valid,
                                "data": data,
                                "position": start_pos
                            }
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to read all records.")
            return
        except Exception as e:
            logger.error(f"Error reading all records: {traceback.format_exc()}")
            return

    def update_record(self, record_id: int, new_data: Dict[str, Any], use_index: bool = True) -> bool:
        """
        Updates an existing record.
        If use_index is True (default), tries to use the index to find the old record's position.
        If use_index is False, scans the file to find the record (slower).
        The old record is marked as invalid, and a new one is inserted.
        """
        old_record: Optional[Dict[str, Any]] = None
        old_position: Optional[int] = None

        if use_index:
            old_record = self.get_record_by_id(record_id, use_index=True)
            if old_record:
                old_position = old_record['position']
        else:
            # Full file scan to find the record
            for rec in self.get_all_records(include_invalid=False):
                if rec['record_id'] == record_id:
                    old_record = rec
                    old_position = rec['position']
                    break
        
        if not old_record or not old_record['is_valid']:
            st.error(f"Registro com ID `{record_id}` não encontrado ou é inválido para atualização. Certifique-se de que o ID é válido e existe.")
            logger.warning(f"Attempted to update non-existent or invalid record {record_id}")
            return False

        if old_record['data'] == new_data:
            st.info(f"Nenhuma alteração detectada para o registro ID `{record_id}`.")
            logger.info(f"Update called for record {record_id} but data is identical.")
            return True

        # Mark the old record as invalid
        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                with open(self.db_file, 'r+b') as f:
                    f.seek(old_position)
                    
                    original_header_bytes = f.read(RECORD_HEADER_SIZE)
                    if len(original_header_bytes) < RECORD_HEADER_SIZE:
                        logger.error(f"Failed to read complete header for update at position {old_position}.")
                        return False
                    
                    # Unpack everything except is_valid
                    old_rec_id, timestamp_float, data_hash_bytes, _ = struct.unpack(RECORD_FORMAT, original_header_bytes)
                    
                    updated_header = struct.pack(
                        RECORD_FORMAT,
                        old_rec_id, # Keep the original ID
                        timestamp_float,
                        data_hash_bytes,
                        False # Mark as invalid
                    )
                    
                    f.seek(old_position)
                    f.write(updated_header)
            logger.info(f"Record {record_id} at position {old_position} marked as invalid.")

            # Insert the new record with the updated data, using the SAME ID
            new_record_id, new_position = self._insert_record(new_data, record_id=record_id, is_valid=True)
            
            # Update the in-memory index cache and persist for the SAME record_id
            self._update_index_cache_entry(new_record_id, new_position)
            logger.info(f"Index for record ID {new_record_id} updated to new position {new_position}.")

            st.success(f"Registro `{record_id}` atualizado com sucesso.")
            return True

        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to update record.")
            return False
        except (IOError, struct.error) as e:
            logger.error(f"IOError or struct error updating record {record_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {traceback.format_exc()}")
            return False

    def delete_record(self, record_id: int, use_index: bool = True) -> bool:
        """
        Deletes a record by marking it as invalid.
        Then, rebuilds the index to remove the invalid record's entry.
        """
        record_to_delete: Optional[Dict[str, Any]] = None
        delete_position: Optional[int] = None

        if use_index:
            record_to_delete = self.get_record_by_id(record_id, use_index=True)
            if record_to_delete:
                delete_position = record_to_delete['position']
        else:
            # Full file scan to find the record
            for rec in self.get_all_records(include_invalid=False):
                if rec['record_id'] == record_id:
                    record_to_delete = rec
                    delete_position = rec['position']
                    break

        if not record_to_delete or not record_to_delete['is_valid']:
            st.error(f"Registro com ID `{record_id}` não encontrado ou já inválido para exclusão. Certifique-se de que o ID é válido e existe.")
            logger.warning(f"Attempted to delete non-existent or invalid record {record_id}")
            return False

        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                with open(self.db_file, 'r+b') as f:
                    f.seek(delete_position)
                    
                    original_header_bytes = f.read(RECORD_HEADER_SIZE)
                    if len(original_header_bytes) < RECORD_HEADER_SIZE:
                        logger.error(f"Failed to read complete header for deletion at position {delete_position}.")
                        return False
                    
                    old_rec_id, timestamp_float, data_hash_bytes, _ = struct.unpack(RECORD_FORMAT, original_header_bytes)
                    
                    updated_header = struct.pack(
                        RECORD_FORMAT,
                        old_rec_id,
                        timestamp_float,
                        data_hash_bytes,
                        False # Mark as invalid
                    )
                    
                    f.seek(delete_position)
                    f.write(updated_header)
            logger.info(f"Record {record_id} at position {delete_position} marked as invalid.")
            st.success(f"Registro `{record_id}` marcado como excluído com sucesso.")

            # Rebuild index after deletion - this will remove the invalid record_id from the index cache and file.
            self.rebuild_index()
            return True

        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to delete record.")
            return False
        except (IOError, struct.error) as e:
            logger.error(f"IOError or struct error deleting record {record_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {traceback.format_exc()}")
            return False

    def get_number_of_records(self) -> int:
        """Returns the total number of valid records in the database based on the index cache."""
        return len(self._index_cache)

    def search_records(self, query: str, use_index: bool = True) -> List[Dict[str, Any]]:
        """
        Searches for records where any string value in the data contains the query.
        If use_index is True (default), it fetches valid records using index and then filters.
        If use_index is False, it scans the entire file.
        Case-insensitive search.
        """
        results = []
        try:
            records_iterator: Iterator[Dict[str, Any]]
            if use_index:
                # Iterate through all valid records via index (more efficient than full file scan)
                # First get all IDs from index, then read records by ID
                indexed_records = []
                for record_id_from_index in self._index_cache.keys():
                    rec = self.get_record_by_id(record_id_from_index, use_index=True)
                    if rec and rec['is_valid']:
                        indexed_records.append(rec)
                records_iterator = iter(indexed_records)
            else:
                # Direct file scan
                records_iterator = self.get_all_records(include_invalid=False)

            for record in records_iterator:
                found = False
                for key, value in record['data'].items():
                    if isinstance(value, str) and query.lower() in value.lower():
                        found = True
                        break
                    elif isinstance(value, (int, float)) and query.lower() in str(value).lower():
                        found = True
                        break
                
                if found:
                    results.append(record)
        except Exception as e:
            logger.error(f"Error during search: {e}")
        return results

    def import_from_csv(self, file_path: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> int:
        """Imports data from a CSV file into the database with progress feedback."""
        imported_count = 0
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > APP_CONFIG["MAX_FILE_SIZE_MB"]:
                st.error(f"O tamanho do arquivo excede o máximo permitido ({APP_CONFIG['MAX_FILE_SIZE_MB']}MB).")
                logger.warning(f"Import failed: File {file_path} too large.")
                return 0

            with open(file_path, 'r', encoding='utf-8') as csvfile:
                # Read first line to get headers and then rewind for DictReader
                header = csvfile.readline()
                csvfile.seek(0)
                # Count total lines for progress bar (estimate)
                total_lines = sum(1 for _ in csvfile) - 1 # Subtract 1 for header
                csvfile.seek(0) # Rewind for DictReader
                if total_lines < 0: total_lines = 0

            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=APP_CONFIG["CSV_DELIMITER"])
                for i, row in enumerate(reader):
                    if progress_callback:
                        progress_callback(i + 1, total_lines)

                    # Clean keys and convert values based on expected types for new fields
                    cleaned_row = {k.strip().replace('\ufeff', ''): v for k, v in row.items()}
                    
                    processed_row = {}
                    for key, value in cleaned_row.items():
                        # Type conversions for new fields based on teste.py inputs
                        if key == 'crash_date' and value:
                            try:
                                processed_row[key] = datetime.strptime(value, '%Y-%m-%d').date().isoformat()
                            except ValueError:
                                logger.warning(f"Could not parse date '{value}' for field '{key}' in row {i+2}. Keeping as string.")
                                processed_row[key] = value
                        elif key in [
                            'num_units', 'crash_hour', 'crash_day_of_week', 'crash_month',
                            'injuries_total', 'injuries_fatal', 'injuries_incapacitating',
                            'injuries_non_incapacitating', 'injuries_reported_not_evident', 'injuries_no_indication'
                        ] and value:
                            try:
                                # Convert to float for injury counts as per teste.py, int for others
                                if key.startswith('injuries_'):
                                    processed_row[key] = float(value)
                                else:
                                    processed_row[key] = int(value)
                            except ValueError:
                                processed_row[key] = value # Keep as string if conversion fails
                        elif key == 'intersection_related_i':
                            processed_row[key] = value.upper() if value else 'NO' # Normalize to 'YES'/'NO'
                        else:
                            processed_row[key] = value

                    record_id, position = self._insert_record(processed_row)
                    self._update_index_cache_entry(record_id, position)
                    imported_count += 1
            logger.info(f"Successfully imported {imported_count} records from {file_path}.")
            st.success(f"Importados {imported_count} registros com sucesso.")
        except FileNotFoundError:
            st.error(f"Arquivo CSV não encontrado em {file_path}")
            logger.error(f"CSV import failed: File not found {file_path}")
        except Exception as e:
            st.error(f"Ocorreu um erro durante a importação CSV: {e}")
            logger.error(f"Error during CSV import from {file_path}: {traceback.format_exc()}")
        return imported_count

    def export_to_csv(self, output_file: str) -> bool:
        """Exports all valid records to a CSV file."""
        try:
            records = list(self.get_all_records(include_invalid=False)) 
            if not records:
                st.info("Nenhum registro para exportar.")
                return False

            all_keys = set()
            for record in records:
                all_keys.update(record['data'].keys())
            
            fieldnames = sorted(list(all_keys)) # Ensure consistent order

            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=APP_CONFIG["CSV_DELIMITER"])
                writer.writeheader()
                for record in records:
                    writer.writerow(record['data'])
            logger.info(f"Successfully exported {len(records)} records to {output_file}.")
            st.success(f"Exportados {len(records)} registros para `{output_file}` com sucesso.")
            return True
        except Exception as e:
            st.error(f"Ocorreu um erro durante a exportação CSV: {e}")
            logger.error(f"Error during CSV export to {output_file}: {traceback.format_exc()}")
            return False

    def create_backup(self) -> Optional[str]:
        """Creates a timestamped backup of the database file and index file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_db_file = os.path.join(BACKUP_PATH, f"traffic_accidents_backup_{timestamp}.db")
            backup_index_file = os.path.join(BACKUP_PATH, f"index_backup_{timestamp}.idx")
            backup_id_counter_file = os.path.join(BACKUP_PATH, f"id_counter_backup_{timestamp}.dat")
            
            with filelock.FileLock(self.lock_file, timeout=10):
                Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
                
                with open(self.db_file, 'rb') as src, open(backup_db_file, 'wb') as dst:
                    while True:
                        chunk = src.read(APP_CONFIG["CHUNK_SIZE"])
                        if not chunk:
                            break
                        dst.write(chunk)
                
                if Path(self.index_file).exists():
                    with open(self.index_file, 'rb') as src_idx, open(backup_index_file, 'wb') as dst_idx:
                        while True:
                            chunk = src_idx.read(APP_CONFIG["CHUNK_SIZE"])
                            if not chunk:
                                break
                            dst_idx.write(chunk)
                else:
                    logger.warning(f"Index file {self.index_file} not found for backup.")
                
                if Path(self.id_counter_file).exists():
                    with open(self.id_counter_file, 'rb') as src_id_c, open(backup_id_counter_file, 'wb') as dst_id_c:
                        while True:
                            chunk = src_id_c.read(APP_CONFIG["CHUNK_SIZE"])
                            if not chunk:
                                break
                            dst_id_c.write(chunk)
                else:
                    logger.warning(f"ID counter file {self.id_counter_file} not found for backup.")

            logger.info(f"Database, index, and ID counter backed up to {backup_db_file}, {backup_index_file}, {backup_id_counter_file}")
            self._manage_backups()
            return backup_db_file
        except filelock.Timeout:
            st.error(f"Não foi possível adquirir o bloqueio para o arquivo do banco de dados {self.lock_file} para criar o backup.")
            logger.error(f"Backup failed: Lock timeout.")
            return None
        except Exception as e:
            st.error(f"Erro ao criar backup: {e}")
            logger.error(f"Error creating backup: {traceback.format_exc()}")
            return None

    def _manage_backups(self):
        """Deletes old backups, keeping only the most recent N."""
        try:
            backups = sorted(
                [f for f in os.listdir(BACKUP_PATH) if f.startswith('traffic_accidents_backup_') and f.endswith('.db')],
                key=lambda f: os.path.getmtime(os.path.join(BACKUP_PATH, f)),
                reverse=True
            )
            
            for i in range(APP_CONFIG["MAX_BACKUPS"], len(backups)):
                old_db_backup = os.path.join(BACKUP_PATH, backups[i])
                os.remove(old_db_backup)
                logger.info(f"Deleted old database backup: {old_db_backup}")
                
                base_name_db = os.path.basename(old_db_backup)
                timestamp_part = base_name_db.replace('traffic_accidents_backup_', '').replace('.db', '')

                old_index_backup = os.path.join(BACKUP_PATH, f"index_backup_{timestamp_part}.idx")
                if Path(old_index_backup).exists():
                    os.remove(old_index_backup)
                    logger.info(f"Deleted old index backup: {old_index_backup}")

                old_id_counter_backup = os.path.join(BACKUP_PATH, f"id_counter_backup_{timestamp_part}.dat")
                if Path(old_id_counter_backup).exists():
                    os.remove(old_id_counter_backup)
                    logger.info(f"Deleted old ID counter backup: {old_id_counter_backup}")

        except Exception as e:
            logger.error(f"Error managing backups: {traceback.format_exc()}")

    def delete_all_data(self):
        """Deletes the main database file, index file, and ID counter file."""
        try:
            with filelock.FileLock(self.lock_file, timeout=10):
                if Path(self.db_file).exists():
                    os.remove(self.db_file)
                    logger.info(f"Database file deleted: {self.db_file}")
                if Path(self.index_file).exists():
                    os.remove(self.index_file)
                    logger.info(f"Index file deleted: {self.index_file}")
                if Path(self.id_counter_file).exists():
                    os.remove(self.id_counter_file)
                    logger.info(f"ID counter file deleted: {self.id_counter_file}")
                
                # Reset in-memory state
                self._index_cache = {}
                self._current_id = 0
                
                st.success("✔️ Todos os dados (banco de dados, índice, contador de IDs) foram excluídos.")
                logger.info("All database files, index, and ID counter deleted.")
        except filelock.Timeout:
            st.error("Não foi possível adquirir o bloqueio para excluir os arquivos do banco de dados. Tente novamente.")
            logger.error(f"Failed to acquire lock for deleting all data files: {self.lock_file}")
        except Exception as e:
            st.error(f"Erro ao excluir todos os dados: {e}")
            logger.error(f"Error deleting all data: {traceback.format_exc()}")

# --- Streamlit UI Setup ---
def setup_ui():
    """Sets up the Streamlit user interface."""
    st.set_page_config(page_title="Sistema de Gestão de Dados de Acidentes de Trânsito", layout="wide")
    st.title("Sistema de Gestão de Dados de Acidentes de Trânsito")

    # --- Custom CSS for old UI look and feel (emojis as icons) ---
    st.markdown(
        """
        <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.1em;
            font-weight: bold;
        }

        /* General button styling */
        .stButton button {
            background-color: #4CAF50; /* Green */
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 8px;
            border: none;
            transition-duration: 0.4s;
        }

        .stButton button:hover {
            background-color: #45a049;
            color: white;
        }

        /* Specific styles for Delete/Cancel buttons */
        .stButton button[kind="secondary"] { /* Streamlit's secondary button often has a different look */
             background-color: #f44336; /* Red */
        }
        .stButton button[kind="secondary"]:hover {
             background-color: #da190b;
        }

        /* Styles for expander headers to make them stand out */
        .streamlit-expanderHeader {
            background-color: #f0f2f6; /* Light grey background */
            border-left: 5px solid #264A72; /* Blue border on the left */
            padding: 10px;
            font-weight: bold;
            color: #264A72;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .streamlit-expanderHeader p {
            font-size: 1.1em !important;
            font-weight: bold !important;
        }

        /* Columns layout adjustment (optional, Streamlit handles columns well by default) */
        .st-emotion-cache-nahz7x { /* Target Streamlit's column container div for spacing */
            gap: 1rem; /* Adjust gap between columns */
        }

        /* Info/Success/Error boxes styling */
        .stAlert {
            border-radius: 8px;
            padding: 10px 15px;
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Initialize DB (only once)
    if 'db' not in st.session_state:
        st.session_state.db = TrafficAccidentsDB(DB_PATH, INDEX_PATH, LOCK_PATH, ID_COUNTER_PATH)
    db = st.session_state.db

    # Initialize cache for all records for paginated view
    if 'all_records_cache' not in st.session_state:
        st.session_state.all_records_cache = []
        st.session_state.records_dirty = True # Flag to indicate if cache needs refresh

    # --- Sidebar for Mode Selection ---
    with st.sidebar:
        st.header("⚙️ Modo de Operação")
        operation_mode = st.selectbox(
            "Selecione o modo de operação:",
            ("Operar via Índice (Recomendado)", "Operar Diretamente no Arquivo"),
            key="operation_mode_selector"
        )
        st.session_state.use_index_for_crud = (operation_mode == "Operar via Índice (Recomendado)")
        st.info(f"Modo atual: **{operation_mode}**")

    # Tabs for navigation
    tab_insert, tab_view, tab_search, tab_import_export, tab_admin = st.tabs([
        "➕ Inserir Registro", "👁️ Visualizar Registros", "🔍 Buscar Registros", "📥📤 Importar/Exportar", "⚙️ Administração"
    ])

    with tab_insert:
        st.header("➕ Inserir Novo Registro")
        with st.form("insert_form", clear_on_submit=True): # Add clear_on_submit
            st.subheader("Detalhes Essenciais do Acidente (*)")
            cols_req = st.columns(2)
            
            with cols_req[0]:
                crash_date = st.date_input(
                    "Data do Acidente*",
                    value=date.today(),
                    help="Data em que o acidente ocorreu (AAAA-MM-DD)",
                    key="add_crash_date_insert" # Unique key for insert form
                )
            with cols_req[1]:
                crash_type = st.text_input(
                    "Tipo de Acidente*",
                    help="Tipo principal de colisão (ex: Colisão Traseira, Frontal, Lateral, Capotamento)",
                    key="add_crash_type_insert"
                )
            
            cols_units_inj = st.columns(2)
            with cols_units_inj[0]:
                num_units = st.number_input(
                    "Unidades Envolvidas*",
                    min_value=0,
                    max_value=999,
                    value=1,
                    step=1,
                    help="Número total de veículos/unidades envolvidos no acidente.",
                    key="add_num_units_insert"
                )
            with cols_units_inj[1]:
                injuries_total = st.number_input(
                    "Total de Lesões*",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    help="Contagem total de todas as lesões (fatais, incapacitantes, etc.).",
                    key="add_injuries_total_insert"
                )
            
            st.markdown("---") # Separator for better readability

            st.subheader("Informações Adicionais do Acidente")
            cols_cond = st.columns(3)
            with cols_cond[0]:
                traffic_control_device = st.selectbox(
                    "Dispositivo de Controle de Tráfego",
                    ["NO CONTROL DEVICE", "TRAFFIC SIGNAL", "STOP SIGN/FLASHER", "UNKNOWN", "OTHER", "SCHOOL CROSSING GUARD", "RAILROAD CROSSING GATE"],
                    index=0, # Default to "NO CONTROL DEVICE"
                    key="add_traffic_control_device_insert"
                )
            with cols_cond[1]:
                weather_condition = st.selectbox(
                    "Condição Climática",
                    ["CLEAR", "RAIN", "CLOUDY/OVERCAST", "SNOW", "FOG/SMOKE/HAZE", "FREEZING RAIN/DRIZZLE", "SLEET/HAIL", "BLOWING SNOW"],
                    index=0, # Default to "CLEAR"
                    key="add_weather_condition_insert"
                )
            with cols_cond[2]:
                lighting_condition = st.selectbox(
                    "Condição de Iluminação",
                    ["DAYLIGHT", "DARKNESS, LIGHTED ROAD", "DARKNESS, UNLIGHTED ROAD", "DAWN", "DUSK"],
                    index=0, # Default to "DAYLIGHT"
                    key="add_lighting_condition_insert"
                )

            st.markdown("---")

            st.subheader("Detalhes da Primeira Colisão e Condições da Via")
            cols_crash_road = st.columns(2)
            with cols_crash_road[0]:
                first_crash_type = st.text_input(
                    "Primeiro Tipo de Colisão",
                    help="Tipo de colisão que iniciou o acidente (ex: ANGLE, REAR END, SIDESWIPE SAME DIRECTION)",
                    key="add_first_crash_type_insert"
                )
            with cols_crash_road[1]:
                roadway_surface_cond = st.selectbox(
                    "Condição da Superfície da Via",
                    ["DRY", "WET", "SNOW OR SLUSH", "ICE", "SAND, MUD, DIRT", "OIL", "WATER (STANDING/MOVING)"],
                    index=0, # Default to "DRY"
                    key="add_roadway_surface_cond_insert"
                )
                road_defect = st.selectbox(
                    "Defeito na Via",
                    ["NO DEFECTS", "RUT, HOLES", "SHOULDER DEFECTS", "WORN SURFACE", "DEBRIS ON ROADWAY"],
                    index=0, # Default to "NO DEFECTS"
                    key="add_road_defect_insert"
                )
            
            st.markdown("---")

            st.subheader("Causa Contributiva Primária e Lesões")
            prim_contributory_cause = st.text_input(
                "Causa Contributiva Primária",
                help="Fator primário que contribuiu para o acidente (ex: FALHA DO MOTORISTA, ALTA VELOCIDADE)",
                key="add_prim_contributory_cause_insert"
            )
            most_severe_injury = st.selectbox(
                "Lesão Mais Grave",
                ["NO INDICATION OF INJURY", "NON-INCAPACITATING INJURY", "REPORTED, NOT EVIDENT", "FATAL", "INCAPACITATING INJURY"],
                index=0,
                key="add_most_severe_injury_insert"
            )

            inj_cols = st.columns(3)
            with inj_cols[0]:
                injuries_fatal = st.number_input("Lesões Fatais", min_value=0.0, value=0.0, step=0.1, key="add_injuries_fatal_insert")
                injuries_incapacitating = st.number_input("Lesões Incapacitantes", min_value=0.0, value=0.0, step=0.1, key="add_injuries_incapacitating_insert")
            with inj_cols[1]:
                injuries_non_incapacitating = st.number_input("Lesões Não Incapacitantes", min_value=0.0, value=0.0, step=0.1, key="add_injuries_non_incapacitating_insert")
                injuries_reported_not_evident = st.number_input("Lesões Reportadas Não Evidentes", min_value=0.0, value=0.0, step=0.1, key="add_injuries_reported_not_evident_insert")
            with inj_cols[2]:
                injuries_no_indication = st.number_input("Sem Indicação de Lesão", min_value=0.0, value=0.0, step=0.1, key="add_injuries_no_indication_insert")
            
            st.markdown("---")

            st.subheader("Detalhes Temporais e Cruzamento")
            temp_cols = st.columns(3)
            with temp_cols[0]:
                crash_hour = st.number_input("Hora do Acidente (0-23)", min_value=0, max_value=23, value=datetime.now().hour, step=1, key="add_crash_hour_insert")
            with temp_cols[1]:
                crash_day_of_week = st.number_input("Dia da Semana (1=Dom, 7=Sáb)", min_value=1, max_value=7, value=datetime.now().isoweekday(), step=1, key="add_crash_day_of_week_insert")
            with temp_cols[2]:
                crash_month = st.number_input("Mês (1-12)", min_value=1, max_value=12, value=datetime.now().month, step=1, key="add_crash_month_insert")
            
            intersection_related_i = st.selectbox(
                "Relacionado a Cruzamento?",
                ["NO", "YES", "NOT APPLICABLE"],
                index=0,
                key="add_intersection_related_i_insert"
            )

            st.markdown("---")
            col_insert_btn, col_spacer = st.columns([0.2, 0.8])
            with col_insert_btn:
                submitted = st.form_submit_button("Inserir Registro")
            
            if submitted:
                record_data = {
                    "crash_date": crash_date.isoformat(),
                    "crash_type": crash_type,
                    "num_units": num_units,
                    "injuries_total": injuries_total,
                    "traffic_control_device": traffic_control_device,
                    "weather_condition": weather_condition,
                    "lighting_condition": lighting_condition,
                    "first_crash_type": first_crash_type,
                    "roadway_surface_cond": roadway_surface_cond,
                    "road_defect": road_defect,
                    "prim_contributory_cause": prim_contributory_cause,
                    "most_severe_injury": most_severe_injury,
                    "injuries_fatal": injuries_fatal,
                    "injuries_incapacitating": injuries_incapacitating,
                    "injuries_non_incapacitating": injuries_non_incapacitating,
                    "injuries_reported_not_evident": injuries_reported_not_evident,
                    "injuries_no_indication": injuries_no_indication,
                    "crash_hour": crash_hour,
                    "crash_day_of_week": crash_day_of_week,
                    "crash_month": crash_month,
                    "intersection_related_i": intersection_related_i,
                }
                try:
                    # Basic validation for required fields
                    if not crash_date or not crash_type or not num_units or injuries_total is None:
                        st.error("Campos marcados com (*) são obrigatórios.")
                    else:
                        record_id = db.insert_data(record_data)
                        st.success(f"Registro inserido com sucesso! ID do Registro: `{record_id}`")
                        logger.info(f"New record inserted via UI: {record_id}")
                        st.session_state.records_dirty = True
                except Exception as e:
                    st.error(f"Erro ao inserir registro: {e}")
                    logger.error(f"UI insert error: {traceback.format_exc()}")

    # Helper function to display record details - MODIFIED
    def display_record_details(record: Dict[str, Any]):
        data_obj = record['data'] # Access the 'data' dictionary directly

        # General Record Metadata (top section)
        st.markdown(f"**ID do Registro:** `{record['record_id']}`")
        st.markdown(f"**Timestamp de Criação/Atualização:** {record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown(f"**Hash dos Dados (Checksum):** `{record['data_hash']}`")
        st.markdown(f"**Válido:** {'Sim' if record['is_valid'] else 'Não'}")
        st.markdown(f"**Posição no DB (Byte Offset):** `{record['position']}`")
        st.markdown("---")

        cols = st.columns(2)
        
        with cols[0]:
            st.subheader("Detalhes do Acidente")
            st.markdown(f"**Data do Acidente:** `{data_obj.get('crash_date', 'N/A')}`")
            st.markdown(f"**Tipo de Acidente:** `{data_obj.get('crash_type', 'N/A')}`")
            st.markdown(f"**Dispositivo de Tráfego:** `{data_obj.get('traffic_control_device', 'N/A')}`")
            st.markdown(f"**Condição Climática:** `{data_obj.get('weather_condition', 'N/A')}`")
            st.markdown(f"**Condição de Iluminação:** `{data_obj.get('lighting_condition', 'N/A')}`")
            st.markdown(f"**Primeiro Tipo de Colisão:** `{data_obj.get('first_crash_type', 'N/A')}`")
            st.markdown(f"**Condição da Via:** `{data_obj.get('roadway_surface_cond', 'N/A')}`")
            st.markdown(f"**Defeito na Via:** `{data_obj.get('road_defect', 'N/A')}`")
        
        with cols[1]:
            st.subheader("Detalhes de Impacto")
            st.markdown(f"**Unidades Envolvidas:** `{data_obj.get('num_units', 0)}`")
            st.markdown(f"**Total de Lesões:** `{data_obj.get('injuries_total', 0.0):.2f}`")
            st.markdown(f"**Lesões Fatais:** `{data_obj.get('injuries_fatal', 0.0):.2f}`")
            st.markdown(f"**Lesões Incapacitantes:** `{data_obj.get('injuries_incapacitating', 0.0):.2f}`")
            st.markdown(f"**Lesões Não Incapacitantes:** `{data_obj.get('injuries_non_incapacitating', 0.0):.2f}`")
            st.markdown(f"**Lesões Reportadas Não Evidentes:** `{data_obj.get('injuries_reported_not_evident', 0.0):.2f}`")
            st.markdown(f"**Sem Indicação de Lesão:** `{data_obj.get('injuries_no_indication', 0.0):.2f}`")
            st.markdown(f"**Lesão Mais Grave:** `{data_obj.get('most_severe_injury', 'N/A')}`")
            st.markdown(f"**Causa Contributiva Primária:** `{data_obj.get('prim_contributory_cause', 'N/A')}`")
            st.markdown(f"**Relacionado a Cruzamento:** `{data_obj.get('intersection_related_i', 'NO')}`")

            st.subheader("Detalhes Temporais")
            st.markdown(f"**Hora do Acidente:** `{data_obj.get('crash_hour', 0)}`")
            st.markdown(f"**Dia da Semana:** `{data_obj.get('crash_day_of_week', 1)}`")
            st.markdown(f"**Mês:** `{data_obj.get('crash_month', 1)}`")

        st.markdown("---")
        st.subheader("Representação JSON Completa:")
        st.json(data_obj)


    with tab_view:
        st.header("👁️ Visualizar e Gerenciar Registros")
        
        # --- Section: Read Record by ID ---
        st.subheader("🔎 Buscar Registro por ID")
        record_id_input_str = st.text_input("Digite o ID do Registro:", key="search_by_id_input")
        
        search_id_button = st.button("Buscar por ID")
        if search_id_button:
            if record_id_input_str:
                try:
                    record_id_to_find = int(record_id_input_str)
                    found_record = db.get_record_by_id(record_id_to_find, use_index=st.session_state.use_index_for_crud)
                    if found_record:
                        st.subheader(f"✅ Registro encontrado para ID: `{record_id_to_find}`")
                        with st.expander("Detalhes do Registro Encontrado", expanded=True):
                            display_record_details(found_record) # Use helper function
                        
                        st.markdown("---")
                        st.subheader("Ações para o Registro Encontrado")
                        col_edit_found, col_delete_found = st.columns(2)
                        with col_edit_found:
                            if st.button(f"✏️ Editar Este Registro ({found_record['record_id']})", key=f"edit_found_{found_record['record_id']}"):
                                st.session_state.edit_record_id = found_record['record_id']
                                st.session_state.edit_record_data = found_record['data']
                                st.session_state.show_edit_form = True
                                st.experimental_rerun()
                        with col_delete_found:
                            if st.button(f"🗑️ Excluir Este Registro ({found_record['record_id']})", key=f"delete_found_{found_record['record_id']}", type="secondary"):
                                st.warning(f"⚠️ Tem certeza que deseja excluir o registro `{found_record['record_id']}`? Esta ação o marcará como inválido e reconstruirá o índice.")
                                if st.button("✅ Confirmar Exclusão", key=f"confirm_delete_found_{found_record['record_id']}"):
                                    try:
                                        if db.delete_record(found_record['record_id'], use_index=st.session_state.use_index_for_crud):
                                            st.success("✔️ Registro excluído com sucesso (marcado como inválido e índice atualizado).")
                                            logger.info(f"Record {found_record['record_id']} deleted via UI.")
                                            st.session_state.records_dirty = True
                                            time.sleep(1)
                                            st.experimental_rerun()
                                        else:
                                            st.error("❌ Falha ao excluir registro.")
                                    except Exception as e:
                                        st.error(f"⚠️ Erro ao excluir registro: {e}")
                                        logger.error(f"UI delete error: {traceback.format_exc()}")
                    else:
                        st.info("ℹ️ Registro não encontrado para o ID fornecido ou está inválido. Verifique o ID.")
                except ValueError:
                    st.warning("⚠️ Por favor, digite um ID de registro válido (número inteiro).")
            else:
                st.info("ℹ️ Digite um ID de registro para buscar.")
        # --- End Section ---

        st.markdown("---")
        st.subheader("📚 Visualizar Todos os Registros (Paginado)")
        
        records_per_page = st.slider("Registros por página", 10, 50, APP_CONFIG["MAX_RECORDS_PER_PAGE"], key="records_per_page_slider")
        
        # Refresh cache if dirty
        if st.session_state.records_dirty:
            st.session_state.all_records_cache = list(db.get_all_records(include_invalid=False))
            st.session_state.records_dirty = False
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1 
            else:
                st.session_state.current_page = 1

        all_records = st.session_state.all_records_cache
        total_records = len(all_records)
        total_pages = (total_records + records_per_page - 1) // records_per_page if total_records > 0 else 1

        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
        
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages
        if st.session_state.current_page < 1:
            st.session_state.current_page = 1

        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            if st.button("⬅️ Página Anterior", key="prev_page_button"):
                if st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.experimental_rerun()
        with col2:
            st.markdown(f"<p style='text-align:center; font-weight:bold;'>Página {st.session_state.current_page} de {total_pages} (Total: {total_records} registros)</p>", unsafe_allow_html=True)
        with col3:
            if st.button("Próxima Página ➡️", key="next_page_button"):
                if st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1
                    st.experimental_rerun()

        start_idx = (st.session_state.current_page - 1) * records_per_page
        end_idx = start_idx + records_per_page
        displayed_records = all_records[start_idx:end_idx]

        if displayed_records:
            for record in displayed_records:
                # Use common fields for expander title
                expander_title = f"ID: {record['record_id']} - Data: {record['data'].get('crash_date', 'N/A')} - Tipo: {record['data'].get('crash_type', 'N/A')}"
                with st.expander(expander_title, expanded=False):
                    display_record_details(record) # Use helper function

                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button(f"✏️ Editar {record['record_id']}", key=f"edit_paginated_{record['record_id']}"):
                            st.session_state.edit_record_id = record['record_id']
                            st.session_state.edit_record_data = record['data']
                            st.session_state.show_edit_form = True
                            st.experimental_rerun()
                    with col_delete:
                        if st.button(f"🗑️ Excluir {record['record_id']}", key=f"delete_paginated_{record['record_id']}", type="secondary"):
                            st.warning(f"⚠️ Tem certeza que deseja excluir o registro `{record['record_id']}`? Isso o marcará como inválido e reconstruirá o índice.")
                            if st.button("✅ Confirmar Exclusão", key=f"confirm_delete_paginated_{record['record_id']}"):
                                try:
                                    if db.delete_record(record['record_id'], use_index=st.session_state.use_index_for_crud):
                                        st.success("✔️ Registro excluído com sucesso (marcado como inválido).")
                                        logger.info(f"Record {record['record_id']} deleted via UI.")
                                        st.session_state.records_dirty = True
                                        time.sleep(1)
                                        st.experimental_rerun()
                                    else:
                                        st.error("❌ Falha ao excluir registro.")
                                except Exception as e:
                                    st.error(f"⚠️ Erro ao excluir registro: {e}")
                                    logger.error(f"UI delete error: {traceback.format_exc()}")
        else:
            st.info("ℹ️ Nenhum registro encontrado.")

        # Edit Form Logic
        if st.session_state.get('show_edit_form', False) and st.session_state.get('edit_record_id') is not None:
            st.markdown("---")
            st.header(f"✏️ Editar Registro: {st.session_state.edit_record_id}")
            record_to_edit_data = st.session_state.edit_record_data

            with st.form("edit_record_form"):
                st.subheader("Detalhes Essenciais do Acidente (*)")
                cols_req_edit = st.columns(2)
                
                with cols_req_edit[0]:
                    # Convert string date back to date object for st.date_input
                    initial_crash_date = date.fromisoformat(record_to_edit_data.get('crash_date')) if record_to_edit_data.get('crash_date') else date.today()
                    edited_crash_date = st.date_input(
                        "Data do Acidente*",
                        value=initial_crash_date,
                        help="Data em que o acidente ocorreu (AAAA-MM-DD)",
                        key="edit_crash_date"
                    )
                with cols_req_edit[1]:
                    edited_crash_type = st.text_input(
                        "Tipo de Acidente*",
                        value=record_to_edit_data.get('crash_type', ''),
                        help="Tipo principal de colisão (ex: Colisão Traseira, Frontal, Lateral, Capotamento)",
                        key="edit_crash_type"
                    )
                
                cols_units_inj_edit = st.columns(2)
                with cols_units_inj_edit[0]:
                    edited_num_units = st.number_input(
                        "Unidades Envolvidas*",
                        min_value=0,
                        max_value=999,
                        value=record_to_edit_data.get('num_units', 1),
                        step=1,
                        help="Número total de veículos/unidades envolvidos no acidente.",
                        key="edit_num_units"
                    )
                with cols_units_inj_edit[1]:
                    edited_injuries_total = st.number_input(
                        "Total de Lesões*",
                        min_value=0.0,
                        value=float(record_to_edit_data.get('injuries_total', 0.0)),
                        step=0.1,
                        help="Contagem total de todas as lesões (fatais, incapacitantes, etc.).",
                        key="edit_injuries_total"
                    )
                
                st.markdown("---")

                st.subheader("Informações Adicionais do Acidente")
                cols_cond_edit = st.columns(3)
                with cols_cond_edit[0]:
                    # Find index for selectbox
                    current_traffic_control = record_to_edit_data.get('traffic_control_device', "NO CONTROL DEVICE")
                    traffic_control_options = ["NO CONTROL DEVICE", "TRAFFIC SIGNAL", "STOP SIGN/FLASHER", "UNKNOWN", "OTHER", "SCHOOL CROSSING GUARD", "RAILROAD CROSSING GATE"]
                    idx_traffic_control = traffic_control_options.index(current_traffic_control) if current_traffic_control in traffic_control_options else 0
                    edited_traffic_control_device = st.selectbox(
                        "Dispositivo de Controle de Tráfego",
                        traffic_control_options,
                        index=idx_traffic_control,
                        key="edit_traffic_control_device"
                    )
                with cols_cond_edit[1]:
                    current_weather = record_to_edit_data.get('weather_condition', "CLEAR")
                    weather_options = ["CLEAR", "RAIN", "CLOUDY/OVERCAST", "SNOW", "FOG/SMOKE/HAZE", "FREEZING RAIN/DRIZZLE", "SLEET/HAIL", "BLOWING SNOW"]
                    idx_weather = weather_options.index(current_weather) if current_weather in weather_options else 0
                    edited_weather_condition = st.selectbox(
                        "Condição Climática",
                        weather_options,
                        index=idx_weather,
                        key="edit_weather_condition"
                    )
                with cols_cond_edit[2]:
                    current_lighting = record_to_edit_data.get('lighting_condition', "DAYLIGHT")
                    lighting_options = ["DAYLIGHT", "DARKNESS, LIGHTED ROAD", "DARKNESS, UNLIGHTED ROAD", "DAWN", "DUSK"]
                    idx_lighting = lighting_options.index(current_lighting) if current_lighting in lighting_options else 0
                    edited_lighting_condition = st.selectbox(
                        "Condição de Iluminação",
                        lighting_options,
                        index=idx_lighting,
                        key="edit_lighting_condition"
                    )

                st.markdown("---")

                st.subheader("Detalhes da Primeira Colisão e Condições da Via")
                cols_crash_road_edit = st.columns(2)
                with cols_crash_road_edit[0]:
                    edited_first_crash_type = st.text_input(
                        "Primeiro Tipo de Colisão",
                        value=record_to_edit_data.get('first_crash_type', ''),
                        help="Tipo de colisão que iniciou o acidente (ex: ANGLE, REAR END, SIDESWIPE SAME DIRECTION)",
                        key="edit_first_crash_type"
                    )
                with cols_crash_road_edit[1]:
                    current_road_surface = record_to_edit_data.get('roadway_surface_cond', "DRY")
                    road_surface_options = ["DRY", "WET", "SNOW OR SLUSH", "ICE", "SAND, MUD, DIRT", "OIL", "WATER (STANDING/MOVING)"]
                    idx_road_surface = road_surface_options.index(current_road_surface) if current_road_surface in road_surface_options else 0
                    edited_roadway_surface_cond = st.selectbox(
                        "Condição da Superfície da Via",
                        road_surface_options,
                        index=idx_road_surface,
                        key="edit_roadway_surface_cond"
                    )
                    current_road_defect = record_to_edit_data.get('road_defect', "NO DEFECTS")
                    road_defect_options = ["NO DEFECTS", "RUT, HOLES", "SHOULDER DEFECTS", "WORN SURFACE", "DEBRIS ON ROADWAY"]
                    idx_road_defect = road_defect_options.index(current_road_defect) if current_road_defect in road_defect_options else 0
                    edited_road_defect = st.selectbox(
                        "Defeito na Via",
                        road_defect_options,
                        index=idx_road_defect,
                        key="edit_road_defect"
                    )
                
                st.markdown("---")

                st.subheader("Causa Contributiva Primária e Lesões")
                edited_prim_contributory_cause = st.text_input(
                    "Causa Contributiva Primária",
                    value=record_to_edit_data.get('prim_contributory_cause', ''),
                    help="Fator primário que contribuiu para o acidente (ex: FALHA DO MOTORISTA, ALTA VELOCIDADE)",
                    key="edit_prim_contributory_cause"
                )
                current_most_severe_injury = record_to_edit_data.get('most_severe_injury', "NO INDICATION OF INJURY")
                most_severe_injury_options = ["NO INDICATION OF INJURY", "NON-INCAPACITATING INJURY", "REPORTED, NOT EVIDENT", "FATAL", "INCAPACITATING INJURY"]
                idx_most_severe_injury = most_severe_injury_options.index(current_most_severe_injury) if current_most_severe_injury in most_severe_injury_options else 0
                edited_most_severe_injury = st.selectbox(
                    "Lesão Mais Grave",
                    most_severe_injury_options,
                    index=idx_most_severe_injury,
                    key="edit_most_severe_injury"
                )

                inj_cols_edit = st.columns(3)
                with inj_cols_edit[0]:
                    edited_injuries_fatal = st.number_input("Lesões Fatais", min_value=0.0, value=float(record_to_edit_data.get('injuries_fatal', 0.0)), step=0.1, key="edit_injuries_fatal")
                    edited_injuries_incapacitating = st.number_input("Lesões Incapacitantes", min_value=0.0, value=float(record_to_edit_data.get('injuries_incapacitating', 0.0)), step=0.1, key="edit_injuries_incapacitating")
                with inj_cols_edit[1]:
                    edited_injuries_non_incapacitating = st.number_input("Lesões Não Incapacitantes", min_value=0.0, value=float(record_to_edit_data.get('injuries_non_incapacitating', 0.0)), step=0.1, key="edit_injuries_non_incapacitating")
                    edited_injuries_reported_not_evident = st.number_input("Lesões Reportadas Não Evidentes", min_value=0.0, value=float(record_to_edit_data.get('injuries_reported_not_evident', 0.0)), step=0.1, key="edit_injuries_reported_not_evident")
                with inj_cols_edit[2]:
                    edited_injuries_no_indication = st.number_input("Sem Indicação de Lesão", min_value=0.0, value=float(record_to_edit_data.get('injuries_no_indication', 0.0)), step=0.1, key="edit_injuries_no_indication")
                
                st.markdown("---")

                st.subheader("Detalhes Temporais e Cruzamento")
                temp_cols_edit = st.columns(3)
                with temp_cols_edit[0]:
                    edited_crash_hour = st.number_input("Hora do Acidente (0-23)", min_value=0, max_value=23, value=record_to_edit_data.get('crash_hour', 0), step=1, key="edit_crash_hour")
                with temp_cols_edit[1]:
                    edited_crash_day_of_week = st.number_input("Dia da Semana (1=Dom, 7=Sáb)", min_value=1, max_value=7, value=record_to_edit_data.get('crash_day_of_week', 1), step=1, key="edit_crash_day_of_week")
                with temp_cols_edit[2]:
                    edited_crash_month = st.number_input("Mês (1-12)", min_value=1, max_value=12, value=record_to_edit_data.get('crash_month', 1), step=1, key="edit_crash_month")
                
                current_intersection_related = record_to_edit_data.get('intersection_related_i', "NO")
                intersection_options = ["NO", "YES", "NOT APPLICABLE"]
                idx_intersection = intersection_options.index(current_intersection_related) if current_intersection_related in intersection_options else 0
                edited_intersection_related_i = st.selectbox(
                    "Relacionado a Cruzamento?",
                    intersection_options,
                    index=idx_intersection,
                    key="edit_intersection_related_i"
                )

                st.markdown("---")
                col_update_btn, col_cancel_btn = st.columns(2)
                with col_update_btn:
                    update_submitted = st.form_submit_button("Atualizar Registro")
                with col_cancel_btn:
                    cancel_update = st.form_submit_button("Cancelar", type="secondary")

                if update_submitted:
                    new_record_data = {
                        "crash_date": edited_crash_date.isoformat(),
                        "crash_type": edited_crash_type,
                        "num_units": edited_num_units,
                        "injuries_total": edited_injuries_total,
                        "traffic_control_device": edited_traffic_control_device,
                        "weather_condition": edited_weather_condition,
                        "lighting_condition": edited_lighting_condition,
                        "first_crash_type": edited_first_crash_type,
                        "roadway_surface_cond": edited_roadway_surface_cond,
                        "road_defect": edited_road_defect,
                        "prim_contributory_cause": edited_prim_contributory_cause,
                        "most_severe_injury": edited_most_severe_injury,
                        "injuries_fatal": edited_injuries_fatal,
                        "injuries_incapacitating": edited_injuries_incapacitating,
                        "injuries_non_incapacitating": edited_injuries_non_incapacitating,
                        "injuries_reported_not_evident": edited_injuries_reported_not_evident,
                        "injuries_no_indication": edited_injuries_no_indication,
                        "crash_hour": edited_crash_hour,
                        "crash_day_of_week": edited_crash_day_of_week,
                        "crash_month": edited_crash_month,
                        "intersection_related_i": edited_intersection_related_i,
                    }
                    try:
                        # Basic validation for required fields
                        if not edited_crash_date or not edited_crash_type or not edited_num_units or edited_injuries_total is None:
                            st.error("Campos marcados com (*) são obrigatórios.")
                        else:
                            if db.update_record(st.session_state.edit_record_id, new_record_data, use_index=st.session_state.use_index_for_crud):
                                st.success("✔️ Registro atualizado com sucesso!")
                                logger.info(f"Record {st.session_state.edit_record_id} updated via UI.")
                                st.session_state.show_edit_form = False
                                st.session_state.edit_record_id = None
                                st.session_state.edit_record_data = None
                                st.session_state.records_dirty = True
                                time.sleep(1)
                                st.experimental_rerun()
                            else:
                                st.error("❌ Falha ao atualizar registro.")
                    except Exception as e:
                        st.error(f"⚠️ Erro ao atualizar registro: {e}")
                        logger.error(f"UI update error: {traceback.format_exc()}")
                
                if cancel_update:
                    st.session_state.show_edit_form = False
                    st.session_state.edit_record_id = None
                    st.session_state.edit_record_data = None
                    st.experimental_rerun()


    with tab_search:
        st.header("🔍 Buscar Registros")
        search_query = st.text_input("Digite sua busca (ex: tipo de acidente, condição climática)")
        if st.button("🔍 Buscar"):
            if search_query:
                found_records = db.search_records(search_query, use_index=st.session_state.use_index_for_crud)
                if found_records:
                    st.subheader(f"Resultados da Busca para '{search_query}':")
                    for record in found_records:
                        expander_title = f"ID: {record['record_id']} - Data: {record['data'].get('crash_date', 'N/A')} - Tipo: {record['data'].get('crash_type', 'N/A')}"
                        with st.expander(expander_title, expanded=False):
                            display_record_details(record) # Use helper function
                else:
                    st.info("ℹ️ Nenhum registro encontrado para sua busca.")
            else:
                st.warning("⚠️ Por favor, digite um termo para buscar.")

    with tab_import_export:
        st.header("📥📤 Importar e Exportar Dados")

        st.subheader("📥 Importar CSV")
        uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=["csv"])
        if uploaded_file is not None:
            progress_bar = st.progress(0)
            progress_text = st.empty()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_csv_path = tmp_file.name
            
            if st.button("🚀 Iniciar Importação"):
                try:
                    def update_progress(current_row, total_rows):
                        if total_rows > 0:
                            percent_complete = min(int((current_row / total_rows) * 100), 100)
                            progress_bar.progress(percent_complete)
                            progress_text.text(f"Importando linha {current_row} de {total_rows}...")
                        else:
                            progress_bar.progress(100)
                            progress_text.text("Importação concluída: 0 registros.")

                    imported_count = db.import_from_csv(temp_csv_path, progress_callback=update_progress)
                    st.success(f"🎉 Importação concluída. {imported_count} registros importados.")
                    logger.info(f"CSV imported from {temp_csv_path}, {imported_count} records.")
                    st.session_state.records_dirty = True
                except Exception as e:
                    st.error(f"❌ Erro durante a importação: {e}")
                    logger.error(f"CSV import failed for {temp_csv_path}: {traceback.format_exc()}")
                finally:
                    os.unlink(temp_csv_path)
                    progress_bar.empty()
                    progress_text.empty()

        st.subheader("📤 Exportar para CSV")
        export_file_name = st.text_input("Nome do arquivo para exportar (ex: acidentes.csv)", "traffic_accidents_export.csv")
        export_path = os.path.join(APP_CONFIG["DB_DIR"], export_file_name)
        if st.button("⬇️ Exportar Dados"):
            try:
                if db.export_to_csv(export_path):
                    with open(export_path, "rb") as file_to_download:
                        st.download_button(
                            label="Baixar Arquivo CSV",
                            data=file_to_download.read(),
                            file_name=export_file_name,
                            mime="text/csv",
                            key="download_csv_button"
                        )
                    logger.info(f"Data exported to {export_path} and offered for download.")
            except Exception as e:
                st.error(f"⚠️ Erro ao preparar exportação: {e}")
                logger.error(f"Export preparation failed for {export_path}: {traceback.format_exc()}")

    with tab_admin:
        st.header("⚙️ Ferramentas de Administração")

        st.subheader("💾 Criar Backup do Banco de Dados")
        if st.button("Criar Backup Agora"):
            try:
                backup_path = db.create_backup()
                if backup_path:
                    st.success(f"✔️ Backup criado com sucesso em `{backup_path}`")
                    logger.info(f"Manual backup created: {backup_path}")
                else:
                    st.error("❌ Falha ao criar backup.")
            except Exception as e:
                st.error(f"⚠️ Erro ao criar backup: {e}")
                logger.error(f"Backup creation error: {traceback.format_exc()}")
        
        st.subheader("🔄 Reconstruir Arquivo de Índice")
        st.info("ℹ️ Isto irá recriar o arquivo de índice (`index.idx`) com base apenas nos registros válidos no banco de dados. Útil para corrigir inconsistências ou após exclusões lógicas.")
        if st.button("Reconstruir Índice"):
            try:
                db.rebuild_index()
                st.success("✔️ Índice reconstruído com sucesso!")
                logger.info("Index rebuilt successfully via UI.")
                st.session_state.records_dirty = True
            except Exception as e:
                st.error(f"❌ Erro ao reconstruir índice: {e}")
                logger.error(f"Index rebuild error: {traceback.format_exc()}")

        st.subheader("⚠️ Excluir Todos os Dados do Banco de Dados")
        st.warning("🚨 Esta ação irá **APAGAR TODOS OS REGISTROS** do banco de dados, incluindo o arquivo de dados, o índice e o contador de IDs. Esta ação é irreversível!")
        confirm_delete_all = st.checkbox("Eu entendo e desejo excluir todos os dados permanentemente.")
        if confirm_delete_all:
            if st.button("🔴 Excluir TUDO Agora", type="secondary"):
                try:
                    db.delete_all_data()
                    st.session_state.records_dirty = True # Force refresh after deletion
                    time.sleep(1) # Give time for message to display
                    st.experimental_rerun() # Rerun to reflect empty state
                except Exception as e:
                    st.error(f"❌ Erro ao excluir todos os dados: {e}")
                    logger.error(f"Delete all data error: {traceback.format_exc()}")
        
        st.subheader("📜 Log de Atividades Recentes")
        st.write(f"Exibindo as últimas {APP_CONFIG['MAX_LOG_ENTRIES_DISPLAY']} entradas do log de atividades (mais recentes primeiro):")
        try:
            if Path(LOG_FILE_PATH).exists():
                with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                    log_lines.reverse()
                    
                    display_entries = []
                    for line in log_lines:
                        # Filter for relevant log messages for display
                        if "inserted" in line or "updated" in line or "deleted" in line or "imported" in line or "rebuilt" in line or "backed up" in line or "All database files" in line or "Critical" in line or "Error" in line:
                            try:
                                parts = line.split(' - ', 3)
                                if len(parts) >= 4:
                                    timestamp_str = parts[0]
                                    log_level = parts[2]
                                    message = parts[3].strip()
                                    
                                    # Highlight errors/critical in red
                                    if log_level == "ERROR" or log_level == "CRITICAL":
                                        display_entries.append(f"**`{timestamp_str}`** <span style='color:red;'>`{log_level}`</span> `{message}`")
                                    else:
                                        display_entries.append(f"**`{timestamp_str}`** `{log_level}` `{message}`")

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
        except Exception as e:
            st.error(f"⚠️ Não foi possível ler o log de atividades: {str(e)}")
            logger.error(f"Error reading activity log: {traceback.format_exc()}")

# --- Main Application Entry Point ---
if __name__ == "__main__":
    try:
        Path(APP_CONFIG["DB_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        st.error(f"Crítico: Não foi possível criar os diretórios do banco de dados. Verifique as permissões para {APP_CONFIG['DB_DIR']}. Erro: {e}")
        logger.critical(f"Initial directory creation failed: {traceback.format_exc()}")
        st.stop()

    setup_ui()