# Django Env Loader

**Gerenciador robusto e type-safe de variáveis de ambiente para projetos Python e Django.**

`django-env-loader` é uma biblioteca moderna que simplifica o gerenciamento de variáveis de ambiente e Docker secrets, oferecendo validação rigorosa, conversão automática de tipos e integração nativa com Django.

---

## ✨ Características

- 🔒 **Type-safe**: Suporte completo a type hints e validação de tipos
- 🐳 **Docker Secrets**: Suporte nativo a Docker secrets com fallback automático
- ⚡ **Performance**: Sistema de cache inteligente para secrets
- 🎯 **Django-ready**: Helpers especializados para configurações Django
- 🛡️ **Validação robusta**: Conversores seguros com tratamento de erros
- 🔧 **Configurável**: Prefixos, encoding, strict mode e muito mais
- 📝 **Bem documentado**: Type hints completos e docstrings detalhadas
- 🧪 **Testado**: Cobertura de testes > 95%

---

## 📦 Instalação

```bash
pip install django-env-loader
```

Para uso com Django (instala dependências adicionais):

```bash
pip install django-env-loader[django]
```

---

## 🚀 Quick Start

### Uso básico

```python
# Forma mais simples - usa instância singleton pré-configurada
from django_env_loader import env_loader

# Obtém variáveis simples
api_key = env_loader.get("API_KEY", required=True)
debug = env_loader.get_bool("DEBUG", default=False)
port = env_loader.get_int("PORT", default=8000)

# Listas e dicionários
allowed_hosts = env_loader.get_list("ALLOWED_HOSTS", default=["localhost"])
database_options = env_loader.get_dict("DB_OPTIONS")  # FORMAT: key1=val1,key2=val2
```

**Ou crie uma instância customizada:**

```python
from django_env_loader import EnvLoader, EnvConfig
from pathlib import Path

config = EnvConfig(env_file=Path(".env.production"), prefix="MYAPP_")
loader = EnvLoader(config)
```

### Uso com Django

```python
# settings.py
# Opção 1: Singleton simples
from django_env_loader import env_loader

SECRET_KEY = env_loader.get("SECRET_KEY", required=True)
DEBUG = env_loader.get_bool("DEBUG", default=False)
ALLOWED_HOSTS = env_loader.get_list("ALLOWED_HOSTS", default=["localhost"])

# Opção 2: DjangoEnvLoader com helpers especializados
from django_env_loader import DjangoEnvLoader

env = DjangoEnvLoader()

# Configurações Django com validação automática
SECRET_KEY = env.get_secret_key()  # Obrigatória, busca em secrets primeiro
DEBUG = env.get_debug(default=False)
ALLOWED_HOSTS = env.get_allowed_hosts()
DATABASE_URL = env.get_database_url()

# Outras configurações
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

EMAIL_HOST = env.get("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.get_int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.get_bool("EMAIL_USE_TLS", default=True)
```

---

## 📚 Documentação Completa

### Configuração Avançada

O `EnvLoader` aceita uma configuração personalizada através da classe `EnvConfig`:

```python
from django_env_loader import EnvLoader, EnvConfig
from pathlib import Path

config = EnvConfig(
    env_file=Path(".env.production"),  # Arquivo .env customizado
    secrets_dir=Path("/run/secrets"),  # Diretório de Docker secrets
    encoding="utf-8",                  # Encoding dos arquivos
    prefix="MYAPP_",                   # Prefixo para todas as variáveis
    override_existing=False,           # Não sobrescreve vars já definidas
    auto_cast=True,                    # Conversão automática de tipos
    cache_secrets=True,                # Cache de secrets
    strict_mode=False,                 # False = warnings, True = exceções
    warn_on_missing=True,              # Avisa sobre variáveis não encontradas
)

loader = EnvLoader(config)
```

### Métodos de Obtenção de Variáveis

#### `get()` - Método base

```python
# Obter string simples
value = loader.get("MY_VAR", default="default_value")

# Obrigatória (levanta SecretNotFoundError se não encontrada)
value = loader.get("REQUIRED_VAR", required=True)

# Sem buscar em Docker secrets
value = loader.get("ENV_ONLY", use_secrets=False)
```

#### `get_bool()` - Booleanos

