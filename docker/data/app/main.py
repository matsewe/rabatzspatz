"""
Based on basic Echobot example

Add command descriptions
https://stackoverflow.com/questions/34457568/how-to-show-options-in-telegram-bot
"""

import logging
import pymysql
import random
import string
import atexit

import telegram
import telegram.ext
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

import mysecrets

# Enable logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def logged_execute(self, data):
    logger.info(data)
    self.execute(data)


pymysql.cursors.Cursor.logged_execute = logged_execute

db = pymysql.connect("db", "rabatzspatz", "spatznrabatz", "rabatzspatz", autocommit=True)
cursor = db.cursor()


def cleanup_stuff():
    db.close()


atexit.register(cleanup_stuff)

button_callbacks = {}


def button_callback(data, fun_handle):
    token = ''.join(random.choices(string.ascii_lowercase, k=16))
    button_callbacks[token] = (fun_handle, data)
    return token


def add_person(update, context, team):
    user_data = update.callback_query.message.chat  # Attention! The update's contents change depending on where we are ... Rather use context ...
    logger.info(f'''Add Person {user_data} to team {team}''')
    logger.info(f'''{context.user_data}''')
    logger.info(f'''{context.chat_data}''')

    first_name = user_data.first_name
    last_name = user_data.last_name
    user_name = user_data.username
    chat_id = user_data.id
    cursor.logged_execute(f'''INSERT INTO Persons (FirstName, LastName, UserName, ChatID, Team, Confirmed, Admin)
        VALUES ("{first_name}", "{last_name}", "{user_name}", {chat_id}, {team}, 0, 0)''')
    db.commit()

    cursor.logged_execute(f'''SELECT Name FROM Teams WHERE ID={team}''')

    team_name = cursor.fetchone()[0]

    update.callback_query.edit_message_text(text=f'''Hey {first_name}. You are now part of team {team_name}. This will be confirmed by an administrator soon.''')


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    user_data = update.message.from_user
    logger.info(f'''Start conversation with {user_data}''')

    cursor.logged_execute(f'''SELECT * FROM Persons WHERE ChatID={user_data.id}''')

    if cursor.rowcount >= 1:
        logger.info(f'''Already signed up: {user_data}''')
        update.message.reply_text(
            'You already signed up. Please contact and administrator, if you have any questions.')
    else:
        cursor.logged_execute(f'''SELECT * FROM Teams''')

        teams = cursor.fetchall()
        logger.info(teams)
        buttons = [[telegram.InlineKeyboardButton(team[1], callback_data=button_callback(team[0], add_person))] for team
                   in
                   teams]  # The [] are needed for layout ...
        logger.info(button_callbacks)

        context.bot.send_message(chat_id=user_data.id,
                                 text="would you like to sign up as person in charge of scoring and spirit for your team at SpatznRabatz? Just press the button assigned to your team. Note: this action needs to be confirmed by an administrator.",
                                 reply_markup=telegram.InlineKeyboardMarkup(buttons))


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def setMood(update, context, mood):
    update.callback_query.edit_message_text(text="Your mood is {}".format(mood))



def callback_notifications(context: telegram.ext.CallbackContext):
    logger.info('Send notifications')
    cursor.logged_execute("SELECT * FROM Persons")

    persons = cursor.fetchall()
    for person in persons:
        logger.info(person)
        buttons = [
            telegram.InlineKeyboardButton("good", callback_data=button_callback(1, setMood)),
            telegram.InlineKeyboardButton("um ...", callback_data=button_callback(0, setMood)),
            telegram.InlineKeyboardButton("bad", callback_data=button_callback(-1, setMood))
        ]
        # three-column-layout [[button1, button2, button3]]
        #context.bot.send_message(chat_id=person[4],
        #                         text="Hey {}, How is your mood today?".format(person[1]),
        #                         reply_markup=telegram.InlineKeyboardMarkup([buttons]))


def button(update, context):
    query = update.callback_query
    cb = button_callbacks[query.data]
    logger.info(f'''Button {query.data}, executing {cb}''')
    cb[0](update, context, cb[1])



def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    updater = Updater(mysecrets.telegramToken(), use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Get the job queue to check for upcoming games, finished games, ...
    jq = updater.job_queue

    job_notifications = jq.run_repeating(callback_notifications, interval=60, first=0)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help, Filters.chat(-1234)))
    dp.add_handler(CallbackQueryHandler(button))

    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
