import streamlit as st
import os
import json
import hashlib
import struct
from datetime import datetime
import collections
import pandas as pd
import requests # Novo import para baixar arquivos de URL
import io # Novo import para lidar com dados em memória como arquivos

# --- DEVE SER A PRIMEIRA CHAMADA DO STREAMLIT ---
st.set_page_config(layout="wide", page_title="Sistema de Dados de Acidentes")

# --- Implementação do AhoCorasick ---
class AhoCorasick:
    def __init__(self, patterns: list[str]):
        self.patterns = patterns
        self.goto_fn = {}
        self.output_fn = {}
        self.failure_fn = {}
        self.node_counter = 0
        
        self._build_automaton()

    def _new_node(self):
        self.node_counter += 1
        self.goto_fn[self.node_counter] = {}
        self.output_fn[self.node_counter] = set()
        return self.node_counter

    def _build_automaton(self):
        self.root = 0
        self.goto_fn[self.root] = {}
        self.output_fn[self.root] = set()
        
        for pattern in self.patterns:
            current_node = self.root
            for char in pattern:
                if char not in self.goto_fn[current_node]:
                    new_node = self._new_node()
                    self.goto_fn[current_node][char] = new_node
                current_node = self.goto_fn[current_node][char]
            self.output_fn[current_node].add(pattern)

        queue = collections.deque()

        for char, node in self.goto_fn[self.root].items():
            self.failure_fn[node] = self.root
            queue.append(node)

        while queue:
            r = queue.popleft()

            for char, s in self.goto_fn[r].items():
                queue.append(s)
                
                state = self.failure_fn[r]
                while state != self.root and char not in self.goto_fn[state]:
                    state = self.failure_fn[state]
                
                if char in self.goto_fn[state]:
                    self.failure_fn[s] = self.goto_fn[state][char]
                else:
                    self.failure_fn[s] = self.root
                
                self.output_fn[s].update(self.output_fn[self.failure_fn[s]])

    def _next_state(self, current_state: int, char: str) -> int:
        while current_state != self.root and char not in self.goto_fn[current_state]:
            current_state = self.failure_fn[current_state]
        
        if char in self.goto_fn[current_state]:
            return self.goto_fn[current_state][char]
        else:
            return self.root

    def search(self, text: str) -> list[tuple[int, str]]:
        current_state = self.root
        found_matches = []

        for i, char in enumerate(text):
            current_state = self._next_state(current_state, char)
            
            if self.output_fn[current_state]:
                for pattern in self.output_fn[current_state]:
                    found_matches.append((i, pattern))
        return found_matches

