<div align="center">

# 🏆 AI Hackathons

**รวมงาน hackathon และ Kaggle competition ของ HexTex**

</div>

---

Repository นี้รวบรวม code และเทคนิคจากการแข่ง hackathon / Kaggle ต่าง ๆ หวังว่าจะเป็นประโยชน์กับผู้เข้าชมไม่มากก็น้อย หากมีข้อผิดพลาดขออภัยมา ณ ที่นี้ด้วยนะครับ — HexTex 😸

**1 โฟลเดอร์ = 1 งาน** แต่ละงานมี `README.md` ของตัวเองที่เล่าโจทย์ วิธีทำ และผลลัพธ์ครบในที่เดียว เปิดโฟลเดอร์ไหนก็อ่านจบได้โดยไม่ต้องย้อนมาที่นี่

## 🗺️ สารบัญ

### 🏁 Hackathons

| # | งาน | Task | Result |
|:-:|---|---|---|
| 1 | 🥇 [Human Activity Recognition](Hackathons/Human_Activity_Recognition/) | Time-series Classification (9 คลาส) | **ชนะเลิศ** on-site |
| 2 | 📈 [Pre-Human Activity Recognition](Hackathons/Pre_Human_Activity_Recognition/) | Time-series Classification (6 คลาส) | รอบเตรียมตัว |
| 3 | 🍐 [Durian Hackathon](Hackathons/Durian_Hackathon/) | Image Classification ×3 | 🏅 อันดับ 5 · Private #3 |
| 4 | 🏨 [Hotel Review Sentiment Analysis](Hackathons/Hotel_Review_Sentiment_Analysis/) | Text → Rating (1–5) | 🚧 กำลังทำ |
| 5 | 🛣️ [Road Users Detection](Hackathons/Road_Users_Detection/) | Object Detection (11 คลาส) | 🔥 กำลังทำ |

### 🚜 Kaggle Competitions

| # | งาน | Task | Result |
|:-:|---|---|---|
| 1 | 🎮 [Kaggriculture](Kaggles/Kaggriculture/) | Simulation Agent (2-player farming sim) | 🔥 กำลังแข่ง |
| 2 | 🚢 [Titanic](Kaggles/Titanic/) | Tabular Classification | ✅ |
| 3 | 🛸 [Spaceship Titanic](Kaggles/Spaceship_Titanic/) | Tabular Classification | ✅ |

### 🧪 Mini Projects

| # | งาน | Task | Result |
|:-:|---|---|---|
| 1 | 🔢 [Thai Handwritten Numbers](mini_projects/thai_number_handwritten_classification/) | Image Classification (๐–๙) | ✅ |

---

## 🏁 Hackathons

#### Human Activity Recognition

🥇 งานแข่ง on-site ณ มหาวิทยาลัยมหิดล รายการ **Mahidol × SuperAI** โจทย์คือรับสัญญาณ accelerometer และ gyroscope แล้วบอกว่าคนคนนั้นกำลังทำท่าอะไรใน 9 ท่า จุดที่ทำให้ชนะคือการ **สร้าง feature ต่อ window** ให้ดีก่อนโยนเข้าโมเดล ไม่ใช่การหาโมเดลที่ใหญ่ขึ้น

> **Task** : Time-series Classification (9 คลาส) &nbsp;|&nbsp; **Tools** : AutoGluon Tabular · pandas &nbsp;|&nbsp; **Result** : 🥇 ชนะเลิศ

#### Pre-Human Activity Recognition

📈 รอบเตรียมตัวก่อนขึ้นเวที on-site ใช้แค่ accelerometer แยก 6 ท่า เป็นที่ทดลองว่า feature ชุดไหนอยู่รอด ก่อนเอาสูตรเดียวกันไปต่อยอดในรอบจริง

> **Task** : Time-series Classification (6 คลาส) &nbsp;|&nbsp; **Tools** : statistical features + FFT · AutoGluon Tabular

#### Durian Hackathon

🍐 Hackathon ด้าน Image Classification ณ มหาวิทยาลัยสงขลานครินทร์ วิทยาเขตภูเก็ต งานเดียวแต่มี 3 โจทย์ย่อย โจทย์หลักคือจำแนกสาเหตุความเสียหายของทุเรียน 4 คลาส ซึ่งยากตรงที่ทั้งเชื้อราและเพลี้ยต่างก็มีหลายชนิดปนอยู่ในคลาสเดียวกัน

| โจทย์ย่อย | สิ่งที่ทำ | Models |
|---|---|---|
| [Durian Disease Classification](Hackathons/Durian_Hackathon/Durian_Disease_Classification/) | จำแนกสาเหตุความเสียหายของทุเรียน 4 คลาส | MaxViT (Lightning) · YOLOv11x-cls · CLIP zero-shot |
| [Fruit Classification](Hackathons/Durian_Hackathon/Fruit_Classification/) | จำแนกชนิดผลไม้ | MaxViT |
| [Sugarcane Disease Classification](Hackathons/Durian_Hackathon/Sugarcane_Disease_Classification/) | จำแนกโรคอ้อย | MaxViT |

