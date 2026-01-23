/**
 * Term Linking Context Provider
 * 
 * Provides global term linking functionality and configuration
 * throughout the application.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { useTermLinking, useTermHover, useTermModal, TermDefinition } from '@/hooks/use-term-linking';
import { TermHoverPreview } from '@/components/ui/term-hover-preview';
import { TermDefinitionModal } from '@/components/ui/term-definition-modal';
import { useRouter } from 'next/navigation';

interface TermLinkingConfig {
  enableHover: boolean;
  enableModal: boolean;
  fallbackToTooltip: boolean;
  maxLinksPerContent: number;
  hoverDelay: number;
}

interface TermLinkingContextValue {
  config: TermLinkingConfig;
  updateConfig: (updates: Partial<TermLinkingConfig>) => void;
  showTermDefinition: (term: string, context?: string) => void;
  refreshTermCache: () => Promise<void>;
  isEnabled: boolean;
  setIsEnabled: (enabled: boolean) => void;
}

const TermLinkingContext = createContext<TermLinkingContextValue | undefined>(undefined);

interface TermLinkingProviderProps {
  children: ReactNode;
  defaultConfig?: Partial<TermLinkingConfig>;
}

const defaultTermLinkingConfig: TermLinkingConfig = {
  enableHover: true,
  enableModal: true,
  fallbackToTooltip: true,
  maxLinksPerContent: 10,
  hoverDelay: 300,
};

export function TermLinkingProvider({ 
  children, 
  defaultConfig = {} 
}: TermLinkingProviderProps) {
  const [config, setConfig] = useState<TermLinkingConfig>({
    ...defaultTermLinkingConfig,
    ...defaultConfig,
  });
  const [isEnabled, setIsEnabled] = useState(true);
  
  const router = useRouter();
  const { hoverState, showHover, hideHover, keepHoverVisible } = useTermHover();
  const { modalState, openModal, closeModal } = useTermModal();

  const updateConfig = useCallback((updates: Partial<TermLinkingConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  }, []);

  const showTermDefinition = useCallback((term: string, context?: string) => {
    if (config.enableModal) {
      openModal(term, context);
    }
  }, [config.enableModal, openModal]);

  const refreshTermCache = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/term-linking/refresh-cache', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to refresh term cache');
      }
      
      console.log('Term cache refreshed successfully');
    } catch (error) {
      console.error('Failed to refresh term cache:', error);
      throw error;
    }
  }, []);

  const handleViewSource = useCallback((sourceType: string, sourceId: string) => {
    if (sourceType === 'encyclopedia') {
      router.push(`/encyclopedia/${sourceId}`);
    } else if (sourceType === 'education') {
      router.push(`/education?content=${sourceId}`);
    }
    closeModal();
  }, [router, closeModal]);

  const handleModalTermClick = useCallback((term: string) => {
    openModal(term);
  }, [openModal]);

  const contextValue: TermLinkingContextValue = {
    config,
    updateConfig,
    showTermDefinition,
    refreshTermCache,
    isEnabled,
    setIsEnabled,
  };

  return (
    <TermLinkingContext.Provider value={contextValue}>
      {children}
      
      {/* Global Hover Preview */}
      {isEnabled && config.enableHover && (
        <TermHoverPreview
          isVisible={hoverState.isVisible}
          term={hoverState.term}
          definition={hoverState.definition}
          position={hoverState.position}
          onMouseEnter={keepHoverVisible}
          onMouseLeave={hideHover}
          onViewDetails={config.enableModal ? openModal : undefined}
        />
      )}
      
      {/* Global Definition Modal */}
      {isEnabled && config.enableModal && (
        <TermDefinitionModal
          isOpen={modalState.isOpen}
          term={modalState.term}
          definition={modalState.definition}
          relatedTerms={modalState.relatedTerms}
          onClose={closeModal}
          onTermClick={handleModalTermClick}
          onViewSource={handleViewSource}
        />
      )}
    </TermLinkingContext.Provider>
  );
}

export function useTermLinkingContext() {
  const context = useContext(TermLinkingContext);
  if (context === undefined) {
    throw new Error('useTermLinkingContext must be used within a TermLinkingProvider');
  }
  return context;
}

/**
 * Hook for components that want to integrate with global term linking
 */
export function useGlobalTermLinking() {
  const context = useTermLinkingContext();
  const { showHover, hideHover } = useTermHover();
  
  const handleTermHover = useCallback((
    term: string, 
    x: number, 
    y: number, 
    termContext?: string
  ) => {
    if (context.isEnabled && context.config.enableHover) {
      showHover(term, x, y, termContext);
    }
  }, [context.isEnabled, context.config.enableHover, showHover]);
  
  const handleTermClick = useCallback((term: string, termContext?: string) => {
    if (context.isEnabled) {
      context.showTermDefinition(term, termContext);
    }
  }, [context]);
  
  const handleTermLeave = useCallback(() => {
    if (context.isEnabled && context.config.enableHover) {
      hideHover();
    }
  }, [context.isEnabled, context.config.enableHover, hideHover]);
  
  return {
    config: context.config,
    isEnabled: context.isEnabled,
    handleTermHover,
    handleTermClick,
    handleTermLeave,
    showTermDefinition: context.showTermDefinition,
  };
}

/**
 * Settings component for term linking configuration
 */
export function TermLinkingSettings() {
  const { config, updateConfig, isEnabled, setIsEnabled } = useTermLinkingContext();
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">Enable Term Linking</label>
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => setIsEnabled(e.target.checked)}
          className="rounded border-gray-300"
        />
      </div>
      
      {isEnabled && (
        <>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Hover Previews</label>
            <input
              type="checkbox"
              checked={config.enableHover}
              onChange={(e) => updateConfig({ enableHover: e.target.checked })}
              className="rounded border-gray-300"
            />
          </div>
          
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Definition Modals</label>
            <input
              type="checkbox"
              checked={config.enableModal}
              onChange={(e) => updateConfig({ enableModal: e.target.checked })}
              className="rounded border-gray-300"
            />
          </div>
          
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Fallback Tooltips</label>
            <input
              type="checkbox"
              checked={config.fallbackToTooltip}
              onChange={(e) => updateConfig({ fallbackToTooltip: e.target.checked })}
              className="rounded border-gray-300"
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium">Max Links Per Content</label>
            <input
              type="range"
              min="1"
              max="20"
              value={config.maxLinksPerContent}
              onChange={(e) => updateConfig({ maxLinksPerContent: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="text-xs text-gray-500 text-center">
              {config.maxLinksPerContent} links
            </div>
          </div>
        </>
      )}
    </div>
  );
}