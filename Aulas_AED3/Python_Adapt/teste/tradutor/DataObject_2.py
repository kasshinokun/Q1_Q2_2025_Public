import datetime
from typing import List, Dict, Any, Union

class DataObject:
    DATE_FORMAT = "%d/%m/%Y"
    
    def __init__(self):
        self.crash_date: str = ""
        self.data: datetime.date = datetime.date(1900, 1, 1)
        self.traffic_control_device: str = ""
        self.weather_condition: str = ""
        self.lighting_condition: List[str] = []
        self.first_crash_type: str = ""
        self.trafficway_type: str = ""
        self.alignment: str = ""
        self.roadway_surface_cond: str = ""
        self.road_defect: str = ""
        self.crash_type: List[str] = []
        self.intersection_related_i: bool = False
        self.damage: str = ""
        self.prim_contributory_cause: str = ""
        self.num_units: int = 0
        self.most_severe_injury: List[str] = []
        self.injuries_total: float = 0.0
        self.injuries_fatal: float = 0.0
        self.injuries_incapacitating: float = 0.0
        self.injuries_non_incapacitating: float = 0.0
        self.injuries_reported_not_evident: float = 0.0
        self.injuries_no_indication: float = 0.0
        self.crash_hour: int = 0
        self.crash_day_of_week: int = 0
        self.crash_month: int = 0

    def set_crash_date_from_timestamp(self, crash_date: str) -> None:
        try:
            date_str = crash_date.split()[0]
            self.data = datetime.datetime.strptime(date_str, self.DATE_FORMAT).date()
            self.crash_date = crash_date
            self.crash_day_of_week = self.data.isoweekday()
            self.crash_month = self.data.month
        except Exception as e:
            print(f"Error setting date: {e}")

    def set_string_intersection_related_i(self, value: str) -> None:
        self.intersection_related_i = self.get_boolean_from_string(value)

    @staticmethod
    def get_boolean_from_string(s: str) -> bool:
        return s.strip().upper().startswith('S') if s else False

    @staticmethod
    def get_string_from_boolean(b: bool) -> str:
        return 'S' if b else 'N'

    @classmethod
    def from_string_list(cls, string_list: List[str]) -> 'DataObject':
        instance = cls()
        if len(string_list) < 22:
            return instance
        
        try:
            # Reformat date from MM/DD/YYYY to DD/MM/YYYY
            date_str = string_list[0]
            reformatted_date = (
                f"{date_str[3:5]}/{date_str[0:2]}/{date_str[6:10]} "
                f"{date_str[11:]}"
            )
            instance.set_crash_date_from_timestamp(reformatted_date)
            
            # Set other fields
            instance.traffic_control_device = string_list[1]
            instance.weather_condition = string_list[2]
            instance.lighting_condition = [s.strip() for s in string_list[3].split(',')]
            instance.first_crash_type = string_list[4]
            instance.trafficway_type = string_list[5]
            instance.alignment = string_list[6]
            instance.roadway_surface_cond = string_list[7]
            instance.road_defect = string_list[8]
            instance.crash_type = [s.strip() for s in string_list[9].split('/')]
            instance.set_string_intersection_related_i(string_list[10])
            instance.damage = string_list[11]
            instance.prim_contributory_cause = string_list[12]
            instance.num_units = int(string_list[13])
            instance.most_severe_injury = [s.strip() for s in string_list[14].split(',')]
            instance.injuries_total = float(string_list[15])
            instance.injuries_fatal = float(string_list[16])
            instance.injuries_incapacitating = float(string_list[17])
            instance.injuries_non_incapacitating = float(string_list[18])
            instance.injuries_reported_not_evident = float(string_list[19])
            instance.injuries_no_indication = float(string_list[20])
            instance.crash_hour = int(string_list[21])
        except Exception as e:
            print(f"Error creating from string list: {e}")
        return instance

    def __str__(self) -> str:
        """Human-readable representation of the object"""
        return (
            f"DataObject(crash_date='{self.crash_date}', "
            f"traffic_control_device='{self.traffic_control_device}', "
            f"weather_condition='{self.weather_condition}', "
            f"first_crash_type='{self.first_crash_type}', "
            f"num_units={self.num_units}, "
            f"crash_hour={self.crash_hour})"
        )

    def __repr__(self) -> str:
        """Official string representation of the object"""
        return (
            f"DataObject(\n"
            f"  crash_date='{self.crash_date}',\n"
            f"  data=datetime.date({self.data.year}, {self.data.month}, {self.data.day}),\n"
            f"  traffic_control_device='{self.traffic_control_device}',\n"
            f"  weather_condition='{self.weather_condition}',\n"
            f"  lighting_condition={self.lighting_condition},\n"
            f"  first_crash_type='{self.first_crash_type}',\n"
            f"  trafficway_type='{self.trafficway_type}',\n"
            f"  alignment='{self.alignment}',\n"
            f"  roadway_surface_cond='{self.roadway_surface_cond}',\n"
            f"  road_defect='{self.road_defect}',\n"
            f"  crash_type={self.crash_type},\n"
            f"  intersection_related_i={self.intersection_related_i},\n"
            f"  damage='{self.damage}',\n"
            f"  prim_contributory_cause='{self.prim_contributory_cause}',\n"
            f"  num_units={self.num_units},\n"
            f"  most_severe_injury={self.most_severe_injury},\n"
            f"  injuries_total={self.injuries_total},\n"
            f"  injuries_fatal={self.injuries_fatal},\n"
            f"  injuries_incapacitating={self.injuries_incapacitating},\n"
            f"  injuries_non_incapacitating={self.injuries_non_incapacitating},\n"
            f"  injuries_reported_not_evident={self.injuries_reported_not_evident},\n"
            f"  injuries_no_indication={self.injuries_no_indication},\n"
            f"  crash_hour={self.crash_hour},\n"
            f"  crash_day_of_week={self.crash_day_of_week},\n"
            f"  crash_month={self.crash_month}\n"
            f")"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary representation"""
        return {
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

    @staticmethod
    def validate_dict(data: Dict[str, Any]) -> bool:
        """Validate if a dictionary contains all required fields with correct types"""
        required_fields = {
            'crash_date': str,
            'traffic_control_device': str,
            'weather_condition': str,
            'lighting_condition': list,
            'first_crash_type': str,
            'trafficway_type': str,
            'alignment': str,
            'roadway_surface_cond': str,
            'road_defect': str,
            'crash_type': list,
            'intersection_related_i': bool,
            'damage': str,
            'prim_contributory_cause': str,
            'num_units': int,
            'most_severe_injury': list,
            'injuries_total': (float, int),
            'injuries_fatal': (float, int),
            'injuries_incapacitating': (float, int),
            'injuries_non_incapacitating': (float, int),
            'injuries_reported_not_evident': (float, int),
            'injuries_no_indication': (float, int),
            'crash_hour': int,
            'crash_day_of_week': int,
            'crash_month': int
        }

        # Check if all required fields are present
        if not all(field in data for field in required_fields):
            return False

        # Check field types
        for field, field_type in required_fields.items():
            value = data[field]
            
            # Handle multiple allowed types
            if isinstance(field_type, tuple):
                if not isinstance(value, field_type):
                    return False
            else:
                if not isinstance(value, field_type):
                    return False

        # Additional validation for date format
        try:
            date_part = data['crash_date'].split()[0]
            datetime.datetime.strptime(date_part, DataObject.DATE_FORMAT)
        except (ValueError, IndexError):
            return False

        return True