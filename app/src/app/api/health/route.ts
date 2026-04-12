import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000), // 5 second timeout
    })

    if (!response.ok) {
      return NextResponse.json({ 
        status: 'error',
        backend: 'unreachable',
        message: 'Backend health check failed'
      }, { status: 503 })
    }

    const backendHealth = await response.json()
    
    return NextResponse.json({
      status: 'ok',
      backend: 'connected',
      backendHealth,
      backendUrl: BACKEND_URL,
    })

  } catch (error) {
    return NextResponse.json({ 
      status: 'degraded',
      backend: 'offline',
      message: 'Backend is not running. Using simulation mode.',
      backendUrl: BACKEND_URL,
    }, { status: 200 }) // Return 200 so frontend knows we're working, just without backend
  }
}
