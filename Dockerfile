FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /workspace/app

ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/api

COPY app/package.json app/package-lock.json ./
RUN npm ci

COPY app/ ./
RUN mkdir -p public && npm run build


FROM node:20-bookworm-slim AS runtime

WORKDIR /workspace

ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/api
ENV HOSTNAME=0.0.0.0
ENV BACKEND_PORT=8000
ENV FASTAPI_ROOT_PATH=/api
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN python3 -m venv "${VIRTUAL_ENV}" \
    && "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir --upgrade pip \
    && "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir -r backend/requirements.txt

COPY . .

COPY --from=frontend-builder /workspace/app/.next/standalone ./app/.next/standalone
COPY --from=frontend-builder /workspace/app/.next/static ./app/.next/standalone/.next/static
COPY --from=frontend-builder /workspace/app/public ./app/.next/standalone/public

RUN chmod +x /workspace/start-combined.sh

EXPOSE 3000

CMD ["/workspace/start-combined.sh"]
