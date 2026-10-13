Alembic Explanation
Database Migration Setup
Full Database Migration Code & Autogenerate


  [Your Python Models]           [Your Live PostgreSQL Database]
  (e.g., class PullRequest)      (Real tables inside Postgres)
             \                       /
              \                     /
               ▼                   ▼
           Alembic compares both schemas
                         │
                         ▼
           Generates Python Migration File
           (e.g., versions/0001_initial.py)
           • upgrade(): creates new tables/columns
           • downgrade(): drops or rolls back


### Table: `pull_requests`

**Used By:** Webhook & Reviewer

| Column | Description |
| --- | --- |
| `pr_number` | PR number |
| `commit_sha` | Commit SHA |
| `repo_name` | Repository name |
| `installation_id` | GitHub App / integration installation ID |
| `review_status` | Current review status (`pending`, `reviewed`) |
| *Constraint/Index* | Prevents duplicate reviews (e.g., unique key on repo + PR/SHA) |

---

### Table: `findings`

**Used By:** Orchestrator & Evaluation

| Column | Description |
| --- | --- |
| `file` | Target file path where the issue was detected |
| `line` | Specific line number of the finding |
| `severity` | Severity level (e.g., `info`, `warning`, `error`, `critical`) |
| `message` | Detailed issue description or recommendation |
| `agent` | Identifier of the specific AI agent that detected the issue |

---

### Table: `patterns`

**Used By:** Learner & Orchestrator

| Column | Description |
| --- | --- |
| `repo_name` | Associated repository identifier |
| `pattern_description` | Signature or classification of the recurring code issue |
| `frequency` | Counter tracking occurrences learned when PRs are merged |

step1.
Create Your SQLAlchemy Models (db/models.py)
Before Alembic can autogenerate anything, we must write the Python classes representing our database tables.
and (from sqlalchemy.orm import declarative_base
Base = declarative_base())

step2 . 
Initialize Alembic with Async Support

Because FastAPI and SQLAlchemy use asyncpg (asynchronous PostgreSQL driver), we initialize Alembic using the async template:

```bash

cd db
uvx alembic init -t async migrations

Note change the comand i will use uv to create them

```
his generates:

alembic.ini
migrations/env.py
migrations/script.py.mako
migrations/versions/


step.3
- Configure env.py for Autogenerate & Dynamic DB URL
 1. Add project root to sys.path so we can import our models
```bash
sys.path.append(str(Path(__file__).resolve().parents[2]))
from db.models import Base
```

2. Dynamically inject DATABASE_URL from environment variable
```bash
database_url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
config.set_main_option("sqlalchemy.url", database_url)
```
CRITICAL: Point target_metadata to our models!
```bash
target_metadata = Base.metadata
```

using postgres image in docker

Here is the exact step-by-step procedure. 

> [!TIP]
> We will use **`postgres:15-alpine`** because it is only **~80 MB** (instead of 400 MB) so it downloads in just a few seconds without network timeout errors.

---

### Step 1: Pull & Run PostgreSQL in Docker

Open your PowerShell terminal and run:

```powershell
docker run -d --name codereviewer-db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=codereviewer -p 5432:5432 postgres:15-alpine
```

Check that the container is up and healthy:
```powershell
docker ps
```
*(You should see `codereviewer-db` with port `0.0.0.0:5432->5432/tcp` and status `Up`)*.

---

### Step 2: Generate the Migration Script via Autogenerate

