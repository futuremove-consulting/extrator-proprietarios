FROM python:3.12-slim

# Metadata
LABEL maintainer="Future Move Consulting"
LABEL description="Extrator de Proprietarios Imobiliarios"
LABEL version="0.1.0"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     curl     && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ src/
COPY .env.example .env

# Create directories
RUN mkdir -p data/logs data/lots && chown -R app:app /app

# Switch to non-root user
USER app

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3     CMD python -c "from extrator_prop.core.health import health_checker; print(health_checker.get_overall_status())" || exit 1

# Default command
CMD ["python", "-m", "extrator_prop.cli.main"]
