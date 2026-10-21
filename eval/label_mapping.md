# Label Mapping — CONFIRMED (do not guess, do not change)

Source of truth: `chat_analyzer/services/fine_tune_sentiment.py` line 52:

    label_name = {0: 'Negative', 1: 'Neutral', 2: 'Positive'}.get(label, 'Unknown')

Applied to: `chat_analyzer/data/labeled_data/labeledsentimentdatatwo_balanced.csv`

| CSV value | Sentiment |
|---|---|
| 0 | Negative |
| 1 | Neutral |
| 2 | Positive |

This mapping is authoritative for:
- eval/annotation_guideline.md (annotator options)
- scripts/compute_agreement.py (κ label vectors)
- supervisor + classmate forms (option order)

Any change to this mapping invalidates the entire eval study — treat as frozen.
