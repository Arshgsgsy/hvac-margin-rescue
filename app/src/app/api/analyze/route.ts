import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

// Run LLM analysis on all flagged projects
export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}))
    const projectId = body.projectId

    if (projectId) {
      // Analyze single project
      const response = await fetch(`${BACKEND_URL}/analyze/${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        const error = await response.text()
        return NextResponse.json({ error }, { status: response.status })
      }

      return NextResponse.json(await response.json())
    } else {
      // Batch analyze all projects
      const response = await fetch(`${BACKEND_URL}/analyze-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        const error = await response.text()
        return NextResponse.json({ error }, { status: response.status })
      }

      return NextResponse.json(await response.json())
    }
  } catch (error) {
    console.error('[v0] Analyze error:', error)
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Analysis failed' 
    }, { status: 500 })
  }
}

// Get existing analyses
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const projectId = searchParams.get('projectId')

    if (projectId) {
      const response = await fetch(`${BACKEND_URL}/analyses/${projectId}`)
      if (!response.ok) {
        return NextResponse.json({ error: 'Analysis not found' }, { status: 404 })
      }
      return NextResponse.json(await response.json())
    } else {
      const response = await fetch(`${BACKEND_URL}/analyses`)
      if (!response.ok) {
        return NextResponse.json({ error: 'Failed to fetch analyses' }, { status: response.status })
      }
      return NextResponse.json(await response.json())
    }
  } catch (error) {
    console.error('[v0] Get analyses error:', error)
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Failed to fetch analyses' 
    }, { status: 500 })
  }
}
