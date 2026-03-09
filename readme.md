## Part 1: Daily Workflow

### Without Debugger (fast development)

Set `PYCHARM_DEBUG: "0"` in `docker-compose.yaml` or pass it as env var.

| Task                                           | Command                                                                                                      |
|------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| Start everything                               | `docker compose up -d`                                                                                       |
| See logs                                       | `docker compose logs -f web`                                                                                 |
| **Python changes** (models, controllers)       | `docker compose restart web`                                                                                 |
| **Python + update module** (new fields, views) | `docker compose run --rm web odoo -d <dbname> -u <module> --stop-after-init && docker compose restart web`   |
| **XML/view changes only**                      | Auto-reloaded thanks to `--dev xml` — just refresh browser                                                   |
| Stop everything                                | `docker compose down`                                                                                        |

### With Debugger

1. **Start** the **Python Debug Server** in PyCharm (the run config)
2. **Then** start the container:
   ```bash
   docker compose up -d
   ```
3. PyCharm console shows **"Connected"** — set breakpoints and use Odoo in browser
4. To **restart** Odoo while keeping debugger:
   - Stop the container: `docker compose stop web`
   - Make sure the debug server is still running in PyCharm (restart it if it stopped)
   - Start again: `docker compose start web`

> **Important:** PyCharm debug server must be running **before** the container starts.
> If the container starts and can't connect, it continues without the debugger
> (no crash, but no breakpoints).

### Switching Debug On/Off Without Editing Files

## Part 2: Setup for a New Project

### Required Files

Copy these files to your new project:
├── Dockerfile 
├── docker-compose.yaml 
├── docker_scripts/ 
│ ├── start-odoo.sh # must be chmod +x 
│ └── pycharm_attach.py # optional backup 
├── config/ 
│ └── odoo.conf 
└── odoo_pg_pass # postgres password file
### Step 1: Odoo Source (for breakpoints in core code)
```bash
bash git clone --depth 1 --branch 19.0 [https://github.com/odoo/odoo.git](https://github.com/odoo/odoo.git) src/odoo-19
```
### Step 2: PyCharm Run Configuration

Create a **Python Debug Server** configuration:

| Setting           | Value   |
|-------------------|---------|
| **IDE host name** | `0.0.0.0` |
| **Port**          | `8888`  |

### Step 3: Path Mappings (in the same run config)

| Local path                              | Remote path                                      |
|-----------------------------------------|--------------------------------------------------|
| `<project>/addons`                      | `/mnt/extra-addons`                              |
| `<project>/src/odoo-19/addons`          | `/usr/lib/python3/dist-packages/odoo/addons`     |
| `<project>/src/odoo-19/odoo`            | `/usr/lib/python3/dist-packages/odoo`            |

### Step 4: Linux Firewall (one-time per machine)
```bash
sudo iptables -I INPUT -i docker0 -p tcp --dport 8888 -j ACCEPT sudo iptables -I INPUT -i br-+ -p tcp --dport 8888 -j ACCEPT
```
### Step 5: Build and Run
```bash
docker compose up --build -d
```

### Environment Variables (docker-compose.yaml)

| Variable              | Default                | Description                                  |
|-----------------------|------------------------|----------------------------------------------|
| `PYCHARM_DEBUG`       | `1`                    | Enable/disable debugger attachment            |
| `PYCHARM_DEBUG_WAIT`  | `0`                    | `1` = suspend on connect (wait for PyCharm)   |
| `PYCHARM_DEBUG_HOST`  | `host.docker.internal` | Host where PyCharm listens                    |
| `PYCHARM_DEBUG_PORT`  | `8888`                 | Debug server port                             |

---

## Troubleshooting
| Problem                                   | Cause                                 | Fix                                                             |
|-------------------------------------------|---------------------------------------|-----------------------------------------------------------------|
| `TimeoutError: timed out`                 | Debug server not running or firewall  | Start debug server first; check `ss -tlnp \| grep 8888`; open firewall |
| `Couldn't apply path mapping`             | Missing or wrong path mapping         | Add all 3 mappings (addons, odoo/addons, odoo core)             |
| `settrace() unexpected keyword argument`  | `pydevd-pycharm` version mismatch    | Match version to PyCharm: `~=253.0` for 2025.3.x               |
| Breakpoints not hit                       | Debugger in wrong process             | Use `start-odoo.sh` approach (settrace + odoo.cli.main in one process) |
| Container continues without debugger      | Non-fatal try/except in settrace      | Check debug server is running; check firewall                   |

### Verify Connectivity from Container
```
docker compose exec web python3 -c
"import socket; s=socket.create_connection(('host.docker.internal', 8888), timeout=5); print('OK'); s.close()"
```

### Verify PyCharm Is Listening
```bash
ss -tlnp | grep 8888
```