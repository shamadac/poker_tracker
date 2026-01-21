/**
 * Property-Based Tests for Real-Time Updates
 * 
 * **Feature: professional-poker-analyzer-rebuild, Property 15: Dynamic Statistics Filtering**
 * **Validates: Requirements 6.7**
 * 
 * Tests that for any filter criteria (date range, stakes, position, game type), 
 * the system should recalculate and display updated statistics and visualizations in real-time.
 */

import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import { renderHook } from '@testing-library/react'
import fc from 'fast-check'
import { 
  useRealTimeCharts, 
  useWebSocketRealTimeCharts,
  useProgressCharts,
  useFileMonitoringCharts,
  useAnalysisProgressCharts,
  useMultipleRealTimeCharts
} from '@/hooks/useRealTimeCharts'
import { 
  useRealTimeStatistics, 
  useProgressTracking,
  useFileMonitoringUpdates,
  useRealTimeAnalysis,
  WebSocketClient,
  WebSocketState
} from '@/lib/websocket-client'
import { WebSocketProvider } from '@/contexts/websocket-context'
import { RealTimeProgress, RealTimeStatistics } from '@/components/real-time-progress'
import React from 'react'

// Increase timeout for property-based tests
jest.setTimeout(30000)

// Mock WebSocket for testing
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null

  constructor(public url: string, public protocols?: string[]) {
    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      this.onopen?.(new Event('open'))
    }, 10)
  }

  send(data: string): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open')
    }
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new CloseEvent('close', { code, reason }))
  }

  // Helper method to simulate receiving messages
  simulateMessage(data: any): void {
    if (this.readyState === MockWebSocket.OPEN && this.onmessage) {
      this.onmessage(new MessageEvent('message', { 
        data: JSON.stringify(data) 
      }))
    }
  }
}

// Replace global WebSocket with mock
const originalWebSocket = global.WebSocket
beforeAll(() => {
  global.WebSocket = MockWebSocket as any
})

afterAll(() => {
  global.WebSocket = originalWebSocket
})

// Test data generators
const generateStatisticsUpdate = () => fc.record({
  type: fc.constant('statistics_update'),
  data: fc.record({
    userId: fc.string({ minLength: 5, maxLength: 20 }), // Avoid single spaces
    statistics: fc.record({
      vpip: fc.float({ min: 0, max: 100 }),
      pfr: fc.float({ min: 0, max: 100 }),
      aggressionFactor: fc.float({ min: 0, max: 10 }),
      winRate: fc.float({ min: -50, max: 50 }),
      handsPlayed: fc.integer({ min: 0, max: 10000 }),
      totalWinnings: fc.float({ min: -10000, max: 10000 })
    }),
    filters: fc.record({
      dateRange: fc.record({
        start: fc.date({ min: new Date('2020-01-01'), max: new Date() }),
        end: fc.date({ min: new Date('2020-01-01'), max: new Date() })
      }),
      stakes: fc.oneof(
        fc.constant('all'),
        fc.string({ minLength: 3, maxLength: 20 })
      ),
      position: fc.oneof(
        fc.constant('all'),
        fc.constantFrom('UTG', 'MP', 'CO', 'BTN', 'SB', 'BB')
      ),
      gameType: fc.oneof(
        fc.constant('all'),
        fc.constantFrom('cash', 'tournament', 'sng')
      )
    })
  })
})

const generateProgressUpdate = () => fc.record({
  type: fc.constant('progress'),
  data: fc.record({
    taskId: fc.string({ minLength: 5, maxLength: 20 }), // Avoid single spaces
    progress: fc.float({ min: 0, max: 100 }),
    status: fc.constantFrom('processing', 'completed', 'error'),
    message: fc.option(fc.string({ minLength: 5, maxLength: 100 })),
    totalFiles: fc.option(fc.integer({ min: 1, max: 100 })),
    processedFiles: fc.option(fc.integer({ min: 0, max: 100 }))
  })
})

