import base64
import hashlib
import os
from dataclasses import dataclass
from typing import Any

import httpx
from jsonschema import Draft202012Validator, FormatChecker


GITHUB_API = "https://api.github.com"
SOURCE_REPO = os.getenv("LICITACAO_REPOSITORY", "carlos-andrade/LICITACAO")
SOURCE_REF = os.getenv("LICITACAO_REF", "main")
OPPORTUNITY_PATH = (
    "ARQUITETURA/exemplos/ufrj-2026-548-oportunidade.json"
)
OPPORTUNITY_SCHEMA_PATH = "ARQUITETURA/schemas/oportunidade.schema.json"


class SourceConfigurationError(RuntimeError):
    pass


class SourceAccessError(RuntimeError):
    pass


class SourceNotFoundError(RuntimeError):
    pass


class SourceValidationError(RuntimeError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("O registo de origem não passou na validação JSON Schema.")


@dataclass
class GitHubFile:
    content: bytes
    blob_sha: str
    path: str
    ref: str


class GitHubReadOnlySource:
    """Leitor estritamente read-only para ficheiros do repositório LICITACAO."""

    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_TOKEN", "").strip()
        self.repository = SOURCE_REPO
        self.ref = SOURCE_REF

    def _headers(self) -> dict[str, str]:
        if not self.token:
            raise SourceConfigurationError(
                "GITHUB_TOKEN não configurado no backend."
            )
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _get_json(self, path: str) -> dict[str, Any]:
        url = f"{GITHUB_API}/repos/{self.repository}/contents/{path}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers=self._headers(),
                params={"ref": self.ref},
            )
        if response.status_code == 404:
            raise SourceNotFoundError("Ficheiro não encontrado na fonte.")
        if response.status_code in (401, 403):
            raise SourceAccessError(
                "GitHub recusou o acesso. Verifique permissões Contents: read."
            )
        if response.status_code == 429 or response.status_code >= 500:
            raise SourceAccessError("GitHub temporariamente indisponível.")
        if response.is_error:
            raise SourceAccessError(
                f"Falha na consulta GitHub (HTTP {response.status_code})."
            )
        return response.json()

    async def read_file(self, path: str) -> GitHubFile:
        payload = await self._get_json(path)
        if payload.get("type") != "file":
            raise SourceNotFoundError("O caminho indicado não é um ficheiro.")
        if payload.get("encoding") != "base64":
            raise SourceAccessError("Formato de conteúdo GitHub não suportado.")
        try:
            content = base64.b64decode(payload["content"], validate=False)
        except (KeyError, ValueError) as exc:
            raise SourceAccessError("Não foi possível descodificar o ficheiro.") from exc
        return GitHubFile(
            content=content,
            blob_sha=str(payload.get("sha", "")),
            path=path,
            ref=self.ref,
        )

    async def repository_status(self) -> dict[str, Any]:
        url = f"{GITHUB_API}/repos/{self.repository}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=self._headers())
        if response.status_code in (401, 403, 404):
            raise SourceAccessError(
                "Não foi possível ler o repositório. Confirme token e acesso."
            )
        if response.is_error:
            raise SourceAccessError(
                f"Falha na consulta GitHub (HTTP {response.status_code})."
            )
        data = response.json()
        return {
            "repository": data.get("full_name"),
            "private": data.get("private"),
            "default_branch": data.get("default_branch"),
            "configured_ref": self.ref,
            "access": "read_only",
        }


async def read_reference_opportunity() -> dict[str, Any]:
    source = GitHubReadOnlySource()
    record_file = await source.read_file(OPPORTUNITY_PATH)
    schema_file = await source.read_file(OPPORTUNITY_SCHEMA_PATH)

    import json

    try:
        record = json.loads(record_file.content)
        schema = json.loads(schema_file.content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceValidationError(["JSON de origem ou schema inválido."]) from exc

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = [
            f"{'/'.join(str(part) for part in error.absolute_path) or '$'}: "
            f"{error.message}"
            for error in errors[:20]
        ]
        raise SourceValidationError(details)

    return {
        "data": record,
        "provenance": {
            "repository": source.repository,
            "ref": record_file.ref,
            "path": record_file.path,
            "blob_sha": record_file.blob_sha,
            "content_sha256": hashlib.sha256(record_file.content).hexdigest(),
            "schema_path": schema_file.path,
            "schema_blob_sha": schema_file.blob_sha,
            "validation": "valid",
            "access_mode": "read_only",
        },
    }
