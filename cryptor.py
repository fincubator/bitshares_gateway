""" Cryptography module to enc/dec private keys"""
import rncryptor
from base64 import b64encode, b64decode

from config import project_root_dir


def encrypt(string_to_encrypt: str, password: str) -> str:
    return b64encode(rncryptor.RNCryptor().encrypt(data=string_to_encrypt, password=password)).decode('utf-8')


def decrypt(encrypted_string: str, password: str) -> str:
    return rncryptor.RNCryptor().decrypt(b64decode(encrypted_string.encode('utf-8')), password=password)


def get_wallet_keys(account_name: str) -> dict:
    keys = {}
    try:
        with open(f"{project_root_dir}/config/.{account_name}.keys", "r") as secret_file:
            keys_string = secret_file.read()
            for key_param in keys_string.split('\n'):
                key_type, key = key_param.split(":")
                keys[key_type] = key
    except FileNotFoundError:
        pass
    finally:
        return keys


def save_wallet_keys(account_name: str, active_key: str, memo_key: str) -> bool:
    """
    Save wallet's keys in config/.account_name.keys file

    :param account_name: Just BitShares account name
    :param active_key: Already base64-encoded encrypted active private key of account_name
    :param memo_key: Already base64-encoded encrypted memo private key of account_name
    """
    with open(f"{project_root_dir}/config/.{account_name}.keys", "w") as secret_file:
        secret_file.write(
            f"active:{active_key}\n"
            f"memo:{memo_key}"
        )
    return True
