export interface Toast {
  title: string
  description?: string
  variant?: "default" | "destructive"
}

export function useToast() {
  const toast = (toastData: Toast) => {
    // In a real implementation, this would show a toast notification
    console.log('Toast:', toastData)
  }

  return { toast }
}