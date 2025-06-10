import struct
import pickle
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
import copy # Importar copy para criar uma cópia do objeto antes de modificar para serialização

# Definindo um tipo para facilitar a leitura das anotações de tipo
StringOrStringList = Union[str, List[str]]

class DataObject:
    def __init__(self,
                 crash_date: datetime,
                 traffic_control_device: str,
                 weather_condition: str,
                 lighting_condition: StringOrStringList,
                 first_crash_type: str,
                 trafficway_type: str,
                 alignment: str,
                 roadway_surface_cond: str,
                 road_defect: str,
                 crash_type: StringOrStringList,
                 intersection_related_i: str,
                 damage: str,
                 prim_contributory_cause: str,
                 num_units: int,
                 most_severe_injury: StringOrStringList,
                 injuries_total: float,
                 injuries_fatal: float,
                 injuries_incapacitating: float,
                 injuries_non_incapacitating: float,
                 injuries_reported_not_eviden: float, # Corrigido nome de atributo
                 injuries_no_indication: float,
                 crash_hour: int,
                 crash_day_of_week: int,
                 crash_month: int,
                 id: Optional[int] = None):
        self.crash_date = crash_date
        self.traffic_control_device = traffic_control_device
        self.weather_condition = weather_condition
        self.lighting_condition = lighting_condition
        self.first_crash_type = first_crash_type
        self.trafficway_type = trafficway_type
        self.alignment = alignment
        self.roadway_surface_cond = roadway_surface_cond
        self.road_defect = road_defect
        self.crash_type = crash_type
        self.intersection_related_i = intersection_related_i
        self.damage = damage
        self.prim_contributory_cause = prim_contributory_cause
        self.num_units = num_units
        self.most_severe_injury = most_severe_injury
        self.injuries_total = injuries_total
        self.injuries_fatal = injuries_fatal
        self.injuries_incapacitating = injuries_incapacitating
        self.injuries_non_incapacitating = injuries_non_incapacitating
        self.injuries_reported_not_eviden = injuries_reported_not_eviden
        self.injuries_no_indication = injuries_no_indication
        self.crash_hour = crash_hour
        self.crash_day_of_week = crash_day_of_week
        self.crash_month = crash_month
        self.id = id

    def __repr__(self):
        lighting_condition_repr = repr(self.lighting_condition)
        crash_type_repr = repr(self.crash_type)
        most_severe_injury_repr = repr(self.most_severe_injury)

        return (f"DataObject(id={self.id}, crash_date={self.crash_date!r}, "
                f"traffic_control_device={self.traffic_control_device!r}, "
                f"weather_condition={self.weather_condition!r}, "
                f"lighting_condition={lighting_condition_repr}, "
                f"crash_type={crash_type_repr}, "
                f"most_severe_injury={most_severe_injury_repr}, "
                f"num_units={self.num_units}, "
                f"injuries_total={self.injuries_total})")

    # --- Atributos que devem ter a conversão de string para lista (na leitura) ---
    _LIST_CONVERTIBLE_STRING_FIELDS = {
        "lighting_condition",
        "crash_type",
        "most_severe_injury"
    }

    # --- NOVA FUNÇÃO para transformar lista em string para serialização ---
    @staticmethod
    def _convert_list_to_string_for_serialization(value: StringOrStringList) -> str:
        """
        Converte uma lista de strings em uma única string delimitada por ' , '.
        Se a lista tiver apenas um item, retorna esse item.
        Se já for uma string, retorna a própria string.
        """
        if isinstance(value, list):
            if len(value) > 1:
                return " , ".join(value)
            elif len(value) == 1:
                return value[0]
            else: # Lista vazia
                return "" # Ou None, dependendo de como você quer representar listas vazias
        return value # Se já é uma string, retorna como está

    # --- Função auxiliar para processar strings com delimitadores (na leitura) ---
    @staticmethod
    def _process_delimited_string(value: str) -> StringOrStringList:
        """
        Converte uma string em lista de strings se contiver ',' ou '/'.
        Remove espaços em branco e elementos vazios após a divisão.
        """
        if isinstance(value, str):
            if ',' in value:
                return [s.strip() for s in value.split(',') if s.strip()]
            elif '/' in value:
                return [s.strip() for s in value.split('/') if s.strip()]
        return value

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'DataObject':
        _id = data_dict.pop('id', None)
        
        def convert_value(key, value):
            if key == 'crash_date':
                if isinstance(value, str):
                    try:
                        return datetime.strptime(value, "%m/%d/%Y %I:%M:%S %p")
                    except ValueError:
                        raise ValueError(f"Formato de data inválido para 'crash_date': '{value}'")
                elif isinstance(value, datetime):
                    return value
                else:
                    raise TypeError(f"Tipo inválido para 'crash_date': esperado str ou datetime, obteve {type(value)}")
            elif key in ['num_units', 'crash_hour', 'crash_day_of_week', 'crash_month']:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Valor inválido para '{key}': '{value}'. Esperado um número inteiro.")
            elif key in ['injuries_total', 'injuries_fatal', 'injuries_incapacitating',
                          'injuries_non_incapacitating', 'injuries_reported_not_eviden',
                          'injuries_no_indication']:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Valor inválido para '{key}': '{value}'. Esperado um número decimal.")
            else:
                if key in DataObject._LIST_CONVERTIBLE_STRING_FIELDS:
                    return DataObject._process_delimited_string(str(value))
                return str(value)

        processed_data = {}
        for key in data_dict:
            try:
                processed_data[key] = convert_value(key, data_dict[key])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Erro ao processar campo '{key}' no dicionário: {e}")

        if 'injuries_reported_not_evident' in processed_data and 'injuries_reported_not_eviden' not in data_dict:
            processed_data['injuries_reported_not_eviden'] = processed_data.pop('injuries_reported_not_evident')

        return cls(id=_id, **processed_data)


    @classmethod
    def from_csv_line(cls, line: str, header: list[str]) -> 'DataObject':
        values = line.strip().split(';')
        if len(values) != len(header):
            raise ValueError(
                f"O número de valores na linha ({len(values)}) não corresponde "
                f"ao número de cabeçalhos ({len(header)}). Linha: '{line}'"
            )

        raw_data_dict = dict(zip(header, values))
        processed_data = {}

        converters = {
            'crash_date': lambda x: datetime.strptime(x, "%m/%d/%Y %I:%M:%S %p"),
            'num_units': int,
            'injuries_total': float,
            'injuries_fatal': float,
            'injuries_incapacitating': float,
            'injuries_non_incapacitating': float,
            'injuries_reported_not_eviden': float,
            'injuries_no_indication': float,
            'crash_hour': int,
            'crash_day_of_week': int,
            'crash_month': int,
        }

        for key in header:
            value = raw_data_dict.get(key)
            if value is None:
                raise ValueError(f"Campo '{key}' faltando na linha CSV: '{line}'")

            try:
                if key in converters:
                    processed_data[key] = converters[key](value)
                else:
                    if key in DataObject._LIST_CONVERTIBLE_STRING_FIELDS:
                        processed_data[key] = DataObject._process_delimited_string(value)
                    else:
                        processed_data[key] = value
            except ValueError as e:
                raise ValueError(f"Falha na conversão de tipo para '{key}': valor '{value}' inválido. Detalhe: {e}")
            except Exception as e:
                raise Exception(f"Erro inesperado ao processar '{key}' da linha CSV: {e}")

        if not (0 <= processed_data.get('crash_hour', -1) <= 23):
             raise ValueError(f"Hora do acidente inválida: {processed_data.get('crash_hour')}. Deve ser entre 0 e 23.")
        if not (1 <= processed_data.get('crash_day_of_week', -1) <= 7):
             raise ValueError(f"Dia da semana inválido: {processed_data.get('crash_day_of_week')}. Deve ser entre 1 e 7.")
        if not (1 <= processed_data.get('crash_month', -1) <= 12):
             raise ValueError(f"Mês inválido: {processed_data.get('crash_month')}. Deve ser entre 1 e 12.")
        
        return cls(**processed_data)

