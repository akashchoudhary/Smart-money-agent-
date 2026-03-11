import React, { useEffect, useRef } from 'react'
import { PricePoint } from '../lib/types'

interface Props {
  data: PricePoint[]
  ticker: string
}

export default function StockChart({ data, ticker }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<any>(null)

  useEffect(() => {
    if (!containerRef.current || !data.length) return

    let chart: any = null

    // Dynamic import to avoid SSR issues
    import('lightweight-charts').then(({ createChart, ColorType, CrosshairMode }) => {
      if (!containerRef.current) return

      chart = createChart(containerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: '#0f1623' },
          textColor: '#64748b',
        },
        grid: {
          vertLines: { color: '#1e2d45' },
          horzLines: { color: '#1e2d45' },
        },
        crosshair: { mode: CrosshairMode.Normal },
        rightPriceScale: { borderColor: '#1e2d45' },
        timeScale: { borderColor: '#1e2d45', timeVisible: true },
        width: containerRef.current.clientWidth,
        height: 300,
      })

      const candleSeries = chart.addCandlestickSeries({
        upColor: '#00d084',
        downColor: '#ff4d6d',
        borderUpColor: '#00d084',
        borderDownColor: '#ff4d6d',
        wickUpColor: '#00d084',
        wickDownColor: '#ff4d6d',
      })

      candleSeries.setData(
        data.map(p => ({
          time: p.time,
          open: p.open,
          high: p.high,
          low: p.low,
          close: p.close,
        }))
      )

      chart.timeScale().fitContent()
      chartRef.current = chart

      const handleResize = () => {
        if (containerRef.current && chart) {
          chart.applyOptions({ width: containerRef.current.clientWidth })
        }
      }
      window.addEventListener('resize', handleResize)
      return () => window.removeEventListener('resize', handleResize)
    })

    return () => {
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
      }
    }
  }, [data])

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-4 py-3 border-b" style={{ borderColor: '#1e2d45' }}>
        <h3 className="font-bold text-white text-sm">{ticker} — Price Chart (90 days)</h3>
      </div>
      <div ref={containerRef} className="w-full" style={{ minHeight: 300 }} />
    </div>
  )
}
