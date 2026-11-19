import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database import User, LinkedAccount, SessionLocal
from solver import login_and_solve, cipher

# التوكن بتاعك جاهز هنا
TOKEN = "8879873627:AAGbzO3_X-Dppnz2KRrd1MhalCIOSIPNVbo"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_or_create_user(tg_user):
    db = SessionLocal()
    user = db.query(User).filter(User.id == tg_user.id).first()
    if not user:
        user = User(id=tg_user.id, username=tg_user.username)
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_or_create_user(update.effective_user)
    db = SessionLocal()
    accounts_count = db.query(LinkedAccount).filter(LinkedAccount.user_id == user.id).count()
    db.close()
    
    welcome_text = (
        "**Qureo Premium Student Space**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "مساحتك لإدارة حساباتك التعليمية ومتابعة الحل.\n\n"
        f"👤 **ملفك الشخصي**\n"
        f"الاسم: {update.effective_user.first_name}\n"
        f"ID: `{user.id}`\n\n"
        "📊 **ملخص الحساب**\n"
        f"🔗 الحسابات: {accounts_count} / 3\n"
        f"💎 عمليات الحل المتبقية اليوم: {user.daily_solves_left}\n"
        f"🔑 الاشتراك: {'مفعل ✅' if user.subscription_active else 'غير مفعل ❌'}\n"
        "📶 حالة الخدمة: متاح\n"
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
        await query.edit_message_text("🔗 **ربط حساب جديد**\n\nأرسل بياناتك بالصيغة التالية:\n`اسم_المستخدم كلمة_المرور`\n\n(مثال: `student123 pass123`)", parse_mode="Markdown")
        context.user_data['awaiting_link'] = True
        
    elif data == "my_accounts":
        db = SessionLocal()
        accounts = db.query(LinkedAccount).filter(LinkedAccount.user_id == query.from_user.id).all()
        db.close()
        if not accounts:
            await query.edit_message_text("🗄 ليس لديك حسابات مرتبطة. اضغط على 'ربط حساب'.")
        else:
            msg = "🗄 **حساباتك المرتبطة:**\n"
            for i, acc in enumerate(accounts, 1):
                msg += f"{i}. `{acc.qureo_username}`\n"
            await query.edit_message_text(msg, parse_mode="Markdown")
            
    elif data == "solve":
        db = SessionLocal()
        user = db.query(User).filter(User.id == query.from_user.id).first()
        account = db.query(LinkedAccount).filter(LinkedAccount.user_id == user.id).first()
        db.close()
        
        if not account:
            await query.edit_message_text("⚠️ يرجى ربط حساب أولاً.")
            return
            
        if user.daily_solves_left <= 0:
            await query.edit_message_text("❌ لقد استنفدت عدد عمليات الحل. قم بالترقية.")
            return
            
        await query.edit_message_text("⏳ جاري الاتصال بالمنصة وبدء الحل...")
        result = await login_and_solve(account.qureo_username, account.qureo_password_encrypted)
        
        if result['success']:
            db = SessionLocal()
            user.daily_solves_left -= 1
            db.commit()
            db.close()
            await query.edit_message_text(f"✅ {result['message']}")
        else:
            await query.edit_message_text(f"❌ {result['message']}")
            
    elif data == "help":
        await query.edit_message_text("👩‍🦰 **للمساعدة**\n\nيرجى التواصل مع المطور: @YourUsername", parse_mode="Markdown")
    else:
        await query.edit_message_text("هذه الميزة قيد التطوير قريباً.")

async def handle_link_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_link'):
        text = update.message.text.strip()
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ صيغة خاطئة. أرسل: `اسم_المستخدم كلمة_المرور`")
            return
        
        username, password = parts
        encrypted_pw = cipher.encrypt(password.encode()).decode()
        
        db = SessionLocal()
        count = db.query(LinkedAccount).filter(LinkedAccount.user_id == update.effective_user.id).count()
        if count >= 3:
            await update.message.reply_text("❌ وصلت للحد الأقصى (3 حسابات).")
        else:
            new_acc = LinkedAccount(user_id=update.effective_user.id, qureo_username=username, qureo_password_encrypted=encrypted_pw)
            db.add(new_acc)
            db.commit()
            await update.message.reply_text(f"✅ تم ربط الحساب `{username}` بنجاح! يمكنك الآن الضغط على 'ابدأ الحل'.")
        db.close()
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
