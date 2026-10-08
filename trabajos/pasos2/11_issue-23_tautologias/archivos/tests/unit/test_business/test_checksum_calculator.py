"""
Tests unitarios para checksum_calculator.

Los valores esperados son SHA-256 publicados (fuente independiente del código),
no se calculan con hashlib dentro del test.
"""

from app.business.domain.checksum_calculator import calculate_checksum

SHA256_HELLO_WORLD = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
SHA256_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestCalculateChecksum:
    def test_returns_sha256_of_known_input(self):
        assert calculate_checksum(b"hello world") == SHA256_HELLO_WORLD

    def test_returns_sha256_of_empty_input(self):
        assert calculate_checksum(b"") == SHA256_EMPTY

    def test_different_content_produces_different_checksum(self):
        assert calculate_checksum(b"file_a") != calculate_checksum(b"file_b")

    def test_handles_large_input(self):
        result = calculate_checksum(b"x" * 10_000_000)  # 10 MB

        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)
