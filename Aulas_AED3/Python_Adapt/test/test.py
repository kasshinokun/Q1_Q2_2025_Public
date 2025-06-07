import os
import struct
import hashlib
import random
import csv

"""
class ExtensibleHash:
    # Formato do Cabeçalho do Arquivo (Fixo no início do arquivo):
    # - int global_depth
    # - int directory_size (número de ponteiros no diretório)
    # - int next_available_block_index (o índice do próximo bloco a ser alocado, também o número total de blocos alocados)
    # - int directory_pointers[] (array de ponteiros para blocos)
    # - int block_local_depths[] (array de profundidades locais, uma para cada bloco alocado)

    # Formato de Cada Bloco de Dados:
    # - int local_depth (profundidade local específica do bloco)
    # - entry1_key_data
    # - entry1_value_data
    # ...
    # - entryN_key_data
    # - entryN_value_data

    def __init__(self, filename="extensible_hash.bin", block_size_kb=4, tuple_size=31, key_type="int", value_type="long"):
        self.filename = filename
        self.block_size = block_size_kb * 1024  # Converte KB para bytes
        self.tuple_size = tuple_size
        self.key_type = key_type
        self.value_type = value_type

        if self.key_type == "int":
            self.key_format = 'i'  # Inteiro (4 bytes)
            self.key_size = struct.calcsize(self.key_format)
            self.empty_key_value = 0 # Valor para indicar um slot de chave vazio
        elif self.key_type == "str":
            self.key_format = '64s' # String (64 bytes, tamanho fixo para simplicidade)
            self.key_size = struct.calcsize(self.key_format)
            self.empty_key_value = b'\x00' * self.key_size # Bytes nulos para indicar um slot de chave vazio
        else:
            raise ValueError("Unsupported key_type. Use 'int' or 'str'.")

        if self.value_type == "long":
            self.value_format = 'q'  # Long long (8 bytes)
            self.value_size = struct.calcsize(self.value_format)
        else:
            raise ValueError("Unsupported value_type. Use 'long'.")

        # Tamanho do cabeçalho de um bloco (apenas a profundidade local)
        self.block_header_size = struct.calcsize('i')
        self.entry_size = self.key_size + self.value_size
        self.entries_per_block = (self.block_size - self.block_header_size) // self.entry_size
        self.max_entries_per_tuple = min(self.tuple_size, self.entries_per_block) # Garante que não exceda o bloco

        self.directory = []  # Lista de índices de blocos
        self.block_local_depths = [] # Lista de profundidades locais para cada bloco
        self.global_depth = 0
        self.next_available_block_index = 0 # Próximo índice para um novo bloco

        self._initialize_hash_file()

    def _initialize_hash_file(self):
        '''Inicializa o arquivo de hash no disco se ele não existir, criando um cabeçalho inicial e blocos.'''
        if not os.path.exists(self.filename):
            print(f"Criando novo arquivo de hash: {self.filename}")
            self.global_depth = 1
            self.directory = [0, 1] # Aponta para os blocos 0 e 1 (reais)
            self.block_local_depths = [1, 1] # Profundidade local inicial para os blocos 0 e 1
            self.next_available_block_index = 2 # Próximo bloco a ser alocado será o 2

            with open(self.filename, 'wb') as f:
                # Escreve o cabeçalho inicial do arquivo
                f.write(struct.pack('i', self.global_depth))
                f.write(struct.pack('i', len(self.directory)))
                f.write(struct.pack('i', self.next_available_block_index))
                f.write(struct.pack(f'{len(self.directory)}i', *self.directory))
                f.write(struct.pack(f'{len(self.block_local_depths)}i', *self.block_local_depths))

                # Escreve blocos vazios iniciais
                for i in range(self.next_available_block_index):
                    f.write(struct.pack('i', self.block_local_depths[i])) # Escreve profundidade local no bloco
                    f.write(b'\x00' * (self.block_size - self.block_header_size)) # Restante do bloco vazio
        else:
            print(f"Carregando arquivo de hash existente: {self.filename}")
            self._read_file_header()

    def _get_hash(self, key):
        '''Retorna o valor hash para a chave.'''
        if self.key_type == "int":
            return key
        elif self.key_type == "str":
            # Usar SHA256 para strings para uma distribuição mais uniforme
            return int(hashlib.sha256(key.encode('utf-8')).hexdigest(), 16)

    def _get_directory_index(self, key_hash):
        '''Calcula o índice do diretório com base no hash da chave e na profundidade global.'''
        return key_hash & ((1 << self.global_depth) - 1)

    def _get_block_offset(self, block_index):
        '''Calcula o offset de bytes para um bloco específico no arquivo.'''
        # Offset do cabeçalho fixo (global_depth, directory_size, next_available_block_index)
        fixed_header_size = 3 * struct.calcsize('i')
        # Offset do array de ponteiros do diretório
        directory_pointers_array_size = len(self.directory) * struct.calcsize('i')
        # Offset do array de profundidades locais dos blocos
        block_local_depths_array_size = len(self.block_local_depths) * struct.calcsize('i')

        header_total_size = fixed_header_size + directory_pointers_array_size + block_local_depths_array_size
        return header_total_size + block_index * self.block_size

    def _read_file_header(self):
        '''Lê todo o cabeçalho do arquivo, incluindo diretório e profundidades locais dos blocos.'''
        with open(self.filename, 'rb') as f:
            f.seek(0)
            self.global_depth = struct.unpack('i', f.read(struct.calcsize('i')))[0]
            directory_size = struct.unpack('i', f.read(struct.calcsize('i')))[0]
            self.next_available_block_index = struct.unpack('i', f.read(struct.calcsize('i')))[0]
            
            self.directory = list(struct.unpack(f'{directory_size}i', f.read(directory_size * struct.calcsize('i'))))
            self.block_local_depths = list(struct.unpack(f'{self.next_available_block_index}i', f.read(self.next_available_block_index * struct.calcsize('i'))))

    def _write_file_header(self):
        '''Escreve todo o cabeçalho do arquivo, incluindo diretório e profundidades locais dos blocos.'''
        with open(self.filename, 'r+b') as f:
            f.seek(0)
            f.write(struct.pack('i', self.global_depth))
            f.write(struct.pack('i', len(self.directory)))
            f.write(struct.pack('i', self.next_available_block_index))
            f.write(struct.pack(f'{len(self.directory)}i', *self.directory))
            f.write(struct.pack(f'{len(self.block_local_depths)}i', *self.block_local_depths))


    def _read_block_content(self, block_index):
        '''Lê os dados de um bloco específico (excluindo seu cabeçalho de profundidade local).'''
        try:
            with open(self.filename, 'rb') as f:
                f.seek(self._get_block_offset(block_index))
                local_depth = struct.unpack('i', f.read(self.block_header_size))[0]
                block_data = f.read(self.block_size - self.block_header_size)
                return local_depth, block_data
        except FileNotFoundError:
            print(f"Erro: Arquivo {self.filename} não encontrado ao ler bloco {block_index}.")
            return 0, b'' # Retorna valores padrão em caso de erro
        except Exception as e:
            print(f"Erro ao ler bloco {block_index}: {e}")
            return 0, b''


    def _write_block_content(self, block_index, local_depth, data):
        '''Escreve a profundidade local e os dados de um bloco específico.'''
        try:
            with open(self.filename, 'r+b') as f:
                f.seek(self._get_block_offset(block_index))
                f.write(struct.pack('i', local_depth))
                f.write(data)
                
                # Atualiza a profundidade local na memória e no cabeçalho do arquivo
                if block_index < len(self.block_local_depths):
                    self.block_local_depths[block_index] = local_depth
                else:
                    # Isso pode acontecer se _find_available_block não foi chamado antes do write,
                    # o que não deve ser o caso em uso normal.
                    print(f"Aviso: block_index {block_index} fora dos limites de block_local_depths.")
                    self.block_local_depths.append(local_depth) # Adiciona se não existir
                self._write_file_header() # Para persistir as profundidades locais
        except FileNotFoundError:
            print(f"Erro: Arquivo {self.filename} não encontrado ao escrever bloco {block_index}.")
        except Exception as e:
            print(f"Erro ao escrever bloco {block_index}: {e}")


    def _allocate_new_block(self):
        '''Aloca um novo bloco no final do arquivo e retorna seu índice.'''
        with open(self.filename, 'r+b') as f:
            f.seek(0, os.SEEK_END) # Vai para o final do arquivo
            
            # Escreve o cabeçalho do bloco (profundidade local)
            f.write(struct.pack('i', self.global_depth)) # Profundidade inicial do novo bloco é a global
            # Escreve o restante do bloco como zeros
            f.write(b'\x00' * (self.block_size - self.block_header_size))
            
            new_block_index = self.next_available_block_index
            self.next_available_block_index += 1

            # Adiciona a profundidade local do novo bloco à lista
            if new_block_index >= len(self.block_local_depths):
                self.block_local_depths.append(self.global_depth)
            else:
                self.block_local_depths[new_block_index] = self.global_depth
            
            self._write_file_header() # Persiste o novo next_available_block_index e block_local_depths
            return new_block_index


    def _split_block(self, block_index_to_split):
        '''Divide um bloco e redistribui suas entradas.'''
        old_local_depth, old_block_data = self._read_block_content(block_index_to_split)
        new_local_depth = old_local_depth + 1

        # Dobrar o diretório se a profundidade local do bloco a ser dividido for igual à profundidade global
        if new_local_depth > self.global_depth:
            self.global_depth += 1
            new_directory_size = 1 << self.global_depth # Dobra o tamanho do diretório
            new_directory = [0] * new_directory_size
            
            # Copia os ponteiros antigos para as novas entradas (cada antigo vira duas novas)
            for i in range(len(self.directory)):
                new_directory[i * 2] = self.directory[i]
                new_directory[i * 2 + 1] = self.directory[i]
            self.directory = new_directory
            self._write_file_header() # Atualiza o diretório no cabeçalho

        # Aloca um novo bloco para a divisão
        new_block_index = self._allocate_new_block()

        new_block1_data = bytearray(self.block_size - self.block_header_size) # Para o bloco original
        new_block2_data = bytearray(self.block_size - self.block_header_size) # Para o novo bloco
        new_block1_count = 0
        new_block2_count = 0

        # Redistribui as entradas do bloco original para os dois novos "buckets"
        for i in range(self.max_entries_per_tuple):
            offset = i * self.entry_size
            entry_data = old_block_data[offset : offset + self.entry_size]

            # Ignora slots vazios
            if self.key_type == "int":
                current_key = struct.unpack(self.key_format, entry_data[:self.key_size])[0]
                if current_key == self.empty_key_value:
                    continue
            elif self.key_type == "str":
                current_key_bytes = entry_data[:self.key_size]
                if current_key_bytes == self.empty_key_value:
                    continue
                current_key = current_key_bytes.decode('utf-8').strip('\x00')

            key_hash = self._get_hash(current_key)
            
            # O bit que decide para qual bloco a entrada vai é o (old_local_depth)-ésimo bit
            # (contando a partir de 0, ou seja, o (old_local_depth + 1)-ésimo bit na representação binária)
            if ((key_hash >> old_local_depth) & 1) == 0: # O bit é 0, fica no bloco original
                start_offset = new_block1_count * self.entry_size
                new_block1_data[start_offset : start_offset + self.entry_size] = entry_data
                new_block1_count += 1
            else: # O bit é 1, vai para o novo bloco
                start_offset = new_block2_count * self.entry_size
                new_block2_data[start_offset : start_offset + self.entry_size] = entry_data
                new_block2_count += 1

        # Escreve os dados redistribuídos nos blocos
        self._write_block_content(block_index_to_split, new_local_depth, new_block1_data)
        self._write_block_content(new_block_index, new_local_depth, new_block2_data)

        # Atualiza os ponteiros do diretório para refletir a divisão
        # Todos os índices no diretório que antes apontavam para block_index_to_split
        # e que agora têm seu (new_local_depth - 1)-ésimo bit (ou seja, o novo bit decisivo) como 1
        # devem ser atualizados para apontar para new_block_index.
        # Os que têm o bit 0 continuam apontando para block_index_to_split.

        # Itera sobre as entradas do diretório. Aquelas que eram "irmãs" antes do split
        # (compartilhando a mesma profundidade old_local_depth) agora podem apontar para blocos diferentes.
        
        # O valor do prefixo (os old_local_depth bits mais significativos) é o mesmo para ambos os blocos.
        # Ex: Se old_local_depth=1, o prefixo é 0 ou 1.
        # Bloco original tinha 00, 01, 10, 11 (mas apenas os old_local_depth bits eram usados).
        # Agora, para new_local_depth, o bloco original representa o prefixo original + 0 no novo bit.
        # O novo bloco representa o prefixo original + 1 no novo bit.

        prefix = block_index_to_split & ((1 << old_local_depth) - 1)
        for i in range(len(self.directory)):
            # Verifica se os bits até old_local_depth correspondem ao prefixo do bloco dividido
            if (i & ((1 << old_local_depth) - 1)) == prefix:
                if ((i >> old_local_depth) & 1) == 0: # O bit que foi adicionado é 0
                    self.directory[i] = block_index_to_split
                else: # O bit que foi adicionado é 1
                    self.directory[i] = new_block_index
        self._write_file_header() # Persiste as mudanças no diretório


    def _add_entry_to_block(self, block_index, key, value):
        '''Tenta adicionar um par chave-valor a um bloco específico.'''
        local_depth, block_data = self._read_block_content(block_index)
        block_data_bytearray = bytearray(block_data)

        for i in range(self.max_entries_per_tuple):
            offset = i * self.entry_size
            current_key_data = block_data_bytearray[offset : offset + self.key_size]
            
            # Verifica se o slot está vazio
            if self.key_type == "int":
                if struct.unpack(self.key_format, current_key_data)[0] == self.empty_key_value:
                    block_data_bytearray[offset : offset + self.key_size] = struct.pack(self.key_format, key)
                    block_data_bytearray[offset + self.key_size : offset + self.entry_size] = struct.pack(self.value_format, value)
                    self._write_block_content(block_index, local_depth, block_data_bytearray)
                    return True
            elif self.key_type == "str":
                if current_key_data == self.empty_key_value:
                    key_bytes = key.encode('utf-8')
                    # Garante que a string tenha o tamanho fixo, preenchendo com nulos ou truncando
                    if len(key_bytes) > self.key_size:
                        key_bytes = key_bytes[:self.key_size]
                    else:
                        key_bytes = key_bytes.ljust(self.key_size, b'\x00')

                    block_data_bytearray[offset : offset + self.key_size] = key_bytes
                    block_data_bytearray[offset + self.key_size : offset + self.entry_size] = struct.pack(self.value_format, value)
                    self._write_block_content(block_index, local_depth, block_data_bytearray)
                    return True
        return False  # Bloco está cheio

    # --- Operações CRUD ---
    def create(self, key, value):
        '''Adiciona um novo par chave-valor ao hash extensível.'''
        key_hash = self._get_hash(key)
        dir_index = self._get_directory_index(key_hash)
        block_index = self.directory[dir_index]

        # Tenta adicionar a entrada no bloco
        if not self._add_entry_to_block(block_index, key, value):
            # Se o bloco estiver cheio, precisamos dividi-lo
            # Loop para garantir que a divisão seja feita até que haja espaço ou o bit de profundidade global seja alcançado
            current_block_ld = self.block_local_depths[block_index]
            
            while not self._add_entry_to_block(block_index, key, value):
                if current_block_ld == self.global_depth:
                    # O bloco já está na profundidade global, então o diretório também precisa ser expandido
                    # O _split_block já lida com o dobramento do diretório se necessário
                    print(f"Bloco {block_index} cheio, profundidade local {current_block_ld} == global {self.global_depth}. Dividindo bloco e possivelmente diretório.")
                    self._split_block(block_index)
                else:
                    # O bloco tem profundidade local menor que a global, então apenas divide o bloco
                    # sem expandir o diretório (apenas redistribui ponteiros no diretório atual)
                    print(f"Bloco {block_index} cheio, profundidade local {current_block_ld} < global {self.global_depth}. Dividindo bloco.")
                    self._split_block(block_index)
                
                # Após a divisão, o item pode ter mudado de bloco. Recalcula o índice.
                block_index = self.directory[self._get_directory_index(key_hash)]
                current_block_ld = self.block_local_depths[block_index]


    def read(self, key):
        '''Lê o valor associado a uma chave.'''
        key_hash = self._get_hash(key)
        dir_index = self._get_directory_index(key_hash)
        block_index = self.directory[dir_index]
        
        _, block_data = self._read_block_content(block_index)

        for i in range(self.max_entries_per_tuple):
            offset = i * self.entry_size
            current_key_data = block_data[offset : offset + self.key_size]
            current_value_data = block_data[offset + self.key_size : offset + self.entry_size]

            if self.key_type == "int":
                current_key = struct.unpack(self.key_format, current_key_data)[0]
                if current_key == key:
                    return struct.unpack(self.value_format, current_value_data)[0]
            elif self.key_type == "str":
                current_key = current_key_data.decode('utf-8').strip('\x00')
                if current_key == key:
                    return struct.unpack(self.value_format, current_value_data)[0]
        return None  # Chave não encontrada

    def update(self, key, new_value):
        '''Atualiza o valor associado a uma chave existente.'''
        key_hash = self._get_hash(key)
        dir_index = self._get_directory_index(key_hash)
        block_index = self.directory[dir_index]
        
        local_depth, block_data = self._read_block_content(block_index)
        block_data_bytearray = bytearray(block_data)

        for i in range(self.max_entries_per_tuple):
            offset = i * self.entry_size
            current_key_data = block_data_bytearray[offset : offset + self.key_size]

            if self.key_type == "int":
                current_key = struct.unpack(self.key_format, current_key_data)[0]
                if current_key == key:
                    block_data_bytearray[offset + self.key_size : offset + self.entry_size] = struct.pack(self.value_format, new_value)
                    self._write_block_content(block_index, local_depth, block_data_bytearray)
                    return True
            elif self.key_type == "str":
                current_key = current_key_data.decode('utf-8').strip('\x00')
                if current_key == key:
                    block_data_bytearray[offset + self.key_size : offset + self.entry_size] = struct.pack(self.value_format, new_value)
                    self._write_block_content(block_index, local_depth, block_data_bytearray)
                    return True
        return False  # Chave não encontrada

    def delete(self, key):
        '''Deleta um par chave-valor do hash extensível.'''
        key_hash = self._get_hash(key)
        dir_index = self._get_directory_index(key_hash)
        block_index = self.directory[dir_index]
        
        local_depth, block_data = self._read_block_content(block_index)
        block_data_bytearray = bytearray(block_data)

        for i in range(self.max_entries_per_tuple):
            offset = i * self.entry_size
            current_key_data = block_data_bytearray[offset : offset + self.key_size]

            if self.key_type == "int":
                current_key = struct.unpack(self.key_format, current_key_data)[0]
                if current_key == key:
                    # Limpa a entrada, preenchendo com o valor vazio
                    block_data_bytearray[offset : offset + self.key_size] = struct.pack(self.key_format, self.empty_key_value)
                    block_data_bytearray[offset + self.key_size : offset + self.entry_size] = struct.pack(self.value_format, 0) # Zera o valor também
                    self._write_block_content(block_index, local_depth, block_data_bytearray)
                    return True
            elif self.key_type == "str":
                current_key = current_key_data.decode('utf-8').strip('\x00')
                if current_key == key:
                    # Limpa a entrada
                    #block_data_bytearray[offset : offset + self.key_size] = self.empty_key_value
                    block_data_bytearray[offset + self.key_size : offset + self.entry_size] = struct.pack(self.value_format, 0) # Zera o valor
                    self._write_block_content(block_index, local_depth, block_data_bytearray)
                    return True
        return False  # Chave não encontrada

# --- Procedimento de Geração de CSV ---
def generate_people_csv(filename="people.csv", num_people=1_000_000):
    print(f"Gerando {num_people} pessoas aleatórias para {filename}...")
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'age', 'position_in_bytes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Calcula o comprimento do cabeçalho CSV em bytes
        header_row_string = ",".join(fieldnames) + "\n"
        current_position = len(header_row_string.encode('utf-8'))

        for i in range(1, num_people + 1):
            person_data = {
                'id': i,
                'age': random.randint(5, 75),
                'position_in_bytes': current_position
            }
            # Escreve a linha e captura o que foi escrito para calcular o próximo offset
            row_string = f"{person_data['id']},{person_data['age']},{person_data['position_in_bytes']}\n"
            row_bytes = row_string.encode('utf-8')
            csvfile.write(row_bytes.decode('utf-8')) # Escreve de volta como string para o writer
            current_position += len(row_bytes)

    print(f"Arquivo CSV '{filename}' gerado com sucesso.")

# --- Processos Principais (Ler CSV e Popular Hash) ---
def populate_hash_from_csv(hash_data_structure: ExtensibleHash, csv_filename="people.csv"):
    '''Popula a estrutura de hash a partir de um arquivo CSV.'''
    print(f"Populando hash de '{csv_filename}'...")
    try:
        with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Garante que o tipo da chave corresponda ao que o hash espera
                if hash_data_structure.key_type == "int":
                    person_key = int(row['id'])
                elif hash_data_structure.key_type == "str":
                    person_key = row['id'] # Mantém como string
                else:
                    raise ValueError(f"Tipo de chave não suportado para popular de CSV: {hash_data_structure.key_type}")

                position_in_bytes = int(row['position_in_bytes'])
                hash_data_structure.create(person_key, position_in_bytes)
        print("População do hash completa.")
    except FileNotFoundError:
        print(f"Erro: Arquivo CSV '{csv_filename}' não encontrado.")
    except Exception as e:
        print(f"Erro durante a população do hash: {e}")

if __name__ == "__main__":
    # --- Configuração ---
    CSV_FILENAME = "people.csv"
    HASH_FILENAME_INT_KEY = "extensible_hash_int_key.bin"
    HASH_FILENAME_STR_KEY = "extensible_hash_str_key.bin"
    NUM_PEOPLE_FOR_TEST = 1_000_000
     # Reduzido para testes mais rápidos. Use 1_000_000 para a versão completa.

    # Limpa arquivos anteriores para uma execução fresca
    print("Iniciando limpeza de arquivos anteriores...")
    for f in [CSV_FILENAME, HASH_FILENAME_INT_KEY, HASH_FILENAME_STR_KEY]:
        if os.path.exists(f):
            os.remove(f)
            print(f"Arquivo removido: {f}")
    print("Limpeza de arquivos concluída.")

    # 1. Gera o arquivo CSV
    generate_people_csv(CSV_FILENAME, NUM_PEOPLE_FOR_TEST)

    # 2. Cria e popula o Hash Extensível com chaves inteiras (id -> position_in_bytes)
    print("\n--- Usando Hash Extensível com Chaves Inteiras ---")
    int_key_hash = ExtensibleHash(filename=HASH_FILENAME_INT_KEY, key_type="int", value_type="long")
    populate_hash_from_csv(int_key_hash, CSV_FILENAME)

    # --- Testa Operações CRUD (Chave Inteira) ---
    print("\n--- Testando CRUD (Chave Inteira) ---")
    
    # Leitura
    test_id_read = random.randint(1, NUM_PEOPLE_FOR_TEST)
    pos = int_key_hash.read(test_id_read)
    print(f"Leitura: ID {test_id_read} -> Posição {pos}")

    # Atualização
    test_id_update = random.randint(1, NUM_PEOPLE_FOR_TEST)
    old_pos_update = int_key_hash.read(test_id_update)
    new_pos_update = 999999999  # Um valor distinto
    int_key_hash.update(test_id_update, new_pos_update)
    updated_pos = int_key_hash.read(test_id_update)
    print(f"Atualização: ID {test_id_update}, Posição Antiga {old_pos_update}, Nova Posição {updated_pos} (Esperado: {new_pos_update})")

    # Criação (nova entrada)
    new_id = NUM_PEOPLE_FOR_TEST + 1
    new_pos = 123456789
    print(f"Criando nova entrada: ID {new_id} com Posição {new_pos}")
    int_key_hash.create(new_id, new_pos)
    created_pos = int_key_hash.read(new_id)
    print(f"Criação: ID {new_id} -> Posição {created_pos} (Esperado: {new_pos})")

    # Deleção
    test_id_delete = random.randint(1, NUM_PEOPLE_FOR_TEST)
    print(f"Deletando entrada: ID {test_id_delete}")
    int_key_hash.delete(test_id_delete)
    deleted_pos = int_key_hash.read(test_id_delete)
    print(f"Deleção: ID {test_id_delete} -> Posição {deleted_pos} (Esperado: None)")

    # 3. Cria e popula o Hash Extensível com chaves de string (id_str -> position_in_bytes)
    print("\n--- Usando Hash Extensível com Chaves de String ---")
    str_key_hash = ExtensibleHash(filename=HASH_FILENAME_STR_KEY, key_type="str", value_type="long")
    populate_hash_from_csv(str_key_hash, CSV_FILENAME)

    # --- Testa Operações CRUD (Chave String) ---
    print("\n--- Testando CRUD (Chave String) ---")
    
    # Leitura
    test_id_read_str = str(random.randint(1, NUM_PEOPLE_FOR_TEST))
    pos_str = str_key_hash.read(test_id_read_str)
    print(f"Leitura: ID '{test_id_read_str}' -> Posição {pos_str}")

    # Atualização
    test_id_update_str = str(random.randint(1, NUM_PEOPLE_FOR_TEST))
    old_pos_update_str = str_key_hash.read(test_id_update_str)
    new_pos_update_str = 1000000000
    str_key_hash.update(test_id_update_str, new_pos_update_str)
    updated_pos_str = str_key_hash.read(test_id_update_str)
    print(f"Atualização: ID '{test_id_update_str}', Posição Antiga {old_pos_update_str}, Nova Posição {updated_pos_str} (Esperado: {new_pos_update_str})")

    # Criação (nova entrada)
    new_id_str = str(NUM_PEOPLE_FOR_TEST + 2)
    new_pos_str = 234567890
    print(f"Criando nova entrada: ID '{new_id_str}' com Posição {new_pos_str}")
    str_key_hash.create(new_id_str, new_pos_str)
    created_pos_str = str_key_hash.read(new_id_str)
    print(f"Criação: ID '{new_id_str}' -> Posição {created_pos_str} (Esperado: {new_pos_str})")

    # Deleção
    test_id_delete_str = str(random.randint(1, NUM_PEOPLE_FOR_TEST))
    print(f"Deletando entrada: ID '{test_id_delete_str}'")
    str_key_hash.delete(test_id_delete_str)
    deleted_pos_str = str_key_hash.read(test_id_delete_str)
    print(f"Deleção: ID '{test_id_delete_str}' -> Posição {deleted_pos_str} (Esperado: None)")

    print("\nDemonstração completa.")
"""