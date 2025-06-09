import csv
import os
import struct
from pathlib import Path
import json

class DataObject:
    def __init__(self, row_data):
        self.crash_date = str(row_data[0])  # String
        self.traffic_control_device = str(row_data[1])  # String
        self.weather_condition = str(row_data[2])  # String
        self.lighting_condition = str(row_data[3])  # String
        self.first_crash_type = str(row_data[4])  # String
        self.trafficway_type = str(row_data[5])  # String
        self.alignment = str(row_data[6])  # String
        self.roadway_surface_cond = str(row_data[7])  # String
        self.road_defect = str(row_data[8])  # String
        self.crash_type = str(row_data[9])  # String
        self.intersection_related_i = str(row_data[10])  # String (Y/N)
        self.damage = str(row_data[11])  # String
        self.prim_contributory_cause = str(row_data[12])  # String
        self.num_units = int(row_data[13])  # Integer
        self.most_severe_injury = str(row_data[14])  # String
        self.injuries_total = float(row_data[15])  # Float
        self.injuries_fatal = float(row_data[16])  # Float
        self.injuries_incapacitating = float(row_data[17])  # Float
        self.injuries_non_incapacitating = float(row_data[18])  # Float
        self.injuries_reported_not_evident = float(row_data[19])  # Float
        self.injuries_no_indication = float(row_data[20])  # Float
        self.crash_hour = int(row_data[21])  # Integer
        self.crash_day_of_week = int(row_data[22])  # Integer
        self.crash_month = int(row_data[23])  # Integer

    def __str__(self):
        return (f"DataObject(crash_date={self.crash_date}, "
                f"traffic_control_device={self.traffic_control_device}, "
                f"weather_condition={self.weather_condition}, ...)")

    def to_bytes(self):
        """Convert the DataObject to a byte array using JSON serialization"""
        data_dict = {
            'crash_date': self.crash_date,
            'traffic_control_device': self.traffic_control_device,
            'weather_condition': self.weather_condition,
            'lighting_condition': self.lighting_condition,
            'first_crash_type': self.first_crash_type,
            'trafficway_type': self.trafficway_type,
            'alignment': self.alignment,
            'roadway_surface_cond': self.roadway_surface_cond,
            'road_defect': self.road_defect,
            'crash_type': self.crash_type,
            'intersection_related_i': self.intersection_related_i,
            'damage': self.damage,
            'prim_contributory_cause': self.prim_contributory_cause,
            'num_units': self.num_units,
            'most_severe_injury': self.most_severe_injury,
            'injuries_total': self.injuries_total,
            'injuries_fatal': self.injuries_fatal,
            'injuries_incapacitating': self.injuries_incapacitating,
            'injuries_non_incapacitating': self.injuries_non_incapacitating,
            'injuries_reported_not_evident': self.injuries_reported_not_evident,
            'injuries_no_indication': self.injuries_no_indication,
            'crash_hour': self.crash_hour,
            'crash_day_of_week': self.crash_day_of_week,
            'crash_month': self.crash_month
        }
        return json.dumps(data_dict).encode('utf-8')

# Ensure the directory exists
output_dir = os.path.join(Path.home(), 'Documents', 'Data')
os.makedirs(output_dir, exist_ok=True)

# Output file path
db_file_path = os.path.join(output_dir, 'traffic_accidents.db')

data_objects = []
with open('traffic_accidents_rev2 (1).csv', 'r') as f:
    reader = csv.reader(f, delimiter=';')
    next(reader)  # Skip header row
    for row in reader:
        data_objects.append(DataObject(row))

# Write to the .db file
with open(db_file_path, 'wb') as db_file:
    id_counter = 1  # Starting ID
    for obj in data_objects:
        # Convert object to bytes
        obj_bytes = obj.to_bytes()
        size = len(obj_bytes)
        
        # Validation flag (set to True if all required fields are present)
        validation = all([
            obj.crash_date,
            obj.crash_type,
            obj.num_units >= 0,
            obj.injuries_total >= 0
        ])
        
        # Write to file:
        # 1. Auto-incremented ID (4 bytes)
        db_file.write(struct.pack('I', id_counter))
        # 2. Validation flag (1 byte)
        db_file.write(struct.pack('?', validation))
        # 3. Size of byte array (4 bytes)
        db_file.write(struct.pack('I', size))
        # 4. The actual byte array
        db_file.write(obj_bytes)
        
        id_counter += 1

print(f"Data successfully written to {db_file_path}")