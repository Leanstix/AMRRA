import { Navigation } from "./navigation"

export function MainLayout({ children }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="amrra-grid pointer-events-none fixed inset-0 opacity-55" />
      <Navigation />
      <main className="relative min-h-screen md:ml-[17.5rem]">
        <div className="mx-auto w-full max-w-[96rem] px-4 pb-12 pt-20 sm:px-6 md:px-8 md:pt-8 xl:px-10">
          {children}
        </div>
      </main>
    </div>
  )
}
