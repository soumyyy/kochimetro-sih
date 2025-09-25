import { useState, useEffect } from 'react'
import { clsx } from 'clsx'
import { X, CheckCircle, AlertTriangle, Info, AlertCircle } from 'lucide-react'

interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

interface ToasterProps {
  toasts?: Toast[]
}

const iconMap = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
}

const colorMap = {
  success: 'text-green-600',
  error: 'text-red-600',
  warning: 'text-yellow-600',
  info: 'text-blue-600',
}

export function Toaster({ toasts }: ToasterProps) {
  const [visibleToasts, setVisibleToasts] = useState<Toast[]>(toasts ?? [])

  useEffect(() => {
    if (toasts === undefined) return
    setVisibleToasts(toasts)
  }, [toasts])

  const removeToast = (id: string) => {
    setVisibleToasts(prev => prev.filter(toast => toast.id !== id))
  }

  if (visibleToasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {visibleToasts.map((toast) => {
        const Icon = iconMap[toast.type]

        return (
          <div
            key={toast.id}
            className={clsx(
              'flex items-center space-x-3 rounded-lg border p-4 shadow-lg bg-white',
              'animate-in slide-in-from-right-full duration-300'
            )}
          >
            <Icon className={clsx('h-5 w-5', colorMap[toast.type])} />
            <span className="text-sm font-medium text-gray-900">
              {toast.message}
            </span>
            <button
              onClick={() => removeToast(toast.id)}
              className="ml-auto text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
