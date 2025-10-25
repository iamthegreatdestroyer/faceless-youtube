#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for staging environment.

This script creates:
- cert.pem: Self-signed certificate valid for 365 days
- key.pem: Private key (RSA 4096-bit)
- certs/ directory: Where certificates are stored

Usage: python generate_certificates.py
"""

import os
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_self_signed_cert(
    cert_dir: str = "certs",
    cert_filename: str = "cert.pem",
    key_filename: str = "key.pem",
    days_valid: int = 365,
) -> tuple[str, str]:
    """
    Generate a self-signed SSL certificate and private key.

    Args:
        cert_dir: Directory to store certificates
        cert_filename: Certificate filename
        key_filename: Private key filename
        days_valid: Days until certificate expiration

    Returns:
        Tuple of (cert_path, key_path)
    """
    # Create certs directory if it doesn't exist
    os.makedirs(cert_dir, exist_ok=True)

    cert_path = os.path.join(cert_dir, cert_filename)
    key_path = os.path.join(cert_dir, key_filename)

    print("🔐 Generating Self-Signed SSL Certificate")
    print(f"   Directory: {cert_dir}")
    print(f"   Certificate: {cert_filename}")
    print(f"   Private Key: {key_filename}")
    print(f"   Validity: {days_valid} days")

    # Generate private key
    print("\n  → Generating private key (RSA 4096-bit)...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    # Generate certificate
    print("  → Generating certificate...")
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Faceless YouTube"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=days_valid))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.DNSName("*.localhost"),
                    x509.DNSName("127.0.0.1"),
                ]
            ),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Write certificate to file
    print("  → Writing certificate to file...")
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # Write private key to file
    print("  → Writing private key to file...")
    with open(key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Set restrictive permissions on private key
    os.chmod(key_path, 0o600)
    print(f"  → Set private key permissions to 0600")

    # Verify files were created
    if os.path.exists(cert_path) and os.path.exists(key_path):
        cert_size = os.path.getsize(cert_path)
        key_size = os.path.getsize(key_path)
        print(f"\n✓ Certificates generated successfully!")
        print(f"  • {cert_path} ({cert_size} bytes)")
        print(f"  • {key_path} ({key_size} bytes)")
        return cert_path, key_path
    else:
        raise FileNotFoundError("Failed to create certificate files")


def display_cert_info(cert_path: str) -> None:
    """Display certificate information."""
    print(f"\n📋 Certificate Information:")
    print(f"   Path: {cert_path}")

    from cryptography import x509

    with open(cert_path, "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read())

    print(f"   Subject: {cert.subject.rfc4514_string()}")
    print(f"   Issuer: {cert.issuer.rfc4514_string()}")
    print(f"   Valid From: {cert.not_valid_before}")
    print(f"   Valid Until: {cert.not_valid_after}")
    print(f"   Serial: {cert.serial_number}")

    # Show SANs
    try:
        san_ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        san_names = [name.value for name in san_ext.value]
        print(f"   SANs: {', '.join(san_names)}")
    except x509.ExtensionNotFound:
        pass


if __name__ == "__main__":
    try:
        cert_path, key_path = generate_self_signed_cert()
        display_cert_info(cert_path)
        print(
            "\n✅ SSL certificates ready for staging deployment\n"
            "   Next: Configure nginx and update docker-compose.staging.yml"
        )
    except Exception as e:
        print(f"\n❌ Error generating certificates: {e}")
        exit(1)
