from datetime import datetime, timezone
from fastapi import FastAPI

app = FastAPI(title="SISTEMA WEB API", description="API central da plataforma SISTEMA WEB.", version="1.0.0")

@app.get("/api/health", tags=["Operação"])
def health() -> dict[str, str]:
    return {"status":"ok","service":"sistema-web-api","version":app.version,"timestamp":datetime.now(timezone.utc).isoformat()}

@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service":"SISTEMA WEB API","docs":"/docs"}
