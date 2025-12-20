import { cn } from '@/lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  title?: string
  subtitle?: string
  action?: React.ReactNode
}

export function Card({ children, className, title, subtitle, action }: CardProps) {
  return (
    <div
      className={cn(
        'bg-surface border border-border-subtle rounded-lg',
        className
      )}
    >
      {(title || action) && (
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
          <div>
            {title && <h3 className="font-semibold text-text-primary">{title}</h3>}
            {subtitle && <p className="text-sm text-text-muted mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={cn(title || action ? '' : '')}>{children}</div>
    </div>
  )
}

export function CardContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('p-6', className)}>{children}</div>
}

export function ChartCard({
  children,
  title,
  subtitle,
  action,
  className,
}: CardProps) {
  return (
    <Card title={title} subtitle={subtitle} action={action} className={cn('chart-container p-0', className)}>
      <div className="p-6">{children}</div>
    </Card>
  )
}