# --- Classes de Dados (DataObject, DataRecord, IndexEntry) ---
class DataObject:
    def __init__(self, default_time_string, traffic_control_device, weather_condition, 
                 lighting_condition, first_crash_type, trafficway_type, 
                 alignment, roadway_surface_cond, road_defect, crash_type, 
                 intersection_related_i, damage, prim_contributory_cause, 
                 num_units, most_severe_injury, injuries_total, injuries_fatal, 
                 injuries_incapacitating, injuries_non_incapacitating, 
                 injuries_reported_not_evident, injuries_no_indication, 
                 crash_hour, crash_day_of_week, crash_month):
        self.default_time_string = default_time_string
        self._crash_date = self._parse_datetime(default_time_string)
        self.traffic_control_device = traffic_control_device
        self.weather_condition = weather_condition
        
        # Manter como atributos privados com propriedades para controlar a conversão
        self._lighting_condition = self._to_list_of_strings(lighting_condition)
        self._crash_type = self._to_list_of_strings(crash_type)
        self._most_severe_injury = self._to_list_of_strings(most_severe_injury)

        self.first_crash_type = first_crash_type
        self.trafficway_type = trafficway_type
        self.alignment = alignment
        self.roadway_surface_cond = roadway_surface_cond
        self.road_defect = road_defect
        self.intersection_related_i = intersection_related_i
        self.damage = damage
        self.prim_contributory_cause = prim_contributory_cause
        self.num_units = num_units
        self.injuries_total = injuries_total
        self.injuries_fatal = injuries_fatal
        self.injuries_incapacitating = injuries_incapacitating
        self.injuries_non_incapacitating = injuries_non_incapacitating
        self.injuries_reported_not_evident = injuries_reported_not_evident
        self.injuries_no_indication = injuries_no_indication
        self.crash_hour = crash_hour
        self.crash_day_of_week = crash_day_of_week
        self.crash_month = crash_month

    def _parse_datetime(self, time_string):
        try:
            return datetime.strptime(time_string, '%m/%d/%Y %I:%M:%S %p')
        except ValueError:
            return None
    
    def _to_list_of_strings(self, value):
        if isinstance(value, list):
            return [s.strip() for s in value if s.strip()]
        elif isinstance(value, str):
            if ',' in value:
                return [s.strip() for s in value.split(',') if s.strip()]
            elif '/' in value:
                return [s.strip() for s in value.split('/') if s.strip()]
            else:
                return [value.strip()] if value.strip() else []
        return []

    def _to_single_string(self, value_list):
        if isinstance(value_list, list):
            return ','.join(value_list)
        return str(value_list)

    @property
    def crash_date(self):
        return self._crash_date

    @property
    def lighting_condition(self):
        return self._lighting_condition

    @property
    def crash_type(self):
        return self._crash_type

    @property
    def most_severe_injury(self):
        return self._most_severe_injury

    @classmethod
    def from_csv_row(cls, row_string):
        parts = row_string.strip().split(';')
        if len(parts) != 24:
            raise ValueError(f"Formato de linha inválido. Esperado 24 colunas, obtido {len(parts)}. Linha: '{row_string}'")
        
        def safe_int(val):
            try:
                return int(val.strip())
            except (ValueError, TypeError):
                return 0

        def safe_float(val):
            try:
                return float(val.strip())
            except (ValueError, TypeError):
                return 0.0

        return cls(
            default_time_string=parts[0].strip(),
            traffic_control_device=parts[1].strip(),
            weather_condition=parts[2].strip(),
            lighting_condition=parts[3].strip(), # Convertido para lista no __init__
            first_crash_type=parts[4].strip(),
            trafficway_type=parts[5].strip(),
            alignment=parts[6].strip(),
            roadway_surface_cond=parts[7].strip(),
            road_defect=parts[8].strip(),
            crash_type=parts[9].strip(),         # Convertido para lista no __init__
            intersection_related_i=parts[10].strip(),
            damage=parts[11].strip(),
            prim_contributory_cause=parts[12].strip(),
            num_units=safe_int(parts[13]),
            most_severe_injury=parts[14].strip(), # Convertido para lista no __init__
            injuries_total=safe_float(parts[15]),
            injuries_fatal=safe_float(parts[16]),
            injuries_incapacitating=safe_float(parts[17]),
            injuries_non_incapacitating=safe_float(parts[18]),
            injuries_reported_not_evident=safe_float(parts[19]),
            injuries_no_indication=safe_float(parts[20]),
            crash_hour=safe_int(parts[21]),
            crash_day_of_week=safe_int(parts[22]),
            crash_month=safe_int(parts[23])
        )

    def to_dict(self):
        return {
            "default_time_string": self.default_time_string,
            "traffic_control_device": self.traffic_control_device,
            "weather_condition": self.weather_condition,
            "lighting_condition": self._to_single_string(self._lighting_condition),
            "first_crash_type": self.first_crash_type,
            "trafficway_type": self.trafficway_type,
            "alignment": self.alignment,
            "roadway_surface_cond": self.roadway_surface_cond,
            "road_defect": self.road_defect,
            "crash_type": self._to_single_string(self._crash_type),
            "intersection_related_i": self.intersection_related_i,
            "damage": self.damage,
            "prim_contributory_cause": self.prim_contributory_cause,
            "num_units": self.num_units,
            "most_severe_injury": self._to_single_string(self._most_severe_injury),
            "injuries_total": self.injuries_total,
            "injuries_fatal": self.injuries_fatal,
            "injuries_incapacitating": self.injuries_incapacitating,
            "injuries_non_incapacitating": self.injuries_non_incapacitating,
            "injuries_reported_not_evident": self.injuries_reported_not_evident,
            "injuries_no_indication": self.injuries_no_indication,
            "crash_hour": self.crash_hour,
            "crash_day_of_week": self.crash_day_of_week,
            "crash_month": self.crash_month
        }

    @classmethod
    def from_dict(cls, data_dict):
        # Mapeamento reverso para lidar com os campos que são listas no __init__
        return cls(
            default_time_string=data_dict["default_time_string"],
            traffic_control_device=data_dict["traffic_control_device"],
            weather_condition=data_dict["weather_condition"],
            lighting_condition=data_dict["lighting_condition"], # Será convertido para lista no __init__
            first_crash_type=data_dict["first_crash_type"],
            trafficway_type=data_dict["trafficway_type"],
            alignment=data_dict["alignment"],
            roadway_surface_cond=data_dict["roadway_surface_cond"],
            road_defect=data_dict["road_defect"],
            crash_type=data_dict["crash_type"], # Será convertido para lista no __init__
            intersection_related_i=data_dict["intersection_related_i"],
            damage=data_dict["damage"],
            prim_contributory_cause=data_dict["prim_contributory_cause"],
            num_units=data_dict["num_units"],
            most_severe_injury=data_dict["most_severe_injury"], # Será convertido para lista no __init__
            injuries_total=data_dict["injuries_total"],
            injuries_fatal=data_dict["injuries_fatal"],
            injuries_incapacitating=data_dict["injuries_incapacitating"],
            injuries_non_incapacitating=data_dict["injuries_non_incapacitating"],
            injuries_reported_not_evident=data_dict["injuries_reported_not_evident"],
            injuries_no_indication=data_dict["injuries_no_indication"],
            crash_hour=data_dict["crash_hour"],
            crash_day_of_week=data_dict["crash_day_of_week"],
            crash_month=data_dict["crash_month"]
        )

    # MÉTODO PARA STREAMLIT: Reconstrói a linha CSV para preenchimento de campos
    def to_csv_row_format(self):
        # Esta função reconstrói a linha CSV a partir dos atributos do DataObject.
        # É importante que a ordem e o formato correspondam ao from_csv_row.
        # Note que _to_single_string é usado para campos que são listas internamente.
        return ";".join([
            self.default_time_string,
            self.traffic_control_device,
            self.weather_condition,
            self._to_single_string(self._lighting_condition),
            self.first_crash_type,
            self.trafficway_type,
            self.alignment,
            self.roadway_surface_cond,
            self.road_defect,
            self._to_single_string(self._crash_type),
            self.intersection_related_i,
            self.damage,
            self.prim_contributory_cause,
            str(self.num_units),
            self._to_single_string(self._most_severe_injury),
            str(self.injuries_total),
            str(self.injuries_fatal),
            str(self.injuries_incapacitating),
            str(self.injuries_non_incapacitating),
            str(self.injuries_reported_not_evident),
            str(self.injuries_no_indication),
            str(self.crash_hour),
            str(self.crash_day_of_week),
            str(self.crash_month)
        ])


import shelve

