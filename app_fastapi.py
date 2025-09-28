#!/usr/bin/env python3
"""
Small FastAPI app with robust CLI behavior.

- GET /sum?a=<float>&b=<float> -> {"result": a+b}
- Type hints, Pydantic response model
- CLI: use --serve to run the server; --help exits immediately (good for tests)
"""

from __future__ import annotations

import argparse
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


class SumResponse(BaseModel):
    """Response model for /sum endpoint."""

    result: float


app = FastAPI(title="Sum API", version="0.1.0", docs_url="/docs", redoc_url="/redoc")


@app.get("/health", summary="Liveness/health check")
def health() -> dict[str, str]:
    """Simple health endpoint for probes and monitoring."""
    return {"status": "ok"}


@app.get("/sum", response_model=SumResponse, summary="Add two numbers")
def get_sum(
    a: float = Query(..., description="First addend."),
    b: float = Query(..., description="Second addend."),
) -> SumResponse:
    """Return the sum of a and b as JSON."""
    try:
        res = a + b
    except Exception as e:  # pragma: no cover (FastAPI will parse/validate)
        raise HTTPException(status_code=400, detail=f"Invalid inputs: {e}") from e

    if res in (float("inf"), float("-inf")) or res != res:  # NaN/Inf guard
        raise HTTPException(status_code=400, detail="Result not finite")

    return SumResponse(result=float(res))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Serve the FastAPI app (optional).")
    p.add_argument("--serve", action="store_true", help="Start the Uvicorn server.")
    p.add_argument(
        "--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)."
    )
    p.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000).")
    return p


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Only run the server if explicitly requested; otherwise (or with --help),
    # argparse will exit or we simply return quickly (useful for tests).
    if args.serve:
        # Pass the ASGI app object directly (no 'module:app' string), and no reload.
        uvicorn.run(app, host=args.host, port=args.port, reload=False, log_level="info")


if __name__ == "__main__":
    main()
