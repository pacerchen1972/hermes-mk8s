# Multi-stage build for Hermes Agent AI on IONOS MK8s
# Stage 1: Builder — installs dependencies and Hermes Agent package
FROM python:3.12-slim-bookworm AS builder

# Install uv for faster package installation
RUN pip install --no-cache-dir uv

WORKDIR /build

# Install hermes-agent with base dependencies (no optional extras by default)
# To add messaging integrations, extend with: hermes-agent[telegram] or [discord], etc.
RUN uv pip install --system "hermes-agent"

# === Stage 2: Runtime — minimal production image ===
FROM python:3.12-slim-bookworm

# Create non-root user for security (uid 1001)
RUN useradd -u 1001 -m hermes

# Copy Python packages from builder stage
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
