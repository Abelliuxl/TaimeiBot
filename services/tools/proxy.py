import os
import json
from typing import Optional

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "config.json")


def get_proxy() -> Optional[str]:
    proxy = os.environ.get("https_proxy") or os.environ.get("http_proxy")
    if proxy:
        return proxy
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                cfg = json.load(f)
            return cfg.get("proxy") or None
    except Exception:
        pass
    return None
