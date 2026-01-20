"""Testes principais do EnvLoader."""

from pathlib import Path

import pytest

from django_env_loader import EnvConfig, EnvLoader, SecretNotFoundError, ValidationError


class TestEnvLoaderBasics:
    """Testes básicos do EnvLoader."""

    def test_singleton_pattern(self):
        """Testa que EnvLoader implementa Singleton."""
        loader1 = EnvLoader()
        loader2 = EnvLoader()
        assert loader1 is loader2

    def test_load_from_env_file(self, temp_env_file):
        """Testa carregamento de arquivo .env."""
        config = EnvConfig(env_file=temp_env_file)
        loader = EnvLoader(config)

        assert loader.get("TEST_VAR") == "test_value"
        assert loader.get_bool("DEBUG") is True
        assert loader.get_int("PORT") == 8080

    def test_get_with_default(self):
        """Testa obtenção com valor padrão."""
        loader = EnvLoader()
        value = loader.get("NONEXISTENT_VAR", default="default_value")
        assert value == "default_value"

    def test_get_required_not_found(self):
        """Testa erro ao buscar variável obrigatória inexistente."""
        loader = EnvLoader()

        with pytest.raises(SecretNotFoundError) as exc_info:
            loader.get("REQUIRED_VAR", required=True)

        assert "REQUIRED_VAR" in str(exc_info.value)
        assert exc_info.value.key == "REQUIRED_VAR"

    def test_get_from_environment(self, monkeypatch):
        """Testa obtenção de variável de ambiente."""
        monkeypatch.setenv("MY_VAR", "env_value")
        loader = EnvLoader()
        assert loader.get("MY_VAR") == "env_value"


class TestDockerSecrets:
    """Testes para Docker secrets."""

    def test_get_from_secret_file(self, temp_secrets_dir):
        """Testa leitura de Docker secret."""
        config = EnvConfig(secrets_dir=temp_secrets_dir)
        loader = EnvLoader(config)
        password = loader.get("DB_PASSWORD", use_secrets=True)
        assert password == "secret123"

    def test_secret_fallback_to_env(self, temp_secrets_dir, monkeypatch):
        """Testa fallback de secret para env var."""
        monkeypatch.setenv("FALLBACK_VAR", "from_env")
        config = EnvConfig(secrets_dir=temp_secrets_dir)
        loader = EnvLoader(config)
        value = loader.get("FALLBACK_VAR", use_secrets=True)
        assert value == "from_env"

    def test_secret_cache(self, temp_secrets_dir):
        """Testa cache de secrets."""
        config = EnvConfig(secrets_dir=temp_secrets_dir, cache_secrets=True)
        loader = EnvLoader(config)

        value1 = loader.get("API_KEY", use_secrets=True)
        (temp_secrets_dir / "API_KEY").unlink()
        value2 = loader.get("API_KEY", use_secrets=True)

        assert value1 == value2 == "api_key_value"

    def test_clear_cache(self, temp_secrets_dir):
        """Testa limpeza do cache."""
        config = EnvConfig(secrets_dir=temp_secrets_dir, cache_secrets=True)
        loader = EnvLoader(config)
        loader.get("API_KEY", use_secrets=True)
        loader.clear_cache()
        (temp_secrets_dir / "API_KEY").unlink()

        with pytest.raises(SecretNotFoundError):
            loader.get("API_KEY", required=True, use_secrets=True)


class TestTypeConversions:
    """Testes para conversões de tipo."""

    def test_get_bool_conversions(self, monkeypatch):
        """Testa conversão de booleanos."""
        loader = EnvLoader()

        monkeypatch.setenv("TRUE_VAR", "true")
        assert loader.get_bool("TRUE_VAR") is True

        monkeypatch.setenv("FALSE_VAR", "0")
        assert loader.get_bool("FALSE_VAR") is False

    def test_get_int_conversions(self, monkeypatch):
        """Testa conversão de inteiros."""
        loader = EnvLoader()
        monkeypatch.setenv("INT_VAR", "42")
        assert loader.get_int("INT_VAR") == 42

    def test_get_float_conversions(self, monkeypatch):
        """Testa conversão de floats."""
        loader = EnvLoader()
        monkeypatch.setenv("FLOAT_VAR", "3.14")
        assert loader.get_float("FLOAT_VAR") == pytest.approx(3.14)

    def test_get_list_conversions(self, monkeypatch):
        """Testa conversão de listas."""
        loader = EnvLoader()
        monkeypatch.setenv("LIST_VAR", "a,b,c")
        assert loader.get_list("LIST_VAR") == ["a", "b", "c"]

    def test_get_dict_conversions(self, monkeypatch):
        """Testa conversão de dicionários."""
        loader = EnvLoader()
        monkeypatch.setenv("DICT_VAR", "key1=val1,key2=val2")
        assert loader.get_dict("DICT_VAR") == {"key1": "val1", "key2": "val2"}


