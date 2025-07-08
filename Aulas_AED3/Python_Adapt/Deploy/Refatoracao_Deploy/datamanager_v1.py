import struct
import json
import hashlib
import os
import fcntl
from typing import Any, Dict # Para sistemas Unix-like
import filelock

from add_registry import DataObject # Importar a biblioteca filelock

# Assumindo que DataObject, Functions e outras dependências de app_v6.py estão disponíveis.
# Importar DataObject e Functions de app_v6.py
# from app_v6 import DataObject, Functions # Esta linha é ilustrativa, o contexto já tem acesso.

# futuramente será a classe DataManager


DB_FILE_PATH = "data_objects.db"
DB_HEADER_SIZE = 4 # 4 bytes para o ID no cabeçalho

def _initialize_db_header(db_file_path: str):
    """
    Inicializa o arquivo DB com um cabeçalho, se ele não existir ou estiver vazio.
    O cabeçalho armazenará o último ID usado (inicialmente 0).
    """
    if not os.path.exists(db_file_path) or os.path.getsize(db_file_path) < DB_HEADER_SIZE:
        try:
            with filelock.FileLock(db_file_path + ".lock"):
                with open(db_file_path, "r+b" if os.path.exists(db_file_path) else "w+b") as f:
                    f.seek(0)
                    # Certifica-se de que o arquivo tem pelo menos o tamanho do cabeçalho
                    if os.path.getsize(db_file_path) < DB_HEADER_SIZE:
                        f.write(struct.pack('<I', 0)) # Escreve ID inicial 0
                        # Se o arquivo foi recém-criado, preenche o resto com zeros ou está vazio.
                        # Caso contrário, apenas atualiza os primeiros 4 bytes.
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
                    # Se por algum motivo o cabeçalho estiver incompleto, reinicializa
                    print("Cabeçalho do DB incompleto. Re-inicializando.")
                    _initialize_db_header(db_file_path)
                    last_id = 0 # Depois da reinicialização, o ID será 0
    except Exception as e:
        print(f"Erro ao ler último ID do cabeçalho do DB: {e}")
        # Em caso de erro, podemos retornar 0 para começar do 1 ou tratar a falha
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

def write_data_object_to_db(data_object: DataObject, db_file_path: str):
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
    if hasattr(data_object, 'id'):
        data_object.id = record_id
    
    # 2. Converter DataObject para dicionário serializável
    data_map = data_object.to_map()
    # Se DataObject não tiver atributo 'id', adicione-o ao mapa aqui
    # para garantir que o ID esteja nos dados serializados.
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
                # O modo 'ab' garante que a escrita começará no final do arquivo,
                # após o cabeçalho principal e quaisquer registros existentes.
                f.write(full_record_data)
            # 6. Atualizar o ID no cabeçalho principal após a escrita bem-sucedida do registro
            _update_last_id_in_header(db_file_path, record_id)
        print(f"Registro ID {record_id} salvo com sucesso em {db_file_path}")
    except Exception as e:
        print(f"Erro ao salvar registro ID {record_id} em {db_file_path}: {e}")
        # Considerar rollback do ID no cabeçalho em caso de falha de escrita aqui,
        # mas isso adiciona complexidade significativa ao tratamento de erros.

def read_db_records(db_file_path: str) -> list[Dict[str, Any]]:
    """
    Lê e decodifica todos os registros do arquivo DB,
    pulando o cabeçalho inicial.
    Retorna uma lista de dicionários representando os DataObjects.
    """
    records = []
    if not os.path.exists(db_file_path) or os.path.getsize(db_file_path) < DB_HEADER_SIZE:
        print(f"Arquivo DB não encontrado ou incompleto: {db_file_path}")
        return records

    try:
        with filelock.FileLock(db_file_path + ".lock"):
            with open(db_file_path, "rb") as f:
                f.seek(DB_HEADER_SIZE) # Pula o cabeçalho principal
                file_size = os.path.getsize(db_file_path)

                while f.tell() < file_size:
                    try:
                        # Lê o cabeçalho interno de cada registro
                        record_id = struct.unpack('<I', f.read(4))[0]
                        boolean_validator = struct.unpack('<B', f.read(1))[0]
                        total_data_size_with_checksum = struct.unpack('<I', f.read(4))[0]

                        if boolean_validator == 0:
                            print(f"Registro ID {record_id} marcado como inválido/excluído. Pulando.")
                            f.read(total_data_size_with_checksum)
                            continue

                        sha256_checksum_read = f.read(32)
                        byte_vector_len = total_data_size_with_checksum - 32
                        byte_vector_read = f.read(byte_vector_len)

                        calculated_checksum = hashlib.sha256(byte_vector_read).digest()
                        if calculated_checksum != sha256_checksum_read:
                            print(f"Erro de integridade no registro ID {record_id}: Checksum inválido. Pulando.")
                            continue

                        json_data_str = byte_vector_read.decode('utf-8')
                        data_map = json.loads(json_data_str)
                        # O ID já deve estar no data_map se o write_data_object_to_db o adicionou
                        records.append(data_map)

                    except struct.error as se:
                        print(f"Erro de estrutura ao ler registro no offset {f.tell() - 9} (provável corrupção): {se}. Interrompendo leitura.")
                        break
                    except json.JSONDecodeError as je:
                        print(f"Erro de decodificação JSON no registro no offset {f.tell() - byte_vector_len}: {je}. Dados corrompidos. Interrompendo leitura.")
                        break
                    except Exception as ex:
                        print(f"Erro desconhecido ao processar registro no offset {f.tell()}: {ex}. Interrompendo leitura.")
                        break

    except Exception as e:
        print(f"Erro ao abrir ou ler arquivo DB: {e}")
    return records
