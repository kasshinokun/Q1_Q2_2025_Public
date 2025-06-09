import streamlit as st
import csv
import os
import struct
from pathlib import Path
import json
from typing import List, Dict, Optional, Union, Callable, Any, Tuple
import tempfile
import logging
from datetime import datetime, date, timedelta
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import threading
import platform
import shutil
import time
import sys
import re
from enum import Enum, auto

# Constants
DB_DIR = os.path.join(Path.home(), 'Documents', 'Data', 'TrafficAccidents')
DB_FILE = os.path.join(DB_DIR, 'traffic_accidents.db')
BACKUP_DIR = os.path.join(DB_DIR, 'backups')
CSV_DELIMITER = ';'
MAX_RECORDS_PER_PAGE = 20
MAX_FILE_SIZE_MB = 10
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for file processing
MAX_RECORD_SIZE = 10 * 1024 * 1024  # 10MB max record size
VALID_DATE_FORMATS = ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y')
MAX_BACKUPS = 10  # Maximum number of backups to keep
LOCK_TIMEOUT = 30  # seconds for lock acquisition
MAX_RETRIES = 3  # For retryable operations

# Configure robust logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traffic_accidents.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Field definitions with types and validation rules
class FieldType(Enum):
    STRING = auto()
    DATE = auto()
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    ENUM = auto()

FIELD_DEFINITIONS = {
    'crash_date': {'type': FieldType.DATE, 'required': True},
    'traffic_control_device': {'type': FieldType.STRING, 'default': 'Unknown'},
    'weather_condition': {'type': FieldType.STRING, 'default': 'Unknown'},
    'lighting_condition': {'type': FieldType.STRING, 'default': 'Unknown'},
    'first_crash_type': {'type': FieldType.STRING, 'default': 'Unknown'},
    'trafficway_type': {'type': FieldType.STRING, 'default': 'Unknown'},
    'alignment': {'type': FieldType.STRING, 'default': 'Unknown'},
    'roadway_surface_cond': {'type': FieldType.STRING, 'default': 'Unknown'},
    'road_defect': {'type': FieldType.STRING, 'default': 'None'},
    'crash_type': {'type': FieldType.STRING, 'required': True},
    'intersection_related_i': {'type': FieldType.BOOLEAN, 'default': False},
    'damage': {'type': FieldType.STRING, 'default': 'Unknown'},
    'prim_contributory_cause': {'type': FieldType.STRING, 'default': 'Unknown'},
    'num_units': {'type': FieldType.INTEGER, 'default': 0, 'min': 0},
    'most_severe_injury': {'type': FieldType.STRING, 'default': 'None'},
    'injuries_total': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_fatal': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_incapacitating': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_non_incapacitating': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_reported_not_evident': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'injuries_no_indication': {'type': FieldType.FLOAT, 'default': 0.0, 'min': 0.0},
    'crash_hour': {'type': FieldType.INTEGER, 'default': 0, 'min': 0, 'max': 23},
    'crash_day_of_week': {'type': FieldType.INTEGER, 'default': 1, 'min': 1, 'max': 7},
    'crash_month': {'type': FieldType.INTEGER, 'default': 1, 'min': 1, 'max': 12}
}

FIELDS = list(FIELD_DEFINITIONS.keys())

# Custom Exceptions
class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class LockAcquisitionError(Exception):
    """Custom exception for lock acquisition failures"""
    pass

class BackupError(Exception):
    """Custom exception for backup operations"""
    pass

