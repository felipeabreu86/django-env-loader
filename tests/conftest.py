"""Configuração compartilhada para testes."""

import tempfile

from pathlib import Path

import pytest

from django_env_loader import DjangoEnvLoader, EnvLoader


@pytest.fixture(autouse=True)
def reset_env_loader():
    """Reset singleton antes e depois de cada teste."""
    EnvLoader.reset_singleton()
    yield
    EnvLoader.reset_singleton()


@pytest.fixture
def env_loader():
    """Fixture que fornece EnvLoader limpo."""
    EnvLoader.reset_singleton()
    return EnvLoader()


@pytest.fixture
def django_env_loader():
    """Fixture que fornece DjangoEnvLoader limpo."""
    DjangoEnvLoader.reset_singleton()
    return DjangoEnvLoader()


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset do singleton antes de cada teste."""
    DjangoEnvLoader.reset_singleton()
    yield
    DjangoEnvLoader.reset_singleton()


@pytest.fixture
def temp_env_file():
    """Cria arquivo .env temporário para testes."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TEST_VAR=test_value\n")
        f.write("DEBUG=true\n")
        f.write("PORT=8080\n")
        f.write("HOSTS=localhost,127.0.0.1\n")
        f.write("OPTIONS=key1=val1,key2=val2\n")
        temp_path = Path(f.name)

    yield temp_path
    temp_path.unlink()


@pytest.fixture
def temp_secrets_dir():
    """Cria diretório temporário para secrets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        secrets_dir = Path(temp_dir)
        (secrets_dir / "DB_PASSWORD").write_text("secret123")
        (secrets_dir / "API_KEY").write_text("api_key_value")
        yield secrets_dir
