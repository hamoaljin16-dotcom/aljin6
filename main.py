import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import db
from solver import login_and_solve, cipher

TOKEN = "8879873627:AAGbzO3_X-Dppnz2KRrd1MhalCIOSIPNVbo"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
db.init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id, update.effective_user.username)
    accounts_count = db.get_accounts_count(user[0])
    
    welcome_text = (
        "**Qureo Premium Student Space**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 **ملفك الشخصي**\n"
        f"الاسم: {update.effective_user.first_name}\n"
        f"ID: `{user[0]}`\n\n"
        "📊 **ملخص الحساب**\n"
        f"🔗 الحسابات: {accounts_count} / 3\n"
        f"💎 عمليات الحل المتبقية اليوم: {user[3]}\n"
        f"🔑 الاشتراك: {'مفعل ✅' if user[2] else 'غير مفعل ❌'}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "اختر الخدمة المطلوبة 👇"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔗 ربط حساب", callback_data="link"), InlineKeyboardButton("🗄 حساباتي", callback_data="my_accounts")],
        [InlineKeyboardButton("💎 ابدأ الحل", callback_data="solve"), InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")],
        [InlineKeyboardButton("🔑 الاشتراك", callback_data="sub"), InlineKeyboardButton("🎁 الدعوات", callback_data="invites")],
        [InlineKeyboardButton("👩‍🦰 المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "link":
        await query.edit_message_text("🔗 **ربط حساب جديد**\n\nأرسل بياناتك بالصيغة التالية:\n`اسم_المستخدم كلمة_المرور`", parse_mode="Markdown")
        context.user_data['awaiting_link'] = True
        
    elif data == "my_accounts":
        accounts = db.get_accounts(query.from_user.id)
        if not accounts:
            await query.edit_message_text("🗄 ليس لديك حسابات مرتبطة.")
        else:
            msg = "🗄 **حساباتك المرتبطة:**\n"
            for i, acc in enumerate(accounts, 1):
                msg += f"{i}. `{acc[2]}`\n"
            await query.edit_message_text(msg, parse_mode="Markdown")
            
    elif data == "solve":
        user = db.get_user(query.from_user.id)
        accounts = db.get_accounts(query.from_user.id)
        if not accounts:
            await query.edit_message_text("⚠️ يرجى ربط حساب أولاً.")
            return
        if user[3] <= 0:
            await query.edit_message_text("❌ لقد استنفدت عدد عمليات الحل.")
            return
            
        await query.edit_message_text("⏳ جاري الاتصال بالمنصة وبدء الحل...")
        result = await login_and_solve(accounts[0][2], accounts[0][3])
        
        if result['success']:
            db.decrease_solve(query.from_user.id)
            await query.edit_message_text(f"✅ {result['message']}")
        else:
            await query.edit_message_text(f"❌ {result['message']}")
            
    elif data == "help":
        await query.edit_message_text("👩‍🦰 **للمساعدة**\n\nتواصل مع المطور: @YourUsername", parse_mode="Markdown")
    else:
        await query.edit_message_text("هذه الميزة قيد التطوير.")

async def handle_link_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_link'):
        text = update.message.text.strip()
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ صيغة خاطئة. أرسل: `اسم_المستخدم كلمة_المرور`")
            return
        
        username, password = parts
        encrypted_pw = cipher.encrypt(password.encode()).decode()
        
        if db.get_accounts_count(update.effective_user.id) >= 3:
            await update.message.reply_text("❌ وصلت للحد الأقصى (3 حسابات).")
        else:
            db.add_account(update.effective_user.id, username, encrypted_pw)
            await update.message.reply_text(f"✅ تم ربط الحساب `{username}` بنجاح!")
        context.user_data['awaiting_link'] = False

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link_input))
    print("البوت شغال...")
    app.run_polling()

if __name__ == '__main__':
    main()
