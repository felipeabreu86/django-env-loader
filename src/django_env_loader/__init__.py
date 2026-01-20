"""Django Env Loader - Gerenciamento de variáveis de ambiente."""

from django_env_loader.exceptions import EnvLoaderError, SecretNotFoundError, ValidationError
from django_env_loader.loader import DjangoEnvLoader, EnvConfig, EnvLoader

__version__ = "1.0.5"
__all__ = [
    "EnvLoader",
    "DjangoEnvLoader",
    "EnvConfig",
    "EnvLoaderError",
    "SecretNotFoundError",
    "ValidationError",
    "env_loader",
]

# Instância singleton padrão para importação direta
# Uso: from django_env_loader import env_loader
env_loader = EnvLoader()
