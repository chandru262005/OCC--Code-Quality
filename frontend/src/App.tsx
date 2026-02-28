import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence, useSpring, useTransform } from "framer-motion"
import { CheckCircle2, XCircle, Code2, Loader2, ArrowRight, ShieldAlert, FileCode2, UploadCloud, File, Github } from "lucide-react"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ""

/** Transform the raw API response into the shape the UI expects */
function transformReport(raw: any) {
  const getAnalyzer = (name: string) =>
    raw.results?.find((r: any) => r.analyzer_name === name)

  return {
    score: raw.overall_score,
    passed_gate: raw.passed,
    target: raw.source === "upload" ? `${raw.files_analyzed} file(s)` : raw.source,
    metrics: {
      lint_score: getAnalyzer("lint")?.score ?? 0,
      static_score: getAnalyzer("static")?.score ?? 0,
      security_score: getAnalyzer("security")?.score ?? 0,
    },
    details: {
      lint: getAnalyzer("lint")?.issues ?? [],
      static: getAnalyzer("static")?.issues ?? [],
      security: getAnalyzer("security")?.issues ?? [],
    },
  }
}

// Custom hook for animated numbers
function AnimatedNumber({ value }: { value: number }) {
  const spring = useSpring(0, { mass: 0.8, stiffness: 75, damping: 15 })
  const display = useTransform(spring, (current) => current.toFixed(1))
  
  useEffect(() => {
    spring.set(value)
  }, [spring, value])

  return <motion.span>{display}</motion.span>
}

