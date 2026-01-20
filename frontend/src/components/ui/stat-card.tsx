"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "./card"
import { cn } from "@/lib/utils"

export interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: {
    value: number
    label: string
    isPositive?: boolean
  }
  icon?: React.ReactNode
  className?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'success' | 'warning' | 'danger'
  loading?: boolean
}

const StatCard = React.forwardRef<HTMLDivElement, StatCardProps>(
  ({ 
    title, 
    value, 
    subtitle, 
    trend, 
    icon, 
    className, 
    size = 'md',
    variant = 'default',
    loading = false 
  }, ref) => {
    const sizeClasses = {
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6'
    }

    const variantClasses = {
      default: 'border-border',
      success: 'border-green-200 bg-green-50/50',
      warning: 'border-yellow-200 bg-yellow-50/50',
      danger: 'border-red-200 bg-red-50/50'
    }

    const valueClasses = {
      default: 'text-foreground',
      success: 'text-green-700',
      warning: 'text-yellow-700',
      danger: 'text-red-700'
    }

    if (loading) {
      return (
        <Card ref={ref} className={cn(variantClasses[variant], className)}>
          <CardContent className={sizeClasses[size]}>
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-2"></div>
              <div className="h-8 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </div>
          </CardContent>
        </Card>
      )
    }

    return (
      <Card ref={ref} className={cn(variantClasses[variant], className)}>
        <CardContent className={sizeClasses[size]}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                {icon && <div className="text-muted-foreground">{icon}</div>}
                <p className="text-sm font-medium text-muted-foreground">{title}</p>
              </div>
              
              <div className={cn("text-2xl font-bold", valueClasses[variant])}>
                {value}
              </div>
              
              {subtitle && (
                <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
              )}
              
              {trend && (
                <div className="flex items-center gap-1 mt-2">
                  <div className={cn(
                    "text-xs font-medium",
                    trend.isPositive ? "text-green-600" : "text-red-600"
                  )}>
                    {trend.isPositive ? "↗" : "↘"} {Math.abs(trend.value)}%
                  </div>
                  <span className="text-xs text-muted-foreground">{trend.label}</span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }
)

StatCard.displayName = "StatCard"

// Specialized poker stat cards
export interface PokerStatCardProps extends Omit<StatCardProps, 'variant'> {
  statType?: 'vpip' | 'pfr' | 'aggression' | 'winrate' | 'hands' | 'profit'
}

export const PokerStatCard = React.forwardRef<HTMLDivElement, PokerStatCardProps>(
  ({ statType, value, ...props }, ref) => {
    const getVariant = (type: string | undefined, val: string | number): StatCardProps['variant'] => {
      if (typeof val !== 'number') return 'default'
      
      switch (type) {
        case 'vpip':
          return val > 30 ? 'warning' : val < 15 ? 'danger' : 'success'
        case 'pfr':
          return val > 25 ? 'warning' : val < 10 ? 'danger' : 'success'
        case 'winrate':
          return val > 0 ? 'success' : 'danger'
        case 'profit':
          return val > 0 ? 'success' : 'danger'
        default:
          return 'default'
      }
    }

    const formatValue = (type: string | undefined, val: string | number): string => {
      if (typeof val !== 'number') return val.toString()
      
      switch (type) {
        case 'vpip':
        case 'pfr':
          return `${val.toFixed(1)}%`
        case 'aggression':
          return val.toFixed(2)
        case 'winrate':
          return `${val > 0 ? '+' : ''}${val.toFixed(2)} BB/100`
        case 'profit':
          return `${val > 0 ? '+' : ''}$${val.toFixed(2)}`
        case 'hands':
          return val.toLocaleString()
        default:
          return val.toString()
      }
    }

    return (
      <StatCard
        ref={ref}
        {...props}
        value={formatValue(statType, value)}
        variant={getVariant(statType, value)}
      />
    )
  }
)

PokerStatCard.displayName = "PokerStatCard"

export { StatCard }