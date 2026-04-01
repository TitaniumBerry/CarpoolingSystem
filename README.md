# Node-Based Carpooling System

A full-stack carpooling platform where drivers publish trips across a graph-based road network and passengers can request to join — including mid-ride — based on proximity rules.

![Python](https://img.shields.io/badge/python-3.12-blue) ![Django](https://img.shields.io/badge/django-6.0-green) ![Docker](https://img.shields.io/badge/docker-containerized-blue) ![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue)

---

## Live Demo

[https://dvmcarpooling.duckdns.org](https://dvmcarpooling.duckdns.org)

---

## What it does

Drivers create trips by selecting a start and end node on a road network graph. The system uses BFS to find the shortest route. Passengers submit carpool requests with a pickup and dropoff node — drivers see nearby requests (within 2 hops of their remaining route) and can make offers with calculated fares. Passengers confirm an offer and pay via an in-app wallet when the trip completes.

---

## Features

- **Graph-based routing** — road network modeled as a directed graph, BFS pathfinding
- **Role-based auth** — separate driver and passenger flows, Google OAuth login
- **Mid-ride carpooling** — passengers can join trips already in progress
- **Dynamic fare calculation** — based on hops and number of passengers per segment
- **In-app wallet** — top up, fare deduction, driver earnings, transaction history
- **Trip rating system** — rate drivers/passengers after trip completion, visible on profiles
- **Interactive network map** — visual map of nodes and edges
- **Route optimization** — optimal pickup/dropoff ordering for multiple passengers
- **Admin panel** — manage road network, view active trips, suspend service
- **Dockerized deployment** — Django + PostgreSQL + Nginx + Gunicorn

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0, Django REST Framework |
| Database | PostgreSQL 15 |
| Auth | Django AllAuth, Google OAuth2 |
| Deployment | Docker, Nginx, Gunicorn |
| Hosting | Google Cloud VPS |
| SSL | Let's Encrypt |

---

## Local Setup

### Requirements
- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (for local dev without Docker)

### With Docker
```bash
git clone https://github.com/TitaniumBerry/CarpoolingSystem.git
cd CarpoolingSystem
```

Create a `.env` file:
```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=carpooling
DB_USER=carpooling_user
DB_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
```

Then run:
```bash
docker-compose up --build -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

Visit `http://localhost`.

### Without Docker
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set `DB_HOST=localhost` in `.env`, then:
```bash
python manage.py migrate
python manage.py runserver
```

---

## Project Structure
```
CarpoolingSystem/
├── carpool/          # main app — models, views, templates
│   ├── models.py     # User, Node, Edge, Trip, CarpoolRequest, Wallet, Rating...
│   ├── views.py      # all views and API endpoints
│   ├── graph.py      # BFS pathfinding, proximity checks, fare calculation
│   └── templates/
├── core/             # project settings and URLs
├── nginx/            # Nginx config
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/trips/<id>/update-node` | Driver updates current node |

---

## Notes


Built as a multi-phase project covering graph algorithms, REST APIs, OAuth, Docker deployment and SSL. The road network is fully configurable via the Django admin panel — admins can add/remove nodes and edges to change available routes.
