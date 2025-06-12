import streamlit as st
import csv
import os
import struct
from pathlib import Path
import json

class DataObject:
    def __init__(self, row_data=None):
        if row_data is not None:
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
            self.num_units = int(row_data[13])
            self.most_severe_injury = str(row_data[14])
            self.injuries_total = float(row_data[15])
            self.injuries_fatal = float(row_data[16])
            self.injuries_incapacitating = float(row_data[17])
            self.injuries_non_incapacitating = float(row_data[18])
            self.injuries_reported_not_evident = float(row_data[19])
            self.injuries_no_indication = float(row_data[20])
            self.crash_hour = int(row_data[21])
            self.crash_day_of_week = int(row_data[22])
            self.crash_month = int(row_data[23])

    def to_bytes(self):
        data_dict = {attr: getattr(self, attr) for attr in vars(self)}
        return json.dumps(data_dict).encode('utf-8')

    @classmethod
    def from_bytes(cls, byte_data):
        data_dict = json.loads(byte_data.decode('utf-8'))
        obj = cls()
        for key, value in data_dict.items():
            setattr(obj, key, value)
        return obj

# Ensure the directory exists
output_dir = os.path.join(Path.home(), 'Documents', 'Data')
os.makedirs(output_dir, exist_ok=True)

# Output file path
db_file_path = os.path.join(output_dir, 'traffic_accidents.db')

def get_last_id(file_path):
    """Read the last ID from the beginning of the file"""
    try:
        with open(file_path, 'rb') as f:
            id_bytes = f.read(4)
            if len(id_bytes) == 4:
                return struct.unpack('I', id_bytes)[0]
    except FileNotFoundError:
        pass
    return 0

def update_last_id(file_path, new_id):
    """Update the last ID at the beginning of the file"""
    with open(file_path, 'r+b') as f:
        f.write(struct.pack('I', new_id))
        f.flush()

def read_all_records(file_path):
    """Read all records from the database file"""
    records = []
    try:
        with open(file_path, 'rb') as f:
            # Skip the first 4 bytes (last ID)
            f.read(4)
            while True:
                # Read record structure
                id_bytes = f.read(4)
                if not id_bytes:
                    break
                record_id = struct.unpack('I', id_bytes)[0]
                validation = struct.unpack('?', f.read(1))[0]
                size = struct.unpack('I', f.read(4))[0]
                data_bytes = f.read(size)
                
                # Convert to DataObject
                obj = DataObject.from_bytes(data_bytes)
                records.append({
                    'id': record_id,
                    'validation': validation,
                    'data': obj
                })
    except FileNotFoundError:
        pass
    return records

def read_record_by_id(file_path, search_id):
    """Read a specific record by ID"""
    try:
        with open(file_path, 'rb') as f:
            # Skip the first 4 bytes (last ID)
            f.read(4)
            while True:
                pos = f.tell()
                id_bytes = f.read(4)
                if not id_bytes:
                    break
                record_id = struct.unpack('I', id_bytes)[0]
                validation = struct.unpack('?', f.read(1))[0]
                size = struct.unpack('I', f.read(4))[0]
                data_bytes = f.read(size)
                
                if record_id == search_id:
                    return {
                        'id': record_id,
                        'validation': validation,
                        'data': DataObject.from_bytes(data_bytes),
                        'position': pos
                    }
    except FileNotFoundError:
        pass
    return None

def write_record(file_path, data_object):
    """Write a single record to the database"""
    last_id = get_last_id(file_path)
    new_id = last_id + 1 if last_id > 0 else 1
    
    obj_bytes = data_object.to_bytes()
    size = len(obj_bytes)
    
    validation = all([
        data_object.crash_date,
        data_object.crash_type,
        data_object.num_units >= 0,
        data_object.injuries_total >= 0
    ])
    
    mode = 'ab' if last_id > 0 else 'wb'
    with open(file_path, mode) as f:
        if last_id == 0:
            f.write(struct.pack('I', 0))  # Placeholder for last ID
        
        # Write record
        f.write(struct.pack('I', new_id))
        f.write(struct.pack('?', validation))
        f.write(struct.pack('I', size))
        f.write(obj_bytes)
        
        # Update last ID
        update_last_id(file_path, new_id)
    
    return new_id

