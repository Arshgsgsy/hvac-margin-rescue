'use client'

import { useState } from 'react'
import { UploadPage } from '@/components/upload-page'
import { ResultsView } from '@/components/results-view'
import { Project } from '@/lib/types'

type AppState = 'upload' | 'results' | 'investigate'

export default function Home() {
  const [appState, setAppState] = useState<AppState>('upload')
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)

  // Handle pipeline completion - show results view
  const handlePipelineComplete = () => {
    setAppState('results')
  }

  // Handle investigating a project
  const handleInvestigate = (project: Project) => {
    setSelectedProject(project)
    setAppState('investigate')
  }

  // Upload page with auto-running pipeline
  if (appState === 'upload') {
    return <UploadPage onComplete={handlePipelineComplete} />
  }

  // Results view showing projects by severity
  if (appState === 'results') {
    return <ResultsView onInvestigate={handleInvestigate} />
  }

  // TODO: Investigate view will be implemented in Step 3
  // For now, return to results if somehow in investigate state
  if (appState === 'investigate' && selectedProject) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-bold mb-2">Investigating: {selectedProject.name}</h2>
          <p className="text-muted-foreground mb-4">Investigation view coming in Step 3</p>
          <button 
            onClick={() => setAppState('results')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
          >
            Back to Results
          </button>
        </div>
      </div>
    )
  }

  return null
}
