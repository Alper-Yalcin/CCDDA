# Emotion Derived 6-Class Dataset

This is a derived dataset created from the local KIDO-style two-class emotion data.
The original files are not modified.

The new labels are pseudo-labels derived from each child's written reflection, not
new manual annotations. Use them in a thesis as secondary or weak labels.

## Labels

- Happiness_General
- Affection_Belonging
- Sadness_General
- Anger_Conflict
- Grief_Loss
- Fear_Anxiety

## Files

- Images: `Images/Emotion_Derived_6Class/<split>/<label>/*.jpg`
- Text metadata: `Texts/Emotion_Derived_6Class/Emotion_Derived_Train.csv`
- Text metadata: `Texts/Emotion_Derived_6Class/Emotion_Derived_Test.csv`
- Counts: `Texts/Emotion_Derived_6Class/class_counts.csv`

## Class Counts

```csv
split,label,count
train,Happiness_General,2622
train,Affection_Belonging,1992
train,Sadness_General,3626
train,Anger_Conflict,371
train,Grief_Loss,401
train,Fear_Anxiety,216
test,Happiness_General,446
test,Affection_Belonging,370
test,Sadness_General,647
test,Anger_Conflict,64
test,Grief_Loss,62
test,Fear_Anxiety,43
```

## Important Method Note

The original emotional ground truth remains Happiness/Sadness. These derived labels
are rule-based weak labels inferred from reflection text. They should be validated
manually on a sample before being presented as final emotion classes.
