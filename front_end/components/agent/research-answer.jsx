"use client"

import { Badge } from "@/components/ui/badge"
import { AssistantIdentity } from "@/components/agent/conversation-message"
import {
  CheckCircle2,
  Gauge,
  Quote,
  Sigma,
  Sparkles,
} from "lucide-react"

function formatMetric(value) {
  if (value === null || value === undefined) return "—"
  const number = Number(value)
  if (!Number.isFinite(number)) return String(value)
  if (number !== 0 && Math.abs(number) < 0.001) return number.toExponential(2)
  if (Math.abs(number) >= 1000) return number.toLocaleString(undefined, { maximumFractionDigits: 2 })
  return number.toFixed(4).replace(/0+$/, "").replace(/\.$/, "")
}

function ResultMetric({ label, value }) {
  return (
    <div className="min-w-0 rounded-xl bg-muted/45 px-3 py-2.5">
      <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-1 truncate font-mono text-sm font-semibold">{value}</p>
    </div>
  )
}

export function ResearchAnswer({ run }) {
  const report = run?.report
  const experiments = run?.experiments || []
  const hypotheses = run?.extraction?.hypotheses || []

  if (!report) return null

  return (
    <div className="animate-soft-in py-4">
      <AssistantIdentity />
      <div className="mt-4 space-y-6 pl-0 sm:pl-9">
        <section>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold tracking-[-0.025em] sm:text-2xl">{report.title}</h2>
            <Badge variant="outline" className="rounded-full text-[10px]">
              {Math.round((report.confidence || 0) * 100)}% confidence
            </Badge>
          </div>
          <p className="mt-3 text-[15px] leading-7 text-foreground/90">{report.summary}</p>
        </section>

        <section className="rounded-2xl border border-primary/15 bg-primary/[0.055] p-4 sm:p-5">
          <div className="flex items-center gap-2 text-primary">
            <Sparkles className="h-4 w-4" />
            <p className="text-[10px] font-bold uppercase tracking-[0.18em]">Conclusion</p>
          </div>
          <p className="mt-2 text-[15px] font-medium leading-7">{report.conclusion}</p>
        </section>

        {experiments.length > 0 && (
          <section>
            <div className="mb-3 flex items-center gap-2">
              <Sigma className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold">Deterministic results</h3>
            </div>
            <div className="space-y-3">
              {experiments.map((result, index) => (
                <div key={`${result.hypothesis_id}-${index}`} className="rounded-2xl border bg-card/70 p-4 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge>{result.test_used}</Badge>
                      <Badge variant="outline">{String(result.status).replaceAll("_", " ")}</Badge>
                    </div>
                    {result.status === "completed" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="h-3.5 w-3.5" /> computed
                      </span>
                    )}
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
                    <ResultMetric label="Statistic" value={formatMetric(result.statistic)} />
                    <ResultMetric label="p-value" value={formatMetric(result.p_value)} />
                    <ResultMetric label="Effect" value={formatMetric(result.effect_size)} />
                    <ResultMetric label="Estimate" value={Array.isArray(result.estimate) ? result.estimate.map(formatMetric).join(", ") : formatMetric(result.estimate)} />
                  </div>
                  <p className="mt-3 text-sm font-medium leading-6">{result.conclusion}</p>
                  {result.method_notes && <p className="mt-1 text-xs leading-5 text-muted-foreground">{result.method_notes}</p>}
                  {result.quality_flags?.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {result.quality_flags.map((flag) => <Badge key={flag} variant="outline">{flag.replaceAll("_", " ")}</Badge>)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {hypotheses.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold">Evidence-backed hypotheses</h3>
            <div className="mt-3 space-y-2.5">
              {hypotheses.map((hypothesis, index) => (
                <div key={hypothesis.hypothesis_id} className="flex gap-3 rounded-xl bg-muted/35 px-3.5 py-3">
                  <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-background text-[10px] font-bold shadow-sm">{index + 1}</span>
                  <div className="min-w-0">
                    <p className="text-sm leading-6">{hypothesis.statement}</p>
                    <p className="mt-1 text-[10px] text-muted-foreground">Grounding confidence {Math.round((hypothesis.confidence || 0) * 100)}%</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {report.limitations?.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold">Limitations</h3>
            <ul className="mt-2 space-y-2 text-sm leading-6 text-muted-foreground">
              {report.limitations.map((item) => (
                <li key={item} className="flex gap-2.5">
                  <span className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-muted-foreground" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {report.citations?.length > 0 && (
          <section>
            <div className="flex items-center gap-2">
              <Quote className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold">Traceable citations</h3>
            </div>
            <div className="mt-3 space-y-2">
              {report.citations.map((citation, index) => (
                <div key={`${citation.chunk_id}-${index}`} className="rounded-xl border-l-2 border-primary/35 bg-muted/30 px-3.5 py-3">
                  <p className="font-mono text-[10px] font-semibold text-primary">{citation.chunk_id}</p>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">{citation.claim}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="flex flex-wrap items-center gap-4 border-t pt-4 text-[10px] text-muted-foreground">
          <span className="inline-flex items-center gap-1.5"><Gauge className="h-3.5 w-3.5" />Judge confidence {Math.round((report.confidence || 0) * 100)}%</span>
          <span>{hypotheses.length} grounded hypotheses</span>
          <span>{experiments.filter((item) => item.status === "completed").length} completed experiments</span>
        </div>
      </div>
    </div>
  )
}