# --- Constantes de Cabeçalhos e Funções de Validação (do código anterior) ---
PORTUGUESE_HEADER_EXPECTED_STR = "data_do_acidente; dispositivo_de_controle_de_tráfego; condição_climática; condição_de_iluminação; tipo_primeiro_acidente; tipo_de_via_de_trânsito; alinhamento; condição_da_superfície_da_estrada; defeito_da_estrada; tipo_do_acidente; i.e. relacionados_ao_interseção; dano; causa_contributiva_primária; n.º_de_unidades; ferimento_mais_grave; total_de_ferimentos; ferimento_fatal; ferimento_incapacitante; ferimento_não_incapacitante; ferimento_relatado_não_evidente; ferimento_sem_indicação; hora_do_acidente; dia_da_semana_do_acidente; mês_do_acidente"
PORTUGUESE_HEADER_EXPECTED_LIST = [h.strip() for h in PORTUGUESE_HEADER_EXPECTED_STR.split(';')]

ENGLISH_HEADER_FOR_DATAOBJECT = [
    "crash_date", "traffic_control_device", "weather_condition", "lighting_condition",
    "first_crash_type", "trafficway_type", "alignment", "roadway_surface_cond",
    "road_defect", "crash_type", "intersection_related_i", "damage",
    "prim_contributory_cause", "num_units", "most_severe_injury", "injuries_total",
    "injuries_fatal", "injuries_incapacitating", "injuries_non_incapacitating",
    "injuries_reported_not_eviden",
    "injuries_no_indication", "crash_hour",
    "crash_day_of_week", "crash_month"
]

