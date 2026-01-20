# Guia de Uso - Django Env Loader

Este guia fornece exemplos práticos e detalhados de como usar o `django-env-loader` em diferentes cenários.

## Índice

- [Instalação](#instalação)
- [Configuração Básica](#configuração-básica)
- [Uso com Django](#uso-com-django)
- [Docker Secrets](#docker-secrets)
- [Conversão de Tipos](#conversão-de-tipos)
- [Validação Customizada](#validação-customizada)
- [Casos de Uso Avançados](#casos-de-uso-avançados)
- [Testes](#testes)
- [Boas Práticas](#boas-práticas)

---

## Instalação

```bash
# Instalação básica
pip install django-env-loader

# Com suporte Django
pip install django-env-loader[django]
```

---

## Configuração Básica

### Importação Simples (Singleton Padrão)

A forma mais simples e recomendada é usar a instância singleton pré-configurada:

```python
# Importa instância singleton pronta para uso
from django_env_loader import env_loader

# Obtém variáveis
api_key = env_loader.get("API_KEY", required=True)
debug = env_loader.get_bool("DEBUG", default=False)
port = env_loader.get_int("PORT", default=8000)
```

### Criação Manual com Configuração Customizada

```python
from django_env_loader import EnvLoader, EnvConfig
from pathlib import Path

# Configuração customizada
config = EnvConfig(
    env_file=Path(".env.production"),
    prefix="MYAPP_",
    strict_mode=True,
    cache_secrets=True,
)

loader = EnvLoader(config)
```

### Arquivo .env

Crie um arquivo `.env` na raiz do projeto:

```bash
# .env
DEBUG=true
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
API_KEY=your-api-key
PORT=8000
```

**Importante:** Adicione `.env` ao `.gitignore`!

```bash
# .gitignore
.env
.env.*
!.env.example
```

---

## Uso com Django

### Configuração Rápida do settings.py

```python
# settings.py
from django_env_loader import env_loader

# Ou use o DjangoEnvLoader especializado:
# from django_env_loader import DjangoEnvLoader
# env_loader = DjangoEnvLoader()

# Configurações básicas
SECRET_KEY = env_loader.get("SECRET_KEY", required=True)
DEBUG = env_loader.get_bool("DEBUG", default=False)
ALLOWED_HOSTS = env_loader.get_list("ALLOWED_HOSTS", default=["localhost"])

# Database
DATABASE_URL = env_loader.get("DATABASE_URL", required=True)
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

# Email
EMAIL_HOST = env_loader.get("EMAIL_HOST", default="localhost")
EMAIL_PORT = env_loader.get_int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env_loader.get_bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env_loader.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env_loader.get("EMAIL_HOST_PASSWORD", use_secrets=True)

# Cache
REDIS_HOST = env_loader.get("REDIS_HOST", default="localhost")
REDIS_PORT = env_loader.get_int("REDIS_PORT", default=6379)
REDIS_DB = env_loader.get_int("REDIS_DB", default=0)
```

### DjangoEnvLoader com Helpers Especializados

```python
# settings.py
from django_env_loader import DjangoEnvLoader

env = DjangoEnvLoader()

# Helpers especializados
SECRET_KEY = env.get_secret_key()  # Sempre obrigatória
DEBUG = env.get_debug(default=False)
ALLOWED_HOSTS = env.get_allowed_hosts()  # Default: ["localhost", "127.0.0.1"]
DATABASE_URL = env.get_database_url()  # Valida formato automaticamente
```

### Múltiplos Ambientes

```python
# settings.py
import os
from pathlib import Path
from django_env_loader import EnvLoader, EnvConfig

# Determina o ambiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
BASE_DIR = Path(__file__).resolve().parent.parent
env_file = BASE_DIR / f".env.{ENVIRONMENT}"

# Configura o loader
config = EnvConfig(
    env_file=env_file if env_file.exists() else None,
    strict_mode=(ENVIRONMENT == "production"),
)

env = EnvLoader(config)

# Configurações específicas do ambiente
DEBUG = env.get_bool("DEBUG", default=(ENVIRONMENT == "development"))
```

---

## Docker Secrets

### Como Funciona

O loader busca variáveis nesta ordem:
1. **Docker secrets** (`/run/secrets/VAR_NAME`)
2. **Variáveis de ambiente** (`VAR_NAME`)
3. **Valor padrão** (se fornecido)

### Exemplo com Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    image: myapp:latest
    secrets:
      - db_password
      - secret_key
      - api_key
    environment:
      - DEBUG=false
      - DATABASE_HOST=db
      - DATABASE_PORT=5432

secrets:
  db_password:
    file: ./secrets/db_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
  api_key:
    external: true  # Secret gerenciado pelo Docker Swarm
```

```python
# settings.py
from django_env_loader import env_loader

# Busca automaticamente em /run/secrets/ primeiro
DB_PASSWORD = env_loader.get("db_password", required=True, use_secrets=True)
SECRET_KEY = env_loader.get("secret_key", required=True, use_secrets=True)
API_KEY = env_loader.get("api_key", required=True, use_secrets=True)

# Variáveis de ambiente normais
DEBUG = env_loader.get_bool("DEBUG", default=False)
DB_HOST = env_loader.get("DATABASE_HOST", default="localhost")
```

### Criando Secrets Localmente (Desenvolvimento)

```bash
# Cria diretório de secrets
mkdir -p secrets

# Cria secrets
echo "my-super-secret-key" > secrets/secret_key.txt
echo "db-password-123" > secrets/db_password.txt

# Protege os arquivos
chmod 600 secrets/*
```

```python
# settings.py (desenvolvimento)
from pathlib import Path
from django_env_loader import EnvLoader, EnvConfig

config = EnvConfig(secrets_dir=Path("secrets"))
env = EnvLoader(config)

SECRET_KEY = env.get("secret_key", required=True, use_secrets=True)
```

---

## Conversão de Tipos

### Booleanos

```python
from django_env_loader import env_loader

# Valores aceitos como True:
# "true", "1", "yes", "y", "on", "t", "sim", "s"
DEBUG = env_loader.get_bool("DEBUG", default=False)
MAINTENANCE_MODE = env_loader.get_bool("MAINTENANCE_MODE", default=False)
EMAIL_USE_TLS = env_loader.get_bool("EMAIL_USE_TLS", default=True)

# Valores aceitos como False:
# "false", "0", "no", "n", "off", "f", "não", "nao", "" (vazio)
FEATURE_ENABLED = env_loader.get_bool("NEW_FEATURE", default=False)
```

### Inteiros e Floats

```python
# Inteiros
PORT = env_loader.get_int("PORT", default=8000)
MAX_CONNECTIONS = env_loader.get_int("MAX_CONNECTIONS", default=100)
TIMEOUT = env_loader.get_int("TIMEOUT", default=30)

# Floats
TAX_RATE = env_loader.get_float("TAX_RATE", default=0.15)
CACHE_TTL = env_loader.get_float("CACHE_TTL", default=60.0)
```

### Listas

```python
# Formato: item1,item2,item3
ALLOWED_HOSTS = env_loader.get_list("ALLOWED_HOSTS", default=["localhost"])

# .env:
# ALLOWED_HOSTS=example.com,api.example.com,www.example.com
# Resultado: ["example.com", "api.example.com", "www.example.com"]

# Delimitador customizado
ADMIN_EMAILS = env_loader.get_list("ADMIN_EMAILS", delimiter=";")

# .env:
# ADMIN_EMAILS=admin1@example.com;admin2@example.com
```

### Dicionários

```python
# Formato: key1=value1,key2=value2
DB_OPTIONS = env_loader.get_dict("DB_OPTIONS")

# .env:
# DB_OPTIONS=connect_timeout=30,pool_size=10,ssl_mode=require
# Resultado: {"connect_timeout": "30", "pool_size": "10", "ssl_mode": "require"}

# Delimitador customizado
FEATURE_FLAGS = env_loader.get_dict("FEATURE_FLAGS", delimiter=";")

# .env:
# FEATURE_FLAGS=new_ui=true;beta_api=false;analytics=true
```

---

## Validação Customizada

### Validador de Email

```python
from django_env_loader import env_loader

def validate_email(value: str) -> str:
    """Valida formato de email."""
    if "@" not in value or "." not in value.split("@")[1]:
        raise ValueError(f"Email inválido: {value}")
    return value.lower()

ADMIN_EMAIL = env_loader.get_with_validator(
    "ADMIN_EMAIL",
    validator=validate_email,
    required=True
)
```

### Validador de URL

```python
def validate_url(value: str) -> str:
    """Valida e normaliza URL."""
    if not value.startswith(("http://", "https://")):
        raise ValueError("URL deve começar com http:// ou https://")
    return value.rstrip("/")  # Remove trailing slash

API_BASE_URL = env_loader.get_with_validator(
    "API_BASE_URL",
    validator=validate_url,
    required=True
)
```

### Validador de Data

```python
from datetime import datetime

def parse_date(value: str) -> datetime:
    """Parse data no formato ISO."""
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"Data inválida. Use formato ISO: {value}")

LAUNCH_DATE = env_loader.get_with_validator(
    "LAUNCH_DATE",
    validator=parse_date,
    default=datetime.now()
)
```

### Validador de Faixa Numérica

```python
def validate_port(value: str) -> int:
    """Valida que porta está entre 1024 e 65535."""
    port = int(value)
    if not 1024 <= port <= 65535:
        raise ValueError(f"Porta deve estar entre 1024 e 65535, recebido: {port}")
    return port

PORT = env_loader.get_with_validator(
    "PORT",
    validator=validate_port,
    default=8000
)
```

---

## Casos de Uso Avançados

### Configuração Multi-serviço com Prefixos

```python
from django_env_loader import EnvLoader, EnvConfig

# Configuração de Email
email_config = EnvConfig(prefix="EMAIL_")
email_loader = EnvLoader(email_config)

EMAIL_CONFIG = {
    "backend": "django.core.mail.backends.smtp.EmailBackend",
    "host": email_loader.get("HOST", default="localhost"),
    "port": email_loader.get_int("PORT", default=587),
    "username": email_loader.get("USERNAME"),
    "password": email_loader.get("PASSWORD", use_secrets=True),
    "use_tls": email_loader.get_bool("USE_TLS", default=True),
    "timeout": email_loader.get_int("TIMEOUT", default=30),
}

# Configuração de Redis
redis_config = EnvConfig(prefix="REDIS_")
redis_loader = EnvLoader(redis_config)

REDIS_CONFIG = {
    "host": redis_loader.get("HOST", default="localhost"),
    "port": redis_loader.get_int("PORT", default=6379),
    "db": redis_loader.get_int("DB", default=0),
    "password": redis_loader.get("PASSWORD", use_secrets=True),
}

# .env:
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USERNAME=user@gmail.com
# REDIS_HOST=redis
# REDIS_PORT=6379
```

### Feature Flags

```python
from django_env_loader import env_loader

# Define feature flags em um dict
FEATURE_FLAGS = env_loader.get_dict("FEATURE_FLAGS")

# .env:
# FEATURE_FLAGS=new_ui=true,beta_api=false,analytics=true,payments_v2=false

# Uso no código
def is_feature_enabled(feature_name: str) -> bool:
    """Verifica se feature está habilitada."""
    return FEATURE_FLAGS.get(feature_name, "false").lower() == "true"

# Views
if is_feature_enabled("new_ui"):
    return render(request, "new_template.html")
else:
    return render(request, "old_template.html")
```

### Configuração Condicional por Ambiente

```python
import os
from django_env_loader import env_loader

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Configurações que mudam por ambiente
if ENVIRONMENT == "production":
    DEBUG = False
    ALLOWED_HOSTS = env_loader.get_list("ALLOWED_HOSTS", required=True)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env_loader.get("DB_NAME", required=True),
            'USER': env_loader.get("DB_USER", required=True),
            'PASSWORD': env_loader.get("DB_PASSWORD", required=True, use_secrets=True),
            'HOST': env_loader.get("DB_HOST", required=True),
            'PORT': env_loader.get_int("DB_PORT", default=5432),
        }
    }
elif ENVIRONMENT == "staging":
    DEBUG = env_loader.get_bool("DEBUG", default=False)
    ALLOWED_HOSTS = env_loader.get_list("ALLOWED_HOSTS", default=["staging.example.com"])
    # Configuração de staging...
else:  # development
    DEBUG = True
    ALLOWED_HOSTS = ["*"]
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }
    }
```

---

## Testes

### Fixture Básica

```python
# conftest.py
import pytest
from django_env_loader import EnvLoader

@pytest.fixture
def env_loader():
    """Cria loader limpo para cada teste."""
    EnvLoader.reset_singleton()
    loader = EnvLoader()
    yield loader
    EnvLoader.reset_singleton()
```

### Testando com Monkeypatch

```python
# test_settings.py
def test_debug_mode(env_loader, monkeypatch):
    """Testa modo debug."""
    monkeypatch.setenv("DEBUG", "true")
    assert env_loader.get_bool("DEBUG") is True

def test_database_url(env_loader, monkeypatch):
    """Testa configuração de banco."""
    db_url = "postgresql://user:pass@localhost/testdb"
    monkeypatch.setenv("DATABASE_URL", db_url)

    assert env_loader.get("DATABASE_URL") == db_url

def test_allowed_hosts_list(env_loader, monkeypatch):
    """Testa lista de hosts permitidos."""
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

    hosts = env_loader.get_list("ALLOWED_HOSTS")
    assert hosts == ["localhost", "127.0.0.1", "testserver"]
```

### Testando Variáveis Obrigatórias

```python
from django_env_loader import SecretNotFoundError

def test_required_variable_missing(env_loader):
    """Testa erro quando variável obrigatória não existe."""
    with pytest.raises(SecretNotFoundError) as exc_info:
        env_loader.get("NONEXISTENT_VAR", required=True)

    assert "NONEXISTENT_VAR" in str(exc_info.value)
    assert exc_info.value.key == "NONEXISTENT_VAR"
```

---

## Boas Práticas

### 1. Use .env.example como Template

```bash
# .env.example (commite este arquivo)
DEBUG=false
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=change-me-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
API_KEY=your-api-key-here
```

### 2. Valide Configurações no Startup

```python
# apps.py ou manage.py
from django.core.exceptions import ImproperlyConfigured
from django_env_loader import env_loader, SecretNotFoundError

def validate_settings():
    """Valida configurações obrigatórias no startup."""
    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "ALLOWED_HOSTS",
    ]

    missing = []
    for var in required_vars:
        if not env_loader.is_set(var):
            missing.append(var)

    if missing:
        raise ImproperlyConfigured(
            f"Configurações obrigatórias faltando: {', '.join(missing)}"
        )

# Execute no startup
validate_settings()
```

### 3. Use Strict Mode em Produção

```python
import os
from django_env_loader import EnvLoader, EnvConfig

is_production = os.getenv("ENVIRONMENT") == "production"

config = EnvConfig(
    strict_mode=is_production,  # Erros fatais em produção
    warn_on_missing=not is_production,  # Warnings apenas em dev
)

env = EnvLoader(config)
```

### 4. Organize por Seções

```python
# settings.py

# ==========================================
# CORE SETTINGS
# ==========================================
SECRET_KEY = env_loader.get("SECRET_KEY", required=True)
DEBUG = env_loader.get_bool("DEBUG", default=False)
ALLOWED_HOSTS = env_loader.get_list("ALLOWED_HOSTS")

# ==========================================
# DATABASE
# ==========================================
DATABASE_URL = env_loader.get("DATABASE_URL", required=True)
DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}

# ==========================================
# CACHE
# ==========================================
REDIS_HOST = env_loader.get("REDIS_HOST", default="localhost")
REDIS_PORT = env_loader.get_int("REDIS_PORT", default=6379)

# ==========================================
# EMAIL
# ==========================================
EMAIL_HOST = env_loader.get("EMAIL_HOST", default="localhost")
EMAIL_PORT = env_loader.get_int("EMAIL_PORT", default=587)
```

### 5. Documente Variáveis de Ambiente

```python
# settings.py

"""
Variáveis de Ambiente Requeridas:
- SECRET_KEY: Chave secreta do Django (obrigatória)
- DATABASE_URL: URL de conexão do banco (obrigatória)
- ALLOWED_HOSTS: Lista de hosts permitidos (opcional, default: localhost)

Variáveis de Ambiente Opcionais:
- DEBUG: Modo debug (default: false)
- EMAIL_HOST: Servidor SMTP (default: localhost)
- REDIS_HOST: Servidor Redis (default: localhost)
"""
```

---

## Troubleshooting

### Variável Não Encontrada

```python
# Verifique se a variável está definida
if env_loader.is_set("MY_VAR"):
    value = env_loader.get("MY_VAR")
else:
    print("MY_VAR não está definida")

# Ou use default para evitar erros
value = env_loader.get("MY_VAR", default="fallback_value")
```

### Erro de Conversão de Tipo

```python
from django_env_loader import ValidationError, EnvConfig, EnvLoader

# Use strict_mode=False para logs em vez de exceções
config = EnvConfig(strict_mode=False)
loader = EnvLoader(config)

# Tentará converter, mas retorna default se falhar
port = loader.get_int("PORT", default=8000)
```

### Cache de Secrets Desatualizado

```python
# Limpa cache manualmente se necessário
env_loader.clear_cache()

# Ou desabilite cache
config = EnvConfig(cache_secrets=False)
loader = EnvLoader(config)
```

---

## Recursos Adicionais

- [README.md](../README.md) - Documentação principal
- [API Reference](../README.md#api-reference) - Referência completa da API
- [Exemplos](../examples/) - Projetos de exemplo
- [Issues](https://github.com/yourusername/django-env-loader/issues) - Reporte bugs

---

**Desenvolvido por [Felipe Abreu](mailto:felipeabreu.rj@gmail.com)**