import os
import time
import heapq
import streamlit as st
from collections import defaultdict
from pathlib import Path

# Constants
SOURCE_FOLDER = "Documents/Source/"
HUFFMAN_FOLDER = "Documents/Huffman/"
DEFAULT_EXTENSION = ".csv"
COMPRESSED_EXTENSION = ".huff"

# Ensure directories exist
Path(SOURCE_FOLDER).mkdir(parents=True, exist_ok=True)
Path(HUFFMAN_FOLDER).mkdir(parents=True, exist_ok=True)

class HuffmanNode:
    def __init__(self, char=None, freq=0, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right
    
    def __lt__(self, other):
        return self.freq < other.freq

def build_frequency_table(data):
    frequency = defaultdict(int)
    for byte in data:
        frequency[byte] += 1
    return frequency

def build_huffman_tree(frequency):
    priority_queue = []
    for char, freq in frequency.items():
        heapq.heappush(priority_queue, HuffmanNode(char=char, freq=freq))
    
    while len(priority_queue) > 1:
        left = heapq.heappop(priority_queue)
        right = heapq.heappop(priority_queue)
        merged = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(priority_queue, merged)
    
    return heapq.heappop(priority_queue)

def build_codebook(root, current_code="", codebook=None):
    if codebook is None:
        codebook = {}
    
    if root.char is not None:
        codebook[root.char] = current_code
        return codebook
    
    build_codebook(root.left, current_code + "0", codebook)
    build_codebook(root.right, current_code + "1", codebook)
    return codebook

def serialize_tree(root):
    if root.char is not None:
        return f"1{root.char:02x}"
    return f"0{serialize_tree(root.left)}{serialize_tree(root.right)}"

def compress_data(data, codebook):
    compressed_bits = ""
    for byte in data:
        compressed_bits += codebook[byte]
    
    # Pad with zeros to make it a multiple of 8
    padding = 8 - (len(compressed_bits) % 8)
    if padding != 8:
        compressed_bits += "0" * padding
    
    # Convert bit string to bytes
    compressed_bytes = bytearray()
    for i in range(0, len(compressed_bits), 8):
        byte = compressed_bits[i:i+8]
        compressed_bytes.append(int(byte, 2))
    
    return bytes(compressed_bytes), padding

def compress_file(input_path, output_path):
    with open(input_path, "rb") as f:
        data = f.read()
    
    if not data:
        return 0
    
    frequency = build_frequency_table(data)
    huffman_tree = build_huffman_tree(frequency)
    codebook = build_codebook(huffman_tree)
    compressed_data, padding = compress_data(data, codebook)
    tree_serialized = serialize_tree(huffman_tree)
    
    with open(output_path, "wb") as f:
        # Write metadata: padding (1 byte), tree length (4 bytes), tree, compressed data
        f.write(bytes([padding]))
        tree_bytes = bytes.fromhex(tree_serialized)
        f.write(len(tree_bytes).to_bytes(4, byteorder="big"))
        f.write(tree_bytes)
        f.write(compressed_data)
    
    original_size = len(data)
    compressed_size = len(compressed_data) + 1 + 4 + len(tree_bytes)
    compression_ratio = (original_size - compressed_size) / original_size * 100
    
    return original_size, compressed_size, compression_ratio

def deserialize_tree(data, index=0):
    if index >= len(data):
        return None, index
    
    node_type = data[index]
    index += 1
    
    if node_type == 49:  # '1' in ASCII
        char = int(data[index:index+2], 16)
        index += 2
        return HuffmanNode(char=char), index
    else:
        left, index = deserialize_tree(data, index)
        right, index = deserialize_tree(data, index)
        return HuffmanNode(left=left, right=right), index

def decompress_data(compressed_data, padding, huffman_tree):
    # Convert bytes to bit string
    bit_string = ""
    for byte in compressed_data:
        bit_string += f"{byte:08b}"
    
    # Remove padding
    if padding != 0:
        bit_string = bit_string[:-padding]
    
    # Decode using Huffman tree
    current_node = huffman_tree
    output = bytearray()
    
    for bit in bit_string:
        if bit == "0":
            current_node = current_node.left
        else:
            current_node = current_node.right
        
        if current_node.char is not None:
            output.append(current_node.char)
            current_node = huffman_tree
    
    return bytes(output)

def decompress_file(input_path, output_path):
    with open(input_path, "rb") as f:
        padding = f.read(1)[0]
        tree_length = int.from_bytes(f.read(4), byteorder="big"))
        tree_data = f.read(tree_length).hex()
        compressed_data = f.read()
    
    huffman_tree, _ = deserialize_tree(tree_data)
    decompressed_data = decompress_data(compressed_data, padding, huffman_tree)
    
    with open(output_path, "wb") as f:
        f.write(decompressed_data)
    
    compressed_size = os.path.getsize(input_path)
    decompressed_size = len(decompressed_data)
    compression_ratio = (compressed_size - decompressed_size) / compressed_size * 100
    
    return compressed_size, decompressed_size, compression_ratio

