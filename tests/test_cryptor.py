import pytest
import os

from rncryptor import DecryptionError

from src.cryptor import encrypt, decrypt, get_wallet_keys, save_wallet_keys
from config import project_root_dir


def test_crypto_types():
    start_string = "some_secret_string"
    test_password = "testpassword"
    encrypted_string = encrypt(start_string, test_password)
    final_string = decrypt(encrypted_string, test_password)
    assert type(encrypted_string) is type(final_string)


def test_crypto_success():
    start_string = "some_secret_string"
    test_password = "testpassword"
    encrypted_string = encrypt(start_string, test_password)
    final_string = decrypt(encrypted_string, test_password)
    assert start_string == final_string


def test_crypto_wrong_pass():
    start_string = "some_secret_string"
    test_password = "testpassword"
    encrypted_string = encrypt(start_string, test_password)
    with pytest.raises(DecryptionError):
        decrypt(encrypted_string, "wrongpassword")


def test_secret_file_write_and_read():
    account_name = "test_acc"
    active_key = "active_key_1"
    memo_key = "memo_key_2"
    test_password = "testpassword"
    enc_key_1 = encrypt(active_key, test_password)
    enc_key_2 = encrypt(memo_key, test_password)

    saved = save_wallet_keys(account_name, enc_key_1, enc_key_2)

    assert saved

    enc_keys = get_wallet_keys(account_name)

    for key_type, key in enc_keys.items():
        if key_type == "active":
            assert active_key == decrypt(key, test_password)
        elif key_type == "memo":
            assert memo_key == decrypt(key, test_password)
        else:
            raise

    os.remove(f"{project_root_dir}/config/.{account_name}.keys")
