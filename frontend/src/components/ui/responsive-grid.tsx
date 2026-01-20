import * as React from "react"
import { cn } from "@/lib/utils"

interface ResponsiveGridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: {
    default?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
  }
  gap?: number
}

const ResponsiveGrid = React.forwardRef<HTMLDivElement, ResponsiveGridProps>(
  ({ className, cols = { default: 1, md: 2, lg: 3 }, gap = 6, ...props }, ref) => {
    const gridClasses = []
    
    // Default columns
    if (cols.default) {
      gridClasses.push(`grid-cols-${cols.default}`)
    }
    
    // Responsive columns
    if (cols.sm) gridClasses.push(`sm:grid-cols-${cols.sm}`)
    if (cols.md) gridClasses.push(`md:grid-cols-${cols.md}`)
    if (cols.lg) gridClasses.push(`lg:grid-cols-${cols.lg}`)
    if (cols.xl) gridClasses.push(`xl:grid-cols-${cols.xl}`)
    
    return (
      <div
        ref={ref}
        className={cn(
          "grid",
          `gap-${gap}`,
          ...gridClasses,
          className
        )}
        {...props}
      />
    )
  }
)
ResponsiveGrid.displayName = "ResponsiveGrid"

export { ResponsiveGrid }