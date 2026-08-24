"use client"

import { FileText, Link2 } from "lucide-react"

const URL_TOKEN_PATTERN = /(https?:\/\/[^\s<>"']+)/gi
const TRAILING_PUNCTUATION = /[.,!?;:\]\)}]+$/

function RichText({ text }) {
  const parts = String(text || "").split(URL_TOKEN_PATTERN)
  return (
    <p className="whitespace-pre-wrap text-[15px] leading-7">
      {parts.map((part, index) => {
        if (!/^https?:\/\//i.test(part)) return <span key={`${part}-${index}`}>{part}</span>
        const url = part.replace(TRAILING_PUNCTUATION, "")
        const suffix = part.slice(url.length)
        return (
          <span key={`${part}-${index}`}>
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex max-w-full items-baseline gap-1 break-all font-medium text-primary underline decoration-primary/30 underline-offset-4 transition hover:decoration-primary"
            >
              <Link2 className="relative top-0.5 inline h-3.5 w-3.5 shrink-0" />
              {url}
            </a>
            {suffix}
          </span>
        )
      })}
    </p>
  )
}

export function UserResearchMessage({ text, attachmentName }) {
  return (
    <div className="animate-soft-in flex justify-end py-3">
      <div className="max-w-[86%] space-y-2 sm:max-w-[78%]">
        <div className="rounded-[1.35rem] bg-secondary px-4 py-3 text-secondary-foreground shadow-sm">
          <RichText text={text} />
        </div>
        {attachmentName && (
          <div className="ml-auto flex w-fit max-w-full items-center gap-2 rounded-xl border bg-card/90 px-3 py-2 text-[11px] shadow-sm">
            <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-3.5 w-3.5" />
            </span>
            <span className="truncate font-medium">{attachmentName}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export function AssistantIdentity({ working = false }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className={`grid h-7 w-7 place-items-center rounded-full bg-foreground text-background shadow-sm ${working ? "animate-status-pulse" : ""}`}>
        <span className="text-[9px] font-bold tracking-[-0.04em]">AR</span>
      </span>
      <span className="text-xs font-semibold">AMRRA</span>
      {working && <span className="text-[10px] text-muted-foreground">working</span>}
    </div>
  )
}
