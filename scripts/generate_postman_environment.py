import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"
OUT_FILE = BASE_DIR / "ZeroWasteAI.postman_environment.json"


def read_env_defaults():
    defaults = {
        "base_url": "http://localhost:3000",
        "internal_secret": "",
        "jwt": "",
    }
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("\r")
            if k == "INTERNAL_SECRET_KEY":
                defaults["internal_secret"] = v
            if k == "PORT":
                try:
                    port = int(v)
                    defaults["base_url"] = f"http://localhost:{port}"
                except ValueError:
                    pass
    return defaults


def build_environment(name: str, values: dict):
    now = datetime.now(timezone.utc).isoformat()
    idem = str(uuid.uuid4())
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "values": [
            {"key": "base_url", "value": values.get("base_url", "http://localhost:3000"), "type": "default", "enabled": True},
            {"key": "jwt", "value": values.get("jwt", ""), "type": "secret", "enabled": True},
            {"key": "internal_secret", "value": values.get("internal_secret", ""), "type": "secret", "enabled": True},
            {"key": "firebase_id_token", "value": "", "type": "secret", "enabled": True},
            {"key": "idempotency_key", "value": idem, "type": "default", "enabled": True},
        ],
        "_postman_variable_scope": "environment",
        "_postman_exported_at": now,
        "_postman_exported_using": "Codex CLI Generator",
    }


def main():
    defaults = read_env_defaults()
    env = build_environment("ZeroWasteAI Local", defaults)
    OUT_FILE.write_text(json.dumps(env, indent=2), encoding="utf-8")
    print(f"Environment written to: {OUT_FILE}")


if __name__ == "__main__":
    main()
