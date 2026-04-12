import { Project, PortfolioSummary, PipelineResult, UploadResult } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function readError(res: Response): Promise<string> {
  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    const payload = await res.json().catch(() => null)
    if (payload?.detail) {
      if (typeof payload.detail === 'string') {
        return payload.detail
      }
      if (payload.detail.message) {
        return payload.detail.message
      }
    }
    if (payload?.error) {
      return payload.error
    }
  }

  return await res.text().catch(() => `HTTP ${res.status}`)
}

export async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  const res = await fetch(`${API_BASE}/portfolio/summary`)
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/portfolio/projects`)
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export async function fetchProject(id: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${id}`)
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export async function uploadDataset(files: File[]): Promise<UploadResult> {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export async function uploadFiles(files: FileList): Promise<UploadResult> {
  return uploadDataset(Array.from(files))
}

export async function runPipeline(): Promise<PipelineResult> {
  const res = await fetch(`${API_BASE}/pipeline/run`, { method: 'POST' })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export { API_BASE }
