import { MainLayout } from "@/components/layout/main-layout"
import { ReportHeader } from "@/components/report/report-header"
import { ReportViewer } from "@/components/report/report-viewer"
import { ReportActions } from "@/components/report/report-actions"
import { ReportSummary } from "@/components/report/report-summary"
import { WorkflowBreadcrumb } from "@/components/shared/workflow-breadcrumb"

export default function ReportPage({ params }) {
  const breadcrumbItems = [
    { label: "Upload Paper", href: "/" },
    { label: "Hypotheses", href: "/hypotheses" },
    { label: "Experiment Plan", href: `/experiment-plan/${params.id}` },
    { label: "Results", href: `/results/${params.id}` },
    { label: "Report", active: true },
  ]

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto space-y-8">
        <WorkflowBreadcrumb items={breadcrumbItems} />
        <ReportHeader reportId={params.id} />

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-3">
            <ReportViewer />
          </div>

          <div className="lg:col-span-1 space-y-6">
            <ReportActions />
            <ReportSummary />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