class DataRecord:
    HEADER_FORMAT = "!I?32sI" # Record ID (int), Is Valid (bool), Checksum (32s), Data Size (int)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, record_id: int, data_object: DataObject, is_valid: bool = True):
        self.record_id = record_id
        self.data_object = data_object
        self.is_valid = is_valid

    def serialize(self) -> bytes:
        data_bytes = json.dumps(self.data_object.to_dict()).encode('utf-8')
        checksum = hashlib.sha256(data_bytes).digest()
        data_size = len(data_bytes)
        
        header_bytes = struct.pack(
            self.HEADER_FORMAT,
            self.record_id,
            self.is_valid,
            checksum,
            data_size
        )
        return header_bytes + data_bytes

    @classmethod
    def deserialize(cls, record_bytes: bytes):
        if len(record_bytes) < cls.HEADER_SIZE:
            raise ValueError("Bytes buffer too small to contain header.")
        
        header_parts = struct.unpack(cls.HEADER_FORMAT, record_bytes[:cls.HEADER_SIZE])
        record_id, is_valid, checksum_read, data_size = header_parts

        data_start = cls.HEADER_SIZE
        data_end = data_start + data_size
        if len(record_bytes) < data_end:
            raise ValueError("Bytes buffer too small to contain full data.")
        
        data_bytes = record_bytes[data_start:data_end]

        calculated_checksum = hashlib.sha256(data_bytes).digest()
        if calculated_checksum != checksum_read:
            is_valid = False # Marca como inválido se o checksum não bater

        data_dict = json.loads(data_bytes.decode('utf-8'))
        data_object = DataObject.from_dict(data_dict)

        return cls(record_id, data_object, is_valid), data_end

class IndexEntry:
    ENTRY_FORMAT = "!I?Q" # Record ID (unsigned int), Is Valid (boolean), Position (unsigned long long)
    ENTRY_SIZE = struct.calcsize(ENTRY_FORMAT)

    def __init__(self, record_id: int, position: int, is_valid: bool = True):
        self.record_id = record_id
        self.is_valid = is_valid
        self.position = position

    def serialize(self) -> bytes:
        return struct.pack(
            self.ENTRY_FORMAT,
            self.record_id,
            self.is_valid,
            self.position
        )

    @classmethod
    def deserialize(cls, entry_bytes: bytes):
        if len(entry_bytes) < cls.ENTRY_SIZE:
            raise ValueError("Bytes buffer too small to contain index entry.")
        
        record_id, is_valid, position = struct.unpack(cls.ENTRY_FORMAT, entry_bytes[:cls.ENTRY_SIZE])
        return cls(record_id, position, is_valid), cls.ENTRY_SIZE


class InvertedIndexManager:
    def __init__(self, inv_filepath_prefix: str):
        self.crash_type_db_path = f"{inv_filepath_prefix}_crash_type"
        self.injuries_total_db_path = f"{inv_filepath_prefix}_injuries_total"
        self.lighting_condition_db_path = f"{inv_filepath_prefix}_lighting_condition"
        self.most_severe_injury_db_path = f"{inv_filepath_prefix}_most_severe_injury"
        
        # Use dicionários para as referências aos shelves abertos
        self.shelves = {}
        self._open_shelves()

    def _open_shelves(self):
        try:
            self.shelves['crash_type'] = shelve.open(self.crash_type_db_path, 'c')
            self.shelves['injuries_total'] = shelve.open(self.injuries_total_db_path, 'c')
            self.shelves['lighting_condition'] = shelve.open(self.lighting_condition_db_path, 'c')
            self.shelves['most_severe_injury'] = shelve.open(self.most_severe_injury_db_path, 'c')
        except Exception as e:
            st.error(f"Erro ao abrir um dos arquivos de índice invertido: {e}")
            raise # Re-raise para que a aplicação não continue com shelves problemáticos


    def _add_to_shelf_index(self, shelf_name: str, key, record_id: int):
        shelf = self.shelves.get(shelf_name)
        if shelf is None:
            st.error(f"Shelf '{shelf_name}' não está aberto.")
            return

        str_key = str(key) 
        record_ids_list = shelf.get(str_key, [])
        if record_id not in record_ids_list:
            record_ids_list.append(record_id)
            shelf[str_key] = record_ids_list

    def _remove_from_shelf_index(self, shelf_name: str, record_id: int):
        shelf = self.shelves.get(shelf_name)
        if shelf is None:
            st.error(f"Shelf '{shelf_name}' não está aberto.")
            return

        keys_to_process = list(shelf.keys()) 
        for key in keys_to_process:
            record_ids_list = shelf[key]
            if record_id in record_ids_list:
                record_ids_list.remove(record_id)
                if not record_ids_list:
                    del shelf[key]
                else:
                    shelf[key] = record_ids_list

    def add_entry(self, data_object: DataObject, record_id: int):
        for val in data_object.crash_type:
            self._add_to_shelf_index('crash_type', val, record_id)
        
        self._add_to_shelf_index('injuries_total', data_object.injuries_total, record_id)

        for val in data_object.lighting_condition:
            self._add_to_shelf_index('lighting_condition', val, record_id)

        for val in data_object.most_severe_injury:
            self._add_to_shelf_index('most_severe_injury', val, record_id)
        
    def get_record_ids_by_crash_type(self, crash_type_value: str) -> list[int]:
        return self.shelves['crash_type'].get(crash_type_value, [])

    def get_record_ids_by_injuries_total(self, injuries_total_value: float) -> list[int]:
        return self.shelves['injuries_total'].get(str(injuries_total_value), [])

    def get_record_ids_by_lighting_condition(self, lighting_condition_value: str) -> list[int]:
        return self.shelves['lighting_condition'].get(lighting_condition_value, [])

    def get_record_ids_by_most_severe_injury(self, most_severe_injury_value: str) -> list[int]:
        return self.shelves['most_severe_injury'].get(most_severe_injury_value, [])
    
    def search_crash_type_with_aho_corasick(self, patterns: list[str]) -> set[int]:
        automaton = AhoCorasick(patterns)
        found_record_ids = set()

        # Iterar sobre as chaves do shelf 'crash_type'
        # Criar uma cópia das chaves para evitar RuntimeError: dictionary changed size during iteration
        keys_in_index = list(self.shelves['crash_type'].keys())

        for key_in_index in keys_in_index:
            matches = automaton.search(key_in_index)
            
            if matches:
                record_ids_for_key = self.shelves['crash_type'].get(key_in_index, [])
                found_record_ids.update(record_ids_for_key)

        return found_record_ids

    def delete_record_from_indexes(self, record_id: int):
        self._remove_from_shelf_index('crash_type', record_id)
        self._remove_from_shelf_index('injuries_total', record_id)
        self._remove_from_shelf_index('lighting_condition', record_id)
        self._remove_from_shelf_index('most_severe_injury', record_id)
        
        # Sincronizar todos os shelves após as operações de exclusão
        for shelf in self.shelves.values():
            if shelf is not None:
                shelf.sync()

    def update_indexes_for_record(self, record_id: int, old_data_object: DataObject, new_data_object: DataObject):
        # 1. Remover entradas antigas
        for val in old_data_object.crash_type:
            self._remove_from_shelf_index('crash_type', record_id)
        self._remove_from_shelf_index('injuries_total', record_id)
        for val in old_data_object.lighting_condition:
            self._remove_from_shelf_index('lighting_condition', record_id)
        for val in old_data_object.most_severe_injury:
            self._remove_from_shelf_index('most_severe_injury', record_id)

        # 2. Adicionar novas entradas
        for val in new_data_object.crash_type:
            self._add_to_shelf_index('crash_type', val, record_id)
        self._add_to_shelf_index('injuries_total', new_data_object.injuries_total, record_id)
        for val in new_data_object.lighting_condition:
            self._add_to_shelf_index('lighting_condition', val, record_id)
        for val in new_data_object.most_severe_injury:
            self._add_to_shelf_index('most_severe_injury', val, record_id)

        # Sincronizar todos os shelves após as operações de atualização
        for shelf in self.shelves.values():
            if shelf is not None:
                shelf.sync()


    def close(self):
        for shelf in self.shelves.values():
            if shelf:
                shelf.close()

