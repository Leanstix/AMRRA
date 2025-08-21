import { MainLayout } from "@/components/layout/main-layout"
import { HeroSection } from "@/components/upload/hero-section"
import { UploadArea } from "@/components/upload/upload-area"
import { RecentExperiments } from "@/components/upload/recent-experiments"

export default function HomePage() {
  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content area */}
          <div className="lg:col-span-2 space-y-8">
            <HeroSection />
            <UploadArea />
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <RecentExperiments />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
