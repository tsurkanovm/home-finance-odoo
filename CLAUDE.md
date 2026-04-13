## Project: Home Finance (Odoo 19)
- **Stack**: Odoo 19.0 Community · Python 3.12 · PostgreSQL 18 · Docker
- **Addons path**: `./addons/` (mounted as `/mnt/extra-addons`)
- **Custom addons**: `home_finance` (14 models + 1 wizard), `nbu_currency_rate` (2 models + 1 wizard)
- **DB**: `home_finance` (user: `odoo`)

## Non-Obvious Architecture Facts
- `home_finance.document` is an **abstract model** — never instantiated directly; `transaction` and `transfer` inherit it
- **Period = last day of the month** always. Enforced in `document.create/write` via `get_month_end_date()` in `utils/date_utils.py`
- `current_period` stored in `ir.config_parameter` key `home_finance.current_period`; read via `get_current_period(self)` from `utils/date_utils.py`
- `wallet.balance` stores **computed snapshots** (not live) — triggered by cron or the recalculate wizard
- `statement.import` is a **persistent record** (not a wizard) with a two-step flow: `action_parse()` → `action_convert()`
- Constants (movement types, wallet types) live in `addons/home_finance/constant.py`

## Deploy Workflow

### Standard deploy (Python/XML changes, no new models or fields)
```bash
git pull
docker compose restart web
docker compose logs -f web          # wait for: HTTP service (werkzeug) running on 0.0.0.0:8069
```

### Deploy with new models, fields, views, or security CSV rows
```bash
git pull
docker compose exec web odoo -u home_finance --stop-after-init
# if nbu_currency_rate also changed:
# docker compose exec web odoo -u home_finance,nbu_currency_rate --stop-after-init
docker compose up -d web
docker compose logs -f web          # wait for: HTTP service (werkzeug) running on 0.0.0.0:8069
```

### Deploy with Dockerfile or requirements.txt changes
```bash
git pull
docker compose build && docker compose up -d
docker compose logs -f web
```

### When to use which deploy
| Change type                    | Action required                                          |
|--------------------------------|----------------------------------------------------------|
| XML view edits only            | `restart web`                                            |
| Python logic changes           | `restart web`                                            |
| New model / new field          | `-u {addon} --stop-after-init` → `up -d web`            |
| New XML data file              | `-u {addon} --stop-after-init` → `up -d web`            |
| New security CSV row           | `-u {addon} --stop-after-init` → `up -d web`            |
| Dockerfile / requirements.txt  | `build && up -d`                                         |

## Commands
```bash
docker compose up -d                                                    # start all services
docker compose down                                                     # stop (preserves volumes)
docker compose restart web                                              # restart Odoo (Python changes)
docker compose build && docker compose up -d                           # rebuild image + restart
docker compose logs -f web                                             # follow Odoo logs
docker compose logs --tail=200 web                                     # last 200 lines
docker compose exec web bash                                           # shell into Odoo container
docker compose exec web odoo -u home_finance --stop-after-init        # upgrade module
docker compose exec db psql -U odoo -d home_finance                   # PostgreSQL shell
```

## Troubleshooting

### Container won't start after deploy
```bash
docker compose logs web 2>&1 | grep -A 10 "ERROR\|Traceback\|SyntaxError\|ImportError"
```
Common causes: syntax error in a new Python file, missing import in `__init__.py`, missing manifest `data` entry.

### Module upgrade fails
1. Check logs for the first `ERROR` line — it names the file and line
2. If `psycopg2.errors` — a DB constraint failed; check `models.Constraint` definitions
3. If `AccessError` — new model missing row in `ir.model.access.csv`

### Log pattern reference
| Pattern                  | Meaning                                        |
|--------------------------|------------------------------------------------|
| `ERROR odoo.`            | Python exception                               |
| `Traceback (most recent` | Stack trace follows — read to the bottom       |
| `psycopg2.errors`        | PostgreSQL constraint violation                |
| `AccessError`            | Missing security rule for a model              |
| `ValidationError`        | `@api.constrains` fired                        |
| `UserError`              | Explicit business logic rejection              |

## AI Assistant Rules
- **Ask before any task requiring 3+ LLM sub-requests** — clarify scope first
- Always mention **file paths** when referencing code
- Always mention **which deploy type** is needed after a change (see Deploy Workflow table above)
- Warn about **access rights** issues proactively (new models need `ir.model.access.csv` rows)
- Use **Magento 2 / 1C analogies** when explaining Odoo concepts (developer background)