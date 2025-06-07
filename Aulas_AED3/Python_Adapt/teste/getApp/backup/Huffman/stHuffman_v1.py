import os
import time
import tempfile
import heapq
import streamlit as st
from collections import defaultdict
from pathlib import Path

class HuffmanNode:
    def __init__(self, char=None, freq=0, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right
    
    def __lt__(self, other):
        return self.freq < other.freq

def build_frequency_dict(data):
    frequency = defaultdict(int)
    for byte in data:
        frequency[byte] += 1
    return frequency

def build_huffman_tree(frequency):
    heap = []
    for byte, freq in frequency.items():
        heapq.heappush(heap, HuffmanNode(char=byte, freq=freq))
    
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)
    
    return heapq.heappop(heap)

def build_codes(root, current_code="", codes={}):
    if root is None:
        return
    
    if root.char is not None:
        codes[root.char] = current_code
        return
    
    build_codes(root.left, current_code + "0", codes)
    build_codes(root.right, current_code + "1", codes)
    
    return codes

def encode_data(data, codes):
    encoded_bits = ""
    for byte in data:
        encoded_bits += codes[byte]
    
    # Pad the encoded bits to make it a multiple of 8
    padding = 8 - len(encoded_bits) % 8
    encoded_bits += "0" * padding
    
    # Convert bit string to bytes
    byte_array = bytearray()
    for i in range(0, len(encoded_bits), 8):
        byte = encoded_bits[i:i+8]
        byte_array.append(int(byte, 2))
    
    return bytes(byte_array), padding

def decode_data(encoded_data, root, padding):
    # Convert bytes back to bit string
    bit_string = ""
    for byte in encoded_data:
        bits = bin(byte)[2:].rjust(8, '0')
        bit_string += bits
    
    # Remove padding
    bit_string = bit_string[:-padding] if padding else bit_string
    
    # Decode using Huffman tree
    current_node = root
    decoded_data = bytearray()
    
    for bit in bit_string:
        if bit == '0':
            current_node = current_node.left
        else:
            current_node = current_node.right
        
        if current_node.char is not None:
            decoded_data.append(current_node.char)
            current_node = root
    
    return bytes(decoded_data)

def serialize_tree(root):
    """Serialize Huffman tree using pre-order traversal"""
    if root is None:
        return b''
    
    if root.char is not None:
        return b'1' + bytes([root.char])
    
    left_serialized = serialize_tree(root.left)
    right_serialized = serialize_tree(root.right)
    return b'0' + left_serialized + right_serialized

def deserialize_tree(data):
    """Deserialize Huffman tree from binary data"""
    def helper():
        nonlocal index
        if index >= len(data):
            return None
        
        flag = data[index]
        index += 1
        
        if flag == ord('1'):
            char = data[index]
            index += 1
            return HuffmanNode(char=char)
        else:
            left = helper()
            right = helper()
            return HuffmanNode(left=left, right=right)
    
    index = 0
    return helper()

def compress(input_file_path, output_file_path):
    """Compress a file using Huffman coding"""
    start_time = time.time()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Read input file
        with open(input_file_path, 'rb') as f:
            data = f.read()
        
        # Build Huffman tree and codes
        frequency = build_frequency_dict(data)
        root = build_huffman_tree(frequency)
        codes = build_codes(root)
        
        # Encode the data
        encoded_data, padding = encode_data(data, codes)
        
        # Serialize the Huffman tree
        serialized_tree = serialize_tree(root)
        
        # Write to output file
        with open(output_file_path, 'wb') as f:
            # Write header (padding + tree size + tree data + encoded data)
            f.write(padding.to_bytes(1, byteorder='big'))
            f.write(len(serialized_tree).to_bytes(4, byteorder='big'))
            f.write(serialized_tree)
            f.write(encoded_data)
        
        progress_bar.progress(1.0)
        status_text.text("Compression complete!")
        
        end_time = time.time()
        original_size = os.path.getsize(input_file_path)
        compressed_size = os.path.getsize(output_file_path)
        ratio = (compressed_size / original_size) * 100
        
        st.success(f"Compression completed in {end_time - start_time:.2f} seconds")
        st.metric("Original size", f"{original_size} bytes")
        st.metric("Compressed size", f"{compressed_size} bytes")
        st.metric("Compression ratio", f"{ratio:.2f}%")
        
        return True
    
    except Exception as e:
        st.error(f"Error during compression: {str(e)}")
        return False

