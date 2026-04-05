# MLH PE Hackathon — Project by Purrduction Engineers

**Stack:** Flask · Peewee ORM · PostgreSQL · uv · Redis · Prometheus · Grafana · Loki · Alloy · Tempo

## Prerequisites

- **Docker & Docker Compose** — for containerizing the app, database and all other services. Install from [docker.com](https://www.docker.com/get-started). This is the easiest option for development and testing as it has all dependencies pre-configured.

### If running locally without Docker, you will need:

- **uv**(Optional) — a fast Python package manager that handles Python versions, virtual environments, and dependencies automatically. This can run the app locally but needs additional setup of dependencies.
  Install it with:

  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

  For other methods see the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/).

- PostgreSQL running locally (you can use Docker or a local instance)

- (Optional) Redis running locally (you can use Docker or a local instance)

- (Optional) Prometheus for metrics collection (you can use Docker or a local instance)

- (Optional) Loki for logs visualization (you can use Docker or a local instance)

- (Optional) Alloy and Tempo for distributed tracing (you can use Docker or a local instance)

- (Optional) Grafana for monitoring (you can use Docker or a local instance)

- (Optional) InfluxDB for storing load testing results as time-series data (you can use Docker or a local instance)

## uv Basics

`uv` manages your Python version, virtual environment, and dependencies automatically — no manual `python -m venv` needed.

| Command               | What it does                                             |
| --------------------- | -------------------------------------------------------- |
| `uv sync`             | Install all dependencies (creates `.venv` automatically) |
| `uv run <script>`     | Run a script using the project's virtual environment     |
| `uv add <package>`    | Add a new dependency                                     |
| `uv remove <package>` | Remove a dependency                                      |

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url> && cd mlh-pe-hackathon

# 2. Configure environment
cp .env.example .env   # edit if your DB credentials differ

# 3. Run the application
docker compose up -d

# 4. Verify
curl http://localhost:5000/health
# → {"status":"ok"}

# 5. (Optional) Setup venv locally for autocomplete
# In Windows PowerShell:
$env:UV_PROJECT_ENVIRONMENT = ".venv_local"
uv sync
# In Linux:
export UV_PROJECT_ENVIRONMENT=".venv_local"
uv sync
```

## Project Structure

```
mlh-pe-hackathon/
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── database.py          # DatabaseProxy, BaseModel, connection hooks
│   ├── models/
│   │   └── __init__.py      # Import your models here
│   └── routes/
│       └── __init__.py      # register_routes() — add blueprints here
├── .env.example             # DB connection template
├── .gitignore               # Python + uv gitignore
├── .python-version          # Pin Python version for uv
├── pyproject.toml           # Project metadata + dependencies
├── run.py                   # Entry point: uv run run.py
└── README.md


