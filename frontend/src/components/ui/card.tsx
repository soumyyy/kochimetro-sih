import type { ReactNode } from 'react'
import { clsx } from 'clsx'

interface CardProps {
  className?: string
  children: ReactNode
}

interface CardHeaderProps {
  className?: string
  children: ReactNode
}

interface CardTitleProps {
  className?: string
  children: ReactNode
}

interface CardContentProps {
  className?: string
  children: ReactNode
}

export function Card({ className, children }: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-3xl border border-white/15 bg-white/10 text-white shadow-[0_24px_80px_-36px_rgba(15,23,42,0.8)] backdrop-blur-xl transition-colors duration-300',
        className,
      )}
    >
      {children}
    </div>
  )
}

export function CardHeader({ className, children }: CardHeaderProps) {
  return (
    <div className={clsx('flex flex-col space-y-1.5 px-6 pt-6', className)}>
      {children}
    </div>
  )
}

export function CardTitle({ className, children }: CardTitleProps) {
  return (
    <h3 className={clsx('text-xl font-semibold leading-snug tracking-tight sm:text-2xl', className)}>
      {children}
    </h3>
  )
}

export function CardContent({ className, children }: CardContentProps) {
  return (
    <div className={clsx('px-6 pb-6 pt-5', className)}>
      {children}
    </div>
  )
}