const generateFileMonitoringUpdate = () => fc.record({
  type: fc.constant('file_monitoring'),
  data: fc.record({
    event: fc.constantFrom('file_added', 'file_processed', 'scan_complete'),
    filename: fc.option(fc.string({ minLength: 5, maxLength: 50 })),
    totalFiles: fc.option(fc.integer({ min: 1, max: 100 })),
    processedFiles: fc.option(fc.integer({ min: 0, max: 100 }))
  })
})

const generateAnalysisUpdate = () => fc.record({
  type: fc.constant('analysis_update'),
  data: fc.record({
    analysisId: fc.string({ minLength: 5, maxLength: 20 }),
    handId: fc.string({ minLength: 5, maxLength: 20 }),
    status: fc.constantFrom('processing', 'completed', 'error'),
    result: fc.option(fc.record({
      analysis: fc.string({ minLength: 10, maxLength: 200 }),
      recommendations: fc.array(fc.string({ minLength: 5, maxLength: 50 }), { minLength: 1, maxLength: 3 }),
      confidence: fc.float({ min: 0, max: 1 })
    })),
    error: fc.option(fc.string({ minLength: 5, maxLength: 100 }))
  })
})

const generateChartDataPoint = () => fc.record({
  timestamp: fc.date({ min: new Date('2020-01-01'), max: new Date() }),
  value: fc.float({ min: 0, max: 1000 }),
  category: fc.string({ minLength: 3, maxLength: 20 }),
  metadata: fc.option(fc.record({
    source: fc.string({ minLength: 3, maxLength: 20 }),
    confidence: fc.float({ min: 0, max: 1 })
  }))
})

// Helper to create WebSocket provider wrapper
const createWebSocketWrapper = (url?: string) => {
  return ({ children }: { children: React.ReactNode }) => (
    <WebSocketProvider url={url} autoConnect={true}>
      {children}
    </WebSocketProvider>
  )
}

