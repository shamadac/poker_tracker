"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "./card"
import { Button } from "./button"
import { Input } from "./input"
import { cn } from "@/lib/utils"

// Table column definition
export interface DataTableColumn<T> {
  key: keyof T | string
  title: string
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, row: T, index: number) => React.ReactNode
  width?: string
  align?: 'left' | 'center' | 'right'
}

// Filter configuration
export interface DataTableFilter {
  key: string
  label: string
  type: 'text' | 'select' | 'date' | 'number'
  options?: Array<{ label: string; value: string }>
  placeholder?: string
}

// Sort configuration
export interface SortConfig {
  key: string
  direction: 'asc' | 'desc'
}

export interface DataTableProps<T> {
  data: T[]
  columns: DataTableColumn<T>[]
  filters?: DataTableFilter[]
  title?: string
  subtitle?: string
  className?: string
  loading?: boolean
  pageSize?: number
  searchable?: boolean
  searchPlaceholder?: string
  onRowClick?: (row: T, index: number) => void
  emptyMessage?: string
}

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  filters = [],
  title,
  subtitle,
  className,
  loading = false,
  pageSize = 10,
  searchable = true,
  searchPlaceholder = "Search...",
  onRowClick,
  emptyMessage = "No data available"
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = React.useState("")
  const [filterValues, setFilterValues] = React.useState<Record<string, string>>({})
  const [sortConfig, setSortConfig] = React.useState<SortConfig | null>(null)
  const [currentPage, setCurrentPage] = React.useState(1)

  // Filter data based on search term and filters
  const filteredData = React.useMemo(() => {
    let filtered = [...data]

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    }

    // Apply column filters
    Object.entries(filterValues).forEach(([key, value]) => {
      if (value) {
        filtered = filtered.filter(row => {
          const rowValue = String(row[key]).toLowerCase()
          return rowValue.includes(value.toLowerCase())
        })
      }
    })

    return filtered
  }, [data, searchTerm, filterValues])

  // Sort data
  const sortedData = React.useMemo(() => {
    if (!sortConfig) return filteredData

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortConfig.key]
      const bValue = b[sortConfig.key]

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1
      }
      return 0
    })
  }, [filteredData, sortConfig])

  // Paginate data
  const paginatedData = React.useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return sortedData.slice(startIndex, startIndex + pageSize)
  }, [sortedData, currentPage, pageSize])

  const totalPages = Math.ceil(sortedData.length / pageSize)

  const handleSort = (key: string) => {
    setSortConfig(current => {
      if (current?.key === key) {
        return current.direction === 'asc' 
          ? { key, direction: 'desc' }
          : null
      }
      return { key, direction: 'asc' }
    })
  }

  const handleFilterChange = (key: string, value: string) => {
    setFilterValues(prev => ({ ...prev, [key]: value }))
    setCurrentPage(1) // Reset to first page when filtering
  }

  const clearFilters = () => {
    setSearchTerm("")
    setFilterValues({})
    setSortConfig(null)
    setCurrentPage(1)
  }

  if (loading) {
    return (
      <Card className={className}>
        {title && (
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
          </CardHeader>
        )}
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-10 bg-gray-200 rounded"></div>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
        </CardHeader>
      )}
      <CardContent>
        {/* Search and Filters */}
        <div className="space-y-4 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            {searchable && (
              <div className="flex-1">
                <Input
                  placeholder={searchPlaceholder}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
              </div>
            )}
            
            {(searchTerm || Object.values(filterValues).some(v => v) || sortConfig) && (
              <Button variant="outline" onClick={clearFilters}>
                Clear Filters
              </Button>
            )}
          </div>

          {filters.length > 0 && (
            <div className="flex flex-wrap gap-4">
              {filters.map((filter) => (
                <div key={filter.key} className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-muted-foreground">
                    {filter.label}
                  </label>
                  {filter.type === 'select' ? (
                    <select
                      className="px-3 py-2 border border-input rounded-md text-sm"
                      value={filterValues[filter.key] || ''}
                      onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                    >
                      <option value="">All</option>
                      {filter.options?.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <Input
                      type={filter.type}
                      placeholder={filter.placeholder}
                      value={filterValues[filter.key] || ''}
                      onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                      className="w-40"
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Table */}
        <div className="rounded-md border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  {columns.map((column) => (
                    <th
                      key={String(column.key)}
                      className={cn(
                        "px-4 py-3 text-left text-sm font-medium text-muted-foreground",
                        column.align === 'center' && "text-center",
                        column.align === 'right' && "text-right",
                        column.sortable && "cursor-pointer hover:text-foreground"
                      )}
                      style={{ width: column.width }}
                      onClick={() => column.sortable && handleSort(String(column.key))}
                    >
                      <div className="flex items-center gap-2">
                        {column.title}
                        {column.sortable && sortConfig?.key === column.key && (
                          <span className="text-xs">
                            {sortConfig.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paginatedData.length === 0 ? (
                  <tr>
                    <td colSpan={columns.length} className="px-4 py-8 text-center text-muted-foreground">
                      {emptyMessage}
                    </td>
                  </tr>
                ) : (
                  paginatedData.map((row, index) => (
                    <tr
                      key={index}
                      className={cn(
                        "border-t hover:bg-muted/50 transition-colors",
                        onRowClick && "cursor-pointer"
                      )}
                      onClick={() => onRowClick?.(row, index)}
                    >
                      {columns.map((column) => {
                        const value = row[column.key]
                        return (
                          <td
                            key={String(column.key)}
                            className={cn(
                              "px-4 py-3 text-sm",
                              column.align === 'center' && "text-center",
                              column.align === 'right' && "text-right"
                            )}
                          >
                            {column.render ? column.render(value, row, index) : String(value || '')}
                          </td>
                        )
                      })}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-muted-foreground">
              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length} results
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = i + 1
                  return (
                    <Button
                      key={page}
                      variant={currentPage === page ? "default" : "outline"}
                      size="sm"
                      onClick={() => setCurrentPage(page)}
                      className="w-8 h-8 p-0"
                    >
                      {page}
                    </Button>
                  )
                })}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Specialized poker hand history table
export interface PokerHandData {
  id: string
  handId: string
  date: string
  gameType: string
  stakes: string
  position: string
  cards: string[]
  result: string
  profit: number
  vpip?: boolean
  pfr?: boolean
}

export interface PokerHandTableProps {
  hands: PokerHandData[]
  title?: string
  className?: string
  loading?: boolean
  onHandClick?: (hand: PokerHandData) => void
}

export const PokerHandTable = React.forwardRef<HTMLDivElement, PokerHandTableProps>(
  ({ hands, title = "Hand History", className, loading = false, onHandClick }, ref) => {
    const columns: DataTableColumn<PokerHandData>[] = [
      {
        key: 'handId',
        title: 'Hand ID',
        sortable: true,
        width: '120px',
        render: (value) => (
          <span className="font-mono text-xs">{value}</span>
        )
      },
      {
        key: 'date',
        title: 'Date',
        sortable: true,
        width: '140px',
        render: (value) => new Date(value).toLocaleString()
      },
      {
        key: 'gameType',
        title: 'Game',
        sortable: true,
        filterable: true,
        width: '100px'
      },
      {
        key: 'stakes',
        title: 'Stakes',
        sortable: true,
        filterable: true,
        width: '80px'
      },
      {
        key: 'position',
        title: 'Position',
        sortable: true,
        filterable: true,
        width: '80px',
        align: 'center'
      },
      {
        key: 'cards',
        title: 'Cards',
        width: '100px',
        align: 'center',
        render: (cards: string[]) => (
          <div className="flex gap-1 justify-center">
            {cards.slice(0, 2).map((card, i) => (
              <span key={i} className="font-mono text-xs bg-muted px-1 py-0.5 rounded">
                {card}
              </span>
            ))}
          </div>
        )
      },
      {
        key: 'result',
        title: 'Result',
        sortable: true,
        width: '80px',
        align: 'center'
      },
      {
        key: 'profit',
        title: 'Profit',
        sortable: true,
        width: '100px',
        align: 'right',
        render: (value: number) => (
          <span className={cn(
            "font-medium",
            value > 0 ? "text-green-600" : value < 0 ? "text-red-600" : "text-muted-foreground"
          )}>
            {value > 0 ? '+' : ''}{value.toFixed(2)}
          </span>
        )
      }
    ]

    const filters: DataTableFilter[] = [
      {
        key: 'gameType',
        label: 'Game Type',
        type: 'select',
        options: [
          { label: 'Hold\'em', value: 'holdem' },
          { label: 'Omaha', value: 'omaha' },
          { label: 'Tournament', value: 'tournament' }
        ]
      },
      {
        key: 'position',
        label: 'Position',
        type: 'select',
        options: [
          { label: 'Early', value: 'early' },
          { label: 'Middle', value: 'middle' },
          { label: 'Late', value: 'late' },
          { label: 'Blinds', value: 'blinds' }
        ]
      }
    ]

    return (
      <div ref={ref}>
        <DataTable
          data={hands}
          columns={columns}
          filters={filters}
          title={title}
          className={className}
          loading={loading}
          onRowClick={onHandClick}
          searchPlaceholder="Search hands..."
          emptyMessage="No hands found"
        />
      </div>
    )
  }
)

PokerHandTable.displayName = "PokerHandTable"