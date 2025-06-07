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
    # ... (keep the existing compress function exactly as is) ...

def decompress(input_file_path, output_file_path):
    """Decompress a file using LZW algorithm with variable-length codes"""
    # ... (keep the existing decompress function exactly as is) ...

def main():
    st.title("LZW File Compression/Decompression")
    st.write("Upload a file to compress or decompress using LZW algorithm")
    
    # Add radio buttons for path selection
    path_option = st.radio(
        "Path Options:",
        ("Default", "User's Choice"),
        horizontal=True
    )
    
    if path_option == "Default":
        # Set default paths
        documents_path = str(Path.home() / "Documents")
        source_path = os.path.join(documents_path, "Source")
        lzw_path = os.path.join(documents_path, "LZW")
        
        # Create directories if they don't exist
        ensure_directory_exists(source_path)
        ensure_directory_exists(lzw_path)
        
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
            # Create a temporary directory for user's choice
            temp_dir = tempfile.mkdtemp()
            input_path = os.path.join(temp_dir, uploaded_file.name)
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
    
    if input_path is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Compress File"):
                if path_option == "Default":
                    # Use default output path
                    output_filename = os.path.basename(input_path) + ".lzw"
                    output_path = os.path.join(lzw_path, output_filename)
                else:
                    # Use temporary path for user's choice
                    output_path = input_path + ".lzw"
                
                if compress(input_path, output_path):
                    if path_option == "Default":
                        st.success(f"File compressed and saved to: {output_path}")
                    else:
                        # Offer download of compressed file
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Download Compressed File",
                                data=f,
                                file_name=os.path.basename(output_path),
                                mime="application/octet-stream"
                            )
        
        with col2:
            if st.button("Decompress File"):
                if input_path.endswith(".lzw"):
                    if path_option == "Default":
                        # Use default output path
                        output_filename = os.path.basename(input_path)[:-4]  # Remove .lzw
                        output_path = os.path.join(lzw_path, output_filename)
                    else:
                        # Use temporary path for user's choice
                        output_filename = os.path.basename(input_path)[:-4] if input_path.endswith('.lzw') else os.path.basename(input_path) + '.decompressed'
                        output_path = os.path.join(tempfile.mkdtemp(), output_filename)
                    
                    if decompress(input_path, output_path):
                        if path_option == "Default":
                            st.success(f"File decompressed and saved to: {output_path}")
                        else:
                            # Offer download of decompressed file
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
                if 'output_path' in locals() and os.path.exists(output_path):
                    os.remove(output_path)
                    os.rmdir(os.path.dirname(output_path))
                if 'temp_dir' in locals() and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                st.warning(f"Could not clean up temporary files: {str(e)}")

if __name__ == "__main__":
    main()