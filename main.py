import os
import logging
from collections import defaultdict
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from groq import Groq
import my_jokes_and_story

# --- Logging setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- Environment variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or GROQ_API_KEY environment variable.")

# --- Initialize Groq client ---
groq_client = Groq(api_key=GROQ_API_KEY)

# --- Conversation history ---
conversation_history = defaultdict(list)
MAX_HISTORY = 10

# --- Available models ---
AVAILABLE_MODELS = {
    "llama": "llama-3.3-70b-versatile",
    "gemma": "gemma2-9b-it"
}
CURRENT_MODEL = "llama"

# --- Bot commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    conversation_history[update.effective_user.id] = []
    
    welcome_txt = f"""Hello, {user_name}! 👋

Nice To Meet You! 🌫️
I'm a powerful bot that can tell jokes, stories, or answer your questions using AI.

Type anything and I will respond!"""
    
    await update.message.reply_text(welcome_txt)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """📋 AVAILABLE COMMANDS:
/start — Start the bot
/help — Show this help message
/clear — Clear conversation history

💬 HOW TO USE:
Just send me any message and I'll respond with AI or tell jokes/stories."""
    await update.message.reply_text(help_text)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("✅ Conversation history cleared!")

# --- AI + joke/story response ---
async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text.strip()
    
    try:
        # Handle jokes
        if "joke" in user_text.lower():
            reply = my_jokes_and_story.get_my_jokes()
        # Handle stories
        elif "story" in user_text.lower():
            reply = my_jokes_and_story.story()
        else:
            # Add user message to history
            conversation_history[user_id].append({"role": "user", "content": user_text})
            if len(conversation_history[user_id]) > MAX_HISTORY:
                conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]
            
            # Call Groq AI
            model_name = AVAILABLE_MODELS.get(CURRENT_MODEL)
            if not model_name:
                reply = "⚠️ Model not available."
            else:
                chat_completion = groq_client.chat.completions.create(
                    messages=conversation_history[user_id],
                    model=model_name
                )
                reply = chat_completion.choices[0].message.content.strip()
                # Add AI response to history
                conversation_history[user_id].append({"role": "assistant", "content": reply})
        
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await update.message.reply_text("⚠️ Sorry, I couldn't process that. Try again.")

# --- Set menu commands ---
async def set_menu(app):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help info"),
        BotCommand("clear", "Clear conversation history")
    ]
    await app.bot.set_my_commands(commands)

# --- Main entry ---
if __name__ == "__main__":
    print("Bot starting...")
    
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))
    
    # Set menu commands
    import asyncio
    asyncio.run(set_menu(app))

    print("Bot is running...")
    app.run_polling()
