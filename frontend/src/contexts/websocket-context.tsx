'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { WebSocketClient, WebSocketState, WebSocketMessageType } from '@/lib/websocket-client';

interface WebSocketContextType {
  client: WebSocketClient | null;
  state: WebSocketState;
  lastMessage: WebSocketMessageType | null;
  connect: () => void;
  disconnect: () => void;
  send: (message: any) => boolean;
  subscribe: (messageType: string, callback: (data: any) => void) => () => void;
  isConnected: boolean;
  isConnecting: boolean;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
  url?: string;
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export function WebSocketProvider({
  children,
  url,
  autoConnect = true,
  onConnect,
  onDisconnect,
  onError,
}: WebSocketProviderProps) {
  const [client, setClient] = useState<WebSocketClient | null>(null);
  const [state, setState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const [lastMessage, setLastMessage] = useState<WebSocketMessageType | null>(null);

  // Initialize WebSocket client
  useEffect(() => {
    const wsClient = new WebSocketClient({
      url,
      onConnect: () => {
        setState(WebSocketState.CONNECTED);
        onConnect?.();
      },
      onDisconnect: () => {
        setState(WebSocketState.DISCONNECTED);
        onDisconnect?.();
      },
      onError: (error) => {
        setState(WebSocketState.ERROR);
        onError?.(error);
      },
      onMessage: (message) => {
        setLastMessage(message);
      },
    });

    setClient(wsClient);

    if (autoConnect) {
      setState(WebSocketState.CONNECTING);
      wsClient.connect();
    }

    return () => {
      wsClient.disconnect();
    };
  }, [url, autoConnect, onConnect, onDisconnect, onError]);

  const connect = () => {
    if (client) {
      setState(WebSocketState.CONNECTING);
      client.connect();
    }
  };

  const disconnect = () => {
    if (client) {
      client.disconnect();
      setState(WebSocketState.DISCONNECTED);
    }
  };

  const send = (message: any): boolean => {
    return client?.send(message) || false;
  };

  const subscribe = (messageType: string, callback: (data: any) => void) => {
    return client?.subscribe(messageType, callback) || (() => {});
  };

  const contextValue: WebSocketContextType = {
    client,
    state,
    lastMessage,
    connect,
    disconnect,
    send,
    subscribe,
    isConnected: state === WebSocketState.CONNECTED,
    isConnecting: state === WebSocketState.CONNECTING,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext(): WebSocketContextType {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}

// Connection status indicator component
export function WebSocketStatus() {
  const { state, isConnected, connect, disconnect } = useWebSocketContext();

  const getStatusColor = () => {
    switch (state) {
      case WebSocketState.CONNECTED:
        return 'text-green-500';
      case WebSocketState.CONNECTING:
        return 'text-yellow-500';
      case WebSocketState.ERROR:
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusText = () => {
    switch (state) {
      case WebSocketState.CONNECTED:
        return 'Connected';
      case WebSocketState.CONNECTING:
        return 'Connecting...';
      case WebSocketState.ERROR:
        return 'Error';
      default:
        return 'Disconnected';
    }
  };

  return (
    <div className="flex items-center space-x-2 text-sm">
      <div className={`w-2 h-2 rounded-full ${getStatusColor().replace('text-', 'bg-')}`} />
      <span className={getStatusColor()}>{getStatusText()}</span>
      {!isConnected && (
        <button
          onClick={connect}
          className="text-blue-500 hover:text-blue-700 underline"
        >
          Reconnect
        </button>
      )}
      {isConnected && (
        <button
          onClick={disconnect}
          className="text-red-500 hover:text-red-700 underline"
        >
          Disconnect
        </button>
      )}
    </div>
  );
}

// Hook for subscribing to specific message types with automatic cleanup
export function useWebSocketSubscription<T = any>(
  messageType: string,
  callback: (data: T) => void,
  dependencies: any[] = []
) {
  const { subscribe } = useWebSocketContext();

  useEffect(() => {
    const unsubscribe = subscribe(messageType, callback);
    return unsubscribe;
  }, [subscribe, messageType, ...dependencies]);
}

// Hook for sending messages with connection state awareness
export function useWebSocketSender() {
  const { send, isConnected } = useWebSocketContext();

  const sendMessage = (message: any): boolean => {
    if (!isConnected) {
      console.warn('Cannot send message: WebSocket not connected');
      return false;
    }
    return send(message);
  };

  return { sendMessage, isConnected };
}