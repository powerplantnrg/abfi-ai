import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { formatDate, formatNumber } from '@/lib/utils'

interface AreaChartProps {
  data: Array<Record<string, unknown>>
  xKey: string
  areas: Array<{
    key: string
    name: string
    color: string
    fillOpacity?: number
  }>
  height?: number
  showGrid?: boolean
  showLegend?: boolean
}

export function AreaChart({
  data,
  xKey,
  areas,
  height = 300,
  showGrid = true,
  showLegend = true,
}: AreaChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsAreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        {showGrid && (
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border-subtle)"
            vertical={false}
          />
        )}
        <XAxis
          dataKey={xKey}
          tickFormatter={(value) => {
            const date = new Date(value)
            return date.toLocaleDateString('en-AU', { month: 'short', day: 'numeric' })
          }}
          stroke="var(--color-text-muted)"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="var(--color-text-muted)"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => formatNumber(value)}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--color-surface-elevated)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            padding: '12px',
          }}
          labelStyle={{ color: 'var(--color-text-primary)', fontWeight: 500 }}
          itemStyle={{ color: 'var(--color-text-secondary)' }}
          labelFormatter={(label) => formatDate(label)}
        />
        {showLegend && (
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={(value) => (
              <span style={{ color: 'var(--color-text-secondary)' }}>{value}</span>
            )}
          />
        )}
        {areas.map((area) => (
          <Area
            key={area.key}
            type="monotone"
            dataKey={area.key}
            name={area.name}
            stroke={area.color}
            fill={area.color}
            fillOpacity={area.fillOpacity ?? 0.2}
            strokeWidth={2}
          />
        ))}
      </RechartsAreaChart>
    </ResponsiveContainer>
  )
}
