#!/bin/bash
set -e

echo "PYCHARM_DEBUG=${PYCHARM_DEBUG:-0} WAIT=${PYCHARM_DEBUG_WAIT:-0}"
echo "DEV_MODE=${ODOO_DEV_MODE:-xml}"

ODOO_ARGS=(
  --config /etc/odoo/odoo.conf
)

if [ -n "${ODOO_DEV_MODE}" ]; then
  ODOO_ARGS+=(--dev "${ODOO_DEV_MODE}")
fi

if [ "${PYCHARM_DEBUG:-0}" = "1" ]; then
    exec python3 -c "
import os
import sys
import pydevd_pycharm

host = os.environ.get('PYCHARM_DEBUG_HOST', 'host.docker.internal')
port = int(os.environ.get('PYCHARM_DEBUG_PORT', '8888'))
suspend = os.environ.get('PYCHARM_DEBUG_WAIT', '0') == '1'

sys.argv = [
    'odoo',
    '--config', '/etc/odoo/odoo.conf',
]

dev_mode = os.environ.get('ODOO_DEV_MODE', '')
if dev_mode:
    sys.argv.extend(['--dev', dev_mode])

pydevd_pycharm.settrace(
    host,
    port=port,
    suspend=suspend,
    patch_multiprocessing=True
)

import odoo.cli
odoo.cli.main()
"
else
    exec /usr/bin/odoo "${ODOO_ARGS[@]}"
fi