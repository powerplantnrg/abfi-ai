import { Line, LineChart, ResponsiveContainer } from 'recharts'

interface SparklineProps {
  data: number[]
  color?: string
  height?: number
  width?: number
}

export function Sparkline({
  data,
  color = 'var(--color-chart-1)',
  height = 24,
  width = 80,
}: SparklineProps) {
  const chartData = data.map((value, index) => ({ value, index }))

  // Determine color based on trend
  const trend = data[data.length - 1] - data[0]
  const trendColor = trend > 0 ? 'var(--color-bullish)' : trend < 0 ? 'var(--color-bearish)' : color

  return (
    <div className="sparkline" style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={trendColor}
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// Text-based sparkline for simple ASCII-style rendering
export function TextSparkline({ data }: { data: number[] }) {
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  const blocks = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

  const sparkline = data.map((value) => {
    const normalized = (value - min) / range
    const index = Math.floor(normalized * (blocks.length - 1))
    return blocks[index]
  })

  const trend = data[data.length - 1] - data[0]
  const colorClass = trend > 0 ? 'number-positive' : trend < 0 ? 'number-negative' : 'number-neutral'

  return <span className={colorClass}>{sparkline.join('')}</span>
}
