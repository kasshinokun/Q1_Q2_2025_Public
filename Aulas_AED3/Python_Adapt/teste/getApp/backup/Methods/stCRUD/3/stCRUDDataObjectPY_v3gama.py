import streamlit as st
import csv
import os
import struct
from pathlib import Path
import json
from typing import List, Dict, Optional, Union, Callable, Any, Iterator
import tempfile
import logging
from datetime import datetime, date
import traceback
import hashlib
import time  # For simulating delays/retries if needed, and for timing operations
import filelock # For cross-platform file locking

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

# --- Constants ---
DB_DIR = os.path.join(Path.home(), 'Documents', 'Data')
DB_FILE = os.path.join(DB_DIR, 'traffic_accidents.db')
BACKUP_DIR = os.path.join(DB_DIR, 'backups')
LOCK_FILE = os.path.join(DB_DIR, 'traffic_accidents.lock') # Dedicated lock file
CSV_DELIMITER = ';'
MAX_RECORDS_PER_PAGE = 20
MAX_FILE_SIZE_MB = 100 # Maximum CSV file size for import
CHUNK_SIZE = 4096     # Read/write chunk size for file operations (4KB)
MAX_BACKUPS = 5       # Keep only the last N backups
MAX_LOG_ENTRIES_DISPLAY = 10 # Max number of log entries to display in the registry

# --- Data Fields ---
# Define all fields for the DataObject and their expected types/validation rules
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

