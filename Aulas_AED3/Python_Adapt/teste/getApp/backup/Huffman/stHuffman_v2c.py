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

def build_frequency_table(data, progress_bar):
    frequency = defaultdict(int)
    total_bytes = len(data)
    progress_text = st.empty()
    
    for i, byte in enumerate(data):
        frequency[byte] += 1
        if i % 1000 == 0 or i == total_bytes - 1:
            progress = (i + 1) / total_bytes
            progress_bar.progress(progress)
            progress_text.text(f"Analyzing file bytes: {i+1}/{total_bytes} ({progress*100:.1f}%)")
    
    return frequency

def build_huffman_tree(frequency, progress_bar):
    priority_queue = []
    total_items = len(frequency)
    progress_text = st.empty()
    
    # Show initial progress
    progress_bar.progress(0)
    progress_text.text("Building priority queue...")
    
    for i, (char, freq) in enumerate(frequency.items()):
        heapq.heappush(priority_queue, HuffmanNode(char=char, freq=freq))
        progress = (i + 1) / total_items * 0.3  # First 30% of progress
        progress_bar.progress(progress)
        progress_text.text(f"Adding nodes to queue: {i+1}/{total_items} ({progress*100:.1f}%)")
    
    # Building the tree
    progress_text.text("Building Huffman tree...")
    step = 0.7 / (len(priority_queue) - 1) if len(priority_queue) > 1 else 0.7
    
    while len(priority_queue) > 1:
        left = heapq.heappop(priority_queue)
        right = heapq.heappop(priority_queue)
        merged = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(priority_queue, merged)
        
        current_progress = 0.3 + step * (len(priority_queue) - 1)
        progress_bar.progress(current_progress)
        progress_text.text(f"Merging nodes: {len(priority_queue)} remaining")
    
    progress_bar.progress(1.0)
    progress_text.text("Huffman tree complete!")
    time.sleep(0.5)  # Let users see the completion
    
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

