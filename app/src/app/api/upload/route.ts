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

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    
    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 })
    }

    const extractedFiles: { name: string; size: number; content: string }[] = []

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
          // Get the actual CSV content as text
          const content = await zipEntry.async('string')
          extractedFiles.push({ 
            name: baseName, 
            size: content.length,
            content: content
          })
        }
      }
    } else if (file.name.endsWith('.csv')) {
      // Single CSV file - read content
      const content = await file.text()
      extractedFiles.push({ 
        name: file.name, 
        size: content.length,
        content: content
      })
    } else {
      return NextResponse.json({ 
        error: 'Invalid file type. Please upload a ZIP file containing CSVs or individual CSV files.' 
      }, { status: 400 })
    }

    // Validate extracted files
    const extractedNames = extractedFiles.map(f => f.name)
    const missingFiles = EXPECTED_CSV_FILES.filter(f => !extractedNames.includes(f))
    const foundFiles = EXPECTED_CSV_FILES.filter(f => extractedNames.includes(f))
    
    // Forward files to Python backend
    const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
    let backendResult = null
    let backendConnected = false

    try {
      const backendFormData = new FormData()
      for (const { name, content } of extractedFiles) {
        const blob = new Blob([content], { type: 'text/csv' })
        backendFormData.append('files', blob, name)
      }

      const backendResponse = await fetch(`${BACKEND_URL}/upload`, {
        method: 'POST',
        body: backendFormData,
      })

      if (backendResponse.ok) {
        backendResult = await backendResponse.json()
        backendConnected = true
      }
    } catch (error) {
      console.error('[v0] Backend upload error:', error)
    }
    
    return NextResponse.json({
      status: 'ok',
      files: extractedFiles.map(f => ({ name: f.name, size: f.size })),
      expectedFiles: EXPECTED_CSV_FILES,
      foundFiles,
      missingFiles,
      backendConnected,
      backendResult,
      message: backendConnected 
        ? 'Files uploaded to backend successfully. Ready to analyze.'
        : `Files extracted locally. Found ${foundFiles.length}/${EXPECTED_CSV_FILES.length} expected files.`,
    })

  } catch (error) {
    console.error('[v0] Upload error:', error)
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Upload failed' 
    }, { status: 500 })
  }
}
