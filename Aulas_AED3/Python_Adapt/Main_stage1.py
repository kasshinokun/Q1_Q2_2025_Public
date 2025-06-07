import os
import csv
import struct
import datetime
from typing import List, Dict, Optional, Tuple

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

    def list_to_string(self, lst: List[str]) -> str:
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
            ba += self._pack_string(self.traffic_control_device)
            ba += self._pack_string(self.weather_condition)
            ba += self._pack_string(self.list_to_string(self.lighting_condition))
            ba += self._pack_string(self.first_crash_type)
            ba += self._pack_string(self.trafficway_type)
            ba += self._pack_string(self.alignment)
            ba += self._pack_string(self.roadway_surface_cond)
            ba += self._pack_string(self.road_defect)
            ba += self._pack_string(self.list_to_string(self.crash_type))
            ba += self._pack_string(self.get_intersection_related_str())
            ba += self._pack_string(self.damage)
            ba += self._pack_string(self.prim_contributory_cause)
            
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
            obj.traffic_control_device, offset = cls._unpack_string(data, offset)
            obj.weather_condition, offset = cls._unpack_string(data, offset)
            
            lighting_str, offset = cls._unpack_string(data, offset)
            obj.lighting_condition = [s.strip() for s in lighting_str.split(',')] if lighting_str else []
            
            obj.first_crash_type, offset = cls._unpack_string(data, offset)
            obj.trafficway_type, offset = cls._unpack_string(data, offset)
            obj.alignment, offset = cls._unpack_string(data, offset)
            obj.roadway_surface_cond, offset = cls._unpack_string(data, offset)
            obj.road_defect, offset = cls._unpack_string(data, offset)
            
            crash_type_str, offset = cls._unpack_string(data, offset)
            obj.crash_type = [s.strip() for s in crash_type_str.split(',')] if crash_type_str else []
            
            intersection_str, offset = cls._unpack_string(data, offset)
            obj.set_intersection_related_from_str(intersection_str)
            
            obj.damage, offset = cls._unpack_string(data, offset)
            obj.prim_contributory_cause, offset = cls._unpack_string(data, offset)
            
            # Unpack integers and floats
            obj.num_units = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            
            severe_injury_str, offset = cls._unpack_string(data, offset)
            obj.most_severe_injury = [s.strip() for s in severe_injury_str.split(',')] if severe_injury_str else []
            
            obj.injuries_total = struct.unpack_from('>f', data, offset)[0]
            offset += 4
            obj.injuries_fatal = struct.unpack_from('>f', data, offset)[0]
            offset += 4
            obj.injuries_incapacitating = struct.unpack_from('>f', data, offset)[0]
            offset += 4
            obj.injuries_non_incapacitating = struct.unpack_from('>f', data, offset)[0]
            offset += 4
            obj.injuries_reported_not_evident = struct.unpack_from('>f', data, offset)[0]
            offset += 4
            obj.injuries_no_indication = struct.unpack_from('>f', data, offset)[0]
            offset += 4
            
            obj.crash_hour = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            obj.crash_day_of_week = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            obj.crash_month = struct.unpack_from('>i', data, offset)[0]
            
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
            f"Total de ferimentos: {self.injuries_total}\n"
            f"Ferimentos fatais: {self.injuries_fatal}\n"
            f"Lesões incapacitantes: {self.injuries_incapacitating}\n"
            f"Lesões não incapacitantes: {self.injuries_non_incapacitating}\n"
            f"Lesões relatadas não evidentes: {self.injuries_reported_not_evident}\n"
            f"Lesões sem indicação: {self.injuries_no_indication}\n"
            f"Hora do acidente: {self.crash_hour}\n"
            f"Dia da semana: {self.crash_day_of_week}\n"
            f"Mês: {self.crash_month}"
        )

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
                    if len(row) < 24:
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
                    obj.num_units = int(row[13])
                    obj.most_severe_injury = [s.strip() for s in row[14].split(',')] if row[14] else []
                    obj.injuries_total = float(row[15])
                    obj.injuries_fatal = float(row[16])
                    obj.injuries_incapacitating = float(row[17])
                    obj.injuries_non_incapacitating = float(row[18])
                    obj.injuries_reported_not_evident = float(row[19])
                    obj.injuries_no_indication = float(row[20])
                    obj.crash_hour = int(row[21])
                    objects.append(obj)
            print(f"Successfully read {len(objects)} records from CSV")
        except Exception as e:
            print(f"Error reading CSV: {e}")
        return objects

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
        except Exception as e:
            print(f"Error reading database: {e}")
        return objects

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
        except Exception as e:
            print(f"Error updating record: {e}")

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
                        return
                    
                    # Move to next record
                    file.seek(pos + 4 + 1 + 4 + size)
            print(f"Record {record_id} not found")
        except Exception as e:
            print(f"Error deleting record: {e}")

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
            print("3. Parte III - Compactação")
            print("4. Sair")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                MenuSystem.part1_menu()
            elif choice == "2":
                print("Funcionalidade da Parte II ainda não implementada")
            elif choice == "3":
                print("Funcionalidade da Parte III ainda não implementada")
            elif choice == "4":
                print("Saindo do sistema...")
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def part1_menu():
        """Display Part 1 menu and handle user input"""
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
            db_path = "data/traffic_accidents.db"
            
            if choice == "1":
                csv_path = input("Caminho do arquivo CSV: ").strip()
                objects = FileHandler.read_csv(csv_path)
                for i, obj in enumerate(objects):
                    obj.ID_registro = i + 1
                FileHandler.write_db(objects, db_path)
            elif choice == "2":
                objects = FileHandler.read_db(db_path)
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
                        FileHandler.update_record(db_path, record_id, updated_obj)
                    else:
                        print("Registro não encontrado")
                except ValueError:
                    print("ID inválido")
            elif choice == "5":
                try:
                    record_id = int(input("ID do registro para excluir: ").strip())
                    FileHandler.delete_record(db_path, record_id)
                except ValueError:
                    print("ID inválido")
            elif choice == "6":
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
            new_val = input(f"{label} [{getattr(obj, attr)}]: ").strip()
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
            ("Número de unidades", "num_units"),
            ("Total de ferimentos", "injuries_total"),
            ("Ferimentos fatais", "injuries_fatal"),
            ("Lesões incapacitantes", "injuries_incapacitating"),
            ("Lesões não incapacitantes", "injuries_non_incapacitating"),
            ("Lesões relatadas não evidentes", "injuries_reported_not_evident"),
            ("Lesões sem indicação", "injuries_no_indication"),
            ("Hora do acidente", "crash_hour")
        ]
        
        for label, attr in numeric_fields:
            while True:
                new_val = input(f"{label} [{getattr(obj, attr)}]: ").strip()
                if not new_val:
                    break
                try:
                    if attr == "num_units" or attr == "crash_hour":
                        setattr(obj, attr, int(new_val))
                    else:
                        setattr(obj, attr, float(new_val))
                    break
                except ValueError:
                    print("Valor inválido. Digite um número.")
        
        print("\nRegistro atualizado:")
        print("="*50)
        print(obj)
        return obj

if __name__ == "__main__":
    # Create data directory if not exists
    os.makedirs("data", exist_ok=True)
    
    # Start the menu system
    MenuSystem.main_menu()