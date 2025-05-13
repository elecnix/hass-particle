import os
import logging
from flask import Flask, request, jsonify
import signal
import sys
import requests
import json
from threading import Thread
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("particle_daemon")

OPTIONS_PATH = "/data/options.json"
API_URL = "https://api.particle.io/v1/integrations"

def get_config():
    try:
        with open(OPTIONS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {OPTIONS_PATH}: {e}")
        return {}

def register_particle_webhook():
    config = get_config()
    PARTICLE_AUTH = config.get("PARTICLE_AUTH")
    PARTICLE_EVENT = config.get("PARTICLE_EVENT", "spark/status")
    HASS_PUBLIC_URL = config.get("HASS_PUBLIC_URL")
    INGRESS_PATH = os.environ.get("INGRESS_PATH")
    from urllib.parse import urljoin
    if HASS_PUBLIC_URL and INGRESS_PATH:
        # Concatenate ingress path and 'webhook', then join with public URL
        full_path = INGRESS_PATH.rstrip('/') + '/webhook'
        WEBHOOK_URL = urljoin(HASS_PUBLIC_URL.rstrip('/') + '/', full_path.lstrip('/'))
    else:
        WEBHOOK_URL = None
    if not PARTICLE_AUTH or not WEBHOOK_URL:
        logger.warning("Skipping webhook registration: PARTICLE_AUTH or WEBHOOK_URL not set.")
        return
    headers = {"Authorization": f"Bearer {PARTICLE_AUTH}"}
    webhook_file = "/data/webhook_id.json"
    webhook_id = None
    # Define data early so it's available for both update and create
    data = {
        "integration_type": "Webhook",
        "event": PARTICLE_EVENT,
        "url": WEBHOOK_URL,
        "requestType": "POST",
    }
    # Check if webhook_id.json exists
    if os.path.exists(webhook_file):
        try:
            with open(webhook_file, "r") as f:
                webhook_info = json.load(f)
                webhook_id = webhook_info.get("id")
            if webhook_id:
                get_url = f"https://api.particle.io/v1/webhooks/{webhook_id}"
                resp = requests.get(get_url, headers=headers)
                if resp.ok:
                    logger.info(f"Webhook {webhook_id} already exists on Particle Cloud. Will update with latest config.")
                    # Update the webhook with a PUT request
                    update_url = f"https://api.particle.io/v1/integrations/{webhook_id}"
                    try:
                        update_resp = requests.put(update_url, headers=headers, data=data)
                        if update_resp.ok:
                            logger.info(f"Webhook {webhook_id} updated successfully: {update_resp.json()}")
                        else:
                            logger.warning(f"Failed to update webhook {webhook_id}: {update_resp.status_code} {update_resp.text}")
                    except Exception as e:
                        logger.error(f"Exception during webhook update: {e}")
                    return
                else:
                    logger.warning(f"Webhook ID {webhook_id} not found on Particle Cloud (status {resp.status_code}), will re-create.")
        except Exception as e:
            logger.error(f"Error reading or verifying existing webhook_id.json: {e}")
    # Create webhook
    data = {
        "integration_type": "Webhook",
        "event": PARTICLE_EVENT,
        "url": WEBHOOK_URL,
        "requestType": "POST",
    }
    try:
        logger.info(f"Registering Particle webhook for event '{PARTICLE_EVENT}' to '{WEBHOOK_URL}'...")
        response = requests.post(API_URL, headers=headers, data=data)
        if response.ok:
            resp_json = response.json()
            logger.info(f"Webhook registered successfully: {resp_json}")
            webhook_id = resp_json.get("id")
            if webhook_id:
                with open(webhook_file, "w") as f:
                    f.write(json.dumps(resp_json))
                logger.info(f"Stored webhook ID to webhook_id.json: {webhook_id}")
        else:
            logger.warning(f"Failed to register webhook: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Exception during webhook registration: {e}")

# Watchdog event handler to reload config and re-register webhook on change
class ConfigChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == OPTIONS_PATH:
            logger.info(f"Detected change in {OPTIONS_PATH}, re-registering webhook...")
            register_particle_webhook()

def start_config_watcher():
    event_handler = ConfigChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(OPTIONS_PATH), recursive=False)
    observer.start()
    logger.info(f"Started watcher for {OPTIONS_PATH}")
    return observer

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.json
    logger.info(f"Received Particle event: {event}")
    return jsonify({"status": "received"}), 200

@app.route('/')
def index():
    return "Particle Home Assistant Addon running.", 200

def handle_shutdown(signalnum, frame):
    logger.info("Shutting down daemon...")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    observer = start_config_watcher()
    try:
        register_particle_webhook()  # Initial registration
        port = int(os.environ.get("PORT", 8099))
        logger.info(f"Starting Flask server on port {port}")
        app.run(host='0.0.0.0', port=port)
    finally:
        observer.stop()
        observer.join()
