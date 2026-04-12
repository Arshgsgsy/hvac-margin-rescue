import { NextResponse } from 'next/server'

// Pipeline runs in simulation mode - the real data processing was done offline
// and results are available in output_summaries/
export async function POST() {
  // Return success - the frontend will use its built-in simulation for the animation
  // The actual data comes from the pre-generated output_summaries JSON files
  return NextResponse.json({
    status: 'simulation',
    message: 'Pipeline running in simulation mode with pre-processed data',
    useSimulation: true,
  })
}
