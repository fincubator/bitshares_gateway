import pytest

from rncryptor import DecryptionError
from cryptor import encrypt, decrypt


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
