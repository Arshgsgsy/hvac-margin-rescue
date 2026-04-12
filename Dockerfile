FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /workspace/app

ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/api

COPY app/package.json app/package-lock.json ./
RUN npm ci

COPY app/ ./
RUN npm run build


FROM node:20-bookworm-slim AS runtime

WORKDIR /workspace

ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/api
ENV HOSTNAME=0.0.0.0
ENV BACKEND_PORT=8000
ENV FASTAPI_ROOT_PATH=/api

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN python3 -m pip install --no-cache-dir -r backend/requirements.txt

COPY . .

COPY --from=frontend-builder /workspace/app/.next/standalone ./app/.next/standalone
COPY --from=frontend-builder /workspace/app/.next/static ./app/.next/static

RUN chmod +x /workspace/start-combined.sh

EXPOSE 3000

CMD ["/workspace/start-combined.sh"]
