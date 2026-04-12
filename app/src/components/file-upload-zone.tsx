'use client'

import { useState, useCallback, useRef } from 'react'
import { Upload, FileArchive, CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-react'

interface UploadedFile {
  name: string
  size: number
  status: 'uploading' | 'success' | 'error'
  progress: number
}

export function FileUploadZone() {
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<UploadedFile[]>([])
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
    
    // Simulate upload progress
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

  return (
    <div className="w-full max-w-2xl mx-auto">
      <input
        ref={fileInputRef}
        type="file"
        accept=".zip"
        multiple
        onChange={handleFileSelect}
        className="hidden"
      />
      
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative overflow-hidden cursor-pointer
          border-2 border-dashed rounded-2xl p-12
          transition-all duration-300 ease-out
          ${isDragging 
            ? 'border-primary bg-primary/10 scale-[1.02]' 
            : 'border-border hover:border-primary/50 hover:bg-muted/50'
          }
        `}
      >
        {/* Animated background gradient */}
        <div className={`
          absolute inset-0 opacity-0 transition-opacity duration-300
          bg-gradient-to-br from-primary/20 via-transparent to-primary/10
          ${isDragging ? 'opacity-100' : ''}
        `} />
        
        {/* Shimmer effect */}
        <div className={`
          absolute inset-0 -translate-x-full bg-gradient-to-r 
          from-transparent via-white/10 to-transparent
          ${isDragging ? 'animate-shimmer' : ''}
        `} />
        
        <div className="relative flex flex-col items-center gap-4 text-center">
          <div className={`
            w-20 h-20 rounded-2xl flex items-center justify-center
            transition-all duration-300
            ${isDragging 
              ? 'bg-primary text-primary-foreground scale-110 animate-bounce-gentle' 
              : 'bg-muted text-muted-foreground'
            }
          `}>
            <Upload className="w-10 h-10" />
          </div>
          
          <div>
            <p className="text-xl font-semibold text-foreground">
              {isDragging ? 'Drop your files here' : 'Upload Financial Data'}
            </p>
            <p className="text-muted-foreground mt-2">
              Drag and drop your ZIP files here, or click to browse
            </p>
            <p className="text-sm text-muted-foreground/70 mt-1">
              Supports: .zip files containing CSV, Excel, JSON data
            </p>
          </div>

          <button
            type="button"
            className="
              mt-2 px-6 py-3 rounded-xl font-medium
              bg-primary text-primary-foreground
              hover:bg-primary-dark transition-colors
              shadow-lg shadow-primary/25
            "
          >
            Browse Files
          </button>
        </div>
      </div>

      {/* Uploaded files list */}
      {files.length > 0 && (
        <div className="mt-6 space-y-3">
          <p className="text-sm font-medium text-muted-foreground">Uploaded Files</p>
          {files.map((file) => (
            <div
              key={file.name}
              className="
                flex items-center gap-4 p-4 rounded-xl
                bg-card border border-border
                animate-scale-in
              "
            >
              <div className={`
                w-12 h-12 rounded-xl flex items-center justify-center shrink-0
                ${file.status === 'success' ? 'bg-green-500/10 text-green-500' : 
                  file.status === 'error' ? 'bg-destructive/10 text-destructive' :
                  'bg-primary/10 text-primary'}
              `}>
                {file.status === 'uploading' ? (
                  <Loader2 className="w-6 h-6 animate-spin" />
                ) : file.status === 'success' ? (
                  <CheckCircle2 className="w-6 h-6" />
                ) : file.status === 'error' ? (
                  <AlertCircle className="w-6 h-6" />
                ) : (
                  <FileArchive className="w-6 h-6" />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">{file.name}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-sm text-muted-foreground">
                    {formatFileSize(file.size)}
                  </span>
                  {file.status === 'uploading' && (
                    <span className="text-sm text-primary">
                      {Math.round(file.progress)}%
                    </span>
                  )}
                  {file.status === 'success' && (
                    <span className="text-sm text-green-500">Complete</span>
                  )}
                </div>
                
                {/* Progress bar */}
                {file.status === 'uploading' && (
                  <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary rounded-full transition-all duration-200"
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
                className="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
