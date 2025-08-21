import { HypothesisCard } from "./hypothesis-card"

const hypotheses = [
  {
    id: 1,
    text: "The Transformer architecture, relying entirely on self-attention mechanisms without recurrence or convolution, can achieve superior performance on machine translation tasks compared to existing sequence-to-sequence models.",
    confidence: 0.92,
    status: "ready",
    metrics: ["BLEU Score", "Training Time", "Model Parameters"],
    dataset: "WMT 2014 English-German",
  },
  {
    id: 2,
    text: "Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions, leading to improved translation quality over single-head attention.",
    confidence: 0.87,
    status: "ready",
    metrics: ["Translation Quality", "Attention Visualization", "Ablation Study"],
    dataset: "WMT 2014 English-French",
  },
  {
    id: 3,
    text: "Positional encoding using sinusoidal functions enables the model to learn relative positions effectively, allowing it to generalize to sequence lengths longer than those seen during training.",
    confidence: 0.78,
    status: "ready",
    metrics: ["Position Accuracy", "Sequence Length Generalization", "Encoding Effectiveness"],
    dataset: "Custom Position Dataset",
  },
  {
    id: 4,
    text: "The scaled dot-product attention mechanism is computationally more efficient than additive attention while maintaining comparable or superior performance in sequence modeling tasks.",
    confidence: 0.85,
    status: "processing",
    metrics: ["Computational Complexity", "Memory Usage", "Performance Comparison"],
    dataset: "Synthetic Attention Dataset",
  },
  {
    id: 5,
    text: "Layer normalization applied before each sub-layer (pre-norm) rather than after (post-norm) leads to more stable training and better convergence in deep transformer networks.",
    confidence: 0.73,
    status: "ready",
    metrics: ["Training Stability", "Convergence Rate", "Final Performance"],
    dataset: "Deep Network Training Dataset",
  },
]

export function HypothesesGrid() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-foreground academic-text">Extracted Hypotheses</h2>
        <div className="text-sm text-muted-foreground control-text">{hypotheses.length} hypotheses identified</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {hypotheses.map((hypothesis) => (
          <HypothesisCard key={hypothesis.id} hypothesis={hypothesis} />
        ))}
      </div>
    </div>
  )
}
