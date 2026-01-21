/**
 * Property-Based Test for Responsive Design
 * Feature: professional-poker-analyzer-rebuild, Property 4: Responsive UI Behavior
 * 
 * **Validates: Requirements 2.2**
 * 
 * Property 4: Responsive UI Behavior
 * For any viewport size (desktop, tablet, mobile), all UI components should render correctly 
 * and maintain functionality across different screen dimensions
 */

import { render, screen, cleanup } from '@testing-library/react'
import * as fc from 'fast-check'
import { Navigation, MobileNavigation } from '@/components/navigation'
import { ResponsiveGrid } from '@/components/ui/responsive-grid'
import { StatCard, PokerStatCard } from '@/components/ui/stat-card'

// Mock Next.js router for navigation components
jest.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
}))

// Viewport size generators
const mobileViewport = fc.record({
  width: fc.integer({ min: 320, max: 767 }),
  height: fc.integer({ min: 568, max: 1024 }),
})

const tabletViewport = fc.record({
  width: fc.integer({ min: 768, max: 1023 }),
  height: fc.integer({ min: 768, max: 1366 }),
})

const desktopViewport = fc.record({
  width: fc.integer({ min: 1024, max: 2560 }),
  height: fc.integer({ min: 768, max: 1440 }),
})

const allViewports = fc.oneof(mobileViewport, tabletViewport, desktopViewport)

// Grid configuration generator
const gridConfig = fc.record({
  cols: fc.record({
    default: fc.integer({ min: 1, max: 4 }),
    sm: fc.option(fc.integer({ min: 1, max: 6 })),
    md: fc.option(fc.integer({ min: 1, max: 8 })),
    lg: fc.option(fc.integer({ min: 1, max: 12 })),
    xl: fc.option(fc.integer({ min: 1, max: 12 })),
  }),
  gap: fc.integer({ min: 1, max: 12 }),
})

// Stat card data generator with unique identifiers
const statCardData = fc.record({
  title: fc.string({ minLength: 5, maxLength: 30 }).map(s => `Card-${s.replace(/[^a-zA-Z0-9]/g, '')}-${Math.random().toString(36).substr(2, 5)}`),
  value: fc.oneof(
    fc.string({ minLength: 3, maxLength: 15 }).filter(s => s.trim().length > 2),
    fc.float({ min: -1000, max: 1000 })
  ),
  subtitle: fc.option(fc.string({ minLength: 5, maxLength: 50 }).map(s => `Sub-${s.replace(/[^a-zA-Z0-9]/g, '')}`)),
  size: fc.constantFrom('sm', 'md', 'lg'),
  variant: fc.constantFrom('default', 'success', 'warning', 'danger'),
})

// Helper function to set viewport size
const setViewportSize = (width: number, height: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  })
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height,
  })
  
  // Update matchMedia to reflect the new viewport
  window.matchMedia = jest.fn().mockImplementation(query => {
    const matches = (() => {
      if (query.includes('(min-width: 1024px)')) return width >= 1024
      if (query.includes('(min-width: 768px)')) return width >= 768
      if (query.includes('(min-width: 640px)')) return width >= 640
      if (query.includes('(max-width: 767px)')) return width <= 767
      if (query.includes('(max-width: 1023px)')) return width <= 1023
      return false
    })()
    
    return {
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }
  })
}

