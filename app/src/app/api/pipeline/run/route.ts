import { NextRequest, NextResponse } from 'next/server'
import { runPipeline } from '@/lib/pipeline/engine'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}))
    const csvFiles = body.csvFiles as Record<string, string> | undefined
    
    if (csvFiles && Object.keys(csvFiles).length > 0) {
      // Run the actual pipeline with provided data
      const csvMap = new Map(Object.entries(csvFiles))
      const result = await runPipeline(csvMap)
      
      return NextResponse.json({
        status: result.status,
        mode: 'live',
        summary: result.summary,
        flagged_projects: result.flagged_projects,
        steps: result.steps,
      })
    }
    
    // No data provided - return instruction to use simulation
    return NextResponse.json({
      status: 'ready',
      mode: 'simulation',
      message: 'No CSV data provided. Upload files first or run in simulation mode.',
    })
    
  } catch (error) {
    console.error('[v0] Pipeline error:', error)
    return NextResponse.json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Pipeline execution failed',
    }, { status: 500 })
  }
}

// Also support GET for status checks
export async function GET() {
  return NextResponse.json({
    status: 'ready',
    mode: 'standalone',
    message: 'Pipeline engine ready. POST with csvFiles to run analysis.',
  })
}
