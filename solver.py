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
        # 🚨 هنا الإضافة: إجبار المتصفح على استخدام DNS خارجي لحل مشكلة ERR_NAME_NOT_RESOLVED
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--dns-server=8.8.8.8',
                '--dns-server=1.1.1.1'
            ]
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # نغير wait_until لـ domcontentloaded عشان ميهنجش لو في صور بطيئة
            await page.goto("https://e-portal.qureo.education", timeout=60000, wait_until="domcontentloaded")
            
            try:
                learning_btn = page.locator("text=Go to Learning Login")
                if await learning_btn.is_visible(timeout=3000):
                    await learning_btn.click()
                    await page.wait_for_timeout(2000)
            except:
                pass
            
            await page.wait_for_selector('input[type="text"]', timeout=15000)
            await page.fill('input[type="text"]', username)
            await page.fill('input[type="password"]', password)
            await page.locator('button:has-text("Login")').click()
            
            await page.wait_for_timeout(6000)
            
            page_text = await page.locator("body").inner_text()
            error_keywords = ["Invalid", "failed", "Incorrect", "خطأ", "غير صحيح", "فشل"]
            is_error = any(word.lower() in page_text.lower() for word in error_keywords)
            
            if "login" in page.url or is_error:
                return {"success": False, "message": "فشل الدخول: تأكد من صحة الـ Login ID والباسورد."}

            # إرسال رسالة النجاح
            if query:
                try:
                    await query.edit_message_text("✅ تم تسجيل الدخول للمنصة بنجاح! جاري تحليل التحدي بالذكاء الاصطناعي...")
                except:
                    pass

            # الذكاء الاصطناعي
            screenshot_bytes = await page.screenshot(type="png")
            base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            prompt = """أنت مساعد أتمتة محترف. حلل صورة الشاشة هذه لمنصة Qureo التعليمية.
            المطلوب منك تحديد الخطوة التالية التي يجب على البوت القيام بها.
            أعد الرد بصيغة JSON فقط:
            {
                "action": "click" أو "type" أو "solve" أو "none",
                "selector": "محدد CSS",
                "text": "النص",
                "solution": "الحل"
            }"""
            
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
            
            result_text = response.choices[0].message.content.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            action_data = json.loads(result_text)
            
            if action_data.get("action") == "click":
                await page.locator(action_data["selector"]).click()
                return {"success": True, "message": f"✅ تم النقر على: {action_data['selector']}"}
            elif action_data.get("action") == "type":
                await page.fill(action_data["selector"], action_data["text"])
                return {"success": True, "message": "✅ تم كتابة النص المطلوب."}
            elif action_data.get("action") == "solve":
                return {"success": True, "message": f"🧠 الحل المقترح: {action_data.get('solution')}"}
            
            return {"success": True, "message": "تم الدخول، لكن الذكاء الاصطناعي لم يجد إجراءً."}
            
        except PlaywrightTimeoutError:
            return {"success": False, "message": "المنصة تأخرت في الاستجابة، أو سيرفر الاستضافة مش قادر يوصل للموقع."}
        except Exception as e:
            return {"success": False, "message": f"حدث خطأ: {str(e)}"}
        finally:
            await browser.close()