├── README.md
├── app
│   ├── __init__.py                 # App factory (create_app)
│   ├── database.py                 # DatabaseProxy, BaseModel, connection hooks
│   ├── errors.py                   # Custom error handlers
│   ├── frontend                    # React frontend project
│   ├── logger.py                   # JSON Logging configuration
│   ├── models
│   │   ├── __init__.py             # Import your models here
│   │   ├── event.py                # Event model
│   │   ├── url.py                  # URL model
│   │   └── user.py                 # User model
│   ├── routes
│   │   ├── __init__.py             # register_routes() — add blueprints here
│   │   ├── events.py               # Event-related routes
│   │   ├── urls.py                 # URL-related routes
│   │   └── users.py                # User-related routes
│   └── utils
│       └── isPostgres.py           # Utility to check if DB is PostgreSQL
├── compose.yml                     # Docker Compose configuration
├── docs
│   └── evidence                    # Documentation and evidence for the hackathon
│       ├── Incidence Response      # For Incidence Response Quest
│       ├── Reliability             # For Reliability Quest
│       └── Scalability             # For Scalability Quest
├── init.sh                         # Get packages for opentelemetry
├── k6
│   ├── run.ps1                     # Windows load test script
│   ├── run.sh                      # Linux load test script
│   ├── script.js                   # Load testing script
│   └── urls.csv                    # Test data for load testing; Needs to be manually loaded to DB before running load tests
├── logs                            # Directory for application logs (mounted to app and monitoring containers)
├── monitoring
│   ├── alloy.alloy                 # Alloy configuration file
│   ├── grafana
│   │   ├── dashboards
│   │   │   ├── k6.json             # Grafana dashboard for k6 load testing results
│   │   │   └── logs.json           # Grafana dashboard for Loki logs
│   │   └── provisioning
│   │       ├── dashboards
│   │       │   └── dashboards.yml  # Grafana provisioning for dashboards
│   │       └── datasources
│   │           └── datasources.yml # Grafana provisioning for data sources
│   ├── loki.yml                    # Loki configuration file
│   ├── nginx
│   │   └── nginx.conf              # Nginx configuration for reverse proxy
│   ├── prometheus.yml              # Prometheus configuration file
│   └── tempo.yml                   # Tempo configuration file
├── pyproject.toml                  # Project metadata + dependencies
├── run.py                          # Entry point: uv run run.py
├── scalability                     # Directory for scalability-related documentation and scripts
│   ├── README.md                   # Documentation for scalability quest
├── scripts
│   └── chaos-restart-proof.ps1     # PowerShell script to restart the app container for chaos testing
├── seeds                           # CSV seed files for initializing the database
│   ├── events.csv
│   ├── urls.csv
│   └── users.csv
├── tests                           # Unit and integration tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api_health.py
│   ├── test_api_urls.py
│   ├── test_api_users.py
│   ├── test_error_contract.py
│   ├── test_event_logic.py
│   ├── test_graceful_failure.py
│   ├── test_url_logic.py
│   └── test_user_logic.py
└── uv.lock                         # uv lockfile for pinned dependencies
```

## How to Add a Model

1. Create a file in `app/models/`, e.g. `app/models/product.py`:

```python
from peewee import CharField, DecimalField, IntegerField

from app.database import BaseModel


class Product(BaseModel):
    name = CharField()
    category = CharField()
    price = DecimalField(decimal_places=2)
    stock = IntegerField()
```

2. Import it in `app/models/__init__.py`:

```python
from app.models.product import Product
```

3. Create the table (run once in a Python shell or a setup script):

```python
from app.database import db
from app.models.product import Product

db.create_tables([Product])
```

## How to Add Routes

1. Create a blueprint in `app/routes/`, e.g. `app/routes/products.py`:

```python
from flask import Blueprint, jsonify
from playhouse.shortcuts import model_to_dict

from app.models.product import Product

products_bp = Blueprint("products", __name__)


@products_bp.route("/products")
def list_products():
    products = Product.select()
    return jsonify([model_to_dict(p) for p in products])
```

2. Register it in `app/routes/__init__.py`:

```python
def register_routes(app):
    from app.routes.products import products_bp
    app.register_blueprint(products_bp)
```

## How to Load CSV Data

```python
import csv
from peewee import chunked
from app.database import db
from app.models.product import Product

def load_csv(filepath):
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with db.atomic():
        for batch in chunked(rows, 100):
            Product.insert_many(batch).execute()
```

## Useful Peewee Patterns

```python
from peewee import fn
from playhouse.shortcuts import model_to_dict

# Select all
products = Product.select()

# Filter
cheap = Product.select().where(Product.price < 10)

# Get by ID
p = Product.get_by_id(1)

# Create
Product.create(name="Widget", category="Tools", price=9.99, stock=50)

# Convert to dict (great for JSON responses)
model_to_dict(p)

# Aggregations
avg_price = Product.select(fn.AVG(Product.price)).scalar()
total = Product.select(fn.SUM(Product.stock)).scalar()

# Group by
from peewee import fn
query = (Product
         .select(Product.category, fn.COUNT(Product.id).alias("count"))
         .group_by(Product.category))
```

## Tips

- Use `model_to_dict` from `playhouse.shortcuts` to convert model instances to dictionaries for JSON responses.
- Wrap bulk inserts in `db.atomic()` for transactional safety and performance.
- The template uses `teardown_appcontext` for connection cleanup, so connections are closed even when requests fail.
- Check `.env.example` for all available configuration options.