export default function App() {
  const [analyzing, setAnalyzing] = useState(false)
  const [loadingPhase, setLoadingPhase] = useState(0)
  const [report, setReport] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [inputType, setInputType] = useState<"file" | "github">("file")
  const [repoUrl, setRepoUrl] = useState("")
  const [threshold, setThreshold] = useState("6.0")
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Drag & drop state
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  // Rotate loading phases
  useEffect(() => {
    if (analyzing) {
      const phases = setInterval(() => {
        setLoadingPhase(p => (p + 1) % 4)
      }, 800)
      return () => clearInterval(phases)
    }
  }, [analyzing])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.name.endsWith('.py')) {
        setSelectedFile(file)
      } else {
        alert("Only .py files are supported.")
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleAnalyzeFile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return

    setAnalyzing(true)
    setReport(null)
    setError(null)
    setLoadingPhase(0)

    const formData = new FormData()
    formData.append("file", selectedFile)
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
      setReport(transformReport(data))
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
    setLoadingPhase(0)

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
      setReport(transformReport(data))
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

  const loadingMessages = [
    "Compiling AST graph...",
    "Running complexity checks...",
    "Scanning for vulnerability patterns...",
    "Generating final metrics..."
  ]

  return (
    <div className="min-h-screen text-[var(--foreground)] flex flex-col items-center relative overflow-hidden">
      <div className="ambient-glow" />
      <div className="noise-overlay" />

      {/* Main Container - Floats above the slightly off-white background to create depth */}
      <div className="w-full max-w-[1600px] flex-1 flex flex-col my-0 lg:my-8 shadow-[0_8px_40px_rgba(0,0,0,0.03)] bg-white border-x border-y border-[var(--border)] overflow-hidden relative z-10 lg:rounded-sm">
        
        {/* Editorial Header */}
        <header className="border-b border-[var(--border)] px-8 py-10 md:py-12 flex flex-col md:flex-row md:items-end justify-between gap-8 bg-white relative z-20">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-4 h-4 bg-[var(--primary)] rounded-none" />
              <span className="font-mono text-sm uppercase tracking-widest font-bold text-[var(--muted-foreground)]">CQG Diagnostics</span>
            </div>
            <h1 className="editorial-title">Code Quality Gate</h1>
          </div>
          <div className="flex gap-10 text-sm font-mono border-l border-[var(--border)] pl-10 py-2">
            <div className="flex flex-col">
              <span className="text-[var(--muted-foreground)] uppercase text-xs mb-2 tracking-wider">Engine Status</span>
              <span className="font-bold flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--success)] inline-block relative">
                  <span className="absolute inset-0 rounded-full bg-[var(--success)] animate-ping opacity-75"></span>
                </span> 
                Operational
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[var(--muted-foreground)] uppercase text-xs mb-2 tracking-wider">Active Rulesets</span>
              <span className="font-bold text-[var(--foreground)]">Flake8, Radon, Sec[42]</span>
            </div>
          </div>
        </header>

        {/* Main Structural Grid */}
        <main className="flex-1 grid grid-cols-1 lg:grid-cols-[450px_1fr]">
          
          {/* Left Sidebar: Controls (The "Instrument Panel") */}
          <div className="border-r border-[var(--border)] bg-white flex flex-col z-20 relative">
            <div className="absolute right-0 top-0 bottom-0 w-[1px] shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-[-1]"></div>
            
            <div className="p-8 border-b border-[var(--border)] flex items-center gap-4">
               <span className="font-mono font-bold text-4xl text-[var(--border)] pointer-events-none">01</span>
               <h2 className="text-xl font-bold uppercase tracking-widest text-[var(--foreground)]">Input Source</h2>
            </div>
            
            <div className="p-8 border-b border-[var(--border)] bg-white/50 backdrop-blur-sm">
              <div className="flex rounded-none border border-[var(--border)] mb-10 bg-[var(--background)] p-1.5 shadow-[inset_0_1px_2px_rgba(0,0,0,0.02)]">
                <button 
                  onClick={() => { setInputType("file"); setReport(null); setSelectedFile(null); }}
                  className={`flex-1 py-3 text-sm font-mono uppercase tracking-wider font-bold transition-all ${inputType === "file" ? "bg-white text-[var(--primary)] shadow-[0_1px_3px_rgba(0,0,0,0.1)] border border-[var(--border)]" : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-black/5"}`}
                >
                  Local File
                </button>
                <button 
                  onClick={() => { setInputType("github"); setReport(null); }}
                  className={`flex-1 py-3 text-sm font-mono uppercase tracking-wider font-bold transition-all ${inputType === "github" ? "bg-white text-[var(--primary)] shadow-[0_1px_3px_rgba(0,0,0,0.1)] border border-[var(--border)]" : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-black/5"}`}
                >
                  Repository
                </button>
              </div>

              {inputType === "file" ? (
                <form onSubmit={handleAnalyzeFile} className="flex flex-col gap-8">
                  <div className="flex flex-col gap-4">
                    <label className="text-sm font-mono text-[var(--foreground)] uppercase font-bold">Target File [.py]</label>
                    
                    {/* Interactive Dropzone */}
                    <div 
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed transition-all duration-200 cursor-pointer ${isDragging ? 'border-[var(--primary)] bg-[var(--primary)]/5 scale-[1.02]' : selectedFile ? 'border-[var(--success)] bg-[var(--success-bg)]/50' : 'border-[var(--border)] hover:border-[var(--primary)]/50 hover:bg-[var(--muted)]'}`}
                    >
                      <input 
                        type="file" 
                        ref={fileInputRef}
                        accept=".py"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                      {selectedFile ? (
                        <div className="flex flex-col items-center gap-3 text-[var(--success)]">
                          <File className="w-10 h-10" />
                          <span className="font-mono font-bold text-base">{selectedFile.name}</span>
                          <span className="text-xs text-[var(--foreground)] opacity-60 uppercase font-mono mt-1 hover:underline">Click to change</span>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-4 text-[var(--muted-foreground)]">
                          <UploadCloud className={`w-12 h-12 ${isDragging ? 'text-[var(--primary)]' : ''} transition-colors`} />
                          <div className="text-center">
                            <span className="font-bold text-[var(--foreground)]">Click to upload</span> or drag and drop<br/>
                            <span className="font-mono text-xs uppercase mt-2 inline-block font-semibold">Python Scripts Only (.py)</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col gap-4">
                    <label className="text-sm font-mono text-[var(--foreground)] uppercase font-bold flex justify-between">
                      <span>Quality Threshold</span>
                      <span className="text-[var(--primary)] text-xl">{threshold}</span>
                    </label>
                    <div className="relative pt-2 pb-4">
                      <input 
                        type="range" 
                        step="0.1" 
                        min="0" 
                        max="10" 
                        value={threshold}
                        onChange={(e) => setThreshold(e.target.value)}
                        className="w-full"
                      />
                    </div>
                  </div>

                  <button 
                    type="submit" 
                    disabled={analyzing || !selectedFile}
                    className="structural-button mt-4 py-5 px-6 flex items-center justify-center gap-3 uppercase tracking-widest text-base font-bold w-full"
                  >
                    {analyzing ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowRight className="w-5 h-5" />}
                    {analyzing ? "Processing..." : "Execute Scan"}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleAnalyzeGithub} className="flex flex-col gap-8">
                  <div className="flex flex-col gap-4">
                    <label className="text-sm font-mono text-[var(--foreground)] uppercase font-bold flex items-center gap-2">
                      <Github className="w-4 h-4" /> Repository URL
                    </label>
                    <input 
                      type="url" 
                      placeholder="https://github.com/user/repo"
                      value={repoUrl}
                      onChange={(e) => setRepoUrl(e.target.value)}
                      className="structural-input p-4 font-mono text-base bg-white"
                      required
                    />
                  </div>
                  
                  <div className="flex flex-col gap-4">
                    <label className="text-sm font-mono text-[var(--foreground)] uppercase font-bold flex justify-between">
                      <span>Quality Threshold</span>
                      <span className="text-[var(--primary)] text-xl">{threshold}</span>
                    </label>
                    <div className="relative pt-2 pb-4">
                      <input 
                        type="range" 
                        step="0.1" 
                        min="0" 
                        max="10" 
                        value={threshold}
                        onChange={(e) => setThreshold(e.target.value)}
                        className="w-full"
                      />
                    </div>
                  </div>
                  
                  <button 
                    type="submit" 
                    disabled={analyzing || !repoUrl}
                    className="structural-button mt-4 py-5 px-6 flex items-center justify-center gap-3 uppercase tracking-widest text-base font-bold w-full"
                  >
                    {analyzing ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowRight className="w-5 h-5" />}
                    {analyzing ? "Processing..." : "Execute Scan"}
                  </button>
                </form>
              )}
            </div>

            <div className="p-8 mt-auto bg-[var(--muted)]/50 text-sm font-mono text-[var(--muted-foreground)] leading-relaxed">
              <p className="font-bold text-[var(--foreground)] uppercase mb-4 border-b border-[var(--border)] pb-3 tracking-widest text-xs">Analysis Protocol</p>
              <ul className="space-y-3 mt-4 text-[var(--foreground)] opacity-80 list-disc pl-5 marker:text-[var(--primary)]">
                <li>Upload local scripts or link remote repositories.</li>
                <li>Engine runs static AST analysis, complexity parsing, and security regex patterns.</li>
                <li>A score below the threshold triggers a gate failure.</li>
              </ul>
            </div>
          </div>

          {/* Right Area: Results */}
          <div className="bg-[var(--background)]/30 flex flex-col relative min-h-[700px] grid-paper z-10">
            {/* Header for right side */}
            <div className="p-8 border-b border-[var(--border)] flex items-center gap-4 bg-white/80 backdrop-blur-md sticky top-0 z-30">
               <span className="font-mono font-bold text-4xl text-[var(--border)] pointer-events-none">02</span>
               <h2 className="text-xl font-bold uppercase tracking-widest text-[var(--foreground)]">Analysis Output</h2>
            </div>

            <div className="flex-1 relative bg-white">
              <AnimatePresence mode="wait">
                {!report && !analyzing && !error && (
                  <motion.div 
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 flex flex-col items-center justify-center text-[var(--muted-foreground)] bg-transparent"
                  >
                    <div className="p-10 border border-[var(--border)] max-w-md w-full mx-auto flex flex-col items-center text-center bg-white shadow-[0_8px_30px_rgba(0,0,0,0.02)]">
                      <FileCode2 className="w-16 h-16 mb-6 text-[var(--border)]" strokeWidth={1} />
                      <p className="font-mono text-base uppercase tracking-widest font-bold text-[var(--foreground)]">Standby Mode</p>
                      <p className="mt-3 text-sm leading-relaxed">System is awaiting input parameters. Provide a file or repository to generate a full analysis report.</p>
                    </div>
                  </motion.div>
                )}

                {analyzing && (
                  <motion.div 
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 flex flex-col items-center justify-center z-10 bg-white/80 backdrop-blur-sm"
                  >
                    <div className="p-12 border border-[var(--border)] max-w-sm w-full flex flex-col items-center bg-white shadow-xl relative overflow-hidden">
                      <Loader2 className="w-12 h-12 animate-spin text-[var(--primary)] mb-8" strokeWidth={1.5} />
                      <p className="font-mono text-sm uppercase tracking-widest font-bold text-[var(--foreground)] mb-2">Diagnostic Scan</p>
                      <AnimatePresence mode="wait">
                        <motion.p 
                          key={loadingPhase}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -5 }}
                          className="text-sm font-mono text-[var(--muted-foreground)] mb-8 h-5 font-medium"
                        >
                          {loadingMessages[loadingPhase]}
                        </motion.p>
                      </AnimatePresence>
                      <div className="w-full h-1 bg-[var(--border)] overflow-hidden absolute bottom-0 left-0">
                        <motion.div 
                          className="h-full bg-[var(--primary)]"
                          initial={{ width: "0%" }}
                          animate={{ width: "100%" }}
                          transition={{ duration: 2, ease: "linear", repeat: Infinity }}
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
                    <div className="p-8 bg-white border border-[var(--error)] shadow-lg max-w-md w-full mx-auto flex flex-col items-center text-center relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-full h-1 bg-[var(--error)]"></div>
                      <XCircle className="w-16 h-16 mb-6 text-[var(--error)]" strokeWidth={1.5} />
                      <p className="font-mono text-base uppercase tracking-widest font-bold text-[var(--error)]">Analysis Failed</p>
                      <p className="mt-3 text-base text-[var(--foreground)] font-medium">{error}</p>
                    </div>
                  </motion.div>
                )}

                {report && !analyzing && (
                  <motion.div 
                    key="results"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                    className="w-full h-full flex flex-col bg-transparent relative z-20"
                  >
                    {/* Score Header */}
                    <div className="p-8 md:p-12 border-b border-[var(--border)] flex flex-col md:flex-row justify-between items-start md:items-center gap-10 bg-white relative overflow-hidden">
                      <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--primary)] opacity-[0.02] rounded-full blur-3xl translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>
                      
                      <div className="flex flex-col relative z-10">
                        <span className="text-sm font-mono font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-2">Aggregate Rating</span>
                        <div className="flex items-baseline gap-2">
                          <span className={`score-display ${getScoreColorClass(report.score)}`}>
                            <AnimatedNumber value={report.score || 0} />
                          </span>
                          <span className="text-4xl font-mono text-[var(--muted-foreground)]">/10</span>
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-start md:items-end gap-5 min-w-[280px] relative z-10">
                        <motion.div 
                          initial={{ scale: 0.95, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          transition={{ delay: 0.2 }}
                          className={`status-badge text-base py-4 px-6 shadow-sm border w-full justify-center md:w-auto ${report.passed_gate ? 'success border-[var(--success)] bg-[var(--success-bg)]/50' : 'error border-[var(--error)] bg-[var(--error-bg)]/50'}`}
                        >
                          {report.passed_gate ? (
                            <><CheckCircle2 className="w-6 h-6 mr-3 inline" /> Gate Passed</>
                          ) : (
                            <><XCircle className="w-6 h-6 mr-3 inline" /> Gate Failed</>
                          )}
                        </motion.div>
                        <div className="flex flex-col w-full border border-[var(--border)] bg-[var(--card)] shadow-sm">
                          <div className="flex justify-between p-4 border-b border-[var(--border)] text-sm">
                            <span className="font-mono font-bold uppercase tracking-wide text-[var(--muted-foreground)]">Threshold</span>
                            <span className="font-mono font-bold text-[var(--primary)] text-base">{threshold}</span>
                          </div>
                          <div className="flex justify-between p-4 text-sm">
                            <span className="font-mono font-bold uppercase tracking-wide text-[var(--muted-foreground)]">Target</span>
                            <span className="font-mono font-bold truncate max-w-[180px]">{report.target || 'unknown'}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Sub-metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-3 border-b border-[var(--border)] bg-white divide-y md:divide-y-0 md:divide-x divide-[var(--border)]">
                      <div className="p-8 md:p-10 flex flex-col items-center justify-center text-center">
                        <span className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-4">Linting / Style</span>
                        <span className="text-5xl font-bold text-[var(--foreground)]"><AnimatedNumber value={report.metrics?.lint_score || 0} /></span>
                      </div>
                      <div className="p-8 md:p-10 flex flex-col items-center justify-center text-center">
                        <span className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-4">Static / Complexity</span>
                        <span className="text-5xl font-bold text-[var(--foreground)]"><AnimatedNumber value={report.metrics?.static_score || 0} /></span>
                      </div>
                      <div className="p-8 md:p-10 flex flex-col items-center justify-center text-center bg-[var(--background)]/30">
                        <span className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-4">Security Vectors</span>
                        <span className={`text-5xl font-bold ${(report.metrics?.security_score || 0) < 10 ? 'text-[var(--error)]' : 'text-[var(--success)]'}`}>
                          <AnimatedNumber value={report.metrics?.security_score || 0} />
                        </span>
                      </div>
                    </div>

                    {/* Details Sections */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-[var(--border)] flex-1 bg-[var(--background)]/20">
                      
                      {/* Security Flaws */}
                      <div className="p-8 md:p-10 flex flex-col h-full bg-white">
                        <h3 className="text-xl font-bold flex items-center gap-3 mb-8 text-[var(--error)]">
                          <ShieldAlert className="w-6 h-6" />
                          Security Violations
                        </h3>
                        <div className="flex-1 space-y-4 pr-2">
                          {!report.details?.security || report.details.security.length === 0 ? (
                            <div className="border border-[var(--success)] bg-[var(--success-bg)] p-6 text-base font-mono text-[var(--success)] font-bold flex items-center gap-4 shadow-[0_2px_4px_rgba(0,0,0,0.02)]">
                              <CheckCircle2 className="w-6 h-6" /> No vulnerabilities detected.
                            </div>
                          ) : (
                            report.details.security.map((sec: any, i: number) => (
                              <motion.div 
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 + (i * 0.1) }}
                                key={i} 
                                className="bg-white border border-[var(--border)] p-6 shadow-[0_4px_12px_rgba(0,0,0,0.03)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] transition-all relative group"
                              >
                                <div className="absolute top-0 left-0 w-[3px] h-full bg-[var(--error)] group-hover:w-[5px] transition-all"></div>
                                <div className="flex justify-between items-start mb-4">
                                  <span className="font-mono text-xs font-bold text-[var(--error)] uppercase px-3 py-1.5 bg-[var(--error-bg)] border border-[var(--error)]/20">Line {sec.line || '?'}</span>
                                  <span className="font-mono text-xs text-[var(--error)] uppercase font-bold tracking-widest">{sec.rule || sec.severity}</span>
                                </div>
                                <p className="text-base font-medium mt-2 text-[var(--foreground)] leading-relaxed">{sec.message || sec.description}</p>
                              </motion.div>
                            ))
                          )}
                        </div>
                      </div>

                      {/* Lint & Static */}
                      <div className="p-8 md:p-10 flex flex-col h-full bg-white">
                        <h3 className="text-xl font-bold flex items-center gap-3 mb-8 text-[var(--warning)]">
                          <Code2 className="w-6 h-6" />
                          Code Smells & Lint
                        </h3>
                        <div className="flex-1 space-y-4 overflow-y-auto max-h-[600px] pr-4 custom-scrollbar">
                          {[...(report.details?.lint || []), ...(report.details?.static || [])].length === 0 ? (
                            <div className="border border-[var(--success)] bg-[var(--success-bg)] p-6 text-base font-mono text-[var(--success)] font-bold flex items-center gap-4 shadow-[0_2px_4px_rgba(0,0,0,0.02)]">
                              <CheckCircle2 className="w-6 h-6" /> Code meets quality standards.
                            </div>
                          ) : (
                            [...(report.details?.lint || []), ...(report.details?.static || [])].map((issue: any, i: number) => (
                              <motion.div 
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.4 + (i * 0.05) }}
                                key={i} 
                                className="bg-white border border-[var(--border)] p-6 shadow-[0_4px_12px_rgba(0,0,0,0.03)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] transition-all relative group"
                              >
                                <div className="absolute top-0 left-0 w-[3px] h-full bg-[var(--warning)] group-hover:w-[5px] transition-all"></div>
                                <div className="flex justify-between items-start mb-4">
                                  <span className="font-mono text-xs font-bold text-[var(--warning)] uppercase px-3 py-1.5 bg-[var(--warning-bg)] border border-[var(--warning)]/20">Line {issue.line || '?'}</span>
                                  <span className="font-mono text-xs text-[var(--warning)] uppercase font-bold tracking-widest">{issue.rule || issue.severity}</span>
                                </div>
                                <p className="text-base font-medium mt-2 text-[var(--foreground)] leading-relaxed">{issue.message || issue.description}</p>
                              </motion.div>
                            ))
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </main>
      </div>

      <footer className="w-full text-center py-6 text-xs font-mono font-bold text-[var(--muted-foreground)] uppercase tracking-widest opacity-60">
        CQG-8000 Engine • v1.2.0 • Strict Enforcement
      </footer>
    </div>
  )
}