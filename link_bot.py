import re
import json
import os
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont

from keep_alive import keep_alive  # <--- YE NAYI LINE YAHAN JODNI HAI

# --- APNA NAYA BOT TOKEN YAHAN DAALEIN ---
BOT_TOKEN = "8518118037:AAGJl7oOuvI5GIy2yHiz0_zBtnfWiFNfuEc"

DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Start & Help Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    help_text = get_help_text(user_first_name)
    
    keyboard = [[InlineKeyboardButton("🔄 Updates", url="https://www.whatsapp.com/channel/0029VbCZGaF4SpkEyXBNAB3o"), InlineKeyboardButton("🆘 Help", callback_data="help_btn")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.effective_message.reply_photo(
            photo=open("start_img.png", "rb"), 
            caption=help_text, 
            parse_mode="HTML", 
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"\n❌ Bhai, Photo bhejne mein ye Error aaya: {e}\n")
        await update.effective_message.reply_text(
            text=help_text, 
            parse_mode="HTML", 
            reply_markup=reply_markup, 
            disable_web_page_preview=True
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help_btn":
        user_first_name = query.from_user.first_name
        help_text = get_help_text(user_first_name)
        keyboard = [[InlineKeyboardButton("🔄 Updates", url="https://www.whatsapp.com/channel/0029VbCZGaF4SpkEyXBNAB3o"), InlineKeyboardButton("🆘 Help", callback_data="help_btn")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(help_text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    help_text = get_help_text(user_first_name)
    keyboard = [[InlineKeyboardButton("🔄 Updates", url="https://www.whatsapp.com/channel/0029VbCZGaF4SpkEyXBNAB3o"), InlineKeyboardButton("🆘 Help", callback_data="help_btn")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True)

def get_help_text(user_first_name):
    return (
        f"<b>Hello {user_first_name} 👋,</b>\n\n"
        "<blockquote><b>Welcome to the Multi-Service Link Converter Bot</b> ❞\n"
        "I can convert your links using multiple services:\n"
        "• <a href='https://clickspay.in'>ClicksPay.in</a> - Alternative service\n"
        "• <a href='https://maalink.in'>Maalink.in</a> - Another great option</blockquote>\n\n"
        "🚀 <b>New Features:</b>\n"
        "<blockquote>• Choose between 2 available services ❞\n"
        "• Set separate API keys for each service\n"
        "• Switch active service anytime\n"
        "• Convert links in bulk or single\n"
        "• Accepts text, media, and links\n"
        "• Set custom footer text\n"
        "• Replace words in captions\n"
        "• View detailed settings\n"
        "• Fast and reliable processing</blockquote>\n\n"
        "🔧 <b>Quick Start:</b>\n"
        "<blockquote><b>1. Choose your service:</b> /set_service clickspay <b>or</b> /set_service maalink ❞\n"
        "<b>2. Set your API key with</b> /clickspay_api <b>or</b> /maalink_api\n"
        "<b>3. Send any message with URLs to convert!</b></blockquote>\n\n"
        ".\n"
        "<blockquote><b>• Bot Developed with ❤️ by:</b>\n"
        "<b>@arun_0116</b> ❞</blockquote>\n\n"
        "<b>For More Info type:</b> /help"
    )

# --- Service API Helpers ---
async def shorten_clickspay(api_key, url):
    try:
        api_url = f"https://clickspay.in/api?api={api_key}&url={url}"
        response = await asyncio.to_thread(requests.get, api_url, timeout=10)
        data = response.json()
        if data.get("status") == "success": return data.get("shortenedUrl")
    except Exception as e: print(f"ClicksPay error: {e}")
    return url

async def shorten_maalink(api_key, url):
    try:
        api_url = f"https://maalink.in/api?api={api_key}&url={url}"
        response = await asyncio.to_thread(requests.get, api_url, timeout=10)
        data = response.json()
        if data.get("status") == "success": return data.get("shortenedUrl")
    except Exception as e: print(f"Maalink error: {e}")
    return url

async def shorten_link(user_id, url):
    data = load_data()
    user_data = data.get(user_id, {})
    active_service = user_data.get("active_service", "clickspay")
    api_key = user_data.get("services", {}).get(active_service)
    if not api_key: return url
    if active_service == "clickspay": return await shorten_clickspay(api_key, url)
    elif active_service == "maalink": return await shorten_maalink(api_key, url)
    return url

def apply_replacements(user_id, text):
    data = load_data()
    replacements = data.get(user_id, {}).get("replacements", {})
    if not replacements: return text
    for old_word, new_word in replacements.items():
        pattern = re.compile(re.escape(old_word), re.IGNORECASE)
        text = pattern.sub(new_word, text)
    return text

# --- Commands: Features ---
async def view_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})
    
    active = user_data.get("active_service", "clickspay")
    
    # --- SMART WATERMARK CHECK ---
    default_wm = "Best Link Shortener - Join Maalink.in" if active == "maalink" else "Best Link Shortener - Join ClicksPay.in"
    wm = user_data.get("watermark", f"{default_wm} (Default)")
    
    footer = user_data.get("footer", "Set nahi hai ❌")
    repls = user_data.get("replacements", {})
    repl_text = "\n".join([f"• {old} -> {new}" for old, new in repls.items()]) if repls else "Set nahi hai ❌"
    
    msg = (f"⚙️ **Settings Overview:**\n\n**Active Shortener:** {active}\n**Watermark:** {wm}\n\n**Words to Replace:**\n{repl_text}\n\n**Custom Footer:**\n{footer}")
    await update.message.reply_text(msg, parse_mode="Markdown")

async def replace_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Sahi tarika: `/replace_word <old_word> <new_word>`", parse_mode="Markdown")
        return
    old_word, new_word = context.args[0], context.args[1]
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data: data[user_id] = {}
    if "replacements" not in data[user_id]: data[user_id]["replacements"] = {}
    data[user_id]["replacements"][old_word] = new_word
    save_data(data)
    await update.message.reply_text(f"✅ Word replacement set: '{old_word}' -> '{new_word}'!")

async def myword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    repls = data.get(user_id, {}).get("replacements", {})
    text = "\n".join([f"• {old} -> {new}" for old, new in repls.items()]) if repls else "Set nahi hai ❌"
    await update.message.reply_text(f"📝 **Aapke Replacements:**\n\n{text}", parse_mode="Markdown")

async def remove_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Sahi tarika: `/remove_word <old_word>`", parse_mode="Markdown")
        return
    old_word = context.args[0]
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id in data and "replacements" in data[user_id] and old_word in data[user_id]["replacements"]:
        del data[user_id]["replacements"][old_word]
        save_data(data)
        await update.message.reply_text(f"✅ Word replacement '{old_word}' remove ho gaya hai!")
    else:
        await update.message.reply_text(f"❌ '{old_word}' set nahi hai.")

async def set_footer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message: return
    user_id = str(update.effective_user.id)
    text_to_save = ""
    if message.caption and message.caption.startswith('/footer'): text_to_save = message.caption.replace('/footer', '', 1).strip()
    elif message.text and message.text.startswith('/footer'): text_to_save = message.text.replace('/footer', '', 1).strip()
    if not text_to_save:
        await message.reply_text("❌ Sahi tarika: `/footer aapka custom text yahan`", parse_mode="Markdown")
        return
    data = load_data()
    if user_id not in data: data[user_id] = {}
    data[user_id]["footer"] = text_to_save
    save_data(data)
    await message.reply_text(f"✅ Aapka Footer save ho gaya hai:\n\n{text_to_save}")

async def myfooter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    footer = data.get(user_id, {}).get("footer", "Set nahi hai ❌")
    await update.message.reply_text(f"📝 **Aapka Footer:**\n\n{footer}", parse_mode="Markdown")

async def remove_footer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id in data and "footer" in data[user_id]:
        del data[user_id]["footer"]
        save_data(data)
        await update.message.reply_text("✅ Aapka custom footer remove ho gaya hai!")
    else:
        await update.message.reply_text("❌ Aapne pehle se custom footer set nahi kiya hai.")

async def set_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Sahi tarika: `/set_service clickspay` ya `/set_service maalink`", parse_mode="Markdown")
        return
    service_name = context.args[0].lower()
    if service_name not in ["clickspay", "maalink"]:
        await update.message.reply_text(f"❌ '{service_name}' available nahi hai.", parse_mode="Markdown")
        return
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data: data[user_id] = {}
    data[user_id]["active_service"] = service_name
    save_data(data)
    await update.message.reply_text(f"✅ Aapka Active Service change hokar '{service_name}' ho gaya hai!\nAb bot {service_name} ke links aur watermark use karega.")

async def set_clickspay_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("❌ Sahi tarika: `/clickspay_api YOUR_KEY`", parse_mode="Markdown")
        return
    data = load_data()
    if user_id not in data: data[user_id] = {}
    if "services" not in data[user_id]: data[user_id]["services"] = {}
    data[user_id]["services"]["clickspay"] = context.args[0]
    save_data(data)
    await update.message.reply_text("✅ Aapka ClicksPay API Key successfully save ho gaya hai!\nIse use karne ke liye `/set_service clickspay` bhejain.")

async def maalink_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("❌ Sahi tarika: `/maalink_api YOUR_KEY`", parse_mode="Markdown")
        return
    data = load_data()
    if user_id not in data: data[user_id] = {}
    if "services" not in data[user_id]: data[user_id]["services"] = {}
    data[user_id]["services"]["maalink"] = context.args[0]
    save_data(data)
    await update.message.reply_text("✅ Aapka Maalink API Key successfully save ho gaya hai!\nIse use karne ke liye `/set_service maalink` bhejain.")

async def my_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})
    active = user_data.get("active_service", "clickspay")
    await update.message.reply_text(f"⚙️ **Active Service:** {active}", parse_mode="Markdown")

async def test_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    test_link = "https://google.com"
    processing_msg = await update.message.reply_text("⏳ API Test ho rahi hai...")
    
    short_link = await shorten_link(user_id, test_link)
    
    await context.bot.delete_message(chat_id=update.message.chat_id, message_id=processing_msg.message_id)
    if short_link != test_link:
        await update.message.reply_text(f"✅ **API Test Successful!**\nAapki service ekdum sahi kaam kar rahi hai.\nTest Link: {short_link}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ **API Test Failed!**\nYa toh aapne API key set nahi ki hai, ya fir key galat hai.", parse_mode="Markdown")

async def set_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text_to_save = " ".join(context.args)
    if not text_to_save:
        await update.message.reply_text("❌ Sahi tarika: `/set_watermark aapka custom text yahan`", parse_mode="Markdown")
        return
    data = load_data()
    if user_id not in data: data[user_id] = {}
    data[user_id]["watermark"] = text_to_save
    save_data(data)
    await update.message.reply_text(f"✅ Aapka Custom Watermark save ho gaya hai:\n\n{text_to_save}")

async def mywatermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})
    active = user_data.get("active_service", "clickspay")
    
    # --- SMART WATERMARK CHECK ---
    default_wm = "Best Link Shortener - Join Maalink.in" if active == "maalink" else "Best Link Shortener - Join ClicksPay.in"
    wm = user_data.get("watermark", f"{default_wm} (Default)")
    
    await update.message.reply_text(f"📝 **Aapka Watermark:**\n\n{wm}", parse_mode="Markdown")

async def remove_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id in data and "watermark" in data[user_id]:
        del data[user_id]["watermark"]
        save_data(data)
        await update.message.reply_text("✅ Aapka custom watermark remove ho gaya hai! Ab active service ka original default aayega.")
    else:
        await update.message.reply_text("❌ Aapne pehle se custom watermark set nahi kiya hai.")


# --- Main Engine (Text + Photo Watermark) ---
async def convert_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    is_photo = False
    original_text = ""
    
    if update.message.text: 
        original_text = update.message.text
    elif update.message.caption: 
        original_text = update.message.caption
        if update.message.photo: 
            is_photo = True
    else: return 

    urls = re.findall(r'(https?://[^\s]+)', original_text)
    if not urls: return

    processing_msg = await update.message.reply_text("⏳ Processing...")
    
    processed_text = apply_replacements(user_id, original_text)
    new_text = processed_text

    for url in urls:
        short_link = await shorten_link(user_id, url)
        new_text = new_text.replace(url, short_link)
            
    data = load_data()
    footer = data.get(user_id, {}).get("footer", "")
    if footer: new_text += f"\n\n{footer}"
        
    await context.bot.delete_message(chat_id=update.message.chat_id, message_id=processing_msg.message_id)
    
    if is_photo:
        try:
            photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
            temp_path = f"temp_{user_id}.jpg"
            await photo_file.download_to_drive(temp_path)
            img = Image.open(temp_path)
            w, h = img.size
            
            patti = max(50, int(h * 0.08)) 
            canvas = Image.new("RGB", (w, h + patti), "white")
            canvas.paste(img, (0, 0)) 
            draw = ImageDraw.Draw(canvas) 
            
            # --- YAHAN BHI SMART WATERMARK ADD KIYA ---
            active_service = data.get(user_id, {}).get("active_service", "clickspay")
            default_wm = "Best Link Shortener - Join Maalink.in" if active_service == "maalink" else "Best Link Shortener - Join ClicksPay.in"
            wm_text = data.get(user_id, {}).get("watermark", default_wm)
            
            f_size = int(patti * 0.60) 
            try: font = ImageFont.truetype("arialbd.ttf", f_size)
            except IOError: font = ImageFont.load_default()

            if hasattr(font, 'getbbox'):
                left, top, right, bottom = font.getbbox(wm_text)
                tw, th = right - left, bottom - top
            else:
                tw, th = draw.textsize(wm_text, font=font)
                top, bottom = 0, th

            x, y = (w - tw) // 2, h + (patti - th) // 2
            draw.text((x, y), wm_text, font=font, fill="black")
            
            wm_path = f"wm_{user_id}.jpg"
            canvas.save(wm_path)
            
            await update.message.reply_photo(photo=open(wm_path, 'rb'), caption=new_text)
            os.remove(temp_path)
            os.remove(wm_path)
        except Exception as e:
            await update.message.reply_photo(photo=update.message.photo[-1].file_id, caption=new_text)
            if os.path.exists(f"temp_{user_id}.jpg"): os.remove(f"temp_{user_id}.jpg")
            if os.path.exists(f"wm_{user_id}.jpg"): os.remove(f"wm_{user_id}.jpg")
    else:
        if update.message.video: await update.message.reply_video(video=update.message.video.file_id, caption=new_text)
        elif update.message.document: await update.message.reply_document(document=update.message.document.file_id, caption=new_text)
        else: await update.message.reply_text(new_text)
def main():
    keep_alive()
    application = Application.builder().token(BOT_TOKEN).build()

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("view_settings", view_settings))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.add_handler(CommandHandler("replace_word", replace_word))
    application.add_handler(CommandHandler("myword", myword))
    application.add_handler(CommandHandler("remove_word", remove_word))
    
    application.add_handler(CommandHandler("footer", set_footer))
    application.add_handler(CommandHandler("myfooter", myfooter))
    application.add_handler(CommandHandler("remove_footer", remove_footer))

    application.add_handler(CommandHandler("set_service", set_service))
    application.add_handler(CommandHandler("clickspay_api", set_clickspay_api))
    application.add_handler(CommandHandler("maalink_api", maalink_api))
    application.add_handler(CommandHandler("my_service", my_service))
    application.add_handler(CommandHandler("test_api", test_api))
    
    application.add_handler(CommandHandler("set_watermark", set_watermark))
    application.add_handler(CommandHandler("mywatermark", mywatermark))
    application.add_handler(CommandHandler("remove_watermark", remove_watermark))
    
    application.add_handler(MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND, convert_links))

    print("Bot is running perfectly with Smart Watermarks...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()