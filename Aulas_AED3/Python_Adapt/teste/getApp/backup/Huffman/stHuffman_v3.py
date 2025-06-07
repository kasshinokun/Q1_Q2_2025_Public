import os
import time
import struct
import heapq
import io
import streamlit as st
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional, Dict

# Constants
SOURCE_FOLDER = "Documents/Source/"
HUFFMAN_FOLDER = "Documents/Huffman/"
DEFAULT_EXTENSION = ".csv"
COMPRESSED_EXTENSION = ".huff"

# Ensure directories exist
Path(SOURCE_FOLDER).mkdir(parents=True, exist_ok=True)
Path(HUFFMAN_FOLDER).mkdir(parents=True, exist_ok=True)

class Node:
    __slots__ = ['char', 'freq', 'left', 'right']  # Memory optimization
    
    def __init__(self, char: Optional[str], freq: int, 
                 left: Optional['Node'] = None, 
                 right: Optional['Node'] = None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other: 'Node'):
        return self.freq < other.freq

class HuffmanProcessor:
    @staticmethod
    def generate_tree(data: bytes, progress_bar=None) -> Optional[Node]:
        """Optimized tree generation with progress tracking"""
        if len(data) < 2:
            return Node(data[0:1], 1) if data else None

        if progress_bar:
            progress_bar.progress(0)
            st.session_state.progress_text.text("Analyzing file content...")

        # Use Counter for frequency analysis
        char_count = Counter(data)
        
        # Handle single-character case
        if len(char_count) == 1:
            char = next(iter(char_count))
            return Node(char, char_count[char])
        
        if progress_bar:
            progress_bar.progress(0.2)
            st.session_state.progress_text.text("Building priority queue...")

        nodes = [Node(char, freq) for char, freq in char_count.items()]
        heapq.heapify(nodes)

        if progress_bar:
            progress_bar.progress(0.3)
            st.session_state.progress_text.text("Constructing Huffman tree...")

        while len(nodes) > 1:
            left = heapq.heappop(nodes)
            right = heapq.heappop(nodes)
            heapq.heappush(nodes, Node(None, left.freq + right.freq, left, right))
            
            if progress_bar and len(nodes) % 10 == 0:
                progress = 0.3 + 0.7 * (1 - len(nodes)/len(char_count))
                progress_bar.progress(progress)

        if progress_bar:
            progress_bar.progress(1.0)
            st.session_state.progress_text.text("Huffman tree complete!")
            time.sleep(0.3)

        return nodes[0] if nodes else None

    @staticmethod
    def build_codebook(root: Optional[Node]) -> Dict[bytes, str]:
        """Optimized codebook generation with iterative DFS"""
        if not root:
            return {}

        codebook = {}
        stack = [(root, "")]
        
        while stack:
            node, code = stack.pop()
            if node.char is not None:
                codebook[node.char] = code or '0'
            else:
                stack.append((node.right, code + '1'))
                stack.append((node.left, code + '0'))
        
        return codebook

    @staticmethod
    def compress_file(input_path: str, output_path: str, progress_bar=None) -> tuple:
        """Optimized compression with progress tracking"""
        start_time = time.time()
        
        # Read input file as binary
        with open(input_path, 'rb') as file:
            data = file.read()

        if not data:
            return 0, 0, 0

        original_size = len(data)
        
        # Skip compression for small files
        if original_size < 100:
            with open(output_path, 'wb') as file:
                file.write(data)
            return original_size, original_size, 0

        # Step 1: Build Huffman tree
        if progress_bar:
            st.subheader("Step 1: Building Huffman Tree")
        root = HuffmanProcessor.generate_tree(data, progress_bar)

        # Step 2: Build codebook
        if progress_bar:
            st.subheader("Step 2: Generating Encoding Dictionary")
            progress_bar.progress(0)
            st.session_state.progress_text.text("Building codebook...")
        
        codebook = HuffmanProcessor.build_codebook(root)
        encode_table = {char: code for char, code in codebook.items()}
        
        if progress_bar:
            progress_bar.progress(1.0)
            st.session_state.progress_text.text("Codebook complete!")
            time.sleep(0.3)

        # Step 3: Compress data
        if progress_bar:
            st.subheader("Step 3: Compressing Data")
            progress_bar.progress(0)
            st.session_state.progress_text.text("Compressing...")

        with open(output_path, 'wb') as file:
            # Write character table (optimized format)
            file.write(struct.pack('I', len(codebook)))
            for char, code in codebook.items():
                file.write(struct.pack('B', len(char)))
                file.write(char)
                file.write(struct.pack('B', len(code)))
                file.write(struct.pack('I', int(code, 2)))

            # Write data size
            file.write(struct.pack('I', original_size))

            # Buffered bit writing
            buffer = bytearray()
            current_byte = 0
            bit_count = 0
            bytes_processed = 0
            
            for char in data:
                code = encode_table[char]
                for bit in code:
                    current_byte = (current_byte << 1) | (bit == '1')
                    bit_count += 1
                    if bit_count == 8:
                        buffer.append(current_byte)
                        if len(buffer) >= 8192:  # 8KB buffer
                            file.write(buffer)
                            buffer.clear()
                        current_byte = 0
                        bit_count = 0
                
                bytes_processed += 1
                if progress_bar and bytes_processed % 1000 == 0:
                    progress = bytes_processed / original_size
                    progress_bar.progress(progress)
                    st.session_state.progress_text.text(
                        f"Compressing: {bytes_processed}/{original_size} bytes ({progress*100:.1f}%)"
                    )

            # Flush remaining bits
            if bit_count > 0:
                current_byte <<= (8 - bit_count)
                buffer.append(current_byte)
            
            if buffer:
                file.write(buffer)
            
            # Write padding size
            file.write(struct.pack('B', (8 - bit_count) % 8))

        if progress_bar:
            progress_bar.progress(1.0)
            st.session_state.progress_text.text("Compression complete!")
            time.sleep(0.3)

        compressed_size = os.path.getsize(output_path)
        compression_ratio = (original_size - compressed_size) / original_size * 100
        process_time = time.time() - start_time

        return original_size, compressed_size, compression_ratio, process_time

    @staticmethod
    def decompress_file(input_path: str, output_path: str, progress_bar=None) -> tuple:
        """Optimized decompression with progress tracking"""
        start_time = time.time()
        
        with open(input_path, 'rb') as file:
            # Read character table (optimized format)
            table_size = struct.unpack('I', file.read(4))[0]
            code_table = {}
            max_code_length = 0
            
            if progress_bar:
                st.subheader("Step 1: Reading Metadata")
                progress_bar.progress(0)
                st.session_state.progress_text.text("Reading code table...")

            for i in range(table_size):
                char_len = struct.unpack('B', file.read(1))[0]
                char = file.read(char_len)
                code_length = struct.unpack('B', file.read(1))[0]
                code_int = struct.unpack('I', file.read(4))[0]
                code = format(code_int, f'0{code_length}b')
                code_table[code] = char
                max_code_length = max(max_code_length, code_length)
                
                if progress_bar and i % 100 == 0:
                    progress = (i + 1) / table_size * 0.3
                    progress_bar.progress(progress)

            # Read data size
            data_size = struct.unpack('I', file.read(4))[0]

            if progress_bar:
                progress_bar.progress(0.4)
                st.session_state.progress_text.text("Preparing to decode...")
                st.subheader("Step 2: Decoding Data")

            # Read remaining data in chunks
            chunk_size = 8192  # 8KB chunks
            result = io.BytesIO()
            current_code = ""
            bytes_decoded = 0
            buffer = bytearray()
            
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                buffer.extend(chunk)
                
                # Process complete bytes (all but last chunk)
                while len(buffer) > 1 or (not chunk and buffer):
                    byte = buffer.pop(0)
                    for i in range(7, -1, -1):
                        bit = (byte >> i) & 1
                        current_code += str(bit)
                        
                        # Check for matches of increasing lengths
                        for l in range(1, min(len(current_code), max_code_length) + 1):
                            if current_code[:l] in code_table:
                                result.write(code_table[current_code[:l]])
                                bytes_decoded += 1
                                current_code = current_code[l:]
                                break
                    
                    if progress_bar and bytes_decoded % 1000 == 0:
                        progress = 0.4 + 0.6 * (bytes_decoded / data_size)
                        progress_bar.progress(progress)
                        st.session_state.progress_text.text(
                            f"Decoding: {bytes_decoded}/{data_size} bytes ({progress*100:.1f}%)"
                        )
                    
                    if bytes_decoded >= data_size:
                        break
                
                if bytes_decoded >= data_size:
                    break

            # Handle last byte with padding
            if buffer and bytes_decoded < data_size:
                padding = buffer[-1] if buffer else 0
                last_byte = buffer[-2] if len(buffer) > 1 else 0
                
                for i in range(7, 7 - (8 - padding), -1):
                    bit = (last_byte >> i) & 1
                    current_code += str(bit)
                    
                    for l in range(1, min(len(current_code), max_code_length) + 1):
                        if current_code[:l] in code_table:
                            result.write(code_table[current_code[:l]])
                            bytes_decoded += 1
                            current_code = current_code[l:]
                            break
                    
                    if bytes_decoded >= data_size:
                        break

        # Write decoded data
        with open(output_path, 'wb') as file:
            file.write(result.getvalue())

        if progress_bar:
            progress_bar.progress(1.0)
            st.session_state.progress_text.text("Decompression complete!")
            time.sleep(0.3)

        compressed_size = os.path.getsize(input_path)
        decompressed_size = os.path.getsize(output_path)
        compression_ratio = (compressed_size - decompressed_size) / compressed_size * 100
        process_time = time.time() - start_time

        return compressed_size, decompressed_size, compression_ratio, process_time

