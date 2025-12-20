import { useSentimentIndex, useLenderScores, useDocumentFeed } from '@/hooks/useApi'
import { KpiCard, KpiGrid } from '@/components/ui/KpiCard'
import { Card, CardContent, ChartCard } from '@/components/ui/Card'
import { Badge, SentimentBadge } from '@/components/ui/Badge'
import { AreaChart } from '@/components/charts/AreaChart'
import { BarList } from '@/components/charts/BarChart'
import { TextSparkline } from '@/components/charts/Sparkline'
import { formatNumber, formatPercent, formatRelativeTime } from '@/lib/utils'
import { TrendingUp, TrendingDown, FileText, AlertCircle } from 'lucide-react'

export function SentimentDashboard() {
  const { data: index, isLoading: indexLoading } = useSentimentIndex()
  const { data: lenders, isLoading: lendersLoading } = useLenderScores()
  const { data: documents, isLoading: documentsLoading } = useDocumentFeed(10)

  // Transform fear components for BarList
  const fearData = index?.fear_components
    ? [
        { name: 'Regulatory Risk', value: index.fear_components.regulatory_risk },
        { name: 'Technology Risk', value: index.fear_components.technology_risk },
        { name: 'Feedstock Risk', value: index.fear_components.feedstock_risk },
        { name: 'Counterparty Risk', value: index.fear_components.counterparty_risk },
        { name: 'Market Risk', value: index.fear_components.market_risk },
        { name: 'ESG Concerns', value: index.fear_components.esg_concerns },
      ]
    : []

  // Mock trend data for the area chart
  const trendData = Array.from({ length: 12 }, (_, i) => ({
    month: new Date(2025, i, 1).toISOString(),
    bullish: 50 + Math.random() * 30,
    bearish: 30 + Math.random() * 20,
    net: 20 + Math.random() * 40 - 20,
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Lending Sentiment Index</h1>
          <p className="text-text-muted">
            AI-powered sentiment analysis across Australian bioenergy market
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select className="bg-surface border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent">
            <option>Last 30 days</option>
            <option>Last 90 days</option>
            <option>Last 12 months</option>
            <option>All time</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <KpiGrid columns={4}>
        <KpiCard
          label="Overall Index"
          value={index?.overall_index ?? 0}
          prefix={index?.overall_index && index.overall_index > 0 ? '+' : ''}
          delta={index?.weekly_change}
          deltaLabel="vs last week"
          loading={indexLoading}
        />
        <KpiCard
          label="Bullish Signals"
          value={index?.bullish_count ?? 0}
          delta={12}
          trend="up"
          loading={indexLoading}
        />
        <KpiCard
          label="Bearish Signals"
          value={index?.bearish_count ?? 0}
          delta={-5}
          trend="down"
          loading={indexLoading}
        />
        <KpiCard
          label="Documents Analyzed"
          value={index?.documents_analyzed ?? 0}
          delta={23}
          deltaLabel="this month"
          loading={indexLoading}
        />
      </KpiGrid>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sentiment Trend Chart - spans 2 columns */}
        <ChartCard
          title="Sentiment Trend"
          subtitle="12-month rolling sentiment indicators"
          className="lg:col-span-2"
        >
          <AreaChart
            data={trendData}
            xKey="month"
            areas={[
              { key: 'bullish', name: 'Bullish', color: 'var(--color-bullish)', fillOpacity: 0.3 },
              { key: 'bearish', name: 'Bearish', color: 'var(--color-bearish)', fillOpacity: 0.3 },
              { key: 'net', name: 'Net Sentiment', color: 'var(--color-accent)', fillOpacity: 0.1 },
            ]}
            height={350}
          />
        </ChartCard>

        {/* Fear Component Breakdown */}
        <Card title="Fear Components" subtitle="Risk factor distribution">
          <CardContent>
            <BarList data={fearData} valueFormatter={(v) => `${v}%`} />
          </CardContent>
        </Card>
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latest Documents */}
        <Card title="Latest Documents" subtitle="Real-time sentiment feed">
          <div className="divide-y divide-border-subtle">
            {documentsLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="p-4">
                  <div className="skeleton h-5 w-3/4 mb-2" />
                  <div className="skeleton h-4 w-1/4" />
                </div>
              ))
            ) : (
              documents?.map((doc) => (
                <div
                  key={doc.id}
                  className="p-4 hover:bg-surface-hover transition-colors cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`mt-1 w-2 h-2 rounded-full ${
                        doc.sentiment === 'BULLISH'
                          ? 'bg-bullish'
                          : doc.sentiment === 'BEARISH'
                          ? 'bg-bearish'
                          : 'bg-neutral'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-text-primary truncate">{doc.title}</p>
                      <div className="flex items-center gap-2 mt-1 text-sm text-text-muted">
                        <span>{doc.source}</span>
                        <span>·</span>
                        <span>{formatRelativeTime(doc.published_date)}</span>
                        <span>·</span>
                        <span
                          className={
                            doc.sentiment_score > 0 ? 'number-positive' : 'number-negative'
                          }
                        >
                          {doc.sentiment_score > 0 ? '+' : ''}
                          {doc.sentiment_score.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    <SentimentBadge sentiment={doc.sentiment} />
                  </div>
                </div>
              ))
            )}
          </div>
          <div className="p-4 border-t border-border-subtle">
            <button className="text-sm text-accent hover:text-accent-hover transition-colors">
              Load more documents →
            </button>
          </div>
        </Card>

        {/* Lender Comparison Matrix */}
        <Card title="Lender Comparison" subtitle="Sentiment by financial institution">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Lender</th>
                  <th className="text-right">Sentiment</th>
                  <th className="text-right">30d Δ</th>
                  <th className="text-right">Docs</th>
                  <th className="text-right">Trend</th>
                </tr>
              </thead>
              <tbody>
                {lendersLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      <td><div className="skeleton h-4 w-20" /></td>
                      <td><div className="skeleton h-4 w-12 ml-auto" /></td>
                      <td><div className="skeleton h-4 w-10 ml-auto" /></td>
                      <td><div className="skeleton h-4 w-8 ml-auto" /></td>
                      <td><div className="skeleton h-4 w-16 ml-auto" /></td>
                    </tr>
                  ))
                ) : (
                  lenders?.map((lender) => (
                    <tr key={lender.lender}>
                      <td className="font-medium">{lender.lender}</td>
                      <td className="text-right">
                        <span
                          className={
                            lender.sentiment > 0 ? 'number-positive' : 'number-negative'
                          }
                        >
                          {lender.sentiment > 0 ? '+' : ''}
                          {lender.sentiment}
                        </span>
                      </td>
                      <td className="text-right">
                        <span
                          className={
                            lender.change_30d > 0
                              ? 'number-positive'
                              : lender.change_30d < 0
                              ? 'number-negative'
                              : 'number-neutral'
                          }
                        >
                          {lender.change_30d > 0 && <TrendingUp size={12} className="inline mr-1" />}
                          {lender.change_30d < 0 && <TrendingDown size={12} className="inline mr-1" />}
                          {formatPercent(lender.change_30d)}
                        </span>
                      </td>
                      <td className="text-right text-text-muted">{lender.documents}</td>
                      <td className="text-right">
                        <TextSparkline data={lender.trend} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Alerts section */}
      <Card title="Active Alerts" action={<Badge>2 active</Badge>}>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-bullish/10 border border-bullish/20 rounded-lg">
              <TrendingUp className="text-bullish" size={20} />
              <div className="flex-1">
                <p className="font-medium text-text-primary">Bullish Spike Alert</p>
                <p className="text-sm text-text-muted">Trigger when overall index {'>'} 60</p>
              </div>
              <Badge variant="bullish">Active</Badge>
            </div>
            <div className="flex items-center gap-3 p-3 bg-surface-elevated border border-border-subtle rounded-lg">
              <AlertCircle className="text-bearish" size={20} />
              <div className="flex-1">
                <p className="font-medium text-text-primary">Bearish Warning</p>
                <p className="text-sm text-text-muted">Trigger when overall index {'<'} -30</p>
              </div>
              <Badge>Watching</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
