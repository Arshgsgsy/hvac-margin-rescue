'use client'

import { useState, useEffect } from 'react'
import { FileUploadZone } from './file-upload-zone'
import { 
  BarChart3, 
  Shield, 
  Zap, 
  TrendingUp, 
  ArrowRight,
  ChevronDown,
  Sparkles
} from 'lucide-react'

const FEATURES = [
  {
    icon: BarChart3,
    title: 'Portfolio Analytics',
    description: 'Get instant visibility into your entire project portfolio with AI-powered insights.',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Shield,
    title: 'Risk Detection',
    description: 'Identify cost overruns and margin erosion before they become critical issues.',
    color: 'from-primary to-pink-500',
  },
  {
    icon: Zap,
    title: 'Instant Processing',
    description: 'Upload your data and receive comprehensive analysis in seconds, not hours.',
    color: 'from-amber-500 to-orange-500',
  },
  {
    icon: TrendingUp,
    title: 'Recovery Opportunities',
    description: 'Discover actionable insights to recover margins and optimize performance.',
    color: 'from-emerald-500 to-teal-500',
  },
]

const STATS = [
  { value: '$2.3M+', label: 'Margin Recovered' },
  { value: '98%', label: 'Accuracy Rate' },
  { value: '150+', label: 'Projects Analyzed' },
  { value: '< 30s', label: 'Analysis Time' },
]

