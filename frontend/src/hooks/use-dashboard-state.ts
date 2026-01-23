"use client"

import { useState, useEffect, useCallback } from "react"

interface DashboardViewState {
  layout: 'grid' | 'list'
  widgetVisibility: Record<string, boolean>
  refreshInterval: number
  autoRefresh: boolean
  filters: Record<string, any>
  sortOrder: string
  expandedWidgets: string[]
  lastRefresh: Date | null
}

interface DashboardPreferences {
  theme: 'light' | 'dark' | 'system'
  compactMode: boolean
  showTrends: boolean
  defaultTimeRange: string
  notifications: boolean
}

const DEFAULT_VIEW_STATE: DashboardViewState = {
  layout: 'grid',
  widgetVisibility: {
    'dashboard-stats': true,
    'performance-chart': true,
    'volume-chart': true,
    'position-chart': true,
    'dashboard-sessions': true,
    'dashboard-hands': true
  },
  refreshInterval: 30000, // 30 seconds
  autoRefresh: true,
  filters: {},
  sortOrder: 'newest',
  expandedWidgets: [],
  lastRefresh: null
}

const DEFAULT_PREFERENCES: DashboardPreferences = {
  theme: 'system',
  compactMode: false,
  showTrends: true,
  defaultTimeRange: '7d',
  notifications: true
}

const VIEW_STATE_KEY = 'dashboard_view_state'
const PREFERENCES_KEY = 'dashboard_preferences'

function saveToStorage<T>(key: string, data: T) {
  try {
    localStorage.setItem(key, JSON.stringify(data))
  } catch (error) {
    console.warn(`Failed to save ${key} to localStorage:`, error)
  }
}

function loadFromStorage<T>(key: string, defaultValue: T): T {
  try {
    const stored = localStorage.getItem(key)
    if (stored) {
      const parsed = JSON.parse(stored)
      // Merge with defaults to handle new properties
      return { ...defaultValue, ...parsed }
    }
  } catch (error) {
    console.warn(`Failed to load ${key} from localStorage:`, error)
  }
  return defaultValue
}

