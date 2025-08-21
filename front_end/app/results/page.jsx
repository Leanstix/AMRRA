import { MainLayout } from "@/components/layout/main-layout"
import { ChartsSection } from "@/components/results/charts-section"
import { VerdictCard } from "@/components/results/verdict-card"
import { StatisticsTable } from "@/components/results/statistics-table"
import { MetadataSection } from "@/components/results/metadata-section"

export default function ResultsIndexPage() {
  const experimentId = "20231026-143000"

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-wrap justify-between gap-3 p-4">
          <div className="flex min-w-72 flex-col gap-3">
            <p className="text-foreground tracking-tight text-[32px] font-bold leading-tight academic-text">
              Experiment Results
            </p>
            <p className="text-muted-foreground text-sm">Experiment ID: {experimentId}</p>
          </div>
        </div>

        <div className="px-4 space-y-8">
          <div className="space-y-3">
            <h2 className="text-xl font-semibold text-foreground academic-text">Charts</h2>
            <ChartsSection />
          </div>

          <div className="space-y-3">
            <h2 className="text-xl font-semibold text-foreground academic-text">Verdict</h2>
            <VerdictCard />
          </div>

          <div className="space-y-3">
            <h2 className="text-xl font-semibold text-foreground academic-text">Statistics</h2>
            <StatisticsTable />
          </div>

          <div className="space-y-3">
            <h2 className="text-xl font-semibold text-foreground academic-text">Metadata</h2>
            <MetadataSection />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}


