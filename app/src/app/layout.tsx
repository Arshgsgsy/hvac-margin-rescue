import type { Metadata } from 'next'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Margin Rescue | HVAC Cash Recovery Agent',
  description: 'Action-first HVAC portfolio recovery plans focused on cash, margin protection, and next-best moves.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground antialiased">
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
