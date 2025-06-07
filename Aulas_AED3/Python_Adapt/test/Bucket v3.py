import os
import io
import struct
import csv
import zlib
import mmap
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Callable, Generic, TypeVar, Union
from collections import defaultdict
from abc import ABC, abstractmethod

K = TypeVar('K', bound=Union[int, str])
V = TypeVar('V')

# --- Shared Helper Classes/Interfaces ---
class Entry(Generic[K, V]):
    @staticmethod
    def create_entry(key: K, value: V) -> 'Entry[K, V]':
        return SimpleEntry(key, value)

class SimpleEntry(Entry[K, V]):
    def __init__(self, key: K, value: V):
        self.key = key
        self.value = value

    def __repr__(self):
        return f"Entry{{key={self.key}, value={self.value}}}"

class EHashStats:
    def __repr__(self):
        return "EHashStats{}"

# --- Interfaces ---
class Page(ABC, Generic[K, V]):
    @abstractmethod
    def contains(self, key: K) -> bool:
        pass

    @abstractmethod
    def get(self, key: K) -> Optional[V]:
        pass

    @abstractmethod
    def put(self, key: K, value: V) -> None:
        pass

    @abstractmethod
    def has_space_for(self, key: K, value: V) -> bool:
        pass

    @abstractmethod
    def depth(self) -> int:
        pass

    @abstractmethod
    def get_id(self) -> int:
        pass

    @abstractmethod
    def get_entries(self) -> List[Entry[K, V]]:
        pass

    @abstractmethod
    def increment_local_depth(self) -> None:
        pass

    @abstractmethod
    def clear_entries_for_split(self) -> None:
        pass

class Directory(ABC):
    @abstractmethod
    def get_page_offset(self, hash_code: int) -> int:
        pass

    @abstractmethod
    def get_global_depth(self) -> int:
        pass

    @abstractmethod
    def extend(self) -> None:
        pass

    @abstractmethod
    def put(self, directory_index: int, page_offset: int) -> None:
        pass

    @abstractmethod
    def load(self) -> None:
        pass

    @abstractmethod
    def save(self) -> None:
        pass

    @abstractmethod
    def get_directory_index(self, hash_code: int) -> int:
        pass

class DataStore(ABC, Generic[K, V]):
    @abstractmethod
    def get_page(self, page_offset: int) -> Page[K, V]:
        pass

    @abstractmethod
    def allocate_new_page(self, depth: int) -> Page[K, V]:
        pass

    @abstractmethod
    def write_page(self, page: Page[K, V]) -> None:
        pass

    @abstractmethod
    def get_next_available_offset(self) -> int:
        pass