describe('Responsive Design Property Tests', () => {
  beforeEach(() => {
    // Reset viewport to default
    setViewportSize(1024, 768)
    cleanup()
  })

  afterEach(() => {
    cleanup()
  })

  describe('Property 4: Responsive UI Behavior', () => {
    it('should render Navigation component correctly across all viewport sizes', () => {
      fc.assert(
        fc.property(allViewports, (viewport) => {
          setViewportSize(viewport.width, viewport.height)
          
          const { container } = render(<Navigation />)
          
          // Navigation should always be present
          expect(container.querySelector('nav')).toBeInTheDocument()
          
          // Logo elements should be present (check for structure, not specific text)
          const logoContainer = container.querySelector('.flex.items-center.space-x-2')
          expect(logoContainer).toBeInTheDocument()
          
          // Container should have proper responsive classes
          const navContainer = container.querySelector('.container')
          expect(navContainer).toBeInTheDocument()
          
          // Mobile menu button should be present on smaller screens
          const mobileMenuButton = container.querySelector('button')
          if (viewport.width < 768) {
            expect(mobileMenuButton).toBeInTheDocument()
          }
          
          // Desktop navigation should be present on larger screens
          const desktopNav = container.querySelector('.hidden.md\\:flex')
          if (viewport.width >= 768) {
            expect(desktopNav).toBeInTheDocument()
          }
          
          cleanup()
          return true
        }),
        { numRuns: 50 }
      )
    })

    it('should render MobileNavigation component correctly on mobile viewports', () => {
      fc.assert(
        fc.property(mobileViewport, (viewport) => {
          setViewportSize(viewport.width, viewport.height)
          
          const { container } = render(<MobileNavigation />)
          
          // Mobile navigation should be present
          expect(container.querySelector('.md\\:hidden')).toBeInTheDocument()
          
          // Should have fixed positioning for mobile
          expect(container.querySelector('.fixed.bottom-0')).toBeInTheDocument()
          
          // Should have grid layout for navigation items
          expect(container.querySelector('.grid.grid-cols-6')).toBeInTheDocument()
          
          // Should have navigation links
          const navLinks = container.querySelectorAll('a')
          expect(navLinks.length).toBe(6) // 6 navigation items
          
          cleanup()
          return true
        }),
        { numRuns: 30 }
      )
    })

    it('should render ResponsiveGrid with correct column classes across viewports', () => {
      fc.assert(
        fc.property(allViewports, gridConfig, (viewport, config) => {
          setViewportSize(viewport.width, viewport.height)
          
          const { container } = render(
            <ResponsiveGrid cols={config.cols} gap={config.gap}>
              <div>Item 1</div>
              <div>Item 2</div>
              <div>Item 3</div>
            </ResponsiveGrid>
          )
          
          const gridElement = container.firstChild as HTMLElement
          expect(gridElement).toBeInTheDocument()
          
          // Should have base grid class
          expect(gridElement).toHaveClass('grid')
          
          // Should have gap class
          expect(gridElement.className).toMatch(/gap-\d+/)
          
          // Should have default columns
          if (config.cols.default) {
            expect(gridElement.className).toMatch(new RegExp(`grid-cols-${config.cols.default}`))
          }
          
          // Should have responsive column classes when specified
          if (config.cols.sm) {
            expect(gridElement.className).toMatch(new RegExp(`sm:grid-cols-${config.cols.sm}`))
          }
          if (config.cols.md) {
            expect(gridElement.className).toMatch(new RegExp(`md:grid-cols-${config.cols.md}`))
          }
          if (config.cols.lg) {
            expect(gridElement.className).toMatch(new RegExp(`lg:grid-cols-${config.cols.lg}`))
          }
          if (config.cols.xl) {
            expect(gridElement.className).toMatch(new RegExp(`xl:grid-cols-${config.cols.xl}`))
          }
          
          cleanup()
          return true
        }),
        { numRuns: 50 }
      )
    })

    it('should render StatCard component correctly across all viewport sizes', () => {
      fc.assert(
        fc.property(allViewports, statCardData, (viewport, cardData) => {
          setViewportSize(viewport.width, viewport.height)
          
          const { container } = render(
            <StatCard
              title={cardData.title}
              value={cardData.value}
              subtitle={cardData.subtitle || undefined}
              size={cardData.size}
              variant={cardData.variant}
            />
          )
          
          // Card should be present
          const card = container.querySelector('.rounded-lg.border')
          expect(card).toBeInTheDocument()
          
          // Title should be present and readable (use container to avoid multiple matches)
          const titleElement = container.querySelector('.text-sm.font-medium.text-muted-foreground')
          expect(titleElement).toBeInTheDocument()
          expect(titleElement?.textContent).toBe(cardData.title)
          
          // Value should be present and readable
          const valueText = typeof cardData.value === 'number' 
            ? cardData.value.toString() 
            : cardData.value
          const valueElement = container.querySelector('.text-2xl.font-bold')
          expect(valueElement).toBeInTheDocument()
          expect(valueElement?.textContent).toBe(valueText)
          
          // Subtitle should be present if provided
          if (cardData.subtitle) {
            const subtitleElement = container.querySelector('.text-xs.text-muted-foreground')
            expect(subtitleElement).toBeInTheDocument()
            expect(subtitleElement?.textContent).toBe(cardData.subtitle)
          }
          
          // Card should have appropriate size classes
          const cardContent = container.querySelector('[class*="p-"]')
          expect(cardContent).toBeInTheDocument()
          
          cleanup()
          return true
        }),
        { numRuns: 50 }
      )
    })

    it('should render PokerStatCard with proper formatting across viewports', () => {
      fc.assert(
        fc.property(allViewports, (viewport) => {
          setViewportSize(viewport.width, viewport.height)
          
          const statTypes = ['vpip', 'pfr', 'aggression', 'winrate', 'hands', 'profit'] as const
          const statType = statTypes[Math.floor(Math.random() * statTypes.length)]
          const value = Math.random() * 100 - 50 // Random value between -50 and 50
          const uniqueTitle = `Test-${statType.toUpperCase()}-${Math.random().toString(36).substr(2, 9)}`
          
          const { container } = render(
            <PokerStatCard
              title={uniqueTitle}
              value={value}
              statType={statType}
            />
          )
          
          // Card should be present
          const card = container.querySelector('.rounded-lg.border')
          expect(card).toBeInTheDocument()
          
          // Title should be present
          expect(screen.getByText(uniqueTitle)).toBeInTheDocument()
          
          // Value should be formatted and present (check for numeric content)
          const valueElement = container.querySelector('.text-2xl.font-bold')
          expect(valueElement).toBeInTheDocument()
          expect(valueElement?.textContent).toBeTruthy()
          
          // Card should have appropriate variant classes
          const cardElement = container.querySelector('.border-green-200, .border-red-200, .border-yellow-200, .border-border')
          expect(cardElement).toBeInTheDocument()
          
          cleanup()
          return true
        }),
        { numRuns: 50 }
      )
    })

    it('should maintain component functionality across viewport changes', () => {
      fc.assert(
        fc.property(
          fc.array(allViewports, { minLength: 2, maxLength: 3 }),
          (viewports) => {
            // Test component across multiple viewport changes
            const { container, rerender } = render(<Navigation />)
            
            viewports.forEach((viewport, index) => {
              setViewportSize(viewport.width, viewport.height)
              
              // Re-render to trigger responsive behavior
              rerender(<Navigation />)
              
              // Navigation should still be functional
              expect(container.querySelector('nav')).toBeInTheDocument()
              
              // Check for logo container structure
              const logoContainer = container.querySelector('.flex.items-center.space-x-2')
              expect(logoContainer).toBeInTheDocument()
              
              // Component should not crash or lose essential elements
              const links = container.querySelectorAll('a')
              expect(links.length).toBeGreaterThan(0)
            })
            
            cleanup()
            return true
          }
        ),
        { numRuns: 20 }
      )
    })

    it('should handle extreme viewport sizes gracefully', () => {
      const extremeViewports = [
        { width: 320, height: 568 },   // iPhone SE
        { width: 2560, height: 1440 }, // Large desktop
        { width: 768, height: 1024 },  // iPad portrait
        { width: 1024, height: 768 },  // iPad landscape
      ]
      
      extremeViewports.forEach((viewport, index) => {
        setViewportSize(viewport.width, viewport.height)
        
        const uniqueId = `test-${index}`
        const { container } = render(
          <div data-testid={uniqueId}>
            <Navigation />
            <ResponsiveGrid cols={{ default: 1, md: 2, lg: 3 }}>
              <StatCard title={`Test-Card-1-${uniqueId}`} value="100" />
              <StatCard title={`Test-Card-2-${uniqueId}`} value="200" />
              <StatCard title={`Test-Card-3-${uniqueId}`} value="300" />
            </ResponsiveGrid>
          </div>
        )
        
        // Components should render without errors
        expect(container.querySelector('nav')).toBeInTheDocument()
        expect(container.querySelector('.grid')).toBeInTheDocument()
        
        // Cards should be present
        const cards = container.querySelectorAll('.rounded-lg.border')
        expect(cards.length).toBeGreaterThanOrEqual(3)
        
        cleanup()
      })
    })
  })
})