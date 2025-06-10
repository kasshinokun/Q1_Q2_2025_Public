import os
import struct
import hashlib
import getpass
from math import ceil

# Imports for cryptography library
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

# Placeholder for Blowfish Implementation.
# IMPORTANT: The actual Blowfish encryption/decryption functions (encrypt_file, decrypt_file)
# are assumed to be provided externally, as they were not part of the snippet.
# These are placeholder definitions to allow the code to run without error.
# If you have the Blowfish.py content, replace these placeholders with it.
def encrypt_file(input_file, output_file, password):
    print("Blowfish encrypt_file: Implementação Blowfish não fornecida. Nenhuma ação realizada.")
    raise NotImplementedError("Implementação Blowfish não fornecida.")

def decrypt_file(input_file, output_file, password):
    print("Blowfish decrypt_file: Implementação Blowfish não fornecida. Nenhuma ação realizada.")
    raise NotImplementedError("Implementação Blowfish não fornecida.")


class CryptographyHandler:
    @staticmethod
    def blowfish_encrypt_file():
        input_file = input("Caminho do arquivo de entrada: ").strip()
        output_file = input("Caminho do arquivo de saída: ").strip()
        password = getpass.getpass("Senha: ")
        
        if not os.path.exists(input_file):
            print("Arquivo de entrada não encontrado!")
            return False
        
        try:
            # This relies on the external Blowfish implementation
            encrypt_file(input_file, output_file, password)
            print("Criptografia Blowfish concluída com sucesso!")
            return True
        except NotImplementedError:
            print("Erro: A implementação do Blowfish não está disponível.")
            return False
        except Exception as e:
            print(f"Erro na criptografia: {e}")
            return False

    @staticmethod
    def blowfish_decrypt_file():
        input_file = input("Caminho do arquivo criptografado: ").strip()
        output_file = input("Caminho do arquivo descriptografado: ").strip()
        password = getpass.getpass("Senha: ")
        
        if not os.path.exists(input_file):
            print("Arquivo de entrada não encontrado!")
            return False
        
        try:
            # This relies on the external Blowfish implementation
            decrypt_file(input_file, output_file, password)
            print("Descriptografia Blowfish concluída com sucesso!")
            return True
        except NotImplementedError:
            print("Erro: A implementação do Blowfish não está disponível.")
            return False
        except Exception as e:
            print(f"Erro na descriptografia: {e}")
            return False

    @staticmethod
    def generate_rsa_keys():
        key_dir = "crypto_keys"
        os.makedirs(key_dir, exist_ok=True)
        
        try:
            # Generate RSA private key using cryptography
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Get public key from private key
            public_key = private_key.public_key()
            
            # Serialize private key to PEM format
            # For a real application, consider using BestAvailableEncryption for password protection
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Serialize public key to PEM format
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            with open(os.path.join(key_dir, "private.pem"), "wb") as f:
                f.write(private_pem)
            
            with open(os.path.join(key_dir, "public.pem"), "wb") as f:
                f.write(public_pem)
            
            print(f"Chaves RSA geradas e salvas em {key_dir}/")
            return True
        except Exception as e:
            print(f"Erro ao gerar chaves RSA: {e}")
            return False

    @staticmethod
    def hybrid_encrypt_file():
        input_file = input("Caminho do arquivo de entrada: ").strip()
        output_file = input("Caminho do arquivo de saída: ").strip()
        public_key_file = input("Caminho da chave pública RSA: ").strip()
        
        if not os.path.exists(input_file):
            print("Arquivo de entrada não encontrado!")
            return False
        if not os.path.exists(public_key_file):
            print("Arquivo de chave pública não encontrado!")
            return False
        
        try:
            # Generate random AES key (256-bit) using os.urandom
            aes_key = os.urandom(32)
            # Generate random IV (128-bit for AES CBC) using os.urandom
            iv = os.urandom(16)
            
            # Encrypt file with AES using cryptography
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            
            with open(input_file, 'rb') as f:
                plaintext = f.read()
            
            # Apply PKCS7 padding using cryptography
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(plaintext) + padder.finalize()
            
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # Encrypt AES key with RSA using cryptography
            with open(public_key_file, 'rb') as f:
                public_key_bytes = f.read()
                public_key = serialization.load_pem_public_key(
                    public_key_bytes,
                    backend=default_backend()
                )
            
            # Encrypt AES key with OAEP padding
            enc_aes_key = public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Write output file
            with open(output_file, 'wb') as f:
                f.write(struct.pack('>I', len(enc_aes_key)))
                f.write(enc_aes_key)
                f.write(iv)
                f.write(ciphertext)
            
            print("Criptografia híbrida concluída com sucesso!")
            return True
        except Exception as e:
            print(f"Erro na criptografia híbrida: {e}")
            return False

    @staticmethod
    def hybrid_decrypt_file():
        input_file = input("Caminho do arquivo criptografado: ").strip()
        output_file = input("Caminho do arquivo descriptografado: ").strip()
        private_key_file = input("Caminho da chave privada RSA: ").strip()
        
        if not os.path.exists(input_file):
            print("Arquivo de entrada não encontrado!")
            return False
        if not os.path.exists(private_key_file):
            print("Arquivo de chave privada não encontrado!")
            return False
        
        try:
            with open(input_file, 'rb') as f:
                # Read encrypted AES key
                key_len = struct.unpack('>I', f.read(4))[0]
                enc_aes_key = f.read(key_len)
                iv = f.read(16)
                ciphertext = f.read()
            
            # Decrypt AES key with RSA using cryptography
            with open(private_key_file, 'rb') as f:
                private_key_bytes = f.read()
                private_key = serialization.load_pem_private_key(
                    private_key_bytes,
                    password=None, # Assuming no password on private key, adjust if needed
                    backend=default_backend()
                )
            
            # Decrypt AES key with OAEP padding
            aes_key = private_key.decrypt(
                enc_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Decrypt file with AES using cryptography
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Unpad PKCS7 data using cryptography
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
            
            with open(output_file, 'wb') as f:
                f.write(decrypted_data)
            
            print("Descriptografia híbrida concluída com sucesso!")
            return True
        except Exception as e:
            print(f"Erro na descriptografia híbrida: {e}")
            return False


# ==============================================
# Updated Menu System
# ==============================================
class MenuSystem:
    @staticmethod
    def main_menu():
        while True:
            print("\n" + "="*50)
            print("Sistema de Gerenciamento de Acidentes de Trânsito")
            print("="*50)
            print("1. Parte I - Gerenciamento de Dados")
            print("2. Parte II - Indexação e Busca")
            print("3. Parte III - Compactação de Dados")
            print("4. Parte IV - Criptografia")
            print("5. Sair")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                MenuSystem.part1_menu()
            elif choice == "2":
                MenuSystem.part2_menu()
            elif choice == "3":
                MenuSystem.part3_menu()
            elif choice == "4":
                MenuSystem.part4_menu()
            elif choice == "5":
                print("Saindo do sistema...")
                return
            else:
                print("Opção inválida. Tente novamente.")

    @staticmethod
    def part4_menu():
        """Display Part 4 menu for cryptography operations"""
        while True:
            print("\n" + "="*50)
            print("Parte IV - Criptografia")
            print("="*50)
            print("1. Criptografar arquivo (Blowfish)")
            print("2. Descriptografar arquivo (Blowfish)")
            print("3. Gerar chaves RSA")
            print("4. Criptografia Híbrida (AES + RSA) - Criptografar")
            print("5. Criptografia Híbrida (AES + RSA) - Descriptografar")
            print("6. Voltar ao menu principal")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                CryptographyHandler.blowfish_encrypt_file()
            elif choice == "2":
                CryptographyHandler.blowfish_decrypt_file()
            elif choice == "3":
                CryptographyHandler.generate_rsa_keys()
            elif choice == "4":
                CryptographyHandler.hybrid_encrypt_file()
            elif choice == "5":
                CryptographyHandler.hybrid_decrypt_file()
            elif choice == "6":
                return
            else:
                print("Opção inválida. Tente novamente.")

# --- DUMMY PLACEHOLDER FUNCTIONS FOR MENU CALLS ---
# These functions would typically be implemented in other parts of the application
# or in files that are imported. They are included here as placeholders
# to make this standalone file runnable and to demonstrate the menu structure.

def part1_menu():
    print("Menu da Parte I (Gerenciamento de Dados) - Implementação não incluída neste arquivo.")
    input("Pressione Enter para continuar...")

def part2_menu():
    print("Menu da Parte II (Indexação e Busca) - Implementação não incluída neste arquivo.")
    input("Pressione Enter para continuar...")

def part3_menu():
    print("Menu da Parte III (Compactação de Dados) - Implementação não incluída neste arquivo.")
    input("Pressione Enter para continuar...")

# --- Main Application Entry Point ---
if __name__ == "__main__":
    # Ensure a dummy directory for keys exists if running standalone
    os.makedirs("crypto_keys", exist_ok=True)
    MenuSystem.main_menu()