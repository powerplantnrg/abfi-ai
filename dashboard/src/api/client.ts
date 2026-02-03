const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD
    ? 'https://abfi-ai.vercel.app'
    : 'http://localhost:8000')

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// Sentiment API
export interface SentimentIndex {
  date: string
  overall_index: number
  bullish_count: number
  bearish_count: number
  neutral_count: number
  documents_analyzed: number
  fear_components: {
    regulatory_risk: number
    technology_risk: number
    feedstock_risk: number
    counterparty_risk: number
    market_risk: number
    esg_concerns: number
  }
  daily_change?: number
  weekly_change?: number
  monthly_change?: number
}

export interface LenderScore {
  lender: string
  sentiment: number
  change_30d: number
  documents: number
  trend: number[]
}

export interface DocumentFeed {
  id: string
  title: string
  source: string
  published_date: string
  sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  sentiment_score: number
  url?: string
}

export const sentimentApi = {
  getIndex: () => fetchApi<SentimentIndex>('/api/v1/sentiment/index'),
  getHistory: (days = 365) =>
    fetchApi<SentimentIndex[]>(`/api/v1/sentiment/index/history?lookback_days=${days}`),
  getLenders: () => fetchApi<LenderScore[]>('/api/v1/sentiment/lenders'),
  getDocumentFeed: (limit = 20) =>
    fetchApi<DocumentFeed[]>(`/api/v1/sentiment/documents/feed?limit=${limit}`),
}

// Prices API
export interface PriceKPI {
  commodity: string
  price: number
  currency: string
  unit: string
  change_pct: number
  change_direction: 'up' | 'down' | 'flat'
}

export interface OHLCDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

export interface ForwardCurve {
  commodity: string
  region: string
  curve_shape: string
  points: Array<{
    tenor: string
    price: number
    change_from_spot: number
  }>
  as_of_date: string
}

export interface RegionalHeatmap {
  commodity: string
  regions: Array<{
    region: string
    region_name: string
    price: number
    change_pct: number
  }>
}

export interface FeedstockPrice {
  feedstock: string
  spot_price: number
  change_7d: number
  currency: string
  unit: string
}

export interface RegionalPrice {
  region: string
  price: number
  change_pct: number
}

export const pricesApi = {
  getKpis: () => fetchApi<PriceKPI[]>('/api/v1/prices/kpis'),
  getOhlc: (commodity: string, period = '1Y') =>
    fetchApi<{ commodity: string; region: string; data: OHLCDataPoint[]; source: string }>(
      `/api/v1/prices/ohlc/${commodity}?period=${period}`
    ),
  getForwardCurve: (commodity: string) =>
    fetchApi<ForwardCurve>(`/api/v1/prices/forward/${commodity}`),
  getHeatmap: (commodity: string) =>
    fetchApi<RegionalHeatmap>(`/api/v1/prices/heatmap/${commodity}`),
  getFeedstockPrices: () => fetchApi<FeedstockPrice[]>('/api/v1/prices/feedstock'),
  getPriceHistory: (feedstock: string, period = '1M') =>
    fetchApi<OHLCDataPoint[]>(`/api/v1/prices/history/${feedstock}?period=${period}`),
  getRegionalPrices: () => fetchApi<RegionalPrice[]>('/api/v1/prices/regional'),
}

// Policy API
export interface PolicyKPI {
  label: string
  value: number
  subtitle: string
}

export interface PolicyTimelineEvent {
  jurisdiction: string
  date: string
  event_type: string
  title: string
  policy_id?: string
}

export interface MandateScenario {
  name: string
  mandate_level: string
  revenue_impact: number
}

export interface CarbonCalculatorResult {
  accu_credits: number
  accu_revenue: number
  safeguard_benefit: number
  total_annual_revenue: number
  sensitivity_low: number
  sensitivity_high: number
}

export interface OfftakeAgreement {
  offtaker: string
  mandate: string
  volume: string
  term: string
  premium: string
}

export interface PolicyUpdate {
  id: string
  title: string
  description: string
  jurisdiction: string
  date: string
  status: string
  impact: string
  priceImpact: number
  link: string
}

export interface CarbonPrice {
  market: string
  price: number
  currency: string
  change_pct: number
}

export interface SustainabilityMetrics {
  totalEmissionsAvoided: number
  projectsFinanced: number
  creditsIssued: number
}

export const policyApi = {
  getKpis: () => fetchApi<PolicyKPI[]>('/api/v1/policy/kpis'),
  getTimeline: () => fetchApi<PolicyTimelineEvent[]>('/api/v1/policy/timeline'),
  getKanban: () =>
    fetchApi<Record<string, Array<{ id: string; title: string; jurisdiction: string }>>>(
      '/api/v1/policy/kanban'
    ),
  getMandateScenarios: () => fetchApi<MandateScenario[]>('/api/v1/policy/mandate-scenarios'),
  calculateCarbon: (input: {
    annual_output_tonnes: number
    emission_factor: number
    carbon_price: number
  }) =>
    fetchApi<CarbonCalculatorResult>('/api/v1/policy/carbon-calculator', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  getOfftakeMarket: () => fetchApi<OfftakeAgreement[]>('/api/v1/policy/offtake-market'),
  getPolicyUpdates: () => fetchApi<PolicyUpdate[]>('/api/v1/policy/updates'),
  getCarbonPrices: () => fetchApi<CarbonPrice[]>('/api/v1/policy/carbon-prices'),
  getSustainabilityMetrics: () => fetchApi<SustainabilityMetrics>('/api/v1/policy/sustainability'),
}
