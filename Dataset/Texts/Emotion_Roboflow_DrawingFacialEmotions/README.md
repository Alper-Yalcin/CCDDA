# Emotion Roboflow Drawing Facial Emotions

Images were processed with Roboflow model `drawing-facial-emotions/1`.

This model is an object detection model, not a whole-image classifier. It returns
face/expression detections when it finds them. Images without detections are kept
in `predictions.csv` as `NoDetection` and are not copied into class folders.

Source model page:
https://universe.roboflow.com/tsz-cheung-shawn-wei-jmvvc/drawing-facial-emotions/model/1

## Output

- Images: `Images/Emotion_Roboflow_DrawingFacialEmotions/<split>/<label>/*.jpg`
- Predictions: `Texts/Emotion_Roboflow_DrawingFacialEmotions/predictions.csv`
- Counts: `Texts/Emotion_Roboflow_DrawingFacialEmotions/class_counts.csv`
- Native model class counts: `Texts/Emotion_Roboflow_DrawingFacialEmotions/model_class_counts.csv`

## Summary

- Total images processed: 10860
- Images with a detection: 2413
- Prediction errors: 1

## Note

Roboflow reports this version as trained on 432 images with mAP@50 25.4%,
precision 51.0%, and recall 20.1%. Treat this output as pseudo-labels that need
manual review before thesis-grade ground truth use.
