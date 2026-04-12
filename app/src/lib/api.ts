import {
  HealthStatus,
  PipelineJob,
  PipelineResult,
  PortfolioSummary,
  Project,
  UploadResult,
} from './types'


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
      if (payload.detail.error) {
        return payload.detail.error
      }
    }
    if (payload?.message) return payload.message
    if (payload?.error) return payload.error
  }

  return await res.text().catch(() => `HTTP ${res.status}`)
}


export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
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


export async function uploadDataset(files: File[], autoRun: boolean = true): Promise<UploadResult> {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  const res = await fetch(`${API_BASE}/upload?auto_run=${autoRun ? 'true' : 'false'}`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}


export async function uploadFiles(files: FileList): Promise<UploadResult> {
  return uploadDataset(Array.from(files))
}


export async function startPipelineRun(): Promise<PipelineJob> {
  const res = await fetch(`${API_BASE}/pipeline/run`, { method: 'POST' })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}


export async function fetchPipelineJob(jobId: string): Promise<PipelineJob> {
  const res = await fetch(`${API_BASE}/pipeline/jobs/${jobId}`)
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}


export async function waitForPipelineJob(
  jobId: string,
  options?: {
    intervalMs?: number
    onUpdate?: (job: PipelineJob) => void
  },
): Promise<PipelineJob> {
  const intervalMs = options?.intervalMs ?? 1200

  while (true) {
    const job = await fetchPipelineJob(jobId)
    options?.onUpdate?.(job)

    if (job.status === 'complete' || job.status === 'error') {
      return job
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }
}


export async function runPipeline(options?: {
  onUpdate?: (job: PipelineJob) => void
  intervalMs?: number
}): Promise<PipelineResult> {
  const job = await startPipelineRun()
  options?.onUpdate?.(job)
  const completedJob = await waitForPipelineJob(job.id, options)
  if (!completedJob.result) {
    throw new Error(completedJob.error || 'Pipeline finished without a result payload')
  }
  return completedJob.result
}


export { API_BASE }