> **Task** : Image Classification &nbsp;|&nbsp; **Tools** : timm (MaxViT) · PyTorch Lightning · Ultralytics · CLIP &nbsp;|&nbsp; **Result** : 🏅 อันดับ 5 (Private score #3)

#### Road Users Detection

🛣️ ตรวจจับผู้ใช้ถนน 11 ประเภทจากภาพกล้องจราจรในไทย ตั้งแต่คนเดินเท้า จักรยาน มอเตอร์ไซค์ ไปจนถึงรถตุ๊กตุ๊กและรถฉุกเฉิน ความยากอยู่ที่ภาพจริงบนถนนมีรถบังกันเป็นชั้น ๆ กล่องซ้อนทับกันหนาแน่น ซึ่งเป็นจุดที่ NMS มักตัดกล่องที่ถูกต้องทิ้ง รอบนี้เลยตั้งใจเทรนเองด้วยโมเดลตระกูล **DETR** ที่ทำนายเป็นเซ็ตโดยตรงและไม่ต้องใช้ NMS

> **Task** : Object Detection (11 คลาส) &nbsp;|&nbsp; **Tools** : DETR family (เป้าหมาย Co-DETR) &nbsp;|&nbsp; **Status** : 🔥 กำลังทำ

#### Hotel Review Sentiment Analysis

🏨 ทำนายคะแนนรีวิวโรงแรม 1–5 ดาว จากข้อความรีวิวภาษาอังกฤษ กำลังทดลองสาย LLM อยู่ ยังไม่สรุปผล

> **Task** : Text → Rating &nbsp;|&nbsp; **Tools** : Qwen3-0.6B · transformers &nbsp;|&nbsp; **Status** : 🚧 กำลังทำ

---

## 🚜 Kaggle Competitions

#### Kaggriculture

🎮 Simulation competition ของ Kaggle × Google เล่นเป็นเกมทำฟาร์ม 2 ผู้เล่นที่ใช้ตลาดร่วมกัน 720 เทิร์น ตัดสินกันที่เงินในธนาคารตอนจบ ไม่ใช่งาน machine learning แต่เป็นงาน **วางแผนเศรษฐกิจ + จัดคิวแรงงาน** ล้วน ๆ เขียนเป็น python ธรรมดาไม่มีโมเดล ประวัติการพัฒนา agent v1 ถึง v23 พร้อมผลวัดทุกเวอร์ชันอยู่ใน README ของโฟลเดอร์

> **Task** : Simulation Agent &nbsp;|&nbsp; **Tools** : kaggle-environments · pure python (rule-based planner) &nbsp;|&nbsp; **Status** : 🔥 กำลังแข่ง

#### Titanic

🚢 โจทย์คลาสสิกของ Kaggle ทำนายว่าผู้โดยสารรอดชีวิตหรือไม่ ใช้เป็นที่ลองของ

> **Task** : Tabular Classification &nbsp;|&nbsp; **Tools** : AutoGluon Tabular

#### Spaceship Titanic

🛸 เวอร์ชันอวกาศของ Titanic ทำนายว่าผู้โดยสารถูกส่งข้ามมิติไปหรือเปล่า

> **Task** : Tabular Classification &nbsp;|&nbsp; **Tools** : AutoGluon Tabular

---

## 🧪 Mini Projects

#### Thai Handwritten Numbers

🔢 จำแนกตัวเลขไทยเขียนมือ ๐–๙ ด้วยการ fine-tune YOLO11x-cls รันบน Google Colab

> **Task** : Image Classification &nbsp;|&nbsp; **Tools** : Ultralytics (YOLO11x-cls)

---

## 📁 โครงสร้างของ Repository

```
AI_Hackathons
├── Hackathons      🏁 งานแข่ง on-site / InClass
├── Kaggles         🚜 Kaggle competitions
└── mini_projects   🧪 งานทดลองเล็ก ๆ
```

แต่ละงานอยู่ในโฟลเดอร์ของตัวเอง มี `README.md` เล่าโจทย์และผลลัพธ์ ส่วน notebook หรือ `.py` ของงานนั้นอยู่ข้างในเลย
งานที่มีโค้ดรันจริงจะมี `pyproject.toml` ของตัวเอง ติดตั้งด้วย `uv sync` ในโฟลเดอร์นั้นได้เลย ไม่ต้องพึ่ง environment กลาง

ข้อมูลและผลลัพธ์ไม่ขึ้น git — `datasets/`, `data/`, `models/`, `submissions/`, `episodes/` ถูก ignore ไว้ทั้งหมด ต้องโหลด dataset เองตามที่ README ของแต่ละงานบอก

## 🙏 Special Thanks

- Tan 👾 — <https://github.com/tara-tan>
- N'PP 🦆 — <https://github.com/Makufff>
- Gun 🐰 — <https://github.com/Rufflogix>

## 📄 License

[MIT](LICENSE) © 2024–2026 HexTex
