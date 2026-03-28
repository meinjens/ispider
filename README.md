# iSpider

Personalisierter News-Aggregator — PWA + FastAPI + Docker Swarm.

## Stack

- **Frontend**: Nginx PWA
- **Backend**: FastAPI (Python 3.12), Hexagonale Architektur
- **Worker**: APScheduler, alle 15 Minuten
- **DB**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **KI**: Anthropic API (Haiku für Batch, Sonnet für On-Demand)
- **Infra**: Docker Swarm + Traefik v3

## Deployment

```bash
# Secrets anlegen (einmalig)
echo "sk-ant-..." | docker secret create anthropic_api_key -
echo "meinpasswort" | docker secret create postgres_password -
echo "vapid-key..." | docker secret create vapid_private_key -

# Images bauen
docker build -t ispider-api:latest ./api
docker build -t ispider-worker:latest -f Dockerfile.worker .

# Stack deployen
DOMAIN=example.com docker stack deploy -c deploy/stack.yml ispider

# Status
docker stack services ispider
docker service logs ispider_worker
```

## Tests

```bash
pip install -r tests/requirements-test.txt
pytest
```

## Projektstruktur

```
api/
├── domain/          # Kernlogik (keine externen Abhängigkeiten)
│   ├── models/
│   ├── services/
│   └── ports/
│       ├── inbound/
│       └── outbound/
├── adapters/
│   ├── inbound/api/routers/
│   └── outbound/
│       ├── postgres/
│       ├── anthropic/
│       ├── rss/
│       ├── scraper/
│       └── webpush/
└── config/
worker/
deploy/
tests/
```