class TestValidation:
    """Testes para validação customizada."""

    def test_custom_validator_success(self, monkeypatch):
        """Testa validador customizado bem-sucedido."""
        loader = EnvLoader()
        monkeypatch.setenv("EMAIL", "test@example.com")

        def validate_email(value: str) -> str:
            if "@" not in value:
                raise ValueError("Email inválido")
            return value.lower()

        email = loader.get_with_validator("EMAIL", validate_email)
        assert email == "test@example.com"

    def test_custom_validator_failure_strict_mode(self, monkeypatch):
        """Testa validador falho em strict mode."""
        config = EnvConfig(strict_mode=True)
        loader = EnvLoader(config)
        monkeypatch.setenv("EMAIL", "invalid")

        def validate_email(value: str) -> str:
            if "@" not in value:
                raise ValueError("Email inválido")
            return value

        with pytest.raises(ValidationError) as exc_info:
            loader.get_with_validator("EMAIL", validate_email)

        assert "EMAIL" in str(exc_info.value)

    def test_custom_validator_failure_non_strict(self, monkeypatch):
        """Testa validador falho sem strict mode."""
        config = EnvConfig(strict_mode=False)
        loader = EnvLoader(config)
        monkeypatch.setenv("EMAIL", "invalid")

        def validate_email(value: str) -> str:
            if "@" not in value:
                raise ValueError("Email inválido")
            return value

        result = loader.get_with_validator("EMAIL", validate_email, default="default@example.com")
        assert result == "default@example.com"


class TestPrefixSupport:
    """Testes para suporte a prefixos."""

    def test_prefix_in_key(self, monkeypatch):
        """Testa uso de prefixo nas chaves."""
        config = EnvConfig(prefix="MYAPP_")
        loader = EnvLoader(config)
        monkeypatch.setenv("MYAPP_VAR", "value")

        assert loader.get("VAR") == "value"
        assert loader.get("MYAPP_VAR") == "value"

    def test_get_all_with_prefix(self, monkeypatch):
        """Testa get_all com filtro de prefixo."""
        config = EnvConfig(prefix="APP_")
        loader = EnvLoader(config)

        monkeypatch.setenv("APP_VAR1", "val1")
        monkeypatch.setenv("APP_VAR2", "val2")
        monkeypatch.setenv("OTHER_VAR", "other")

        all_vars = loader.get_all()

        assert "APP_VAR1" in all_vars
        assert "APP_VAR2" in all_vars
        assert "OTHER_VAR" not in all_vars


class TestUtilityMethods:
    """Testes para métodos utilitários."""

    def test_is_set_true(self, monkeypatch):
        """Testa is_set com variável definida."""
        loader = EnvLoader()
        monkeypatch.setenv("EXISTING_VAR", "value")
        assert loader.is_set("EXISTING_VAR") is True

    def test_is_set_false(self):
        """Testa is_set com variável não definida."""
        loader = EnvLoader()
        assert loader.is_set("NONEXISTENT_VAR") is False

    def test_is_set_empty_string(self, monkeypatch):
        """Testa is_set com string vazia."""
        loader = EnvLoader()
        monkeypatch.setenv("EMPTY_VAR", "")
        assert loader.is_set("EMPTY_VAR") is False

    def test_get_all(self, monkeypatch):
        """Testa obtenção de todas as variáveis."""
        loader = EnvLoader()
        monkeypatch.setenv("VAR1", "val1")
        monkeypatch.setenv("VAR2", "val2")

        all_vars = loader.get_all()
        assert "VAR1" in all_vars
        assert "VAR2" in all_vars


class TestStrictMode:
    """Testes para strict mode."""

    def test_strict_mode_missing_env_file(self):
        """Testa erro em strict mode com arquivo ausente."""
        config = EnvConfig(env_file=Path("nonexistent.env"), strict_mode=True)

        with pytest.raises(FileNotFoundError):
            EnvLoader(config)

    def test_non_strict_mode_missing_env_file(self):
        """Testa warning sem strict mode com arquivo ausente."""
        config = EnvConfig(env_file=Path("nonexistent.env"), strict_mode=False)
        loader = EnvLoader(config)
        assert loader is not None
