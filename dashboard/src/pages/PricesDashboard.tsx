import { useEffect, useRef, useState } from 'react'
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from 'lightweight-charts'
import type { IChartApi } from 'lightweight-charts'
import { useFeedstockPrices, usePriceHistory, useRegionalPrices } from '@/hooks/useApi'
import { KpiCard, KpiGrid } from '@/components/ui/KpiCard'
import { Card, CardContent, ChartCard } from '@/components/ui/Card'
import { Badge, RiskBadge } from '@/components/ui/Badge'
import { formatCurrency, formatPercent, formatNumber } from '@/lib/utils'
import { TrendingUp, TrendingDown, BarChart3, Globe2 } from 'lucide-react'

const FEEDSTOCK_OPTIONS = [
  { id: 'uco', name: 'Used Cooking Oil', unit: '$/L' },
  { id: 'tallow', name: 'Tallow', unit: '$/MT' },
  { id: 'canola', name: 'Canola Oil', unit: '$/MT' },
  { id: 'palm', name: 'Palm Oil', unit: '$/MT' },
]

export function PricesDashboard() {
  const [selectedFeedstock, setSelectedFeedstock] = useState('uco')
  const [timeframe, setTimeframe] = useState('1M')
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)

  const { data: prices, isLoading: pricesLoading } = useFeedstockPrices()
  const { data: history } = usePriceHistory(selectedFeedstock, timeframe)
  const { data: regional, isLoading: regionalLoading } = useRegionalPrices()

  // Initialize TradingView Lightweight Chart
  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: 'var(--color-text-muted)',
      },
      grid: {
        vertLines: { color: 'var(--color-border-subtle)' },
        horzLines: { color: 'var(--color-border-subtle)' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: 'var(--color-border-subtle)',
      },
      timeScale: {
        borderColor: 'var(--color-border-subtle)',
        timeVisible: true,
      },
    })

    chartRef.current = chart

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    })

    // Generate mock OHLC data
    const mockData = generateMockOHLCData(selectedFeedstock, timeframe)
    candlestickSeries.setData(mockData)

    // Add volume series
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#3b82f6',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    })

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

    const volumeData = mockData.map((d) => ({
      time: d.time,
      value: Math.random() * 1000000,
      color: d.close >= d.open ? '#10b98133' : '#ef444433',
    }))
    volumeSeries.setData(volumeData)

    chart.timeScale().fitContent()

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [selectedFeedstock, timeframe])

  // Get current feedstock data
  const currentFeedstock = prices?.find((p) => p.feedstock.toLowerCase() === selectedFeedstock)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Feedstock Price Index</h1>
          <p className="text-text-muted">IOSCO-compliant benchmark pricing for Australian bioenergy feedstocks</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="bullish" className="flex items-center gap-1">
            <Globe2 size={12} />
            IOSCO Compliant
          </Badge>
        </div>
      </div>

      {/* Price KPI Cards */}
      <KpiGrid columns={4}>
        {FEEDSTOCK_OPTIONS.map((feedstock) => {
          const data = prices?.find((p) => p.feedstock.toLowerCase() === feedstock.id)
          return (
            <KpiCard
              key={feedstock.id}
              label={feedstock.name}
              value={data?.spot_price ?? 0}
              prefix="$"
              suffix={feedstock.id === 'uco' ? '/L' : '/MT'}
              delta={data?.change_7d}
              deltaLabel="7d"
              loading={pricesLoading}
              onClick={() => setSelectedFeedstock(feedstock.id)}
              className={selectedFeedstock === feedstock.id ? 'ring-2 ring-accent' : ''}
            />
          )
        })}
      </KpiGrid>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Price Chart - spans 2 columns */}
        <ChartCard
          title={`${FEEDSTOCK_OPTIONS.find((f) => f.id === selectedFeedstock)?.name} Price`}
          subtitle="OHLC with volume"
          className="lg:col-span-2"
          action={
            <div className="flex gap-1">
              {['1D', '1W', '1M', '3M', '1Y'].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`px-2 py-1 text-xs rounded ${
                    timeframe === tf
                      ? 'bg-accent text-background'
                      : 'bg-surface-hover text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          }
        >
          <div ref={chartContainerRef} className="w-full" />
        </ChartCard>

        {/* Market Stats */}
        <Card title="Market Statistics" subtitle="Current session">
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-text-muted">Open</span>
                <span className="font-mono text-text-primary">
                  {formatCurrency(currentFeedstock?.spot_price ?? 0 * 0.98)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-muted">High</span>
                <span className="font-mono number-positive">
                  {formatCurrency((currentFeedstock?.spot_price ?? 0) * 1.02)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-muted">Low</span>
                <span className="font-mono number-negative">
                  {formatCurrency((currentFeedstock?.spot_price ?? 0) * 0.96)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-muted">Close</span>
                <span className="font-mono text-text-primary">
                  {formatCurrency(currentFeedstock?.spot_price ?? 0)}
                </span>
              </div>
              <div className="border-t border-border-subtle pt-4">
                <div className="flex justify-between items-center">
                  <span className="text-text-muted">Volume</span>
                  <span className="font-mono text-text-primary">
                    {formatNumber(Math.floor(Math.random() * 50000 + 10000))} MT
                  </span>
                </div>
                <div className="flex justify-between items-center mt-2">
                  <span className="text-text-muted">VWAP</span>
                  <span className="font-mono text-text-primary">
                    {formatCurrency((currentFeedstock?.spot_price ?? 0) * 0.995)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Regional Price Heatmap */}
        <Card title="Regional Prices" subtitle="Price variation by state">
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {regionalLoading
                ? Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="p-4 bg-surface-elevated rounded-lg">
                      <div className="skeleton h-4 w-12 mb-2" />
                      <div className="skeleton h-6 w-20" />
                    </div>
                  ))
                : regional?.map((region) => {
                    const variance = ((region.price - (currentFeedstock?.spot_price ?? 0)) / (currentFeedstock?.spot_price ?? 1)) * 100
                    return (
                      <div
                        key={region.region}
                        className={`p-4 rounded-lg border ${
                          variance > 2
                            ? 'bg-bullish/10 border-bullish/30'
                            : variance < -2
                            ? 'bg-bearish/10 border-bearish/30'
                            : 'bg-surface-elevated border-border-subtle'
                        }`}
                      >
                        <div className="text-sm text-text-muted">{region.region}</div>
                        <div className="font-mono text-lg text-text-primary">
                          {formatCurrency(region.price)}
                        </div>
                        <div
                          className={`text-xs ${
                            variance > 0 ? 'number-positive' : variance < 0 ? 'number-negative' : 'number-neutral'
                          }`}
                        >
                          {variance > 0 ? '+' : ''}
                          {variance.toFixed(1)}% vs benchmark
                        </div>
                      </div>
                    )
                  })}
            </div>
          </CardContent>
        </Card>

        {/* Forward Curve */}
        <Card title="Forward Curve" subtitle="Futures pricing by delivery month">
          <CardContent>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Delivery</th>
                  <th className="text-right">Price</th>
                  <th className="text-right">Change</th>
                  <th className="text-right">Spread</th>
                </tr>
              </thead>
              <tbody>
                {generateForwardCurve(currentFeedstock?.spot_price ?? 100).map((row) => (
                  <tr key={row.month}>
                    <td className="font-medium">{row.month}</td>
                    <td className="text-right font-mono">{formatCurrency(row.price)}</td>
                    <td className="text-right">
                      <span className={row.change > 0 ? 'number-positive' : 'number-negative'}>
                        {row.change > 0 && <TrendingUp size={12} className="inline mr-1" />}
                        {row.change < 0 && <TrendingDown size={12} className="inline mr-1" />}
                        {formatPercent(row.change)}
                      </span>
                    </td>
                    <td className="text-right text-text-muted">{formatCurrency(row.spread)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>

      {/* Counterparty Risk Section */}
      <Card title="Counterparty Risk Monitor" subtitle="Credit exposure by supplier">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Counterparty</th>
                <th className="text-right">Exposure</th>
                <th className="text-right">Credit Rating</th>
                <th className="text-right">Risk Score</th>
                <th className="text-right">Status</th>
              </tr>
            </thead>
            <tbody>
              {generateCounterpartyData().map((cp) => (
                <tr key={cp.name}>
                  <td className="font-medium">{cp.name}</td>
                  <td className="text-right font-mono">{formatCurrency(cp.exposure)}</td>
                  <td className="text-right">
                    <Badge
                      variant={
                        cp.rating.startsWith('A') ? 'bullish' : cp.rating.startsWith('B') ? 'neutral' : 'bearish'
                      }
                    >
                      {cp.rating}
                    </Badge>
                  </td>
                  <td className="text-right">
                    <RiskBadge level={cp.riskLevel} />
                  </td>
                  <td className="text-right">
                    <span
                      className={`inline-flex items-center gap-1 text-sm ${
                        cp.status === 'Active' ? 'text-bullish' : 'text-neutral'
                      }`}
                    >
                      <span
                        className={`w-2 h-2 rounded-full ${
                          cp.status === 'Active' ? 'bg-bullish animate-pulse' : 'bg-neutral'
                        }`}
                      />
                      {cp.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

// Helper functions for mock data
function generateMockOHLCData(feedstock: string, timeframe: string) {
  const basePrice = feedstock === 'uco' ? 1.2 : feedstock === 'tallow' ? 850 : feedstock === 'canola' ? 1100 : 900
  const days = timeframe === '1D' ? 24 : timeframe === '1W' ? 7 : timeframe === '1M' ? 30 : timeframe === '3M' ? 90 : 365
  const data = []
  let currentPrice = basePrice

  for (let i = days; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    const volatility = basePrice * 0.02
    const open = currentPrice
    const close = open + (Math.random() - 0.5) * volatility
    const high = Math.max(open, close) + Math.random() * volatility * 0.5
    const low = Math.min(open, close) - Math.random() * volatility * 0.5

    data.push({
      time: date.toISOString().split('T')[0],
      open,
      high,
      low,
      close,
    })

    currentPrice = close
  }

  return data
}

function generateForwardCurve(spotPrice: number) {
  const months = ['Jan 25', 'Feb 25', 'Mar 25', 'Apr 25', 'May 25', 'Jun 25']
  return months.map((month, i) => ({
    month,
    price: spotPrice * (1 + i * 0.01 + Math.random() * 0.02),
    change: (Math.random() - 0.3) * 5,
    spread: spotPrice * (i + 1) * 0.005,
  }))
}

function generateCounterpartyData() {
  return [
    { name: 'Clean Energy Fuels', exposure: 2500000, rating: 'A-', riskLevel: 'low' as const, status: 'Active' },
    { name: 'BioRefinery Australia', exposure: 1800000, rating: 'BBB+', riskLevel: 'low' as const, status: 'Active' },
    { name: 'Pacific Biodiesel', exposure: 1200000, rating: 'BBB', riskLevel: 'medium' as const, status: 'Active' },
    { name: 'GreenFuels Corp', exposure: 950000, rating: 'BB+', riskLevel: 'medium' as const, status: 'Active' },
    { name: 'Aussie Bioenergy', exposure: 600000, rating: 'BB', riskLevel: 'high' as const, status: 'Review' },
  ]
}
