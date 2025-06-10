# ... existing code ...

# ==============================================
# Cryptography (Stage 4)
# ==============================================
import os
import struct
import hashlib
import getpass
from math import ceil
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

# Blowfish Implementation (from provided file)
# ... [Insert entire Blowfish.py content here] ...

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
            encrypt_file(input_file, output_file, password)
            print("Criptografia Blowfish concluída com sucesso!")
            return True
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
            decrypt_file(input_file, output_file, password)
            print("Descriptografia Blowfish concluída com sucesso!")
            return True
        except Exception as e:
            print(f"Erro na descriptografia: {e}")
            return False

    @staticmethod
    def generate_rsa_keys():
        key_dir = "crypto_keys"
        os.makedirs(key_dir, exist_ok=True)
        
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        
        with open(os.path.join(key_dir, "private.pem"), "wb") as f:
            f.write(private_key)
        
        with open(os.path.join(key_dir, "public.pem"), "wb") as f:
            f.write(public_key)
        
        print(f"Chaves RSA geradas e salvas em {key_dir}/")
        return True

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
            # Generate random AES key
            aes_key = get_random_bytes(32)  # 256-bit key
            
            # Encrypt file with AES
            iv = get_random_bytes(16)
            cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
            
            with open(input_file, 'rb') as f:
                plaintext = f.read()
            
            padded_data = pad(plaintext, AES.block_size)
            ciphertext = cipher_aes.encrypt(padded_data)
            
            # Encrypt AES key with RSA
            with open(public_key_file, 'rb') as f:
                public_key = RSA.import_key(f.read())
            
            rsa_cipher = PKCS1_OAEP.new(public_key)
            enc_aes_key = rsa_cipher.encrypt(aes_key)
            
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
            
            # Decrypt AES key with RSA
            with open(private_key_file, 'rb') as f:
                private_key = RSA.import_key(f.read())
            
            rsa_cipher = PKCS1_OAEP.new(private_key)
            aes_key = rsa_cipher.decrypt(enc_aes_key)
            
            # Decrypt file with AES
            cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher_aes.decrypt(ciphertext), AES.block_size)
            
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
            print("4. Parte IV - Criptografia")  # New option
            print("5. Sair")
            print("="*50)
            
            choice = input("Selecione uma opção: ").strip()
            
            if choice == "1":
                MenuSystem.part1_menu()
            elif choice == "2":
                MenuSystem.part2_menu()
            elif choice == "3":
                MenuSystem.part3_menu()
            elif choice == "4":  # New cryptography menu
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

# ... rest of existing code ...