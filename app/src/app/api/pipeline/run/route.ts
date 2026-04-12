import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export interface PipelineStep {
  id: string
  label: string
  description: string
  status: 'idle' | 'running' | 'complete' | 'error'
  duration: number
  logs: string[]
}

export interface PipelineResult {
  status: 'complete' | 'error'
  total_duration_seconds: number
  steps: PipelineStep[]
}

export async function POST() {
  try {
    const response = await fetch(`${BACKEND_URL}/pipeline/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const error = await response.text()
      return NextResponse.json({ 
        error: `Pipeline execution failed: ${error}` 
      }, { status: response.status })
    }

    const result: PipelineResult = await response.json()
    
    return NextResponse.json(result)

  } catch (error) {
    console.error('[v0] Pipeline error:', error)
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Pipeline execution failed' 
    }, { status: 500 })
  }
}
