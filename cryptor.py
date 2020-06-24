""" Cryptography module to enc/dec private keys"""
import rncryptor
from base64 import b64encode, b64decode


def encrypt(string_to_encrypt: str, password: str) -> str:
    return b64encode(rncryptor.RNCryptor().encrypt(data=string_to_encrypt, password=password)).decode('utf-8')


def decrypt(encrypted_string: str, password: str) -> str:
    return rncryptor.RNCryptor().decrypt(b64decode(encrypted_string.encode('utf-8')), password=password)
