# SabiRoute API image (Sprint 5 deployment foundation, not a production launch).
#
# Reproducible installs from uv.lock; the gateway runs as a non-root user.
# The container probes READINESS, not liveness: readiness re-validates the
# database schema, so an unmigrated or otherwise degraded gateway reports
# unhealthy instead of passing. Schema is never created by this image's
# startup path — run the explicit migration first (see the note below CMD).
# Secrets come from the environment at run time — never baked in, never
# copied (see .dockerignore). Static UI ships from web/ at /app/.

FROM python:3.11-slim AS runtime

# A wheel install relocates the package away from its sibling directories,
# so file-based configuration is pinned explicitly instead of relying on
# repository-relative resolution (which only holds for host-run checkouts).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    SABIROUTE_HOST=0.0.0.0 \
    SABIROUTE_API_PORT=8000 \
    SABIROUTE_CONFIG_PATH=/srv/sabiroute/config/config.yaml \
    SABIROUTE_ROUTES_PATH=/srv/sabiroute/config/routes \
    SABIROUTE_WEB_DIR=/srv/sabiroute/web

WORKDIR /srv/sabiroute

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock README.md LICENSE ./
# Dependencies first (cached layer), then the project itself: building the
# wheel requires src/ to exist, so installing the project happens after it
# is copied. A single COPY-everything step would also work but would
# re-resolve dependencies on every source change.
RUN uv sync --frozen --no-dev --no-editable --no-install-project

COPY src/ ./src/
COPY config/ ./config/
COPY web/ ./web/
RUN uv sync --frozen --no-dev --no-editable

RUN groupadd --system sabiroute \
    && useradd --system --gid sabiroute --create-home sabiroute \
    && chown -R sabiroute:sabiroute /srv/sabiroute
USER sabiroute

ENV PATH="/srv/sabiroute/.venv/bin:$PATH"

EXPOSE 8000

# Readiness, not liveness: the container must only report healthy when the
# gateway can actually serve requests. A fresh, unmigrated database fails the
# read-only schema check at startup, so readiness returns 503 and this probe
# marks the container unhealthy instead of falsely healthy. Liveness alone
# would pass in that degraded state.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=4)"

# This image never creates or alters schema: store constructors only open
# connections and startup only validates. Apply the schema explicitly before
# starting the container, e.g.:
#   docker run --rm --env-file <environment file> <image> python -m sabiroute.migrate
# docker-compose.yml performs this as the one-shot ``sabiroute-migrate``
# service and starts this container only after it exits 0.
CMD ["sabiroute"]
