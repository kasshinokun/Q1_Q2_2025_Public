import streamlit as st
import csv
import os
import struct
from pathlib import Path
import json
from typing import List, Dict, Optional, Union, Callable, Any
import tempfile
import logging
from datetime import datetime, date
import traceback
from concurrent.futures import ThreadPoolExecutor
import hashlib

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

# Constants
DB_DIR = os.path.join(Path.home(), 'Documents', 'Data')
DB_FILE = os.path.join(DB_DIR, 'traffic_accidents.db')
BACKUP_DIR = os.path.join(DB_DIR, 'backups')
CSV_DELIMITER = ';'
MAX_RECORDS_PER_PAGE = 20
MAX_FILE_SIZE_MB = 10
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for file processing

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

class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class DataObject:
    """Represents a traffic accident record with enhanced validation and serialization."""
    
    def __init__(self, row_data: Optional[List[str]] = None):
        # Initialize all fields with type-appropriate default values
        self._initialize_defaults()
        
        if row_data is not None:
            try:
                self._initialize_from_row(row_data)
                if not self.validate():
                    raise DataValidationError("Data validation failed during initialization")
            except Exception as e:
                logger.error(f"Error initializing DataObject: {str(e)}")
                raise DataValidationError(f"Invalid data: {str(e)}")

    def _initialize_defaults(self):
        """Initialize all fields with type-appropriate default values"""
        # String fields
        self.crash_date = ""
        self.traffic_control_device = "Unknown"
        self.weather_condition = "Unknown"
        self.lighting_condition = "Unknown"
        self.first_crash_type = "Unknown"
        self.trafficway_type = "Unknown"
        self.alignment = "Unknown"
        self.roadway_surface_cond = "Unknown"
        self.road_defect = "None"
        self.crash_type = "Unknown"
        self.intersection_related_i = "No"
        self.damage = "Unknown"
        self.prim_contributory_cause = "Unknown"
        self.most_severe_injury = "None"
        
        # Numeric fields
        self.num_units = 0
        self.injuries_total = 0.0
        self.injuries_fatal = 0.0
        self.injuries_incapacitating = 0.0
        self.injuries_non_incapacitating = 0.0
        self.injuries_reported_not_evident = 0.0
        self.injuries_no_indication = 0.0
        self.crash_hour = 0
        self.crash_day_of_week = 1  # Monday
        self.crash_month = 1  # January

    def _initialize_from_row(self, row_data: List[str]):
        """Initialize object from CSV row data with enhanced type conversion and validation."""
        if len(row_data) != len(FIELDS):
            raise DataValidationError(f"Expected {len(FIELDS)} fields, got {len(row_data)}")
        
        # Convert empty strings to None for proper validation
        processed_data = [value if value.strip() else None for value in row_data]
        
        try:
            self.crash_date = self._validate_date(processed_data[0])
            self.traffic_control_device = self._validate_string(processed_data[1], "traffic_control_device")
            self.weather_condition = self._validate_string(processed_data[2], "weather_condition")
            self.lighting_condition = self._validate_string(processed_data[3], "lighting_condition")
            self.first_crash_type = self._validate_string(processed_data[4], "first_crash_type")
            self.trafficway_type = self._validate_string(processed_data[5], "trafficway_type")
            self.alignment = self._validate_string(processed_data[6], "alignment")
            self.roadway_surface_cond = self._validate_string(processed_data[7], "roadway_surface_cond")
            self.road_defect = self._validate_string(processed_data[8], "road_defect")
            self.crash_type = self._validate_string(processed_data[9], "crash_type")
            self.intersection_related_i = self._validate_yes_no(processed_data[10])
            self.damage = self._validate_string(processed_data[11], "damage")
            self.prim_contributory_cause = self._validate_string(processed_data[12], "prim_contributory_cause")
            self.num_units = self._validate_positive_int(processed_data[13], "num_units")
            self.most_severe_injury = self._validate_string(processed_data[14], "most_severe_injury")
            self.injuries_total = self._validate_positive_float(processed_data[15], "injuries_total")
            self.injuries_fatal = self._validate_positive_float(processed_data[16], "injuries_fatal")
            self.injuries_incapacitating = self._validate_positive_float(processed_data[17], "injuries_incapacitating")
            self.injuries_non_incapacitating = self._validate_positive_float(processed_data[18], "injuries_non_incapacitating")
            self.injuries_reported_not_evident = self._validate_positive_float(processed_data[19], "injuries_reported_not_evident")
            self.injuries_no_indication = self._validate_positive_float(processed_data[20], "injuries_no_indication")
            self.crash_hour = self._validate_range(processed_data[21], "crash_hour", 0, 23)
            self.crash_day_of_week = self._validate_range(processed_data[22], "crash_day_of_week", 1, 7)
            self.crash_month = self._validate_range(processed_data[23], "crash_month", 1, 12)
        except Exception as e:
            logger.error(f"Validation error in field initialization: {str(e)}")
            raise DataValidationError(f"Field validation failed: {str(e)}")

    @staticmethod
    def _validate_date(date_str: Optional[str]) -> str:
        """Validate and standardize date format with enhanced checks."""
        if not date_str:
            return ""
        
        try:
            # Try multiple date formats
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y'):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            raise ValueError(f"Invalid date format: {date_str}")
        except Exception as e:
            logger.warning(f"Invalid date '{date_str}': {str(e)}")
            return ""

    @staticmethod
    def _validate_string(value: Optional[str], field_name: str) -> str:
        """Validate string fields with sanitization."""
        if value is None:
            return "Unknown"
        
        value = str(value).strip()
        if not value:
            return "Unknown"
        
        # Basic sanitization
        value = value.replace(';', ',').replace('\n', ' ').replace('\r', '')
        return value[:255]  # Limit string length

    @staticmethod
    def _validate_yes_no(value: Optional[str]) -> str:
        """Validate yes/no fields."""
        if value is None:
            return "No"
        
        value = str(value).strip().lower()
        return "Yes" if value in ('yes', 'y', 'true', '1') else "No"

    @staticmethod
    def _validate_positive_int(value: Optional[str], field_name: str) -> int:
        """Validate positive integers."""
        try:
            num = int(float(value)) if value else 0
            if num < 0:
                raise ValueError(f"{field_name} cannot be negative")
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value '{value}' for {field_name}")
            return 0

    @staticmethod
    def _validate_positive_float(value: Optional[str], field_name: str) -> float:
        """Validate positive floats."""
        try:
            num = float(value) if value else 0.0
            if num < 0:
                raise ValueError(f"{field_name} cannot be negative")
            return round(num, 2)
        except (ValueError, TypeError):
            logger.warning(f"Invalid float value '{value}' for {field_name}")
            return 0.0

    @staticmethod
    def _validate_range(value: Optional[str], field_name: str, min_val: int, max_val: int) -> int:
        """Validate numeric fields within a specific range."""
        try:
            num = int(float(value)) if value else min_val
            if num < min_val or num > max_val:
                raise ValueError(f"{field_name} must be between {min_val} and {max_val}")
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid range value '{value}' for {field_name}")
            return min_val

    def to_bytes(self) -> bytes:
        """Serialize object to bytes using JSON with error handling."""
        try:
            data_dict = {attr: getattr(self, attr) for attr in FIELDS}
            return json.dumps(data_dict, sort_keys=True).encode('utf-8')
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
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
            
            return obj
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise DatabaseError("Invalid data format")
        except Exception as e:
            logger.error(f"Deserialization error: {str(e)}")
            raise DatabaseError("Failed to deserialize record")

    def validate(self) -> bool:
        """Comprehensive validation of the object's fields."""
        try:
            # Required fields validation
            if not self.crash_date:
                raise DataValidationError("Crash date is required")
            
            if not self.crash_type:
                raise DataValidationError("Crash type is required")
            
            if not isinstance(self.num_units, int) or self.num_units < 0:
                raise DataValidationError("Number of units must be a positive integer")
            
            if not isinstance(self.injuries_total, (int, float)) or self.injuries_total < 0:
                raise DataValidationError("Total injuries must be a positive number")
            
            # Date validation
            try:
                datetime.strptime(self.crash_date, '%Y-%m-%d')
            except ValueError:
                raise DataValidationError("Invalid date format (expected YYYY-MM-DD)")
            
            return True
        except DataValidationError as e:
            logger.warning(f"Validation failed: {str(e)}")
            return False