Aceita múltiplos formatos: `true/false`, `1/0`, `yes/no`, `on/off`, `sim/não`

```python
debug = loader.get_bool("DEBUG", default=False)
maintenance = loader.get_bool("MAINTENANCE_MODE", required=True)

# Valores aceitos para True
# "true", "1", "yes", "y", "on", "t", "sim", "s"

# Valores aceitos para False
# "false", "0", "no", "n", "off", "f", "não", "nao", ""
```

#### `get_int()` - Números inteiros

```python
port = loader.get_int("PORT", default=8000)
workers = loader.get_int("WORKERS", required=True)
timeout = loader.get_int("TIMEOUT", default=30)
```

#### `get_float()` - Números decimais

```python
tax_rate = loader.get_float("TAX_RATE", default=0.15)
temperature = loader.get_float("MAX_TEMP", default=98.6)
```

#### `get_list()` - Listas

```python
# Formato: item1,item2,item3
hosts = loader.get_list("ALLOWED_HOSTS", default=["localhost"])

# Delimitador customizado
emails = loader.get_list("ADMIN_EMAILS", delimiter=";")

# De variável de ambiente:
# ALLOWED_HOSTS=example.com,api.example.com,www.example.com
# Resultado: ["example.com", "api.example.com", "www.example.com"]
```

#### `get_dict()` - Dicionários

```python
# Formato: key1=value1,key2=value2
options = loader.get_dict("DB_OPTIONS")

# Delimitador customizado
config = loader.get_dict("FEATURE_FLAGS", delimiter=";")

# De variável de ambiente:
# DB_OPTIONS=timeout=30,pool_size=10,ssl=true
# Resultado: {"timeout": "30", "pool_size": "10", "ssl": "true"}
```

#### `get_with_validator()` - Validação customizada

```python
from typing import Callable
from datetime import datetime

# Validador de email
def validate_email(value: str) -> str:
    if "@" not in value:
        raise ValueError(f"Email inválido: {value}")
    return value.lower()

admin_email = loader.get_with_validator(
    "ADMIN_EMAIL",
    validator=validate_email,
    required=True
)

# Validador de data
def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value)

launch_date = loader.get_with_validator(
    "LAUNCH_DATE",
    validator=parse_date,
    default=datetime.now()
)

# Validador de URL
def validate_url(value: str) -> str:
    if not value.startswith(("http://", "https://")):
        raise ValueError(f"URL deve começar com http:// ou https://")
    return value.rstrip("/")

api_url = loader.get_with_validator(
    "API_URL",
    validator=validate_url,
    required=True
)
```

### Docker Secrets

O loader busca automaticamente em Docker secrets antes de tentar variáveis de ambiente:

```python
# Ordem de busca:
# 1. /run/secrets/DATABASE_PASSWORD (Docker secret)
# 2. DATABASE_PASSWORD (variável de ambiente)

db_password = loader.get("DATABASE_PASSWORD", required=True, use_secrets=True)
```

**Exemplo com Docker Compose:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    image: myapp:latest
    secrets:
      - db_password
      - secret_key
    environment:
      - DEBUG=false
      - DATABASE_HOST=db

secrets:
  db_password:
    file: ./secrets/db_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

```python
# settings.py
from django_env_loader import DjangoEnvLoader

env = DjangoEnvLoader()

# Busca automaticamente em /run/secrets/SECRET_KEY
SECRET_KEY = env.get_secret_key()

# Busca em /run/secrets/DATABASE_PASSWORD
db_password = env.get("DATABASE_PASSWORD", required=True)
```

### Verificação de Variáveis

```python
# Verifica se variável existe e não está vazia
if loader.is_set("FEATURE_FLAG"):
    enable_feature()

# Obtém todas as variáveis carregadas
all_vars = loader.get_all(include_secrets=False)
print(all_vars)
```

### Gerenciamento de Cache

```python
# Limpar cache de secrets (útil para recarregar valores)
loader.clear_cache()

# Reset completo do singleton (útil em testes)
from django_env_loader import EnvLoader
EnvLoader.reset_singleton()
```

---

## 🎯 Casos de Uso Comuns

### 1. Configuração Multi-ambiente

```python
# .env.development
DEBUG=true
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1

# .env.production
DEBUG=false
DATABASE_URL=postgresql://user:pass@db:5432/mydb
ALLOWED_HOSTS=myapp.com,www.myapp.com
```

