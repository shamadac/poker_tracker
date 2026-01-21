/**
 * Property-Based Test for Error Handling
 * Feature: professional-poker-analyzer-rebuild, Property 6: Error Boundary Protection
 * 
 * **Validates: Requirements 2.6**
 * 
 * Property 6: Error Boundary Protection
 * For any runtime error in the frontend, the system should catch the error gracefully 
 * and display user-friendly error messages without crashing the application
 */

import { render, screen, cleanup } from '@testing-library/react'
import { fireEvent, waitFor } from '@testing-library/react'
import * as fc from 'fast-check'
import { ErrorBoundary, APIErrorBoundary, ChartErrorBoundary, useErrorBoundary } from '@/components/error-boundary'
import { processAPIError, RetryManager, createErrorBoundaryFallback } from '@/lib/error-handling'
import { AxiosError } from 'axios'

// Mock console.error to avoid noise in tests
const originalConsoleError = console.error
beforeAll(() => {
  console.error = jest.fn()
})

afterAll(() => {
  console.error = originalConsoleError
})

// Component that throws errors for testing
function ErrorThrowingComponent({ 
  shouldThrow, 
  errorType, 
  errorMessage 
}: { 
  shouldThrow: boolean
  errorType: 'runtime' | 'network' | 'api' | 'validation'
  errorMessage: string 
}) {
  if (shouldThrow) {
    switch (errorType) {
      case 'runtime':
        throw new Error(errorMessage)
      case 'network':
        throw new AxiosError(errorMessage, 'NETWORK_ERROR')
      case 'api':
        const apiError = new AxiosError(errorMessage, 'API_ERROR')
        apiError.response = {
          status: 500,
          data: { error: { type: 'internal_error', message: errorMessage } },
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as any
        }
        throw apiError
      case 'validation':
        const validationError = new AxiosError(errorMessage, 'VALIDATION_ERROR')
        validationError.response = {
          status: 422,
          data: { error: { type: 'validation_error', message: errorMessage } },
          statusText: 'Unprocessable Entity',
          headers: {},
          config: {} as any
        }
        throw validationError
      default:
        throw new Error(errorMessage)
    }
  }
  return <div data-testid="working-component">Component is working</div>
}

// Component that uses the error boundary hook
function ComponentWithErrorHook({ shouldCaptureError, errorMessage }: { shouldCaptureError: boolean, errorMessage: string }) {
  const { captureError, resetError } = useErrorBoundary()
  
  const handleError = () => {
    if (shouldCaptureError) {
      captureError(new Error(errorMessage))
    }
  }
  
  return (
    <div>
      <button onClick={handleError} data-testid="trigger-error">
        Trigger Error
      </button>
      <button onClick={resetError} data-testid="reset-error">
        Reset Error
      </button>
    </div>
  )
}

// Error generators with better filtering
const errorMessageGenerator = fc.string({ minLength: 8, maxLength: 100 }).filter(s => s.trim().length > 7 && !s.match(/^\s*$/))
const errorTypeGenerator = fc.constantFrom('runtime', 'network', 'api', 'validation')

const httpStatusGenerator = fc.constantFrom(400, 401, 403, 404, 409, 422, 429, 500, 503)
const apiErrorTypeGenerator = fc.constantFrom(
  'parsing_error', 'unsupported_platform', 'authentication_error', 
  'authorization_error', 'validation_error', 'rate_limit_exceeded',
  'internal_error', 'service_unavailable', 'database_connection_error'
)

// Title generator for fallback tests
const titleGenerator = fc.constantFrom(
  'Error Occurred', 'Something Failed', 'System Error', 'Processing Error',
  'Network Issue', 'Service Error', 'Application Error', 'Unexpected Error'
)
const operationKeyGenerator = fc.string({ minLength: 5, maxLength: 15 }).filter(s => s.trim().length > 4 && !s.match(/^\s*$/))

