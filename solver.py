from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from cryptography.fernet import Fernet

# مفتاح التشفير بتاعك
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
            # 1. فتح رابط منصة Qureo الرسمي
            await page.goto("https://e-portal.qureo.education", timeout=60000, wait_until="networkidle")
            
            # 2. حل مشكلة صفحة اختيار البوابة (لو ظهرت)
            # لو ظهر زرار "Go to Learning Login"، البوت هيضغط عليه
            try:
                learning_btn = page.locator("text=Go to Learning Login")
                if await learning_btn.is_visible(timeout=3000):
                    await learning_btn.click()
                    await page.wait_for_timeout(2000)
            except:
                pass # لو مظهرش، يبقى إحنا في صفحة الدخول على طول
            
            # 3. انتظار ظهور خانة الـ Login ID
            await page.wait_for_selector('input[type="text"]', timeout=15000)
            
            # 4. إدخال البيانات
            # بياخد الـ Login ID من اللي المستخدم بعته في البوت
            await page.fill('input[type="text"]', username)
            # بياخد الباسورد المفكوك
            await page.fill('input[type="password"]', password)
            
            # 5. الضغط على زر Login
            await page.locator('button:has-text("Login")').click()
            
            # 6. انتظار تحميل صفحة الطالب
            await page.wait_for_timeout(5000)
            
            # =======================================================
            # 🚨 هنا بقى السحر كله: إحنا دلوقتي جوه حساب الطالب
            # =======================================================
            
            # هنعمل إيه دلوقتي؟ لازم ندور على زرار "ابدأ التحدي" أو "Start Lesson"
            # وعشان نعمل ده، محتاجين نشوف شكل الصفحة اللي بعد الدخول
            
            return {"success": True, "message": "تم تسجيل الدخول بنجاح إلى منصة Qureo! (محتاجين سكرين شوت للصفحة اللي بعد الدخول عشان نظبط كود الحل)."}
            
        except PlaywrightTimeoutError:
            return {"success": False, "message": "المنصة اتأخرت في الاستجابة، أو حقل الدخول مش ظاهر (تأكد من الرابط)."}
        except Exception as e:
            return {"success": False, "message": f"حدث خطأ: {str(e)}"}
        finally:
            await browser.close()
