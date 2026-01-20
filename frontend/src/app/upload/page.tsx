"use client"

import { useState, useCallback } from 'react'
import { Container } from '@/components/ui/container'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FileUpload } from '@/components/ui/file-upload'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import { 
  Upload, 
  FileText, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Loader2,
  RefreshCw,
  X
} from 'lucide-react'

interface ProcessingTask {
  id: string
  taskName: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progressPercentage: number
  currentStep: string
  handsProcessed: number
  handsFailed: number
  createdAt: string
  estimatedCompletion?: string
  processingRate?: number
}

export default function UploadPage() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [platform, setPlatform] = useState<string>('')
  const [taskName, setTaskName] = useState<string>('')
  const [isUploading, setIsUploading] = useState(false)
  const [processingTasks, setProcessingTasks] = useState<ProcessingTask[]>([])
  const { toast } = useToast()

  const handleFilesSelected = useCallback((files: File[]) => {
    setSelectedFiles(files)
    if (files.length === 1) {
      setTaskName(`Process ${files[0].name}`)
    } else if (files.length > 1) {
      setTaskName(`Batch process ${files.length} files`)
    }
  }, [])

  const uploadFiles = useCallback(async (files: File[]) => {
    setIsUploading(true)
    
    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        if (platform) formData.append('platform', platform)
        if (taskName) formData.append('task_name', taskName)

        const response = await fetch('/api/v1/file-processing/upload-and-process', {
          method: 'POST',
          body: formData,
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}` // Adjust based on your auth
          }
        })

        if (!response.ok) {
          throw new Error(`Failed to upload ${file.name}`)
        }

        const result = await response.json()
        
        // Add task to processing list
        const newTask: ProcessingTask = {
          id: result.task_id,
          taskName: result.message || `Processing ${file.name}`,
          status: 'pending',
          progressPercentage: 0,
          currentStep: 'Initializing...',
          handsProcessed: 0,
          handsFailed: 0,
          createdAt: new Date().toISOString()
        }
        
        setProcessingTasks(prev => [newTask, ...prev])
        
        toast({
          title: "Upload Started",
          description: `${file.name} has been uploaded and processing started.`,
        })
      }
      
      // Clear selected files after successful upload
      setSelectedFiles([])
      setTaskName('')
      
    } catch (error) {
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to upload files",
        variant: "destructive"
      })
    } finally {
      setIsUploading(false)
    }
  }, [platform, taskName, toast])

  const refreshTaskProgress = useCallback(async (taskId: string) => {
    try {
      const response = await fetch(`/api/v1/file-processing/progress/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        const progress = await response.json()
        setProcessingTasks(prev => prev.map(task => 
          task.id === taskId 
            ? {
                ...task,
                status: progress.is_active ? 'processing' : 
                       progress.progress_percentage === 100 ? 'completed' : task.status,
                progressPercentage: progress.progress_percentage,
                currentStep: progress.current_step,
                handsProcessed: progress.hands_processed,
                handsFailed: progress.hands_failed,
                estimatedCompletion: progress.estimated_completion,
                processingRate: progress.processing_rate
              }
            : task
        ))
      }
    } catch (error) {
      console.error('Failed to refresh task progress:', error)
    }
  }, [])

  const cancelTask = useCallback(async (taskId: string) => {
    try {
      const response = await fetch(`/api/v1/file-processing/cancel/${taskId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        setProcessingTasks(prev => prev.map(task => 
          task.id === taskId 
            ? { ...task, status: 'cancelled', currentStep: 'Cancelled by user' }
            : task
        ))
        
        toast({
          title: "Task Cancelled",
          description: "Processing task has been cancelled.",
        })
      }
    } catch (error) {
      toast({
        title: "Cancellation Failed",
        description: "Failed to cancel the task.",
        variant: "destructive"
      })
    }
  }, [toast])

  const removeTask = useCallback((taskId: string) => {
    setProcessingTasks(prev => prev.filter(task => task.id !== taskId))
  }, [])

  const getStatusIcon = (status: ProcessingTask['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'cancelled':
        return <X className="h-4 w-4 text-gray-500" />
      default:
        return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusBadge = (status: ProcessingTask['status']) => {
    const variants = {
      pending: 'secondary',
      processing: 'default',
      completed: 'success',
      failed: 'destructive',
      cancelled: 'outline'
    } as const

    return (
      <Badge variant={variants[status] || 'secondary'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    )
  }

  return (
    <Container className="py-4 sm:py-6 lg:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Upload Hand Histories</h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Upload and process your poker hand history files
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                File Upload
              </CardTitle>
              <CardDescription>
                Select and upload your hand history files for processing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Platform Selection */}
              <div className="space-y-2">
                <Label htmlFor="platform">Platform (Optional)</Label>
                <Select value={platform} onValueChange={setPlatform}>
                  <SelectTrigger>
                    <SelectValue placeholder="Auto-detect platform" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Auto-detect</SelectItem>
                    <SelectItem value="pokerstars">PokerStars</SelectItem>
                    <SelectItem value="ggpoker">GGPoker</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Task Name */}
              <div className="space-y-2">
                <Label htmlFor="taskName">Task Name (Optional)</Label>
                <Input
                  id="taskName"
                  value={taskName}
                  onChange={(e) => setTaskName(e.target.value)}
                  placeholder="Custom task name"
                />
              </div>
            </CardContent>
          </Card>

          {/* File Upload Component */}
          <FileUpload
            onFilesSelected={handleFilesSelected}
            onUpload={uploadFiles}
            accept=".txt,.log"
            multiple={true}
            maxSize={50 * 1024 * 1024} // 50MB
            maxFiles={10}
            disabled={isUploading}
          />

          {/* Upload Button */}
          {selectedFiles.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <Button
                  onClick={() => uploadFiles(selectedFiles)}
                  disabled={isUploading}
                  className="w-full"
                  size="lg"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Upload and Process {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Processing Tasks Section */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Processing Tasks
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    processingTasks.forEach(task => {
                      if (task.status === 'processing' || task.status === 'pending') {
                        refreshTaskProgress(task.id)
                      }
                    })
                  }}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
              </CardTitle>
              <CardDescription>
                Monitor the progress of your file processing tasks
              </CardDescription>
            </CardHeader>
            <CardContent>
              {processingTasks.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No processing tasks yet</p>
                  <p className="text-sm">Upload files to see processing progress here</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {processingTasks.map((task) => (
                    <div key={task.id} className="border rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(task.status)}
                          <h4 className="font-medium">{task.taskName}</h4>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusBadge(task.status)}
                          {(task.status === 'processing' || task.status === 'pending') && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => cancelTask(task.id)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                          {(task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled') && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeTask(task.id)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>

                      {task.status === 'processing' && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>{task.currentStep}</span>
                            <span>{task.progressPercentage}%</span>
                          </div>
                          <Progress value={task.progressPercentage} />
                        </div>
                      )}

                      <div className="flex justify-between text-sm text-muted-foreground">
                        <div className="space-x-4">
                          <span>Processed: {task.handsProcessed}</span>
                          {task.handsFailed > 0 && (
                            <span className="text-red-500">Failed: {task.handsFailed}</span>
                          )}
                        </div>
                        <div className="space-x-4">
                          {task.processingRate && (
                            <span>{task.processingRate.toFixed(1)} hands/sec</span>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => refreshTaskProgress(task.id)}
                          >
                            <RefreshCw className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>

                      {task.estimatedCompletion && task.status === 'processing' && (
                        <div className="text-sm text-muted-foreground">
                          Estimated completion: {new Date(task.estimatedCompletion).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Container>
  )
}