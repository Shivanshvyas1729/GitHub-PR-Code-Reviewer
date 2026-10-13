created db 

set alembic.ini env.py and versions using 

uvx alembic init -t async migrations

task of alembic 1. data versioning 2. data migration 
For building this project (**FastAPI + SQLAlchemy + PostgreSQL**), you **do not need to read the entire Alembic documentation**. 

You only need about **15–20% of Alembic** (the 80/20 rule) to handle 95% of your project's database needs.

Here is the exact breakdown of **what you must know**, **the commands you will use**, and **what you can ignore**.

---

### 1. The 5 Core Concepts You Must Know

| # | Concept | What it means for your project |
|---|---|---|
| **1** | **`Base.metadata` in `env.py`** | How Alembic knows your tables exist. In `migrations/env.py`, you point `target_metadata = Base.metadata` from your SQLAlchemy models. |
| **2** | **Dynamic DB URL** | How Alembic connects to Postgres securely without hardcoding passwords in `alembic.ini` (reading `DATABASE_URL` from `.env`). |
| **3** | **Autogenerate** | Alembic compares your SQLAlchemy models against the actual PostgreSQL schema and writes the migration script for you. |
| **4** | **`upgrade()` & `downgrade()`** | Every migration file has two functions: `upgrade()` (applies changes) and `downgrade()` (undoes them). |
| **5** | **The `alembic_version` table** | A single 1-row table Alembic creates in PostgreSQL to track which migration hash is currently applied. |

---

### 2. The Only 4 Commands You Will Actually Use

In day-to-day development, you will only use these 4 commands:

```powershell
# 1. Create a migration after modifying your SQLAlchemy models
alembic revision --autogenerate -m "create pull_requests and reviews tables"

# 2. Apply the migration to your database
alembic upgrade head

# 3. Roll back the last migration (if you made a mistake)
alembic downgrade -1

# 4. Check the current migration version applied in the database
alembic current
```

---

### 3. The 3 "Gotchas" You Must Be Careful About

Alembic's autogenerate is smart, but not perfect. You should know:

1. **Renaming a column:** Alembic thinks you **dropped** the old column and **created** a new one (which will delete existing data). You have to manually edit the migration file to use `op.alter_column('table', 'old_name', new_column_name='new_name')`.
2. **Postgres Enums & UUIDs:** Custom Postgres types sometimes need to be imported manually in the generated migration file.
3. **Always inspect the migration file:** Never run `alembic upgrade head` immediately after `--autogenerate`. Open the generated file in `migrations/versions/` and verify that `upgrade()` and `downgrade()` make sense.

---

### 4. What You Can Safely IGNORE Right Now

Do **not** waste time reading about:
* ❌ Alembic branches, joins, and merge trees (`alembic merge`, multiple heads) — only needed in large teams with 10+ devs making conflicting migrations simultaneously.
* ❌ Offline migrations (`--sql` dump mode) — only needed if your company's DBA requires raw SQL scripts.
* ❌ Custom migration script templates (`script.py.mako` customization).
* ❌ Alembic internal Operations API.

---

### 💡 Summary: Recommended 10-Minute Next Step

Instead of reading extensive docs, your next practical steps are:
1. Define your SQLAlchemy models (e.g., `PullRequest`, `ReviewComment`, `Repository`).
2. Wire `target_metadata = Base.metadata` in [`migrations/env.py`](file:///c:/Users/DELL/Desktop/git_hub_code_reviewer/migrations/env.py).
3. Run `alembic revision --autogenerate -m "initial schema"` to generate your first real migration file.


Here is a simple, clear explanation of **PostgreSQL** and **SQLAlchemy**—their purpose, why you need them, and how they connect to Alembic in your GitHub PR Code Reviewer project:

---

### 1. 🗄️ PostgreSQL (The Database Engine)

#### **What it is:**
PostgreSQL is the **storage engine** running on your server (or AWS RDS). It is where data actually lives on disk.

#### **Purpose in your project:**
* **Persistent Storage:** Stores PR records, review comments, bot analysis results, and repo configs permanently.
* **Deduplication:** Uses unique indexes (e.g., commit `SHA` + `PR Number`) so your bot doesn't review the same commit twice.
* **JSONB Support:** GitHub webhooks and LangGraph AI agent outputs are large JSON structures. PostgreSQL has native, indexed JSON storage (`JSONB`).
* **ACID Transactions:** Ensures that if saving a review fails midway, the database rolls back cleanly without leaving corrupted or partial data.

#### **Why you need it:**
> Without a database like PostgreSQL, everything your bot learns, reviews, or processes would disappear from RAM every time your FastAPI app restarts.

---

### 2. 🐍 SQLAlchemy (The Python ORM & Query Builder)

#### **What it is:**
SQLAlchemy is the bridge between your **Python code** and **PostgreSQL**. It is an **ORM** (*Object-Relational Mapper*).

#### **Purpose in your project:**
* **Write Python, not raw SQL strings:** Instead of writing messy SQL queries by hand:
  ```python
  # ❌ Without SQLAlchemy (Raw SQL - prone to typos & SQL injection):
  cursor.execute("SELECT * FROM pull_requests WHERE repo_name = %s", (repo,))

  # ✅ With SQLAlchemy (Clean Python objects):
  result = await session.execute(select(PullRequest).where(PullRequest.repo == repo))
  ```
* **Define Database Tables as Python Classes:**
  ```python
  class PullRequest(Base):
      __tablename__ = "pull_requests"

      id = Column(Integer, primary_key=True)
      repo_name = Column(String, index=True)
      pr_number = Column(Integer)
      commit_sha = Column(String, unique=True)
      status = Column(String, default="pending")
  ```
* **Async Performance:** Paired with `asyncpg`, SQLAlchemy lets FastAPI execute queries non-blockingly, handling thousands of webhook requests concurrently.
* **Security:** Automatically sanitizes queries against SQL injection attacks.

#### **Why you need it:**
> Without SQLAlchemy, you would have to write, maintain, and sanitize hundreds of lines of raw SQL queries manually, and convert SQL query results into Python dictionaries by hand.

---

### 3. 🧩 How PostgreSQL + SQLAlchemy + Alembic Work Together

Think of them like this:

| Tool | Real-World Analogy | Role in your Project |
| :--- | :--- | :--- |
| **PostgreSQL** | 🏢 **The Secure Warehouse** | Stores the physical tables and data on disk. |
| **SQLAlchemy** | 🗣️ **The Translator** | Translates Python code into SQL queries and converts database rows back into Python objects. |
| **Alembic** | 📐 **The Architect** | Modifies the layout of the warehouse (adds columns, creates new tables) over time **without destroying existing data**. |

---

### In Summary:
* **PostgreSQL** holds the data.
* **SQLAlchemy** lets your FastAPI app read and write that data using Python.
* **Alembic** evolves the database structure as your SQLAlchemy models change over time.