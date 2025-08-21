import { MainLayout } from "@/components/layout/main-layout"
import { ExperimentHeader } from "@/components/results/experiment-header"
import { VerdictCard } from "@/components/results/verdict-card"
import { ChartsSection } from "@/components/results/charts-section"
import { StatisticsTable } from "@/components/results/statistics-table"
import { MetadataSection } from "@/components/results/metadata-section"
import { ActionButtons } from "@/components/results/action-buttons"
import { WorkflowBreadcrumb } from "@/components/shared/workflow-breadcrumb"

export default function ResultsPage({ params }) {
  const breadcrumbItems = [
    { label: "Upload Paper", href: "/" },
    { label: "Hypotheses", href: "/hypotheses" },
    { label: "Experiment Plan", href: `/experiment-plan/${params.id}` },
    { label: "Results", active: true },
  ]

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto space-y-8">
        <WorkflowBreadcrumb items={breadcrumbItems} />
        <ExperimentHeader experimentId={params.id} />

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-3 space-y-8">
            <VerdictCard />
            <ChartsSection />
            <StatisticsTable />
          </div>

          <div className="lg:col-span-1 space-y-6">
            <MetadataSection />
            <ActionButtons />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
