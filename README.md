# SISTEMA-WEB

> Fundação de infraestrutura, arquitetura e implantação web para transformar o projeto **LICITACAO** numa aplicação operacional, instalada no servidor Ubuntu e acessível pelo navegador.

## 1. Origem e finalidade

Este repositório nasceu de uma necessidade concreta do projeto **LICITACAO**: transformar o trabalho já existente — documentação, scripts, validadores, cálculos e integrações — numa plataforma web real, sem descartar o desenvolvimento acumulado.

O SISTEMA-WEB não é um segundo projeto de negócio nem substitui o LICITACAO. É a frente técnica dedicada à arquitetura web, infraestrutura de execução, implantação e operação da aplicação LICITACAO.

- **LICITACAO:** domínio de negócio, regras, dados, módulos funcionais, evidências e governança das atividades de licitação.
- **SISTEMA-WEB:** fundação técnica para disponibilizar esses recursos por uma aplicação web, gerir os serviços de execução e estabelecer o processo de implantação no servidor Ubuntu.

A integração deverá aproveitar os componentes existentes no LICITACAO após auditoria. Não se deve duplicar módulos nem reescrever código funcional sem uma justificativa técnica documentada.

## 2. Repositórios e responsabilidades

| Repositório | Responsabilidade | Estado reconhecido |
|---|---|---|
| [LICITACAO](https://github.com/carlos-andrade/LICITACAO) | Projeto de negócio, módulos Python, documentação, dados, regras e governança | Repositório privado; branch `main`; conteúdo existente a auditar e reutilizar |
| [SISTEMA-WEB](https://github.com/carlos-andrade/SISTEMA-WEB) | Arquitetura web, infraestrutura, implantação e operação | Repositório público; branch `main`; documentação inicial |

Os repositórios mantêm históricos e finalidades próprios. A integração entre eles deve ocorrer por interfaces, contratos, dependências e procedimentos versionados — não pela cópia indiscriminada de diretórios.

## 3. Objetivo funcional da plataforma LICITACAO

A aplicação deverá apoiar a identificação, análise e acompanhamento de oportunidades de fornecimento a órgãos públicos brasileiros, com decisões comerciais rastreáveis e revisão humana nos pontos críticos.

O escopo funcional de referência contempla:

1. Painel principal com indicadores calculados a partir dos dados persistidos.
2. Editais: consulta, documentos, itens, requisitos, prazos e retificações.
3. Fornecedores: pesquisa, validação cadastral e histórico.
4. Comparação de preços: cotações, equivalência técnica e preço entregue.
5. Viabilidade: custos completos, margens e riscos.
6. Decisão: regras, recomendação fundamentada e aprovação humana.
7. Contratos: execução, prazos, entregas, ocorrências e pagamentos.

Fluxo de referência de um edital: consultar o registo oficial no PNCP; recuperar documentos; extrair itens e requisitos; identificar exigências; pesquisar fornecedores; comparar preços equivalentes; calcular custos e riscos; apresentar cenários; registar decisão humana e evidências.

**Regra de integridade:** a interface não pode inventar informações nem apresentar uma análise como concluída quando faltarem dados. Toda conclusão deve identificar origem, data, referência, premissas e estado de validação.

## 4. Arquitetura tecnológica de referência

A proposta definida para a aplicação é um **monólito modular**, executado em serviços separados por Docker Compose. Essa abordagem mantém uma aplicação central organizada por módulos de negócio, evitando a complexidade prematura de microsserviços distribuídos.

| Camada | Tecnologia definida | Responsabilidade |
|---|---|---|
| Frontend | React + TypeScript | Interface web e navegação |
| Componentes visuais | Biblioteca própria sobre componentes reutilizáveis | Consistência entre telas |
| Backend | Python + FastAPI | API, autenticação, permissões e regras de negócio |
| Persistência | PostgreSQL | Base de dados central |
| ORM e migrações | SQLAlchemy + Alembic | Modelagem e evolução do esquema |
| Processamento | Workers Python | Consultas, downloads e análises em segundo plano |
| Filas e cache | Redis | Filas e cache, quando necessários |
| Documentos | Armazenamento persistente | PDFs, anexos e evidências |
| Contentores | Docker Compose | Execução e isolamento dos serviços |
| Proxy reverso | Nginx | Encaminhamento e terminação HTTPS |
| Versionamento | GitHub | Código, documentação e histórico |

**Por que Python:** o repositório LICITACAO já contém trabalho em Python, incluindo scripts, validadores, cálculos e rotinas de integração. A estratégia é reaproveitar esse património, depois de auditoria técnica, em vez de reescrever tudo noutra linguagem.

Redis, workers e outros serviços auxiliares devem ser dimensionados conforme a necessidade real. A presença na arquitetura de referência não significa que já estejam implementados.

## 5. Arquitetura lógica e implantação

```text
UTILIZADOR
    |
Navegador Web
    |
HTTPS / TLS
    |
Nginx — proxy reverso
    |
Frontend React + TypeScript
    |
API Python + FastAPI
    |
    +----------------------+----------------------+
    |                      |                      |
PostgreSQL             Workers Python          Redis
    |                      |                 (fila/cache)
    +----------------------+----------------------+
                           |
                 Armazenamento persistente
                 PDFs, anexos e evidências

FONTES EXTERNAS
PNCP | Receita Federal | CEIS/CNEP
Fornecedores | Fontes de preços

OPERAÇÃO
Logs | Auditoria | Backups | Monitorização
                           |
                    Servidor Ubuntu

ENTREGA
GitHub -> revisão -> validação -> implantação controlada
```

### Ambiente de referência

O ambiente de destino é o servidor Ubuntu 24.04 LTS já utilizado no laboratório. A implantação proposta deverá manter os serviços do LICITACAO isolados dos restantes projetos existentes no servidor.

- Contentores e redes próprios para a aplicação.
- PostgreSQL exclusivo do LICITACAO, conforme a recomendação inicial.
- Volumes persistentes para dados, documentos e backups.
- Credenciais e configurações específicas do ambiente fora do Git.
- Política de firewall, DNS, HTTPS e acesso definida antes da publicação.
- Avaliação de CPU, memória e armazenamento antes de dimensionar os serviços.

O Nginx poderá funcionar como proxy reverso. A arquitetura deve ser compatibilizada com os serviços já ativos no servidor, sem assumir que uma configuração existente pode ser reutilizada sem auditoria.

### Acesso

A recomendação inicial é começar com acesso restrito por rede privada ou VPN. A exposição à Internet deverá ocorrer posteriormente, com autenticação, HTTPS, firewall e revisão de segurança. O domínio apresentado no documento de origem é apenas uma possibilidade, não uma configuração já existente.

## 6. Integração com o LICITACAO

A integração não deverá criar um segundo projeto dentro do primeiro nem substituir a estrutura existente.

Antes de desenvolver a aplicação, será necessário:

- Inventariar a árvore atual do LICITACAO.
- Identificar scripts, módulos, schemas, workflows e dependências reutilizáveis.
- Identificar duplicações, acoplamentos e funcionalidades incompletas.
- Definir contratos entre a API web e os módulos existentes.
- Preservar a governança, os critérios de validação e a rastreabilidade do projeto de negócio.
- Manter as regras de negócio no backend e nos módulos de domínio, não na camada visual.

Estrutura-alvo indicativa para a organização funcional do LICITACAO (sujeita à auditoria da árvore existente):

```text
LICITACAO/
├── frontend/
│   └── src/
│       ├── components/
│       ├── layouts/
│       ├── pages/
│       └── services/
├── backend/
│   └── app/
│       ├── api/
│       ├── core/
│       ├── models/
│       ├── schemas/
│       └── modules/
│           ├── oportunidades/
│           ├── documentos/
│           ├── fornecedores/
│           ├── precos/
│           ├── viabilidade/
│           ├── decisao/
│           └── contratos/
├── scripts/
├── database/
│   ├── migrations/
│   └── seeds/
├── deploy/
├── docs/
└── .github/
    └── workflows/
```

Esta estrutura é uma referência de destino, não uma ordem para criar pastas indiscriminadamente. A localização final de cada componente depende do inventário e das decisões de integração.

## 7. Dados, evidências e decisão humana

A plataforma deve garantir quatro elementos em cada funcionalidade:

1. **Código:** implementação versionada.
2. **Dados:** registos persistidos e relacionados corretamente.
3. **Evidência:** origem, data, referência e validação.
4. **Teste:** prova reproduzível de funcionamento.

Exemplo: um fornecedor não pode aparecer simplesmente como aprovado. O sistema deve permitir rastrear o CNPJ e estabelecimento consultados, comprovantes oficiais, data da consulta, documento e respetivo hash, CNAE, sanções verificadas e regra que produziu o resultado.

O mesmo princípio aplica-se a preços, equivalência técnica, custos e recomendações de participação. A decisão final de participar, apresentar lance, habilitar ou executar contrato permanece sujeita à revisão humana autorizada.

## 8. Roadmap de desenvolvimento

O plano de origem estabelece oito fases com critérios objetivos de aprovação:

| Fase | Escopo | Critério de aprovação |
|---|---|---|
| 0 — Auditoria técnica e inventário | Scripts reutilizáveis, schemas, workflows, dependências, duplicações e lacunas | Inventário e diagnóstico documentados |
| 1 — Infraestrutura | Docker, redes, volumes, PostgreSQL, HTTPS, backups, logs e ambiente de desenvolvimento | Aplicação mínima acessível no servidor, com persistência e recuperação testadas |
| 2 — Backend e banco de dados | Autenticação, utilizadores, permissões, migrações, API e entidades | Criar, consultar, alterar e auditar registos com integridade |
| 3 — Interface web | Padrão visual aprovado, navegação, componentes e seis telas de referência | Interface consumindo dados reais da API |
| 4 — Integração PNCP | Captura, paginação, documentos, retificações, normalização e rastreabilidade | Fluxo validado com oportunidades reais e documentos conferidos |
| 5 — Inteligência comercial | Fornecedores, preços, equivalência, custos, tributos, logística, margens e riscos | Análise reproduzível, com evidências e premissas explícitas |
| 6 — Decisão e execução | Habilitação, propostas, aprovações, contratos, entregas e pagamentos | Fluxo auditável com autorização humana nos pontos críticos |
| 7 — Homologação e produção | Testes integrados, segurança, carga, backup, restauração e monitorização | Gates de governança aprovados antes da operação |

Nenhuma fase será considerada concluída apenas porque a documentação foi escrita ou os diretórios foram criados. A conclusão exige evidência verificável.

## 9. Princípios de segurança e operação

- Isolar serviços, redes, volumes e credenciais da aplicação.
- Utilizar o princípio do menor privilégio para utilizadores e serviços.
- Não versionar segredos, ficheiros `.env` reais, chaves privadas ou dados sensíveis.
- Manter dados e documentos em volumes persistentes.
- Definir backups e testar a restauração antes da produção.
- Registar logs, eventos relevantes e trilhos de auditoria sem expor dados sensíveis.
- Identificar a versão implantada e manter procedimento de rollback.
- Monitorizar disponibilidade, recursos, erros e serviços críticos.
- Não expor a aplicação à Internet antes de validar autenticação, HTTPS, firewall e política de acesso.

A integração com Zabbix e outros serviços do laboratório deverá ser feita com indicadores e verificações definidos, sem misturar bases de dados ou comprometer o isolamento dos projetos.

## 10. Estado reconhecido em 01/11/2026

### SISTEMA-WEB

- Repositório público: `carlos-andrade/SISTEMA-WEB`.
- Branch principal: `main`.
- Licença identificada: MIT.
- Conteúdo reconhecido no início: `README.md` e `LICENSE`.
- Aplicação web, contentores, pipeline e implantação: ainda não comprovados neste repositório.

### LICITACAO

- Repositório privado: `carlos-andrade/LICITACAO`.
- Branch principal: `main`.
- Linguagem principal indicada pelo GitHub: Python.
- Repositório com conteúdo e documentação preexistentes, que precisam ser auditados para integração.
- O README do LICITACAO declara que ainda não existe aplicação de negócio implementada.

Este reconhecimento é uma fotografia documental da data indicada. Não equivale a auditoria integral do código, dos serviços do servidor ou da segurança da infraestrutura.

## 11. Próximas ações técnicas

A sequência recomendada é:

1. **Auditar o LICITACAO:** árvore, módulos Python, scripts, schemas, dependências, testes e workflows.
2. **Inventariar o Ubuntu:** versão, CPU, RAM, armazenamento, interfaces de rede, portas e serviços ativos.
3. **Fechar decisões de implantação:** isolamento, Docker Compose, PostgreSQL exclusivo, volumes, backups e acesso privado.
4. **Definir contratos de integração:** API, autenticação, entidades e fronteiras entre módulos.
5. **Construir o primeiro incremento funcional:** ambiente mínimo, backend, frontend, login e persistência.
6. **Homologar antes de expandir:** testes, evidências, segurança, restauração e aprovação dos gates.

A prioridade é provar primeiro a infraestrutura e a persistência. A integração PNCP e o motor de decisão devem avançar sobre dados confiáveis, não sobre telas demonstrativas.

## 12. Governança deste repositório

- Manter a branch `main` como estado integrado e validado.
- Usar commits descritivos e alterações de escopo limitado.
- Utilizar branches e pull requests quando a revisão trouxer benefício.
- Não duplicar no SISTEMA-WEB a governança de negócio mantida no LICITACAO.
- Documentar decisões que afetem arquitetura, segurança, implantação ou integração.
- Distinguir sempre os estados **planeado**, **em desenvolvimento**, **implementado** e **validado**.
- Não declarar serviços operacionais sem evidência de execução e teste.

---

**Princípio orientador:** o LICITACAO contém o negócio e o trabalho funcional acumulado; o SISTEMA-WEB fornece a fundação para o transformar numa aplicação web operacional. Primeiro auditar e preservar; depois integrar e implementar; finalmente homologar e automatizar.
