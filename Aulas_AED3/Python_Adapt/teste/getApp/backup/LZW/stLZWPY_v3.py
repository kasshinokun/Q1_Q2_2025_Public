import os
import time
import tempfile
import streamlit as st
import math
from pathlib import Path

def ensure_directory_exists(path):
    """Ensure the directory exists, create if it doesn't"""
    Path(path).mkdir(parents=True, exist_ok=True)

def compress(input_file_path, output_file_path):
    """Compress a file using LZW algorithm with variable-length codes"""
    start_time = time.time()
    
    # Initialize progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Read the input file as bytes
        with open(input_file_path, 'rb') as f:
            data = f.read()
        
        # Initialize dictionary with all possible single bytes
        dictionary = {bytes([i]): i for i in range(256)}
        next_code = 256
        compressed_data = []
        w = bytes()
        
        total_bytes = len(data)
        processed_bytes = 0
        
        # Determine the minimum number of bits needed initially
        bits = 9  # Start with 9 bits (can represent up to 511)
        max_code = 2**bits - 1
        
        for byte in data:
            c = bytes([byte])
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                compressed_data.append(dictionary[w])
                # Add wc to the dictionary
                dictionary[wc] = next_code
                next_code += 1
                
                # Increase bit length if needed
                if next_code > max_code and bits < 24:  # Limit to 24 bits (16MB dictionary)
                    bits += 1
                    max_code = 2**bits - 1
                
                w = c
            
            processed_bytes += 1
            if processed_bytes % 1000 == 0:
                progress = processed_bytes / total_bytes
                progress_bar.progress(min(progress, 1.0))
                status_text.text(f"Compressing... {processed_bytes}/{total_bytes} bytes processed")
        
        if w:
            compressed_data.append(dictionary[w])
        
        # Write compressed data to output file
        with open(output_file_path, 'wb') as f:
            # Write header with number of codes and initial bits
            f.write(len(compressed_data).to_bytes(4, byteorder='big'))
            f.write(bits.to_bytes(1, byteorder='big'))
            
            # Pack codes into bytes
            buffer = 0
            buffer_length = 0
            
            for code in compressed_data:
                buffer = (buffer << bits) | code
                buffer_length += bits
                
                while buffer_length >= 8:
                    byte = (buffer >> (buffer_length - 8)) & 0xFF
                    f.write(bytes([byte]))
                    buffer_length -= 8
                    buffer = buffer & ((1 << buffer_length) - 1)
            
            # Write remaining bits
            if buffer_length > 0:
                byte = (buffer << (8 - buffer_length)) & 0xFF
                f.write(bytes([byte]))
        
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
    """Decompress a file using LZW algorithm with variable-length codes"""
    start_time = time.time()
    
    # Initialize progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Read the compressed file
        with open(input_file_path, 'rb') as f:
            # Read header
            num_codes = int.from_bytes(f.read(4), byteorder='big')
            bits = int.from_bytes(f.read(1), byteorder='big')
            
            # Read all remaining data
            compressed_bytes = f.read()
        
        # Initialize dictionary with all possible single bytes
        dictionary = {i: bytes([i]) for i in range(256)}
        next_code = 256
        decompressed_data = bytearray()
        
        # Unpack bits into codes
        buffer = 0
        buffer_length = 0
        byte_pos = 0
        codes = []
        
        while len(codes) < num_codes:
            # Fill buffer
            while buffer_length < bits and byte_pos < len(compressed_bytes):
                buffer = (buffer << 8) | compressed_bytes[byte_pos]
                byte_pos += 1
                buffer_length += 8
            
            if buffer_length < bits:
                break  # End of data
            
            # Extract code
            code = (buffer >> (buffer_length - bits)) & ((1 << bits) - 1)
            codes.append(code)
            buffer_length -= bits
            buffer = buffer & ((1 << buffer_length) - 1)
            
            # Update progress
            if len(codes) % 1000 == 0:
                progress = len(codes) / num_codes
                progress_bar.progress(min(progress, 1.0))
                status_text.text(f"Reading compressed data... {len(codes)}/{num_codes} codes processed")
        
        # Check if we got all expected codes
        if len(codes) != num_codes:
            st.error(f"Expected {num_codes} codes but got {len(codes)}")
            return False
        
        # Process codes
        w = dictionary[codes[0]]
        decompressed_data.extend(w)
        
        for code in codes[1:]:
            if code in dictionary:
                entry = dictionary[code]
            elif code == next_code:
                entry = w + w[:1]
            else:
                st.error(f"Bad compressed code: {code}")
                return False
            
            decompressed_data.extend(entry)
            
            # Add w + entry[0] to the dictionary
            dictionary[next_code] = w + entry[:1]
            next_code += 1
            
            # Increase bit length if needed
            if next_code >= (1 << bits) and bits < 24:
                bits += 1
            
            w = entry
            
            # Update progress
            if len(decompressed_data) % 100000 == 0:  # Update every 100KB
                progress = len(decompressed_data) / (len(decompressed_data) + (num_codes - len(codes)) * 3)  # Estimate
                progress_bar.progress(min(progress, 1.0))
                status_text.text(f"Decompressing... {len(decompressed_data)//1024}KB processed")
        
        # Write decompressed data to output file
        with open(output_file_path, 'wb') as f:
            f.write(decompressed_data)
        
        progress_bar.progress(1.0)
        status_text.text("Decompression complete!")
        
        end_time = time.time()
        st.success(f"Decompression completed in {end_time - start_time:.2f} seconds")
        
        return True
    
    except Exception as e:
        st.error(f"Error during decompression: {str(e)}")
        return False

