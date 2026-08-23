"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { BrainCircuit, Menu, X } from "lucide-react"

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        className="fixed left-4 top-4 z-50 md:hidden"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
      </Button>
      <Card className={`fixed left-0 top-0 z-40 h-full w-64 rounded-none border-y-0 border-l-0 bg-sidebar transition-transform md:translate-x-0 ${isOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="p-6">
          <Link href="/" onClick={() => setIsOpen(false)} className="block">
            <div className="flex items-center gap-2"><BrainCircuit className="h-5 w-5 text-primary" /><span className="font-bold">AMRRA</span></div>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">Agentic Machine Learning Research Reproducibility Assistant</p>
          </Link>
          <nav className="mt-8">
            <Link href="/" onClick={() => setIsOpen(false)} className="flex items-center gap-3 rounded-md bg-sidebar-accent px-3 py-2 text-sm font-medium">
              <BrainCircuit className="h-4 w-4" />Research Workbench
            </Link>
          </nav>
          <div className="mt-8 border-t pt-6 text-xs leading-5 text-muted-foreground">
            Evidence extraction is probabilistic. Statistical computations are deterministic and validated separately.
          </div>
        </div>
      </Card>
      {isOpen && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-black/20 md:hidden" onClick={() => setIsOpen(false)} />}
    </>
  )
}
