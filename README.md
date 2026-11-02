# SISTEMA WEB

Plataforma web independente, com desenvolvimento, código, documentação e artefactos mantidos neste repositório.

> **Regra de repositórios:** SISTEMA-WEB é o único repositório de desenvolvimento e armazenamento do produto. LICITACAO é exclusivamente uma fonte externa de consulta. É proibido criar, editar, apagar ou gravar qualquer conteúdo no repositório LICITACAO no âmbito deste projeto.

## V1 — Bootstrap dark

| Camada | Tecnologia | Estado V1 |
|---|---|---|
| Interface | React + TypeScript + Vite | Implementação inicial |
| API | Python + FastAPI | Endpoint de saúde |
| Execução | Docker Compose | Configuração inicial |
| Persistência | PostgreSQL | Fora do bootstrap |
| Cache/filas | Redis | Fora do bootstrap |
| Autenticação | A definir | Não implementada |

### Acesso no laboratório
- Dashboard: http://192.168.60.141:5173
- API: http://192.168.60.141:8000
- Saúde da API: http://192.168.60.141:8000/api/health
- OpenAPI: http://192.168.60.141:8000/docs

As portas estão vinculadas à interface 192.168.60.141, não a todas as interfaces do servidor. Confirmar que o IP permanece atribuído e que as portas estão livres antes do primeiro arranque.

### Arranque

```bash
sudo docker compose -f deploy/docker-compose.yml config
sudo docker compose -f deploy/docker-compose.yml up -d --build
sudo docker compose -f deploy/docker-compose.yml ps
```

Instruções: [docs/V1-BOOTSTRAP.md](docs/V1-BOOTSTRAP.md).

## Princípios arquiteturais
- Monólito modular como direção; não introduzir microsserviços prematuramente.
- Isolar contentores, rede, volumes e credenciais do SISTEMA WEB.
- Não reutilizar nem alterar serviços de outros projetos sem decisão técnica explícita.
- Não versionar segredos ou ficheiros .env reais.
- Distinguir estados **planeado**, **implementado** e **validado**.
- Não declarar um serviço operacional sem teste verificável.

## Roadmap
1. **V1 — Bootstrap:** dashboard dark, API e Docker Compose.
2. **V1.1 — Navegação e validação:** seis módulos, comunicação frontend/API e homologação manual.
3. **V1.2 — LICITACAO read-only:** conector GitHub privado, validação JSON Schema e apresentação da oportunidade de referência com proveniência. **Aprovado para prova de conceito em laboratório, com âmbito limitado.** Ver [relatório de homologação](docs/V1.2-HOMOLOGACAO.md) e [documentação da integração](docs/V1.2-INTEGRACAO-LICITACAO.md).
4. **V1.3 — Catálogo de oportunidades:** inventário da fonte, listagem paginada, pesquisa, filtros, preservação do original, proveniência e histórico de alterações. **Especificado; implementação ainda não iniciada.** Ver [especificação V1.3](docs/V1.3-ESPECIFICACAO-CATALOGO-OPORTUNIDADES.md).
5. **V1.3-D — Catálogo de compradores e itens:** órgãos, unidades, contratações e consulta sob demanda dos itens no PNCP. Implementação em branch de revisão; homologação local pendente. Ver [documentação V1.3-D](docs/V1.3-D-CATALOGO-ORGAOS-UNIDADES-ITENS.md).
6. **V2 — Fundação aplicacional:** autenticação e persistência após desenho dos requisitos.
6. **V3 — Módulos funcionais:** domínios e integrações adicionais.
7. **Homologação de produção:** segurança, backups, recuperação, observabilidade e implantação controlada.

## Ambiente conhecido
O servidor de laboratório Ubuntu 24.04 possui Docker e Docker Compose. O acesso administrativo e as interfaces web dos serviços existentes utilizam 192.168.60.141. A configuração real deve ser novamente validada antes do primeiro arranque desta stack.

## Repositório
- Código, documentação e decisões: [carlos-andrade/SISTEMA-WEB](https://github.com/carlos-andrade/SISTEMA-WEB)
- LICITACAO: consulta apenas; nunca destino de escrita deste projeto.
