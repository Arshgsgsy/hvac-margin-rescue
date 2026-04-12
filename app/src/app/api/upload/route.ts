import { NextRequest, NextResponse } from 'next/server'
import JSZip from 'jszip'

const EXPECTED_CSV_FILES = [
  "contracts_all.csv",
  "labor_logs_all.csv",
  "billing_history_all.csv",
  "billing_line_items_all.csv",
  "change_orders_all.csv",
  "material_deliveries_all.csv",
  "rfis_all.csv",
  "field_notes_all.csv",
  "sov_all.csv",
  "sov_budget_all.csv",
]

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    
    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 })
    }

    const extractedFiles: { name: string; content: Blob }[] = []

    // Check if it's a ZIP file
    if (file.name.endsWith('.zip')) {
      const arrayBuffer = await file.arrayBuffer()
      const zip = await JSZip.loadAsync(arrayBuffer)
      
      // Extract CSV files from ZIP
      for (const [filename, zipEntry] of Object.entries(zip.files)) {
        if (zipEntry.dir) continue
        
        // Get just the filename without path
        const baseName = filename.split('/').pop() || filename
        
        if (baseName.endsWith('.csv')) {
          const content = await zipEntry.async('blob')
          extractedFiles.push({ name: baseName, content })
        }
      }
    } else if (file.name.endsWith('.csv')) {
      // Single CSV file
      extractedFiles.push({ name: file.name, content: file })
    } else {
      return NextResponse.json({ 
        error: 'Invalid file type. Please upload a ZIP file containing CSVs or individual CSV files.' 
      }, { status: 400 })
    }

    // Validate extracted files
    const extractedNames = extractedFiles.map(f => f.name)
    const missingFiles = EXPECTED_CSV_FILES.filter(f => !extractedNames.includes(f))
    
    if (missingFiles.length > 0 && extractedFiles.length > 0) {
      // Allow partial uploads but warn
      console.log(`[v0] Warning: Missing expected files: ${missingFiles.join(', ')}`)
    }

    // Try to forward files to backend
    let backendResult = null
    let backendConnected = false
    
    try {
      const backendFormData = new FormData()
      for (const { name, content } of extractedFiles) {
        backendFormData.append('files', content, name)
      }

      const backendResponse = await fetch(`${BACKEND_URL}/upload`, {
        method: 'POST',
        body: backendFormData,
        signal: AbortSignal.timeout(10000), // 10 second timeout
      })

      if (backendResponse.ok) {
        backendResult = await backendResponse.json()
        backendConnected = true
      } else {
        console.log('[v0] Backend upload failed, will use simulation mode')
      }
    } catch (error) {
      console.log('[v0] Backend offline, will use simulation mode:', error)
    }
    
    return NextResponse.json({
      status: 'ok',
      files: extractedFiles.map(f => f.name),
      backendConnected,
      backendResult,
      message: backendConnected 
        ? 'Files uploaded to backend successfully' 
        : 'Files processed locally (backend offline - demo mode)',
    })

  } catch (error) {
    console.error('[v0] Upload error:', error)
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Upload failed' 
    }, { status: 500 })
  }
}
