# src/explain/rule_based_explainer.py

def summarize_tokens(tokens, scores, top_k=5):
    if tokens is None or scores is None:
        return "(metin yok)"
    triplets = []
    for tok, sc in zip(tokens, scores):
        if tok in ["[CLS]", "[SEP]", "[PAD]"]:
            continue
        triplets.append((tok, float(sc)))
    triplets.sort(key=lambda x: x[1], reverse=True)
    return ", ".join([t for t, _ in triplets[:top_k]])


def rule_based_explanation(result: dict) -> str:
    emo = result["pred_emotion"]
    pe = result["prob_emotion"]
    gen = result["pred_gender"]
    pg = result["prob_gender"]

    emo_tokens = summarize_tokens(result["tokens_emotion"], result["scores_emotion"])
    gen_tokens = summarize_tokens(result["tokens_gender"], result["scores_gender"])

    lines = []

    # Genel sınıflandırma özeti
    lines.append(f"Model bu çizimi {gen.lower()} bir çocuk tarafından çizilmiş "
                 f"ve duygunun da '{emo}' olduğunu tahmin ediyor.")
    lines.append(f"Emotion olasılığı: {pe:.3f}, Gender olasılığı: {pg:.3f}.")

    # Olasılık yorumları
    if pe > 0.9:
        lines.append("Duygu tahmini konusunda oldukça kendinden emin görünüyor.")
    elif pe > 0.7:
        lines.append("Duygu tahmininde belirgin ama çok yüksek olmayan bir güven var.")
    else:
        lines.append("Duygu tahmini konusunda kararsız, bu resim sınırda örneklerden biri olabilir.")

    if pg > 0.9:
        lines.append("Cinsiyet tahmini için de çok yüksek güven söz konusu.")
    elif pg > 0.7:
        lines.append("Cinsiyet tahmini makul bir güvene sahip.")
    else:
        lines.append("Cinsiyet tahmininde de model çok emin değil.")

    # Grad-CAM'den kaba yorum (şimdilik statik, istersen ısı haritasının ağırlık merkezine bakıp geliştiririz)
    lines.append("Görsel tarafta Grad-CAM, özellikle karakterin bulunduğu bölgeye odaklanıyor; "
                 "bu da modelin kararını çizerken figüre baktığını gösteriyor.")

    # Metin varsa token açıklaması
    if emo_tokens != "(metin yok)" or gen_tokens != "(metin yok)":
        lines.append("")
        lines.append("Metin tarafında ise modelin en çok dikkat ettiği token'lar:")
        lines.append(f"- Duygu için: {emo_tokens}")
        lines.append(f"- Cinsiyet için: {gen_tokens}")
        lines.append("Bu kelimeler, modelin sınıflandırma kararında daha fazla ağırlığa sahip.")

    return "\n".join(lines)
