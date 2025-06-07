import datetime
import struct
from typing import List, Tuple

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
            self.crash_day_of_week = self.data.isoweekday()  # Monday=1, Sunday=7
            self.crash_month = self.data.month
        except Exception as e:
            print(f"Error setting date: {e}")

    def get_intersection_related_str(self) -> str:
        return "S" if self.intersection_related_i else "N"
    
    def set_intersection_related_from_str(self, value: str):
        self.intersection_related_i = value.strip().upper() == "S"

    def list_to_string(self, lst: List[str]) -> str:
        return " , ".join(lst)

    def string_to_list(self, s: str, delimiter: str) -> List[str]:
        return [item.strip() for item in s.split(delimiter)] if s else []

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
            obj.lighting_condition = obj.string_to_list(lighting_str, ',')
            
            obj.first_crash_type, offset = cls._unpack_string(data, offset)
            obj.trafficway_type, offset = cls._unpack_string(data, offset)
            obj.alignment, offset = cls._unpack_string(data, offset)
            obj.roadway_surface_cond, offset = cls._unpack_string(data, offset)
            obj.road_defect, offset = cls._unpack_string(data, offset)
            
            crash_type_str, offset = cls._unpack_string(data, offset)
            obj.crash_type = obj.string_to_list(crash_type_str, ',')
            
            intersection_str, offset = cls._unpack_string(data, offset)
            obj.set_intersection_related_from_str(intersection_str)
            
            obj.damage, offset = cls._unpack_string(data, offset)
            obj.prim_contributory_cause, offset = cls._unpack_string(data, offset)
            
            # Unpack integers and floats
            obj.num_units = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            
            severe_injury_str, offset = cls._unpack_string(data, offset)
            obj.most_severe_injury = obj.string_to_list(severe_injury_str, ',')
            
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
            f"\nID Registro---------------------------> {self.ID_registro}"
            f"\nData do Acidente----------------------> {self.crash_date}"
            f"\nData por LocalDate--------------------> {self.data.strftime(self.DATE_FORMAT)}"
            f"\nDispositivo de controle de tráfego----> {self.traffic_control_device}"
            f"\nCondição climática--------------------> {self.weather_condition}"
            f"\nCondição de iluminação----------------> {self.list_to_string(self.lighting_condition)}"
            f"\nTipo de primeira colisão--------------> {self.first_crash_type}"
            f"\nTipo de via de tráfego----------------> {self.trafficway_type}"
            f"\nAlinhamento---------------------------> {self.alignment}"
            f"\nCondição da superfície da via---------> {self.roadway_surface_cond}"
            f"\nDefeito na estrada--------------------> {self.road_defect}"
            f"\nTipo de acidente----------------------> {self.list_to_string(self.crash_type)}"
            f"\nInterseção relacionada i--------------> {self.get_intersection_related_str()}"
            f"\nDanos---------------------------------> {self.damage}"
            f"\nCausa contributiva primária-----------> {self.prim_contributory_cause}"
            f"\nNumero de Unidades--------------------> {self.num_units}"
            f"\nFerimento mais grave------------------> {self.list_to_string(self.most_severe_injury)}"
            f"\nTotal de ferimentos-------------------> {self.injuries_total}"
            f"\nFerimentos fatais---------------------> {self.injuries_fatal}"
            f"\nLesões incapacitantes-----------------> {self.injuries_incapacitating}"
            f"\nLesões não incapacitantes-------------> {self.injuries_non_incapacitating}"
            f"\nLesões relatadas não evidentes--------> {self.injuries_reported_not_evident}"
            f"\nLesões sem indicação------------------> {self.injuries_no_indication}"
            f"\nHora do acidente----------------------> {self.crash_hour}"
            f"\nDia da Semana do acidente-------------> {self.crash_day_of_week}"
            f"\nMês do acidente-----------------------> {self.crash_month}"
        )


