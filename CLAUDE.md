# iSpider — Projektkontext

## Architektur

Hexagonale Architektur (Ports & Adapters). Details in `docs/index.md`.

- `api/domain/` — Kernlogik, keine externen Abhängigkeiten
- `api/adapters/inbound/` — FastAPI Router
- `api/adapters/outbound/` — PostgreSQL, Redis, Anthropic, RSS, WebPush
- `api/config/` — Settings (Swarm Secrets), DB, DI
- `worker/` — APScheduler, alle 15 min
- `deploy/` — Docker Swarm Stack

## Offene Phasen

- Phase 4: PWA Frontend (Nginx, Service Worker, Push-Subscription)
- Phase 5: Web-Scraping Typ-Erkennung (läuft, Verbesserungen möglich)
- Phase 6: Push VAPID-Key-Generierung
- Phase 7: Monitoring, Error-Handling, OPML-Export

## Tests ausführen

pip install -r tests/requirements-test.txt
pytest

## Deployment

DOMAIN=example.com docker stack deploy -c deploy/stack.yml ispider