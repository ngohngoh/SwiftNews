import logging
import time
import random

from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
from datascraper import *

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, SECOND_CHOICE = range(2)

data_folder_name = "SGNews"
data_folder = os.path.join(os.getcwd(), data_folder_name)

print(data_transform(data_folder))

new_data = pd.read_pickle("database/" + data_folder_name + ".pkl")

keywords_count = {}

for index, row in new_data.iterrows():
    keywords = row["keywords"]
    for word in keywords:
        if word in keywords_count:
            keywords_count[word] += 1
        else:
            keywords_count[word] = 1

keywords_appearance = sorted(keywords_count.items(), key=lambda x:x[1], reverse = True)

print(keywords_appearance[:5])


reply_keyboard = [[keywords_appearance[0][0]],
                  [keywords_appearance[1][0]]]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)



def start(update, context):
    update.message.reply_text(
        "Hi! My name is SwiftNews_bot. Please select a topic/keyword for a news you want to read about.",
        reply_markup=markup)

    return CHOOSING

from gensim.summarization.summarizer import summarize
from telegram import ChatAction

def regular_choice(update, context):

    text = update.message.text.lower()
    update.message.reply_text("Getting your recent new(s) on: {} ...".format(text))

    context.bot.sendChatAction(chat_id=update.message.chat_id, action = ChatAction.TYPING)

    user_news = []
    for index, row in new_data.iterrows():
        keywords = row["keywords"]
        if text in keywords:
            user_news.append(index)

    random.shuffle(user_news)

    time.sleep(5)

    if len(user_news) > 50:
        update.message.reply_text("The topic you chose has too many recent news")
        update.message.reply_text("Please specify a second topic/keyword")
        context.user_data['first'] = (text, user_news)
        return SECOND_CHOICE
    elif len(user_news) > 0: 
        update.message.reply_text('Article returned:')
        for news in user_news[:2]:
            result = new_data.iloc[news]["description"]
            update.message.reply_text(summarize(result, word_count=100))
        update.message.reply_text('Feel free to pick another topic to read up')
    else: 
        update.message.reply_text("Your topic cannot be found in our recent news")
        update.message.reply_text('Please pick another topic to read up or choose the few we provided :)')

    return CHOOSING


def second_choice(update, context):
    text = update.message.text.lower()
    first_text, first = context.user_data['first']
    second = []

    update.message.reply_text("Getting your recent new(s) on: {} and {} ...".format(first_text, text))

    context.bot.sendChatAction(chat_id=update.message.chat_id, action = ChatAction.TYPING)

    for row in first:
        keywords = new_data.iloc[row]["keywords"]
        if text in keywords:
            second.append(row)

    random.shuffle(second)

    time.sleep(5)

    if len(second) > 0: 
        update.message.reply_text('Article returned based on your 2 keywords:')
        for news in second[:2]:
            result = new_data.iloc[news]["description"]
            update.message.reply_text(summarize(result, word_count=100))
        update.message.reply_text('Feel free to pick another topic to read up')
    else: 
        update.message.reply_text("Your topic cannot be found in our recent news")
        update.message.reply_text('Please pick another topic to read up or choose the few we provided :)')
        return SECOND_CHOICE
    

    return CHOOSING


def done(update, context):
    update.message.reply_text("Until next time {} ! ".format(update.message.chat.username))

    return ConversationHandler.END

########## FORCE USER TO START ##########
# def force_start(update, context):
#     context.bot.send_message(chat_id=update.message.chat_id, text="Please type in /start to begin using the bot!")

# from telegram.ext import MessageHandler, Filters
# forcestart_handler = MessageHandler(Filters.text, force_start)



def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

########## UNKNOWN COMMAND ##########
def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")

unknown_handler = MessageHandler(Filters.command, unknown)



def main():

    from telebot.credentials import bot_token, bot_user, URL
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            # CHOOSING: [MessageHandler(Filters.regex('^(Recommended Topic 1|Recommended Topic 2)$'),
            #                           regular_choice),
            #            MessageHandler(Filters.regex('^Custom Topic'),
            #                           custom_choice)
            #            ],
            CHOOSING: [MessageHandler(Filters.language("en"),
                                        regular_choice)
                        ],

            SECOND_CHOICE: [MessageHandler(Filters.language("en"),
                                           second_choice)
                            ],

            # TYPING_REPLY: [MessageHandler(Filters.text,
            #                               received_information),
            #                ],
        },

        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    dp.add_handler(unknown_handler)

    # dp.add_handler(forcestart_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
