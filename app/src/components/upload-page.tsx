'use client'

import { useState, useRef, useCallback } from 'react'
import { Upload, FileArchive, CheckCircle2, X, ArrowRight, Shield, BarChart3, Zap, FileSpreadsheet } from 'lucide-react'

interface UploadedFile {
  name: string
  size: number
  type: string
}

interface UploadPageProps {
  onProceed: () => void
}

export function UploadPage({ onProceed }: UploadPageProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = useCallback((fileList: FileList | null) => {
    if (!fileList) return
    
    const newFiles: UploadedFile[] = []
    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i]
      // Accept zip files and common financial data formats
      if (file.name.endsWith('.zip') || file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.json')) {
        newFiles.push({
          name: file.name,
          size: file.size,
          type: file.type || 'application/zip'
        })
      }
    }
    
    if (newFiles.length > 0) {
      setIsUploading(true)
      // Simulate upload processing
      setTimeout(() => {
        setFiles(prev => [...prev, ...newFiles])
        setIsUploading(false)
        setUploadComplete(true)
      }, 1500)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }, [handleFiles])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
    if (files.length === 1) {
      setUploadComplete(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/20 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-foreground font-bold text-lg">MarginIQ</h1>
              <p className="text-muted-foreground text-xs">Financial Intelligence Platform</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-3xl">
          {/* Title section */}
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-foreground mb-3">
              Upload Your Financial Data
            </h2>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              Upload a ZIP file containing your company&apos;s financial records. Our AI will analyze margins, detect risks, and identify recovery opportunities.
            </p>
          </div>

          {/* Upload zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => inputRef.current?.click()}
            className={`
              relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer
              transition-all duration-300
              ${isDragging 
                ? 'border-primary bg-primary/10 scale-[1.02]' 
                : uploadComplete 
                  ? 'border-emerald-500/50 bg-emerald-500/5' 
                  : 'border-border hover:border-primary/50 hover:bg-muted/30'
              }
            `}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".zip,.csv,.xlsx,.json"
              multiple
              onChange={(e) => handleFiles(e.target.files)}
              className="hidden"
            />

            {isUploading ? (
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center animate-pulse">
                  <Upload className="w-8 h-8 text-primary" />
                </div>
                <p className="text-foreground font-semibold">Processing files...</p>
                <div className="w-48 h-1.5 rounded-full bg-muted overflow-hidden">
                  <div className="h-full bg-primary rounded-full animate-[loading_1.5s_ease-in-out_infinite]" style={{ width: '60%' }} />
                </div>
              </div>
            ) : uploadComplete && files.length > 0 ? (
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 flex items-center justify-center">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                </div>
                <div>
                  <p className="text-foreground font-semibold text-lg">Files Ready</p>
                  <p className="text-muted-foreground text-sm mt-1">
                    {files.length} file{files.length > 1 ? 's' : ''} uploaded successfully
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center">
                  <FileArchive className="w-8 h-8 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-foreground font-semibold text-lg">
                    Drop your ZIP file here
                  </p>
                  <p className="text-muted-foreground text-sm mt-1">
                    or click to browse
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  <span>Supports: ZIP, CSV, XLSX, JSON</span>
                </div>
              </div>
            )}
          </div>

          {/* Uploaded files list */}
          {files.length > 0 && (
            <div className="mt-6 space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between px-4 py-3 rounded-xl bg-card border border-border/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <FileArchive className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-foreground text-sm font-medium">{file.name}</p>
                      <p className="text-muted-foreground text-xs">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFile(index)
                    }}
                    className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                  >
                    <X className="w-4 h-4 text-muted-foreground" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Proceed button */}
          <div className="mt-8 flex justify-center">
            <button
              onClick={onProceed}
              disabled={files.length === 0}
              className={`
                flex items-center gap-2 px-8 py-3.5 rounded-xl text-sm font-semibold
                transition-all duration-200
                ${files.length > 0
                  ? 'bg-primary text-white hover:bg-primary/90 shadow-lg shadow-primary/25'
                  : 'bg-muted text-muted-foreground cursor-not-allowed'
                }
              `}
            >
              <Zap className="w-4 h-4" />
              Analyze Financial Data
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Features */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                icon: BarChart3,
                title: 'Margin Analysis',
                description: 'Identify margin erosion across your entire portfolio'
              },
              {
                icon: Zap,
                title: 'AI Root Cause',
                description: 'Claude AI identifies why costs exceeded budgets'
              },
              {
                icon: Shield,
                title: 'Recovery Actions',
                description: 'Get dollar-quantified recommendations to recover losses'
              }
            ].map((feature) => (
              <div
                key={feature.title}
                className="flex items-start gap-3 p-4 rounded-xl bg-card/50 border border-border/30"
              >
                <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                  <feature.icon className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <p className="text-foreground text-sm font-semibold">{feature.title}</p>
                  <p className="text-muted-foreground text-xs mt-0.5">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Security note */}
          <div className="mt-8 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <Shield className="w-3.5 h-3.5" />
            <span>Your data is processed securely and never stored permanently</span>
          </div>
        </div>
      </main>
    </div>
  )
}
