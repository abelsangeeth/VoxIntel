FROM python:3.11-slim

WORKDIR /app

# Build arg: "dev" skips torch/pyannote (default), "full" installs everything
ARG BUILD_TARGET=dev

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Full build also needs ffmpeg + libsndfile for audio processing
RUN if [ "$BUILD_TARGET" = "full" ]; then \
      apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg libsndfile1 \
      && rm -rf /var/lib/apt/lists/*; \
    fi

# Copy requirements first for better layer caching
COPY requirements-dev.txt requirements-full.txt* ./

# Install the right set of dependencies
RUN if [ "$BUILD_TARGET" = "full" ]; then \
      pip install --no-cache-dir -r requirements-full.txt; \
    else \
      pip install --no-cache-dir -r requirements-dev.txt; \
    fi

COPY . .

CMD ["celery", "-A", "app.main", "worker", "--loglevel=info", "--concurrency=4"]
