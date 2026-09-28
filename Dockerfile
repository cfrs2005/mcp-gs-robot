FROM node:20 AS h5-build
WORKDIR /build/h5
COPY h5/package.json h5/package-lock.json ./
RUN npm ci
COPY h5/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /usr/local/bin/
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY --from=h5-build /build/src/gs_openapi/server/static/ ./src/gs_openapi/server/static/
RUN uv pip install --system --no-cache .
EXPOSE 8000
CMD ["gs-robot-server"]
