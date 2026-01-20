import { Metadata } from 'next'
import { WifiOff, RefreshCw } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Offline',
  description: 'You are currently offline',
}

export default function OfflinePage() {
  const handleRetry = () => {
    if (typeof window !== 'undefined') {
      window.location.reload()
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-6 p-8">
        <div className="flex justify-center">
          <WifiOff className="h-24 w-24 text-muted-foreground" />
        </div>
        
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">You're Offline</h1>
          <p className="text-muted-foreground max-w-md">
            It looks like you've lost your internet connection. Some features may not be available.
          </p>
        </div>

        <div className="space-y-4">
          <button
            onClick={handleRetry}
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
          
          <div className="text-sm text-muted-foreground">
            <p>While offline, you can still:</p>
            <ul className="mt-2 space-y-1">
              <li>• View previously loaded statistics</li>
              <li>• Access cached hand analysis results</li>
              <li>• Browse the poker education content</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}