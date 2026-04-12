'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import ProjectDrilldown from '@/components/project-drilldown'
import { fetchProject } from '@/lib/api'
import { Project } from '@/lib/types'
import { Loader2 } from 'lucide-react'

export default function ProjectPage() {
  const params = useParams()
  const id = params.id as string
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchProject(id)
      .then(setProject)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0a0f1e' }}>
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0a0f1e' }}>
        <div className="text-center">
          <p className="text-red-400 mb-2">Project not found</p>
          <Link href="/" className="text-blue-400 text-sm">Back to portfolio</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ background: '#0a0f1e' }}>
      <header className="border-b" style={{ borderColor: '#1e3a5f', background: '#0d1526' }}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/" className="text-sm flex items-center gap-1.5" style={{ color: '#64748b' }}>
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Portfolio
          </Link>
          <span style={{ color: '#1e3a5f' }}>/</span>
          <span className="text-white font-medium">{project.id}</span>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8">
        <ProjectDrilldown project={project} />
      </main>
    </div>
  )
}
