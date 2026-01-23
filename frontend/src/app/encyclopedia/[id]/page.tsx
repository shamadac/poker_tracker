'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, BookOpen, Clock, User, ExternalLink, Share2 } from 'lucide-react';

interface EncyclopediaEntry {
  id: string;
  title: string;
  content: string;
  status: 'draft' | 'published' | 'archived';
  ai_provider: string;
  created_by: string;
  approved_by?: string;
  published_at?: string;
  created_at: string;
  updated_at: string;
  source_links?: EncyclopediaLink[];
  target_links?: EncyclopediaLink[];
}

interface EncyclopediaLink {
  id: string;
  source_entry_id: string;
  target_entry_id: string;
  anchor_text: string;
  context?: string;
  created_at: string;
}

interface RelatedEntry {
  id: string;
  title: string;
}

export default function EncyclopediaEntryPage() {
  const params = useParams();
  const router = useRouter();
  const [entry, setEntry] = useState<EncyclopediaEntry | null>(null);
  const [relatedEntries, setRelatedEntries] = useState<RelatedEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  const entryId = params.id as string;

  useEffect(() => {
    if (entryId) {
      loadEntry();
    }
  }, [entryId]);

  const loadEntry = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/v1/encyclopedia/entries/${entryId}`);
      
      if (response.ok) {
        const data = await response.json();
        setEntry(data);
        
        // Load related entries based on links
        if (data.source_links && data.source_links.length > 0) {
          loadRelatedEntries(data.source_links);
        }
      } else if (response.status === 404) {
        toast({
          title: 'Entry Not Found',
          description: 'The encyclopedia entry you are looking for does not exist.',
          variant: 'destructive'
        });
        router.push('/encyclopedia');
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load encyclopedia entry',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load encyclopedia entry',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadRelatedEntries = async (links: EncyclopediaLink[]) => {
    try {
      // Get unique target entry IDs
      const targetIds = [...new Set(links.map(link => link.target_entry_id))];
      
      // For now, we'll create mock related entries
      // In a full implementation, you'd fetch the actual entries
      const related = targetIds.slice(0, 5).map((id, index) => ({
        id,
        title: `Related Topic ${index + 1}`
      }));
      
      setRelatedEntries(related);
    } catch (error) {
      console.error('Failed to load related entries:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const shareEntry = async () => {
    if (navigator.share && entry) {
      try {
        await navigator.share({
          title: entry.title,
          text: `Check out this poker encyclopedia entry: ${entry.title}`,
          url: window.location.href
        });
      } catch (error) {
        // Fallback to copying URL
        copyToClipboard();
      }
    } else {
      copyToClipboard();
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      toast({
        title: 'Link Copied',
        description: 'Encyclopedia entry link copied to clipboard'
      });
    });
  };

  const renderContentWithLinks = (content: string, links?: EncyclopediaLink[]) => {
    if (!links || links.length === 0) {
      return <div className="prose prose-lg max-w-none" dangerouslySetInnerHTML={{ __html: content.replace(/\n/g, '<br />') }} />;
    }

    // For now, return content as-is
    // In a full implementation, you'd replace anchor text with actual links
    return <div className="prose prose-lg max-w-none" dangerouslySetInnerHTML={{ __html: content.replace(/\n/g, '<br />') }} />;
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading encyclopedia entry...</p>
        </div>
      </div>
    );
  }

  if (!entry) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="text-center py-12">
            <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Entry Not Found</h3>
            <p className="text-muted-foreground mb-4">
              The encyclopedia entry you are looking for does not exist or is not available.
            </p>
            <Link href="/encyclopedia">
              <Button>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Encyclopedia
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Navigation */}
      <div className="flex items-center space-x-2 text-sm text-muted-foreground">
        <Link href="/encyclopedia" className="hover:text-primary transition-colors">
          Encyclopedia
        </Link>
        <span>/</span>
        <span className="text-foreground">{entry.title}</span>
      </div>

      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h1 className="text-4xl font-bold mb-4">{entry.title}</h1>
          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
            <div className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>Published {formatDate(entry.published_at || entry.created_at)}</span>
            </div>
            <Separator orientation="vertical" className="h-4" />
            <Badge variant="outline">
              {entry.ai_provider.toUpperCase()}
            </Badge>
          </div>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={shareEntry}>
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
          <Link href="/encyclopedia">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-3">
          <Card>
            <CardContent className="p-8">
              {renderContentWithLinks(entry.content, entry.source_links)}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Entry Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Entry Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Status</p>
                <Badge variant={entry.status === 'published' ? 'default' : 'secondary'}>
                  {entry.status.charAt(0).toUpperCase() + entry.status.slice(1)}
                </Badge>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">AI Provider</p>
                <p className="text-sm">{entry.ai_provider.toUpperCase()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Created</p>
                <p className="text-sm">{formatDate(entry.created_at)}</p>
              </div>
              {entry.updated_at !== entry.created_at && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
                  <p className="text-sm">{formatDate(entry.updated_at)}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Related Entries */}
          {relatedEntries.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Related Topics</CardTitle>
                <CardDescription>
                  Explore connected concepts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {relatedEntries.map((related) => (
                  <Link
                    key={related.id}
                    href={`/encyclopedia/${related.id}`}
                    className="block p-2 rounded hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{related.title}</span>
                      <ExternalLink className="h-3 w-3 text-muted-foreground" />
                    </div>
                  </Link>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start" onClick={shareEntry}>
                <Share2 className="h-4 w-4 mr-2" />
                Share Entry
              </Button>
              <Link href="/encyclopedia" className="block">
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <BookOpen className="h-4 w-4 mr-2" />
                  Browse Encyclopedia
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}