# --- DataObject Class ---
class DataObject:
    """
    Represents a traffic accident record with enhanced validation and serialization.
    Each instance corresponds to a single record in the database.
    """
    
    def __init__(self, row_data: Optional[List[str]] = None, existing_data_dict: Optional[Dict[str, Any]] = None):
        """
        Initializes a DataObject.
        Can be initialized from a list of row data (e.g., from CSV) or an existing dictionary.
        """
        # Initialize all fields with type-appropriate default values
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
        self.crash_day_of_week = 1 # Monday
        self.crash_month = 1      # January

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
        for field in FIELDS:
            if field in data_dict:
                # Direct assignment for most fields, validation happens in .validate()
                # Special handling for date, numbers where type conversion is needed
                if field == 'crash_date':
                    self.crash_date = self._validate_date(data_dict[field])
                elif field in ['num_units', 'crash_hour', 'crash_day_of_week', 'crash_month']:
                    setattr(self, field, self._validate_positive_int(str(data_dict[field]), field))
                elif field.startswith('injuries_') and field != 'injuries_no_indication': # All injury fields are floats
                    setattr(self, field, self._validate_positive_float(str(data_dict[field]), field))
                elif field == 'injuries_no_indication': # This one also float
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
        Validates and standardizes a date string to APAC-MM-DD format.
        Handles various common input formats including those with time and AM/PM.
        Raises DataValidationError if a non-empty string cannot be parsed.
        """
        logger.debug(f"[_validate_date] Input date_str: '{date_str}' ({type(date_str)})")
        if not date_str:
            logger.debug(f"[_validate_date] Input date_str is empty/None. Returning ''")
            return "" # Return empty string for None or empty input
        
        date_str = date_str.strip()
        if not date_str: # After stripping, if it becomes empty
            logger.debug(f"[_validate_date] Input date_str became empty after stripping. Returning ''")
            return ""

        # Try multiple common date and datetime formats
        # Added formats to handle time and AM/PM
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d', 
                    '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', # 24-hour time
                    '%m/%d/%Y %I:%M:%S %p', '%Y-%m-%d %I:%M:%S %p'): # 12-hour time with AM/PM
            try:
                dt = datetime.strptime(date_str, fmt)
                formatted_date = dt.strftime('%Y-%m-%d') # Always store as APAC-MM-DD
                logger.debug(f"[_validate_date] Successfully parsed '{date_str}' with '{fmt}'. Returning '{formatted_date}'")
                return formatted_date
            except ValueError:
                logger.debug(f"[_validate_date] Failed to parse '{date_str}' with format '{fmt}'")
                continue # Try next format
        
        # If execution reaches here, it means date_str was not empty but could not be parsed
        logger.error(f"[_validate_date] Failed to parse date string '{date_str}' into any known format. Raising DataValidationError.")
        raise DataValidationError(f"Invalid date format: '{date_str}'. Expected APAC-MM-DD or common date/datetime format (e.g., MM/DD/YYYY, DD-MM-YYYY, or with time/AM/PM).")

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
        value = value.replace(CSV_DELIMITER, ',').replace('\n', ' ').replace('\r', '')
        
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
            if num < min_val:
                logger.warning(f"Integer value for {field_name} ({num}) is less than minimum {min_val}. Setting to {min_val}.")
                return min_val
            return num
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
            if num < min_val:
                logger.warning(f"Float value for {field_name} ({num}) is less than minimum {min_val}. Setting to {min_val}.")
                return min_val
            return round(num, 2) # Round to 2 decimal places for consistency
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
            if not (min_val <= num <= max_val):
                logger.warning(f"Value for {field_name} ({num}) is out of range [{min_val}-{max_val}]. Setting to {min_val}.")
                return min_val # Default to min_val if out of range
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid numeric value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val
            
    def to_bytes(self) -> bytes:
        """
        Serializes the DataObject into bytes using JSON format.
        Uses sorted keys for consistent byte representation.
        """
        try:
            data_dict = {attr: getattr(self, attr) for attr in FIELDS}
            # Ensure JSON is compact and consistent for hashing
            return json.dumps(data_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
        except TypeError as e:
            logger.error(f"Serialization TypeError in DataObject: {e}. Data dict: {data_dict}")
            raise DatabaseError(f"Failed to serialize record due to invalid data type: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected serialization error in DataObject: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to serialize record: {str(e)}")

    @classmethod
    def from_bytes(cls, byte_data: bytes) -> 'DataObject':
        """
        Deserializes byte data back into a DataObject instance.
        Handles various deserialization errors.
        """
        if not byte_data:
            raise DataValidationError("Attempted to deserialize empty byte data.")
        
        try:
            data_dict = json.loads(byte_data.decode('utf-8'))
            obj = cls(existing_data_dict=data_dict) # Initialize using the dictionary constructor
            # Validation is already done in the DataObject constructor
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
                    raise DataValidationError("Invalid crash date format (expected APAC-MM-DD).")
            
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
            
    def __repr__(self) -> str:
        """Provides a string representation of the DataObject for debugging."""
        return f"DataObject(ID=N/A, Date='{self.crash_date}', Type='{self.crash_type}', TotalInjuries={self.injuries_total})"

# --- TrafficAccidentsDB Class ---
class TrafficAccidentsDB:
    """
    Handles all database operations for traffic accident records.
    Implements file-based storage with robust locking, backups, and error recovery.
    """
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.lock_file_path = LOCK_FILE
        self._ensure_directories()
        self._last_read_id = 0 # To track the last ID in the file header
        self._lock = filelock.FileLock(self.lock_file_path) # Initialize filelock

    def _ensure_directories(self):
        """Ensures the database and backup directories exist with appropriate permissions."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            os.makedirs(BACKUP_DIR, exist_ok=True)
            # Set permissions for the directories (e.g., rwx for owner, rx for group/others)
            os.chmod(os.path.dirname(self.db_path), 0o755)
            os.chmod(BACKUP_DIR, 0o755)
            logger.info(f"Ensured DB directory '{os.path.dirname(self.db_path)}' and backup directory '{BACKUP_DIR}' exist.")
        except OSError as e:
            logger.critical(f"OS error ensuring directories: {e}")
            raise DatabaseError(f"Failed to create necessary directories: {str(e)}")
        except Exception as e:
            logger.critical(f"Unexpected error ensuring directories: {traceback.format_exc()}")
            raise DatabaseError(f"Critical error initializing database paths: {str(e)}")

    def _acquire_lock(self, timeout: int = 10, interval: float = 0.5):
        """
        Acquires an exclusive file lock to ensure single-process access to the database.
        Implements a timeout and retry mechanism using filelock.
        """
        try:
            self._lock.acquire(timeout=timeout)
            logger.debug(f"Acquired lock on {self.lock_file_path}")
        except filelock.Timeout:
            raise FileLockError(f"Failed to acquire file lock on {self.lock_file_path} within {timeout} seconds. Another process might be holding the lock.")
        except Exception as e:
            logger.error(f"Error acquiring file lock: {e}")
            raise FileLockError(f"Failed to acquire file lock: {str(e)}")

    def _release_lock(self):
        """Releases the acquired file lock."""
        try:
            self._lock.release()
            logger.debug(f"Released lock on {self.lock_file_path}")
        except Exception as e:
            logger.error(f"Error releasing file lock: {e}")
            # Don't re-raise, as it might prevent cleanup

    def _create_backup(self):
        """
        Creates a timestamped backup of the database file and manages backup rotation.
        Keeps only the last MAX_BACKUPS.
        """
        try:
            if not os.path.exists(self.db_path):
                logger.info("No database file found to backup.")
                return
            
            # Clean up old backups first
            backups = sorted(Path(BACKUP_DIR).glob("backup_*.db"))
            while len(backups) >= MAX_BACKUPS:
                oldest = backups.pop(0)
                try:
                    os.unlink(oldest)
                    logger.info(f"Removed old backup: {oldest}")
                except OSError as e:
                    logger.warning(f"Could not remove old backup '{oldest}': {e}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
            
            with open(self.db_path, 'rb') as src:
                with open(backup_path, 'wb') as dst:
                    while True:
                        chunk = src.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        dst.write(chunk)
            
            logger.info(f"Created database backup: {backup_path}")
        except Exception as e:
            logger.error(f"Backup failed: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to create database backup: {str(e)}")

    def get_last_id(self) -> int:
        """Reads the last recorded ID from the database file header."""
        try:
            self._acquire_lock()
            if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) < 4:
                return 0 # File doesn't exist or is too small for an ID header
            
            with open(self.db_path, 'rb') as f:
                id_bytes = f.read(4)
                if len(id_bytes) == 4:
                    self._last_read_id = struct.unpack('I', id_bytes)[0]
                    return self._last_read_id
                else:
                    logger.warning("DB file header is corrupt or incomplete. Resetting last ID to 0.")
                    return 0
        except FileLockError:
            raise # Re-raise if lock failed
        except FileNotFoundError:
            return 0
        except struct.error as e:
            logger.error(f"Structural error reading last ID: {e}")
            raise DatabaseError("Database header corrupt, cannot read last ID.")
        except Exception as e:
            logger.error(f"Error getting last ID: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to retrieve last ID: {str(e)}")
        finally:
            self._release_lock()

    def update_last_id(self, new_id: int):
        """Updates the last recorded ID in the database file header."""
        try:
            self._acquire_lock()
            # Ensure file exists, create with initial ID 0 if not
            mode = 'r+b' if os.path.exists(self.db_path) and os.path.getsize(self.db_path) >= 4 else 'wb'
            with open(self.db_path, mode) as f:
                f.seek(0) # Go to the beginning of the file
                f.write(struct.pack('I', new_id))
                f.flush()
                os.fsync(f.fileno()) # Ensure data is written to disk
            logger.debug(f"Updated last ID to {new_id}")
            self._last_read_id = new_id
        except FileLockError:
            raise # Re-raise if lock failed
        except Exception as e:
            logger.error(f"Error updating last ID: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to update last ID: {str(e)}")
        finally:
            self._release_lock()

    def read_records_paginated(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Reads records from the database file with pagination.
        Includes error recovery for individual corrupt records.
        Returns raw record data (with 'data_bytes').
        """
        records = []
        records_read_count = 0
        try:
            self._acquire_lock()
            if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) < 4:
                logger.info("No database file or empty file to read records from.")
                return []
                
            with open(self.db_path, 'rb') as f:
                f.read(4) # Skip last ID header
                
                current_record_index_in_file = 0 # Logical index counter for records in file (0-based)
                while True:
                    current_pos_before_read = f.tell() # Store position before attempting to read a record
                    record_data_raw = self._read_next_record_raw(f)
                    
                    if record_data_raw is None: # End of file
                        break
                    
                    current_record_index_in_file += 1 # Increment for each record successfully read (raw)
                    
                    # Apply offset (0-based index)
                    if current_record_index_in_file <= offset:
                        continue
                    
                    # Apply limit
                    if limit is not None and records_read_count >= limit:
                        break
                    
                    # Add start_offset to the raw record data for future use
                    record_data_raw['start_offset'] = current_pos_before_read
                    records.append(record_data_raw)
                    records_read_count += 1
        
            logger.info(f"Successfully read {len(records)} raw records from the database (offset: {offset}, limit: {limit}).")
            return records
        except FileLockError:
            raise
        except FileNotFoundError:
            return [] # No database file, return empty list
        # Catch DatabaseError specifically for structural issues
        except DatabaseError as e: 
            logger.error(f"Error reading paginated records: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to read paginated records: {str(e)}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while reading paginated records: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to read paginated records: {str(e)}")
        finally:
            self._release_lock()


    def read_record_by_id(self, search_id: int) -> Optional[Dict[str, Any]]:
        """
        Reads a specific record by its ID.
        Performs a linear scan, as binary search is not practical for this file structure.
        Returns the raw record data (with 'data_bytes' and 'start_offset').
        """
        if search_id <= 0:
            raise ValueError("Record ID must be positive.")
        
        try:
            self._acquire_lock()
            if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) < 4:
                return None
                
            with open(self.db_path, 'rb') as f:
                f.read(4) # Skip last ID header
                
                while True:
                    current_pos_before_read = f.tell()
                    record_data_raw = self._read_next_record_raw(f)
                    if record_data_raw is None: # End of file
                        break
                    
                    if record_data_raw['id'] == search_id:
                        record_data_raw['start_offset'] = current_pos_before_read # Add offset
                        return record_data_raw # Return raw data for subsequent DataObject creation
                    # Catch DatabaseError specifically for structural issues
                    if DatabaseError: 
                        logger.warning(f"Skipping corrupt record at position {current_pos_before_read} during ID search: {str(DatabaseError)}")
                        # Try to jump past the corrupt record
                        f.seek(current_pos_before_read + CHUNK_SIZE)
                        continue
                    if Exception:
                        logger.error(f"Unexpected error during search for ID {search_id} at {current_pos_before_read}: {traceback.format_exc()}")
                        break # Stop search on unexpected error
            
            return None # Record not found
        except FileLockError:
            raise
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error searching for record {search_id}: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to search for record {search_id}: {str(e)}")
        finally:
            self._release_lock()

    def _read_next_record_raw(self, file_obj) -> Optional[Dict[str, Any]]:
        """
        Reads the raw binary components of the next record from the file.
        Does not perform DataObject deserialization here.
        Raises DatabaseError for structural corruption.
        """
        try:
            # Read fixed-size header components
            id_bytes = file_obj.read(4)
            if not id_bytes: return None # End of file
            
            validation_byte = file_obj.read(1)
            if not validation_byte: raise DatabaseError("Incomplete record header: missing validation byte.")
            
            size_bytes = file_obj.read(4)
            if not size_bytes: raise DatabaseError("Incomplete record header: missing size bytes.")
            
            # Unpack binary data
            try:
                record_id = struct.unpack('I', id_bytes)[0]
                validation_flag = struct.unpack('?', validation_byte)[0]
                data_size = struct.unpack('I', size_bytes)[0]
            except struct.error as e:
                raise DatabaseError(f"Corrupt record header structure: {str(e)}")
            
            # Validate size before attempting to read data
            if not (0 < data_size <= 10 * 1024 * 1024): # Max 10MB per record
                raise DatabaseError(f"Invalid record data size ({data_size} bytes). Corrupt header or too large.")
            
            data_bytes = file_obj.read(data_size)
            if len(data_bytes) != data_size:
                raise DatabaseError(f"Incomplete record data: expected {data_size} bytes, got {len(data_bytes)}.")
            
            # Calculate checksum for data integrity verification
            checksum = hashlib.md5(data_bytes).hexdigest()
            
            return {
                'id': record_id,
                'validation': validation_flag,
                'size': data_size,
                'checksum': checksum,
                'data_bytes': data_bytes
            }
        except DatabaseError: # Re-raise custom DB errors as they are specific structural issues
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading raw record: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to read raw record data: {str(e)}")

    def write_record(self, data_object: DataObject) -> int:
        """
        Writes a single DataObject to the database file.
        Acquires a lock, creates a backup, appends the record, and updates the last ID.
        """
        if not isinstance(data_object, DataObject):
            raise TypeError("Expected DataObject instance to write.")
        
        # Pre-validate the object before attempting to write
        if not data_object.validate():
            raise DataValidationError("Attempted to write an invalid DataObject.")

        try:
            self._acquire_lock()
            self._create_backup() # Backup before modification
            
            last_id = self.get_last_id() # Get last ID with lock acquired
            new_id = last_id + 1 if last_id > 0 else 1
            
            obj_bytes = data_object.to_bytes()
            size = len(obj_bytes)
            validation_flag = data_object.validate() # Final validation flag
            
            # Use 'ab' (append binary) to append records.
            # If the file is new or empty, 'wb' (write binary) will create/truncate it,
            # ensuring the header is written correctly.
            mode = 'ab' if os.path.exists(self.db_path) and os.path.getsize(self.db_path) >= 4 else 'wb'
            with open(self.db_path, mode) as f:
                # If opening in 'wb' mode, write the initial ID header (0 for now, updated later)
                if mode == 'wb':
                    f.write(struct.pack('I', 0)) # Placeholder for last ID
                
                # Write record header: ID, validation flag, size of data
                f.write(struct.pack('I', new_id))
                f.write(struct.pack('?', validation_flag))
                f.write(struct.pack('I', size))
                f.write(obj_bytes) # Write the actual data bytes
                
                f.flush()
                os.fsync(f.fileno()) # Ensure data is physically written
                
            self.update_last_id(new_id) # Update the file header with the new last ID
            logger.info(f"Successfully wrote record {new_id} to database.")
            return new_id
        except (FileLockError, DatabaseError, DataValidationError):
            raise # Re-raise specific exceptions
        except Exception as e:
            logger.error(f"Unexpected error writing record: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to write record: {str(e)}")
        finally:
            self._release_lock()

    def invalidate_record(self, record_id: int, record_start_offset: int):
        """
        Marks an existing record as invalid by changing its validation flag in the file.
        This is used when a record is logically "deleted" or replaced by a larger update.
        """
        try:
            self._acquire_lock()
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database file not found: {self.db_path}")

            with open(self.db_path, 'r+b') as f:
                # Seek to the position of the validation byte
                # Header: 4 bytes (ID) + 1 byte (Validation Flag)
                validation_byte_offset = record_start_offset + 4 
                f.seek(validation_byte_offset)
                f.write(struct.pack('?', False)) # Write False (0) for validation flag
                f.flush()
                os.fsync(f.fileno())
            logger.info(f"Record ID {record_id} at offset {record_start_offset} marked as invalid.")
        except FileLockError:
            raise
        except Exception as e:
            logger.error(f"Error invalidating record {record_id}: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to invalidate record {record_id}: {str(e)}")
        finally:
            self._release_lock()

    def update_record(self, original_record_id: int, new_data_object: DataObject) -> int:
        """
        Updates an existing record.
        If the new data size is less than or equal to the original, it overwrites in place.
        If the new data size is greater, it invalidates the old record and appends the new one.
        Returns the ID of the updated/new record.
        """
        if not isinstance(new_data_object, DataObject):
            raise TypeError("Expected DataObject instance for new data.")
        if not new_data_object.validate():
            raise DataValidationError("Attempted to update with an invalid DataObject.")

        try:
            self._acquire_lock()
            self._create_backup() # Backup before modification

            # Find the original record's details
            original_record_info = self.read_record_by_id(original_record_id)
            if not original_record_info:
                raise DatabaseError(f"Original record with ID {original_record_id} not found for update.")
            
            original_start_offset = original_record_info['start_offset']
            original_size = original_record_info['size']
            
            new_obj_bytes = new_data_object.to_bytes()
            new_size = len(new_obj_bytes)
            new_validation_flag = new_data_object.validate()

            if new_size <= original_size:
                # Overwrite in place
                with open(self.db_path, 'r+b') as f:
                    f.seek(original_start_offset)
                    # Write original ID, new validation flag, new size, new data
                    f.write(struct.pack('I', original_record_id)) # Keep original ID
                    f.write(struct.pack('?', new_validation_flag))
                    f.write(struct.pack('I', new_size))
                    f.write(new_obj_bytes)
                    
                    # Pad with null bytes if new data is smaller
                    padding_needed = original_size - new_size
                    if padding_needed > 0:
                        f.write(b'\x00' * padding_needed)
                    
                    f.flush()
                    os.fsync(f.fileno())
                logger.info(f"Record ID {original_record_id} updated in place at offset {original_start_offset}.")
                return original_record_id # Return the original ID as it was updated in place
            else:
                # Invalidate old record and append new one
                self.invalidate_record(original_record_id, original_start_offset)
                # Append the new record; it will get a new ID automatically
                new_appended_id = self.write_record(new_data_object)
                logger.info(f"Record ID {original_record_id} invalidated, new record appended with ID {new_appended_id}.")
                return new_appended_id
        except (FileLockError, DatabaseError, DataValidationError):
            raise # Re-raise specific exceptions
        except Exception as e:
            logger.error(f"Unexpected error during record update: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to update record {original_record_id}: {str(e)}")
        finally:
            self._release_lock()


    def _read_csv_iter(self, csv_path: str) -> Iterator[List[str]]:
        """
        Reads CSV file line by line and yields raw row data as a list of strings.
        Handles file encoding and basic CSV errors.
        """
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f, delimiter=CSV_DELIMITER)
                
                # Skip header
                try:
                    next(reader)
                except StopIteration:
                    logger.warning(f"CSV file '{csv_path}' is empty or only contains a header.")
                    return # No data rows to yield
                
                for line_num, row in enumerate(reader, 2): # Start counting from line 2 (after header)
                    yield row
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            raise DatabaseError(f"CSV file not found: {csv_path}")
        except csv.Error as e:
            logger.error(f"CSV parsing error in '{csv_path}': {e}")
            raise DatabaseError(f"Error parsing CSV file: {str(e)}")
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error reading CSV '{csv_path}': {e}. Ensure UTF-8 encoding.")
            raise DatabaseError(f"Encoding error reading CSV. Please ensure it's UTF-8: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error reading CSV file: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to read CSV file: {str(e)}")

    def write_from_csv(
        self, 
        csv_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        Bulk imports records from a CSV file into the database.
        Processes records in a streaming fashion to optimize memory usage.
        Provides progress updates via callback.
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        file_size = os.path.getsize(csv_path)
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"CSV file size ({file_size / (1024*1024):.2f}MB) exceeds maximum allowed of {MAX_FILE_SIZE_MB}MB.")
        
        imported_count = 0
        try:
            self._acquire_lock()
            self._create_backup() # Backup before bulk operation
            
            # Get the current last ID to calculate new IDs sequentially
            last_id = self.get_last_id()
            current_id = last_id + 1 if last_id > 0 else 1

            # Count total records for accurate progress reporting (requires a separate pass)
            total_records = 0
            with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                total_records = sum(1 for line in f) - 1 # Subtract header line

            if total_records <= 0:
                logger.warning(f"No data rows found in CSV file '{csv_path}'.")
                return 0 # No records to import
                
            # Determine initial write mode: 'ab' for append, 'wb' for new file (initial header)
            mode = 'ab' if os.path.exists(self.db_path) and os.path.getsize(self.db_path) >= 4 else 'wb'
            
            with open(self.db_path, mode) as f:
                if mode == 'wb':
                    f.write(struct.pack('I', 0)) # Placeholder for last ID in new file
                
                for i, row in enumerate(self._read_csv_iter(csv_path)):
                    try:
                        # Attempt to create DataObject from the raw row data
                        data_obj = DataObject(row)
                        
                        obj_bytes = data_obj.to_bytes()
                        size = len(obj_bytes)
                        validation_flag = data_obj.validate()
                        
                        f.write(struct.pack('I', current_id))
                        f.write(struct.pack('?', validation_flag))
                        f.write(struct.pack('I', size))
                        f.write(obj_bytes)
                        
                        imported_count += 1
                        current_id += 1 # Increment for the next record
                        
                        # Update progress if callback is provided
                        if progress_callback:
                            progress_callback(i + 1, total_records) # i+1 because enumerate is 0-indexed
                            
                    except (DataValidationError, DatabaseError) as e:
                        logger.warning(f"Skipping invalid record from CSV line {i+2}: {str(e)}") # +2 for 0-indexed i, and header
                        # Continue processing other records even if one fails
                    except Exception as e:
                        logger.error(f"Unexpected error processing CSV line {i+2}: {traceback.format_exc()}")
                        # If an unexpected error occurs, log it and continue
                        
                f.flush()
                os.fsync(f.fileno()) # Ensure all written data is on disk
                
            # Update the last ID in the header after all records are written
            self.update_last_id(current_id - 1)
            logger.info(f"Successfully imported {imported_count} records from CSV.")
            return imported_count
        except (FileLockError, DatabaseError, ValueError, FileNotFoundError):
            raise # Re-raise specific exceptions
        except Exception as e:
            logger.error(f"Unexpected error during CSV import: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to import from CSV: {str(e)}")
        finally:
            self._release_lock()

# --- Streamlit UI Functions ---

def setup_ui():
    """Configures the Streamlit page and applies custom CSS styling."""
    st.set_page_config(
        page_title="Traffic Accidents DB", 
        layout="wide",
        page_icon="🚗"
    )
    
    # Custom CSS for better styling and responsiveness
    st.markdown("""
        <style>
            /* Progress bar styling */
            .stProgress > div > div > div > div {
                background-color: #4CAF50; /* Green */
            }
            /* Main container padding */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1200px; /* Limit content width */
            }
            /* Sidebar styling */
            .sidebar .sidebar-content {
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
            }
            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                color: #2c3e50; /* Darker text for readability */
            }
            /* Custom alert styling */
            .stAlert {
                border-left: 5px solid;
                border-radius: 8px;
                padding: 10px 15px;
                margin-bottom: 15px;
            }
            .stAlert.success { border-color: #4CAF50; background-color: #e6ffe6; }
            .stAlert.info { border-color: #2196F3; background-color: #e0f2fe; }
            .stAlert.warning { border-color: #ff9800; background-color: #fff3e0; }
            .stAlert.error { border-color: #f44336; background-color: #ffe0e0; }

            /* Button styling */
            .stButton>button {
                background-color: #007bff; /* Primary blue */
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                border: none;
                transition: all 0.3s ease;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            }
            .stButton>button:hover {
                background-color: #0056b3; /* Darker blue on hover */
                transform: translateY(-2px); /* Slight lift effect */
                box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
            }
            .stButton>button:active {
                transform: translateY(0);
                box_shadow: 1px 1px 3px rgba(0,0,0,0.2);
            }
            /* Expander styling */
            .streamlit-expanderHeader {
                background-color: #e9ecef; /* Light gray */
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
            /* Text input and selectbox styling */
            .stTextInput>div>div>input, .stSelectbox>div>div>select {
                border-radius: 5p x;
                border: 1px solid #ced4da;
                padding: 8px;
            }
            /* Responsive columns */
            @media (max-width: 768px) {
                .main .block-container {
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
                .st-cf { /* Target columns for smaller screens */
                    flex-direction: column;
                }
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🚗 Traffic Accidents Database Manager")
    st.caption("A comprehensive system for managing traffic accident records")
    
    try:
        db = TrafficAccidentsDB() # Initialize DB handler

        # Initialize or retrieve operation from session state
        # Use a temporary signal for redirection to avoid direct modification of `sidebar_operation`
        if 'redirect_to_operation' not in st.session_state:
            st.session_state.redirect_to_operation = None
        
        # Determine the initial operation for the radio button
        initial_operation_index = 0 # Default to 'View All Records'
        operations_list = ["📄 View All Records", "🔍 Search by ID", "✍️ Add New Record", "🔄 Update Existing Record", "📤 Import from CSV"]

        if st.session_state.redirect_to_operation:
            if st.session_state.redirect_to_operation in operations_list:
                initial_operation_index = operations_list.index(st.session_state.redirect_to_operation)
            st.session_state.redirect_to_operation = None # Clear the redirection signal


        with st.sidebar:
            st.header("Navigation")
            operation = st.radio(
                "Select Operation",
                operations_list,
                index=initial_operation_index, # Set the initial selection based on redirection
                label_visibility="visible",
                key="sidebar_operation" # Ensure unique key
            )
            
            st.divider()
            st.header("Database Info")
            try:
                last_id = db.get_last_id()
                st.metric("Last Record ID", last_id if last_id > 0 else "No records yet")
            except Exception as e:
                st.error(f"Could not retrieve last record ID: {str(e)}")
                logger.error(f"Failed to get last ID for sidebar: {e}")
            
            st.markdown("---") # Visual separator
            st.subheader("Actions")
            if st.button("🔄 Refresh Application", use_container_width=True, help="Reloads the entire Streamlit application."):
                st.rerun() # Use st.rerun for a full app refresh

            st.markdown("---") # Visual separator
            display_activity_log() # Display the activity log
        
        # Dispatch based on selected operation
        if operation == "📄 View All Records":
            view_all_records(db)
        elif operation == "🔍 Search by ID":
            search_by_id(db)
        elif operation == "✍️ Add New Record":
            add_new_record(db)
        elif operation == "🔄 Update Existing Record":
            update_record_ui(db)
        elif operation == "📤 Import from CSV":
            import_from_csv(db)
            
    except DatabaseError as e:
        st.error(f"🚨 A critical database error occurred: {str(e)}. Please check application logs.")
        logger.critical(f"Critical DatabaseError in main application setup: {traceback.format_exc()}")
    except FileLockError as e:
        st.error(f"🔒 Failed to acquire file lock: {str(e)}. Another process might be using the database.")
        logger.critical(f"FileLockError in main application setup: {traceback.format_exc()}")
    except Exception as e:
        st.error(f"❌ An unexpected error occurred: {str(e)}. Please try again or contact support.")
        logger.critical(f"Unexpected error in main application setup: {traceback.format_exc()}")

def display_record_data(data_obj: DataObject):
    """
    Displays the details of a single DataObject in a user-friendly format.
    Handles missing attributes gracefully.
    """
    try:
        cols = st.columns(2)
        
        with cols[0]:
            st.subheader("Accident Details")
            st.markdown(f"**Date:** `{getattr(data_obj, 'crash_date', 'N/A')}`")
            st.markdown(f"**Type:** `{getattr(data_obj, 'crash_type', 'N/A')}`")
            st.markdown(f"**Traffic Control:** `{getattr(data_obj, 'traffic_control_device', 'N/A')}`")
            st.markdown(f"**Weather:** `{getattr(data_obj, 'weather_condition', 'N/A')}`")
            st.markdown(f"**Lighting:** `{getattr(data_obj, 'lighting_condition', 'N/A')}`")
            st.markdown(f"**First Crash Type:** `{getattr(data_obj, 'first_crash_type', 'N/A')}`")
            st.markdown(f"**Road Surface:** `{getattr(data_obj, 'roadway_surface_cond', 'N/A')}`")
            st.markdown(f"**Road Defect:** `{getattr(data_obj, 'road_defect', 'N/A')}`")
        
        with cols[1]:
            st.subheader("Impact Details")
            st.markdown(f"**Units Involved:** `{getattr(data_obj, 'num_units', 0)}`")
            st.markdown(f"**Total Injuries:** `{getattr(data_obj, 'injuries_total', 0.0):.2f}`")
            st.markdown(f"**Fatal Injuries:** `{getattr(data_obj, 'injuries_fatal', 0.0):.2f}`")
            st.markdown(f"**Incapacitating:** `{getattr(data_obj, 'injuries_incapacitating', 0.0):.2f}`")
            st.markdown(f"**Non-Incapacitating:** `{getattr(data_obj, 'injuries_non_incapacitating', 0.0):.2f}`")
            st.markdown(f"**Reported Not Evident:** `{getattr(data_obj, 'injuries_reported_not_evident', 0.0):.2f}`")
            st.markdown(f"**No Indication:** `{getattr(data_obj, 'injuries_no_indication', 0.0):.2f}`")
            st.markdown(f"**Primary Cause:** `{getattr(data_obj, 'prim_contributory_cause', 'N/A')}`")
            st.markdown(f"**Intersection Related:** `{getattr(data_obj, 'intersection_related_i', 'NO')}`")

            st.subheader("Temporal Details")
            st.markdown(f"**Crash Hour:** `{getattr(data_obj, 'crash_hour', 0)}`")
            st.markdown(f"**Day of Week:** `{getattr(data_obj, 'crash_day_of_week', 1)}`")
            st.markdown(f"**Month:** `{getattr(data_obj, 'crash_month', 1)}`")
    except Exception as e:
        logger.error(f"Error displaying record data: {traceback.format_exc()}")
        st.error("Failed to display record details due to an internal error.")

def view_all_records(db: TrafficAccidentsDB):
    """
    Displays records with pagination and filtering options.
    Records are fetched in chunks to optimize performance.
    """
    st.header("All Records")
    
    # Get total records from the database header (most efficient way)
    total_records_in_db = db.get_last_id()

    if total_records_in_db == 0:
        st.info("No records found in the database. Try importing from CSV or adding a new record.")
        return

    # --- Filtering and Pagination Controls ---
    with st.expander("🔍 Filter & Sort Records", expanded=True):
        filter_cols = st.columns(3)
        with filter_cols[0]:
            search_query = st.text_input("Search Crash Type", key="search_crash_type_all", help="Enter text to filter by crash type.")
        with filter_cols[1]:
            min_injuries = st.number_input("Min Total Injuries", min_value=0.0, value=0.0, step=0.1, key="min_injuries_all", help="Only show records with at least this many total injuries.")
        with filter_cols[2]:
            only_valid = st.checkbox("Show Only Valid Records", value=False, key="only_valid_checkbox", help="Toggle to display only records marked as valid.")
        
    # Pagination controls
    page_cols = st.columns([1, 1, 2])
    with page_cols[0]:
        page_size = st.selectbox(
            "Records per page",
            [10, 20, 50, 100, total_records_in_db], # Option to show all records if applicable
            index=1, # Default to 20 per page
            key="view_page_size"
        )
    
    # Calculate total pages based on the actual total records in DB, not just filtered ones
    total_pages = max(1, (total_records_in_db + page_size - 1) // page_size) 
    
    # Create a list of page numbers for the selectbox
    page_options = list(range(1, total_pages + 1))
    
    with page_cols[1]:
        # Determine the initial index for the selectbox to maintain current page if possible
        # Ensure the selected page is within the valid range
        current_page = st.selectbox(
            "Page", 
            options=page_options,
            index=min(st.session_state.get("view_page_num", 1), total_pages) - 1, # Default to page 1, adjust for 0-indexed selectbox
            key="view_page_num"
        )

    # Calculate offset for fetching records
    start_offset = (current_page - 1) * page_size
    
    # Fetch only the records for the current page
    current_page_raw_records = []
    with st.spinner(f"Loading records for page {current_page}..."):
        try:
            current_page_raw_records = db.read_records_paginated(offset=start_offset, limit=page_size)
            logger.info(f"Loaded {len(current_page_raw_records)} raw records for page {current_page}.")
        except DatabaseError as e:
            st.error(f"Failed to load records for current page: {str(e)}")
            logger.error(f"Error loading paginated records: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred while loading page records: {str(e)}")
            logger.error(f"Unexpected error in view_all_records pagination: {traceback.format_exc()}")


    # Filter records based on the fetched subset
    filtered_records_with_obj = [] # Will store {id, validation, checksum, data_obj_instance}
    for record_raw in current_page_raw_records:
        try:
            # Reconstruct DataObject from raw bytes for filtering and display
            data_obj = DataObject.from_bytes(record_raw['data_bytes'])
            
            # Apply 'only_valid' filter
            if only_valid and not record_raw.get('validation', True): 
                continue
            
            # Apply search query filter (case-insensitive)
            if search_query:
                if not getattr(data_obj, 'crash_type', '').lower().startswith(search_query.lower()):
                    continue
            
            # Apply min injuries filter
            if getattr(data_obj, 'injuries_total', 0.0) < min_injuries:
                continue
            
            # Add the reconstructed object and its original metadata
            filtered_records_with_obj.append({
                'id': record_raw['id'],
                'validation': record_raw['validation'],
                'size': record_raw['size'],
                'checksum': record_raw['checksum'],
                'data': data_obj # This is now the DataObject instance
            })
        except (DataValidationError, DatabaseError) as e:
            logger.warning(f"Skipping record ID {record_raw.get('id', 'N/A')} due to deserialization/validation error: {e}")
            continue # Skip corrupt or invalid records during display
        except Exception as e:
            logger.error(f"Unexpected error processing raw record for display (ID: {record_raw.get('id', 'N/A')}): {traceback.format_exc()}")
            continue

    st.info(f"Displaying {len(filtered_records_with_obj)} record(s) on page {current_page} after filtering.")
    
    if not filtered_records_with_obj:
        st.warning("No records match your current filters on this page.")
    
    for i, record_with_obj in enumerate(filtered_records_with_obj):
        # Use a unique key for each expander based on record ID
        expander_key = f"record_expander_{record_with_obj['id']}"
        with st.expander(
            f"📝 Record ID: {record_with_obj['id']} "
            f"({'✅ Valid' if record_with_obj['validation'] else '❌ Invalid'}) "
            f"- {getattr(record_with_obj['data'], 'crash_date', 'N/A')} - {getattr(record_with_obj['data'], 'crash_type', 'N/A')}",
            expanded=False # Start collapsed
        ):
            tab1, tab2, tab3 = st.tabs(["Data View", "Raw Data", "Checksum Info"])
            with tab1:
                display_record_data(record_with_obj['data']) # Pass the reconstructed DataObject
            with tab2:
                # Convert DataObject back to dict for JSON display
                record_data_dict = {field: getattr(record_with_obj['data'], field, None) for field in FIELDS}
                st.json(record_data_dict)
            with tab3:
                st.markdown(f"**Record Size (bytes):** `{record_with_obj['size']}`")
                st.markdown(f"**MD5 Checksum:** `{record_with_obj['checksum']}`")
                st.info("Checksum helps verify data integrity. Mismatches could indicate corruption.")
    
    st.caption(f"Showing records {start_offset + 1}-{start_offset + len(filtered_records_with_obj)} of {total_records_in_db} (Total: {total_records_in_db})")


def search_by_id(db: TrafficAccidentsDB):
    """
    Provides an interface to search for a specific record by its ID.
    Displays detailed information for the found record.
    Includes functionality to delete (invalidate) a record.
    """
    st.header("Search Record by ID")
    
    # Use session state to store search result, error message, and delete confirmation status
    if 'search_result_raw' not in st.session_state:
        st.session_state.search_result_raw = None # Stores the raw record data including start_offset
    if 'search_result_data_obj' not in st.session_state:
        st.session_state.search_result_data_obj = None # Stores the DataObject instance for display
    if 'search_error_id' not in st.session_state:
        st.session_state.search_error_id = None
    if 'confirm_delete_id' not in st.session_state:
        st.session_state.confirm_delete_id = None
    if 'delete_message' not in st.session_state:
        st.session_state.delete_message = None

    col1, col2 = st.columns([1, 3])
    
    with col1:
        last_id = db.get_last_id() # Get last ID to set max_value for input
        search_id_input = st.number_input(
            "Enter Record ID", 
            min_value=1, 
            max_value=last_id if last_id > 0 else 1000000, # Provide a large max if no records
            step=1,
            value=st.session_state.get("search_id_input_val", 1), # Persist input value
            key="search_id_input",
            help=f"Enter a numeric ID to search (e.g., between 1 and {last_id if last_id > 0 else 'N/A'})."
        )
        st.session_state.search_id_input_val = search_id_input # Store for persistence
        
        search_button_clicked = st.button("🔎 Search", key="search_button")
        clear_search_button_clicked = st.button("🗑️ Clear Search", key="clear_search_button")
        
        if search_button_clicked:
            if search_id_input > last_id and last_id > 0:
                st.session_state.search_error_id = f"ID {search_id_input} is greater than the last recorded ID ({last_id})."
                st.session_state.search_result_raw = None
                st.session_state.search_result_data_obj = None
                st.session_state.confirm_delete_id = None # Clear any pending confirmation
                st.session_state.delete_message = None
            else:
                with st.spinner(f"Searching for record ID {search_id_input}..."):
                    try:
                        record_raw = db.read_record_by_id(search_id_input) # Get raw data including start_offset
                        if record_raw:
                            st.session_state.search_result_raw = record_raw
                            st.session_state.search_result_data_obj = DataObject.from_bytes(record_raw['data_bytes'])
                            st.session_state.search_error_id = None
                            st.session_state.confirm_delete_id = None # Clear any pending confirmation
                            st.session_state.delete_message = None
                        else:
                            st.session_state.search_result_raw = None
                            st.session_state.search_result_data_obj = None
                            st.session_state.search_error_id = f"Record ID {search_id_input} not found in the database."
                            st.session_state.confirm_delete_id = None
                            st.session_state.delete_message = None
                    except (DatabaseError, DataValidationError, ValueError) as e:
                        st.session_state.search_error_id = f"Search failed: {str(e)}"
                        st.session_state.search_result_raw = None
                        st.session_state.search_result_data_obj = None
                        st.session_state.confirm_delete_id = None
                        st.session_state.delete_message = None
                        logger.error(f"Error during search_by_id: {traceback.format_exc()}")
                    except Exception as e:
                        st.session_state.search_error_id = f"An unexpected error occurred during search: {str(e)}"
                        logger.error(f"Unexpected error during search_by_id: {traceback.format_exc()}")
                        st.session_state.search_result_raw = None
                        st.session_state.search_result_data_obj = None
                        st.session_state.confirm_delete_id = None
                        st.session_state.delete_message = None
        
        if clear_search_button_clicked:
            st.session_state.search_result_raw = None
            st.session_state.search_result_data_obj = None
            st.session_state.search_error_id = None
            st.session_state.confirm_delete_id = None
            st.session_state.delete_message = None
            st.session_state.search_id_input_val = 1 # Reset input value for widget
            st.rerun() # Rerun to clear the display area cleanly
            
    with col2:
        if st.session_state.delete_message:
            st.info(st.session_state.delete_message)
            # Clear message after display, unless it's a success message that causes rerun
            if "successfully deleted" not in st.session_state.delete_message:
                time.sleep(2) # Give user time to read
                st.session_state.delete_message = None
                st.rerun() # Rerun to clear the message

        if st.session_state.search_result_raw and st.session_state.search_result_data_obj:
            record_raw = st.session_state.search_result_raw
            record_data_obj = st.session_state.search_result_data_obj
            
            st.success(f"✅ Found record ID: {record_raw['id']}")
            
            # Display delete confirmation if pending for this ID
            if st.session_state.confirm_delete_id == record_raw['id']:
                st.warning(f"Are you sure you want to delete Record ID: **{record_raw['id']}**?")
                col_confirm = st.columns(2)
                with col_confirm[0]:
                    if st.button("Yes, Delete", key="confirm_delete_yes"):
                        try:
                            # Use the stored original offset to invalidate the record
                            db.invalidate_record(record_raw['id'], record_raw['start_offset'])
                            st.session_state.delete_message = f"✅ Record ID **{record_raw['id']}** successfully deleted (marked as invalid)."
                            st.session_state.search_result_raw = None # Clear search result
                            st.session_state.search_result_data_obj = None
                            st.session_state.confirm_delete_id = None # Clear confirmation
                            st.session_state.search_id_input_val = 1 # Reset input after delete
                            # Set the redirection signal
                            st.session_state.redirect_to_operation = "📄 View All Records"
                            st.rerun() # Rerun to navigate
                        except DatabaseError as e:
                            st.session_state.delete_message = f"❌ Error deleting record: {str(e)}"
                            logger.error(f"Failed to delete record: {traceback.format_exc()}")
                        except Exception as e:
                            st.session_state.delete_message = f"❌ An unexpected error occurred during deletion: {str(e)}"
                            logger.error(f"Unexpected error during deletion: {traceback.format_exc()}")
                        st.rerun() # Rerun to update status/message
                with col_confirm[1]:
                    if st.button("No, Keep", key="confirm_delete_no"):
                        st.session_state.delete_message = "The record has been kept in the Database."
                        st.session_state.confirm_delete_id = None # Clear confirmation
                        st.rerun() # Rerun to clear confirmation prompt and show message
            else:
                # Show delete button if no confirmation is pending for this ID
                col_actions = st.columns(2)
                with col_actions[0]:
                    if st.button("🗑️ Delete Registry", key="delete_registry_button"):
                        st.session_state.confirm_delete_id = record_raw['id']
                        st.session_state.delete_message = None # Clear previous delete message
                        st.rerun() # Rerun to show the confirmation prompt
                with col_actions[1]:
                    if st.button("🔄 Redirect to Update Form", key="redirect_to_update_button"):
                        # Set the redirection signal
                        st.session_state.redirect_to_operation = "🔄 Update Existing Record"
                        st.session_state.update_record_id_input = record_raw['id']
                        # Pre-fill the update form with the current record's raw data
                        st.session_state.loaded_record_for_update = record_raw
                        st.rerun()


            # Display the record details if not in confirmation mode
            if not st.session_state.confirm_delete_id:
                tab1, tab2, tab3 = st.tabs(["Data View", "Raw JSON", "Checksum Info"])
                with tab1:
                    display_record_data(record_data_obj) # Pass the reconstructed DataObject
                with tab2:
                    # Convert DataObject back to dict for JSON display
                    record_data_dict = {field: getattr(record_data_obj, field, None) for field in FIELDS}
                    st.json(record_data_dict)
                with tab3:
                    st.markdown(f"**Record Size (bytes):** `{record_raw['size']}`")
                    st.markdown(f"**MD5 Checksum:** `{record_raw['checksum']}`")
                    st.info("Checksum helps verify data integrity. Mismatches could indicate corruption.")
        elif st.session_state.search_error_id:
            st.error(st.session_state.search_error_id)
        else:
            st.info("Enter an ID and click 'Search' to find a record.")

def update_record_ui(db: TrafficAccidentsDB):
    """
    Provides a UI to search for a record, load its data into a form,
    and then update it (either in-place or by invalidating and appending).
    """
    st.header("Update Existing Record")

    if 'update_record_id_input' not in st.session_state:
        st.session_state.update_record_id_input = 1 # Default value
    if 'loaded_record_for_update' not in st.session_state:
        st.session_state.loaded_record_for_update = None # Stores the raw record data + offset
    if 'update_record_error' not in st.session_state:
        st.session_state.update_record_error = None
    if 'update_record_success' not in st.session_state:
        st.session_state.update_record_success = None

    col_load, col_display = st.columns([1, 3])

    with col_load:
        last_id = db.get_last_id()
        st.session_state.update_record_id_input = st.number_input(
            "Enter Record ID to Update",
            min_value=1,
            max_value=last_id if last_id > 0 else 1000000,
            step=1,
            value=st.session_state.update_record_id_input,
            key="update_record_id_input_widget", # Unique key for the widget
            help=f"Enter the ID of the record you wish to update (e.g., between 1 and {last_id if last_id > 0 else 'N/A'})."
        )

        if st.button("Load Record for Update", key="load_record_update_button"):
            st.session_state.update_record_error = None
            st.session_state.update_record_success = None
            if st.session_state.update_record_id_input > last_id and last_id > 0:
                st.session_state.update_record_error = f"ID {st.session_state.update_record_id_input} is greater than the last recorded ID ({last_id})."
                st.session_state.loaded_record_for_update = None
            else:
                with st.spinner(f"Loading record ID {st.session_state.update_record_id_input}..."):
                    try:
                        # read_record_by_id now includes 'start_offset'
                        record_raw = db.read_record_by_id(st.session_state.update_record_id_input)
                        if record_raw:
                            st.session_state.loaded_record_for_update = record_raw
                        else:
                            st.session_state.update_record_error = f"Record ID {st.session_state.update_record_id_input} not found."
                            st.session_state.loaded_record_for_update = None
                    except (DatabaseError, ValueError) as e:
                        st.session_state.update_record_error = f"Failed to load record: {str(e)}"
                        logger.error(f"Error loading record for update UI: {traceback.format_exc()}")
                        st.session_state.loaded_record_for_update = None
                    except Exception as e:
                        st.session_state.update_record_error = f"An unexpected error occurred loading record: {str(e)}"
                        logger.error(f"Unexpected error loading record for update UI: {traceback.format_exc()}")
                        st.session_state.loaded_record_for_update = None
        
        if st.button("Clear Update Form", key="clear_update_form_button"):
            st.session_state.loaded_record_for_update = None
            st.session_state.update_record_error = None
            st.session_state.update_record_success = None
            st.session_state.update_record_id_input = 1 # Reset input
            st.rerun() # Rerun to clear the form

    with col_display:
        if st.session_state.update_record_error:
            st.error(st.session_state.update_record_error)
        if st.session_state.update_record_success:
            st.success(st.session_state.update_record_success)

        if st.session_state.loaded_record_for_update:
            original_record_id = st.session_state.loaded_record_for_update['id']
            # Convert raw bytes to DataObject for form pre-filling
            original_data_obj = DataObject.from_bytes(st.session_state.loaded_record_for_update['data_bytes'])

            st.subheader(f"Editing Record ID: {original_record_id}")
            if not st.session_state.loaded_record_for_update['validation']:
                st.warning("⚠️ This record is currently marked as invalid. Updating it will create a new valid entry if its size increases.")

            with st.form("edit_record_form", clear_on_submit=False):
                # Pre-fill form fields using the loaded DataObject
                # You'll need to map each field from DataObject to a Streamlit widget
                # Example for required fields:
                cols_req = st.columns(2)
                with cols_req[0]:
                    edited_crash_date = st.date_input(
                        "Crash Date*",
                        value=datetime.strptime(original_data_obj.crash_date, '%Y-%m-%d').date() if original_data_obj.crash_date else date.today(),
                        key="edit_crash_date"
                    )
                with cols_req[1]:
                    edited_crash_type = st.text_input(
                        "Crash Type*",
                        value=original_data_obj.crash_type,
                        key="edit_crash_type"
                    )
                
                cols_units_inj = st.columns(2)
                with cols_units_inj[0]:
                    edited_num_units = st.number_input(
                        "Number of Units Involved*",
                        min_value=0, max_value=999, value=original_data_obj.num_units, step=1,
                        key="edit_num_units"
                    )
                with cols_units_inj[1]:
                    edited_injuries_total = st.number_input(
                        "Total Injuries*",
                        min_value=0.0, value=original_data_obj.injuries_total, step=0.1,
                        key="edit_injuries_total"
                    )

                st.subheader("Optional Details")
                cols1 = st.columns(3)
                with cols1[0]:
                    edited_traffic_control_device = st.selectbox(
                        "Traffic Control Device",
                        ["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN", "YIELD SIGN", "NONE", "OTHER"],
                        index=["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN", "YIELD SIGN", "NONE", "OTHER"].index(original_data_obj.traffic_control_device) if original_data_obj.traffic_control_device in ["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN", "YIELD SIGN", "NONE", "OTHER"] else 0,
                        key="edit_tcd"
                    )
                    edited_weather_condition = st.selectbox(
                        "Weather Condition",
                        ["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG", "SEVERE CROSSWINDS", "SLEET", "OTHER"],
                        index=["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG", "SEVERE CROSSWINDS", "SLEET", "OTHER"].index(original_data_obj.weather_condition) if original_data_obj.weather_condition in ["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG", "SEVERE CROSSWINDS", "SLEET", "OTHER"] else 0,
                        key="edit_weather"
                    )
                    edited_lighting_condition = st.selectbox(
                        "Lighting Condition",
                        ["UNKNOWN", "DAYLIGHT", "DARK - LIGHTED", "DARK - NOT LIGHTED", "DUSK/DAWN"],
                        index=["UNKNOWN", "DAYLIGHT", "DARK - LIGHTED", "DARK - NOT LIGHTED", "DUSK/DAWN"].index(original_data_obj.lighting_condition) if original_data_obj.lighting_condition in ["UNKNOWN", "DAYLIGHT", "DARK - LIGHTED", "DARK - NOT LIGHTED", "DUSK/DAWN"] else 0,
                        key="edit_lighting"
                    )
                with cols1[1]:
                    edited_first_crash_type = st.text_input("First Crash Type (Specific)", value=original_data_obj.first_crash_type, key="edit_first_crash_type")
                    edited_trafficway_type = st.text_input("Trafficway Type", value=original_data_obj.trafficway_type, key="edit_trafficway_type")
                    edited_alignment = st.text_input("Alignment", value=original_data_obj.alignment, key="edit_alignment")
                    edited_roadway_surface_cond = st.selectbox(
                        "Roadway Surface Condition",
                        ["UNKNOWN", "DRY", "WET", "SNOW/ICE", "SAND/MUD/DIRT/OIL"],
                        index=["UNKNOWN", "DRY", "WET", "SNOW/ICE", "SAND/MUD/DIRT/OIL"].index(original_data_obj.roadway_surface_cond) if original_data_obj.roadway_surface_cond in ["UNKNOWN", "DRY", "WET", "SNOW/ICE", "SAND/MUD/DIRT/OIL"] else 0,
                        key="edit_surface_cond"
                    )
                with cols1[2]:
                    edited_road_defect = st.selectbox(
                        "Road Defect",
                        ["NONE", "RUT, HOLES", "SHOULDER DEFECT", "DEBRIS ON ROADWAY", "OTHER"],
                        index=["NONE", "RUT, HOLES", "SHOULDER DEFECT", "DEBRIS ON ROADWAY", "OTHER"].index(original_data_obj.road_defect) if original_data_obj.road_defect in ["NONE", "RUT, HOLES", "SHOULDER DEFECT", "DEBRIS ON ROADWAY", "OTHER"] else 0,
                        key="edit_road_defect"
                    )
                    edited_intersection_related_i = st.selectbox(
                        "Intersection Related?",
                        ["NO", "YES"],
                        index=["NO", "YES"].index(original_data_obj.intersection_related_i) if original_data_obj.intersection_related_i in ["NO", "YES"] else 0,
                        key="edit_intersection_related"
                    )
                    edited_damage = st.text_input("Damage Description", value=original_data_obj.damage, key="edit_damage")
                    edited_prim_contributory_cause = st.text_input("Primary Contributory Cause", value=original_data_obj.prim_contributory_cause, key="edit_prim_cause")
                    edited_most_severe_injury = st.selectbox(
                        "Most Severe Injury",
                        ["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"],
                        index=["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"].index(original_data_obj.most_severe_injury) if original_data_obj.most_severe_injury in ["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"] else 0,
                        key="edit_most_severe_injury"
                    )

                st.subheader("Detailed Injuries & Temporal Data")
                inj_cols = st.columns(3)
                with inj_cols[0]:
                    edited_injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0, value=original_data_obj.injuries_fatal, step=0.1, key="edit_injuries_fatal")
                    edited_injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0, value=original_data_obj.injuries_incapacitating, step=0.1, key="edit_injuries_incapacitating")
                with inj_cols[1]:
                    edited_injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0, value=original_data_obj.injuries_non_incapacitating, step=0.1, key="edit_injuries_non_incapacitating")
                    edited_injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0, value=original_data_obj.injuries_reported_not_evident, step=0.1, key="edit_injuries_reported_not_evident")
                with inj_cols[2]:
                    edited_injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0, value=original_data_obj.injuries_no_indication, step=0.1, key="edit_injuries_no_indication")
                
                temp_cols = st.columns(3)
                with temp_cols[0]:
                    edited_crash_hour = st.slider("Crash Hour (0-23)", 0, 23, original_data_obj.crash_hour, key="edit_crash_hour")
                with temp_cols[1]:
                    edited_crash_day_of_week = st.slider("Day of Week (1=Monday, 7=Sunday)", 1, 7, original_data_obj.crash_day_of_week, key="edit_crash_day_of_week")
                with temp_cols[2]:
                    edited_crash_month = st.slider("Month (1-12)", 1, 12, original_data_obj.crash_month, key="edit_crash_month")
                
                update_submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)

                if update_submitted:
                    # Basic frontend validation
                    if edited_crash_date is None:
                        st.error("🚨 Crash Date is a required field.")
                        st.stop()
                    if not edited_crash_type:
                        st.error("🚨 Crash Type is a required field.")
                        st.stop()
                    if edited_num_units is None or edited_num_units < 0:
                        st.error("🚨 Number of Units must be a non-negative number.")
                        st.stop()
                    if edited_injuries_total is None or edited_injuries_total < 0:
                        st.error("🚨 Total Injuries must be a non-negative number.")
                        st.stop()

                    try:
                        # Prepare row_data for new DataObject constructor
                        new_row_data = [""] * len(FIELDS)
                        new_row_data[0] = edited_crash_date.strftime('%Y-%m-%d') if edited_crash_date else ""
                        new_row_data[1] = edited_traffic_control_device
                        new_row_data[2] = edited_weather_condition
                        new_row_data[3] = edited_lighting_condition
                        new_row_data[4] = edited_first_crash_type
                        new_row_data[5] = edited_trafficway_type
                        new_row_data[6] = edited_alignment
                        new_row_data[7] = edited_roadway_surface_cond
                        new_row_data[8] = edited_road_defect
                        new_row_data[9] = edited_crash_type
                        new_row_data[10] = edited_intersection_related_i
                        new_row_data[11] = edited_damage
                        new_row_data[12] = edited_prim_contributory_cause
                        new_row_data[13] = str(edited_num_units)
                        new_row_data[14] = edited_most_severe_injury
                        new_row_data[15] = str(edited_injuries_total)
                        new_row_data[16] = str(edited_injuries_fatal)
                        new_row_data[17] = str(edited_injuries_incapacitating)
                        new_row_data[18] = str(edited_injuries_non_incapacitating)
                        new_row_data[19] = str(edited_injuries_reported_not_evident)
                        new_row_data[20] = str(edited_injuries_no_indication)
                        new_row_data[21] = str(edited_crash_hour)
                        new_row_data[22] = str(edited_crash_day_of_week)
                        new_row_data[23] = str(edited_crash_month)
                        
                        new_data_obj = DataObject(new_row_data)
                        
                        updated_id = db.update_record(original_record_id, new_data_obj)
                        
                        st.session_state.update_record_success = f"🎉 Record ID **{original_record_id}** successfully updated. New ID (if appended): **{updated_id}**"
                        st.session_state.update_record_error = None
                        st.session_state.loaded_record_for_update = None # Clear loaded record to force re-load
                        st.balloons()
                        st.rerun() # Rerun to show success and clear form
                    except (DatabaseError, DataValidationError, ValueError) as e:
                        st.session_state.update_record_error = f"❌ Error updating record: {str(e)}"
                        st.session_state.update_record_success = None
                        logger.error(f"Failed to update record: {traceback.format_exc()}")
                    except Exception as e:
                        st.session_state.update_record_error = f"❌ An unexpected error occurred during update: {str(e)}"
                        st.session_state.update_record_success = None
                        logger.error(f"Unexpected error updating record: {traceback.format_exc()}")

def import_from_csv(db: TrafficAccidentsDB):
    """
    Handles CSV file upload and imports records into the database.
    Provides real-time progress updates and detailed results.
    """
    st.header("Import Records from CSV")
    
    try:
        uploaded_file = st.file_uploader(
            "Choose a CSV file to import", 
            type="csv",
            key="csv_uploader",
            help=f"Select a CSV file (max {MAX_FILE_SIZE_MB}MB) with traffic accident data. Data should be delimited by '{CSV_DELIMITER}'."
        )
        
        if uploaded_file is not None:
            # Display uploaded file details
            st.info(f"File '{uploaded_file.name}' uploaded. Size: {uploaded_file.size / (1024*1024):.2f} MB")
            
            # Frontend check for file size (already done by DB class, but good for UX)
            if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"🚫 File size exceeds maximum allowed of {MAX_FILE_SIZE_MB}MB.")
                return
            
            # Use a temporary file to save the uploaded content
            # Streamlit runs in different environments, tempfile is safest
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            if st.button("🚀 Start Import", key="import_button", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                result_container = st.empty()
                
                def update_progress(current: int, total: int):
                    """Callback function to update the Streamlit progress bar and status text."""
                    if total > 0:
                        progress = min(int((current / total) * 100), 100)
                    else:
                        progress = 100 # Handle case of 0 total records gracefully
                    progress_bar.progress(progress)
                    status_text.markdown(
                        f"**Progress:** {current}/{total} records ({progress}%)"
                    )
                
                try:
                    with st.spinner("Importing records... This may take a while for large files."):
                        start_time = time.time()
                        imported_count = db.write_from_csv(tmp_path, update_progress)
                        duration = time.time() - start_time
                    
                    progress_bar.progress(100) # Ensure 100% completion
                    status_text.empty() # Clear status text
                    
                    result_container.success(
                        f"🎉 Import complete! Successfully imported {imported_count} records.  \n"
                        f"**Last Record ID:** {db.get_last_id()}  \n"
                        f"**Time elapsed:** {duration:.2f} seconds"
                    )
                    st.balloons()
                    # Rerun to refresh 'View All Records' or 'Search by ID' if user navigates there
                    st.rerun() 
                except (DatabaseError, FileLockError, ValueError, FileNotFoundError) as e:
                    progress_bar.empty()
                    status_text.empty()
                    result_container.error(f"❌ Import failed: {str(e)}")
                    logger.error(f"CSV import failed: {traceback.format_exc()}")
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    result_container.error(f"❌ An unexpected error occurred during import: {str(e)}")
                    logger.error(f"Unexpected error during CSV import: {traceback.format_exc()}")
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        logger.info(f"Cleaned up temporary CSV file: {tmp_path}")
        else:
            st.info("Upload a CSV file to begin the import process.")
    except Exception as e:
        logger.error(f"Error in import_from_csv UI setup: {traceback.format_exc()}")
        st.error(f"An error occurred while setting up the CSV import interface: {str(e)}")


def add_new_record(db: TrafficAccidentsDB):
    """
    Provides a form for users to manually add a new accident record.
    Includes input validation and clear feedback.
    """
    st.header("Add New Accident Record")
    
    with st.form("record_form", clear_on_submit=True):
        st.subheader("Required Accident Details (*)")
        cols_req = st.columns(2)
        
        with cols_req[0]:
            crash_date = st.date_input(
                "Crash Date*",
                value=date.today(),
                help="Date of the accident (YYYY-MM-DD)",
                key="add_crash_date"
            )
        with cols_req[1]:
            crash_type = st.text_input(
                "Crash Type*",
                help="Main type of collision (e.g., Rear-End, Head-On, Side-Swipe, Rollover)",
                key="add_crash_type"
            )
        
        cols_units_inj = st.columns(2)
        with cols_units_inj[0]:
            num_units = st.number_input(
                "Number of Units Involved*",
                min_value=0,
                max_value=999,
                value=1,
                step=1,
                help="Total number of vehicles/units involved in the crash.",
                key="add_num_units"
            )
        with cols_units_inj[1]:
            injuries_total = st.number_input(
                "Total Injuries*",
                min_value=0.0,
                value=0.0,
                step=0.1,
                help="Total count of all injuries (fatal, incapacitating, etc.).",
                key="add_injuries_total"
            )

        st.subheader("Optional Details")
        cols1 = st.columns(3)
        with cols1[0]:
            traffic_control_device = st.selectbox(
                "Traffic Control Device",
                ["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN", "YIELD SIGN", "NONE", "OTHER"],
                index=0, key="add_tcd"
            )
            weather_condition = st.selectbox(
                "Weather Condition",
                ["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG", "SEVERE CROSSWINDS", "SLEET", "OTHER"],
                index=0, key="add_weather"
            )
            lighting_condition = st.selectbox(
                "Lighting Condition",
                ["UNKNOWN", "DAYLIGHT", "DARK - LIGHTED", "DARK - NOT LIGHTED", "DUSK/DAWN"],
                index=0, key="add_lighting"
            )
        with cols1[1]:
            first_crash_type = st.text_input(
                "First Crash Type (Specific)",
                help="More specific first contact point, if known.",
                key="add_first_crash_type"
            )
            trafficway_type = st.text_input(
                "Trafficway Type",
                help="Type of roadway (e.g., INTERSTATE, LOCAL STREET, ALLEY)",
                key="add_trafficway_type"
            )
            alignment = st.text_input(
                "Alignment",
                help="Roadway alignment (e.g., STRAIGHT AND LEVEL, CURVE ON GRADE)",
                key="add_alignment"
            )
            roadway_surface_cond = st.selectbox(
                "Roadway Surface Condition",
                ["UNKNOWN", "DRY", "WET", "SNOW/ICE", "SAND/MUD/DIRT/OIL"],
                index=0, key="add_surface_cond"
            )
        with cols1[2]:
            road_defect = st.selectbox(
                "Road Defect",
                ["NONE", "RUT, HOLES", "SHOULDER DEFECT", "DEBRIS ON ROADWAY", "OTHER"],
                index=0, key="add_road_defect"
            )
            intersection_related_i = st.selectbox(
                "Intersection Related?",
                ["NO", "YES"],
                index=0, key="add_intersection_related"
            )
            damage = st.text_input(
                "Damage Description",
                help="Brief description of property in damage.",
                key="add_damage"
            )
            prim_contributory_cause = st.text_input(
                "Primary Contributory Cause",
                help="Main factor contributing to the crash (e.g., UNSAFE SPEED, FAILED TO YIELD)",
                key="add_prim_cause"
            )
            most_severe_injury = st.selectbox(
                "Most Severe Injury",
                ["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"],
                index=0, key="add_most_severe_injury"
            )

        st.subheader("Detailed Injuries & Temporal Data")
        inj_cols = st.columns(3)
        with inj_cols[0]:
            injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0, value=0.0, step=0.1, key="add_injuries_fatal")
            injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0, value=0.0, step=0.1, key="add_injuries_incapacitating")
        with inj_cols[1]:
            injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0, value=0.0, step=0.1, key="add_injuries_non_incapacitating")
            injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0, value=0.0, step=0.1, key="add_injuries_reported_not_evident")
        with inj_cols[2]:
            injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0, value=0.0, step=0.1, key="add_injuries_no_indication")
        
        temp_cols = st.columns(3)
        with temp_cols[0]:
            crash_hour = st.slider("Crash Hour (0-23)", 0, 23, 12, key="add_crash_hour")
        with temp_cols[1]:
            crash_day_of_week = st.slider("Day of Week (1=Monday, 7=Sunday)", 1, 7, 1, key="add_crash_day_of_week")
        with temp_cols[2]:
            crash_month = st.slider("Month (1-12)", 1, 12, datetime.now().month, key="add_crash_month")
        
        submitted = st.form_submit_button("💾 Save Record", use_container_width=True)
        
        if submitted:
            # Basic frontend validation for required fields
            if crash_date is None: 
                st.error("🚨 Crash Date is a required field and cannot be empty.")
            elif not crash_type:
                st.error("🚨 Crash Type is a required field.")
            elif num_units is None or num_units < 0:
                st.error("🚨 Number of Units must be a non-negative number.")
            elif injuries_total is None or injuries_total < 0:
                st.error("🚨 Total Injuries must be a non-negative number.")
            else:
                try:
                    # Convert date object to string for DataObject, ensuring it's not None
                    crash_date_str = crash_date.strftime('%Y-%m-%d') if crash_date else ""
                    logger.debug(f"Crash date string from form for DataObject: '{crash_date_str}'")

                    # Construct a list of strings mimicking a CSV row based on FIELDS order
                    row_data = [""] * len(FIELDS)
                    row_data[0] = crash_date_str
                    row_data[1] = traffic_control_device
                    row_data[2] = weather_condition
                    row_data[3] = lighting_condition
                    row_data[4] = first_crash_type
                    row_data[5] = trafficway_type
                    row_data[6] = alignment
                    row_data[7] = roadway_surface_cond
                    row_data[8] = road_defect
                    row_data[9] = crash_type
                    row_data[10] = intersection_related_i
                    row_data[11] = damage
                    row_data[12] = prim_contributory_cause
                    row_data[13] = str(num_units)
                    row_data[14] = most_severe_injury
                    row_data[15] = str(injuries_total)
                    row_data[16] = str(injuries_fatal)
                    row_data[17] = str(injuries_incapacitating)
                    row_data[18] = str(injuries_non_incapacitating)
                    row_data[19] = str(injuries_reported_not_evident)
                    row_data[20] = str(injuries_no_indication)
                    row_data[21] = str(crash_hour)
                    row_data[22] = str(crash_day_of_week)
                    row_data[23] = str(crash_month)
                    
                    # Create DataObject and write to DB
                    new_record_obj = DataObject(row_data) # DataObject constructor performs validation
                    new_id = db.write_record(new_record_obj)
                    
                    st.success(f"🎉 Record saved successfully with ID: **{new_id}**")
                    st.balloons()
                    # Rerun to clear the form and update database info in sidebar
                    st.rerun() 
                except (DatabaseError, DataValidationError, ValueError) as e:
                    st.error(f"❌ Error saving record: {str(e)}")
                    logger.error(f"Failed to save new record: {traceback.format_exc()}")
                except Exception as e:
                    st.error(f"❌ An unexpected error occurred while saving: {str(e)}")
                    logger.error(f"Unexpected error saving new record: {traceback.format_exc()}")