class TrafficAccidentsDB:
    """Enhanced database handler with thread-safe operations, backups, and recovery."""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._ensure_db_directory()
        self._ensure_backup_directory()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists with proper permissions."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            # Set secure permissions (rwx for owner, rx for group/others)
            os.chmod(os.path.dirname(self.db_path), 0o755)
        except Exception as e:
            logger.error(f"Failed to create database directory: {str(e)}")
            raise DatabaseError("Could not initialize database directory")

    def _ensure_backup_directory(self):
        """Ensure the backup directory exists."""
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            os.chmod(BACKUP_DIR, 0o755)
        except Exception as e:
            logger.error(f"Failed to create backup directory: {str(e)}")
            raise DatabaseError("Could not initialize backup directory")

    def _create_backup(self):
        """Create a timestamped backup of the database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
            
            with open(self.db_path, 'rb') as src, open(backup_path, 'wb') as dst:
                while True:
                    chunk = src.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    dst.write(chunk)
            
            logger.info(f"Created database backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise DatabaseError("Could not create database backup")

    def get_last_id(self) -> int:
        """Get the last used ID from the database with error handling."""
        try:
            with self.lock:
                with open(self.db_path, 'rb') as f:
                    id_bytes = f.read(4)
                    return struct.unpack('I', id_bytes)[0] if len(id_bytes) == 4 else 0
        except FileNotFoundError:
            return 0
        except Exception as e:
            logger.error(f"Error getting last ID: {str(e)}")
            raise DatabaseError("Failed to read last ID")

    def update_last_id(self, new_id: int):
        """Safely update the last ID in the database."""
        try:
            with self.lock:
                with open(self.db_path, 'r+b') as f:
                    f.write(struct.pack('I', new_id))
                    f.flush()
                    os.fsync(f.fileno())
        except Exception as e:
            logger.error(f"Error updating last ID: {str(e)}")
            raise DatabaseError("Failed to update last ID")

    def read_all_records(self) -> List[Dict[str, Any]]:
        """Read all records from the database with recovery capabilities."""
        records = []
        try:
            with self.lock:
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
        
            logger.info(f"Successfully read {len(records)} records")
            return records
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.error(f"Error reading records: {str(e)}")
            raise DatabaseError("Failed to read records")

    def read_record_by_id(self, search_id: int) -> Optional[Dict[str, Any]]:
        """Read a specific record by ID with binary search for efficiency."""
        if search_id <= 0:
            raise ValueError("ID must be positive")
        
        try:
            with self.lock:
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
            
            return None
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error searching for record {search_id}: {str(e)}")
            raise DatabaseError(f"Failed to search for record {search_id}")

    def _read_next_record(self, file_obj) -> Optional[Dict[str, Any]]:
        """Read the next record from the file with robust error handling."""
        try:
            # Read record header
            id_bytes = file_obj.read(4)
            if not id_bytes:
                return None
            
            validation_byte = file_obj.read(1)
            if not validation_byte:
                return None
            
            size_bytes = file_obj.read(4)
            if not size_bytes:
                return None
            
            # Unpack binary data
            try:
                record_id = struct.unpack('I', id_bytes)[0]
                validation = struct.unpack('?', validation_byte)[0]
                size = struct.unpack('I', size_bytes)[0]
                
                # Validate size before reading
                if size > 10 * 1024 * 1024:  # 10MB max record size
                    raise DatabaseError(f"Record size {size} exceeds maximum allowed")
                
                data_bytes = file_obj.read(size)
                if len(data_bytes) != size:
                    return None
                
                # Verify data checksum
                checksum = hashlib.md5(data_bytes).hexdigest()
                
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
            logger.error(f"Record read error: {str(e)}")
            raise DatabaseError(f"Failed to read record: {str(e)}")

    def write_record(self, data_object: DataObject) -> int:
        """Write a single record to the database with file locking and backup."""
        if not isinstance(data_object, DataObject):
            raise TypeError("Expected DataObject instance")
        
        try:
            # Create backup before writing
            self._create_backup()
            
            with self.lock:
                last_id = self.get_last_id()
                new_id = last_id + 1 if last_id > 0 else 1
                
                obj_bytes = data_object.to_bytes()
                size = len(obj_bytes)
                validation = data_object.validate()
                
                mode = 'ab' if last_id > 0 else 'wb'
                with open(self.db_path, mode) as f:
                    if last_id == 0:
                        f.write(struct.pack('I', 0))
                    
                    f.write(struct.pack('I', new_id))
                    f.write(struct.pack('?', validation))
                    f.write(struct.pack('I', size))
                    f.write(obj_bytes)
                    
                    self.update_last_id(new_id)
                
                logger.info(f"Successfully wrote record {new_id}")
                return new_id
        except Exception as e:
            logger.error(f"Error writing record: {str(e)}")
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
            self._create_backup()
            
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
            
            with self.lock:
                with open(self.db_path, 'ab' if last_id > 0 else 'wb') as f:
                    if last_id == 0:
                        f.write(struct.pack('I', 0))
                    
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
            
            final_id = starting_id - 1
            logger.info(f"Imported {final_id - last_id} records from CSV")
            return final_id
        except Exception as e:
            logger.error(f"CSV import failed: {str(e)}")
            raise DatabaseError(f"Failed to import from CSV: {str(e)}")

    def _count_csv_records(self, csv_path: str) -> int:
        """Count records in CSV file efficiently with error handling."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Skip empty lines and count
                return sum(1 for line in f if line.strip()) - 1  # Subtract header
        except Exception as e:
            logger.error(f"Error counting CSV records: {str(e)}")
            raise DatabaseError("Failed to count CSV records")

    def _read_csv(self, csv_path: str) -> List[DataObject]:
        """Read and parse CSV file into DataObjects with comprehensive error handling."""
        data_objects = []
        line_num = 1  # Track line numbers for error reporting
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=CSV_DELIMITER)
                
                # Skip header
                try:
                    header = next(reader)
                    line_num += 1
                except StopIteration:
                    raise DataValidationError("Empty CSV file")
                
                # Process rows
                for row in reader:
                    line_num += 1
                    
                    try:
                        if len(row) != len(FIELDS):
                            raise DataValidationError(
                                f"Expected {len(FIELDS)} fields, got {len(row)}"
                            )
                        
                        # Skip empty rows
                        if not any(field.strip() for field in row):
                            continue
                        
                        data_objects.append(DataObject(row))
                    except DataValidationError as e:
                        logger.warning(
                            f"Skipping invalid row at line {line_num}: {str(e)}"
                        )
                        continue
                    except Exception as e:
                        logger.error(
                            f"Unexpected error processing line {line_num}: {str(e)}"
                        )
                        continue
        
            if not data_objects:
                raise DataValidationError("No valid records found in CSV")
            
            return data_objects
        except csv.Error as e:
            raise DataValidationError(f"CSV parsing error at line {line_num}: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading CSV: {str(e)}")
            raise DatabaseError("Failed to read CSV file")

