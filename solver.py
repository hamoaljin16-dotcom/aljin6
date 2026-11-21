import base64
import json
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from cryptography.fernet import Fernet
from openai import OpenAI

cipher = Fernet("hD8bN6O2m2q7X4p8Z9w0Y1v3T5r7U9i1O3p5A7s9D0f=".encode())

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

async def login_and_solve(username: str, encrypted_password: str, query=None):
    try:
        password = cipher.decrypt(encrypted_password.encode()).decode()
    except Exception:
        return {"success": False, "message": "خطأ في فك تشفير كلمة المرور."}

    async with async_playwright() as p:
        # 🚨 إعدادات جديدة لتخطي أخطاء SSL والشبكة
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',              # تعطيل فحص أمان الويب
                '--disable-site-isolation-trials',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-proxy-server',                   # تجاهل أي بروكسي في الاستضافة
                '--ssl-version-fallback-min=tls1.2'    # السماح بالاتصال بـ TLS 1.2
            ]
        )
        
        context = await browser.new_context(
            ignore_https_errors=True, # تجاهل أخطاء شهادة SSL
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. فتح رابط المنصة
            await page.goto("https://me-portal.qureo.education", timeout=90000, wait_until="domcontentloaded")
            
            # ... (باقي الكود كما هو: إدخال البيانات، التحقق، الذكاء الاصطناعي) ...
            # (يمكنك نسخ باقي الكود من ملفك السابق دون تغيير)
