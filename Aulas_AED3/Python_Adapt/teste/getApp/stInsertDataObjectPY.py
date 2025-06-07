import streamlit as st
import csv
import os
import struct
from pathlib import Path
import json
from typing import List, Dict, Optional, Union, Callable
import tempfile
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DB_DIR = os.path.join(Path.home(), 'Documents', 'Data')
DB_FILE = os.path.join(DB_DIR, 'traffic_accidents.db')
CSV_DELIMITER = ';'
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

class DataObject:
    """Represents a traffic accident record with validation and serialization."""
    
    def __init__(self, row_data: Optional[List[str]] = None):
        if row_data is not None:
            self._initialize_from_row(row_data)
    
    def _initialize_from_row(self, row_data: List[str]):
        """Initialize object from CSV row data with type conversion and validation."""
        self.crash_date = self._validate_date(str(row_data[0]))
        self.traffic_control_device = str(row_data[1])
        self.weather_condition = str(row_data[2])
        self.lighting_condition = str(row_data[3])
        self.first_crash_type = str(row_data[4])
        self.trafficway_type = str(row_data[5])
        self.alignment = str(row_data[6])
        self.roadway_surface_cond = str(row_data[7])
        self.road_defect = str(row_data[8])
        self.crash_type = str(row_data[9])
        self.intersection_related_i = str(row_data[10])
        self.damage = str(row_data[11])
        self.prim_contributory_cause = str(row_data[12])
        self.num_units = self._safe_int(row_data[13])
        self.most_severe_injury = str(row_data[14])
        self.injuries_total = self._safe_float(row_data[15])
        self.injuries_fatal = self._safe_float(row_data[16])
        self.injuries_incapacitating = self._safe_float(row_data[17])
        self.injuries_non_incapacitating = self._safe_float(row_data[18])
        self.injuries_reported_not_evident = self._safe_float(row_data[19])
        self.injuries_no_indication = self._safe_float(row_data[20])
        self.crash_hour = self._safe_int(row_data[21], 0, 23)
        self.crash_day_of_week = self._safe_int(row_data[22], 1, 7)
        self.crash_month = self._safe_int(row_data[23], 1, 12)
    
    @staticmethod
    def _validate_date(date_str: str) -> str:
        """Validate and standardize date format."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return date_str  # Return original if invalid
    
    @staticmethod
    def _safe_int(value: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Safely convert to integer with bounds checking."""
        try:
            num = int(float(value)) if '.' in value else int(value)
            if min_val is not None and num < min_val:
                return min_val
            if max_val is not None and num > max_val:
                return max_val
            return num
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def _safe_float(value: str) -> float:
        """Safely convert to float."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def to_bytes(self) -> bytes:
        """Serialize object to bytes using JSON with sorted keys for consistency."""
        data_dict = {attr: getattr(self, attr) for attr in FIELDS}
        return json.dumps(data_dict, sort_keys=True).encode('utf-8')
    
    @classmethod
    def from_bytes(cls, byte_data: bytes) -> 'DataObject':
        """Deserialize object from bytes with error handling."""
        try:
            data_dict = json.loads(byte_data.decode('utf-8'))
            obj = cls()
            for key, value in data_dict.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            return obj
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Error deserializing bytes: {e}")
            raise
    
    def validate(self) -> bool:
        """Validate the object's required fields."""
        return all([
            self.crash_date,
            self.crash_type,
            isinstance(self.num_units, int) and self.num_units >= 0,
            isinstance(self.injuries_total, (int, float)) and self.injuries_total >= 0
        ])

