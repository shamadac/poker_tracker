"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRealTimeStatistics, useWebSocket } from '@/lib/websocket-client'

// Types for real-time chart data
export interface ChartDataPoint {
  [key: string]: any
}

export interface RealTimeChartConfig {
  refreshInterval?: number // milliseconds
  maxDataPoints?: number
  autoRefresh?: boolean
  onDataUpdate?: (data: ChartDataPoint[]) => void
  onError?: (error: Error) => void
}

// Hook for managing real-time chart updates
export function useRealTimeCharts<T extends ChartDataPoint>(
  fetchData: () => Promise<T[]>,
  config: RealTimeChartConfig = {}
) {
  const {
    refreshInterval = 30000, // 30 seconds default
    maxDataPoints = 100,
    autoRefresh = true,
    onDataUpdate,
    onError
  } = config

  const [data, setData] = useState<T[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)

  // Manual refresh function
  const refresh = useCallback(async () => {
    if (!mountedRef.current) return

    setLoading(true)
    setError(null)

    try {
      const newData = await fetchData()
      
      if (!mountedRef.current) return

      // Limit data points if specified
      const limitedData = maxDataPoints 
        ? newData.slice(-maxDataPoints)
        : newData

      setData(limitedData)
      setLastUpdate(new Date())
      
      if (onDataUpdate) {
        onDataUpdate(limitedData)
      }
    } catch (err) {
      if (!mountedRef.current) return
      
      const error = err instanceof Error ? err : new Error('Failed to fetch data')
      setError(error)
      
      if (onError) {
        onError(error)
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false)
      }
    }
  }, [fetchData, maxDataPoints, onDataUpdate, onError])

  // Start/stop auto refresh
  const startAutoRefresh = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    intervalRef.current = setInterval(refresh, refreshInterval)
  }, [refresh, refreshInterval])

  const stopAutoRefresh = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  // Toggle auto refresh
  const toggleAutoRefresh = useCallback(() => {
    if (intervalRef.current) {
      stopAutoRefresh()
    } else {
      startAutoRefresh()
    }
  }, [startAutoRefresh, stopAutoRefresh])

  // Initial data load and auto refresh setup
  useEffect(() => {
    refresh() // Initial load

    if (autoRefresh) {
      startAutoRefresh()
    }

    return () => {
      stopAutoRefresh()
    }
  }, [refresh, autoRefresh, startAutoRefresh, stopAutoRefresh])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false
      stopAutoRefresh()
    }
  }, [stopAutoRefresh])

  return {
    data,
    loading,
    error,
    lastUpdate,
    refresh,
    startAutoRefresh,
    stopAutoRefresh,
    toggleAutoRefresh,
    isAutoRefreshing: intervalRef.current !== null
  }
}

// Hook for managing multiple chart data sources
export function useMultipleRealTimeCharts<T extends Record<string, ChartDataPoint[]>>(
  dataSources: Record<keyof T, () => Promise<T[keyof T]>>,
  config: RealTimeChartConfig = {}
) {
  const [data, setData] = useState<T>({} as T)
  const [loading, setLoading] = useState<Record<keyof T, boolean>>({} as Record<keyof T, boolean>)
  const [errors, setErrors] = useState<Record<keyof T, Error | null>>({} as Record<keyof T, Error | null>)
  const [lastUpdates, setLastUpdates] = useState<Record<keyof T, Date | null>>({} as Record<keyof T, Date | null>)

  const refreshAll = useCallback(async () => {
    const keys = Object.keys(dataSources) as (keyof T)[]
    
    // Set loading state for all sources
    setLoading(prev => {
      const newLoading = { ...prev }
      keys.forEach(key => {
        newLoading[key] = true
      })
      return newLoading
    })

    // Clear errors
    setErrors(prev => {
      const newErrors = { ...prev }
      keys.forEach(key => {
        newErrors[key] = null
      })
      return newErrors
    })

    // Fetch all data sources in parallel
    const results = await Promise.allSettled(
      keys.map(async (key) => {
        try {
          const result = await dataSources[key]()
          return { key, data: result, error: null }
        } catch (error) {
          return { 
            key, 
            data: null, 
            error: error instanceof Error ? error : new Error('Failed to fetch data')
          }
        }
      })
    )

    // Process results
    const newData = { ...data }
    const newLoading = { ...loading }
    const newErrors = { ...errors }
    const newLastUpdates = { ...lastUpdates }

    results.forEach((result, index) => {
      const key = keys[index]
      newLoading[key] = false

      if (result.status === 'fulfilled') {
        const { data: resultData, error } = result.value
        
        if (error) {
          newErrors[key] = error
        } else if (resultData) {
          newData[key] = resultData
          newLastUpdates[key] = new Date()
        }
      } else {
        newErrors[key] = new Error('Promise rejected')
      }
    })

    setData(newData)
    setLoading(newLoading)
    setErrors(newErrors)
    setLastUpdates(newLastUpdates)
  }, [dataSources, data, loading, errors, lastUpdates])

  const refreshSingle = useCallback(async (key: keyof T) => {
    setLoading(prev => ({ ...prev, [key]: true }))
    setErrors(prev => ({ ...prev, [key]: null }))

    try {
      const result = await dataSources[key]()
      setData(prev => ({ ...prev, [key]: result }))
      setLastUpdates(prev => ({ ...prev, [key]: new Date() }))
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch data')
      setErrors(prev => ({ ...prev, [key]: err }))
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }))
    }
  }, [dataSources])

  // Use a dummy function for the single chart hook since we're managing multiple sources
  const dummyFetch = useCallback(async () => [], [])
  
  const { 
    refresh: _, 
    startAutoRefresh, 
    stopAutoRefresh, 
    toggleAutoRefresh, 
    isAutoRefreshing 
  } = useRealTimeCharts(dummyFetch, config)

  // Override refresh to use our refreshAll function
  const refresh = refreshAll

  return {
    data,
    loading,
    errors,
    lastUpdates,
    refresh,
    refreshSingle,
    startAutoRefresh,
    stopAutoRefresh,
    toggleAutoRefresh,
    isAutoRefreshing
  }
}

