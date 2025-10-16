from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import my_jokes_and_story
from telegram import Update, ReactionTypeEmoji, BotCommand
import asyncio
import platform
import nest_asyncio
from groq import Groq
import reaction

BOT_TOKEN = ""
GROQ_API_KEY = ""

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

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
    user_name = update.effective_user.first_name
    welcome_txt = f"""👋 Welcome, {user_name}!

I'm your AI assistant powered by cutting-edge language models. I can help you with:

🤖 **AI Conversations** - Ask me anything and get intelligent responses
😂 **Jokes** - Brighten your day with random humor
📖 **Stories** - Enjoy creative tales

                 **Quick Start:**

• Just type any message and I'll respond with AI
• Use /help for all available commands

Let's get started! What would you like to talk about?"""
    
    photo_url = "https://graph.org/vTelegraphBot-07-28-35"
    
    message = await update.message.reply_photo(photo=photo_url, caption=welcome_txt)
    
    try:
        await asyncio.sleep(0.5)
        random_rec=reaction.reaction()
        await message.set_reaction(reaction=[ReactionTypeEmoji(emoji=random_rec)])
    except Exception as e:
        print(f"Reaction error: {e}")

# help command
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """📋 **Available Commands:**

/start - Start the bot
/help - Show this help message

💬 **How to Use:**
Just send me any message and I'll respond with AI!

Ask me about anything - I'm here to help!"""
    message = await update.message.reply_text(help_text)
    try:
        await asyncio.sleep(0.5)
        await message.set_reaction(reaction=[ReactionTypeEmoji(emoji="❤️")])
    except Exception as e:
        print(f"Reaction error: {e}")

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    print(f"User message: {user_message}")
    
    try:
        answer = None
        reaction_emoji = "👍"
        # you can even import pyjoke
        if "joke" in user_message.lower():
            answer = my_jokes_and_story.get_my_jokes()
            reaction_emoji = reaction.reaction()
        # for short story
        elif "story" in user_message.lower():
            answer = my_jokes_and_story.story()
            reaction_emoji =reaction.reaction()
        else:
            # this for ai 
            try:
                print("Calling Groq AI...")
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    ],
                    model=AVAILABLE_MODELS[CURRENT_MODEL],
                )
                answer = chat_completion.choices[0].message.content
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
# for ser manu feature in the chat_bot
async def set_manu(app):
    commands = [
        BotCommand("start", "start the bot"),
        BotCommand("help", "Show help information"),
    ]
    await app.bot.set_my_commands(commands)

if __name__ == "__main__":
    # main funtion
    print("bot start.....")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))

    # set menu asynchronously
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(set_manu(app))

    print("Bot is running...")
    app.run_polling()