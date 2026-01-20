"""Testes para DjangoEnvLoader."""

import pytest

from django_env_loader import DjangoEnvLoader, EnvConfig, SecretNotFoundError, ValidationError


class TestDjangoEnvLoader:
    """Testes para DjangoEnvLoader."""

    def test_initialization_with_django_prefix(self):
        """Testa inicialização com prefixo Django."""
        loader = DjangoEnvLoader()
        assert loader.config.prefix == "DJANGO_"

    def test_initialization_with_custom_config(self):
        """Testa inicialização com config customizada."""
        config = EnvConfig(prefix="CUSTOM_")
        loader = DjangoEnvLoader(config)
        assert loader.config.prefix == "CUSTOM_"

    def test_get_secret_key_success(self, monkeypatch):
        """Testa obtenção de SECRET_KEY."""
        loader = DjangoEnvLoader()
        monkeypatch.setenv("DJANGO_SECRET_KEY", "my-secret-key-123")

        secret_key = loader.get_secret_key()
        assert secret_key == "my-secret-key-123"

    def test_get_secret_key_required(self):
        """Testa que SECRET_KEY é obrigatória."""
        loader = DjangoEnvLoader()

        with pytest.raises(SecretNotFoundError) as exc_info:
            loader.get_secret_key()

        assert "SECRET_KEY" in str(exc_info.value)

    def test_get_debug_default_false(self):
        """Testa que DEBUG padrão é False."""
        loader = DjangoEnvLoader()
        assert loader.get_debug() is False

    def test_get_debug_from_env(self, monkeypatch):
        """Testa obtenção de DEBUG do ambiente."""
        loader = DjangoEnvLoader()
        monkeypatch.setenv("DJANGO_DEBUG", "true")
        assert loader.get_debug() is True

    def test_get_allowed_hosts_default(self):
        """Testa ALLOWED_HOSTS padrão."""
        loader = DjangoEnvLoader()
        hosts = loader.get_allowed_hosts()
        assert hosts == ["localhost", "127.0.0.1"]

    def test_get_allowed_hosts_from_env(self, monkeypatch):
        """Testa ALLOWED_HOSTS do ambiente."""
        loader = DjangoEnvLoader()
        monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com,api.example.com")

        hosts = loader.get_allowed_hosts()
        assert hosts == ["example.com", "api.example.com"]

    def test_get_database_url_success(self, monkeypatch):
        """Testa obtenção de DATABASE_URL válida."""
        loader = DjangoEnvLoader()
        monkeypatch.setenv("DJANGO_DATABASE_URL", "postgresql://user:pass@localhost/db")

        url = loader.get_database_url()
        assert url == "postgresql://user:pass@localhost/db"

    def test_get_database_url_validation_failure(self, monkeypatch):
        """Testa validação de DATABASE_URL inválida."""
        loader = DjangoEnvLoader()
        monkeypatch.setenv("DJANGO_DATABASE_URL", "invalid-url")

        with pytest.raises(ValidationError) as exc_info:
            loader.get_database_url()

        assert "DATABASE_URL" in str(exc_info.value)
        assert "://" in str(exc_info.value)

    def test_get_database_url_with_default(self):
        """Testa DATABASE_URL com valor padrão."""
        loader = DjangoEnvLoader()
        url = loader.get_database_url(default="sqlite:///db.sqlite3")
        assert url == "sqlite:///db.sqlite3"

    def test_get_database_url_required_when_no_default(self):
        """Testa que DATABASE_URL é obrigatória sem default."""
        loader = DjangoEnvLoader()

        with pytest.raises(SecretNotFoundError):
            loader.get_database_url()


class TestDjangoIntegration:
    """Testes de integração com Django."""

    def test_typical_django_settings(self, monkeypatch):
        """Testa configuração típica do Django."""
        loader = DjangoEnvLoader()

        monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret-key-123")
        monkeypatch.setenv("DJANGO_DEBUG", "false")
        monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com,www.example.com")
        monkeypatch.setenv("DJANGO_DATABASE_URL", "postgresql://user:pass@db:5432/mydb")

        SECRET_KEY = loader.get_secret_key()
        DEBUG = loader.get_debug()
        ALLOWED_HOSTS = loader.get_allowed_hosts()
        DATABASE_URL = loader.get_database_url()

        assert SECRET_KEY == "test-secret-key-123"
        assert DEBUG is False
        assert ALLOWED_HOSTS == ["example.com", "www.example.com"]
        assert DATABASE_URL == "postgresql://user:pass@db:5432/mydb"

    def test_development_vs_production(self, monkeypatch):
        """Testa diferença entre dev e prod."""
        # Development
        DjangoEnvLoader.reset_singleton()
        dev_loader = DjangoEnvLoader()
        monkeypatch.setenv("DJANGO_DEBUG", "true")
        monkeypatch.setenv("DJANGO_SECRET_KEY", "dev-key")

        assert dev_loader.get_debug() is True

        # Production
        DjangoEnvLoader.reset_singleton()
        prod_loader = DjangoEnvLoader()
        monkeypatch.setenv("DJANGO_DEBUG", "false")
        monkeypatch.setenv("DJANGO_SECRET_KEY", "prod-key")

        assert prod_loader.get_debug() is False