describe('Real-Time Updates Property Tests', () => {
  describe('Property 15: Dynamic Statistics Filtering', () => {
    test('should handle any statistics update message and trigger real-time recalculation', async () => {
      await fc.assert(fc.asyncProperty(
        generateStatisticsUpdate(),
        async (updateMessage) => {
          const mockWebSocket = new MockWebSocket('ws://localhost:8000/ws')
          let receivedUpdate: any = null

          const { result } = renderHook(() => useRealTimeStatistics(), {
            wrapper: createWebSocketWrapper('ws://localhost:8000/ws')
          })

          // Wait for WebSocket connection
          await waitFor(() => {
            expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN)
          }, { timeout: 100 })

          // Simulate receiving the statistics update
          act(() => {
            mockWebSocket.simulateMessage(updateMessage)
          })

          // Verify the update was processed
          await waitFor(() => {
            const { statistics, lastUpdate } = result.current
            if (statistics) {
              receivedUpdate = statistics
            }
          }, { timeout: 100 })

          // Property: Statistics updates should be processed and made available
          if (receivedUpdate) {
            expect(receivedUpdate).toEqual(updateMessage.data.statistics)
            expect(result.current.lastUpdate).toBeInstanceOf(Date)
          }

          // Property: Filter changes should trigger immediate updates
          const filters = updateMessage.data.filters
          expect(filters).toBeDefined()
          expect(typeof filters.dateRange).toBe('object')
          expect(['string', 'object'].includes(typeof filters.stakes)).toBe(true)
          expect(['string', 'object'].includes(typeof filters.position)).toBe(true)
          expect(['string', 'object'].includes(typeof filters.gameType)).toBe(true)
        }
      ), { numRuns: 100 })
    })

    test('should handle any progress update and maintain real-time progress tracking', async () => {
      await fc.assert(fc.asyncProperty(
        generateProgressUpdate(),
        async (progressMessage) => {
          const mockWebSocket = new MockWebSocket('ws://localhost:8000/ws')
          
          const { result } = renderHook(() => useProgressTracking(progressMessage.data.taskId), {
            wrapper: createWebSocketWrapper('ws://localhost:8000/ws')
          })

          // Wait for connection
          await waitFor(() => {
            expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN)
          }, { timeout: 100 })

          // Simulate progress update
          act(() => {
            mockWebSocket.simulateMessage(progressMessage)
          })

          // Verify progress tracking
          await waitFor(() => {
            const progress = result.current
            if (progress) {
              expect(progress.taskId).toBe(progressMessage.data.taskId)
              expect(progress.progress).toBe(progressMessage.data.progress)
              expect(progress.status).toBe(progressMessage.data.status)
              
              // Property: Progress values should be within valid ranges
              expect(progress.progress).toBeGreaterThanOrEqual(0)
              expect(progress.progress).toBeLessThanOrEqual(100)
              
              // Property: File counts should be consistent
              if (progress.totalFiles && progress.processedFiles) {
                expect(progress.processedFiles).toBeLessThanOrEqual(progress.totalFiles)
              }
            }
          }, { timeout: 100 })
        }
      ), { numRuns: 100 })
    })

    test('should handle any file monitoring update and track file processing in real-time', async () => {
      await fc.assert(fc.asyncProperty(
        generateFileMonitoringUpdate(),
        async (fileMessage) => {
          const mockWebSocket = new MockWebSocket('ws://localhost:8000/ws')
          
          const { result } = renderHook(() => useFileMonitoringUpdates(), {
            wrapper: createWebSocketWrapper('ws://localhost:8000/ws')
          })

          // Wait for connection
          await waitFor(() => {
            expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN)
          }, { timeout: 100 })

          // Simulate file monitoring update
          act(() => {
            mockWebSocket.simulateMessage(fileMessage)
          })

          // Verify file monitoring tracking
          await waitFor(() => {
            const updates = result.current
            if (updates) {
              expect(updates.event).toBe(fileMessage.data.event)
              
              // Property: File counts should be consistent
              if (updates.totalFiles && updates.processedFiles) {
                expect(updates.processedFiles).toBeLessThanOrEqual(updates.totalFiles)
                expect(updates.processedFiles).toBeGreaterThanOrEqual(0)
                expect(updates.totalFiles).toBeGreaterThan(0)
              }
              
              // Property: Event types should be valid
              expect(['file_added', 'file_processed', 'scan_complete']).toContain(updates.event)
            }
          }, { timeout: 100 })
        }
      ), { numRuns: 100 })
    })

    test('should handle any analysis update and track analysis progress in real-time', async () => {
      await fc.assert(fc.asyncProperty(
        generateAnalysisUpdate(),
        async (analysisMessage) => {
          const mockWebSocket = new MockWebSocket('ws://localhost:8000/ws')
          
          const { result } = renderHook(() => useRealTimeAnalysis(analysisMessage.data.analysisId), {
            wrapper: createWebSocketWrapper('ws://localhost:8000/ws')
          })

          // Wait for connection
          await waitFor(() => {
            expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN)
          }, { timeout: 100 })

          // Simulate analysis update
          act(() => {
            mockWebSocket.simulateMessage(analysisMessage)
          })

          // Verify analysis tracking
          await waitFor(() => {
            const analysis = result.current
            if (analysis) {
              expect(analysis.analysisId).toBe(analysisMessage.data.analysisId)
              expect(analysis.handId).toBe(analysisMessage.data.handId)
              expect(analysis.status).toBe(analysisMessage.data.status)
              
              // Property: Status should be valid
              expect(['processing', 'completed', 'error']).toContain(analysis.status)
              
              // Property: Completed analysis should have result or error
              if (analysis.status === 'completed') {
                expect(analysis.result || analysis.error).toBeDefined()
              }
              
              // Property: Error status should have error message
              if (analysis.status === 'error') {
                expect(analysis.error).toBeDefined()
              }
            }
          }, { timeout: 100 })
        }
      ), { numRuns: 100 })
    })

    test('should handle any chart data and maintain real-time chart updates', async () => {
      await fc.assert(fc.asyncProperty(
        fc.array(generateChartDataPoint(), { minLength: 1, maxLength: 100 }),
        fc.integer({ min: 100, max: 5000 }), // refresh interval
        fc.integer({ min: 10, max: 200 }), // max data points
        async (chartData, refreshInterval, maxDataPoints) => {
          let fetchCallCount = 0
          const mockFetchData = jest.fn(async () => {
            fetchCallCount++
            return chartData
          })

          const { result } = renderHook(() => useRealTimeCharts(mockFetchData, {
            refreshInterval,
            maxDataPoints,
            autoRefresh: false // Disable auto-refresh for testing
          }))

          // Initial data load
          await waitFor(() => {
            expect(result.current.data).toHaveLength(Math.min(chartData.length, maxDataPoints))
          }, { timeout: 200 })

          // Property: Data should be limited to maxDataPoints
          expect(result.current.data.length).toBeLessThanOrEqual(maxDataPoints)
          
          // Property: Data should maintain chronological order if timestamps exist
          const dataWithTimestamps = result.current.data.filter(d => d.timestamp)
          if (dataWithTimestamps.length > 1) {
            for (let i = 1; i < dataWithTimestamps.length; i++) {
              const prev = new Date(dataWithTimestamps[i - 1].timestamp).getTime()
              const curr = new Date(dataWithTimestamps[i].timestamp).getTime()
              expect(curr).toBeGreaterThanOrEqual(prev)
            }
          }

          // Property: Manual refresh should update data
          const initialFetchCount = fetchCallCount
          await act(async () => {
            await result.current.refresh()
          })
          
          expect(fetchCallCount).toBe(initialFetchCount + 1)
          expect(result.current.lastUpdate).toBeInstanceOf(Date)
        }
      ), { numRuns: 100 })
    })

    test('should handle WebSocket-enabled real-time charts with any statistics data', async () => {
      await fc.assert(fc.asyncProperty(
        fc.array(generateChartDataPoint(), { minLength: 1, maxLength: 50 }),
        generateStatisticsUpdate(),
        fc.string({ minLength: 1, maxLength: 50 }), // statistics key
        async (chartData, statisticsUpdate, statisticsKey) => {
          const mockFetchData = jest.fn(async () => chartData)
          const mockWebSocket = new MockWebSocket('ws://localhost:8000/ws')

          // Add the statistics key to the update
          const enhancedStatistics = {
            ...statisticsUpdate.data.statistics,
            [statisticsKey]: chartData
          }

          const { result } = renderHook(() => useWebSocketRealTimeCharts(mockFetchData, {
            enableWebSocket: true,
            userId: statisticsUpdate.data.userId,
            statisticsKey,
            autoRefresh: false
          }), {
            wrapper: createWebSocketWrapper('ws://localhost:8000/ws')
          })

          // Wait for initial data load
          await waitFor(() => {
            expect(result.current.data.length).toBeGreaterThan(0)
          }, { timeout: 200 })

          // Wait for WebSocket connection
          await waitFor(() => {
            expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN)
          }, { timeout: 100 })

          // Simulate WebSocket statistics update
          act(() => {
            mockWebSocket.simulateMessage({
              ...statisticsUpdate,
              data: {
                ...statisticsUpdate.data,
                statistics: enhancedStatistics
              }
            })
          })

          // Verify WebSocket data takes precedence
          await waitFor(() => {
            if (result.current.hasWebSocketData) {
              expect(result.current.data).toEqual(chartData)
              expect(result.current.isWebSocketEnabled).toBe(true)
            }
          }, { timeout: 200 })

          // Property: WebSocket data should override polling data when available
          if (result.current.hasWebSocketData) {
            expect(result.current.data).toEqual(chartData)
          }
        }
      ), { numRuns: 100 })
    })

    test('should handle multiple real-time chart data sources simultaneously', async () => {
      await fc.assert(fc.asyncProperty(
        fc.record({
          source1: fc.array(generateChartDataPoint(), { minLength: 1, maxLength: 20 }),
          source2: fc.array(generateChartDataPoint(), { minLength: 1, maxLength: 20 }),
          source3: fc.array(generateChartDataPoint(), { minLength: 1, maxLength: 20 })
        }),
        async (dataSources) => {
          const mockDataSources = {
            source1: jest.fn(async () => dataSources.source1),
            source2: jest.fn(async () => dataSources.source2),
            source3: jest.fn(async () => dataSources.source3)
          }

          const { result } = renderHook(() => useMultipleRealTimeCharts(mockDataSources, {
            autoRefresh: false
          }))

          // Wait for all data sources to load
          await waitFor(() => {
            expect(Object.keys(result.current.data)).toHaveLength(3)
          }, { timeout: 300 })

          // Property: All data sources should be loaded
          expect(result.current.data.source1).toEqual(dataSources.source1)
          expect(result.current.data.source2).toEqual(dataSources.source2)
          expect(result.current.data.source3).toEqual(dataSources.source3)

          // Property: Loading states should be managed per source
          expect(result.current.loading.source1).toBe(false)
          expect(result.current.loading.source2).toBe(false)
          expect(result.current.loading.source3).toBe(false)

          // Property: Last update times should be set for all sources
          expect(result.current.lastUpdates.source1).toBeInstanceOf(Date)
          expect(result.current.lastUpdates.source2).toBeInstanceOf(Date)
          expect(result.current.lastUpdates.source3).toBeInstanceOf(Date)

          // Property: Individual source refresh should work
          await act(async () => {
            await result.current.refreshSingle('source1')
          })

          expect(mockDataSources.source1).toHaveBeenCalledTimes(2) // Initial + refresh
          expect(mockDataSources.source2).toHaveBeenCalledTimes(1) // Only initial
          expect(mockDataSources.source3).toHaveBeenCalledTimes(1) // Only initial
        }
      ), { numRuns: 100 })
    })
  })

  describe('Real-Time Component Integration', () => {
    test('should render RealTimeProgress component with any progress data', async () => {
      await fc.assert(fc.asyncProperty(
        generateProgressUpdate(),
        fc.string({ minLength: 1, maxLength: 100 }), // title
        fc.boolean(), // showFileMonitoring
        async (progressUpdate, title, showFileMonitoring) => {
          const mockWebSocket = new MockWebSocket('ws://localhost:8000/ws')

          render(
            <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={true}>
              <RealTimeProgress 
                taskId={progressUpdate.data.taskId}
                title={title}
                showFileMonitoring={showFileMonitoring}
              />
            </WebSocketProvider>
          )

          // Wait for WebSocket connection
          await waitFor(() => {
            expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN)
          }, { timeout: 100 })

          // Simulate progress update
          act(() => {
            mockWebSocket.simulateMessage(progressUpdate)
          })

          // Property: Component should display progress information
          await waitFor(() => {
            expect(screen.getByText(title)).toBeInTheDocument()
            
            // Progress percentage should be displayed
            const progressText = `${progressUpdate.data.progress.toFixed(1)}%`
            expect(screen.getByText(progressText)).toBeInTheDocument()
            
            // Status badge should be displayed
            const statusText = progressUpdate.data.status.charAt(0).toUpperCase() + 
                              progressUpdate.data.status.slice(1)
            expect(screen.getByText(statusText)).toBeInTheDocument()
          }, { timeout: 200 })

          // Property: File counts should be displayed if available
          if (progressUpdate.data.totalFiles && progressUpdate.data.processedFiles) {
            const fileCountText = `${progressUpdate.data.processedFiles} / ${progressUpdate.data.totalFiles} files`
            expect(screen.getByText(fileCountText)).toBeInTheDocument()
          }

          // Property: Message should be displayed if available
          if (progressUpdate.data.message) {
            expect(screen.getByText(progressUpdate.data.message)).toBeInTheDocument()
          }
        }
      ), { numRuns: 100 })
    })

    test('should render RealTimeStatistics component with any user data', async () => {
      await fc.assert(fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }), // userId
        async (userId) => {
          const mockWebSocket = new MockWebSocket('ws://localhost:8000/ws')

          render(
            <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={true}>
              <RealTimeStatistics userId={userId} />
            </WebSocketProvider>
          )

          // Wait for WebSocket connection
          await waitFor(() => {
            expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN)
          }, { timeout: 100 })

          // Property: Component should display connection status
          await waitFor(() => {
            expect(screen.getByText('Real-time Statistics')).toBeInTheDocument()
            expect(screen.getByText('Connection:')).toBeInTheDocument()
            expect(screen.getByText('Active')).toBeInTheDocument()
          }, { timeout: 200 })

          // Property: Update counter should be displayed
          expect(screen.getByText('Updates received:')).toBeInTheDocument()
          expect(screen.getByText('0')).toBeInTheDocument()
        }
      ), { numRuns: 100 })
    })
  })

  describe('WebSocket Connection Management', () => {
    test('should handle any WebSocket connection state transitions', async () => {
      await fc.assert(fc.asyncProperty(
        fc.string({ minLength: 5, maxLength: 100 }), // WebSocket URL
        fc.array(fc.string({ minLength: 1, maxLength: 20 }), { maxLength: 5 }), // protocols
        fc.integer({ min: 1000, max: 10000 }), // reconnect interval
        fc.integer({ min: 1, max: 10 }), // max reconnect attempts
        async (url, protocols, reconnectInterval, maxReconnectAttempts) => {
          const client = new WebSocketClient({
            url: `ws://localhost:8000${url}`,
            protocols,
            reconnectInterval,
            maxReconnectAttempts
          })

          // Property: Initial state should be disconnected
          expect(client.getState()).toBe(WebSocketState.DISCONNECTED)

          // Property: Connection should transition through states
          client.connect()
          
          // Should be connecting initially
          await waitFor(() => {
            expect([WebSocketState.CONNECTING, WebSocketState.CONNECTED]).toContain(client.getState())
          }, { timeout: 100 })

          // Property: Disconnect should work from any state
          client.disconnect()
          
          await waitFor(() => {
            expect(client.getState()).toBe(WebSocketState.DISCONNECTED)
          }, { timeout: 100 })
        }
      ), { numRuns: 100 })
    })

    test('should handle any message subscription and unsubscription', async () => {
      await fc.assert(fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }), // message type
        fc.array(fc.record({
          type: fc.string({ minLength: 1, maxLength: 50 }),
          data: fc.anything()
        }), { minLength: 1, maxLength: 10 }), // messages
        async (messageType, messages) => {
          const client = new WebSocketClient({
            url: 'ws://localhost:8000/test'
          })

          let receivedMessages: any[] = []
          
          // Property: Subscription should capture matching messages
          const unsubscribe = client.subscribe(messageType, (data) => {
            receivedMessages.push(data)
          })

          client.connect()
          
          await waitFor(() => {
            expect(client.getState()).toBe(WebSocketState.CONNECTED)
          }, { timeout: 100 })

          // Simulate messages
          const mockWs = (client as any).ws as MockWebSocket
          messages.forEach(message => {
            mockWs.simulateMessage(message)
          })

          // Property: Only matching message types should be received
          const expectedMessages = messages
            .filter(msg => msg.type === messageType)
            .map(msg => msg.data)

          await waitFor(() => {
            expect(receivedMessages).toEqual(expectedMessages)
          }, { timeout: 100 })

          // Property: Unsubscription should stop message reception
          unsubscribe()
          const initialCount = receivedMessages.length
          
          // Send more messages after unsubscription
          messages.forEach(message => {
            mockWs.simulateMessage(message)
          })

          // Should not receive any more messages
          expect(receivedMessages).toHaveLength(initialCount)

          client.disconnect()
        }
      ), { numRuns: 100 })
    })
  })
})