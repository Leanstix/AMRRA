"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { BarChart3, Settings, Upload, Menu, X, Target, FileCheck } from "lucide-react"

const navigationItems = [
  { href: "/", label: "Upload", icon: Upload },
  { href: "/hypotheses", label: "Hypotheses", icon: Target },
  { href: "/results", label: "Results", icon: BarChart3 },
  { href: "/report", label: "Reports", icon: FileCheck },
  { href: "/settings", label: "Settings", icon: Settings },
]

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()

  const isActiveRoute = (href) => {
    if (href === "/") {
      return pathname === "/"
    }
    else if (href === "/hypotheses") {
      return pathname === "/hypotheses"
    }
    else if (href === "/results") {
      return pathname === "/results"
    }
    else if (href === "/report") {
      return pathname === "/report"
    }
    else if (href === "/settings") {
      return pathname === "/settings"
    }
    return pathname.startsWith(href)
  }

  return (
    <>
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="sm"
        className="md:hidden fixed top-4 left-4 z-50 control-text"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
      </Button>

      {/* Sidebar */}
      <Card
        className={`
        fixed left-0 top-0 h-full w-64 bg-sidebar border-r border-sidebar-border z-40 transition-transform duration-200 ease-in-out
        ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
      `}
      >
        <div className="p-6">
          <Link href="/" onClick={() => setIsOpen(false)}>
            <h1 className="text-xl font-bold text-sidebar-foreground academic-text mb-8 hover:text-primary transition-colors">
              AI Research Reproducibility Copilot
            </h1>
          </Link>

          <nav className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon
              const isActive = isActiveRoute(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-3 py-2 rounded-md transition-colors control-text
                    ${
                      isActive
                        ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                        : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                    }
                  `}
                  onClick={() => setIsOpen(false)}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          <div className="mt-8 pt-6 border-t border-sidebar-border">
            <h3 className="text-sm font-medium text-sidebar-foreground control-text mb-3">Workflow Progress</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-sidebar-foreground">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="control-text">Paper Uploaded</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-sidebar-foreground">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="control-text">Hypotheses Extracted</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-sidebar-foreground">
                <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                <span className="control-text">Experiment Running</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-sidebar-foreground">
                <div className="w-2 h-2 rounded-full bg-gray-300"></div>
                <span className="control-text">Report Generated</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Overlay for mobile */}
      {isOpen && <div className="fixed inset-0 bg-black/20 z-30 md:hidden" onClick={() => setIsOpen(false)} />}
    </>
  )
}
