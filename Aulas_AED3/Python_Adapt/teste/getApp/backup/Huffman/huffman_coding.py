import struct
from heapq import heapify, heappop, heappush
from collections import Counter
from typing import Optional

class Node:
    def __init__(self, char: Optional[str], freq: int, left: Optional['Node'] = None, right: Optional['Node'] = None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other: 'Node'):
        return self.freq < other.freq

class HuffmanCoding:
    @staticmethod
    def generate_tree(text: str) -> Optional[Node]:
        if not text:
            return None

        char_count = Counter(text)
        nodes = [Node(char, freq) for char, freq in char_count.items()]
        heapify(nodes)

        while len(nodes) > 1:
            left, right = heappop(nodes), heappop(nodes)
            heappush(nodes, Node(None, left.freq + right.freq, left, right))

        return nodes[0] if nodes else None

    @staticmethod
    def build_char_table(root: Optional[Node], table: dict[str, str] = None, code: str = '') -> dict[str, str]:
        if table is None:
            table = {}
        if root is None:
            return table

        if root.char is not None:
            table[root.char] = code or '0'  # Use '0' for single character input
        else:
            HuffmanCoding.build_char_table(root.left, table, code + '0')
            HuffmanCoding.build_char_table(root.right, table, code + '1')

        return table

    @staticmethod
    def encode_file(infilepath: str, outfilepath: str):

        with open(infilepath, 'r') as file:
            text = file.read()

        if len(text) < 100:  # Minimum file size to apply compression
            print(f"File too small ({len(text)} bytes), copying without compression")
            with open(outfilepath, 'w') as file:
                file.write(text)
            return

        root = HuffmanCoding.generate_tree(text)
        char_table = HuffmanCoding.build_char_table(root)

        with open(outfilepath, 'wb') as file:
            # Write character table
            file.write(struct.pack('I', len(char_table)))
            for char, code in char_table.items():
                file.write(char.encode('utf-8'))
                file.write(struct.pack('B', len(code)))
                file.write(struct.pack('I', int(code, 2)))

            # Write data size
            file.write(struct.pack('I', len(text)))

            # Encode and write data
            current_byte = 0
            bit_count = 0
            for char in text:
                code = char_table[char]
                for bit in code:
                    current_byte = (current_byte << 1) | int(bit)
                    bit_count += 1
                    if bit_count == 8:
                        file.write(bytes([current_byte]))
                        current_byte = 0
                        bit_count = 0

            # Write any remaining bits
            if bit_count > 0:
                current_byte <<= (8 - bit_count)
                file.write(bytes([current_byte]))

            # Write padding size
            file.write(struct.pack('B', (8 - bit_count) % 8))

    @staticmethod
    def decode_file(infilepath: str, outfilepath: str):
        with open(infilepath, 'rb') as file:
            # Read character table
            table_size = struct.unpack('I', file.read(4))[0]
            char_table = {}
            for _ in range(table_size):
                char = file.read(1).decode('utf-8')
                code_length = struct.unpack('B', file.read(1))[0]
                code_int = struct.unpack('I', file.read(4))[0]
                code = format(code_int, f'0{code_length}b')
                char_table[code] = char

            # Read data size
            data_size = struct.unpack('I', file.read(4))[0]

            # Read and decode data
            result = []
            current_code = ""
            bytes_read = 0
            
            while bytes_read < data_size:
                byte = file.read(1)[0]
                for i in range(7, -1, -1):
                    bit = (byte >> i) & 1
                    current_code += str(bit)
                    if current_code in char_table:
                        result.append(char_table[current_code])
                        current_code = ""
                        bytes_read += 1
                        if bytes_read == data_size:
                            break

            # Read padding size (not used in decoding, but part of the file format)
            _ = struct.unpack('B', file.read(1))[0]

        # Write decoded data
        with open(outfilepath, 'w') as file:
            file.write(''.join(result))