import { useState } from 'react'
import { usePolicyUpdates, useCarbonPrices, useSustainabilityMetrics } from '@/hooks/useApi'
import { KpiCard, KpiGrid } from '@/components/ui/KpiCard'
import { Card, CardContent, ChartCard } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { AreaChart } from '@/components/charts/AreaChart'
import { BarList } from '@/components/charts/BarChart'
import { formatCurrency, formatNumber, formatPercent, formatDate } from '@/lib/utils'
import {
  FileText,
  Calculator,
  TrendingUp,
  TrendingDown,
  Leaf,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ExternalLink,
} from 'lucide-react'

// Carbon calculator parameters
interface CalculatorInputs {
  annualProduction: number
  feedstockType: string
  certificationScheme: string
}

export function PolicyDashboard() {
  const { data: policies, isLoading: policiesLoading } = usePolicyUpdates()
  const { data: carbonPrices, isLoading: carbonLoading } = useCarbonPrices()
  const { data: metrics, isLoading: metricsLoading } = useSustainabilityMetrics()

  const [calculator, setCalculator] = useState<CalculatorInputs>({
    annualProduction: 50000,
    feedstockType: 'uco',
    certificationScheme: 'iscc',
  })

  // Calculate carbon revenue
  const calculateRevenue = () => {
    const baseRate = 85 // CO2 reduction factor based on feedstock
    const ciReduction =
      calculator.feedstockType === 'uco'
        ? 85
        : calculator.feedstockType === 'tallow'
        ? 75
        : calculator.feedstockType === 'canola'
        ? 65
        : 55

    const certMultiplier = calculator.certificationScheme === 'iscc' ? 1.15 : 1.0
    const euPrice = carbonPrices?.find((p) => p.market === 'EU')?.price ?? 80
    const accuPrice = carbonPrices?.find((p) => p.market === 'ACCU')?.price ?? 35

    const totalCredits = (calculator.annualProduction * ciReduction * certMultiplier) / 1000
    const euRevenue = totalCredits * euPrice * 0.6
    const accuRevenue = totalCredits * accuPrice * 0.4

    return {
      totalCredits: Math.round(totalCredits),
      euRevenue: Math.round(euRevenue),
      accuRevenue: Math.round(accuRevenue),
      totalRevenue: Math.round(euRevenue + accuRevenue),
      ciScore: Math.round(ciReduction * certMultiplier),
    }
  }

  const revenue = calculateRevenue()

  // Carbon price trend data
  const carbonTrendData = Array.from({ length: 12 }, (_, i) => ({
    month: new Date(2024, i, 1).toISOString(),
    EU: 75 + Math.random() * 20 + i * 0.5,
    ACCU: 30 + Math.random() * 10 + i * 0.3,
    VCU: 15 + Math.random() * 8 + i * 0.2,
  }))

  // Policy impact data for BarList
  const policyImpactData = [
    { name: 'EU RED III', value: 85 },
    { name: 'Aus Safeguard Mechanism', value: 72 },
    { name: 'CORSIA', value: 65 },
    { name: 'US RFS', value: 58 },
    { name: 'UK RTFO', value: 45 },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Policy & Carbon Revenue</h1>
          <p className="text-text-muted">Regulatory tracker and carbon credit calculator</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge className="flex items-center gap-1">
            <Clock size={12} />
            Last updated: Today
          </Badge>
        </div>
      </div>

      {/* Carbon Price KPIs */}
      <KpiGrid columns={4}>
        <KpiCard
          label="EU ETS"
          value={carbonPrices?.find((p) => p.market === 'EU')?.price ?? 82}
          prefix="€"
          suffix="/tCO₂"
          delta={3.2}
          trend="up"
          loading={carbonLoading}
        />
        <KpiCard
          label="ACCU"
          value={carbonPrices?.find((p) => p.market === 'ACCU')?.price ?? 35}
          prefix="A$"
          suffix="/tCO₂"
          delta={-1.5}
          trend="down"
          loading={carbonLoading}
        />
        <KpiCard
          label="VCU (Nature)"
          value={carbonPrices?.find((p) => p.market === 'VCU')?.price ?? 18}
          prefix="$"
          suffix="/tCO₂"
          delta={0.8}
          loading={carbonLoading}
        />
        <KpiCard
          label="Active Policies"
          value={policies?.length ?? 12}
          delta={2}
          deltaLabel="this quarter"
          loading={policiesLoading}
        />
      </KpiGrid>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Carbon Price Trends - spans 2 columns */}
        <ChartCard
          title="Carbon Price Trends"
          subtitle="12-month price evolution by market"
          className="lg:col-span-2"
        >
          <AreaChart
            data={carbonTrendData}
            xKey="month"
            areas={[
              { key: 'EU', name: 'EU ETS', color: 'var(--color-chart-1)', fillOpacity: 0.2 },
              { key: 'ACCU', name: 'ACCU', color: 'var(--color-chart-2)', fillOpacity: 0.2 },
              { key: 'VCU', name: 'VCU', color: 'var(--color-chart-3)', fillOpacity: 0.2 },
            ]}
            height={350}
          />
        </ChartCard>

        {/* Policy Impact */}
        <Card title="Policy Impact Score" subtitle="Market influence ranking">
          <CardContent>
            <BarList data={policyImpactData} valueFormatter={(v) => `${v}%`} />
          </CardContent>
        </Card>
      </div>

      {/* Carbon Calculator Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card
          title="Carbon Revenue Calculator"
          subtitle="Estimate your carbon credit potential"
          action={<Calculator size={20} className="text-accent" />}
        >
          <CardContent>
            <div className="space-y-6">
              {/* Annual Production Input */}
              <div>
                <label className="block text-sm text-text-muted mb-2">Annual Production (litres)</label>
                <input
                  type="range"
                  min="10000"
                  max="500000"
                  step="5000"
                  value={calculator.annualProduction}
                  onChange={(e) =>
                    setCalculator({ ...calculator, annualProduction: parseInt(e.target.value) })
                  }
                  className="w-full h-2 bg-surface-elevated rounded-lg appearance-none cursor-pointer accent-accent"
                />
                <div className="flex justify-between text-sm text-text-muted mt-1">
                  <span>10K L</span>
                  <span className="font-mono text-text-primary">
                    {formatNumber(calculator.annualProduction)} L
                  </span>
                  <span>500K L</span>
                </div>
              </div>

              {/* Feedstock Type */}
              <div>
                <label className="block text-sm text-text-muted mb-2">Feedstock Type</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 'uco', name: 'UCO', ci: 85 },
                    { id: 'tallow', name: 'Tallow', ci: 75 },
                    { id: 'canola', name: 'Canola', ci: 65 },
                    { id: 'palm', name: 'Palm', ci: 55 },
                  ].map((fs) => (
                    <button
                      key={fs.id}
                      onClick={() => setCalculator({ ...calculator, feedstockType: fs.id })}
                      className={`p-3 rounded-lg text-left transition-colors ${
                        calculator.feedstockType === fs.id
                          ? 'bg-accent text-background'
                          : 'bg-surface-elevated hover:bg-surface-hover text-text-secondary'
                      }`}
                    >
                      <div className="font-medium">{fs.name}</div>
                      <div className="text-xs opacity-75">CI: {fs.ci}%</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Certification Scheme */}
              <div>
                <label className="block text-sm text-text-muted mb-2">Certification Scheme</label>
                <select
                  value={calculator.certificationScheme}
                  onChange={(e) =>
                    setCalculator({ ...calculator, certificationScheme: e.target.value })
                  }
                  className="w-full bg-surface-elevated border border-border rounded-lg px-4 py-3 text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="iscc">ISCC (15% premium)</option>
                  <option value="rsb">RSB Certification</option>
                  <option value="none">No certification</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Calculator Results */}
        <Card title="Projected Revenue" subtitle="Based on current market prices">
          <CardContent>
            <div className="space-y-4">
              {/* CI Score */}
              <div className="p-4 bg-accent/10 rounded-lg border border-accent/20">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Leaf className="text-accent" size={20} />
                    <span className="text-text-secondary">Carbon Intensity Score</span>
                  </div>
                  <span className="text-2xl font-bold text-accent">{revenue.ciScore}%</span>
                </div>
              </div>

              {/* Credits Generated */}
              <div className="flex justify-between items-center p-4 bg-surface-elevated rounded-lg">
                <span className="text-text-muted">Total Credits Generated</span>
                <span className="text-xl font-mono text-text-primary">
                  {formatNumber(revenue.totalCredits)} tCO₂e
                </span>
              </div>

              {/* Revenue Breakdown */}
              <div className="space-y-3 pt-4 border-t border-border-subtle">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-chart-1" />
                    <span className="text-text-secondary">EU ETS Revenue</span>
                  </div>
                  <span className="font-mono text-text-primary">{formatCurrency(revenue.euRevenue)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-chart-2" />
                    <span className="text-text-secondary">ACCU Revenue</span>
                  </div>
                  <span className="font-mono text-text-primary">{formatCurrency(revenue.accuRevenue)}</span>
                </div>
              </div>

              {/* Total */}
              <div className="p-4 bg-bullish/10 rounded-lg border border-bullish/20 mt-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-text-primary">Estimated Annual Revenue</span>
                  <span className="text-2xl font-bold number-positive">
                    {formatCurrency(revenue.totalRevenue)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Policy Updates Feed */}
      <Card title="Policy Updates" subtitle="Latest regulatory changes and impacts">
        <div className="divide-y divide-border-subtle">
          {policiesLoading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="p-4">
                <div className="skeleton h-5 w-3/4 mb-2" />
                <div className="skeleton h-4 w-1/2" />
              </div>
            ))
          ) : (
            mockPolicyUpdates.map((policy) => (
              <div
                key={policy.id}
                className="p-4 hover:bg-surface-hover transition-colors cursor-pointer"
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`p-2 rounded-lg ${
                      policy.impact === 'positive'
                        ? 'bg-bullish/10 text-bullish'
                        : policy.impact === 'negative'
                        ? 'bg-bearish/10 text-bearish'
                        : 'bg-neutral/10 text-neutral'
                    }`}
                  >
                    {policy.impact === 'positive' ? (
                      <TrendingUp size={18} />
                    ) : policy.impact === 'negative' ? (
                      <TrendingDown size={18} />
                    ) : (
                      <AlertTriangle size={18} />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-text-primary">{policy.title}</h4>
                      <Badge
                        variant={
                          policy.status === 'enacted'
                            ? 'bullish'
                            : policy.status === 'pending'
                            ? 'neutral'
                            : 'default'
                        }
                      >
                        {policy.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-text-muted mt-1">{policy.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-text-muted">
                      <span>{policy.jurisdiction}</span>
                      <span>·</span>
                      <span>{formatDate(policy.date)}</span>
                      <span>·</span>
                      <a
                        href={policy.link}
                        className="text-accent hover:underline flex items-center gap-1"
                      >
                        Source <ExternalLink size={10} />
                      </a>
                    </div>
                  </div>
                  <div className="text-right">
                    <div
                      className={`text-sm font-medium ${
                        policy.priceImpact > 0
                          ? 'number-positive'
                          : policy.priceImpact < 0
                          ? 'number-negative'
                          : 'number-neutral'
                      }`}
                    >
                      {policy.priceImpact > 0 ? '+' : ''}
                      {formatPercent(policy.priceImpact)}
                    </div>
                    <div className="text-xs text-text-muted">price impact</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Sustainability Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="text-center">
          <CardContent>
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-bullish/10 mb-3">
              <CheckCircle2 className="text-bullish" size={24} />
            </div>
            <div className="text-3xl font-bold text-text-primary mb-1">
              {formatNumber(metrics?.totalEmissionsAvoided ?? 125000)}
            </div>
            <div className="text-sm text-text-muted">tCO₂e Avoided (YTD)</div>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent>
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-accent/10 mb-3">
              <Leaf className="text-accent" size={24} />
            </div>
            <div className="text-3xl font-bold text-text-primary mb-1">
              {formatNumber(metrics?.projectsFinanced ?? 47)}
            </div>
            <div className="text-sm text-text-muted">Projects Financed</div>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent>
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-chart-3/10 mb-3">
              <FileText className="text-chart-3" size={24} />
            </div>
            <div className="text-3xl font-bold text-text-primary mb-1">
              {formatNumber(metrics?.creditsIssued ?? 89000)}
            </div>
            <div className="text-sm text-text-muted">Credits Issued</div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Mock policy data
const mockPolicyUpdates = [
  {
    id: '1',
    title: 'EU RED III Implementation Guidelines Released',
    description:
      'European Commission publishes detailed guidelines for biofuel sustainability criteria under RED III directive.',
    jurisdiction: 'European Union',
    date: '2025-01-10',
    status: 'enacted',
    impact: 'positive',
    priceImpact: 5.2,
    link: '#',
  },
  {
    id: '2',
    title: 'Australian Safeguard Mechanism Update',
    description:
      'Revised baseline calculations and new sector-specific guidance for bioenergy facilities.',
    jurisdiction: 'Australia',
    date: '2025-01-08',
    status: 'pending',
    impact: 'neutral',
    priceImpact: 1.5,
    link: '#',
  },
  {
    id: '3',
    title: 'CORSIA Phase 2 Eligibility Criteria',
    description:
      'ICAO releases updated eligibility criteria for sustainable aviation fuel under CORSIA scheme.',
    jurisdiction: 'International',
    date: '2025-01-05',
    status: 'enacted',
    impact: 'positive',
    priceImpact: 3.8,
    link: '#',
  },
  {
    id: '4',
    title: 'US RFS Volumes Proposed for 2026',
    description:
      'EPA proposes renewable fuel volume requirements showing modest increase for biomass-based diesel.',
    jurisdiction: 'United States',
    date: '2024-12-28',
    status: 'proposed',
    impact: 'neutral',
    priceImpact: 0,
    link: '#',
  },
]
