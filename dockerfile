ARG BUILDIMG=public.ecr.aws/docker/library/python:3.15.0b3-slim@sha256:544b7fae9bed4fd9e9b85546fed2c9226557b3aec3986e19976cb7468affd5d9

FROM ${BUILDIMG} AS build

ARG WORKDIR=/app
WORKDIR ${WORKDIR}

ARG BUILDSCR=buildscr.sh
COPY ${BUILDSCR} ${WORKDIR}/
RUN bash ${BUILDSCR} installdeps

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --extra ui --no-dev

COPY . .

FROM ${BUILDIMG} AS prod

ARG WORKDIR=/app
WORKDIR ${WORKDIR}

COPY --from=build /usr/local/bin/uv /usr/local/bin/uvx /usr/local/bin/
COPY --from=build /root/.local/share/uv /root/.local/share/uv
COPY --from=build /app /app

ENV PATH="/app/.venv/bin:${PATH}"

CMD ["python", "-m", "uvicorn", "src.ui.app:app", "--host", "0.0.0.0", "--port", "8765"]
