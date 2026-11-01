# SISTEMA WEB V1 — Bootstrap

## Objetivo
Disponibilizar a primeira versão navegável com frontend React/TypeScript e API FastAPI em contentores Docker isolados.

## Limites
- Incluído: dashboard dark, frontend Vite, API FastAPI, endpoint de saúde e Docker Compose.
- Não incluído: autenticação, PostgreSQL, Redis, workers, proxy reverso, TLS ou integrações externas.
- LICITACAO é exclusivamente fonte de consulta. Código, documentação e artefactos do produto ficam neste repositório.

## Rede e portas
A publicação é vinculada apenas à interface 192.168.60.141:
- Frontend: TCP 5173.
- Backend: TCP 8000.

A stack usa rede Docker própria (sistema-web-v1-network). Não modifica redes, contentores, volumes ou configurações dos serviços preexistentes.

## Arranque
Na raiz do clone local:

```bash
sudo docker compose -f deploy/docker-compose.yml config
sudo docker compose -f deploy/docker-compose.yml up -d --build
sudo docker compose -f deploy/docker-compose.yml ps
```

Acesso:
- Dashboard: http://192.168.60.141:5173
- API health: http://192.168.60.141:8000/api/health
- OpenAPI: http://192.168.60.141:8000/docs

## Validação

```bash
curl --fail http://192.168.60.141:8000/api/health
curl --fail http://192.168.60.141:5173/
sudo docker compose -f deploy/docker-compose.yml logs --tail=100
```

## Paragem
Parar apenas esta stack:

```bash
sudo docker compose -f deploy/docker-compose.yml down
```

Não usar `down -v` sem decisão explícita, pois remove volumes nomeados desta stack.

## Estado
- Código inicial: implementado nesta branch.
- Validação no Ubuntu: pendente de execução local.
- Acesso no navegador: pendente de confirmação.
