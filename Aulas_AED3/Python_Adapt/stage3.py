import os
import heapq
import struct
import time
from collections import defaultdict, deque
from heapq import heappush, heappop
from typing import Dict, List, Optional, Tuple, Union

# ==============================================
# Compression Algorithms (Part III)
# ==============================================
class CompressionHandler:
    @staticmethod
    def huffman_compress(input_file: str, output_file: str):
        """Huffman compression (character-based)"""
        start_time = time.time()
        
        # Read input data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = f.read()
        
        # Build frequency table
        freq = defaultdict(int)
        for char in data:
            freq[char] += 1
        
        # Build Huffman tree
        heap = [[weight, [char, ""]] for char, weight in freq.items()]
        heapq.heapify(heap)
        
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
        
        # Generate codes
        huff_codes = dict(heap[0][1:])
        
        # Encode data
        encoded_data = ''.join(huff_codes[char] for char in data)
        
        # Pad encoded data to make it multiple of 8
        extra_padding = 8 - len(encoded_data) % 8
        encoded_data += '0' * extra_padding
        
        # Convert bit string to bytes
        byte_array = bytearray()
        for i in range(0, len(encoded_data), 8):
            byte = encoded_data[i:i+8]
            byte_array.append(int(byte, 2))
        
        # Write to file
        with open(output_file, 'wb') as f:
            # Write metadata
            f.write(struct.pack('I', len(data)))  # Original data length
            f.write(struct.pack('I', extra_padding))  # Padding length
            f.write(struct.pack('I', len(freq)))  # Frequency table size
            
            # Write frequency table
            for char, count in freq.items():
                f.write(struct.pack('c', char.encode('utf-8')))
                f.write(struct.pack('I', count))
            
            # Write compressed data
            f.write(bytes(byte_array))
        
        # Calculate stats
        original_size = os.path.getsize(input_file)
        compressed_size = os.path.getsize(output_file)
        ratio = (compressed_size / original_size) * 100
        elapsed = time.time() - start_time
        
        print(f"Compression complete: {input_file} -> {output_file}")
        print(f"Original size: {original_size} bytes")
        print(f"Compressed size: {compressed_size} bytes")
        print(f"Compression ratio: {ratio:.2f}%")
        print(f"Time: {elapsed:.2f} seconds")

    @staticmethod
    def huffman_decompress(input_file: str, output_file: str):
        """Huffman decompression (character-based)"""
        start_time = time.time()
        
        with open(input_file, 'rb') as f:
            # Read metadata
            data_len = struct.unpack('I', f.read(4))[0]
            padding = struct.unpack('I', f.read(4))[0]
            freq_size = struct.unpack('I', f.read(4))[0]
            
            # Rebuild frequency table
            freq = {}
            for _ in range(freq_size):
                char = f.read(1).decode('utf-8')
                count = struct.unpack('I', f.read(4))[0]
                freq[char] = count
            
            # Read compressed data
            compressed_data = f.read()
        
        # Rebuild Huffman tree
        heap = [[weight, [char, ""]] for char, weight in freq.items()]
        heapq.heapify(heap)
        
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
        
        huff_codes = dict(heap[0][1:])
        reverse_codes = {code: char for char, code in huff_codes.items()}
        
        # Convert bytes to bit string
        bit_string = ""
        for byte in compressed_data:
            bits = bin(byte)[2:].rjust(8, '0')
            bit_string += bits
        
        # Remove padding
        bit_string = bit_string[:-padding] if padding > 0 else bit_string
        
        # Decode data
        current_code = ""
        decoded_data = []
        
        for bit in bit_string:
            current_code += bit
            if current_code in reverse_codes:
                decoded_data.append(reverse_codes[current_code])
                current_code = ""
        
        # Write decompressed data
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(decoded_data))
        
        # Verify
        original_size = os.path.getsize(input_file)
        decompressed_size = os.path.getsize(output_file)
        elapsed = time.time() - start_time
        
        print(f"Decompression complete: {input_file} -> {output_file}")
        print(f"Compressed size: {original_size} bytes")
        print(f"Decompressed size: {decompressed_size} bytes")
        print(f"Time: {elapsed:.2f} seconds")

    @staticmethod
    def huffman_byte_compress(input_file: str, output_file: str):
        """Huffman compression (byte-based)"""
        start_time = time.time()
        
        # Read input data
        with open(input_file, 'rb') as f:
            data = f.read()
        
        # Build frequency table
        freq = defaultdict(int)
        for byte in data:
            freq[byte] += 1
        
        # Build Huffman tree
        heap = [[weight, [byte, ""]] for byte, weight in freq.items()]
        heapq.heapify(heap)
        
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
        
        # Generate codes
        huff_codes = dict(heap[0][1:])
        
        # Encode data
        bit_string = ''.join(huff_codes[byte] for byte in data)
        
        # Pad encoded data to make it multiple of 8
        padding = 8 - len(bit_string) % 8
        bit_string += '0' * padding
        
        # Convert bit string to bytes
        byte_array = bytearray()
        for i in range(0, len(bit_string), 8):
            byte = bit_string[i:i+8]
            byte_array.append(int(byte, 2))
        
        # Write to file
        with open(output_file, 'wb') as f:
            # Write metadata
            f.write(struct.pack('I', len(data)))  # Original data length
            f.write(struct.pack('I', padding))  # Padding length
            f.write(struct.pack('I', len(freq)))  # Frequency table size
            
            # Write frequency table
            for byte, count in freq.items():
                f.write(struct.pack('B', byte))
                f.write(struct.pack('I', count))
            
            # Write compressed data
            f.write(bytes(byte_array))
        
        # Calculate stats
        original_size = os.path.getsize(input_file)
        compressed_size = os.path.getsize(output_file)
        ratio = (compressed_size / original_size) * 100
        elapsed = time.time() - start_time
        
        print(f"Compression complete: {input_file} -> {output_file}")
        print(f"Original size: {original_size} bytes")
        print(f"Compressed size: {compressed_size} bytes")
        print(f"Compression ratio: {ratio:.2f}%")
        print(f"Time: {elapsed:.2f} seconds")

    @staticmethod
    def huffman_byte_decompress(input_file: str, output_file: str):
        """Huffman decompression (byte-based)"""
        start_time = time.time()
        
        with open(input_file, 'rb') as f:
            # Read metadata
            data_len = struct.unpack('I', f.read(4))[0]
            padding = struct.unpack('I', f.read(4))[0]
            freq_size = struct.unpack('I', f.read(4))[0]
            
            # Rebuild frequency table
            freq = {}
            for _ in range(freq_size):
                byte = struct.unpack('B', f.read(1))[0]
                count = struct.unpack('I', f.read(4))[0]
                freq[byte] = count
            
            # Read compressed data
            compressed_data = f.read()
        
        # Rebuild Huffman tree
        heap = [[weight, [byte, ""]] for byte, weight in freq.items()]
        heapq.heapify(heap)
        
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
        
        huff_codes = dict(heap[0][1:])
        reverse_codes = {code: byte for byte, code in huff_codes.items()}
        
        # Convert bytes to bit string
        bit_string = ""
        for byte in compressed_data:
            bits = bin(byte)[2:].rjust(8, '0')
            bit_string += bits
        
        # Remove padding
        bit_string = bit_string[:-padding] if padding > 0 else bit_string
        
        # Decode data
        current_code = ""
        decoded_data = bytearray()
        
        for bit in bit_string:
            current_code += bit
            if current_code in reverse_codes:
                decoded_data.append(reverse_codes[current_code])
                current_code = ""
        
        # Write decompressed data
        with open(output_file, 'wb') as f:
            f.write(decoded_data)
        
        # Verify
        original_size = os.path.getsize(input_file)
        decompressed_size = os.path.getsize(output_file)
        elapsed = time.time() - start_time
        
        print(f"Decompression complete: {input_file} -> {output_file}")
        print(f"Compressed size: {original_size} bytes")
        print(f"Decompressed size: {decompressed_size} bytes")
        print(f"Time: {elapsed:.2f} seconds")

    @staticmethod
    def lzw_compress(input_file: str, output_file: str):
        """LZW compression"""
        start_time = time.time()
        
        # Initialize dictionary
        dict_size = 256
        dictionary = {bytes([i]): i for i in range(dict_size)}
        
        # Read input data
        with open(input_file, 'rb') as f:
            data = f.read()
        
        # Compression
        w = bytes()
        compressed = []
        
        for byte in data:
            wc = w + bytes([byte])
            if wc in dictionary:
                w = wc
            else:
                compressed.append(dictionary[w])
                # Add new sequence to dictionary
                dictionary[wc] = dict_size
                dict_size += 1
                w = bytes([byte])
        
        if w:
            compressed.append(dictionary[w])
        
        # Write to file
        with open(output_file, 'wb') as f:
            # Write number of codes
            f.write(struct.pack('I', len(compressed)))
            # Write codes
            for code in compressed:
                f.write(struct.pack('H', code))  # Use 2-byte unsigned int
        
        # Calculate stats
        original_size = os.path.getsize(input_file)
        compressed_size = os.path.getsize(output_file)
        ratio = (compressed_size / original_size) * 100
        elapsed = time.time() - start_time
        
        print(f"Compression complete: {input_file} -> {output_file}")
        print(f"Original size: {original_size} bytes")
        print(f"Compressed size: {compressed_size} bytes")
        print(f"Compression ratio: {ratio:.2f}%")
        print(f"Time: {elapsed:.2f} seconds")

    @staticmethod
    def lzw_decompress(input_file: str, output_file: str):
        """LZW decompression"""
        start_time = time.time()
        
        # Initialize dictionary
        dict_size = 256
        dictionary = {i: bytes([i]) for i in range(dict_size)}
        
        # Read compressed data
        with open(input_file, 'rb') as f:
            num_codes = struct.unpack('I', f.read(4))[0]
            codes = [struct.unpack('H', f.read(2))[0] for _ in range(num_codes)]
        
        # Decompression
        result = bytearray()
        w = bytes([codes[0]])
        result.extend(w)
        
        for k in codes[1:]:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dict_size:
                entry = w + bytes([w[0]])
            else:
                raise ValueError(f"Bad compressed code: {k}")
            
            result.extend(entry)
            
            # Add new sequence to dictionary
            dictionary[dict_size] = w + bytes([entry[0]])
            dict_size += 1
            
            w = entry
        
        # Write decompressed data
        with open(output_file, 'wb') as f:
            f.write(result)
        
        # Verify
        original_size = os.path.getsize(input_file)
        decompressed_size = os.path.getsize(output_file)
        elapsed = time.time() - start_time
        
        print(f"Decompression complete: {input_file} -> {output_file}")
        print(f"Compressed size: {original_size} bytes")
        print(f"Decompressed size: {decompressed_size} bytes")
        print(f"Time: {elapsed:.2f} seconds")

    @staticmethod
    def test_algorithms():
        """Test all compression algorithms with sample data"""
        sample_file = "sample.txt"
        sample_content = "this is a test string for compression algorithms. this is another test."
        
        # Create sample file
        with open(sample_file, 'w') as f:
            f.write(sample_content)
        
        print("Testing Huffman (character-based)...")
        CompressionHandler.huffman_compress(sample_file, "sample.huffc")
        CompressionHandler.huffman_decompress("sample.huffc", "sample_decompressed.txt")
        
        print("\nTesting Huffman (byte-based)...")
        CompressionHandler.huffman_byte_compress(sample_file, "sample.huffb")
        CompressionHandler.huffman_byte_decompress("sample.huffb", "sample_decompressed_byte.txt")
        
        print("\nTesting LZW...")
        CompressionHandler.lzw_compress(sample_file, "sample.lzw")
        CompressionHandler.lzw_decompress("sample.lzw", "sample_decompressed_lzw.txt")
        
        # Clean up
        os.remove("sample.huffc")
        os.remove("sample.huffb")
        os.remove("sample.lzw")
        os.remove("sample_decompressed.txt")
        os.remove("sample_decompressed_byte.txt")
        os.remove("sample_decompressed_lzw.txt")
        
        print("\nAll tests completed successfully!")


