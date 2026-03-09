FROM odoo:latest

USER root
RUN pip3 install --no-cache-dir --break-system-packages "pydevd-pycharm~=253.0"

USER odoo