"""
pytest configuration for BugsBuzzy Backend tests.
This file sets up the test environment without requiring a .env file.
"""
import os
import pytest


# Set default environment variables for tests before Django settings are loaded
# These will only be set if not already present in the environment
def pytest_configure(config):
    """Configure pytest and set default environment variables for testing."""
    
    # Set test environment variables with defaults
    test_env_defaults = {
        'DJANGO_SECRET_KEY': 'test-secret-key-for-pytest-12345678901234567890',
        'DJANGO_DEBUG': 'True',  # Changed to True for better test output
        'DATABASE_URL': 'sqlite:///:memory:',
        'DJANGO_ALLOWED_HOSTS': 'localhost,testserver',
        'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend',
        'ACCESS_TOKEN_LIFETIME_MINUTES': '60',
        'REFRESH_TOKEN_LIFETIME_DAYS': '7',
    }
    
    # Only set if not already present (don't override existing env vars)
    for key, value in test_env_defaults.items():
        if key not in os.environ:
            os.environ[key] = value


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Give all tests access to the database.
    This is a convenience fixture to avoid having to add @pytest.mark.django_db to every test.
    """
    pass
