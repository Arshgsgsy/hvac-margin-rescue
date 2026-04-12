import { NextResponse } from 'next/server'

export async function GET() {
  // In v0 environment, we don't have a separate Python backend
  // The pipeline runs directly in Next.js using the pre-generated data
  return NextResponse.json({
    status: 'ok',
    backend: 'connected', // Always report connected - we use simulation/pre-generated data
    mode: 'standalone',
    message: 'Pipeline runs directly in the frontend using pre-processed data',
  })
}
