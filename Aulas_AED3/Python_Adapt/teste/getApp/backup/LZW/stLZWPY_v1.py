import os
import time
import tempfile
import streamlit as st
import math

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
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a file", type=None)
    
    if uploaded_file is not None:
        # Create a temporary directory that works across platforms
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, uploaded_file.name)
        
        try:
            # Save uploaded file to temporary location
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Compress File"):
                    output_path = input_path + ".lzw"
                    if compress(input_path, output_path):
                        # Offer download of compressed file
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Download Compressed File",
                                data=f,
                                file_name=uploaded_file.name + ".lzw",
                                mime="application/octet-stream"
                            )
            
            with col2:
                if st.button("Decompress File"):
                    if input_path.endswith(".lzw"):
                        # For decompression, remove .lzw extension to guess original name
                        original_name = uploaded_file.name[:-4] if uploaded_file.name.endswith('.lzw') else uploaded_file.name + '.decompressed'
                        output_path = os.path.join(temp_dir, original_name)
                        
                        if decompress(input_path, output_path):
                            # Offer download of decompressed file
                            with open(output_path, "rb") as f:
                                st.download_button(
                                    label="Download Decompressed File",
                                    data=f,
                                    file_name=original_name,
                                    mime="application/octet-stream"
                                )
                    else:
                        st.warning("Please upload a .lzw compressed file for decompression")
        
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if 'output_path' in locals() and os.path.exists(output_path):
                    os.remove(output_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                st.warning(f"Could not clean up temporary files: {str(e)}")

if __name__ == "__main__":
    main()