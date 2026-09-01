import { pipeline, env } from '@xenova/transformers';

// 1. Force the engine to never use the internet
env.allowRemoteModels = false;

// 2. Tell the engine exactly where our downloaded models are
// (This points to the public/models directory in a Vite app)
env.localModelPath = '/models/';

// Simple JS implementation of cosine similarity to replace FAISS
function cosineSimilarity(vecA: number[], vecB: number[]) {
  let dotProduct = 0.0;
  let normA = 0.0;
  let normB = 0.0;
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

// Sample bad vectors (in a real app, these would be precomputed and loaded from a JSON)
const SCAM_PHRASES = [
  "Your account has been suspended",
  "Share your OTP immediately",
  "You won a lottery",
  "Send money to this bitcoin address"
];

export class ScamShieldEdge {
  private extractor: any = null;
  private scamEmbeddings: number[][] = [];
  
  async init() {
    if (this.extractor) return;
    console.log("Loading AI Models locally in browser...");
    // Load the exact same MiniLM model used in the Python SDK!
    // Since env.allowRemoteModels is false, it will look at /models/Xenova/all-MiniLM-L6-v2/
    this.extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    
    // Precompute embeddings for our bad phrases
    for (const phrase of SCAM_PHRASES) {
      const output = await this.extractor(phrase, { pooling: 'mean', normalize: true });
      this.scamEmbeddings.push(Array.from(output.data));
    }
    console.log("Edge SDK initialized locally!");
  }

  async scanText(text: string) {
    if (!this.extractor) await this.init();

    const output = await this.extractor(text, { pooling: 'mean', normalize: true });
    const userEmbedding = Array.from(output.data) as number[];

    let maxSimilarity = 0;
    for (const scamEmb of this.scamEmbeddings) {
      const sim = cosineSimilarity(userEmbedding, scamEmb);
      if (sim > maxSimilarity) maxSimilarity = sim;
    }

    if (maxSimilarity > 0.6) {
      return {
        alert_level: 'red',
        confidence_score: maxSimilarity,
        explanation: 'Local AI detected high semantic similarity to known scam scripts.'
      };
    }
    
    return { alert_level: 'none', confidence_score: maxSimilarity, explanation: 'Looks safe locally.' };
  }
}

export const scamShield = new ScamShieldEdge();