"""
# --- ExtensibleHashingCSV Implementation ---
class ExtensibleHashingCSV:
    BUCKET_SIZE = 1024
    DATA_FILE_CSV = "indexed_data/test/data_csv.dat"
    REGISTRY_FILE_CSV = "indexed_data/test/registry_csv.dat"
    CSV_INPUT_FILE = "indexed_data/test/random_people_for_csv_hashing.csv"

    def __init__(self):
        self.global_depth = 1
        initial_directory_size = 1 << self.global_depth
        self.directory: List['Bucket'] = [Bucket(self.global_depth) for _ in range(initial_directory_size)]
        self.data_file: Optional[io.BufferedRandom] = None

    class Bucket:
        def __init__(self, local_depth: int):
            self.local_depth = local_depth
            self.entries: Dict[str, int] = {}

        def __repr__(self):
            return f"Bucket@{hex(id(self))}{{ld={self.local_depth}, entries={len(self.entries)}}}"

    def initialize_files(self) -> None:
        self.data_file = open(self.DATA_FILE_CSV, "r+b")

    def close_files(self) -> None:
        if self.data_file:
            self.data_file.close()
        print("Arquivos ExtensibleHashingCSV fechados.")

    def load_registry(self) -> None:
        if not os.path.exists(self.REGISTRY_FILE_CSV) or os.path.getsize(self.REGISTRY_FILE_CSV) == 0:
            print(f"Nenhum registro encontrado ou vazio, inicializando novo. Profundidade Global: {self.global_depth}")
            initial_directory_size = 1 << self.global_depth
            self.directory = [Bucket(self.global_depth) for _ in range(initial_directory_size)]
            return

        with open(self.REGISTRY_FILE_CSV, "rb") as f:
            self.global_depth = struct.unpack('i', f.read(4))[0]
            directory_size = 1 << self.global_depth
            self.directory = []

            for _ in range(directory_size):
                if f.tell() + 8 > os.path.getsize(self.REGISTRY_FILE_CSV):
                    print("Arquivo de registro corrompido ou incompleto")
                    self.directory.append(Bucket(self.global_depth))
                    continue

                local_depth = struct.unpack('i', f.read(4))[0]
                bucket = Bucket(local_depth)
                bucket_entry_count = struct.unpack('i', f.read(4))[0]

                for _ in range(bucket_entry_count):
                    if f.tell() >= os.path.getsize(self.REGISTRY_FILE_CSV):
                        print("Arquivo de registro terminou inesperadamente")
                        break

                    key_length = struct.unpack('H', f.read(2))[0]
                    key = f.read(key_length).decode('utf-8')
                    offset = struct.unpack('q', f.read(8))[0]
                    bucket.entries[key] = offset

                self.directory.append(bucket)

        print(f"Registro carregado. Profundidade Global: {self.global_depth}, Tamanho do Diretório: {len(self.directory)}")

    def save_registry(self) -> None:
        with open(self.REGISTRY_FILE_CSV, "wb") as f:
            f.write(struct.pack('i', self.global_depth))
            
            for bucket in self.directory:
                f.write(struct.pack('i', bucket.local_depth))
                f.write(struct.pack('i', len(bucket.entries)))
                
                for key, offset in bucket.entries.items():
                    key_bytes = key.encode('utf-8')
                    f.write(struct.pack('H', len(key_bytes)))
                    f.write(key_bytes)
                    f.write(struct.pack('q', offset))

        print(f"Registro salvo. Profundidade Global: {self.global_depth}")

    def process_csv(self, csv_file_path: str, key_extractor: Callable[[str], str]) -> None:
        if not os.path.exists(csv_file_path):
            print(f"Criando arquivo CSV de teste: {csv_file_path}")
            with open(csv_file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for i in range(1, 210001):
                    writer.writerow([i, f"FirstName{i}", f"LastName{i}", i * 10])

        if not self.data_file:
            self.initialize_files()

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            self.data_file.seek(0, io.SEEK_END)
            current_offset = self.data_file.tell()

            for row in reader:
                if not row:
                    continue

                try:
                    key = key_extractor(row[0])
                except (IndexError, ValueError) as e:
                    print(f"Pulando linha CSV malformada: {row}, erro: {e}")
                    continue

                line = ','.join(row) + '\n'
                self.data_file.write(line.encode('utf-8'))
                self.insert(key, current_offset)
                current_offset = self.data_file.tell()

        print("Processamento CSV concluído para ExtensibleHashingCSV.")

    def hash(self, key: str) -> int:
        return zlib.crc32(key.encode('utf-8')) & 0xffffffff

    def get_bucket_index(self, hash_value: int, depth: int) -> int:
        return hash_value & ((1 << depth) - 1)

    def insert(self, key: str, offset: int) -> None:
        bucket_index = self.get_bucket_index(self.hash(key), self.global_depth)
        bucket = self.directory[bucket_index]

        if key in bucket.entries or len(bucket.entries) < self.BUCKET_SIZE:
            bucket.entries[key] = offset
        else:
            self.split_bucket(bucket_index, key, offset)
            self.insert(key, offset)  # Tentar novamente após a divisão

    def split_bucket(self, bucket_index_to_split: int, key_causing_split: str, offset_causing_split: int) -> None:
        old_bucket = self.directory[bucket_index_to_split]
        old_local_depth = old_bucket.local_depth

        if old_local_depth == self.global_depth:
            old_dir_size = len(self.directory)
            if old_dir_size >= (1 << 30):  # Limite prático
                print("Tamanho máximo do diretório atingido, não pode dobrar mais.")
                return

            self.directory.extend(self.directory[:])
            self.global_depth += 1
            print(f"ExtHashingCSV: Profundidade global aumentada para: {self.global_depth}")

        new_local_depth = old_local_depth + 1
        new_bucket = Bucket(new_local_depth)
        old_bucket.local_depth = new_local_depth

        # Atualizar ponteiros de diretório
        for i in range(len(self.directory)):
            prefix_mask = (1 << old_local_depth) - 1
            if (i & prefix_mask) == (bucket_index_to_split & prefix_mask):
                if ((i >> old_local_depth) & 1) == 1:
                    self.directory[i] = new_bucket

        # Redistribuir entradas
        temp_entries = old_bucket.entries.copy()
        temp_entries[key_causing_split] = offset_causing_split
        old_bucket.entries.clear()

        for key, offset in temp_entries.items():
            target_bucket_index = self.get_bucket_index(self.hash(key), self.global_depth)
            target_bucket = self.directory[target_bucket_index]
            
            if len(target_bucket.entries) < self.BUCKET_SIZE or key in target_bucket.entries:
                target_bucket.entries[key] = offset
            else:
                print(f"ExtHashingCSV: Erro durante a redistribuição na divisão. Bucket ainda cheio para a chave: {key}")

    def find_record_offset(self, key: str) -> int:
        hash_val = self.hash(key)
        bucket_index = self.get_bucket_index(hash_val, self.global_depth)
        
        if bucket_index < 0 or bucket_index >= len(self.directory):
            print(f"Erro ExtHashingCSV: Índice de bucket {bucket_index} fora dos limites. Chave: {key}")
            return -1

        bucket = self.directory[bucket_index]
        return bucket.entries.get(key, -1)

    def read_record(self, offset: int) -> Optional[str]:
        if offset == -1:
            return None

        if not self.data_file:
            self.initialize_files()

        if offset >= os.path.getsize(self.DATA_FILE_CSV):
            print(f"Erro ExtHashingCSV: Deslocamento {offset} está além do comprimento do arquivo")
            return None

        self.data_file.seek(offset)
        return self.data_file.readline().decode('utf-8').strip()

    @classmethod
    def run_extensible_hashing_csv(cls):
        print("--- Executando Teste ExtensibleHashingCSV ---")
        hashing = cls()

        for file in [cls.DATA_FILE_CSV, cls.REGISTRY_FILE_CSV, cls.CSV_INPUT_FILE]:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass

        try:
            hashing.initialize_files()
            hashing.load_registry()
            hashing.process_csv(cls.CSV_INPUT_FILE, lambda line: line.split(',')[0])
            hashing.save_registry()

            print("ExtHashingCSV: Estado do diretório após o processamento:")
            for i, bucket in enumerate(hashing.directory):
                print(f"Dir[{i}] -> {bucket} (Entradas: {list(bucket.entries.keys())[:5]}...)")

        except Exception as e:
            print(f"Erro no processamento principal de ExtensibleHashingCSV: {e}")
            import traceback
            traceback.print_exc()
        finally:
            hashing.close_files()

        print("\n--- Teste de Leitura para ExtensibleHashingCSV ---")
        hashing_read = cls()
        try:
            hashing_read.initialize_files()
            hashing_read.load_registry()

            search_keys = ["1", "5", "10", "15", "20", "1000", "999999"]
            for search_key in search_keys:
                print(f"Buscando por chave: {search_key}")
                offset = hashing_read.find_record_offset(search_key)
                if offset != -1:
                    record = hashing_read.read_record(offset)
                    print(f"Registro encontrado para a chave '{search_key}': {record}")
                else:
                    print(f"Registro com a chave '{search_key}' não encontrado.")

        except Exception as e:
            print(f"Erro no teste de leitura de ExtensibleHashingCSV: {e}")
            traceback.print_exc()
        finally:
            hashing_read.close_files()

        print("--- Teste ExtensibleHashingCSV Finalizado ---")

# --- FileBasedExtendibleHashing Implementation ---
class FileBasedPage(Page[int, int]):
    MAX_ENTRIES = 3
    HEADER_SIZE = 8  # 2 integers: entry_count, local_depth
    ENTRY_SIZE = 12  # 1 integer (key) + 1 long (value)

    def __init__(self, file_offset: int, depth_to_set_if_new: int, raf: io.BufferedRandom):
        self.file_offset = file_offset
        self.raf = raf
        self.entries_map: Dict[int, int] = {}
        self.is_new_page = raf.tell() <= file_offset or raf.tell() < file_offset + self.HEADER_SIZE

        raf.seek(file_offset)
        if self.is_new_page:
            self.local_depth = depth_to_set_if_new
            self.entry_count = 0
            raf.write(struct.pack('ii', self.entry_count, self.local_depth))
        else:
            header_data = raf.read(self.HEADER_SIZE)
            if len(header_data) < self.HEADER_SIZE:
                raise IOError("Incomplete page header")
            
            self.entry_count, self.local_depth = struct.unpack('ii', header_data)
            
            for _ in range(self.entry_count):
                entry_data = raf.read(self.ENTRY_SIZE)
                if len(entry_data) < self.ENTRY_SIZE:
                    break
                key, value = struct.unpack('iq', entry_data)
                self.entries_map[key] = value

            if self.entry_count != len(self.entries_map) and self.entry_count > 0:
                print(f"Aviso FBPage: Entradas incompatíveis para a página {file_offset}")
                self.entry_count = len(self.entries_map)
                self.persist_header()

    def persist_header(self) -> None:
        self.raf.seek(self.file_offset)
        self.raf.write(struct.pack('ii', self.entry_count, self.local_depth))

    def persist_entries(self) -> None:
        self.raf.seek(self.file_offset + self.HEADER_SIZE)
        for key, value in self.entries_map.items():
            self.raf.write(struct.pack('iq', key, value))

    def contains(self, key: int) -> bool:
        return key in self.entries_map

    def get(self, key: int) -> Optional[int]:
        return self.entries_map.get(key)

    def put(self, key: int, value: int) -> None:
        new_key = key not in self.entries_map
        if new_key and self.entry_count >= self.MAX_ENTRIES:
            raise ValueError(f"FBPage full at offset {self.file_offset}. Cannot add new key: {key}")

        self.entries_map[key] = value
        if new_key:
            self.entry_count += 1

        self.persist_header()
        self.persist_entries()

    def has_space_for(self, key: int, value: int) -> bool:
        return key in self.entries_map or self.entry_count < self.MAX_ENTRIES

    def depth(self) -> int:
        return self.local_depth

    def increment_local_depth(self) -> None:
        self.local_depth += 1
        self.persist_header()

    def get_id(self) -> int:
        return self.file_offset

    def get_entries(self) -> List[Entry[int, int]]:
        return [Entry.create_entry(k, v) for k, v in self.entries_map.items()]

    def clear_entries_for_split(self) -> None:
        self.entries_map.clear()
        self.entry_count = 0
        self.persist_header()
        self.raf.seek(self.file_offset + self.HEADER_SIZE)

class FileBasedDirectory(Directory):
    INITIAL_GLOBAL_DEPTH = 1
    DIR_METADATA_OFFSET = 0
    GLOBAL_DEPTH_BYTES = 4
    DIR_ENTRIES_OFFSET = GLOBAL_DEPTH_BYTES

    def __init__(self, raf: io.BufferedRandom):
        self.raf = raf
        self.page_offsets: List[int] = []
        self.load()

    def get_global_depth(self) -> int:
        return self.global_depth

    def get_directory_index(self, hash_code: int) -> int:
        if self.global_depth == 0:
            return 0
        return hash_code & ((1 << self.global_depth) - 1)

    def get_page_offset(self, hash_code: int) -> int:
        index = self.get_directory_index(hash_code)
        if 0 <= index < len(self.page_offsets):
            return self.page_offsets[index]
        print(f"Erro FBDirectory: Índice {index} fora dos limites. Hash: {hash_code}, PG: {self.global_depth}")
        return 0

    def extend(self) -> None:
        old_size = 1 << self.global_depth
        self.global_depth += 1
        new_size = 1 << self.global_depth

        if new_size < old_size or new_size > (1 << 30):
            print("FBDirectory: Não é possível estender o diretório. Novo tamanho muito grande ou estouro.")
            self.global_depth -= 1
            raise IOError("Limite de tamanho do diretório atingido.")

        new_page_offsets = [0] * new_size
        for i in range(old_size):
            new_page_offsets[i] = self.page_offsets[i]
            new_page_offsets[i | old_size] = self.page_offsets[i]

        self.page_offsets = new_page_offsets
        print(f"FBDirectory: Estendido. Nova profundidade global: {self.global_depth}, Novo tamanho: {new_size}")

    def put(self, directory_index: int, page_offset: int) -> None:
        if 0 <= directory_index < len(self.page_offsets):
            self.page_offsets[directory_index] = page_offset
        else:
            print(f"Erro FBDirectory: Tentativa de inserção em índice inválido {directory_index}")
            raise IOError(f"Índice de diretório inválido para inserção: {directory_index}")

    def load(self) -> None:
        if os.path.getsize(self.raf.name) >= self.DIR_METADATA_OFFSET + self.GLOBAL_DEPTH_BYTES:
            self.raf.seek(self.DIR_METADATA_OFFSET)
            self.global_depth = struct.unpack('i', self.raf.read(self.GLOBAL_DEPTH_BYTES))[0]
            
            if self.global_depth < 0 or self.global_depth > 30:
                print(f"Aviso FBDirectory: Profundidade global irrazoável {self.global_depth} carregada. Reiniciando.")
                self.initialize_default_directory_state()
                return

            expected_size = 1 << self.global_depth
            self.page_offsets = [0] * expected_size

            if os.path.getsize(self.raf.name) >= self.DIR_ENTRIES_OFFSET + expected_size * 8:
                self.raf.seek(self.DIR_ENTRIES_OFFSET)
                for i in range(expected_size):
                    if self.raf.tell() + 8 > os.path.getsize(self.raf.name):
                        print(f"Erro FBDirectory: Arquivo terminou ao ler deslocamentos de página no índice {i}")
                        break
                    self.page_offsets[i] = struct.unpack('q', self.raf.read(8))[0]

                print(f"FBDirectory: Carregado do arquivo. Profundidade global: {self.global_depth}, Tamanho: {expected_size}")
                if all(p == 0 for p in self.page_offsets) and expected_size > 2:
                    print("Aviso FBDirectory: O diretório carregado parece ter todos os deslocamentos zero.")
            else:
                print(f"FBDirectory: O arquivo existe, mas está incompleto para as entradas. Profundidade carregada: {self.global_depth}")
        else:
            print("FBDirectory: Arquivo não encontrado ou muito pequeno. Inicializando novo diretório.")
            self.initialize_default_directory_state()

    def initialize_default_directory_state(self) -> None:
        self.global_depth = self.INITIAL_GLOBAL_DEPTH
        initial_size = 1 << self.global_depth
        self.page_offsets = [0] * initial_size

    def save(self) -> None:
        self.raf.seek(self.DIR_METADATA_OFFSET)
        self.raf.write(struct.pack('i', self.global_depth))
        self.raf.seek(self.DIR_ENTRIES_OFFSET)
        for offset in self.page_offsets:
            self.raf.write(struct.pack('q', offset))
        print(f"FBDirectory: Salvo. Profundidade global: {self.global_depth}")

class FileBasedDataStore(DataStore[int, int]):
    DATA_PAGES_START_OFFSET = 4096
    PAGE_ALLOCATION_SIZE = 512

    def __init__(self, raf: io.BufferedRandom):
        self.raf = raf
        if os.path.getsize(raf.name) < self.DATA_PAGES_START_OFFSET:
            self.next_available_page_offset = self.DATA_PAGES_START_OFFSET
        else:
            self.next_available_page_offset = os.path.getsize(raf.name)

        # Alinhar a um limite de bloco
        if self.next_available_page_offset % self.PAGE_ALLOCATION_SIZE != 0:
            self.next_available_page_offset = ((self.next_available_page_offset // self.PAGE_ALLOCATION_SIZE) + 1) * self.PAGE_ALLOCATION_SIZE

        print(f"FBDataStore: Inicializado. Próximo deslocamento de página disponível: {self.next_available_page_offset}")

    def get_page(self, page_offset: int) -> Page[int, int]:
        if page_offset < self.DATA_PAGES_START_OFFSET and page_offset != 0:
            print(f"Aviso FBDataStore: Tentativa de obter página em deslocamento suspeito: {page_offset}")
        return FileBasedPage(page_offset, -1, self.raf)

    def allocate_new_page(self, depth_for_new_page: int) -> Page[int, int]:
        new_page_file_offset = self.next_available_page_offset
        new_page = FileBasedPage(new_page_file_offset, depth_for_new_page, self.raf)
        self.next_available_page_offset += self.PAGE_ALLOCATION_SIZE
        print(f"FBDataStore: Nova página alocada em {new_page_file_offset} profundidade {depth_for_new_page}")
        return new_page

    def write_page(self, page: Page[int, int]) -> None:
        pass  # FileBasedPage já persiste seus dados

    def get_next_available_offset(self) -> int:
        return self.next_available_page_offset

class FileBasedEHash(Generic[K, V]):
    HASH_SIZE_METADATA_OFFSET = 2048

    def __init__(self, directory: Directory, data_store: DataStore[K, V], metadata_file: io.BufferedRandom):
        self.directory = directory
        self.data_store = data_store
        self.metadata_file = metadata_file
        self.stats = EHashStats()
        self.size = 0
        self.dirty = False
        self.load_size()

    def contains(self, key: K) -> bool:
        hash_code = hash(key)
        page_offset = self.directory.get_page_offset(hash_code)
        if page_offset != 0:
            page = self.data_store.get_page(page_offset)
            return page.contains(key)
        return False

    def get(self, key: K) -> Optional[V]:
        hash_code = hash(key)
        page_offset = self.directory.get_page_offset(hash_code)
        if page_offset != 0:
            page = self.data_store.get_page(page_offset)
            return page.get(key)
        return None

    def put(self, key: K, value: V) -> None:
        hash_code = hash(key)
        page_offset = self.directory.get_page_offset(hash_code)
        page: Optional[Page[K, V]] = None

        if page_offset == 0:
            page = self.data_store.allocate_new_page(self.directory.get_global_depth())
            page_offset = page.get_id()
            dir_index = self.directory.get_directory_index(hash_code)
            self.directory.put(dir_index, page_offset)
        else:
            page = self.data_store.get_page(page_offset)

        if page.contains(key):
            page.put(key, value)
            self.dirty = True
            return

        if not page.has_space_for(key, value):
            old_page_local_depth = page.depth()

            if old_page_local_depth == self.directory.get_global_depth():
                self.directory.extend()

            new_split_pages_local_depth = old_page_local_depth + 1
            new_page1 = self.data_store.allocate_new_page(new_split_pages_local_depth)
            new_page2 = self.data_store.allocate_new_page(new_split_pages_local_depth)

            entries_to_redistribute = page.get_entries()
            entries_to_redistribute.append(Entry.create_entry(key, value))
            page.clear_entries_for_split()

            for entry in entries_to_redistribute:
                entry_hash = hash(entry.key())
                if ((entry_hash >> old_page_local_depth) & 1) == 0:
                    new_page1.put(entry.key(), entry.value())
                else:
                    new_page2.put(entry.key(), entry.value())

            old_page_dir_prefix = self.directory.get_directory_index(hash_code) & ((1 << old_page_local_depth) - 1)

            for i in range(1 << self.directory.get_global_depth()):
                if (i & ((1 << old_page_local_depth) - 1)) == old_page_dir_prefix:
                    if ((i >> old_page_local_depth) & 1) == 0:
                        self.directory.put(i, new_page1.get_id())
                    else:
                        self.directory.put(i, new_page2.get_id())
        else:
            page.put(key, value)

        self.size += 1
        self.dirty = True

    def get_size(self) -> int:
        return self.size

    def save(self) -> None:
        if self.dirty:
            self.directory.save()
            self.save_size()
            self.dirty = False
            print(f"FileBasedEHash: Salvo. Tamanho: {self.size}")

    def load_size(self) -> None:
        if os.path.getsize(self.metadata_file.name) >= self.HASH_SIZE_METADATA_OFFSET + 8:
            self.metadata_file.seek(self.HASH_SIZE_METADATA_OFFSET)
            self.size = struct.unpack('q', self.metadata_file.read(8))[0]
            print(f"FileBasedEHash: Tamanho carregado: {self.size}")
        else:
            self.size = 0
            print("FileBasedEHash: Metadados de tamanho não encontrados ou arquivo muito pequeno")

    def save_size(self) -> None:
        self.metadata_file.seek(self.HASH_SIZE_METADATA_OFFSET)
        self.metadata_file.write(struct.pack('q', self.size))

    def close(self) -> None:
        self.save()
        print("FileBasedEHash: Fechado (arquivo gerenciado externamente).")

class MergedHashingImplementations:
    FB_CSV_FILE = "src/estagio2/addons/persons_for_fb_hashing.csv"
    FB_HASH_STORAGE_FILE = "src/estagio2/addons/extendible_hash_storage.dat"
    FB_EXTERNAL_DATA_RECORDS_FILE = "src/estagio2/addons/persons_external_records.dat"

    def __init__(self):
        os.makedirs(os.path.dirname(self.FB_HASH_STORAGE_FILE), exist_ok=True)
        self.hash_storage_raf = open(self.FB_HASH_STORAGE_FILE, "r+b")
        
        directory = FileBasedDirectory(self.hash_storage_raf)
        data_store = FileBasedDataStore(self.hash_storage_raf)
        self.extendible_hash = FileBasedEHash(directory, data_store, self.hash_storage_raf)

    def process_csv_and_store_positions(self) -> None:
        if not os.path.exists(self.FB_CSV_FILE):
            print(f"Criando CSV de teste para FileBasedHashing: {self.FB_CSV_FILE}")
            with open(self.FB_CSV_FILE, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for i in range(1, 210001):
                    writer.writerow([i, f"Person {i}", f"Age {i % 80 + 18}"])

        with open(self.FB_EXTERNAL_DATA_RECORDS_FILE, "w+b") as external_data_raf:
            external_data_raf.truncate(0)
            current_position = 0

            with open(self.FB_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if not row:
                        continue

                    try:
                        id_ = int(row[0])
                        line = ','.join(row)
                        
                        external_data_raf.seek(current_position)
                        external_data_raf.write(struct.pack('i', id_))
                        line_bytes = line.encode('utf-8')
                        external_data_raf.write(struct.pack('I', len(line_bytes)))
                        external_data_raf.write(line_bytes)

                        self.extendible_hash.put(id_, current_position)
                        current_position = external_data_raf.tell()

                    except (ValueError, IndexError) as e:
                        print(f"Pulando ID inválido em FileBasedHashing: {row[0]}, erro: {e}")

        self.extendible_hash.save()
        print("Processamento CSV e armazenamento de FileBasedHashing concluídos.")

    def get_person_data(self, id_: int) -> Optional[str]:
        position = self.extendible_hash.get(id_)
        if position is not None:
            with open(self.FB_EXTERNAL_DATA_RECORDS_FILE, "rb") as raf:
                raf.seek(position)
                try:
                    retrieved_id = struct.unpack('i', raf.read(4))[0]
                    line_length = struct.unpack('I', raf.read(4))[0]
                    line = raf.read(line_length).decode('utf-8')
                    
                    if retrieved_id == id_:
                        return line
                    else:
                        print(f"FB Hashing: ID incompatível no deslocamento para a chave {id_}")
                except struct.error:
                    print(f"Erro ao ler dados para ID {id_}")
        return None

    def close(self) -> None:
        if self.extendible_hash:
            self.extendible_hash.close()
        if self.hash_storage_raf:
            self.hash_storage_raf.close()
        print("Recursos de FileBasedExtendibleHashing fechados.")

    @classmethod
    def run_file_based_extendible_hashing(cls):
        print("\n--- Executando Teste de FileBasedExtendibleHashing ---\n")
        
        for file in [cls.FB_CSV_FILE, cls.FB_HASH_STORAGE_FILE, cls.FB_EXTERNAL_DATA_RECORDS_FILE]:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass

        storage = None
        try:
            storage = cls()
            storage.process_csv_and_store_positions()

            search_ids = [1, 15, 30, 49, 50, 100, 7, 210000]
            for search_id in search_ids:
                print(f"\nBuscando pessoa com ID (FB): {search_id}")
                person_data = storage.get_person_data(search_id)
                if person_data:
                    print(f"Dados para o ID {search_id}: {person_data}")
                else:
                    print(f"Pessoa com ID {search_id} não encontrada.")

        except Exception as e:
            print(f"Erro durante a operação de armazenamento de FileBasedHashing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if storage:
                storage.close()

        print("--- Teste de FileBasedExtendibleHashing Finalizado ---")

    @classmethod
    def main(cls):
        print("Iniciando a Suíte de Testes de Implementações de Hashing...")
        print(f"Data/Hora Atual: {datetime.now()}")
        print(f"Diretório de trabalho atual: {os.path.abspath('.')}")
        print("Nota: As operações de arquivo dependem das permissões do ambiente.")

        ExtensibleHashingCSV.run_extensible_hashing_csv()
        print("\n=================================================\n")
        cls.run_file_based_extendible_hashing()

        print("\nSuíte de Testes de Implementações de Hashing Finalizada.")
        print("Verifique o console para saída, erros e arquivos .dat/.csv criados.")

if __name__ == "__main__":
    MergedHashingImplementations.main()
"""