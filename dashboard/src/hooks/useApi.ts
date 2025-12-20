import { useQuery, useMutation } from '@tanstack/react-query'
import { sentimentApi, pricesApi, policyApi } from '@/api/client'

// Sentiment hooks
export function useSentimentIndex() {
  return useQuery({
    queryKey: ['sentiment', 'index'],
    queryFn: sentimentApi.getIndex,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useSentimentHistory(days = 365) {
  return useQuery({
    queryKey: ['sentiment', 'history', days],
    queryFn: () => sentimentApi.getHistory(days),
    staleTime: 5 * 60 * 1000,
  })
}

export function useLenderScores() {
  return useQuery({
    queryKey: ['sentiment', 'lenders'],
    queryFn: sentimentApi.getLenders,
    staleTime: 5 * 60 * 1000,
  })
}

export function useDocumentFeed(limit = 20) {
  return useQuery({
    queryKey: ['sentiment', 'documents', limit],
    queryFn: () => sentimentApi.getDocumentFeed(limit),
    staleTime: 1 * 60 * 1000, // 1 minute - more frequent updates
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  })
}

// Prices hooks
export function usePriceKpis() {
  return useQuery({
    queryKey: ['prices', 'kpis'],
    queryFn: pricesApi.getKpis,
    staleTime: 1 * 60 * 1000,
    refetchInterval: 30 * 1000,
  })
}

export function useFeedstockPrices() {
  return useQuery({
    queryKey: ['prices', 'feedstock'],
    queryFn: pricesApi.getFeedstockPrices,
    staleTime: 1 * 60 * 1000,
  })
}

export function usePriceHistory(feedstock: string, period = '1M') {
  return useQuery({
    queryKey: ['prices', 'history', feedstock, period],
    queryFn: () => pricesApi.getPriceHistory(feedstock, period),
    staleTime: 5 * 60 * 1000,
    enabled: !!feedstock,
  })
}

export function useRegionalPrices() {
  return useQuery({
    queryKey: ['prices', 'regional'],
    queryFn: pricesApi.getRegionalPrices,
    staleTime: 5 * 60 * 1000,
  })
}

export function useOhlcData(commodity: string, period = '1Y') {
  return useQuery({
    queryKey: ['prices', 'ohlc', commodity, period],
    queryFn: () => pricesApi.getOhlc(commodity, period),
    staleTime: 5 * 60 * 1000,
    enabled: !!commodity,
  })
}

export function useForwardCurve(commodity: string) {
  return useQuery({
    queryKey: ['prices', 'forward', commodity],
    queryFn: () => pricesApi.getForwardCurve(commodity),
    staleTime: 5 * 60 * 1000,
    enabled: !!commodity,
  })
}

export function useRegionalHeatmap(commodity: string) {
  return useQuery({
    queryKey: ['prices', 'heatmap', commodity],
    queryFn: () => pricesApi.getHeatmap(commodity),
    staleTime: 5 * 60 * 1000,
    enabled: !!commodity,
  })
}

// Policy hooks
export function usePolicyKpis() {
  return useQuery({
    queryKey: ['policy', 'kpis'],
    queryFn: policyApi.getKpis,
    staleTime: 5 * 60 * 1000,
  })
}

export function usePolicyUpdates() {
  return useQuery({
    queryKey: ['policy', 'updates'],
    queryFn: policyApi.getPolicyUpdates,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCarbonPrices() {
  return useQuery({
    queryKey: ['policy', 'carbon'],
    queryFn: policyApi.getCarbonPrices,
    staleTime: 5 * 60 * 1000,
  })
}

export function useSustainabilityMetrics() {
  return useQuery({
    queryKey: ['policy', 'sustainability'],
    queryFn: policyApi.getSustainabilityMetrics,
    staleTime: 10 * 60 * 1000,
  })
}

export function usePolicyTimeline() {
  return useQuery({
    queryKey: ['policy', 'timeline'],
    queryFn: policyApi.getTimeline,
    staleTime: 10 * 60 * 1000,
  })
}

export function usePolicyKanban() {
  return useQuery({
    queryKey: ['policy', 'kanban'],
    queryFn: policyApi.getKanban,
    staleTime: 10 * 60 * 1000,
  })
}

export function useMandateScenarios() {
  return useQuery({
    queryKey: ['policy', 'mandates'],
    queryFn: policyApi.getMandateScenarios,
    staleTime: 10 * 60 * 1000,
  })
}

export function useCarbonCalculator() {
  return useMutation({
    mutationFn: policyApi.calculateCarbon,
  })
}

export function useOfftakeMarket() {
  return useQuery({
    queryKey: ['policy', 'offtake'],
    queryFn: policyApi.getOfftakeMarket,
    staleTime: 10 * 60 * 1000,
  })
}