class DataIndex:
    DATE_FORMAT = "%d/%m/%Y"
    
    def __init__(self, 
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
            self.crash_day_of_week = self.data.isoweekday()  # Monday=1, Sunday=7
            self.crash_month = self.data.month
        except Exception as e:
            print(f"Error setting date: {e}")

    def get_intersection_related_str(self) -> str:
        return "S" if self.intersection_related_i else "N"
    
    def set_intersection_related_from_str(self, value: str):
        self.intersection_related_i = value.strip().upper() == "S"

    def list_to_string(self, lst: List[str]) -> str:
        return " , ".join(lst)

    def string_to_list(self, s: str, delimiter: str) -> List[str]:
        return [item.strip() for item in s.split(delimiter)] if s else []

    def to_byte_array(self) -> bytes:
        try:
            ba = bytearray()
            # Pack strings and date
            ba += self._pack_string(self.crash_date)
            
            epoch = datetime.date(1970, 1, 1)
            days = (self.data - epoch).days
            ba += struct.pack('>q', days)
            
            ba += self._pack_string(self.traffic_control_device)
            ba += self._pack_string(self.weather_condition)
            
            # Pack array lengths and content
            ba += struct.pack('>i', len(self.lighting_condition))
            ba += self._pack_string(self.list_to_string(self.lighting_condition))
            
            # Pack remaining strings
            ba += self._pack_string(self.first_crash_type)
            ba += self._pack_string(self.trafficway_type)
            ba += self._pack_string(self.alignment)
            ba += self._pack_string(self.roadway_surface_cond)
            ba += self._pack_string(self.road_defect)
            
            # Pack crash_type array
            ba += struct.pack('>i', len(self.crash_type))
            ba += self._pack_string(self.list_to_string(self.crash_type))
            
            ba += self._pack_string(self.get_intersection_related_str())
            ba += self._pack_string(self.damage)
            ba += self._pack_string(self.prim_contributory_cause)
            ba += struct.pack('>i', self.num_units)
            
            # Pack most_severe_injury array
            ba += struct.pack('>i', len(self.most_severe_injury))
            ba += self._pack_string(self.list_to_string(self.most_severe_injury))
            
            # Pack floats and integers
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
            
            # Unpack strings and date
            obj.crash_date, offset = cls._unpack_string(data, offset)
            
            days = struct.unpack_from('>q', data, offset)[0]
            offset += 8
            obj.data = datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
            
            obj.traffic_control_device, offset = cls._unpack_string(data, offset)
            obj.weather_condition, offset = cls._unpack_string(data, offset)
            
            # Unpack lighting_condition array
            length = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            lighting_str, offset = cls._unpack_string(data, offset)
            obj.lighting_condition = obj.string_to_list(lighting_str, ',')
            
            # Unpack remaining strings
            obj.first_crash_type, offset = cls._unpack_string(data, offset)
            obj.trafficway_type, offset = cls._unpack_string(data, offset)
            obj.alignment, offset = cls._unpack_string(data, offset)
            obj.roadway_surface_cond, offset = cls._unpack_string(data, offset)
            obj.road_defect, offset = cls._unpack_string(data, offset)
            
            # Unpack crash_type array
            length = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            crash_type_str, offset = cls._unpack_string(data, offset)
            obj.crash_type = obj.string_to_list(crash_type_str, ',')
            
            # Unpack boolean string
            intersection_str, offset = cls._unpack_string(data, offset)
            obj.set_intersection_related_from_str(intersection_str)
            
            obj.damage, offset = cls._unpack_string(data, offset)
            obj.prim_contributory_cause, offset = cls._unpack_string(data, offset)
            obj.num_units = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            
            # Unpack most_severe_injury array
            length = struct.unpack_from('>i', data, offset)[0]
            offset += 4
            severe_injury_str, offset = cls._unpack_string(data, offset)
            obj.most_severe_injury = obj.string_to_list(severe_injury_str, ',')
            
            # Unpack floats and integers
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
        if s is None:
            s = ""
        encoded = s.encode('utf-8')
        return struct.pack('>H', len(encoded)) + encoded

    @staticmethod
    def _unpack_string(data: bytes, offset: int) -> Tuple[str, int]:
        length = struct.unpack_from('>H', data, offset)[0]
        offset += 2
        s = data[offset:offset+length].decode('utf-8')
        return s, offset + length

    def __str__(self):
        return (
            f"\nData do Acidente----------------------> {self.crash_date}"
            f"\nData por LocalDate--------------------> {self.data.strftime(self.DATE_FORMAT)}"
            f"\nDispositivo de controle de tráfego----> {self.traffic_control_device}"
            f"\nCondição climática--------------------> {self.weather_condition}"
            f"\nCondição de iluminação----------------> {self.list_to_string(self.lighting_condition)}"
            f"\nTipo de primeira colisão--------------> {self.first_crash_type}"
            f"\nTipo de via de tráfego----------------> {self.trafficway_type}"
            f"\nAlinhamento---------------------------> {self.alignment}"
            f"\nCondição da superfície da via---------> {self.roadway_surface_cond}"
            f"\nDefeito na estrada--------------------> {self.road_defect}"
            f"\nTipo de acidente----------------------> {self.list_to_string(self.crash_type)}"
            f"\nInterseção relacionada i--------------> {self.get_intersection_related_str()}"
            f"\nDanos---------------------------------> {self.damage}"
            f"\nCausa contributiva primária-----------> {self.prim_contributory_cause}"
            f"\nNumero de Unidades--------------------> {self.num_units}"
            f"\nFerimento mais grave------------------> {self.list_to_string(self.most_severe_injury)}"
            f"\nTotal de ferimentos-------------------> {self.injuries_total}"
            f"\nFerimentos fatais---------------------> {self.injuries_fatal}"
            f"\nLesões incapacitantes-----------------> {self.injuries_incapacitating}"
            f"\nLesões não incapacitantes-------------> {self.injuries_non_incapacitating}"
            f"\nLesões relatadas não evidentes--------> {self.injuries_reported_not_evident}"
            f"\nLesões sem indicação------------------> {self.injuries_no_indication}"
            f"\nHora do acidente----------------------> {self.crash_hour}"
            f"\nDia da Semana do acidente-------------> {self.crash_day_of_week}"
            f"\nMês do acidente-----------------------> {self.crash_month}"
        )


class Index:
    def __init__(self, key: int = 0, pointer: int = -1, lapide: bool = False):
        self.key = key
        self.pointer = pointer
        self.lapide = lapide

    def to_byte_array(self) -> bytes:
        try:
            return struct.pack('>?iq', self.lapide, self.key, self.pointer)
        except Exception as e:
            print(f"Serialization error: {e}")
            return b''

    @classmethod
    def from_byte_array(cls, data: bytes):
        try:
            lapide = struct.unpack_from('>?', data, 0)[0]
            key = struct.unpack_from('>i', data, 1)[0]
            pointer = struct.unpack_from('>q', data, 5)[0]
            return cls(key, pointer, lapide)
        except Exception as e:
            print(f"Deserialization error: {e}")
            return None

    def __str__(self):
        return (
            f"\nID Registro---------------------------> {self.key}"
            f"\nPosição-------------------------------> {self.pointer}"
            f"\nValidade------------------------------> {self.lapide}"
        )