# --- DataManager ---
class DataManager:
    def __init__(self, db_filepath: str, index_filepath: str, inv_filepath_prefix: str):
        self.db_filepath = db_filepath
        self.index_filepath = index_filepath
        self.inv_filepath_prefix = inv_filepath_prefix
        self.current_id = 0 
        self.index_map = {} # Cache in-memory do índice
        self.inverted_index_manager = None # Inicializar após carregar o índice, se necessário
        
        self._load_index()
        # O InvertedIndexManager só é instanciado e aberto após o DataManager tentar carregar seu índice.
        # Isso garante que a limpeza de arquivos (se habilitada) ocorra antes.
        self.inverted_index_manager = InvertedIndexManager(inv_filepath_prefix)


    def _load_index(self):
        if not os.path.exists(self.index_filepath):
            return

        with open(self.index_filepath, 'rb') as f:
            while True:
                entry_bytes = f.read(IndexEntry.ENTRY_SIZE)
                if not entry_bytes:
                    break # Fim do arquivo
                try:
                    entry, _ = IndexEntry.deserialize(entry_bytes)
                    # Não adicionamos entradas inválidas ao index_map durante o carregamento.
                    # Elas são 'buracos' no arquivo de índice, mas o get_record() ainda as ignoraria.
                    if entry.is_valid:
                        self.index_map[entry.record_id] = entry
                        if entry.record_id >= self.current_id:
                            self.current_id = entry.record_id + 1
                except ValueError as e:
                    st.warning(f"Erro ao carregar entrada do índice: {e}. O arquivo de índice pode estar corrompido a partir deste ponto.")
                    break # Parar de ler o índice se encontrar um erro

    def _write_index_entry(self, entry: IndexEntry):
        # Escreve a nova entrada no final do arquivo de índice.
        # Isso é um append. Não se sobrescreve entradas existentes.
        with open(self.index_filepath, 'ab') as f:
            f.write(entry.serialize())
        self.index_map[entry.record_id] = entry # Atualiza o cache in-memory

    def add_record(self, data_object: DataObject) -> int:
        record_id = self.current_id
        
        data_record = DataRecord(record_id, data_object, is_valid=True)
        serialized_data = data_record.serialize()
        
        current_position = 0
        if os.path.exists(self.db_filepath):
            current_position = os.path.getsize(self.db_filepath)

        with open(self.db_filepath, 'ab') as f:
            f.write(serialized_data)
        
        index_entry = IndexEntry(record_id, current_position, is_valid=True)
        self._write_index_entry(index_entry)
        
        self.inverted_index_manager.add_entry(data_object, record_id)
        
        self.current_id += 1 # Incrementa o ID para o próximo registro
        return record_id

    def get_record(self, record_id: int) -> DataObject | None:
        if record_id not in self.index_map:
            return None
        
        index_entry = self.index_map[record_id]
        if not index_entry.is_valid:
            return None # Registro marcado como inválido no índice

        try:
            with open(self.db_filepath, 'rb') as f:
                f.seek(index_entry.position)
                header_bytes = f.read(DataRecord.HEADER_SIZE)
                if len(header_bytes) < DataRecord.HEADER_SIZE:
                    st.warning(f"Erro: Cabeçalho incompleto lido para o registro ID {record_id}. Posição: {index_entry.position}")
                    return None
                
                # Desempacotar o cabeçalho para obter o tamanho dos dados e checksum
                record_id_db, is_valid_db, checksum_read, data_size = struct.unpack(DataRecord.HEADER_FORMAT, header_bytes)
                
                if not is_valid_db: # Checa a validade no cabeçalho do DB também
                    return None

                remaining_bytes = f.read(data_size)
                
                full_record_bytes = header_bytes + remaining_bytes
                
                data_record, bytes_consumed = DataRecord.deserialize(full_record_bytes)
                
                if not data_record.is_valid: # Checa validade após deserialização (inclui checksum)
                    st.warning(f"Registro ID {record_id} está corrompido (checksum inválido) ou marcado como inválido no DB.")
                    return None
                
                return data_record.data_object
        except FileNotFoundError:
            st.error(f"Arquivo de banco de dados não encontrado: {self.db_filepath}")
            return None
        except ValueError as e:
            st.error(f"Erro ao ler registro ID {record_id} do DB: {e}")
            return None
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao recuperar registro ID {record_id}: {e}")
            return None

    def delete_record(self, record_id: int) -> bool:
        if record_id not in self.index_map:
            st.warning(f"Registro com ID {record_id} não encontrado para exclusão.")
            return False

        index_entry = self.index_map[record_id]
        if not index_entry.is_valid:
            st.warning(f"Registro com ID {record_id} já está marcado como inválido.")
            return False

        try:
            old_data_object = self.get_record(record_id)
            if not old_data_object:
                st.warning(f"Não foi possível recuperar DataObject para o registro ID {record_id} para limpeza do índice.")
                # Prosseguir com a marcação no DB e índice, mas notificar
            
            with open(self.db_filepath, 'r+b') as f:
                f.seek(index_entry.position)
                
                header_bytes_original = f.read(DataRecord.HEADER_SIZE)
                if len(header_bytes_original) < DataRecord.HEADER_SIZE:
                    st.error(f"Erro: Cabeçalho incompleto para o registro ID {record_id} na posição {index_entry.position}. Não pode ser marcado como inválido.")
                    return False
                
                # Apenas para obter o data_size original
                _, _, _, data_size_original = struct.unpack(DataRecord.HEADER_FORMAT, header_bytes_original)

                # Criar um novo cabeçalho com is_valid=False
                invalid_header_bytes = struct.pack(
                    DataRecord.HEADER_FORMAT,
                    record_id,
                    False, # Marcar como inválido
                    hashlib.sha256(b'').digest(), # Checksum vazio/inválido
                    data_size_original
                )

                f.seek(index_entry.position) # Voltar para a posição do registro
                f.write(invalid_header_bytes)
                f.flush() # Garantir que as alterações sejam gravadas no disco

            # Marcar como inválido no cache in-memory do índice
            self.index_map[record_id].is_valid = False
            # Escrever uma nova entrada no arquivo de índice (apenas para registrar a invalidação, não estritamente necessário para funcionamento)
            # É mais robusto reescrever o arquivo de índice periodicamente ou em um shutdown limpo.
            # Por enquanto, a marcação in-memory e a remoção dos índices invertidos são suficientes.
            
            self.inverted_index_manager.delete_record_from_indexes(record_id)
            
            return True

        except FileNotFoundError:
            st.error(f"Arquivo de banco de dados não encontrado: {self.db_filepath}")
            return False
        except Exception as e:
            st.error(f"Ocorreu um erro durante a exclusão do registro ID {record_id}: {e}")
            return False

    def update_record(self, record_id: int, new_data_object: DataObject) -> bool:
        if record_id not in self.index_map or not self.index_map[record_id].is_valid:
            st.warning(f"Registro com ID {record_id} não encontrado ou é inválido para atualização.")
            return False

        original_index_entry = self.index_map[record_id]
        original_position = original_index_entry.position

        try:
            # 1. Obter dados antigos para calcular tamanho e atualizar índices invertidos
            with open(self.db_filepath, 'rb') as f:
                f.seek(original_position)
                
                header_bytes_old = f.read(DataRecord.HEADER_SIZE)
                if len(header_bytes_old) < DataRecord.HEADER_SIZE:
                    st.error(f"Erro: Cabeçalho incompleto para o registro ID {record_id} na posição {original_position}.")
                    return False
                
                old_rec_id, old_is_valid, old_checksum, old_data_size = struct.unpack(
                    DataRecord.HEADER_FORMAT, header_bytes_old
                )
                
                old_data_bytes = f.read(old_data_size)
                # Recria o DataRecord para obter o old_data_object para atualização do índice invertido
                old_full_record_bytes = header_bytes_old + old_data_bytes
                old_data_record, _ = DataRecord.deserialize(old_full_record_bytes)
                old_data_object = old_data_record.data_object # Objeto original para remover dos índices
                
                original_record_total_size = DataRecord.HEADER_SIZE + old_data_size

            # 2. Serializar o novo DataObject
            new_data_record = DataRecord(record_id, new_data_object, is_valid=True)
            serialized_new_record = new_data_record.serialize()
            new_record_total_size = len(serialized_new_record)
            
            # 3. Decidir se sobrescreve ou realoca
            with open(self.db_filepath, 'r+b') as f:
                if new_record_total_size > original_record_total_size:
                    # O novo registro é maior, então ele precisa ser escrito no final do arquivo.
                    # O registro antigo na posição original é marcado como inválido.
                    st.info(f"Registro {record_id}: Novo tamanho ({new_record_total_size}) é maior que o original ({original_record_total_size}). Realocando para o final do arquivo.")
                    
                    # Marcar o registro antigo como inválido no local original
                    f.seek(original_position)
                    invalid_header_bytes = struct.pack(
                        DataRecord.HEADER_FORMAT,
                        record_id,
                        False, # Marcar como inválido
                        hashlib.sha256(b'').digest(), # Checksum vazio/inválido para o registro antigo
                        old_data_size # Manter o data_size original
                    )
                    f.write(invalid_header_bytes)
                    f.flush() # Garantir que as alterações sejam gravadas

                    # Escrever o novo registro no final do arquivo
                    new_position = os.path.getsize(self.db_filepath)
                    f.seek(new_position)
                    f.write(serialized_new_record)
                    f.flush()

                    # Criar uma nova entrada de índice para a nova posição
                    new_index_entry = IndexEntry(record_id, new_position, is_valid=True)
                    self._write_index_entry(new_index_entry) # Adiciona no final do arquivo de índice
                    
                else:
                    # O novo registro é menor ou igual, pode sobrescrever no local.
                    st.info(f"Registro {record_id}: Novo tamanho ({new_record_total_size}) é menor ou igual ao original ({original_record_total_size}). Sobrescrevendo no local.")
                    
                    f.seek(original_position)
                    f.write(serialized_new_record)
                    
                    # Preencher o restante do espaço com zeros se o novo registro for menor
                    bytes_to_pad = original_record_total_size - new_record_total_size
                    if bytes_to_pad > 0:
                        f.write(b'\x00' * bytes_to_pad)
                    f.flush() # Garantir que as alterações sejam gravadas

                    # Atualizar a entrada de índice (apenas para garantir a validade no arquivo de índice se reescrito)
                    new_index_entry = IndexEntry(record_id, original_position, is_valid=True)
                    self._write_index_entry(new_index_entry) # Adiciona no final do arquivo de índice

            # 4. Atualizar índices invertidos com base nos dados antigos e novos
            self.inverted_index_manager.update_indexes_for_record(record_id, old_data_object, new_data_object)
            
            return True

        except FileNotFoundError:
            st.error(f"Arquivo de banco de dados não encontrado: {self.db_filepath}")
            return False
        except Exception as e:
            st.error(f"Ocorreu um erro durante a atualização do registro ID {record_id}: {e}")
            return False
            
    def close(self):
        if self.inverted_index_manager:
            self.inverted_index_manager.close()


