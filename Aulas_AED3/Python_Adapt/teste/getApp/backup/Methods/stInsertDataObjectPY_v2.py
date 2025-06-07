import streamlit as st
import csv
import os
import struct
from pathlib import Path
import json
from typing import List, Dict, Optional, Union
import tempfile
import logging

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
    """Represents a traffic accident record with validation."""
    
    def __init__(self, row_data: Optional[List[str]] = None):
        if row_data is not None:
            self._initialize_from_row(row_data)
    
    def _initialize_from_row(self, row_data: List[str]):
        """Initialize object from CSV row data with type conversion."""
        self.crash_date = str(row_data[0])
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
    def _safe_int(value: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Safely convert to integer with optional bounds checking."""
        try:
            num = int(value)
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
        """Serialize object to bytes using JSON."""
        data_dict = {attr: getattr(self, attr) for attr in FIELDS}
        return json.dumps(data_dict).encode('utf-8')
    
    @classmethod
    def from_bytes(cls, byte_data: bytes) -> 'DataObject':
        """Deserialize object from bytes."""
        data_dict = json.loads(byte_data.decode('utf-8'))
        obj = cls()
        for key, value in data_dict.items():
            setattr(obj, key, value)
        return obj
    
    def validate(self) -> bool:
        """Validate the object's data."""
        return all([
            self.crash_date,
            self.crash_type,
            self.num_units >= 0,
            self.injuries_total >= 0
        ])

class TrafficAccidentsDB:
    """Handles all database operations."""
    
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
        """Read a specific record by ID."""
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
        """Read the next record from the file."""
        id_bytes = file_obj.read(4)
        if not id_bytes:
            return None
        
        return {
            'id': struct.unpack('I', id_bytes)[0],
            'validation': struct.unpack('?', file_obj.read(1))[0],
            'data': DataObject.from_bytes(file_obj.read(struct.unpack('I', file_obj.read(4))[0]))
        }
    
    def write_record(self, data_object: DataObject) -> int:
        """Write a single record to the database."""
        last_id = self.get_last_id()
        new_id = last_id + 1 if last_id > 0 else 1
        
        obj_bytes = data_object.to_bytes()
        size = len(obj_bytes)
        validation = data_object.validate()
        
        mode = 'ab' if last_id > 0 else 'wb'
        try:
            with open(self.db_path, mode) as f:
                if last_id == 0:
                    f.write(struct.pack('I', 0))  # Placeholder for last ID
                
                f.write(struct.pack('I', new_id))
                f.write(struct.pack('?', validation))
                f.write(struct.pack('I', size))
                f.write(obj_bytes)
                
                self.update_last_id(new_id)
            return new_id
        except Exception as e:
            logger.error(f"Error writing record: {e}")
            raise
    
    def write_from_csv(self, csv_path: str) -> int:
        """Write records from CSV file to database."""
        data_objects = self._read_csv(csv_path)
        last_id = self.get_last_id()
        starting_id = last_id + 1 if last_id > 0 else 1
        
        try:
            with open(self.db_path, 'ab' if last_id > 0 else 'wb') as f:
                if last_id == 0:
                    f.write(struct.pack('I', 0))
                
                for obj in data_objects:
                    obj_bytes = obj.to_bytes()
                    size = len(obj_bytes)
                    validation = obj.validate()
                    
                    f.write(struct.pack('I', starting_id))
                    f.write(struct.pack('?', validation))
                    f.write(struct.pack('I', size))
                    f.write(obj_bytes)
                    
                    self.update_last_id(starting_id)
                    starting_id += 1
            
            return starting_id - 1
        except Exception as e:
            logger.error(f"Error writing from CSV: {e}")
            raise
    
    def _read_csv(self, csv_path: str) -> List[DataObject]:
        """Read and parse CSV file into DataObjects."""
        data_objects = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=CSV_DELIMITER)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= len(FIELDS):  # Basic validation
                        data_objects.append(DataObject(row))
                    else:
                        logger.warning(f"Skipping malformed row: {row}")
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            raise
        return data_objects

