"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Copy, Check, Code } from "lucide-react"

const codeSnippet = `# Transformer Model Training Script
# Auto-generated for hypothesis validation

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from datasets import load_dataset
import evaluate

# Configuration
CONFIG = {
    'model_name': 'transformer-base',
    'dataset': 'wmt14-en-de',
    'batch_size': 25000,
    'learning_rate': 1e-4,
    'warmup_steps': 4000,
    'max_epochs': 50,
    'dropout': 0.1,
    'label_smoothing': 0.1
}

# Load dataset
dataset = load_dataset('wmt14', 'de-en')
tokenizer = AutoTokenizer.from_pretrained('bert-base-multilingual-cased')

# Model architecture
class TransformerModel(nn.Module):
    def __init__(self, vocab_size, d_model=512, nhead=8, num_layers=6):
        super().__init__()
        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=nhead,
            num_encoder_layers=num_layers,
            num_decoder_layers=num_layers,
            dropout=CONFIG['dropout']
        )
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.output_projection = nn.Linear(d_model, vocab_size)
    
    def forward(self, src, tgt):
        src_emb = self.embedding(src)
        tgt_emb = self.embedding(tgt)
        output = self.transformer(src_emb, tgt_emb)
        return self.output_projection(output)

# Training loop
def train_model():
    model = TransformerModel(vocab_size=37000)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=CONFIG['learning_rate'],
        betas=(0.9, 0.98),
        eps=1e-9
    )
    
    # Training implementation
    for epoch in range(CONFIG['max_epochs']):
        # Training step
        train_loss = train_epoch(model, train_loader, optimizer)
        
        # Validation step
        val_bleu = evaluate_model(model, val_loader)
        
        print(f"Epoch {epoch}: Loss={train_loss:.4f}, BLEU={val_bleu:.2f}")
        
        # Early stopping if BLEU > 28.4
        if val_bleu > 28.4:
            print("Target BLEU score achieved!")
            break

if __name__ == "__main__":
    train_model()`

export function CodeSnippet() {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(codeSnippet)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Code className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold text-foreground academic-text">Auto-Generated Code</h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="control-text">
            Python
          </Badge>
          <Button variant="outline" size="sm" onClick={handleCopy} className="control-text bg-transparent">
            {copied ? <Check className="h-4 w-4 mr-1" /> : <Copy className="h-4 w-4 mr-1" />}
            {copied ? "Copied!" : "Copy"}
          </Button>
        </div>
      </div>

      <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
        <pre className="text-sm text-gray-100 font-mono leading-relaxed">
          <code>{codeSnippet}</code>
        </pre>
      </div>

      <div className="mt-4 text-sm text-muted-foreground control-text">
        This code implements the experimental setup based on your pre-registered plan. All hyperparameters and
        evaluation metrics are configured according to the hypothesis requirements.
      </div>
    </Card>
  )
}
