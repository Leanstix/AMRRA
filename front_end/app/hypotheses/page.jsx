import { MainLayout } from "@/components/layout/main-layout"
import { HypothesesGrid } from "@/components/hypotheses/hypotheses-grid"
import { PaperSummary } from "@/components/hypotheses/paper-summary"
import { WorkflowBreadcrumb } from "@/components/shared/workflow-breadcrumb"

export default function HypothesesPage() {
  const breadcrumbItems = [
    { label: "Upload Paper", href: "/" },
    { label: "Hypotheses", active: true },
  ]

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto space-y-8">
        <WorkflowBreadcrumb items={breadcrumbItems} />
        <PaperSummary />
        <HypothesesGrid />
      </div>
    </MainLayout>
  )
}
