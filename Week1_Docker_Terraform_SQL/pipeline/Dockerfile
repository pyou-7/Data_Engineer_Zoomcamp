# base Docker image that we will build on
FROM python:3.13.11-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# set up the working directory inside the container
WORKDIR /app

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files first (better layer caching)
COPY "pyproject.toml" "uv.lock" ".python-version" ./
# Install dependencies from lock file (ensures reproducible builds)
RUN uv sync --locked

# copy the script to the container. 1st name is source file, 2nd is destination
COPY nyc_taxi_load.py .

# Set entry point
ENTRYPOINT ["uv", "run", "python", "nyc_taxi_load.py"]

# Connect to PostgreSQL database: uv run pgcli -h localhost -p 5432 -u root -d ny_taxi