import os
import struct
import io
import hashlib
from typing import Dict, List, Optional, Tuple
"""
# --- Constantes de Arquivo ---
FB_HASH_STORAGE_FILE = "extendible_hash_storage.dat"  # Para diretório, páginas, metadados
FB_EXTERNAL_DATA_RECORDS_FILE = "persons_external_records.dat"  # Dados reais da pessoa (String)
FB_METADATA_FILE = "extendible_hash_metadata.dat" # Arquivo separado para metadados, como o tamanho do hash.

# --- Funções Auxiliares ---
def delete_if_exists(path: str) -> None:
    '''Deleta um arquivo se ele existir.'''
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError as e:
            print(f"Aviso: Não foi possível deletar o arquivo: {path}. Erro: {e}")

def get_hash_bits(key: int, num_bits: int) -> int:
    '''Calcula um hash para a chave e retorna os 'num_bits' menos significativos.'''
    # Usar uma função hash mais robusta, como SHA-256 e pegar os bits.
    # Para chaves inteiras, uma simples máscara de bits pode ser suficiente para demonstração.
    # Convertendo a chave int para bytes para usar SHA-256
    key_bytes = key.to_bytes((key.bit_length() + 7) // 8, 'big') if key else b'\0'
    hash_object = hashlib.sha256(key_bytes)
    hash_int = int(hash_object.hexdigest(), 16)
    return hash_int & ((1 << num_bits) - 1)

# --- Classes de Implementação ---

class FileBasedPage:
    MAX_ENTRIES = 31  # Chaves por bucket
    # HEADER_SIZE = 8: 4 bytes para entry_count + 4 bytes para local_depth
    # ENTRY_SIZE = 12: 4 bytes para chave (int) + 8 bytes para offset (long)
    HEADER_SIZE = 8
    ENTRY_SIZE = 4 + 8 # int key, long data_offset

    def __init__(self, file_offset: int, depth_to_set: int, raf: io.BufferedRandom):
        self.file_offset = file_offset
        self.raf = raf
        self.local_depth = depth_to_set
        self.entry_count = 0
        # self.entries: Dict[int, int] = {} # Mapeia chave para offset de dados
        self.entries: List[Tuple[int, int]] = [] # Lista de tuplas (key, data_offset) para manter a ordem e gerenciar espaço

        # Inicializa se for uma nova página ou carrega uma existente
        if self.is_new_page():
            self.initialize_new_page()
        else:
            self.load_existing_page()

    def is_new_page(self) -> bool:
        '''Verifica se o offset da página aponta para um local 'novo' no arquivo.'''
        # Se o arquivo não tem dados no offset, consideramos novo
        self.raf.seek(0, os.SEEK_END)
        return self.file_offset >= self.raf.tell()

    def initialize_new_page(self) -> None:
        '''Inicializa uma nova página no disco.'''
        self.raf.seek(self.file_offset)
        self.raf.write(struct.pack('>i', 0))  # entry_count = 0
        self.raf.write(struct.pack('>i', self.local_depth)) # local_depth
        # Preenche o restante da página com zeros para garantir o tamanho fixo
        self.raf.write(b'\0' * (self.MAX_ENTRIES * self.ENTRY_SIZE))
        self.raf.flush()

    def load_existing_page(self) -> None:
        '''Carrega uma página existente do disco.'''
        self.raf.seek(self.file_offset)
        header_data = self.raf.read(self.HEADER_SIZE)
        if len(header_data) < self.HEADER_SIZE:
            # Arquivo corrompido ou fim inesperado, tratar como nova página
            print(f"Aviso: Cabeçalho incompleto na página {self.file_offset}. Reinicializando.")
            self.initialize_new_page()
            return

        self.entry_count, self.local_depth = struct.unpack('>ii', header_data)
        self.entries = []
        for _ in range(self.entry_count):
            entry_data = self.raf.read(self.ENTRY_SIZE)
            if len(entry_data) < self.ENTRY_SIZE:
                print(f"Aviso: Entrada incompleta na página {self.file_offset}. Dados podem estar corrompidos.")
                break # Para de carregar se a entrada está incompleta
            key, data_offset = struct.unpack('>iQ', entry_data) # Q para unsigned long long (8 bytes)
            self.entries.append((key, data_offset))

    def save(self) -> None:
        '''Salva o estado atual da página no disco.'''
        self.raf.seek(self.file_offset)
        self.raf.write(struct.pack('>i', self.entry_count))
        self.raf.write(struct.pack('>i', self.local_depth))
        for key, data_offset in self.entries:
            self.raf.write(struct.pack('>iQ', key, data_offset))
        # Preencher o restante com zeros se houver espaço não utilizado
        remaining_bytes = (self.MAX_ENTRIES - self.entry_count) * self.ENTRY_SIZE
        if remaining_bytes > 0:
            self.raf.write(b'\0' * remaining_bytes)
        self.raf.flush()

    def put(self, key: int, data_offset: int) -> bool:
        '''Adiciona uma chave-offset à página. Retorna True se adicionado, False se cheio.'''
        # Se a chave já existe, atualiza o offset
        for i, (existing_key, _) in enumerate(self.entries):
            if existing_key == key:
                self.entries[i] = (key, data_offset)
                self.save()
                return True

        if self.entry_count < self.MAX_ENTRIES:
            self.entries.append((key, data_offset))
            self.entry_count += 1
            self.save()
            return True
        return False # Página cheia

    def get(self, key: int) -> Optional[int]:
        '''Busca o offset de dados para uma chave.'''
        for existing_key, data_offset in self.entries:
            if existing_key == key:
                return data_offset
        return None

    def delete(self, key: int) -> bool:
        '''Deleta uma chave da página. Retorna True se deletado, False se não encontrado.'''
        original_count = self.entry_count
        self.entries = [(k, v) for k, v in self.entries if k != key]
        if len(self.entries) < original_count:
            self.entry_count = len(self.entries)
            self.save()
            return True
        return False

    def is_full(self) -> bool:
        '''Verifica se a página está cheia.'''
        return self.entry_count == self.MAX_ENTRIES

    def is_empty(self) -> bool:
        '''Verifica se a página está vazia.'''
        return self.entry_count == 0

class FileBasedDirectory:
    # Offset para o global_depth no arquivo de diretório
    GLOBAL_DEPTH_OFFSET = 0
    # Offset para o início dos ponteiros de bucket
    BUCKET_POINTERS_OFFSET = 4 # 4 bytes para global_depth

    def __init__(self, raf: io.BufferedRandom, metadata_raf: io.BufferedRandom):
        self.raf = raf # random access file para o diretório
        self.metadata_raf = metadata_raf # random access file para metadados globais
        self.global_depth = 0
        self.bucket_offsets: List[int] = [] # Lista de offsets de páginas (buckets)
        self.load()

    def load(self) -> None:
        '''Carrega o diretório do disco.'''
        # Carregar global_depth
        self.metadata_raf.seek(self.GLOBAL_DEPTH_OFFSET)
        try:
            self.global_depth = struct.unpack('>i', self.metadata_raf.read(4))[0]
        except struct.error:
            self.global_depth = 0 # Arquivo vazio ou corrompido, inicia do zero

        # Carregar ponteiros de bucket
        self.raf.seek(self.BUCKET_POINTERS_OFFSET)
        num_pointers = 1 << self.global_depth
        self.bucket_offsets = []
        for _ in range(num_pointers):
            try:
                offset = struct.unpack('>Q', self.raf.read(8))[0] # Q for unsigned long long (8 bytes)
                self.bucket_offsets.append(offset)
            except struct.error:
                # Se não há mais offsets para carregar, parar
                break
        
        # Se não carregou nada, inicializar diretório
        if not self.bucket_offsets and self.global_depth == 0:
            self.initialize_new_directory()

    def initialize_new_directory(self) -> None:
        '''Inicializa um novo diretório com profundidade global 0 e um único bucket.'''
        self.global_depth = 0
        # O offset do primeiro bucket será logo após os metadados do diretório
        # O offset real do bucket será gerenciado pelo FileBasedEHash
        # CORREÇÃO: Usar 0 em vez de -1 para inicialização, pois '>Q' não aceita negativos.
        self.bucket_offsets = [0] * (1 << self.global_depth) # 0 indica que o offset ainda não foi atribuído
        self.save()

    def save(self) -> None:
        '''Salva o estado atual do diretório no disco.'''
        # Salvar global_depth
        self.metadata_raf.seek(self.GLOBAL_DEPTH_OFFSET)
        self.metadata_raf.write(struct.pack('>i', self.global_depth))
        self.metadata_raf.flush()

        # Salvar ponteiros de bucket
        self.raf.seek(self.BUCKET_POINTERS_OFFSET)
        for offset in self.bucket_offsets:
            self.raf.write(struct.pack('>Q', offset))
        self.raf.flush()

    def double_directory(self) -> None:
        '''Dobra o tamanho do diretório.'''
        old_size = 1 << self.global_depth
        self.global_depth += 1
        new_size = 1 << self.global_depth

        new_bucket_offsets = [0] * new_size
        for i in range(old_size):
            new_bucket_offsets[i] = self.bucket_offsets[i]
            new_bucket_offsets[i + old_size] = self.bucket_offsets[i] # Copia os ponteiros existentes
        self.bucket_offsets = new_bucket_offsets
        self.save()

    def get_bucket_index(self, key: int) -> int:
        '''Retorna o índice do bucket no diretório para uma dada chave.'''
        return get_hash_bits(key, self.global_depth)

    def get_bucket_offset(self, key: int) -> int:
        '''Retorna o offset do bucket no arquivo de armazenamento para uma dada chave.'''
        idx = self.get_bucket_index(key)
        return self.bucket_offsets[idx]

    def set_bucket_offset(self, index: int, offset: int) -> None:
        '''Define o offset de um bucket no diretório.'''
        self.bucket_offsets[index] = offset
        self.save() # Salva imediatamente para persistência

    def close(self) -> None:
        self.save()
        # Não fechar o raf aqui, pois ele é gerenciado pelo FileBasedEHash

class FileBasedEHash:
    # Offset para o tamanho do hash (number of entries) no arquivo de metadados
    HASH_SIZE_METADATA_OFFSET = 4 # Depois do global_depth (4 bytes)

    def __init__(self, directory_file_path: str, storage_file_path: str, external_data_file_path: str, page_size_bytes: int = 4096):
        self.directory_file_path = directory_file_path
        self.storage_file_path = storage_file_path
        self.external_data_file_path = external_data_file_path
        self.page_size_bytes = page_size_bytes

        self.directory_raf: io.BufferedRandom
        self.storage_raf: io.BufferedRandom
        self.metadata_raf: io.BufferedRandom
        self.external_data_raf: io.BufferedRandom

        self.directory: FileBasedDirectory
        self.size = 0 # Número total de chaves no hash
        self.dirty = False # Indica se há mudanças não salvas

        self._open_files()
        self.directory = FileBasedDirectory(self.directory_raf, self.metadata_raf)
        self._load_size()

        # Cache de páginas para reduzir acessos a disco (Lembrar de salvar!)
        self.page_cache: Dict[int, FileBasedPage] = {} # {offset_pagina: FileBasedPage}

    def _open_files(self):
        '''Abre os arquivos RandomAccessFile necessários.'''
        try:
            self.directory_raf = open(self.directory_file_path, 'rb+', buffering=self.page_size_bytes)
        except FileNotFoundError:
            self.directory_raf = open(self.directory_file_path, 'wb+', buffering=self.page_size_bytes)

        try:
            self.storage_raf = open(self.storage_file_path, 'rb+', buffering=self.page_size_bytes)
        except FileNotFoundError:
            self.storage_raf = open(self.storage_file_path, 'wb+', buffering=self.page_size_bytes)
        
        try:
            self.metadata_raf = open(self.metadata_file_path(), 'rb+', buffering=4) # Buffering pequeno para metadados
        except FileNotFoundError:
            self.metadata_raf = open(self.metadata_file_path(), 'wb+', buffering=4)

        try:
            self.external_data_raf = open(self.external_data_file_path, 'rb+', buffering=self.page_size_bytes * 4) # Buffering maior para dados
        except FileNotFoundError:
            self.external_data_raf = open(self.external_data_file_path, 'wb+', buffering=self.page_size_bytes * 4)


    def _load_size(self):
        '''Carrega o número total de chaves do arquivo de metadados.'''
        self.metadata_raf.seek(self.HASH_SIZE_METADATA_OFFSET)
        try:
            self.size = struct.unpack('>Q', self.metadata_raf.read(8))[0] # Q for unsigned long long
            print(f"FileBasedEHash: Tamanho carregado: {self.size}")
        except struct.error:
            self.size = 0
            print("FileBasedEHash: Metadados de tamanho não encontrados ou arquivo muito pequeno, tamanho definido para 0.")

    def _save_size(self):
        '''Salva o número total de chaves no arquivo de metadados.'''
        self.metadata_raf.seek(self.HASH_SIZE_METADATA_OFFSET)
        self.metadata_raf.write(struct.pack('>Q', self.size))
        self.metadata_raf.flush()

    def _get_page(self, page_offset: int, local_depth: int = 0) -> FileBasedPage:
        '''Retorna uma página do cache ou carrega do disco.'''
        if page_offset not in self.page_cache:
            page = FileBasedPage(page_offset, local_depth, self.storage_raf)
            self.page_cache[page_offset] = page
        return self.page_cache[page_offset]
    
    def _allocate_new_page(self) -> int:
        '''Aloca espaço para uma nova página no arquivo de armazenamento e retorna seu offset.'''
        self.storage_raf.seek(0, os.SEEK_END)
        new_page_offset = self.storage_raf.tell()
        # Escreve um cabeçalho inicial para reservar o espaço
        # A página será completamente inicializada quando FileBasedPage for instanciada
        self.storage_raf.write(b'\0' * (FileBasedPage.HEADER_SIZE + FileBasedPage.MAX_ENTRIES * FileBasedPage.ENTRY_SIZE))
        self.storage_raf.flush()
        return new_page_offset

    def _write_external_data(self, value: str) -> int:
        '''Escreve um valor (String) no arquivo de dados externo e retorna seu offset.'''
        self.external_data_raf.seek(0, os.SEEK_END)
        offset = self.external_data_raf.tell()
        # Escreve o tamanho da string (4 bytes) e a string (UTF-8)
        encoded_value = value.encode('utf-8')
        self.external_data_raf.write(struct.pack('>i', len(encoded_value)))
        self.external_data_raf.write(encoded_value)
        self.external_data_raf.flush()
        return offset

    def _read_external_data(self, offset: int) -> Optional[str]:
        '''Lê um valor (String) do arquivo de dados externo a partir de um offset.'''
        if offset == 0: # Offset inválido/vazio (agora 0 é o marcador de vazio)
            return None
        self.external_data_raf.seek(offset)
        try:
            length = struct.unpack('>i', self.external_data_raf.read(4))[0]
            data = self.external_data_raf.read(length).decode('utf-8')
            return data
        except struct.error:
            print(f"Erro ao ler dados externos no offset {offset}.")
            return None
        except UnicodeDecodeError:
            print(f"Erro de decodificação ao ler dados externos no offset {offset}. Dados corrompidos?")
            return None

    def put(self, key: int, value: str) -> None:
        '''Insere ou atualiza um par chave-valor no hash extensível.'''
        data_offset = self._write_external_data(value)
        
        while True:
            # Encontra o índice do bucket e o offset da página
            bucket_index = self.directory.get_bucket_index(key)
            page_offset = self.directory.get_bucket_offset(key)

            if page_offset == 0: # Novo bucket precisa ser alocado (usando 0 como marcador de vazio)
                new_page_offset = self._allocate_new_page()
                # A profundidade local inicial de uma nova página é igual à profundidade global do diretório
                page = self._get_page(new_page_offset, self.directory.global_depth)
                self.directory.set_bucket_offset(bucket_index, new_page_offset)
                
            else:
                page = self._get_page(page_offset)

            if page.put(key, data_offset):
                self.size += 1
                self.dirty = True
                return
            else: # Página está cheia, precisa dividir o bucket ou dobrar o diretório
                if page.local_depth == self.directory.global_depth:
                    # Profundidade local igual à global, precisamos dobrar o diretório
                    self.directory.double_directory()
                    # Tentar novamente após o diretório ter sido dobrado
                    continue
                else:
                    # Profundidade local menor que a global, podemos dividir o bucket
                    self._split_bucket(bucket_index, page)
                    # Tentar novamente a inserção, a chave agora deve ir para o novo bucket ou para o original modificado
                    continue

    def _split_bucket(self, old_bucket_index: int, old_page: FileBasedPage) -> None:
        '''Divide um bucket cheio.'''
        old_page.local_depth += 1 # Aumenta a profundidade local da página antiga

        # Aloca uma nova página para o bucket dividido
        new_page_offset = self._allocate_new_page()
        new_page = self._get_page(new_page_offset, old_page.local_depth)

        # Redistribui as entradas
        entries_to_redistribute = list(old_page.entries)
        old_page.entries = [] # Limpa a página antiga para repopulá-la
        old_page.entry_count = 0
        
        # Calcula a máscara para o novo bit que será usado para a divisão
        split_bit_mask = 1 << (old_page.local_depth - 1)
        
        # Percorre todos os índices do diretório
        for i in range(1 << self.directory.global_depth):
            # Calcula o prefixo da old_page antes da divisão, com a profundidade anterior
            old_prefix_before_split = get_hash_bits(old_bucket_index, old_page.local_depth - 1)
            
            # Calcula o prefixo do índice atual 'i' com a mesma profundidade
            current_index_prefix = get_hash_bits(i, old_page.local_depth - 1)
            
            # Se o prefixo do índice atual 'i' corresponde ao prefixo que estava apontando para a old_page
            if current_index_prefix == old_prefix_before_split:
                # Agora, verifique o bit que foi "adicionado" (o `old_page.local_depth - 1`-ésimo bit)
                if (i & split_bit_mask) == 0:
                    # Este índice 'i' deve apontar para a old_page (metade com o bit desligado)
                    self.directory.set_bucket_offset(i, old_page.file_offset)
                else:
                    # Este índice 'i' deve apontar para a new_page (metade com o bit ligado)
                    self.directory.set_bucket_offset(i, new_page_offset)

        # Redistribui as entradas
        for key, data_offset in entries_to_redistribute:
            self._internal_put_redistribute(key, data_offset)

    def _internal_put_redistribute(self, key: int, data_offset: int) -> None:
        '''Usado internamente durante a redistribuição após a divisão de um bucket.'''
        # Encontra o bucket correto (que agora pode ser a página antiga ou a nova)
        bucket_index = self.directory.get_bucket_index(key)
        page_offset = self.directory.get_bucket_offset(key)
        page = self._get_page(page_offset)
        
        # Adiciona a chave à página. Assume que a página não estará cheia novamente imediatamente.
        page.put(key, data_offset) # Não precisa verificar retorno, pois a lógica de split garante espaço.


    def get(self, key: int) -> Optional[str]:
        '''Busca um valor pela chave.'''
        bucket_index = self.directory.get_bucket_index(key)
        page_offset = self.directory.get_bucket_offset(key)

        if page_offset == 0: # Bucket não existe (usando 0 como marcador de vazio)
            return None

        page = self._get_page(page_offset)
        data_offset = page.get(key)
        if data_offset is not None:
            return self._read_external_data(data_offset)
        return None

    def update(self, key: int, new_value: str) -> bool:
        '''Atualiza o valor associado a uma chave existente.'''
        bucket_index = self.directory.get_bucket_index(key)
        page_offset = self.directory.get_bucket_offset(key)

        if page_offset == 0: # Chave não existe (usando 0 como marcador de vazio)
            return False

        page = self._get_page(page_offset)
        # Verifica se a chave existe antes de tentar atualizar
        if page.get(key) is not None:
            # Escreve o novo valor no arquivo de dados externos e obtém o novo offset
            new_data_offset = self._write_external_data(new_value)
            # Atualiza a entrada na página (o put já trata de atualizações)
            page.put(key, new_data_offset)
            self.dirty = True
            return True
        return False

    def delete(self, key: int) -> bool:
        '''Deleta uma chave e seu valor associado.'''
        bucket_index = self.directory.get_bucket_index(key)
        page_offset = self.directory.get_bucket_offset(key)

        if page_offset == 0: # Chave não existe (usando 0 como marcador de vazio)
            return False

        page = self._get_page(page_offset)
        if page.delete(key):
            self.size -= 1
            self.dirty = True
            # TODO: Implementar fusão de buckets se eles ficarem vazios e tiverem a mesma profundidade local
            # e apontarem para o mesmo pai no diretório.
            # Isso é mais complexo e pode ser deixado para uma versão futura.
            return True
        return False
    
    def size(self) -> int:
        '''Retorna o número total de chaves no hash.'''
        return self.size

    def save(self) -> None:
        '''Salva todas as mudanças pendentes no disco.'''
        if self.dirty:
            self.directory.save() # Salva o diretório
            self._save_size() # Salva o tamanho do hash
            # Salvar todas as páginas no cache que foram modificadas (implementação mais robusta exigiria um flag 'dirty' nas páginas)
            # Por simplicidade, assumimos que put/delete em FileBasedPage já salvam a página individualmente.
            # A principal responsabilidade do save do hash é o diretório e o size.
            self.dirty = False
            print(f"FileBasedEHash: Salvo. Tamanho: {self.size}")

    def close(self) -> None:
        '''Fecha os arquivos abertos.'''
        self.save()
        if self.directory_raf:
            self.directory_raf.close()
        if self.storage_raf:
            self.storage_raf.close()
        if self.metadata_raf:
            self.metadata_raf.close()
        if self.external_data_raf:
            self.external_data_raf.close()
        print("FileBasedEHash: Arquivos fechados.")

    def metadata_file_path(self) -> str:
        '''Gera o caminho para o arquivo de metadados.'''
        return self.storage_file_path + ".metadata"

# --- Função Principal para Testes ---
def main():
    print("Iniciando a Suíte de Testes de Implementações de Hashing Extensível...")
    print(f"Diretório de trabalho atual: {os.getcwd()}")

    # Limpar arquivos antigos para um teste limpo
    delete_if_exists(FB_HASH_STORAGE_FILE)
    delete_if_exists(FB_EXTERNAL_DATA_RECORDS_FILE)
    delete_if_exists(FB_HASH_STORAGE_FILE + ".metadata")
    delete_if_exists(FB_HASH_STORAGE_FILE + ".directory") # Diretório agora é um arquivo separado

    # Instanciar o hash extensível
    # Passamos os paths para os arquivos separados
    hashing = FileBasedEHash(
        directory_file_path=FB_HASH_STORAGE_FILE + ".directory",
        storage_file_path=FB_HASH_STORAGE_FILE,
        external_data_file_path=FB_EXTERNAL_DATA_RECORDS_FILE
    )

    NUM_ENTRIES = 1_000_000 # 1 milhão de registros

    print(f"\n--- Inserindo {NUM_ENTRIES} pares chave-valor ---")
    import time
    start_time = time.time()
    for i in range(NUM_ENTRIES):
        key = i
        value = f"Valor da chave {i}." * 2 # Tornar a string um pouco mais longa
        hashing.put(key, value)
        if (i + 1) % 100000 == 0:
            print(f"Inseridos {i + 1} registros...")
    end_time = time.time()
    print(f"Inserção concluída em {end_time - start_time:.2f} segundos.")
    print(f"Tamanho final do hash: {hashing.size()}")
    hashing.save() # Forçar salvamento após inserções

    print("\n--- Testando operações CRUD ---")

    # READ (Leitura)
    test_keys_read = [0, 1, 99999, 500000, 999999, 1000000] # 1000000 não deve existir
    print("\nTeste de Leitura:")
    for key in test_keys_read:
        start_read_time = time.time()
        value = hashing.get(key)
        end_read_time = time.time()
        if value:
            print(f"Chave {key}: '{value[:30]}...' (Tempo: {end_read_time - start_read_time:.6f}s)")
        else:
            print(f"Chave {key}: NÃO ENCONTRADA (Tempo: {end_read_time - start_read_time:.6f}s)")

    # UPDATE (Atualização)
    key_to_update = 500000
    new_value_for_update = "NOVO VALOR ATUALIZADO PARA A CHAVE 500000!"
    print(f"\nTeste de Atualização da chave {key_to_update}:")
    start_update_time = time.time()
    updated = hashing.update(key_to_update, new_value_for_update)
    end_update_time = time.time()
    if updated:
        print(f"Chave {key_to_update} atualizada com sucesso. (Tempo: {end_update_time - start_update_time:.6f}s)")
        # Verificar se a atualização foi bem-sucedida
        retrieved_value = hashing.get(key_to_update)
        print(f"Valor após atualização: '{retrieved_value}'")
    else:
        print(f"Falha ao atualizar chave {key_to_update}. (Tempo: {end_update_time - start_update_time:.6f}s)")

    # CREATE (Inserção de nova chave) - já fizemos 1 milhão, mas vamos inserir uma a mais
    new_key = 1_000_000
    new_value = "Esta é uma nova chave inserida após as iniciais."
    print(f"\nTeste de Inserção de nova chave {new_key}:")
    start_create_time = time.time()
    hashing.put(new_key, new_value)
    end_create_time = time.time()
    print(f"Nova chave {new_key} inserida. (Tempo: {end_create_time - start_create_time:.6f}s)")
    print(f"Tamanho atual do hash: {hashing.size()}")
    retrieved_new_value = hashing.get(new_key)
    print(f"Valor da nova chave: '{retrieved_new_value}'")

    # DELETE (Exclusão)
    key_to_delete = 100000 # Uma chave do meio
    print(f"\nTeste de Exclusão da chave {key_to_delete}:")
    start_delete_time = time.time()
    deleted = hashing.delete(key_to_delete)
    end_delete_time = time.time()
    if deleted:
        print(f"Chave {key_to_delete} deletada com sucesso. (Tempo: {end_delete_time - start_delete_time:.6f}s)")
        print(f"Tamanho atual do hash: {hashing.size()}")
        # Verificar se foi realmente deletado
        retrieved_after_delete = hashing.get(key_to_delete)
        if retrieved_after_delete is None:
            print(f"Confirmação: Chave {key_to_delete} não encontrada após a exclusão.")
        else:
            print(f"Erro: Chave {key_to_delete} ainda encontrada após a exclusão!")
    else:
        print(f"Falha ao deletar chave {key_to_delete}. (Tempo: {end_delete_time - start_delete_time:.6f}s)")

    # Tentar deletar uma chave que não existe
    key_non_existent = 9999999
    print(f"\nTentando deletar chave inexistente {key_non_existent}:")
    deleted_non_existent = hashing.delete(key_non_existent)
    if not deleted_non_existent:
        print(f"Chave {key_non_existent} não existia, exclusão falhou como esperado.")
    else:
        print(f"Erro: Chave {key_non_existent} que não deveria existir foi deletada!")

    hashing.close()
    print("\nTestes concluídos. Arquivos de persistência gerados.")

if __name__ == "__main__":
    main()
"""