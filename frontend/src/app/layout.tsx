import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Navigation, MobileNavigation } from '@/components/navigation'
import { ErrorBoundary } from '@/components/error-boundary'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Professional Poker Analyzer',
  description: 'Advanced poker hand analysis and statistics platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ErrorBoundary>
          <div className="min-h-screen bg-background">
            <Navigation />
            <main className="pb-16 md:pb-0">
              {children}
            </main>
            <MobileNavigation />
          </div>
        </ErrorBoundary>
      </body>
    </html>
  )
}