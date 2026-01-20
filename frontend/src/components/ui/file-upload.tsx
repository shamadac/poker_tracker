"use client"

import React, { useCallback, useState, useRef } from 'react'
import { Upload, X, FileText, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { Button } from './button'
import { Card, CardContent } from './card'
import { Progress } from './progress'
import { cn } from '@/lib/utils'

export interface FileUploadProps {
  onFilesSelected: (files: File[]) => void
  onUpload?: (files: File[]) => Promise<void>
  accept?: string
  multiple?: boolean
  maxSize?: number // in bytes
  maxFiles?: number
  disabled?: boolean
  className?: string
  children?: React.ReactNode
}

export interface UploadedFile {
  file: File
  id: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
  taskId?: string
}

export function FileUpload({
  onFilesSelected,
  onUpload,
  accept = '.txt,.log',
  multiple = true,
  maxSize = 50 * 1024 * 1024, // 50MB
  maxFiles = 10,
  disabled = false,
  className,
  children
}: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = useCallback((file: File): string | null => {
    if (file.size > maxSize) {
      return `File size exceeds ${Math.round(maxSize / 1024 / 1024)}MB limit`
    }
    
    if (accept && !accept.split(',').some(ext => 
      file.name.toLowerCase().endsWith(ext.trim().toLowerCase())
    )) {
      return `File type not supported. Accepted: ${accept}`
    }
    
    return null
  }, [maxSize, accept])

  const handleFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files)
    const validFiles: File[] = []
    const newUploadedFiles: UploadedFile[] = []

    // Check total file count
    if (uploadedFiles.length + fileArray.length > maxFiles) {
      alert(`Maximum ${maxFiles} files allowed`)
      return
    }

    fileArray.forEach((file, index) => {
      const error = validateFile(file)
      const id = `${Date.now()}-${index}`
      
      if (error) {
        newUploadedFiles.push({
          file,
          id,
          status: 'error',
          progress: 0,
          error
        })
      } else {
        validFiles.push(file)
        newUploadedFiles.push({
          file,
          id,
          status: 'pending',
          progress: 0
        })
      }
    })

    setUploadedFiles(prev => [...prev, ...newUploadedFiles])
    
    if (validFiles.length > 0) {
      onFilesSelected(validFiles)
    }
  }, [uploadedFiles.length, maxFiles, validateFile, onFilesSelected])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragOver(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    
    if (disabled) return
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFiles(files)
    }
  }, [disabled, handleFiles])

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFiles(files)
    }
    // Reset input value to allow selecting the same file again
    e.target.value = ''
  }, [handleFiles])

  const handleClick = useCallback(() => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click()
    }
  }, [disabled])

  const removeFile = useCallback((id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id))
  }, [])

  const clearAllFiles = useCallback(() => {
    setUploadedFiles([])
  }, [])

  const updateFileStatus = useCallback((id: string, status: UploadedFile['status'], progress?: number, error?: string, taskId?: string) => {
    setUploadedFiles(prev => prev.map(f => 
      f.id === id 
        ? { ...f, status, progress: progress ?? f.progress, error, taskId }
        : f
    ))
  }, [])

  const handleUpload = useCallback(async () => {
    if (!onUpload) return

    const pendingFiles = uploadedFiles.filter(f => f.status === 'pending')
    if (pendingFiles.length === 0) return

    for (const uploadedFile of pendingFiles) {
      try {
        updateFileStatus(uploadedFile.id, 'uploading', 0)
        await onUpload([uploadedFile.file])
        updateFileStatus(uploadedFile.id, 'success', 100)
      } catch (error) {
        updateFileStatus(uploadedFile.id, 'error', 0, error instanceof Error ? error.message : 'Upload failed')
      }
    }
  }, [uploadedFiles, onUpload, updateFileStatus])

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const pendingFiles = uploadedFiles.filter(f => f.status === 'pending')
  const hasFiles = uploadedFiles.length > 0

  return (
    <div className={cn("space-y-4", className)}>
      {/* Drop Zone */}
      <Card
        className={cn(
          "border-2 border-dashed transition-colors cursor-pointer",
          isDragOver && !disabled && "border-primary bg-primary/5",
          disabled && "opacity-50 cursor-not-allowed",
          !isDragOver && "border-muted-foreground/25 hover:border-muted-foreground/50"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <CardContent className="flex flex-col items-center justify-center py-8 px-4 text-center">
          <Upload className={cn(
            "h-10 w-10 mb-4",
            isDragOver && !disabled ? "text-primary" : "text-muted-foreground"
          )} />
          
          {children || (
            <>
              <h3 className="text-lg font-semibold mb-2">
                {isDragOver ? "Drop files here" : "Upload Hand History Files"}
              </h3>
              <p className="text-muted-foreground mb-4">
                Drag and drop your poker hand history files here, or click to browse
              </p>
              <div className="text-sm text-muted-foreground space-y-1">
                <p>Supported formats: {accept}</p>
                <p>Maximum file size: {Math.round(maxSize / 1024 / 1024)}MB</p>
                <p>Maximum files: {maxFiles}</p>
              </div>
            </>
          )}
          
          <input
            ref={fileInputRef}
            type="file"
            accept={accept}
            multiple={multiple}
            onChange={handleFileInputChange}
            className="hidden"
            disabled={disabled}
          />
        </CardContent>
      </Card>

      {/* File List */}
      {hasFiles && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold">
                Selected Files ({uploadedFiles.length})
              </h4>
              <div className="flex gap-2">
                {onUpload && pendingFiles.length > 0 && (
                  <Button
                    onClick={handleUpload}
                    size="sm"
                    disabled={disabled}
                  >
                    Upload {pendingFiles.length} file{pendingFiles.length !== 1 ? 's' : ''}
                  </Button>
                )}
                <Button
                  onClick={clearAllFiles}
                  variant="outline"
                  size="sm"
                  disabled={disabled}
                >
                  Clear All
                </Button>
              </div>
            </div>

            <div className="space-y-3">
              {uploadedFiles.map((uploadedFile) => (
                <div
                  key={uploadedFile.id}
                  className="flex items-center gap-3 p-3 border rounded-lg"
                >
                  {getStatusIcon(uploadedFile.status)}
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-medium truncate">
                        {uploadedFile.file.name}
                      </p>
                      <span className="text-sm text-muted-foreground">
                        {formatFileSize(uploadedFile.file.size)}
                      </span>
                    </div>
                    
                    {uploadedFile.status === 'uploading' && (
                      <Progress value={uploadedFile.progress} className="h-2" />
                    )}
                    
                    {uploadedFile.error && (
                      <p className="text-sm text-red-500 mt-1">
                        {uploadedFile.error}
                      </p>
                    )}
                    
                    {uploadedFile.status === 'success' && (
                      <p className="text-sm text-green-600 mt-1">
                        Upload completed successfully
                        {uploadedFile.taskId && (
                          <span className="ml-2 text-muted-foreground">
                            Task ID: {uploadedFile.taskId}
                          </span>
                        )}
                      </p>
                    )}
                  </div>
                  
                  <Button
                    onClick={() => removeFile(uploadedFile.id)}
                    variant="ghost"
                    size="sm"
                    disabled={disabled || uploadedFile.status === 'uploading'}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Progress component if not already available
export function Progress({ value, className, ...props }: {
  value: number
  className?: string
  [key: string]: any
}) {
  return (
    <div
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-secondary",
        className
      )}
      {...props}
    >
      <div
        className="h-full w-full flex-1 bg-primary transition-all"
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </div>
  )
}