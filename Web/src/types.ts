export type Page = 'home' | 'analysis' | 'about';

export type ApiResult = {
  prediction?: string;
  predicted_class?: string;
  pred_class?: string;
  class_name?: string;
  pred_emotion?: string;
  confidence?: number;
  confidence_score?: number;
  probability?: number;
  confidence_emotion?: number;
  probs?: number[];
  probabilities?: number[];
  probs_emotion?: number[];
  class_names?: string[];
  heatmap_b64?: string | null;
  heatmap_emotion_b64?: string | null;
  explanation?: string | null;
  gradcam_focus_region?: string;
};
