"""Read-only PNCP buyer catalogue based on the LICITACAO source snapshot."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from typing import Any

import httpx

GITHUB_API = "https://api.github.com"
PNCP_API = "https://pncp.gov.br/api/pncp/v1"
SOURCE_REPOSITORY = os.getenv("LICITACAO_REPOSITORY", "carlos-andrade/LICITACAO")
SOURCE_REF = os.getenv("LICITACAO_REF", "main")
SNAPSHOT_PATH = "EDITAIS/pncp-editais-abertos.json"
METADATA_PATH = "EDITAIS/pncp-editais-metadados.json"


class BuyerCatalogError(RuntimeError):
    pass


def _cnpj_valid(value: str) -> bool:
    """Validate numeric and alphanumeric CNPJ check digits (RFB alphanumeric layout)."""
    value = re.sub(r"[^0-9A-Z]", "", value.upper())
    if not re.fullmatch(r"[0-9A-Z]{12}[0-9]{2}", value):
        return False
    numbers = [ord(char) - 48 for char in value]
    if len(set(value)) == 1:
        return False
    def digit(values: list[int], weights: list[int]) -> int:
        remainder = sum(a * b for a, b in zip(values, weights)) % 11
        return 0 if remainder < 2 else 11 - remainder
    first = digit(numbers[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
    second = digit(numbers[:12] + [first], [6,5,4,3,2,9,8,7,6,5,4,3,2])
    return numbers[-2:] == [first, second]


class GitHubSnapshot:
    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_TOKEN", "").strip()
        if not self.token:
            raise BuyerCatalogError("GITHUB_TOKEN não configurado no backend.")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def read(self, path: str) -> tuple[bytes, str]:
        url = f"{GITHUB_API}/repos/{SOURCE_REPOSITORY}/contents/{path}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=self.headers, params={"ref": SOURCE_REF})
        if response.status_code in (401, 403):
            raise BuyerCatalogError("GitHub recusou o acesso de leitura à fonte LICITACAO.")
        if response.status_code == 404:
            raise BuyerCatalogError("Artefacto do catálogo não encontrado na fonte.")
        if response.is_error:
            raise BuyerCatalogError(f"Falha ao consultar GitHub (HTTP {response.status_code}).")
        payload = response.json()
        if payload.get("type") != "file" or payload.get("encoding") != "base64":
            raise BuyerCatalogError("Formato inesperado no artefacto de origem.")
        raw = base64.b64decode(payload["content"])
        return raw, str(payload.get("sha", ""))


async def _snapshot() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    source = GitHubSnapshot()
    raw, blob = await source.read(SNAPSHOT_PATH)
    meta_raw, meta_blob = await source.read(METADATA_PATH)
    try:
        records = json.loads(raw)
        metadata = json.loads(meta_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BuyerCatalogError("JSON do snapshot ou metadados inválidos.") from exc
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise BuyerCatalogError("O snapshot não contém uma lista de contratações.")
    provenance = {
        "repository": SOURCE_REPOSITORY,
        "ref": SOURCE_REF,
        "snapshot_path": SNAPSHOT_PATH,
        "snapshot_blob_sha": blob,
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "metadata_path": METADATA_PATH,
        "metadata_blob_sha": meta_blob,
        "metadata_sha256": hashlib.sha256(meta_raw).hexdigest(),
        "access_mode": "read_only",
    }
    return records, metadata, provenance


def _buyer_key(record: dict[str, Any]) -> str:
    return str((record.get("orgaoEntidade") or {}).get("cnpj") or "").strip().upper()


def _unit(record: dict[str, Any]) -> dict[str, Any] | None:
    unit = record.get("unidadeOrgao") or {}
    code = str(unit.get("codigoUnidade") or "").strip()
    name = str(unit.get("nomeUnidade") or "").strip()
    if not (code or name):
        return None
    uf = str(unit.get("ufSigla") or unit.get("uf") or "").strip().upper()
    municipio = str(unit.get("municipioNome") or "").strip()
    return {
        "code": code,
        "key": "|".join((code, uf, municipio, name)),
        "name": name,
        "uf": uf,
        "municipio": municipio,
        "codigo_ibge": str(unit.get("codigoIbge") or "").strip(),
    }


async def list_buyers(q: str = "", uf: str = "", municipio: str = "", page: int = 1, page_size: int = 20) -> dict[str, Any]:
    records, metadata, provenance = await _snapshot()
    grouped: dict[str, dict[str, Any]] = {}
    for record in records:
        cnpj = _buyer_key(record)
        if not cnpj:
            continue
        org = record.get("orgaoEntidade") or {}
        buyer = grouped.setdefault(cnpj, {
            "cnpj": cnpj,
            "name": str(org.get("razaoSocial") or "").strip(),
            "cnpj_valid": _cnpj_valid(cnpj),
            "units": {},
            "contract_count": 0,
        })
        buyer["contract_count"] += 1
        unit = _unit(record)
        if unit:
            key = unit["key"]
            buyer["units"].setdefault(key, {**unit, "contract_count": 0})
            buyer["units"][key]["contract_count"] += 1
    query = q.casefold().strip()
    rows = []
    for buyer in grouped.values():
        units = list(buyer["units"].values())
        matching_units = [u for u in units if (not uf or u["uf"] == uf.upper()) and (not municipio or municipio.casefold() in u["municipio"].casefold())]
        if (uf or municipio) and not matching_units:
            continue
        haystack = " ".join([buyer["cnpj"], buyer["name"], *(u["name"] for u in units), *(u["municipio"] for u in units)]).casefold()
        if query and query not in haystack:
            continue
        visible_units = matching_units if (uf or municipio) else units
        rows.append({
            **buyer,
            "units": visible_units,
            "unit_count": len(visible_units),
            "contract_count": sum(unit["contract_count"] for unit in visible_units) if (uf or municipio) else buyer["contract_count"],
        })
    rows.sort(key=lambda item: (item["name"].casefold(), item["cnpj"]))
    total = len(rows)
    start = (page - 1) * page_size
    return {
        "status": "PARTIAL_SOURCE_SNAPSHOT",
        "coverage": "PARTIAL",
        "summary": {"buyers": total, "units": sum(row["unit_count"] for row in rows), "contracts": sum(row["contract_count"] for row in rows)},
        "pagination": {"page": page, "page_size": page_size, "total": total, "pages": (total + page_size - 1) // page_size},
        "buyers": [{**row, "units": list(row["units"].values()) if isinstance(row["units"], dict) else row["units"]} for row in rows[start:start + page_size]],
        "source": {"capture_status": metadata.get("status"), "captured_at": metadata.get("capturado_em_utc"), "records": metadata.get("registros_unicos_capturados"), "modality": metadata.get("codigoModalidadeContratacao"), **provenance},
    }


async def list_unit_contracts(cnpj: str, unit_code: str) -> dict[str, Any]:
    records, metadata, provenance = await _snapshot()
    wanted = cnpj.strip().upper()
    contracts = []
    for record in records:
        if _buyer_key(record) != wanted:
            continue
        unit = _unit(record) or {}
        if unit.get("key") != unit_code:
            continue
        contracts.append({
            "control_id": record.get("numeroControlePNCP"),
            "cnpj": wanted,
            "year": record.get("anoCompra"),
            "sequence": record.get("sequencialCompra"),
            "number": record.get("numeroCompra"),
            "process": record.get("processo"),
            "object": record.get("objetoCompra"),
            "status": record.get("situacaoCompraNome"),
            "published_at": record.get("dataPublicacaoPncp"),
            "proposal_end": record.get("dataEncerramentoProposta"),
            "estimated_value": record.get("valorTotalEstimado"),
            "homologated_value": record.get("valorTotalHomologado"),
            "unit": unit,
            "pncp_url": _pncp_url(record),
        })
    return {"status": "PARTIAL_SOURCE_SNAPSHOT", "contracts": contracts, "source": {"captured_at": metadata.get("capturado_em_utc"), **provenance}}


def _pncp_url(record: dict[str, Any]) -> str | None:
    control = str(record.get("numeroControlePNCP") or "")
    match = re.fullmatch(r"([0-9A-Z]{14})-([0-9]+)-([0-9]+)/([0-9]{4})", control)
    if not match:
        return None
    cnpj, _modality, sequence, year = match.groups()
    return f"https://pncp.gov.br/app/editais/{cnpj}/{year}/{int(sequence)}"


async def fetch_contract_items(cnpj: str, year: int, sequence: int) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9A-Z]{12}[0-9]{2}", cnpj.upper()) or year < 2000 or sequence < 1:
        raise BuyerCatalogError("Identificador da contratação inválido.")
    url = f"{PNCP_API}/orgaos/{cnpj.upper()}/compras/{year}/{sequence}/itens"
    items = []
    total_pages = 1
    async with httpx.AsyncClient(timeout=30.0, headers={"Accept": "application/json", "User-Agent": "SISTEMA-WEB/1.0"}) as client:
        for page in range(1, 101):
            response = await client.get(url, params={"pagina": page, "tamanhoPagina": 100})
            if response.status_code == 404:
                raise BuyerCatalogError("A API do PNCP não encontrou os itens desta contratação.")
            if response.status_code == 429:
                raise BuyerCatalogError("Limite temporário da API do PNCP atingido; tente novamente.")
            if response.is_error:
                raise BuyerCatalogError(f"Falha na consulta de itens ao PNCP (HTTP {response.status_code}).")
            payload = response.json()
            data: Any = payload
            if isinstance(payload, dict):
                for key in ("data", "resultado", "content", "items", "itens"):
                    if isinstance(payload.get(key), list):
                        data = payload[key]
                        break
                try:
                    total_pages = int(payload.get("totalPaginas") or payload.get("totalPages") or total_pages)
                except (TypeError, ValueError):
                    pass
            if not isinstance(data, list):
                raise BuyerCatalogError("Formato de resposta de itens não reconhecido.")
            items.extend(item for item in data if isinstance(item, dict))
            if page >= total_pages or not data or len(data) < 100:
                break
    if total_pages > 100:
        raise BuyerCatalogError("A contratação excede o limite de 100 páginas de itens.")
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "number": item.get("numeroItem"),
            "description": item.get("descricao"),
            "type": item.get("materialOuServicoNome") or item.get("materialOuServico"),
            "quantity": item.get("quantidade"),
            "unit": item.get("unidadeMedida"),
            "unit_estimated_value": item.get("valorUnitarioEstimado"),
            "total_estimated_value": item.get("valorTotal"),
            "budget_confidential": item.get("orcamentoSigiloso"),
            "status": item.get("situacaoCompraItemNome"),
            "award_criterion": item.get("criterioJulgamentoNome"),
            "benefit": item.get("tipoBeneficioNome"),
            "catalog_code": item.get("catalogoCodigoItem"),
            "ncm_nbs_code": item.get("ncmNbsCodigo"),
            "has_result": item.get("temResultado"),
        })
    return {"status": "LIVE_PNCP", "coverage": "CONTRACT_ITEMS_ONLY", "contract": {"cnpj": cnpj.upper(), "year": year, "sequence": sequence}, "items": normalized, "pagination": {"pages_fetched": min(total_pages, 100), "total_pages_reported": total_pages}, "source_url": url, "retrieved_from": "PNCP public API"}
