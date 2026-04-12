import { Project, PortfolioSummary, PipelineResult } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  const res = await fetch(`${API_BASE}/portfolio/summary`)
  if (!res.ok) throw new Error(`Failed to fetch portfolio summary: ${res.status}`)
  return res.json()
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/portfolio/projects`)
  if (!res.ok) throw new Error(`Failed to fetch projects: ${res.status}`)
  return res.json()
}

export async function fetchProject(id: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${id}`)
  if (!res.ok) throw new Error(`Failed to fetch project ${id}: ${res.status}`)
  return res.json()
}

export async function uploadFiles(files: FileList): Promise<{ status: string; files: { name: string; size_bytes: number }[] }> {
  const formData = new FormData()
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i])
  }
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
  return res.json()
}

export async function runPipeline(): Promise<PipelineResult> {
  const res = await fetch(`${API_BASE}/pipeline/run`, { method: 'POST' })
  if (!res.ok) throw new Error(`Pipeline failed: ${res.status}`)
  return res.json()
}

export { API_BASE }
