import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getProject } from '@/lib/data'
import ProjectDrilldown from '@/components/project-drilldown'

interface Props {
  params: { id: string }
}

export default function ProjectPage({ params }: Props) {
  const project = getProject(params.id)
  if (!project) notFound()

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
