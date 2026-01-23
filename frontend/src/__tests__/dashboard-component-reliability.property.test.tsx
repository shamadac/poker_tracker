/**
 * Property-Based Test for Dashboard Component Reliability
 * Feature: poker-app-fixes-and-cleanup, Property 3: Dashboard Component Reliability
 * 
 * **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
 * 
 * Property 3: Dashboard Component Reliability
 * For any dashboard loading scenario, all statistical widgets should render successfully 
 * with reasonable performance, display partial data with clear error indicators when 
 * individual components fail, show appropriate loading states during data fetching, 
 * and maintain user view state during refresh operations.
 */

import React from 'react'
import { render, screen, cleanup, waitFor, act, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import * as fc from 'fast-check'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardWidget } from '@/components/dashboard/dashboard-widget'

// Increase timeout for property-based tests
jest.setTimeout(30000)

// Mock localStorage and sessionStorage
const mockStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: mockStorage,
  writable: true
})

Object.defineProperty(window, 'sessionStorage', {
  value: mockStorage,
  writable: true
})

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0
      }
    }
  })

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// Simple generators for property-based testing
const widgetIdGenerator = fc.integer({ min: 1, max: 100000 }).map(n => `widget-${n}`)
const widgetTitleGenerator = fc.integer({ min: 1, max: 100000 }).map(n => `Widget ${n}`)
const priorityGenerator = fc.constantFrom('high', 'medium', 'low')
const errorMessageGenerator = fc.constantFrom('Network Error', 'Timeout Error', 'Server Error', 'Database Error')

