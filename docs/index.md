# iSpider — Architekturdokumentation (arc42)

**Version:** 0.1 (Entwurf)
**Datum:** 19.03.2026
**Status:** In Arbeit
**Zielplattform:** Docker Swarm, Traefik v3, PWA

---

## Inhaltsverzeichnis

1. [Einführung und Ziele](#1-einführung-und-ziele)
2. [Randbedingungen](#2-randbedingungen)
3. [Kontextabgrenzung](#3-kontextabgrenzung)
4. [Lösungsstrategie](#4-lösungsstrategie)
5. [Bausteinsicht](#5-bausteinsicht)
6. [Laufzeitsicht](#6-laufzeitsicht)
7. [Verteilungssicht](#7-verteilungssicht)
8. [Querschnittliche Konzepte](#8-querschnittliche-konzepte)
9. [Architekturentscheidungen](#9-architekturentscheidungen)
10. [Qualitätsszenarien](#10-qualitätsszenarien)
11. [Risiken und technische Schulden](#11-risiken-und-technische-schulden)
12. [Implementierungsreihenfolge](#12-implementierungsreihenfolge)

---

## 1. Einführung und Ziele

iSpider ist ein personalisierter News-Aggregator für den Einzelnutzer. Die Anwendung bündelt RSS-Feeds, Blogs und Websites ohne RSS-Feed in einer einzigen, kuratierten Ansicht. KI-gestütztes Relevanz-Scoring und Keyword-Alerts stellen sicher, dass der Nutzer nur über tatsächlich wichtige Nachrichten benachrichtigt wird.

### 1.1 Aufgabenstellung

Der Nutzer konsumiert täglich Nachrichten aus den Bereichen Tech/KI und Sport in Deutsch und Englisch. Das Problem: zu viele Quellen, zu viel Rauschen, keine zentrale Anlaufstelle, keine intelligente Filterung. iSpider löst dieses Problem durch:

- Aggregation beliebiger Quellen (RSS, Websites, Blogs)
- KI-basiertes Relevanz-Scoring jedes Artikels (0–100)
- Push-Benachrichtigungen nur bei tatsächlich relevanten Inhalten
- On-Demand-KI-Analyse des aktuellen Feeds

### 1.2 Qualitätsziele

| Priorität | Qualitätsziel | Beschreibung |
|-----------|---------------|--------------|
| 1 | Relevanz | Nur wirklich wichtige Artikel erzeugen Benachrichtigungen |
| 2 | Aktualität | Neue Artikel werden spätestens alle 15 Minuten erfasst |
| 3 | Verfügbarkeit | App ist als PWA offline nutzbar (bereits geladene Artikel) |
| 4 | Einfachheit | Single-User — kein komplexes Auth-System nötig |
| 5 | Kostenkontrolle | KI-Kosten minimiert durch Haiku für Batch-Tasks |

### 1.3 Stakeholder

| Rolle | Erwartung |
|-------|-----------|
| Nutzer (Betreiber) | Kuratierter Feed, Push bei Breaking News, stabile PWA auf iOS/Android |
| Betrieb | Einfaches Deployment via `docker stack deploy`, Secrets über Swarm |

---

## 2. Randbedingungen

### 2.1 Technische Randbedingungen

| Constraint | Vorgabe |
|------------|---------|
| Deployment | Docker Swarm (bestehender Cluster) |
| Reverse Proxy | Traefik v3 (bereits laufend) |
| TLS | Let's Encrypt via Traefik, eigene Domain |
| Datenbank | PostgreSQL (bereits vorhanden im Cluster) |
| Backend-Sprache | Python / FastAPI |
| Secrets | Docker Swarm Secrets (kein `.env` im Produktivbetrieb) |
| KI-Provider | Anthropic API (Claude Haiku + Sonnet) |
| Mobile | PWA (keine native App) |

### 2.2 Organisatorische Randbedingungen

- Single-User-System — kein Multi-Tenancy erforderlich
- Kein dediziertes Team — Betrieb und Entwicklung durch eine Person
- Kosten für Claude API müssen im Rahmen bleiben (Haiku für High-Frequency-Tasks)

---

## 3. Kontextabgrenzung

### 3.1 Fachlicher Kontext

iSpider steht im Zentrum eines Datenflusses zwischen externen Quellen und dem Nutzer:

| Nachbarsystem | Richtung | Beschreibung |
|---------------|----------|--------------|
| RSS/Atom-Feeds | → iSpider | Strukturierte Nachrichtenfeeds externer Verlage |
| Websites / Blogs | → iSpider | Unstrukturierte Webseiten ohne RSS (per Scraping) |
| Anthropic API | ↔ iSpider | KI-Analyse: Scraping, Scoring, On-Demand-Query |
| PWA (Browser) | ↔ iSpider | Benutzeroberfläche: Feed lesen, Quellen verwalten |
| Web Push Service | ← iSpider | Push-Benachrichtigungen an Browser (iOS/Android) |
| OPML-Dateien | → iSpider | Quellen-Import aus anderen RSS-Readern |

### 3.2 Technischer Kontext

```
Internet / Nutzer-Browser (PWA)
        |
Traefik v3 (TLS-Termination, Routing)
     |              |
  Frontend       Backend API
  (Nginx/PWA)    (FastAPI :8000)
                    |         |
                 Worker     Redis
                 (Cron)       |
                    |      Job-Queue
               PostgreSQL
               (Persistenz)
                    |
              Anthropic API
           (Claude Haiku / Sonnet)
```

---

## 4. Lösungsstrategie

Das Backend folgt der **Hexagonalen Architektur (Ports & Adapters)**. Die Kerndomäne kennt keine externen Abhängigkeiten — alle Integrationen (Datenbank, KI, Push, Feed-Fetching) hängen an abstrakten Ports und werden durch austauschbare Adapter implementiert. Frontend, Worker und Datenbank sind eigenständige Deployment-Einheiten.

| Entscheidung | Wahl | Begründung |
|--------------|------|------------|
| Backend-Architektur | Hexagonal (Ports & Adapters) | Wartbarkeit, Austauschbarkeit von Adaptern, Testbarkeit der Domain |
| Backend-Framework | FastAPI (Python) | Typsicherheit, async-fähig, automatische OpenAPI-Docs |
| Datenbank | PostgreSQL | Bereits vorhanden, ACID, gut für strukturierte Artikel-Daten |
| Queue/Cache | Redis | Einfache Job-Queue, kein Overhead wie Kafka/RabbitMQ |
| Worker | APScheduler in Python | Leichtgewichtig, kein separater Celery-Stack nötig |
| KI (Batch) | Claude Haiku | Günstig, schnell — für 15-min-Intervalle optimiert |
| KI (On-Demand) | Claude Sonnet | Bessere Qualität für interaktive Nutzerfragen |
| Frontend | PWA (Nginx) | Installierbar auf iOS/Android, kein App Store nötig |
| Secrets | Docker Swarm Secrets | Sicherer als `.env`, in Swarm nativ unterstützt |

---

## 5. Bausteinsicht

### 5.1 Ebene 1 — Gesamtsystem

| Service | Docker Image | Aufgabe |
|---------|-------------|---------|
| `frontend` | `nginx:alpine` | PWA ausliefern, statische Assets |
| `api` | `python:3.12` / FastAPI | REST API, Business Logic, Push-Handling |
| `worker` | `python:3.12` | Feed-Fetching, Scraping, KI-Scoring (Cron) |
| `db` | `postgres:16` | Persistente Datenhaltung |
| `redis` | `redis:7-alpine` | Job-Queue, Caching, Push-State |

### 5.2 Backend (FastAPI) — API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/items` | GET | Artikel abrufen (Filter: Tag, Quelle, Score, gelesen) |
| `/api/sources` | POST | Neue Quelle hinzufügen (Auto-Detect RSS vs. Webpage) |
| `/api/sources/opml` | POST | Quellen-Import via OPML-Datei |
| `/api/sources/{id}` | PUT | Quelle bearbeiten (Priorität, Tags, aktiv/inaktiv) |
| `/api/sources/{id}` | DELETE | Quelle entfernen |
| `/api/tags` | GET / POST | Tags verwalten |
| `/api/keywords` | GET / POST | Keyword-Alerts konfigurieren |
| `/api/push/subscribe` | POST | Web-Push-Subscription registrieren |
| `/api/ai/query` | POST | On-Demand KI-Analyse mit Feed-Kontext |

### 5.3 Backend — Hexagonale Architektur (Ports & Adapters)

Das Backend ist nach dem Prinzip der Hexagonalen Architektur strukturiert. Die `domain/` hat keine Abhängigkeiten zu FastAPI, SQLAlchemy oder externen Bibliotheken — sie kennt ausschließlich eigene Models und abstrakte Port-Interfaces. Alle externen Integrationen sind austauschbare Adapter.

```
ispider-api/
├── domain/                    # Kernlogik — keine externen Abhängigkeiten
│   ├── models/                # FeedItem, Source, Keyword, Score, Tag
│   ├── services/              # FeedService, ScoringService, NotificationService
│   └── ports/
│       ├── inbound/           # IFeedQuery, ISourceCommand, IAIQueryCommand
│       └── outbound/          # IItemRepository, IAIProvider, IPushSender,
│                              # IFeedFetcher, IQueueAdapter
│
├── adapters/
│   ├── inbound/
│   │   └── api/               # FastAPI Router — ruft inbound Ports auf
│   └── outbound/
│       ├── postgres/          # IItemRepository → SQLAlchemy
│       ├── redis/             # IQueueAdapter → Redis
│       ├── anthropic/         # IAIProvider → Claude Haiku / Sonnet
│       ├── rss/               # IFeedFetcher → feedparser
│       ├── scraper/           # IFeedFetcher → httpx + Claude
│       └── webpush/           # IPushSender → pywebpush
│
└── config/                    # Settings, Dependency Injection
```

**Vorteil für iSpider:** Neue Quell-Typen (z.B. Newsletter, Podcasts) oder ein Wechsel des KI-Providers erfordern nur einen neuen Adapter — die Domain-Logik bleibt unberührt.

### 5.4 Worker — Verarbeitungspipeline

```
Für jede aktive Quelle:
  1. Typ prüfen: RSS/Atom vs. Webpage
     RSS   → feedparser → Items extrahieren
     Web   → httpx fetch → Claude Haiku → JSON [{title, url, summary, date}]

  2. Deduplizierung via SHA-256(url) gegen bestehende feed_items

  3. Neue Items: Claude Haiku bewertet Relevanz
     Input:  Titel + Summary + Nutzerpräferenzen (Tech/Sport, DE/EN)
     Output: { score: 0-100, reason: "...", tags: [...] }

  4. Keyword-Abgleich gegen keywords-Tabelle

  5. Push-Trigger:
     score > threshold  OR  keyword_match == true
     → pywebpush → Web Push an registrierte Endpoints

  6. Items in feed_items + scored_items persistieren
```

---

## 6. Laufzeitsicht

### 6.1 Feed-Fetch-Zyklus (alle 15 Minuten)

1. APScheduler triggert Worker-Job
2. Worker lädt aktive Quellen aus PostgreSQL
3. Parallel: HTTP-Requests an alle Quellen (httpx, async, Timeout 8s)
4. RSS-Quellen: feedparser parst Feed-XML
5. Web-Quellen: Rohinhalt an Claude Haiku → strukturierte Artikel-Liste
6. Deduplizierung: URL-Hash gegen bestehende Einträge
7. Neue Items: Relevanz-Scoring via Claude Haiku
8. Keyword-Matching gegen konfigurierte Begriffe
9. Score > Schwellenwert oder Keyword-Hit → Push via pywebpush
10. Alle Items in DB persistieren

### 6.2 Nutzer-Interaktion (PWA)

1. Nutzer öffnet PWA im Browser oder als installierte App
2. PWA lädt Artikel via `GET /api/items` (gefiltert nach Präferenzen)
3. Nutzer stellt Frage in KI-Analyse-Panel
4. `POST /api/ai/query` — Backend baut Kontext aus letzten 30 Items
5. Claude Sonnet antwortet — Antwort wird in UI gestreamt

### 6.3 Push-Notification-Flow

1. PWA registriert Service Worker beim ersten Start
2. Service Worker abonniert Web-Push-Endpoint (VAPID)
3. Subscription-Objekt wird via `POST /api/push/subscribe` gespeichert
4. Worker triggert Push bei relevanten Items via pywebpush
5. Browser-OS liefert Notification — auch wenn PWA geschlossen ist

---

## 7. Verteilungssicht

### 7.1 Docker Swarm Stack

```yaml
networks:
  ispider_public:    # Overlay — Traefik <-> frontend, api
    driver: overlay
    attachable: true
  ispider_internal:  # Overlay — api, worker, db, redis (kein Außenzugriff)
    driver: overlay

secrets:
  anthropic_api_key:  { external: true }
  postgres_password:  { external: true }

services:
  frontend:
    image: ispider-frontend:latest
    networks: [ispider_public]
    deploy:
      replicas: 1
      restart_policy: { condition: on-failure }
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.ispider-fe.rule=Host(`ispider.domain.com`)"
        - "traefik.http.routers.ispider-fe.entrypoints=websecure"
        - "traefik.http.routers.ispider-fe.tls.certresolver=letsencrypt"
        - "traefik.http.services.ispider-fe.loadbalancer.server.port=80"

  api:
    image: ispider-api:latest
    networks: [ispider_public, ispider_internal]
    secrets: [anthropic_api_key, postgres_password]
    deploy:
      replicas: 1
      restart_policy: { condition: on-failure }
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.ispider-api.rule=Host(`ispider.domain.com`) && PathPrefix(`/api`)"
        - "traefik.http.routers.ispider-api.entrypoints=websecure"
        - "traefik.http.routers.ispider-api.tls.certresolver=letsencrypt"
        - "traefik.http.services.ispider-api.loadbalancer.server.port=8000"

  worker:
    image: ispider-worker:latest
    networks: [ispider_internal]   # kein öffentlicher Zugriff
    secrets: [anthropic_api_key, postgres_password]
    deploy:
      replicas: 1
      restart_policy: { condition: on-failure }

  db:
    image: postgres:16
    networks: [ispider_internal]
    secrets: [postgres_password]
    volumes:
      - ispider_pgdata:/var/lib/postgresql/data
    deploy:
      replicas: 1
      placement:
        constraints: [node.role == manager]  # Volume-Sticky

  redis:
    image: redis:7-alpine
    networks: [ispider_internal]
    deploy:
      replicas: 1

volumes:
  ispider_pgdata:
    driver: local
```

### 7.2 Netzwerktopologie

| Netzwerk | Typ | Services | Zweck |
|----------|-----|----------|-------|
| `ispider_public` | Overlay | Traefik, frontend, api | Extern erreichbar via Traefik |
| `ispider_internal` | Overlay | api, worker, db, redis | Interne Kommunikation, kein Außenzugriff |

### 7.3 Secrets-Management

```bash
# Einmalig auf dem Swarm-Manager anlegen:
echo "sk-ant-api03-..." | docker secret create anthropic_api_key -
echo "supersecretpw"    | docker secret create postgres_password -

# Im Container verfügbar unter:
# /run/secrets/anthropic_api_key
# /run/secrets/postgres_password
```

---

## 8. Querschnittliche Konzepte

### 8.1 Datenpersistenz — PostgreSQL Schema

| Tabelle | Wichtige Felder | Beschreibung |
|---------|-----------------|--------------|
| `sources` | `id, url, type (rss\|web), name, active, priority, created_at` | Alle konfigurierten Quellen |
| `feed_items` | `id, source_id, url_hash, title, description, pub_date, raw_content` | Rohartikel aus Feeds |
| `scored_items` | `item_id, ki_score, ki_reason, keywords_matched, notified_at` | KI-Bewertungen |
| `tags` | `id, name, color` | Nutzer-definierte Tags |
| `source_tags` | `source_id, tag_id` | N:M Verknüpfung Quellen ↔ Tags |
| `keywords` | `id, term, threshold, notify, active` | Keyword-Alert-Konfiguration |
| `push_subscriptions` | `id, endpoint, p256dh, auth, created_at` | Web-Push-Endpoints |

### 8.2 KI-Integration (Anthropic API)

| Anwendungsfall | Modell | Trigger | Kostenfaktor |
|----------------|--------|---------|--------------|
| Web-Scraping ohne RSS | Claude Haiku | Worker, pro Quelle ohne Feed | Gering (kleiner Kontext) |
| Relevanz-Scoring | Claude Haiku | Worker, pro neuem Artikel | Gering (Batch-optimiert) |
| On-Demand-Analyse | Claude Sonnet | Nutzer-Request (PWA) | Mittel (seltener Aufruf) |

### 8.3 Push-Notification-Konzept

- Standard: Web Push API (VAPID, RFC 8292)
- Backend: `pywebpush`-Bibliothek
- VAPID-Keys: einmalig generiert, in Swarm Secrets gespeichert
- Trigger-Logik: KI-Score > konfigurierbarer Schwellenwert (Default: 70) **oder** Keyword-Match
- Rate Limiting: max. 5 Pushes pro Stunde (verhindert Notification Fatigue)

### 8.4 Quellen-Typ-Erkennung

Beim Hinzufügen einer neuen Quelle erkennt das Backend automatisch den Typ:

1. HTTP HEAD/GET auf die URL
2. `Content-Type: application/rss+xml` oder `application/atom+xml` → RSS-Feed
3. HTML mit `<link rel="alternate" type="application/rss+xml">` → RSS-Feed (Link extrahieren)
4. Sonst → Webpage-Modus (KI-Scraping im Worker aktiviert)

---

## 9. Architekturentscheidungen

### ADR-001: PWA statt nativer App

| | |
|--|--|
| **Kontext** | App soll auf iOS und Android laufen, Single-User, kein App-Store-Overhead |
| **Entscheidung** | Progressive Web App (PWA) |
| **Begründung** | Kein App-Store-Review, direkt über Domain deployt, Push-Notifications via Web Push API |
| **Konsequenz** | iOS-Push erfordert iOS 16.4+ und "Add to Home Screen" |

### ADR-002: Haiku für Batch, Sonnet für On-Demand

| | |
|--|--|
| **Kontext** | Claude API verursacht Kosten pro Token — Worker läuft alle 15 Minuten |
| **Entscheidung** | Claude Haiku für Worker-Tasks, Claude Sonnet nur für interaktive Nutzer-Queries |
| **Begründung** | Haiku ist ~20x günstiger als Sonnet, für Scoring/Scraping ausreichend präzise |
| **Konsequenz** | Scoring-Qualität minimal schlechter als Sonnet — akzeptabel für Single-User |

### ADR-003: Redis statt PostgreSQL für Job-Queue

| | |
|--|--|
| **Kontext** | Worker braucht Job-Queue und kurzlebigen State (Push-Deduplizierung) |
| **Entscheidung** | Redis als Queue und Cache |
| **Begründung** | Kein Overhead durch Celery/RabbitMQ, APScheduler + Redis ausreichend für Single-Worker |
| **Konsequenz** | Bei mehreren Worker-Replicas würde Locking-Logik nötig — aktuell kein Bedarf |

### ADR-004: Neues Overlay-Netzwerk statt bestehendem Traefik-Netzwerk

| | |
|--|--|
| **Kontext** | Traefik v3 läuft bereits mit eigenem Overlay-Netzwerk auf dem Cluster |
| **Entscheidung** | Eigenes Overlay-Netzwerk `ispider_public` im Stack definieren, an Traefik anhängen |
| **Begründung** | Saubere Isolation des iSpider-Stacks; kein Eingriff in bestehende Cluster-Konfiguration |
| **Konsequenz** | `ispider_public` muss `attachable: true` sein damit Traefik joinen kann |

### ADR-005: Hexagonale Architektur für das Backend

| | |
|--|--|
| **Kontext** | Das Backend integriert mehrere externe Systeme (PostgreSQL, Redis, Anthropic API, RSS, Web Push) die sich unabhängig voneinander ändern können |
| **Entscheidung** | Hexagonale Architektur (Ports & Adapters) für den API-Service |
| **Begründung** | Isoliert die Kerndomäne von externen Abhängigkeiten; neue Adapter (z.B. anderer KI-Provider, neuer Feed-Typ) können ohne Änderung der Business-Logik ergänzt werden; verbessert Testbarkeit (Domain isoliert mockbar) |
| **Konsequenz** | Mehr initialer Strukturaufwand gegenüber einem flachen Service-Layer; zahlt sich bei wachsender Adapter-Anzahl aus |



| ID | Qualitätsmerkmal | Szenario | Reaktion / Ziel |
|----|-----------------|----------|-----------------|
| Q1 | Aktualität | Breaking News erscheint bei einer Quelle | Nutzer erhält Push innerhalb von 15 Minuten |
| Q2 | Relevanz | Unwichtiger Artikel mit Score 30 erscheint | Kein Push, Artikel nur im Feed sichtbar |
| Q3 | Verfügbarkeit | Nutzer öffnet PWA ohne Internetzugang | Letzte geladene Artikel aus IndexedDB sichtbar |
| Q4 | Robustheit | Eine Quelle liefert Timeout oder HTTP 500 | Worker logt Fehler, übrige Quellen werden normal verarbeitet |
| Q5 | Kosten | Worker läuft bei 10 aktiven Web-Quellen | Haiku-Kosten bleiben unter $1/Tag (geschätzt) |
| Q6 | Datenschutz | Keine anderen Nutzer | Keine Auth-Komplexität, kein Multi-Tenancy |

---

## 11. Risiken und technische Schulden

| Risiko | Wahrscheinlichkeit | Auswirkung | Maßnahme |
|--------|--------------------|------------|----------|
| Anthropic API-Ausfall | Gering | Kein Scoring, kein Web-Scraping | Graceful Degradation: Items ohne Score speichern, RSS weiter funktional |
| iOS Web Push Einschränkungen | Mittel | Push auf iOS < 16.4 nicht verfügbar | Dokumentieren; Fallback: In-App-Badge beim nächsten Öffnen |
| RSS-Feed-Änderungen | Mittel | Quell-URLs ändern sich oder Feed wird eingestellt | Fehler-Counter pro Quelle, bei N Fehlern Auto-Disable + Hinweis in UI |
| Robots.txt / Scraping-Verbote | Mittel | Web-Scraping für manche Sites rechtlich unzulässig | `robots.txt` prüfen vor Scraping-Aktivierung |
| KI-Kosten bei vielen Quellen | Gering | Unerwartete API-Kosten | Monatliches Budget-Limit in Anthropic Console setzen |

---

## 12. Implementierungsreihenfolge

| Phase | Inhalte | Ergebnis |
|-------|---------|----------|
| 1 — Fundament | DB-Schema, FastAPI-Grundgerüst, Sources/Items CRUD, Docker Stack Skeleton | Deploybare Basis, API via OpenAPI dokumentiert |
| 2 — Worker | APScheduler, RSS-Fetching via feedparser, Deduplizierung, Items in DB | Feed-Daten fließen alle 15 min in die DB |
| 3 — KI-Scoring | Claude Haiku Integration im Worker, `scored_items`-Tabelle, Keyword-Matching | Jeder Artikel hat einen Relevanz-Score |
| 4 — Frontend | PWA: Feed-Ansicht, Filter, Quellen-Verwaltung, Tags, OPML-Import | Vollständige Benutzeroberfläche |
| 5 — Web-Scraping | Typ-Erkennung beim Source-Add, Claude Haiku Scraping-Prompt, Fallback-Logik | Auch Websites ohne RSS werden erfasst |
| 6 — Push | Service Worker, VAPID-Keys, pywebpush im Backend, Push-Threshold-Konfiguration | Push-Benachrichtigungen auf iOS/Android |
| 7 — Polish | OPML-Export, Fehler-Handling, Rate Limits, Monitoring, Dokumentation | Produktionsreifes System |

### Deployment

```bash
docker secret create anthropic_api_key -  # API Key als Secret
docker secret create postgres_password -  # DB-Passwort als Secret
docker stack deploy -c stack.yml ispider   # Stack deployen
docker stack services ispider              # Status prüfen
```

---

## Anhang: Technologie-Stack

| Schicht | Technologie | Version | Zweck |
|---------|-------------|---------|-------|
| Frontend | Nginx | alpine | PWA-Auslieferung |
| Frontend | Service Worker API | W3C Standard | Offline-Support, Push-Empfang |
| Backend | Python | 3.12 | Laufzeitumgebung |
| Backend | FastAPI | aktuell | REST API Framework |
| Backend | SQLAlchemy | aktuell | ORM für PostgreSQL |
| Backend | pywebpush | aktuell | Web Push Notifications |
| Worker | APScheduler | aktuell | Cron-Job-Verwaltung |
| Worker | feedparser | aktuell | RSS/Atom-Parsing |
| Worker | httpx | aktuell | Async HTTP-Client |
| Daten | PostgreSQL | 16 | Relationale Datenbank |
| Daten | Redis | 7 | Queue, Cache |
| KI | Claude Haiku | aktuell | Scraping, Scoring (Batch) |
| KI | Claude Sonnet | aktuell | On-Demand-Analyse |
| Infra | Docker Swarm | aktuell | Container-Orchestrierung |
| Infra | Traefik | v3 | Reverse Proxy, TLS |
