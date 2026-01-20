import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Navigation, MobileNavigation } from '@/components/navigation'
import { ErrorBoundary } from '@/components/error-boundary'
import { ReactQueryProvider } from '@/lib/react-query'
import { WebSocketProvider } from '@/contexts/websocket-context'
import { PerformanceMonitorComponent } from '@/components/performance-monitor'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  preload: true,
})

export const metadata: Metadata = {
  title: {
    default: 'Professional Poker Analyzer',
    template: '%s | Professional Poker Analyzer'
  },
  description: 'Advanced poker hand analysis and statistics platform with AI-powered insights',
  keywords: ['poker', 'analysis', 'statistics', 'AI', 'hand history', 'PokerStars', 'GGPoker'],
  authors: [{ name: 'Professional Poker Analyzer Team' }],
  creator: 'Professional Poker Analyzer',
  publisher: 'Professional Poker Analyzer',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: '/',
    title: 'Professional Poker Analyzer',
    description: 'Advanced poker hand analysis and statistics platform with AI-powered insights',
    siteName: 'Professional Poker Analyzer',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Professional Poker Analyzer',
    description: 'Advanced poker hand analysis and statistics platform with AI-powered insights',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#000000' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.className}>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
        <link rel="dns-prefetch" href="//fonts.gstatic.com" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Poker Analyzer" />
        <link rel="apple-touch-icon" href="/icon-192x192.png" />
      </head>
      <body className="antialiased">
        <PerformanceMonitorComponent />
        <ReactQueryProvider>
          <WebSocketProvider>
            <ErrorBoundary>
              <div className="min-h-screen bg-background">
                <a 
                  href="#main-content" 
                  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50"
                >
                  Skip to main content
                </a>
                <Navigation />
                <main id="main-content" className="pb-16 md:pb-0" role="main">
                  {children}
                </main>
                <MobileNavigation />
              </div>
            </ErrorBoundary>
          </WebSocketProvider>
        </ReactQueryProvider>
      </body>
    </html>
  )
}