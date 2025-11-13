import pytest
from unittest.mock import patch

from accounts import utils


def test_normalize_email_trims_and_lowercases():
    assert utils.normalize_email("  USER@Example.com  ") == "user@example.com"


def test_generate_verification_code_range():
    for _ in range(10):
        code = utils.generate_verification_code()
        assert 100000 <= code <= 999999


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1234567891", True),
        ("1234567890", False),
        ("abcdefghij", False),
        ("123", False),
    ],
)
def test_validate_national_code_variants(value, expected):
    assert utils.validate_national_code(value) is expected


@patch("accounts.utils.send_mail")
@patch("accounts.utils.render_to_string", return_value="<p>code</p>")
def test_send_verification_email_success(mock_render, mock_send_mail):
    mock_send_mail.return_value = 1

    result = utils.send_verification_email("user@example.com", 123456)

    assert result is True
    mock_render.assert_called_once()
    mock_send_mail.assert_called_once()


@patch("accounts.utils.send_mail", side_effect=Exception("boom"))
@patch("accounts.utils.render_to_string", return_value="<p>code</p>")
def test_send_verification_email_failure(mock_render, mock_send_mail):
    result = utils.send_verification_email("user@example.com", 123456)

    assert result is False
    mock_render.assert_called_once()
    mock_send_mail.assert_called_once()