```python
# settings.py
import os
from pathlib import Path
from django_env_loader import env_loader, EnvLoader, EnvConfig

# Opção 1: Usando singleton com config customizada
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
env_file = Path(f".env.{ENVIRONMENT}")

# Reconfigura o singleton (faça isso antes de qualquer uso)
EnvLoader.reset_singleton()
config = EnvConfig(env_file=env_file, strict_mode=True)
env = EnvLoader(config)

# Opção 2: Criar nova instância (não recomendado se usar singleton em outros lugares)
# config = EnvConfig(env_file=env_file, strict_mode=True)
# env = EnvLoader(config)

DEBUG = env.get_bool("DEBUG")
DATABASE_URL = env.get("DATABASE_URL", required=True)
ALLOWED_HOSTS = env.get_list("ALLOWED_HOSTS")
```

### 2. Validação de Configurações Obrigatórias

```python
from django_env_loader import env_loader, SecretNotFoundError

try:
    # Garante que variáveis críticas existem
    api_key = env_loader.get("API_KEY", required=True)
    secret_key = env_loader.get("SECRET_KEY", required=True)
    database_url = env_loader.get("DATABASE_URL", required=True)

except SecretNotFoundError as e:
    print(f"❌ Configuração faltando: {e}")
    print(f"   Locais buscados: {e.searched_locations}")
    import sys
    sys.exit(1)
```

### 3. Feature Flags

```python
# .env
FEATURE_FLAGS=new_ui=true,beta_api=false,analytics=true

# app.py
from django_env_loader import env_loader

features = env_loader.get_dict("FEATURE_FLAGS")

if features.get("new_ui") == "true":
    enable_new_ui()

if features.get("beta_api") == "true":
    enable_beta_api()
```

### 4. Configuração de Múltiplos Serviços

```python
from django_env_loader import EnvLoader, EnvConfig

# Serviço de email
email_config = EnvConfig(prefix="EMAIL_")
email_loader = EnvLoader(email_config)

EMAIL_CONFIG = {
    "host": email_loader.get("HOST", default="localhost"),
    "port": email_loader.get_int("PORT", default=587),
    "username": email_loader.get("USERNAME"),
    "password": email_loader.get("PASSWORD", use_secrets=True),
    "use_tls": email_loader.get_bool("USE_TLS", default=True),
}

# Serviço de cache
cache_config = EnvConfig(prefix="REDIS_")
cache_loader = EnvLoader(cache_config)

REDIS_CONFIG = {
    "host": cache_loader.get("HOST", default="localhost"),
    "port": cache_loader.get_int("PORT", default=6379),
    "db": cache_loader.get_int("DB", default=0),
    "password": cache_loader.get("PASSWORD", use_secrets=True),
}
```

### 5. Integração com Pydantic Settings

```python
from pydantic_settings import BaseSettings
from django_env_loader import env_loader

class Settings(BaseSettings):
    app_name: str = env_loader.get("APP_NAME", default="MyApp")
    debug: bool = env_loader.get_bool("DEBUG", default=False)
    database_url: str = env_loader.get("DATABASE_URL", required=True)
    secret_key: str = env_loader.get("SECRET_KEY", required=True)
    allowed_hosts: list[str] = env_loader.get_list("ALLOWED_HOSTS")

    class Config:
        case_sensitive = False

settings = Settings()
```

---

## 🔒 Segurança

### Boas Práticas

1. **Nunca commite arquivos `.env`** com dados sensíveis
   ```bash
   # .gitignore
   .env
   .env.*
   !.env.example
   ```

2. **Use Docker secrets** para dados sensíveis em produção
   ```python
   # Prioriza secrets sobre env vars
   secret_key = loader.get("SECRET_KEY", use_secrets=True, required=True)
   ```

3. **Valide configurações** no startup
   ```python
   # manage.py ou app startup
   from django_env_loader import DjangoEnvLoader, SecretNotFoundError

   env = DjangoEnvLoader()

   try:
       env.get_secret_key()
       env.get_database_url()
   except SecretNotFoundError as e:
       logger.critical(f"Configuração crítica faltando: {e}")
       sys.exit(1)
   ```

