FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    PYTHONUNBUFFERED=1

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install "poetry==2.4.1"

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=cache,target=/root/.cache/pip \
    poetry install --only main --no-root --no-ansi

COPY README.md LICENSE ./
COPY src ./src

RUN --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=cache,target=/root/.cache/pip \
    poetry install --only-root --no-ansi

FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    espeak-ng \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

CMD ["jerry-bot-tts", "--socket-path", "/data/tts.sock", "--write-path", "/data/audio"]
