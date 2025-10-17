from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import my_jokes_and_story
from telegram import Update, ReactionTypeEmoji, BotCommand
import asyncio
import platform
import os
from groq import Groq
import reaction
from collections import defaultdict

# Get tokens from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Conversation history storage - keeps last 10 messages per user
conversation_history = defaultdict(list)
MAX_HISTORY = 10

# Available models
AVAILABLE_MODELS = {
    "llama": "llama-3.3-70b-versatile",  
    "gemma": "gemma2-9b-it",             
}
CURRENT_MODEL = "llama"

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Clear conversation history on start
    conversation_history[user_id] = []
    
    welcome_txt = f"""Hello, CA. {user_name}! 👋

Nice To Meet You, My Dear Friend! 🌫️

I'm Powerful Bot, You Can Use Me As A Auto-filter... I Can Provide You Movies, Web Series And TV Shows That I Have indexed !!

<b>|🔥 Powered By » 「 @OTTProvider 」 "</b>"""
    
    photo_url = "https://graph.org/vTelegraphBot-07-28-35"
    
    message = await update.message.reply_photo(photo=photo_url, caption=welcome_txt)
    
    try:
        await asyncio.sleep(0.5)
        random_rec = reaction.reaction()
        await message.set_reaction(reaction=[ReactionTypeEmoji(emoji=random_rec)])
    except Exception as e:
        print(f"Reaction error: {e}")

# help command
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """📋 AVAILABLE COMMANDS:
/start — Start the bot
/help — Show this help message
/clear — Clear conversation history

💬 HOW TO USE:
Just send me any message and I'll respond with AI!
Ask me about anything — I'm here to help!"""
    message = await update.message.reply_text(help_text)
    try:
        await asyncio.sleep(0.5)
        await message.set_reaction(reaction=[ReactionTypeEmoji(emoji="❤️")])
    except Exception as e:
        print(f"Reaction error: {e}")

# clear history command
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    
    clear_text = "✅ Conversation history cleared! Let's start fresh."
    message = await update.message.reply_text(clear_text)
    try:
        await asyncio.sleep(0.5)
        await message.set_reaction(reaction=[ReactionTypeEmoji(emoji="🗑️")])
    except Exception as e:
        print(f"Reaction error: {e}")

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    print(f"User message: {user_message}")
    
    try:
        answer = None
        reaction_emoji = "👍"
        
        if "joke" in user_message.lower():
            answer = my_jokes_and_story.get_my_jokes()
            reaction_emoji = reaction.reaction()
        elif "story" in user_message.lower():
            answer = my_jokes_and_story.story()
            reaction_emoji = reaction.reaction()
        else:
            try:
                print("Calling Groq AI...")
                
                # Add user message to history
                conversation_history[user_id].append({
                    "role": "user",
                    "content": user_message
                })
                
                # Keep only last MAX_HISTORY messages
                if len(conversation_history[user_id]) > MAX_HISTORY:
                    conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]
                
                # Send entire conversation history to AI
                chat_completion = groq_client.chat.completions.create(
                    messages=conversation_history[user_id],
                    model=AVAILABLE_MODELS[CURRENT_MODEL],
                )
                answer = chat_completion.choices[0].message.content
                
                # Add AI response to history
                conversation_history[user_id].append({
                    "role": "assistant",
                    "content": answer
                })
                
                reaction_emoji = reaction.reaction()
                print(f"AI Response: {answer}")
            except Exception as ai_error:
                print(f"AI Error: {ai_error}")
                answer = "I didn't understand. Try asking something else!"
                reaction_emoji = reaction.reaction()
        
        try:
            await asyncio.sleep(0.3)
            await update.message.set_reaction(reaction=[ReactionTypeEmoji(emoji=reaction_emoji)])
        except Exception as e:
            print(f"Reaction error: {e}")
        
        # Send response
        await update.message.reply_text(answer)
        
    except Exception as e:
        print(f"Error: {e}")

# set menu feature
async def set_manu(app):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help information"),
        BotCommand("clear", "Clear conversation history"),
    ]
    await app.bot.set_my_commands(commands)

if __name__ == "__main__":
    print("bot start.....")
    
    # Validate required environment variables
   
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))

    print("Bot is running...")
    app.run_polling()

