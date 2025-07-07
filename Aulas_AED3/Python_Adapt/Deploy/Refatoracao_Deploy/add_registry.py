import locale
import streamlit as st
import os
import datetime
import re
from typing import List, Dict, Any, Optional

class Functions:
    """
    A collection of utility methods for handling various tasks such as user input, 
    file and directory operations, date and time formatting, and file path manipulation.
    """

    def __init__(self):
        # The scanner is not needed in Python as input() handles reading
        pass

    @staticmethod
    def only_int() -> int:
        """
        Reads an integer from the console. If the input is not an integer, 
        it prints an error message and prompts again.
        """
        while True:
            try:
                value = int(input("Por favor, digite um número inteiro: "))
                return value
            except ValueError:
                print("Entrada inválida. Por favor, digite um número inteiro.")

    @staticmethod
    def only_float() -> float:
        """
        Reads a float from the console. If the input is not a float, 
        it prints an error message and prompts again.
        """
        while True:
            try:
                value = float(input("Por favor, digite um número flutuante: "))
                return value
            except ValueError:
                print("Entrada inválida. Por favor, digite um número flutuante.")

    @staticmethod
    def only_double() -> float:
        """
        Reads a double (float in Python) from the console. If the input is not a float, 
        it prints an error message and prompts again.
        """
        while True:
            try:
                value = float(input("Por favor, digite um número decimal: "))
                return value
            except ValueError:
                print("Entrada inválida. Por favor, digite um número decimal.")

    @staticmethod
    def only_long() -> int:
        """
        Reads a long (integer in Python) from the console. If the input is not an integer, 
        it prints an error message and prompts again.
        """
        while True:
            try:
                value = int(input("Por favor, digite um número longo: "))
                return value
            except ValueError:
                print("Entrada inválida. Por favor, digite um número longo.")

    @staticmethod
    def reading() -> str:
        """
        Reads a line of string input from the console.
        """
        return input()

    @staticmethod
    def get_year_now() -> int:
        """
        Returns the current year.
        """
        return datetime.date.today().year

    @staticmethod
    def find_file(path: str) -> bool:
        """
        Checks if a file exists at the specified path.
        """
        return os.path.exists(path)

    @staticmethod
    def check_directory(path: str) -> None:
        """
        Creates a directory at the specified path if it does not already exist.
        """
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def get_boolean_from_string(root: str) -> bool:
        """
        Converts a string to a boolean. Returns True if the trimmed string 
        (case-insensitive) is "S", otherwise False.
        """
        return root is not None and root.strip().upper() == "S"

    @staticmethod
    def get_string_from_boolean(request: bool) -> str:
        """
        Converts a boolean to a string. Returns "S" if request is True, otherwise "N".
        """
        return "S" if request else "N"

    @staticmethod
    def date_to_string(datetime_str: str) -> str:
        """
        Converts a date and time string (expected format: "MM/dd/yyyy hh:mm:ss a") 
        into a formatted string showing "Data de Registro: DD/MM/YYYY" 
        and "Horario --------: HH:mm:ss".
        Handles ParseException and prints an error if the input date format is invalid.
        """
        try:
            # Python's strptime handles AM/PM with %p
            dt_object = datetime.datetime.strptime(datetime_str, "%m/%d/%Y %I:%M:%S %p")
            formatted_date = dt_object.strftime("%d/%m/%Y")
            formatted_time = dt_object.strftime("%H:%M:%S")
            return f"Data de Registro: {formatted_date}\nHorario --------: {formatted_time}"
        except ValueError as e:
            print(f"Erro ao analisar a data: {e}")
            return "Data Inválida"

    @staticmethod
    def get_day_week(date: datetime.date) -> int:
        """
        Returns the day of the week (1 for Monday, 7 for Sunday) for a given date.
        """
        return date.isoweekday() # Monday is 1, Sunday is 7

    @staticmethod
    def get_num_month(date: datetime.date) -> int:
        """
        Returns the month value (1-12) for a given date.
        """
        return date.month

    @staticmethod
    def get_count_list() -> int:
        """
        Prompts the user to enter the quantity of items to be listed. 
        It ensures the input is an integer and is at least 1.
        """
        count = 0
        while count < 1:
            print("\nPor favor, digite a quantidade de itens a ser listada:")
            count = Functions.only_int()
            if count < 1:
                print("A quantidade deve ser pelo menos 1.")
        return count

    @staticmethod
    def generate_string_list(enunciado: str, count: int) -> List[str]:
        """
        Generates a list of strings by prompting the user for `count` number of inputs, 
        prefixed with an `enunciado` (statement/prompt).
        """
        result = []
        for i in range(count):
            print(f"{enunciado}{i + 1}: ")
            result.append(Functions.reading())
        return result
    def check_time_input(date_set,hour_set):
        # Validação e feedback para o usuário (já que não há min_value/max_value no time_input)
        if date_set == datetime.date.today():
            current_datetime = datetime.datetime.now()
            selected_datetime_combined = datetime.datetime.combine(date_set, hour_set)

            if selected_datetime_combined > current_datetime:
                st.warning("A hora selecionada está no futuro para a data atual. Por favor, ajuste a hora.")
                return current_datetime.time()
            elif selected_datetime_combined == current_datetime:
                st.info("A hora selecionada é a hora atual.")
                return hour_set
            elif selected_datetime_combined < current_datetime:
                st.info("A hora selecionada é uma hora válida.")
                return hour_set
            else:
                st.success("Hora válida selecionada para a data atual.")
                return hour_set
        else:
            st.success("Hora válida selecionada para a data passada.")
            return hour_set
