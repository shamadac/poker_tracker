"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { processAPIError, createErrorBoundaryFallback } from "@/lib/error-handling"

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error?: Error; reset: () => void }>
  title?: string
  showDetails?: boolean
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    
    // Log error details for debugging
    const processedError = processAPIError(error);
    console.error('Processed error details:', {
      category: processedError.category,
      severity: processedError.severity,
      userMessage: processedError.userMessage,
      technicalMessage: processedError.technicalMessage,
      canRetry: processedError.canRetry,
      suggestedActions: processedError.suggestedActions
    });
  }

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || 
        createErrorBoundaryFallback(this.props.title, this.props.showDetails);
      
      return (
        <FallbackComponent 
          error={this.state.error} 
          reset={() => this.setState({ hasError: false, error: undefined })}
        />
      )
    }

    return this.props.children
  }
}

// Enhanced default error fallback with better UX
function DefaultErrorFallback({ error, reset }: { error?: Error; reset: () => void }) {
  const processedError = processAPIError(error);
  
  return (
    <div className="min-h-[400px] flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-destructive flex items-center gap-2">
            <ErrorIcon className="h-5 w-5" />
            Something went wrong
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {processedError.userMessage}
          </p>
          
          {processedError.suggestedActions.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-700">What you can do:</p>
              <ul className="text-xs text-gray-600 space-y-1">
                {processedError.suggestedActions.map((action, index) => (
                  <li key={index} className="flex items-start gap-1">
                    <span className="text-gray-400">•</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {error && process.env.NODE_ENV === 'development' && (
            <details className="text-left">
              <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                Technical Details (Development)
              </summary>
              <pre className="text-xs text-gray-400 mt-2 p-2 bg-gray-50 rounded overflow-auto max-h-32">
                {processedError.technicalMessage}
              </pre>
            </details>
          )}
          
          <div className="flex flex-col sm:flex-row gap-2">
            {processedError.canRetry && (
              <Button onClick={reset} className="flex-1">
                Try Again
              </Button>
            )}
            <Button 
              variant="outline" 
              onClick={() => window.location.reload()}
              className="flex-1"
            >
              Reload Page
            </Button>
          </div>
          
          {processedError.severity === 'high' || processedError.severity === 'critical' && (
            <div className="text-center">
              <Button 
                variant="link" 
                size="sm"
                onClick={() => window.open('/support', '_blank')}
                className="text-xs"
              >
                Contact Support
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Hook for functional components with enhanced error handling
export function useErrorBoundary() {
  const [error, setError] = React.useState<Error | null>(null)

  const resetError = React.useCallback(() => {
    setError(null)
  }, [])

  const captureError = React.useCallback((error: Error) => {
    // Process the error before setting it
    const processedError = processAPIError(error);
    console.error('Error captured by hook:', processedError);
    setError(error)
  }, [])

  React.useEffect(() => {
    if (error) {
      throw error
    }
  }, [error])

  return { captureError, resetError }
}

// Specialized error boundaries for different contexts
export function APIErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      title="API Error"
      showDetails={process.env.NODE_ENV === 'development'}
      fallback={createErrorBoundaryFallback("API Error", process.env.NODE_ENV === 'development')}
    >
      {children}
    </ErrorBoundary>
  );
}

export function ChartErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      title="Chart Error"
      fallback={({ reset }) => (
        <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
          <div className="text-center">
            <ErrorIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-3">Unable to load chart</p>
            <Button variant="outline" size="sm" onClick={reset}>
              Retry
            </Button>
          </div>
        </div>
      )}
    >
      {children}
    </ErrorBoundary>
  );
}

function ErrorIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
    </svg>
  );
}