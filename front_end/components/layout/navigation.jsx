"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  BrainCircuit,
  ChevronRight,
  FlaskConical,
  Menu,
  ShieldCheck,
  Sparkles,
  Workflow,
  X,
} from "lucide-react"

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <Button
        variant="outline"
        size="icon"
        className="glass-panel fixed left-4 top-4 z-50 h-10 w-10 rounded-xl shadow-sm md:hidden"
        onClick={() => setIsOpen((value) => !value)}
        aria-label={isOpen ? "Close navigation" : "Open navigation"}
      >
        {isOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
      </Button>

      <aside
        className={`glass-panel fixed left-0 top-0 z-40 flex h-full w-[17.5rem] flex-col border-r border-sidebar-border/80 transition-transform duration-300 ease-out md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex min-h-0 flex-1 flex-col px-5 py-6">
          <Link href="/" onClick={() => setIsOpen(false)} className="group block rounded-2xl p-1">
            <div className="flex items-center gap-3">
              <div className="relative grid h-11 w-11 place-items-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 transition-transform duration-300 group-hover:scale-[1.04]">
                <BrainCircuit className="h-5 w-5" />
                <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full border-2 border-sidebar bg-emerald-500" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold tracking-[-0.02em]">AMRRA</span>
                  <span className="rounded-full border border-primary/15 bg-primary/8 px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.18em] text-primary">
                    agentic
                  </span>
                </div>
                <p className="mt-0.5 text-[11px] font-medium text-muted-foreground">Research intelligence system</p>
              </div>
            </div>
          </Link>

          <div className="mt-8">
            <p className="px-3 text-[10px] font-bold uppercase tracking-[0.22em] text-muted-foreground/70">Workspace</p>
            <nav className="mt-2 space-y-1.5">
              <Link
                href="/"
                onClick={() => setIsOpen(false)}
                className="group flex items-center justify-between rounded-xl border border-primary/10 bg-primary/8 px-3 py-3 text-sm font-semibold text-sidebar-accent-foreground shadow-sm transition-all duration-200 hover:border-primary/20 hover:bg-primary/12"
              >
                <span className="flex items-center gap-3">
                  <Workflow className="h-4 w-4 text-primary" />
                  Research Workbench
                </span>
                <ChevronRight className="h-4 w-4 text-primary/70 transition-transform duration-200 group-hover:translate-x-0.5" />
              </Link>
            </nav>
          </div>

          <div className="mt-8">
            <p className="px-3 text-[10px] font-bold uppercase tracking-[0.22em] text-muted-foreground/70">System model</p>
            <div className="mt-3 space-y-2">
              <div className="rounded-xl border bg-card/70 p-3">
                <div className="flex items-center gap-2 text-xs font-semibold">
                  <Sparkles className="h-3.5 w-3.5 text-primary" />
                  Probabilistic reasoning
                </div>
                <p className="mt-1.5 text-[11px] leading-5 text-muted-foreground">Retrieval, extraction and judgement are model-assisted.</p>
              </div>
              <div className="rounded-xl border bg-card/70 p-3">
                <div className="flex items-center gap-2 text-xs font-semibold">
                  <FlaskConical className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                  Deterministic science
                </div>
                <p className="mt-1.5 text-[11px] leading-5 text-muted-foreground">Planning contracts and statistical calculations stay outside the LLM.</p>
              </div>
            </div>
          </div>

          <div className="mt-auto pt-6">
            <div className="rounded-2xl border border-primary/10 bg-gradient-to-br from-primary/10 via-card/70 to-accent/30 p-4">
              <div className="flex items-center gap-2 text-xs font-semibold">
                <ShieldCheck className="h-4 w-4 text-primary" />
                Evidence-first by design
              </div>
              <p className="mt-2 text-[11px] leading-5 text-muted-foreground">
                Claims remain tied to persisted evidence. Unsupported inference degrades safely instead of fabricating data.
              </p>
            </div>
            <div className="mt-4 flex items-center justify-between px-1 text-[10px] font-medium text-muted-foreground/70">
              <span>AMRRA v2</span>
              <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> operational</span>
            </div>
          </div>
        </div>
      </aside>

      {isOpen && (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-30 bg-background/60 backdrop-blur-sm md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  )
}