# --- Configuração de Arquivos para Streamlit ---
DB_FILE = 'crash_data.db'
INDEX_FILE = 'crash_data.idx'
INV_INDEX_PREFIX = 'crash_data_inv'

# --- Inicialização do DataManager (usando st.cache_resource para persistência) ---
@st.cache_resource
def get_data_manager_for_streamlit():
    # Limpa arquivos anteriores se existirem.
    # CUIDADO: Estas linhas apagarão seus dados e índices persistidos cada vez que o Streamlit
    # for *reiniciado*. Para manter dados entre sessões, remova ou comente estas linhas
    # após a primeira execução, OU use um nome de arquivo diferente para testar a persistência.
    print(f"[{datetime.now()}] Inicializando DataManager para Streamlit. Verificando e limpando arquivos antigos...")
    for f_path in [DB_FILE, INDEX_FILE]:
        if os.path.exists(f_path):
            os.remove(f_path)
            print(f"[{datetime.now()}] Removido: {f_path}")
    # Limpa os arquivos do shelve que têm extensões variadas
    for ext in ['', '.dat', '.dir', '.bak']:
        for prefix in ['crash_type', 'injuries_total', 'lighting_condition', 'most_severe_injury']:
            shelf_file = f"{INV_INDEX_PREFIX}_{prefix}{ext}"
            if os.path.exists(shelf_file):
                os.remove(shelf_file)
                print(f"[{datetime.now()}] Removido: {shelf_file}")
    print(f"[{datetime.now()}] Arquivos de dados e índices limpos/verificados.")
    
    manager = DataManager(DB_FILE, INDEX_FILE, INV_INDEX_PREFIX)
    print(f"[{datetime.now()}] DataManager instanciado para Streamlit com ID inicial: {manager.current_id}")
    return manager

