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
export function APIErrorBoundary({ 
  children, 
  title = "API Error",
  fallbackData,
  onRetry
}: { 
  children: React.ReactNode;
  title?: string;
  fallbackData?: any;
  onRetry?: () => void;
}) {
  return (
    <ErrorBoundary
      title={title}
      showDetails={process.env.NODE_ENV === 'development'}
      fallback={({ error, reset }) => (
        <div className="min-h-[200px] flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-destructive flex items-center gap-2">
                <ErrorIcon className="h-5 w-5" />
                {title}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                This component encountered an error and couldn't load properly.
              </p>
              
              {fallbackData && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-md">
                  <p className="text-xs text-amber-700 mb-2">
                    Showing cached data while we try to resolve the issue.
                  </p>
                </div>
              )}
              
              <div className="flex flex-col sm:flex-row gap-2">
                <Button onClick={() => {
                  reset();
                  onRetry?.();
                }} className="flex-1">
                  Try Again
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => window.location.reload()}
                  className="flex-1"
                >
                  Reload Page
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    >
      {children}
    </ErrorBoundary>
  );
}

export function ChartErrorBoundary({ 
  children, 
  onRetry,
  fallbackData 
}: { 
  children: React.ReactNode;
  onRetry?: () => void;
  fallbackData?: any;
}) {
  return (
    <ErrorBoundary
      title="Chart Error"
      fallback={({ reset }) => (
        <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-center">
            <ErrorIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-3">Unable to load chart</p>
            
            {fallbackData && (
              <p className="text-xs text-amber-600 mb-3">
                Cached chart data is available
              </p>
            )}
            
            <div className="flex flex-col sm:flex-row gap-2 justify-center">
              <Button variant="outline" size="sm" onClick={() => {
                reset();
                onRetry?.();
              }}>
                Retry
              </Button>
              
              {fallbackData && (
                <Button variant="ghost" size="sm" onClick={() => {
                  // Show fallback data logic would go here
                  reset();
                }}>
                  Show Cached
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    >
      {children}
    </ErrorBoundary>
  );
}

// Widget-specific error boundary with enhanced features
export function WidgetErrorBoundary({ 
  children, 
  widgetId,
  title,
  onRetry,
  fallbackData,
  priority = "medium"
}: { 
  children: React.ReactNode;
  widgetId: string;
  title: string;
  onRetry?: () => void;
  fallbackData?: any;
  priority?: "high" | "medium" | "low";
}) {
  const [retryCount, setRetryCount] = React.useState(0);
  const maxRetries = priority === "high" ? 3 : 1;

  const handleRetry = React.useCallback(() => {
    if (retryCount < maxRetries) {
      setRetryCount(prev => prev + 1);
      onRetry?.();
    }
  }, [retryCount, maxRetries, onRetry]);

  // Auto-retry for high priority widgets
  React.useEffect(() => {
    if (priority === "high" && retryCount > 0 && retryCount < maxRetries) {
      const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 8000);
      const timer = setTimeout(handleRetry, delay);
      return () => clearTimeout(timer);
    }
  }, [retryCount, priority, maxRetries, handleRetry]);

  return (
    <ErrorBoundary
      title={`${title} Error`}
      fallback={({ error, reset }) => (
        <Card className="min-h-[200px] border-destructive/20 bg-destructive/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-destructive flex items-center gap-2">
              <ErrorIcon className="h-4 w-4" />
              {title} Error
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground mb-4">
                This widget encountered an error and couldn't load.
              </p>
              
              {fallbackData && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-md mb-4">
                  <p className="text-xs text-amber-700">
                    Cached data is available for this widget.
                  </p>
                </div>
              )}
              
              {retryCount > 0 && (
                <p className="text-xs text-muted-foreground mb-3">
                  Retry attempt {retryCount}/{maxRetries}
                </p>
              )}
              
              <div className="flex flex-col gap-2">
                {retryCount < maxRetries && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => {
                      reset();
                      handleRetry();
                    }}
                  >
                    {retryCount > 0 ? 'Retry Again' : 'Try Again'}
                  </Button>
                )}
                
                {fallbackData && (
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => {
                      // Logic to show fallback data would be handled by parent
                      reset();
                    }}
                  >
                    Show Cached Data
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
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