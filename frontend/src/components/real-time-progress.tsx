'use client';

import { useState, useEffect } from 'react';
import { useProgressTracking, useFileMonitoringUpdates } from '@/lib/websocket-client';
import { useWebSocketContext } from '@/contexts/websocket-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface ProgressBarProps {
  progress: number;
  status: 'processing' | 'completed' | 'error';
  className?: string;
}

function ProgressBar({ progress, status, className = '' }: ProgressBarProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-blue-500';
    }
  };

  return (
    <div className={`w-full bg-gray-200 rounded-full h-2 ${className}`}>
      <div
        className={`h-2 rounded-full transition-all duration-300 ${getStatusColor()}`}
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      />
    </div>
  );
}

interface RealTimeProgressProps {
  taskId?: string;
  title?: string;
  showFileMonitoring?: boolean;
}

export function RealTimeProgress({ 
  taskId, 
  title = 'Processing Progress',
  showFileMonitoring = false 
}: RealTimeProgressProps) {
  const { isConnected, state } = useWebSocketContext();
  const progress = useProgressTracking(taskId);
  const fileMonitoring = useFileMonitoringUpdates();
  const [progressHistory, setProgressHistory] = useState<any[]>([]);

  // Track progress history for visualization
  useEffect(() => {
    if (progress) {
      setProgressHistory(prev => {
        const newHistory = [...prev, { ...progress, timestamp: new Date() }];
        return newHistory.slice(-10); // Keep last 10 progress updates
      });
    }
  }, [progress]);

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      processing: 'default',
      completed: 'secondary',
      error: 'destructive',
    };
    
    return (
      <Badge variant={variants[status] || 'outline'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      {/* WebSocket Connection Status */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Real-time Connection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm">
              {isConnected ? 'Connected' : `Disconnected (${state})`}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Progress Tracking */}
      {progress && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">{title}</CardTitle>
              {getStatusBadge(progress.status)}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <ProgressBar 
              progress={progress.progress} 
              status={progress.status}
            />
            
            <div className="flex justify-between text-xs text-gray-600">
              <span>{progress.progress.toFixed(1)}%</span>
              {progress.totalFiles && (
                <span>
                  {progress.processedFiles || 0} / {progress.totalFiles} files
                </span>
              )}
            </div>
            
            {progress.message && (
              <p className="text-xs text-gray-500">{progress.message}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* File Monitoring Updates */}
      {showFileMonitoring && fileMonitoring && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">File Monitoring</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Latest Event:</span>
                <Badge variant="outline">
                  {fileMonitoring.event.replace('_', ' ')}
                </Badge>
              </div>
              
              {fileMonitoring.filename && (
                <p className="text-xs text-gray-600">
                  File: {fileMonitoring.filename}
                </p>
              )}
              
              {fileMonitoring.totalFiles && (
                <div className="text-xs text-gray-600">
                  Progress: {fileMonitoring.processedFiles || 0} / {fileMonitoring.totalFiles}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Progress History */}
      {progressHistory.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Progress History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {progressHistory.slice(-5).reverse().map((item, index) => (
                <div key={index} className="flex justify-between text-xs">
                  <span>{item.timestamp.toLocaleTimeString()}</span>
                  <span>{item.progress.toFixed(1)}%</span>
                  <span className="text-gray-500">{item.status}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Component for displaying real-time statistics updates
export function RealTimeStatistics({ userId }: { userId?: string }) {
  const { isConnected } = useWebSocketContext();
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [updateCount, setUpdateCount] = useState(0);

  useEffect(() => {
    if (isConnected) {
      // Subscribe to statistics updates
      // This would be handled by the useRealTimeStatistics hook
      setLastUpdate(new Date());
      setUpdateCount(prev => prev + 1);
    }
  }, [isConnected]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Real-time Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span>Connection:</span>
            <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
              {isConnected ? 'Active' : 'Inactive'}
            </span>
          </div>
          
          <div className="flex justify-between">
            <span>Updates received:</span>
            <span>{updateCount}</span>
          </div>
          
          {lastUpdate && (
            <div className="flex justify-between">
              <span>Last update:</span>
              <span>{lastUpdate.toLocaleTimeString()}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Hook for integrating real-time updates with React Query
export function useRealTimeQueryInvalidation() {
  const { subscribe } = useWebSocketContext();
  
  useEffect(() => {
    // Subscribe to various update types and invalidate relevant queries
    const unsubscribers = [
      subscribe('statistics_update', () => {
        // Invalidate statistics queries
        // This would integrate with React Query's invalidateQueries
        console.log('Statistics updated - invalidating queries');
      }),
      
      subscribe('analysis_update', () => {
        // Invalidate analysis queries
        console.log('Analysis updated - invalidating queries');
      }),
      
      subscribe('file_monitoring', () => {
        // Invalidate file monitoring queries
        console.log('File monitoring updated - invalidating queries');
      }),
    ];

    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe());
    };
  }, [subscribe]);
}