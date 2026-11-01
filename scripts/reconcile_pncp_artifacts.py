#!/usr/bin/env python3
"""Reconcilia CSV, JSON bruto e XLSX do snapshot PNCP, sem escrever na fonte.

Requisitos: Python 3.10+ (biblioteca padrão).
Execução: export GITHUB_TOKEN; python3 scripts/reconcile_pncp_artifacts.py
A transformação JSON -> colunas replica a função flatten do script de captura
LICITACAO/scripts/capture_pncp_editais.py, sem executar código da fonte.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import audit_licitacao_snapshot as audit

COLS = [
    "numero_controle_pncp", "numero_compra", "ano_compra", "modalidade_id",
    "modalidade_nome", "situacao", "objeto", "orgao_cnpj", "orgao_nome",
    "unidade_codigo", "unidade_nome", "uf", "municipio",
    "data_publicacao_pncp", "data_atualizacao", "data_abertura_proposta",
    "data_encerramento_proposta", "valor_total_estimado",
    "valor_total_homologado", "srp", "amparo_legal", "modo_disputa",
    "fonte_sistema", "link_sistema_origem", "link_pncp", "capturado_em_utc",
]

def val(x):
    if x is None:
        return ""
    if isinstance(x, bool):
        return "Sim" if x else "Não"
    if isinstance(x, (dict, list)):
        return json.dumps(x, ensure_ascii=False, sort_keys=True)
    return re.sub(r"\s+", " ", str(x)).strip()

def pick(d, *keys, default=""):
    for key in keys:
        value = d.get(key)
        if value not in (None, "", [], {}):
            return value
    return default

def obj(d, key):
    value = d.get(key, {})
    return value if isinstance(value, dict) else {}

def edital_url(d):
    control = val(pick(d, "numeroControlePNCP", "numeroControlePncp"))
    if control:
        match = re.fullmatch(r"(\d{14})-(\d+)-(\d+)/(\d{4})", control)
        if match:
            cnpj, modalidade, seq, ano = match.groups()
            return f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
        return "https://pncp.gov.br/app/editais?id=" + quote(control)
    return "https://pncp.gov.br/app/editais"

def flatten(d, captured):
    org, unit, legal = obj(d, "orgaoEntidade"), obj(d, "unidadeOrgao"), obj(d, "amparoLegal")
    return {
        "numero_controle_pncp": val(pick(d, "numeroControlePNCP", "numeroControlePncp")),
        "numero_compra": val(pick(d, "numeroCompra", "numeroProcesso", "numero")),
        "ano_compra": val(pick(d, "anoCompra", "ano")),
        "modalidade_id": val(pick(d, "modalidadeId", "codigoModalidadeContratacao")),
        "modalidade_nome": val(pick(d, "modalidadeNome", "nomeModalidade", "modalidade")),
        "situacao": val(pick(d, "situacaoCompraNome", "situacaoNome", "situacaoCompraId", "situacao")),
        "objeto": val(pick(d, "objetoCompra", "objeto", "informacaoComplementar")),
        "orgao_cnpj": val(pick(org, "cnpj", default=pick(d, "cnpjOrgao", "cnpj"))),
        "orgao_nome": val(pick(org, "razaoSocial", "nome", default=pick(d, "nomeOrgao"))),
        "unidade_codigo": val(pick(unit, "codigoUnidade", "codigo", default=pick(d, "codigoUnidadeAdministrativa"))),
        "unidade_nome": val(pick(unit, "nomeUnidade", "nome", default=pick(d, "unidadeNome"))),
        "uf": val(pick(unit, "uf", default=pick(d, "uf"))),
        "municipio": val(pick(unit, "municipioNome", "nomeMunicipio", default=pick(d, "municipioNome", "municipio"))),
        "data_publicacao_pncp": val(pick(d, "dataPublicacaoPncp", "dataPublicacao", "dataInclusao")),
        "data_atualizacao": val(pick(d, "dataAtualizacao", "dataAtualizacaoGlobal")),
        "data_abertura_proposta": val(pick(d, "dataAberturaProposta", "dataInicioRecebimentoPropostas")),
        "data_encerramento_proposta": val(pick(d, "dataEncerramentoProposta", "dataFimRecebimentoPropostas")),
        "valor_total_estimado": val(pick(d, "valorTotalEstimado", "valorTotalEstimadoCompra", "valorTotal")),
        "valor_total_homologado": val(pick(d, "valorTotalHomologado")),
        "srp": val(pick(d, "srp", "registroPreco")),
        "amparo_legal": val(pick(legal, "nome", "descricao", default=pick(d, "amparoLegalNome"))),
        "modo_disputa": val(pick(d, "modoDisputaNome", "modoDisputaId")),
        "fonte_sistema": val(pick(d, "nomeUsuario", "usuarioNome", "fonte")),
        "link_sistema_origem": val(pick(d, "linkSistemaOrigem", "linkProcessoEletronico")),
        "link_pncp": edital_url(d),
        "capturado_em_utc": captured,
    }

def matrix_by_header(rows):
    matrix = audit.rows_to_matrix(rows)
    nonempty = [row for row in matrix if any(str(v).strip() for v in row)]
    if not nonempty:
        return [], []
    header = [str(v) for v in nonempty[0]]
    records = []
    for line_no, row in enumerate(nonempty[1:], start=2):
        padded = row + [""] * max(0, len(header) - len(row))
        records.append((line_no, dict(zip(header, padded))))
    return header, records

def main():
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        print("ERRO: GITHUB_TOKEN não definido.", file=sys.stderr)
        return 2

    tree = audit.api(f"/git/trees/{audit.REF}?recursive=1", token)
    by_path = {item["path"]: item for item in tree.get("tree", [])}
    blobs = {}
    for path in audit.FILES:
        entry = by_path.get(path)
        if not entry or entry.get("type") != "blob":
            raise FileNotFoundError(f"Artefacto ausente: {path}")
        blobs[path] = audit.blob_bytes(entry["sha"], token)

    meta = json.loads(blobs[audit.FILES[0]])
    csv_text = blobs[audit.FILES[1]].decode("utf-8-sig")
    csv_reader = csv.DictReader(io.StringIO(csv_text, newline=""), delimiter=";")
    csv_rows = list(csv_reader)
    raw_json = json.loads(blobs[audit.FILES[2]])
    sheets = audit.excel_sheets(blobs[audit.FILES[3]])
    if "Editais PNCP" not in sheets:
        raise ValueError("Folha 'Editais PNCP' não encontrada no XLSX.")
    xlsx_header, xlsx_records = matrix_by_header(sheets["Editais PNCP"])

    captured = meta.get("capturado_em_utc", "")
    json_rows = [flatten(record, captured) for record in raw_json]
    csv_by_id = {r.get("numero_controle_pncp", ""): r for r in csv_rows}
    json_by_id = {r.get("numero_controle_pncp", ""): r for r in json_rows}
    xlsx_by_id = {r.get("numero_controle_pncp", ""): (line, r) for line, r in xlsx_records}

    id_sets = {
        "csv": set(csv_by_id) - {""},
        "json_flattened": set(json_by_id) - {""},
        "xlsx": set(xlsx_by_id) - {""},
    }
    all_ids = sorted(set.union(*id_sets.values()) if id_sets else set())
    missing_ids = {
        name: sorted(set.union(*id_sets.values()) - ids)
        for name, ids in id_sets.items()
    }
    mismatches = []
    field_counts = Counter()
    for record_id in all_ids:
        sources = {
            "csv": csv_by_id.get(record_id),
            "json_flattened": json_by_id.get(record_id),
            "xlsx": xlsx_by_id.get(record_id, (None, None))[1],
        }
        for field in COLS:
            values = {name: (row.get(field, "") if row is not None else None)
                      for name, row in sources.items()}
            present = [v for v in values.values() if v is not None]
            if len(present) >= 2 and len(set(present)) > 1:
                field_counts[field] += 1
                if len(mismatches) < 1000:
                    mismatches.append({
                        "numero_controle_pncp": record_id,
                        "field": field,
                        "values": values,
                        "xlsx_row": xlsx_by_id.get(record_id, (None, None))[0],
                    })

    duplicate_ids = {
        "csv": [k for k, n in Counter(r.get("numero_controle_pncp", "") for r in csv_rows).items() if k and n > 1],
        "json_flattened": [k for k, n in Counter(r.get("numero_controle_pncp", "") for r in json_rows).items() if k and n > 1],
        "xlsx": [k for k, n in Counter(r.get("numero_controle_pncp", "") for _, r in xlsx_records).items() if k and n > 1],
    }
    header_issues = {
        "csv_missing_or_extra_columns": sorted(set(COLS) ^ set(csv_reader.fieldnames or [])),
        "xlsx_missing_or_extra_columns": sorted(set(COLS) ^ set(xlsx_header)),
    }

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": f"{audit.OWNER}/{audit.REPO}",
        "ref": audit.REF,
        "mode": "read-only",
        "capture_timestamp": captured,
        "artifact_sha256": {
            path: hashlib.sha256(data).hexdigest() for path, data in blobs.items()
        },
        "counts": {
            "csv_records": len(csv_rows),
            "json_records": len(raw_json),
            "xlsx_data_rows": len(xlsx_records),
            "unique_ids_union": len(all_ids),
            "ids_by_format": {name: len(ids) for name, ids in id_sets.items()},
        },
        "id_reconciliation": {
            "same_id_set_all_three": id_sets["csv"] == id_sets["json_flattened"] == id_sets["xlsx"],
            "missing_ids_by_format": missing_ids,
            "duplicate_ids": duplicate_ids,
        },
        "schema_reconciliation": {
            "expected_columns": len(COLS),
            "csv_columns": len(csv_reader.fieldnames or []),
            "xlsx_columns": len(xlsx_header),
            "header_issues": header_issues,
        },
        "cell_reconciliation": {
            "comparison": "CSV vs JSON flattened with source mapping vs XLSX",
            "fields_with_mismatches": dict(sorted(field_counts.items())),
            "mismatch_count": sum(field_counts.values()),
            "mismatches_truncated_at": 1000,
            "mismatches": mismatches,
        },
        "known_mapping_semantics": {
            "uf": "flatten replicates source mapping: unit.uf then root.uf; unit.ufSigla is not consulted",
            "link_sistema_origem": "flatten replicates fallback order: linkSistemaOrigem then linkProcessoEletronico",
            "link_pncp": "derived URL, not a direct source JSON field",
            "capturado_em_utc": "capture metadata timestamp, not a direct field in each source record",
        },
        "xlsx_metadata_sheet_present": "Metadados" in sheets,
        "limitations": [
            "JSON flattened values are independently recomputed by a faithful replica of the source flatten mapping.",
            "The reconciliation compares exported values as strings; it does not infer semantic equivalence beyond the source's flatten rules.",
            "The source repository is accessed only through GitHub GET operations.",
            "Mismatch detail is capped at 1000 entries; per-field counts cover all records.",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