def get_default_files():
    files = []
    if os.path.exists(SOURCE_FOLDER):
        for file in os.listdir(SOURCE_FOLDER):
            if file.endswith(DEFAULT_EXTENSION):
                files.append(file)
    return files

def main():
    st.title("Huffman File Compression/Decompression")
    
    # Operation selection
    operation = st.radio("Select Operation:", ("Compression", "Decompression"))
    
    # File selection
    file_source = st.radio("Select File Source:", ("Default", "User's Choice"))
    
    selected_file = None
    uploaded_file = None
    
    if file_source == "Default":
        if operation == "Compression":
            default_files = get_default_files()
            if default_files:
                selected_file = st.selectbox("Select a file to compress:", default_files)
            else:
                st.warning(f"No {DEFAULT_EXTENSION} files found in {SOURCE_FOLDER}")
        else:  # Decompression
            default_files = [f for f in os.listdir(HUFFMAN_FOLDER) if f.endswith(COMPRESSED_EXTENSION)]
            if default_files:
                selected_file = st.selectbox("Select a file to decompress:", default_files)
            else:
                st.warning(f"No {COMPRESSED_EXTENSION} files found in {HUFFMAN_FOLDER}")
    else:  # User's Choice
        uploaded_file = st.file_uploader(
            f"Choose a file to {'compress' if operation == 'Compression' else 'decompress'}",
            type=None if operation == "Decompression" else [DEFAULT_EXTENSION[1:]]
        )
    
    # Process button
    if (selected_file or uploaded_file) and st.button(f"{operation} File"):
        start_time = time.time()
        
        try:
            if operation == "Compression":
                if uploaded_file:
                    input_path = os.path.join(SOURCE_FOLDER, uploaded_file.name)
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    output_filename = uploaded_file.name + COMPRESSED_EXTENSION
                else:
                    input_path = os.path.join(SOURCE_FOLDER, selected_file)
                    output_filename = selected_file + COMPRESSED_EXTENSION
                
                output_path = os.path.join(HUFFMAN_FOLDER, output_filename)
                original_size, compressed_size, compression_ratio = compress_file(input_path, output_path)
                
                st.success(f"File compressed successfully!")
                st.write(f"Original size: {original_size} bytes")
                st.write(f"Compressed size: {compressed_size} bytes")
                st.write(f"Compression ratio: {compression_ratio:.2f}%")
                st.write(f"Compressed file saved to: {output_path}")
            
            else:  # Decompression
                if uploaded_file:
                    input_path = os.path.join(HUFFMAN_FOLDER, uploaded_file.name)
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    output_filename = uploaded_file.name[:-len(COMPRESSED_EXTENSION)]
                else:
                    input_path = os.path.join(HUFFMAN_FOLDER, selected_file)
                    output_filename = selected_file[:-len(COMPRESSED_EXTENSION)]
                
                output_path = os.path.join(HUFFMAN_FOLDER, output_filename)
                compressed_size, decompressed_size, compression_ratio = decompress_file(input_path, output_path)
                
                st.success(f"File decompressed successfully!")
                st.write(f"Compressed size: {compressed_size} bytes")
                st.write(f"Decompressed size: {decompressed_size} bytes")
                st.write(f"Compression ratio: {compression_ratio:.2f}%")
                st.write(f"Decompressed file saved to: {output_path}")
            
            process_time = time.time() - start_time
            st.write(f"Processing time: {process_time:.2f} seconds")
        
        except Exception as e:
            st.error(f"Error during {operation.lower()}: {str(e)}")

if __name__ == "__main__":
    main()