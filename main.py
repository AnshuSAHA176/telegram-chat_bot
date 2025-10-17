from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import my_jokes_and_story
from telegram import Update, ReactionTypeEmoji, BotCommand
import asyncio
import platform
import nest_asyncio
from groq import Groq
import reaction
from collections import defaultdict


BOT_TOKEN = "BOT_TOKEN"
GROQ_API_KEY = "GROQ_AP"


# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)
conversation_history = defaultdict(list)
MAX_HISTORY = 100


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
    conversation_history[user_id] = []
    welcome_txt = f"""HELLO 👋, {user_name}!


I'm your AI assistant powered by cutting-edge language models. I can help you with:


🤖 AI Conversations — Ask me anything and get intelligent responses
😂 Jokes — Brighten your day with random humor
📖 Stories — Enjoy creative tales


⚡ Quick Start:
• Just type any message and I'll respond with AI
• Use /help for all available commands


Let's get started! What would you like to talk about?"""


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
        await message.set_reaction(reaction=[ReactionTypeEmoji(emoji="❤")])
    except Exception as e:
        print(f"Reaction error: {e}")


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    clear_text = "✅ Conversation history cleared! Let's start fresh."
    message = await update.message.reply_text(clear_text)
    try:
        await asyncio.sleep(0.3)
        await message.set_reaction(reaction=[ReactionTypeEmoji(emoji="✅")])
    except Exception as e:
        print(f"Reaction error: {e}")


async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    print(f"User message: {user_message}")


    # Send thinking sticker before processing
    thinking_sticker = None
    try:
        # Replace this with your sticker file_id after getting it
        thinking_sticker = await context.bot.send_sticker(
            chat_id=update.effective_chat.id,
            sticker="CAACAgQAAxkBAAEK99dlfC7LDqnuwtGRkIoacot_dGC4zQACbg8AAuHqsVDaMQeY6CcRojME"
        )
    except Exception as e:
        print(f"Sticker send error: {e}")


    try:
        answer = None
        reaction_emoji = "👍"
        
        # Check for jokes
        if "joke" in user_message.lower():
            answer = my_jokes_and_story.get_my_jokes()
            reaction_emoji = reaction.reaction()
        # Check for story
        elif "story" in user_message.lower():
            answer = my_jokes_and_story.story()
            reaction_emoji = reaction.reaction()
        else:
            # AI response
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
            except Exception as ai_error:
                print(f"AI Error: {ai_error}")
                answer = "I didn't understand. Try asking something else!"
                reaction_emoji = reaction.reaction()


        # Delete the thinking sticker before sending response
        if thinking_sticker:
            try:
                await thinking_sticker.delete()
            except Exception as e:
                print(f"Sticker delete error: {e}")


        # Add reaction to user's message
        try:
            await asyncio.sleep(0.3)
            await update.message.set_reaction(reaction=[ReactionTypeEmoji(emoji=reaction.reaction())])
        except Exception as e:
            print(f"Reaction error: {e}")


        # Send response
        await update.message.reply_text(answer)


    except Exception as e:
        print(f"Error: {e}")
        # Clean up sticker if error occurs
        if thinking_sticker:
            try:
                await thinking_sticker.delete()
            except:
                pass


# Set menu feature in the chat_bot
async def set_manu(app):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help information"),
        BotCommand("clear", "Clear conversation history"),
    ]
    await app.bot.set_my_commands(commands)


if __name__ == "__main__":
    # main function
    print("Bot starting.....")
    app = Application.builder().token(BOT_TOKEN).build()


    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))
    
    # Removed get_sticker_id handler as requested


    # Set menu asynchronously
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(set_manu(app))


    print("Bot is running...")
    app.run_polling()

