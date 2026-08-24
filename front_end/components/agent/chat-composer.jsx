"use client"

import { useEffect, useMemo, useRef } from "react"
import { Button } from "@/components/ui/button"
import { extractHttpUrls } from "@/lib/amrra-client.mjs"
import {
  ArrowUp,
  FileText,
  Link2,
  Loader2,
  Plus,
  X,
} from "lucide-react"

const MAX_PDF_BYTES = 10 * 1024 * 1024

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) return ""
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

export function ChatComposer({
  value,
  onChange,
  file,
  onFileChange,
  onSubmit,
  disabled = false,
  busy = false,
  compact = false,
  onValidationError,
}) {
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)
  const urls = useMemo(() => extractHttpUrls(value), [value])

  useEffect(() => {
    const node = textareaRef.current
    if (!node) return
    node.style.height = "0px"
    const maxHeight = compact ? 180 : 220
    node.style.height = `${Math.min(node.scrollHeight, maxHeight)}px`
  }, [value, compact])

  function validateAndSetFile(candidate) {
    if (!candidate) return
    const isPdf = candidate.type === "application/pdf" || candidate.name?.toLowerCase().endsWith(".pdf")
    if (!isPdf) {
      onValidationError?.("AMRRA currently accepts PDF research attachments.")
      return
    }
    if (candidate.size > MAX_PDF_BYTES) {
      onValidationError?.("PDF attachments must be 10 MB or smaller.")
      return
    }
    onValidationError?.("")
    onFileChange(candidate)
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent?.isComposing) {
      event.preventDefault()
      if (!disabled && value.trim()) onSubmit()
    }
  }

  return (
    <div className={`overflow-hidden rounded-[1.7rem] border border-border/90 bg-card/95 shadow-[0_1px_2px_rgba(0,0,0,0.05),0_16px_45px_rgba(15,23,42,0.08)] backdrop-blur-xl transition-shadow focus-within:border-primary/25 focus-within:shadow-[0_1px_2px_rgba(0,0,0,0.05),0_20px_55px_rgba(15,23,42,0.10)] dark:shadow-black/20 ${compact ? "rounded-[1.55rem]" : ""}`}>
      {(file || urls.length > 0) && (
        <div className="flex flex-wrap gap-2 px-3.5 pt-3.5">
          {file && (
            <div className="inline-flex max-w-full items-center gap-2 rounded-xl border bg-background/85 px-2.5 py-2 shadow-sm">
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
                <FileText className="h-3.5 w-3.5" />
              </span>
              <span className="min-w-0">
                <span className="block max-w-52 truncate text-[11px] font-semibold">{file.name}</span>
                <span className="block text-[9px] text-muted-foreground">{formatBytes(file.size)} · PDF</span>
              </span>
              <button
                type="button"
                className="grid h-6 w-6 shrink-0 place-items-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground"
                onClick={() => onFileChange(null)}
                aria-label="Remove attachment"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
          {urls.slice(0, 3).map((url) => (
            <a
              key={url}
              href={url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex max-w-64 items-center gap-2 rounded-xl border bg-background/85 px-2.5 py-2 text-[10px] text-muted-foreground shadow-sm transition hover:border-primary/30 hover:text-foreground"
            >
              <Link2 className="h-3.5 w-3.5 shrink-0 text-primary" />
              <span className="truncate">{url}</span>
            </a>
          ))}
          {urls.length > 3 && (
            <span className="inline-flex items-center rounded-xl border bg-background/70 px-2.5 py-2 text-[10px] text-muted-foreground">
              +{urls.length - 3} links
            </span>
          )}
        </div>
      )}

      <textarea
        ref={textareaRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={1}
        maxLength={1000}
        placeholder="Ask AMRRA a research question…"
        className="max-h-56 min-h-[56px] w-full resize-none bg-transparent px-4 pb-2 pt-4 text-[15px] leading-6 text-foreground outline-none placeholder:text-muted-foreground/75 disabled:cursor-not-allowed disabled:opacity-60"
        aria-label="Research message"
      />

      <div className="flex items-center justify-between gap-3 px-3 pb-3">
        <div className="flex min-w-0 items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf,.pdf"
            className="hidden"
            onChange={(event) => {
              validateAndSetFile(event.target.files?.[0] || null)
              event.target.value = ""
            }}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-9 w-9 shrink-0 rounded-full border border-border/80 bg-background/80 shadow-sm hover:bg-muted"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            aria-label="Attach research PDF"
            title="Attach PDF"
          >
            <Plus className="h-4 w-4" />
          </Button>
          <span className="truncate text-[10px] text-muted-foreground">
            {urls.length > 0
              ? `${urls.length} public ${urls.length === 1 ? "link" : "links"} detected`
              : file
                ? "PDF attached"
                : "Attach a PDF or include a public URL"}
          </span>
        </div>

        <Button
          type="button"
          size="icon"
          className="h-9 w-9 shrink-0 rounded-full shadow-sm transition-transform active:scale-95"
          onClick={onSubmit}
          disabled={disabled || !value.trim()}
          aria-label={busy ? "AMRRA is working" : "Send research request"}
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" strokeWidth={2.4} />}
        </Button>
      </div>
    </div>
  )
}
