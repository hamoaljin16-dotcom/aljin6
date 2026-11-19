from playwright.async_api import async_playwright
from cryptography.fernet import Fernet

# مفتاح التشفير جاهز هنا
cipher = Fernet("hD8bN6O2m2q7X4p8Z9w0Y1v3T5r7U9i1O3p5A7s9D0f=".encode())

async def login_and_solve(username: str, encrypted_password: str):
    try:
        password = cipher.decrypt(encrypted_password.encode()).decode()
    except Exception:
        return {"success": False, "message": "خطأ في فك تشفير كلمة المرور."}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto("https://me-portal.qureo.education/login", timeout=60000)
            # محاكاة انتظار (هنا بيتحط كود تسجيل الدخول الحقيقي بعدين)
            await page.wait_for_timeout(3000)
            
            return {"success": True, "message": "تم الاتصال بالمنصة (الكود شغال والمتصفح بيفتح)."}
            
        except Exception as e:
            return {"success": False, "message": f"حدث خطأ: {str(e)}"}
        finally:
            await browser.close()
