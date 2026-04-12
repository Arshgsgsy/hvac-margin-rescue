import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    // Forward the request to the Python backend
    const response = await fetch(`${BACKEND_URL}/pipeline/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      const error = await response.text()
      return NextResponse.json({ 
        status: 'error',
        error: `Backend pipeline failed: ${error}` 
      }, { status: response.status })
    }

    const result = await response.json()
    return NextResponse.json(result)
    
  } catch (error) {
    console.error('[v0] Pipeline error:', error)
    return NextResponse.json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Pipeline execution failed',
    }, { status: 500 })
  }
}

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/pipeline/status`)
    if (response.ok) {
      return NextResponse.json(await response.json())
    }
    return NextResponse.json({ status: 'ready' })
  } catch {
    return NextResponse.json({ status: 'backend_offline' })
  }
}
