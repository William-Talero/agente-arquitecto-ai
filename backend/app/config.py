"""Configuración cargada desde variables de entorno / archivo .env."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_RAIZ_BACKEND = Path(__file__).resolve().parent.parent


def _flag(nombre: str, defecto: str = "true") -> bool:
    return os.getenv(nombre, defecto).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    project_endpoint: str = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
    model: str = os.getenv("FOUNDRY_MODEL", "gpt-4.1-mini")

    web_search_enabled: bool = _flag("WEB_SEARCH_ENABLED")
    learn_mcp_enabled: bool = _flag("LEARN_MCP_ENABLED")
    learn_mcp_url: str = os.getenv("LEARN_MCP_URL", "https://learn.microsoft.com/api/mcp")

    # Lineamientos propios del negocio (documentos que personalizan las reglas).
    lineamientos_dir: Path = Path(
        os.getenv("LINEAMIENTOS_DIR", str(_RAIZ_BACKEND / "data" / "lineamientos"))
    )
    lineamientos_max_chars_doc: int = int(os.getenv("LINEAMIENTOS_MAX_CHARS_DOC", "40000"))
    lineamientos_max_chars_prompt: int = int(os.getenv("LINEAMIENTOS_MAX_CHARS_PROMPT", "12000"))

    # SPA compilado servido por el backend en producción (mismo origen que la API).
    frontend_dist: Path = Path(os.getenv("FRONTEND_DIST", str(_RAIZ_BACKEND / "webroot")))


settings = Settings()
