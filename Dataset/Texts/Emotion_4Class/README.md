# Emotion 4-Class Dataset

This dataset was derived from the local two-class KIDO-style emotion dataset.
The original dataset was not modified.

## Labels

- Happy
- Sadness
- Anger
- Anxiety

## Derivation

- Original `Happiness` rows are mapped to `Happy`.
- Original `Sadness` rows are kept as `Sadness` unless the English reflection
  contains rule keywords for `Anger` or `Anxiety`.

These labels are weak/pseudo labels for `Anger` and `Anxiety`; validate a sample
manually before reporting them as final ground truth.

## Files

- Images: `Images/Emotion_4Class/<split>/<label>/*.jpg`
- Train metadata: `Texts/Emotion_4Class/Emotion_4Class_Train.csv`
- Test metadata: `Texts/Emotion_4Class/Emotion_4Class_Test.csv`
- Counts: `Texts/Emotion_4Class/class_counts.csv`

## Class Counts

```csv
split,label,count
train,Happy,4614
train,Sadness,3990
train,Anger,386
train,Anxiety,238
test,Happy,816
test,Sadness,703
test,Anger,66
test,Anxiety,47
```
