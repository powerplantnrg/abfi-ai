import { cn, formatNumber, formatPercent } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface KpiCardProps {
  label: string
  value: string | number
  delta?: number
  deltaLabel?: string
  trend?: 'up' | 'down' | 'flat'
  prefix?: string
  suffix?: string
  className?: string
  loading?: boolean
  onClick?: () => void
}

export function KpiCard({
  label,
  value,
  delta,
  deltaLabel,
  trend,
  prefix,
  suffix,
  className,
  loading,
  onClick,
}: KpiCardProps) {
  const displayValue = typeof value === 'number' ? formatNumber(value) : value
  const determinedTrend = trend || (delta ? (delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat') : 'flat')

  if (loading) {
    return (
      <div className={cn('kpi-card', className)}>
        <div className="skeleton h-4 w-24 mb-2" />
        <div className="skeleton h-10 w-32 mb-2" />
        <div className="skeleton h-4 w-20" />
      </div>
    )
  }

  return (
    <div className={cn('kpi-card card-hover', onClick && 'cursor-pointer', className)} onClick={onClick}>
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">
        {prefix}
        {displayValue}
        {suffix}
      </p>
      {delta !== undefined && (
        <div
          className={cn('kpi-delta', {
            'number-positive': determinedTrend === 'up',
            'number-negative': determinedTrend === 'down',
            'number-neutral': determinedTrend === 'flat',
          })}
        >
          {determinedTrend === 'up' && <TrendingUp size={14} />}
          {determinedTrend === 'down' && <TrendingDown size={14} />}
          {determinedTrend === 'flat' && <Minus size={14} />}
          <span>{formatPercent(delta)}</span>
          {deltaLabel && <span className="text-text-muted ml-1">{deltaLabel}</span>}
        </div>
      )}
    </div>
  )
}

interface KpiGridProps {
  children: React.ReactNode
  columns?: 2 | 3 | 4 | 5
  className?: string
}

export function KpiGrid({ children, columns = 4, className }: KpiGridProps) {
  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-2 lg:grid-cols-4',
    5: 'grid-cols-2 lg:grid-cols-5',
  }

  return (
    <div className={cn('grid gap-4', gridCols[columns], className)}>
      {children}
    </div>
  )
}
