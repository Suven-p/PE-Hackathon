"""
Unit tests for URL business logic (app/models/url.py).
These tests exercise pure functions only — no database, no Flask context required.
"""
import string

import pytest

from app.models.url import generate_short_code, is_valid_url, create_short_url


class TestIsValidUrl:
    def test_valid_http(self):
        assert is_valid_url("http://example.com") is True

    def test_valid_https(self):
        assert is_valid_url("https://example.com") is True

    def test_valid_with_path_and_query(self):
        assert is_valid_url("https://example.com/path?q=1&lang=en") is True

    def test_valid_with_subdomain(self):
        assert is_valid_url("https://sub.example.co.uk/page") is True

    def test_empty_string(self):
        assert is_valid_url("") is False

    def test_no_scheme(self):
        assert is_valid_url("example.com") is False

    def test_scheme_only(self):
        assert is_valid_url("https://") is False

    def test_non_string_none(self):
        assert is_valid_url(None) is False

    def test_random_string(self):
        assert is_valid_url("not-a-url") is False

    def test_ftp_scheme_is_valid(self):
        # urlparse accepts any scheme with a netloc
        assert is_valid_url("ftp://files.example.com") is True


class TestGenerateShortCode:
    def test_default_length_is_six(self):
        assert len(generate_short_code()) == 6

    def test_custom_length(self):
        assert len(generate_short_code(10)) == 10

    def test_only_alphanumeric_characters(self):
        valid_chars = set(string.ascii_letters + string.digits)
        code = generate_short_code(50)
        assert all(c in valid_chars for c in code)

    def test_codes_are_not_all_identical(self):
        # With a 6-char alphanumeric space (62^6 ≈ 56 billion), collisions in
        # 200 samples would be astronomically unlikely.
        codes = {generate_short_code() for _ in range(200)}
        assert len(codes) > 190


class TestCreateShortUrlValidation:
    """
    Only test the validation paths that raise ValueError before touching the DB.
    Happy-path tests live in test_api_urls.py (integration tests).
    """

    def test_empty_url_raises_value_error(self):
        with pytest.raises(ValueError, match="URL must start with"):
            create_short_url("", title="Test Title")

    def test_invalid_url_raises_value_error(self):
        with pytest.raises(ValueError):
            create_short_url("not-a-url", title="Test Title")

    def test_missing_title_raises_value_error(self):
        with pytest.raises(ValueError, match="Title is required"):
            create_short_url("https://example.com", title=None)

    def test_empty_title_raises_value_error(self):
        with pytest.raises(ValueError, match="Title is required"):
            create_short_url("https://example.com", title="")

    def test_title_too_long_raises_value_error(self):
        with pytest.raises(ValueError, match="Title too long"):
            create_short_url("https://example.com", title="x" * 256)
