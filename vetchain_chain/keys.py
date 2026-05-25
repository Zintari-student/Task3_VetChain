"""ECDSA secp256k1 — generowanie kluczy, podpis, weryfikacja, adresy."""

import hashlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature


CURVE = ec.SECP256K1()


def generate_keypair() -> tuple[bytes, bytes]:
    """Zwraca (priv_pem, pub_pem) jako bytes."""
    priv = ec.generate_private_key(CURVE)
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def priv_from_pem(priv_pem: bytes):
    return serialization.load_pem_private_key(priv_pem, password=None)


def pub_from_pem(pub_pem: bytes):
    return serialization.load_pem_public_key(pub_pem)


def priv_to_hex(priv_pem: bytes) -> str:
    priv = priv_from_pem(priv_pem)
    if not isinstance(priv, ec.EllipticCurvePrivateKey):
        raise TypeError("Klucz prywatny musi być EC secp256k1.")
    raw = priv.private_numbers().private_value.to_bytes(32, "big")
    return raw.hex()


def priv_from_hex(hex_str: str) -> bytes:
    """Hex 32-bajtowego scalara → priv_pem."""
    raw = bytes.fromhex(hex_str.strip().removeprefix("0x"))
    if len(raw) != 32:
        raise ValueError(f"Hex klucza prywatnego musi mieć 64 znaki ({len(raw)*2} dostarczone).")
    secret = int.from_bytes(raw, "big")
    priv = ec.derive_private_key(secret, CURVE)
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def pub_pem_from_priv(priv_pem: bytes) -> bytes:
    priv = priv_from_pem(priv_pem)
    return priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def derive_address(pub_pem: bytes) -> str:
    """Adres = '0x' + 20-bajtowy SHA-256 z surowego klucza publicznego (hex)."""
    pub = pub_from_pem(pub_pem)
    raw = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    digest = hashlib.sha256(raw).digest()
    return "0x" + digest[:20].hex()


def address_from_priv(priv_pem: bytes) -> str:
    return derive_address(pub_pem_from_priv(priv_pem))


def sign(priv_pem: bytes, data: bytes) -> str:
    priv = priv_from_pem(priv_pem)
    if not isinstance(priv, ec.EllipticCurvePrivateKey):
        raise TypeError("Klucz prywatny musi być EC secp256k1.")
    sig = priv.sign(data, ec.ECDSA(hashes.SHA256()))
    return sig.hex()


def verify(pub_pem: bytes, data: bytes, sig_hex: str) -> bool:
    pub = pub_from_pem(pub_pem)
    if not isinstance(pub, ec.EllipticCurvePublicKey):
        return False
    try:
        pub.verify(bytes.fromhex(sig_hex), data, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False
