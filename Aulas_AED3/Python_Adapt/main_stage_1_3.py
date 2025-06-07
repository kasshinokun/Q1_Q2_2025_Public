import os
import csv
import struct
import datetime
import heapq
import time
from typing import List, Dict, Optional, Tuple, Union, DefaultDict, Deque
from collections import defaultdict, deque
from heapq import heappush, heappop

# ==============================================
# Data Object Definition
# ==============================================
class DataObject:
    DATE_FORMAT = "%d/%m/%Y"
    
    def __init__(self, 
                 ID_registro: int = 0,
                 crash_date: str = "",
                 data: datetime.date = None,
                 traffic_control_device: str = "",
                 weather_condition: str = "",
                 lighting_condition: List[str] = None,
                 first_crash_type: str = "",
                 trafficway_type: str = "",
                 alignment: str = "",
                 roadway_surface_cond: str = "",
                 road_defect: str = "",
                 crash_type: List[str] = None,
                 intersection_related_i: bool = False,
                 damage: str = "",
                 prim_contributory_cause: str = "",
                 num_units: int = 0,
                 most_severe_injury: List[str] = None,
                 injuries_total: float = 0.0,
                 injuries_fatal: float = 0.0,
                 injuries_incapacitating: float = 0.0,
                 injuries_non_incapacitating: float = 0.0,
                 injuries_reported_not_evident: float = 0.0,
                 injuries_no_indication: float = 0.0,
                 crash_hour: int = 0,
                 crash_day_of_week: int = 0,
                 crash_month: int = 0):
        
        self.ID_registro = ID_registro
        self.crash_date = crash_date
        self.data = data or datetime.date(1900, 1, 1)
        self.traffic_control_device = traffic_control_device
        self.weather_condition = weather_condition
        self.lighting_condition = lighting_condition or []
        self.first_crash_type = first_crash_type
        self.trafficway_type = trafficway_type
        self.alignment = alignment
        self.roadway_surface_cond = roadway_surface_cond
        self.road_defect = road_defect
        self.crash_type = crash_type or []
        self.intersection_related_i = intersection_related_i
        self.damage = damage
        self.prim_contributory_cause = prim_contributory_cause
        self.num_units = num_units
        self.most_severe_injury = most_severe_injury or []
        self.injuries_total = injuries_total
        self.injuries_fatal = injuries_fatal
        self.injuries_incapacitating = injuries_incapacitating
        self.injuries_non_incapacitating = injuries_non_incapacitating
        self.injuries_reported_not_evident = injuries_reported_not_evident
        self.injuries_no_indication = injuries_no_indication
        self.crash_hour = crash_hour
        self.crash_day_of_week = crash_day_of_week
        self.crash_month = crash_month

    def set_crash_date_from_timestamp(self, crash_date: str):
        try:
            self.data = datetime.datetime.strptime(crash_date[:10], self.DATE_FORMAT).date()
            self.crash_date = crash_date
            self.crash_day_of_week = self.data.isoweekday()
            self.crash_month = self.data.month
        except Exception as e:
            print(f"Error setting date: {e}")

    def get_intersection_related_str(self) -> str:
        return "S" if self.intersection_related_i else "N"
    
    def set_intersection_related_from_str(self, value: str):
        self.intersection_related_i = value.strip().upper() == "S"

    @staticmethod
    def list_to_string(lst: List[str]) -> str:
        return " , ".join(lst)

    def to_byte_array(self) -> bytes:
        try:
            ba = bytearray()
            # Pack fixed-size values
            ba += struct.pack('>i', self.ID_registro)
            ba += self._pack_string(self.crash_date)
            
            # Convert date to epoch days
            epoch = datetime.date(1970, 1, 1)
            days = (self.data - epoch).days
            ba += struct.pack('>q', days)
            
            # Pack strings
            for attr in [
                self.traffic_control_device,
                self.weather_condition,
                self.list_to_string(self.lighting_condition),
                self.first_crash_type,
                self.trafficway_type,
                self.alignment,
                self.roadway_surface_cond,
                self.road_defect,
                self.list_to_string(self.crash_type),
                self.get_intersection_related_str(),
                self.damage,
                self.prim_contributory_cause
            ]:
                ba += self._pack_string(attr)
            
            # Pack integers and floats
            ba += struct.pack('>i', self.num_units)
            ba += self._pack_string(self.list_to_string(self.most_severe_injury))
            ba += struct.pack('>f', self.injuries_total)
            ba += struct.pack('>f', self.injuries_fatal)
            ba += struct.pack('>f', self.injuries_incapacitating)
            ba += struct.pack('>f', self.injuries_non_incapacitating)
            ba += struct.pack('>f', self.injuries_reported_not_evident)
            ba += struct.pack('>f', self.injuries_no_indication)
            ba += struct.pack('>i', self.crash_hour)
            ba += struct.pack('>i', self.crash_day_of_week)
            ba += struct.pack('>i', self.crash_month)
            
            return bytes(ba)
        except Exception as e:
            print(f"Serialization error: {e}")
            return b''

    @classmethod
    def from_byte_array(cls, data: bytes):
        try:
            obj = cls()
            offset = 0
            
            # Unpack fixed-size values
            obj.ID_registro = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            obj.crash_date, offset = cls._unpack_string(data, offset)
            
            # Unpack date (epoch days)
            days = struct.unpack_from('>q', data, offset)[0]
            offset += 8
            obj.data = datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
            
            # Unpack strings
            string_attrs = [
                'traffic_control_device',
                'weather_condition',
                'lighting_condition',
                'first_crash_type',
                'trafficway_type',
                'alignment',
                'roadway_surface_cond',
                'road_defect',
                'crash_type',
                'intersection_related_i',
                'damage',
                'prim_contributory_cause'
            ]
            
            for attr in string_attrs:
                value, offset = cls._unpack_string(data, offset)
                if attr == 'lighting_condition':
                    obj.lighting_condition = [s.strip() for s in value.split(',')] if value else []
                elif attr == 'crash_type':
                    obj.crash_type = [s.strip() for s in value.split(',')] if value else []
                elif attr == 'intersection_related_i':
                    obj.set_intersection_related_from_str(value)
                else:
                    setattr(obj, attr, value)
            
            # Unpack integers and floats
            obj.num_units = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            
            severe_injury_str, offset = cls._unpack_string(data, offset)
            obj.most_severe_injury = [s.strip() for s in severe_injury_str.split(',')] if severe_injury_str else []
            
            float_attrs = [
                'injuries_total',
                'injuries_fatal',
                'injuries_incapacitating',
                'injuries_non_incapacitating',
                'injuries_reported_not_evident',
                'injuries_no_indication'
            ]
            
            for attr in float_attrs:
                setattr(obj, attr, struct.unpack_from('>f', data, offset)[0])
                offset += 4
                
            int_attrs = [
                'crash_hour',
                'crash_day_of_week',
                'crash_month'
            ]
            
            for attr in int_attrs:
                setattr(obj, attr, struct.unpack_from('>i', data, offset)[0])
                offset += 4
            
            return obj
        except Exception as e:
            print(f"Deserialization error: {e}")
            return None

    @staticmethod
    def _pack_string(s: str) -> bytes:
        """Pack string with 2-byte length prefix (big-endian)"""
        if s is None:
            s = ""
        encoded = s.encode('utf-8')
        return struct.pack('>H', len(encoded)) + encoded

    @staticmethod
    def _unpack_string(data: bytes, offset: int) -> Tuple[str, int]:
        """Unpack string with 2-byte length prefix (big-endian)"""
        length = struct.unpack_from('>H', data, offset)[0]
        offset += 2
        s = data[offset:offset+length].decode('utf-8')
        return s, offset + length

    def __str__(self):
        return (
            f"ID Registro: {self.ID_registro}\n"
            f"Data do Acidente: {self.crash_date}\n"
            f"Data (LocalDate): {self.data.strftime(self.DATE_FORMAT)}\n"
            f"Dispositivo de controle de tráfego: {self.traffic_control_device}\n"
            f"Condição climática: {self.weather_condition}\n"
            f"Condição de iluminação: {self.list_to_string(self.lighting_condition)}\n"
            f"Tipo de primeira colisão: {self.first_crash_type}\n"
            f"Tipo de via de tráfego: {self.trafficway_type}\n"
            f"Alinhamento: {self.alignment}\n"
            f"Condição da superfície da via: {self.roadway_surface_cond}\n"
            f"Defeito na estrada: {self.road_defect}\n"
            f"Tipo de acidente: {self.list_to_string(self.crash_type)}\n"
            f"Interseção relacionada: {self.get_intersection_related_str()}\n"
            f"Danos: {self.damage}\n"
            f"Causa contributiva primária: {self.prim_contributory_cause}\n"
            f"Número de unidades: {self.num_units}\n"
            f"Ferimento mais grave: {self.list_to_string(self.most_severe_injury)}\n"
            f"Total de ferimentos: {self.injuries_total:.1f}\n"
            f"Ferimentos fatais: {self.injuries_fatal:.1f}\n"
            f"Lesões incapacitantes: {self.injuries_incapacitating:.1f}\n"
            f"Lesões não incapacitantes: {self.injuries_non_incapacitating:.1f}\n"
            f"Lesões relatadas não evidentes: {self.injuries_reported_not_evident:.1f}\n"
            f"Lesões sem indicação: {self.injuries_no_indication:.1f}\n"
            f"Hora do acidente: {self.crash_hour}\n"
            f"Dia da semana: {self.crash_day_of_week}\n"
            f"Mês: {self.crash_month}"
        )