# Streamlit UI
def main():
    st.set_page_config(page_title="Traffic Accidents DB", layout="wide")
    st.title("🚗 Traffic Accidents Database Manager")
    
    db = TrafficAccidentsDB()
    
    with st.sidebar:
        st.header("Navigation")
        operation = st.radio(
            "Select Operation",
            ["📄 View All Records", "🔍 Search by ID", "📤 Import from CSV", "✍️ Add New Record"]
        )
        st.divider()
        st.header("Database Info")
        last_id = db.get_last_id()
        st.metric("Last Record ID", last_id if last_id > 0 else "No records")
    
    if operation == "📄 View All Records":
        st.header("All Records")
        if st.button("🔄 Refresh Data"):
            st.experimental_rerun()
        
        records = db.read_all_records()
        if not records:
            st.warning("No records found in the database.")
        else:
            st.success(f"Found {len(records)} records")
            for record in records:
                with st.expander(f"📝 Record ID: {record['id']} ({'✅ Valid' if record['validation'] else '❌ Invalid'})"):
                    st.json({k: getattr(record['data'], k) for k in FIELDS})
    
    elif operation == "🔍 Search by ID":
        st.header("Search Record by ID")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            search_id = st.number_input("Enter Record ID", min_value=1, step=1)
            if st.button("🔎 Search"):
                record = db.read_record_by_id(search_id)
                if record:
                    st.session_state.current_record = record
        
        if 'current_record' in st.session_state and st.session_state.current_record:
            record = st.session_state.current_record
            with col2:
                st.success(f"Found record ID: {record['id']}")
                st.json({k: getattr(record['data'], k) for k in FIELDS})
        else:
            col2.warning("No record found with that ID")
    
    elif operation == "📤 Import from CSV":
        st.header("Import Records from CSV")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            if st.button("💾 Import Records"):
                try:
                    with st.spinner("Importing records..."):
                        last_id = db.write_from_csv(tmp_path)
                    st.success(f"Successfully imported records up to ID {last_id}")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error during import: {str(e)}")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    elif operation == "✍️ Add New Record":
        st.header("Add New Accident Record")
        
        with st.form("record_form", clear_on_submit=True):
            cols = st.columns(2)
            
            # Form fields organized in two columns
            with cols[0]:
                st.subheader("Accident Details")
                crash_date = st.text_input("Crash Date*", help="Format: YYYY-MM-DD")
                crash_type = st.text_input("Crash Type*")
                traffic_control_device = st.text_input("Traffic Control Device")
                weather_condition = st.text_input("Weather Condition")
                lighting_condition = st.text_input("Lighting Condition")
                first_crash_type = st.text_input("First Crash Type")
                trafficway_type = st.text_input("Trafficway Type")
                alignment = st.text_input("Alignment")
                roadway_surface_cond = st.text_input("Roadway Surface Condition")
                road_defect = st.text_input("Road Defect")
                intersection_related_i = st.selectbox("Intersection Related", ["Y", "N"])
            
            with cols[1]:
                st.subheader("Injury & Impact")
                num_units = st.number_input("Number of Units*", min_value=0)
                most_severe_injury = st.text_input("Most Severe Injury")
                injuries_total = st.number_input("Total Injuries*", min_value=0.0)
                injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0)
                injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0)
                injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0)
                st.subheader("Other Details")
                damage = st.text_input("Damage")
                prim_contributory_cause = st.text_input("Primary Contributory Cause")
                crash_hour = st.slider("Crash Hour", 0, 23)
                crash_day_of_week = st.selectbox("Crash Day of Week", range(1, 8), format_func=lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x-1])
                crash_month = st.selectbox("Crash Month", range(1, 13), format_func=lambda x: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][x-1])
            
            submitted = st.form_submit_button("💾 Save Record")
            
            if submitted:
                if not all([crash_date, crash_type, num_units >= 0, injuries_total >= 0]):
                    st.error("Please fill all required fields (*)")
                else:
                    try:
                        row_data = [
                            crash_date, traffic_control_device, weather_condition, lighting_condition,
                            first_crash_type, trafficway_type, alignment, roadway_surface_cond,
                            road_defect, crash_type, intersection_related_i, damage,
                            prim_contributory_cause, num_units, most_severe_injury,
                            injuries_total, injuries_fatal, injuries_incapacitating,
                            injuries_non_incapacitating, injuries_reported_not_evident,
                            injuries_no_indication, crash_hour, crash_day_of_week, crash_month
                        ]
                        new_id = db.write_record(DataObject(row_data))
                        st.success(f"Record saved successfully with ID: {new_id}")
                    except Exception as e:
                        st.error(f"Error saving record: {str(e)}")

if __name__ == "__main__":
    main()