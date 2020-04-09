import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "./vendored"))

from telegram.ext import Dispatcher, Updater, CommandHandler, MessageHandler, Filters
from telegram import Update, Bot, ParseMode

from btjx import addNameInDB, watchPartieInDB, unwatchPartieInDB, getParties, getPartieState


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        "Hey there!\nI'm btjxBot. I will help you follow your games and turns on the board game site boiteajeux :)\nSend /help to get a overview of what I can do for you...")


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        'You need help...\n'
        'No problem - You can send the following commands:\n'
        '/addName - Add a player name for which to watch out for turns.\n'
        '/removeName - Remove a player name for which no longer to watch out for turns.\n'
        '/parties - List all parties and whose turn it is.\n'
        '/watchPartie - Add a partie which should be watched by the bot. Enter the id which is inside the URL of the game (e.g. 3640806).\n'
        '/unwatchPartie - Remove a partie from the watch list.\n'
        '\n'
        'You can always find more infos at https://github.com/Boman/BtjxBot\nAdieu!')


def addName(update, context):
    """Set the player name for which to watch out for turns."""
    chatID = update.message.chat_id
    userID = update.message.from_user.id
    try:
        name = context.args[0]
        update.message.reply_text(addNameInDB.addNameInDB(name, chatID, userID))
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /addName <player name>')


def removeName(update, context):
    """Remove a player name for which no longer to watch out for turns."""
    chatID = update.message.chat_id
    userID = update.message.from_user.id
    try:
        name = context.args[0]
        update.message.reply_text(addNameInDB.removeNameInDB(name, chatID, userID))
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /removeName <player name>')


def parties(update, context):
    """List all parties and whose turn it is."""
    chatID = update.message.chat_id
    userID = update.message.from_user.id
    try:
        update.message.reply_text(getParties.getParties(chatID, userID), parse_mode=ParseMode.HTML,
                                  disable_web_page_preview=True)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /parties')


def watchPartie(update, context):
    """Add a partie which should be watched by the bot. Enter the id which is inside the URL of the game."""
    chatID = update.message.chat_id
    userID = update.message.from_user.id
    try:
        partieID = context.args[0]
        update.message.reply_text(watchPartieInDB.watchPartieInDB(partieID, chatID, userID))
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /watchPartie <partieID>')


def unwatchPartie(update, context):
    """Remove a partie from the watch list."""
    chatID = update.message.chat_id
    userID = update.message.from_user.id
    try:
        partieID = context.args[0]
        update.message.reply_text(unwatchPartieInDB.unwatchPartieInDB(partieID, chatID, userID))
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /unwatchPartie <partieID>')


TOKEN = os.environ['TELEGRAM_TOKEN']
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

# Get the dispatcher to register handlers
dp = dispatcher

# on different commands - answer in Telegram
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help))
dp.add_handler(CommandHandler("addName", addName,
                              pass_args=True,
                              pass_job_queue=True,
                              pass_chat_data=True))
dp.add_handler(CommandHandler("removeName", removeName,
                              pass_args=True,
                              pass_job_queue=True,
                              pass_chat_data=True))
dp.add_handler(CommandHandler("parties", parties,
                              pass_args=True,
                              pass_job_queue=True,
                              pass_chat_data=True))
dp.add_handler(CommandHandler("watchPartie", watchPartie,
                              pass_args=True,
                              pass_job_queue=True,
                              pass_chat_data=True))
dp.add_handler(CommandHandler("unwatchPartie", unwatchPartie,
                              pass_args=True,
                              pass_job_queue=True,
                              pass_chat_data=True))


def btjxbot_handler(event, context):
    try:
        dispatcher.process_update(
            Update.de_json(json.loads(event["body"]), bot)
        )

    except Exception as e:
        print(e)
        return {"statusCode": 500}

    return {"statusCode": 200}


def cron_handler(event, context):
    try:
        getPartieState.checkTurns()

    except Exception as e:
        print(e)
        return {"statusCode": 500}

    return {"statusCode": 200}