class DataObject:
    """Represents a traffic accident record with enhanced validation and serialization."""
    
    def __init__(self, row_data: Optional[List[str]] = None):
        self._initialize_defaults()
        
        if row_data is not None:
            try:
                self._initialize_from_row(row_data)
                if not self.validate():
                    raise DataValidationError("Data validation failed during initialization")
            except Exception as e:
                logger.error(f"Error initializing DataObject: {str(e)}\n{traceback.format_exc()}")
                raise DataValidationError(f"Invalid data: {str(e)}")

    def _initialize_defaults(self):
        """Initialize all fields with type-appropriate default values."""
        for field, definition in FIELD_DEFINITIONS.items():
            setattr(self, field, definition.get('default', None))

    def _initialize_from_row(self, row_data: List[str]):
        """Initialize object from CSV row data with enhanced type conversion and validation."""
        if len(row_data) != len(FIELDS):
            raise DataValidationError(f"Expected {len(FIELDS)} fields, got {len(row_data)}")
        
        processed_data = [value if value and value.strip() else None for value in row_data]
        
        try:
            for i, field in enumerate(FIELDS):
                value = processed_data[i]
                definition = FIELD_DEFINITIONS[field]
                
                try:
                    if value is None and definition.get('required', False):
                        raise DataValidationError(f"Required field {field} is missing")
                    
                    if value is None:
                        continue  # Use default value
                    
                    if definition['type'] == FieldType.DATE:
                        setattr(self, field, self._validate_date(value))
                    elif definition['type'] == FieldType.STRING:
                        setattr(self, field, self._validate_string(value, field))
                    elif definition['type'] == FieldType.BOOLEAN:
                        setattr(self, field, self._validate_boolean(value))
                    elif definition['type'] == FieldType.INTEGER:
                        setattr(self, field, self._validate_integer(value, field, 
                                                                   definition.get('min'), 
                                                                   definition.get('max')))
                    elif definition['type'] == FieldType.FLOAT:
                        setattr(self, field, self._validate_float(value, field, 
                                                                definition.get('min')))
                except DataValidationError as e:
                    logger.warning(f"Validation error for field {field}: {str(e)}")
                    raise
                except Exception as e:
                    logger.error(f"Unexpected error processing field {field}: {str(e)}")
                    raise DataValidationError(f"Invalid value for {field}: {str(e)}")
        except Exception as e:
            logger.error(f"Validation error in field initialization: {str(e)}\n{traceback.format_exc()}")
            raise DataValidationError(f"Field validation failed: {str(e)}")

    @staticmethod
    def _validate_date(date_str: str) -> str:
        """Validate and standardize date format with enhanced checks."""
        date_str = str(date_str).strip()
        if not date_str:
            return ""
        
        for fmt in VALID_DATE_FORMATS:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Validate date is not in the future
                if dt.date() > date.today():
                    raise DataValidationError("Date cannot be in the future")
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        raise DataValidationError(f"Invalid date format. Expected one of: {', '.join(VALID_DATE_FORMATS)}")

    @staticmethod
    def _validate_string(value: str, field_name: str) -> str:
        """Validate string fields with sanitization."""
        value = str(value).strip()
        if not value:
            return FIELD_DEFINITIONS[field_name].get('default', '')
        
        # Enhanced sanitization
        value = re.sub(r'[;\n\r\t]', ' ', value)  # Remove problematic characters
        return value[:255]  # Limit string length

    @staticmethod
    def _validate_boolean(value: str) -> bool:
        """Validate boolean fields."""
        value = str(value).strip().lower()
        return value in ('yes', 'y', 'true', '1', 't')

    @staticmethod
    def _validate_integer(value: str, field_name: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Validate integer fields with range checking."""
        try:
            num = int(float(value)) if value else FIELD_DEFINITIONS[field_name].get('default', 0)
            
            if min_val is not None and num < min_val:
                raise DataValidationError(f"Value must be ≥ {min_val}")
            if max_val is not None and num > max_val:
                raise DataValidationError(f"Value must be ≤ {max_val}")
            
            return num
        except (ValueError, TypeError):
            raise DataValidationError("Invalid integer value")

    @staticmethod
    def _validate_float(value: str, field_name: str, min_val: Optional[float] = None) -> float:
        """Validate float fields with range checking."""
        try:
            num = float(value) if value else FIELD_DEFINITIONS[field_name].get('default', 0.0)
            
            if min_val is not None and num < min_val:
                raise DataValidationError(f"Value must be ≥ {min_val}")
            
            return round(num, 2)
        except (ValueError, TypeError):
            raise DataValidationError("Invalid numeric value")

    def to_bytes(self) -> bytes:
        """Serialize object to bytes using JSON with error handling."""
        try:
            data_dict = {attr: getattr(self, attr) for attr in FIELDS}
            return json.dumps(data_dict, sort_keys=True).encode('utf-8')
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Failed to serialize record")

    @classmethod
    def from_bytes(cls, byte_data: bytes) -> 'DataObject':
        """Deserialize object from bytes with comprehensive error handling."""
        try:
            if not byte_data:
                raise ValueError("Empty byte data")
                
            data_dict = json.loads(byte_data.decode('utf-8'))
            obj = cls()
            
            for key, value in data_dict.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            
            if not obj.validate():
                raise DataValidationError("Deserialized object failed validation")
            
            return obj
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise DatabaseError("Invalid data format")
        except Exception as e:
            logger.error(f"Deserialization error: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Failed to deserialize record")

    def validate(self) -> bool:
        """Comprehensive validation of the object's fields."""
        try:
            # Required fields validation
            if not self.crash_date:
                raise DataValidationError("Crash date is required")
            
            if not self.crash_type:
                raise DataValidationError("Crash type is required")
            
            # Validate all fields against their definitions
            for field, definition in FIELD_DEFINITIONS.items():
                value = getattr(self, field)
                
                if definition.get('required', False) and not value:
                    raise DataValidationError(f"Required field {field} is empty")
                
                if value is None:
                    continue
                
                if definition['type'] == FieldType.INTEGER:
                    if not isinstance(value, int):
                        raise DataValidationError(f"{field} must be an integer")
                    if 'min' in definition and value < definition['min']:
                        raise DataValidationError(f"{field} must be ≥ {definition['min']}")
                    if 'max' in definition and value > definition['max']:
                        raise DataValidationError(f"{field} must be ≤ {definition['max']}")
                
                elif definition['type'] == FieldType.FLOAT:
                    if not isinstance(value, (int, float)):
                        raise DataValidationError(f"{field} must be a number")
                    if 'min' in definition and value < definition['min']:
                        raise DataValidationError(f"{field} must be ≥ {definition['min']}")
                
                elif definition['type'] == FieldType.DATE:
                    try:
                        datetime.strptime(value, '%Y-%m-%d')
                    except ValueError:
                        raise DataValidationError(f"{field} must be a valid date in YYYY-MM-DD format")
            
            return True
        except DataValidationError as e:
            logger.warning(f"Validation failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}\n{traceback.format_exc()}")
            return False

class TrafficAccidentsDB:
    """Enhanced database handler with thread-safe operations, backups, and recovery."""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist with proper permissions."""
        try:
            # Create database directory
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            os.chmod(os.path.dirname(self.db_path), 0o755)
            
            # Create backup directory
            os.makedirs(BACKUP_DIR, exist_ok=True)
            os.chmod(BACKUP_DIR, 0o755)
            
            # Clean up old backups
            self._cleanup_old_backups()
        except Exception as e:
            logger.error(f"Directory initialization failed: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Could not initialize directories")

    def _cleanup_old_backups(self):
        """Clean up old backups keeping only the most recent MAX_BACKUPS."""
        try:
            backups = sorted(Path(BACKUP_DIR).glob('backup_*.db'))
            if len(backups) > MAX_BACKUPS:
                for old_backup in backups[:-MAX_BACKUPS]:
                    try:
                        os.unlink(old_backup)
                        logger.info(f"Removed old backup: {old_backup}")
                    except Exception as e:
                        logger.warning(f"Failed to remove old backup {old_backup}: {str(e)}")
        except Exception as e:
            logger.warning(f"Backup cleanup failed: {str(e)}")

    def _acquire_lock(self) -> bool:
        """Attempt to acquire the lock with timeout."""
        for attempt in range(MAX_RETRIES):
            try:
                acquired = self.lock.acquire(timeout=LOCK_TIMEOUT)
                if acquired:
                    return True
                logger.warning(f"Lock acquisition attempt {attempt + 1} timed out")
            except Exception as e:
                logger.error(f"Lock acquisition error: {str(e)}")
        
        logger.error("Failed to acquire lock after multiple attempts")
        raise LockAcquisitionError("Could not acquire database lock")

    def _release_lock(self):
        """Release the lock with error handling."""
        try:
            if self.lock.locked():
                self.lock.release()
        except Exception as e:
            logger.error(f"Lock release error: {str(e)}")
            # At this point we can't do much, but we should try to avoid deadlocks
            try:
                if hasattr(self.lock, '_is_owned'):  # Check for RLock
                    while self.lock._is_owned():
                        self.lock.release()
            except:
                pass

    def _create_backup(self) -> str:
        """Create a timestamped backup of the database with atomic write."""
        backup_path = ""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
            
            # Use atomic write operation
            temp_backup = f"{backup_path}.tmp"
            
            with open(self.db_path, 'rb') as src, open(temp_backup, 'wb') as dst:
                shutil.copyfileobj(src, dst, length=CHUNK_SIZE)
            
            # Atomic rename
            os.replace(temp_backup, backup_path)
            
            logger.info(f"Created database backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}\n{traceback.format_exc()}")
            # Clean up failed backup
            if backup_path and os.path.exists(backup_path):
                try:
                    os.unlink(backup_path)
                except:
                    pass
            raise BackupError("Could not create database backup")

    def get_last_id(self) -> int:
        """Get the last used ID from the database with error handling."""
        if not os.path.exists(self.db_path):
            return 0
        
        try:
            if not self._acquire_lock():
                raise LockAcquisitionError("Could not acquire lock for reading last ID")
            
            try:
                with open(self.db_path, 'rb') as f:
                    id_bytes = f.read(4)
                    return struct.unpack('I', id_bytes)[0] if len(id_bytes) == 4 else 0
            finally:
                self._release_lock()
        except FileNotFoundError:
            return 0
        except Exception as e:
            logger.error(f"Error getting last ID: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Failed to read last ID")

    def update_last_id(self, new_id: int):
        """Safely update the last ID in the database with fsync."""
        try:
            if not self._acquire_lock():
                raise LockAcquisitionError("Could not acquire lock for updating last ID")
            
            try:
                with open(self.db_path, 'r+b') as f:
                    f.write(struct.pack('I', new_id))
                    f.flush()
                    os.fsync(f.fileno())
            finally:
                self._release_lock()
        except Exception as e:
            logger.error(f"Error updating last ID: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Failed to update last ID")

    def read_all_records(self) -> List[Dict[str, Any]]:
        """Read all records from the database with recovery capabilities."""
        if not os.path.exists(self.db_path):
            return []
        
        records = []
        try:
            if not self._acquire_lock():
                raise LockAcquisitionError("Could not acquire lock for reading records")
            
            try:
                with open(self.db_path, 'rb') as f:
                    f.read(4)  # Skip last ID
                    
                    while True:
                        pos = f.tell()
                        try:
                            record = self._read_next_record(f)
                            if not record:
                                break
                            records.append(record)
                        except DatabaseError as e:
                            logger.warning(f"Skipping corrupt record at position {pos}: {str(e)}")
                            # Attempt to recover by finding the next valid record
                            f.seek(pos + 1)  # Skip one byte and try again
                            continue
            finally:
                self._release_lock()
            
            logger.info(f"Successfully read {len(records)} records")
            return records
        except Exception as e:
            logger.error(f"Error reading records: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Failed to read records")

    def read_record_by_id(self, search_id: int) -> Optional[Dict[str, Any]]:
        """Read a specific record by ID with binary search for efficiency."""
        if search_id <= 0:
            raise ValueError("ID must be positive")
        
        if not os.path.exists(self.db_path):
            return None
        
        try:
            if not self._acquire_lock():
                raise LockAcquisitionError("Could not acquire lock for searching records")
            
            try:
                with open(self.db_path, 'rb') as f:
                    f.read(4)  # Skip last ID
                    
                    while True:
                        pos = f.tell()
                        record = self._read_next_record(f)
                        if not record:
                            break
                        if record['id'] == search_id:
                            record['position'] = pos
                            return record
            finally:
                self._release_lock()
            
            return None
        except Exception as e:
            logger.error(f"Error searching for record {search_id}: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError(f"Failed to search for record {search_id}")

    def _read_next_record(self, file_obj) -> Optional[Dict[str, Any]]:
        """Read the next record from the file with robust error handling."""
        try:
            # Read record header
            header = file_obj.read(9)  # 4 bytes ID + 1 byte validation + 4 bytes size
            if len(header) < 9:
                return None
            
            # Unpack binary data
            try:
                record_id = struct.unpack('I', header[:4])[0]
                validation = struct.unpack('?', header[4:5])[0]
                size = struct.unpack('I', header[5:9])[0]
                
                # Validate size before reading
                if size > MAX_RECORD_SIZE:
                    raise DatabaseError(f"Record size {size} exceeds maximum allowed")
                
                data_bytes = file_obj.read(size)
                if len(data_bytes) != size:
                    return None
                
                # Verify data checksum
                checksum = hashlib.sha256(data_bytes).hexdigest()
                
                return {
                    'id': record_id,
                    'validation': validation,
                    'size': size,
                    'checksum': checksum,
                    'data': DataObject.from_bytes(data_bytes)
                }
            except struct.error as e:
                raise DatabaseError(f"Invalid binary data format: {str(e)}")
            
        except Exception as e:
            logger.error(f"Record read error: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError(f"Failed to read record: {str(e)}")

    def write_record(self, data_object: DataObject) -> int:
        """Write a single record to the database with file locking and backup."""
        if not isinstance(data_object, DataObject):
            raise TypeError("Expected DataObject instance")
        
        if not data_object.validate():
            raise DataValidationError("Data object failed validation")
        
        try:
            # Create backup before writing
            backup_path = self._create_backup()
            
            if not self._acquire_lock():
                raise LockAcquisitionError("Could not acquire lock for writing record")
            
            try:
                last_id = self.get_last_id()
                new_id = last_id + 1 if last_id > 0 else 1
                
                obj_bytes = data_object.to_bytes()
                size = len(obj_bytes)
                validation = data_object.validate()
                
                mode = 'ab' if last_id > 0 else 'wb'
                with open(self.db_path, mode) as f:
                    if last_id == 0:
                        f.write(struct.pack('I', 0))  # Initialize last ID
                    
                    f.write(struct.pack('I', new_id))
                    f.write(struct.pack('?', validation))
                    f.write(struct.pack('I', size))
                    f.write(obj_bytes)
                    f.flush()
                    os.fsync(f.fileno())
                    
                    self.update_last_id(new_id)
                
                logger.info(f"Successfully wrote record {new_id}")
                return new_id
            finally:
                self._release_lock()
        except Exception as e:
            logger.error(f"Error writing record: {str(e)}\n{traceback.format_exc()}")
            
            # Attempt to restore from backup if we have one
            if 'backup_path' in locals() and os.path.exists(backup_path):
                try:
                    shutil.copy(backup_path, self.db_path)
                    logger.info("Restored database from backup after write failure")
                except Exception as restore_error:
                    logger.error(f"Failed to restore from backup: {str(restore_error)}")
            
            raise DatabaseError("Failed to write record")

    def write_from_csv(
        self, 
        csv_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """Bulk import records from CSV with progress reporting and error handling."""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Validate file size
        file_size = os.path.getsize(csv_path)
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File size exceeds maximum of {MAX_FILE_SIZE_MB}MB")
        
        try:
            # Create backup before bulk operation
            backup_path = self._create_backup()
            
            # Count records first
            total_records = self._count_csv_records(csv_path)
            if total_records <= 0:
                raise DataValidationError("No valid records found in CSV")
            
            # Read and validate all objects first
            data_objects = self._read_csv(csv_path)
            if not data_objects:
                raise DataValidationError("No valid data objects created from CSV")
            
            last_id = self.get_last_id()
            starting_id = last_id + 1 if last_id > 0 else 1
            
            if not self._acquire_lock():
                raise LockAcquisitionError("Could not acquire lock for bulk import")
            
            try:
                with open(self.db_path, 'ab' if last_id > 0 else 'wb') as f:
                    if last_id == 0:
                        f.write(struct.pack('I', 0))  # Initialize last ID
                    
                    for i, obj in enumerate(data_objects, 1):
                        try:
                            obj_bytes = obj.to_bytes()
                            size = len(obj_bytes)
                            validation = obj.validate()
                            
                            f.write(struct.pack('I', starting_id))
                            f.write(struct.pack('?', validation))
                            f.write(struct.pack('I', size))
                            f.write(obj_bytes)
                            
                            self.update_last_id(starting_id)
                            starting_id += 1
                            
                            if progress_callback:
                                progress_callback(i, total_records)
                        except Exception as e:
                            logger.warning(f"Skipping record due to error: {str(e)}")
                            continue
            finally:
                self._release_lock()
            
            final_id = starting_id - 1
            logger.info(f"Imported {final_id - last_id} records from CSV")
            return final_id
        except Exception as e:
            logger.error(f"CSV import failed: {str(e)}\n{traceback.format_exc()}")
            
            # Attempt to restore from backup if we have one
            if 'backup_path' in locals() and os.path.exists(backup_path):
                try:
                    shutil.copy(backup_path, self.db_path)
                    logger.info("Restored database from backup after import failure")
                except Exception as restore_error:
                    logger.error(f"Failed to restore from backup: {str(restore_error)}")
            
            raise DatabaseError(f"Failed to import from CSV: {str(e)}")

    def _count_csv_records(self, csv_path: str) -> int:
        """Count records in CSV file efficiently with error handling."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Skip empty lines and count
                return sum(1 for line in f if line.strip()) - 1  # Subtract header
        except Exception as e:
            logger.error(f"Error counting CSV records: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Failed to count CSV records")

    def _read_csv(self, csv_path: str) -> List[DataObject]:
        """Read and parse CSV file into DataObjects with comprehensive error handling."""
        data_objects = []
        line_num = 1  # Track line numbers for error reporting
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Detect delimiter if not standard
                sample = f.read(1024)
                f.seek(0)
                
                dialect = csv.Sniffer().sniff(sample)
                if dialect.delimiter != CSV_DELIMITER:
                    logger.warning(f"Detected non-standard delimiter '{dialect.delimiter}' in CSV file")
                
                reader = csv.reader(f, delimiter=CSV_DELIMITER)
                
                # Skip header
                try:
                    header = next(reader)
                    line_num += 1
                except StopIteration:
                    raise DataValidationError("Empty CSV file")
                
                # Process rows in parallel for large files
                if os.path.getsize(csv_path) > 5 * 1024 * 1024:  # 5MB threshold
                    with ThreadPoolExecutor() as executor:
                        futures = []
                        for row in reader:
                            line_num += 1
                            futures.append(executor.submit(self._process_csv_row, row, line_num))
                        
                        for future in as_completed(futures):
                            result = future.result()
                            if result:
                                data_objects.append(result)
                else:
                    for row in reader:
                        line_num += 1
                        result = self._process_csv_row(row, line_num)
                        if result:
                            data_objects.append(result)
        
            if not data_objects:
                raise DataValidationError("No valid records found in CSV")
            
            return data_objects
        except csv.Error as e:
            raise DataValidationError(f"CSV parsing error at line {line_num}: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading CSV: {str(e)}\n{traceback.format_exc()}")
            raise DatabaseError("Failed to read CSV file")

    def _process_csv_row(self, row: List[str], line_num: int) -> Optional[DataObject]:
        """Process a single CSV row with error handling."""
        try:
            if len(row) != len(FIELDS):
                raise DataValidationError(f"Expected {len(FIELDS)} fields, got {len(row)}")
            
            # Skip empty rows
            if not any(field.strip() for field in row):
                return None
            
            return DataObject(row)
        except DataValidationError as e:
            logger.warning(f"Skipping invalid row at line {line_num}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing line {line_num}: {str(e)}")
            return None

def setup_ui():
    """Configure Streamlit UI with enhanced styling and layout."""
    st.set_page_config(
        page_title="Traffic Accidents DB", 
        layout="wide",
        page_icon="🚗",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
            .stProgress > div > div > div > div {
                background-color: #4CAF50;
            }
            .st-bb {
                background-color: #f0f2f6;
            }
            .st-at {
                background-color: #ffffff;
            }
            .reportview-container .main .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
                padding-left: 2rem;
                padding-right: 2rem;
            }
            .sidebar .sidebar-content {
                background-color: #f8f9fa;
                padding: 1.5rem;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 0.5rem;
            }
            .stAlert {
                border-left: 4px solid #4CAF50;
                padding: 1rem;
            }
            .stButton>button {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 0.5rem 1rem;
                border: none;
            }
            .stButton>button:hover {
                background-color: #45a049;
            }
            .stTextInput>div>div>input, 
            .stNumberInput>div>div>input,
            .stTextArea>div>div>textarea,
            .stSelectbox>div>div>select {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 0.5rem;
            }
            .stExpander {
                border: 1px solid #e1e4e8;
                border-radius: 4px;
                margin-bottom: 1rem;
            }
            .stExpander>.streamlit-expanderHeader {
                background-color: #f8f9fa;
                padding: 0.75rem 1rem;
                font-weight: 600;
            }
            .stTab {
                margin-top: 1rem;
            }
            .stTab>.streamlit-tab {
                padding: 0.5rem 1rem;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🚗 Traffic Accidents Database Manager")
    st.caption("A comprehensive system for managing traffic accident records")
    
    try:
        db = TrafficAccidentsDB()
        
        with st.sidebar:
            st.header("Navigation")
            operation = st.radio(
                "Select Operation",
                ["📄 View All Records", "🔍 Search by ID", "📤 Import from CSV", "✍️ Add New Record"],
                label_visibility="visible"
            )
            
            st.divider()
            st.header("Database Info")
            last_id = db.get_last_id()
            st.metric("Last Record ID", last_id if last_id > 0 else "No records")
            
            if operation in ["📄 View All Records", "🔍 Search by ID"]:
                if st.button("🔄 Refresh Database", use_container_width=True):
                    st.experimental_rerun()
            
            st.divider()
            st.header("System Info")
            st.write(f"**Python:** {platform.python_version()}")
            st.write(f"**Streamlit:** {st.__version__}")
            st.write(f"**Database Path:** `{DB_FILE}`")
            st.write(f"**Records:** {len(db.read_all_records())}")
        
        if operation == "📄 View All Records":
            view_all_records(db)
        elif operation == "🔍 Search by ID":
            search_by_id(db)
        elif operation == "📤 Import from CSV":
            import_from_csv(db)
        elif operation == "✍️ Add New Record":
            add_new_record(db)
            
    except DatabaseError as e:
        st.error(f"Database error: {str(e)}")
        logger.error(f"Database error in main: {e}\n{traceback.format_exc()}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in main: {e}\n{traceback.format_exc()}")

def display_record_data(data_obj: DataObject):
    """Display record data in a user-friendly format with error handling."""
    try:
        cols = st.columns(2)
        
        with cols[0]:
            st.subheader("Accident Details")
            st.write(f"**Date:** {getattr(data_obj, 'crash_date', 'N/A')}")
            st.write(f"**Type:** {getattr(data_obj, 'crash_type', 'N/A')}")
            st.write(f"**Traffic Control:** {getattr(data_obj, 'traffic_control_device', 'N/A')}")
            st.write(f"**Weather:** {getattr(data_obj, 'weather_condition',