/**
 * Hook for managing educational term linking functionality.
 * 
 * Provides term detection, hover previews, and modal displays for poker terms
 * throughout the application interface.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export interface TermDefinition {
  term: string;
  definition: string;
  explanation?: string;
  source_type: 'encyclopedia' | 'education';
  source_id: string;
  context_appropriate: boolean;
  difficulty_level?: string;
  category?: string;
}

export interface TermLink {
  term: string;
  start_position: number;
  end_position: number;
  definition: TermDefinition;
  confidence: number;
}

export interface LinkedContent {
  original_content: string;
  linked_content: string;
  detected_terms: TermLink[];
  link_count: number;
}

interface LinkContentRequest {
  content: string;
  context?: string;
  max_links?: number;
}

interface TermLookupRequest {
  term: string;
  context?: string;
}

interface HoverState {
  isVisible: boolean;
  term: string;
  definition?: TermDefinition;
  position: { x: number; y: number };
}

interface ModalState {
  isOpen: boolean;
  term: string;
  definition?: TermDefinition;
  relatedTerms: TermDefinition[];
}

/**
 * Main hook for term linking functionality
 */
export function useTermLinking() {
  const queryClient = useQueryClient();
  
  // Link content mutation
  const linkContentMutation = useMutation({
    mutationFn: async (request: LinkContentRequest): Promise<LinkedContent> => {
      const response = await fetch('/api/v1/term-linking/link-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      
      if (!response.ok) {
        throw new Error('Failed to link content');
      }
      
      return response.json();
    },
  });
  
  // Term lookup mutation
  const termLookupMutation = useMutation({
    mutationFn: async (request: TermLookupRequest): Promise<TermDefinition | null> => {
      const response = await fetch('/api/v1/term-linking/lookup-term', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      
      if (!response.ok) {
        throw new Error('Failed to lookup term');
      }
      
      return response.json();
    },
  });
  
  const linkContent = useCallback(
    (content: string, context?: string, maxLinks?: number) => {
      return linkContentMutation.mutateAsync({
        content,
        context,
        max_links: maxLinks,
      });
    },
    [linkContentMutation]
  );
  
  const lookupTerm = useCallback(
    (term: string, context?: string) => {
      return termLookupMutation.mutateAsync({ term, context });
    },
    [termLookupMutation]
  );
  
  return {
    linkContent,
    lookupTerm,
    isLinking: linkContentMutation.isPending,
    isLookingUp: termLookupMutation.isPending,
    linkError: linkContentMutation.error,
    lookupError: termLookupMutation.error,
  };
}

/**
 * Hook for managing term hover previews
 */
export function useTermHover() {
  const [hoverState, setHoverState] = useState<HoverState>({
    isVisible: false,
    term: '',
    position: { x: 0, y: 0 },
  });
  
  const hoverTimeoutRef = useRef<NodeJS.Timeout>();
  const { lookupTerm } = useTermLinking();
  
  const showHover = useCallback(
    async (term: string, x: number, y: number, context?: string) => {
      // Clear any existing timeout
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
      
      // Set loading state
      setHoverState({
        isVisible: true,
        term,
        position: { x, y },
      });
      
      try {
        const definition = await lookupTerm(term, context);
        
        // Only update if we're still hovering the same term
        setHoverState(prev => {
          if (prev.term === term && prev.isVisible) {
            return {
              ...prev,
              definition: definition || undefined,
            };
          }
          return prev;
        });
      } catch (error) {
        console.error('Failed to lookup term:', error);
        // Show fallback tooltip
        setHoverState(prev => ({
          ...prev,
          definition: {
            term,
            definition: `Definition for "${term}" is currently unavailable.`,
            source_type: 'encyclopedia' as const,
            source_id: '',
            context_appropriate: true,
          },
        }));
      }
    },
    [lookupTerm]
  );
  
  const hideHover = useCallback(() => {
    // Delay hiding to allow moving to hover content
    hoverTimeoutRef.current = setTimeout(() => {
      setHoverState({
        isVisible: false,
        term: '',
        position: { x: 0, y: 0 },
      });
    }, 100);
  }, []);
  
  const keepHoverVisible = useCallback(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
  }, []);
  
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);
  
  return {
    hoverState,
    showHover,
    hideHover,
    keepHoverVisible,
  };
}

/**
 * Hook for managing term definition modals
 */
export function useTermModal() {
  const [modalState, setModalState] = useState<ModalState>({
    isOpen: false,
    term: '',
    relatedTerms: [],
  });
  
  const { lookupTerm } = useTermLinking();
  
  // Query for related terms
  const { data: relatedTerms = [] } = useQuery({
    queryKey: ['related-terms', modalState.term],
    queryFn: async () => {
      if (!modalState.term) return [];
      
      const response = await fetch(`/api/v1/term-linking/related-terms/${encodeURIComponent(modalState.term)}?limit=5`);
      if (!response.ok) {
        throw new Error('Failed to fetch related terms');
      }
      
      return response.json() as Promise<TermDefinition[]>;
    },
    enabled: modalState.isOpen && !!modalState.term,
  });
  
  const openModal = useCallback(
    async (term: string, context?: string) => {
      try {
        const definition = await lookupTerm(term, context);
        
        setModalState({
          isOpen: true,
          term,
          definition: definition || undefined,
          relatedTerms: [],
        });
      } catch (error) {
        console.error('Failed to lookup term for modal:', error);
        // Show modal with error state
        setModalState({
          isOpen: true,
          term,
          definition: {
            term,
            definition: `Definition for "${term}" is currently unavailable.`,
            source_type: 'encyclopedia' as const,
            source_id: '',
            context_appropriate: true,
          },
          relatedTerms: [],
        });
      }
    },
    [lookupTerm]
  );
  
  const closeModal = useCallback(() => {
    setModalState({
      isOpen: false,
      term: '',
      relatedTerms: [],
    });
  }, []);
  
  // Update related terms when they're loaded
  useEffect(() => {
    if (relatedTerms.length > 0) {
      setModalState(prev => ({
        ...prev,
        relatedTerms,
      }));
    }
  }, [relatedTerms]);
  
  return {
    modalState,
    openModal,
    closeModal,
  };
}

/**
 * Hook for term suggestions (autocomplete)
 */
export function useTermSuggestions() {
  const [query, setQuery] = useState('');
  
  const { data: suggestions = [], isLoading } = useQuery({
    queryKey: ['term-suggestions', query],
    queryFn: async () => {
      if (!query || query.length < 2) return [];
      
      const response = await fetch(`/api/v1/term-linking/suggestions?partial_term=${encodeURIComponent(query)}&limit=10`);
      if (!response.ok) {
        throw new Error('Failed to fetch term suggestions');
      }
      
      return response.json() as Promise<string[]>;
    },
    enabled: query.length >= 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  return {
    query,
    setQuery,
    suggestions,
    isLoading,
  };
}