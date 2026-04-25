# Multi-stage build for Hermes Agent AI on IONOS MK8s
# Stage 1: Builder — clones repo and installs dependencies
FROM python:3.12-slim-bookworm AS builder

# Install git and uv
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

WORKDIR /build

# Clone Hermes Agent from source (not on PyPI)
RUN git clone --depth=1 https://github.com/NousResearch/hermes-agent.git .

# Install hermes-agent and its dependencies
RUN uv pip install --system -e ".[all]"

# === Stage 2: Runtime — minimal production image ===
FROM python:3.12-slim-bookworm

# Create non-root user for security (uid 1001)
RUN useradd -u 1001 -m hermes

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/hermes /usr/local/bin/hermes

# Set working directory and create data volume mount point
WORKDIR /opt/data
RUN mkdir -p /opt/data && chown -R hermes:hermes /opt/data

# Volume for persistent Hermes data (memories, skills, sessions, config)
VOLUME /opt/data

# Expose gateway port
EXPOSE 8642

# Switch to non-root user
USER hermes

# Default command: run Hermes in gateway mode
CMD ["hermes", "gateway", "--port", "8642"]
