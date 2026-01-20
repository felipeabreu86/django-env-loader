from typing import Any

# ============================================================================
# Exceções customizadas
# ============================================================================


class EnvLoaderError(Exception):
    """Classe base para exceções do EnvLoader."""


class SecretNotFoundError(EnvLoaderError):
    """Exceção levantada quando um secret obrigatório não é encontrado."""

    def __init__(self, key: str, /, searched_locations: list[str] | None = None):
        self.key = key
        self.searched_locations = searched_locations or []
        locations = ", ".join(self.searched_locations) if self.searched_locations else "padrão"
        super().__init__(f"Secret '{key}' não encontrado. Locais buscados: {locations}")


class ValidationError(EnvLoaderError):
    """Exceção levantada quando a validação de uma variável falha."""

    def __init__(self, key: str, value: Any, reason: str):
        self.key = key
        self.value = value
        self.reason = reason
        super().__init__(f"Validação falhou para '{key}': {reason} (valor: {value!r})")
