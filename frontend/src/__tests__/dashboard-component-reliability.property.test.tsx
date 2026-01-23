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
const widgetIdGenerator = fc.integer({ min: 1, max: 100000 }).map(n => `widget-${n}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`)
const widgetTitleGenerator = fc.integer({ min: 1, max: 100000 }).map(n => `Widget ${n}`)
const priorityGenerator = fc.constantFrom('high', 'medium', 'low')
const errorMessageGenerator = fc.constantFrom('Network Error', 'Timeout Error', 'Server Error', 'Database Error')

describe('Dashboard Component Reliability Property Tests', () => {
  beforeEach(() => {
    // Force cleanup of any existing DOM elements
    document.body.innerHTML = ''
    cleanup()
    jest.clearAllMocks()
    jest.clearAllTimers()
    jest.useFakeTimers()
    
    // Reset mocks
    mockStorage.getItem.mockReturnValue(null)
    mockStorage.setItem.mockClear()
  })

  afterEach(() => {
    // Ensure complete cleanup after each test
    cleanup()
    document.body.innerHTML = ''
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
            // Ensure clean DOM state
            cleanup()
            
            const containerId = `dashboard-container-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
            const startTime = performance.now()
            
            const { unmount } = render(
              <TestWrapper>
                <div data-testid={containerId}>
                  {widgets.map((widget, index) => (
                    <DashboardWidget
                      key={widget.id}
                      id={widget.id}
                      title={widget.title}
                      priority={widget.priority}
                      loading={false}
                    >
                      <div data-testid={`content-${widget.id}-${index}`}>
                        Widget content {index}
                      </div>
                    </DashboardWidget>
                  ))}
                </div>
              </TestWrapper>
            )
            
            try {
              const renderTime = performance.now() - startTime
              
              // Property: Dashboard container should render
              expect(screen.getByTestId(containerId)).toBeInTheDocument()
              
              // Property: All widgets should render
              widgets.forEach((widget, index) => {
                expect(screen.getByText(widget.title)).toBeInTheDocument()
                expect(screen.getByTestId(`content-${widget.id}-${index}`)).toBeInTheDocument()
              })
              
              // Property: Performance should be reasonable (under 200ms for up to 5 widgets)
              expect(renderTime).toBeLessThan(200)
              
              // Property: No error indicators should be present
              expect(screen.queryByText(/failed to load/i)).not.toBeInTheDocument()
            } finally {
              unmount()
              cleanup()
            }
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
            // Ensure clean DOM state
            cleanup()
            
            const mockRetry = jest.fn()
            const error = new Error(errorMessage)
            const fallbackData = hasCachedData ? { test: 'cached' } : undefined
            
            const { unmount } = render(
              <TestWrapper>
                <DashboardWidget
                  id={id}
                  title={title}
                  error={error}
                  onRetry={mockRetry}
                  fallbackData={fallbackData}
                  autoRetry={false} // Disable auto-retry for predictable testing
                >
                  <div data-testid={`widget-content-${id}`}>
                    Normal content
                  </div>
                </DashboardWidget>
              </TestWrapper>
            )
            
            try {
              // Property: Widget title should always be visible
              expect(screen.getByText(title)).toBeInTheDocument()
              
              if (hasCachedData) {
                // Wait for component to settle and check if it's in retrying state
                const isRetrying = screen.queryByText(/retrying/i)
                
                if (isRetrying) {
                  // Component is in retrying state, should show loading skeleton
                  const skeletons = document.querySelectorAll('.animate-pulse')
                  expect(skeletons.length).toBeGreaterThan(0)
                  
                  // Should not show normal content during retry
                  expect(screen.queryByTestId(`widget-content-${id}`)).not.toBeInTheDocument()
                } else {
                  // Property: Cached data should be indicated when available and not retrying
                  const cachedDataElements = screen.getAllByText(/cached data|showing cached data/i)
                  expect(cachedDataElements.length).toBeGreaterThan(0)
                  
                  // Property: Normal content should be visible but dimmed in fallback state
                  expect(screen.getByTestId(`widget-content-${id}`)).toBeInTheDocument()
                }
                
                // Property: Retry option should be available (if not currently retrying)
                if (!isRetrying) {
                  const retryButtons = screen.getAllByText(/retry/i)
                  const clickableRetryButton = retryButtons.find(button => 
                    button.tagName === 'BUTTON' || button.closest('button')
                  )
                  expect(clickableRetryButton).toBeInTheDocument()
                  
                  // Property: Retry should be functional
                  fireEvent.click(clickableRetryButton!)
                  expect(mockRetry).toHaveBeenCalledTimes(1)
                }
              } else {
                // Property: Error state should be indicated
                expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
                
                // Property: Retry option should be available
                const retryButton = screen.getByText(/try again/i)
                expect(retryButton).toBeInTheDocument()
                
                // Property: Retry should be functional
                fireEvent.click(retryButton)
                expect(mockRetry).toHaveBeenCalledTimes(1)
                
                // Property: Normal content should not be visible in error state
                expect(screen.queryByTestId(`widget-content-${id}`)).not.toBeInTheDocument()
              }
            } finally {
              unmount()
              cleanup()
            }
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
            // Ensure clean DOM state
            cleanup()
            
            const { unmount } = render(
              <TestWrapper>
                <DashboardWidget
                  id={id}
                  title={title}
                  loading={isLoading}
                  skeletonRows={skeletonRows}
                >
                  <div data-testid={`widget-content-${id}`}>
                    Actual content
                  </div>
                </DashboardWidget>
              </TestWrapper>
            )
            
            try {
              // Property: Widget title should always be visible
              expect(screen.getByText(title)).toBeInTheDocument()
              
              if (isLoading) {
                // Property: Loading skeleton should be visible
                const skeletons = document.querySelectorAll('.animate-pulse')
                expect(skeletons.length).toBeGreaterThan(0)
                
                // Property: Actual content should not be visible when loading
                expect(screen.queryByTestId(`widget-content-${id}`)).not.toBeInTheDocument()
              } else {
                // Property: Actual content should be visible when not loading
                expect(screen.getByTestId(`widget-content-${id}`)).toBeInTheDocument()
              }
            } finally {
              unmount()
              cleanup()
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
            // Ensure clean DOM state
            cleanup()
            
            const mockRetry = jest.fn()
            const error = new Error(errorMessage)
            
            const { unmount } = render(
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
                  <div data-testid={`widget-content-${id}`}>
                    Content
                  </div>
                </DashboardWidget>
              </TestWrapper>
            )
            
            try {
              // Property: Widget title should always be visible
              expect(screen.getByText(title)).toBeInTheDocument()
              
              // Wait for component to settle
              act(() => {
                jest.advanceTimersByTime(100)
              })
              
              // Property: Auto-retry should work when enabled
              if (autoRetry) {
                act(() => {
                  jest.advanceTimersByTime(retryDelay + 50)
                })
                
                expect(mockRetry).toHaveBeenCalled()
              } else {
                // Property: Error recovery options should be available when auto-retry is disabled
                expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
                
                // Property: Manual retry should always work
                const retryButton = screen.getByText(/try again/i)
                expect(retryButton).toBeInTheDocument()
                fireEvent.click(retryButton)
                expect(mockRetry).toHaveBeenCalled()
              }
            } finally {
              unmount()
              cleanup()
            }
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
            
            // Ensure clean DOM state
            cleanup()
            
            // Initial render
            const { rerender, unmount } = render(
              <TestWrapper>
                <DashboardWidget
                  id={id}
                  title={title}
                  loading={states.initialLoading}
                  onRetry={mockRetry}
                >
                  <div data-testid={`widget-content-${id}`}>
                    Content
                  </div>
                </DashboardWidget>
              </TestWrapper>
            )
            
            try {
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
                      <div data-testid={`widget-content-${id}`}>
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
                    <div data-testid={`widget-content-${id}`}>
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
                expect(screen.getByTestId(`widget-content-${id}`)).toBeInTheDocument()
              }
            } finally {
              unmount()
              cleanup()
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
            // Generate unique container ID for this property test iteration
            const containerId = `multi-widget-container-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
            const mockRetries = widgets.map(() => jest.fn())
            
            // Ensure clean DOM state before rendering
            cleanup()
            
            const { unmount } = render(
              <TestWrapper>
                <div data-testid={containerId}>
                  {widgets.map((widget, index) => (
                    <DashboardWidget
                      key={widget.id}
                      id={widget.id}
                      title={widget.title}
                      loading={widget.loading}
                      error={widget.hasError ? new Error('Test error') : null}
                      onRetry={mockRetries[index]}
                      priority={widget.priority}
                      autoRetry={false} // Disable auto-retry for predictable testing
                    >
                      <div data-testid={`content-${widget.id}-${index}`}>
                        Content {index}
                      </div>
                    </DashboardWidget>
                  ))}
                </div>
              </TestWrapper>
            )
            
            try {
              // Property: Container should render
              expect(screen.getByTestId(containerId)).toBeInTheDocument()
              
              // Property: All widget titles should be visible (use getAllByText for duplicates)
              widgets.forEach(widget => {
                const titleElements = screen.getAllByText(widget.title)
                expect(titleElements.length).toBeGreaterThan(0)
              })
              
              // Property: Widget states should be independent
              widgets.forEach((widget, index) => {
                const contentTestId = `content-${widget.id}-${index}`
                
                // When both loading and error are true, loading takes precedence
                if (widget.loading) {
                  // Loading widgets should show skeleton (regardless of error state)
                  expect(screen.queryByTestId(contentTestId)).not.toBeInTheDocument()
                  // Should have loading skeleton
                  const skeletons = document.querySelectorAll('.animate-pulse')
                  expect(skeletons.length).toBeGreaterThan(0)
                } else if (widget.hasError) {
                  // Error widgets (when not loading) should show error state
                  expect(screen.queryByTestId(contentTestId)).not.toBeInTheDocument()
                } else {
                  // Normal widgets should show content
                  expect(screen.getByTestId(contentTestId)).toBeInTheDocument()
                }
              })
              
              // Property: Error widgets should have retry functionality (only when not loading)
              const errorWidgetsNotLoading = widgets.filter(w => w.hasError && !w.loading)
              if (errorWidgetsNotLoading.length > 0) {
                // Should have error messages (use getAllByText for multiple)
                const errorMessages = screen.getAllByText(/failed to load/i)
                expect(errorMessages.length).toBe(errorWidgetsNotLoading.length)
                
                const retryButtons = screen.getAllByText(/try again/i)
                expect(retryButtons.length).toBe(errorWidgetsNotLoading.length)
              }
            } finally {
              // Ensure cleanup after each property test iteration
              unmount()
              cleanup()
            }
          }
        ),
        { numRuns: 8 }
      )
    })
  })
})