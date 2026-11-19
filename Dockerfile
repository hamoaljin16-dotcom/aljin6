# استخدام صورة رسمية تحتوي على بايثون و Playwright جاهزين
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# تعيين مجلد العمل
WORKDIR /app

# نسخ المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# أمر تشغيل البوت
CMD ["python", "main.py"]
