/**
 * Term Linked Content Component
 * 
 * Automatically detects and links poker terms in content, providing hover
 * previews and modal displays for educational definitions.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useTermLinking, useTermHover, useTermModal } from '@/hooks/use-term-linking';
import { TermHoverPreview, TermTooltip } from './term-hover-preview';
import { TermDefinitionModal } from './term-definition-modal';
import { useRouter } from 'next/navigation';

interface TermLinkedContentProps {
  content: string;
  context?: string;
  maxLinks?: number;
  className?: string;
  enableHover?: boolean;
  enableModal?: boolean;
  fallbackToTooltip?: boolean;
}

export function TermLinkedContent({
  content,
  context,
  maxLinks = 10,
  className = '',
  enableHover = true,
  enableModal = true,
  fallbackToTooltip = true,
}: TermLinkedContentProps) {
  const [linkedContent, setLinkedContent] = useState<string>(content);
  const [isProcessed, setIsProcessed] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  
  const { linkContent, isLinking } = useTermLinking();
  const { hoverState, showHover, hideHover, keepHoverVisible } = useTermHover();
  const { modalState, openModal, closeModal } = useTermModal();

  // Process content for term linking
  useEffect(() => {
    const processContent = async () => {
      if (!content || content.trim().length === 0) {
        setLinkedContent(content);
        setIsProcessed(true);
        return;
      }

      try {
        const result = await linkContent(content, context, maxLinks);
        setLinkedContent(result.linked_content);
        setIsProcessed(true);
      } catch (error) {
        console.error('Failed to process content for term linking:', error);
        // Graceful degradation - show original content
        setLinkedContent(content);
        setIsProcessed(true);
      }
    };

    setIsProcessed(false);
    processContent();
  }, [content, context, maxLinks, linkContent]);

  // Set up event listeners for term interactions
  useEffect(() => {
    if (!contentRef.current || !isProcessed) return;

    const handleTermHover = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      
      if (target.classList.contains('poker-term-link')) {
        if (enableHover) {
          const term = target.getAttribute('data-term') || target.textContent || '';
          const rect = target.getBoundingClientRect();
          showHover(term, rect.left, rect.bottom, context);
        } else if (fallbackToTooltip) {
          // Show simple tooltip as fallback
          const term = target.getAttribute('data-term') || target.textContent || '';
          const rect = target.getBoundingClientRect();
          showHover(term, rect.left, rect.bottom, context);
        }
      }
    };

    const handleTermLeave = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      
      if (target.classList.contains('poker-term-link')) {
        hideHover();
      }
    };

    const handleTermClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      
      if (target.classList.contains('poker-term-link')) {
        event.preventDefault();
        
        if (enableModal) {
          const term = target.getAttribute('data-term') || target.textContent || '';
          openModal(term, context);
        }
      }
    };

    const element = contentRef.current;
    element.addEventListener('mouseover', handleTermHover);
    element.addEventListener('mouseleave', handleTermLeave);
    element.addEventListener('click', handleTermClick);

    return () => {
      element.removeEventListener('mouseover', handleTermHover);
      element.removeEventListener('mouseleave', handleTermLeave);
      element.removeEventListener('click', handleTermClick);
    };
  }, [isProcessed, enableHover, enableModal, fallbackToTooltip, showHover, hideHover, openModal, context]);

  const handleViewSource = useCallback((sourceType: string, sourceId: string) => {
    if (sourceType === 'encyclopedia') {
      router.push(`/encyclopedia/${sourceId}`);
    } else if (sourceType === 'education') {
      router.push(`/education?content=${sourceId}`);
    }
    closeModal();
  }, [router, closeModal]);

  const handleModalTermClick = useCallback((term: string) => {
    openModal(term, context);
  }, [openModal, context]);

  if (!isProcessed && isLinking) {
    return (
      <div className={`${className} relative`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
        <div className="absolute inset-0 flex items-center justify-center bg-white/50">
          <div className="text-xs text-gray-500">Processing terms...</div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div
        ref={contentRef}
        className={`${className} term-linked-content`}
        dangerouslySetInnerHTML={{ __html: linkedContent }}
        style={{
          // CSS for term links
          '--term-link-color': '#2563eb',
          '--term-link-hover-color': '#1d4ed8',
        } as React.CSSProperties}
      />
      
      {/* Hover Preview */}
      {enableHover && (
        <TermHoverPreview
          isVisible={hoverState.isVisible}
          term={hoverState.term}
          definition={hoverState.definition}
          position={hoverState.position}
          onMouseEnter={keepHoverVisible}
          onMouseLeave={hideHover}
          onViewDetails={enableModal ? openModal : undefined}
        />
      )}
      
      {/* Fallback Tooltip */}
      {!enableHover && fallbackToTooltip && (
        <TermTooltip
          isVisible={hoverState.isVisible}
          term={hoverState.term}
          position={hoverState.position}
        />
      )}
      
      {/* Definition Modal */}
      {enableModal && (
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
      
      <style jsx>{`
        .term-linked-content :global(.poker-term-link) {
          color: var(--term-link-color);
          text-decoration: underline;
          text-decoration-style: dotted;
          cursor: pointer;
          transition: color 0.2s ease;
        }
        
        .term-linked-content :global(.poker-term-link:hover) {
          color: var(--term-link-hover-color);
          text-decoration-style: solid;
        }
        
        .term-linked-content :global(.poker-term-link:focus) {
          outline: 2px solid var(--term-link-color);
          outline-offset: 2px;
          border-radius: 2px;
        }
      `}</style>
    </>
  );
}

/**
 * Simplified version for basic term linking without hover/modal features
 */
interface SimpleTermLinkedContentProps {
  content: string;
  context?: string;
  maxLinks?: number;
  className?: string;
  onTermClick?: (term: string) => void;
}

export function SimpleTermLinkedContent({
  content,
  context,
  maxLinks = 5,
  className = '',
  onTermClick,
}: SimpleTermLinkedContentProps) {
  const [linkedContent, setLinkedContent] = useState<string>(content);
  const contentRef = useRef<HTMLDivElement>(null);
  
  const { linkContent, isLinking } = useTermLinking();

  useEffect(() => {
    const processContent = async () => {
      if (!content || content.trim().length === 0) {
        setLinkedContent(content);
        return;
      }

      try {
        const result = await linkContent(content, context, maxLinks);
        setLinkedContent(result.linked_content);
      } catch (error) {
        console.error('Failed to process content for term linking:', error);
        setLinkedContent(content);
      }
    };

    processContent();
  }, [content, context, maxLinks, linkContent]);

  useEffect(() => {
    if (!contentRef.current || !onTermClick) return;

    const handleTermClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      
      if (target.classList.contains('poker-term-link')) {
        event.preventDefault();
        const term = target.getAttribute('data-term') || target.textContent || '';
        onTermClick(term);
      }
    };

    const element = contentRef.current;
    element.addEventListener('click', handleTermClick);

    return () => {
      element.removeEventListener('click', handleTermClick);
    };
  }, [onTermClick]);

  if (isLinking) {
    return (
      <div className={`${className} animate-pulse`}>
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
    );
  }

  return (
    <div
      ref={contentRef}
      className={`${className} simple-term-linked-content`}
      dangerouslySetInnerHTML={{ __html: linkedContent }}
    />
  );
}