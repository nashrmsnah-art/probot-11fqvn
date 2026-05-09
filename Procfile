    worker: python main.py
    ```
    *(تأكد أن ملف الكود الأساسي اسمه `main.py`)*.

---

## الخطوة الثانية: الرفع على GitHub
1. افتح حسابك على [GitHub](https://github.com/).
2. أنشئ مستودعاً جديداً (**New Repository**)، اجعله **Private** (خاص) لحماية كودك.
3. ارفع الملفات الثلاثة (`main.py`, `requirements.txt`, `Procfile`) إلى المستودع.

---

## الخطوة الثالثة: الربط مع Railway
1. اذهب إلى موقع [Railway.app](https://railway.app/) وسجل دخولك عبر حساب GitHub.
2. اضغط على **+ New Project**.
3. اختر **Deploy from GitHub repo**.
4. اختر المستودع الذي أنشأته منذ قليل.
5. اضغط على **Deploy Now**.

---

## الخطوة الرابعة: إضافة التوكن (Variables)
لكي يعمل البوت دون كتابة التوكن داخل الكود (وهو الأفضل أمنياً)، اتبع الآتي في Railway:
1. اذهب إلى تبويب **Variables** في مشروعك على Railway.
2. أضف متغيراتك كالتالي:
   *   `BOT_TOKEN`: ضع توكن بوتك هنا.
   *   `ADMIN_ID`: ضع رقم الآيدي الخاص بك.
3. قم بتعديل السطور الأولى في كودك على GitHub لتصبح هكذا:
   
```python
   import os
   API_TOKEN = os.getenv("BOT_TOKEN")
   ADMIN_ID = int(os.getenv("ADMIN_ID"))