# ==============================================
# Updated Menu System (Part III Integration)
# ==============================================
class MenuSystem:
    @staticmethod
    def main_menu():
        """Display the main menu and handle user input"""
        while True:
            print("\n" + "="*50)
            print("Sistema de Gerenciamento de Acidentes de Trânsito")
            print("="*50)
            print("1. Parte I - Gerenciamento de Dados")
            print("2. Parte II - Indexação e Busca")
            print("3. Parte III - Compactação de Dados")
            print("4. Sair")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                MenuSystem.part1_menu()
            elif choice == "2":
                MenuSystem.part2_menu()
            elif choice == "3":
                MenuSystem.part3_menu()
            elif choice == "4":
                print("Saindo do sistema...")
                return
            else:
                print("Opção inválida. Tente novamente.")

    # Existing Part I and Part II menus remain unchanged
    # ...

    @staticmethod
    def part3_menu():
        """Display Part 3 menu and handle user input"""
        while True:
            print("\n" + "="*50)
            print("Parte III - Compactação de Dados")
            print("="*50)
            print("1. Compactar arquivo (Huffman)")
            print("2. Descompactar arquivo (Huffman)")
            print("3. Compactar arquivo (Huffman Byte)")
            print("4. Descompactar arquivo (Huffman Byte)")
            print("5. Compactar arquivo (LZW)")
            print("6. Descompactar arquivo (LZW)")
            print("7. Testar algoritmos com arquivo de amostra")
            print("8. Voltar ao menu principal")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                input_file = input("Caminho do arquivo de entrada: ").strip()
                output_file = input("Caminho do arquivo de saída (.huffc): ").strip()
                CompressionHandler.huffman_compress(input_file, output_file)
            elif choice == "2":
                input_file = input("Caminho do arquivo compactado (.huffc): ").strip()
                output_file = input("Caminho do arquivo descompactado: ").strip()
                CompressionHandler.huffman_decompress(input_file, output_file)
            elif choice == "3":
                input_file = input("Caminho do arquivo de entrada: ").strip()
                output_file = input("Caminho do arquivo de saída (.huffb): ").strip()
                CompressionHandler.huffman_byte_compress(input_file, output_file)
            elif choice == "4":
                input_file = input("Caminho do arquivo compactado (.huffb): ").strip()
                output_file = input("Caminho do arquivo descompactado: ").strip()
                CompressionHandler.huffman_byte_decompress(input_file, output_file)
            elif choice == "5":
                input_file = input("Caminho do arquivo de entrada: ").strip()
                output_file = input("Caminho do arquivo de saída (.lzw): ").strip()
                CompressionHandler.lzw_compress(input_file, output_file)
            elif choice == "6":
                input_file = input("Caminho do arquivo compactado (.lzw): ").strip()
                output_file = input("Caminho do arquivo descompactado: ").strip()
                CompressionHandler.lzw_decompress(input_file, output_file)
            elif choice == "7":
                CompressionHandler.test_algorithms()
            elif choice == "8":
                return
            else:
                print("Opção inválida. Tente novamente.")


# ==============================================
# Main Execution
# ==============================================
if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("indexed_data", exist_ok=True)
    
    # Start the menu system
    MenuSystem.main_menu()