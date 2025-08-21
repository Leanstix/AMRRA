import { MainLayout } from "@/components/layout/main-layout"
import { HypothesisOverview } from "@/components/experiment-plan/hypothesis-overview"
import { PreRegisteredPlan } from "@/components/experiment-plan/pre-registered-plan"
import { CodeSnippet } from "@/components/experiment-plan/code-snippet"
import { ExecutionControls } from "@/components/experiment-plan/execution-controls"
import { WorkflowBreadcrumb } from "@/components/shared/workflow-breadcrumb"

export default function ExperimentPlanPage({ params }) {
  const breadcrumbItems = [
    { label: "Upload Paper", href: "/" },
    { label: "Hypotheses", href: "/hypotheses" },
    { label: "Experiment Plan", active: true },
  ]

  return (
    <MainLayout>
      <div className="max-w-6xl mx-auto space-y-8">
        <WorkflowBreadcrumb items={breadcrumbItems} />
        <HypothesisOverview hypothesisId={params.id} />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <PreRegisteredPlan />
            <CodeSnippet />
          </div>
          <div className="lg:col-span-1">
            <ExecutionControls />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
