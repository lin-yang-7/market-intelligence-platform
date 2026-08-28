from fastapi import FastAPI
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes

app = FastAPI(title="Auth Service", version="0.1.0")
install_logging(app, "auth-service")
app.add_middleware(RequestIdMiddleware)
install_ops_routes(app, "auth-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
