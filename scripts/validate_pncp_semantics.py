#!/usr/bin/env python3
"""Validação semântica read-only do snapshot PNCP."""
from __future__ import annotations
import hashlib, json, os, re, sys
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
import audit_licitacao_snapshot as audit

TZ = ZoneInfo("America/Sao_Paulo")
UF = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
CONTROL = re.compile(r"^(\d{14})-(\d+)-(\d+)/(\d{4})$")

def cnpj_ok(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{14}", v) or len(set(v)) == 1:
        return False
    def digit(s, w):
        n = sum(int(c)*x for c,x in zip(s,w)) % 11
        return "0" if n < 2 else str(11-n)
    a = digit(v[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
    b = digit(v[:12]+a, [6,5,4,3,2,9,8,7,6,5,4,3,2])
    return v[-2:] == a+b

def dt(v):
    if not isinstance(v, str) or not v.strip(): return None
    try: x = datetime.fromisoformat(v.strip())
    except ValueError: return None
    return x.replace(tzinfo=TZ) if x.tzinfo is None else x.astimezone(TZ)

def main():
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        print("GITHUB_TOKEN não definido", file=sys.stderr); return 2
    tree = audit.api(f"/git/trees/{audit.REF}?recursive=1", token)
    entries = {x["path"]:x for x in tree.get("tree",[])}
    paths = [audit.FILES[0], audit.FILES[2]]
    blobs = {}
    for p in paths:
        e = entries.get(p)
        if not e or e.get("type") != "blob": raise FileNotFoundError(p)
        blobs[p] = audit.blob_bytes(e["sha"], token)
    meta, rows = json.loads(blobs[paths[0]]), json.loads(blobs[paths[1]])
    captured_raw = meta.get("capturado_em_utc")
    captured = datetime.fromisoformat(captured_raw.replace("Z","+00:00")) if captured_raw else None
    if captured and captured.tzinfo is None: captured = captured.replace(tzinfo=timezone.utc)
    captured_local = captured.astimezone(TZ) if captured else None
    issues=[]
    def add(code, severity, r, field, value, message):
        issues.append({"code":code,"severity":severity,"numeroControlePNCP":r.get("numeroControlePNCP"),"field":field,"value":value,"message":message})
    ids=[r.get("numeroControlePNCP") for r in rows]
    for r in rows:
        rid=str(r.get("numeroControlePNCP") or "")
        org=r.get("orgaoEntidade") or {}; unit=r.get("unidadeOrgao") or {}
        m=CONTROL.fullmatch(rid); cnpj=org.get("cnpj")
        if not m: add("PNCP_CONTROL_FORMAT","HIGH",r,"numeroControlePNCP",rid,"Formato inválido.")
        else:
            if m.group(1)!=str(cnpj or ""): add("PNCP_CONTROL_CNPJ_MISMATCH","HIGH",r,"numeroControlePNCP",rid,"CNPJ do identificador difere do órgão.")
            if m.group(3)!=str(r.get("sequencialCompra","")).zfill(len(m.group(3))): add("PNCP_CONTROL_SEQUENCE_MISMATCH","HIGH",r,"sequencialCompra",r.get("sequencialCompra"),"Sequencial divergente.")
            if m.group(4)!=str(r.get("anoCompra","")): add("PNCP_CONTROL_YEAR_MISMATCH","HIGH",r,"anoCompra",r.get("anoCompra"),"Ano divergente.")
        if not cnpj_ok(cnpj): add("CNPJ_INVALID","HIGH",r,"orgaoEntidade.cnpj",cnpj,"CNPJ inválido ou com dígitos verificadores incorretos.")
        if unit.get("ufSigla") not in UF: add("UF_INVALID","HIGH",r,"unidadeOrgao.ufSigla",unit.get("ufSigla"),"UF inválida ou ausente.")
        if not re.fullmatch(r"\d{7}",str(unit.get("codigoIbge") or "")): add("IBGE_CODE_FORMAT","HIGH",r,"unidadeOrgao.codigoIbge",unit.get("codigoIbge"),"Código IBGE deve conter sete dígitos.")
        if not str(r.get("objetoCompra") or "").strip(): add("OBJECT_EMPTY","HIGH",r,"objetoCompra",r.get("objetoCompra"),"Objeto vazio.")
        value=r.get("valorTotalEstimado")
        if not isinstance(value,(int,float)) or isinstance(value,bool): add("ESTIMATED_VALUE_TYPE","HIGH",r,"valorTotalEstimado",value,"Valor estimado não numérico.")
        elif value<0: add("ESTIMATED_VALUE_NEGATIVE","HIGH",r,"valorTotalEstimado",value,"Valor negativo.")
        elif value==0: add("ESTIMATED_VALUE_ZERO_REVIEW","MEDIUM",r,"valorTotalEstimado",value,"Valor zero requer confirmação na documentação do procedimento.")
        link=r.get("linkSistemaOrigem")
        if link is not None and str(link).strip():
            u=urlsplit(str(link).strip())
            if u.scheme not in ("http","https") or not u.netloc: add("ORIGIN_LINK_NOT_ABSOLUTE","MEDIUM",r,"linkSistemaOrigem",link,"Não é URL HTTP(S) absoluta.")
        dates={k:dt(r.get(k)) for k in ("dataPublicacaoPncp","dataAberturaProposta","dataEncerramentoProposta","dataAtualizacaoGlobal")}
        for k,v in dates.items():
            if v is None: add("DATETIME_INVALID","HIGH",r,k,r.get(k),"Data/hora ausente ou inválida.")
        pub,start,end,updated=(dates[k] for k in ("dataPublicacaoPncp","dataAberturaProposta","dataEncerramentoProposta","dataAtualizacaoGlobal"))
        if pub and end and pub>end: add("PUBLICATION_AFTER_CLOSING","HIGH",r,"dataPublicacaoPncp",r.get("dataPublicacaoPncp"),"Publicação posterior ao encerramento.")
        if start and end and start>end: add("CLOSING_BEFORE_OPENING","HIGH",r,"dataEncerramentoProposta",r.get("dataEncerramentoProposta"),"Encerramento anterior à abertura.")
        if pub and updated and updated<pub: add("UPDATE_BEFORE_PUBLICATION","MEDIUM",r,"dataAtualizacaoGlobal",r.get("dataAtualizacaoGlobal"),"Atualização anterior à publicação.")
        if r.get("modalidadeId")!=meta.get("codigoModalidadeContratacao"): add("MODALITY_FILTER_MISMATCH","HIGH",r,"modalidadeId",r.get("modalidadeId"),"Modalidade difere do filtro de captura.")
        if captured_local and end and end<=captured_local: add("CLOSED_AT_CAPTURE","MEDIUM",r,"dataEncerramentoProposta",r.get("dataEncerramentoProposta"),"Proposta encerrada no instante da captura.")
    dup=sorted(k for k,n in Counter(ids).items() if k and n>1)
    for rid in dup: issues.append({"code":"DUPLICATE_CONTROL_ID","severity":"HIGH","numeroControlePNCP":rid})
    codes=Counter(x["code"] for x in issues); sev=Counter(x["severity"] for x in issues)
    fields=["numeroControlePNCP","orgaoEntidade","unidadeOrgao","dataInclusao","dataAtualizacao","dataAberturaProposta","dataEncerramentoProposta","dataPublicacaoPncp","valorTotalEstimado","modalidadeId","modalidadeNome","situacaoCompraId","situacaoCompraNome","objetoCompra","valorTotalHomologado","linkSistemaOrigem","linkProcessoEletronico"]
    report={
      "generated_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
      "source":f"{audit.OWNER}/{audit.REPO}","source_ref":audit.REF,"mode":"read-only",
      "capture_timestamp_utc":captured_raw,"business_timezone":"America/Sao_Paulo",
      "source_artifacts_sha256":{p:hashlib.sha256(b).hexdigest() for p,b in blobs.items()},
      "scope":{"records":len(rows),"unique_control_ids":len(set(ids)),"duplicate_control_ids":dup,"metadata_status":meta.get("status"),"api_reported_records":meta.get("total_registros_informado_pela_api")},
      "missingness_counts": {
          k: sum(
              r.get(k) is None
              or (isinstance(r.get(k), str) and not r.get(k).strip())
              for r in rows
          )
          for k in fields
      },

      "distributions":{k:dict(Counter(str((r.get("unidadeOrgao") or {}).get(k)) if k=="ufSigla" else str(r.get(k)) for r in rows)) for k in ("modalidadeId","modalidadeNome","situacaoCompraId","situacaoCompraNome","modoDisputaNome","tipoInstrumentoConvocatorioNome","ufSigla")},
      "value_profile":{"estimated_zero":sum(r.get("valorTotalEstimado")==0 for r in rows),"estimated_negative":sum(isinstance(r.get("valorTotalEstimado"),(int,float)) and r.get("valorTotalEstimado")<0 for r in rows),"estimated_sum_brl":round(sum((r.get("valorTotalEstimado") or 0) for r in rows),2),"estimated_min_brl":min((r.get("valorTotalEstimado") for r in rows if isinstance(r.get("valorTotalEstimado"),(int,float))),default=None),"estimated_max_brl":max((r.get("valorTotalEstimado") for r in rows if isinstance(r.get("valorTotalEstimado"),(int,float))),default=None)},
      "issue_summary":{"total":len(issues),"by_severity":dict(sev),"by_code":dict(sorted(codes.items()))},"issues":issues,
      "limitations":["CNPJ validates check digits; IBGE checks seven-digit format only, not official municipality registry.","PNCP timestamps without offsets are interpreted as America/Sao_Paulo.","Zero estimated values are review warnings, not automatic errors.","Links are syntax-checked only and are not opened or probed.","Report concerns the captured snapshot, not current procurement status.","Source repository is accessed only via GitHub GET operations."]
    }
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
