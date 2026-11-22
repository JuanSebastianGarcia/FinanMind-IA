"""Locates the Cloudflare D1 account/database ids and API token."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class D1Credentials:
    account_id: str
    database_id: str
    api_token: str

    def is_complete(self) -> bool:
        return all(v.strip() for v in (self.account_id, self.database_id, self.api_token))


class D1CredentialsStore:
    """Production reads ``%LOCALAPPDATA%\\Finanmind\\cloudflare_d1.json``.

    That file lives outside the executable and the workspace folder, and the token
    inside it is DPAPI-encrypted (only this Windows user can decrypt it). The
    installer builder writes it from the repo's ``cloudflare.env``.

    When running from source, ``CLOUDFLARE_*`` environment variables or the repo's
    ``cloudflare.env`` are accepted as a fallback.
    """

    FILENAME = "cloudflare_d1.json"
    ENV_FILENAME = "cloudflare.env"
    ENV_KEYS = ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_D1_DATABASE_ID", "CLOUDFLARE_API_TOKEN")

    @classmethod
    def path(cls) -> Path:
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / ".finanmind"
        return root / "Finanmind" / cls.FILENAME

    @classmethod
    def load(cls) -> D1Credentials | None:
        """Return the first complete set of credentials found, or None."""
        for loader in (cls._from_local_file, cls._from_environment, cls._from_repo_env_file):
            creds = loader()
            if creds is not None and creds.is_complete():
                return creds
        return None

    @classmethod
    def save(cls, creds: D1Credentials) -> Path:
        """Persist credentials for the production app (token DPAPI-encrypted)."""
        from finanmind.services.dpapi_secret_codec import DpapiSecretCodec

        target = cls.path()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "account_id": creds.account_id.strip(),
            "database_id": creds.database_id.strip(),
            "api_token": DpapiSecretCodec.encrypt(creds.api_token.strip()),
        }
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, target)
        return target

    @classmethod
    def read_env_file(cls, env_path: Path) -> D1Credentials | None:
        """Parse a ``KEY=value`` file such as the repo's ``cloudflare.env``."""
        if not env_path.is_file():
            return None
        values: dict[str, str] = {}
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")
        return cls._from_mapping(values)

    @classmethod
    def _from_local_file(cls) -> D1Credentials | None:
        target = cls.path()
        if not target.is_file():
            return None
        from finanmind.services.dpapi_secret_codec import DpapiSecretCodec

        data = json.loads(target.read_text(encoding="utf-8"))
        token = DpapiSecretCodec.decrypt(data.get("api_token", ""))
        return D1Credentials(data.get("account_id", ""), data.get("database_id", ""), token)

    @classmethod
    def _from_environment(cls) -> D1Credentials | None:
        return cls._from_mapping(dict(os.environ))

    @classmethod
    def _from_repo_env_file(cls) -> D1Credentials | None:
        if getattr(sys, "frozen", False):
            return None
        repo_root = Path(__file__).resolve().parents[3]
        return cls.read_env_file(repo_root / cls.ENV_FILENAME)

    @classmethod
    def _from_mapping(cls, values: dict[str, str]) -> D1Credentials | None:
        account, database, token = (values.get(k, "") for k in cls.ENV_KEYS)
        if not (account or database or token):
            return None
        return D1Credentials(account, database, token)
