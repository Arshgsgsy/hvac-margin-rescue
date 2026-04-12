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
    
    // Build csvFiles map for pipeline
    const csvFiles: Record<string, string> = {}
    for (const file of extractedFiles) {
      csvFiles[file.name] = file.content
    }
    
    return NextResponse.json({
      status: 'ok',
      files: extractedFiles.map(f => ({ name: f.name, size: f.size })),
      csvFiles, // Include actual CSV content for pipeline
      expectedFiles: EXPECTED_CSV_FILES,
      foundFiles,
      missingFiles,
      message: missingFiles.length === 0 
        ? 'All expected files found! Ready to analyze.'
        : `Found ${foundFiles.length}/${EXPECTED_CSV_FILES.length} expected files. Ready to analyze.`,
    })

  } catch (error) {
    console.error('[v0] Upload error:', error)
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Upload failed' 
    }, { status: 500 })
  }
}
