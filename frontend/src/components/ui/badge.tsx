import { ReactNode } from 'react'
import { clsx } from 'clsx'

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'secondary'
  className?: string
  children: ReactNode
}

const variantStyles = {
  default: 'border-transparent bg-gray-100 text-gray-900 hover:bg-gray-200',
  success: 'border-transparent bg-green-100 text-green-900 hover:bg-green-200',
  warning: 'border-transparent bg-yellow-100 text-yellow-900 hover:bg-yellow-200',
  danger: 'border-transparent bg-red-100 text-red-900 hover:bg-red-200',
  info: 'border-transparent bg-blue-100 text-blue-900 hover:bg-blue-200',
  secondary: 'border-transparent bg-gray-100 text-gray-900 hover:bg-gray-200',
}

export function Badge({ variant = 'default', className, children }: BadgeProps) {
  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      variantStyles[variant],
      className
    )}>
      {children}
    </span>
  )
}