def atribuir_objeto_se_cabecalho_correto(csv_header_line: str, csv_data_line: str) -> Optional[DataObject]:
    provided_header_list = [h.strip() for h in csv_header_line.strip().split(';')]
    if provided_header_list == PORTUGUESE_HEADER_EXPECTED_LIST:
        try:
            data_object = DataObject.from_csv_line(csv_data_line, ENGLISH_HEADER_FOR_DATAOBJECT)
            return data_object
        except ValueError as e:
            raise ValueError(f"Erro ao processar a linha de dados mesmo com cabeçalho correto: {e}")
        except Exception as e:
            raise Exception(f"Erro inesperado ao criar o objeto de dados: {e}")
    else:
        raise ValueError(
            "O cabeçalho do CSV não corresponde ao padrão português esperado.\n"
            f"Esperado: {';'.join(PORTUGUESE_HEADER_EXPECTED_LIST)}\n"
            f"Recebido: {csv_header_line}"
        )

# --- Programa para Ler CSV e Gravar no Arquivo .db (do código anterior, com ajustes para a nova função) ---
import os

DB_HEADER_SIZE = 4
RECORD_METADATA_SIZE = 4 + 1 + 4

def process_csv_to_db(csv_filepath: str, db_filepath: str):
    current_id = 0

    if os.path.exists(db_filepath):
        try:
            with open(db_filepath, 'r+b') as f:
                if os.fstat(f.fileno()).st_size >= DB_HEADER_SIZE:
                    f.seek(0)
                    next_id_bytes = f.read(DB_HEADER_SIZE)
                    current_id = struct.unpack('<I', next_id_bytes)[0]
                    print(f"Arquivo DB existente. Próxima ID disponível lida: {current_id}")
                else:
                    print("Arquivo DB existente mas corrompido ou vazio. Reinicializando ID para 0.")
                    current_id = 0
                    f.seek(0)
                    f.write(struct.pack('<I', current_id))
        except Exception as e:
            print(f"Erro ao ler cabeçalho do DB, reinicializando ID para 0: {e}")
            current_id = 0
            with open(db_filepath, 'wb') as f:
                f.write(struct.pack('<I', current_id))
    else:
        print("Arquivo DB não encontrado. Criando novo arquivo e inicializando ID para 0.")
        with open(db_filepath, 'wb') as f:
            f.write(struct.pack('<I', current_id))

    try:
        with open(csv_filepath, 'r', encoding='utf-8') as csv_f, \
             open(db_filepath, 'r+b') as db_f:

            csv_header_line = csv_f.readline().strip()
            print(f"Cabeçalho CSV lido: '{csv_header_line}'")

            try:
                provided_header_list = [h.strip() for h in csv_header_line.split(';')]
                if provided_header_list != PORTUGUESE_HEADER_EXPECTED_LIST:
                     raise ValueError(
                        "O cabeçalho do CSV não corresponde ao padrão português esperado.\n"
                        f"Esperado: {';'.join(PORTUGUESE_HEADER_EXPECTED_LIST)}\n"
                        f"Recebido: {csv_header_line}"
                    )
                print("Cabeçalho CSV validado com sucesso.")

            except ValueError as e:
                print(f"Erro de validação do cabeçalho: {e}")
                return

            for line_num, csv_data_line in enumerate(csv_f, start=2):
                csv_data_line = csv_data_line.strip()
                if not csv_data_line:
                    continue

                is_valid_record = True

                try:
                    data_obj = DataObject.from_csv_line(csv_data_line, ENGLISH_HEADER_FOR_DATAOBJECT)
                    
                    current_id += 1
                    data_obj.id = current_id

                    # --- NOVA LÓGICA DE SERIALIZAÇÃO DE ATRIBUTOS ESPECÍFICOS ---
                    # Cria uma cópia rasa do objeto para modificação antes da serialização.
                    # Isso evita alterar o objeto original `data_obj` se ele for usado posteriormente.
                    data_obj_to_pickle = copy.copy(data_obj) 

                    # Itera sobre os campos que precisam de transformação para string
                    for field_name in DataObject._LIST_CONVERTIBLE_STRING_FIELDS:
                        current_value = getattr(data_obj_to_pickle, field_name)
                        serialized_value = DataObject._convert_list_to_string_for_serialization(current_value)
                        setattr(data_obj_to_pickle, field_name, serialized_value)

                    # Agora, serializa a cópia modificada
                    pickled_data = pickle.dumps(data_obj_to_pickle)
                    # --- FIM DA NOVA LÓGICA ---

                    record_size = len(pickled_data)

                    record_bytes_to_write = struct.pack('<I', data_obj.id) + \
                                            struct.pack('!?', is_valid_record) + \
                                            struct.pack('<I', record_size) + \
                                            pickled_data
                    
                    db_f.seek(0, os.SEEK_END)
                    db_f.write(record_bytes_to_write)
                    
                    db_f.seek(0)
                    db_f.write(struct.pack('<I', current_id))

                    print(f"Registro ID {data_obj.id} (linha {line_num}) gravado. Tamanho: {record_size} bytes.")

                except (ValueError, Exception) as e:
                    is_valid_record = False
                    print(f"Erro ao processar linha {line_num}: '{csv_data_line}' - {e}. Registro ignorado.")
                    pass

        print(f"\nProcessamento concluído. Última ID gerada: {current_id}")

    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado. Verifique os caminhos: CSV '{csv_filepath}', DB '{db_filepath}'")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# --- Exemplo de Uso com novos dados de teste ---
