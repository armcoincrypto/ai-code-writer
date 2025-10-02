# filename: main.py
#
# To run this file:
# 1. Make sure you have Python 3.11+ installed.
# 2. Install the required libraries:
#    pip install "fastapi[all]"
# 3. Run the script from your terminal:
#    python main.py
#
# The API will be available at http://127.0.0.1:8000
# Interactive documentation (Swagger UI) will be at http://127.0.0.1:8000/docs

"""
A complete, runnable single-file FastAPI application that provides a /debug
route to inspect non-sensitive environment variables.
"""

from __future__ import annotations

import os
from typing import Final

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

# --- Constants ---

# Define substrings to detect sensitive environment variables.
# The check will be case-insensitive.
SECRET_SUBSTRINGS: Final[tuple[str, ...]] = ("KEY", "TOKEN", "SECRET", "PASS")

# --- Pydantic Models ---


class DebugInfo(BaseModel):
    """
    Response model for the /debug endpoint.
    Contains filtered environment variables to avoid exposing secrets.
    """

    environment: dict[str, str] = Field(
        ...,
        description="A dictionary of non-sensitive environment variables.",
        examples=[
            {
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "HOME": "/home/user",
                "PYTHON_VERSION": "3.11",
            }
        ],
    )


# --- FastAPI App Initialization ---

app = FastAPI(
    title="Simple Debug API",
    description="An expert-level example API that exposes a /debug endpoint to view "
    "non-sensitive environment variables. Created for Python 3.11+.",
    version="1.0.0",
    contact={
        "name": "Expert Python Developer",
        "url": "https://www.example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# --- Path Operations (API Endpoints) ---


@app.get("/", include_in_schema=False)
async def read_root() -> dict[str, str]:
    """A simple root endpoint to confirm the API is running."""
    return {"message": "API is running. Visit /docs for documentation."}


@app.get(
    "/debug",
    response_model=DebugInfo,
    tags=["Debugging"],
    summary="Get Non-Sensitive Environment Variables",
)
async def get_debug_info() -> DebugInfo:
    """
    Retrieves a filtered list of environment variables.

    This endpoint is useful for debugging application configuration in various
    environments. It intentionally filters out any environment variables
    containing potentially sensitive substrings (e.g., 'KEY', 'TOKEN',
    'SECRET', 'PASS') to prevent accidental exposure of credentials.

    Returns:
        A `DebugInfo` object containing a dictionary of safe environment variables.
    """
    filtered_env = {
        key: value
        for key, value in os.environ.items()
        if not any(sub in key.upper() for sub in SECRET_SUBSTRINGS)
    }
    return DebugInfo(environment=filtered_env)


# --- Main Execution Block ---


def main() -> None:
    """
    Starts the Uvicorn server to run the FastAPI application.

    This function is the main entry point when the script is executed directly.
    """
    print("--- Starting Uvicorn Server ---")
    print("API available at: http://127.0.0.1:8000")
    print("Swagger UI docs:  http://127.0.0.1:8000/docs")
    print("Press Ctrl+C to stop the server.")
    print("---------------------------------")

    # Programmatically run the uvicorn server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    # This block allows the script to be run directly.
    # For development, you might prefer to use uvicorn's command-line tool
    # for features like auto-reloading:
    # uvicorn main:app --reload
    main()
