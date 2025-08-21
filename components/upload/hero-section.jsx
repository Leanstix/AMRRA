export function HeroSection() {
  return (
    <div className="text-center space-y-6 py-12">
      <h1 className="text-4xl md:text-5xl font-bold text-foreground academic-text">
        AI Research Reproducibility Copilot
      </h1>

      <p className="text-xl text-muted-foreground academic-text max-w-3xl mx-auto">
        Extract hypotheses from ML papers, generate pre-registered experiment plans, execute experiments, and create
        comprehensive reproducibility reports.
      </p>

      <p className="text-lg text-muted-foreground control-text">
        Upload your research paper to begin the reproducibility analysis
      </p>
    </div>
  )
}
