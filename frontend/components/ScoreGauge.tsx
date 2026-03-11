import React from 'react'
import { scoreColor, scoreLabel } from '../lib/api'

interface Props { score: number; label?: string }

export default function ScoreGauge({ score, label }: Props) {
  const color = scoreColor(score)
  const pct = Math.min(100, score)
  const circumference = 2 * Math.PI * 45
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-28 h-28">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" fill="none" stroke="#1e2d45" strokeWidth="8" />
          <circle
            cx="50" cy="50" r="45" fill="none"
            stroke={color} strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color }}>{score.toFixed(0)}</span>
          <span className="text-xs" style={{ color: '#64748b' }}>/ 100</span>
        </div>
      </div>
      {label && <span className="text-xs font-bold" style={{ color }}>{scoreLabel(score)}</span>}
    </div>
  )
}
