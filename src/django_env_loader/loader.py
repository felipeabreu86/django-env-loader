"""Pacote para gerenciamento de variáveis de ambiente e secrets.

Este módulo fornece uma interface type-safe e extensível para carregar e validar
variáveis de ambiente, com suporte especial para Docker secrets e integração Django.
"""

from __future__ import annotations

import logging
import os
import warnings

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar, overload

from dotenv import load_dotenv

from django_env_loader.exceptions import SecretNotFoundError, ValidationError

__version__ = "1.0.0"
__all__ = ["EnvLoader", "EnvConfig", SecretNotFoundError, ValidationError]

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# Configuração
# ============================================================================


@dataclass
class EnvConfig:
    """Configuração para o EnvLoader.

    Attributes:
        env_file: Caminho para arquivo .env (None = auto-detect)
        secrets_dir: Diretório base para Docker secrets (padrão: /run/secrets)
        encoding: Encoding para leitura de arquivos
        prefix: Prefixo para filtrar variáveis (ex: 'DJANGO_')
        override_existing: Se deve sobrescrever variáveis já definidas
        auto_cast: Se deve tentar conversão automática de tipos
        cache_secrets: Se deve cachear secrets lidos de arquivos
        strict_mode: Se deve levantar exceções em vez de warnings
        warn_on_missing: Se deve emitir warnings para variáveis não encontradas
    """

    env_file: Path | str | None = None
    secrets_dir: Path = field(default_factory=lambda: Path("/run/secrets"))
    encoding: str = "utf-8"
    prefix: str = ""
    override_existing: bool = False
    auto_cast: bool = True
    cache_secrets: bool = True
    strict_mode: bool = False
    warn_on_missing: bool = True

    def __post_init__(self) -> None:
        """Valida e normaliza a configuração."""
        if self.env_file is not None:
            self.env_file = Path(self.env_file)
        if isinstance(self.secrets_dir, str):
            self.secrets_dir = Path(self.secrets_dir)


# ============================================================================
# Conversores de tipo
# ============================================================================


class TypeConverter:
    """Conversor type-safe de valores de ambiente."""

    @staticmethod
    def to_bool(value: str | bool) -> bool:
        """Converte string para boolean de forma segura."""
        if isinstance(value, bool):
            return value

        if not isinstance(value, str):
            raise ValidationError("boolean", value, "Tipo inválido, esperado str ou bool")

        normalized = value.lower().strip()

        if normalized in {"true", "1", "yes", "y", "on", "t", "sim", "s"}:
            return True
        if normalized in {"false", "0", "no", "n", "off", "f", "não", "nao", ""}:
            return False

        raise ValidationError("boolean", value, f"Valor inválido para bool: '{value}'")

    @staticmethod
    def to_int(value: str | int) -> int:
        """Converte string para inteiro."""
        if isinstance(value, int):
            return value
        try:
            return int(str(value).strip())
        except (ValueError, TypeError) as e:
            raise ValidationError("int", value, str(e)) from e

    @staticmethod
    def to_float(value: str | float) -> float:
        """Converte string para float."""
        if isinstance(value, float):
            return value
        try:
            return float(str(value).strip())
        except (ValueError, TypeError) as e:
            raise ValidationError("float", value, str(e)) from e

    @staticmethod
    def to_list(value: str | list[str], delimiter: str = ",") -> list[str]:
        """Converte string delimitada em lista."""
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [item.strip() for item in str(value).split(delimiter) if item.strip()]

    @staticmethod
    def to_dict(value: str | dict[str, str], delimiter: str = ",") -> dict[str, str]:
        """Converte string 'key=value,key2=value2' em dicionário."""
        if isinstance(value, dict):
            return value
        if not value:
            return {}

        result: dict[str, str] = {}
        for item in str(value).split(delimiter):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                result[k.strip()] = v.strip()
            elif item:
                result[item] = ""
        return result


# ============================================================================
# EnvLoader Principal
# ============================================================================


