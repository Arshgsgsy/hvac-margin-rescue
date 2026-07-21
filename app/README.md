# HVAC Margin Rescue - Dashboard

Next.js frontend for the HVAC Margin Rescue platform. It provides the upload and pipeline workflow, the portfolio dashboard, and per-project drill-down pages backed by the FastAPI service in `../backend`.

## Stack

- Next.js 16 (App Router, standalone output) with React 18 and TypeScript
- Tailwind CSS with shadcn/ui-style components
- Recharts for charts, Lucide for icons

## Routes

| Route | Purpose |
| --- | --- |
| `/` | Upload CSVs, run the pipeline, and review flagged projects and analysis output |
| `/dashboard` | Portfolio overview with KPIs and prioritized projects |
| `/projects/[id]` | Project drill-down: costs, root causes, recovery actions, and streaming chat |

## Development

```bash
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

The app expects the backend to be running at `NEXT_PUBLIC_API_URL`. In the combined Docker deployment this is set to `/api` and the backend is served behind the same host.

## Checks and build

```bash
npm run typecheck   # tsc against tsconfig.check.json
npm run build       # production build (standalone output)
npm run check       # typecheck + build
```
