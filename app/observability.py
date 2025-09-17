import os

from fastapi import FastAPI

import logfire


def configure_observability(app: FastAPI) -> None:
    """Initialize Logfire, instrument FastAPI, add redaction defaults and correlation IDs.

    This function is idempotent and safe to call once per process.
    """
    service_name = os.getenv("SERVICE_NAME", "chip-api")
    environment = os.getenv("ENV", "development")

    # Configure Logfire with sane defaults
    logfire.configure(service_name=service_name, environment=environment)

    # Instrument FastAPI (autogenerates spans, logging, route attributes)
    logfire.instrument_fastapi(app)
