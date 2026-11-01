#!/usr/bin/env python3
"""Audita snapshot PNCP do LICITACAO em modo exclusivamente read-only.

Requisitos: Python 3.10+ (biblioteca padrão).
Variável obrigatória: GITHUB_TOKEN com Contents: Read-only e Metadata: Read-only
Uso: GITHUB_TOKEN=... python3 scripts/audit_licitacao_snapshot.py
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone

OWNER = "carlos-andrade"
REPO = "LICITACAO"
REF = "main"
ROOT = f"https://api.github.com/repos/{OWNER}/{REPO}"
FILES = [
    "EDITAIS/pncp-editais-metadados.json",
    "EDITAIS/pncp-editais-abertos.csv",
    "EDITAIS/pncp-editais-abertos.json",
    "EDITAIS/pncp-editais-abertos.xlsx",
]
NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def api(path: str, token: str):
    req = urllib.request.Request(
        ROOT + path,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "SISTEMA-WEB-read-only-audit/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read())


def blob_bytes(sha: str, token: str) -> bytes:
    obj = api(f"/git/blobs/{sha}", token)
    if obj.get("encoding") != "base64":
        raise ValueError(f"Encoding inesperado no blob {sha}: {obj.get('encoding')}")
    return base64.b64decode(obj["content"])


def cell_value(cell, shared):
    typ = cell.attrib.get("t")
    value = cell.find("main:v", NS)
    if typ == "inlineStr":
        return "".join(cell.itertext())
    if value is None:
        return ""
    raw = value.text or ""
    if typ == "s":
        return shared[int(raw)]
    if typ == "b":
        return "true" if raw == "1" else "false"
    return raw


def excel_sheets(data: bytes):
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        bad = zf.testzip()
        if bad:
            raise ValueError(f"CRC inválido no membro XLSX: {bad}")
        names = set(zf.namelist())
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared = ["".join(si.itertext()) for si in root.findall("main:si", NS)]
        result = {}
        for sheet in workbook.findall("main:sheets/main:sheet", NS):
            title = sheet.attrib["name"]
            rid = sheet.attrib[f"{{{NS['rel']}}}id"]
            target = relmap[rid].lstrip("/")
            path = target if target.startswith("xl/") else "xl/" + target
            root = ET.fromstring(zf.read(path))
            rows = []
            for row in root.findall(".//main:sheetData/main:row", NS):
                vals = {}
                for cell in row.findall("main:c", NS):
                    ref = cell.attrib["r"]
                    col = "".join(ch for ch in ref if ch.isalpha())
                    vals[col] = cell_value(cell, shared)
                rows.append(vals)
            result[title] = rows
        return result


def col_index(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def rows_to_matrix(rows):
    matrix = []
    for row in rows:
        if not row:
            matrix.append([])
            continue
        width = max(col_index(c) for c in row) + 1
        matrix.append([row.get(next((k for k in row if col_index(k) == i), ""), "") for i in range(width)])
    return matrix


def main():
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        print("ERRO: defina GITHUB_TOKEN no ambiente; não coloque o token no código.", file=sys.stderr)
        return 2

    repo_meta = api("", token)
    tree = api(f"/git/trees/{REF}?recursive=1", token)
    entries = tree.get("tree", [])
    paths = [x["path"] for x in entries]
    selected = {}
    for path in FILES:
        entry = next((x for x in entries if x["path"] == path and x["type"] == "blob"), None)
        if not entry:
            raise FileNotFoundError(f"Ficheiro ausente na árvore {REF}: {path}")
        selected[path] = (entry, blob_bytes(entry["sha"], token))

    meta = json.loads(selected[FILES[0]][1])
    csv_bytes = selected[FILES[1]][1]
    csv_text = csv_bytes.decode("utf-8-sig")
    csv_rows = list(csv.DictReader(io.StringIO(csv_text, newline=""), delimiter=";"))
    raw_json = json.loads(selected[FILES[2]][1])
    xlsx_bytes = selected[FILES[3]][1]
    sheets = excel_sheets(xlsx_bytes)

    csv_ids = [r.get("numero_controle_pncp", "") for r in csv_rows]
    json_ids = [r.get("numeroControlePNCP", "") for r in raw_json]
    duplicates_csv = [k for k, v in Counter(csv_ids).items() if k and v > 1]
    duplicates_json = [k for k, v in Counter(json_ids).items() if k and v > 1]

    xlsx_summary = {}
    for title, rows in sheets.items():
        matrix = rows_to_matrix(rows)
        nonempty = [r for r in matrix if any(str(v).strip() for v in r)]
        xlsx_summary[title] = {
            "nonempty_rows": len(nonempty),
            "header": nonempty[0] if nonempty else [],
            "data_rows": max(0, len(nonempty) - 1),
            "first_data_row": nonempty[1] if len(nonempty) > 1 else [],
        }

    # Verificação da implementação de flatten no script-fonte, por conteúdo do blob.
    source_entry = next((x for x in entries if x["path"] == "scripts/capture_pncp_editais.py"), None)
    source_text = blob_bytes(source_entry["sha"], token).decode("utf-8") if source_entry else ""
    findings = {
        "uf_mapping_uses_uf_instead_of_ufSigla": '"uf":val(pick(unit,"uf",default=pick(d,"uf")))' in source_text,
        "origin_link_falls_back_to_linkProcessoEletronico": '"link_sistema_origem":val(pick(d,"linkSistemaOrigem","linkProcessoEletronico"))' in source_text,
        "xlsx_generated_from_flattened_rows": 'ws.append([row.get(k,"") for k in COLS])' in source_text,
    }

    relevant = [
        p for p in paths
        if p.startswith(("ARQUITETURA/", "EDITAIS/"))
    ]
    ext_counts = Counter((p.rsplit(".", 1)[-1].lower() if "." in p.rsplit("/", 1)[-1] else "[sem extensão]") for p in relevant)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": f"{OWNER}/{REPO}",
        "ref": REF,
        "repository": {
            "private": repo_meta.get("private"),
            "default_branch": repo_meta.get("default_branch"),
            "size_kb": repo_meta.get("size"),
            "tree_truncated": tree.get("truncated"),
            "total_tree_entries": len(entries),
            "relevant_architecture_and_edital_paths": len(relevant),
            "relevant_extensions": dict(sorted(ext_counts.items())),
        },
        "artifacts": {
            path: {
                "git_blob_sha": entry["sha"],
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for path, (entry, data) in selected.items()
        },
        "capture_metadata": meta,
        "csv": {
            "records": len(csv_rows),
            "distinct_ids": len(set(csv_ids)),
            "duplicate_ids": duplicates_csv,
            "columns": list(csv_rows[0].keys()) if csv_rows else [],
            "xlsx_rows_are_not_inferred": True,
        },
        "json": {
            "records": len(raw_json),
            "distinct_ids": len(set(json_ids)),
            "duplicate_ids": duplicates_json,
            "same_id_set_as_csv": set(csv_ids) == set(json_ids),
        },
        "xlsx": {
            "bytes": len(xlsx_bytes),
            "sheets": xlsx_summary,
            "csv_json_reconciliation_not_assumed": True,
        },
        "source_script_findings": findings,
        "limitations": [
            "A enumeração é integral apenas se tree_truncated for false.",
            "O script calcula SHA-256 dos bytes recuperados e conserva os Git Blob SHAs.",
            "O XLSX é lido diretamente por ZIP/XML; não depende de openpyxl.",
            "Este script não escreve no repositório de origem.",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
