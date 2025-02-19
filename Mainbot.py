from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Define states
QUESTION_1, QUESTION_2, HUMAN_SUPPORT = range(3)

# Store the admin/operator Telegram ID
HUMAN_OPERATOR_ID = 6310571020  # Replace with actual operator's chat ID

# Keep track of users in live mode
user_states = {}  # {user_id: True/False}

# Start conversation
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hi! I am your assistant bot. Let's get started.")
    return QUESTION_1

# First question
async def ask_question_1(update: Update, context: CallbackContext):
    await update.message.reply_text("How can I assist you today? Please answer briefly.")
    return QUESTION_2

# Second question
async def ask_question_2(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_answer = update.message.text

    if 'help' in user_answer.lower():  # Trigger human support condition
        await update.message.reply_text("I will notify a human operator to assist you. You can now chat with the operator.")
        # await notify_human(update, context)
        user_states[user_id] = True  # Mark user as in live chat mode
        return HUMAN_SUPPORT  # Switch to live chat mode
    else:
        await update.message.reply_text("Thank you! Here's a predefined answer.")
        return ConversationHandler.END  # End conversation if no human support needed

# Notify human operator
async def notify_human(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    text = update.message.text
    operator_message = f"🔔 New chat started with user {user_id}:\n{text}"
    await context.bot.send_message(chat_id=HUMAN_OPERATOR_ID, text=operator_message)

# Live chat mode - forward user messages to the operator
async def forward_to_operator(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    text = update.message.text
    print(user_id)
    if user_states.get(user_id, False):  # If user is in live mode
        await context.bot.send_message(chat_id=HUMAN_OPERATOR_ID, text=f"User {user_id}: {text}")

# Handle operator replies and send back to the user
async def handle_operator_reply(update: Update, context: CallbackContext):
    """Handles replies from the human operator and forwards them to the correct user."""
    if update.message.reply_to_message:
        try:
            original_text = update.message.reply_to_message.text
            user_id = int(original_text.split(" ")[1].split(":")[0])  # Extract user ID
            await context.bot.send_message(chat_id=user_id, text=f"Operator: {update.message.text}")
        except Exception as e:
            await update.message.reply_text("Error: Could not extract user ID.")

# End conversation
async def end(update: Update, context: CallbackContext):
    await update.message.reply_text("Thank you for your time! Goodbye.")
    return ConversationHandler.END

# Set up the ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question_1)],
        QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question_2)],
        HUMAN_SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_operator)],  # Live chat mode
    },
    fallbacks=[CommandHandler('start', start)],
)

# Setup the Application
TOKEN = "7685322159:AAEmnxuvhEG8rkKD0u-kJknSKYXC9qDvWjY"

app = Application.builder().token(TOKEN).build()

# Add handlers
app.add_handler(conv_handler)
app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, handle_operator_reply))  # Operator replies

# Start the bot
print("Bot is running...")
app.run_polling()
