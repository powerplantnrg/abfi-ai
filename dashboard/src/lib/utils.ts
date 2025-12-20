import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat('en-AU', {
    maximumFractionDigits: 2,
    ...options,
  }).format(value)
}

export function formatCurrency(value: number, currency = 'AUD'): string {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

export function formatCompactNumber(value: number): string {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`
  }
  return value.toString()
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(date))
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date()
  const target = new Date(date)
  const diffMs = now.getTime() - target.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)

  if (diffHours < 1) {
    const diffMins = Math.floor(diffMs / (1000 * 60))
    return `${diffMins}m ago`
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`
  }
  return formatDate(date)
}

export function getSentimentColor(sentiment: string): string {
  switch (sentiment.toUpperCase()) {
    case 'BULLISH':
      return 'var(--color-bullish)'
    case 'BEARISH':
      return 'var(--color-bearish)'
    default:
      return 'var(--color-neutral)'
  }
}

export function getRiskColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'low':
      return 'var(--color-risk-low)'
    case 'medium':
      return 'var(--color-risk-medium)'
    case 'high':
      return 'var(--color-risk-high)'
    default:
      return 'var(--color-text-muted)'
  }
}

export function getChangeDirection(value: number): 'up' | 'down' | 'flat' {
  if (value > 0.1) return 'up'
  if (value < -0.1) return 'down'
  return 'flat'
}