def decompress(input_file_path, output_file_path):
    """Decompress a file using Huffman coding"""
    start_time = time.time()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Read compressed file
        with open(input_file_path, 'rb') as f:
            # Read header
            padding = int.from_bytes(f.read(1), byteorder='big')
            tree_size = int.from_bytes(f.read(4), byteorder='big')
            tree_data = f.read(tree_size)
            encoded_data = f.read()
        
        # Deserialize Huffman tree
        root = deserialize_tree(tree_data)
        
        # Decode the data
        decoded_data = decode_data(encoded_data, root, padding)
        
        # Write decompressed data
        with open(output_file_path, 'wb') as f:
            f.write(decoded_data)
        
        progress_bar.progress(1.0)
        status_text.text("Decompression complete!")
        
        end_time = time.time()
        st.success(f"Decompression completed in {end_time - start_time:.2f} seconds")
        
        return True
    
    except Exception as e:
        st.error(f"Error during decompression: {str(e)}")
        return False

def ensure_directory_exists(path):
    """Ensure the directory exists, create if it doesn't"""
    Path(path).mkdir(parents=True, exist_ok=True)

def main():
    st.title("Huffman File Compression/Decompression")
    
    # Initialize paths
    documents_path = str(Path.home() / "Documents")
    source_path = os.path.join(documents_path, "Source")
    huffman_path = os.path.join(documents_path, "Huffman")
    ensure_directory_exists(source_path)
    ensure_directory_exists(huffman_path)
    
    # Operation mode selection
    operation_mode = st.selectbox(
        "Select Operation Mode:",
        ("Compression", "Decompression")
    )
    
    # Path selection
    path_option = st.radio(
        "File Selection Method:",
        ("Standard", "User's Choice"),
        horizontal=True
    )
    
    uploaded_file = None
    input_path = None
    
    if operation_mode == "Compression":
        if path_option == "Standard":
            # List files in Source directory
            try:
                source_files = [f for f in os.listdir(source_path) 
                              if os.path.isfile(os.path.join(source_path, f))]
                if source_files:
                    selected_file = st.selectbox("Select a file from Source directory:", source_files)
                    st.text(f"Selected file: {selected_file}")
                    input_path = os.path.join(source_path, selected_file)
                else:
                    st.warning(f"No files found in {source_path}")
            except Exception as e:
                st.error(f"Error accessing source directory: {str(e)}")
        else:  # User's Choice
            uploaded_file = st.file_uploader("Choose a file to compress", type=None)
            if uploaded_file is not None:
                temp_dir = tempfile.mkdtemp()
                input_path = os.path.join(temp_dir, uploaded_file.name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
        
        # Show compress button if we have a file
        if (path_option == "Standard" and input_path is not None) or (path_option == "User's Choice" and uploaded_file is not None):
            if st.button("Compress File"):
                output_filename = os.path.basename(input_path) + ".huff"
                output_path = os.path.join(huffman_path, output_filename)
                
                if compress(input_path, output_path):
                    st.success(f"File compressed and saved to: {output_path}")
                    
                    if path_option == "User's Choice":
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Download Compressed File",
                                data=f,
                                file_name=output_filename,
                                mime="application/octet-stream"
                            )
    
    else:  # Decompression mode
        if path_option == "Standard":
            # List Huffman files in Huffman directory
            try:
                huff_files = [f for f in os.listdir(huffman_path) 
                            if os.path.isfile(os.path.join(huffman_path, f)) and f.lower().endswith('.huff')]
                if huff_files:
                    selected_file = st.selectbox("Select a Huffman file from Huffman directory:", huff_files)
                    st.text(f"Selected file: {selected_file}")
                    input_path = os.path.join(huffman_path, selected_file)
                else:
                    st.warning(f"No Huffman files found in {huffman_path}")
            except Exception as e:
                st.error(f"Error accessing Huffman directory: {str(e)}")
        else:  # User's Choice
            uploaded_file = st.file_uploader("Choose a Huffman file to decompress", type=['huff'])
            if uploaded_file is not None:
                temp_dir = tempfile.mkdtemp()
                input_path = os.path.join(temp_dir, uploaded_file.name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
        
        # Show decompress button if we have a file
        if (path_option == "Standard" and input_path is not None) or (path_option == "User's Choice" and uploaded_file is not None):
            if st.button("Decompress File"):
                output_filename = os.path.basename(input_path)[:-5]  # Remove .huff
                output_path = os.path.join(huffman_path, output_filename)
                
                if decompress(input_path, output_path):
                    st.success(f"File decompressed and saved to: {output_path}")
                    
                    if path_option == "User's Choice":
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Download Decompressed File",
                                data=f,
                                file_name=output_filename,
                                mime="application/octet-stream"
                            )
    
    # Clean up temporary files if using user's choice
    if path_option == "User's Choice" and uploaded_file is not None:
        try:
            if input_path and os.path.exists(input_path):
                os.remove(input_path)
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            st.warning(f"Could not clean up temporary files: {str(e)}")

if __name__ == "__main__":
    main()