Navigate to your [`db/`](file:///c:/Users/DELL/Desktop/git_hub_code_reviewer/db) folder and run Alembic using `uv run`:

```powershell
cd C:\Users\DELL\Desktop\git_hub_code_reviewer\db
uv run alembic revision --autogenerate -m "initial_schema"
```

#### What happens behind the scenes:
1. Alembic connects to your live PostgreSQL database on port 5432.
2. It looks at `target_metadata = Base.metadata` from your [`db/models.py`](file:///c:/Users/DELL/Desktop/git_hub_code_reviewer/db/models.py).
3. It detects that PostgreSQL has 0 tables, but your models define:
   - `pull_requests`
   - `findings`
   - `patterns`
4. Alembic automatically creates a new file inside [`db/migrations/versions/`](file:///c:/Users/DELL/Desktop/git_hub_code_reviewer/db/migrations/versions), for example:
   `db/migrations/versions/1a2b3c4d5e_initial_schema.py`.

---

### Step 3: Inspect the Generated Migration File

Open the newly created file in [`db/migrations/versions/`](file:///c:/Users/DELL/Desktop/git_hub_code_reviewer/db/migrations/versions). You will see:

* **`upgrade()`**: Contains `op.create_table(...)` for all 3 tables with their UUID primary keys, columns, foreign keys, and constraints.
* **`downgrade()`**: Contains `op.drop_table(...)` in reverse dependency order (`patterns`, `findings`, then `pull_requests`).

---

### Step 4: Apply the Migration to PostgreSQL

Apply the migration so the physical tables are created inside Postgres:

```powershell
uv run alembic upgrade head
```

---

### Step 5: Verify the Current Database Version

Check that the migration version was committed:

```powershell
uv run alembic current
```

Postgres will now have:
- `alembic_version` (stores the current migration revision hash)
- `pull_requests`
- `findings`
- `patterns`

---

and 

using installed postgres in pc 

----


Phase 2 


All Microservices Code

1. All Microservices Explained (Architecture & Data Contracts)
2. Gateway Microservice (Port 8000) ───► We build this first
3. Webhook Microservice (Port 8001)
4. Orchestrator Microservice (Port 8002)
5. Reviewer Microservice (Port 8003)
6. Learner Microservice (Port 8004)


Internet 
   │
   ▼ (Port 8000)
┌───────────────────────┐
│  1. GATEWAY SERVICE   │ 🛡️ Security Border
│  FastAPI              │ • Validates GitHub HMAC SHA-256 signature
└──────────┬────────────┘ • Rejects fake requests immediately (401 Unauthorized)
           ▼ HTTP POST
┌───────────────────────┐
│  2. WEBHOOK SERVICE   │ 🪝 Ingestion & Dedup
│  FastAPI + Postgres   │ • Parses PR number, commit SHA, repo name
└──────────┬────────────┘ • Deduplicates & writes PR to DB ('pending')
           │              • Returns HTTP 202 to GitHub immediately (<1 sec)
           ▼ Pushes job
      [REDIS QUEUE] ── Celery Worker ──┐
                                        ▼ HTTP POST (Port 8002)
                             ┌────────────────────────┐
                             │3. ORCHESTRATOR SERVICE │ 🧠 AI Brain
                             │   FastAPI + LangGraph  │ • Fetches git diff from GitHub API
                             └──────────┬─────────────┘ • Loads past repo patterns from DB
                                        │               • Runs 4 AI agents in parallel
                                        │               • Stores findings in DB
                                        ▼ HTTP POST (Port 8003)
                             ┌────────────────────────┐
                             │  4. REVIEWER SERVICE   │ 💬 GitHub Integration
                             │  FastAPI + GitHub App  │ • Signs JWT & gets installation token
                             └──────────┬─────────────┘ • Posts inline comments on PR diff lines
                                        │               • Updates PR status to 'reviewed'
                                        ▼ (When PR is Merged)
                             ┌────────────────────────┐
                             │   5. LEARNER SERVICE   │ 📈 Continuous Learning
                             │   FastAPI + Celery     │ • Extracts frequent warning/error issues
                             └────────────────────────┘ • Upserts into 'patterns' table


Part 2: Building Microservice 1 — The Gateway Service
Why does the Gateway exist?
When your webhook endpoint is exposed to the public internet, anyone can send fake POST requests claiming: "Hey, review PR #999".

To prevent this:

When configuring a GitHub Webhook, you define a Webhook Secret (e.g., my_secret_token).
Every time GitHub sends a payload, it hashes the payload using HMAC SHA-256 with your secret and sends the hash in the HTTP header: X-Hub-Signature-256: sha256=abcdef123456...
The Gateway computes the HMAC hash of the incoming request body using the same secret.
If the signatures match (hmac.compare_digest), it forwards the request internally to http://webhook:8001/events.
If they don't match, it throws 401 Unauthorized and drops the request.


1. take the . meta. payload from req
2. compute SHA256 of that body and compare with what the github sent to me in req.  
3. forward it to internal webhook serive using httpx

4. Use a constant-time comparison