# ==============================================
# File Handling
# ==============================================
class FileHandler:
    @staticmethod
    def read_csv(path: str) -> List[DataObject]:
        """Read CSV file and return list of DataObjects"""
        objects = []
        try:
            with open(path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                next(reader)  # Skip header
                for row in reader:
                    if len(row) < 22:  # Adjusted for actual columns
                        print(f"Skipping invalid row: {row}")
                        continue
                    
                    obj = DataObject()
                    obj.set_crash_date_from_timestamp(
                        f"{row[0][3:5]}/{row[0][0:2]}/{row[0][6:10]} {row[0][11:]}"
                    )
                    obj.traffic_control_device = row[1]
                    obj.weather_condition = row[2]
                    obj.lighting_condition = [s.strip() for s in row[3].split(',')] if row[3] else []
                    obj.first_crash_type = row[4]
                    obj.trafficway_type = row[5]
                    obj.alignment = row[6]
                    obj.roadway_surface_cond = row[7]
                    obj.road_defect = row[8]
                    obj.crash_type = [s.strip() for s in row[9].split('/')] if row[9] else []
                    obj.set_intersection_related_from_str(row[10])
                    obj.damage = row[11]
                    obj.prim_contributory_cause = row[12]
                    obj.num_units = int(row[13]) if row[13] else 0
                    obj.most_severe_injury = [s.strip() for s in row[14].split(',')] if row[14] else []
                    
                    # Handle float conversion safely
                    float_fields = [
                        row[15], row[16], row[17], row[18], row[19], row[20]
                    float_values = [0.0] * 6
                    
                    for i, val in enumerate(float_fields):
                        try:
                            float_values[i] = float(val) if val else 0.0
                        except ValueError:
                            pass
                    
                    (obj.injuries_total, obj.injuries_fatal, obj.injuries_incapacitating,
                     obj.injuries_non_incapacitating, obj.injuries_reported_not_evident,
                     obj.injuries_no_indication) = float_values
                    
                    obj.crash_hour = int(row[21]) if row[21] else 0
                    objects.append(obj)
            
            print(f"Successfully read {len(objects)} records from CSV")
            return objects
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return []

    @staticmethod
    def write_db(objects: List[DataObject], path: str):
        """Write objects to database file"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as file:
                # Write header with last ID
                last_id = objects[-1].ID_registro if objects else 0
                file.write(struct.pack('>i', last_id))
                
                # Write records
                for obj in objects:
                    data = obj.to_byte_array()
                    file.write(struct.pack('>i', obj.ID_registro))
                    file.write(struct.pack('?', True))  # Active record
                    file.write(struct.pack('>i', len(data)))
                    file.write(data)
            print(f"Successfully wrote {len(objects)} records to database")
        except Exception as e:
            print(f"Error writing database: {e}")

    @staticmethod
    def read_db(path: str) -> List[DataObject]:
        """Read database file and return list of DataObjects"""
        objects = []
        try:
            if not os.path.exists(path):
                print(f"Database file not found: {path}")
                return []
                
            with open(path, 'rb') as file:
                # Read header
                last_id = struct.unpack('>i', file.read(4))[0]
                
                while file.tell() < os.path.getsize(path):
                    record_id = struct.unpack('>i', file.read(4))[0]
                    active = struct.unpack('?', file.read(1))[0]
                    size = struct.unpack('>i', file.read(4))[0]
                    data = file.read(size)
                    
                    if active:
                        obj = DataObject.from_byte_array(data)
                        if obj:
                            objects.append(obj)
            print(f"Successfully read {len(objects)} records from database")
            return objects
        except Exception as e:
            print(f"Error reading database: {e}")
            return []

    @staticmethod
    def update_record(path: str, record_id: int, updated_obj: DataObject):
        """Update a record in the database"""
        try:
            # Read all records
            records = []
            with open(path, 'rb') as file:
                last_id = struct.unpack('>i', file.read(4))[0]
                
                while file.tell() < os.path.getsize(path):
                    pos = file.tell()
                    rid = struct.unpack('>i', file.read(4))[0]
                    active = struct.unpack('?', file.read(1))[0]
                    size = struct.unpack('>i', file.read(4))[0]
                    data = file.read(size)
                    
                    if rid == record_id and active:
                        # Mark existing record as inactive
                        records.append((pos, rid, False, size, data))
                        # Add updated record at end
                        new_data = updated_obj.to_byte_array()
                        records.append((None, rid, True, len(new_data), new_data))
                    else:
                        records.append((pos, rid, active, size, data))
            
            # Write all records back
            with open(path, 'wb') as file:
                file.write(struct.pack('>i', last_id))
                for pos, rid, active, size, data in records:
                    if pos is None:  # New record
                        file.write(struct.pack('>i', rid))
                        file.write(struct.pack('?', active))
                        file.write(struct.pack('>i', size))
                        file.write(data)
                    else:  # Existing record
                        file.write(struct.pack('>i', rid))
                        file.write(struct.pack('?', active))
                        file.write(struct.pack('>i', size))
                        file.write(data)
            print(f"Record {record_id} updated successfully")
            return True
        except Exception as e:
            print(f"Error updating record: {e}")
            return False

    @staticmethod
    def delete_record(path: str, record_id: int):
        """Mark a record as deleted in the database"""
        try:
            with open(path, 'r+b') as file:
                file.read(4)  # Skip header
                
                while file.tell() < os.path.getsize(path):
                    pos = file.tell()
                    rid = struct.unpack('>i', file.read(4))[0]
                    active = struct.unpack('?', file.read(1))[0]
                    size = struct.unpack('>i', file.read(4))[0]
                    
                    if rid == record_id and active:
                        # Mark record as inactive
                        file.seek(pos + 4)
                        file.write(struct.pack('?', False))
                        print(f"Record {record_id} marked as deleted")
                        return True
                    
                    # Move to next record
                    file.seek(pos + 4 + 1 + 4 + size)
            print(f"Record {record_id} not found")
            return False
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False


# ==============================================
# Indexed File Handling
# ==============================================
class IndexedFileHandler:
    INDEX_ENTRY_SIZE = 13  # 4 (ID) + 8 (pointer) + 1 (active flag)
    
    @staticmethod
    def write_from_csv(csv_path: str, data_file_path: str, index_file_path: str):
        """Import data from CSV to indexed database"""
        try:
            # Create necessary directories
            os.makedirs(os.path.dirname(data_file_path), exist_ok=True)
            os.makedirs(os.path.dirname(index_file_path), exist_ok=True)
            
            with open(data_file_path, 'wb') as data_file, \
                 open(index_file_path, 'wb') as index_file:
                
                # Write initial header (last ID = 0)
                index_file.write(struct.pack('>i', 0))
                last_id = 0
                
                with open(csv_path, 'r', encoding='utf-8') as csv_file:
                    reader = csv.reader(csv_file, delimiter=';')
                    next(reader)  # Skip header
                    
                    for row in reader:
                        if len(row) < 22:  # Adjusted for actual columns
                            continue
                        
                        # Create DataObject from CSV row
                        obj = DataObject()
                        obj.set_crash_date_from_timestamp(
                            f"{row[0][3:5]}/{row[0][0:2]}/{row[0][6:10]} {row[0][11:]}"
                        )
                        obj.traffic_control_device = row[1]
                        obj.weather_condition = row[2]
                        obj.lighting_condition = [s.strip() for s in row[3].split(',')] if row[3] else []
                        obj.first_crash_type = row[4]
                        obj.trafficway_type = row[5]
                        obj.alignment = row[6]
                        obj.roadway_surface_cond = row[7]
                        obj.road_defect = row[8]
                        obj.crash_type = [s.strip() for s in row[9].split('/')] if row[9] else []
                        obj.set_intersection_related_from_str(row[10])
                        obj.damage = row[11]
                        obj.prim_contributory_cause = row[12]
                        obj.num_units = int(row[13]) if row[13] else 0
                        obj.most_severe_injury = [s.strip() for s in row[14].split(',')] if row[14] else []
                        
                        # Handle float conversion safely
                        float_fields = [
                            row[15], row[16], row[17], row[18], row[19], row[20]
                        float_values = [0.0] * 6
                        
                        for i, val in enumerate(float_fields):
                            try:
                                float_values[i] = float(val) if val else 0.0
                            except ValueError:
                                pass
                        
                        (obj.injuries_total, obj.injuries_fatal, obj.injuries_incapacitating,
                         obj.injuries_non_incapacitating, obj.injuries_reported_not_evident,
                         obj.injuries_no_indication) = float_values
                        
                        obj.crash_hour = int(row[21]) if row[21] else 0
                        
                        # Assign ID and increment
                        last_id += 1
                        obj.ID_registro = last_id
                        
                        # Write to data file
                        data_pos = data_file.tell()
                        data = obj.to_byte_array()
                        data_file.write(struct.pack('?', True))  # Active flag
                        data_file.write(struct.pack('>i', len(data)))
                        data_file.write(data)
                        
                        # Write to index file
                        index_file.write(struct.pack('>i', obj.ID_registro))
                        index_file.write(struct.pack('>q', data_pos))
                        index_file.write(struct.pack('?', True))
                
                # Update header with last ID
                index_file.seek(0)
                index_file.write(struct.pack('>i', last_id))
            
            print(f"Successfully imported {last_id} records to indexed database")
            return True
        except Exception as e:
            print(f"Error importing CSV to indexed database: {e}")
            return False

    @staticmethod
    def find_index_entry(index_file_path: str, record_id: int) -> Tuple[Union[int, None], Union[bool, None]]:
        """Find index entry using binary search"""
        try:
            if not os.path.exists(index_file_path):
                return None, None
                
            with open(index_file_path, 'rb') as index_file:
                # Read header (last ID)
                last_id = struct.unpack('>i', index_file.read(4))[0]
                
                # Binary search in sorted index
                low, high = 0, last_id - 1
                while low <= high:
                    mid = (low + high) // 2
                    # Calculate position of index entry
                    index_file.seek(4 + mid * IndexedFileHandler.INDEX_ENTRY_SIZE)
                    
                    # Read index entry
                    entry_id = struct.unpack('>i', index_file.read(4))[0]
                    pointer = struct.unpack('>q', index_file.read(8))[0]
                    active = struct.unpack('?', index_file.read(1))[0]
                    
                    if entry_id == record_id:
                        return pointer, active
                    elif entry_id < record_id:
                        low = mid + 1
                    else:
                        high = mid - 1
            return None, None
        except Exception as e:
            print(f"Error finding index entry: {e}")
            return None, None

    @staticmethod
    def read_record(data_file_path: str, index_file_path: str, record_id: int) -> Union[DataObject, None]:
        """Read record using index"""
        pointer, active = IndexedFileHandler.find_index_entry(index_file_path, record_id)
        if pointer is None or not active:
            return None
            
        try:
            with open(data_file_path, 'rb') as data_file:
                data_file.seek(pointer)
                active = struct.unpack('?', data_file.read(1))[0]
                if not active:
                    return None
                    
                size = struct.unpack('>i', data_file.read(4))[0]
                data = data_file.read(size)
                return DataObject.from_byte_array(data)
        except Exception as e:
            print(f"Error reading record from data file: {e}")
            return None

    @staticmethod
    def update_record(data_file_path: str, index_file_path: str, 
                      record_id: int, updated_obj: DataObject) -> bool:
        """Update a record in the indexed database"""
        pointer, active = IndexedFileHandler.find_index_entry(index_file_path, record_id)
        if pointer is None or not active:
            return False
            
        new_data = updated_obj.to_byte_array()
        
        try:
            with open(data_file_path, 'r+b') as data_file:
                # Check if new data fits in existing space
                data_file.seek(pointer)
                old_active = struct.unpack('?', data_file.read(1))[0]
                old_size = struct.unpack('>i', data_file.read(4))[0]
                
                if len(new_data) <= old_size:
                    # Overwrite existing record
                    data_file.seek(pointer)
                    data_file.write(struct.pack('?', True))
                    data_file.write(struct.pack('>i', len(new_data)))
                    data_file.write(new_data)
                else:
                    # Write new record at end of file
                    data_file.seek(0, os.SEEK_END)
                    new_pointer = data_file.tell()
                    data_file.write(struct.pack('?', True))
                    data_file.write(struct.pack('>i', len(new_data)))
                    data_file.write(new_data)
                    
                    # Update index entry
                    with open(index_file_path, 'r+b') as index_file:
                        # Find index entry position
                        last_id = struct.unpack('>i', index_file.read(4))[0]
                        low, high = 0, last_id - 1
                        while low <= high:
                            mid = (low + high) // 2
                            pos = 4 + mid * IndexedFileHandler.INDEX_ENTRY_SIZE
                            index_file.seek(pos)
                            entry_id = struct.unpack('>i', index_file.read(4))[0]
                            
                            if entry_id == record_id:
                                # Update pointer
                                index_file.seek(pos + 4)
                                index_file.write(struct.pack('>q', new_pointer))
                                break
                            elif entry_id < record_id:
                                low = mid + 1
                            else:
                                high = mid - 1
                
                    # Mark old record as deleted
                    data_file.seek(pointer)
                    data_file.write(struct.pack('?', False))
            return True
        except Exception as e:
            print(f"Error updating record: {e}")
            return False

    @staticmethod
    def delete_record(data_file_path: str, index_file_path: str, record_id: int) -> bool:
        """Mark a record as deleted in the indexed database"""
        pointer, active = IndexedFileHandler.find_index_entry(index_file_path, record_id)
        if pointer is None or not active:
            return False
            
        try:
            # Update index entry
            with open(index_file_path, 'r+b') as index_file:
                last_id = struct.unpack('>i', index_file.read(4))[0]
                low, high = 0, last_id - 1
                while low <= high:
                    mid = (low + high) // 2
                    pos = 4 + mid * IndexedFileHandler.INDEX_ENTRY_SIZE
                    index_file.seek(pos)
                    entry_id = struct.unpack('>i', index_file.read(4))[0]
                    
                    if entry_id == record_id:
                        # Mark as deleted
                        index_file.seek(pos + 12)
                        index_file.write(struct.pack('?', False))
                        break
                    elif entry_id < record_id:
                        low = mid + 1
                    else:
                        high = mid - 1
            
            # Update data file
            with open(data_file_path, 'r+b') as data_file:
                data_file.seek(pointer)
                data_file.write(struct.pack('?', False))
            
            return True
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False


# ==============================================
# Compression Algorithms
# ==============================================
class CompressionHandler:
    @staticmethod
    def huffman_compress(input_file: str, output_file: str):
        """Huffman compression (character-based)"""
        start_time = time.time()
        
        try:
            # Read input data
            with open(input_file, 'r', encoding='utf-8') as f:
                data = f.read()
            
            # Build frequency table
            freq = defaultdict(int)
            for char in data:
                freq[char] += 1
            
            # Build Huffman tree
            heap = [[weight, [char, ""]] for char, weight in freq.items()]
            heapq.heapify(heap)
            
            while len(heap) > 1:
                lo = heapq.heappop(heap)
                hi = heapq.heappop(heap)
                for pair in lo[1:]:
                    pair[1] = '0' + pair[1]
                for pair in hi[1:]:
                    pair[1] = '1' + pair[1]
                heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
            
            # Generate codes
            huff_codes = dict(heap[0][1:])
            
            # Encode data
            encoded_data = ''.join(huff_codes[char] for char in data)
            
            # Pad encoded data to make it multiple of 8
            extra_padding = 8 - len(encoded_data) % 8
            encoded_data += '0' * extra_padding
            
            # Convert bit string to bytes
            byte_array = bytearray()
            for i in range(0, len(encoded_data), 8):
                byte = encoded_data[i:i+8]
                byte_array.append(int(byte, 2))
            
            # Write to file
            with open(output_file, 'wb') as f:
                # Write metadata
                f.write(struct.pack('I', len(data)))  # Original data length
                f.write(struct.pack('I', extra_padding))  # Padding length
                f.write(struct.pack('I', len(freq)))  # Frequency table size
                
                # Write frequency table
                for char, count in freq.items():
                    f.write(char.encode('utf-8'))
                    f.write(struct.pack('I', count))
                
                # Write compressed data
                f.write(bytes(byte_array))
            
            # Calculate stats
            original_size = os.path.getsize(input_file)
            compressed_size = os.path.getsize(output_file)
            ratio = (compressed_size / original_size) * 100
            elapsed = time.time() - start_time
            
            print(f"Compression complete: {input_file} -> {output_file}")
            print(f"Original size: {original_size} bytes")
            print(f"Compressed size: {compressed_size} bytes")
            print(f"Compression ratio: {ratio:.2f}%")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Compression error: {e}")
            return False

    @staticmethod
    def huffman_decompress(input_file: str, output_file: str):
        """Huffman decompression (character-based)"""
        start_time = time.time()
        
        try:
            with open(input_file, 'rb') as f:
                # Read metadata
                data_len = struct.unpack('I', f.read(4))[0]
                padding = struct.unpack('I', f.read(4))[0]
                freq_size = struct.unpack('I', f.read(4))[0]
                
                # Rebuild frequency table
                freq = {}
                for _ in range(freq_size):
                    char = f.read(1).decode('utf-8')
                    count = struct.unpack('I', f.read(4))[0]
                    freq[char] = count
                
                # Read compressed data
                compressed_data = f.read()
            
            # Rebuild Huffman tree
            heap = [[weight, [char, ""]] for char, weight in freq.items()]
            heapq.heapify(heap)
            
            while len(heap) > 1:
                lo = heapq.heappop(heap)
                hi = heapq.heappop(heap)
                for pair in lo[1:]:
                    pair[1] = '0' + pair[1]
                for pair in hi[1:]:
                    pair[1] = '1' + pair[1]
                heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
            
            huff_codes = dict(heap[0][1:])
            reverse_codes = {code: char for char, code in huff_codes.items()}
            
            # Convert bytes to bit string
            bit_string = ""
            for byte in compressed_data:
                bits = bin(byte)[2:].rjust(8, '0')
                bit_string += bits
            
            # Remove padding
            bit_string = bit_string[:-padding] if padding > 0 else bit_string
            
            # Decode data
            current_code = ""
            decoded_data = []
            
            for bit in bit_string:
                current_code += bit
                if current_code in reverse_codes:
                    decoded_data.append(reverse_codes[current_code])
                    current_code = ""
            
            # Write decompressed data
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(''.join(decoded_data))
            
            # Verify
            original_size = os.path.getsize(input_file)
            decompressed_size = os.path.getsize(output_file)
            elapsed = time.time() - start_time
            
            print(f"Decompression complete: {input_file} -> {output_file}")
            print(f"Compressed size: {original_size} bytes")
            print(f"Decompressed size: {decompressed_size} bytes")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Decompression error: {e}")
            return False

    @staticmethod
    def huffman_byte_compress(input_file: str, output_file: str):
        """Huffman compression (byte-based)"""
        start_time = time.time()
        
        try:
            # Read input data
            with open(input_file, 'rb') as f:
                data = f.read()
            
            # Build frequency table
            freq = defaultdict(int)
            for byte in data:
                freq[byte] += 1
            
            # Build Huffman tree
            heap = [[weight, [byte, ""]] for byte, weight in freq.items()]
            heapq.heapify(heap)
            
            while len(heap) > 1:
                lo = heapq.heappop(heap)
                hi = heapq.heappop(heap)
                for pair in lo[1:]:
                    pair[1] = '0' + pair[1]
                for pair in hi[1:]:
                    pair[1] = '1' + pair[1]
                heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
            
            # Generate codes
            huff_codes = dict(heap[0][1:])
            
            # Encode data
            bit_string = ''.join(huff_codes[byte] for byte in data)
            
            # Pad encoded data to make it multiple of 8
            padding = 8 - len(bit_string) % 8
            bit_string += '0' * padding
            
            # Convert bit string to bytes
            byte_array = bytearray()
            for i in range(0, len(bit_string), 8):
                byte = bit_string[i:i+8]
                byte_array.append(int(byte, 2))
            
            # Write to file
            with open(output_file, 'wb') as f:
                # Write metadata
                f.write(struct.pack('I', len(data)))  # Original data length
                f.write(struct.pack('I', padding))  # Padding length
                f.write(struct.pack('I', len(freq)))  # Frequency table size
                
                # Write frequency table
                for byte, count in freq.items():
                    f.write(struct.pack('B', byte))
                    f.write(struct.pack('I', count))
                
                # Write compressed data
                f.write(bytes(byte_array))
            
            # Calculate stats
            original_size = os.path.getsize(input_file)
            compressed_size = os.path.getsize(output_file)
            ratio = (compressed_size / original_size) * 100
            elapsed = time.time() - start_time
            
            print(f"Compression complete: {input_file} -> {output_file}")
            print(f"Original size: {original_size} bytes")
            print(f"Compressed size: {compressed_size} bytes")
            print(f"Compression ratio: {ratio:.2f}%")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Compression error: {e}")
            return False

    @staticmethod
    def huffman_byte_decompress(input_file: str, output_file: str):
        """Huffman decompression (byte-based)"""
        start_time = time.time()
        
        try:
            with open(input_file, 'rb') as f:
                # Read metadata
                data_len = struct.unpack('I', f.read(4))[0]
                padding = struct.unpack('I', f.read(4))[0]
                freq_size = struct.unpack('I', f.read(4))[0]
                
                # Rebuild frequency table
                freq = {}
                for _ in range(freq_size):
                    byte = struct.unpack('B', f.read(1))[0]
                    count = struct.unpack('I', f.read(4))[0]
                    freq[byte] = count
                
                # Read compressed data
                compressed_data = f.read()
            
            # Rebuild Huffman tree
            heap = [[weight, [byte, ""]] for byte, weight in freq.items()]
            heapq.heapify(heap)
            
            while len(heap) > 1:
                lo = heapq.heappop(heap)
                hi = heapq.heappop(heap)
                for pair in lo[1:]:
                    pair[1] = '0' + pair[1]
                for pair in hi[1:]:
                    pair[1] = '1' + pair[1]
                heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
            
            huff_codes = dict(heap[0][1:])
            reverse_codes = {code: byte for byte, code in huff_codes.items()}
            
            # Convert bytes to bit string
            bit_string = ""
            for byte in compressed_data:
                bits = bin(byte)[2:].rjust(8, '0')
                bit_string += bits
            
            # Remove padding
            bit_string = bit_string[:-padding] if padding > 0 else bit_string
            
            # Decode data
            current_code = ""
            decoded_data = bytearray()
            
            for bit in bit_string:
                current_code += bit
                if current_code in reverse_codes:
                    decoded_data.append(reverse_codes[current_code])
                    current_code = ""
            
            # Write decompressed data
            with open(output_file, 'wb') as f:
                f.write(decoded_data)
            
            # Verify
            original_size = os.path.getsize(input_file)
            decompressed_size = os.path.getsize(output_file)
            elapsed = time.time() - start_time
            
            print(f"Decompression complete: {input_file} -> {output_file}")
            print(f"Compressed size: {original_size} bytes")
            print(f"Decompressed size: {decompressed_size} bytes")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Decompression error: {e}")
            return False

    @staticmethod
    def lzw_compress(input_file: str, output_file: str):
        """LZW compression"""
        start_time = time.time()
        
        try:
            # Initialize dictionary
            dict_size = 256
            dictionary = {bytes([i]): i for i in range(dict_size)}
            
            # Read input data
            with open(input_file, 'rb') as f:
                data = f.read()
            
            # Compression
            w = bytes()
            compressed = []
            
            for byte in data:
                wc = w + bytes([byte])
                if wc in dictionary:
                    w = wc
                else:
                    compressed.append(dictionary[w])
                    # Add new sequence to dictionary
                    if dict_size < 65536:  # Limit to 16-bit codes
                        dictionary[wc] = dict_size
                        dict_size += 1
                    w = bytes([byte])
            
            if w:
                compressed.append(dictionary[w])
            
            # Write to file
            with open(output_file, 'wb') as f:
                # Write number of codes
                f.write(struct.pack('I', len(compressed)))
                # Write codes
                for code in compressed:
                    f.write(struct.pack('H', code))  # Use 2-byte unsigned int
            
            # Calculate stats
            original_size = os.path.getsize(input_file)
            compressed_size = os.path.getsize(output_file)
            ratio = (compressed_size / original_size) * 100
            elapsed = time.time() - start_time
            
            print(f"Compression complete: {input_file} -> {output_file}")
            print(f"Original size: {original_size} bytes")
            print(f"Compressed size: {compressed_size} bytes")
            print(f"Compression ratio: {ratio:.2f}%")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Compression error: {e}")
            return False

    @staticmethod
    def lzw_decompress(input_file: str, output_file: str):
        """LZW decompression"""
        start_time = time.time()
        
        try:
            # Initialize dictionary
            dict_size = 256
            dictionary = {i: bytes([i]) for i in range(dict_size)}
            
            # Read compressed data
            with open(input_file, 'rb') as f:
                num_codes = struct.unpack('I', f.read(4))[0]
                codes = [struct.unpack('H', f.read(2))[0] for _ in range(num_codes)]
            
            # Decompression
            result = bytearray()
            w = bytes([codes[0]])
            result.extend(w)
            
            for k in codes[1:]:
                if k in dictionary:
                    entry = dictionary[k]
                elif k == dict_size:
                    entry = w + bytes([w[0]])
                else:
                    raise ValueError(f"Bad compressed code: {k}")
                
                result.extend(entry)
                
                # Add new sequence to dictionary
                if dict_size < 65536:  # Limit to 16-bit codes
                    dictionary[dict_size] = w + bytes([entry[0]])
                    dict_size += 1
                
                w = entry
            
            # Write decompressed data
            with open(output_file, 'wb') as f:
                f.write(result)
            
            # Verify
            original_size = os.path.getsize(input_file)
            decompressed_size = os.path.getsize(output_file)
            elapsed = time.time() - start_time
            
            print(f"Decompression complete: {input_file} -> {output_file}")
            print(f"Compressed size: {original_size} bytes")
            print(f"Decompressed size: {decompressed_size} bytes")
            print(f"Time: {elapsed:.2f} seconds")
            return True
        except Exception as e:
            print(f"Decompression error: {e}")
            return False

    @staticmethod
    def test_algorithms():
        """Test all compression algorithms with sample data"""
        sample_file = "sample.txt"
        sample_content = "this is a test string for compression algorithms. this is another test."
        
        try:
            # Create sample file
            with open(sample_file, 'w') as f:
                f.write(sample_content)
            
            print("Testing Huffman (character-based)...")
            CompressionHandler.huffman_compress(sample_file, "sample.huffc")
            CompressionHandler.huffman_decompress("sample.huffc", "sample_decompressed.txt")
            
            print("\nTesting Huffman (byte-based)...")
            CompressionHandler.huffman_byte_compress(sample_file, "sample.huffb")
            CompressionHandler.huffman_byte_decompress("sample.huffb", "sample_decompressed_byte.txt")
            
            print("\nTesting LZW...")
            CompressionHandler.lzw_compress(sample_file, "sample.lzw")
            CompressionHandler.lzw_decompress("sample.lzw", "sample_decompressed_lzw.txt")
            
            # Clean up
            for f in ["sample.huffc", "sample.huffb", "sample.lzw", 
                     "sample_decompressed.txt", "sample_decompressed_byte.txt", 
                     "sample_decompressed_lzw.txt"]:
                if os.path.exists(f):
                    os.remove(f)
            
            print("\nAll tests completed successfully!")
            return True
        except Exception as e:
            print(f"Test error: {e}")
            return False
        finally:
            if os.path.exists(sample_file):
                os.remove(sample_file)


# ==============================================
# Menu System
# ==============================================
class MenuSystem:
    @staticmethod
    def main_menu():
        """Display the main menu and handle user input"""
        while True:
            print("\n" + "="*50)
            print("Sistema de Gerenciamento de Acidentes de Trânsito")
            print("="*50)
            print("1. Parte I - Gerenciamento de Dados")
            print("2. Parte II - Indexação e Busca")
            print("3. Parte III - Compactação de Dados")
            print("4. Sair")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                MenuSystem.part1_menu()
            elif choice == "2":
                MenuSystem.part2_menu()
            elif choice == "3":
                MenuSystem.part3_menu()
            elif choice == "4":
                print("Saindo do sistema...")
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def part1_menu():
        """Display Part 1 menu and handle user input"""
        db_path = "data/traffic_accidents.db"
        while True:
            print("\n" + "="*50)
            print("Parte I - Gerenciamento de Dados")
            print("="*50)
            print("1. Importar dados de CSV")
            print("2. Listar todos os registros")
            print("3. Buscar registro por ID")
            print("4. Atualizar registro")
            print("5. Excluir registro")
            print("6. Voltar ao menu principal")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                csv_path = input("Caminho do arquivo CSV: ").strip()
                if not os.path.exists(csv_path):
                    print("Arquivo não encontrado!")
                    continue
                    
                objects = FileHandler.read_csv(csv_path)
                for i, obj in enumerate(objects):
                    obj.ID_registro = i + 1
                FileHandler.write_db(objects, db_path)
            elif choice == "2":
                objects = FileHandler.read_db(db_path)
                if not objects:
                    print("Nenhum registro encontrado!")
                    continue
                    
                for obj in objects:
                    print("\n" + "="*50)
                    print(obj)
            elif choice == "3":
                try:
                    record_id = int(input("ID do registro: ").strip())
                    objects = FileHandler.read_db(db_path)
                    found = [obj for obj in objects if obj.ID_registro == record_id]
                    if found:
                        print("\n" + "="*50)
                        print(found[0])
                    else:
                        print("Registro não encontrado")
                except ValueError:
                    print("ID inválido")
            elif choice == "4":
                try:
                    record_id = int(input("ID do registro para atualizar: ").strip())
                    objects = FileHandler.read_db(db_path)
                    found = [obj for obj in objects if obj.ID_registro == record_id]
                    
                    if found:
                        updated_obj = MenuSystem.update_object_ui(found[0])
                        if FileHandler.update_record(db_path, record_id, updated_obj):
                            print("Registro atualizado com sucesso!")
                    else:
                        print("Registro não encontrado")
                except ValueError:
                    print("ID inválido")
            elif choice == "5":
                try:
                    record_id = int(input("ID do registro para excluir: ").strip())
                    if FileHandler.delete_record(db_path, record_id):
                        print("Registro excluído com sucesso!")
                except ValueError:
                    print("ID inválido")
            elif choice == "6":
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def part2_menu():
        """Display Part 2 menu and handle user input"""
        data_path = "indexed_data/traffic_accidents.db"
        index_path = "indexed_data/indexTrafficAccidents.db"
        os.makedirs("indexed_data", exist_ok=True)
        
        while True:
            print("\n" + "="*50)
            print("Parte II - Indexação e Busca")
            print("="*50)
            print("1. Importar dados de CSV (indexado)")
            print("2. Buscar registro por ID (indexado)")
            print("3. Atualizar registro (indexado)")
            print("4. Excluir registro (indexado)")
            print("5. Voltar ao menu principal")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                csv_path = input("Caminho do arquivo CSV: ").strip()
                if not os.path.exists(csv_path):
                    print("Arquivo não encontrado!")
                    continue
                    
                if IndexedFileHandler.write_from_csv(csv_path, data_path, index_path):
                    print("Dados importados com sucesso!")
            elif choice == "2":
                try:
                    record_id = int(input("ID do registro: ").strip())
                    obj = IndexedFileHandler.read_record(data_path, index_path, record_id)
                    if obj:
                        print("\n" + "="*50)
                        print(obj)
                    else:
                        print("Registro não encontrado ou excluído")
                except ValueError:
                    print("ID inválido")
            elif choice == "3":
                try:
                    record_id = int(input("ID do registro para atualizar: ").strip())
                    obj = IndexedFileHandler.read_record(data_path, index_path, record_id)
                    if obj:
                        updated_obj = MenuSystem.update_object_ui(obj)
                        if IndexedFileHandler.update_record(data_path, index_path, record_id, updated_obj):
                            print("Registro atualizado com sucesso!")
                    else:
                        print("Registro não encontrado")
                except ValueError:
                    print("ID inválido")
            elif choice == "4":
                try:
                    record_id = int(input("ID do registro para excluir: ").strip())
                    if IndexedFileHandler.delete_record(data_path, index_path, record_id):
                        print("Registro excluído com sucesso!")
                except ValueError:
                    print("ID inválido")
            elif choice == "5":
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def part3_menu():
        """Display Part 3 menu and handle user input"""
        while True:
            print("\n" + "="*50)
            print("Parte III - Compactação de Dados")
            print("="*50)
            print("1. Compactar arquivo (Huffman)")
            print("2. Descompactar arquivo (Huffman)")
            print("3. Compactar arquivo (Huffman Byte)")
            print("4. Descompactar arquivo (Huffman Byte)")
            print("5. Compactar arquivo (LZW)")
            print("6. Descompactar arquivo (LZW)")
            print("7. Testar algoritmos com arquivo de amostra")
            print("8. Voltar ao menu principal")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                input_file = input("Caminho do arquivo de entrada: ").strip()
                output_file = input("Caminho do arquivo de saída (.huffc): ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo de entrada não encontrado!")
                    continue
                CompressionHandler.huffman_compress(input_file, output_file)
            elif choice == "2":
                input_file = input("Caminho do arquivo compactado (.huffc): ").strip()
                output_file = input("Caminho do arquivo descompactado: ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo compactado não encontrado!")
                    continue
                CompressionHandler.huffman_decompress(input_file, output_file)
            elif choice == "3":
                input_file = input("Caminho do arquivo de entrada: ").strip()
                output_file = input("Caminho do arquivo de saída (.huffb): ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo de entrada não encontrado!")
                    continue
                CompressionHandler.huffman_byte_compress(input_file, output_file)
            elif choice == "4":
                input_file = input("Caminho do arquivo compactado (.huffb): ").strip()
                output_file = input("Caminho do arquivo descompactado: ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo compactado não encontrado!")
                    continue
                CompressionHandler.huffman_byte_decompress(input_file, output_file)
            elif choice == "5":
                input_file = input("Caminho do arquivo de entrada: ").strip()
                output_file = input("Caminho do arquivo de saída (.lzw): ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo de entrada não encontrado!")
                    continue
                CompressionHandler.lzw_compress(input_file, output_file)
            elif choice == "6":
                input_file = input("Caminho do arquivo compactado (.lzw): ").strip()
                output_file = input("Caminho do arquivo descompactado: ").strip()
                if not os.path.exists(input_file):
                    print("Arquivo compactado não encontrado!")
                    continue
                CompressionHandler.lzw_decompress(input_file, output_file)
            elif choice == "7":
                CompressionHandler.test_algorithms()
            elif choice == "8":
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def update_object_ui(obj: DataObject) -> DataObject:
        """Update a DataObject through user input"""
        print("\nAtualize os campos (deixe em branco para manter o valor atual)")
        print("="*50)
        
        # Date and time
        new_date = input(f"Data do Acidente [{obj.crash_date}]: ").strip()
        if new_date:
            obj.set_crash_date_from_timestamp(new_date)
        
        # String fields
        fields = [
            ("Dispositivo de controle de tráfego", "traffic_control_device"),
            ("Condição climática", "weather_condition"),
            ("Tipo de primeira colisão", "first_crash_type"),
            ("Tipo de via de tráfego", "trafficway_type"),
            ("Alinhamento", "alignment"),
            ("Condição da superfície da via", "roadway_surface_cond"),
            ("Defeito na estrada", "road_defect"),
            ("Danos", "damage"),
            ("Causa contributiva primária", "prim_contributory_cause")
        ]
        
        for label, attr in fields:
            current_val = getattr(obj, attr)
            new_val = input(f"{label} [{current_val}]: ").strip()
            if new_val:
                setattr(obj, attr, new_val)
        
        # List fields
        list_fields = [
            ("Condições de iluminação (separadas por vírgula)", "lighting_condition"),
            ("Tipos de acidente (separados por vírgula)", "crash_type"),
            ("Ferimentos mais graves (separados por vírgula)", "most_severe_injury")
        ]
        
        for label, attr in list_fields:
            current = ", ".join(getattr(obj, attr))
            new_val = input(f"{label} [{current}]: ").strip()
            if new_val:
                setattr(obj, attr, [s.strip() for s in new_val.split(",")])
        
        # Boolean field
        intersection = input(f"Interseção relacionada (S/N) [{obj.get_intersection_related_str()}]: ").strip()
        if intersection:
            obj.set_intersection_related_from_str(intersection)
        
        # Numeric fields
        numeric_fields = [
            ("Número de unidades", "num_units", int),
            ("Total de ferimentos", "injuries_total", float),
            ("Ferimentos fatais", "injuries_fatal", float),
            ("Lesões incapacitantes", "injuries_incapacitating", float),
            ("Lesões não incapacitantes", "injuries_non_incapacitating", float),
            ("Lesões relatadas não evidentes", "injuries_reported_not_evident", float),
            ("Lesões sem indicação", "injuries_no_indication", float),
            ("Hora do acidente", "crash_hour", int)
        ]
        
        for label, attr, conv_type in numeric_fields:
            current_val = getattr(obj, attr)
            while True:
                new_val = input(f"{label} [{current_val}]: ").strip()
                if not new_val:
                    break
                try:
                    setattr(obj, attr, conv_type(new_val))
                    break
                except ValueError:
                    print(f"Valor inválido. Digite um {'número inteiro' if conv_type == int else 'número'}.")
        
        print("\nRegistro atualizado:")
        print("="*50)
        print(obj)
        return obj


# ==============================================
# Main Execution
# ==============================================
if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("indexed_data", exist_ok=True)
    
    # Start the menu system
    MenuSystem.main_menu()