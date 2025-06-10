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
import shutil # For file operations like copy2 during restore
import tempfile
import traceback

# --- Configuration Constants (Centralized) ---
APP_CONFIG = {
    "DB_DIR": os.path.join(Path.home(), 'Documents', 'Data'),
    "DB_FILE_NAME": 'traffic_accidents.db',
    "INDEX_FILE_NAME": 'index.idx',
    "LOCK_FILE_NAME": 'traffic_accidents.lock',
    "ID_COUNTER_FILE_NAME": 'id_counter.dat', # File for auto-increment ID
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

# --- Data Fields ---
# Define all fields for the DataObject and their expected types/validation rules
# These fields are used for internal DataObject structure and CSV mapping
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

# --- DataObject Class (Unified and Optimized from v5alpha0.1.b.py) ---
class DataObject:
    """
    Represents a traffic accident record with enhanced validation and serialization.
    Each instance corresponds to a single record in the database.
    Includes an 'id' field for unique identification.
    """

    def __init__(self, row_data: Optional[List[str]] = None, existing_data_dict: Optional[Dict[str, Any]] = None):
        """
        Initializes a DataObject.
        Can be initialized from a list of row data (e.g., from CSV) or an existing dictionary.
        """
        self.id: Optional[int] = None # Unique ID for the record, assigned by DB
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

        # Perform comprehensive validation after initialization
        if not self.validate():
            raise DataValidationError("Data validation failed after initialization.")

    def _initialize_defaults(self):
        """Initializes all fields with safe and type-appropriate default values."""
        # Initialize fields based on FIELDS list
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
        """
        Populates object fields from a list of strings (e.g., from a CSV row).
        Performs basic type conversion and uses validation helpers.
        """
        if len(row_data) != len(FIELDS):
            raise ValueError(f"Expected {len(FIELDS)} fields, but got {len(row_data)}.")

        # Processed data: strip whitespace and convert empty strings to None
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
        self.crash_type = self._validate_string(processed_data[9], "crash_type", allow_empty=False) # Required field
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
        self.crash_day_of_week = self._validate_range(processed_data[22], "crash_day_of_week", 1, 7) # 1=Monday, 7=Sunday
        self.crash_month = self._validate_range(processed_data[23], "crash_month", 1, 12)

    def _initialize_from_dict(self, data_dict: Dict[str, Any]):
        """
        Populates object fields from a dictionary (e.g., from JSON deserialization).
        Assumes dictionary keys match field names.
        """
        # Set the ID first if present
        retrieved_id = data_dict.get('id', data_dict.get('record_id')) # Allow 'record_id' for compatibility
        if retrieved_id is not None:
            try:
                self.id = int(retrieved_id)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert 'id' ({retrieved_id}) to integer during DataObject init from dict. Setting to None.")
                self.id = None
        else:
            self.id = None # Default to None if not present

        for field in FIELDS:
            if field in data_dict:
                # Direct assignment for most fields, validation happens in .validate()
                # Special handling for date, numbers where type conversion is needed
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
                # Default values already set by _initialize_defaults

    @staticmethod
    def _validate_date(date_str: Optional[str]) -> str:
        """
        Validates and standardizes a date string to-MM-DD format.
        Handles various common input formats including those with time and AM/PM.
        Raises DataValidationError if a non-empty string cannot be parsed.
        """
        if not date_str:
            return ""

        date_str = date_str.strip()
        if not date_str: # After stripping, if it becomes empty
            return ""

        # Try multiple common date and datetime formats
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d',
                    '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', # 24-hour time
                    '%m/%d/%Y %I:%M:%S %p', '%Y-%m-%d %I:%M:%S %p'): # 12-hour time with AM/PM
            try:
                dt = datetime.strptime(date_str, fmt)
                formatted_date = dt.strftime('%Y-%m-%d') # Always store as-MM-DD
                return formatted_date
            except ValueError:
                continue # Try next format

        # If execution reaches here, it means date_str was not empty but could not be parsed
        raise DataValidationError(f"Invalid date format: '{date_str}'. Expected-MM-DD or common date/datetime format (e.g., MM/DD/YYYY, DD-MM-YYYY, or with time/AM/PM).")

    @staticmethod
    def _validate_string(value: Optional[str], field_name: str, max_len: int = 255, allow_empty: bool = True) -> str:
        """
        Validates and sanitizes string fields.
        Converts None to "UNKNOWN" if not allowed to be empty.
        Truncates to max_len and removes problematic characters.
        """
        if value is None:
            return "UNKNOWN" if not allow_empty else ""

        value = str(value).strip()

        if not value:
            return "UNKNOWN" if not allow_empty else ""

        # Basic sanitization: remove delimiters and newlines that could break CSV/JSON
        value = value.replace(APP_CONFIG["CSV_DELIMITER"], ',').replace('\n', ' ').replace('\r', '')

        return value[:max_len] # Truncate to max_len

    @staticmethod
    def _validate_yes_no(value: Optional[str]) -> str:
        """Validates input for 'Yes'/'No' fields."""
        if value is None:
            return "NO"

        value = str(value).strip().lower()
        return "YES" if value in ('yes', 'y', 'true', '1') else "NO"

    @staticmethod
    def _validate_positive_int(value: Optional[str], field_name: str, min_val: int = 0) -> int:
        """Validates and converts a value to a non-negative integer."""
        try:
            # Handle empty string or None by returning min_val
            if value is None or value == '':
                return min_val

            num = int(float(value)) # Convert via float to handle "5.0"
            return max(num, min_val) # Ensure it's not less than min_val
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    @staticmethod
    def _validate_positive_float(value: Optional[str], field_name: str, min_val: float = 0.0) -> float:
        """Validates and converts a value to a non-negative float."""
        try:
            # Handle empty string or None by returning min_val
            if value is None or value == '':
                return min_val

            num = float(value)
            return max(round(num, 2), min_val) # Round and ensure it's not less than min_val
        except (ValueError, TypeError):
            logger.warning(f"Invalid float value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    @staticmethod
    def _validate_range(value: Optional[str], field_name: str, min_val: int, max_val: int) -> int:
        """Validates a numeric field to be within a specific integer range."""
        try:
            # Handle empty string or None by returning min_val
            if value is None or value == '':
                return min_val

            num = int(float(value)) # Convert via float to handle "12.0"
            return min(max(num, min_val), max_val) # Ensure it's within [min_val, max_val]
        except (ValueError, TypeError):
            logger.warning(f"Invalid numeric value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    def validate(self) -> bool:
        """
        Performs comprehensive semantic validation on the DataObject's fields.
        Ensures consistency and correctness of data.
        """
        try:
            # 1. Required fields check
            if not self.crash_date:
                raise DataValidationError("Crash date is required.")
            if not self.crash_type or self.crash_type == "UNKNOWN":
                raise DataValidationError("Crash type is required.")
            if not isinstance(self.num_units, int) or self.num_units < 0:
                raise DataValidationError("Number of units must be a non-negative integer.")
            if not isinstance(self.injuries_total, (int, float)) or self.injuries_total < 0:
                raise DataValidationError("Total injuries must be a non-negative number.")

            # 2. Date format validation (already done by _validate_date but double-check)
            if self.crash_date: # Only check if not empty
                try:
                    datetime.strptime(self.crash_date, '%Y-%m-%d')
                except ValueError:
                    raise DataValidationError("Invalid crash date format (expected-MM-DD).")

            # 3. Consistency checks for injuries
            total_reported_injuries = (
                self.injuries_fatal + self.injuries_incapacitating +
                self.injuries_non_incapacitating + self.injuries_reported_not_evident +
                self.injuries_no_indication
            )
            # Allow for slight floating point inaccuracies or where total includes unclassified injuries
            if self.injuries_total < total_reported_injuries - 0.01: # Small tolerance for float comparison
                logger.warning(f"Total injuries ({self.injuries_total}) less than sum of specific injuries ({total_reported_injuries}).")
                # For now, this is a warning, not an error that fails validation.
                # Could be changed to an error if strict consistency is required.

            # 4. Range validation (already done by _validate_range, but for robustness)
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

    def to_dict(self) -> Dict[str, Any]:
        """Converts the DataObject instance into a dictionary, including its ID."""
        data = {field: getattr(self, field) for field in FIELDS}
        if self.id is not None:
            data['id'] = self.id # Include ID in the dictionary representation
        return data

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'DataObject':
        """Creates a DataObject instance from a dictionary."""
        # The constructor already handles 'id' from existing_data_dict
        return cls(existing_data_dict=data_dict)

    def __repr__(self) -> str:
        """Provides a string representation of the DataObject for debugging."""
        return f"DataObject(ID={self.id}, Date='{self.crash_date}', Type='{self.crash_type}', TotalInjuries={self.injuries_total})"

# --- Database Class (from v5alpha0.1.b.py, optimized for DataObject and ID management) ---
# Data Structure: record_id (unsigned long long - 8 bytes), timestamp (double), data_hash (32 bytes for hex hash), is_valid (boolean)
RECORD_FORMAT = "<Q d 32s ?"
RECORD_HEADER_SIZE = struct.calcsize(RECORD_FORMAT)

class TrafficAccidentsDB:
    """
    Handles all database operations for traffic accident records.
    Implements file-based storage with robust locking, backups, indexing,
    and auto-increment ID management.
    """
    def __init__(self, db_file: str, index_file: str, lock_file: str, id_counter_file: str, backup_dir: str):
        self.db_file = db_file
        self.index_file = index_file
        self.lock_file = lock_file
        self.id_counter_file = id_counter_file
        self.backup_dir = backup_dir
        self._index_cache: Dict[int, int] = {}  # In-memory cache for the index (ID -> Position)
        self._current_id = 0  # Auto-increment ID counter

        self._ensure_directories()
        self._initialize_db_file()
        self._load_id_counter()
        self._lock = filelock.FileLock(self.lock_file) # Initialize filelock here
        self.rebuild_index() # Rebuild index on init to ensure consistency

    def _ensure_directories(self):
        """Ensures the database and index directories exist."""
        try:
            Path(self.db_file).parent.mkdir(parents=True, exist_ok=True)
            Path(self.index_file).parent.mkdir(parents=True, exist_ok=True)
            Path(self.id_counter_file).parent.mkdir(parents=True, exist_ok=True)
            Path(self.backup_dir).mkdir(parents=True, exist_ok=True) # Ensure backup dir exists
            logger.info("Ensured all necessary directories exist.")
        except OSError as e:
            logger.critical(f"Critical: Cannot create database directories. Error: {e}")
            raise DatabaseError(f"Failed to create necessary directories: {str(e)}")

    def _initialize_db_file(self):
        """Creates the database file if it doesn't exist."""
        if not Path(self.db_file).exists():
            try:
                with open(self.db_file, 'wb') as f:
                    pass  # Create an empty file
                logger.info(f"Database file created: {self.db_file}")
            except IOError as e:
                logger.critical(f"Critical: Cannot create database file {self.db_file}. Error: {e}")
                raise DatabaseError(f"Failed to create database file: {str(e)}")

    def _load_id_counter(self):
        """Loads the last used ID from the counter file."""
        if Path(self.id_counter_file).exists():
            try:
                with self._lock.acquire(timeout=10): # Acquire lock to read ID counter
                    with open(self.id_counter_file, 'r') as f:
                        self._current_id = int(f.read().strip())
                logger.info(f"ID counter loaded: {self._current_id}")
            except (IOError, ValueError) as e:
                logger.error(f"Error loading ID counter from {self.id_counter_file}: {e}. Resetting to 0.")
                self._current_id = 0
            except filelock.Timeout:
                logger.error(f"Could not acquire lock for ID counter file {self.lock_file} to load counter.")
                self._current_id = 0 # Proceed with 0 if lock cannot be acquired
                raise FileLockError(f"Failed to load ID counter: {self.lock_file} timed out.") # Raise after logging
        else:
            logger.info("ID counter file does not exist. Starting ID from 0.")
            self._current_id = 0
            self._save_id_counter() # Create file with initial 0

    def _save_id_counter(self):
        """Saves the current ID counter to the file."""
        try:
            with self._lock.acquire(timeout=10): # Acquire lock to save ID counter
                with open(self.id_counter_file, 'w') as f:
                    f.write(str(self._current_id))
            logger.info(f"ID counter saved: {self._current_id}")
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for ID counter file {self.lock_file} to save counter.")
            raise FileLockError(f"Failed to save ID counter: {self.lock_file} timed out.") # Re-raise
        except IOError as e:
            logger.error(f"Error saving ID counter to {self.id_counter_file}: {e}")
            raise DatabaseError(f"Failed to save ID counter: {str(e)}")

    def _get_next_id(self) -> int:
        """Increments and returns the next ID."""
        self._current_id += 1
        self._save_id_counter()
        return self._current_id

    def _calculate_data_hash(self, data_dict: Dict[str, Any]) -> str:
        """Calculates SHA256 hash of the data content (excluding 'id')."""
        # Ensure 'id' field is not included in the hash calculation
        data_to_hash = {k: v for k, v in data_dict.items() if k != 'id'}
        data_string = json.dumps(data_to_hash, sort_keys=True).encode('utf-8')
        return hashlib.sha256(data_string).hexdigest()

    def _load_index_to_cache(self):
        """Loads the index file into the in-memory cache."""
        self._index_cache = {}
        if not Path(self.index_file).exists():
            logger.info("Index file does not exist. Starting with an empty index cache.")
            return

        try:
            with self._lock.acquire(timeout=10):
                with open(self.index_file, 'rb') as f_idx:
                    entry_size = struct.calcsize("<Q Q") # ID (Q) + Position (Q)
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
            self._index_cache = {} # Clear cache if lock fails
            raise FileLockError(f"Failed to load index: {self.lock_file} timed out.") # Re-raise
        except Exception as e:
            logger.error(f"Error loading index file {self.index_file} to cache: {e}")
            self._index_cache = {} # Clear cache if error occurs
            raise DatabaseError(f"Failed to load index: {str(e)}") # Re-raise for general errors

    def _save_index_from_cache(self):
        """Saves the in-memory index cache to the index file."""
        logger.info("Saving index cache to disk...")
        try:
            with self._lock.acquire(timeout=10):
                with open(self.index_file, 'wb') as f_idx:
                    for r_id, pos in self._index_cache.items():
                        f_idx.write(struct.pack("<Q Q", r_id, pos))
            logger.info(f"Index cache saved to disk. {len(self._index_cache)} entries.")
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for index file {self.lock_file} to save index cache.")
            raise FileLockError(f"Failed to save index: {self.lock_file} timed out.") # Re-raise
        except Exception as e:
            logger.error(f"Error saving index cache to file {self.index_file}: {e}")
            raise DatabaseError(f"Failed to save index: {str(e)}") # Re-raise

    def _update_index_cache_entry(self, record_id: int, position: int):
        """Updates a single entry in the in-memory index cache and saves it to disk."""
        self._index_cache[record_id] = position
        self._save_index_from_cache()

    def rebuild_index(self):
        """
        Rebuilds the index file from scratch, including only valid records.
        This updates the in-memory cache and then persists it to disk.
        Also updates the ID counter based on the maximum ID found.
        """
        logger.info("Rebuilding index file from DB and updating cache...")
        new_index_data = {}
        max_id_in_db = 0
        try:
            with self._lock.acquire(timeout=10):
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
                            logger.error(f"Failed to unpack header at position {start_pos}. Corrupted header. Skipping to next potential record.")
                            # Attempt to skip past the likely corrupted record to continue parsing
                            f_db.seek(start_pos + RECORD_HEADER_SIZE + 4 + APP_CONFIG["CHUNK_SIZE"]) # Skip header + size + a chunk of data
                            continue

                        data_size_bytes = f_db.read(4)
                        if not data_size_bytes or len(data_size_bytes) < 4:
                            logger.warning(f"Incomplete data size at position {f_db.tell()}. Skipping remaining file during index rebuild.")
                            break

                        try:
                            data_size = struct.unpack("<I", data_size_bytes)[0]
                        except struct.error:
                            logger.error(f"Failed to unpack data size at position {f_db.tell()}. Corrupted data size. Skipping.")
                            f_db.seek(f_db.tell() + APP_CONFIG["CHUNK_SIZE"]) # Skip some data
                            continue

                        f_db.seek(data_size, os.SEEK_CUR) # Skip past the data payload

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
            raise FileLockError(f"Failed to rebuild index: {self.lock_file} timed out.")
        except Exception as e:
            logger.error(f"Error rebuilding index: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to rebuild index: {str(e)}")

    def _insert_raw_record(self, record_data_dict: Dict[str, Any], record_id: Optional[int] = None, is_valid: bool = True) -> (int, int):
        """
        Internal method to insert a record into the .db file.
        If record_id is None, a new auto-increment ID is generated.
        Returns a tuple of (record_id, position_in_db).
        Accepts a dictionary of data to be stored.
        """
        if record_id is None:
            record_id = self._get_next_id()

        timestamp = datetime.now().timestamp()
        data_hash = self._calculate_data_hash(record_data_dict) # Hashing only content, not ID
        data_bytes = json.dumps(record_data_dict, sort_keys=True).encode('utf-8')
        data_size = len(data_bytes)

        record_header = struct.pack(
            RECORD_FORMAT,
            record_id,
            timestamp,
            bytes.fromhex(data_hash),
            is_valid
        )

        try:
            with self._lock.acquire(timeout=10):
                with open(self.db_file, 'ab') as f:
                    current_position = f.tell()
                    f.write(record_header)
                    f.write(struct.pack("<I", data_size)) # Write data size as 4-byte unsigned int
                    f.write(data_bytes)

            logger.info(f"Raw record {record_id} inserted at position {current_position}.")
            return record_id, current_position
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to insert raw record.")
            raise FileLockError(f"Failed to insert raw record: {self.lock_file} timed out.")
        except IOError as e:
            logger.error(f"IOError inserting raw record: {e}")
            raise DatabaseError(f"Failed to insert raw record: {str(e)}")
        except Exception as e:
            logger.error(f"Error inserting raw record: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to insert raw record: {str(e)}")

    def insert_data(self, data_object: DataObject) -> int:
        """
        Public method to insert a new DataObject.
        Assigns an ID to the DataObject and stores its dictionary representation.
        """
        if not data_object.validate():
            raise DataValidationError("Attempted to insert an invalid DataObject.")

        # Get dictionary representation of the DataObject
        data_dict = data_object.to_dict()
        # Remove 'id' from the dictionary that gets stored as data, as it's part of the record header.
        if 'id' in data_dict:
            del data_dict['id']

        record_id, position = self._insert_raw_record(data_dict, is_valid=True)
        data_object.id = record_id # Assign the newly generated ID back to the DataObject
        self._update_index_cache_entry(record_id, position)
        logger.info(f"New record inserted: ID {record_id}")
        return record_id

    def _read_raw_record_at_position(self, position: int) -> Optional[Dict[str, Any]]:
        """
        Reads a single raw record (header + data) from a specific byte position.
        Returns a dictionary containing record_id, timestamp, data_hash, is_valid, data_dict, and position.
        """
        try:
            with self._lock.acquire(timeout=10):
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
                        logger.warning(f"Incomplete data at position {f.tell()}. Expected {data_size} bytes, got {len(data_bytes)}. This record may be truncated.")
                        # Removed 'pass' as it's not strictly necessary here and might be causing parsing issues
                        

                    try:
                        data = json.loads(data_bytes.decode('utf-8'))
                    except json.JSONDecodeError:
                        logger.error(f"JSON decode error for record ID {record_id} at position {position}. Data might be corrupt.")
                        data = {} # Return empty data if corrupt
                    except UnicodeDecodeError:
                        logger.error(f"Unicode decode error for record ID {record_id} at position {position}. Data might be corrupt.")
                        data = {} # Return empty data if corrupt

                    timestamp = datetime.fromtimestamp(timestamp_float)
                    data_hash = data_hash_bytes.hex()
                    return {
                        "record_id": record_id,
                        "timestamp": timestamp,
                        "data_hash": data_hash,
                        "is_valid": is_valid,
                        "data": data, # This 'data' is the original dictionary content
                        "position": position
                    }
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to read raw record at position {position}.")
            raise FileLockError(f"Failed to read raw record: {self.lock_file} timed out.")
        except (IOError, struct.error) as e:
            logger.error(f"Data corruption or read error at position {position}: {e}. Record might be unreadable.")
            raise DatabaseError(f"Corrupt data or error reading record at position {position}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error reading raw record at position {position}: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to read raw record at position {position}: {str(e)}")

    def get_record_by_id(self, record_id: int) -> Optional[DataObject]:
        """
        Retrieves a single record by its ID using the index.
        Returns a DataObject instance.
        """
        position = self._index_cache.get(record_id) # Use in-memory index
        if position is None:
            logger.info(f"Record with ID {record_id} not found in index cache.")
            return None

        record_info = self._read_raw_record_at_position(position)
        if record_info and record_info["is_valid"]:
            # Combine record_id with data before passing to DataObject.from_dict
            full_data_dict = {"id": record_info["record_id"], **record_info["data"]}
            return DataObject.from_dict(full_data_dict)
        elif record_info and not record_info["is_valid"]:
            logger.info(f"Record ID {record_id} found but marked as invalid.")
        else:
            logger.warning(f"Record ID {record_id} not found at indexed position {position} or read failed.")
        return None

    def get_all_records(self) -> Dict[int, DataObject]:
        """
        Retrieves all valid records from the database using the index.
        Returns a dictionary mapping record ID to DataObject instance.
        """
        all_records = {}
        # Iterate over a copy of keys to avoid modification issues if index is rebuilt mid-loop
        for record_id in list(self._index_cache.keys()):
            record_obj = self.get_record_by_id(record_id)
            if record_obj: # Only add valid, successfully retrieved records
                all_records[record_id] = record_obj
        return all_records

    def update_record(self, record_id: int, new_data_object: DataObject) -> bool:
        """
        Updates an existing record.
        Marks the old record as invalid in the database file and inserts a new record
        with the same ID at the end of the file. The index is updated to point to the new location.
        """
        if not new_data_object.validate():
            raise DataValidationError("Attempted to update with an invalid DataObject.")

        old_position = self._index_cache.get(record_id)
        if old_position is None: # Corrected from '=== None' to 'is None'
            logger.warning(f"Attempted to update non-existent record with ID: {record_id}. Record not found in index.")
            return False

        try:
            with self._lock.acquire(timeout=10):
                self._create_backup_internal() # Create backup before modification

                # 1. Mark the old record as invalid
                with open(self.db_file, 'r+b') as f:
                    f.seek(old_position)
                    header_bytes = f.read(RECORD_HEADER_SIZE)
                    if not header_bytes or len(header_bytes) < RECORD_HEADER_SIZE:
                        logger.error(f"Incomplete header for record {record_id} at position {old_position} during update invalidation.")
                        return False

                    # Unpack, set is_valid to False, and repack
                    r_id, timestamp_float, data_hash_bytes, is_valid_old = struct.unpack(RECORD_FORMAT, header_bytes)

                    # Seek back to write only the is_valid flag (last byte of header)
                    f.seek(old_position + struct.calcsize("<Q d 32s"))
                    f.write(struct.pack("?", False))
                    f.flush()
                    os.fsync(f.fileno()) # Ensure write is flushed to disk

                logger.info(f"Marked old record {record_id} at position {old_position} as invalid.")

                # 2. Insert the new record with the same ID
                # Ensure the new_data_object's ID is set to the correct record_id for consistency
                new_data_object.id = record_id
                new_data_dict = new_data_object.to_dict()
                if 'id' in new_data_dict: # Remove ID from the stored data dict
                    del new_data_dict['id']

                # Insert the new record (will be appended to the end of the file)
                new_record_id, new_position = self._insert_raw_record(new_data_dict, record_id=record_id, is_valid=True)

                # 3. Update the in-memory index cache and persist for the SAME record_id
                self._update_index_cache_entry(new_record_id, new_position) # Index now points to the new position

            logger.info(f"Record {record_id} updated successfully. New position: {new_position}.")
            return True
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to update record.")
            raise FileLockError(f"Failed to update record: {self.lock_file} timed out.")
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to update record {record_id}: {str(e)}")

    def delete_record(self, record_id: int) -> bool:
        """
        Deletes a record by marking it as invalid in the database file
        and removing it from the in-memory index cache.
        """
        position = self._index_cache.get(record_id)
        if position is None:
            logger.warning(f"Attempted to delete non-existent record with ID: {record_id}. Record not found in index.")
            return False

        try:
            with self._lock.acquire(timeout=10):
                self._create_backup_internal() # Create backup before modification

                with open(self.db_file, 'r+b') as f:
                    f.seek(position)
                    header_bytes = f.read(RECORD_HEADER_SIZE)
                    if not header_bytes or len(header_bytes) < RECORD_HEADER_SIZE:
                        logger.error(f"Incomplete header for record {record_id} at position {position} during deletion invalidation.")
                        return False

                    # Unpack, set is_valid to False, and repack
                    r_id, timestamp_float, data_hash_bytes, is_valid_old = struct.unpack(RECORD_FORMAT, header_bytes)
                    f.seek(position + struct.calcsize("<Q d 32s")) # Seek to the boolean flag
                    f.write(struct.pack("?", False)) # Write False to mark as invalid
                    f.flush()
                    os.fsync(f.fileno()) # Ensure write is flushed to disk

                if record_id in self._index_cache:
                    del self._index_cache[record_id] # Remove from cache
                    self._save_index_from_cache() # Persist the change to the index file
                logger.info(f"Record {record_id} marked as invalid and removed from index.")
            return True
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to delete record.")
            raise FileLockError(f"Failed to delete record: {self.lock_file} timed out.")
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to delete record {record_id}: {str(e)}")

    def get_number_of_records(self) -> int:
        """Returns the total number of valid records in the database based on the index cache."""
        return len(self._index_cache)

    def search_records(self, query: str) -> List[DataObject]:
        """
        Searches for records where any string value in the data contains the query.
        Performs search on all valid records in the index cache. Case-insensitive search.
        Returns a list of DataObject instances.
        """
        results = []
        if not query:
            return results

        query_lower = query.lower()
        all_valid_records = self.get_all_records() # Get all valid DataObjects via index

        for record_obj in all_valid_records.values():
            found = False
            record_dict = record_obj.to_dict() # Get dictionary representation for searching
            for key, value in record_dict.items():
                if isinstance(value, str) and query_lower in value.lower():
                    found = True
                    break
                # Convert numbers to string for searching too
                elif isinstance(value, (int, float)) and query_lower in str(value).lower():
                    found = True
                    break
            if found:
                results.append(record_obj)

        return results

    def import_from_csv(self, file_path: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> int:
        """
        Imports data from a CSV file into the database with progress feedback.
        Each row is converted to a DataObject and inserted.
        """
        imported_count = 0
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > APP_CONFIG["MAX_FILE_SIZE_MB"]:
                st.error(f"Arquivo muito grande. O tamanho máximo permitido é {APP_CONFIG['MAX_FILE_SIZE_MB']} MB.") # Changed to st.error for immediate user feedback
                raise ValueError(f"O tamanho do arquivo excede o máximo permitido ({APP_CONFIG['MAX_FILE_SIZE_MB']}MB).")

            with open(file_path, 'r', encoding='utf-8') as csvfile_for_count:
                header = csvfile_for_count.readline()
                csvfile_for_count.seek(0)
                total_lines = sum(1 for _ in csvfile_for_count) - 1 # Subtract 1 for header
                if total_lines < 0: total_lines = 0

            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=APP_CONFIG["CSV_DELIMITER"])
                csv_header = next(reader) # Read actual CSV header

                if len(csv_header) < len(FIELDS):
                    logger.warning(f"CSV header has {len(csv_header)} columns, expected at least {len(FIELDS)}. Data may be incomplete.")

                for i, row in enumerate(reader):
                    if progress_callback:
                        progress_callback(i + 1, total_lines)

                    if not row: # Skip empty rows
                        continue

                    try:
                        if len(row) < len(FIELDS):
                            padded_row = row + [''] * (len(FIELDS) - len(row))
                            data_object = DataObject(row_data=padded_row)
                        else:
                            data_object = DataObject(row_data=row[:len(FIELDS)]) # Use only the expected number of fields

                        self.insert_data(data_object)
                        imported_count += 1
                    except (DataValidationError, ValueError) as e:
                        logger.warning(f"Skipping CSV row {i+2} due to validation/format error: {e} | Row: {row}")
                    except Exception as e:
                        logger.error(f"Unexpected error processing CSV row {i+2}: {traceback.format_exc()} | Row: {row}")

            self._create_backup_internal() # Create backup after successful import
            self.rebuild_index() # Rebuild index after import to reflect all new records
            logger.info(f"Successfully imported {imported_count} records from {file_path}.")
            return imported_count
        except FileNotFoundError:
            logger.error(f"CSV import failed: File not found {file_path}")
            raise DatabaseError(f"Arquivo CSV não encontrado em {file_path}")
        except Exception as e:
            logger.error(f"Error during CSV import from {file_path}: {traceback.format_exc()}")
            raise DatabaseError(f"Ocorreu um erro durante a importação CSV: {e}")

    def export_to_csv(self, output_file_path: str) -> bool:
        """Exports all valid records to a CSV file."""
        try:
            records = list(self.get_all_records().values()) # Get DataObject instances
            if not records:
                logger.info("No records to export.")
                return False

            fieldnames = FIELDS

            with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=APP_CONFIG["CSV_DELIMITER"])
                writer.writeheader()
                for record_obj in records:
                    record_data_for_csv = {field: getattr(record_obj, field) for field in FIELDS}
                    writer.writerow(record_data_for_csv)
            logger.info(f"Successfully exported {len(records)} records to {output_file_path}.")
            return True
        except Exception as e:
            logger.error(f"Error during CSV export to {output_file_path}: {traceback.format_exc()}")
            raise DatabaseError(f"Ocorreu um erro durante a exportação CSV: {e}")

    def _create_backup_internal(self):
        """Internal helper to create a timestamped backup of the database file and manages backup rotation."""
        try:
            if not os.path.exists(self.db_file):
                logger.info("No database file found to backup internally.")
                return

            # Clean up old backups first
            backups = sorted(
                [f for f in os.listdir(self.backup_dir) if f.startswith('backup_') and f.endswith('.db')],
                key=lambda f: os.path.getmtime(os.path.join(self.backup_dir, f))
            )
            while len(backups) >= APP_CONFIG["MAX_BACKUPS"]:
                oldest = os.path.join(self.backup_dir, backups.pop(0))
                try:
                    os.unlink(oldest)
                    logger.info(f"Removed old database backup: {oldest}")
                except OSError as e:
                    logger.warning(f"Could not remove old backup '{oldest}': {e}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}.db")

            with self._lock.acquire(timeout=10):
                shutil.copy2(self.db_file, backup_path) # More robust copy
                logger.info(f"Created internal database backup: {backup_path}")
        except filelock.Timeout:
            logger.error(f"Could not acquire lock for database file {self.lock_file} to create internal backup.")
            raise FileLockError(f"Failed to create internal backup: {self.lock_file} timed out.")
        except Exception as e:
            logger.error(f"Internal backup failed: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to create internal database backup: {str(e)}")

    def create_backup(self) -> Optional[str]:
        """Public method to create a timestamped backup of the database file and index file."""
        try:
            with self._lock.acquire(timeout=10): # Ensure lock is acquired for entire backup process
                self._create_backup_internal() # Handles DB file backup and rotation

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Backup index file
                backup_index_file = os.path.join(self.backup_dir, f"index_backup_{timestamp}.idx")
                if Path(self.index_file).exists():
                    shutil.copy2(self.index_file, backup_index_file)
                    logger.info(f"Backed up index file to {backup_index_file}")
                else:
                    logger.warning(f"Index file {self.index_file} not found for backup.")

                # Backup ID counter file
                backup_id_counter_file = os.path.join(self.backup_dir, f"id_counter_backup_{timestamp}.dat")
                if Path(self.id_counter_file).exists():
                    shutil.copy2(self.id_counter_file, backup_id_counter_file)
                    logger.info(f"Backed up ID counter file to {backup_id_counter_file}")
                else:
                    logger.warning(f"ID counter file {self.id_counter_file} not found for backup.")

            logger.info(f"Full backup initiated: DB, index, and ID counter backed up to {self.backup_dir}")
            return os.path.join(self.backup_dir, f"backup_{timestamp}.db") # Return main DB backup path
        except filelock.Timeout:
            st.error(f"Não foi possível adquirir o bloqueio para o arquivo do banco de dados {self.lock_file} para criar o backup.")
            logger.error(f"Public backup failed: Lock timeout.")
            return None
        except Exception as e:
            st.error(f"Erro ao criar backup: {e}")
            logger.error(f"Error creating public backup: {traceback.format_exc()}")
            return None

    def delete_all_data(self):
        """Deletes the main database file, index file, and ID counter file."""
        try:
            with self._lock.acquire(timeout=10):
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

# --- Streamlit UI Components (from stCRUDDataObjectPY_v5alpha0.1.b.py, adapted for new backend) ---

def display_activity_log():
    """Displays the recent activity log entries."""
    st.subheader("📝 Log de Atividades Recentes")
    log_file_path = LOG_FILE_PATH
    MAX_LOG_ENTRIES_DISPLAY = APP_CONFIG["MAX_LOG_ENTRIES_DISPLAY"]

    if not Path(log_file_path).exists():
        st.info("ℹ️ Arquivo de log de atividades não encontrado.")
        return

    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            log_lines = f.readlines()

        display_entries = []
        # Read from end of file to get most recent entries
        for line in reversed(log_lines):
            try:
                # Example log format: '2023-10-27 15:30:00,123 - __main__ - INFO - Message'
                parts = line.strip().split(' - ', 3) # Split by ' - ' up to 3 times
                if len(parts) == 4:
                    timestamp_str_full = parts[0]
                    log_level = parts[2]
                    message = parts[3]
                    # Format timestamp for display (e.g., remove milliseconds if present)
                    timestamp_parts = timestamp_str_full.split(',')
                    timestamp_str = timestamp_parts[0] # Take only the date and time, ignore milliseconds

                    if "CRITICAL" in log_level.upper():
                        display_entries.append(f"**<span style='color:red;'>CRITICAL</span>** `{timestamp_str}` `{message}`")
                    elif "ERROR" in log_level.upper():
                        display_entries.append(f"**<span style='color:orange;'>ERROR</span>** `{timestamp_str}` `{message}`")
                    elif "WARNING" in log_level.upper():
                        display_entries.append(f"**<span style='color:gold;'>WARNING</span>** `{timestamp_str}` `{message}`")
                    elif "INFO" in log_level.upper():
                        display_entries.append(f"**<span style='color:cyan;'>INFO</span>** `{timestamp_str}` `{message}`")
                    elif "DEBUG" in log_level.upper():
                        display_entries.append(f"**<span style='color:grey;'>DEBUG</span>** `{timestamp_str}` `{message}`")
                    else:
                        display_entries.append(f"**`{timestamp_str}`** `{log_level}` `{message}`") # Default for unknown levels

                    if len(display_entries) >= MAX_LOG_ENTRIES_DISPLAY:
                        break
            except Exception as e:
                logger.warning(f"Failed to parse log line for registry: {line.strip()} - {e}")
                continue

        if display_entries:
            for entry in display_entries:
                st.markdown(entry, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Nenhum registro recente de atividade relevante encontrado no log.")
    except Exception as e:
        st.error(f"⚠️ Não foi possível ler o log de atividades: {str(e)}")
        logger.error(f"Error reading activity log: {traceback.format_exc()}")


def record_form_ui(data_object: Optional[DataObject] = None, is_edit: bool = False):
    """
    Renders the form for creating or editing a DataObject.
    Pre-fills fields if a data_object is provided for editing.
    Returns a dictionary of form data on submit.
    """
    form_key = f"record_form_{'edit' if is_edit else 'add'}"
    if is_edit and data_object and data_object.id is not None:
        form_key += f"_{data_object.id}" # Append ID to key for unique edit forms

    with st.form(key=form_key):
        st.subheader(f"{'Editar' if is_edit else 'Registrar Novo'} Registro de Acidente")

        if is_edit and data_object and data_object.id is not None:
            st.markdown(f"**ID do Registro:** `{data_object.id}`")

        col1, col2 = st.columns(2)
        with col1:
            crash_date_val = datetime.strptime(data_object.crash_date, '%Y-%m-%d').date() if data_object and data_object.crash_date else datetime.now().date()
            crash_date = st.date_input("Data do Acidente*", value=crash_date_val, key=f"crash_date_{form_key}")

            # Using text_input for selectbox-like fields from v3alpha UI, as requested
            traffic_control_device = st.text_input("Dispositivo de Controle de Tráfego", value=data_object.traffic_control_device if data_object else "", key=f"traffic_control_device_{form_key}")
            lighting_condition = st.text_input("Condição de Iluminação", value=data_object.lighting_condition if data_object else "", key=f"lighting_condition_{form_key}")
            trafficway_type = st.text_input("Tipo de Via", value=data_object.trafficway_type if data_object else "", key=f"trafficway_type_{form_key}")
            roadway_surface_cond = st.text_input("Condição da Superfície da Via", value=data_object.roadway_surface_cond if data_object else "", key=f"roadway_surface_cond_{form_key}")
            crash_type = st.text_input("Tipo de Colisão*", value=data_object.crash_type if data_object else "", help="Campo obrigatório", key=f"crash_type_{form_key}")
            damage = st.text_input("Dano", value=data_object.damage if data_object else "", key=f"damage_{form_key}")
            num_units = st.number_input("Número de Unidades Envolvidas*", min_value=0, value=data_object.num_units if data_object else 0, step=1, key=f"num_units_{form_key}")
            injuries_total = st.number_input("Total de Feridos*", min_value=0.0, value=data_object.injuries_total if data_object else 0.0, step=0.1, format="%.2f", key=f"injuries_total_{form_key}")
            injuries_incapacitating = st.number_input("Ferimentos Incapacitantes", min_value=0.0, value=data_object.injuries_incapacitating if data_object else 0.0, step=0.1, format="%.2f", key=f"injuries_incapacitating_{form_key}")
            injuries_reported_not_evident = st.number_input("Ferimentos Reportados (Não Evidentes)", min_value=0.0, value=data_object.injuries_reported_not_evident if data_object else 0.0, step=0.1, format="%.2f", key=f"injuries_reported_not_evident_{form_key}")
            crash_day_of_week = st.slider("Dia da Semana da Colisão (1=Seg, 7=Dom)", min_value=1, max_value=7, value=data_object.crash_day_of_week if data_object else 1, key=f"crash_day_of_week_{form_key}")

        with col2:
            weather_condition = st.text_input("Condição Climática", value=data_object.weather_condition if data_object else "", key=f"weather_condition_{form_key}")
            first_crash_type = st.text_input("Primeiro Tipo de Colisão", value=data_object.first_crash_type if data_object else "", key=f"first_crash_type_{form_key}")
            alignment = st.text_input("Alinhamento", value=data_object.alignment if data_object else "", key=f"alignment_{form_key}")
            road_defect = st.text_input("Defeito na Via", value=data_object.road_defect if data_object else "", key=f"road_defect_{form_key}")

            intersection_index = 0
            if data_object and data_object.intersection_related_i == "YES":
                intersection_index = 1
            intersection_related_i = st.selectbox("Relacionado a Cruzamento?", ["NO", "YES"], index=intersection_index, key=f"intersection_related_i_{form_key}")

            prim_contributory_cause = st.text_input("Principal Causa Contributiva", value=data_object.prim_contributory_cause if data_object else "", key=f"prim_contributory_cause_{form_key}")
            most_severe_injury = st.text_input("Lesão Mais Grave", value=data_object.most_severe_injury if data_object else "", key=f"most_severe_injury_{form_key}")
            injuries_fatal = st.number_input("Ferimentos Fatais", min_value=0.0, value=data_object.injuries_fatal if data_object else 0.0, step=0.1, format="%.2f", key=f"injuries_fatal_{form_key}")
            injuries_non_incapacitating = st.number_input("Ferimentos Não Incapacitantes", min_value=0.0, value=data_object.injuries_non_incapacitating if data_object else 0.0, step=0.1, format="%.2f", key=f"injuries_non_incapacitating_{form_key}")
            injuries_no_indication = st.number_input("Sem Indicação de Ferimentos", min_value=0.0, value=data_object.injuries_no_indication if data_object else 0.0, step=0.1, format="%.2f", key=f"injuries_no_indication_{form_key}")
            crash_hour = st.slider("Hora da Colisão (0-23)", min_value=0, max_value=23, value=data_object.crash_hour if data_object else 0, key=f"crash_hour_{form_key}")
            crash_month = st.slider("Mês da Colisão (1-12)", min_value=1, max_value=12, value=data_object.crash_month if data_object else 1, key=f"crash_month_{form_key}")

        submit_button_label = "Atualizar Registro" if is_edit else "Adicionar Registro"
        submitted = st.form_submit_button(submit_button_label)

        if submitted:
            # Frontend validation for required fields before returning data
            if crash_date is None:
                st.error("🚨 Campo 'Data do Acidente' é obrigatório.")
                return None # Prevent submission if validation fails
            if not crash_type:
                st.error("🚨 Campo 'Tipo de Colisão' é obrigatório.")
                return None
            if num_units is None or num_units < 0:
                st.error("🚨 Campo 'Número de Unidades Envolvidas' deve ser um número não negativo.")
                return None
            if injuries_total is None or injuries_total < 0:
                st.error("🚨 Campo 'Total de Feridos' deve ser um número não negativo.")
                return None

            form_data = {
                'crash_date': crash_date.strftime('%Y-%m-%d'),
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
                'crash_hour': crash_hour,
                'crash_day_of_week': crash_day_of_week,
                'crash_month': crash_month
            }
            if is_edit and data_object and data_object.id is not None:
                form_data['id'] = data_object.id # Preserve the ID if it's an edit operation
            return form_data
    return None

def display_record_details(record_obj: DataObject):
    """
    Displays the details of a single DataObject in a user-friendly format.
    Accepts a DataObject instance.
    """
    st.markdown(f"**ID do Registro:** `{record_obj.id if record_obj.id else 'N/A'}`")
    st.markdown(f"**Data do Acidente:** `{record_obj.crash_date}`")
    st.markdown(f"**Dispositivo de Controle de Tráfego:** `{record_obj.traffic_control_device}`")
    st.markdown(f"**Condição Climática:** `{record_obj.weather_condition}`")
    st.markdown(f"**Condição de Iluminação:** `{record_obj.lighting_condition}`")
    st.markdown(f"**Primeiro Tipo de Colisão:** `{record_obj.first_crash_type}`")
    st.markdown(f"**Tipo de Via:** `{record_obj.trafficway_type}`")
    st.markdown(f"**Alinhamento:** `{record_obj.alignment}`")
    st.markdown(f"**Condição da Superfície da Via:** `{record_obj.roadway_surface_cond}`")
    st.markdown(f"**Defeito na Via:** `{record_obj.road_defect}`")
    st.markdown(f"**Tipo de Colisão:** `{record_obj.crash_type}`")
    st.markdown(f"**Relacionado a Cruzamento?** `{record_obj.intersection_related_i}`")
    st.markdown(f"**Dano:** `{record_obj.damage}`")
    st.markdown(f"**Principal Causa Contributiva:** `{record_obj.prim_contributory_cause}`")
    st.markdown(f"**Número de Unidades Envolvidas:** `{record_obj.num_units}`")
    st.markdown(f"**Lesão Mais Grave:** `{record_obj.most_severe_injury}`")
    st.markdown(f"**Total de Feridos:** `{record_obj.injuries_total}`")
    st.markdown(f"**Ferimentos Fatais:** `{record_obj.injuries_fatal}`")
    st.markdown(f"**Ferimentos Incapacitantes:** `{record_obj.injuries_incapacitating}`")
    st.markdown(f"**Ferimentos Não Incapacitantes:** `{record_obj.injuries_non_incapacitating}`")
    st.markdown(f"**Ferimentos Reportados (Não Evidentes):** `{record_obj.injuries_reported_not_evident}`")
    st.markdown(f"**Sem Indicação de Ferimentos:** `{record_obj.injuries_no_indication}`")
    st.markdown(f"**Hora da Colisão:** `{record_obj.crash_hour}`")
    st.markdown(f"**Dia da Semana da Colisão:** `{record_obj.crash_day_of_week}`")
    st.markdown(f"**Mês da Colisão:** `{record_obj.crash_month}`")
    st.markdown("---")
    st.subheader("Representação JSON Completa (Excluindo ID):")
    # Display the internal data dictionary that gets stored
    temp_dict = record_obj.to_dict()
    if 'id' in temp_dict:
        del temp_dict['id'] # Remove ID for this JSON representation
    st.json(temp_dict)


def setup_ui():
    """Sets up the Streamlit UI for CRUD operations."""
    st.set_page_config(layout="wide", page_title="Sistema de Gerenciamento de Acidentes de Trânsito")
    st.title("Sistema de Gerenciamento de Acidentes de Trânsito")

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

    # Initialize DB (singleton pattern for Streamlit)
    if 'db' not in st.session_state:
        try:
            st.session_state.db = TrafficAccidentsDB(
                db_file=DB_PATH,
                index_file=INDEX_PATH,
                lock_file=LOCK_PATH,
                id_counter_file=ID_COUNTER_PATH,
                backup_dir=BACKUP_PATH
            )
            logger.info("Database initialized successfully.")
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o banco de dados: {e}")
            logger.critical(f"Critical DB initialization error: {traceback.format_exc()}")
            st.stop() # Stop the app if DB cannot be initialized

    db = st.session_state.db

    # Initialize cache for all records for paginated view
    # The cache should store DataObject instances
    if 'all_records_cache' not in st.session_state:
        st.session_state.all_records_cache = {} # Dict[int, DataObject]
        st.session_state.records_dirty = True # Flag to indicate if cache needs refresh

    # --- Sidebar for Mode Selection ---
    with st.sidebar:
        st.header("⚙️ Modo de Operação")
        operation_mode = st.selectbox(
            "Selecione o modo de operação:",
            ("Operar via Índice (Recomendado)", "Operar Diretamente no Arquivo"), # Direct file operation is mostly internal now
            key="operation_mode_selector"
        )
        # This state variable will now indicate preferred search behavior, but CRUD will use index for efficiency.
        st.session_state.use_index_for_crud = (operation_mode == "Operar via Índice (Recomendado)")
        st.info(f"Modo atual: **{operation_mode}**")

    # Tabs for navigation
    tab_insert, tab_view, tab_search, tab_import_export, tab_admin = st.tabs([
        "➕ Inserir Registro", "👁️ Visualizar Registros", "🔍 Buscar Registros", "📥📤 Importar/Exportar", "⚙️ Administração"
    ])

    with tab_insert:
        st.header("➕ Inserir Novo Registro")
        # Use the unified record_form_ui for adding new records
        new_record_data = record_form_ui(is_edit=False)
        if new_record_data:
            try:
                # Remove the 'id' if present, as it will be generated by the DB
                if 'id' in new_record_data:
                    del new_record_data['id']
                new_data_object = DataObject.from_dict(new_record_data)
                record_id = db.insert_data(new_data_object)
                st.success(f"Registro inserido com sucesso! ID do Registro: `{record_id}`")
                logger.info(f"New record inserted via UI: {record_id}")
                st.session_state.records_dirty = True # Mark cache as dirty
                st.rerun() # Rerun to clear form and refresh view if user goes to view page
            except DataValidationError as e:
                st.error(f"Erro de validação dos dados: {e}")
                logger.warning(f"Data validation error on add: {e}")
            except Exception as e:
                st.error(f"Erro ao inserir registro: {e}")
                logger.error(f"Error adding record: {traceback.format_exc()}")

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
                    found_record_obj = db.get_record_by_id(record_id_to_find) # Returns DataObject
                    if found_record_obj:
                        st.subheader(f"✅ Registro encontrado para ID: `{record_id_to_find}`")
                        with st.expander("Detalhes do Registro Encontrado", expanded=True):
                            display_record_details(found_record_obj)

                        st.markdown("---")
                        st.subheader("Ações para o Registro Encontrado")
                        col_edit_found, col_delete_found = st.columns(2)
                        with col_edit_found:
                            if st.button(f"✏️ Editar Este Registro ({found_record_obj.id})", key=f"edit_found_{found_record_obj.id}"):
                                st.session_state.edit_record_id = found_record_obj.id
                                st.session_state.edit_record_data = found_record_obj # Pass DataObject instance
                                st.session_state.show_edit_form = True
                                st.rerun()
                        with col_delete_found:
                            # Use a temporary state for confirmation
                            if f"confirm_delete_found_{found_record_obj.id}" not in st.session_state:
                                st.session_state[f"confirm_delete_found_{found_record_obj.id}"] = False

                            if st.button(f"🗑️ Excluir Este Registro ({found_record_obj.id})", key=f"delete_found_{found_record_obj.id}", type="secondary"):
                                st.session_state[f"confirm_delete_found_{found_record_obj.id}"] = True
                                st.rerun() # Rerun to show confirmation

                            if st.session_state[f"confirm_delete_found_{found_record_obj.id}"]:
                                st.warning(f"⚠️ Tem certeza que deseja excluir o registro `{found_record_obj.id}`? Esta ação o marcará como inválido e removerá do índice.")
                                col_confirm = st.columns(2)
                                with col_confirm[0]:
                                    if st.button("✅ Confirmar Exclusão", key=f"confirm_delete_found_yes_{found_record_obj.id}"):
                                        try:
                                            if db.delete_record(found_record_obj.id): # Call delete on backend
                                                st.success("✔️ Registro excluído com sucesso (marcado como inválido e removido do índice).")
                                                logger.info(f"Record {found_record_obj.id} deleted via UI.")
                                                st.session_state.records_dirty = True
                                                del st.session_state[f"confirm_delete_found_{found_record_obj.id}"]
                                                st.rerun() # Rerun to refresh UI
                                            else:
                                                st.error("❌ Falha ao excluir registro.")
                                        except Exception as e:
                                            st.error(f"⚠️ Erro ao excluir registro: {e}")
                                            logger.error(f"UI delete error: {traceback.format_exc()}")
                                with col_confirm[1]:
                                    if st.button("❌ Cancelar", key=f"confirm_delete_found_no_{found_record_obj.id}"):
                                        st.info("Operação de exclusão cancelada.")
                                        del st.session_state[f"confirm_delete_found_{found_record_obj.id}"]
                                        st.rerun() # Rerun to clear confirmation

                    # Clear confirmation state if search ID changes
                    # This logic needs to be careful if the previous search ID and new search ID are the same.
                    # This simple check ensures it's cleared if the search_id_input_str actually changed.
                    if "current_search_id_val" not in st.session_state or st.session_state.current_search_id_val != record_id_input_str:
                         # Iterate through all potential confirmation keys and clear them
                        for key in list(st.session_state.keys()):
                            if key.startswith("confirm_delete_found_"):
                                del st.session_state[key]
                    st.session_state.current_search_id_val = record_id_input_str # Store current search ID for next rerun check

                else:
                    st.info("ℹ️ Registro não encontrado para o ID fornecido ou está inválido. Verifique o ID.")
            except ValueError:
                st.warning("⚠️ Por favor, digite um ID de registro válido (número inteiro).")
            except Exception as e:
                st.error(f"⚠️ Erro ao buscar registro: {e}")
                logger.error(f"UI search by ID error: {traceback.format_exc()}")
        else:
            st.info("ℹ️ Digite um ID de registro para buscar.")
        # --- End Section: Read Record by ID ---


        st.markdown("---")
        st.subheader("📚 Visualizar Todos os Registros (Paginado)")

        records_per_page = st.slider("Registros por página", 10, 50, APP_CONFIG["MAX_RECORDS_PER_PAGE"], key="records_per_page_slider")

        # Refresh cache if dirty
        if st.session_state.records_dirty:
            st.session_state.all_records_cache = db.get_all_records() # Get all valid DataObjects
            st.session_state.records_dirty = False
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
            else:
                st.session_state.current_page = 1 # Reset to page 1 on refresh

        all_records_list = sorted(st.session_state.all_records_cache.values(), key=lambda x: x.id if x.id is not None else 0) # Sort by ID
        total_records = len(all_records_list)
        total_pages = (total_records + records_per_page - 1) // records_per_page if total_records > 0 else 1

        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        if st.session_state.current_page > total_pages and total_pages > 0:
            st.session_state.current_page = total_pages
        if st.session_state.current_page < 1:
            st.session_state.current_page = 1

        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            if st.button("⬅️ Página Anterior", disabled=(st.session_state.current_page == 1), key="prev_page_button"):
                if st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()
        with col2:
            st.markdown(f"<p style='text-align:center; font-weight:bold;'>Página {st.session_state.current_page} de {total_pages} (Total: {total_records} registros)</p>", unsafe_allow_html=True)
        with col3:
            if st.button("Próxima Página ➡️", disabled=(st.session_state.current_page == total_pages), key="next_page_button"):
                if st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1
                    st.rerun()

        start_idx = (st.session_state.current_page - 1) * records_per_page
        end_idx = start_idx + records_per_page
        displayed_records = all_records_list[start_idx:end_idx]

        if displayed_records:
            for record_obj in displayed_records: # Iterate DataObject instances
                expander_title = f"ID: {record_obj.id if record_obj.id else 'N/A'} - Data: {record_obj.crash_date} - Tipo: {record_obj.crash_type}"
                with st.expander(expander_title, expanded=False):
                    display_record_details(record_obj) # Use helper function with DataObject

                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button(f"✏️ Editar {record_obj.id}", key=f"edit_paginated_{record_obj.id}"):
                            st.session_state.edit_record_id = record_obj.id
                            st.session_state.edit_record_data = record_obj # Pass DataObject instance
                            st.session_state.show_edit_form = True # Explicitly show edit form
                            st.rerun()
                    with col_delete:
                        # Use a temporary state for confirmation
                        if f"confirm_delete_paginated_{record_obj.id}" not in st.session_state:
                            st.session_state[f"confirm_delete_paginated_{record_obj.id}"] = False

                        if st.button(f"🗑️ Excluir {record_obj.id}", key=f"delete_paginated_{record_obj.id}", type="secondary"):
                            st.session_state[f"confirm_delete_paginated_{record_obj.id}"] = True
                            st.rerun() # Rerun to show confirmation

                        if st.session_state[f"confirm_delete_paginated_{record_obj.id}"]:
                            st.warning(f"⚠️ Tem certeza que deseja excluir o registro `{record_obj.id}`? Isso o marcará como inválido e removerá do índice.")
                            col_confirm_paginated = st.columns(2)
                            with col_confirm_paginated[0]:
                                if st.button("✅ Confirmar Exclusão", key=f"confirm_delete_paginated_yes_{record_obj.id}"):
                                    try:
                                        if db.delete_record(record_obj.id): # Call delete on backend
                                            st.success("✔️ Registro excluído com sucesso (marcado como inválido e removido do índice).")
                                            logger.info(f"Record {record_obj.id} deleted via UI.")
                                            st.session_state.records_dirty = True
                                            del st.session_state[f"confirm_delete_paginated_{record_obj.id}"]
                                            # Clear edit state if the deleted record was being edited
                                            if 'edit_record_id' in st.session_state and st.session_state.edit_record_id == record_obj.id:
                                                del st.session_state.edit_record_id
                                                del st.session_state.edit_record_data
                                            st.rerun() # Rerun to refresh UI
                                        else:
                                            st.error("❌ Falha ao excluir registro.")
                                    except Exception as e:
                                        st.error(f"⚠️ Erro ao excluir registro: {e}")
                                        logger.error(f"UI delete error: {traceback.format_exc()}")
                            with col_confirm_paginated[1]:
                                if st.button("❌ Cancelar", key=f"confirm_delete_paginated_no_{record_obj.id}"):
                                    st.info("Operação de exclusão cancelada.")
                                    del st.session_state[f"confirm_delete_paginated_{record_obj.id}"]
                                    st.rerun() # Rerun to clear confirmation
        else:
            st.info("ℹ️ Nenhum registro encontrado.")

        # Edit Form Logic (Centralized)
        if st.session_state.get('show_edit_form', False) and st.session_state.get('edit_record_id') is not None:
            st.markdown("---")
            st.header(f"✏️ Editar Registro ID: {st.session_state.edit_record_id}")
            record_to_edit_obj = st.session_state.edit_record_data # This is already a DataObject

            if record_to_edit_obj is None:
                st.error(f"Registro com ID {st.session_state.edit_record_id} não encontrado para edição. Ele pode ter sido excluído.")
                del st.session_state.edit_record_id
                del st.session_state.edit_record_data
                st.session_state.show_edit_form = False
                st.rerun()
            else:
                updated_data = record_form_ui(record_to_edit_obj, is_edit=True)
                col_update_btn, col_cancel_btn = st.columns(2)
                with col_update_btn:
                    # The record_form_ui already contains the submit button logic.
                    # We just check its return value here.
                    pass # This column is now just a placeholder for the form's submit button.
                with col_cancel_btn:
                    cancel_update = st.button("Cancelar Edição", type="secondary", key="cancel_edit_form_btn")


                if updated_data: # This means the form's submit button was clicked
                    try:
                        updated_data_object = DataObject.from_dict(updated_data) # Create new DataObject from form data
                        if db.update_record(st.session_state.edit_record_id, updated_data_object):
                            st.success(f"Registro {st.session_state.edit_record_id} atualizado com sucesso!")
                            logger.info(f"Record {st.session_state.edit_record_id} updated via UI.")
                            st.session_state.records_dirty = True
                            st.session_state.show_edit_form = False # Hide form
                            del st.session_state.edit_record_id # Clear edit state
                            del st.session_state.edit_record_data
                            st.rerun() # Refresh list to show updated data
                        else:
                            st.error(f"Falha ao atualizar registro {st.session_state.edit_record_id}.")
                    except DataValidationError as e:
                        st.error(f"Erro de validação dos dados para atualização: {e}")
                        logger.warning(f"Data validation error on update: {e}")
                    except Exception as e:
                        st.error(f"Erro ao atualizar registro {st.session_state.edit_record_id}: {e}")
                        logger.error(f"Error updating record {st.session_state.edit_record_id}: {traceback.format_exc()}")

                if cancel_update:
                    st.session_state.show_edit_form = False
                    del st.session_state.edit_record_id
                    del st.session_state.edit_record_data
                    st.rerun()

    with tab_search:
        st.header("🔍 Buscar Registros")
        search_query = st.text_input("Digite sua busca (ex: nome da rua, tipo de acidente)")
        if st.button("🔍 Buscar"):
            if search_query:
                found_records_objs = db.search_records(search_query) # Returns list of DataObjects
                if found_records_objs:
                    st.subheader(f"Resultados da Busca para '{search_query}':")
                    for record_obj in found_records_objs:
                        expander_title = f"ID: {record_obj.id if record_obj.id else 'N/A'} - Data: {record_obj.crash_date} - Tipo: {record_obj.crash_type}"
                        with st.expander(expander_title, expanded=False):
                            display_record_details(record_obj)
                else:
                    st.info("ℹ️ Nenhum registro encontrado para sua busca.")
            else:
                st.warning("⚠️ Por favor, digite um termo para buscar.")

    with tab_import_export:
        st.header("📥📤 Importar e Exportar Dados")

        st.subheader("📥 Importar CSV")
        uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=["csv"])
        st.info(f"O delimitador CSV configurado é: `{APP_CONFIG['CSV_DELIMITER']}`")

        if uploaded_file is not None:
            if uploaded_file.size > APP_CONFIG["MAX_FILE_SIZE_MB"] * 1024 * 1024:
                st.error(f"Arquivo muito grande. O tamanho máximo permitido é {APP_CONFIG['MAX_FILE_SIZE_MB']} MB.")
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name

            if st.button("🚀 Iniciar Importação"):
                progress_bar = st.progress(0)
                progress_text = st.empty()
                try:
                    def update_progress_callback(current_row, total_rows):
                        if total_rows > 0:
                            percent_complete = min(int((current_row / total_rows) * 100), 100)
                            progress_bar.progress(percent_complete)
                            progress_text.text(f"Importando linha {current_row} de {total_rows}...")
                        else:
                            progress_bar.progress(100)
                            progress_text.text("Importação concluída: 0 registros.")

                    imported_count = db.import_from_csv(temp_path, progress_callback=update_progress_callback)
                    st.success(f"🎉 Importação concluída. {imported_count} registros importados.")
                    logger.info(f"CSV imported from {temp_path}, {imported_count} records.")
                    st.session_state.records_dirty = True # Mark cache as dirty
                    st.rerun() # Refresh UI
                except Exception as e:
                    st.error(f"❌ Erro durante a importação: {e}")
                    logger.error(f"CSV import failed for {temp_path}: {traceback.format_exc()}")
                finally:
                    os.unlink(temp_path) # Clean up temp file
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
                else:
                    st.info("Nenhum registro para exportar.")
            except Exception as e:
                st.error(f"⚠️ Erro ao preparar exportação: {e}")
                logger.error(f"Export preparation failed for {export_path}: {traceback.format_exc()}")

    with tab_admin:
        st.header("⚙️ Ferramentas de Administração")

        st.subheader("💾 Criar Backup do Banco de Dados")
        if st.button("Criar Backup Agora"):
            try:
                backup_path = db.create_backup() # Public method
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
                st.session_state.records_dirty = True # Mark cache as dirty
                st.rerun() # Refresh UI
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
                    # Clear edit state if any
                    if 'edit_record_id' in st.session_state:
                        del st.session_state.edit_record_id
                    if 'edit_record_data' in st.session_state:
                        del st.session_state.edit_record_data
                    time.sleep(1) # Give time for message to display
                    st.rerun() # Rerun to reflect empty state
                except Exception as e:
                    st.error(f"❌ Erro ao excluir todos os dados: {e}")
                    logger.error(f"Delete all data error: {traceback.format_exc()}")

        st.subheader("📜 Log de Atividades Recentes")
        st.write(f"Exibindo as últimas {APP_CONFIG['MAX_LOG_ENTRIES_DISPLAY']} entradas do log de atividades (mais recentes primeiro):")
        display_activity_log() # Directly call the log display

# --- Main Application Entry Point ---
if __name__ == "__main__":
    try:
        # Ensure base directories are created before any DB operations
        Path(APP_CONFIG["DB_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        st.error(f"Crítico: Não foi possível criar os diretórios do banco de dados. Verifique as permissões para {APP_CONFIG['DB_DIR']}. Erro: {e}")
        logger.critical(f"Initial directory creation failed: {traceback.format_exc()}")
        st.stop()

    setup_ui()
