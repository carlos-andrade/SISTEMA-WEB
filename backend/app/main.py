from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.licitation_source import (
    SourceAccessError,
    SourceConfigurationError,
    SourceNotFoundError,
    SourceValidationError,
    read_reference_opportunity,
)

app = FastAPI(
    title="SISTEMA WEB API",
    description="API central da plataforma SISTEMA WEB.",
    version="1.2.0",
)


@app.get("/api/health", tags=["Operação"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "sistema-web-api",
        "version": app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/integrations/licitation/opportunities/reference", tags=["LICITACAO"])
async def licitation_reference_opportunity() -> dict:
    """Consulta e valida o registo de referência no LICITACAO; não escreve na origem."""
    try:
        return await read_reference_opportunity()
    except SourceConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SourceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": str(exc), "errors": exc.errors},
        ) from exc
    except SourceAccessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": "SISTEMA WEB API", "docs": "/docs"}
