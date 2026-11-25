import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest, Conflict
import db
from solver import login_and_solve, cipher

# 🚨 التوكن بتاعك ثابت هنا زي ما طلبت
TOKEN = "8879873627:AAFZuAICIl11LRffbQ0NP5vVUV6MUeTRFRY"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
db.init_db()

# --- دالة لفتح بورت وهمي عشان منصة Cloady متقفلش البوت ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), BaseHTTPRequestHandler)
    server.serve_forever()

# تشغيل السيرفر الوهمي في الخلفية
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- الأزرار الثابتة ---
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("حساباتي 📚", callback_data="my_accounts"), InlineKeyboardButton("إضافة حساب +", callback_data="link")],
        [InlineKeyboardButton("معلومات الحساب 👤", callback_data="info"), InlineKeyboardButton("بدء الحل ⚡", callback_data="solve")],
        [InlineKeyboardButton("إنجازاتي 📈", callback_data="stats"), InlineKeyboardButton("تفعيل اشتراك VIP 🏷️", callback_data="sub")],
        [InlineKeyboardButton("دعوة صديق 🎁", callback_data="invites"), InlineKeyboardButton("المساعدة ❓", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- رسالة البدء (الواجهة الرئيسية) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id, update.effective_user.username)
    accounts_count = db.get_accounts_count(user[0])
    
    welcome_text = (
        "**QUREO مركز التعلم**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"أهلاً **{update.effective_user.first_name}**🕊🤍، دي لوحة حسابك\n"
        "وخدماتك.\n\n"
        "**حسابك**\n"
        f"🆔 `{user[0]}`\n"
        f"🔗 الحسابات المرتبطة: {accounts_count} / 3\n"
        f"⚡ الحلول المتبقية اليوم: {user[3]} / 1\n\n"
        "**الاشتراك والخدمة**\n"
        f"🏷️ اشتراكك: {'مفعل VIP 👑' if user[2] else 'غير مفعل ❌'}\n"
        "🧭 وضع البوت: مجاني\n"
        "🛰️ حالة الخدمة: متاحة\n"
        f"🎁 دعوات ناجحة: 0\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "استخدم الأزرار بالأسفل للتنقل بسرعة."
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

# --- معالج الأزرار ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    user = db.get_user(user_id, query.from_user.username)
    accounts_count = db.get_accounts_count(user_id)

    if data == "info":
        text = (
            "**معلومات الحساب**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👤 **الاسم:** {query.from_user.first_name}\n"
            f"📝 **اسم المستخدم:** @{query.from_user.username if query.from_user.username else 'لا يوجد'}\n"
            f"🆔 **Telegram ID:** `{user_id}`\n\n"
            f"🔗 **الحسابات التعليمية:** {accounts_count} / 3\n"
            f"⚡ **الحلول المتبقية اليوم:** {user[3]} من 1 متبقية\n"
            f"🏷️ **حالة الاشتراك:** {'مفعل VIP' if user[2] else 'غير مفعل'}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "اختر حساباً تعليمياً لعرض تفاصيله، أو أضف حساباً جديداً."
        )
        keyboard = [
            [InlineKeyboardButton("إضافة حساب +", callback_data="link")],
            [InlineKeyboardButton("الرئيسية 🏠", callback_data="main_menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "my_accounts":
        accounts = db.get_accounts(user_id)
        if not accounts:
            text = "لا توجد حسابات مرتبطة بعد."
            keyboard = [[InlineKeyboardButton("ربط حساب 🔗", callback_data="link")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            text = "🗄 **حساباتك المرتبطة:**\n\n"
            for i, acc in enumerate(accounts, 1):
                text += f"{i}. `{acc[2]}`\n"
            keyboard = [
                [InlineKeyboardButton("بدء الحل ⚡", callback_data="solve")],
                [InlineKeyboardButton("الرئيسية 🏠", callback_data="main_menu")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "sub":
        await query.edit_message_text("ابعت كود الاشتراك: 🏷️", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="main_menu")]]))
        context.user_data['awaiting_vip'] = True

    elif data == "stats":
        text = f"إحصائياتك 📊\nالحسابات: {accounts_count}\nعمليات الحل: {1 - user[3] if user[3] <= 1 else 0}"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "help":
        text = "مركز المساعدة ✨\nاربط حسابك أولاً، ثم افتح حساباتي واختر «ابدأ الحل» وحدد المادة."
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "invites":
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        text = f"رابط الدعوة الخاص بك:\n`{ref_link}`"
        await query.edit_message_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

    elif data == "link":
        await query.edit_message_text("🔗 **ربط حساب جديد**\n\nأرسل بياناتك بالصيغة التالية:\n`Login_ID Password`", parse_mode="Markdown")
        context.user_data['awaiting_link'] = True

    elif data == "solve":
        accounts = db.get_accounts(user_id)
        if not accounts:
            await query.edit_message_text("⚠️ يرجى ربط حساب أولاً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ربط حساب 🔗", callback_data="link")]]))
            return
        if user[3] <= 0:
            await query.edit_message_text("❌ لقد استنفدت عدد عمليات الحل. قم بالترقية.", reply_markup=get_main_keyboard())
            return
            
        await query.edit_message_text("⏳ جاري الاتصال بالمنصة وبدء الحل...")
        result = await login_and_solve(accounts[0][2], accounts[0][3], query=query)
        
        if result['success']:
            db.decrease_solve(user_id)
            await query.edit_message_text(f"✅ {result['message']}", reply_markup=get_main_keyboard())
        else:
            await query.edit_message_text(f"❌ {result['message']}", reply_markup=get_main_keyboard())

    elif data == "main_menu":
        context.user_data['awaiting_link'] = False
        context.user_data['awaiting_vip'] = False
        await start(update, context)

# --- معالج الرسائل النصية ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_link'):
        text = update.message.text.strip()
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ صيغة خاطئة. أرسل: `Login_ID Password`")
            return
        
        username, password = parts
        encrypted_pw = cipher.encrypt(password.encode()).decode()
        
        if db.get_accounts_count(update.effective_user.id) >= 3:
            await update.message.reply_text("❌ وصلت للحد الأقصى (3 حسابات).")
        else:
            db.add_account(update.effective_user.id, username, encrypted_pw)
            await update.message.reply_text(f"✅ تم ربط الحساب `{username}` بنجاح!")
        context.user_data['awaiting_link'] = False

    elif context.user_data.get('awaiting_vip'):
        await update.message.reply_text("✅ تم استلام الكود، جاري التحقق منه...")
        context.user_data['awaiting_vip'] = False

# --- معالج الأخطاء ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, Conflict):
        return 
    if isinstance(context.error, BadRequest) and "Message is not modified" in str(context.error):
        return
    print(f"Update {update} caused error {context.error}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    
    print("البوت شغال...")
    app.run_polling()

if __name__ == '__main__':
    main()
