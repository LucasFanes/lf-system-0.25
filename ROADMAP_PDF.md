# ROADMAP PDF

## Fase 1 - Infraestrutura de testes e qualidade

Status: concluída.

- Criar configuração central do projeto em `pyproject.toml`.
- Configurar pytest, pytest-cov e Ruff.
- Criar `.gitignore` para excluir caches, PDFs pessoais, bancos reais, logs e arquivos gerados.
- Criar estrutura `tests/unit`, `tests/integration` e `tests/fixtures`.
- Gerar PDFs temporários dentro dos testes.
- Cobrir abertura, fechamento, contagem de páginas, salvar, salvar como, giro e extração de páginas.
- Adicionar testes iniciais para criptografia, descriptografia e marca-d'água quando suportado.

## Fase 2 - Refatoração segura do núcleo de PDF

Status: concluída.

- Mapear responsabilidades atuais do núcleo de PDF.
- Corrigir nomes inconsistentes sem quebrar compatibilidade.
- Separar operações puras, persistência e validações.
- Padronizar erros e retornos.
- Ampliar testes antes de alterar comportamento.

## Fase 3 - Interface profissional e melhoria dos botões

Status: concluída.

Observação: `.pytest_tmp` ficou inacessível por ACL no Windows; a validação equivalente foi concluída com `.pytest_tmp_run`.

- Revisar fluxo do menu de PDF.
- Melhorar rótulos, estados e confirmação de ações.
- Reduzir repetição de prompts e mensagens.
- Tornar ações destrutivas explícitas.
- Preservar atalhos e comandos existentes sempre que possível.

## Fase 4 - Integração do PDF com o LF System e testes de interface

Status: concluída.

Melhoria complementar: visualizador central ampliado, painéis laterais recolhíveis, tela cheia, zoom por modo e redimensionamento proporcional validados.

- Integrar o menu de PDF ao fluxo principal.
- Validar caminhos padrão e pastas do sistema.
- Criar testes de integração para os fluxos principais.
- Cobrir falhas comuns de entrada do usuário.

## Fase 5 - Limpeza segura dos demais módulos do projeto

Status: concluída.

Observação: `.pytest_cache` e `.pytest_tmp` antigos permanecem inacessíveis por ACL no Windows; novas execuções usam caches temporários ignorados e graváveis.

- Inventariar duplicidades e código legado.
- Remover somente o que tiver uso descartado por evidência.
- Melhorar organização sem alterar comportamento externo.
- Isolar dependências opcionais.

## Fase 6 - Documentação, CI, cobertura e revisão final

Status: concluída.

- Atualizar documentação de instalação e uso.
- Adicionar comandos de teste, lint e cobertura.
- Preparar CI para Windows.
- Revisar cobertura e riscos restantes.
- Fazer revisão final do comportamento do PDF integrado.
