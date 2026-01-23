/**
 * Term Hover Preview Component
 * 
 * Displays a hover preview with term definitions when users hover over
 * linked poker terms throughout the interface.
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { Badge } from './badge';
import { Button } from './button';
import { ExternalLink, BookOpen, GraduationCap } from 'lucide-react';
import { TermDefinition } from '@/hooks/use-term-linking';

interface TermHoverPreviewProps {
  isVisible: boolean;
  term: string;
  definition?: TermDefinition;
  position: { x: number; y: number };
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
  onViewDetails?: (term: string) => void;
}

export function TermHoverPreview({
  isVisible,
  term,
  definition,
  position,
  onMouseEnter,
  onMouseLeave,
  onViewDetails,
}: TermHoverPreviewProps) {
  if (!isVisible) {
    return null;
  }

  // Calculate position to keep preview on screen
  const previewWidth = 320;
  const previewHeight = 200;
  const padding = 16;
  
  const adjustedX = Math.min(
    position.x,
    window.innerWidth - previewWidth - padding
  );
  const adjustedY = Math.min(
    position.y + 20, // Offset below cursor
    window.innerHeight - previewHeight - padding
  );

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'encyclopedia':
        return <BookOpen className="h-4 w-4" />;
      case 'education':
        return <GraduationCap className="h-4 w-4" />;
      default:
        return <BookOpen className="h-4 w-4" />;
    }
  };

  const getDifficultyColor = (difficulty?: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'advanced':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div
      className="fixed z-50 pointer-events-auto"
      style={{
        left: adjustedX,
        top: adjustedY,
        width: previewWidth,
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <Card className="shadow-lg border-2 bg-white/95 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg font-semibold text-gray-900">
                {term}
              </CardTitle>
              <div className="flex items-center gap-2 mt-1">
                {definition && (
                  <>
                    <Badge
                      variant="outline"
                      className="text-xs flex items-center gap-1"
                    >
                      {getSourceIcon(definition.source_type)}
                      {definition.source_type}
                    </Badge>
                    {definition.difficulty_level && (
                      <Badge
                        className={`text-xs ${getDifficultyColor(definition.difficulty_level)}`}
                      >
                        {definition.difficulty_level}
                      </Badge>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="pt-0">
          {definition ? (
            <div className="space-y-3">
              <CardDescription className="text-sm leading-relaxed">
                {definition.definition}
              </CardDescription>
              
              {definition.category && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Category:</span>
                  <Badge variant="secondary" className="text-xs">
                    {definition.category.replace('_', ' ')}
                  </Badge>
                </div>
              )}
              
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="text-xs text-muted-foreground">
                  Click for full details
                </span>
                {onViewDetails && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onViewDetails(term)}
                    className="h-7 px-2 text-xs"
                  >
                    <ExternalLink className="h-3 w-3 mr-1" />
                    View
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              </div>
              <CardDescription className="text-center text-xs">
                Loading definition...
              </CardDescription>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Fallback tooltip component for when full definitions are unavailable
 */
interface TermTooltipProps {
  isVisible: boolean;
  term: string;
  position: { x: number; y: number };
}

export function TermTooltip({ isVisible, term, position }: TermTooltipProps) {
  if (!isVisible) {
    return null;
  }

  return (
    <div
      className="fixed z-40 pointer-events-none"
      style={{
        left: position.x,
        top: position.y + 20,
      }}
    >
      <div className="bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg max-w-xs">
        Poker term: {term}
        <br />
        <span className="text-gray-300">Click for definition</span>
      </div>
    </div>
  );
}