// Utility hook for chart data transformations
export function useChartDataTransform<TInput, TOutput>(
  data: TInput[],
  transform: (data: TInput[]) => TOutput[]
) {
  const [transformedData, setTransformedData] = useState<TOutput[]>([])

  useEffect(() => {
    try {
      const result = transform(data)
      setTransformedData(result)
    } catch (error) {
      console.error('Chart data transformation error:', error)
      setTransformedData([])
    }
  }, [data, transform])

  return transformedData
}

// Enhanced real-time charts hook with WebSocket integration
export function useWebSocketRealTimeCharts<T extends ChartDataPoint>(
  fetchData: () => Promise<T[]>,
  config: RealTimeChartConfig & {
    enableWebSocket?: boolean;
    userId?: string;
    statisticsKey?: string;
  } = {}
) {
  const {
    enableWebSocket = true,
    userId,
    statisticsKey,
    ...chartConfig
  } = config;

  // Use the existing polling-based hook as fallback
  const pollingResult = useRealTimeCharts(fetchData, chartConfig);
  
  // WebSocket real-time updates
  const { statistics: wsStatistics, lastUpdate: wsLastUpdate } = useRealTimeStatistics(userId);
  const [wsData, setWsData] = useState<T[]>([]);

  // Process WebSocket statistics updates
  useEffect(() => {
    if (enableWebSocket && wsStatistics && statisticsKey) {
      try {
        // Extract relevant data from WebSocket statistics
        const relevantData = wsStatistics[statisticsKey];
        if (relevantData && Array.isArray(relevantData)) {
          setWsData(relevantData as T[]);
        }
      } catch (error) {
        console.error('WebSocket data processing error:', error);
      }
    }
  }, [wsStatistics, statisticsKey, enableWebSocket]);

  // Merge WebSocket and polling data
  const finalData = enableWebSocket && wsData.length > 0 ? wsData : pollingResult.data;
  const finalLastUpdate = enableWebSocket && wsLastUpdate ? wsLastUpdate : pollingResult.lastUpdate;

  return {
    ...pollingResult,
    data: finalData,
    lastUpdate: finalLastUpdate,
    isWebSocketEnabled: enableWebSocket,
    hasWebSocketData: wsData.length > 0,
  };
}

// Hook for real-time progress charts
export function useProgressCharts(taskId?: string) {
  const [progressData, setProgressData] = useState<ChartDataPoint[]>([]);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('progress', (data: any) => {
      if (!taskId || data.taskId === taskId) {
        const newDataPoint: ChartDataPoint = {
          timestamp: new Date().toISOString(),
          progress: data.progress,
          status: data.status,
          processedFiles: data.processedFiles || 0,
          totalFiles: data.totalFiles || 0,
          message: data.message,
        };

        setProgressData(prev => {
          const updated = [...prev, newDataPoint];
          // Keep only last 100 data points
          return updated.slice(-100);
        });
      }
    });

    return unsubscribe;
  }, [subscribe, taskId]);

  const clearProgress = useCallback(() => {
    setProgressData([]);
  }, []);

  return {
    progressData,
    clearProgress,
    latestProgress: progressData[progressData.length - 1],
  };
}

// Hook for real-time file monitoring charts
export function useFileMonitoringCharts() {
  const [monitoringData, setMonitoringData] = useState<ChartDataPoint[]>([]);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('file_monitoring', (data: any) => {
      const newDataPoint: ChartDataPoint = {
        timestamp: new Date().toISOString(),
        event: data.event,
        filename: data.filename,
        totalFiles: data.totalFiles || 0,
        processedFiles: data.processedFiles || 0,
      };

      setMonitoringData(prev => {
        const updated = [...prev, newDataPoint];
        // Keep only last 200 data points
        return updated.slice(-200);
      });
    });

    return unsubscribe;
  }, [subscribe]);

  const clearMonitoring = useCallback(() => {
    setMonitoringData([]);
  }, []);

  return {
    monitoringData,
    clearMonitoring,
    latestEvent: monitoringData[monitoringData.length - 1],
  };
}

// Hook for real-time analysis progress
export function useAnalysisProgressCharts(analysisId?: string) {
  const [analysisData, setAnalysisData] = useState<ChartDataPoint[]>([]);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('analysis_update', (data: any) => {
      if (!analysisId || data.analysisId === analysisId) {
        const newDataPoint: ChartDataPoint = {
          timestamp: new Date().toISOString(),
          analysisId: data.analysisId,
          handId: data.handId,
          status: data.status,
          hasResult: !!data.result,
          hasError: !!data.error,
        };

        setAnalysisData(prev => {
          const updated = [...prev, newDataPoint];
          return updated.slice(-50); // Keep last 50 analysis updates
        });
      }
    });

    return unsubscribe;
  }, [subscribe, analysisId]);

  const clearAnalysis = useCallback(() => {
    setAnalysisData([]);
  }, []);

  return {
    analysisData,
    clearAnalysis,
    latestAnalysis: analysisData[analysisData.length - 1],
  };
}