4. **Use strict_mode** em produção
   ```python
   config = EnvConfig(strict_mode=True)
   loader = EnvLoader(config)
   # Agora erros de validação levantam exceções em vez de warnings
   ```

---

## 🧪 Testes

### Testando código que usa EnvLoader

```python
import pytest
from django_env_loader import EnvLoader, EnvConfig
from pathlib import Path

@pytest.fixture
def loader():
    """Fixture que cria loader limpo para cada teste."""
    EnvLoader.reset_singleton()
    config = EnvConfig(env_file=Path("tests/.env.test"))
    return EnvLoader(config)

def test_get_database_url(loader, monkeypatch):
    """Testa obtenção de DATABASE_URL."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/testdb")

    url = loader.get("DATABASE_URL", required=True)
    assert url == "postgresql://localhost/testdb"

def test_missing_required_variable(loader):
    """Testa erro ao buscar variável obrigatória inexistente."""
    from django_env_loader import SecretNotFoundError

    with pytest.raises(SecretNotFoundError) as exc_info:
        loader.get("NONEXISTENT", required=True)

    assert "NONEXISTENT" in str(exc_info.value)

def test_bool_conversion(loader, monkeypatch):
    """Testa conversão de valores booleanos."""
    monkeypatch.setenv("FEATURE_ENABLED", "true")
    assert loader.get_bool("FEATURE_ENABLED") is True

    monkeypatch.setenv("FEATURE_DISABLED", "0")
    assert loader.get_bool("FEATURE_DISABLED") is False
```

---

## 📖 API Reference

### Classes Principais

#### `EnvLoader`
Gerenciador principal de variáveis de ambiente.

**Métodos:**
- `get(key, *, default, required, use_secrets)` → `str | T`
- `get_bool(key, *, default, required, use_secrets)` → `bool`
- `get_int(key, *, default, required, use_secrets)` → `int`
- `get_float(key, *, default, required, use_secrets)` → `float`
- `get_list(key, *, default, delimiter, required, use_secrets)` → `list[str]`
- `get_dict(key, *, default, delimiter, required, use_secrets)` → `dict[str, str]`
- `get_with_validator(key, validator, *, default, required, use_secrets)` → `T | None`
- `is_set(key, *, use_secrets)` → `bool`
- `get_all(*, include_secrets)` → `dict[str, str]`
- `clear_cache()` → `None`
- `reset_singleton()` → `None` (class method)

#### `DjangoEnvLoader`
Subclasse especializada para Django.

**Métodos adicionais:**
- `get_database_url(default)` → `str`
- `get_allowed_hosts()` → `list[str]`
- `get_debug(default)` → `bool`
- `get_secret_key()` → `str`

#### `EnvConfig`
Configuração do EnvLoader.

**Atributos:**
- `env_file: Path | str | None`
- `secrets_dir: Path`
- `encoding: str`
- `prefix: str`
- `override_existing: bool`
- `auto_cast: bool`
- `cache_secrets: bool`
- `strict_mode: bool`
- `warn_on_missing: bool`

### Exceções

#### `SecretNotFoundError`
Levantada quando um secret obrigatório não é encontrado.

**Atributos:**
- `key: str` - Nome da variável
- `searched_locations: list[str]` - Locais onde foi buscada

#### `ValidationError`
Levantada quando a validação de uma variável falha.

**Atributos:**
- `key: str` - Nome da variável
- `value: Any` - Valor que falhou na validação
- `reason: str` - Motivo da falha

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes de Desenvolvimento

- Escreva testes para novas funcionalidades
- Mantenha cobertura de testes > 95%
- Use type hints em todo o código
- Siga o guia de estilo PEP 8
- Atualize a documentação

---

## 📝 Changelog

Veja o arquivo [CHANGELOG.md](CHANGELOG.md) para histórico de mudanças.

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 📬 Suporte

- **Issues**: [GitHub Issues](https://github.com/felipeabreu86/django-env-loader/issues)
- **Discussões**: [GitHub Discussions](https://github.com/felipeabreu86/django-env-loader/discussions)

---

## 🔗 Links Úteis

- [PyPI](https://pypi.org/project/django-env-loader/)
- [Código fonte](https://github.com/felipeabreu86/django-env-loader)
- [Exemplos](https://github.com/felipeabreu86/django-env-loader/tree/main/examples)