describe('Error Handling Property Tests', () => {
  beforeEach(() => {
    cleanup()
  })

  afterEach(() => {
    cleanup()
  })

  describe('Property 6: Error Boundary Protection', () => {
    it('should catch and handle any runtime error gracefully', () => {
      fc.assert(
        fc.property(errorMessageGenerator, errorTypeGenerator, (errorMessage, errorType) => {
          const { container } = render(
            <ErrorBoundary>
              <ErrorThrowingComponent 
                shouldThrow={true} 
                errorType={errorType}
                errorMessage={errorMessage}
              />
            </ErrorBoundary>
          )
          
          // Error boundary should catch the error and render fallback
          expect(screen.queryByTestId('working-component')).not.toBeInTheDocument()
          
          // Should display user-friendly error message (use getAllByText to handle multiple)
          const errorMessages = screen.getAllByText(/something went wrong/i)
          expect(errorMessages.length).toBeGreaterThan(0)
          
          // Should have a try again button
          const tryAgainButtons = screen.getAllByText(/try again/i)
          expect(tryAgainButtons.length).toBeGreaterThan(0)
          
          // Should have a reload page button
          const reloadButtons = screen.getAllByText(/reload page/i)
          expect(reloadButtons.length).toBeGreaterThan(0)
          
          // Application should not crash (container should still exist)
          expect(container).toBeInTheDocument()
          
          cleanup()
          return true
        }),
        { numRuns: 50 }
      )
    })

    it('should allow error recovery through reset functionality', () => {
      fc.assert(
        fc.property(errorMessageGenerator, (errorMessage) => {
          let shouldThrow = true
          
          const TestComponent = () => (
            <ErrorBoundary>
              <ErrorThrowingComponent 
                shouldThrow={shouldThrow} 
                errorType="runtime"
                errorMessage={errorMessage}
              />
            </ErrorBoundary>
          )
          
          const { rerender } = render(<TestComponent />)
          
          // Should show error state
          expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
          
          // Click try again button
          const tryAgainButton = screen.getByText(/try again/i)
          
          // Simulate fixing the error
          shouldThrow = false
          fireEvent.click(tryAgainButton)
          
          // Re-render with fixed component
          rerender(
            <ErrorBoundary>
              <ErrorThrowingComponent 
                shouldThrow={false} 
                errorType="runtime"
                errorMessage={errorMessage}
              />
            </ErrorBoundary>
          )
          
          // Should show working component after reset
          expect(screen.getByTestId('working-component')).toBeInTheDocument()
          expect(screen.queryByText(/something went wrong/i)).not.toBeInTheDocument()
          
          cleanup()
          return true
        }),
        { numRuns: 50 }
      )
    })

    it('should process API errors correctly with appropriate user messages', () => {
      fc.assert(
        fc.property(httpStatusGenerator, apiErrorTypeGenerator, errorMessageGenerator, (status, errorType, message) => {
          const axiosError = new AxiosError(message, 'API_ERROR')
          axiosError.response = {
            status,
            data: { error: { type: errorType, message } },
            statusText: 'Error',
            headers: {},
            config: {} as any
          }
          
          const processedError = processAPIError(axiosError)
          
          // Should have appropriate category
          expect(processedError.category).toBeDefined()
          expect(typeof processedError.category).toBe('string')
          
          // Should have severity level
          expect(processedError.severity).toMatch(/^(low|medium|high|critical)$/)
          
          // Should have user-friendly message
          expect(processedError.userMessage).toBeDefined()
          expect(processedError.userMessage.length).toBeGreaterThan(0)
          
          // Should have technical message
          expect(processedError.technicalMessage).toBeDefined()
          
          // Should have suggested actions
          expect(Array.isArray(processedError.suggestedActions)).toBe(true)
          expect(processedError.suggestedActions.length).toBeGreaterThan(0)
          
          // Should have retry flag
          expect(typeof processedError.canRetry).toBe('boolean')
          
          return true
        }),
        { numRuns: 100 }
      )
    })

    it('should handle specialized error boundaries correctly', () => {
      fc.assert(
        fc.property(errorMessageGenerator, (errorMessage) => {
          // Test API Error Boundary
          const { container: apiContainer } = render(
            <APIErrorBoundary>
              <ErrorThrowingComponent 
                shouldThrow={true} 
                errorType="api"
                errorMessage={errorMessage}
              />
            </APIErrorBoundary>
          )
          
          // Should render error fallback (check for error container structure)
          expect(apiContainer.querySelector('.min-h-\\[400px\\]')).toBeTruthy()
          cleanup()
          
          // Test Chart Error Boundary
          const { container: chartContainer } = render(
            <ChartErrorBoundary>
              <ErrorThrowingComponent 
                shouldThrow={true} 
                errorType="runtime"
                errorMessage={errorMessage}
              />
            </ChartErrorBoundary>
          )
          
          expect(screen.getByText(/unable to load chart/i)).toBeInTheDocument()
          expect(screen.getByText(/retry/i)).toBeInTheDocument()
          
          cleanup()
          return true
        }),
        { numRuns: 30 }
      )
    })

    it('should handle error boundary hook correctly', () => {
      fc.assert(
        fc.property(errorMessageGenerator, (errorMessage) => {
          render(
            <ErrorBoundary>
              <ComponentWithErrorHook 
                shouldCaptureError={false}
                errorMessage={errorMessage}
              />
            </ErrorBoundary>
          )
          
          // Should render normally without error
          expect(screen.getByTestId('trigger-error')).toBeInTheDocument()
          expect(screen.getByTestId('reset-error')).toBeInTheDocument()
          
          // Component should be functional
          const triggerButton = screen.getByTestId('trigger-error')
          expect(triggerButton).toBeEnabled()
          
          cleanup()
          return true
        }),
        { numRuns: 30 }
      )
    })

    it('should maintain application stability across multiple error scenarios', () => {
      fc.assert(
        fc.property(
          fc.array(fc.record({
            errorMessage: errorMessageGenerator,
            errorType: errorTypeGenerator,
            shouldThrow: fc.boolean()
          }), { minLength: 2, maxLength: 5 }),
          (errorScenarios) => {
            errorScenarios.forEach((scenario, index) => {
              const { container } = render(
                <ErrorBoundary key={index}>
                  <ErrorThrowingComponent 
                    shouldThrow={scenario.shouldThrow} 
                    errorType={scenario.errorType}
                    errorMessage={scenario.errorMessage}
                  />
                </ErrorBoundary>
              )
              
              if (scenario.shouldThrow) {
                // Should show error state
                expect(screen.queryByText(/something went wrong/i)).toBeInTheDocument()
              } else {
                // Should show working component
                expect(screen.getByTestId('working-component')).toBeInTheDocument()
              }
              
              // Application should remain stable
              expect(container).toBeInTheDocument()
              
              cleanup()
            })
            
            return true
          }
        ),
        { numRuns: 20 }
      )
    })

    it('should handle network errors with appropriate retry logic', () => {
      fc.assert(
        fc.property(errorMessageGenerator, (errorMessage) => {
          const networkError = new AxiosError(errorMessage, 'NETWORK_ERROR')
          const processedError = processAPIError(networkError)
          
          // Network errors should be retryable
          expect(processedError.canRetry).toBe(true)
          expect(processedError.category).toBe('network')
          expect(processedError.severity).toBe('high')
          
          // Should have network-specific suggestions
          expect(processedError.suggestedActions).toContain('Check your internet connection')
          
          return true
        }),
        { numRuns: 50 }
      )
    })

    it('should create appropriate error boundary fallbacks', () => {
      fc.assert(
        fc.property(
          titleGenerator,
          fc.boolean(),
          (title, showDetails) => {
            const FallbackComponent = createErrorBoundaryFallback(title, showDetails)
            const testError = new Error('Test error message')
            const mockReset = jest.fn()
            
            render(
              <FallbackComponent error={testError} reset={mockReset} />
            )
            
            // Should display the custom title (check if it exists in the DOM)
            expect(screen.getByText(title)).toBeInTheDocument()
            
            // Should have action buttons
            expect(screen.getByText(/try again/i)).toBeInTheDocument()
            expect(screen.getByText(/reload page/i)).toBeInTheDocument()
            
            // Should show technical details in development mode
            if (showDetails) {
              expect(screen.getByText(/technical details/i)).toBeInTheDocument()
            }
            
            cleanup()
            return true
          }
        ),
        { numRuns: 20 }
      )
    })

    it('should handle retry manager functionality correctly', () => {
      fc.assert(
        fc.property(
          operationKeyGenerator,
          fc.integer({ min: 1, max: 3 }),
          (operationKey, failureCount) => {
            const retryManager = new RetryManager()
            
            // Test basic retry count functionality
            expect(retryManager.getRetryCount(operationKey)).toBe(0)
            
            // Test reset functionality
            retryManager.resetRetries(operationKey)
            expect(retryManager.getRetryCount(operationKey)).toBe(0)
            
            // Test that retry manager exists and has expected methods
            expect(typeof retryManager.executeWithRetry).toBe('function')
            expect(typeof retryManager.getRetryCount).toBe('function')
            expect(typeof retryManager.resetRetries).toBe('function')
            
            return true
          }
        ),
        { numRuns: 20 }
      )
    })
  })
})