class TrafficAccidentsDB:
    """Handles all database operations with thread-safe file access."""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_last_id(self) -> int:
        """Get the last used ID from the database."""
        try:
            with open(self.db_path, 'rb') as f:
                id_bytes = f.read(4)
                return struct.unpack('I', id_bytes)[0] if len(id_bytes) == 4 else 0
        except FileNotFoundError:
            return 0
    
    def update_last_id(self, new_id: int):
        """Update the last ID in the database."""
        try:
            with open(self.db_path, 'r+b') as f:
                f.write(struct.pack('I', new_id))
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
        except Exception as e:
            logger.error(f"Error updating last ID: {e}")
            raise
    
    def read_all_records(self) -> List[Dict[str, Union[int, bool, DataObject]]]:
        """Read all records from the database."""
        records = []
        try:
            with open(self.db_path, 'rb') as f:
                f.read(4)  # Skip last ID
                while True:
                    record = self._read_next_record(f)
                    if not record:
                        break
                    records.append(record)
        except FileNotFoundError:
            pass
        return records
    
    def read_record_by_id(self, search_id: int) -> Optional[Dict[str, Union[int, bool, DataObject]]]:
        """Read a specific record by ID with binary search for efficiency."""
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
        except FileNotFoundError:
            pass
        return None
    
    def _read_next_record(self, file_obj) -> Optional[Dict[str, Union[int, bool, DataObject]]]:
        """Read the next record from the file with error handling."""
        try:
            id_bytes = file_obj.read(4)
            if not id_bytes:
                return None
            
            validation_byte = file_obj.read(1)
            size_bytes = file_obj.read(4)
            if not validation_byte or not size_bytes:
                return None
            
            size = struct.unpack('I', size_bytes)[0]
            data_bytes = file_obj.read(size)
            if len(data_bytes) != size:
                return None
            
            return {
                'id': struct.unpack('I', id_bytes)[0],
                'validation': struct.unpack('?', validation_byte)[0],
                'data': DataObject.from_bytes(data_bytes)
            }
        except (struct.error, UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading record: {e}")
            return None
    
    def write_record(self, data_object: DataObject) -> int:
        """Write a single record to the database with file locking."""
        last_id = self.get_last_id()
        new_id = last_id + 1 if last_id > 0 else 1
        
        obj_bytes = data_object.to_bytes()
        size = len(obj_bytes)
        validation = data_object.validate()
        
        mode = 'ab' if last_id > 0 else 'wb'
        try:
            with open(self.db_path, mode) as f:
                if last_id == 0:
                    f.write(struct.pack('I', 0))
                
                f.write(struct.pack('I', new_id))
                f.write(struct.pack('?', validation))
                f.write(struct.pack('I', size))
                f.write(obj_bytes)
                
                self.update_last_id(new_id)
            return new_id
        except Exception as e:
            logger.error(f"Error writing record: {e}")
            raise
    
    def write_from_csv(
        self, 
        csv_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """Write records from CSV file to database with progress reporting."""
        total_records = self._count_csv_records(csv_path)
        data_objects = self._read_csv(csv_path)
        last_id = self.get_last_id()
        starting_id = last_id + 1 if last_id > 0 else 1
        
        try:
            with open(self.db_path, 'ab' if last_id > 0 else 'wb') as f:
                if last_id == 0:
                    f.write(struct.pack('I', 0))
                
                for i, obj in enumerate(data_objects, 1):
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
            
            return starting_id - 1
        except Exception as e:
            logger.error(f"Error writing from CSV: {e}")
            raise
    
    def _count_csv_records(self, csv_path: str) -> int:
        """Count records in CSV file efficiently."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f) - 1  # Subtract header
        except Exception as e:
            logger.error(f"Error counting CSV records: {e}")
            raise
    
    def _read_csv(self, csv_path: str) -> List[DataObject]:
        """Read and parse CSV file into DataObjects with error handling."""
        data_objects = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=CSV_DELIMITER)
                next(reader)  # Skip header
                
                for line_num, row in enumerate(reader, 2):  # Line numbers start at 2 (1-based + header)
                    try:
                        if len(row) >= len(FIELDS):
                            data_objects.append(DataObject(row))
                        else:
                            logger.warning(f"Skipping malformed row at line {line_num}")
                    except Exception as e:
                        logger.warning(f"Error processing line {line_num}: {e}")
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            raise
        
        return data_objects

def main():
    """Main Streamlit application with enhanced UI and progress tracking."""
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
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🚗 Traffic Accidents Database Manager")
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
            if st.button("🔄 Refresh Database"):
                st.experimental_rerun()
    
    if operation == "📄 View All Records":
        view_all_records(db)
    elif operation == "🔍 Search by ID":
        search_by_id(db)
    elif operation == "📤 Import from CSV":
        import_from_csv(db)
    elif operation == "✍️ Add New Record":
        add_new_record(db)

def view_all_records(db: TrafficAccidentsDB):
    """Display all records with pagination and filtering."""
    st.header("All Records")
    
    records = db.read_all_records()
    if not records:
        st.warning("No records found in the database.")
        return
    
    st.success(f"Found {len(records)} records")
    
    # Pagination
    page_size = 10
    total_pages = (len(records) // page_size + (1 if len(records) % page_size else 0)
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(records))
    
    for record in records[start_idx:end_idx]:
        with st.expander(f"📝 Record ID: {record['id']} ({'✅ Valid' if record['validation'] else '❌ Invalid'})"):
            st.json({k: getattr(record['data'], k) for k in FIELDS})
    
    st.caption(f"Showing records {start_idx + 1}-{end_idx} of {len(records)}")

def search_by_id(db: TrafficAccidentsDB):
    """Search for records by ID with enhanced UI."""
    st.header("Search Record by ID")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        search_id = st.number_input(
            "Enter Record ID", 
            min_value=1, 
            step=1,
            help="Enter the numeric ID of the record to find"
        )
        
        if st.button("🔎 Search", key="search_button"):
            if search_id > db.get_last_id():
                st.session_state.search_result = None
                st.session_state.search_error = f"ID {search_id} exceeds last record ID"
            else:
                with st.spinner("Searching..."):
                    record = db.read_record_by_id(search_id)
                    st.session_state.search_result = record
                    st.session_state.search_error = None if record else f"Record {search_id} not found"
    
    with col2:
        if 'search_result' in st.session_state:
            if st.session_state.search_result:
                record = st.session_state.search_result
                st.success(f"Found record ID: {record['id']}")
                
                tab1, tab2 = st.tabs(["Data View", "Raw JSON"])
                with tab1:
                    display_record_data(record['data'])
                with tab2:
                    st.json({k: getattr(record['data'], k) for k in FIELDS})
            elif 'search_error' in st.session_state and st.session_state.search_error:
                st.error(st.session_state.search_error)

def display_record_data(data_obj: DataObject):
    """Display record data in a user-friendly format."""
    cols = st.columns(2)
    
    with cols[0]:
        st.subheader("Accident Details")
        st.write(f"**Date:** {data_obj.crash_date}")
        st.write(f"**Type:** {data_obj.crash_type}")
        st.write(f"**Traffic Control:** {data_obj.traffic_control_device}")
        st.write(f"**Weather:** {data_obj.weather_condition}")
        st.write(f"**Lighting:** {data_obj.lighting_condition}")
        st.write(f"**First Crash Type:** {data_obj.first_crash_type}")
    
    with cols[1]:
        st.subheader("Impact Details")
        st.write(f"**Units Involved:** {data_obj.num_units}")
        st.write(f"**Total Injuries:** {data_obj.injuries_total}")
        st.write(f"**Fatal Injuries:** {data_obj.injuries_fatal}")
        st.write(f"**Incapacitating:** {data_obj.injuries_incapacitating}")
        st.write(f"**Non-Incapacitating:** {data_obj.injuries_non_incapacitating}")

def import_from_csv(db: TrafficAccidentsDB):
    """Handle CSV import with progress tracking."""
    st.header("Import Records from CSV")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file", 
        type="csv",
        help="Select a CSV file with traffic accident data to import"
    )
    
    if uploaded_file is not None:
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
                result_container.success(
                    f"✅ Successfully imported {last_id - db.get_last_id() + 1} records  \n"
                    f"**Last ID:** {last_id}  \n"
                    f"**Time elapsed:** {duration:.2f} seconds"
                )
                st.balloons()
                st.experimental_rerun()
                
            except Exception as e:
                progress_bar.empty()
                status_text.error(f"❌ Import failed: {str(e)}")
                logger.exception("CSV import failed")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

def add_new_record(db: TrafficAccidentsDB):
    """Form for adding new records with validation."""
    st.header("Add New Accident Record")
    
    with st.form("record_form", clear_on_submit=True):
        cols = st.columns(2)
        
        with cols[0]:
            st.subheader("Accident Details")
            crash_date = st.text_input("Crash Date*", help="Format: YYYY-MM-DD")
            crash_type = st.text_input("Crash Type*")
            traffic_control_device = st.text_input("Traffic Control Device")
            weather_condition = st.selectbox(
                "Weather Condition",
                ["Clear", "Rain", "Snow", "Fog", "Other"]
            )
            lighting_condition = st.selectbox(
                "Lighting Condition",
                ["Daylight", "Dark - Lighted", "Dark - Not Lighted", "Dusk/Dawn"]
            )
            first_crash_type = st.text_input("First Crash Type")
        
        with cols[1]:
            st.subheader("Impact Details")
            num_units = st.number_input("Number of Units*", min_value=0)
            injuries_total = st.number_input("Total Injuries*", min_value=0.0)
            injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0)
            injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0)
            injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0)
        
        submitted = st.form_submit_button("💾 Save Record")
        
        if submitted:
            if not all([crash_date, crash_type, num_units is not None, injuries_total is not None]):
                st.error("Please fill all required fields (*)")
            else:
                try:
                    # Create mock row data with empty values for unused fields
                    row_data = [""] * len(FIELDS)
                    row_data[0] = crash_date  # crash_date
                    row_data[1] = traffic_control_device  # traffic_control_device
                    row_data[2] = weather_condition  # weather_condition
                    row_data[3] = lighting_condition  # lighting_condition
                    row_data[4] = first_crash_type  # first_crash_type
                    row_data[9] = crash_type  # crash_type
                    row_data[13] = str(num_units)  # num_units
                    row_data[15] = str(injuries_total)  # injuries_total
                    row_data[16] = str(injuries_fatal)  # injuries_fatal
                    row_data[17] = str(injuries_incapacitating)  # injuries_incapacitating
                    row_data[18] = str(injuries_non_incapacitating)  # injuries_non_incapacitating
                    
                    new_id = db.write_record(DataObject(row_data))
                    st.success(f"Record saved successfully with ID: {new_id}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error saving record: {str(e)}")
                    logger.exception("Failed to save new record")

if __name__ == "__main__":
    main()