class EnvLoader:
    """Gerenciador robusto de variáveis de ambiente e secrets.

    Fornece interface type-safe para carregar, validar e converter variáveis
    de ambiente e Docker secrets com suporte a cache e validação customizada.

    Exemplo:
        >>> loader = EnvLoader()
        >>> db_host = loader.get("DATABASE_URL", required=True)
        >>> debug = loader.get_bool("DEBUG", default=False)
        >>> allowed_hosts = loader.get_list("ALLOWED_HOSTS", default=[])
    """

    _instance: EnvLoader | None = None
    _initialized: bool = False

    def __new__(cls, config: EnvConfig | None = None) -> EnvLoader:
        """Implementa padrão Singleton (opcional)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: EnvConfig | None = None) -> None:
        """Inicializa o loader com configuração opcional.

        Args:
            config: Configuração customizada (None = configuração padrão)
        """
        # Evita reinicialização no padrão Singleton
        if self._initialized:
            return

        self.config = config or EnvConfig()
        self._secrets_cache: dict[str, str] = {}
        self._load_env_file()
        self._initialized = True

    def _load_env_file(self) -> None:
        """Carrega arquivo .env se especificado."""
        if self.config.env_file:
            env_path = Path(self.config.env_file)
            if env_path.is_file():
                load_dotenv(
                    env_path,
                    override=self.config.override_existing,
                    encoding=self.config.encoding,
                )
                logger.debug(f"Arquivo .env carregado: {env_path}")
            else:
                msg = f"Arquivo .env não encontrado: {env_path}"
                if self.config.strict_mode:
                    raise FileNotFoundError(msg)
                logger.warning(msg)
        else:
            load_dotenv(override=self.config.override_existing, encoding=self.config.encoding)

    def _get_prefixed_key(self, key: str) -> str:
        """Retorna a chave com prefixo aplicado."""
        return (
            f"{self.config.prefix}{key}"
            if self.config.prefix and not key.startswith(self.config.prefix)
            else key
        )

    def _read_secret_file(self, secret_path: Path) -> str | None:
        """Lê conteúdo de arquivo secret com tratamento de erros."""
        try:
            if not secret_path.exists():
                return None

            content = secret_path.read_text(encoding=self.config.encoding).strip()
            path_str = str(secret_path)

            if self.config.cache_secrets:
                self._secrets_cache[path_str] = content  # ← Armazena pelo caminho

            logger.debug(f"Secret lido: {secret_path}")
            return content

        except (OSError, PermissionError) as e:
            logger.error(f"Erro ao ler secret {secret_path}: {e}")
            if self.config.strict_mode:
                raise
            return None

    def _get_from_secret(self, key: str) -> str | None:
        """Tenta obter valor de Docker secret."""
        secret_path = self.config.secrets_dir / key
        path_str = str(secret_path)

        # Verifica cache primeiro (pelo caminho do arquivo)
        if self.config.cache_secrets and path_str in self._secrets_cache:
            return self._secrets_cache[path_str]

        # Tenta ler do arquivo secret
        return self._read_secret_file(secret_path)

    def _get_from_env(self, key: str) -> str | None:
        """Obtém valor de variável de ambiente."""
        prefixed_key = self._get_prefixed_key(key)
        return os.environ.get(prefixed_key)

    @overload
    def get(self, key: str, *, default: T, required: bool = False) -> str | T: ...

    @overload
    def get(self, key: str, *, default: None = None, required: bool = True) -> str: ...

    def get(
        self,
        key: str,
        *,
        default: T | None = None,
        required: bool = False,
        use_secrets: bool = True,
    ) -> str | T:
        """Obtém variável de ambiente ou secret.

        Args:
            key: Nome da variável (sem prefixo)
            default: Valor padrão se não encontrado
            required: Se True, levanta SecretNotFoundError se não encontrado
            use_secrets: Se deve buscar em Docker secrets

        Returns:
            Valor da variável ou default

        Raises:
            SecretNotFoundError: Se required=True e variável não encontrada
        """
        value: str | None = None
        searched: list[str] = []

        # Busca em secrets primeiro
        if use_secrets:
            value = self._get_from_secret(key)
            searched.append(f"secret:{self.config.secrets_dir / key}")

        # Fallback para variável de ambiente
        if value is None:
            value = self._get_from_env(key)
            searched.append(f"env:{self._get_prefixed_key(key)}")

        # Validação
        if value is None or not value.strip():
            if required:
                raise SecretNotFoundError(key, searched)

            if self.config.warn_on_missing and default is None:
                warnings.warn(f"Variável '{key}' não encontrada", UserWarning, stacklevel=2)

            return default if default is not None else ""

        return value

    def get_bool(
        self,
        key: str,
        *,
        default: bool = False,
        required: bool = False,
        use_secrets: bool = True,
    ) -> bool:
        """Obtém variável como boolean."""
        value = self.get(key, default=str(default), required=required, use_secrets=use_secrets)
        try:
            return TypeConverter.to_bool(value)
        except ValidationError as e:
            if self.config.strict_mode:
                raise
            logger.warning(f"Erro ao converter '{key}' para bool: {e}. Usando default: {default}")
            return default

    def get_int(
        self,
        key: str,
        *,
        default: int = 0,
        required: bool = False,
        use_secrets: bool = True,
    ) -> int:
        """Obtém variável como inteiro."""
        value = self.get(key, default=str(default), required=required, use_secrets=use_secrets)
        try:
            return TypeConverter.to_int(value)
        except ValidationError as e:
            if self.config.strict_mode:
                raise
            logger.warning(f"Erro ao converter '{key}' para int: {e}. Usando default: {default}")
            return default

    def get_float(
        self,
        key: str,
        *,
        default: float = 0.0,
        required: bool = False,
        use_secrets: bool = True,
    ) -> float:
        """Obtém variável como float."""
        value = self.get(key, default=str(default), required=required, use_secrets=use_secrets)
        try:
            return TypeConverter.to_float(value)
        except ValidationError as e:
            if self.config.strict_mode:
                raise
            logger.warning(f"Erro ao converter '{key}' para float: {e}. Usando default: {default}")
            return default

    def get_list(
        self,
        key: str,
        *,
        default: list[str] | None = None,
        delimiter: str = ",",
        required: bool = False,
        use_secrets: bool = True,
    ) -> list[str]:
        """Obtém variável como lista."""
        if default is None:
            default = []

        # Tenta obter a variável sem valor padrão
        value = self.get(key, default=None, required=False, use_secrets=use_secrets)

        if value is None or value == "":
            # Variável não existe ou é string vazia
            if required:
                raise SecretNotFoundError(key, [])
            return default

        # Variável existe, converte para lista
        return TypeConverter.to_list(value, delimiter)

    def get_dict(
        self,
        key: str,
        *,
        default: dict[str, str] | None = None,
        delimiter: str = ",",
        required: bool = False,
        use_secrets: bool = True,
    ) -> dict[str, str]:
        """Obtém variável como dicionário."""
        if default is None:
            default = {}

        # Tenta obter a variável sem valor padrão
        value = self.get(key, default=None, required=False, use_secrets=use_secrets)

        if value is None or value == "":
            # Variável não existe ou é string vazia
            if required:
                raise SecretNotFoundError(key, [])
            return default

        # Variável existe, converte para dicionário
        return TypeConverter.to_dict(value, delimiter)

    def get_with_validator(
        self,
        key: str,
        validator: Callable[[str], T],
        *,
        default: T | None = None,
        required: bool = False,
        use_secrets: bool = True,
    ) -> T | None:
        """Obtém variável com validação customizada.

        Args:
            key: Nome da variável
            validator: Função que valida/converte o valor
            default: Valor padrão
            required: Se é obrigatória
            use_secrets: Se deve buscar em secrets

        Returns:
            Valor validado ou default
        """
        value = self.get(key, default=None, required=required, use_secrets=use_secrets)
        if value is None:
            return default

        try:
            return validator(value)
        except Exception as e:
            if self.config.strict_mode:
                raise ValidationError(key, value, str(e)) from e
            logger.warning(f"Validação falhou para '{key}': {e}. Usando default")
            return default

    def is_set(self, key: str, *, use_secrets: bool = True) -> bool:
        """Verifica se variável está definida e não vazia."""
        try:
            value = self.get(key, required=False, use_secrets=use_secrets)
            return bool(value and str(value).strip())
        except Exception:
            return False

    def get_all(self, *, include_secrets: bool = False) -> dict[str, str]:
        """Retorna todas as variáveis carregadas.

        Args:
            include_secrets: Se deve incluir secrets em cache

        Returns:
            Dicionário com todas as variáveis
        """
        result = dict(os.environ)

        if include_secrets and self.config.cache_secrets:
            result.update(self._secrets_cache)

        # Filtra por prefixo se configurado
        if self.config.prefix:
            result = {k: v for k, v in result.items() if k.startswith(self.config.prefix)}

        return result

    def clear_cache(self) -> None:
        """Limpa o cache de secrets."""
        self._secrets_cache.clear()
        logger.debug("Cache de secrets limpo")

    @classmethod
    def reset_singleton(cls) -> None:
        """Reset do singleton (útil para testes)."""
        cls._instance = None
        cls._initialized = False


# ============================================================================
# Utilitários para Django
# ============================================================================


class DjangoEnvLoader(EnvLoader):
    """Loader especializado para projetos Django.

    Fornece helpers específicos para configurações Django comuns.
    """

    def __init__(self, config: EnvConfig | None = None) -> None:
        """Inicializa com defaults para Django."""
        if config is None:
            config = EnvConfig(prefix="DJANGO_", auto_cast=True)
        super().__init__(config)

    def get_database_url(self, default: str | None = None) -> str:
        """Obtém DATABASE_URL com validação básica."""
        url = self.get("DATABASE_URL", default=default, required=default is None)
        # Validação básica de formato
        if url and "://" not in url:
            raise ValidationError(
                "DATABASE_URL", url, "URL inválida (formato esperado: scheme://...)"
            )
        return url

    def get_allowed_hosts(self) -> list[str]:
        """Obtém ALLOWED_HOSTS como lista."""
        return self.get_list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

    def get_debug(self, default: bool = False) -> bool:
        """Obtém DEBUG com segurança."""
        return self.get_bool("DEBUG", default=default)

    def get_secret_key(self) -> str:
        """Obtém SECRET_KEY (sempre obrigatória)."""
        return self.get("SECRET_KEY", required=True, use_secrets=True)
