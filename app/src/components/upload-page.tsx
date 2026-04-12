'use client'

import { useState, useCallback, useRef } from 'react'
import { 
  Upload, 
  FileArchive, 
  CheckCircle2, 
  AlertCircle, 
  X, 
  Loader2,
  BarChart3,
  Shield,
  Zap,
  ArrowRight
} from 'lucide-react'
import PipelineRunner from './pipeline-runner'

interface UploadedFile {
  name: string
  size: number
  status: 'uploading' | 'success' | 'error'
  progress: number
}

const SUPPORTED_FILES = [
  { name: 'CSV Files', desc: 'Billing, labor, materials data' },
  { name: 'Excel Files', desc: 'Budget and cost spreadsheets' },
  { name: 'JSON Files', desc: 'Structured financial records' },
]

export function UploadPage() {
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [showPipeline, setShowPipeline] = useState(false)
  const [pipelineComplete, setPipelineComplete] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const simulateUpload = (file: File) => {
    const newFile: UploadedFile = {
      name: file.name,
      size: file.size,
      status: 'uploading',
      progress: 0,
    }
    
    setFiles(prev => [...prev, newFile])
    
    const interval = setInterval(() => {
      setFiles(prev => prev.map(f => {
        if (f.name === file.name && f.status === 'uploading') {
          const newProgress = Math.min(f.progress + Math.random() * 30, 100)
          if (newProgress >= 100) {
            clearInterval(interval)
            return { ...f, progress: 100, status: 'success' }
          }
          return { ...f, progress: newProgress }
        }
        return f
      }))
    }, 200)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const droppedFiles = Array.from(e.dataTransfer.files)
    const zipFiles = droppedFiles.filter(f => f.name.endsWith('.zip'))
    
    zipFiles.forEach(file => simulateUpload(file))
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      selectedFiles.forEach(file => simulateUpload(file))
    }
  }

  const removeFile = (fileName: string) => {
    setFiles(prev => prev.filter(f => f.name !== fileName))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const completedFiles = files.filter(f => f.status === 'success')
  const canAnalyze = completedFiles.length > 0 && !showPipeline

  const handleAnalyze = () => {
    if (canAnalyze) {
      setShowPipeline(true)
    }
  }

  const handlePipelineComplete = () => {
    setPipelineComplete(true)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b-2 border-primary bg-background">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg border-2 border-primary flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary" />
            </div>
            <span className="text-xl font-bold text-primary tracking-tight">MarginIQ</span>
          </div>
          
          <nav className="hidden md:flex items-center gap-8">
            <a href="#" className="text-muted-foreground hover:text-primary font-medium transition-colors">
              Documentation
            </a>
            <a href="#" className="text-muted-foreground hover:text-primary font-medium transition-colors">
              Support
            </a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-12">
        {!showPipeline ? (
          <>
            {/* Step Header */}
            <div className="mb-10">
              <h1 className="text-2xl font-bold text-primary uppercase tracking-wide">
                Step 1: Upload Financial Data
              </h1>
              <p className="mt-2 text-muted-foreground text-lg">
                Upload your company&apos;s financial data as a ZIP file to begin analysis. 
                We support CSV, Excel, and JSON formats.
              </p>
            </div>

            <div className="grid lg:grid-cols-3 gap-8">
              {/* Upload Zone - Main Column */}
              <div className="lg:col-span-2 space-y-6">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".zip"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                />

                {/* Upload Area */}
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`
                    relative cursor-pointer rounded-lg
                    border-2 border-dashed p-10
                    transition-all duration-200
                    ${isDragging 
                      ? 'border-accent bg-accent/10' 
                      : 'border-primary hover:border-accent hover:bg-muted/50'
                    }
                  `}
                >
                  <div className="flex flex-col items-center text-center">
                    <div className={`
                      w-16 h-16 rounded-lg flex items-center justify-center mb-4
                      border-2 transition-colors duration-200
                      ${isDragging 
                        ? 'border-accent bg-accent text-accent-foreground' 
                        : 'border-primary bg-primary text-primary-foreground'
                      }
                    `}>
                      <Upload className="w-8 h-8" />
                    </div>
                    
                    <p className="text-lg font-semibold text-foreground">
                      {isDragging ? 'Drop your files here' : 'Drag & Drop a file here'}
                    </p>
                    <p className="mt-1 text-muted-foreground">
                      or click to browse your files
                    </p>
                  </div>
                </div>

                {/* Upload Button */}
                <div className="flex items-center gap-4">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="
                      px-6 py-3 rounded border-2 border-primary
                      bg-background text-primary font-semibold
                      hover:bg-primary hover:text-primary-foreground
                      transition-colors duration-200
                    "
                  >
                    Upload file
                  </button>
                  
                  <button
                    type="button"
                    disabled={!canAnalyze}
                    onClick={handleAnalyze}
                    className={`
                      px-6 py-3 rounded font-semibold flex items-center gap-2
                      transition-all duration-200
                      ${canAnalyze 
                        ? 'bg-accent text-accent-foreground hover:bg-accent/90 shadow-lg cursor-pointer' 
                        : 'bg-muted text-muted-foreground cursor-not-allowed'
                      }
                    `}
                  >
                    Analyze Data
                    <ArrowRight className="w-4 h-4" />
                  </button>

                  {files.some(f => f.status === 'uploading') && (
                    <span className="text-muted-foreground flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing...
                    </span>
                  )}
                </div>

                {/* Uploaded Files List */}
                {files.length > 0 && (
                  <div className="border-2 border-primary rounded-lg overflow-hidden">
                    <div className="bg-primary px-4 py-2">
                      <p className="text-sm font-semibold text-primary-foreground uppercase tracking-wide">
                        Uploaded Files
                      </p>
                    </div>
                    <div className="divide-y divide-border">
                      {files.map((file) => (
                        <div
                          key={file.name}
                          className="flex items-center gap-4 p-4 bg-card"
                        >
                          <div className={`
                            w-10 h-10 rounded flex items-center justify-center shrink-0
                            ${file.status === 'success' 
                              ? 'bg-emerald-100 text-emerald-600' 
                              : file.status === 'error' 
                                ? 'bg-red-100 text-red-600'
                                : 'bg-accent/20 text-accent'
                            }
                          `}>
                            {file.status === 'uploading' ? (
                              <Loader2 className="w-5 h-5 animate-spin" />
                            ) : file.status === 'success' ? (
                              <CheckCircle2 className="w-5 h-5" />
                            ) : file.status === 'error' ? (
                              <AlertCircle className="w-5 h-5" />
                            ) : (
                              <FileArchive className="w-5 h-5" />
                            )}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-foreground truncate">{file.name}</p>
                            <div className="flex items-center gap-3 mt-1">
                              <span className="text-sm text-muted-foreground">
                                {formatFileSize(file.size)}
                              </span>
                              {file.status === 'uploading' && (
                                <span className="text-sm text-accent font-medium">
                                  {Math.round(file.progress)}%
                                </span>
                              )}
                              {file.status === 'success' && (
                                <span className="text-sm text-emerald-600 font-medium">Ready</span>
                              )}
                            </div>
                            
                            {file.status === 'uploading' && (
                              <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-accent rounded-full transition-all duration-200"
                                  style={{ width: `${file.progress}%` }}
                                />
                              </div>
                            )}
                          </div>
                          
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              removeFile(file.name)
                            }}
                            className="p-2 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Supported Files Card */}
                <div className="border-2 border-primary rounded-lg overflow-hidden">
                  <div className="bg-primary px-4 py-2">
                    <p className="text-sm font-semibold text-primary-foreground uppercase tracking-wide">
                      Supported File Types
                    </p>
                  </div>
                  <div className="p-4 bg-card space-y-3">
                    {SUPPORTED_FILES.map((item) => (
                      <div key={item.name} className="flex items-start gap-3">
                        <FileArchive className="w-5 h-5 text-accent mt-0.5 shrink-0" />
                        <div>
                          <p className="font-medium text-foreground">{item.name}</p>
                          <p className="text-sm text-muted-foreground">{item.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Features Card */}
                <div className="border-2 border-primary rounded-lg overflow-hidden">
                  <div className="bg-primary px-4 py-2">
                    <p className="text-sm font-semibold text-primary-foreground uppercase tracking-wide">
                      What We Analyze
                    </p>
                  </div>
                  <div className="p-4 bg-card space-y-4">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center shrink-0">
                        <BarChart3 className="w-4 h-4 text-accent" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">Margin Analysis</p>
                        <p className="text-sm text-muted-foreground">Track cost vs budget performance</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center shrink-0">
                        <Shield className="w-4 h-4 text-accent" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">Risk Detection</p>
                        <p className="text-sm text-muted-foreground">Identify potential issues early</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center shrink-0">
                        <Zap className="w-4 h-4 text-accent" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">Instant Insights</p>
                        <p className="text-sm text-muted-foreground">Results in under 30 seconds</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Security Notice */}
                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-muted-foreground mt-0.5 shrink-0" />
                    <div>
                      <p className="font-medium text-foreground">Secure Processing</p>
                      <p className="text-sm text-muted-foreground">
                        Your data is encrypted and processed securely. We never store raw financial data.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Pipeline View */}
            <div className="mb-10">
              <h1 className="text-2xl font-bold text-primary uppercase tracking-wide">
                Step 2: Analyzing Your Data
              </h1>
              <p className="mt-2 text-muted-foreground text-lg">
                Our pipeline is processing your financial data. This includes data cleaning, 
                loading into our analytics engine, and AI-powered root cause analysis.
              </p>
            </div>

            <div className="max-w-4xl">
              <PipelineRunner onComplete={handlePipelineComplete} />
            </div>

            {pipelineComplete && (
              <div className="mt-8 p-6 rounded-lg bg-emerald-500/10 border-2 border-emerald-500/30">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                  <div>
                    <h3 className="font-semibold text-foreground">Analysis Complete</h3>
                    <p className="text-muted-foreground text-sm mt-1">
                      Your dashboard is ready. Navigate to the dashboard to view detailed insights and recommendations.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t-2 border-primary mt-auto">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded border-2 border-primary flex items-center justify-center">
              <BarChart3 className="w-3 h-3 text-primary" />
            </div>
            <span className="font-semibold text-primary">MarginIQ</span>
          </div>
          <p className="text-sm text-muted-foreground">
            2026 MarginIQ. Built for financial excellence.
          </p>
        </div>
      </footer>
    </div>
  )
}