def display_activity_log():
    """
    Reads recent updates from the log file and displays them in a Streamlit expander.
    """
    st.subheader("Activity Log")
    log_file_path = 'traffic_accidents.log'
    
    if not os.path.exists(log_file_path):
        st.info("No activity log found yet.")
        return

    with st.expander("Recent Updates", expanded=False):
        try:
            # Read the last N lines of the log file for efficiency
            # A more robust solution for very large logs would involve a dedicated log parser
            # or a separate small registry file.
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Filter and display relevant log entries in reverse order
            update_entries = []
            for line in reversed(lines):
                if "Record saved successfully with ID:" in line or "Successfully imported" in line or "Record ID" in line and "updated in place" in line or "Record ID" in line and "invalidated, new record appended" in line:
                    # Extract timestamp and message
                    try:
                        # Log format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                        # Example: '2023-10-27 10:30:00,123 - __main__ - INFO - Record saved successfully with ID: 1'
                        parts = line.split(' - ', 3) # Split into 4 parts
                        if len(parts) >= 4:
                            timestamp_str = parts[0]
                            message = parts[3].strip() # Get the actual log message
                            update_entries.append(f"**`{timestamp_str}`** `{message}`")
                            if len(update_entries) >= MAX_LOG_ENTRIES_DISPLAY:
                                break
                    except Exception as e:
                        logger.warning(f"Failed to parse log line for registry: {line.strip()} - {e}")
                        continue
            
            if update_entries:
                for entry in update_entries:
                    st.markdown(entry)
            else:
                st.info("No recent record updates or imports found in the log.")
        except Exception as e:
            st.error(f"Could not read activity log: {str(e)}")
            logger.error(f"Error reading activity log: {traceback.format_exc()}")

# --- Main Application Entry Point ---
if __name__ == "__main__":
    # Ensure the DB directory is created before any DB operations
    # This is done within TrafficAccidentsDB.__init__ but can be called standalone
    # to catch early errors if __init__ fails before setup_ui handles it.
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
    except OSError as e:
        st.error(f"Critical: Cannot create database directories. Please check permissions for {DB_DIR}. Error: {e}")
        logger.critical(f"Initial directory creation failed: {traceback.format_exc()}")
        st.stop() # Stop the app if directories cannot be created

    setup_ui() # Start the Streamlit UI
