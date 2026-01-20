import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { queryKeys, useInvalidateQueries } from '@/lib/react-query';
import { useWebSocketSubscription } from '@/contexts/websocket-context';

// Types for API responses
export interface User {
  id: string;
  email: string;
  name?: string;
  preferences: Record<string, any>;
  apiKeys: {
    gemini?: string;
    groq?: string;
  };
  handHistoryPaths: {
    pokerstars?: string;
    ggpoker?: string;
  };
}

export interface PokerHand {
  id: string;
  handId: string;
  platform: 'pokerstars' | 'ggpoker';
  gameType: string;
  stakes: string;
  datePlayedAt: string;
  playerCards: string[];
  boardCards: string[];
  position: string;
  result: string;
  potSize: number;
  analysis?: any[];
}

export interface Statistics {
  vpip: number;
  pfr: number;
  aggressionFactor: number;
  winRate: number;
  handsPlayed: number;
  [key: string]: number;
}

export interface FileMonitoringStatus {
  isActive: boolean;
  lastScan?: string;
  filesProcessed: number;
  errors: string[];
}

// User hooks
export function useUserProfile() {
  return useQuery({
    queryKey: queryKeys.user.profile,
    queryFn: async () => {
      const response = await api.users.getProfile();
      return response.data as User;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useUpdateUserProfile() {
  const queryClient = useQueryClient();
  const { invalidateUser } = useInvalidateQueries();

  return useMutation({
    mutationFn: async (data: Partial<User>) => {
      const response = await api.users.updateProfile(data);
      return response.data;
    },
    onSuccess: () => {
      invalidateUser();
    },
    onError: (error) => {
      console.error('Failed to update profile:', error);
    },
  });
}

export function useUpdateUserSettings() {
  const queryClient = useQueryClient();
  const { invalidateUser } = useInvalidateQueries();

  return useMutation({
    mutationFn: async (settings: Record<string, any>) => {
      const response = await api.users.updateSettings(settings);
      return response.data;
    },
    onSuccess: () => {
      invalidateUser();
    },
  });
}

// Hand history hooks
export function useHands(filters?: any) {
  return useQuery({
    queryKey: queryKeys.hands.list(filters),
    queryFn: async () => {
      const response = await api.hands.getHands(filters);
      return response.data as PokerHand[];
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useHand(handId: string) {
  return useQuery({
    queryKey: queryKeys.hands.detail(handId),
    queryFn: async () => {
      const response = await api.hands.getHand(handId);
      return response.data as PokerHand;
    },
    enabled: !!handId,
  });
}

export function useUploadHandHistory() {
  const { invalidateHands, invalidateStatistics } = useInvalidateQueries();

  return useMutation({
    mutationFn: async ({ 
      file, 
      onProgress 
    }: { 
      file: File; 
      onProgress?: (progress: number) => void;
    }) => {
      const response = await api.hands.uploadFile(file, onProgress);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate hands and statistics after successful upload
      invalidateHands();
      invalidateStatistics();
    },
  });
}

export function useBatchUploadHandHistory() {
  const { invalidateHands, invalidateStatistics } = useInvalidateQueries();

  return useMutation({
    mutationFn: async (files: File[]) => {
      const response = await api.hands.batchUpload(files);
      return response.data;
    },
    onSuccess: () => {
      invalidateHands();
      invalidateStatistics();
    },
  });
}

// Statistics hooks with real-time updates
export function useBasicStatistics(filters?: any) {
  const queryClient = useQueryClient();
  
  // Subscribe to real-time statistics updates
  useWebSocketSubscription('statistics_update', (data: any) => {
    // Update the cache with real-time data
    queryClient.setQueryData(queryKeys.statistics.basic(filters), data.statistics);
  }, [filters]);

  return useQuery({
    queryKey: queryKeys.statistics.basic(filters),
    queryFn: async () => {
      const response = await api.statistics.getBasicStats(filters);
      return response.data as Statistics;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useAdvancedStatistics(filters?: any) {
  const queryClient = useQueryClient();
  
  useWebSocketSubscription('statistics_update', (data: any) => {
    queryClient.setQueryData(queryKeys.statistics.advanced(filters), data.statistics);
  }, [filters]);

  return useQuery({
    queryKey: queryKeys.statistics.advanced(filters),
    queryFn: async () => {
      const response = await api.statistics.getAdvancedStats(filters);
      return response.data as Statistics;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useStatisticsTrends(period: string, filters?: any) {
  const queryClient = useQueryClient();
  
  useWebSocketSubscription('statistics_update', (data: any) => {
    // Invalidate trends when statistics update
    queryClient.invalidateQueries({ queryKey: queryKeys.statistics.trends(period, filters) });
  }, [period, filters]);

  return useQuery({
    queryKey: queryKeys.statistics.trends(period, filters),
    queryFn: async () => {
      const response = await api.statistics.getTrends(period, filters);
      return response.data;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes for trends
  });
}

export function usePositionalStatistics(filters?: any) {
  const queryClient = useQueryClient();
  
  useWebSocketSubscription('statistics_update', (data: any) => {
    queryClient.setQueryData(queryKeys.statistics.positional(filters), data.statistics);
  }, [filters]);

  return useQuery({
    queryKey: queryKeys.statistics.positional(filters),
    queryFn: async () => {
      const response = await api.statistics.getPositionalStats(filters);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useExportStatistics() {
  return useMutation({
    mutationFn: async ({ 
      format, 
      filters 
    }: { 
      format: 'csv' | 'pdf'; 
      filters?: any;
    }) => {
      const response = await api.statistics.exportStats(format, filters);
      
      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `poker-statistics.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      return response.data;
    },
  });
}

// AI Analysis hooks
export function useAnalyzeHand() {
  const { invalidateAnalysis } = useInvalidateQueries();

  return useMutation({
    mutationFn: async ({ 
      handId, 
      provider, 
      options 
    }: { 
      handId: string; 
      provider: 'gemini' | 'groq'; 
      options?: any;
    }) => {
      const response = await api.analysis.analyzeHand(handId, provider, options);
      return response.data;
    },
    onSuccess: () => {
      invalidateAnalysis();
    },
  });
}

export function useAnalyzeSession() {
  const { invalidateAnalysis } = useInvalidateQueries();

  return useMutation({
    mutationFn: async ({ 
      handIds, 
      provider, 
      options 
    }: { 
      handIds: string[]; 
      provider: 'gemini' | 'groq'; 
      options?: any;
    }) => {
      const response = await api.analysis.analyzeSession(handIds, provider, options);
      return response.data;
    },
    onSuccess: () => {
      invalidateAnalysis();
    },
  });
}

export function useAnalysis(analysisId: string) {
  return useQuery({
    queryKey: queryKeys.analysis.detail(analysisId),
    queryFn: async () => {
      const response = await api.analysis.getAnalysis(analysisId);
      return response.data;
    },
    enabled: !!analysisId,
  });
}

export function useAnalysisHistory(params?: any) {
  return useQuery({
    queryKey: queryKeys.analysis.history(params),
    queryFn: async () => {
      const response = await api.analysis.getAnalysisHistory(params);
      return response.data;
    },
    staleTime: 2 * 60 * 1000,
  });
}

// File monitoring hooks with real-time updates
export function useFileMonitoringStatus() {
  const queryClient = useQueryClient();
  
  // Subscribe to real-time file monitoring updates
  useWebSocketSubscription('file_monitoring', (data: any) => {
    // Update the status cache with real-time data
    queryClient.invalidateQueries({ queryKey: queryKeys.fileMonitoring.status });
    queryClient.invalidateQueries({ queryKey: queryKeys.fileMonitoring.progress });
  });

  return useQuery({
    queryKey: queryKeys.fileMonitoring.status,
    queryFn: async () => {
      const response = await api.fileMonitoring.getStatus();
      return response.data as FileMonitoringStatus;
    },
    refetchInterval: 5000, // Fallback polling every 5 seconds
    staleTime: 0, // Always consider stale for real-time updates
  });
}

export function useFileMonitoringProgress() {
  const queryClient = useQueryClient();
  
  useWebSocketSubscription('progress', (data: any) => {
    // Update progress cache with real-time data
    queryClient.setQueryData(queryKeys.fileMonitoring.progress, data);
  });

  return useQuery({
    queryKey: queryKeys.fileMonitoring.progress,
    queryFn: async () => {
      const response = await api.fileMonitoring.getProgress();
      return response.data;
    },
    refetchInterval: 2000, // Fallback polling every 2 seconds
    staleTime: 0,
  });
}

export function useStartFileMonitoring() {
  const { invalidateFileMonitoring } = useInvalidateQueries();

  return useMutation({
    mutationFn: async (paths: { pokerstars?: string; ggpoker?: string }) => {
      const response = await api.fileMonitoring.startMonitoring(paths);
      return response.data;
    },
    onSuccess: () => {
      invalidateFileMonitoring();
    },
  });
}

export function useStopFileMonitoring() {
  const { invalidateFileMonitoring } = useInvalidateQueries();

  return useMutation({
    mutationFn: async () => {
      const response = await api.fileMonitoring.stopMonitoring();
      return response.data;
    },
    onSuccess: () => {
      invalidateFileMonitoring();
    },
  });
}

// Education hooks
export function useEducationContent(params?: any) {
  return useQuery({
    queryKey: queryKeys.education.content(params),
    queryFn: async () => {
      const response = await api.education.getContent(params);
      return response.data;
    },
    staleTime: 30 * 60 * 1000, // 30 minutes - education content doesn't change often
  });
}

export function useEducationContentById(contentId: string) {
  return useQuery({
    queryKey: queryKeys.education.detail(contentId),
    queryFn: async () => {
      const response = await api.education.getContentById(contentId);
      return response.data;
    },
    enabled: !!contentId,
    staleTime: 30 * 60 * 1000,
  });
}

export function useSearchEducationContent(query: string, filters?: any) {
  return useQuery({
    queryKey: queryKeys.education.search(query, filters),
    queryFn: async () => {
      const response = await api.education.searchContent(query, filters);
      return response.data;
    },
    enabled: !!query && query.length > 2, // Only search if query is at least 3 characters
    staleTime: 10 * 60 * 1000,
  });
}

export function useEducationCategories() {
  return useQuery({
    queryKey: queryKeys.education.categories,
    queryFn: async () => {
      const response = await api.education.getCategories();
      return response.data;
    },
    staleTime: 60 * 60 * 1000, // 1 hour - categories rarely change
  });
}