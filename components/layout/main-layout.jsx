import { Navigation } from "./navigation"

export function MainLayout({ children }) {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="md:ml-64 min-h-screen">
        <div className="p-6 md:p-8">{children}</div>
      </main>
    </div>
  )
}