def get_default_files(operation: str) -> list:
    """Get files from default directory based on operation"""
    folder = SOURCE_FOLDER if operation == "Compression" else HUFFMAN_FOLDER
    extension = DEFAULT_EXTENSION if operation == "Compression" else COMPRESSED_EXTENSION
    
    files = []
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file.endswith(extension):
                files.append(file)
    return files

def main():
    st.title("Optimized Huffman File Compression/Decompression")
    
    # Initialize session state for progress tracking
    if 'progress_text' not in st.session_state:
        st.session_state.progress_text = st.empty()
    
    # Operation selection
    operation = st.radio("Select Operation:", ("Compression", "Decompression"))
    
    # File selection
    file_source = st.radio("Select File Source:", ("Default", "User's Choice"))
    
    selected_file = None
    uploaded_file = None
    
    if file_source == "Default":
        default_files = get_default_files(operation)
        if default_files:
            selected_file = st.selectbox(f"Select a file to {operation.lower()}:", default_files)
        else:
            folder = SOURCE_FOLDER if operation == "Compression" else HUFFMAN_FOLDER
            ext = DEFAULT_EXTENSION if operation == "Compression" else COMPRESSED_EXTENSION
            st.warning(f"No {ext} files found in {folder}")
    else:  # User's Choice
        uploaded_file = st.file_uploader(
            f"Choose a file to {operation.lower()}",
            type=None if operation == "Decompression" else [DEFAULT_EXTENSION[1:]]
        )
    
    # Process button
    if (selected_file or uploaded_file) and st.button(f"{operation} File"):
        progress_bar = st.progress(0)
        st.session_state.progress_text.text("Initializing...")
        
        try:
            if operation == "Compression":
                if uploaded_file:
                    input_path = os.path.join(SOURCE_FOLDER, uploaded_file.name)
                    with open(input_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    output_filename = uploaded_file.name + COMPRESSED_EXTENSION
                else:
                    input_path = os.path.join(SOURCE_FOLDER, selected_file)
                    output_filename = selected_file + COMPRESSED_EXTENSION
                
                output_path = os.path.join(HUFFMAN_FOLDER, output_filename)
                original_size, compressed_size, compression_ratio, process_time = (
                    HuffmanProcessor.compress_file(input_path, output_path, progress_bar)
                )
                
                st.success("File compressed successfully!")
                st.metric("Original Size", f"{original_size:,} bytes")
                st.metric("Compressed Size", f"{compressed_size:,} bytes")
                st.metric("Compression Ratio", f"{compression_ratio:.2f}%")
                st.metric("Processing Time", f"{process_time:.2f} seconds")
                st.write(f"Compressed file saved to: `{output_path}`")
            
            else:  # Decompression
                if uploaded_file:
                    input_path = os.path.join(HUFFMAN_FOLDER, uploaded_file.name)
                    with open(input_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    output_filename = uploaded_file.name[:-len(COMPRESSED_EXTENSION)]
                else:
                    input_path = os.path.join(HUFFMAN_FOLDER, selected_file)
                    output_filename = selected_file[:-len(COMPRESSED_EXTENSION)]
                
                output_path = os.path.join(HUFFMAN_FOLDER, output_filename)
                compressed_size, decompressed_size, compression_ratio, process_time = (
                    HuffmanProcessor.decompress_file(input_path, output_path, progress_bar)
                )
                
                st.success("File decompressed successfully!")
                st.metric("Compressed Size", f"{compressed_size:,} bytes")
                st.metric("Decompressed Size", f"{decompressed_size:,} bytes")
                st.metric("Compression Ratio", f"{compression_ratio:.2f}%")
                st.metric("Processing Time", f"{process_time:.2f} seconds")
                st.write(f"Decompressed file saved to: `{output_path}`")
        
        except Exception as e:
            st.error(f"Error during {operation.lower()}: {str(e)}")
        finally:
            progress_bar.empty()
            st.session_state.progress_text.empty()

if __name__ == "__main__":
    main()