def write_from_csv(csv_path):
    """Write records from CSV file to database"""
    data_objects = []
    with open(csv_path, 'r') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)  # Skip header row
        for row in reader:
            data_objects.append(DataObject(row))
    
    last_id = get_last_id(db_file_path)
    starting_id = last_id + 1 if last_id > 0 else 1
    
    with open(db_file_path, 'ab' if last_id > 0 else 'wb') as db_file:
        id_counter = starting_id
        
        if last_id == 0:
            db_file.write(struct.pack('I', 0))
        
        for obj in data_objects:
            obj_bytes = obj.to_bytes()
            size = len(obj_bytes)
            
            validation = all([
                obj.crash_date,
                obj.crash_type,
                obj.num_units >= 0,
                obj.injuries_total >= 0
            ])
            
            db_file.write(struct.pack('I', id_counter))
            db_file.write(struct.unpack('?', validation))
            db_file.write(struct.pack('I', size))
            db_file.write(obj_bytes)
            
            update_last_id(db_file_path, id_counter)
            id_counter += 1
    
    return id_counter - 1

# Streamlit UI
st.title("Traffic Accidents Database")

option = st.sidebar.selectbox(
    "Select Operation",
    ["Read all", "Read one by ID", "Write from CSV File", "Write one registry"]
)

if option == "Read all":
    st.header("Read All Records")
    if st.button("Load Records"):
        records = read_all_records(db_file_path)
        if not records:
            st.warning("No records found in the database.")
        else:
            st.success(f"Found {len(records)} records")
            for record in records:
                with st.expander(f"Record ID: {record['id']} (Validation: {'OK' if record['validation'] else 'INVALID'})"):
                    st.json(vars(record['data']))

elif option == "Read one by ID":
    st.header("Read Record by ID")
    search_id = st.number_input("Enter Record ID", min_value=1, step=1)
    if st.button("Search"):
        record = read_record_by_id(db_file_path, search_id)
        if record:
            st.success(f"Found record ID: {record['id']}")
            st.json(vars(record['data']))
        else:
            st.warning(f"No record found with ID {search_id}")

elif option == "Write from CSV File":
    st.header("Write Records from CSV")
    csv_file = st.file_uploader("Upload CSV File", type=["csv"])
    if csv_file is not None and st.button("Write to Database"):
        # Save uploaded file temporarily
        temp_path = os.path.join(output_dir, "temp_upload.csv")
        with open(temp_path, "wb") as f:
            f.write(csv_file.getbuffer())
        
        try:
            last_id = write_from_csv(temp_path)
            st.success(f"Successfully wrote records up to ID {last_id}")
        except Exception as e:
            st.error(f"Error writing records: {str(e)}")
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

elif option == "Write one registry":
    st.header("Write Single Record")
    
    with st.form("record_form"):
        st.subheader("Enter Record Details")
        col1, col2 = st.columns(2)
        
        with col1:
            crash_date = st.text_input("Crash Date")
            traffic_control_device = st.text_input("Traffic Control Device")
            weather_condition = st.text_input("Weather Condition")
            lighting_condition = st.text_input("Lighting Condition")
            first_crash_type = st.text_input("First Crash Type")
            trafficway_type = st.text_input("Trafficway Type")
            alignment = st.text_input("Alignment")
            roadway_surface_cond = st.text_input("Roadway Surface Condition")
            road_defect = st.text_input("Road Defect")
            crash_type = st.text_input("Crash Type")
            intersection_related_i = st.text_input("Intersection Related (Y/N)")
        
        with col2:
            damage = st.text_input("Damage")
            prim_contributory_cause = st.text_input("Primary Contributory Cause")
            num_units = st.number_input("Number of Units", min_value=0)
            most_severe_injury = st.text_input("Most Severe Injury")
            injuries_total = st.number_input("Total Injuries", min_value=0.0)
            injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0)
            injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0)
            injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0)
            injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0)
            injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0)
            crash_hour = st.number_input("Crash Hour", min_value=0, max_value=23)
            crash_day_of_week = st.number_input("Crash Day of Week (1-7)", min_value=1, max_value=7)
            crash_month = st.number_input("Crash Month (1-12)", min_value=1, max_value=12)
        
        submitted = st.form_submit_button("Submit Record")
        if submitted:
            # Create DataObject from form data
            row_data = [
                crash_date, traffic_control_device, weather_condition, lighting_condition,
                first_crash_type, trafficway_type, alignment, roadway_surface_cond,
                road_defect, crash_type, intersection_related_i, damage,
                prim_contributory_cause, num_units, most_severe_injury,
                injuries_total, injuries_fatal, injuries_incapacitating,
                injuries_non_incapacitating, injuries_reported_not_evident,
                injuries_no_indication, crash_hour, crash_day_of_week, crash_month
            ]
            
            try:
                obj = DataObject(row_data)
                new_id = write_record(db_file_path, obj)
                st.success(f"Record successfully written with ID: {new_id}")
            except Exception as e:
                st.error(f"Error writing record: {str(e)}")

# Display database info
st.sidebar.header("Database Information")
last_id = get_last_id(db_file_path)
st.sidebar.write(f"Last Record ID: {last_id if last_id > 0 else 'No records yet'}")