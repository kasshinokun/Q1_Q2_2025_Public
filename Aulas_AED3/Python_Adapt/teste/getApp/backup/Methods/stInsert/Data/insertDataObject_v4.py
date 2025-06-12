import csv
import os
import struct
from pathlib import Path
import json

class DataObject:
    def __init__(self, row_data):
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

# Ensure the directory exists
output_dir = os.path.join(Path.home(), 'Documents', 'Data')
os.makedirs(output_dir, exist_ok=True)

# Output file path
db_file_path = os.path.join(output_dir, 'traffic_accidents.db')

def get_last_id(file_path):
    """Read the last ID from the beginning of the file"""
    try:
        with open(file_path, 'rb') as f:
            # Read the first 4 bytes which contain the last ID
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

# Read CSV and create DataObjects
data_objects = []
with open('traffic_accidents_rev2 (1).csv', 'r') as f:
    reader = csv.reader(f, delimiter=';')
    next(reader)  # Skip header row
    for row in reader:
        data_objects.append(DataObject(row))

# Determine starting ID
last_id = get_last_id(db_file_path)
starting_id = last_id + 1 if last_id > 0 else 1
print(f"Last ID in DB: {last_id}, Starting with ID: {starting_id}")

# Write to the .db file
with open(db_file_path, 'ab' if last_id > 0 else 'wb') as db_file:
    id_counter = starting_id
    
    # If new file, write the initial ID (will be updated after first record)
    if last_id == 0:
        db_file.write(struct.pack('I', 0))
    
    for obj in data_objects:
        # Convert object to bytes
        obj_bytes = obj.to_bytes()
        size = len(obj_bytes)
        
        # Validation flag
        validation = all([
            obj.crash_date,
            obj.crash_type,
            obj.num_units >= 0,
            obj.injuries_total >= 0
        ])
        
        # Get current position (for debugging)
        pos = db_file.tell()
        
        # Write the record:
        # 1. Auto-incremented ID (4 bytes)
        db_file.write(struct.pack('I', id_counter))
        # 2. Validation flag (1 byte)
        db_file.write(struct.pack('?', validation))
        # 3. Size of byte array (4 bytes)
        db_file.write(struct.pack('I', size))
        # 4. The actual byte array
        db_file.write(obj_bytes)
        
        # Update the last ID at beginning of file
        update_last_id(db_file_path, id_counter)
        
        print(f"Recorded ID {id_counter} at position {pos} (Validation: {'OK' if validation else 'INVALID'})")
        id_counter += 1

print(f"Data successfully written to {db_file_path}")
print(f"Last ID is now: {id_counter - 1}")