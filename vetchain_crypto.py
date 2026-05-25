import base64
import os
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class VetChainCrypto:
    @staticmethod
    def generate_shared_key():
        """Generuje losowy klucz symetryczny (np. 256-bit AES)"""
        return os.urandom(32)

    @staticmethod
    def encrypt_visit_data(key: bytes, medical_text: str, financial_text: str) -> dict:
        """
        Szyfruje oddzielnie dane medyczne i finansowe tym samym kluczem, 
        ale z różnymi wektorami inicjalizacyjnymi (IV).
        """
        med_bytes = medical_text.encode('utf-8')
        fin_bytes = financial_text.encode('utf-8')
        
        iv_med = os.urandom(12)
        encryptor_med = Cipher(algorithms.AES(key), modes.GCM(iv_med)).encryptor()
        ciphertext_med = encryptor_med.update(med_bytes) + encryptor_med.finalize()
        
        iv_fin = os.urandom(12)
        encryptor_fin = Cipher(algorithms.AES(key), modes.GCM(iv_fin)).encryptor()
        ciphertext_fin = encryptor_fin.update(fin_bytes) + encryptor_fin.finalize()
        
        return {
            "med_data": base64.b64encode(iv_med + ciphertext_med + encryptor_med.tag).decode('utf-8'),
            "fin_data": base64.b64encode(iv_fin + ciphertext_fin + encryptor_fin.tag).decode('utf-8')
        }

    @staticmethod
    def decrypt_section(key: bytes, encoded_ciphertext: str) -> str:
        """Deszyfruje wskazaną sekcję (medyczną lub finansową)"""
        try:
            data = base64.b64decode(encoded_ciphertext.encode('utf-8'))
            iv = data[:12]
            tag = data[-16:]
            ciphertext = data[12:-16]
            
            decryptor = Cipher(algorithms.AES(key), modes.GCM(iv, tag)).decryptor()
            decrypted_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            return decrypted_bytes.decode('utf-8')
        except Exception:
            return "[⚠️ BŁĄD DESZYFROWANIA: Brak uprawnień do tej sekcji]"