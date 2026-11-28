# Belfort in a container, for running and testing it on any machine with Docker.
#
#   docker build -t belfort .
#   docker run --rm -p 127.0.0.1:8765:8765 -v belfort-data:/data belfort     # then open http://localhost:8765
#
#   docker build --target test -t belfort-test .
#   docker run --rm belfort-test                                             # lint and the offline tests
#
# Publish the port on 127.0.0.1 only, as above. Belfort is a single-user app and is not meant to be a public service
# (docs/COMPLIANCE.md).

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# The repository as built, minus everything .dockerignore leaves out (secrets, local data, build output).
FROM base AS source
COPY . .
RUN mkdir -p data

FROM source AS test
RUN pip install -r requirements-dev.txt
CMD ["sh", "-c", "ruff check . && ruff format --check . && pytest --cov"]

# Last stage, so a plain `docker build .` makes the app. It holds only what the app reads at run time.
FROM base AS runtime
COPY --from=source /app/belfort ./belfort
COPY --from=source /app/content ./content
COPY --from=source /app/data ./data
RUN useradd --uid 10001 --create-home belfort && mkdir /data && chown belfort /data
ENV BELFORT_DATA_DIR=/data
USER belfort
VOLUME /data
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/config', timeout=4)"]
# 0.0.0.0 is inside the container; the published port decides who can reach it.
CMD ["python", "-m", "uvicorn", "belfort.main:app", "--host", "0.0.0.0", "--port", "8765"]
