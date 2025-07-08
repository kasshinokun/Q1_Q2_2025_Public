import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Union, Any, Callable
import traceback
import csv
import io
import re
from pathlib import Path
import filelock # Para gerenciamento de concorrência
import struct
import json
import hashlib
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, # Pode ser alterado para logging.DEBUG para mais detalhes
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Log para o console
    ]
)
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---
class DataValidationError(ValueError):
    """Exceção personalizada para erros de validação de dados."""
    pass

class DatabaseError(Exception):
    """Exceção personalizada para erros relacionados ao banco de dados."""
    pass

# --- Definição dos Campos de Dados ---
# Define todos os campos para o DataObject, seus tipos esperados e regras de validação básicas.
FIELDS = [
    # (nome_do_campo, tipo_esperado, valor_padrao, eh_obrigatorio)
    # 'crash_date' agora espera o formato "MM/DD/YYYY HH:MM:SS AM/PM" do CSV e contém a data e hora completas.
    ('crash_date', str, '01/01/2020 00:00:00 AM', True),
    ('crash_hour', int, 0, True),
    ('crash_day_of_week', int, 0, True),
    ('crash_month', int, 0, True),
    ('traffic_control_device', str, 'UNKNOWN', False),
    ('weather_condition', str, 'UNKNOWN', False),
    ('lighting_condition', str, 'UNKNOWN', False),
    ('first_crash_type', str, 'UNKNOWN', False),
    ('trafficway_type', str, 'UNKNOWN', False),
    ('alignment', str, 'UNKNOWN', False),
    ('roadway_surface_cond', str, 'UNKNOWN', False),
    ('road_defect', str, 'UNKNOWN', False),
    ('crash_type', str, 'UNKNOWN', False),
    ('intersection_related_i', str, 'UNKNOWN', False), # 'Y' ou 'N'
    ('damage', str, 'UNKNOWN', False),
    ('prim_contributory_cause', str, 'UNKNOWN', False),
    ('num_units', int, 0, False),
    ('most_severe_injury', str, 'NONE', False),
    ('injuries_total', int, 0, False),
    ('injuries_fatal', int, 0, False),
    ('injuries_incapacitating', int, 0, False),
    ('injuries_non_incapacitating', int, 0, False),
    ('injuries_reported_not_evident', int, 0, False),
    ('injuries_no_indication', int, 0, False),
]

# Mapeamento de nomes de campos para português brasileiro para __repr__
FIELD_NAMES_PT = {
    'crash_date': 'Data do Acidente',
    'crash_hour': 'Hora do Acidente',
    'crash_day_of_week': 'Dia da Semana do Acidente',
    'crash_month': 'Mês do Acidente',
    'traffic_control_device': 'Dispositivo de Controle de Tráfego',
    'weather_condition': 'Condição Climática',
    'lighting_condition': 'Condição de Iluminação',
    'first_crash_type': 'Primeiro Tipo de Colisão',
    'trafficway_type': 'Tipo de Via',
    'alignment': 'Alinhamento',
    'roadway_surface_cond': 'Condição da Superfície da Via',
    'road_defect': 'Defeito na Via',
    'crash_type': 'Tipo de Acidente',
    'intersection_related_i': 'Relacionado a Interseção',
    'damage': 'Dano',
    'prim_contributory_cause': 'Causa Contributiva Primária',
    'num_units': 'Número de Unidades',
    'most_severe_injury': 'Lesão Mais Grave',
    'injuries_total': 'Lesões Totais',
    'injuries_fatal': 'Lesões Fatais',
    'injuries_incapacitating': 'Lesões Incapacitantes',
    'injuries_non_incapacitating': 'Lesões Não Incapacitantes',
    'injuries_reported_not_evident': 'Lesões Reportadas Não Evidentes',
    'injuries_no_indication': 'Sem Indicação de Lesões',
    'id': 'ID do Registro' # Adicionado para o campo 'id' que pode ser inserido
}


