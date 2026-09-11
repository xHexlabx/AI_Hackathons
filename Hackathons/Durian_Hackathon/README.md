# Durian Hackathon 🍐

Hackathon ด้าน Image Classification ณ มหาวิทยาลัยสงขลานครินทร์ วิทยาเขตภูเก็ต — pipeline หลัก (Durian Disease) ได้ **อันดับ 5 บน public LB และอันดับ 3 บน private score**

| Sub-project | Task | Models | Notebooks |
|---|---|---|---|
| [Durian_Disease_Classification](Durian_Disease_Classification/) | จำแนกสาเหตุความเสียหายของทุเรียน 4 คลาส | MaxViT (PyTorch Lightning), YOLOv11x-cls, CLIP zero-shot | [notebooks/](Durian_Disease_Classification/notebooks/) |
| [Fruit_Classification](Fruit_Classification/) | จำแนกชนิดผลไม้ | MaxViT | [notebooks/](Fruit_Classification/notebooks/) |
| [Sugarcane_Disease_Classification](Sugarcane_Disease_Classification/) | จำแนกโรคอ้อย | MaxViT | [notebooks/](Sugarcane_Disease_Classification/notebooks/) |

## คลาสของโจทย์ Durian Disease
1. ไม่เป็นโรค
2. หนอนและแมลงปีกแข็ง
3. เชื้อรา (ใบจุด, ใบจุดสาหร่าย, ราสนิม, ใบไหม้, ฟิวซาเรียม, รากเน่าโคนเน่า, ราดำ)
4. เพลี้ย (จักจั่นฝอย, เพลี้ยไก่แจ้, เพลี้ยนาสาร, เพลี้ยแป้ง, เพลี้ยหอย, ไรแดง)

> Notebook ทั้งหมดเขียนสำหรับ Google Colab (ดาวน์โหลดข้อมูลผ่าน Kaggle API ไปที่ `/content`)

## ⭐ Special Thanks
- N'PP 🦆 — <https://github.com/Makufff>
- Gun 🐰 — <https://github.com/Rufflogix>
