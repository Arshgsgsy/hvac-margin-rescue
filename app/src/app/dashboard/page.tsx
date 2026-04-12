'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ArrowLeft, Loader2 } from 'lucide-react'

import { fetchPortfolioSummary, fetchProjects } from '@/lib/api'
import type { PortfolioSummary, Project } from '@/lib/types'
import HeroSection from '@/components/hero-section'
import PriorityQueue from '@/components/priority-queue'
import { AlertCard } from '@/components/alert-card'

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    Promise.all([fetchPortfolioSummary(), fetchProjects()])
      .then(([summary, flaggedProjects]) => {
        if (cancelled) return
        setPortfolio(summary)
        setProjects(flaggedProjects)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data.')
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0a0f1e' }}>
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6" style={{ background: '#0a0f1e' }}>
        <div className="max-w-xl rounded-2xl border border-red-500/30 bg-red-500/5 p-6 text-center">
          <p className="text-red-400 font-semibold">Dashboard unavailable</p>
          <p className="text-slate-300 text-sm mt-2">{error}</p>
          <Link href="/" className="inline-flex items-center gap-2 mt-5 text-sm text-blue-400">
            <ArrowLeft className="w-4 h-4" />
            Upload a dataset
          </Link>
        </div>
      </div>
    )
  }

  if (!portfolio || projects.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6" style={{ background: '#0a0f1e' }}>
        <div className="max-w-xl rounded-2xl border border-border/50 bg-card/80 p-6 text-center">
          <p className="text-white font-semibold">No flagged projects available.</p>
          <p className="text-slate-400 text-sm mt-2">Upload a dataset and run the pipeline to populate the dashboard.</p>
          <Link href="/" className="inline-flex items-center gap-2 mt-5 text-sm text-blue-400">
            <ArrowLeft className="w-4 h-4" />
            Upload a dataset
          </Link>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen px-6 py-8 space-y-8" style={{ background: '#0a0f1e' }}>
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="inline-flex items-center gap-2 text-sm" style={{ color: '#94a3b8' }}>
            <ArrowLeft className="w-4 h-4" />
            Upload another dataset
          </Link>
          {portfolio.data_availability?.degraded_mode && (
            <div className="rounded-full border border-yellow-500/30 bg-yellow-500/10 px-4 py-2 text-xs text-yellow-300">
              Running in degraded mode. Missing optional sources: {portfolio.data_availability.missing_features.join(', ')}
            </div>
          )}
        </div>

        <HeroSection projects={projects} portfolio={portfolio} />
        <PriorityQueue projects={projects} />

        <section id="all-projects" className="space-y-6">
          <div>
            <p className="text-xs font-semibold tracking-widest uppercase mb-1" style={{ color: '#60a5fa' }}>
              Full Queue
            </p>
            <h2 className="text-2xl md:text-3xl font-semibold text-white">
              All Flagged Projects
            </h2>
            <p className="text-slate-400 text-sm mt-1">
              Ranked by severity, billing gap, and overrun exposure. Open a project for the detailed drilldown.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {projects.map((project, index) => (
              <AlertCard key={project.id} project={project} rank={index + 1} />
            ))}
          </div>
        </section>
      </div>
    </main>
  )
}