class DataObject:
    """
    Representa um registro de acidente de trânsito, otimizado para validação e serialização,
    adaptado para ser usado em app_v6.py e compatível com datamanager_v1.py.
    Inclui métodos __str__ e __repr__ aprimorados.
    """
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """
        Inicializa uma nova instância de DataObject.
        Pode ser inicializada a partir de um dicionário.

        Args:
            data (Optional[Dict[str, Any]]): Um dicionário contendo os dados do acidente.
        """
        self._data = {}
        self._initialize_defaults()
        if data:
            self._initialize_from_dict(data)

    def _initialize_defaults(self):
        """Define valores padrão para todos os campos."""
        for field_name, field_type, default_value, _ in FIELDS:
            self._data[field_name] = default_value

    def _initialize_from_dict(self, data_dict: Dict[str, Any]):
        """Popula os campos a partir de um dicionário, realizando conversão básica."""
        for field_name, field_type, _, _ in FIELDS:
            if field_name in data_dict:
                value = data_dict[field_name]
                try:
                    if field_type == int:
                        # Tenta converter para int, lidando com floats em string (ex: "1.0")
                        self._data[field_name] = int(float(value)) if isinstance(value, str) and '.' in value else int(value)
                    elif field_type == float:
                        self._data[field_name] = float(value)
                    else:
                        self._data[field_name] = str(value).strip()
                except (ValueError, TypeError):
                    logger.warning(f"Erro de conversão de tipo para o campo '{field_name}'. Valor: '{value}'. Usando valor padrão.")
                    # Pega o valor padrão da definição FIELDS
                    default_value_for_field = next((f[2] for f in FIELDS if f[0] == field_name), None)
                    self._data[field_name] = default_value_for_field


    @classmethod
    def from_csv_row(cls, row_data: List[str]) -> "DataObject":
        """
        Cria uma instância de DataObject a partir de uma lista de strings (linha CSV).
        Adapta o método de parsing robusto de app_v6.py.

        Args:
            row_data (List[str]): Uma lista de strings representando uma linha CSV.

        Returns:
            DataObject: Uma nova instância de DataObject.

        Raises:
            DataValidationError: Se o número de colunas não corresponder ao esperado.
        """
        # A ordem das colunas CSV deve corresponder à ordem definida em FIELDS
        if len(row_data) != len(FIELDS):
            raise DataValidationError(
                f"Número de colunas ({len(row_data)}) não corresponde ao esperado ({len(FIELDS)})."
            )

        data_dict = {}
        for i, (field_name, field_type, default_value, _) in enumerate(FIELDS):
            raw_value = row_data[i].strip()

            # Se o valor bruto for vazio, use o valor padrão
            if not raw_value:
                data_dict[field_name] = default_value
                continue

            try:
                if field_type == int:
                    # Tenta converter para int, lidando com floats em string (ex: "1.0")
                    data_dict[field_name] = int(float(raw_value))
                elif field_type == float:
                    data_dict[field_name] = float(raw_value)
                elif field_type == str:
                    data_dict[field_name] = raw_value
                else:
                    data_dict[field_name] = raw_value # Fallback
            except ValueError:
                logger.warning(
                    f"Não foi possível converter '{raw_value}' para o tipo esperado '{field_type.__name__}' "
                    f"para o campo '{field_name}'. Usando valor padrão."
                )
                data_dict[field_name] = default_value # Usa valor padrão em erro de conversão

        obj = cls(data_dict)
        return obj

    def to_map(self) -> Dict[str, Any]:
        """
        Converte a instância de DataObject para um dicionário (mapa),
        compatível com a lógica de datamanager_v1.py.
        """
        return self._data.copy()

    # Propriedades baseadas em getters/setters para melhor encapsulamento (similar a app_v6.py)
    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        # Permite acesso a atributos que não são dados, como métodos da classe
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any):
        # Permite definir _data diretamente durante a inicialização
        if name == "_data":
            super().__setattr__(name, value)
            return

        # Verifica se o atributo é um campo definido
        for field_name, field_type, _, _ in FIELDS:
            if field_name == name:
                # Validação básica de tipo ao definir
                try:
                    if field_name == 'crash_date': # Special handling for crash_date now containing full datetime
                        # Just store as string, datetime object will be derived by crash_datetime property
                        self._data[field_name] = str(value)
                    elif field_type == int:
                        self._data[field_name] = int(value)
                    elif field_type == float:
                        self._data[field_name] = float(value)
                    elif field_type == str:
                        self._data[field_name] = str(value)
                    else:
                        self._data[field_name] = value
                except (ValueError, TypeError):
                    raise DataValidationError(f"Valor '{value}' inválido para o campo '{field_name}'. Esperado: {field_type.__name__}.")
                return

        # Se não for um campo definido, comporta-se como setattr normal
        super().__setattr__(name, value)

    @property
    def crash_datetime(self) -> Optional[datetime]:
        """Retorna a data e hora do acidente como um objeto datetime.
        Espera que 'crash_date' seja uma string no formato "MM/DD/YYYY HH:MM:SS AM/PM" ou "MM/DD/YYYY HH:MM AM/PM".
        """
        try:
            # Tenta parsear com segundos
            return datetime.strptime(self.crash_date, '%m/%d/%Y %I:%M:%S %p')
        except ValueError:
            try:
                # Se falhar, tenta parsear sem segundos (HH:MM AM/PM)
                return datetime.strptime(self.crash_date, '%m/%d/%Y %I:%M %p')
            except (ValueError, TypeError):
                logger.warning(f"Não foi possível parsear 'crash_date' ('{self.crash_date}') para datetime. Formato inválido.")
                return None

    @crash_datetime.setter
    def crash_datetime(self, dt: datetime):
        """Define a data e hora do acidente a partir de um objeto datetime.
        Armazena no atributo 'crash_date' no formato "MM/DD/YYYY HH:MM:SS AM/PM".
        """
        self.crash_date = dt.strftime('%m/%d/%Y %I:%M:%S %p') # Armazena a data e hora combinadas em 'crash_date'

    def validate(self) -> bool:
        """
        Realiza uma validação abrangente dos dados do DataObject.
        Combina e aprimora as validações de dataobject_revb.py.

        Returns:
            bool: True se a validação for bem-sucedida, False caso contrário.
        """
        try:
            # 1. Validação de campos obrigatórios e tipos
            for field_name, field_type, _, is_required in FIELDS:
                value = self._data.get(field_name)

                if is_required and (value is None or (isinstance(value, str) and not value.strip() and field_name != 'intersection_related_i')):
                    raise DataValidationError(f"Campo obrigatório '{field_name}' está vazio.")

                if value is not None and not (isinstance(value, str) and not value.strip()): # Não verifica tipo para string vazia
                    if field_type == int and not isinstance(value, int):
                         raise DataValidationError(f"Campo '{field_name}' deve ser um inteiro. Valor: {value}.")
                    if field_type == float and not isinstance(value, float):
                         raise DataValidationError(f"Campo '{field_name}' deve ser um float. Valor: {value}.")
                    if field_type == str and not isinstance(value, str):
                         raise DataValidationError(f"Campo '{field_name}' deve ser uma string. Valor: {value}.")

            # 2. Validação específica de data/hora
            # A data e hora são agora derivadas da string crash_date.
            c_datetime = self.crash_datetime
            if c_datetime is None:
                raise DataValidationError(f"Formato de data/hora inválido para 'crash_date' ('{self.crash_date}'). Esperado MM/DD/YYYY HH:MM:SS AM/PM ou MM/DD/YYYY HH:MM AM/PM.")
            
            # Atualiza crash_hour, crash_day_of_week, crash_month a partir de crash_datetime
            # para garantir consistência e validação baseada em datetime.
            self._data['crash_hour'] = c_datetime.hour
            self._data['crash_day_of_week'] = c_datetime.isoweekday() # Monday is 1 and Sunday is 7
            self._data['crash_month'] = c_datetime.month

            # 3. Validações de intervalo e lógica (aprimorado de dataobject_revb.py)
            if not (0 <= self.crash_hour <= 23): # Já atualizado pelo crash_datetime
                raise DataValidationError("Hora do acidente fora do intervalo válido (0-23).")
            if not (1 <= self.crash_day_of_week <= 7): # Já atualizado pelo crash_datetime
                raise DataValidationError("Dia da semana do acidente fora do intervalo válido (1-7).")
            if not (1 <= self.crash_month <= 12): # Já atualizado pelo crash_datetime
                raise DataValidationError("Mês do acidente fora do intervalo válido (1-12).")

            # Validação para 'intersection_related_i'
            if self.intersection_related_i.upper() not in ['Y', 'N', 'UNKNOWN', '']:
                raise DataValidationError(f"Valor inválido para 'intersection_related_i': '{self.intersection_related_i}'. Esperado 'Y', 'N', 'UNKNOWN' ou vazio.")

            # Validação de somas de lesões
            reported_injuries = (
                self.injuries_fatal + self.injuries_incapacitating +
                self.injuries_non_incapacitating + self.injuries_reported_not_evident +
                self.injuries_no_indication
            )
            if self.injuries_total < reported_injuries and self.injuries_total > 0:
                logger.warning(
                    f"Total de lesões ({self.injuries_total}) é menor que a soma das lesões específicas ({reported_injuries})."
                    f" ID do registro (data+hora): {self.crash_date}"
                )

            return True
        except DataValidationError as e:
            logger.warning(f"Falha na validação do DataObject: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado durante a validação do DataObject: {traceback.format_exc()}")
            return False

    def __str__(self):
        """
        Retorna uma representação de string concisa e amigável ao usuário.
        Adaptado do app_v6.py para português.
        """
        return (f"Acidente em {self.crash_date} - Tipo: {self.crash_type} - "
                f"Lesões Totais: {self.injuries_total}")

    def __repr__(self):
        """
        Retorna uma representação de string detalhada para depuração,
        exibindo todos os campos em português brasileiro.
        """
        details = []
        # Itera sobre os campos definidos em FIELDS para garantir a ordem
        for field_name, _, _, _ in FIELDS:
            pt_name = FIELD_NAMES_PT.get(field_name, field_name)
            value = getattr(self, field_name)
            details.append(f"{pt_name}='{value}'")
        
        # Adiciona o 'id' se ele estiver presente no _data (pode ser adicionado pela função de escrita no DB)
        if 'id' in self._data:
            pt_name = FIELD_NAMES_PT.get('id', 'ID') # Pega o nome em português ou usa 'ID'
            details.append(f"{pt_name}='{self._data['id']}'")

        return f"DataObject({', '.join(details)})"


