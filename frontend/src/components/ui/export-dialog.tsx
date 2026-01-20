"use client"

import React, { useState } from 'react'
import { Button } from './button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select'
import { Label } from './label'
import { Checkbox } from './checkbox'
import { Badge } from './badge'
import { useToast } from '@/hooks/use-toast'
import { exportUtils, ExportOptions } from '@/lib/export-utils'
import { 
  Download, 
  FileText, 
  FileSpreadsheet, 
  Loader2, 
  Calendar,
  Filter,
  Settings,
  X
} from 'lucide-react'

export interface ExportDialogProps {
  isOpen: boolean
  onClose: () => void
  currentFilters?: any
  title?: string
  description?: string
}

export function ExportDialog({ 
  isOpen, 
  onClose, 
  currentFilters = {},
  title = "Export Data",
  description = "Choose your export format and options"
}: ExportDialogProps) {
  const [exportType, setExportType] = useState<'statistics' | 'hands' | 'comprehensive'>('statistics')
  const [format, setFormat] = useState<'csv' | 'pdf'>('pdf')
  const [includeCharts, setIncludeCharts] = useState(true)
  const [includeHands, setIncludeHands] = useState(false)
  const [handsLimit, setHandsLimit] = useState(1000)
  const [isExporting, setIsExporting] = useState(false)
  const { toast } = useToast()

  if (!isOpen) return null

  const handleExport = async () => {
    setIsExporting(true)
    
    try {
      const options: ExportOptions = {
        includeCharts: format === 'pdf' ? includeCharts : undefined,
        includeHands: exportType === 'comprehensive' ? includeHands : undefined
      }

      switch (exportType) {
        case 'statistics':
          if (format === 'csv') {
            await exportUtils.exportCurrentStatsCSV(currentFilters)
          } else {
            await exportUtils.exportCurrentStatsPDF(currentFilters, includeCharts)
          }
          break
          
        case 'hands':
          await exportUtils.exportCurrentHandsCSV(currentFilters, handsLimit)
          break
          
        case 'comprehensive':
          // Only PDF format for comprehensive reports
          const { exportService } = await import('@/lib/export-utils')
          await exportService.exportComprehensiveReportPDF({
            ...options,
            gameType: currentFilters.gameType,
            stakes: currentFilters.stakes,
            position: currentFilters.position
          })
          break
      }

      toast({
        title: "Export Started",
        description: "Your file download should begin shortly.",
      })
      
      onClose()
      
    } catch (error) {
      toast({
        title: "Export Failed",
        description: error instanceof Error ? error.message : "Failed to export data",
        variant: "destructive"
      })
    } finally {
      setIsExporting(false)
    }
  }

  const getExportIcon = () => {
    if (format === 'csv') return <FileSpreadsheet className="h-4 w-4" />
    return <FileText className="h-4 w-4" />
  }

  const getFormatDescription = () => {
    switch (format) {
      case 'csv':
        return "Spreadsheet format perfect for data analysis in Excel or Google Sheets"
      case 'pdf':
        return "Professional report format with charts and formatted tables"
      default:
        return ""
    }
  }

  const getExportTypeDescription = () => {
    switch (exportType) {
      case 'statistics':
        return "Export your poker statistics and performance metrics"
      case 'hands':
        return "Export detailed hand history data for analysis"
      case 'comprehensive':
        return "Export a complete poker analysis report with all data"
      default:
        return ""
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Download className="h-5 w-5" />
                {title}
              </CardTitle>
              <CardDescription>{description}</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Current Filters Display */}
          {Object.keys(currentFilters).length > 0 && (
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Filter className="h-4 w-4" />
                Current Filters
              </Label>
              <div className="flex flex-wrap gap-2">
                {currentFilters.dateRange && currentFilters.dateRange !== 'all' && (
                  <Badge variant="secondary">
                    <Calendar className="h-3 w-3 mr-1" />
                    {currentFilters.dateRange}
                  </Badge>
                )}
                {currentFilters.gameType && currentFilters.gameType !== 'all' && (
                  <Badge variant="secondary">Game: {currentFilters.gameType}</Badge>
                )}
                {currentFilters.stakes && currentFilters.stakes !== 'all' && (
                  <Badge variant="secondary">Stakes: {currentFilters.stakes}</Badge>
                )}
                {currentFilters.position && currentFilters.position !== 'all' && (
                  <Badge variant="secondary">Position: {currentFilters.position}</Badge>
                )}
              </div>
            </div>
          )}

          {/* Export Type Selection */}
          <div className="space-y-3">
            <Label>Export Type</Label>
            <Select value={exportType} onValueChange={(value: any) => setExportType(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="statistics">Statistics Report</SelectItem>
                <SelectItem value="hands">Hand History</SelectItem>
                <SelectItem value="comprehensive">Comprehensive Report</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              {getExportTypeDescription()}
            </p>
          </div>

          {/* Format Selection */}
          <div className="space-y-3">
            <Label>Format</Label>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant={format === 'csv' ? 'default' : 'outline'}
                onClick={() => setFormat('csv')}
                className="h-auto p-4 flex flex-col items-center gap-2"
                disabled={exportType === 'comprehensive'} // Comprehensive only supports PDF
              >
                <FileSpreadsheet className="h-6 w-6" />
                <div className="text-center">
                  <div className="font-medium">CSV</div>
                  <div className="text-xs text-muted-foreground">Spreadsheet</div>
                </div>
              </Button>
              
              <Button
                variant={format === 'pdf' ? 'default' : 'outline'}
                onClick={() => setFormat('pdf')}
                className="h-auto p-4 flex flex-col items-center gap-2"
              >
                <FileText className="h-6 w-6" />
                <div className="text-center">
                  <div className="font-medium">PDF</div>
                  <div className="text-xs text-muted-foreground">Report</div>
                </div>
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              {getFormatDescription()}
            </p>
          </div>

          {/* PDF Options */}
          {format === 'pdf' && (
            <div className="space-y-3">
              <Label className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                PDF Options
              </Label>
              
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeCharts"
                    checked={includeCharts}
                    onCheckedChange={setIncludeCharts}
                  />
                  <Label htmlFor="includeCharts" className="text-sm">
                    Include charts and graphs
                  </Label>
                </div>
                
                {exportType === 'comprehensive' && (
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="includeHands"
                      checked={includeHands}
                      onCheckedChange={setIncludeHands}
                    />
                    <Label htmlFor="includeHands" className="text-sm">
                      Include detailed hand history
                    </Label>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Hand History Options */}
          {exportType === 'hands' && (
            <div className="space-y-3">
              <Label>Hand Limit</Label>
              <Select value={handsLimit.toString()} onValueChange={(value) => setHandsLimit(parseInt(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="100">100 hands</SelectItem>
                  <SelectItem value="500">500 hands</SelectItem>
                  <SelectItem value="1000">1,000 hands</SelectItem>
                  <SelectItem value="5000">5,000 hands</SelectItem>
                  <SelectItem value="10000">10,000 hands</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Maximum number of hands to include in the export
              </p>
            </div>
          )}

          {/* Export Button */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button variant="outline" onClick={onClose} disabled={isExporting}>
              Cancel
            </Button>
            <Button onClick={handleExport} disabled={isExporting}>
              {isExporting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  {getExportIcon()}
                  <span className="ml-2">Export {format.toUpperCase()}</span>
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Checkbox component if not already available
export function Checkbox({ 
  checked, 
  onCheckedChange, 
  id, 
  className,
  ...props 
}: {
  checked: boolean
  onCheckedChange: (checked: boolean) => void
  id?: string
  className?: string
  [key: string]: any
}) {
  return (
    <input
      type="checkbox"
      id={id}
      checked={checked}
      onChange={(e) => onCheckedChange(e.target.checked)}
      className={`h-4 w-4 rounded border border-input bg-background ${className}`}
      {...props}
    />
  )
}