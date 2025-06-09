# based on file stCRUDDataObjectPY_v3alpha.py

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

# Custom Exceptions
class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass

class ValidationError(DatabaseError):
    """Custom exception for data validation errors."""
    pass

class LockError(DatabaseError):
    """Custom exception for file locking errors."""
    pass

class DataObject:
    """
    Represents a single traffic accident record.
    Uses properties for controlled access and validation.
    """
    REQUIRED_FIELDS = [
        "crash_date", "crash_type", "num_units", "injuries_total",
        "fatalities_total", "crash_severity", "most_severe_injury",
        "timestamp" # Internal field, but required for data integrity
    ]

    NUMERIC_FIELDS = [
        "num_units", "injuries_total", "injuries_fatal", "injuries_incapacitating",
        "injuries_non_incapacitating", "injuries_reported_not_evident",
        "injuries_no_indication", "fatalities_total", "num_occupants_unit_1",
        "num_occupants_unit_2", "num_occupants_unit_3", "num_occupants_unit_4"
    ]
    
    # Define a comprehensive list of all fields that the DataObject should manage
    # This helps in strict validation and ensures consistency
    ALL_FIELDS = [
        "id", "crash_date", "crash_type", "num_units", "injuries_total",
        "fatalities_total", "crash_severity", "most_severe_injury",
        "pre_crash_action_unit_1", "pre_crash_action_unit_2",
        "pre_crash_action_unit_3", "pre_crash_action_unit_4",
        "injuries_fatal", "injuries_incapacitating",
        "injuries_non_incapacitating", "injuries_reported_not_evident",
        "injuries_no_indication",
        "num_occupants_unit_1", "num_occupants_unit_2",
        "num_occupants_unit_3", "num_occupants_unit_4",
        "timestamp" # Internal timestamp for last modification/creation
    ]

    def __init__(self, id: Optional[str] = None, existing_data_dict: Optional[Dict[str, Any]] = None):
        self._data = {} # Internal dictionary to store data
        self.id = id if id else self._generate_id()
        self.timestamp = datetime.now().isoformat() # ISO 8601 string

        if existing_data_dict:
            self._initialize_from_dict(existing_data_dict)
        else:
            self._initialize_defaults()
        
        self.validate() # Validate data on initialization


    def _initialize_defaults(self):
        """Initializes all fields with default values."""
        for field in self.ALL_FIELDS:
            if field == "id":
                continue # ID is set separately in __init__
            elif field == "timestamp":
                self.timestamp = datetime.now().isoformat()
            elif field == "crash_date":
                self.crash_date = date.today().isoformat()
            elif field in self.NUMERIC_FIELDS:
                setattr(self, field, 0.0 if "injuries" in field else 0) # Default to 0.0 for injuries, 0 for others
            else:
                setattr(self, field, "N/A") # Default string value

    def _initialize_from_dict(self, data_dict: Dict[str, Any]):
        """Initializes fields from a dictionary, applying validation."""
        if 'id' in data_dict: # Ensure ID from dict is used if provided
            self.id = data_dict['id']

        for field in self.ALL_FIELDS:
            if field == 'id':
                continue # ID is handled separately
            if field in data_dict:
                value = data_dict[field]
                if field == "crash_date":
                    setattr(self, field, self._validate_date_format(str(value), field))
                elif field == "timestamp":
                    # Ensure timestamp is always a valid ISO format, regenerate if invalid
                    try:
                        datetime.fromisoformat(value)
                        setattr(self, field, value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid timestamp format for field '{field}': '{value}'. Regenerating.")
                        setattr(self, field, datetime.now().isoformat())
                elif field.startswith('injuries_') and field != 'injuries_no_indication': # All injury counts are floats
                    setattr(self, field, self._validate_positive_float(str(value), field))
                elif field == 'num_units' or field == 'fatalities_total' or field.startswith('num_occupants_'): # These are ints
                    setattr(self, field, self._validate_positive_int(str(value), field))
                else:
                    setattr(self, field, value) # Assign directly for other fields
            else:
                # If a field is missing from the dict, initialize it to its default
                if field == "crash_date":
                    setattr(self, field, date.today().isoformat())
                elif field == "timestamp":
                    setattr(self, field, datetime.now().isoformat())
                elif field in self.NUMERIC_FIELDS:
                    setattr(self, field, 0.0 if "injuries" in field else 0)
                else:
                    setattr(self, field, "N/A")

    def _generate_id(self) -> str:
        """Generates a unique ID for the record."""
        # Using timestamp + hash of random data for more uniqueness
        unique_string = f"{datetime.now().isoformat()}-{os.urandom(16).hex()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()

    def validate(self):
        """Validates the data object's required fields."""
        for field in self.REQUIRED_FIELDS:
            if not getattr(self, field, None):
                raise ValidationError(f"Required field '{field}' is missing or empty.")
        
        # Specific validation for numeric fields
        for field in self.NUMERIC_FIELDS:
            value = getattr(self, field)
            if not isinstance(value, (int, float)):
                # This should ideally be caught by _initialize_from_dict
                logger.error(f"Validation error: Field '{field}' has non-numeric value '{value}' ({type(value).__name__}).")
                # Attempt to fix or raise, depending on desired strictness
                if isinstance(value, str):
                    if "injuries" in field:
                        setattr(self, field, self._validate_positive_float(value, field))
                    else:
                        setattr(self, field, self._validate_positive_int(value, field))
                else:
                    raise ValidationError(f"Field '{field}' must be numeric, got {type(value).__name__}.")

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
    def _validate_positive_int(value: Optional[str], field_name: str, min_val: int = 0) -> int:
        """Validates and converts a value to a non-negative integer."""
        try:
            if value is None or value == '':
                return min_val
            
            num = int(float(value)) # Convert to float first to handle "5.0"
            if num < min_val:
                logger.warning(f"Integer value for {field_name} ({num}) is less than minimum {min_val}. Setting to {min_val}.")
                return min_val
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    @staticmethod
    def _validate_date_format(date_str: Optional[str], field_name: str) -> str:
        """Validates if a string is in 'YYYY-MM-DD' format and returns it, else today's date."""
        if not date_str:
            return date.today().isoformat()
        try:
            datetime.strptime(date_str, '%Y-%m-%d').date() # Only validate date part
            return date_str
        except ValueError:
            logger.warning(f"Invalid date format '{date_str}' for {field_name}. Expected YYYY-MM-DD. Setting to today's date.")
            return date.today().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Converts the DataObject instance to a dictionary."""
        # Directly access attributes and exclude internal _data dict
        data = {field: getattr(self, field, None) for field in self.ALL_FIELDS if hasattr(self, field)}
        return data

    def to_bytes(self) -> bytes:
        """Serializes the DataObject to bytes (JSON)."""
        data = self.to_dict()
        try:
            return json.dumps(data).encode('utf-8')
        except TypeError as e:
            logger.error(f"TypeError during DataObject to_bytes serialization: {e}")
            raise DatabaseError(f"Failed to serialize DataObject: {e}")

    @classmethod
    def from_bytes(cls, data_bytes: bytes):
        """Deserializes bytes (JSON) back to a DataObject instance."""
        try:
            data_dict = json.loads(data_bytes.decode('utf-8'))
            return cls(existing_data_dict=data_dict)
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError during DataObject from_bytes deserialization: {e}")
            raise DatabaseError(f"Failed to deserialize record: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during DataObject from_bytes: {e}")
            raise DatabaseError(f"Failed to create DataObject from bytes: {e}")

    @staticmethod
    def get_header_fields() -> List[str]:
        """Returns the list of all fields in the order they should appear for CSV."""
        return DataObject.ALL_FIELDS

    def to_csv_row(self) -> List[Any]:
        """Returns a list of values representing the record for CSV export."""
        row = []
        for field in self.ALL_FIELDS:
            value = getattr(self, field, "") # Get attribute, default to empty string if not found
            # Ensure numeric fields are correctly represented for CSV if they are not already
            if field in self.NUMERIC_FIELDS:
                if isinstance(value, (int, float)):
                    row.append(value)
                elif isinstance(value, str):
                    try: # Try to convert if it's a string that should be numeric
                        if "injuries" in field:
                            row.append(float(value))
                        else:
                            row.append(int(value))
                    except ValueError:
                        row.append(value) # Keep as string if conversion fails, or consider a default
                else:
                    row.append(value)
            else:
                row.append(value)
        return row

    # Properties for controlled access (optional, but good practice)
    # They directly map to self._data keys
    def __getattr__(self, name):
        if name in self.ALL_FIELDS:
            return self._data.get(name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name == "_data" or name not in self.ALL_FIELDS:
            super().__setattr__(name, value)
        else:
            self._data[name] = value

class TrafficAccidentsDB:
    """Manages the storage and retrieval of Traffic Accident DataObjects."""

    def __init__(self, db_file: str, lock_file: str):
        self.db_file = db_file
        self.lock_file = lock_file
        self.lock = filelock.FileLock(self.lock_file, timeout=10) # 10 seconds timeout for lock acquisition
        # Ensure DB directory exists
        try:
            os.makedirs(os.path.dirname(db_file), exist_ok=True)
        except OSError as e:
            logger.critical(f"Failed to create database directory {os.path.dirname(db_file)}: {e}")
            raise DatabaseError(f"Failed to create database directory: {e}")

    def _acquire_lock(self):
        """Acquires the file lock."""
        try:
            self.lock.acquire()
            logger.debug(f"Lock acquired for {self.db_file}")
        except filelock.Timeout:
            logger.error(f"Could not acquire lock on {self.db_file}. Another process might be holding it.")
            raise LockError("Database is currently locked by another operation. Please try again.")
        except Exception as e:
            logger.error(f"Unexpected error acquiring lock: {e}")
            raise LockError(f"Failed to acquire database lock: {e}")

    def _release_lock(self):
        """Releases the file lock."""
        try:
            self.lock.release()
            logger.debug(f"Lock released for {self.db_file}")
        except Exception as e:
            logger.error(f"Unexpected error releasing lock: {e}")
            # Do not re-raise, as this often happens during cleanup and might hide original error

    def _read_all_records_from_file(self) -> Dict[str, Dict[str, Any]]:
        """Reads all records from the database file."""
        records = {}
        if not os.path.exists(self.db_file) or os.path.getsize(self.db_file) == 0:
            return records

        try:
            with open(self.db_file, 'rb') as f:
                # Read 4-byte length prefix
                while True:
                    len_bytes = f.read(4)
                    if not len_bytes:
                        break # EOF
                    
                    if len(len_bytes) < 4:
                        logger.warning(f"Incomplete length prefix read at end of file. Bytes read: {len(len_bytes)}")
                        break # Incomplete read

                    try:
                        record_len = struct.unpack('!I', len_bytes)[0]
                    except struct.error:
                        logger.error(f"Corrupt length prefix in DB file: {len_bytes.hex()}")
                        raise DatabaseError("Database file is corrupt (invalid length prefix).")

                    record_data_bytes = f.read(record_len)
                    if len(record_data_bytes) < record_len:
                        logger.error(f"Incomplete record data read. Expected {record_len} bytes, got {len(record_data_bytes)}.")
                        raise DatabaseError("Database file is corrupt (incomplete record data).")
                    
                    try:
                        data_dict = json.loads(record_data_bytes.decode('utf-8'))
                        if 'id' in data_dict:
                            records[data_dict['id']] = {'data_bytes': record_data_bytes, 'offset': f.tell() - record_len - 4}
                        else:
                            logger.warning(f"Record found without 'id' key. Skipping. Data: {data_dict}")
                    except json.JSONDecodeError:
                        logger.error(f"Corrupt JSON data in DB file at offset {f.tell() - record_len}. Skipping record.")
                    except Exception as e:
                        logger.error(f"Unexpected error processing record from DB file: {e}. Data: {record_data_bytes.decode('utf-8', errors='ignore')}")

        except FileNotFoundError:
            logger.info(f"Database file not found: {self.db_file}. A new one will be created.")
        except IOError as e:
            logger.error(f"IOError reading database file {self.db_file}: {e}")
            raise DatabaseError(f"Error reading database file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in _read_all_records_from_file: {e}")
            raise DatabaseError(f"An unexpected error occurred while reading database: {e}")

        return records

    def _write_all_records_to_file(self, records: Dict[str, Dict[str, Any]]):
        """Writes all records to the database file."""
        temp_db_file = self.db_file + ".tmp"
        try:
            with open(temp_db_file, 'wb') as f:
                for record_id in sorted(records.keys()): # Ensure consistent order
                    record_info = records[record_id]
                    data_bytes = record_info['data_bytes']
                    
                    # Write 4-byte length prefix
                    f.write(struct.pack('!I', len(data_bytes)))
                    # Write record data
                    f.write(data_bytes)
            
            # Replace old file with new one
            os.replace(temp_db_file, self.db_file)
            logger.debug(f"Successfully wrote records to {self.db_file}")

        except IOError as e:
            logger.error(f"IOError writing to database file {temp_db_file}: {e}")
            raise DatabaseError(f"Error writing to database file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in _write_all_records_to_file: {e}")
            raise DatabaseError(f"An unexpected error occurred while writing database: {e}")
        finally:
            if os.path.exists(temp_db_file):
                try:
                    os.remove(temp_db_file) # Clean up temp file if error occurred
                except OSError as e:
                    logger.warning(f"Failed to remove temporary database file {temp_db_file}: {e}")

    def insert_record(self, record: DataObject):
        """Inserts a new DataObject into the database."""
        try:
            self._acquire_lock()
            records = self._read_all_records_from_file()
            if record.id in records:
                raise DatabaseError(f"Record with ID {record.id} already exists.")
            
            record.timestamp = datetime.now().isoformat() # Set creation timestamp
            record_bytes = record.to_bytes()
            records[record.id] = {'data_bytes': record_bytes, 'offset': -1} # Offset will be set on next read
            self._write_all_records_to_file(records)
            logger.info(f"Record {record.id} inserted successfully.")
        except DatabaseError as e:
            logger.error(f"Failed to insert record {record.id}: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during insert_record: {e}")
            raise DatabaseError(f"An unexpected error occurred during insert: {e}")
        finally:
            self._release_lock()

    def update_record(self, record: DataObject):
        """Updates an existing DataObject in the database."""
        try:
            self._acquire_lock()
            records = self._read_all_records_from_file()
            if record.id not in records:
                raise DatabaseError(f"Record with ID {record.id} not found for update.")
            
            record.timestamp = datetime.now().isoformat() # Update modification timestamp
            record_bytes = record.to_bytes()
            records[record.id] = {'data_bytes': record_bytes, 'offset': -1}
            self._write_all_records_to_file(records)
            logger.info(f"Record {record.id} updated successfully.")
        except DatabaseError as e:
            logger.error(f"Failed to update record {record.id}: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during update_record: {e}")
            raise DatabaseError(f"An unexpected error occurred during update: {e}")
        finally:
            self._release_lock()

    def delete_record(self, record_id: str):
        """Deletes a DataObject from the database by its ID."""
        try:
            self._acquire_lock()
            records = self._read_all_records_from_file()
            if record_id not in records:
                raise DatabaseError(f"Record with ID {record_id} not found for deletion.")
            
            del records[record_id]
            self._write_all_records_to_file(records)
            logger.info(f"Record {record_id} deleted successfully.")
        except DatabaseError as e:
            logger.error(f"Failed to delete record {record_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during delete_record: {e}")
            raise DatabaseError(f"An unexpected error occurred during delete: {e}")
        finally:
            self._release_lock()

    def read_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Reads a single record by its ID, returning its raw data."""
        try:
            self._acquire_lock()
            records = self._read_all_records_from_file()
            return records.get(record_id)
        except DatabaseError as e:
            logger.error(f"Failed to read record by ID {record_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during read_record_by_id: {e}")
            raise DatabaseError(f"An unexpected error occurred during read by ID: {e}")
        finally:
            self._release_lock()

    def read_records_paginated(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        """Reads records with pagination."""
        try:
            self._acquire_lock()
            records = self._read_all_records_from_file()
            sorted_ids = sorted(records.keys())
            paginated_ids = sorted_ids[offset : offset + limit]
            return [records[record_id] for record_id in paginated_ids]
        except DatabaseError as e:
            logger.error(f"Failed to read paginated records: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during read_records_paginated: {e}")
            raise DatabaseError(f"An unexpected error occurred during pagination: {e}")
        finally:
            self._release_lock()

    def get_total_records(self) -> int:
        """Returns the total number of records in the database."""
        try:
            self._acquire_lock()
            records = self._read_all_records_from_file()
            return len(records)
        except DatabaseError as e:
            logger.error(f"Failed to get total records: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during get_total_records: {e}")
            raise DatabaseError(f"An unexpected error occurred while counting records: {e}")
        finally:
            self._release_lock()

    def search_records(self, query: str) -> List[Dict[str, Any]]:
        """Searches records by ID or any string field."""
        results = []
        if not query:
            return results

        query_lower = query.lower()
        try:
            self._acquire_lock()
            records = self._read_all_records_from_file()
            for record_id, record_info in records.items():
                try:
                    record_obj = DataObject.from_bytes(record_info['data_bytes'])
                    # Search in ID
                    if query_lower in record_id.lower():
                        results.append(record_info)
                        continue # Move to next record once found
                    
                    # Search in string fields
                    record_dict = record_obj.to_dict()
                    for field, value in record_dict.items():
                        # Only search in string values that are not numeric fields
                        if isinstance(value, str) and field not in DataObject.NUMERIC_FIELDS:
                            if query_lower in value.lower():
                                results.append(record_info)
                                break # Found in this record, move to next
                except DatabaseError as e:
                    logger.warning(f"Skipping corrupt record {record_id} during search: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error processing record {record_id} during search: {e}")
        except DatabaseError as e:
            logger.error(f"Failed to search records: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during search_records: {e}")
            raise DatabaseError(f"An unexpected error occurred during search: {e}")
        finally:
            self._release_lock()
        return results

    def backup_database(self):
        """Creates a timestamped backup of the database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"traffic_accidents_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            if os.path.exists(self.db_file):
                with open(self.db_file, 'rb') as src, open(backup_path, 'wb') as dest:
                    while chunk := src.read(CHUNK_SIZE):
                        dest.write(chunk)
                logger.info(f"Database backed up to {backup_path}")
            else:
                logger.info("No database file to backup.")
            
            # Clean up old backups
            self._clean_old_backups()
        except IOError as e:
            logger.error(f"IOError during database backup to {backup_path}: {e}")
            raise DatabaseError(f"Failed to create backup: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during backup_database: {e}")
            raise DatabaseError(f"An unexpected error occurred during backup: {e}")

    def _clean_old_backups(self):
        """Removes older backup files, keeping only MAX_BACKUPS."""
        try:
            backups = sorted([os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.startswith("traffic_accidents_backup_") and f.endswith(".db")], key=os.path.getmtime)
            for i in range(len(backups) - MAX_BACKUPS):
                os.remove(backups[i])
                logger.info(f"Removed old backup: {backups[i]}")
        except OSError as e:
            logger.error(f"Error cleaning old backups in {BACKUP_DIR}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during _clean_old_backups: {e}")

    def restore_database(self, backup_file_path: str):
        """Restores the database from a selected backup file."""
        try:
            if not os.path.exists(backup_file_path):
                raise FileNotFoundError(f"Backup file not found: {backup_file_path}")
            
            self._acquire_lock() # Lock the database before restoration
            
            # Create a temporary file for the current database before overwriting
            temp_current_db = self.db_file + ".pre_restore_bak"
            if os.path.exists(self.db_file):
                with open(self.db_file, 'rb') as src, open(temp_current_db, 'wb') as dest:
                    while chunk := src.read(CHUNK_SIZE):
                        dest.write(chunk)

            # Copy backup to main DB file
            with open(backup_file_path, 'rb') as src, open(self.db_file, 'wb') as dest:
                while chunk := src.read(CHUNK_SIZE):
                    dest.write(chunk)
            
            logger.info(f"Database restored from {backup_file_path}")
            # Clean up temp_current_db if restore was successful
            if os.path.exists(temp_current_db):
                os.remove(temp_current_db)

        except FileNotFoundError as e:
            logger.error(f"Restore failed: {e}")
            raise DatabaseError(f"Restore failed: {e}")
        except IOError as e:
            logger.error(f"IOError during database restore from {backup_file_path}: {e}")
            # Attempt to restore the temp_current_db if an error occurred during copy
            if os.path.exists(temp_current_db):
                try:
                    os.replace(temp_current_db, self.db_file)
                    logger.info("Attempted to revert to pre-restore database due to error.")
                except OSError as revert_e:
                    logger.error(f"Failed to revert database after failed restore: {revert_e}")
            raise DatabaseError(f"Failed to restore database: {e}")
        except LockError as e:
            logger.error(f"Restore failed due to lock acquisition issue: {e}")
            raise DatabaseError(f"Restore failed: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during restore_database: {e}")
            raise DatabaseError(f"An unexpected error occurred during restore: {e}")
        finally:
            self._release_lock()
            if os.path.exists(temp_current_db):
                try:
                    os.remove(temp_current_db) # Ensure temp file is removed
                except OSError as e:
                    logger.warning(f"Failed to remove temporary pre-restore database file {temp_current_db}: {e}")


# --- Streamlit UI Functions ---

def display_record_details(data_obj: Dict[str, Any]):
    """
    Helper function to display a single record's details in a structured format.
    Ensures numeric values are properly cast before formatting to prevent ValueError.
    """
    st.subheader(f"Record Details (ID: {data_obj.get('id', 'N/A')})")

    cols_main = st.columns(3)
    with cols_main[0]:
        st.markdown(f"**Crash Date:** `{data_obj.get('crash_date', 'N/A')}`")
    with cols_main[1]:
        st.markdown(f"**Crash Type:** `{data_obj.get('crash_type', 'N/A')}`")
    with cols_main[2]:
        # Ensure num_units is an integer before formatting
        num_units_val = data_obj.get('num_units', 0)
        try:
            st.markdown(f"**Number of Units Involved:** `{int(num_units_val)}`")
        except (ValueError, TypeError):
            st.markdown(f"**Number of Units Involved:** `Invalid Value`")
            logger.warning(f"Failed to cast 'num_units' ({num_units_val}) to int for display.")

    cols_inj_sev = st.columns(2)
    with cols_inj_sev[0]:
        # Ensure injuries_total is a float before formatting
        injuries_total_val = data_obj.get('injuries_total', 0.0)
        try:
            st.markdown(f"**Total de Lesões:** `{float(injuries_total_val):.2f}`")
        except (ValueError, TypeError):
            st.markdown(f"**Total de Lesões:** `Invalid Value`")
            logger.warning(f"Failed to cast 'injuries_total' ({injuries_total_val}) to float for display.")
            
    with cols_inj_sev[1]:
        st.markdown(f"**Crash Severity:** `{data_obj.get('crash_severity', 'N/A')}`")
        st.markdown(f"**Most Severe Injury:** `{data_obj.get('most_severe_injury', 'N/A')}`")

    st.subheader("Pre-Crash Actions & Occupants")
    cols_pre_crash = st.columns(2)
    with cols_pre_crash[0]:
        st.markdown(f"**Pre-Crash Action (Unit 1):** `{data_obj.get('pre_crash_action_unit_1', 'N/A')}`")
        st.markdown(f"**Pre-Crash Action (Unit 2):** `{data_obj.get('pre_crash_action_unit_2', 'N/A')}`")
    with cols_pre_crash[1]:
        st.markdown(f"**Pre-Crash Action (Unit 3):** `{data_obj.get('pre_crash_action_unit_3', 'N/A')}`")
        st.markdown(f"**Pre-Crash Action (Unit 4):** `{data_obj.get('pre_crash_action_unit_4', 'N/A')}`")

    cols_occupants = st.columns(2)
    with cols_occupants[0]:
        # Ensure fatalities_total is an integer before formatting
        fatalities_total_val = data_obj.get('fatalities_total', 0)
        try:
            st.markdown(f"**Total Fatalities:** `{int(fatalities_total_val)}`")
        except (ValueError, TypeError):
            st.markdown(f"**Total Fatalities:** `Invalid Value`")
            logger.warning(f"Failed to cast 'fatalities_total' ({fatalities_total_val}) to int for display.")

    with cols_occupants[1]:
        # Ensure num_occupants_unit_1 is an integer before formatting
        num_occupants_unit_1_val = data_obj.get('num_occupants_unit_1', 0)
        try:
            st.markdown(f"**Number of Occupants (Unit 1):** `{int(num_occupants_unit_1_val)}`")
        except (ValueError, TypeError):
            st.markdown(f"**Number of Occupants (Unit 1):** `Invalid Value`")
            logger.warning(f"Failed to cast 'num_occupants_unit_1' ({num_occupants_unit_1_val}) to int for display.")
        
        # Ensure num_occupants_unit_2 is an integer before formatting
        num_occupants_unit_2_val = data_obj.get('num_occupants_unit_2', 0)
        try:
            st.markdown(f"**Number of Occupants (Unit 2):** `{int(num_occupants_unit_2_val)}`")
        except (ValueError, TypeError):
            st.markdown(f"**Number of Occupants (Unit 2):** `Invalid Value`")
            logger.warning(f"Failed to cast 'num_occupants_unit_2' ({num_occupants_unit_2_val}) to int for display.")

        # Ensure num_occupants_unit_3 is an integer before formatting
        num_occupants_unit_3_val = data_obj.get('num_occupants_unit_3', 0)
        try:
            st.markdown(f"**Number of Occupants (Unit 3):** `{int(num_occupants_unit_3_val)}`")
        except (ValueError, TypeError):
            st.markdown(f"**Number of Occupants (Unit 3):** `Invalid Value`")
            logger.warning(f"Failed to cast 'num_occupants_unit_3' ({num_occupants_unit_3_val}) to int for display.")

        # Ensure num_occupants_unit_4 is an integer before formatting
        num_occupants_unit_4_val = data_obj.get('num_occupants_unit_4', 0)
        try:
            st.markdown(f"**Number of Occupants (Unit 4):** `{int(num_occupants_unit_4_val)}`")
        except (ValueError, TypeError):
            st.markdown(f"**Number of Occupants (Unit 4):** `Invalid Value`")
            logger.warning(f"Failed to cast 'num_occupants_unit_4' ({num_occupants_unit_4_val}) to int for display.")

    st.subheader("Detailed Injuries")
    cols_detailed_inj = st.columns(2)
    with cols_detailed_inj[0]:
        # Ensure injuries_fatal is a float before formatting
        injuries_fatal_val = data_obj.get('injuries_fatal', 0.0)
        try:
            st.markdown(f"**Fatal Injuries:** `{float(injuries_fatal_val):.2f}`")
        except (ValueError, TypeError):
            st.markdown(f"**Fatal Injuries:** `Invalid Value`")
            logger.warning(f"Failed to cast 'injuries_fatal' ({injuries_fatal_val}) to float for display.")

        # Ensure injuries_incapacitating is a float before formatting
        injuries_incapacitating_val = data_obj.get('injuries_incapacitating', 0.0)
        try:
            st.markdown(f"**Incapacitating Injuries:** `{float(injuries_incapacitating_val):.2f}`")
        except (ValueError, TypeError):
            st.markdown(f"**Incapacitating Injuries:** `Invalid Value`")
            logger.warning(f"Failed to cast 'injuries_incapacitating' ({injuries_incapacitating_val}) to float for display.")
        
    with cols_detailed_inj[1]:
        # Ensure injuries_non_incapacitating is a float before formatting
        injuries_non_incapacitating_val = data_obj.get('injuries_non_incapacitating', 0.0)
        try:
            st.markdown(f"**Non-Incapacitating Injuries:** `{float(injuries_non_incapacitating_val):.2f}`")
        except (ValueError, TypeError):
            st.markdown(f"**Non-Incapacitating Injuries:** `Invalid Value`")
            logger.warning(f"Failed to cast 'injuries_non_incapacitating' ({injuries_non_incapacitating_val}) to float for display.")

        # Ensure injuries_reported_not_evident is a float before formatting
        injuries_reported_not_evident_val = data_obj.get('injuries_reported_not_evident', 0.0)
        try:
            st.markdown(f"**Injuries Reported Not Evident:** `{float(injuries_reported_not_evident_val):.2f}`")
        except (ValueError, TypeError):
            st.markdown(f"**Injuries Reported Not Evident:** `Invalid Value`")
            logger.warning(f"Failed to cast 'injuries_reported_not_evident' ({injuries_reported_not_evident_val}) to float for display.")

        # Ensure injuries_no_indication is a float before formatting
        injuries_no_indication_val = data_obj.get('injuries_no_indication', 0.0)
        try:
            st.markdown(f"**Injuries No Indication:** `{float(injuries_no_indication_val):.2f}`")
        except (ValueError, TypeError):
            st.markdown(f"**Injuries No Indication:** `Invalid Value`")
            logger.warning(f"Failed to cast 'injuries_no_indication' ({injuries_no_indication_val}) to float for display.")


    st.markdown(f"---")
    st.markdown(f"**Last Modified/Created:** `{data_obj.get('timestamp', 'N/A')}`")


def add_record_section(db: TrafficAccidentsDB):
    st.header("Adicionar Novo Registro de Acidente")

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

    st.subheader("Severity & Most Severe Injury (*)")
    cols_severity = st.columns(2)
    with cols_severity[0]:
        crash_severity = st.selectbox(
            "Crash Severity*",
            ["N/A", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "POSSIBLE", "NO INDICATION"],
            index=0, key="add_crash_severity"
        )
    with cols_severity[1]:
        most_severe_injury = st.selectbox(
            "Most Severe Injury*",
            ["N/A", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"],
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
        fatalities_total = st.number_input("Total Fatalities", min_value=0, value=0, step=1, key="add_fatalities_total")

    st.subheader("Pre-Crash Actions per Unit")
    pre_crash_cols = st.columns(2)
    with pre_crash_cols[0]:
        pre_crash_action_unit_1 = st.text_input("Pre-Crash Action (Unit 1)", value="N/A", key="add_pre_crash_action_unit_1")
        pre_crash_action_unit_2 = st.text_input("Pre-Crash Action (Unit 2)", value="N/A", key="add_pre_crash_action_unit_2")
    with pre_crash_cols[1]:
        pre_crash_action_unit_3 = st.text_input("Pre-Crash Action (Unit 3)", value="N/A", key="add_pre_crash_action_unit_3")
        pre_crash_action_unit_4 = st.text_input("Pre-Crash Action (Unit 4)", value="N/A", key="add_pre_crash_action_unit_4")

    st.subheader("Number of Occupants per Unit")
    occupants_cols = st.columns(2)
    with occupants_cols[0]:
        num_occupants_unit_1 = st.number_input("Number of Occupants (Unit 1)", min_value=0, value=0, step=1, key="add_num_occupants_unit_1")
        num_occupants_unit_2 = st.number_input("Number of Occupants (Unit 2)", min_value=0, value=0, step=1, key="add_num_occupants_unit_2")
    with occupants_cols[1]:
        num_occupants_unit_3 = st.number_input("Number of Occupants (Unit 3)", min_value=0, value=0, step=1, key="add_num_occupants_unit_3")
        num_occupants_unit_4 = st.number_input("Number of Occupants (Unit 4)", min_value=0, value=0, step=1, key="add_num_occupants_unit_4")

    if st.button("Adicionar Registro"):
        new_record_data = {
            "crash_date": crash_date.isoformat(),
            "crash_type": crash_type,
            "num_units": num_units,
            "injuries_total": injuries_total,
            "crash_severity": crash_severity,
            "most_severe_injury": most_severe_injury,
            "pre_crash_action_unit_1": pre_crash_action_unit_1,
            "pre_crash_action_unit_2": pre_crash_action_unit_2,
            "pre_crash_action_unit_3": pre_crash_action_unit_3,
            "pre_crash_action_unit_4": pre_crash_action_unit_4,
            "injuries_fatal": injuries_fatal,
            "injuries_incapacitating": injuries_incapacitating,
            "injuries_non_incapacitating": injuries_non_incapacitating,
            "injuries_reported_not_evident": injuries_reported_not_evident,
            "injuries_no_indication": injuries_no_indication,
            "fatalities_total": fatalities_total,
            "num_occupants_unit_1": num_occupants_unit_1,
            "num_occupants_unit_2": num_occupants_unit_2,
            "num_occupants_unit_3": num_occupants_unit_3,
            "num_occupants_unit_4": num_occupants_unit_4,
        }
        try:
            new_record = DataObject(existing_data_dict=new_record_data)
            db.insert_record(new_record)
            st.success(f"Record '{new_record.id}' added successfully!")
            st.session_state.current_page = "View Records" # Redirect after adding
            st.rerun() # Rerun to refresh view
        except ValidationError as e:
            st.error(f"Validation Error: {e}")
            logger.error(f"Validation error when adding record: {traceback.format_exc()}")
        except DatabaseError as e:
            st.error(f"Database Error: {e}")
            logger.error(f"Database error when adding record: {traceback.format_exc()}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            logger.error(f"Unexpected error when adding record: {traceback.format_exc()}")

def edit_record_section(db: TrafficAccidentsDB):
    st.header("Editar Registro Existente")
    record_id_to_edit = st.text_input("Enter Record ID to Edit:", key="edit_record_id_input")

    if record_id_to_edit:
        try:
            raw_record_data = db.read_record_by_id(record_id_to_edit)
            if raw_record_data:
                record_obj = DataObject.from_bytes(raw_record_data['data_bytes'])
                
                st.markdown("---")
                st.subheader(f"Editing Record: {record_obj.id}")

                # Populate fields with current record data
                cols_req = st.columns(2)
                with cols_req[0]:
                    edited_crash_date = st.date_input(
                        "Crash Date*",
                        value=datetime.strptime(record_obj.crash_date, '%Y-%m-%d').date(),
                        key="edit_crash_date"
                    )
                with cols_req[1]:
                    edited_crash_type = st.text_input("Crash Type*", value=record_obj.crash_type, key="edit_crash_type")

                cols_units_inj = st.columns(2)
                with cols_units_inj[0]:
                    edited_num_units = st.number_input(
                        "Number of Units Involved*",
                        min_value=0, max_value=999, value=record_obj.num_units, step=1,
                        key="edit_num_units"
                    )
                with cols_units_inj[1]:
                    edited_injuries_total = st.number_input(
                        "Total Injuries*",
                        min_value=0.0, value=record_obj.injuries_total, step=0.1,
                        key="edit_injuries_total"
                    )

                cols_severity = st.columns(2)
                with cols_severity[0]:
                    crash_severity_options = ["N/A", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "POSSIBLE", "NO INDICATION"]
                    edited_crash_severity = st.selectbox(
                        "Crash Severity*",
                        crash_severity_options,
                        index=crash_severity_options.index(record_obj.crash_severity) if record_obj.crash_severity in crash_severity_options else 0,
                        key="edit_crash_severity"
                    )
                with cols_severity[1]:
                    most_severe_injury_options = ["N/A", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"]
                    edited_most_severe_injury = st.selectbox(
                        "Most Severe Injury*",
                        most_severe_injury_options,
                        index=most_severe_injury_options.index(record_obj.most_severe_injury) if record_obj.most_severe_injury in most_severe_injury_options else 0,
                        key="edit_most_severe_injury"
                    )

                st.subheader("Detailed Injuries & Temporal Data")
                inj_cols = st.columns(3)
                with inj_cols[0]:
                    edited_injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0, value=record_obj.injuries_fatal, step=0.1, key="edit_injuries_fatal")
                    edited_injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0, value=record_obj.injuries_incapacitating, step=0.1, key="edit_injuries_incapacitating")
                with inj_cols[1]:
                    edited_injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0, value=record_obj.injuries_non_incapacitating, step=0.1, key="edit_injuries_non_incapacitating")
                    edited_injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0, value=record_obj.injuries_reported_not_evident, step=0.1, key="edit_injuries_reported_not_evident")
                with inj_cols[2]:
                    edited_injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0, value=record_obj.injuries_no_indication, step=0.1, key="edit_injuries_no_indication")
                
                temp_cols = st.columns(3)
                with temp_cols[0]:
                    edited_fatalities_total = st.number_input("Total Fatalities", min_value=0, value=record_obj.fatalities_total, step=1, key="edit_fatalities_total")

                st.subheader("Pre-Crash Actions per Unit")
                pre_crash_cols = st.columns(2)
                with pre_crash_cols[0]:
                    edited_pre_crash_action_unit_1 = st.text_input("Pre-Crash Action (Unit 1)", value=record_obj.pre_crash_action_unit_1, key="edit_pre_crash_action_unit_1")
                    edited_pre_crash_action_unit_2 = st.text_input("Pre-Crash Action (Unit 2)", value=record_obj.pre_crash_action_unit_2, key="edit_pre_crash_action_unit_2")
                with pre_crash_cols[1]:
                    edited_pre_crash_action_unit_3 = st.text_input("Pre-Crash Action (Unit 3)", value=record_obj.pre_crash_action_unit_3, key="edit_pre_crash_action_unit_3")
                    edited_pre_crash_action_unit_4 = st.text_input("Pre-Crash Action (Unit 4)", value=record_obj.pre_crash_action_unit_4, key="edit_pre_crash_action_unit_4")

                st.subheader("Number of Occupants per Unit")
                occupants_cols = st.columns(2)
                with occupants_cols[0]:
                    edited_num_occupants_unit_1 = st.number_input("Number of Occupants (Unit 1)", min_value=0, value=record_obj.num_occupants_unit_1, step=1, key="edit_num_occupants_unit_1")
                    edited_num_occupants_unit_2 = st.number_input("Number of Occupants (Unit 2)", min_value=0, value=record_obj.num_occupants_unit_2, step=1, key="edit_num_occupants_unit_2")
                with occupants_cols[1]:
                    edited_num_occupants_unit_3 = st.number_input("Number of Occupants (Unit 3)", min_value=0, value=record_obj.num_occupants_unit_3, step=1, key="edit_num_occupants_unit_3")
                    edited_num_occupants_unit_4 = st.number_input("Number of Occupants (Unit 4)", min_value=0, value=record_obj.num_occupants_unit_4, step=1, key="edit_num_occupants_unit_4")

                if st.button("Salvar Alterações"):
                    updated_record_data = {
                        "id": record_obj.id, # Ensure ID is preserved
                        "crash_date": edited_crash_date.isoformat(),
                        "crash_type": edited_crash_type,
                        "num_units": edited_num_units,
                        "injuries_total": edited_injuries_total,
                        "crash_severity": edited_crash_severity,
                        "most_severe_injury": edited_most_severe_injury,
                        "pre_crash_action_unit_1": edited_pre_crash_action_unit_1,
                        "pre_crash_action_unit_2": edited_pre_crash_action_unit_2,
                        "pre_crash_action_unit_3": edited_pre_crash_action_unit_3,
                        "pre_crash_action_unit_4": edited_pre_crash_action_unit_4,
                        "injuries_fatal": edited_injuries_fatal,
                        "injuries_incapacitating": edited_injuries_incapacitating,
                        "injuries_non_incapacitating": edited_injuries_non_incapacitating,
                        "injuries_reported_not_evident": edited_injuries_reported_not_evident,
                        "injuries_no_indication": edited_injuries_no_indication,
                        "fatalities_total": edited_fatalities_total,
                        "num_occupants_unit_1": edited_num_occupants_unit_1,
                        "num_occupants_unit_2": edited_num_occupants_unit_2,
                        "num_occupants_unit_3": edited_num_occupants_unit_3,
                        "num_occupants_unit_4": edited_num_occupants_unit_4,
                    }
                    try:
                        updated_record = DataObject(existing_data_dict=updated_record_data)
                        db.update_record(updated_record)
                        st.success(f"Record '{record_obj.id}' updated successfully!")
                        st.session_state.current_page = "View Records" # Redirect after update
                        st.rerun()
                    except ValidationError as e:
                        st.error(f"Validation Error: {e}")
                        logger.error(f"Validation error when updating record {record_obj.id}: {traceback.format_exc()}")
                    except DatabaseError as e:
                        st.error(f"Database Error: {e}")
                        logger.error(f"Database error when updating record {record_obj.id}: {traceback.format_exc()}")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")
                        logger.error(f"Unexpected error when updating record {record_obj.id}: {traceback.format_exc()}")
            else:
                st.warning(f"No record found with ID: {record_id_to_edit}")
        except DatabaseError as e:
            st.error(f"Database Error retrieving record: {e}")
            logger.error(f"Database error when retrieving record {record_id_to_edit} for edit: {traceback.format_exc()}")
        except Exception as e:
            st.error(f"An unexpected error occurred while fetching record for edit: {e}")
            logger.error(f"Unexpected error fetching record {record_id_to_edit} for edit: {traceback.format_exc()}")

def delete_record_section(db: TrafficAccidentsDB):
    st.header("Deletar Registro")
    record_id_to_delete = st.text_input("Enter Record ID to Delete:", key="delete_record_id_input")

    if st.button("Deletar Registro", type="secondary"):
        if record_id_to_delete:
            try:
                db.delete_record(record_id_to_delete)
                st.success(f"Record '{record_id_to_delete}' deleted successfully.")
                st.session_state.current_page = "View Records" # Redirect after delete
                st.rerun()
            except DatabaseError as e:
                st.error(f"Database Error: {e}")
                logger.error(f"Database error when deleting record {record_id_to_delete}: {traceback.format_exc()}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                logger.error(f"Unexpected error when deleting record {record_id_to_delete}: {traceback.format_exc()}")
        else:
            st.warning("Please enter a Record ID to delete.")

def search_records_section(db: TrafficAccidentsDB):
    st.header("Pesquisar Registros")
    search_query = st.text_input("Enter search term (ID, Crash Type, etc.):", key="search_query_input")

    if st.button("Search"):
        try:
            if search_query:
                found_records_raw = db.search_records(search_query)
                st.subheader("Search Results:")
                if found_records_raw:
                    for raw_record_data in found_records_raw:
                        if 'data_bytes' in raw_record_data:
                            try:
                                record = DataObject.from_bytes(raw_record_data['data_bytes'])
                                display_record_details(record) # Display the found record
                            except DatabaseError as e:
                                st.error(f"Error loading record {raw_record_data.get('id', 'N/A')} from search results: {e}")
                                logger.error(f"Failed to load record from search results: {traceback.format_exc()}")
                            except Exception as e:
                                st.error(f"An unexpected error occurred while displaying search result {raw_record_data.get('id', 'N/A')}: {e}")
                                logger.error(f"Unexpected error displaying search result: {traceback.format_exc()}")
                        else:
                            st.warning(f"Search result data for ID {raw_record_data.get('id', 'N/A')} is incomplete.")
                else:
                    st.info("No records found matching your search query.")
            else:
                st.warning("Please enter a search term.")
        except DatabaseError as e:
            st.error(f"Database Error during search: {e}")
            logger.error(f"Database error during search '{search_query}': {traceback.format_exc()}")
        except Exception as e:
            st.error(f"An unexpected error occurred during search: {e}")
            logger.error(f"Unexpected error during search '{search_query}': {traceback.format_exc()}")

def upload_csv_section(db: TrafficAccidentsDB):
    st.header("Importar Dados de CSV")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"File size exceeds the limit of {MAX_FILE_SIZE_MB} MB.")
            return

        st.info(f"Processing CSV file: {uploaded_file.name} (Size: {uploaded_file.size / (1024*1024):.2f} MB)")
        
        # Create a temporary file to write the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        success_count = 0
        fail_count = 0
        
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as temp_file:
                csv_reader = csv.reader(temp_file, delimiter=CSV_DELIMITER)
                try:
                    header = [h.strip() for h in next(csv_reader)] # Get header
                except StopIteration:
                    st.error("The uploaded CSV file is empty or has no header.")
                    return
                
                header_mapping = {field: i for i, field in enumerate(header)}
                
                # Check for required fields in CSV header
                missing_fields = [f for f in DataObject.REQUIRED_FIELDS if f not in header_mapping]
                if missing_fields:
                    st.error(f"CSV is missing required header fields: {', '.join(missing_fields)}")
                    st.warning("Please ensure your CSV header matches the expected fields: " + ", ".join(DataObject.ALL_FIELDS))
                    return

                total_rows = sum(1 for row in csv.reader(open(temp_file_path, 'r', encoding='utf-8'), delimiter=CSV_DELIMITER)) - 1 # Recount rows, excluding header
                progress_bar = st.progress(0)
                st.write(f"Importing {total_rows} records...")

                temp_file.seek(0) # Reset file pointer after reading header and counting
                next(csv_reader) # Skip header again

                db_records = db._read_all_records_from_file() # Read current records once to check for duplicates
                
                for i, row in enumerate(csv_reader):
                    if len(row) != len(header):
                        logger.warning(f"Skipping row {i+2} (CSV row num) due to column mismatch: {row}")
                        fail_count += 1
                        continue

                    record_data = {header[j]: value.strip() for j, value in enumerate(row)}

                    # Use existing ID if present, otherwise DataObject will generate one
                    record_id = record_data.get('id')

                    # Skip if record ID already exists in DB
                    if record_id and record_id in db_records:
                        logger.warning(f"Skipping row {i+2}: Record with ID '{record_id}' already exists. Use 'Edit Record' to update.")
                        fail_count += 1
                        continue

                    try:
                        new_record = DataObject(id=record_id, existing_data_dict=record_data) # Pass existing_data_dict
                        db.insert_record(new_record)
                        success_count += 1
                    except (ValidationError, DatabaseError) as e:
                        logger.error(f"Error importing row {i+2} (ID: {record_id or 'N/A'}): {e}. Data: {record_data}")
                        fail_count += 1
                    except Exception as e:
                        logger.error(f"Unexpected error importing row {i+2} (ID: {record_id or 'N/A'}): {e}. {traceback.format_exc()}")
                        fail_count += 1

                    progress_bar.progress(min(1.0, (i + 1) / total_rows))

            st.success(f"CSV import complete. Successfully imported: {success_count}. Failed: {fail_count}.")
            # Trigger a rerun to show newly added records if in View Records tab
            st.session_state.current_page = "View Records"
            st.rerun()

        except StopIteration:
            st.error("The uploaded CSV file is empty or has no header.")
        except FileNotFoundError: # Should be caught by uploaded_file check, but good to have
            st.error("CSV file not found on server.")
        except csv.Error as e:
            st.error(f"Error reading CSV file: {e}. Please ensure it's a valid CSV with '{CSV_DELIMITER}' delimiter.")
            logger.error(f"CSV read error: {traceback.format_exc()}")
        except UnicodeDecodeError:
            st.error("Failed to decode CSV file. Please ensure it's a UTF-8 encoded file.")
            logger.error(f"UnicodeDecodeError during CSV import: {traceback.format_exc()}")
        except Exception as e:
            st.error(f"An unexpected error occurred during CSV file processing: {e}")
            logger.error(f"Unexpected error in upload_csv_section: {traceback.format_exc()}")
        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path) # Clean up temp file
                except OSError as e:
                    logger.warning(f"Failed to remove temporary CSV file {temp_file_path}: {e}")

def export_csv_section(db: TrafficAccidentsDB):
    st.header("Exportar Dados para CSV")
    
    all_records_raw = []
    try:
        all_records_raw = db.read_records_paginated(0, db.get_total_records()) # Get all records
    except DatabaseError as e:
        st.error(f"Error fetching records for export: {e}")
        logger.error(f"Database error during export_csv_section record fetch: {traceback.format_exc()}")
        return
    except Exception as e:
        st.error(f"An unexpected error occurred fetching records for export: {e}")
        logger.error(f"Unexpected error during export_csv_section record fetch: {traceback.format_exc()}")
        return

    if not all_records_raw:
        st.info("No records to export.")
        return

    csv_data = None
    try:
        with tempfile.TemporaryFile(mode='w+', delete=False, encoding='utf-8', newline='') as temp_file:
            csv_writer = csv.writer(temp_file, delimiter=CSV_DELIMITER)
            csv_writer.writerow(DataObject.get_header_fields())

            for record_data in all_records_raw:
                try:
                    record_obj = DataObject.from_bytes(record_data['data_bytes'])
                    csv_writer.writerow(record_obj.to_csv_row())
                except Exception as e:
                    logger.error(f"Error processing record ID {record_data.get('id', 'N/A')} for CSV export: {e}")
                    st.warning(f"Skipped record ID {record_data.get('id', 'N/A')} due to an error during export.")
                    continue
            
            temp_file_path = temp_file.name
            temp_file.seek(0) # Rewind to read content
            csv_data = temp_file.read().encode('utf-8')
            
    except IOError as e:
        st.error(f"Could not write CSV file: {e}")
        logger.error(f"IOError during CSV export: {traceback.format_exc()}")
        return
    except Exception as e:
        st.error(f"An unexpected error occurred during CSV export: {e}")
        logger.error(f"Unexpected error in export_csv_section: {traceback.format_exc()}")
        return
    finally:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError as e:
                logger.warning(f"Failed to remove temporary export CSV file {temp_file_path}: {e}")


    if csv_data:
        st.download_button(
            label="Download CSV File",
            data=csv_data,
            file_name="traffic_accidents.csv",
            mime="text/csv",
            help="Download all current records as a CSV file."
        )

def manage_backups_section(db: TrafficAccidentsDB):
    st.header("Gerenciar Backups do Banco de Dados")

    if st.button("Criar Backup Agora"):
        try:
            db.backup_database()
            st.success("Backup criado com sucesso!")
        except DatabaseError as e:
            st.error(f"Erro ao criar backup: {e}")
            logger.error(f"Error creating backup: {traceback.format_exc()}")
        except Exception as e:
            st.error(f"Um erro inesperado ocorreu ao criar backup: {e}")
            logger.error(f"Unexpected error creating backup: {traceback.format_exc()}")
    
    st.markdown("---")
    st.subheader("Restaurar de Backup")
    
    backup_files = []
    try:
        if os.path.exists(BACKUP_DIR):
            backup_files = sorted(
                [f for f in os.listdir(BACKUP_DIR) if f.startswith("traffic_accidents_backup_") and f.endswith(".db")],
                key=lambda f: os.path.getmtime(os.path.join(BACKUP_DIR, f)),
                reverse=True
            )
    except OSError as e:
        st.error(f"Erro ao listar arquivos de backup em {BACKUP_DIR}: {e}")
        logger.error(f"Error listing backup files: {traceback.format_exc()}")
        backup_files = [] # Reset to empty list if error occurs

    if not backup_files:
        st.info("Nenhum arquivo de backup encontrado.")
    else:
        selected_backup = st.selectbox(
            "Selecione um arquivo de backup para restaurar:",
            options=backup_files,
            format_func=lambda x: f"{x} (Last modified: {datetime.fromtimestamp(os.path.getmtime(os.path.join(BACKUP_DIR, x))).strftime('%Y-%m-%d %H:%M:%S')})"
        )

        if st.button("Restaurar do Backup Selecionado", type="primary"):
            if selected_backup:
                backup_path = os.path.join(BACKUP_DIR, selected_backup)
                confirm_restore = st.warning(f"Certeza que deseja restaurar de '{selected_backup}'? Esta ação irá sobrescrever o banco de dados atual.")
                if st.button("Confirmar Restauração"):
                    try:
                        db.restore_database(backup_path)
                        st.success(f"Banco de dados restaurado com sucesso de '{selected_backup}'!")
                        st.session_state.current_page = "View Records" # Redirect after restore
                        st.rerun()
                    except DatabaseError as e:
                        st.error(f"Erro ao restaurar banco de dados: {e}")
                        logger.error(f"Error restoring database from {backup_path}: {traceback.format_exc()}")
                    except FileNotFoundError as e:
                        st.error(f"Erro: Arquivo de backup não encontrado. {e}")
                        logger.error(f"Backup file not found during restore: {traceback.format_exc()}")
                    except Exception as e:
                        st.error(f"Um erro inesperado ocorreu ao restaurar o banco de dados: {e}")
                        logger.error(f"Unexpected error restoring database: {traceback.format_exc()}")
            else:
                st.warning("Por favor, selecione um arquivo de backup.")

def read_activity_log():
    st.header("Registro de Atividades Recentes")
    log_file_path = 'traffic_accidents.log'
    MAX_LOG_ENTRIES_DISPLAY = 20 # Limit the number of log entries to display

    if not os.path.exists(log_file_path):
        st.info("Nenhum registro de atividade encontrado ainda.")
        return

    try:
        log_lines = []
        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        # Display latest entries
        st.subheader("Últimas 20 Entradas no Log:")
        if log_lines:
            for line in reversed(log_lines[-MAX_LOG_ENTRIES_DISPLAY:]): # Get last N lines
                st.code(line.strip(), language='log')
        else:
            st.info("O arquivo de log está vazio.")

        st.markdown("---")
        st.subheader("Atualizações e Importações de Registro (Últimas 20):")
        update_entries = []
        try:
            # Filter for specific log messages related to record updates/imports
            # Iterating in reverse is more efficient for getting recent entries
            for line in reversed(log_lines):
                if "inserted successfully" in line or "updated successfully" in line or "CSV import complete" in line:
                    parts = line.split(" - ")
                    if len(parts) >= 4:
                        timestamp_str = parts[0]
                        message = parts[3].strip()
                        update_entries.append(f"**`{timestamp_str}`** `{message}`")
                        if len(update_entries) >= MAX_LOG_ENTRIES_DISPLAY:
                            break
            # Add specific messages for import completion
            for line in reversed(log_lines):
                if "CSV import complete" in line:
                    parts = line.split(" - ")
                    if len(parts) >= 4:
                        timestamp_str = parts[0]
                        message = parts[3].strip()
                        if f"**`{timestamp_str}`** `{message}`" not in update_entries: # Avoid duplicates
                            update_entries.append(f"**`{timestamp_str}`** `{message}`")
                            if len(update_entries) >= MAX_LOG_ENTRIES_DISPLAY:
                                break
        except Exception as e:
            logger.warning(f"Failed to parse log line for registry: {line.strip()} - {e}")
            # continue - no need to continue here, as we are in a loop for parsing
            # if an error happens in parsing, it will break the loop for the current line
            # but the overall log display should still proceed.

        if update_entries:
            # Display in chronological order (oldest first)
            for entry in reversed(update_entries):
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

    # Initialize session state for page navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "View Records"

    # Initialize the database object
    if 'db' not in st.session_state:
        try:
            st.session_state.db = TrafficAccidentsDB(DB_FILE, LOCK_FILE)
            logger.info("Database initialized successfully.")
        except DatabaseError as e:
            st.error(f"Fatal Error: Could not initialize database. {e}")
            logger.critical(f"Database initialization failed: {traceback.format_exc()}")
            st.stop() # Stop the app if DB cannot be initialized
        except Exception as e:
            st.error(f"An unexpected fatal error occurred during database initialization: {e}")
            logger.critical(f"Unexpected fatal error during database initialization: {traceback.format_exc()}")
            st.stop()

    def setup_ui():
        db = st.session_state.db # Get DB instance from session state

        st.sidebar.title("Navegação")
        if st.sidebar.button("Ver Registros", key="nav_view"):
            st.session_state.current_page = "View Records"
        if st.sidebar.button("Adicionar Registro", key="nav_add"):
            st.session_state.current_page = "Add Record"
        if st.sidebar.button("Editar Registro", key="nav_edit"):
            st.session_state.current_page = "Edit Record"
        if st.sidebar.button("Deletar Registro", key="nav_delete"):
            st.session_state.current_page = "Delete Record"
        if st.sidebar.button("Pesquisar Registros", key="nav_search"):
            st.session_state.current_page = "Search Records"
        if st.sidebar.button("Importar CSV", key="nav_import"):
            st.session_state.current_page = "Import CSV"
        if st.sidebar.button("Exportar CSV", key="nav_export"):
            st.session_state.current_page = "Export CSV"
        if st.sidebar.button("Gerenciar Backups", key="nav_backups"):
            st.session_state.current_page = "Manage Backups"
        if st.sidebar.button("Ver Log de Atividades", key="nav_log"):
            st.session_state.current_page = "View Log"

        st.title("Sistema de Gerenciamento de Acidentes de Trânsito")

        if st.session_state.current_page == "View Records":
            st.header("Registros de Acidentes de Trânsito")
            try:
                total_records = db.get_total_records()
                st.write(f"Total de registros: {total_records}")

                # Pagination controls
                num_pages = (total_records + MAX_RECORDS_PER_PAGE - 1) // MAX_RECORDS_PER_PAGE
                if 'current_page_num' not in st.session_state:
                    st.session_state.current_page_num = 1
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("Previous", disabled=(st.session_state.current_page_num <= 1)):
                        st.session_state.current_page_num -= 1
                        st.rerun()
                with col2:
                    st.markdown(f"<h3 style='text-align: center;'>Página {st.session_state.current_page_num} de {num_pages if num_pages > 0 else 1}</h3>", unsafe_allow_html=True)
                with col3:
                    if st.button("Next", disabled=(st.session_state.current_page_num >= num_pages)):
                        st.session_state.current_page_num += 1
                        st.rerun()

                offset = (st.session_state.current_page_num - 1) * MAX_RECORDS_PER_PAGE
                
                raw_records = db.read_records_paginated(offset, MAX_RECORDS_PER_PAGE)
                st.write(f"Displaying records {offset + 1} to {min(offset + MAX_RECORDS_PER_PAGE, total_records)} of {total_records}")

                if not raw_records:
                    st.info("No records to display.")
                else:
                    for i, raw_record_data in enumerate(raw_records):
                        # Ensure record is a DataObject for display_record_details
                        if 'data_bytes' in raw_record_data:
                            try:
                                record = DataObject.from_bytes(raw_record_data['data_bytes'])
                                # Call display_record_details with a dictionary representation
                                # or adapt display_record_details to take DataObject directly.
                                # For consistency with old usage, convert to dict.
                                display_record_details(record.to_dict()) # Pass dictionary for .get() compatibility
                            except DatabaseError as e:
                                st.error(f"Error loading record {raw_record_data.get('id', 'N/A')}: {e}")
                                logger.error(f"Failed to load record from bytes: {traceback.format_exc()}")
                            except Exception as e:
                                st.error(f"An unexpected error occurred while displaying record {raw_record_data.get('id', 'N/A')}: {e}")
                                logger.error(f"Unexpected error displaying record: {traceback.format_exc()}")
                        else:
                            st.warning(f"Record data for ID {raw_record_data.get('id', 'N/A')} is incomplete.")
            except DatabaseError as e:
                st.error(f"Error accessing database: {e}")
                logger.error(f"Database access error in View Records: {traceback.format_exc()}")
            except Exception as e:
                st.error(f"An unexpected error occurred in View Records: {e}")
                logger.error(f"Unexpected error in View Records: {traceback.format_exc()}")

        elif st.session_state.current_page == "Add Record":
            add_record_section(db)
        elif st.session_state.current_page == "Edit Record":
            edit_record_section(db)
        elif st.session_state.current_page == "Delete Record":
            delete_record_section(db)
        elif st.session_state.current_page == "Search Records":
            search_records_section(db)
        elif st.session_state.current_page == "Import CSV":
            upload_csv_section(db)
        elif st.session_state.current_page == "Export CSV":
            export_csv_section(db)
        elif st.session_state.current_page == "Manage Backups":
            manage_backups_section(db)
        elif st.session_state.current_page == "View Log":
            read_activity_log()

    setup_ui() # Start the Streamlit UI