# --- Funções de Banco de Dados de datamanager_v1.py (Copiadas e adaptadas) ---

DB_FILE_PATH = "data_objects.db" # Caminho padrão do arquivo DB
DB_HEADER_SIZE = 4 # 4 bytes para o ID no cabeçalho

def _initialize_db_header(db_file_path: str):
    """
    Inicializa o arquivo DB com um cabeçalho, se ele não existir ou estiver vazio.
    O cabeçalho armazenará o último ID usado (inicialmente 0).
    """
    if not os.path.exists(db_file_path) or os.path.getsize(db_file_path) < DB_HEADER_SIZE:
        try:
            with filelock.FileLock(db_file_path + ".lock"):
                # Garante que o diretório exista
                Path(db_file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(db_file_path, "r+b" if os.path.exists(db_file_path) else "w+b") as f:
                    f.seek(0)
                    if os.path.getsize(db_file_path) < DB_HEADER_SIZE:
                        f.write(struct.pack('<I', 0)) # Escreve ID inicial 0
                    print(f"Arquivo DB '{db_file_path}' inicializado com cabeçalho ID 0.")
        except Exception as e:
            print(f"Erro ao inicializar o cabeçalho do arquivo DB: {e}")

def _read_last_id_from_header(db_file_path: str) -> int:
    """
    Lê o último ID do cabeçalho do arquivo DB.
    Assume que o cabeçalho já foi inicializado.
    """
    _initialize_db_header(db_file_path) # Garante que o cabeçalho exista

    last_id = 0
    try:
        with filelock.FileLock(db_file_path + ".lock"):
            with open(db_file_path, "rb") as f:
                f.seek(0) # Vai para o início do arquivo
                header_bytes = f.read(DB_HEADER_SIZE)
                if len(header_bytes) == DB_HEADER_SIZE:
                    last_id = struct.unpack('<I', header_bytes)[0]
                else:
                    print("Cabeçalho do DB incompleto. Re-inicializando.")
                    _initialize_db_header(db_file_path)
                    last_id = 0
    except Exception as e:
        print(f"Erro ao ler último ID do cabeçalho do DB: {e}")
        last_id = 0
    return last_id

def _update_last_id_in_header(db_file_path: str, new_id: int):
    """
    Atualiza o último ID no cabeçalho do arquivo DB.
    """
    try:
        with filelock.FileLock(db_file_path + ".lock"):
            with open(db_file_path, "r+b") as f: # Abrir para leitura e escrita binária
                f.seek(0) # Vai para o início para sobrescrever o cabeçalho
                f.write(struct.pack('<I', new_id))
            print(f"Cabeçalho do DB atualizado com ID: {new_id}")
    except Exception as e:
        print(f"Erro ao atualizar ID no cabeçalho do DB: {e}")

def write_data_object_to_db(data_object: DataObject, db_file_path: str = DB_FILE_PATH):
    """
    Serializa um DataObject e o escreve no arquivo DB com o formato especificado.
    Utiliza o ID do cabeçalho otimizado.
    """
    # Garante que o cabeçalho esteja inicializado
    _initialize_db_header(db_file_path)

    # 1. Obter o próximo ID
    current_last_id = _read_last_id_from_header(db_file_path)
    record_id = current_last_id + 1
    print(f"Gerando registro com ID: {record_id}")

    # Atribuir o ID ao DataObject (se ele tiver um atributo 'id')
    # O `datamanager_v1.py` espera que 'id' possa ser definido no DataObject,
    # então vamos adicionar um setter para ele na nossa classe DataObject,
    # embora não seja um FIELD padrão.
    if hasattr(data_object, 'id'):
        data_object.id = record_id
    
    # 2. Converter DataObject para dicionário serializável
    # Usamos to_map() para compatibilidade com a expectativa de datamanager_v1.py
    data_map = data_object.to_map()
    # Adiciona o ID ao mapa se não estiver presente (garantindo que o ID esteja nos dados serializados)
    if 'id' not in data_map:
         data_map['id'] = record_id

    json_data = json.dumps(data_map, ensure_ascii=False)
    byte_vector = json_data.encode('utf-8')

    # 3. Calcular SHA-256 checksum
    sha256_checksum = hashlib.sha256(byte_vector).digest()

    # 4. Construir o cabeçalho do registro e o registro completo
    boolean_validator = 1 # Para registros válidos
    total_data_size_with_checksum = len(byte_vector) + len(sha256_checksum)

    # Formato do cabeçalho do registro (ID, validador, tamanho total)
    record_inner_header = struct.pack('<I B I', record_id, boolean_validator, total_data_size_with_checksum)

    # Registro completo: cabeçalho do registro + checksum + vetor de bytes
    full_record_data = record_inner_header + sha256_checksum + byte_vector

    # 5. Escrever no arquivo .db (após o cabeçalho principal)
    try:
        with filelock.FileLock(db_file_path + ".lock"):
            with open(db_file_path, "ab") as f: # Abrir em modo append binário
                f.write(full_record_data)
            # 6. Atualizar o ID no cabeçalho principal após a escrita bem-sucedida do registro
            _update_last_id_in_header(db_file_path, record_id)
        print(f"Registro ID {record_id} salvo com sucesso em {db_file_path}")
    except Exception as e:
        print(f"Erro ao salvar registro ID {record_id} em {db_file_path}: {e}")
        # Em um cenário real, considerar um mecanismo de rollback ou tratamento de falhas mais robusto.


# --- Novo método para ler CSV e escrever no .db ---

def process_csv_to_db(csv_filepath: str, db_filepath: str = DB_FILE_PATH):
    """
    Lê um arquivo CSV, processa cada linha como um DataObject, valida-o
    e o escreve em um arquivo .db usando a lógica de datamanager_v1.py.

    Args:
        csv_filepath (str): Caminho para o arquivo CSV de entrada.
        db_filepath (str): Caminho para o arquivo de banco de dados .db de saída.
    """
    processed_count = 0
    invalid_count = 0
    try:
        with open(csv_filepath, 'r', encoding='utf-8', newline='') as f:
            csv_reader = csv.reader(f, delimiter=';') # Assumindo ';' como delimitador
            header = next(csv_reader) # Pula o cabeçalho

            # Opcional: Validar se o cabeçalho do CSV corresponde aos FIELDS esperados
            expected_header = [field[0] for field in FIELDS]
            if header != expected_header:
                logger.warning(
                    f"O cabeçalho do CSV de entrada ({header}) não corresponde "
                    f"aos campos esperados ({expected_header}). Isso pode causar erros de parsing."
                )

            for i, row in enumerate(csv_reader):
                logger.info(f"Processando linha {i+1}: {row}")
                try:
                    data_obj = DataObject.from_csv_row(row)
                    if data_obj.validate():
                        write_data_object_to_db(data_obj, db_filepath)
                        processed_count += 1
                    else:
                        invalid_count += 1
                        logger.warning(f"Linha {i+1} inválida, não adicionada ao DB: {row}")
                except DataValidationError as e:
                    invalid_count += 1
                    logger.error(f"Erro de validação na linha {i+1}: {e} - Dados: {row}")
                except Exception as e:
                    invalid_count += 1
                    logger.error(f"Erro inesperado ao processar linha {i+1}: {traceback.format_exc()} - Dados: {row}")
    except FileNotFoundError:
        logger.error(f"Arquivo CSV não encontrado: {csv_filepath}")
    except Exception as e:
        logger.error(f"Erro ao ler arquivo CSV: {traceback.format_exc()}")

    logger.info(f"Processamento concluído. Registros válidos escritos no DB: {processed_count}. Registros inválidos/erros: {invalid_count}.")

# --- Exemplo de Uso ---
def run_example():
    """
    Exemplo de uso da classe DataObject adaptada e da função process_csv_to_db.
    """
    # Criar um arquivo CSV de exemplo (simulando dados de entrada)
    # Note que a coluna crash_date agora inclui a hora.
    example_csv_content = """crash_date;crash_hour;crash_day_of_week;crash_month;traffic_control_device;weather_condition;lighting_condition;first_crash_type;trafficway_type;alignment;roadway_surface_cond;road_defect;crash_type;intersection_related_i;damage;prim_contributory_cause;num_units;most_severe_injury;injuries_total;injuries_fatal;injuries_incapacitating;injuries_non_incapacitating;injuries_reported_not_evident;injuries_no_indication
01/01/2024 10:00:00 AM;10;2;1;SINAL DE TRAFEGO;CEU LIMPO;DIA CLARO;COLISAO FRONTAL;VIA EXPRESSA;RETO;SECO;NENHUM;NAO COLISAO;Y;MINIMO;NAO INFORMADO;2;NENHUMA;0;0;0;0;0;0
01/02/2024 03:30:00 PM;15;3;1;SINAL DE PARE;CHUVA;CREPUSCULO;COLISAO TRASEIRA;RUA RESIDENCIAL;CURVA;MOLHADO;BURACO;COLISAO;N;MAIOR;EXCESSO DE VELOCIDADE;2;LESÃO INCAPACITANTE;1;0;1;0;0;0
01/03/2024 08:00:00 PM;20;4;1;NENHUM;NEVE;NOITE;SAIDA DE PISTA;ESTRADA;DECLIVE;NEVE;NENHUM;NAO COLISAO;N;SUBSTANCIAL;FALHA MECANICA;1;LESÃO FATAL;1;1;0;0;0;0
01/04/2024 09:00:00 AM;99;5;1;NENHUM;NUBLADO;DIA CLARO;COLISAO LATERAL;RUA COMERCIAL;RETO;SECO;NENHUM;COLISAO;Y;MENOR;DISTRAÇÃO;2;NENHUMA;0;0;0;0;0;0
01/05/2024 12:00:00 PM;12;7;1;SEM SINALIZACAO;FOG;NOITE;NAO COLISAO;ALAMEDA;RETO;MOLHADO;SEM DEFEITO;NAO COLISAO;N;NENHUM;NAO INFORMADO;1;NENHUMA;0;0;0;0;0;0
"""
    dummy_csv_path = Path("example_input.csv")
    dummy_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dummy_csv_path, 'w', encoding='utf-8', newline='') as f:
        f.write(example_csv_content.strip())
    logger.info(f"Arquivo CSV de exemplo criado em: {dummy_csv_path}")

    output_db_file = "data/adapted_accidents_v3.db"
    
    # Executa o processo de leitura do CSV e escrita no DB
    process_csv_to_db(str(dummy_csv_path), output_db_file)

    # Limpeza: Remover o arquivo CSV de exemplo
    dummy_csv_path.unlink(missing_ok=True)
    logger.info(f"Arquivo CSV de exemplo '{dummy_csv_path}' removido.")
    
    # Limpeza: Remover o arquivo DB e o lock file para re-execuções limpas
    Path(output_db_file).unlink(missing_ok=True)
    Path(output_db_file + ".lock").unlink(missing_ok=True)
    logger.info(f"Arquivo DB '{output_db_file}' e seu lock file removidos.")

# Chama a função de exemplo para demonstrar o uso
run_example()