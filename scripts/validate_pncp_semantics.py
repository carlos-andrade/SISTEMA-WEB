#!/usr/bin/env python3
"""Validação semântica do snapshot PNCP; acesso exclusivamente GET ao LICITACAO.

Execução:
  export GITHUB_TOKEN  # token Contents: read e Metadata: read para LICITACAO
  python3 scripts/validate_pncp_semantics.py

As datas sem offset da API PNCP são interpretadas como hora local de
America/Sao_Paulo. O timestamp da captura é convertido de UTC para esse fuso.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import audit_licitacao_snapshot as audit

TZ = ZoneInfo("America/Sao_Paulo")
UF_VALIDAS = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
CONTROL_RE = re.compile(r"^(\d{14})-(\d+)-(\d+)/(\d{4})$")

def issue(out, code, severity, record, field, value, message):
    out.append({
        "code": code,
        "severity": severity,
        "numeroControlePNCP": record.get("numeroControlePNCP"),
        "field": field,
        "value": value,
        "message": message,
    })

def cnpj_valid(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{14}", value):
        return False
    if value == value[0] * 14:
        return False
    def digit(base, weights):
        total = sum(int(n) * w for n, w in zip(base, weights))
        rem = total % 11
        return "0" if rem < 2 else str(11 - rem)
    first = digit(value[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
    second = digit(value[:12] + first, [6,5,4,3,2,9,8,7,6,5,4,3,2])
    return value[-2:] == first + second

def parse_pncp_datetime(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        dt = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)

def main():
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        print("ERRO: GITHUB_TOKEN não definido.", file=sys.stderr)
        return 2

    tree = audit.api(f"/git/trees/{audit.REF}?recursive=1", token)
    by_path = {entry["path"]: entry for entry in tree.get("tree", [])}
    required = audit.FILES[:3]
    blobs = {}
    for path in required:
        entry = by_path.get(path)
        if not entry or entry.get("type") != "blob":
            raise FileNotFoundError(f"Artefacto ausente: {path}")
        blobs[path] = audit.blob_bytes(entry["sha"], token)

    meta = json.loads(blobs[audit.FILES[0]])
    rows = json.loads(blobs[audit.FILES[2]])
    captured_raw = meta.get("capturado_em_utc", "")
    captured = datetime.fromisoformat(captured_raw.replace("Z", "+00:00")) if captured_raw else None
    if captured and captured.tzinfo is None:
        captured = captured.replace(tzinfo=timezone.utc)
    captured_local = captured.astimezone(TZ) if captured else None

    issues = []
    ids = [r.get("numeroControlePNCP") for r in rows]
    duplicates = sorted(k for k, n in Counter(ids).items() if k and n > 1)

    required_top = [
        "numeroControlePNCP", "orgaoEntidade", "unidadeOrgao", "dataInclusao",
        "dataAtualizacao", "dataAberturaProposta", "dataEncerramentoProposta",
        "dataPublicacaoPncp", "valorTotalEstimado", "modalidadeId",
        "modalidadeNome", "situacaoCompraId", "situacaoCompraNome", "objetoCompra",
    ]
    null_counts = {}
    for field in required_top + ["valorTotalHomologado", "linkSistemaOrigem", "linkProcessoEletronico"]:
        null_counts[field] = sum(r.get(field) is None or r.get(field) == "" for r in rows)

    for record in rows:
        rid = record.get("numeroControlePNCP", "")
        cnpj = (record.get("orgaoEntidade") or {}).get("cnpj")
        unit = record.get("unidadeOrgao") or {}
        control = CONTROL_RE.fullmatch(str(rid))
        if not control:
            issue(issues, "PNCP_CONTROL_FORMAT", "HIGH", record, "numeroControlePNCP", rid, "Formato do identificador PNCP inválido.")
        else:
            if control.group(1) != str(cnpj or ""):
                issue(issues, "PNCP_CONTROL_CNPJ_MISMATCH", "HIGH", record, "numeroControlePNCP", rid, "CNPJ do identificador difere de orgaoEntidade.cnpj.")
            if control.group(3) != str(record.get("sequencialCompra", "" )).zfill(len(control.group(3))):
                issue(issues, "PNCP_CONTROL_SEQUENCE_MISMATCH", "HIGH", record, "sequencialCompra", record.get("sequencialCompra"), "Sequencial não coincide com o identificador PNCP.")
            if control.group(4) != str(record.get("anoCompra", "")):
                issue(issues, "PNCP_CONTROL_YEAR_MISMATCH", "HIGH", record, "anoCompra", record.get("anoCompra"), "Ano não coincide com o identificador PNCP.")

        if not cnpj_valid(cnpj):
            issue(issues, "CNPJ_INVALID", "HIGH", record, "orgaoEntidade.cnpj", cnpj, "CNPJ ausente, malformado ou com dígitos verificadores inválidos.")

        uf = unit.get("ufSigla")
        if uf not in UF_VALIDAS:
            issue(issues, "UF_INVALID", "HIGH", record, "unidadeOrgao.ufSigla", uf, "UF ausente ou fora do conjunto oficial de siglas estaduais.")

        ibge = unit.get("codigoIbge")
        if not isinstance(ibge, str) or not re.fullmatch(r"\d{7}", ibge):
            issue(issues, "IBGE_CODE_FORMAT", "HIGH", record, "unidadeOrgao.codigoIbge", ibge, "Código IBGE municipal deve conter sete dígitos.")

        if not str(record.get("objetoCompra") or "").strip():
            issue(issues, "OBJECT_EMPTY", "HIGH", record, "objetoCompra", record.get("objetoCompra"), "Objeto da contratação vazio.")

        value = record.get("valorTotalEstimado")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            issue(issues, "ESTIMATED_VALUE_TYPE", "HIGH", record, "valorTotalEstimado", value, "Valor estimado não é numérico.")
        elif value < 0:
            issue(issues, "ESTIMATED_VALUE_NEGATIVE", "HIGH", record, "valorTotalEstimado", value, "Valor estimado negativo.")
        elif value == 0:
            issue(issues, "ESTIMATED_VALUE_ZERO_REVIEW", "MEDIUM", record, "valorTotalEstimado", value, "Valor zero requer confirmação no documento de origem; não foi tratado como erro automaticamente.")

        link = record.get("linkSistemaOrigem")
        if link is not None and str(link).strip():
            parsed = urlsplit(str(link).strip())
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                issue(issues, "ORIGIN_LINK_NOT_ABSOLUTE", "MEDIUM", record, "linkSistemaOrigem", link, "Link não é URL HTTP(S) absoluta; preservar original e normalizar apenas numa camada derivada.")

        date_fields = ["dataPublicacaoPncp", "dataAberturaProposta", "dataEncerramentoProposta", "dataAtualizacaoGlobal"]
        dates = {field: parse_pncp_datetime(record.get(field)) for field in date_fields}
        for field, parsed in dates.items():
            if parsed is None:
                issue(issues, "DATETIME_INVALID", "HIGH", record, field, record.get(field), "Data/hora ausente ou inválida.")
        pub, start, end, updated = (dates[k] for k in date_fields)
        if pub and end and pub > end:
            issue(issues, "PUBLICATION_AFTER_CLOSING", "HIGH", record, "dataPublicacaoPncp", record.get("dataPublicacaoPncp"), "Publicação posterior ao encerramento.")
        if start and end and start > end:
            issue(issues, "CLOSING_BEFORE_OPENING", "HIGH", record, "dataEncerramentoProposta", record.get("dataEncerramentoProposta"), "Encerramento anterior à abertura.")
        if pub and updated and updated < pub:
            issue(issues, "UPDATE_BEFORE_PUBLICATION", "MEDIUM", record, "dataAtualizacaoGlobal", record.get("dataAtualizacaoGlobal"), "Atualização anterior à publicação.")

        if record.get("modalidadeId") != meta.get("codigoModalidadeContratacao"):
            issue(issues, "MODALITY_FILTER_MISMATCH", "HIGH", record, "modalidadeId", record.get("modalidadeId"), "Modalidade do registo difere do filtro registado nos metadados.")

        if captured_local and end and end <= captured_local:
            issue(issues, "CLOSED_AT_CAPTURE", "MEDIUM", record, "dataEncerramentoProposta", record.get("dataEncerramentoProposta"), "Encerramento já ocorrido no instante da captura, considerando America/Sao_Paulo.")

    for rid in duplicates:
        issues.append({"code":"DUPLICATE_CONTROL_ID","severity":"HIGH","numeroControlePNCP":rid,"field":"numeroControlePNCP","value":rid,"message":"Identificador PNCP duplicado no snapshot."})

    issue_counts = Counter(i["code"] for i in issues)
    severity_counts = Counter(i["severity"] for i in issues)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": f"{audit.OWNER}/{audit.REPO}",
        "source_ref": audit.REF,
        "mode": "read-only",
        "capture_timestamp_utc": captured_raw,
        "business_timezone": "America/Sao_Paulo",
        "source_artifacts_sha256": {path: hashlib.sha256(data).hexdigest() for path, data in blobs.items()},
        "scope": {"records":len(rows),"unique_control_ids":len(set(ids)),"duplicate_control_ids":duplicates,"metadata_status":meta.get("status"),"api_reported_records":meta.get("total_registros_informado_pela_api")},
        "missingness_counts": null_counts,
        "distributions": {
            "modalidadeId": dict(Counter(str(r.get("modalidadeId")) for r in rows)),
            "modalidadeNome": dict(Counter(str(r.get("modalidadeNome")) for r in rows)),
            "situacaoCompraId": dict(Counter(str(r.get("situacaoCompraId")) for r in rows)),
            "situacaoCompraNome": dict(Counter(str(r.get("situacaoCompraNome")) for r in rows)),
            "modoDisputaNome": dict(Counter(str(r.get("modoDisputaNome")) for r in rows)),
            "tipoInstrumentoConvocatorioNome": dict(Counter(str(r.get("tipoInstrumentoConvocatorioNome")) for r in rows)),
            "ufSigla": dict(Counter(str((r.get("unidadeOrgao") or {}).get("ufSigla")) for r in rows)),
        },
        "value_profile": {
            "estimated_zero": sum(r.get("valorTotalEstimado") == 0 for r in rows),
            "estimated_negative": sum(isinstance(r.get("valorTotalEstimado"), (int,float)) and r.get("valorTotalEstimado") < 0 for r in rows),
            "estimated_sum_brl": round(sum((r.get("valorTotalEstimado") or 0) for r in rows), 2),
            "estimated_min_brl": min((r.get("valorTotalEstimado") for r in rows if isinstance(r.get("valorTotalEstimado"), (int,float))), default=None),
            "estimated_max_brl": max((r.get("valorTotalEstimado") for r in rows if isinstance(r.get("valorTotalEstimado"), (int,float))), default=None),
        },
        "issue_summary": {"total":len(issues),"by_severity":dict(severity_counts),"by_code":dict(sorted(issue_counts.items()))},
        "issues": issues,
        "limitations": [
            "CNPJ uses its published check-digit algorithm; IBGE code validation checks seven-digit format only, not the official municipality registry.",
            "The identifier's sequence, CNPJ and year are cross-checked; its intermediate segment is preserved but not assigned an undocumented meaning.",
            "PNCP date-times without offsets are interpreted in America/Sao_Paulo; this assumption is explicit and must be revisited if the API contract changes.",
            "Zero estimated values are review warnings, not automatic invalidations.",
            "Origin links are syntax-checked only; no external links are opened or probed.",
            "This report assesses the captured snapshot, not current procurement status.",
            "The source repository is accessed only through GitHub GET operations."
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
