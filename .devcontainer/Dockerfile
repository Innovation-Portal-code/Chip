ARG VARIANT="ubuntu-24.04"
FROM mcr.microsoft.com/devcontainers/base:${VARIANT}

ARG UV_VERSION="0.6.14"
ARG PYTHON_VERSION="3.13"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_SYSTEM_PYTHON=1

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl ca-certificates build-essential pkg-config git \
       openssl libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN UV_VERSION=${UV_VERSION} curl -fsSL https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && uv --version

# Install Python with uv and create project venv
WORKDIR /workspaces/Chip

COPY pyproject.toml uv.lock* ./

RUN uv python install ${PYTHON_VERSION} \
    && uv venv .venv --python ${PYTHON_VERSION} \
    && uv sync --frozen --all-extras

# Create non-root user if not present (devcontainers base already has vscode)
USER vscode

ENV PATH=/workspaces/Chip/.venv/bin:${PATH}

# Default shell
SHELL ["/bin/bash", "-lc"]


