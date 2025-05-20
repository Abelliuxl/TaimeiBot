import json
import os

# 加载 config.json
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = config["token"]
VERIFY_TOKEN = config.get("verify_token")
ENCRYPT_TOKEN = config.get("encrypt_token")
