"use client"

import Link from "next/link"
import { ChevronRight } from "lucide-react"

export function WorkflowBreadcrumb({ items }) {
  return (
    <nav className="flex items-center space-x-2 text-sm control-text mb-6">
      {items.map((item, index) => (
        <div key={index} className="flex items-center">
          {index > 0 && <ChevronRight className="h-4 w-4 text-muted-foreground mx-2" />}
          {item.href && !item.active ? (
            <Link href={item.href} className="text-muted-foreground hover:text-foreground transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className={item.active ? "text-foreground font-medium" : "text-muted-foreground"}>{item.label}</span>
          )}
        </div>
      ))}
    </nav>
  )
}