def setup_ui():
    """Configure Streamlit UI with enhanced styling and layout."""
    st.set_page_config(
        page_title="Traffic Accidents DB", 
        layout="wide",
        page_icon="🚗"
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
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .sidebar .sidebar-content {
                background-color: #f8f9fa;
            }
            h1 {
                color: #2c3e50;
            }
            .stAlert {
                border-left: 4px solid #4CAF50;
            }
            .st-b7 {
                background-color: #4CAF50 !important;
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
        logger.error(f"Database error in main: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in main: {e}")
def display_record_data(data_obj: DataObject):
    """Display record data in a user-friendly format with error handling."""
    try:
        cols = st.columns(2)
        
        with cols[0]:
            st.subheader("Accident Details")
            st.write(f"**Date:** {getattr(data_obj, 'crash_date', 'N/A')}")
            st.write(f"**Type:** {getattr(data_obj, 'crash_type', 'N/A')}")
            st.write(f"**Traffic Control:** {getattr(data_obj, 'traffic_control_device', 'N/A')}")
            st.write(f"**Weather:** {getattr(data_obj, 'weather_condition', 'N/A')}")
            st.write(f"**Lighting:** {getattr(data_obj, 'lighting_condition', 'N/A')}")
            st.write(f"**First Crash Type:** {getattr(data_obj, 'first_crash_type', 'N/A')}")
            st.write(f"**Road Surface:** {getattr(data_obj, 'roadway_surface_cond', 'N/A')}")
        
        with cols[1]:
            st.subheader("Impact Details")
            st.write(f"**Units Involved:** {getattr(data_obj, 'num_units', 0)}")
            st.write(f"**Total Injuries:** {getattr(data_obj, 'injuries_total', 0.0)}")
            st.write(f"**Fatal Injuries:** {getattr(data_obj, 'injuries_fatal', 0.0)}")
            st.write(f"**Incapacitating:** {getattr(data_obj, 'injuries_incapacitating', 0.0)}")
            st.write(f"**Non-Incapacitating:** {getattr(data_obj, 'injuries_non_incapacitating', 0.0)}")
            st.write(f"**Primary Cause:** {getattr(data_obj, 'prim_contributory_cause', 'N/A')}")
            st.write(f"**Intersection Related:** {getattr(data_obj, 'intersection_related_i', 'No')}")
    except Exception as e:
        logger.error(f"Error displaying record: {str(e)}")
        st.error("Failed to display record details")

def view_all_records(db: TrafficAccidentsDB):
    """Display all records with pagination, filtering, and error handling."""
    st.header("All Records")
    
    try:
        with st.spinner("Loading records..."):
            records = db.read_all_records()
        
        if not records:
            st.warning("No records found in the database.")
            return
        
        st.success(f"Found {len(records)} records")
        
        # Pagination controls
        col1, col2 = st.columns([1, 3])
        with col1:
            page_size = st.selectbox(
                "Records per page",
                [10, 20, 50, 100],
                index=1,
                key="page_size"
            )
            
            total_pages = max(1, (len(records) // page_size + (1 if len(records) % page_size else 0)))
            page = st.number_input(
                "Page", 
                min_value=1, 
                max_value=total_pages, 
                value=1,
                key="page_num"
            )
        
        # Display records for current page
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, len(records))
        
        for record in records[start_idx:end_idx]:
            with st.expander(
                f"📝 Record ID: {record['id']} "
                f"({'✅ Valid' if record['validation'] else '❌ Invalid'})"
            ):
                try:
                    tab1, tab2 = st.tabs(["Data View", "Raw Data"])
                    with tab1:
                        display_record_data(record['data'])
                    with tab2:
                        record_data = {k: getattr(record['data'], k, None) for k in FIELDS}
                        st.json(record_data)
                except Exception as e:
                    st.error(f"Error displaying record {record['id']}: {str(e)}")
        
        st.caption(f"Showing records {start_idx + 1}-{end_idx} of {len(records)}")
    except Exception as e:
        logger.error(f"Error in view_all_records: {str(e)}")
        st.error("Failed to load records. Please check the logs for details.")

def search_by_id(db: TrafficAccidentsDB):
    """Search for records by ID with enhanced UI and error handling."""
    st.header("Search Record by ID")
    
    try:
        last_id = db.get_last_id()
        col1, col2 = st.columns([1, 3])
        
        with col1:
            search_id = st.number_input(
                "Enter Record ID", 
                min_value=1, 
                max_value=last_id if last_id > 0 else None,
                step=1,
                help=f"Enter ID between 1 and {last_id if last_id > 0 else 'N/A'}"
            )
            
            if st.button("🔎 Search", key="search_button"):
                if last_id > 0 and search_id > last_id:
                    st.session_state.search_error = f"ID {search_id} exceeds last record ID ({last_id})"
                    st.session_state.search_result = None
                else:
                    with st.spinner("Searching..."):
                        try:
                            record = db.read_record_by_id(search_id)
                            st.session_state.search_result = record
                            st.session_state.search_error = None if record else f"Record {search_id} not found"
                        except Exception as e:
                            st.session_state.search_error = f"Search failed: {str(e)}"
                            st.session_state.search_result = None
        
        with col2:
            if 'search_result' in st.session_state:
                if st.session_state.search_result:
                    record = st.session_state.search_result
                    st.success(f"Found record ID: {record['id']}")
                    
                    tab1, tab2 = st.tabs(["Data View", "Raw JSON"])
                    with tab1:
                        display_record_data(record['data'])
                    with tab2:
                        record_data = {k: getattr(record['data'], k, None) for k in FIELDS}
                        st.json(record_data)
                elif 'search_error' in st.session_state and st.session_state.search_error:
                    st.error(st.session_state.search_error)
    except Exception as e:
        logger.error(f"Error in search_by_id: {str(e)}")
        st.error("Failed to perform search. Please check the logs for details.")

def import_from_csv(db: TrafficAccidentsDB):
    """Handle CSV import with progress tracking and error handling."""
    st.header("Import Records from CSV")
    
    try:
        uploaded_file = st.file_uploader(
            "Choose a CSV file", 
            type="csv",
            help=f"Select a CSV file (max {MAX_FILE_SIZE_MB}MB) with traffic accident data"
        )
        
        if uploaded_file is not None:
            # Validate file size
            if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"File size exceeds maximum of {MAX_FILE_SIZE_MB}MB")
                return
            
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            if st.button("💾 Import Records", key="import_button"):
                try:
                    # Setup progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    result_container = st.empty()
                    
                    def update_progress(current: int, total: int):
                        """Update progress bar and status text."""
                        progress = min(int((current / total) * 100), 100)
                        progress_bar.progress(progress)
                        status_text.markdown(
                            f"**Progress:** {current}/{total} records ({progress}%)  \n"
                            f"**Current ID:** {db.get_last_id() + 1}"
                        )
                    
                    # Perform import
                    with st.spinner("Starting import..."):
                        start_time = datetime.now()
                        last_id = db.write_from_csv(tmp_path, update_progress)
                        duration = (datetime.now() - start_time).total_seconds()
                    
                    # Final update
                    progress_bar.progress(100)
                    status_text.empty()
                    imported_count = last_id - db.get_last_id() + 1
                    result_container.success(
                        f"✅ Successfully imported {imported_count} records  \n"
                        f"**Last ID:** {last_id}  \n"
                        f"**Time elapsed:** {duration:.2f} seconds"
                    )
                    st.balloons()
                    st.rerun()
                
                except Exception as e:
                    progress_bar.empty()
                    status_text.error(f"❌ Import failed: {str(e)}")
                    logger.exception("CSV import failed")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Error in import_from_csv: {str(e)}")
        st.error("Failed to process CSV import. Please check the logs for details.")

def add_new_record(db: TrafficAccidentsDB):
    """Form for adding new records with enhanced validation and error handling."""
    st.header("Add New Accident Record")
    
    try:
        with st.form("record_form", clear_on_submit=True):
            cols = st.columns(2)
            
            with cols[0]:
                st.subheader("Accident Details")
                crash_date = st.date_input(
                    "Crash Date*",
                    value=date.today(),
                    help="Date of the accident"
                )
                crash_type = st.text_input(
                    "Crash Type*",
                    help="Type of collision (e.g., rear-end, side-swipe)"
                )
                traffic_control_device = st.selectbox(
                    "Traffic Control Device",
                    ["Unknown", "Traffic Signal", "Stop Sign", "Yield Sign", "None"],
                    index=0
                )
                weather_condition = st.selectbox(
                    "Weather Condition",
                    ["Unknown", "Clear", "Rain", "Snow", "Fog", "Severe Crosswinds"],
                    index=0
                )
                lighting_condition = st.selectbox(
                    "Lighting Condition",
                    ["Unknown", "Daylight", "Dark - Lighted", "Dark - Not Lighted", "Dusk/Dawn"],
                    index=0
                )
                first_crash_type = st.text_input(
                    "First Crash Type",
                    help="Initial point of impact"
                )
            
            with cols[1]:
                st.subheader("Impact Details")
                num_units = st.number_input(
                    "Number of Units*",
                    min_value=0,
                    max_value=100,
                    value=1,
                    help="Number of vehicles involved"
                )
                injuries_total = st.number_input("Total Injuries*", min_value=0.0, value=0.0)
            injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0, value=0.0)
            injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0, value=0.0)
            injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0, value=0.0)
            injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0, value=0.0)
            injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0, value=0.0)
            
            st.subheader("Temporal Details")
            crash_hour = st.slider("Crash Hour", 0, 23, 12)
            crash_day_of_week = st.slider("Day of Week (1=Monday)", 1, 7, 1)
            crash_month = st.slider("Month", 1, 12, datetime.now().month)
        
    submitted = st.form_submit_button("💾 Save Record", use_container_width=True)
    
    if submitted:
        if not all([crash_date, crash_type, num_units is not None, injuries_total is not None]):
            st.error("Please fill all required fields (*)")
        else:
            try:
                # Create mock row data with empty values for unused fields
                row_data = [""] * len(FIELDS)
                row_data[0] = crash_date.strftime('%Y-%m-%d')  # crash_date
                row_data[1] = traffic_control_device  # traffic_control_device
                row_data[2] = weather_condition  # weather_condition
                row_data[3] = lighting_condition  # lighting_condition
                row_data[4] = first_crash_type  # first_crash_type
                row_data[7] = roadway_surface_cond  # roadway_surface_cond
                row_data[8] = road_defect  # road_defect
                row_data[9] = crash_type  # crash_type
                row_data[13] = str(num_units)  # num_units
                row_data[15] = str(injuries_total)  # injuries_total
                row_data[16] = str(injuries_fatal)  # injuries_fatal
                row_data[17] = str(injuries_incapacitating)  # injuries_incapacitating
                row_data[18] = str(injuries_non_incapacitating)  # injuries_non_incapacitating
                row_data[19] = str(injuries_reported_not_evident)  # injuries_reported_not_evident
                row_data[20] = str(injuries_no_indication)  # injuries_no_indication
                row_data[21] = str(crash_hour)  # crash_hour
                row_data[22] = str(crash_day_of_week)  # crash_day_of_week
                row_data[23] = str(crash_month)  # crash_month
                
                new_id = db.write_record(DataObject(row_data))
                st.success(f"Record saved successfully with ID: {new_id}")
                st.balloons()
            except DatabaseError as e:
                st.error(f"Error saving record: {str(e)}")
                logger.error(f"Failed to save new record: {e}")
            except Exception as e:
                st.error(f"Unexpected error saving record: {str(e)}")
                logger.error(f"Unexpected error saving new record: {e}")
    except Exception as e:
        logger.error(f"Error in add_new_record: {str(e)}")
        st.error("Failed to add new record. Please check the logs for details.")

if __name__ == "__main__":
    setup_ui()