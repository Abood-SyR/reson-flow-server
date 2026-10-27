FROM python:3.11-slim

WORKDIR /app

# تثبيت التبعيات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# HF Spaces يتطلب التشغيل كمستخدم uid 1000
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

# HF Spaces يستخدم المنفذ 7860
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]