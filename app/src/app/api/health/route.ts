import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET() {
  try {
    // Check if Python backend is running
    const response = await fetch(`${BACKEND_URL}/health`, {
      signal: AbortSignal.timeout(5000),
    })

    if (response.ok) {
      const backendHealth = await response.json()
      return NextResponse.json({
        status: 'ok',
        backend: 'connected',
        backendHealth,
        backendUrl: BACKEND_URL,
      })
    }

    return NextResponse.json({
      status: 'degraded',
      backend: 'error',
      message: 'Backend returned non-OK status',
    })

  } catch (error) {
    return NextResponse.json({
      status: 'degraded',
      backend: 'offline',
      message: 'Python backend is not running',
      backendUrl: BACKEND_URL,
    })
  }
}
