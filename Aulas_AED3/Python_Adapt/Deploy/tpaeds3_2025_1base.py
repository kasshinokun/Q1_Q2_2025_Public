import base64
import fnmatch
import locale
from queue import Full
import tempfile
import shutil
import requests
import streamlit as st
import os
import re
import struct
from pathlib import Path
import time  # For simulating delays/retries if needed, and for timing operations
import filelock # For cross-platform file locking
import csv
import tempfile
import heapq
import io
import pandas as pd
import json
import logging
import traceback
import hashlib
import math
from matplotlib import pyplot as plt
from collections import Counter, defaultdict
from typing import Tuple, Optional, Dict, Callable,List, Union, Any, Iterator
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import platform
import sys
from enum import Enum, auto
# --- Cryptography Imports (for RSA and AES) ---
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag as CryptoInvalidTag # Renomeado para evitar conflito

# ===================================================== add_registry.py
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
        return date.today().year

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
            dt_object = datetime.strptime(datetime_str, "%m/%d/%Y %I:%M:%S %p")
            formatted_date = dt_object.strftime("%d/%m/%Y")
            formatted_time = dt_object.strftime("%H:%M:%S")
            return f"Data de Registro: {formatted_date}\nHorario --------: {formatted_time}"
        except ValueError as e:
            print(f"Erro ao analisar a data: {e}")
            return "Data Inválida"

    @staticmethod
    def get_day_week(date: date) -> int:
        """
        Returns the day of the week (1 for Monday, 7 for Sunday) for a given date.
        """
        return date.isoweekday() # Monday is 1, Sunday is 7

    @staticmethod
    def get_num_month(date: date) -> int:
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
        if date_set == date.today():
            current_datetime = datetime.now()
            selected_datetime_combined = datetime.combine(date_set, hour_set)

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

    def _parse_datetime(self, time_string: str) -> Optional[datetime]:
        """
        Parses a date/time string into a datetime object.
        """
        if not time_string or not time_string.strip():
            print("Aviso: String de data/hora vazia ou nula. Retornando None para crash_date.")
            return None
        try:
            return datetime.strptime(time_string, self.DATE_TIME_FORMATTER)
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
    def crash_date(self) -> Optional[datetime]:
        return self._crash_date

    @crash_date.setter
    def crash_date(self, value: Optional[datetime]):
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
        st.subheader("➕ Inserir Novo Registro")
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
        jan_1 = date(2020, 1, 1)
        with cols0[0]:
            date_accident=st.date_input("Dia do Acidente",
                        value="today", # Usar datetime.date.today() é o ideal
                        min_value=jan_1,
                        max_value="today", # Usar datetime.date.today() é o ideal
                        format=formato_data, # Aqui aplicamos o formato determinado pelo if ternário
            )
            hour_accident=st.time_input(
                "Hora do Acidente",
                step=timedelta(minutes=15), # Opcional: define o passo para minutos
                
            )
            #hour_accident=Functions.check_time_input(date_accident,hour_accident) 
        default_timestamp_string=datetime.strptime(date_accident.strftime("%m-%d-%Y")+" "+hour_accident.strftime("%I:%M:%S %p"), "%m-%d-%Y %I:%M:%S %p")
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
                "Tipo de Acidente", key="crash_type" 
            )
            traffic_control_device = st.selectbox(
                "Dispositivo de Controle de Tráfego",
                ["DESCONHECIDO", "SINAL DE TRÁFEGO", "PLACA DE PARE", "PLACA DE RENDIMENTO", "NENHUM", "OUTRO"], 
                index=0,
                key="tcd"
            )
            weather_condition = st.selectbox(
                "Condição Climática",
                ["DESCONHECIDO", "LIMPO", "CHUVA", "NEVE", "NEBLINA", "VENTOS FORTES", "GEADA", "OUTRO"], 
                index=0,
                key="weather"
            )
            lighting_condition = st.selectbox(
                "Condição de Iluminação", 
                ["DESCONHECIDO", "LUZ DO DIA", "ESCURIDÃO - ILUMINADO", "ESCURIDÃO - NÃO ILUMINADO", "CREPÚSCULO/AMANHECER"], 
                index=0,
                key="lighting"
            )
        with cols1[1]:
            first_crash_type = st.text_input("Primeiro Tipo de Acidente (Específico)", key="first_crash_type") 
            trafficway_type = st.text_input("Tipo de Via", key="trafficway_type") 
            alignment = st.text_input("Alinhamento", key="alignment")
            roadway_surface_cond = st.selectbox(
                "Condição da Superfície da Via", 
                ["DESCONHECIDO", "SECO", "MOLHADO", "NEVE/GELO", "AREIA/LAMA/SUJEIRA/ÓLEO"], 
                index=0,
                key="surface_condition"
            )
        with cols1[2]:
            road_defect = st.selectbox(
                "Defeito na Via", 
                ["NENHUM", "BURACOS", "DEFEITO NO ACOSTAMENTO", "DETRITOS NA VIA", "OUTRO"],
                index=0,
                key="road_defect"
            )
            intersection_related_i = st.selectbox(
                "Relacionado à Interseção?", 
                ["NÃO", "SIM"],
                index=0,
                key="intersection_related"
            )
            damage = st.text_input("Descrição do Dano",  key="damage")
            prim_contributory_cause = st.text_input("Causa Contributiva Primária", key="prim_cause")
            most_severe_injury = st.selectbox(
                "Lesão Mais Severa",
                ["NENHUMA", "FATAL", "INCAPACITANTE", "NÃO-INCAPACITANTE", "RELATADA, NÃO EVIDENTE"],
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
        submitted = st.button("💾 Salvar Registro" if save_settings =="Etapa 1" else "💾 Salvar Registro e Atualizar Índice", use_container_width=True)
    if add_registry=="Arquivo CSV":
        st.write("Arquivo CSV")
# =====================================================================
def main():
    st.set_page_config(page_title="Traffic Accidents DB",
        layout="wide",
        page_icon="🚗"
    )

    # Título principal da aplicação
    st.title("Sistema de Gerenciamento de Dados de Acidentes de Trânsito")
    st.markdown("---") # Separador visual

    # Menu principal na sidebar
    st.sidebar.title("Navegação Principal")
    st.sidebar.markdown("Selecione uma das etapas abaixo para interagir com o sistema.")
    main_option = st.sidebar.selectbox(
        "Escolha uma Seção",
        ("Etapa 1", "Etapa 2", "Etapa 3", "Etapa 4","Administração do Sistema","Sobre"),
        help="Navegue entre as principais funcionalidades do sistema."
    )
    st.sidebar.markdown("---") # Separador visual

    # --- Conteúdo da Etapa 1 ---
    if main_option == "Etapa 1":
        st.header("🗄️ Etapa 1: Gerenciamento de Arquivo de Dados")
        st.write("Esta seção permite operações diretas sobre o arquivo de dados principal.")
        st.markdown("---") # Separador visual

        st.sidebar.subheader("Opções de Arquivo de Dados")
        sub_option_etapa1 = st.sidebar.selectbox(
            "Selecione uma Ação",
            ("Carregar dados do CSV", "Carregar dados do arquivo de dados",
             "Inserir um registro", "Editar um registro",
             "Apagar um registro", "Exportar dados como CSV"),
            help="Escolha a operação que deseja realizar no arquivo de dados."
        )

        st.info(f"Você está em: **Etapa 1** - **{sub_option_etapa1}**")

        if sub_option_etapa1 == "Carregar dados do CSV":
            st.subheader("📤 Carregar Dados de um Arquivo CSV")
            st.write("Selecione um arquivo CSV para importar dados para o sistema.")
            uploaded_csv_file = st.file_uploader(
                "Arraste e solte seu arquivo CSV aqui ou clique para procurar.",
                type=["csv"],
                help="O arquivo CSV deve conter os dados dos acidentes."
            )
            if uploaded_csv_file is not None:
                st.success(f"Arquivo '{uploaded_csv_file.name}' carregado com sucesso! (Aguardando implementação da lógica de processamento)")
                # Exemplo: df = pd.read_csv(uploaded_csv_file)
                # st.dataframe(df.head()) # Mostrar prévia dos dados
        elif sub_option_etapa1 == "Carregar dados do arquivo de dados":
            st.subheader("📥 Carregar Dados do Arquivo Interno (.db)")
            st.write("Carregue o arquivo de dados principal do sistema para visualização ou processamento.")
            uploaded_db_file = st.file_uploader(
                "Selecione o arquivo de dados (.db)",
                type=["db"],
                help="Este é o arquivo binário onde os registros de acidentes são armazenados."
            )
            if uploaded_db_file is not None:
                st.success(f"Arquivo '{uploaded_db_file.name}' carregado com sucesso! (Aguardando implementação da lógica de carregamento)")
        elif sub_option_etapa1 == "Inserir um registro":
            add_record("Manual",main_option)
        elif sub_option_etapa1 == "Editar um registro":
            st.subheader("✏️ Editar Registro Existente")
            st.write("Localize um registro existente pelo seu ID e atualize suas informações.")
            record_id_edit = st.text_input("ID do Registro a Editar", help="Insira o identificador único do registro.")
            if record_id_edit:
                st.info(f"Buscando registro com ID: **{record_id_edit}**... (Aguardando lógica de busca)")
                # Simular carregamento de dados para edição
                # if record_found:
                with st.form("edit_record_form"):
                    st.write("Preencha os campos abaixo para atualizar o registro:")
                    # Campos pré-preenchidos com dados do registro (simulados)
                    col1, col2 = st.columns(2)
                    with col1:
                        data_acidente_edit = st.date_input("Data do Acidente", value=date.today(), key="edit_data_acidente", help="Data atual para demonstração.")
                        gravidade_edit = st.selectbox("Gravidade", ["Leve", "Moderada", "Grave", "Fatal"], index=0, key="edit_gravidade")
                    with col2:
                        localizacao_edit = st.text_input("Localização", value="Exemplo de Localização", key="edit_localizacao")
                        veiculos_envolvidos_edit = st.number_input("Veículos Envolvidos", min_value=1, value=1, key="edit_veiculos")
                    observacoes_edit = st.text_area("Observações", value="Exemplo de observações para edição.", key="edit_obs")

                    edit_submitted = st.form_submit_button("Atualizar Registro")
                    if edit_submitted:
                        st.success(f"Registro com ID {record_id_edit} atualizado! (Aguardando lógica de edição)")
                        st.json({ # Apenas para demonstração
                            "id": record_id_edit,
                            "data_acidente": str(data_acidente_edit),
                            "gravidade": gravidade_edit,
                            "localizacao": localizacao_edit,
                            "veiculos_envolvidos": veiculos_envolvidos_edit,
                            "observacoes": observacoes_edit
                        })
                # else: st.warning("Registro não encontrado.")
        elif sub_option_etapa1 == "Apagar um registro":
            st.subheader("🗑️ Apagar Registro")
            st.write("Insira o ID do registro que deseja remover permanentemente do banco de dados.")
            record_id_delete = st.text_input("ID do Registro a Apagar", help="O ID é o identificador único do registro.")
            if st.button("Apagar Registro", help="Esta ação é irreversível!"):
                if record_id_delete:
                    st.warning(f"Tentando apagar registro com ID: **{record_id_delete}**... (Aguardando lógica de exclusão)")
                    # if deletion_successful:
                    st.success(f"Registro com ID {record_id_delete} apagado com sucesso! (Aguardando confirmação)")
                    # else: st.error("Falha ao apagar o registro. Verifique o ID.")
                else:
                    st.error("Por favor, insira um ID de registro para apagar.")
        elif sub_option_etapa1 == "Exportar dados como CSV":
            st.subheader("⬇️ Exportar Dados para CSV")
            st.write("Exporte todo o conteúdo do arquivo de dados principal para um arquivo CSV.")
            if st.button("Gerar CSV para Download"):
                with st.spinner("Gerando arquivo CSV..."):
                    time.sleep(2) # Simula o processamento
                    # Na implementação real, você leria os dados do seu .db e os formataria em CSV
                    sample_data = "coluna1,coluna2,coluna3\nvalor1,valor2,valor3\nvalorA,valorB,valorC"
                    st.download_button(
                        label="Clique para Baixar CSV",
                        data=sample_data,
                        file_name="dados_acidentes.csv",
                        mime="text/csv",
                        help="Baixe o arquivo CSV gerado contendo todos os registros."
                    )
                    st.success("Arquivo CSV pronto para download!")

    # --- Conteúdo da Etapa 2 ---
    elif main_option == "Etapa 2":
        st.header("🗂️ Etapa 2: Gerenciamento de Arquivo de Dados e Índice")
        st.write("Nesta etapa, você pode gerenciar o arquivo de dados juntamente com seus índices para otimização de busca.")
        st.markdown("---") # Separador visual

        st.sidebar.subheader("Opções de Dados e Índice")
        sub_option_etapa2 = st.sidebar.selectbox(
            "Selecione uma Ação",
            ("Carregar dados do CSV", "Carregar arquivo de dados e índice",
             "Inserir um registro", "Editar um registro",
             "Apagar um registro", "Exportar arquivo de dados e índice como CSV"),
            help="Escolha a operação que envolve tanto o arquivo de dados quanto o arquivo de índice."
        )

        st.info(f"Você está em: **Etapa 2** - **{sub_option_etapa2}**")

        if sub_option_etapa2 == "Carregar dados do CSV":
            st.subheader("📤 Carregar Dados de um Arquivo CSV (com Índice)")
            st.write("Importe dados de um CSV e, opcionalmente, construa ou atualize um índice associado.")
            uploaded_csv_file_e2 = st.file_uploader(
                "Arraste e solte seu arquivo CSV aqui ou clique para procurar.",
                type=["csv"], key="csv_e2",
                help="O arquivo CSV será usado para popular o banco de dados e o índice."
            )
            if uploaded_csv_file_e2 is not None:
                st.success(f"Arquivo '{uploaded_csv_file_e2.name}' carregado! (Aguardando lógica de processamento com índice)")
        elif sub_option_etapa2 == "Carregar arquivo de dados e índice":
            st.subheader("📥 Carregar Arquivo de Dados (.db) e Índice (.idx)")
            st.write("Selecione os arquivos de dados e índice para carregar o sistema completo.")
            uploaded_db_file_e2 = st.file_uploader(
                "Selecione o arquivo de dados (.db)",
                type=["db"], key="db_e2",
                help="Arquivo binário de registros."
            )
            uploaded_idx_file_e2 = st.file_uploader(
                "Selecione o arquivo de índice (.idx)",
                type=["idx"], key="idx_e2",
                help="Arquivo com a estrutura de índice para busca rápida."
            )
            if uploaded_db_file_e2 is not None and uploaded_idx_file_e2 is not None:
                st.success(f"Arquivos '{uploaded_db_file_e2.name}' e '{uploaded_idx_file_e2.name}' carregados! (Aguardando lógica de carregamento)")
            elif uploaded_db_file_e2 is not None or uploaded_idx_file_e2 is not None:
                st.warning("Por favor, carregue AMBOS os arquivos (.db e .idx) para esta operação.")
        elif sub_option_etapa2 == "Inserir um registro":
             add_record("Manual",main_option)
        elif sub_option_etapa2 == "Editar um registro":
            st.subheader("✏️ Editar Registro Existente (com Atualização de Índice)")
            st.write("Modifique um registro e tenha certeza que o índice refletirá as mudanças.")
            record_id_edit_e2 = st.text_input("ID do Registro a Editar", key="e2_edit_id")
            if record_id_edit_e2:
                st.info(f"Buscando registro com ID: **{record_id_edit_e2}**... (Aguardando lógica de busca e edição)")
                with st.form("edit_record_form_e2"):
                    st.write("Atualize os campos:")
                    col1, col2 = st.columns(2)
                    with col1:
                        data_acidente_edit = st.date_input("Data do Acidente", value=date.today(), key="e2_edit_data")
                        gravidade_edit = st.selectbox("Gravidade", ["Leve", "Moderada", "Grave", "Fatal"], index=0, key="e2_edit_gravidade")
                    with col2:
                        localizacao_edit = st.text_input("Localização", value="Exemplo de Localização", key="e2_edit_local")
                        veiculos_envolvidos_edit = st.number_input("Veículos Envolvidos", min_value=1, value=1, key="e2_edit_veiculos")
                    observacoes_edit = st.text_area("Observações", value="Exemplo de observações para edição.", key="e2_edit_obs")
                    edit_submitted_e2 = st.form_submit_button("Atualizar Registro e Índice")
                    if edit_submitted_e2:
                        st.success(f"Registro com ID {record_id_edit_e2} atualizado e índice refeito! (Aguardando lógica de edição)")
        elif sub_option_etapa2 == "Apagar um registro":
            st.subheader("🗑️ Apagar Registro (com Atualização de Índice)")
            st.write("Remova um registro e veja o índice ser ajustado para refletir a exclusão.")
            record_id_delete_e2 = st.text_input("ID do Registro a Apagar", key="e2_delete_id")
            if st.button("Apagar Registro e Atualizar Índice", key="e2_delete_btn"):
                if record_id_delete_e2:
                    st.warning(f"Tentando apagar registro com ID: **{record_id_delete_e2}** e seu índice... (Aguardando lógica de exclusão)")
                    st.success(f"Registro com ID {record_id_delete_e2} e sua entrada no índice apagados! (Aguardando confirmação)")
                else:
                    st.error("Por favor, insira um ID de registro para apagar.")
        elif sub_option_etapa2 == "Exportar arquivo de dados e índice como CSV":
            st.subheader("⬇️ Exportar Dados e Índice para CSV")
            st.write("Esta opção permite exportar os dados brutos e/ou informações do índice para um formato CSV.")
            export_type = st.radio(
                "O que você deseja exportar?",
                ("Apenas Dados", "Apenas Índice", "Ambos (Dados e Índice Relacionados)"),
                help="Escolha o tipo de informação a ser exportada."
            )
            if st.button("Gerar CSV(s) para Download", key="e2_export_btn"):
                with st.spinner(f"Gerando {export_type.lower()} para download..."):
                    time.sleep(2) # Simula processamento
                    # Lógica para gerar CSV de dados e/ou índice
                    if "Dados" in export_type:
                        sample_data_e2 = "coluna1,coluna2,coluna3\nvalorX,valorY,valorZ"
                        st.download_button(
                            label="Baixar Dados CSV",
                            data=sample_data_e2,
                            file_name="dados_acidentes_e2.csv",
                            mime="text/csv",
                            key="download_data_e2"
                        )
                    if "Índice" in export_type:
                        sample_index_e2 = "id_registro,offset,tamanho\n1,0,100\n2,101,120"
                        st.download_button(
                            label="Baixar Índice CSV",
                            data=sample_index_e2,
                            file_name="indice_acidentes_e2.csv",
                            mime="text/csv",
                            key="download_index_e2"
                        )
                    st.success(f"{export_type} pronto(s) para download!")

    # --- Conteúdo da Etapa 3 ---
    elif main_option == "Etapa 3":
        st.header("🔐 Etapa 3: Compactação e Criptografia")
        st.write("Otimize o armazenamento e a segurança dos seus dados aplicando técnicas de compactação e criptografia.")
        st.markdown("---") # Separador visual

        st.sidebar.subheader("Opções de Segurança e Otimização")
        sub_option_etapa3 = st.sidebar.selectbox(
            "Selecione uma Ferramenta",
            ("Compactação", "Criptografia"),
            help="Escolha entre compactar dados para economizar espaço ou criptografá-los para segurança."
        )

        st.info(f"Você está em: **Etapa 3** - **{sub_option_etapa3}**")

        if sub_option_etapa3 == "Compactação":
            st.subheader("📦 Compactação de Arquivos")
            st.write("Reduza o tamanho dos seus arquivos usando diferentes algoritmos de compactação.")
            compact_method = st.selectbox(
                "Método de Compactação",
                ("Huffman", "LZW", "LZ78"),
                help="Selecione o algoritmo de compactação a ser utilizado."
            )
            compact_mode_selection = st.radio(
                "Modo de Operação",
                ("Padrão", "Escolha do Usuário"),
                help="No modo 'Padrão', você compacta arquivos internos do sistema. No modo 'Escolha do Usuário', você seleciona um arquivo local."
            )
            compact_action = st.selectbox(
                "Ação",
                ("Compactar", "Descompactar"),
                help="Escolha entre compactar um arquivo para reduzir seu tamanho ou descompactar para restaurá-lo."
            )

            if compact_mode_selection == "Padrão" and compact_action == "Compactar":
                st.write("Selecione qual componente do sistema você deseja compactar:")
                st.selectbox(
                    "Tipo de Arquivo para Compactar",
                    ("Arquivo de Dados", "Índice", "Árvore B"),
                    help="Escolha o arquivo interno do sistema para compactar."
                )
                if st.button(f"{compact_action} Arquivo (Padrão)"):
                    with st.spinner(f"{compact_action} arquivo padrão com {compact_method}..."):
                        time.sleep(2) # Simula
                        st.success(f"Arquivo padrão {compact_action.lower()} com sucesso usando {compact_method}! (Aguardando lógica)")
            elif compact_mode_selection == "Escolha do Usuário":
                st.write("Carregue seu próprio arquivo para compactar ou descompactar.")
                uploaded_file_compact = st.file_uploader(
                    "Carregar arquivo para processamento",
                    type=["db", "idx", "btr", "huff", "lzw", "lz78", "csv"],
                    help="Arraste e solte arquivos nos formatos .db, .idx, .btr, .huff, .lzw, .lz78 ou .csv."
                )
                if uploaded_file_compact is not None:
                    st.info(f"Arquivo '{uploaded_file_compact.name}' carregado.")
                    if st.button(f"{compact_action} Arquivo", key="compact_user_file_btn"):
                        with st.spinner(f"{compact_action} '{uploaded_file_compact.name}' com {compact_method}..."):
                            time.sleep(3) # Simula
                            st.success(f"Arquivo '{uploaded_file_compact.name}' {compact_action.lower()} com sucesso usando {compact_method}! (Aguardando lógica)")
                            st.download_button(
                                label=f"Baixar Arquivo {compact_action}",
                                data="conteúdo_do_arquivo_processado", # Substituir pelo conteúdo real
                                file_name=f"{Path(uploaded_file_compact.name).stem}_processed.bin", # Nome de arquivo de exemplo
                                mime="application/octet-stream",
                                help="Baixe o arquivo após a operação de compactação/descompactação."
                            )

        elif sub_option_etapa3 == "Criptografia":
            st.subheader("🔒 Criptografia de Arquivos")
            st.write("Proteja seus dados sensíveis aplicando criptografia avançada.")
            crypto_method = st.selectbox(
                "Método de Criptografia",
                ("Gerar Chaves RSA/Blowfish", "Blowfish", "AES-RSA"),
                help="Selecione o algoritmo de criptografia. 'Gerar Chaves' cria novos pares de chaves."
            )
            crypto_mode_selection = st.radio(
                "Modo de Operação",
                ("Padrão", "Escolha do Usuário"),
                help="No modo 'Padrão', você criptografa arquivos internos do sistema. No modo 'Escolha do Usuário', você seleciona um arquivo local e chaves."
            )
            crypto_action = st.selectbox(
                "Ação",
                ("Criptografar", "Descriptografar"),
                help="Escolha entre criptografar um arquivo para protegê-lo ou descriptografá-lo para acessá-lo."
            )

            if crypto_method == "Gerar Chaves RSA/Blowfish":
                st.info("Esta opção irá gerar um novo par de chaves RSA (pública/privada) e uma chave Blowfish.")
                if st.button("Gerar Novas Chaves", help="Isso pode levar alguns instantes."):
                    with st.spinner("Gerando chaves..."):
                        time.sleep(3) # Simula
                        st.success("Chaves geradas com sucesso! (Aguardando lógica de geração)")
                        # No futuro, adicione botões de download para as chaves geradas
                        st.download_button(
                            label="Baixar Chave Pública (RSA)",
                            data="chave_publica_rsa_exemplo",
                            file_name="public_key.pem",
                            mime="application/x-pem-file"
                        )
                        st.download_button(
                            label="Baixar Chave Privada (RSA)",
                            data="chave_privada_rsa_exemplo",
                            file_name="private_key.pem",
                            mime="application/x-pem-file"
                        )
                        st.download_button(
                            label="Baixar Chave Blowfish",
                            data="chave_blowfish_exemplo",
                            file_name="blowfish_key.bin",
                            mime="application/octet-stream"
                        )
            else: # Blowfish ou AES-RSA
                if crypto_mode_selection == "Padrão" and crypto_action == "Criptografar":
                    st.write("Selecione qual componente do sistema você deseja criptografar:")
                    st.selectbox(
                        "Tipo de Arquivo para Criptografar",
                        ("Arquivo de Dados", "Índice", "Árvore B"),
                        help="Escolha o arquivo interno do sistema para criptografar."
                    )
                    if st.button("Autogerar Chaves e Criptografar (Padrão)", help="Utiliza chaves padrão do sistema para criptografia."):
                        with st.spinner(f"Criptografando arquivo padrão com {crypto_method} e chaves autogeradas..."):
                            time.sleep(3) # Simula
                            st.success(f"Arquivo padrão criptografado com sucesso usando {crypto_method}! (Aguardando lógica)")
                elif crypto_mode_selection == "Escolha do Usuário":
                    st.write("Carregue as chaves e o arquivo para criptografar/descriptografar.")
                    st.subheader("🔑 Chave(s) de Criptografia")
                    uploaded_key_file = st.file_uploader(
                        "Carregar arquivo de chave (.pem)",
                        type=["pem", "bin"], # Blowfish key might be .bin
                        help="Para RSA, carregue a chave pública (.pem) para criptografar ou a privada (.pem) para descriptografar. Para Blowfish, a chave binária."
                    )
                    st.subheader("📄 Arquivo a ser Processado")
                    uploaded_file_crypto = st.file_uploader(
                        "Carregar arquivo para processamento",
                        type=["db", "idx", "btr", "enc", "enc_aes", "csv"],
                        help="Selecione o arquivo de dados (.db), índice (.idx), árvore B (.btr), ou arquivos já criptografados (.enc, .enc_aes, .csv)."
                    )
                    if uploaded_key_file is not None and uploaded_file_crypto is not None:
                        st.info(f"Chave '{uploaded_key_file.name}' e arquivo '{uploaded_file_crypto.name}' carregados.")
                        if st.button(f"{crypto_action} Arquivo", key="crypto_user_file_btn"):
                            with st.spinner(f"{crypto_action} '{uploaded_file_crypto.name}' com {crypto_method}..."):
                                time.sleep(3) # Simula
                                st.success(f"Arquivo '{uploaded_file_crypto.name}' {crypto_action.lower()} com sucesso usando {crypto_method}! (Aguardando lógica)")
                                st.download_button(
                                    label=f"Baixar Arquivo {crypto_action}",
                                    data="conteúdo_do_arquivo_processado", # Substituir pelo conteúdo real
                                    file_name=f"{Path(uploaded_file_crypto.name).stem}_processed.bin", # Nome de arquivo de exemplo
                                    mime="application/octet-stream",
                                    help="Baixe o arquivo após a operação de criptografia/descriptografia."
                                )
                    elif uploaded_key_file is not None or uploaded_file_crypto is not None:
                        st.warning("Por favor, carregue a chave e o arquivo a ser processado para continuar.")

    # --- Conteúdo da Etapa 4 ---
    elif main_option == "Etapa 4":
        st.header("🔍 Etapa 4: Casamento Padrão e Busca Avançada")
        st.write("Utilize algoritmos eficientes para buscar padrões em seus dados.")
        st.markdown("---") # Separador visual

        st.sidebar.subheader("Opções de Casamento Padrão")
        sub_option_etapa4 = st.sidebar.selectbox(
            "Selecione uma Ação de Busca",
            ("Gerar sistema de Busca por Aho-Corasik", "Buscar registros por Casamento Padrão"),
            help="Escolha entre construir uma estrutura para busca múltipla de padrões ou realizar uma busca direta."
        )

        st.info(f"Você está em: **Etapa 4** - **{sub_option_etapa4}**")

        if sub_option_etapa4 == "Gerar sistema de Busca por Aho-Corasik":
            st.subheader("⚙️ Gerar Sistema de Busca por Aho-Corasik")
            st.write("Esta função constrói o autômato de Aho-Corasik a partir de um conjunto de padrões, otimizando a busca simultânea de múltiplos termos.")
            st.caption("Escolha a etapa de construção do sistema:")
            st.selectbox(
                "Etapas de Geração",
                ("Etapa 1: Carregar Padrões", "Etapa 2: Construir Autômato"),
                help="Etapa 1: Defina os padrões de busca. Etapa 2: Construa a estrutura de Aho-Corasik."
            )
            if st.button("Gerar sistema de Busca por Aho-Corasik", help="Inicia a construção da estrutura de busca."):
                with st.spinner("Gerando sistema Aho-Corasik..."):
                    time.sleep(3) # Simula
                    st.success("Sistema de Busca por Aho-Corasik gerado com sucesso! (Aguardando lógica)")
                    st.download_button(
                        label="Baixar Sistema Aho-Corasik",
                        data="dados_do_sistema_aho_corasik_serializados", # Substituir
                        file_name="aho_corasik_system.bin",
                        mime="application/octet-stream",
                        help="Baixe o arquivo binário do sistema Aho-Corasik gerado."
                    )
        elif sub_option_etapa4 == "Buscar registros por Casamento Padrão":
            st.subheader("🎯 Buscar Registros por Casamento Padrão")
            st.write("Pesquise registros no banco de dados utilizando algoritmos de casamento de padrão.")
            st.caption("Escolha a etapa da busca:")
            st.selectbox(
                "Etapas da Busca",
                ("Etapa 1: Carregar Dados de Busca", "Etapa 2: Executar Busca"),
                help="Etapa 1: Carregue os dados onde a busca será realizada. Etapa 2: Execute a busca com o padrão definido."
            )
            pattern_to_locate = st.text_input(
                "Digite o padrão a ser localizado",
                help="Insira o texto ou padrão que você deseja encontrar nos registros.",
                placeholder="Ex: 'acidente grave', 'colisão lateral'"
            )
            if st.button("Buscar registros por Casamento Padrão", help="Inicia a busca pelo padrão especificado."):
                if pattern_to_locate:
                    with st.spinner(f"Buscando por '{pattern_to_locate}'..."):
                        time.sleep(4) # Simula
                        st.success(f"Busca por '{pattern_to_locate}' concluída! (Aguardando lógica)")
                        st.subheader("Resultados da Busca:")
                        # Exemplo de exibição de resultados (você preencherá com dados reais)
                        st.dataframe(pd.DataFrame({
                            "ID do Registro": [1, 5, 12],
                            "Localização": ["Rua A, Bairro C", "Rodovia X", "Avenida Y"],
                            "Trecho Encontrado": ["Ocorreu um **acidente grave**.", "Colisão frontal em **acidente grave**.", "**acidente grave** próximo ao semáforo"]
                        }))
                        st.info("Nenhum resultado encontrado para o padrão especificado." if not pattern_to_locate else "Resultados exibidos acima.")
                else:
                    st.error("Por favor, digite um padrão para realizar a busca.")

     # --- Conteúdo da Administração do Sistema ---
    elif main_option == "Administração do Sistema":
        st.header("⚙️ Administração do Sistema")
        st.write("Ferramentas para manutenção e gerenciamento do banco de dados e arquivos do sistema.")
        st.markdown("---")

        st.subheader("📊 Backup e Exportação")
        col_backup, col_export = st.columns(2)
        with col_backup:
            if st.button("Realizar Backup Agora", key="backup_db_button", help="Cria uma cópia de segurança do banco de dados principal."):
                with st.spinner("Realizando backup..."):
                    time.sleep(2) # Simula
                    st.success("Backup do banco de dados realizado com sucesso!")
                    # Lógica real para fazer backup
        with col_export:
            if st.button("Exportar Dados para CSV", key="export_csv_button", help="Exporta todo o conteúdo do banco de dados para um arquivo CSV."):
                with st.spinner("Exportando para CSV..."):
                    time.sleep(2) # Simula
                    sample_data_admin = "col1,col2\nval1,val2\nval3,val4"
                    st.download_button(
                        label="Baixar Dados Exportados",
                        data=sample_data_admin,
                        file_name="dados_completos_backup.csv",
                        mime="text/csv",
                        key="download_admin_csv"
                    )
                    st.success("Dados exportados para CSV com sucesso!")

        st.markdown("---")

        admin_opt=st.selectbox(
            "Selecione o Escopo da Operação",
            ("Etapa 1: Apenas Banco de Dados", "Etapa 2: Banco de Dados e Índices"),
            help="Escolha o nível de arquivos a serem importados ou gerenciados."
        )

        if admin_opt=="Etapa 1: Apenas Banco de Dados":
            st.subheader("⬆️ Importar Banco de Dados (.db)")
            st.write("Faça upload de um arquivo `.db` para restaurar ou substituir o banco de dados principal.")
            uploaded_file_import_db = st.file_uploader(
                "Selecione um arquivo .db para importar",
                type="db", key="import_db_uploader",
                help="Este arquivo substituirá o banco de dados principal atual. Faça um backup antes!"
            )
            if uploaded_file_import_db is not None:
                st.success(f"Arquivo '{uploaded_file_import_db.name}' pronto para importação. (Aguardando ação)")
                if st.button("Confirmar Importação de DB", key="confirm_import_db_btn"):
                    with st.spinner("Importando banco de dados..."):
                        time.sleep(3) # Simula
                        st.success("Banco de dados importado com sucesso!")

            st.markdown("---")
            st.subheader("⚠️ Excluir Banco de Dados Principal")
            st.warning("Esta ação é irreversível e excluirá *permanentemente* o arquivo do banco de dados principal (`traffic_accidents.db`). **Faça um backup antes!**")
            if st.button("Excluir Banco de Dados Principal", key="delete_db_button", help="Cuidado! Esta ação não pode ser desfeita."):
                if st.checkbox("Tenho certeza que quero excluir o banco de dados principal.", key="confirm_delete_db"):
                    with st.spinner("Excluindo banco de dados..."):
                        time.sleep(2) # Simula
                        st.error("Banco de dados principal excluído! (Aguardando lógica de exclusão)")
                        st.info("Recomenda-se reiniciar a aplicação para garantir a integridade.")
                else:
                    st.info("Confirme a exclusão marcando a caixa de seleção.")

        if admin_opt=="Etapa 2: Banco de Dados e Índices":
            st.subheader("⬆️ Importar Arquivos de Índice e Banco de Dados")
            st.write("Faça upload de arquivos `.btr` (Árvore B), `.inv` (Índice Invertido) e `.idx` (Índice Geral) para restaurar os índices do sistema, juntamente com o `.db`.")

            col_idx1, col_idx2, col_idx3 = st.columns(3)
            with col_idx1:
                uploaded_btr_file = st.file_uploader("Selecione Árvore B (.btr)", type=["btr"], key="import_btr_uploader", help="Arquivo da estrutura de Árvore B.")
                if uploaded_btr_file: st.success(f"'{uploaded_btr_file.name}' carregado.")
            with col_idx2:
                uploaded_inv_file = st.file_uploader("Selecione Índice Invertido (.inv)", type=["inv"], key="import_inv_uploader", help="Arquivo do Índice Invertido.")
                if uploaded_inv_file: st.success(f"'{uploaded_inv_file.name}' carregado.")
            with col_idx3:
                uploaded_idx_file = st.file_uploader("Selecione Índice Geral (.idx)", type=["idx"], key="import_idx_uploader", help="Arquivo do Índice Geral.")
                if uploaded_idx_file: st.success(f"'{uploaded_idx_file.name}' carregado.")

            st.subheader("⬆️ Importar Banco de Dados (.db) para Conjunto")
            uploaded_db_file_e2_admin = st.file_uploader(
                "Selecione o arquivo .db para este conjunto",
                type="db", key="import_db2_uploader",
                help="Este é o arquivo de dados associado aos índices que você está importando."
            )
            if uploaded_db_file_e2_admin: st.success(f"'{uploaded_db_file_e2_admin.name}' carregado.")

            if st.button("Confirmar Importação de Banco de Dados e Índices", key="confirm_import_full_btn"):
                if uploaded_btr_file or uploaded_inv_file or uploaded_idx_file or uploaded_db_file_e2_admin:
                    with st.spinner("Importando arquivos..."):
                        time.sleep(3) # Simula
                        st.success("Banco de Dados e Índices importados com sucesso! (Aguardando lógica de restauração)")
                else:
                    st.error("Por favor, carregue pelo menos um arquivo para importar.")

            st.markdown("---")
            st.subheader("⚠️ Excluir Banco de Dados Principal e Índices")
            st.warning("Esta ação é irreversível e excluirá *permanentemente* o banco de dados principal (`traffic_accidents.db`), Árvore B (`.btr`), Índice Invertido (`.inv`) e Índice Geral (`.idx`). **Faça um backup antes!**")
            if st.button("Excluir TUDO (DB e Índices)", key="delete_2db_button", help="Esta é uma exclusão completa. Não há volta!"):
                if st.checkbox("Tenho certeza que quero excluir o banco de dados principal e todos os índices.", key="confirm_delete_full"):
                    with st.spinner("Excluindo banco de dados e índices..."):
                        time.sleep(3) # Simula
                        st.error("Banco de dados principal e todos os índices excluídos! (Aguardando lógica de exclusão)")
                        st.info("Recomenda-se reiniciar a aplicação para garantir a integridade.")
                else:
                    st.info("Confirme a exclusão marcando a caixa de seleção.")
        st.markdown("---")

        st.subheader("📜 Visualização e Exclusão de Arquivos de Log")
        st.write("Acesse os logs do sistema para depuração ou remova-os para liberar espaço.")
        col_log_view, col_log_delete = st.columns(2)
        with col_log_view:
            if st.button("Visualizar Conteúdo do Log", key="view_log_button", help="Exibe os registros de atividades do sistema."):
                st.info("Exibindo conteúdo do log (Simulação)...")
                st.code("2024-07-07 10:30:01 - INFO - Aplicação iniciada.\n2024-07-07 10:35:15 - WARNING - Tentativa de acesso negada.")
                # Lógica real para ler e exibir o log
        with col_log_delete:
            if st.button("Excluir Arquivo de Log", key="delete_log_button", help="Remove o arquivo de log do sistema."):
                if st.checkbox("Confirmar exclusão do arquivo de log", key="confirm_delete_log"):
                    with st.spinner("Excluindo arquivo de log..."):
                        time.sleep(1) # Simula
                        st.success("Arquivo de log excluído com sucesso! (Aguardando lógica)")
                else:
                    st.info("Marque a caixa para confirmar a exclusão do log.")

    # --- Conteúdo da Seção "Sobre" ---
    elif main_option == "Sobre":
        st.header("ℹ️ Sobre este Sistema")
        st.markdown("---")

        st.subheader("Autor")
        st.write("Desenvolvido por: [Gabriel da Silva Cassino](https://github.com/kasshinokun)")

        st.subheader("Descrição do Projeto")
        st.write("""
        Este é um sistema de gerenciamento de banco de dados de acidentes de trânsito
        com funcionalidades avançadas de compressão (LZW e Huffman), criptografia (híbrida AES e RSA)
        e indexação eficiente usando uma estrutura de dados B-Tree e Índice Invertido.
        """)
        st.write("""
        Desenvolvido como trabalho prático para a disciplina de **Algoritmos e Estruturas de Dados III**
        da graduação em Engenharia da Computação pela **PUC Minas Coração Eucarístico**.
        """)
        st.write("O programa será reconstruído gradativamente. No repositório da aplicação (link abaixo), existem as prévias iniciais.")
        st.markdown("Link do Repositório: [Deploy da Aplicação](https://github.com/kasshinokun/Q1_Q2_2025_Public/tree/main/Aulas_AED3/Python_Adapt/Deploy)")

        st.subheader("Tecnologias Utilizadas")
        st.markdown("""
        * **Python**: Linguagem de programação principal.
        * **Streamlit**: Para a interface de usuário web interativa e ágil.
        * **`cryptography`**: Biblioteca robusta para operações criptográficas (AES, RSA, Blowfish).
        * **`filelock`**: Para gerenciamento de concorrência e garantia da integridade do arquivo em operações multi-threaded/multi-processo.
        * **`pathlib`**: Módulo para manipulação de caminhos de arquivos e diretórios de forma orientada a objetos.
        * **`pandas`**: Essencial para manipulação e exibição de dados tabulares (DataFrames).
        * **`matplotlib`**: Para geração de gráficos de comparação e visualização de dados (se implementado).
        * **`collections`**: Módulos como `Counter` e `defaultdict` para estruturas de dados eficientes.
        * **`typing`**: Suporte para tipagem estática, melhorando a clareza e manutenibilidade do código.
        * **`concurrent.futures`**: Para gerenciamento de threads e processos, permitindo operações assíncronas.
        * **`threading`**: Para controle de threads de execução.
        """)
        st.write("Versão: 1.0_20250707 Alpha")
        st.markdown("---")
        st.info("Agradecemos seu interesse em nossa aplicação!")


if __name__ == "__main__":
    main()
