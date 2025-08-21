import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FileText, Users, Calendar } from "lucide-react"

export function PaperSummary() {
  return (
    <Card className="p-6">
      <div className="flex items-start gap-4">
        <div className="p-3 bg-primary/10 rounded-lg">
          <FileText className="h-6 w-6 text-primary" />
        </div>

        <div className="flex-1 space-y-3">
          <div>
            <h1 className="text-2xl font-bold text-foreground academic-text">Attention Is All You Need</h1>
            <p className="text-muted-foreground control-text mt-1">
              Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser,
              Illia Polosukhin
            </p>
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground control-text">
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              <span>8 authors</span>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>2017</span>
            </div>
            <Badge variant="secondary" className="control-text">
              Neural Machine Translation
            </Badge>
          </div>

          <p className="text-foreground academic-text leading-relaxed">
            The dominant sequence transduction models are based on complex recurrent or convolutional neural networks
            that include an encoder and a decoder. The best performing models also connect the encoder and decoder
            through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely
            on attention mechanisms, dispensing with recurrence and convolutions entirely.
          </p>
        </div>
      </div>
    </Card>
  )
}