describe('Dashboard Component Reliability Property Tests', () => {
  beforeEach(() => {
    cleanup()
    jest.clearAllMocks()
    jest.clearAllTimers()
    jest.useFakeTimers()
    
    // Reset mocks
    mockStorage.getItem.mockReturnValue(null)
    mockStorage.setItem.mockClear()
  })

  afterEach(() => {
    cleanup()
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  describe('Property 3: Dashboard Component Reliability', () => {
    
    it('should render statistical widgets successfully with reasonable performance', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.record({
              id: widgetIdGenerator,
              title: widgetTitleGenerator,
              priority: priorityGenerator
            }),
            { minLength: 1, maxLength: 5 }
          ),
          (widgets) => {
            const startTime = performance.now()
            
            render(
              <TestWrapper>
                <div data-testid="dashboard-container">
                  {widgets.map((widget, index) => (
                    <DashboardWidget
                      key={widget.id}
                      id={widget.id}
                      title={widget.title}
                      priority={widget.priority}
                      loading={false}
                    >
                      <div data-testid={`content-${index}`}>
                        Widget content {index}
                      </div>
                    </DashboardWidget>
                  ))}
                </div>
              </TestWrapper>
            )
            
            const renderTime = performance.now() - startTime
            
            // Property: Dashboard container should render
            expect(screen.getByTestId('dashboard-container')).toBeInTheDocument()
            
            // Property: All widgets should render
            widgets.forEach((widget, index) => {
              expect(screen.getByText(widget.title)).toBeInTheDocument()
              expect(screen.getByTestId(`content-${index}`)).toBeInTheDocument()
            })
            
            // Property: Performance should be reasonable (under 200ms for up to 5 widgets)
            expect(renderTime).toBeLessThan(200)
            
            // Property: No error indicators should be present
            expect(screen.queryByText(/failed to load/i)).not.toBeInTheDocument()
          }
        ),
        { numRuns: 20 }
      )
    })

    it('should display error indicators when components fail', () => {
      fc.assert(
        fc.property(
          widgetIdGenerator,
          widgetTitleGenerator,
          errorMessageGenerator,
          fc.boolean(), // hasCachedData
          (id, title, errorMessage, hasCachedData) => {
            const mockRetry = jest.fn()
            const error = new Error(errorMessage)
            const fallbackData = hasCachedData ? { test: 'cached' } : undefined
            
            render(
              <TestWrapper>
                <DashboardWidget
                  id={id}
                  title={title}
                  error={error}
                  onRetry={mockRetry}
                  fallbackData={fallbackData}
                >
                  <div data-testid="widget-content">
                    Normal content
                  </div>
                </DashboardWidget>
              </TestWrapper>
            )
            
            // Property: Widget title should always be visible
            expect(screen.getByText(title)).toBeInTheDocument()
            
            // Property: Error state should be indicated
            expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
            
            // Property: Retry option should be available
            const retryButton = screen.getByText(/try again/i)
            expect(retryButton).toBeInTheDocument()
            
            // Property: Retry should be functional
            fireEvent.click(retryButton)
            expect(mockRetry).toHaveBeenCalledTimes(1)
            
            // Property: Cached data should be indicated when available
            if (hasCachedData) {
              expect(screen.getByText(/cached data|last known values/i)).toBeInTheDocument()
            }
            
            // Property: Normal content should not be visible in error state
            expect(screen.queryByTestId('widget-content')).not.toBeInTheDocument()
          }
        ),
        { numRuns: 15 }
      )
    })

    it('should show loading states during data fetching', () => {
      fc.assert(
        fc.property(
          widgetIdGenerator,
          widgetTitleGenerator,
          fc.boolean(), // isLoading
          fc.integer({ min: 1, max: 5 }), // skeletonRows
          (id, title, isLoading, skeletonRows) => {
            render(
              <TestWrapper>
                <DashboardWidget
                  id={id}
                  title={title}
                  loading={isLoading}
                  skeletonRows={skeletonRows}
                >
                  <div data-testid="widget-content">
                    Actual content
                  </div>
                </DashboardWidget>
              </TestWrapper>
            )
            
            // Property: Widget title should always be visible
            expect(screen.getByText(title)).toBeInTheDocument()
            
            if (isLoading) {
              // Property: Loading skeleton should be visible
              const skeletons = document.querySelectorAll('.animate-pulse')
              expect(skeletons.length).toBeGreaterThan(0)
              
              // Property: Actual content should not be visible when loading
              expect(screen.queryByTestId('widget-content')).not.toBeInTheDocument()
            } else {
              // Property: Actual content should be visible when not loading
              expect(screen.getByTestId('widget-content')).toBeInTheDocument()
            }
          }
        ),
        { numRuns: 15 }
      )
    })

    it('should provide error recovery with automatic retry', () => {
      fc.assert(
        fc.property(
          widgetIdGenerator,
          widgetTitleGenerator,
          errorMessageGenerator,
          fc.boolean(), // autoRetry
          fc.integer({ min: 1, max: 3 }), // maxRetries
          fc.integer({ min: 100, max: 500 }), // retryDelay
          (id, title, errorMessage, autoRetry, maxRetries, retryDelay) => {
            const mockRetry = jest.fn()
            const error = new Error(errorMessage)
            
            render(
              <TestWrapper>
                <DashboardWidget
                  id={id}
                  title={title}
                  error={error}
                  onRetry={mockRetry}
                  autoRetry={autoRetry}
                  maxRetries={maxRetries}
                  retryDelay={retryDelay}
                >
                  <div data-testid="widget-content">
                    Content
                  </div>
                </DashboardWidget>
              </TestWrapper>
            )
            
            // Property: Error recovery options should be available
            expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
            expect(screen.getByText(/try again/i)).toBeInTheDocument()
            
            // Property: Auto-retry should work when enabled
            if (autoRetry) {
              act(() => {
                jest.advanceTimersByTime(retryDelay + 50)
              })
              
              expect(mockRetry).toHaveBeenCalled()
            }
            
            // Property: Manual retry should always work
            const retryButton = screen.getByText(/try again/i)
            fireEvent.click(retryButton)
            expect(mockRetry).toHaveBeenCalled()
          }
        ),
        { numRuns: 10 }
      )
    })

    it('should handle widget state transitions correctly', () => {
      fc.assert(
        fc.property(
          widgetIdGenerator,
          widgetTitleGenerator,
          fc.record({
            initialLoading: fc.boolean(),
            hasError: fc.boolean(),
            errorMessage: fc.option(errorMessageGenerator),
            finalLoading: fc.boolean()
          }),
          (id, title, states) => {
            const mockRetry = jest.fn()
            
            // Initial render
            const { rerender } = render(
              <TestWrapper>
                <DashboardWidget
                  id={id}
                  title={title}
                  loading={states.initialLoading}
                  onRetry={mockRetry}
                >
                  <div data-testid="widget-content">
                    Content
                  </div>
                </DashboardWidget>
              </TestWrapper>
            )
            
            // Property: Title should always be visible
            expect(screen.getByText(title)).toBeInTheDocument()
            
            // Transition to error state if applicable
            if (states.hasError && states.errorMessage) {
              const error = new Error(states.errorMessage)
              rerender(
                <TestWrapper>
                  <DashboardWidget
                    id={id}
                    title={title}
                    error={error}
                    onRetry={mockRetry}
                  >
                    <div data-testid="widget-content">
                      Content
                    </div>
                  </DashboardWidget>
                </TestWrapper>
              )
              
              // Property: Error state should be handled
              expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
            }
            
            // Transition to final loading state
            rerender(
              <TestWrapper>
                <DashboardWidget
                  id={id}
                  title={title}
                  loading={states.finalLoading}
                  onRetry={mockRetry}
                >
                  <div data-testid="widget-content">
                    Content
                  </div>
                </DashboardWidget>
              </TestWrapper>
            )
            
            // Property: Final state should be correct
            if (states.finalLoading) {
              const skeletons = document.querySelectorAll('.animate-pulse')
              expect(skeletons.length).toBeGreaterThan(0)
            } else {
              expect(screen.getByTestId('widget-content')).toBeInTheDocument()
            }
          }
        ),
        { numRuns: 10 }
      )
    })

    it('should maintain consistent behavior across multiple widgets', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.record({
              id: widgetIdGenerator,
              title: widgetTitleGenerator,
              loading: fc.boolean(),
              hasError: fc.boolean(),
              priority: priorityGenerator
            }),
            { minLength: 2, maxLength: 4 }
          ),
          (widgets) => {
            const mockRetries = widgets.map(() => jest.fn())
            
            render(
              <TestWrapper>
                <div data-testid="multi-widget-container">
                  {widgets.map((widget, index) => (
                    <DashboardWidget
                      key={widget.id}
                      id={widget.id}
                      title={widget.title}
                      loading={widget.loading}
                      error={widget.hasError ? new Error('Test error') : null}
                      onRetry={mockRetries[index]}
                      priority={widget.priority}
                    >
                      <div data-testid={`content-${index}`}>
                        Content {index}
                      </div>
                    </DashboardWidget>
                  ))}
                </div>
              </TestWrapper>
            )
            
            // Property: Container should render
            expect(screen.getByTestId('multi-widget-container')).toBeInTheDocument()
            
            // Property: All widget titles should be visible
            widgets.forEach(widget => {
              expect(screen.getByText(widget.title)).toBeInTheDocument()
            })
            
            // Property: Widget states should be independent
            widgets.forEach((widget, index) => {
              if (widget.loading) {
                // Loading widgets should show skeleton
                expect(screen.queryByTestId(`content-${index}`)).not.toBeInTheDocument()
              } else if (widget.hasError) {
                // Error widgets should show error state
                expect(screen.queryByTestId(`content-${index}`)).not.toBeInTheDocument()
              } else {
                // Normal widgets should show content
                expect(screen.getByTestId(`content-${index}`)).toBeInTheDocument()
              }
            })
            
            // Property: Error widgets should have retry functionality
            const errorWidgets = widgets.filter(w => w.hasError)
            if (errorWidgets.length > 0) {
              const retryButtons = screen.getAllByText(/try again/i)
              expect(retryButtons.length).toBe(errorWidgets.length)
            }
          }
        ),
        { numRuns: 8 }
      )
    })
  })
})