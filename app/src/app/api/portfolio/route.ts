import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const endpoint = searchParams.get('endpoint') || 'summary'

    let url = `${BACKEND_URL}/portfolio/${endpoint}`
    
    const response = await fetch(url)
    
    if (!response.ok) {
      const error = await response.text()
      return NextResponse.json({ error }, { status: response.status })
    }

    return NextResponse.json(await response.json())

  } catch (error) {
    console.error('[v0] Portfolio fetch error:', error)
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Failed to fetch portfolio data' 
    }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const action = searchParams.get('action')
    
    if (action === 'optimize') {
      const response = await fetch(`${BACKEND_URL}/portfolio/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      if (!response.ok) {
        const error = await response.text()
        return NextResponse.json({ error }, { status: response.status })
      }
      
      return NextResponse.json(await response.json())
    }
    
    return NextResponse.json({ error: 'Invalid action' }, { status: 400 })

  } catch (error) {
    console.error('[v0] Portfolio action error:', error)
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Portfolio action failed' 
    }, { status: 500 })
  }
}
