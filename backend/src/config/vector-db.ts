export interface VectorDocument {
  id: string;
  vector: number[];
  payload: Record<string, any>;
}

export class VectorDBClient {
  private collection = new Map<string, VectorDocument>();

  constructor(private provider: 'qdrant' | 'weaviate' | 'milvus' = 'qdrant') {
    console.log(`[VECTOR DB] Initialized client using provider: ${provider}`);
  }

  public async upsert(id: string, vector: number[], payload: Record<string, any>): Promise<boolean> {
    this.collection.set(id, { id, vector, payload });
    console.log(`[VECTOR DB] Indexed document: ${id} with metadata fields:`, Object.keys(payload));
    return true;
  }

  // Basic cosine similarity function
  private cosineSimilarity(v1: number[], v2: number[]): number {
    if (v1.length !== v2.length) return 0;
    let dotProduct = 0;
    let normA = 0;
    let normB = 0;
    for (let i = 0; i < v1.length; i++) {
      dotProduct += v1[i] * v2[i];
      normA += v1[i] * v1[i];
      normB += v2[i] * v2[i];
    }
    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  }

  public async query(vector: number[], topK: number = 3): Promise<VectorDocument[]> {
    const scoredDocs = Array.from(this.collection.values()).map(doc => {
      const score = this.cosineSimilarity(vector, doc.vector);
      return { doc, score };
    });
    
    // Sort descending by score
    scoredDocs.sort((a, b) => b.score - a.score);
    
    console.log(`[VECTOR DB] Query matched ${scoredDocs.length} items. Returning top ${topK}.`);
    return scoredDocs.slice(0, topK).map(item => item.doc);
  }
}