export function LandingPage() {
  const [mounted, setMounted] = useState(false)
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    setMounted(true)
    const handleScroll = () => setScrollY(window.scrollY)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Animated background elements */}
      <div className="fixed inset-0 pointer-events-none">
        <div 
          className="absolute top-20 left-10 w-72 h-72 bg-primary/30 rounded-full blur-[100px] animate-float"
          style={{ transform: `translateY(${scrollY * 0.1}px)` }}
        />
        <div 
          className="absolute top-40 right-20 w-96 h-96 bg-pink-500/20 rounded-full blur-[120px] animate-float animation-delay-200"
          style={{ transform: `translateY(${scrollY * -0.05}px)` }}
        />
        <div 
          className="absolute bottom-20 left-1/3 w-80 h-80 bg-cyan-500/20 rounded-full blur-[100px] animate-float animation-delay-400"
          style={{ transform: `translateY(${scrollY * 0.08}px)` }}
        />
      </div>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-pink-500 flex items-center justify-center animate-pulse-glow">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-foreground">MarginIQ</span>
          </div>
          
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#upload" className="text-muted-foreground hover:text-foreground transition-colors">Upload</a>
            <a href="#stats" className="text-muted-foreground hover:text-foreground transition-colors">Results</a>
          </div>
          
          <button className="px-5 py-2.5 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary-dark transition-all hover:shadow-lg hover:shadow-primary/25">
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-20 pb-32 px-6">
        <div className="max-w-7xl mx-auto text-center">
          {/* Badge */}
          <div 
            className={`
              inline-flex items-center gap-2 px-4 py-2 rounded-full
              bg-primary/10 border border-primary/20 mb-8
              transition-all duration-700
              ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
            `}
          >
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">AI-Powered Financial Intelligence</span>
          </div>

          {/* Main headline */}
          <h1 
            className={`
              text-5xl md:text-7xl font-bold leading-tight
              transition-all duration-700 delay-100
              ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
            `}
          >
            <span className="text-foreground">Transform Your</span>
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-pink-500 to-cyan-500 animate-gradient">
              Financial Data
            </span>
          </h1>

          <p 
            className={`
              mt-6 text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed
              transition-all duration-700 delay-200
              ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
            `}
          >
            Upload your project data and unlock powerful insights. Our AI analyzes margin variances, 
            identifies risks, and reveals recovery opportunities in seconds.
          </p>

          {/* CTA buttons */}
          <div 
            className={`
              mt-10 flex flex-col sm:flex-row items-center justify-center gap-4
              transition-all duration-700 delay-300
              ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
            `}
          >
            <a 
              href="#upload"
              className="
                group flex items-center gap-2 px-8 py-4 rounded-2xl
                bg-gradient-to-r from-primary to-pink-500
                text-white font-semibold text-lg
                shadow-xl shadow-primary/30
                hover:shadow-2xl hover:shadow-primary/40
                hover:scale-105 transition-all duration-300
              "
            >
              Upload Your Data
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </a>
            <button className="
              flex items-center gap-2 px-8 py-4 rounded-2xl
              border border-border bg-card/50 backdrop-blur
              text-foreground font-semibold text-lg
              hover:bg-card hover:border-primary/30 transition-all
            ">
              Watch Demo
            </button>
          </div>

          {/* Scroll indicator */}
          <div 
            className={`
              mt-20 flex flex-col items-center gap-2 text-muted-foreground
              transition-all duration-700 delay-500
              ${mounted ? 'opacity-100' : 'opacity-0'}
            `}
          >
            <span className="text-sm">Scroll to explore</span>
            <ChevronDown className="w-5 h-5 animate-bounce" />
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section id="stats" className="py-20 px-6 border-y border-border/50 bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {STATS.map((stat, i) => (
              <div 
                key={stat.label}
                className="text-center animate-slide-up-fade"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <p className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-pink-500">
                  {stat.value}
                </p>
                <p className="mt-2 text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-foreground">
              Powerful Features
            </h2>
            <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
              Everything you need to understand your financial performance
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {FEATURES.map((feature, i) => {
              const Icon = feature.icon
              return (
                <div
                  key={feature.title}
                  className="
                    group relative p-8 rounded-3xl
                    bg-card border border-border
                    hover:border-primary/30 hover:shadow-xl hover:shadow-primary/5
                    transition-all duration-300 hover:-translate-y-1
                    animate-slide-up-fade
                  "
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                  {/* Gradient overlay on hover */}
                  <div className={`
                    absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100
                    bg-gradient-to-br ${feature.color} transition-opacity duration-300
                  `} style={{ opacity: 0.03 }} />
                  
                  <div className={`
                    w-14 h-14 rounded-2xl flex items-center justify-center
                    bg-gradient-to-br ${feature.color} text-white
                    group-hover:scale-110 transition-transform duration-300
                  `}>
                    <Icon className="w-7 h-7" />
                  </div>
                  
                  <h3 className="mt-6 text-xl font-semibold text-foreground">
                    {feature.title}
                  </h3>
                  <p className="mt-3 text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Upload Section */}
      <section id="upload" className="py-24 px-6 bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold text-foreground">
              Get Started Now
            </h2>
            <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
              Upload your financial data ZIP files and let our AI do the heavy lifting
            </p>
          </div>

          <FileUploadZone />

          <div className="mt-12 text-center">
            <p className="text-sm text-muted-foreground">
              Your data is encrypted and processed securely. We never store raw financial data.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="relative p-12 rounded-3xl bg-gradient-to-br from-primary/10 via-pink-500/10 to-cyan-500/10 border border-primary/20">
            {/* Animated border glow */}
            <div className="absolute inset-0 rounded-3xl animate-pulse-glow opacity-50" />
            
            <h2 className="relative text-3xl md:text-4xl font-bold text-foreground">
              Ready to Transform Your Financial Analysis?
            </h2>
            <p className="relative mt-4 text-lg text-muted-foreground">
              Join hundreds of teams already using MarginIQ to optimize their project performance.
            </p>
            <button className="
              relative mt-8 px-10 py-4 rounded-2xl
              bg-gradient-to-r from-primary to-pink-500
              text-white font-semibold text-lg
              shadow-xl shadow-primary/30
              hover:shadow-2xl hover:shadow-primary/40
              hover:scale-105 transition-all duration-300
            ">
              Start Free Trial
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-border/50">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-pink-500 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-foreground">MarginIQ</span>
          </div>
          <p className="text-sm text-muted-foreground">
            2026 MarginIQ. Built for financial excellence.
          </p>
        </div>
      </footer>
    </div>
  )
}