data_manager = get_data_manager_for_streamlit()

def setup_ui():
    # --- Título da Aplicação ---
    st.title("🚧 Sistema de Gerenciamento de Dados de Acidentes de Trânsito 🚧")
    st.markdown("Uma aplicação para gerenciar e consultar registros de acidentes.")

    # --- Sidebar para Navegação ou Ações Principais ---
    st.sidebar.header("Funções Principais")
    option = st.sidebar.radio(
        "Selecione uma operação:",
        ("Adicionar Registro", "Carregar Dados CSV", "Buscar Registro", "Atualizar Registro", "Excluir Registro", "Consultar Índices", "Visualizar Todos os Registros")
    )

    # --- Seção para Adicionar Registro ---
    if option == "Adicionar Registro":
        st.header("➕ Adicionar Novo Registro")
        st.info("Insira os dados do registro no formato CSV (campos separados por ';'). Certifique-se de que há 24 campos.")
        
        # Exemplo de dados para facilitar o teste
        example_csv = "01/01/2023 12:00:00 PM;STOP SIGN;CLEAR;DAYLIGHT;REAR END;NOT APPLICABLE;STRAIGHT AND LEVEL;DRY;NO DEFECTS;PEDESTRIAN/BICYCLE;N;NONE;UNSAFE SPEED;2;NO INDICATION OF INJURY,MINOR INJURY;0.0;0.0;0.0;0.0;0.0;0.0;12;1;1"
        
        csv_input = st.text_area("Dados do Registro (CSV)", height=150, value=example_csv,
                                help="Cole aqui uma linha de dados CSV com 24 campos. Ex: Data;DispositivoControle;Clima;...")
        
        if st.button("Salvar Novo Registro"):
            if csv_input.strip():
                try:
                    data_obj = DataObject.from_csv_row(csv_input)
                    record_id = data_manager.add_record(data_obj)
                    st.success(f"✅ Registro adicionado com sucesso! Novo ID: **{record_id}**")
                    st.subheader("Dados do Novo Registro:")
                    st.json(data_obj.to_dict())
                except ValueError as e:
                    st.error(f"❌ Erro de formato CSV: {e}. Por favor, verifique se todos os 24 campos estão presentes e corretos.")
                except Exception as e:
                    st.error(f"❌ Ocorreu um erro inesperado ao adicionar o registro: {e}")
            else:
                st.warning("⚠️ Por favor, insira os dados do registro para adicionar.")

    # --- Seção para Carregar Dados CSV ---
    elif option == "Carregar Dados CSV":
        st.header("📥 Carregar Dados a Partir de CSV")
        st.info("Escolha carregar um arquivo .csv do seu computador ou de uma URL.")

        uploaded_file = st.file_uploader("Upload de arquivo CSV", type=["csv"],
                                        help="Arraste e solte ou clique para fazer upload de um arquivo CSV.")
        
        st.markdown("---")
        csv_url = st.text_input("Ou insira uma URL de arquivo CSV:", 
                                placeholder="Ex: https://raw.githubusercontent.com/user/repo/data.csv",
                                help="Certifique-se de que a URL aponta diretamente para o conteúdo RAW do CSV.")
        colup,colset=st.columns(2)
        with colup:
            setupload =st.button("Carregar Dados do CSV")
        with colset:
            setencode=st.selectbox("Encode do CSV",["latin-1","utf-8","utf-16"],key="encode")
        if setupload:    
            csv_content = None
            source_name = ""

            if uploaded_file is not None:
                csv_content = uploaded_file.getvalue().decode(setencode)
                source_name = uploaded_file.name
            elif csv_url:
                try:
                    with st.spinner("Baixando CSV da URL..."):
                        response = requests.get(csv_url)
                        response.raise_for_status() # Levanta um erro para status HTTP ruins (4xx ou 5xx)
                        csv_content = response.text
                        source_name = csv_url
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Erro ao baixar o arquivo da URL: {e}. Verifique a URL e sua conexão.")
                    csv_content = None
            
            if csv_content:
                lines = csv_content.strip().split('\n')
                
                # Heurística simples para detectar cabeçalho
                # Assume que a primeira linha é o cabeçalho se houver mais de uma linha e o upload não for de uma linha única.
                has_header = st.checkbox("Meu arquivo CSV tem cabeçalho (primeira linha)?", value=True)
                
                if has_header and len(lines) > 0:
                    header = lines[0]
                    lines = lines[1:] # Ignora o cabeçalho
                    st.info(f"Cabeçalho detectado e ignorado: `{header}`")

                if not lines:
                    st.warning("⚠️ O arquivo CSV está vazio ou contém apenas o cabeçalho.")
                else:
                    total_records = len(lines)
                    records_added = 0
                    errors_count = 0
                    
                    progress_text = "Processando registros CSV..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    for i, line in enumerate(lines):
                        if line.strip(): # Garante que a linha não esteja vazia
                            try:
                                data_obj = DataObject.from_csv_row(line)
                                data_manager.add_record(data_obj)
                                records_added += 1
                            except ValueError as e:
                                st.warning(f"⚠️ Linha {i+1} ignorada devido a erro de formato: {e}. Linha: `{line[:100]}...`")
                                errors_count += 1
                            except Exception as e:
                                st.error(f"❌ Erro inesperado ao processar linha {i+1}: {e}. Linha: `{line[:100]}...`")
                                errors_count += 1
                        my_bar.progress((i + 1) / total_records, text=f"{progress_text} ({i+1}/{total_records})")
                    
                    my_bar.empty() # Remove a barra de progresso

                    if records_added > 0:
                        st.success(f"✅ {records_added} registros do arquivo **{source_name}** adicionados com sucesso à aplicação.")
                    if errors_count > 0:
                        st.warning(f"⚠️ {errors_count} linhas foram ignoradas devido a erros de processamento.")
                    if records_added == 0 and errors_count == 0:
                        st.info("Nenhuma linha válida encontrada no arquivo CSV para adicionar.")
            else:
                st.warning("⚠️ Por favor, faça upload de um arquivo CSV ou insira uma URL válida.")


    # --- Seção para Buscar Registro ---
    elif option == "Buscar Registro":
        st.header("🔍 Buscar Registro por ID")
        
        record_id_to_search = st.number_input("Digite o ID do Registro:", min_value=0, value=0, step=1, 
                                            help="Cada registro tem um ID único. Insira-o para buscar.")
        
        if st.button("Buscar Registro"):
            record = data_manager.get_record(record_id_to_search)
            if record:
                st.success(f"✅ Registro ID **{record_id_to_search}** encontrado:")
                st.subheader("Detalhes do Registro:")
                st.json(record.to_dict())
            else:
                st.warning(f"⚠️ Registro ID **{record_id_to_search}** não encontrado ou marcado como inválido.")

    # --- Seção para Atualizar Registro ---
    elif option == "Atualizar Registro":
        st.header("🔄 Atualizar Registro Existente")
        st.info("Primeiro, digite o ID do registro que deseja atualizar para carregar seus dados atuais.")
        
        record_id_to_update = st.number_input("ID do Registro para Atualizar:", min_value=0, value=0, step=1)
        
        if st.button("Carregar Registro para Edição"):
            if record_id_to_update is not None:
                current_record_obj = data_manager.get_record(record_id_to_update)
                if current_record_obj:
                    st.session_state['current_record_id'] = record_id_to_update
                    st.session_state['current_csv_data'] = current_record_obj.to_csv_row_format()
                    st.success(f"Registro ID {record_id_to_update} carregado. Edite os dados abaixo.")
                else:
                    st.error(f"❌ Registro ID {record_id_to_update} não encontrado ou inválido.")
                    # Limpa o estado se o ID não for válido
                    if 'current_record_id' in st.session_state:
                        del st.session_state['current_record_id']
                    if 'current_csv_data' in st.session_state:
                        del st.session_state['current_csv_data']
            else:
                st.warning("⚠️ Por favor, insira um ID de registro.")

        # Só mostra a área de edição se um registro válido foi carregado
        if 'current_record_id' in st.session_state and st.session_state['current_record_id'] == record_id_to_update:
            st.subheader(f"Editando Registro ID: {st.session_state['current_record_id']}")
            new_csv_input = st.text_area("Novos Dados do Registro (CSV)", height=150, 
                                        value=st.session_state.get('current_csv_data', ''),
                                        help="Edite esta linha CSV com os novos dados para o registro.")
            
            if st.button("Salvar Alterações"):
                try:
                    new_data_obj = DataObject.from_csv_row(new_csv_input)
                    update_success = data_manager.update_record(st.session_state['current_record_id'], new_data_obj)
                    if update_success:
                        st.success(f"✅ Registro ID **{st.session_state['current_record_id']}** atualizado com sucesso!")
                        st.subheader("Novos Dados:")
                        st.json(new_data_obj.to_dict())
                        # Limpar estado após atualização bem-sucedida para evitar edição acidental
                        del st.session_state['current_record_id']
                        del st.session_state['current_csv_data']
                    else:
                        st.error(f"❌ Falha ao atualizar registro ID **{st.session_state['current_record_id']}**.")
                except ValueError as e:
                    st.error(f"❌ Erro de formato CSV nos novos dados: {e}. Verifique os 24 campos.")
                except Exception as e:
                    st.error(f"❌ Ocorreu um erro inesperado durante a atualização: {e}")
        elif 'current_record_id' in st.session_state and st.session_state['current_record_id'] != record_id_to_update:
            # Informa ao usuário que ele precisa recarregar se mudar o ID no input
            st.warning("⚠️ O ID do registro no campo de entrada mudou. Clique em 'Carregar Registro para Edição' novamente para o novo ID.")


    # --- Seção para Excluir Registro ---
    elif option == "Excluir Registro":
        st.header("🗑️ Excluir Registro")
        st.warning("🚨 A exclusão aqui é **lógica**: o registro será marcado como inválido no banco de dados e removido dos índices invertidos. Ele não será fisicamente removido do arquivo.")
        
        record_id_to_delete = st.number_input("ID do Registro para Excluir:", min_value=0, value=0, step=1)
        
        if st.button("Confirmar Exclusão"):
            delete_success = data_manager.delete_record(record_id_to_delete)
            if delete_success:
                st.success(f"✅ Registro ID **{record_id_to_delete}** logicamente excluído com sucesso e removido dos índices.")
            else:
                st.error(f"❌ Falha ao excluir registro ID **{record_id_to_delete}**. Verifique se o ID existe e é válido.")

    # --- Seção para Consultar Índices ---
    elif option == "Consultar Índices":
        st.header("📊 Consultar Índices Invertidos")
        
        st.subheader("Busca por Tipo de Acidente (Aho-Corasick)")
        patterns_input = st.text_input("Padrões de busca (separados por vírgula, ex: PEDESTRIAN,BICYCLE):", "VEHICLE", 
                                    help="Insira múltiplos padrões separados por vírgula.")
        if st.button("Buscar por Tipo de Acidente"):
            patterns = [p.strip() for p in patterns_input.split(',') if p.strip()]
            if patterns:
                found_ids = data_manager.inverted_index_manager.search_crash_type_with_aho_corasick(patterns)
                if found_ids:
                    st.success(f"✅ Registros encontrados com padrões `{patterns}`: **{sorted(list(found_ids))}**")
                else:
                    st.info(f"ℹ️ Nenhum registro encontrado para padrões `{patterns}`.")
            else:
                st.warning("⚠️ Por favor, insira pelo menos um padrão de busca.")

        st.subheader("Busca por Total de Feridos")
        injuries_total_search = st.number_input("Total de Feridos (ex: 1.0, 2.0):", min_value=0.0, value=0.0, step=0.1)
        if st.button("Buscar por Total de Feridos"):
            found_ids = data_manager.inverted_index_manager.get_record_ids_by_injuries_total(injuries_total_search)
            if found_ids:
                st.success(f"✅ Registros com **{injuries_total_search}** feridos: **{sorted(list(found_ids))}**")
            else:
                st.info(f"ℹ️ Nenhum registro encontrado com **{injuries_total_search}** feridos.")

        st.subheader("Busca por Condição de Iluminação")
        # Tente listar as condições existentes no seu índice para um selectbox mais preciso
        # Por simplicidade, estou usando algumas comuns aqui.
        lighting_conditions_options = ["DAYLIGHT", "DAWN", "DARKNESS", "DUSK", "UNKNOWN", "OTHER"] 
        selected_lighting = st.selectbox("Selecione a Condição de Iluminação:", lighting_conditions_options)
        if st.button("Buscar por Condição de Iluminação"):
            found_ids = data_manager.inverted_index_manager.get_record_ids_by_lighting_condition(selected_lighting)
            if found_ids:
                st.success(f"✅ Registros com '{selected_lighting}': **{sorted(list(found_ids))}**")
            else:
                st.info(f"ℹ️ Nenhum registro encontrado com '{selected_lighting}'.")

        st.subheader("Busca por Lesão Mais Grave")
        most_severe_injuries_options = ["NO INDICATION OF INJURY", "MINOR INJURY", "FATAL INJURY", 
                                        "NON-INCAPACITATING INJURY", "INCAPACITATING INJURY", "UNKNOWN"] 
        selected_injury = st.selectbox("Selecione a Lesão Mais Grave:", most_severe_injuries_options)
        if st.button("Buscar por Lesão Mais Grave"):
            found_ids = data_manager.inverted_index_manager.get_record_ids_by_most_severe_injury(selected_injury)
            if found_ids:
                st.success(f"✅ Registros com '{selected_injury}': **{sorted(list(found_ids))}**")
            else:
                st.info(f"ℹ️ Nenhum registro encontrado com '{selected_injury}'.")

    # --- Seção para Visualizar Todos os Registros (para depuração/visão geral) ---
    elif option == "Visualizar Todos os Registros":
        st.header("📋 Visualizar Todos os Registros Válidos")
        st.info("Isso pode demorar um pouco se houver muitos registros. Exibe apenas os registros logicamente válidos.")

        if st.button("Carregar Todos os Registros"):
            all_records_data = []
            # Percorrer o index_map para obter todos os IDs válidos
            valid_ids = sorted([rec_id for rec_id, entry in data_manager.index_map.items() if entry.is_valid])
            
            if not valid_ids:
                st.info("Nenhum registro válido encontrado no banco de dados.")
            else:
                progress_text = "Carregando registros... Aguarde."
                my_bar = st.progress(0, text=progress_text)
                
                for i, record_id in enumerate(valid_ids):
                    record_obj = data_manager.get_record(record_id)
                    if record_obj:
                        record_dict = record_obj.to_dict()
                        record_dict['record_id'] = record_id # Adiciona o ID ao dicionário para visualização
                        all_records_data.append(record_dict)
                    my_bar.progress((i + 1) / len(valid_ids), text=f"{progress_text} ({i+1}/{len(valid_ids)})")
                
                my_bar.empty() # Remove a barra de progresso

                if all_records_data:
                    st.subheader(f"Total de Registros Válidos: {len(all_records_data)}")
                    # Converter para DataFrame para uma visualização tabular mais bonita
                    df = pd.DataFrame(all_records_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Nenhum registro válido encontrado após a tentativa de carregamento (pode haver problemas de leitura).")
        
if __name__ == "__main__":
    setup_ui()