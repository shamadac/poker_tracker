"use client"

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { ServiceStatus } from '@/lib/error-handling';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface ServiceStatusBannerProps {
  className?: string;
}

export function ServiceStatusBanner({ className = '' }: ServiceStatusBannerProps) {
  const [dismissed, setDismissed] = useState<string[]>([]);
  
  // Query system health status
  const { data: healthStatus, isError } = useQuery({
    queryKey: ['system', 'health'],
    queryFn: async () => {
      const response = await api.system.getHealth();
      return response.data as ServiceStatus & { status: string; timestamp: string; version: string };
    },
    refetchInterval: 30000, // Check every 30 seconds
    retry: 1, // Don't retry too aggressively for health checks
  });

  // Reset dismissed warnings when health status changes
  useEffect(() => {
    if (healthStatus?.overall_health === 'healthy') {
      setDismissed([]);
    }
  }, [healthStatus?.overall_health]);

  if (isError || !healthStatus) {
    return (
      <div className={`bg-red-50 border-l-4 border-red-400 p-4 ${className}`}>
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">
              Unable to check system status. Some features may be unavailable.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Don't show banner if system is healthy
  if (healthStatus.overall_health === 'healthy') {
    return null;
  }

  // Generate warning messages for degraded features
  const warnings = generateWarningMessages(healthStatus);
  const visibleWarnings = warnings.filter(warning => !dismissed.includes(warning.id));

  if (visibleWarnings.length === 0) {
    return null;
  }

  return (
    <div className={className}>
      {visibleWarnings.map((warning) => (
        <Card key={warning.id} className={`mb-2 border-l-4 ${warning.borderColor} ${warning.bgColor}`}>
          <CardContent className="p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <warning.icon className={`h-5 w-5 ${warning.iconColor}`} />
              </div>
              <div className="ml-3 flex-1">
                <h3 className={`text-sm font-medium ${warning.textColor}`}>
                  {warning.title}
                </h3>
                <p className={`mt-1 text-sm ${warning.descriptionColor}`}>
                  {warning.description}
                </p>
                {warning.actions && warning.actions.length > 0 && (
                  <div className="mt-2">
                    <ul className={`text-xs ${warning.descriptionColor} list-disc list-inside`}>
                      {warning.actions.map((action, index) => (
                        <li key={index}>{action}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <div className="ml-3 flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDismissed([...dismissed, warning.id])}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

interface Warning {
  id: string;
  title: string;
  description: string;
  actions?: string[];
  severity: 'low' | 'medium' | 'high';
  icon: React.ComponentType<{ className?: string }>;
  bgColor: string;
  borderColor: string;
  textColor: string;
  iconColor: string;
  descriptionColor: string;
}

function generateWarningMessages(healthStatus: ServiceStatus & { status: string }): Warning[] {
  const warnings: Warning[] = [];
  const services = healthStatus.services;
  const degradedFeatures = healthStatus.degraded_features || [];

  // Database issues
  if (!services.database) {
    warnings.push({
      id: 'database-down',
      title: 'Database Unavailable',
      description: 'The database is currently unavailable. You cannot save or load data.',
      actions: [
        'Try refreshing the page',
        'Check back in a few minutes',
        'Contact support if the issue persists'
      ],
      severity: 'high',
      icon: DatabaseIcon,
      bgColor: 'bg-red-50',
      borderColor: 'border-red-400',
      textColor: 'text-red-800',
      iconColor: 'text-red-400',
      descriptionColor: 'text-red-700'
    });
  }

  // Redis/Caching issues
  if (!services.redis) {
    warnings.push({
      id: 'cache-down',
      title: 'Reduced Performance Mode',
      description: 'Caching is temporarily unavailable. The system will work but may be slower than usual.',
      severity: 'low',
      icon: SpeedIcon,
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-400',
      textColor: 'text-yellow-800',
      iconColor: 'text-yellow-400',
      descriptionColor: 'text-yellow-700'
    });
  }

  // AI Provider issues
  const aiProviders = services.ai_providers || {};
  const downProviders = Object.entries(aiProviders)
    .filter(([_, isUp]) => !isUp)
    .map(([provider]) => provider);

  if (downProviders.length > 0) {
    const allDown = downProviders.length === Object.keys(aiProviders).length;
    
    warnings.push({
      id: 'ai-providers-down',
      title: allDown ? 'AI Analysis Unavailable' : 'Some AI Providers Unavailable',
      description: allDown 
        ? 'AI analysis is temporarily unavailable. Manual analysis is still available.'
        : `${downProviders.join(', ')} AI provider${downProviders.length > 1 ? 's are' : ' is'} temporarily unavailable.`,
      actions: allDown ? [
        'Try again later',
        'Use manual analysis features',
        'Check our status page for updates'
      ] : [
        'Try using a different AI provider',
        'Check back later for restored service'
      ],
      severity: allDown ? 'medium' : 'low',
      icon: BrainIcon,
      bgColor: allDown ? 'bg-orange-50' : 'bg-yellow-50',
      borderColor: allDown ? 'border-orange-400' : 'border-yellow-400',
      textColor: allDown ? 'text-orange-800' : 'text-yellow-800',
      iconColor: allDown ? 'text-orange-400' : 'text-yellow-400',
      descriptionColor: allDown ? 'text-orange-700' : 'text-yellow-700'
    });
  }

  // File monitoring issues
  if (!services.file_monitoring) {
    warnings.push({
      id: 'file-monitoring-down',
      title: 'Auto-Import Unavailable',
      description: 'Automatic file monitoring is temporarily unavailable. You can still upload files manually.',
      actions: [
        'Use the manual file upload feature',
        'Check back later for automatic monitoring'
      ],
      severity: 'low',
      icon: FolderIcon,
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-400',
      textColor: 'text-blue-800',
      iconColor: 'text-blue-400',
      descriptionColor: 'text-blue-700'
    });
  }

  return warnings;
}

// Icon components
function DatabaseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
    </svg>
  );
}

function SpeedIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}

function BrainIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>
  );
}