class DataObject:
    """
    Representa um único registro de acidente, analisando dados de linhas CSV.
    """

    # Class-level attribute for date time formatting, similar to static final in Java
    DATE_TIME_FORMATTER = "%m/%d/%Y %I:%M:%S %p" # %I for 12-hour, %p for AM/PM

    def __init__(self,
                 default_time_string: str,
                 traffic_control_device: str,
                 weather_condition: str,
                 lighting_condition_str: str, # Changed from List to str for initial constructor input
                 first_crash_type: str,
                 trafficway_type: str,
                 alignment: str,
                 roadway_surface_cond: str,
                 road_defect: str,
                 crash_type_str: str, # Changed from List to str for initial constructor input
                 intersection_related_i_str: str, # Changed from bool to str for initial constructor input
                 damage: str,
                 prim_contributory_cause: str,
                 num_units: int,
                 most_severe_injury_str: str, # Changed from List to str for initial constructor input
                 injuries_total: float,
                 injuries_fatal: float,
                 injuries_incapacitating: float,
                 injuries_non_incapacitating: float,
                 injuries_reported_not_evident: float,
                 injuries_no_indication: float,
                 crash_hour: int,
                 crash_day_of_week: int,
                 crash_month: int,
                 _from_map: bool = False, # Internal flag for map constructor
                 _raw_data_map: Optional[Dict[str, Any]] = None # Raw map data for map constructor
                 ):

        if _from_map and _raw_data_map:
            # Constructor for deserialization from a dictionary (map)
            data_map = _raw_data_map
            self._default_time_string = data_map.get("default_time_string")
            self._crash_date = self._parse_datetime(self._default_time_string)
            self._traffic_control_device = data_map.get("traffic_control_device")
            self._weather_condition = data_map.get("weather_condition")
            self._lighting_condition = self._to_list_of_strings(data_map.get("lighting_condition"))
            self._first_crash_type = data_map.get("first_crash_type")
            self._trafficway_type = data_map.get("trafficway_type")
            self._alignment = data_map.get("alignment")
            self._roadway_surface_cond = data_map.get("roadway_surface_cond")
            self._road_defect = data_map.get("road_defect")
            self._crash_type = self._to_list_of_strings(data_map.get("crash_type"))
            self._intersection_related_i = data_map.get("intersection_related_i")
            self._damage = data_map.get("damage")
            self._prim_contributory_cause = data_map.get("prim_contributory_cause")
            self._num_units = int(data_map.get("num_units", 0))
            self._most_severe_injury = self._to_list_of_strings(data_map.get("most_severe_injury"))
            self._injuries_total = float(data_map.get("injuries_total", 0.0))
            self._injuries_fatal = float(data_map.get("injuries_fatal", 0.0))
            self._injuries_incapacitating = float(data_map.get("injuries_incapacitating", 0.0))
            self._injuries_non_incapacitating = float(data_map.get("injuries_non_incapacitating", 0.0))
            self._injuries_reported_not_evident = float(data_map.get("injuries_reported_not_evident", 0.0))
            self._injuries_no_indication = float(data_map.get("injuries_no_indication", 0.0))
            self._crash_hour = int(data_map.get("crash_hour", 0))
            self._crash_day_of_week = int(data_map.get("crash_day_of_week", 0))
            self._crash_month = int(data_map.get("crash_month", 0))

        else:
            # Original constructor for parsing CSV line data
            self._default_time_string = default_time_string
            self._crash_date = self._parse_datetime(default_time_string)
            self._traffic_control_device = traffic_control_device
            self._weather_condition = weather_condition
            self._lighting_condition = self._to_list_of_strings(lighting_condition_str)
            self._first_crash_type = first_crash_type
            self._trafficway_type = trafficway_type
            self._alignment = alignment
            self._roadway_surface_cond = roadway_surface_cond
            self._road_defect = road_defect
            self._crash_type = self._to_list_of_strings(crash_type_str)
            self._intersection_related_i = Functions.get_boolean_from_string(intersection_related_i_str)
            self._damage = damage
            self._prim_contributory_cause = prim_contributory_cause
            self._num_units = num_units
            self._most_severe_injury = self._to_list_of_strings(most_severe_injury_str)
            self._injuries_total = injuries_total
            self._injuries_fatal = injuries_fatal
            self._injuries_incapacitating = injuries_incapacitating
            self._injuries_non_incapacitating = injuries_non_incapacitating
            self._injuries_reported_not_evident = injuries_reported_not_evident
            self._injuries_no_indication = injuries_no_indication
            self._crash_hour = crash_hour
            # Overwrite crash_day_of_week and crash_month if crash_date was successfully parsed
            self._crash_day_of_week = Functions.get_day_week(self.crash_date.date()) if self.crash_date else crash_day_of_week
            self._crash_month = Functions.get_num_month(self.crash_date.date()) if self.crash_date else crash_month

    @classmethod
    def from_map(cls, data_map: Dict[str, Any]):
        """
        Constructor for deserialization from a dictionary (map).
        This is Pythonic way to provide multiple constructors.
        """
        return cls(
            default_time_string=None, # These are placeholders, actual values come from data_map
            traffic_control_device=None,
            weather_condition=None,
            lighting_condition_str=None,
            first_crash_type=None,
            trafficway_type=None,
            alignment=None,
            roadway_surface_cond=None,
            road_defect=None,
            crash_type_str=None,
            intersection_related_i_str=None,
            damage=None,
            prim_contributory_cause=None,
            num_units=0,
            most_severe_injury_str=None,
            injuries_total=0.0,
            injuries_fatal=0.0,
            injuries_incapacitating=0.0,
            injuries_non_incapacitating=0.0,
            injuries_reported_not_evident=0.0,
            injuries_no_indication=0.0,
            crash_hour=0,
            crash_day_of_week=0,
            crash_month=0,
            _from_map=True,
            _raw_data_map=data_map
        )

    def _parse_datetime(self, time_string: str) -> Optional[datetime.datetime]:
        """
        Parses a date/time string into a datetime object.
        """
        if not time_string or not time_string.strip():
            print("Aviso: String de data/hora vazia ou nula. Retornando None para crash_date.")
            return None
        try:
            return datetime.datetime.strptime(time_string, self.DATE_TIME_FORMATTER)
        except ValueError as e:
            print(f"Erro ao analisar data/hora '{time_string}': {e}")
            print("Verifique se o formato da data no CSV corresponde a 'MM/dd/yyyy hh:mm:ss a' (ex: '01/01/2023 12:00:00 PM').")
            return None

    def _to_list_of_strings(self, value: Optional[str]) -> List[str]:
        """
        Converts a string into a list of strings, splitting by ',' or '/'.
        """
        if not value or not value.strip():
            return []
        
        # Using re.split with a regex pattern to handle both ',' and '/' as delimiters
        # and also handle multiple delimiters or surrounding whitespace
        parts = [s.strip() for s in re.split(r'[,/]+', value) if s.strip()]
        return parts

    def _to_single_string(self, value_list: List[str]) -> str:
        """
        Converts a list of strings back into a single comma-separated string.
        """
        return ",".join(value_list)

    @staticmethod
    def from_csv_row(row_string: str):
        """
        Cria um objeto DataObject a partir de uma linha CSV.
        """
        parts = row_string.strip().split(";")
        
        if len(parts) != 24:
            raise ValueError(
                f"Formato de linha inválido. Esperado 24 colunas, obtido {len(parts)}. Linha: '{row_string}'"
            )

        def safe_int(val: str) -> int:
            try:
                cleaned_val = re.sub(r"[^\d.-]", "", val.strip())
                if not cleaned_val:
                    return 0
                return int(float(cleaned_val))
            except (ValueError, TypeError):
                print(f"Aviso: Falha ao analisar inteiro '{val}'. Usando 0.")
                return 0

        def safe_float(val: str) -> float:
            try:
                cleaned_val = re.sub(r"[^\d.]", "", val.strip())
                if not cleaned_val:
                    return 0.0
                return float(cleaned_val)
            except (ValueError, TypeError):
                print(f"Aviso: Falha ao analisar double/float '{val}'. Usando 0.0.")
                return 0.0

        return DataObject(
            parts[0].strip(),  # default_time_string
            parts[1].strip(),  # traffic_control_device
            parts[2].strip(),  # weather_condition
            parts[3].strip(),  # lighting_condition (passed as string to constructor)
            parts[4].strip(),  # first_crash_type
            parts[5].strip(),  # trafficway_type
            parts[6].strip(),  # alignment
            parts[7].strip(),  # roadway_surface_cond
            parts[8].strip(),  # road_defect
            parts[9].strip(),  # crash_type (passed as string to constructor)
            parts[10].strip(), # intersection_related_i (String "S" or "N")
            parts[11].strip(), # damage
            parts[12].strip(), # prim_contributory_cause
            safe_int(parts[13]),  # num_units
            parts[14].strip(), # most_severe_injury (passed as string to constructor)
            safe_float(parts[15]), # injuries_total
            safe_float(parts[16]), # injuries_fatal
            safe_float(parts[17]), # injuries_incapacitating
            safe_float(parts[18]), # injuries_non_incapacitating
            safe_float(parts[19]), # injuries_reported_not_evident
            safe_float(parts[20]), # injuries_no_indication
            safe_int(parts[21]),  # crash_hour
            safe_int(parts[22]),  # crash_day_of_week (will be overwritten if crash_date is parsed)
            safe_int(parts[23])   # crash_month (will be overwritten if crash_date is parsed)
        )

    def to_map(self) -> Dict[str, Any]:
        """
        Converts the DataObject instance to a dictionary (map).
        """
        data_map = {
            "default_time_string": self.default_time_string,
            "traffic_control_device": self.traffic_control_device,
            "weather_condition": self.weather_condition,
            "lighting_condition": self._to_single_string(self.lighting_condition),
            "first_crash_type": self.first_crash_type,
            "trafficway_type": self.trafficway_type,
            "alignment": self.alignment,
            "roadway_surface_cond": self.roadway_surface_cond,
            "road_defect": self.road_defect,
            "crash_type": self._to_single_string(self.crash_type),
            "intersection_related_i": self.intersection_related_i,
            "damage": self.damage,
            "prim_contributory_cause": self.prim_contributory_cause,
            "num_units": self.num_units,
            "most_severe_injury": self._to_single_string(self.most_severe_injury),
            "injuries_total": self.injuries_total,
            "injuries_fatal": self.injuries_fatal,
            "injuries_incapacitating": self.injuries_incapacitating,
            "injuries_non_incapacitating": self.injuries_non_incapacitating,
            "injuries_reported_not_evident": self.injuries_reported_not_evident,
            "injuries_no_indication": self.injuries_no_indication,
            "crash_hour": self.crash_hour,
            "crash_day_of_week": Functions.get_day_week(self.crash_date.date()) if self.crash_date else 0,
            "crash_month": Functions.get_num_month(self.crash_date.date()) if self.crash_date else 0,
        }
        return data_map

    # Getters (properties in Python)
    @property
    def crash_type(self) -> List[str]:
        return self._crash_type

    @crash_type.setter
    def crash_type(self, value: List[str]):
        self._crash_type = value

    @property
    def injuries_total(self) -> float:
        return self._injuries_total

    @injuries_total.setter
    def injuries_total(self, value: float):
        self._injuries_total = value

    @property
    def lighting_condition(self) -> List[str]:
        return self._lighting_condition

    @lighting_condition.setter
    def lighting_condition(self, value: List[str]):
        self._lighting_condition = value

    @property
    def most_severe_injury(self) -> List[str]:
        return self._most_severe_injury

    @most_severe_injury.setter
    def most_severe_injury(self, value: List[str]):
        self._most_severe_injury = value

    @property
    def default_time_string(self) -> str:
        return self._default_time_string

    @default_time_string.setter
    def default_time_string(self, value: str):
        self._default_time_string = value

    @property
    def traffic_control_device(self) -> str:
        return self._traffic_control_device

    @traffic_control_device.setter
    def traffic_control_device(self, value: str):
        self._traffic_control_device = value

    @property
    def weather_condition(self) -> str:
        return self._weather_condition

    @weather_condition.setter
    def weather_condition(self, value: str):
        self._weather_condition = value

    @property
    def first_crash_type(self) -> str:
        return self._first_crash_type

    @first_crash_type.setter
    def first_crash_type(self, value: str):
        self._first_crash_type = value

    @property
    def trafficway_type(self) -> str:
        return self._trafficway_type

    @trafficway_type.setter
    def trafficway_type(self, value: str):
        self._trafficway_type = value

    @property
    def alignment(self) -> str:
        return self._alignment

    @alignment.setter
    def alignment(self, value: str):
        self._alignment = value

    @property
    def roadway_surface_cond(self) -> str:
        return self._roadway_surface_cond

    @roadway_surface_cond.setter
    def roadway_surface_cond(self, value: str):
        self._roadway_surface_cond = value

    @property
    def road_defect(self) -> str:
        return self._road_defect

    @road_defect.setter
    def road_defect(self, value: str):
        self._road_defect = value

    @property
    def intersection_related_i(self) -> bool:
        return self._intersection_related_i

    @intersection_related_i.setter
    def intersection_related_i(self, value: bool):
        self._intersection_related_i = value

    @property
    def damage(self) -> str:
        return self._damage

    @damage.setter
    def damage(self, value: str):
        self._damage = value

    @property
    def prim_contributory_cause(self) -> str:
        return self._prim_contributory_cause

    @prim_contributory_cause.setter
    def prim_contributory_cause(self, value: str):
        self._prim_contributory_cause = value

    @property
    def num_units(self) -> int:
        return self._num_units

    @num_units.setter
    def num_units(self, value: int):
        self._num_units = value

    @property
    def injuries_fatal(self) -> float:
        return self._injuries_fatal

    @injuries_fatal.setter
    def injuries_fatal(self, value: float):
        self._injuries_fatal = value

    @property
    def injuries_incapacitating(self) -> float:
        return self._injuries_incapacitating

    @injuries_incapacitating.setter
    def injuries_incapacitating(self, value: float):
        self._injuries_incapacitating = value

    @property
    def injuries_non_incapacitating(self) -> float:
        return self._injuries_non_incapacitating

    @injuries_non_incapacitating.setter
    def injuries_non_incapacitating(self, value: float):
        self._injuries_non_incapacitating = value

    @property
    def injuries_reported_not_evident(self) -> float:
        return self._injuries_reported_not_evident

    @injuries_reported_not_evident.setter
    def injuries_reported_not_evident(self, value: float):
        self._injuries_reported_not_evident = value

    @property
    def injuries_no_indication(self) -> float:
        return self._injuries_no_indication

    @injuries_no_indication.setter
    def injuries_no_indication(self, value: float):
        self._injuries_no_indication = value

    @property
    def crash_hour(self) -> int:
        return self._crash_hour

    @crash_hour.setter
    def crash_hour(self, value: int):
        self._crash_hour = value

    @property
    def crash_day_of_week(self) -> int:
        return Functions.get_day_week(self.crash_date.date()) if self.crash_date else self._crash_day_of_week

    @crash_day_of_week.setter
    def crash_day_of_week(self, value: int):
        self._crash_day_of_week = value

    @property
    def crash_month(self) -> int:
        return Functions.get_num_month(self.crash_date.date()) if self.crash_date else self._crash_month

    @crash_month.setter
    def crash_month(self, value: int):
        self._crash_month = value

    @property
    def crash_date(self) -> Optional[datetime.datetime]:
        return self._crash_date

    @crash_date.setter
    def crash_date(self, value: Optional[datetime.datetime]):
        self._crash_date = value


    def __str__(self) -> str:
        """
        String representation of the DataObject, displaying all fields in Portuguese.
        """
        crash_date_str = self.crash_date.strftime("%d/%m/%Y %H:%M:%S") if self.crash_date else "N/A"
        
        output = (
            f"--- Detalhes do Registro de Acidente ---\n"
            f"  Data/Hora do Registro: {self.default_time_string}\n"
            f"  Data do Acidente (Parseada): {crash_date_str}\n"
            f"  Dispositivo de Controle de Tráfego: {self.traffic_control_device}\n"
            f"  Condição Climática: {self.weather_condition}\n"
            f"  Condição de Iluminação: {self._to_single_string(self.lighting_condition)}\n"
            f"  Primeiro Tipo de Acidente: {self.first_crash_type}\n"
            f"  Tipo de Via: {self.trafficway_type}\n"
            f"  Alinhamento: {self.alignment}\n"
            f"  Condição da Superfície da Via: {self.roadway_surface_cond}\n"
            f"  Defeito na Via: {self.road_defect}\n"
            f"  Tipo de Acidente: {self._to_single_string(self.crash_type)}\n"
            f"  Relacionado à Interseção: {Functions.get_string_from_boolean(self.intersection_related_i)}\n"
            f"  Dano: {self.damage}\n"
            f"  Causa Contributiva Primária: {self.prim_contributory_cause}\n"
            f"  Número de Unidades Envolvidas: {self.num_units}\n"
            f"  Lesão Mais Severa: {self._to_single_string(self.most_severe_injury)}\n"
            f"  Total de Feridos: {self.injuries_total:.2f}\n"
            f"  Feridos Fatais: {self.injuries_fatal:.2f}\n"
            f"  Feridos Incapacitantes: {self.injuries_incapacitating:.2f}\n"
            f"  Feridos Não Incapacitantes: {self.injuries_non_incapacitating:.2f}\n"
            f"  Feridos Relatados (Não Evidentes): {self.injuries_reported_not_evident:.2f}\n"
            f"  Feridos (Sem Indicação): {self.injuries_no_indication:.2f}\n"
            f"  Hora do Acidente: {self.crash_hour}\n"
            f"  Dia da Semana do Acidente: {self.crash_day_of_week}\n"
            f"  Mês do Acidente: {self.crash_month}\n"
            f"-----------------------------------------"
        )
        return output