def main():
    st.title("LZW File Compression/Decompression")
    st.write("Upload a file to compress or decompress using LZW algorithm")
    
    # Add radio buttons for path selection
    path_option = st.radio(
        "Path Options:",
        ("Default", "User's Choice"),
        horizontal=True
    )
    
    # Initialize paths
    documents_path = str(Path.home() / "Documents")
    lzw_path = os.path.join(documents_path, "LZW")
    ensure_directory_exists(lzw_path)
    
    if path_option == "Default":
        # Set default source path
        source_path = os.path.join(documents_path, "Source")
        ensure_directory_exists(source_path)
        
        st.info(f"Source files should be placed in: {source_path}")
        st.info(f"Compressed files will be saved to: {lzw_path}")
        
        # Get list of files in source directory
        try:
            source_files = [f for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))]
            if source_files:
                selected_file = st.selectbox("Select a file from Source directory:", source_files)
                input_path = os.path.join(source_path, selected_file)
            else:
                st.warning(f"No files found in {source_path}")
                input_path = None
        except Exception as e:
            st.error(f"Error accessing source directory: {str(e)}")
            input_path = None
    else:
        # User's choice - use file uploader
        uploaded_file = st.file_uploader("Choose a file", type=None)
        input_path = None
        if uploaded_file is not None:
            # Save to temporary location
            temp_dir = tempfile.mkdtemp()
            input_path = os.path.join(temp_dir, uploaded_file.name)
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
    
    if input_path is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Compress File"):
                # For both Default and User's Choice, output goes to Documents/LZW/
                output_filename = os.path.basename(input_path) + ".lzw"
                output_path = os.path.join(lzw_path, output_filename)
                
                if compress(input_path, output_path):
                    st.success(f"File compressed and saved to: {output_path}")
                    
                    # For User's Choice, also offer download option
                    if path_option == "User's Choice":
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Download Compressed File",
                                data=f,
                                file_name=output_filename,
                                mime="application/octet-stream"
                            )
        
        with col2:
            if st.button("Decompress File"):
                if input_path.endswith(".lzw"):
                    # For both Default and User's Choice, output goes to Documents/LZW/
                    output_filename = os.path.basename(input_path)[:-4]  # Remove .lzw
                    output_path = os.path.join(lzw_path, output_filename)
                    
                    if decompress(input_path, output_path):
                        st.success(f"File decompressed and saved to: {output_path}")
                        
                        # For User's Choice, also offer download option
                        if path_option == "User's Choice":
                            with open(output_path, "rb") as f:
                                st.download_button(
                                    label="Download Decompressed File",
                                    data=f,
                                    file_name=output_filename,
                                    mime="application/octet-stream"
                                )
                else:
                    st.warning("Please select a .lzw compressed file for decompression")
        
        # Clean up temporary files if using user's choice
        if path_option == "User's Choice":
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if 'temp_dir' in locals() and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                st.warning(f"Could not clean up temporary files: {str(e)}")

if __name__ == "__main__":
    main()