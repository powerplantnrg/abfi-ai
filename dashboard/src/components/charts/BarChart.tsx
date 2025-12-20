import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { formatNumber, formatCurrency } from '@/lib/utils'

interface BarChartProps {
  data: Array<Record<string, unknown>>
  xKey: string
  yKey: string
  height?: number
  layout?: 'horizontal' | 'vertical'
  showGrid?: boolean
  colorByValue?: boolean
  formatValue?: (value: number) => string
}

export function BarChart({
  data,
  xKey,
  yKey,
  height = 300,
  layout = 'horizontal',
  showGrid = true,
  colorByValue = false,
  formatValue = formatNumber,
}: BarChartProps) {
  const getBarColor = (value: number) => {
    if (!colorByValue) return 'var(--color-chart-1)'
    if (value > 0) return 'var(--color-bullish)'
    if (value < 0) return 'var(--color-bearish)'
    return 'var(--color-text-muted)'
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart
        data={data}
        layout={layout === 'horizontal' ? 'vertical' : 'horizontal'}
        margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
      >
        {showGrid && (
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border-subtle)"
            horizontal={layout === 'horizontal'}
            vertical={layout === 'vertical'}
          />
        )}
        {layout === 'horizontal' ? (
          <>
            <XAxis
              type="number"
              stroke="var(--color-text-muted)"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => formatValue(value)}
            />
            <YAxis
              type="category"
              dataKey={xKey}
              stroke="var(--color-text-muted)"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              width={100}
            />
          </>
        ) : (
          <>
            <XAxis
              dataKey={xKey}
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
              tickFormatter={(value) => formatValue(value)}
            />
          </>
        )}
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--color-surface-elevated)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            padding: '12px',
          }}
          formatter={(value) => [formatValue(value as number), '']}
        />
        <Bar dataKey={yKey} radius={[4, 4, 4, 4]} maxBarSize={40}>
          {data.map((entry, index) => (
            <Cell
              key={index}
              fill={getBarColor(entry[yKey] as number)}
            />
          ))}
        </Bar>
      </RechartsBarChart>
    </ResponsiveContainer>
  )
}

// Horizontal bar list like Tremor BarList
interface BarListItem {
  name: string
  value: number
}

interface BarListProps {
  data: BarListItem[]
  valueFormatter?: (value: number) => string
}

export function BarList({ data, valueFormatter = (v) => `${v}%` }: BarListProps) {
  const maxValue = Math.max(...data.map((d) => d.value))

  return (
    <div className="space-y-3">
      {data.map((item) => (
        <div key={item.name}>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-text-secondary">{item.name}</span>
            <span className="font-medium text-text-primary">{valueFormatter(item.value)}</span>
          </div>
          <div className="h-2 bg-surface-elevated rounded-full overflow-hidden">
            <div
              className="h-full bg-chart-1 rounded-full transition-all duration-500"
              style={{ width: `${(item.value / maxValue) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