def compress_data(data, codebook, progress_bar):
    compressed_bits = ""
    total_bytes = len(data)
    progress_text = st.empty()
    
    for i, byte in enumerate(data):
        compressed_bits += codebook[byte]
        if i % 1000 == 0 or i == total_bytes - 1:
            progress = (i + 1) / total_bytes
            progress_bar.progress(progress)
            progress_text.text(f"Compressing data: {i+1}/{total_bytes} ({progress*100:.1f}%)")
    
    # Pad with zeros to make it a multiple of 8
    padding = 8 - (len(compressed_bits) % 8)
    if padding != 8:
        compressed_bits += "0" * padding
    
    # Convert bit string to bytes
    compressed_bytes = bytearray()
    total_chunks = len(compressed_bits) // 8
    progress_text.text("Finalizing compressed data...")
    
    for i in range(0, len(compressed_bits), 8):
        byte = compressed_bits[i:i+8]
        compressed_bytes.append(int(byte, 2))
        if i % 8000 == 0 or i == len(compressed_bits) - 8:
            progress = (i//8 + 1) / total_chunks
            progress_bar.progress(progress)
    
    progress_bar.progress(1.0)
    progress_text.text("Compression complete!")
    time.sleep(0.5)
    
    return bytes(compressed_bytes), padding

def compress_file(input_path, output_path):
    progress_bar = st.progress(0)
    
    with open(input_path, "rb") as f:
        data = f.read()
    
    if not data:
        return 0, 0, 0
    
    # Step 1: Build frequency table
    st.subheader("Step 1: Analyzing file content")
    frequency = build_frequency_table(data, progress_bar)
    
    # Step 2: Build Huffman tree
    st.subheader("Step 2: Building Huffman tree")
    huffman_tree = build_huffman_tree(frequency, progress_bar)
    
    # Step 3: Build codebook
    st.subheader("Step 3: Generating encoding dictionary")
    codebook = build_codebook(huffman_tree)
    progress_bar.progress(1.0)
    st.success("Encoding dictionary created!")
    time.sleep(0.5)
    
    # Step 4: Compress data
    st.subheader("Step 4: Compressing data")
    compressed_data, padding = compress_data(data, codebook, progress_bar)
    
    # Step 5: Serialize tree and write to file
    st.subheader("Step 5: Saving compressed file")
    progress_text = st.empty()
    progress_bar.progress(0)
    progress_text.text("Serializing Huffman tree...")
    tree_serialized = serialize_tree(huffman_tree)
    progress_bar.progress(0.3)
    
    progress_text.text("Writing metadata...")
    with open(output_path, "wb") as f:
        # Write metadata: padding (1 byte), tree length (4 bytes), tree, compressed data
        f.write(bytes([padding]))
        tree_bytes = bytes.fromhex(tree_serialized)
        f.write(len(tree_bytes).to_bytes(4, byteorder="big"))
        progress_bar.progress(0.6)
        
        f.write(tree_bytes)
        progress_bar.progress(0.8)
        
        f.write(compressed_data)
        progress_bar.progress(1.0)
    
    progress_text.text("File saved successfully!")
    time.sleep(0.5)
    
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

def decompress_data(compressed_data, padding, huffman_tree, progress_bar):
    # Convert bytes to bit string
    bit_string = ""
    total_bytes = len(compressed_data)
    progress_text = st.empty()
    
    for i, byte in enumerate(compressed_data):
        bit_string += f"{byte:08b}"
        if i % 1000 == 0 or i == total_bytes - 1:
            progress = (i + 1) / total_bytes * 0.3  # First 30% of progress
            progress_bar.progress(progress)
            progress_text.text(f"Converting bytes to bits: {i+1}/{total_bytes} ({progress*100:.1f}%)")
    
    # Remove padding
    if padding != 0:
        bit_string = bit_string[:-padding]
    
    # Decode using Huffman tree
    progress_text.text("Decoding data...")
    current_node = huffman_tree
    output = bytearray()
    total_bits = len(bit_string)
    
    for i, bit in enumerate(bit_string):
        if bit == "0":
            current_node = current_node.left
        else:
            current_node = current_node.right
        
        if current_node.char is not None:
            output.append(current_node.char)
            current_node = huffman_tree
        
        if i % 100000 == 0 or i == total_bits - 1:
            progress = 0.3 + (i + 1) / total_bits * 0.7  # Remaining 70% of progress
            progress_bar.progress(progress)
            progress_text.text(f"Decoding bits: {i+1}/{total_bits} ({progress*100:.1f}%)")
    
    progress_bar.progress(1.0)
    progress_text.text("Decompression complete!")
    time.sleep(0.5)
    
    return bytes(output)

def decompress_file(input_path, output_path):
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    # Step 1: Read metadata
    st.subheader("Step 1: Reading compressed file")
    progress_text.text("Reading file metadata...")
    with open(input_path, "rb") as f:
        padding = f.read(1)[0]
        progress_bar.progress(0.1)
        
        tree_length = int.from_bytes(f.read(4), byteorder="big")
        progress_bar.progress(0.2)
        
        tree_data = f.read(tree_length).hex()
        progress_bar.progress(0.4)
        
        compressed_data = f.read()
        progress_bar.progress(0.6)
    
    # Step 2: Rebuild Huffman tree
    st.subheader("Step 2: Rebuilding Huffman tree")
    progress_text.text("Rebuilding Huffman tree...")
    huffman_tree, _ = deserialize_tree(tree_data)
    progress_bar.progress(0.8)
    
    # Step 3: Decompress data
    st.subheader("Step 3: Decompressing data")
    decompressed_data = decompress_data(compressed_data, padding, huffman_tree, progress_bar)
    
    # Step 4: Save decompressed file
    st.subheader("Step 4: Saving decompressed file")
    progress_text.text("Writing decompressed data...")
    with open(output_path, "wb") as f:
        f.write(decompressed_data)
    progress_bar.progress(1.0)
    progress_text.text("File saved successfully!")
    time.sleep(0.5)
    
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
            st.write(f"Total processing time: {process_time:.2f} seconds")
        
        except Exception as e:
            st.error(f"Error during {operation.lower()}: {str(e)}")

if __name__ == "__main__":
    main()