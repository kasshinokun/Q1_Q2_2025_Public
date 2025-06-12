import csv
import os
import struct
from pathlib import Path

class DataObject:
    def __init__(self, row):
        # Initialize your DataObject with the row data
        self.data = row  # You might want to process this into specific attributes
    
    def to_bytes(self):
        # Convert the DataObject to a byte array
        # This is a simple implementation - you should adapt it to your needs
        return str(self.data).encode('utf-8')

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
        
        # Validation flag (always True in this example)
        validation = True
        
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