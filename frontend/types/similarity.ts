export interface SimilarQuestion {
  id: string;
  title: string;
  score: number;
  answer_count: number;
  has_accepted_answer: boolean;
  similarity: number;
}
