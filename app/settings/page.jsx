"use client"

import { MainLayout } from "@/components/layout/main-layout"
import { useSettings, getDefaultSettings } from "@/components/shared/settings-context"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Slider } from "@/components/ui/slider"
import { Textarea } from "@/components/ui/textarea"

function Section({ title, description, children }) {
  return (
    <Card className="p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold academic-text">{title}</h3>
        {description ? <p className="text-sm text-muted-foreground control-text">{description}</p> : null}
      </div>
      <div className="grid gap-4">{children}</div>
    </Card>
  )
}

function Row({ label, tooltip, children }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
      <div className="space-y-1">
        <Label className="control-text">{label}</Label>
        {tooltip ? <p className="text-xs text-muted-foreground control-text">{tooltip}</p> : null}
      </div>
      <div className="md:col-span-2">{children}</div>
    </div>
  )
}

export default function SettingsPage() {
  const { settings, updateSettings, resetSettings } = useSettings()
  const defaults = getDefaultSettings()

  return (
    <MainLayout>
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold academic-text">Settings</h1>
            <p className="text-sm text-muted-foreground control-text">Configure experiments, data, execution, and reporting.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => resetSettings()} className="bg-transparent control-text">
              Reset to Defaults
            </Button>
            <Button onClick={() => alert("Settings saved")}>Save Settings</Button>
          </div>
        </div>

        <Tabs defaultValue="experiment" className="space-y-6">
          <TabsList className="flex flex-wrap gap-2 p-2">
            <TabsTrigger value="experiment">Experiment</TabsTrigger>
            <TabsTrigger value="data">Data</TabsTrigger>
            <TabsTrigger value="paper">Paper & Hypotheses</TabsTrigger>
            <TabsTrigger value="execution">Resources</TabsTrigger>
            <TabsTrigger value="reporting">Reporting</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="advanced">Advanced</TabsTrigger>
          </TabsList>

          <TabsContent value="experiment" className="space-y-4">
            <Section title="Experiment Settings" description="Defaults for running experiments and analyses.">
              <Row label="Random seed" tooltip="Seed used to make runs deterministic across trials.">
                <Input
                  type="number"
                  value={settings.experiment.randomSeed}
                  onChange={(e) => updateSettings((s) => ({ ...s, experiment: { ...s.experiment, randomSeed: Number(e.target.value) } }))}
                />
              </Row>
              <Row label="Number of runs/trials" tooltip="How many times to repeat the experiment for robust estimates.">
                <Input
                  type="number"
                  min={1}
                  value={settings.experiment.numRuns}
                  onChange={(e) => updateSettings((s) => ({ ...s, experiment: { ...s.experiment, numRuns: Number(e.target.value) } }))}
                />
              </Row>
              <Row label="Confidence level" tooltip="Statistical confidence level used for intervals (e.g., 0.95).">
                <Slider
                  value={[Math.round(settings.experiment.confidenceLevel * 100)]}
                  onValueChange={([v]) => updateSettings((s) => ({ ...s, experiment: { ...s.experiment, confidenceLevel: v / 100 } }))}
                />
                <div className="text-xs text-muted-foreground">{Math.round(settings.experiment.confidenceLevel * 100)}%</div>
              </Row>
              <Row label="Metrics selection" tooltip="Primary metrics to compute and report.">
                <Select
                  value={settings.experiment.metrics[0]}
                  onValueChange={(v) => updateSettings((s) => ({ ...s, experiment: { ...s.experiment, metrics: [v] } }))}
                >
                  <SelectTrigger className="w-full"><SelectValue placeholder="Select metric" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Accuracy">Accuracy</SelectItem>
                    <SelectItem value="F1">F1</SelectItem>
                    <SelectItem value="BLEU">BLEU</SelectItem>
                    <SelectItem value="ROC-AUC">ROC-AUC</SelectItem>
                  </SelectContent>
                </Select>
              </Row>
              <Row label="Sandbox mode" tooltip="Run experiments in an isolated environment with mocked side effects.">
                <Switch
                  checked={settings.experiment.sandboxMode}
                  onCheckedChange={(v) => updateSettings((s) => ({ ...s, experiment: { ...s.experiment, sandboxMode: v } }))}
                />
              </Row>
            </Section>
          </TabsContent>

          <TabsContent value="data" className="space-y-4">
            <Section title="Data Settings" description="Configure data source and preprocessing.">
              <Row label="Dataset source" tooltip="Choose between uploading a dataset or generating a synthetic one.">
                <Select
                  value={settings.data.source}
                  onValueChange={(v) => updateSettings((s) => ({ ...s, data: { ...s.data, source: v } }))}
                >
                  <SelectTrigger className="w-full"><SelectValue placeholder="Select source" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="upload">Upload</SelectItem>
                    <SelectItem value="synthetic">Synthetic</SelectItem>
                  </SelectContent>
                </Select>
              </Row>
              <Row label="Dataset hashing" tooltip="Compute and store content hash to ensure dataset versioning.">
                <Switch
                  checked={settings.data.hashingEnabled}
                  onCheckedChange={(v) => updateSettings((s) => ({ ...s, data: { ...s.data, hashingEnabled: v } }))}
                />
              </Row>
              <Row label="Data preprocessing" tooltip="Common preprocessing operations to apply before training.">
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center justify-between"><span className="text-sm control-text">Normalize</span><Switch checked={settings.data.preprocessing.normalize} onCheckedChange={(v) => updateSettings((s) => ({ ...s, data: { ...s.data, preprocessing: { ...s.data.preprocessing, normalize: v } } }))} /></div>
                  <div className="flex items-center justify-between"><span className="text-sm control-text">Tokenize</span><Switch checked={settings.data.preprocessing.tokenize} onCheckedChange={(v) => updateSettings((s) => ({ ...s, data: { ...s.data, preprocessing: { ...s.data.preprocessing, tokenize: v } } }))} /></div>
                  <div className="flex items-center justify-between"><span className="text-sm control-text">Lowercase</span><Switch checked={settings.data.preprocessing.lowercase} onCheckedChange={(v) => updateSettings((s) => ({ ...s, data: { ...s.data, preprocessing: { ...s.data.preprocessing, lowercase: v } } }))} /></div>
                  <div className="flex items-center justify-between"><span className="text-sm control-text">Remove stopwords</span><Switch checked={settings.data.preprocessing.removeStopwords} onCheckedChange={(v) => updateSettings((s) => ({ ...s, data: { ...s.data, preprocessing: { ...s.data.preprocessing, removeStopwords: v } } }))} /></div>
                </div>
              </Row>
            </Section>
          </TabsContent>

          <TabsContent value="paper" className="space-y-4">
            <Section title="Paper & Hypothesis Settings" description="Control extraction and generation behavior.">
              <Row label="Paper input format" tooltip="How the paper is provided for parsing.">
                <Select
                  value={settings.paper.inputFormat}
                  onValueChange={(v) => updateSettings((s) => ({ ...s, paper: { ...s.paper, inputFormat: v } }))}
                >
                  <SelectTrigger className="w-full"><SelectValue placeholder="Format" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pdf">PDF</SelectItem>
                    <SelectItem value="arxiv">arXiv ID</SelectItem>
                    <SelectItem value="text">Plain Text</SelectItem>
                  </SelectContent>
                </Select>
              </Row>
              <Row label="Claim extraction sensitivity" tooltip="Adjust how aggressively claims are extracted from text.">
                <Slider
                  value={[Math.round(settings.paper.claimSensitivity * 100)]}
                  onValueChange={([v]) => updateSettings((s) => ({ ...s, paper: { ...s.paper, claimSensitivity: v / 100 } }))}
                />
                <div className="text-xs text-muted-foreground">{Math.round(settings.paper.claimSensitivity * 100)}%</div>
              </Row>
              <Row label="Hypothesis generation parameters" tooltip="Thresholds and assumptions governing hypothesis creation.">
                <div className="grid md:grid-cols-3 gap-3">
                  <div>
                    <Label className="text-xs control-text">Threshold</Label>
                    <Input type="number" step="0.01" value={settings.paper.hypothesis.threshold} onChange={(e) => updateSettings((s) => ({ ...s, paper: { ...s.paper, hypothesis: { ...s.paper.hypothesis, threshold: Number(e.target.value) } } }))} />
                  </div>
                  <div>
                    <Label className="text-xs control-text">Min effect size</Label>
                    <Input type="number" step="0.01" value={settings.paper.hypothesis.minEffectSize} onChange={(e) => updateSettings((s) => ({ ...s, paper: { ...s.paper, hypothesis: { ...s.paper.hypothesis, minEffectSize: Number(e.target.value) } } }))} />
                  </div>
                  <div>
                    <Label className="text-xs control-text">Null assumption</Label>
                    <Select value={settings.paper.hypothesis.nullAssumption} onValueChange={(v) => updateSettings((s) => ({ ...s, paper: { ...s.paper, hypothesis: { ...s.paper.hypothesis, nullAssumption: v } } }))}>
                      <SelectTrigger className="w-full"><SelectValue placeholder="Null" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="two_tailed">Two-tailed</SelectItem>
                        <SelectItem value="one_tailed">One-tailed</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </Row>
            </Section>
          </TabsContent>

          <TabsContent value="execution" className="space-y-4">
            <Section title="Resource / Execution Settings" description="Limits, parallelism and logging.">
              <Row label="CPU limit" tooltip="Maximum CPU cores to use.">
                <Input type="number" min={1} value={settings.execution.cpuLimit} onChange={(e) => updateSettings((s) => ({ ...s, execution: { ...s.execution, cpuLimit: Number(e.target.value) } }))} />
              </Row>
              <Row label="GPU limit" tooltip="Maximum GPUs to allocate.">
                <Input type="number" min={0} value={settings.execution.gpuLimit} onChange={(e) => updateSettings((s) => ({ ...s, execution: { ...s.execution, gpuLimit: Number(e.target.value) } }))} />
              </Row>
              <Row label="Timeout (minutes)" tooltip="Abort runs exceeding this timeout.">
                <Input type="number" min={1} value={settings.execution.timeoutMinutes} onChange={(e) => updateSettings((s) => ({ ...s, execution: { ...s.execution, timeoutMinutes: Number(e.target.value) } }))} />
              </Row>
              <Row label="Parallel runs" tooltip="Number of concurrent runs to execute.">
                <Input type="number" min={1} value={settings.execution.parallelRuns} onChange={(e) => updateSettings((s) => ({ ...s, execution: { ...s.execution, parallelRuns: Number(e.target.value) } }))} />
              </Row>
              <Row label="Logging level" tooltip="Verbosity of logs emitted during execution.">
                <Select value={settings.execution.loggingLevel} onValueChange={(v) => updateSettings((s) => ({ ...s, execution: { ...s.execution, loggingLevel: v } }))}>
                  <SelectTrigger className="w-full"><SelectValue placeholder="Level" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="error">Error</SelectItem>
                    <SelectItem value="warn">Warn</SelectItem>
                    <SelectItem value="info">Info</SelectItem>
                    <SelectItem value="debug">Debug</SelectItem>
                  </SelectContent>
                </Select>
              </Row>
            </Section>
          </TabsContent>

          <TabsContent value="reporting" className="space-y-4">
            <Section title="Reporting Settings" description="Customize exported reports and artifacts.">
              <Row label="Report format" tooltip="Default format for generated reports.">
                <Select value={settings.reporting.format} onValueChange={(v) => updateSettings((s) => ({ ...s, reporting: { ...s.reporting, format: v } }))}>
                  <SelectTrigger className="w-full"><SelectValue placeholder="Format" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="html">HTML</SelectItem>
                    <SelectItem value="pdf">PDF</SelectItem>
                  </SelectContent>
                </Select>
              </Row>
              <Row label="Include code in report" tooltip="Embed key code snippets in the exported report.">
                <Switch checked={settings.reporting.includeCode} onCheckedChange={(v) => updateSettings((s) => ({ ...s, reporting: { ...s.reporting, includeCode: v } }))} />
              </Row>
              <Row label="Include plots & metrics" tooltip="Attach generated figures and tables to the report.">
                <Switch checked={settings.reporting.includePlots} onCheckedChange={(v) => updateSettings((s) => ({ ...s, reporting: { ...s.reporting, includePlots: v } }))} />
              </Row>
              <Row label="Artifact directory path" tooltip="Where to write exported artifacts on the filesystem.">
                <Input value={settings.reporting.artifactDir} onChange={(e) => updateSettings((s) => ({ ...s, reporting: { ...s.reporting, artifactDir: e.target.value } }))} />
              </Row>
            </Section>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-4">
            <Section title="Notifications / Alerts" description="Get notified about run completion and failures.">
              <Row label="Run completion alerts" tooltip="Notify when a run or batch finishes.">
                <Switch checked={settings.notifications.onCompletion} onCheckedChange={(v) => updateSettings((s) => ({ ...s, notifications: { ...s.notifications, onCompletion: v } }))} />
              </Row>
              <Row label="Error/warning alerts" tooltip="Notify when errors or warnings occur.">
                <Switch checked={settings.notifications.onErrors} onCheckedChange={(v) => updateSettings((s) => ({ ...s, notifications: { ...s.notifications, onErrors: v } }))} />
              </Row>
            </Section>
          </TabsContent>

          <TabsContent value="advanced" className="space-y-4">
            <Section title="Advanced / Developer Settings" description="Low-level agent and vector store configuration.">
              <Row label="Agent timeout (seconds)" tooltip="Maximum time to wait for agent responses.">
                <Input type="number" min={1} value={settings.advanced.agentTimeoutSeconds} onChange={(e) => updateSettings((s) => ({ ...s, advanced: { ...s.advanced, agentTimeoutSeconds: Number(e.target.value) } }))} />
              </Row>
              <Row label="Custom agent prompt overrides" tooltip="Optional system/prompt overrides for the agent.">
                <Textarea value={settings.advanced.customAgentPrompt} onChange={(e) => updateSettings((s) => ({ ...s, advanced: { ...s.advanced, customAgentPrompt: e.target.value } }))} />
              </Row>
              <Row label="Vector store (FAISS)" tooltip="Configure FAISS index location for semantic search.">
                <div className="grid md:grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs control-text">Provider</Label>
                    <Input value={settings.advanced.vectorStore.provider} onChange={(e) => updateSettings((s) => ({ ...s, advanced: { ...s.advanced, vectorStore: { ...s.advanced.vectorStore, provider: e.target.value } } }))} />
                  </div>
                  <div>
                    <Label className="text-xs control-text">Index path</Label>
                    <Input value={settings.advanced.vectorStore.indexPath} onChange={(e) => updateSettings((s) => ({ ...s, advanced: { ...s.advanced, vectorStore: { ...s.advanced.vectorStore, indexPath: e.target.value } } }))} />
                  </div>
                </div>
              </Row>
            </Section>
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  )
}


