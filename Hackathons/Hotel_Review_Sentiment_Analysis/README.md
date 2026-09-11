# Hotel Review Sentiment Analysis 🚧

ทำนายคะแนนรีวิวโรงแรม (Rating 1–5) จากข้อความรีวิวภาษาอังกฤษ

- **Data** — `data/train_data.csv` (ID, Review, Rating), `data/test_data.csv`, `data/submit.csv` (sample) — git-ignored
- **Status** — กำลังทดลอง LLM-based approach (Qwen3-0.6B) ใน [`notebooks/hotel_review_sentiment_analysis.ipynb`](notebooks/hotel_review_sentiment_analysis.ipynb)

```bash
export HF_TOKEN=...      # ห้าม hardcode token ใน notebook
```