if __name__ == "__main__":
    CSV_FILE = "dados_acidentes.csv"
    DB_FILE = "acidentes.db"

    # Criar um arquivo CSV de teste com exemplos para os atributos específicos
    # - lighting_condition: com '/'
    # - crash_type: com ','
    # - most_severe_injury: com '/'
    test_csv_content = f"""{PORTUGUESE_HEADER_EXPECTED_STR}
07/29/2023 01:00:00 PM;TRAFFIC SIGNAL;CLEAR;DAYLIGHT/TWILIGHT;TURNING;NOT DIVIDED;STRAIGHT AND LEVEL;UNKNOWN;UNKNOWN;NO INJURY / DRIVE AWAY;Y;$501 - $1,500;UNABLE TO DETERMINE;2;NO INDICATION OF INJURY;0.0;0.0;0.0;0.0;0.0;3.0;13;7;7
07/30/2023 02:30:00 AM;NO CONTROLS;RAIN;DARKNESS;REAR END, ANGLE;DIVIDED - W/ MEDIAN;STRAIGHT AND LEVEL;WET;NO DEFECTS;INJURY AND / OR TOW;N;$1,501 - $2,500;FOLLOWING TOO CLOSELY;2;NONINCAPACITATING INJURY;1.0;0.0;0.0;1.0;0.0;1.0;2;1;7
08/01/2023 10:00:00 PM;STOP SIGN;CLEAR;DAYLIGHT/DARKNESS, LIGHTED ROAD;FIXED OBJECT;NOT DIVIDED;CURVE ON GRADE;DRY;NO DEFECTS;PROPERTY DAMAGE;N;$501 - $1,500;FAILURE TO REDUCE SPEED;1;FATAL/INCAPACITATING;0.0;0.0;0.0;0.0;0.0;1.0;22;3;8
08/02/2023 03:00:00 PM;YIELD SIGN;SNOW;DAYLIGHT;OVERTURNED;UNKNOWN;STRAIGHT AND LEVEL;SNOW OR ICE;UNKNOWN;INJURY AND / OR TOW;N;$2,501 - $9,999;IMPROPER TURNING;1;INCAPACITATING INJURY;1.0;0.0;1.0;0.0;0.0;0.0;15;4;8
08/03/2023 04:00:00 AM;TRAFFIC SIGNAL;CLEAR;DAYLIGHT;SIDESWIPE;NOT DIVIDED;STRAIGHT AND LEVEL;DRY;NO DEFECTS;NO INJURY / DRIVE AWAY;Y;$501 - $1,500;DISREGARDING TRAFFIC SIGNALS;2;NO INDICATION OF INJURY;0.0;0.0;0.0;0.0;0.0;2.0;4;5;8
"""

    print("--- Executando Teste: CSV com Campos Específicos com Delimitadores para Serialização ---")
    with open(CSV_FILE, 'w', encoding='utf-8') as f:
        f.write(test_csv_content)
    
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Arquivo '{DB_FILE}' existente removido.")

    process_csv_to_db(CSV_FILE, DB_FILE)
    print("\n")

    # --- Função auxiliar para ler e verificar o conteúdo do DB ---
    def read_db_records(db_filepath: str) -> List[DataObject]:
        records = []
        if not os.path.exists(db_filepath):
            return records
        
        try:
            with open(db_filepath, 'rb') as f:
                if os.fstat(f.fileno()).st_size < DB_HEADER_SIZE:
                    print("Arquivo DB muito pequeno para ter um cabeçalho.")
                    return records
                f.seek(0)
                next_id_in_db_header = struct.unpack('<I', f.read(DB_HEADER_SIZE))[0]
                print(f"Próxima ID disponível no cabeçalho do DB: {next_id_in_db_header}")

                while True:
                    metadata_bytes = f.read(RECORD_METADATA_SIZE)
                    if not metadata_bytes:
                        break
                    if len(metadata_bytes) < RECORD_METADATA_SIZE:
                        print(f"Dados insuficientes para metadados de registro. Restante: {len(metadata_bytes)} bytes.")
                        break

                    record_id, is_valid_byte, record_size = struct.unpack('<IBI', metadata_bytes)
                    is_valid = bool(is_valid_byte)

                    pickled_data = f.read(record_size)
                    if len(pickled_data) < record_size:
                        print(f"Dados de registro incompletos para ID {record_id}. Esperado {record_size}, lido {len(pickled_data)}.")
                        break

                    try:
                        data_obj = pickle.loads(pickled_data)
                        records.append(data_obj)
                        print(f"Lido registro ID {record_id}, Válido: {is_valid}, Tamanho: {record_size} bytes.")
                    except pickle.UnpicklingError as pe:
                        print(f"Erro ao des-serializar registro ID {record_id}: {pe}")
                    except Exception as ex:
                        print(f"Erro desconhecido ao processar registro ID {record_id}: {ex}")

        except Exception as e:
            print(f"Erro ao ler arquivo DB: {e}")
        return records

    print("\n--- Conteúdo do arquivo DB após o teste (verifique a formatação dos campos) ---")
    final_records = read_db_records(DB_FILE)
    for rec in final_records:
        print(rec)
        # Verificando os campos específicos
        if rec.id == 1:
            print(f"  Lighting Condition para ID 1 (depois de serializar/des-serializar): {rec.lighting_condition} (tipo: {type(rec.lighting_condition)})")
        if rec.id == 2:
            print(f"  Crash Type para ID 2 (depois de serializar/des-serializar): {rec.crash_type} (tipo: {type(rec.crash_type)})")
        if rec.id == 3:
            print(f"  Most Severe Injury para ID 3 (depois de serializar/des-serializar): {rec.most_severe_injury} (tipo: {type(rec.most_severe_injury)})")
        if rec.id == 4:
            print(f"  Lighting Condition para ID 4 (depois de serializar/des-serializar): {rec.lighting_condition} (tipo: {type(rec.lighting_condition)})")
        if rec.id == 5:
            print(f"  Lighting Condition para ID 5 (depois de serializar/des-serializar): {rec.lighting_condition} (tipo: {type(rec.lighting_condition)})")


    print(f"Total de registros lidos do DB: {len(final_records)}")