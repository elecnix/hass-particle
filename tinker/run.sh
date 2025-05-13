#!/usr/bin/with-contenv bashio

export INGRESS_PATH=$(bashio::addon.ingress_url)
exec /.venv/bin/python /daemon.py
