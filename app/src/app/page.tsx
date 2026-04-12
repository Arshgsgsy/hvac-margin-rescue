'use client'

import { useState } from 'react'
import { UploadPage } from '@/components/upload-page'
import { ResultsView } from '@/components/results-view'
import { InvestigateModal } from '@/components/investigate-modal'
import { Project } from '@/lib/types'

type AppState = 'upload' | 'results'

export default function Home() {
  const [appState, setAppState] = useState<AppState>('upload')
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)

  // Handle pipeline completion - show results view
  const handlePipelineComplete = () => {
    setAppState('results')
  }

  // Handle investigating a project - opens modal
  const handleInvestigate = (project: Project) => {
    setSelectedProject(project)
  }

  // Close investigate modal
  const handleCloseInvestigate = () => {
    setSelectedProject(null)
  }

  // Upload page with auto-running pipeline
  if (appState === 'upload') {
    return <UploadPage onComplete={handlePipelineComplete} />
  }

  // Results view showing projects by severity with modal overlay
  return (
    <>
      <ResultsView onInvestigate={handleInvestigate} />
      {selectedProject && (
        <InvestigateModal 
          project={selectedProject} 
          onClose={handleCloseInvestigate} 
        />
      )}
    </>
  )
}
