import { cn } from '@/lib/utils'

interface BadgeProps {
  variant?: 'bullish' | 'bearish' | 'neutral' | 'default'
  children: React.ReactNode
  className?: string
}

export function Badge({ variant = 'default', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'badge',
        {
          'badge-bullish': variant === 'bullish',
          'badge-bearish': variant === 'bearish',
          'badge-neutral': variant === 'neutral',
          'bg-surface-elevated text-text-secondary': variant === 'default',
        },
        className
      )}
    >
      {children}
    </span>
  )
}

export function SentimentBadge({ sentiment }: { sentiment: string }) {
  const variant = sentiment.toUpperCase() as 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  const variantMap = {
    BULLISH: 'bullish' as const,
    BEARISH: 'bearish' as const,
    NEUTRAL: 'neutral' as const,
  }

  return <Badge variant={variantMap[variant] || 'neutral'}>{sentiment}</Badge>
}

export function RiskBadge({ level }: { level: 'low' | 'medium' | 'high' }) {
  const colors = {
    low: 'bg-risk-low/20 text-risk-low',
    medium: 'bg-risk-medium/20 text-risk-medium',
    high: 'bg-risk-high/20 text-risk-high',
  }

  const labels = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
  }

  return <span className={cn('badge', colors[level])}>{labels[level]}</span>
}
