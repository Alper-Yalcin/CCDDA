# Emotion SigLIP 4-Class Dataset

This dataset was automatically classified from the local KIDO-style child
drawing images using a zero-shot vision-language model.

## Model

- Model: `google/siglip-base-patch16-224`
- Method: zero-shot image classification with text prompts

## Labels and Prompts

| Label | Prompt |
| --- | --- |
| Happy | a child drawing expressing happiness |
| Sad | a child drawing expressing sadness |
| Angry | a child drawing expressing anger |
| Fear | a child drawing expressing fear or anxiety |

## Files

- Images: `Images/Emotion_SigLIP_4Class/<split>/<label>/*.jpg`
- Predictions: `Texts/Emotion_SigLIP_4Class/predictions.csv`
- Counts: `Texts/Emotion_SigLIP_4Class/class_counts.csv`

## Class Counts

```csv
split,label,count
train,Happy,4076
train,Sad,2653
train,Angry,588
train,Fear,1911
test,Happy,738
test,Sad,435
test,Angry,115
test,Fear,344
```

## Important Note

These are automatic model predictions, not human-verified clinical labels. Use
them as pseudo-labels and manually review a sample, especially low-confidence
predictions, before presenting them as final ground truth.
