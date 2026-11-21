import base64
import json
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from cryptography.fernet import Fernet
from openai import OpenAI

# مفتاح التشفير بتاعك
cipher = Fernet("hD8bN6O2m2q7X4p8Z9w0Y1v3T5r7U9i1O3p5A7s9D0f=".encode())

# إعداد عميل OpenRouter بالمفتاح بتاعك
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

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
            # 1. تسجيل الدخول للمنصة
            await page.goto("https://e-portal.qureo.education", timeout=60000, wait_until="networkidle")
            
            # الضغط على بوابة التعلم لو ظهرت
            try:
                learning_btn = page.locator("text=Go to Learning Login")
                if await learning_btn.is_visible(timeout=3000):
                    await learning_btn.click()
                    await page.wait_for_timeout(2000)
            except:
                pass
            
            # إدخال البيانات
            await page.wait_for_selector('input[type="text"]', timeout=15000)
            await page.fill('input[type="text"]', username)
            await page.fill('input[type="password"]', password)
            await page.locator('button:has-text("Login")').click()
            
            # انتظار التحميل
            await page.wait_for_timeout(6000)
            
            if "login" in page.url:
                return {"success": False, "message": "فشل الدخول: تأكد من الـ Login ID والباسورد."}

            # ==========================================
            # 🤖 الذكاء الاصطناعي (OpenRouter)
            # ==========================================
            
            # التقاط صورة للشاشة
            screenshot_bytes = await page.screenshot(type="png")
            base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            prompt = """أنت مساعد أتمتة محترف. حلل صورة الشاشة هذه لمنصة Qureo التعليمية.
            المطلوب منك تحديد الخطوة التالية التي يجب على البوت القيام بها.
            
            ملاحظات هامة:
            - إذا كان هناك زر لبدء التحدي أو الدرس، حدد إجراء "click".
            - إذا كان هناك سؤال يحتاج إلى إجابة، حدد إجراء "solve" وضع الإجابة في حقل solution.
            - أعد الرد بصيغة JSON فقط، بدون أي نصوص إضافية أو علامات Markdown.
            
            الشكل المطلوب:
            {
                "action": "click" أو "type" أو "solve" أو "none",
                "selector": "محدد CSS (مثل button.start-btn)",
                "text": "النص المراد كتابته",
                "solution": "الحل الكامل"
            }"""
            
            # إرسال الصورة للنموذج المجاني
            response = client.chat.completions.create(
                model="qwen/qwen2.5-vl-72b-instruct:free", 
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]}
                ],
                max_tokens=1000
            )
            
            # استلام الرد وتحويله
            result_text = response.choices[0].message.content.strip()
            
            # تنظيف الرد من أي علامات زيادة
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            action_data = json.loads(result_text)
            
            # تنفيذ الإجراء بناءً على كلام الذكاء الاصطناعي
            if action_data.get("action") == "click":
                await page.locator(action_data["selector"]).click()
                return {"success": True, "message": f"✅ تم النقر على: {action_data['selector']}"}
            elif action_data.get("action") == "type":
                await page.fill(action_data["selector"], action_data["text"])
                return {"success": True, "message": "✅ تم كتابة النص المطلوب بواسطة AI."}
            elif action_data.get("action") == "solve":
                return {"success": True, "message": f"🧠 الحل المقترح: {action_data.get('solution')}"}
            
            return {"success": True, "message": "تم الدخول، لكن الذكاء الاصطناعي لم يجد إجراءً واضحاً."}
            
        except PlaywrightTimeoutError:
            return {"success": False, "message": "المنصة تأخرت في الاستجابة."}
        except Exception as e:
            return {"success": False, "message": f"حدث خطأ: {str(e)}"}
        finally:
            await browser.close()
