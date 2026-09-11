# Pre-Human Activity Recognition 📈

Hackathon เตรียมความพร้อมก่อนงาน on-site **Mahidol × SuperAI Human Activity Recognition**

- **Data** — accelerometer (x, y, z) เป็น time-series ต่อ sample
- **Task** — จำแนกท่าทาง 6 คลาส: Walking, Jogging, Upstairs, Downstairs, Sitting, Standing
- **Approach** — สร้าง statistical features ต่อ window (mean/std/percentiles/FFT ฯลฯ) แล้วเทรนด้วย **AutoGluon Tabular**
- **Notebook** — [`notebooks/Pre_Human_Activity_Recognition.ipynb`](notebooks/Pre_Human_Activity_Recognition.ipynb)

> Notebook อ้างอิง path `./datasets`, `./database`, `./features`, `./submissions` จาก project root — วาง dataset ไว้ที่ `datasets/` แล้วรันจากโฟลเดอร์นี้ (โฟลเดอร์เหล่านี้ถูก git-ignore)

## ⭐ Special Thanks
- Tan 👾 — <https://github.com/tara-tan>
- N'PP 🦆 — <https://github.com/Makufff>
