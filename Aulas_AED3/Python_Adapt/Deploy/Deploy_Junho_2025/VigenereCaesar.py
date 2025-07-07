import streamlit as st
import os
import random
import string
from io import BytesIO

# Hybrid Encryption Functions
def hybrid_encrypt(data: bytes, password: str, padding: int) -> bytes:
    """Encrypt data using Vigenere + Caesar ciphers"""
    key_bytes = password.encode('utf-8')
    encrypted = bytearray()
    
    # Vigenere encryption
    for i, byte in enumerate(data):
        shift = key_bytes[i % len(key_bytes)]
        encrypted.append((byte + shift) % 256)
    
    # Caesar encryption
    encrypted = bytearray((b + padding) % 256 for b in encrypted)
    return bytes(encrypted)

def hybrid_decrypt(data: bytes, password: str, padding: int) -> bytes:
    """Decrypt data using Caesar + Vigenere ciphers"""
    key_bytes = password.encode('utf-8')
    decrypted = bytearray()
    
    # Caesar decryption
    for byte in data:
        decrypted.append((byte - padding) % 256)
    
    # Vigenere decryption
    result = bytearray()
    for i, byte in enumerate(decrypted):
        shift = key_bytes[i % len(key_bytes)]
        result.append((byte - shift) % 256)
    
    return bytes(result)

# Key File Operations
def create_key_file(password: str, padding: int, filename: str) -> BytesIO:
    """Generate key file content"""
    content = f"password: {password}\npadding: {padding}\nfilename: {filename}"
    return BytesIO(content.encode('utf-8'))

def parse_key_file(key_file: BytesIO) -> tuple:
    """Extract password, padding, and filename from key file"""
    content = key_file.read().decode('utf-8')
    lines = content.splitlines()
    
    password = None
    padding = None
    filename = None
    
    for line in lines:
        if line.startswith('password:'):
            password = line.split(': ')[1]
        elif line.startswith('padding:'):
            padding = int(line.split(': ')[1])
        elif line.startswith('filename:'):
            filename = line.split(': ')[1]
    
    return password, padding, filename

# Streamlit App
st.title("🔒 Hybrid File Encryption")
st.write("Encrypt/decrypt .db, .idx, and .btr files using Vigenere + Caesar ciphers")

tab_encrypt, tab_decrypt = st.tabs(["🔐 Encryption", "🔓 Decryption"])

with tab_encrypt:
    st.subheader("Encrypt Files")
    uploaded_file = st.file_uploader("Choose file to encrypt", 
                                    type=['db', 'idx', 'btr'],
                                    key="enc_upload")
    
    col1, col2 = st.columns(2)
    password = col1.text_input("Encryption Password (leave blank to auto-generate)", 
                              type="password", 
                              key="enc_pwd")
    padding = col2.number_input("Padding Value (0-255, 0=auto)", 
                               min_value=0, max_value=255, value=0,
                               key="enc_pad")
    
    if st.button("Encrypt File", use_container_width=True):
        if uploaded_file:
            # Generate credentials if not provided
            if password == "":
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
                st.info(f"Auto-generated Password: `{password}`")
            
            if padding == 0:
                padding = random.randint(1, 255)
                st.info(f"Auto-generated Padding: `{padding}`")
            
            # Process encryption
            original_data = uploaded_file.read()
            encrypted_data = hybrid_encrypt(original_data, password, padding)
            
            # Create key file
            key_file = create_key_file(password, padding, uploaded_file.name)
            
            # Download results
            st.success("Encryption Complete!")
            col1, col2 = st.columns(2)
            col1.download_button(
                label="Download Encrypted File",
                data=encrypted_data,
                file_name=f"{uploaded_file.name}.enc",
                mime="application/octet-stream"
            )
            col2.download_button(
                label="Download Key File",
                data=key_file,
                file_name=f"{uploaded_file.name}.key",
                mime="text/plain"
            )
        else:
            st.warning("Please upload a file first")

with tab_decrypt:
    st.subheader("Decrypt Files")
    enc_file = st.file_uploader("Upload Encrypted File", 
                               type=['enc'],
                               key="dec_enc")
    key_file = st.file_uploader("Upload Key File", 
                               type=['key'],
                               key="dec_key")
    
    if st.button("Decrypt File", use_container_width=True):
        if enc_file and key_file:
            try:
                # Parse key file
                password, padding, original_filename = parse_key_file(key_file)
                
                # Process decryption
                encrypted_data = enc_file.read()
                decrypted_data = hybrid_decrypt(encrypted_data, password, padding)
                
                # Download result
                st.success("Decryption Complete!")
                st.download_button(
                    label="Download Decrypted File",
                    data=decrypted_data,
                    file_name=original_filename,
                    mime="application/octet-stream"
                )
                
                # Clean up temporary files
                key_file.close()
                enc_file.close()
                del password, padding
                
            except Exception as e:
                st.error(f"Decryption failed: {str(e)}")
        else:
            st.warning("Please upload both encrypted file and key file")

st.markdown("---")
st.caption("ℹ️ Key file contains password, padding value, and original filename. Store securely!")