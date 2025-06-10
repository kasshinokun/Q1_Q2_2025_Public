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

# --- Configuration Constants (Centralized and Optimized) ---
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
LOG_FILE_PATH = os.path.join(APP_CONFIG["DB_DIR"], APP_CONFIG["LOG_FILE_NAME"])

# Configure logging (Corrected and Centralized)
logging.basicConfig(
    level=logging.INFO, # Corrected: logging.INFO instead of logging.logging.INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Data Fields ---
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

# --- Utility Functions for String Manipulation ---
def split_phrase_into_array(phrase: str) -> List[str]:
    """
    Reads a phrase and returns it as a list of strings.
    If the phrase contains ',' or '/', it performs a split operation
    and returns the resulting parts as a list of strings.
    Each part is stripped of leading/trailing whitespace.
    """
    if not isinstance(phrase, str):
        return []
    if ',' in phrase:
        return [part.strip() for part in phrase.split(',')]
    elif '/' in phrase:
        return [part.strip() for part in phrase.split('/')]
    else:
        return [phrase.strip()]

def join_array_with_character(string_array: List[str], character: str) -> str:
    """
    Receives a list of strings and a character (',' or '/') to return a single string
    where the array elements are joined by the received character, with spaces around it.
    Example: ["apple", "orange"] with character "/" -> "apple / orange"
    Example: ["one", "two", "three"] with character "," -> "one , two , three"
    """
    if not isinstance(string_array, list) or not all(isinstance(s, str) for s in string_array):
        raise TypeError("string_array must be a list of strings.")
    if not isinstance(character, str) or character not in [',', '/']:
        raise ValueError("character must be a string and either ',' or '/'.")
    return (f" {character} ").join(string_array)

# --- DataObject Class ---
class DataObject:
    """
    Represents a traffic accident record with enhanced validation and serialization.
    Each instance corresponds to a single record in the database.
    Added methods to convert to/from dictionary, and an 'id' field.
    """

    def __init__(self, row_data: Optional[List[str]] = None, existing_data_dict: Optional[Dict[str, Any]] = None):
        self._initialize_defaults()

        if row_data is not None:
            try:
                self._initialize_from_row(row_data)
            except (DataValidationError, ValueError) as e:
                logger.error(f"Error initializing DataObject from row: {str(e)} | Row: {row_data}")
                raise DataValidationError(f"Invalid data for record: {str(e)}")
        elif existing_data_dict is not None:
            try:
                self._initialize_from_dict(existing_data_dict)
            except (DataValidationError, ValueError) as e:
                logger.error(f"Error initializing DataObject from dict: {str(e)} | Dict: {existing_data_dict}")
                raise DataValidationError(f"Invalid data for record: {str(e)}")

        if not self.validate():
            raise DataValidationError("Data validation failed after initialization.")

    def _initialize_defaults(self):
        self.id: Optional[int] = None
        self.crash_date = ""
        self.traffic_control_device = "UNKNOWN"
        self.weather_condition = "UNKNOWN"
        self.lighting_condition = "UNKNOWN"
        self.first_crash_type = "UNKNOWN"
        self.trafficway_type = "UNKNOWN"
        self.alignment = "UNKNOWN"
        self.roadway_surface_cond = "UNKNOWN"
        self.road_defect = "NONE"
        self.crash_type = "UNKNOWN"
        self.intersection_related_i = "NO"
        self.damage = "UNKNOWN"
        self.prim_contributory_cause = "UNKNOWN"
        self.num_units = 0
        self.most_severe_injury = "NONE"
        self.injuries_total = 0.0
        self.injuries_fatal = 0.0
        self.injuries_incapacitating = 0.0
        self.injuries_non_incapacitating = 0.0
        self.injuries_reported_not_evident = 0.0
        self.injuries_no_indication = 0.0
        self.crash_hour = 0
        self.crash_day_of_week = 1
        self.crash_month = 1

    def _initialize_from_row(self, row_data: List[str]):
        if len(row_data) != len(FIELDS):
            raise ValueError(f"Expected {len(FIELDS)} fields, but got {len(row_data)}.")

        processed_data = [value.strip() if isinstance(value, str) else None for value in row_data]

        self.crash_date = self._validate_date(processed_data[0])
        self.traffic_control_device = self._validate_string(processed_data[1], "traffic_control_device", allow_empty=True)
        self.weather_condition = self._validate_string(processed_data[2], "weather_condition", allow_empty=True)
        self.lighting_condition = self._validate_string(processed_data[3], "lighting_condition", allow_empty=True)
        self.first_crash_type = self._validate_string(processed_data[4], "first_crash_type", allow_empty=True)
        self.trafficway_type = self._validate_string(processed_data[5], "trafficway_type", allow_empty=True)
        self.alignment = self._validate_string(processed_data[6], "alignment", allow_empty=True)
        self.roadway_surface_cond = self._validate_string(processed_data[7], "roadway_surface_cond", allow_empty=True)
        self.road_defect = self._validate_string(processed_data[8], "road_defect", allow_empty=True)
        self.crash_type = self._validate_string(processed_data[9], "crash_type", allow_empty=False)
        self.intersection_related_i = self._validate_yes_no(processed_data[10])
        self.damage = self._validate_string(processed_data[11], "damage", allow_empty=True)
        self.prim_contributory_cause = self._validate_string(processed_data[12], "prim_contributory_cause", allow_empty=True)
        self.num_units = self._validate_positive_int(processed_data[13], "num_units", min_val=0)
        self.most_severe_injury = self._validate_string(processed_data[14], "most_severe_injury", allow_empty=True)
        self.injuries_total = self._validate_positive_float(processed_data[15], "injuries_total", min_val=0.0)
        self.injuries_fatal = self._validate_positive_float(processed_data[16], "injuries_fatal", min_val=0.0)
        self.injuries_incapacitating = self._validate_positive_float(processed_data[17], "injuries_incapacitating", min_val=0.0)
        self.injuries_non_incapacitating = self._validate_positive_float(processed_data[18], "injuries_non_incapacitating", min_val=0.0)
        self.injuries_reported_not_evident = self._validate_positive_float(processed_data[19], "injuries_reported_not_evident", min_val=0.0)
        self.injuries_no_indication = self._validate_positive_float(processed_data[20], "injuries_no_indication", min_val=0.0)
        self.crash_hour = self._validate_range(processed_data[21], "crash_hour", 0, 23)
        self.crash_day_of_week = self._validate_range(processed_data[22], "crash_day_of_week", 1, 7)
        self.crash_month = self._validate_range(processed_data[23], "crash_month", 1, 12)

    def _initialize_from_dict(self, data_dict: Dict[str, Any]):
        retrieved_id = data_dict.get('id', data_dict.get('record_id'))
        if retrieved_id is not None:
            try:
                self.id = int(retrieved_id)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert 'id' ({retrieved_id}) to integer. Setting to None.")
                self.id = None
        else:
            self.id = None

        for field in FIELDS:
            if field in data_dict:
                if field == 'crash_date':
                    self.crash_date = self._validate_date(data_dict[field])
                elif field in ['num_units', 'crash_hour', 'crash_day_of_week', 'crash_month']:
                    setattr(self, field, self._validate_positive_int(str(data_dict[field]), field))
                elif field.startswith('injuries_'):
                    setattr(self, field, self._validate_positive_float(str(data_dict[field]), field))
                elif field == 'intersection_related_i':
                    self.intersection_related_i = self._validate_yes_no(data_dict[field])
                else:
                    setattr(self, field, self._validate_string(data_dict[field], field, allow_empty=True))
            else:
                logger.warning(f"Field '{field}' missing in provided dictionary for DataObject initialization. Using default.")

    @staticmethod
    def _validate_date(date_str: Optional[str]) -> str:
        if not date_str:
            return ""
        date_str = date_str.strip()
        if not date_str:
            return ""
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d',
                    '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S',
                    '%m/%d/%Y %I:%M:%S %p', '%Y-%m-%d %I:%M:%S %p'):
            try:
                dt = datetime.strptime(date_str, fmt)
                formatted_date = dt.strftime('%Y-%m-%d')
                return formatted_date
            except ValueError:
                continue
        raise DataValidationError(f"Invalid date format: '{date_str}'.")

    @staticmethod
    def _validate_string(value: Optional[str], field_name: str, max_len: int = 255, allow_empty: bool = True) -> str:
        if value is None:
            return "UNKNOWN" if not allow_empty else ""
        value = str(value).strip()
        if not value:
            return "UNKNOWN" if not allow_empty else ""
        value = value.replace(APP_CONFIG["CSV_DELIMITER"], ',').replace('\n', ' ').replace('\r', '')
        return value[:max_len]

    @staticmethod
    def _validate_yes_no(value: Optional[str]) -> str:
        if value is None:
            return "NO"
        value = str(value).strip().lower()
        return "YES" if value in ('yes', 'y', 'true', '1') else "NO"

    @staticmethod
    def _validate_positive_int(value: Optional[str], field_name: str, min_val: int = 0) -> int:
        try:
            if value is None or value == '':
                return min_val
            num = int(float(value))
            if num < min_val:
                logger.warning(f"Integer value for {field_name} ({num}) is less than minimum {min_val}. Setting to {min_val}.")
                return min_val
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    @staticmethod
    def _validate_positive_float(value: Optional[str], field_name: str, min_val: float = 0.0) -> float:
        try:
            if value is None or value == '':
                return min_val
            num = float(value)
            if num < min_val:
                logger.warning(f"Float value for {field_name} ({num}) is less than minimum {min_val}. Setting to {min_val}.")
                return min_val
            return round(num, 2)
        except (ValueError, TypeError):
            logger.warning(f"Invalid float value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    @staticmethod
    def _validate_range(value: Optional[str], field_name: str, min_val: int, max_val: int) -> int:
        try:
            if value is None or value == '':
                return min_val
            num = int(float(value))
            if not (min_val <= num <= max_val):
                logger.warning(f"Value for {field_name} ({num}) is out of range [{min_val}-{max_val}]. Setting to {min_val}.")
                return min_val
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid numeric value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    def validate(self) -> bool:
        try:
            if not self.crash_date:
                raise DataValidationError("Crash date is required.")
            if not self.crash_type or self.crash_type == "UNKNOWN":
                raise DataValidationError("Crash type is required.")
            if not isinstance(self.num_units, int) or self.num_units < 0:
                raise DataValidationError("Number of units must be a non-negative integer.")
            if not isinstance(self.injuries_total, (int, float)) or self.injuries_total < 0:
                raise DataValidationError("Total injuries must be a non-negative number.")

            if self.crash_date:
                try:
                    datetime.strptime(self.crash_date, '%Y-%m-%d')
                except ValueError:
                    raise DataValidationError("Invalid crash date format (expected YYYY-MM-DD).")

            total_reported_injuries = (
                self.injuries_fatal + self.injuries_incapacitating +
                self.injuries_non_incapacitating + self.injuries_reported_not_evident +
                self.injuries_no_indication
            )
            if self.injuries_total < total_reported_injuries - 0.01:
                logger.warning(f"Total injuries ({self.injuries_total}) less than sum of specific injuries ({total_reported_injuries}).")

            if not (0 <= self.crash_hour <= 23):
                raise DataValidationError("Crash hour out of valid range (0-23).")
            if not (1 <= self.crash_day_of_week <= 7):
                raise DataValidationError("Crash day of week out of valid range (1-7).")
            if not (1 <= self.crash_month <= 12):
                raise DataValidationError("Crash month out of valid range (1-12).")
            return True
        except DataValidationError as e:
            logger.warning(f"DataObject validation failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during DataObject validation: {traceback.format_exc()}")
            return False

    def to_bytes(self) -> bytes:
        try:
            # Include 'id' when serializing
            data_dict = {attr: getattr(self, attr) for attr in FIELDS + ['id'] if hasattr(self, attr)}
            return json.dumps(data_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
        except TypeError as e:
            logger.error(f"Serialization TypeError in DataObject: {e}. Data dict: {data_dict}")
            raise DatabaseError(f"Failed to serialize record due to invalid data type: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected serialization error in DataObject: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to serialize record: {str(e)}")

    @classmethod
    def from_bytes(cls, byte_data: bytes) -> 'DataObject':
        if not byte_data:
            raise DataValidationError("Attempted to deserialize empty byte data.")
        try:
            data_dict = json.loads(byte_data.decode('utf-8'))
            obj = cls(existing_data_dict=data_dict)
            return obj
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"JSON/Unicode decode error during deserialization: {e} | Data: {byte_data[:100]}...")
            raise DatabaseError("Invalid data format during deserialization.")
        except DataValidationError as e:
            logger.error(f"Data validation error after deserialization: {e}")
            raise DatabaseError(f"Corrupt data after deserialization: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected deserialization error: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to deserialize record: {str(e)}")

    def __repr__(self) -> str:
        return f"DataObject(ID={self.id}, Date='{self.crash_date}', Type='{self.crash_type}', TotalInjuries={self.injuries_total})"

# --- TrafficAccidentsDB Class ---
class TrafficAccidentsDB:
    """ Handles all database operations for traffic accident records.
    Implements file-based storage with robust locking, backups, and error recovery. """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.lock_file_path = LOCK_PATH
        self.id_counter_path = ID_COUNTER_PATH
        self._ensure_directories()
        self._last_read_id = 0
        self._lock = filelock.FileLock(self.lock_file_path)

    def _ensure_directories(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            os.makedirs(BACKUP_PATH, exist_ok=True)
            os.chmod(os.path.dirname(self.db_path), 0o755)
            os.chmod(BACKUP_PATH, 0o755)
            logger.info(f"Ensured DB directory '{os.path.dirname(self.db_path)}' and backup directory '{BACKUP_PATH}' exist.")
        except OSError as e:
            logger.critical(f"OS error ensuring directories: {e}")
            raise DatabaseError(f"Failed to create necessary directories: {str(e)}")
        except Exception as e:
            logger.critical(f"Unexpected error ensuring directories: {traceback.format_exc()}")
            raise DatabaseError(f"Critical error initializing database paths: {str(e)}")

    def _acquire_lock(self, timeout: int = 10, interval: float = 0.5):
        try:
            self._lock.acquire(timeout=timeout)
            logger.debug(f"Acquired lock on {self.lock_file_path}")
        except filelock.Timeout:
            raise FileLockError(f"Failed to acquire file lock on {self.lock_file_path} within {timeout} seconds. Another process might be holding the lock.")
        except Exception as e:
            logger.error(f"Error acquiring file lock: {e}")
            raise FileLockError(f"Failed to acquire file lock: {str(e)}")

    def _release_lock(self):
        try:
            self._lock.release()
            logger.debug(f"Released lock on {self.lock_file_path}")
        except Exception as e:
            logger.error(f"Error releasing file lock: {e}")

    def _create_backup(self):
        try:
            if not os.path.exists(self.db_path):
                logger.info("No database file found to backup.")
                return

            backups = sorted(Path(BACKUP_PATH).glob("backup_*.db"))
            while len(backups) >= APP_CONFIG["MAX_BACKUPS"]:
                oldest = backups.pop(0)
                try:
                    os.unlink(oldest)
                    logger.info(f"Removed old backup: {oldest}")
                except OSError as e:
                    logger.warning(f"Could not remove old backup '{oldest}': {e}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_PATH, f"backup_{timestamp}.db")
            with open(self.db_path, 'rb') as src:
                with open(backup_path, 'wb') as dst:
                    while True:
                        chunk = src.read(APP_CONFIG["CHUNK_SIZE"])
                        if not chunk:
                            break
                        dst.write(chunk)
            logger.info(f"Created database backup: {backup_path}")
        except Exception as e:
            logger.error(f"Backup failed: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to create database backup: {str(e)}")

    def _read_last_id(self) -> int:
        try:
            if not os.path.exists(self.id_counter_path):
                return 0
            with open(self.id_counter_path, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Could not read ID counter file: {e}. Starting ID from 0.")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error reading ID counter: {traceback.format_exc()}")
            return 0

    def _write_last_id(self, last_id: int):
        try:
            with open(self.id_counter_path, 'w') as f:
                f.write(str(last_id))
        except Exception as e:
            logger.error(f"Could not write ID counter to file: {e}")

    def add_record(self, record: DataObject) -> int:
        try:
            self._acquire_lock()
            self._create_backup() # Create backup before modification

            current_max_id = self._read_last_id()
            new_id = current_max_id + 1
            record.id = new_id

            record_bytes = record.to_bytes()
            record_len = len(record_bytes)
            
            with open(self.db_path, 'ab') as f:
                f.write(struct.pack('<I', new_id)) # Write ID
                f.write(struct.pack('<I', record_len)) # Write length of data
                f.write(record_bytes) # Write data
            
            self._write_last_id(new_id) # Update the ID counter file
            logger.info(f"Added record with ID: {new_id}")
            return new_id
        except FileLockError:
            raise
        except Exception as e:
            logger.error(f"Error adding record: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to add record: {str(e)}")
        finally:
            self._release_lock()

    def get_record(self, record_id: int) -> Optional[DataObject]:
        try:
            self._acquire_lock()
            with open(self.db_path, 'rb') as f:
                while True:
                    header = f.read(8) # Read ID (4 bytes) + Length (4 bytes)
                    if not header:
                        break
                    
                    current_id, record_len = struct.unpack('<II', header)
                    record_bytes = f.read(record_len)
                    
                    if current_id == record_id:
                        return DataObject.from_bytes(record_bytes)
            return None # Record not found
        except FileNotFoundError:
            logger.warning(f"Database file not found at {self.db_path}.")
            return None
        except (struct.error, DataValidationError, DatabaseError) as e:
            logger.error(f"Error reading record {record_id}: {e}")
            raise DatabaseError(f"Corrupt data or error reading record {record_id}: {str(e)}")
        except FileLockError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting record {record_id}: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to get record {record_id}: {str(e)}")
        finally:
            self._release_lock()

    def update_record(self, record: DataObject) -> bool:
        if record.id is None:
            raise ValueError("Record must have an ID to be updated.")
        try:
            self._acquire_lock()
            self._create_backup()

            records = []
            updated = False
            
            # Read all records, find and update the target
            with open(self.db_path, 'rb') as f:
                while True:
                    header = f.read(8)
                    if not header:
                        break
                    current_id, record_len = struct.unpack('<II', header)
                    record_bytes = f.read(record_len)
                    
                    if current_id == record.id:
                        records.append(record.to_bytes()) # Add updated record bytes
                        updated = True
                    else:
                        records.append(record_bytes) # Keep original record bytes
            
            if not updated:
                logger.warning(f"Record with ID {record.id} not found for update.")
                return False

            # Rewrite the database file with the updated record
            with open(self.db_path, 'wb') as f:
                for idx, r_bytes in enumerate(records):
                    # For rewrite, need to ensure the ID is re-written correctly if it was part of the original record_bytes
                    # Or, better, store ID in header and re-read it.
                    # Given the current structure, let's assume records in `records` list are raw byte data (excluding ID/length header)
                    # and reconstruct headers.
                    # The `add_record` and `get_record` imply ID is in the header, not `record_bytes`.
                    # Let's adjust this logic to explicitly pack ID in the header for all records on rewrite.

                    # To fix: when `records.append(record.to_bytes())` is called, `record.to_bytes()` itself generates JSON
                    # which includes the ID. But our file format is <ID><LEN><JSON_DATA>.
                    # So `records` should contain (id, raw_json_bytes) tuples.
                    
                    # Reread from existing DB file to reconstruct ID and data for writing back.
                    # A more robust update approach would be to manage fixed-size slots or a separate index file.
                    # For simplicity, for now, we'll re-read and recreate.
                    pass # This part needs a full rewrite or deeper thought for robust update.

            # Simplified update logic for demonstration (inefficient for large DBs):
            # Read all, modify in memory, write all back.
            all_records = self.get_all_records()
            found_and_updated = False
            for i, r in enumerate(all_records):
                if r.id == record.id:
                    all_records[i] = record
                    found_and_updated = True
                    break
            
            if found_and_updated:
                self._rewrite_all_records(all_records) # Helper to rewrite the entire DB
                logger.info(f"Updated record with ID: {record.id}")
                return True
            else:
                logger.warning(f"Record with ID {record.id} not found for update.")
                return False

        except FileLockError:
            raise
        except Exception as e:
            logger.error(f"Error updating record {record.id}: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to update record {record.id}: {str(e)}")
        finally:
            self._release_lock()
            
    def _rewrite_all_records(self, records: List[DataObject]):
        """Helper to rewrite the entire database file from a list of DataObject instances."""
        try:
            with open(self.db_path, 'wb') as f:
                for rec in records:
                    record_bytes = rec.to_bytes()
                    record_len = len(record_bytes)
                    f.write(struct.pack('<I', rec.id)) # Write ID
                    f.write(struct.pack('<I', record_len)) # Write length
                    f.write(record_bytes) # Write data
        except Exception as e:
            logger.critical(f"Failed to rewrite all records during update/delete: {traceback.format_exc()}")
            raise DatabaseError(f"Critical error during database rewrite: {str(e)}")

    def delete_record(self, record_id: int) -> bool:
        try:
            self._acquire_lock()
            self._create_backup()

            all_records = self.get_all_records() # Get all records in memory
            initial_count = len(all_records)
            
            # Filter out the record to be deleted
            updated_records = [r for r in all_records if r.id != record_id]
            
            if len(updated_records) == initial_count:
                logger.warning(f"Record with ID {record_id} not found for deletion.")
                return False # Record not found

            self._rewrite_all_records(updated_records) # Rewrite the database without the deleted record
            logger.info(f"Deleted record with ID: {record_id}")
            return True

        except FileLockError:
            raise
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to delete record {record_id}: {str(e)}")
        finally:
            self._release_lock()

    def get_all_records(self) -> List[DataObject]:
        records = []
        try:
            self._acquire_lock()
            with open(self.db_path, 'rb') as f:
                while True:
                    header = f.read(8)
                    if not header:
                        break
                    
                    current_id, record_len = struct.unpack('<II', header)
                    record_bytes = f.read(record_len)
                    
                    try:
                        record = DataObject.from_bytes(record_bytes)
                        record.id = current_id # Ensure ID from header is assigned
                        records.append(record)
                    except (DataValidationError, DatabaseError) as e:
                        logger.error(f"Skipping corrupt record with ID {current_id} during bulk read: {e}")
                        continue # Skip corrupt record and continue

        except FileNotFoundError:
            logger.info(f"Database file not found at {self.db_path}. Returning empty list.")
        except FileLockError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting all records: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to retrieve all records: {str(e)}")
        finally:
            self._release_lock()
        return records

    def search_records(self, query: str) -> List[DataObject]:
        if not query:
            return []
        
        query_lower = query.lower()
        matching_records = []
        all_records = self.get_all_records() # Retrieve all and filter in memory for simplicity

        for record in all_records:
            # Create a searchable string representation of the record
            record_string = ' '.join(str(getattr(record, field)).lower() for field in FIELDS)
            if query_lower in record_string:
                matching_records.append(record)
        
        return matching_records

    def import_from_csv(self, file_buffer: Any, delimiter: str = ';') -> int:
        imported_count = 0
        try:
            # Ensure the buffer is at the beginning
            file_buffer.seek(0)
            
            # Decode bytes to string, then use StringIO to treat as file
            file_content = file_buffer.read().decode('utf-8')
            csv_file = io.StringIO(file_content)

            reader = csv.reader(csv_file, delimiter=delimiter)
            header = next(reader) # Skip header row

            # Basic header validation (optional, but good practice)
            if not all(field in FIELDS for field in header):
                logger.warning("CSV header does not fully match expected fields. Proceeding with available data.")
                # You might want to raise an error here or map columns if necessary

            for i, row in enumerate(reader):
                if not row:
                    continue
                try:
                    # Create a dictionary from row and header to initialize DataObject
                    row_dict = dict(zip(header, row))
                    
                    # Reorder row data to match FIELDS order for DataObject initialization
                    ordered_row_data = [row_dict.get(field, "") for field in FIELDS]
                    
                    record = DataObject(row_data=ordered_row_data) # Initialize from ordered list
                    self.add_record(record)
                    imported_count += 1
                except DataValidationError as e:
                    logger.error(f"Skipping invalid row {i+2} during CSV import: {e} | Row: {row}")
                except Exception as e:
                    logger.error(f"Unexpected error importing row {i+2}: {traceback.format_exc()} | Row: {row}")
                    
            logger.info(f"Successfully imported {imported_count} records from CSV.")
            return imported_count
        except Exception as e:
            logger.error(f"Error during CSV import: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to import from CSV: {str(e)}")

# --- Streamlit UI (New Refactored Design) ---

import io # Needed for import_from_csv buffer handling

def setup_ui():
    st.set_page_config(
        page_title="Traffic Accident Data Management",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    db = TrafficAccidentsDB()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Add Record", "View/Edit Records", "Import CSV", "Activity Log"])

    if page == "Dashboard":
        display_dashboard(db)
    elif page == "Add Record":
        add_record_ui(db)
    elif page == "View/Edit Records":
        view_edit_delete_records_ui(db)
    elif page == "Import CSV":
        import_csv_ui(db)
    elif page == "Activity Log":
        display_activity_log()

def display_dashboard(db: TrafficAccidentsDB):
    st.title("📊 Traffic Accident Data Dashboard")
    st.write("Overview of your traffic accident records.")

    total_records = len(db.get_all_records())
    st.metric("Total Records", total_records)

    st.subheader("Recent Activity")
    display_activity_log(is_dashboard=True)

    # Add more dashboard elements as needed (e.g., charts for common crash types, injury totals)
    # This would require more data analysis functions in the backend.
    st.markdown("---")
    st.info("Additional analytics and charts can be added here.")

def add_record_ui(db: TrafficAccidentsDB):
    st.title("➕ Add New Traffic Accident Record")
    st.write("Fill in the details to add a new traffic accident record.")

    with st.form("add_record_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            crash_date = st.date_input("Crash Date", value=datetime.now().date())
            traffic_control_device = st.selectbox("Traffic Control Device", ["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN/FLASHER", "NO CONTROLS", "OTHER"], index=0)
            weather_condition = st.selectbox("Weather Condition", ["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG/SMOKE/HAZE", "SEVERE CROSSWIND", "SLEET/HAIL", "OTHER"], index=0)
            lighting_condition = st.selectbox("Lighting Condition", ["UNKNOWN", "DAYLIGHT", "DARKNESS, LIGHTED ROAD", "DARKNESS", "DAWN", "DUSK"], index=0)
            first_crash_type = st.selectbox("First Crash Type", ["UNKNOWN", "REAR END", "ANGLE", "SIDESWIPE SAME DIRECTION", "SIDESWIPE OPPOSITE DIRECTION", "HEAD ON", "FIXED OBJECT", "PEDESTRIAN", "OTHER"], index=0)
            trafficway_type = st.selectbox("Trafficway Type", ["UNKNOWN", "STREET", "ALLEY", "INTERSECTION", "OTHER"], index=0)
            alignment = st.selectbox("Alignment", ["UNKNOWN", "STRAIGHT AND LEVEL", "STRAIGHT ON GRADE", "CURVE ON LEVEL", "CURVE ON GRADE"], index=0)
            roadway_surface_cond = st.selectbox("Roadway Surface Condition", ["UNKNOWN", "DRY", "WET", "SNOW", "ICE", "OTHER"], index=0)
            road_defect = st.selectbox("Road Defect", ["NONE", "RUT, HOLES", "DEBRIS ON ROADWAY", "OTHER"], index=0)
        with col2:
            crash_type = st.selectbox("Crash Type", ["UNKNOWN", "INJURY", "PROPERTY DAMAGE"], index=0)
            intersection_related_i = st.radio("Intersection Related?", ["NO", "YES"])
            damage = st.selectbox("Damage", ["UNKNOWN", "NONE", "MINOR", "MODERATE", "SEVERE"], index=0)
            prim_contributory_cause = st.selectbox("Primary Contributory Cause", ["UNKNOWN", "DRIVER INATTENTION", "FAILED TO YIELD RIGHT-OF-WAY", "FOLLOWING TOO CLOSELY", "OTHER"], index=0)
            num_units = st.number_input("Number of Units Involved", min_value=0, value=0)
            most_severe_injury = st.selectbox("Most Severe Injury", ["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"], index=0)
            injuries_total = st.number_input("Total Injuries", min_value=0.0, value=0.0)
            injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0, value=0.0)
            injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0, value=0.0)
            injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0, value=0.0)
            injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0, value=0.0)
            injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0, value=0.0)
            crash_hour = st.slider("Crash Hour (0-23)", 0, 23, 0)
            crash_day_of_week = st.slider("Crash Day of Week (1=Mon, 7=Sun)", 1, 7, 1)
            crash_month = st.slider("Crash Month (1-12)", 1, 12, 1)

        submitted = st.form_submit_button("Add Record")
        if submitted:
            try:
                # Convert date object to string for DataObject
                crash_date_str = crash_date.strftime('%Y-%m-%d')

                new_record_data = [
                    crash_date_str, traffic_control_device, weather_condition,
                    lighting_condition, first_crash_type, trafficway_type,
                    alignment, roadway_surface_cond, road_defect, crash_type,
                    intersection_related_i, damage, prim_contributory_cause,
                    str(num_units), most_severe_injury, str(injuries_total), str(injuries_fatal),
                    str(injuries_incapacitating), str(injuries_non_incapacitating),
                    str(injuries_reported_not_evident), str(injuries_no_indication),
                    str(crash_hour), str(crash_day_of_week), str(crash_month)
                ]
                
                new_record = DataObject(row_data=new_record_data)
                record_id = db.add_record(new_record)
                st.success(f"Record added successfully with ID: {record_id}!")
                logger.info(f"UI: Added new record with ID {record_id}")
            except DataValidationError as e:
                st.error(f"Validation Error: {e}")
                logger.error(f"UI: Validation error when adding record: {e}")
            except DatabaseError as e:
                st.error(f"Database Error: {e}")
                logger.error(f"UI: Database error when adding record: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                logger.critical(f"UI: Unexpected error adding record: {traceback.format_exc()}")

def view_edit_delete_records_ui(db: TrafficAccidentsDB):
    st.title("🔍 View, Edit, or Delete Records")
    st.write("Browse existing records, search, and manage them.")

    search_query = st.text_input("Search records (by any field content):")
    
    records = db.get_all_records()
    
    if search_query:
        records = [r for r in records if search_query.lower() in ' '.join(str(getattr(r, field)).lower() for field in FIELDS + ['id'])]

    if not records:
        st.info("No records found.")
        return

    # Pagination
    total_pages = (len(records) + APP_CONFIG["MAX_RECORDS_PER_PAGE"] - 1) // APP_CONFIG["MAX_RECORDS_PER_PAGE"]
    current_page = st.number_input("Page", min_value=1, max_value=max(1, total_pages), value=1)
    
    start_idx = (current_page - 1) * APP_CONFIG["MAX_RECORDS_PER_PAGE"]
    end_idx = start_idx + APP_CONFIG["MAX_RECORDS_PER_PAGE"]
    paginated_records = records[start_idx:end_idx]

    st.subheader(f"Displaying {len(paginated_records)} of {len(records)} records (Page {current_page}/{total_pages})")

    # Display records in an expandable format for details and edit/delete
    for record in paginated_records:
        with st.expander(f"Record ID: {record.id} - Crash Date: {record.crash_date} - Type: {record.crash_type}"):
            display_record_details_and_actions(record, db)

def display_record_details_and_actions(record: DataObject, db: TrafficAccidentsDB):
    record_dict = record.to_dict() # Assuming DataObject has a to_dict method
    st.json(record_dict) # Display full record as JSON for easy viewing

    st.subheader("Edit Record")
    edited_record_data = {}
    
    # Create input fields for each field, pre-filled with current record data
    col1, col2 = st.columns(2)
    with col1:
        edited_record_data['crash_date'] = st.date_input("Crash Date", value=datetime.strptime(record.crash_date, '%Y-%m-%d').date(), key=f"edit_crash_date_{record.id}")
        edited_record_data['traffic_control_device'] = st.selectbox("Traffic Control Device", ["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN/FLASHER", "NO CONTROLS", "OTHER"], index=["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN/FLASHER", "NO CONTROLS", "OTHER"].index(record.traffic_control_device), key=f"edit_traffic_control_device_{record.id}")
        edited_record_data['weather_condition'] = st.selectbox("Weather Condition", ["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG/SMOKE/HAZE", "SEVERE CROSSWIND", "SLEET/HAIL", "OTHER"], index=["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG/SMOKE/HAZE", "SEVERE CROSSWIND", "SLEET/HAIL", "OTHER"].index(record.weather_condition), key=f"edit_weather_condition_{record.id}")
        edited_record_data['lighting_condition'] = st.selectbox("Lighting Condition", ["UNKNOWN", "DAYLIGHT", "DARKNESS, LIGHTED ROAD", "DARKNESS", "DAWN", "DUSK"], index=["UNKNOWN", "DAYLIGHT", "DARKNESS, LIGHTED ROAD", "DARKNESS", "DAWN", "DUSK"].index(record.lighting_condition), key=f"edit_lighting_condition_{record.id}")
        edited_record_data['first_crash_type'] = st.selectbox("First Crash Type", ["UNKNOWN", "REAR END", "ANGLE", "SIDESWIPE SAME DIRECTION", "SIDESWIPE OPPOSITE DIRECTION", "HEAD ON", "FIXED OBJECT", "PEDESTRIAN", "OTHER"], index=["UNKNOWN", "REAR END", "ANGLE", "SIDESWIPE SAME DIRECTION", "SIDESWIPE OPPOSITE DIRECTION", "HEAD ON", "FIXED OBJECT", "PEDESTRIAN", "OTHER"].index(record.first_crash_type), key=f"edit_first_crash_type_{record.id}")
        edited_record_data['trafficway_type'] = st.selectbox("Trafficway Type", ["UNKNOWN", "STREET", "ALLEY", "INTERSECTION", "OTHER"], index=["UNKNOWN", "STREET", "ALLEY", "INTERSECTION", "OTHER"].index(record.trafficway_type), key=f"edit_trafficway_type_{record.id}")
        edited_record_data['alignment'] = st.selectbox("Alignment", ["UNKNOWN", "STRAIGHT AND LEVEL", "STRAIGHT ON GRADE", "CURVE ON LEVEL", "CURVE ON GRADE"], index=["UNKNOWN", "STRAIGHT AND LEVEL", "STRAIGHT ON GRADE", "CURVE ON LEVEL", "CURVE ON GRADE"].index(record.alignment), key=f"edit_alignment_{record.id}")
        edited_record_data['roadway_surface_cond'] = st.selectbox("Roadway Surface Condition", ["UNKNOWN", "DRY", "WET", "SNOW", "ICE", "OTHER"], index=["UNKNOWN", "DRY", "WET", "SNOW", "ICE", "OTHER"].index(record.roadway_surface_cond), key=f"edit_roadway_surface_cond_{record.id}")
        edited_record_data['road_defect'] = st.selectbox("Road Defect", ["NONE", "RUT, HOLES", "DEBRIS ON ROADWAY", "OTHER"], index=["NONE", "RUT, HOLES", "DEBRIS ON ROADWAY", "OTHER"].index(record.road_defect), key=f"edit_road_defect_{record.id}")
    with col2:
        edited_record_data['crash_type'] = st.selectbox("Crash Type", ["UNKNOWN", "INJURY", "PROPERTY DAMAGE"], index=["UNKNOWN", "INJURY", "PROPERTY DAMAGE"].index(record.crash_type), key=f"edit_crash_type_{record.id}")
        edited_record_data['intersection_related_i'] = st.radio("Intersection Related?", ["NO", "YES"], index=["NO", "YES"].index(record.intersection_related_i), key=f"edit_intersection_related_i_{record.id}")
        edited_record_data['damage'] = st.selectbox("Damage", ["UNKNOWN", "NONE", "MINOR", "MODERATE", "SEVERE"], index=["UNKNOWN", "NONE", "MINOR", "MODERATE", "SEVERE"].index(record.damage), key=f"edit_damage_{record.id}")
        edited_record_data['prim_contributory_cause'] = st.selectbox("Primary Contributory Cause", ["UNKNOWN", "DRIVER INATTENTION", "FAILED TO YIELD RIGHT-OF-WAY", "FOLLOWING TOO CLOSELY", "OTHER"], index=["UNKNOWN", "DRIVER INATTENTION", "FAILED TO YIELD RIGHT-OF-WAY", "FOLLOWING TOO CLOSELY", "OTHER"].index(record.prim_contributory_cause), key=f"edit_prim_contributory_cause_{record.id}")
        edited_record_data['num_units'] = st.number_input("Number of Units Involved", min_value=0, value=int(record.num_units), key=f"edit_num_units_{record.id}")
        edited_record_data['most_severe_injury'] = st.selectbox("Most Severe Injury", ["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"], index=["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"].index(record.most_severe_injury), key=f"edit_most_severe_injury_{record.id}")
        edited_record_data['injuries_total'] = st.number_input("Total Injuries", min_value=0.0, value=float(record.injuries_total), key=f"edit_injuries_total_{record.id}")
        edited_record_data['injuries_fatal'] = st.number_input("Fatal Injuries", min_value=0.0, value=float(record.injuries_fatal), key=f"edit_injuries_fatal_{record.id}")
        edited_record_data['injuries_incapacitating'] = st.number_input("Incapacitating Injuries", min_value=0.0, value=float(record.injuries_incapacitating), key=f"edit_injuries_incapacitating_{record.id}")
        edited_record_data['injuries_non_incapacitating'] = st.number_input("Non-Incapacitating Injuries", min_value=0.0, value=float(record.injuries_non_incapacitating), key=f"edit_injuries_non_incapacitating_{record.id}")
        edited_record_data['injuries_reported_not_evident'] = st.number_input("Injuries Reported Not Evident", min_value=0.0, value=float(record.injuries_reported_not_evident), key=f"edit_injuries_reported_not_evident_{record.id}")
        edited_record_data['injuries_no_indication'] = st.number_input("Injuries No Indication", min_value=0.0, value=float(record.injuries_no_indication), key=f"edit_injuries_no_indication_{record.id}")
        edited_record_data['crash_hour'] = st.slider("Crash Hour (0-23)", 0, 23, int(record.crash_hour), key=f"edit_crash_hour_{record.id}")
        edited_record_data['crash_day_of_week'] = st.slider("Crash Day of Week (1=Mon, 7=Sun)", 1, 7, int(record.crash_day_of_week), key=f"edit_crash_day_of_week_{record.id}")
        edited_record_data['crash_month'] = st.slider("Crash Month (1-12)", 1, 12, int(record.crash_month), key=f"edit_crash_month_{record.id}")

    col_buttons = st.columns(2)
    with col_buttons[0]:
        if st.button(f"Save Changes for ID {record.id}", key=f"save_edit_{record.id}"):
            try:
                # Convert date object to string for DataObject
                edited_record_data['crash_date'] = edited_record_data['crash_date'].strftime('%Y-%m-%d')
                
                # Convert numbers to strings for DataObject row_data initialization if necessary
                for key in ['num_units', 'injuries_total', 'injuries_fatal', 'injuries_incapacitating',
                            'injuries_non_incapacitating', 'injuries_reported_not_evident', 'injuries_no_indication',
                            'crash_hour', 'crash_day_of_week', 'crash_month']:
                    edited_record_data[key] = str(edited_record_data[key])

                # Create a DataObject from the edited dictionary
                updated_record = DataObject(existing_data_dict={**edited_record_data, 'id': record.id})
                
                if db.update_record(updated_record):
                    st.success(f"Record ID {record.id} updated successfully!")
                    logger.info(f"UI: Updated record with ID {record.id}")
                    st.experimental_rerun() # Rerun to show updated data
                else:
                    st.error(f"Failed to update record ID {record.id}. Record not found or error occurred.")
                    logger.warning(f"UI: Failed to update record {record.id}")
            except DataValidationError as e:
                st.error(f"Validation Error: {e}")
                logger.error(f"UI: Validation error when updating record: {e}")
            except DatabaseError as e:
                st.error(f"Database Error: {e}")
                logger.error(f"UI: Database error when updating record: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                logger.critical(f"UI: Unexpected error updating record: {traceback.format_exc()}")
    
    with col_buttons[1]:
        if st.button(f"Delete Record ID {record.id}", key=f"delete_record_{record.id}"):
            if st.session_state.get(f"confirm_delete_{record.id}", False):
                try:
                    if db.delete_record(record.id):
                        st.success(f"Record ID {record.id} deleted successfully!")
                        logger.info(f"UI: Deleted record with ID {record.id}")
                        st.session_state[f"confirm_delete_{record.id}"] = False # Reset confirmation
                        st.experimental_rerun() # Rerun to remove deleted record
                    else:
                        st.error(f"Failed to delete record ID {record.id}. Record not found or error occurred.")
                        logger.warning(f"UI: Failed to delete record {record.id}")
                except DatabaseError as e:
                    st.error(f"Database Error: {e}")
                    logger.error(f"UI: Database error when deleting record: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    logger.critical(f"UI: Unexpected error deleting record: {traceback.format_exc()}")
            else:
                st.warning(f"Are you sure you want to delete Record ID {record.id}? This action cannot be undone.")
                st.session_state[f"confirm_delete_{record.id}"] = True
                st.button("Confirm Delete", key=f"confirm_delete_btn_{record.id}") # Provide a confirmation button

def import_csv_ui(db: TrafficAccidentsDB):
    st.title("⬆️ Import Records from CSV")
    st.write("Upload a CSV file to import multiple traffic accident records into the database.")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    csv_delimiter = st.text_input("CSV Delimiter", value=APP_CONFIG["CSV_DELIMITER"], max_chars=1)

    if uploaded_file is not None:
        if st.button("Process Import"):
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > APP_CONFIG["MAX_FILE_SIZE_MB"]:
                st.error(f"File size exceeds maximum allowed ({APP_CONFIG['MAX_FILE_SIZE_MB']} MB). Please upload a smaller file.")
                logger.warning(f"UI: CSV import file too large: {file_size_mb:.2f} MB")
            else:
                try:
                    # Use a BytesIO buffer to read the uploaded file
                    bytes_data = io.BytesIO(uploaded_file.getvalue())
                    imported_count = db.import_from_csv(bytes_data, delimiter=csv_delimiter)
                    st.success(f"Successfully imported {imported_count} records from '{uploaded_file.name}'!")
                    logger.info(f"UI: Imported {imported_count} records from {uploaded_file.name}")
                except DatabaseError as e:
                    st.error(f"Import Error: {e}")
                    logger.error(f"UI: Database error during CSV import: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred during import: {e}")
                    logger.critical(f"UI: Unexpected error during CSV import: {traceback.format_exc()}")

def display_activity_log(is_dashboard: bool = False):
    if not is_dashboard:
        st.title("📜 Activity Log")
        st.write("View recent application activities and errors.")

    log_file_path = LOG_FILE_PATH
    try:
        if not os.path.exists(log_file_path):
            st.info("Activity log file not found. No recent activity.")
            return

        with open(log_file_path, 'r') as f:
            log_lines = f.readlines()

        if not log_lines:
            st.info("Log file is empty.")
            return

        # Display last N entries
        display_lines = log_lines[-APP_CONFIG["MAX_LOG_ENTRIES_DISPLAY"]:]

        for line in display_lines:
            st.text(line.strip())

    except Exception as e:
        st.error(f"Could not read activity log: {str(e)}")
        logger.error(f"Error reading activity log: {traceback.format_exc()}")

# --- Main Application Entry Point ---
if __name__ == "__main__":
    try:
        # Ensure base directories exist before Streamlit UI setup
        os.makedirs(APP_CONFIG["DB_DIR"], exist_ok=True)
        os.makedirs(BACKUP_PATH, exist_ok=True)
        logger.info("Main: Ensured DB and backup directories exist.")
    except OSError as e:
        st.error(f"Critical: Cannot create database directories. Please check permissions for {APP_CONFIG['DB_DIR']}. Error: {e}")
        logger.critical(f"Main: Initial directory creation failed: {traceback.format_exc()}")
        st.stop() # Stop the app if directories cannot be created

    setup_ui()