def add_record(add_registry,save_settings):
    if add_registry=="Manual":
        st.subheader("🚗 Detalhes do Registro de Acidente")
        st.subheader("Detalhes Iniciais")
        try:
            locale.setlocale(locale.LC_ALL, '') # Define a localidade para a do sistema
        except locale.Error:
            # Caso não consiga definir a localidade, use um fallback
            print("Não foi possível definir a localidade do sistema. Usando 'en_US' como fallback.")
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') # Exemplo de fallback para inglês

        # Pega o código do idioma principal (ex: 'pt' para português)
        # Isso é uma simplificação, pois a localidade pode ser mais complexa
        idioma_sistema = locale.getdefaultlocale()[0] # Ex: ('pt_BR', 'UTF-8') -> 'pt_BR'

        # Gera o if ternário para o formato
        formato_data = "DD/MM/YYYY" if idioma_sistema and idioma_sistema.startswith('pt') else "MM/DD/YYYY"

        cols0 = st.columns(2)
        
        with cols0[0]:
            date_accident=st.date_input("Dia do Acidente",
                        value=datetime.date.today(), # Usar datetime.date.today() é o ideal
                        min_value=datetime.date(2020, 1, 1),
                        max_value=datetime.date.today(), # Usar datetime.date.today() é o ideal
                        format=formato_data, # Aqui aplicamos o formato determinado pelo if ternário
            )
            hour_accident=st.time_input(
                "Hora do Acidente",
                step=datetime.timedelta(minutes=15), # Opcional: define o passo para minutos
                
            )
            #hour_accident=Functions.check_time_input(date_accident,hour_accident) 
        default_timestamp_string=datetime.datetime.strptime(date_accident.strftime("%m-%d-%Y")+" "+hour_accident.strftime("%I:%M:%S %p"), "%m-%d-%Y %I:%M:%S %p")
        with cols0[1]:
            hour_accident=Functions.check_time_input(date_accident,hour_accident) 
            st.write(f"Timestamp a ser salvo: {default_timestamp_string}")
            st.write(f"  Hora do Acidente: {hour_accident.hour}")
            st.write(f"  Dia da Semana do Acidente: {date_accident.isoweekday()+1}")
            st.write(f"  Mês do Acidente: {date_accident.month}")

        num_units = st.number_input(
            "Número de Unidades Envolvidas",
            min_value=0, max_value=999, value=0, step=1,
            key="num_units"
        )
        st.subheader("Demais Detalhes")
        cols1 = st.columns(3)
        with cols1[0]:
            crash_type = st.text_input(
                            "Crash Type",
                            key="crash_type"
                        )
            traffic_control_device = st.selectbox(
                "Traffic Control Device",
                ["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN", "YIELD SIGN", "NONE", "OTHER"],
                index=0,
                key="tcd"
            )
            weather_condition = st.selectbox(
                "Weather Condition",
                ["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG", "SEVERE CROSSWINDS", "SLEET", "OTHER"],
                index=0,
                key="weather"
            )
            lighting_condition = st.selectbox(
                "Lighting Condition",
                ["UNKNOWN", "DAYLIGHT", "DARK - LIGHTED", "DARK - NOT LIGHTED", "DUSK/DAWN"],
                index=0,
                key="lighting"
            )
        with cols1[1]:
            first_crash_type = st.text_input("First Crash Type (Specific)",  key="first_crash_type")
            trafficway_type = st.text_input("Trafficway Type", key="trafficway_type")
            alignment = st.text_input("Alignment", key="alignment")
            roadway_surface_cond = st.selectbox(
                "Roadway Surface Condition",
                ["UNKNOWN", "DRY", "WET", "SNOW/ICE", "SAND/MUD/DIRT/OIL"],
                index=0,
                key="surface_condition"
            )
        with cols1[2]:
            road_defect = st.selectbox(
                "Road Defect",
                ["NONE", "RUT, HOLES", "SHOULDER DEFECT", "DEBRIS ON ROADWAY", "OTHER"],
                index=0,
                key="road_defect"
            )
            intersection_related_i = st.selectbox(
                "Intersection Related?",
                ["NO", "YES"],
                index=0,
                key="intersection_related"
            )
            damage = st.text_input("Damage Description",  key="damage")
            prim_contributory_cause = st.text_input("Primary Contributory Cause", key="prim_cause")
            most_severe_injury = st.selectbox(
                "Most Severe Injury",
                ["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"],
                index=0,
                key="most_severe_injury"
            )

        st.subheader("Ferimentos - Detalhamento")
        inj_cols = st.columns(3)
        with inj_cols[0]:
            injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0,  step=0.1, key="injuries_fatal")
            injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0, step=0.1, key="injuries_incapacitating")
        with inj_cols[1]:
            injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0, key="injuries_non_incapacitating")
            injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0, step=0.1, key="injuries_reported_not_evident")
        with inj_cols[2]:
            injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0, step=0.1, key="injuries_no_indication")
            injuries_total = st.number_input(
                            "Total Injuries",
                            min_value=0.0, step=0.1,
                            key="injuries_total"
                        )
        submitted = st.button("💾 Salvar Registro", use_container_width=True)
    if add_registry=="Arquivo CSV":
        st.write("Arquivo CSV")
if __name__ == "__main__":
    condition_registry=st.sidebar.selectbox("Fonte",["Manual","Arquivo CSV"])
    stage_set="Etapa 1"
    add_record(condition_registry,stage_set)