export function useDashboardState() {
  const [viewState, setViewState] = useState<DashboardViewState>(DEFAULT_VIEW_STATE)
  const [preferences, setPreferences] = useState<DashboardPreferences>(DEFAULT_PREFERENCES)
  const [isLoading, setIsLoading] = useState(true)

  // Load initial state from localStorage
  useEffect(() => {
    const loadedViewState = loadFromStorage(VIEW_STATE_KEY, DEFAULT_VIEW_STATE)
    const loadedPreferences = loadFromStorage(PREFERENCES_KEY, DEFAULT_PREFERENCES)
    
    setViewState(loadedViewState)
    setPreferences(loadedPreferences)
    setIsLoading(false)
  }, [])

  // Save view state changes
  const updateViewState = useCallback((updates: Partial<DashboardViewState>) => {
    setViewState(prev => {
      const newState = { ...prev, ...updates }
      saveToStorage(VIEW_STATE_KEY, newState)
      return newState
    })
  }, [])

  // Save preference changes
  const updatePreferences = useCallback((updates: Partial<DashboardPreferences>) => {
    setPreferences(prev => {
      const newPrefs = { ...prev, ...updates }
      saveToStorage(PREFERENCES_KEY, newPrefs)
      return newPrefs
    })
  }, [])

  // Widget visibility controls
  const toggleWidget = useCallback((widgetId: string) => {
    updateViewState({
      widgetVisibility: {
        ...viewState.widgetVisibility,
        [widgetId]: !viewState.widgetVisibility[widgetId]
      }
    })
  }, [viewState.widgetVisibility, updateViewState])

  const showWidget = useCallback((widgetId: string) => {
    updateViewState({
      widgetVisibility: {
        ...viewState.widgetVisibility,
        [widgetId]: true
      }
    })
  }, [viewState.widgetVisibility, updateViewState])

  const hideWidget = useCallback((widgetId: string) => {
    updateViewState({
      widgetVisibility: {
        ...viewState.widgetVisibility,
        [widgetId]: false
      }
    })
  }, [viewState.widgetVisibility, updateViewState])

  // Layout controls
  const setLayout = useCallback((layout: 'grid' | 'list') => {
    updateViewState({ layout })
  }, [updateViewState])

  // Filter controls
  const updateFilters = useCallback((filters: Record<string, any>) => {
    updateViewState({ filters })
  }, [updateViewState])

  const clearFilters = useCallback(() => {
    updateViewState({ filters: {} })
  }, [updateViewState])

  // Enhanced refresh controls with state preservation
  const setAutoRefresh = useCallback((autoRefresh: boolean) => {
    updateViewState({ autoRefresh })
  }, [updateViewState])

  const setRefreshInterval = useCallback((interval: number) => {
    updateViewState({ refreshInterval: interval })
  }, [updateViewState])

  const markRefreshed = useCallback(() => {
    updateViewState({ lastRefresh: new Date() })
  }, [updateViewState])

  // View state preservation during refresh
  const preserveViewState = useCallback(() => {
    const currentState = {
      layout: viewState.layout,
      widgetVisibility: viewState.widgetVisibility,
      expandedWidgets: viewState.expandedWidgets,
      filters: viewState.filters,
      sortOrder: viewState.sortOrder
    }
    
    // Store in sessionStorage for refresh persistence
    try {
      sessionStorage.setItem('dashboard_refresh_state', JSON.stringify(currentState))
    } catch (error) {
      console.warn('Failed to preserve view state:', error)
    }
    
    return currentState
  }, [viewState])

  const restoreViewState = useCallback(() => {
    try {
      const stored = sessionStorage.getItem('dashboard_refresh_state')
      if (stored) {
        const restoredState = JSON.parse(stored)
        updateViewState(restoredState)
        sessionStorage.removeItem('dashboard_refresh_state')
        return true
      }
    } catch (error) {
      console.warn('Failed to restore view state:', error)
    }
    return false
  }, [updateViewState])

  // Auto-restore view state on mount
  useEffect(() => {
    if (!isLoading) {
      restoreViewState()
    }
  }, [isLoading, restoreViewState])

  // Widget expansion controls
  const toggleWidgetExpansion = useCallback((widgetId: string) => {
    const isExpanded = viewState.expandedWidgets.includes(widgetId)
    const expandedWidgets = isExpanded
      ? viewState.expandedWidgets.filter(id => id !== widgetId)
      : [...viewState.expandedWidgets, widgetId]
    
    updateViewState({ expandedWidgets })
  }, [viewState.expandedWidgets, updateViewState])

  const expandWidget = useCallback((widgetId: string) => {
    if (!viewState.expandedWidgets.includes(widgetId)) {
      updateViewState({
        expandedWidgets: [...viewState.expandedWidgets, widgetId]
      })
    }
  }, [viewState.expandedWidgets, updateViewState])

  const collapseWidget = useCallback((widgetId: string) => {
    updateViewState({
      expandedWidgets: viewState.expandedWidgets.filter(id => id !== widgetId)
    })
  }, [viewState.expandedWidgets, updateViewState])

  const collapseAllWidgets = useCallback(() => {
    updateViewState({ expandedWidgets: [] })
  }, [updateViewState])

  // Reset functions
  const resetViewState = useCallback(() => {
    setViewState(DEFAULT_VIEW_STATE)
    saveToStorage(VIEW_STATE_KEY, DEFAULT_VIEW_STATE)
  }, [])

  const resetPreferences = useCallback(() => {
    setPreferences(DEFAULT_PREFERENCES)
    saveToStorage(PREFERENCES_KEY, DEFAULT_PREFERENCES)
  }, [])

  const resetAll = useCallback(() => {
    resetViewState()
    resetPreferences()
  }, [resetViewState, resetPreferences])

  // Computed values
  const visibleWidgets = Object.entries(viewState.widgetVisibility)
    .filter(([_, visible]) => visible)
    .map(([id]) => id)

  const hiddenWidgets = Object.entries(viewState.widgetVisibility)
    .filter(([_, visible]) => !visible)
    .map(([id]) => id)

  const isWidgetVisible = useCallback((widgetId: string) => {
    return viewState.widgetVisibility[widgetId] ?? true
  }, [viewState.widgetVisibility])

  const isWidgetExpanded = useCallback((widgetId: string) => {
    return viewState.expandedWidgets.includes(widgetId)
  }, [viewState.expandedWidgets])

  return {
    // State
    viewState,
    preferences,
    isLoading,
    
    // View state controls
    updateViewState,
    updatePreferences,
    
    // Widget controls
    toggleWidget,
    showWidget,
    hideWidget,
    isWidgetVisible,
    
    // Layout controls
    setLayout,
    
    // Filter controls
    updateFilters,
    clearFilters,
    
    // Refresh controls
    setAutoRefresh,
    setRefreshInterval,
    markRefreshed,
    preserveViewState,
    restoreViewState,
    
    // Expansion controls
    toggleWidgetExpansion,
    expandWidget,
    collapseWidget,
    collapseAllWidgets,
    isWidgetExpanded,
    
    // Reset functions
    resetViewState,
    resetPreferences,
    resetAll,
    
    // Computed values
    visibleWidgets,
    hiddenWidgets
  }
}