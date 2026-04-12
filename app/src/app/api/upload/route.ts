import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const incoming = await request.formData()
    const files = incoming.getAll('files')

    if (files.length === 0) {
      const single = incoming.get('file')
      if (single) {
        files.push(single)
      }
    }

    if (files.length === 0) {
      return NextResponse.json({ error: 'No files uploaded' }, { status: 400 })
    }

    const backendFormData = new FormData()
    for (const item of files) {
      if (!(item instanceof File)) {
        return NextResponse.json({ error: 'Invalid multipart payload' }, { status: 400 })
      }
      backendFormData.append('files', item, item.name)
    }

    const response = await fetch(`${BACKEND_URL}/upload`, {
      method: 'POST',
      body: backendFormData,
    })

    const body = await response.text()
    if (!response.ok) {
      return NextResponse.json({ error: body || 'Upload failed' }, { status: response.status })
    }

    return new NextResponse(body, {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (error) {
    console.error('[v0] Upload proxy error:', error)
    return NextResponse.json({
      error: error instanceof Error ? error.message : 'Upload failed',
    }, { status: 500 })
  }
}
