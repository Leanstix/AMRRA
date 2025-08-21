export async function POST(request) {
  try {
    const { url } = await request.json();
    
    // Mock data - same schema as the drag-and-drop provides
    const mockPaperData = {
      title: "Attention Is All You Need",
      abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
      claims: [
        {
          id: "claim-1",
          text: "Transformer models outperform traditional RNN/CNN architectures on translation tasks.",
          confidence: 0.92
        },
        {
          id: "claim-2",
          text: "Self-attention mechanisms can replace recurrent layers entirely.",
          confidence: 0.85
        },
        {
          id: "claim-3",
          text: "The Transformer architecture is more parallelizable than RNN-based models.",
          confidence: 0.95
        }
      ],
      url: url // Include the original URL
    };
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return Response.json(mockPaperData);
  } catch (error) {
    console.error("Error fetching paper:", error);
    return Response.json(
      { error: "Failed to fetch paper" },
      { status: 500 }
    );
  }
}