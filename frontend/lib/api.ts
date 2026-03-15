import axios from 'axios'
import type { SignalResponse, StockDetailResponse } from './types'

export type { SignalResponse, StockDetailResponse }

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: BASE, timeout: 15000 })

export async function fetchSignals(minScore?: number, signal?: string): Promise<SignalResponse[]> {
  const params: Record<string, string | number> = {}
  if (minScore) params.min_score = minScore
  if (signal) params.signal = signal
  const { data } = await api.get('/signals', { params })
  return data
}

export async function fetchStock(ticker: string): Promise<StockDetailResponse> {
  const { data } = await api.get(`/stocks/${ticker.toUpperCase()}`)
  return data
}

export async function fetchOptionsFlow(limit = 20) {
  const { data } = await api.get('/options-flow', { params: { limit } })
  return data
}

export async function fetchDarkPool(limit = 20) {
  const { data } = await api.get('/darkpool', { params: { limit } })
  return data
}

export async function fetchGamma(limit = 20) {
  const { data } = await api.get('/gamma', { params: { limit } })
  return data
}

export async function fetchAIPredictions(limit = 20) {
  const { data } = await api.get('/ai-predictions', { params: { limit } })
  return data
}

export async function fetchAlerts() {
  const { data } = await api.get('/alerts')
  return data
}

export const exportUrls = {
  csv: `${BASE}/export/csv`,
  json: `${BASE}/export/json`,
  excel: `${BASE}/export/excel`,
}

export function scoreColor(score: number): string {
  if (score >= 85) return '#00d084'
  if (score >= 70) return '#f97316'
  if (score >= 40) return '#f59e0b'
  return '#64748b'
}

export function scoreLabel(score: number): string {
  if (score >= 85) return 'EXPLOSIVE'
  if (score >= 70) return 'STRONG'
  if (score >= 40) return 'ACCUMULATION'
  return 'WEAK'
}

export function fmt(n: number, decimals = 2): string {
  return n.toFixed(decimals)
}

export function fmtMoney(n: number): string {
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

export function fmtMarketCap(n: number): string {
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  return `$${(n / 1e6).toFixed(0)}M`
}
