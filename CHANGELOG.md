# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado
- Suporte a async/await
- CLI para validação de variáveis
- Integração com Pydantic Settings

## [1.0.5] - 2024-01-20

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