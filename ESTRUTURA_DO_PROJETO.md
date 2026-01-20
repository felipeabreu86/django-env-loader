# Estrutura do Projeto Django Env Loader

## Estrutura Completa

```
django-env-loader/
├── .github/
│   └── workflows/
│       ├── tests.yml
│       └── publish.yml
├── docs/
│   └── usage.md
├── src/
│   └── django_env_loader/
│       ├── __init__.py
│       ├── exceptions.py
│       ├── loader.py
│       └── py.typed
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_converters.py
│   ├── test_loader.py
│   └── test_django.py
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
└── CHANGELOG.md
```

## Descrição dos Arquivos

### Raiz do Projeto

- **`.github/workflows/`**: Configurações de CI/CD (GitHub Actions)
- **`.gitignore`**: Arquivos ignorados pelo git
- **`LICENSE`**: Licença MIT do projeto
- **`README.md`**: Documentação principal
- **`pyproject.toml`**: Configuração do projeto (Poetry)
- **`CHANGELOG.md`**: Histórico de mudanças

### Código Fonte (`src/django_env_loader/`)

- **`__init__.py`**: Exports públicos e instância singleton
- **`exceptions.py`**: Exceções customizadas
- **`loader.py`**: Implementação principal
- **`py.typed`**: Marker para PEP 561 (type hints)

### Testes (`tests/`)

- **`conftest.py`**: Fixtures compartilhadas do pytest
- **`test_converters.py`**: Testes dos conversores de tipo
- **`test_loader.py`**: Testes do EnvLoader
- **`test_django.py`**: Testes do DjangoEnvLoader

### Documentação (`docs/`)

- **`usage.md`**: Guia de uso detalhado

## Arquivo Conftest Recomendado

Crie `tests/conftest.py`:

```python
"""Configuração compartilhada para testes."""

import pytest
from django_env_loader import EnvLoader, DjangoEnvLoader


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
```

## GitHub Actions

### `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -
        echo "$HOME/.local/bin" >> $GITHUB_PATH

    - name: Install dependencies
      run: |
        poetry install --with dev

    - name: Run linters
      run: |
        poetry run ruff check .
        poetry run mypy src

    - name: Run tests with coverage
      run: |
        poetry run pytest --cov=django_env_loader --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -
        echo "$HOME/.local/bin" >> $GITHUB_PATH

    - name: Build package
      run: poetry build

    - name: Publish to PyPI
      env:
        POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
      run: poetry publish
```

## CHANGELOG.md

```markdown
# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado
- Suporte a async/await
- CLI para validação de variáveis
- Integração com Pydantic Settings

## [1.0.0] - 2024-01-20

### Added
- Implementação inicial do EnvLoader
- Suporte a Docker secrets com fallback automático
- Conversores type-safe para bool, int, float, list, dict
- Validadores customizados via `get_with_validator`
- Cache configurável de secrets
- DjangoEnvLoader com helpers especializados
- Suporte a prefixos em variáveis
- Strict mode e warn_on_missing
- Exceções customizadas (SecretNotFoundError, ValidationError)
- Documentação completa
- Testes com cobertura > 95%
- Instância singleton pré-configurada para importação direta

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- Implementação segura de leitura de Docker secrets
- Validação rigorosa de tipos
```

## Comandos Úteis

```bash
# Instalar dependências
poetry install --with dev

# Executar testes
poetry run pytest -v

# Testes com coverage
poetry run pytest --cov=django_env_loader --cov-report=html

# Linters
poetry run ruff check --fix .
poetry run ruff format .

# Type checking
poetry run mypy src

# Executar todos os checks
poetry run task check-all

# Build do pacote
poetry build

# Publicar no TestPyPI (para testes)
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi

# Publicar no PyPI
poetry publish
```

## Próximos Passos

1. ✅ Implementar código base
2. ✅ Escrever testes
3. ✅ Criar documentação
4. ⬜ Configurar GitHub Actions
5. ⬜ Adicionar badges ao README
6. ⬜ Criar exemplos de uso
7. ⬜ Publicar no TestPyPI para validação
8. ⬜ Publicar no PyPI oficial
9. ⬜ Criar releases no GitHub
10. ⬜ Configurar ReadTheDocs (opcional)

## Recursos Adicionais

- [Poetry Documentation](https://python-poetry.org/docs/)
- [PyPI Publishing Guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)