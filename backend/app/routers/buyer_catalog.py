import httpx
from fastapi import APIRouter, HTTPException, Query

from app.buyer_catalog import (
    BuyerCatalogError,
    fetch_contract_items,
    list_buyers,
    list_unit_contracts,
)

router = APIRouter(prefix="/api/licitation", tags=["Catálogo de compradores"])


@router.get("/buyers")
async def buyers(
    q: str = "",
    uf: str = "",
    municipio: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        return await list_buyers(q=q, uf=uf, municipio=municipio, page=page, page_size=page_size)
    except BuyerCatalogError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Falha de comunicação ou resposta inválida na fonte externa.") from exc


@router.get("/buyers/{cnpj}/units/{unit_code}/contracts")
async def unit_contracts(cnpj: str, unit_code: str):
    try:
        return await list_unit_contracts(cnpj, unit_code)
    except BuyerCatalogError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Falha de comunicação ou resposta inválida na fonte externa.") from exc


@router.get("/contracts/{cnpj}/{year}/{sequence}/items")
async def contract_items(cnpj: str, year: int, sequence: int):
    try:
        return await fetch_contract_items(cnpj, year, sequence)
    except BuyerCatalogError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Falha de comunicação ou resposta inválida na fonte externa.") from exc
