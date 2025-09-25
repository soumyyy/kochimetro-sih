import type { ReactNode } from 'react'
import { clsx } from 'clsx'

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'secondary'
  className?: string
  children: ReactNode
}

const variantStyles = {
  default: 'border-white/25 bg-white/20 text-white hover:bg-white/30',
  success: 'border-emerald-200/40 bg-emerald-400/20 text-emerald-100 hover:bg-emerald-400/30',
  warning: 'border-amber-200/40 bg-amber-400/20 text-amber-100 hover:bg-amber-400/30',
  danger: 'border-rose-200/50 bg-rose-500/20 text-rose-100 hover:bg-rose-500/30',
  info: 'border-sky-200/50 bg-sky-500/20 text-sky-100 hover:bg-sky-500/30',
  secondary: 'border-white/20 bg-white/10 text-white/90 hover:bg-white/20',
}

export function Badge({ variant = 'default', className, children }: BadgeProps) {
  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium backdrop-blur-lg transition-colors',
      variantStyles[variant],
      className
    )}>
      {children}
    </span>
  )
}
