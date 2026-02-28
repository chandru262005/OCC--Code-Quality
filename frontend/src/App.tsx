import { useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { CheckCircle2, XCircle, Code2, Loader2, ArrowRight, ShieldAlert, FileCode2, DatabaseZap } from "lucide-react"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ""

export default function App() {
  const [analyzing, setAnalyzing] = useState(false)
  const [report, setReport] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [inputType, setInputType] = useState<"file" | "github">("file")
  const [repoUrl, setRepoUrl] = useState("")
  const [threshold, setThreshold] = useState("6.0")
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleAnalyzeFile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!fileInputRef.current?.files?.[0]) return

    setAnalyzing(true)
    setReport(null)
    setError(null)

    const formData = new FormData()
    formData.append("file", fileInputRef.current.files[0])
    formData.append("threshold", threshold)

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/analyze/file`, {
        method: "POST",
        body: formData,
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => null)
        throw new Error(errData?.detail || `Server error: ${res.status}`)
      }
      const data = await res.json()
      setReport(data)
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : "Failed to connect to the analysis server.")
    } finally {
      setAnalyzing(false)
    }
  }

  const handleAnalyzeGithub = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!repoUrl) return

    setAnalyzing(true)
    setReport(null)
    setError(null)

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/analyze/github`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, threshold: parseFloat(threshold) }),
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => null)
        throw new Error(errData?.detail || `Server error: ${res.status}`)
      }
      const data = await res.json()
      setReport(data)
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : "Failed to connect to the analysis server.")
    } finally {
      setAnalyzing(false)
    }
  }

  const getScoreColorClass = (score: number) => {
    if (score >= parseFloat(threshold)) return 'text-[var(--success)]'
    if (score >= 5) return 'text-[var(--warning)]'
    return 'text-[var(--error)]'
  }

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)] selection:bg-[var(--primary)] selection:text-white flex flex-col items-center">
      {/* Editorial Header */}
      <header className="w-full max-w-[1600px] border-b border-[var(--border)] px-6 py-8 md:py-12 flex flex-col md:flex-row md:items-end justify-between gap-6 bg-[var(--background)] sticky top-0 z-50">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 bg-[var(--primary)] rounded-none" />
            <span className="font-mono text-xs uppercase tracking-widest font-bold text-[var(--muted-foreground)]">System Diagnostics</span>
          </div>
          <h1 className="editorial-title">Code Quality Gate</h1>
        </div>
        <div className="flex gap-8 text-sm font-mono border-l border-[var(--border)] pl-8 py-2">
          <div className="flex flex-col">
            <span className="text-[var(--muted-foreground)] uppercase text-xs mb-1 tracking-wider">Engine Status</span>
            <span className="font-bold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--success)] inline-block"></span> Operational
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-[var(--muted-foreground)] uppercase text-xs mb-1 tracking-wider">Active Rulesets</span>
            <span className="font-bold">Flake8, Radon, Sec[42]</span>
          </div>
        </div>
      </header>

      {/* Main Structural Grid */}
      <main className="w-full max-w-[1600px] flex-1 grid grid-cols-1 lg:grid-cols-[400px_1fr] border-l border-r border-[var(--border)]">
        
        {/* Left Sidebar: Controls (The "Instrument Panel") */}
        <div className="border-r border-[var(--border)] bg-[var(--background)] flex flex-col">
          <div className="p-8 border-b border-[var(--border)]">
            <h2 className="text-2xl font-bold mb-8 flex items-center gap-2">
              <DatabaseZap className="w-6 h-6 text-[var(--primary)]" />
              Analysis Input
            </h2>
            
            <div className="flex rounded-none border border-[var(--border)] mb-8 bg-[var(--card)] p-1">
              <button 
                onClick={() => setInputType("file")}
                className={`flex-1 py-3 text-sm font-mono uppercase tracking-wider font-semibold transition-colors ${inputType === "file" ? "bg-[var(--primary)] text-white shadow-sm" : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)]"}`}
              >
                Local File
              </button>
              <button 
                onClick={() => setInputType("github")}
                className={`flex-1 py-3 text-sm font-mono uppercase tracking-wider font-semibold transition-colors ${inputType === "github" ? "bg-[var(--primary)] text-white shadow-sm" : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)]"}`}
              >
                Repository
              </button>
            </div>

            {inputType === "file" ? (
              <form onSubmit={handleAnalyzeFile} className="flex flex-col gap-6">
                <div className="flex flex-col gap-3">
                  <label className="text-sm font-mono text-[var(--foreground)] uppercase font-bold">Target File [.py]</label>
                  <input 
                    type="file" 
                    ref={fileInputRef}
                    accept=".py"
                    className="structural-input p-4 font-mono text-base w-full cursor-pointer file:mr-4 file:py-2 file:px-4 file:border file:border-[var(--primary)] file:bg-transparent file:text-[var(--primary)] file:font-mono file:text-sm file:font-bold file:uppercase file:cursor-pointer hover:file:bg-[var(--primary)] hover:file:text-white file:transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20 focus:border-[var(--primary)]"
                  />
                </div>
                <div className="flex flex-col gap-3">
                  <label className="text-sm font-mono text-[var(--foreground)] uppercase font-bold flex justify-between">
                    <span>Quality Threshold</span>
                    <span className="text-[var(--primary)] text-lg">{threshold}</span>
                  </label>
                  <input 
                    type="range" 
                    step="0.1" 
                    min="0" 
                    max="10" 
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    className="w-full accent-[var(--primary)] cursor-ew-resize h-2 bg-[var(--border)] rounded-none appearance-none"
                  />
                </div>
                <button 
                  type="submit" 
                  disabled={analyzing}
                  className="structural-button mt-6 py-4 px-6 flex items-center justify-center gap-3 uppercase tracking-widest text-base font-bold w-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--foreground)]"
                >
                  {analyzing ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                  {analyzing ? "Processing" : "Execute Scan"}
                </button>
              </form>
            ) : (
              <form onSubmit={handleAnalyzeGithub} className="flex flex-col gap-6">
                <div className="flex flex-col gap-3">
                  <label className="text-sm font-mono text-[var(--foreground)] uppercase font-bold">Repository URL</label>
                  <input 
                    type="url" 
                    placeholder="https://github.com/..."
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    className="structural-input p-4 font-mono text-base focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20 focus:border-[var(--primary)] placeholder:text-[var(--muted-foreground)]/50 bg-white"
                  />
                </div>
                <div className="flex flex-col gap-3">
                  <label className="text-sm font-mono text-[var(--foreground)] uppercase font-bold flex justify-between">
                    <span>Quality Threshold</span>
                    <span className="text-[var(--primary)] text-lg">{threshold}</span>
                  </label>
                  <input 
                    type="range" 
                    step="0.1" 
                    min="0" 
                    max="10" 
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    className="w-full accent-[var(--primary)] cursor-ew-resize h-2 bg-[var(--border)] rounded-none appearance-none"
                  />
                </div>
                <button 
                  type="submit" 
                  disabled={analyzing}
                  className="structural-button mt-6 py-4 px-6 flex items-center justify-center gap-3 uppercase tracking-widest text-base font-bold w-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--foreground)]"
                >
                  {analyzing ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                  {analyzing ? "Processing" : "Execute Scan"}
                </button>
              </form>
            )}
          </div>
          
          <div className="p-8 mt-auto bg-[var(--muted)]/50 text-sm font-mono text-[var(--muted-foreground)] leading-relaxed border-t border-[var(--border)]">
            <p className="font-bold text-[var(--foreground)] uppercase mb-3 border-b border-[var(--border)] pb-2 text-base">Analysis Protocol</p>
            <ul className="space-y-3 mt-4 text-[var(--foreground)] opacity-90 list-disc pl-5 marker:text-[var(--primary)]">
              <li>Upload local scripts or link remote repositories.</li>
              <li>Engine runs static AST analysis, complexity parsing, and security regex patterns.</li>
              <li>A score below the threshold triggers a gate failure.</li>
            </ul>
          </div>
        </div>

        {/* Right Area: Results (Editorial Layout) */}
        <div className="bg-[var(--background)] flex flex-col relative min-h-[600px] grid-paper">
          <AnimatePresence mode="wait">
            {!report && !analyzing && (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 flex flex-col items-center justify-center text-[var(--muted-foreground)]"
              >
                <div className="p-6 bg-white border border-[var(--border)] shadow-sm max-w-sm w-full mx-auto flex flex-col items-center text-center">
                  <FileCode2 className="w-12 h-12 mb-4 text-[var(--border)]" strokeWidth={1} />
                  <p className="font-mono text-sm uppercase tracking-widest font-bold">Standby Mode</p>
                  <p className="mt-2 text-sm">Provide input parameters to generate an analysis report.</p>
                </div>
              </motion.div>
            )}

            {analyzing && (
              <motion.div 
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--background)]/80 backdrop-blur-sm z-10"
              >
                <div className="p-8 bg-white border border-[var(--border)] shadow-md flex flex-col items-center">
                  <Loader2 className="w-10 h-10 animate-spin text-[var(--primary)] mb-6" />
                  <p className="font-mono text-sm uppercase tracking-widest font-bold text-[var(--foreground)]">Computing Metrics</p>
                  <div className="w-48 h-1 bg-[var(--border)] mt-4 overflow-hidden">
                    <motion.div 
                      className="h-full bg-[var(--primary)]"
                      initial={{ width: "0%" }}
                      animate={{ width: "100%" }}
                      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {error && !analyzing && (
              <motion.div
                key="error"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 flex flex-col items-center justify-center text-[var(--muted-foreground)]"
              >
                <div className="p-6 bg-white border border-[var(--error)] shadow-sm max-w-sm w-full mx-auto flex flex-col items-center text-center">
                  <XCircle className="w-12 h-12 mb-4 text-[var(--error)]" strokeWidth={1} />
                  <p className="font-mono text-sm uppercase tracking-widest font-bold text-[var(--error)]">Analysis Failed</p>
                  <p className="mt-2 text-sm text-[var(--foreground)]">{error}</p>
                </div>
              </motion.div>
            )}

            {report && !analyzing && (
              <motion.div 
                key="results"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                className="w-full h-full flex flex-col bg-white border-l border-[var(--border)] relative z-20"
              >
                {/* Score Header */}
                <div className="p-8 md:p-12 border-b border-[var(--border)] flex flex-col md:flex-row justify-between items-start md:items-center gap-8 bg-[var(--background)]">
                  <div className="flex flex-col">
                    <span className="text-sm font-mono font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-2">Aggregate Score</span>
                    <div className="flex items-baseline gap-2">
                      <span className={`score-display ${getScoreColorClass(report.score)}`}>
                        {report.score?.toFixed(1) || '0.0'}
                      </span>
                      <span className="text-3xl font-mono text-[var(--muted-foreground)]">/10</span>
                    </div>
                  </div>
                  
                  <div className="flex flex-col items-start md:items-end gap-4 min-w-[200px]">
                    <div className={`status-badge text-base py-3 px-6 shadow-sm border ${report.passed_gate ? 'success border-[var(--success)]' : 'error border-[var(--error)]'}`}>
                      {report.passed_gate ? (
                        <><CheckCircle2 className="w-5 h-5 mr-3 inline" /> Quality Gate Passed</>
                      ) : (
                        <><XCircle className="w-5 h-5 mr-3 inline" /> Quality Gate Failed</>
                      )}
                    </div>
                    <div className="flex flex-col w-full border border-[var(--border)] bg-[var(--card)] shadow-sm">
                      <div className="flex justify-between p-4 border-b border-[var(--border)] text-base">
                        <span className="font-mono font-semibold text-[var(--muted-foreground)]">Threshold Required</span>
                        <span className="font-bold text-[var(--primary)] text-lg">{threshold}</span>
                      </div>
                      <div className="flex justify-between p-4 text-base">
                        <span className="font-mono font-semibold text-[var(--muted-foreground)]">Target</span>
                        <span className="font-mono font-bold truncate max-w-[150px]">{report.target || 'unknown'}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Sub-metrics */}
                <div className="grid grid-cols-1 md:grid-cols-3 border-b border-[var(--border)] bg-[var(--background)] divide-y md:divide-y-0 md:divide-x divide-[var(--border)]">
                  <div className="p-8 flex flex-col items-center justify-center text-center">
                    <span className="text-sm font-mono font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-3">Linting & Style</span>
                    <span className="text-5xl font-bold">{report.metrics?.lint_score?.toFixed(1) || '0.0'}</span>
                  </div>
                  <div className="p-8 flex flex-col items-center justify-center text-center">
                    <span className="text-sm font-mono font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-3">Static & Complexity</span>
                    <span className="text-5xl font-bold">{report.metrics?.static_score?.toFixed(1) || '0.0'}</span>
                  </div>
                  <div className="p-8 flex flex-col items-center justify-center text-center">
                    <span className="text-sm font-mono font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-3">Security Patterns</span>
                    <span className={`text-5xl font-bold ${(report.metrics?.security_score || 0) < 10 ? 'text-[var(--error)]' : 'text-[var(--success)]'}`}>
                      {report.metrics?.security_score?.toFixed(1) || '0.0'}
                    </span>
                  </div>
                </div>

                {/* Details Sections */}
                <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-[var(--border)] flex-1 bg-[var(--background)]">
                  
                  {/* Security Flaws */}
                  <div className="p-8 flex flex-col h-full bg-[var(--card)]/50">
                    <h3 className="text-xl font-bold flex items-center gap-3 mb-6 text-[var(--error)] border-b border-[var(--error)]/20 pb-4">
                      <ShieldAlert className="w-6 h-6" />
                      Security Violations
                    </h3>
                    <div className="flex-1 space-y-4">
                      {!report.details?.security || report.details.security.length === 0 ? (
                        <div className="border border-[var(--success)] bg-[var(--success-bg)] p-5 text-base font-mono text-[var(--success)] font-bold flex items-center gap-3 shadow-sm">
                          <CheckCircle2 className="w-5 h-5" /> No vulnerabilities detected.
                        </div>
                      ) : (
                        report.details.security.map((sec: any, i: number) => (
                          <div key={i} className="bg-[var(--card)] border border-[var(--error)] p-5 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-3 border-b border-[var(--border)] pb-3">
                              <span className="font-mono text-sm font-bold text-[var(--error)] uppercase px-3 py-1 bg-[var(--error-bg)] border border-[var(--error)]">Line {sec.line || '?'}</span>
                              <span className="font-mono text-sm text-[var(--muted-foreground)] uppercase font-semibold">{sec.type}</span>
                            </div>
                            <p className="text-base font-medium mt-4 text-[var(--foreground)]">{sec.message || sec.description}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Lint & Static */}
                  <div className="p-8 flex flex-col h-full bg-[var(--card)]/50">
                    <h3 className="text-xl font-bold flex items-center gap-3 mb-6 text-[var(--warning)] border-b border-[var(--warning)]/20 pb-4">
                      <Code2 className="w-6 h-6" />
                      Code Smells & Lint
                    </h3>
                    <div className="flex-1 space-y-4 overflow-y-auto max-h-[500px] pr-4 custom-scrollbar">
                      {[...(report.details?.lint || []), ...(report.details?.static || [])].length === 0 ? (
                        <div className="border border-[var(--success)] bg-[var(--success-bg)] p-5 text-base font-mono text-[var(--success)] font-bold flex items-center gap-3 shadow-sm">
                          <CheckCircle2 className="w-5 h-5" /> Code meets quality standards.
                        </div>
                      ) : (
                        [...(report.details?.lint || []), ...(report.details?.static || [])].map((issue: any, i: number) => (
                          <div key={i} className="bg-[var(--card)] border border-[var(--warning)] p-5 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-3 border-b border-[var(--border)] pb-3">
                              <span className="font-mono text-sm font-bold text-[var(--warning)] uppercase px-3 py-1 bg-[var(--warning-bg)] border border-[var(--warning)]">Line {issue.line || '?'}</span>
                              <span className="font-mono text-sm text-[var(--muted-foreground)] uppercase font-semibold">{issue.code || issue.type}</span>
                            </div>
                            <p className="text-base font-medium mt-4 text-[var(--foreground)]">{issue.message || issue.description}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>

              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="w-full max-w-[1600px] border-t border-[var(--border)] p-6 bg-[var(--background)] flex justify-between items-center text-xs font-mono text-[var(--muted-foreground)] uppercase">
        <span>CQG-8000 Engine v1.2</span>
        <span>Strict Enforcement Mode</span>
      </footer>
    </div>
  )
}