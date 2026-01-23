/**
 * Basic tests for Dashboard Component Reliability
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { DashboardWidget } from '@/components/dashboard/dashboard-widget'

describe('Dashboard Widget Reliability', () => {
  it('should render widget with title', () => {
    render(
      <DashboardWidget
        id="test-widget"
        title="Test Widget"
      >
        <div data-testid="content">Widget content</div>
      </DashboardWidget>
    )

    expect(screen.getByText('Test Widget')).toBeInTheDocument()
    expect(screen.getByTestId('content')).toBeInTheDocument()
  })

  it('should show loading skeleton when loading', () => {
    render(
      <DashboardWidget
        id="test-widget"
        title="Test Widget"
        loading={true}
      >
        <div>Widget content</div>
      </DashboardWidget>
    )

    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('should show error state when error is provided', () => {
    const error = new Error('Test error')
    
    render(
      <DashboardWidget
        id="test-widget"
        title="Test Widget"
        error={error}
      >
        <div>Widget content</div>
      </DashboardWidget>
    )

    expect(screen.getByText('Failed to load test widget')).toBeInTheDocument()
  })

  it('should show cached data overlay when fallback data is provided with error', () => {
    const error = new Error('Test error')
    const fallbackData = { test: 'data' }
    
    render(
      <DashboardWidget
        id="test-widget"
        title="Test Widget"
        error={error}
        fallbackData={fallbackData}
      >
        <div>Widget content</div>
      </DashboardWidget>
    )

    expect(screen.getByText('Showing cached data')).toBeInTheDocument()
  })
})