import os
import logging
import json
import asyncio
import datetime
import random

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

logging.getLogger("httpx").setLevel(logging.WARNING)

#GETTING BOT_TOKEN
load_dotenv()
bot_token = os.getenv('BOT_TOKEN')

#MEMORY ACCESS FUNCTIONS
def create_user_data_folder():
    with open('bot_data/Bot_user_data.json', 'w') as file:
        data = {}
        json.dump(data, file, indent=4, ensure_ascii=False)

def create_anc_data_folder():
    with open('bot_data/Bot_anc_data.json', 'w') as file:
        data = {"Maxim": {},
                "AnecdotovoStreet": {}
                }
        json.dump(data, file, indent=4, ensure_ascii=False)

def open_anc():
    with open("anecdotes.json", encoding='utf-8') as file:
        anecdotes = json.load(file)

    return anecdotes

def open_data():
    with open('bot_data/Bot_user_data.json') as file:
        user_data = json.load(file)

    return user_data

def open_score():
    with open('bot_data/Bot_anc_data.json') as file:
        anc_data = json.load(file)

    return anc_data

def save_user_data(user_data):
    with open('bot_data/Bot_user_data.json', 'w') as file:
        json.dump(user_data, file, indent=4, ensure_ascii=False)

def save_anc_score(anc_data):
    with open('bot_data/Bot_anc_data.json', 'w') as file:
        json.dump(anc_data, file, indent=4, ensure_ascii=False)


#CHANGE DATA SCORE
async def increase_like_score(update: Update, context: ContextTypes.DEFAULT_TYPE):

    #INSTALL ALL DATA
    user_data = open_data()
    anc_data = open_score()
    user_id = str(update.effective_user.id)
    chapter = user_data[user_id][3][0]
    anc_id = str(user_data[user_id][3][1])

    # Create Inline Buttons
    buttons = [
        [InlineKeyboardButton('Ещё', callback_data='send_anecdote'),
         InlineKeyboardButton('Назад >', callback_data='backflip')]
    ]
    markup = InlineKeyboardMarkup(buttons)

    #INCREASE LIKE SCORE AND SET THE BOOL
    if not(user_data[user_id][2][chapter][anc_id]):
        anc_data[chapter][anc_id] += 1
        user_data[user_id][2][chapter][anc_id] = True

        logging.warning(f'{user_id} поставил лайк')

    #REPLY BOT'S RESPOND
    await context.bot.editMessageText(text='Вы оценили анекдот!', message_id=user_data[user_id][0],
                                      chat_id=user_data[user_id][1],
                                      reply_markup=markup)

    #SAVE THE DATA
    save_anc_score(anc_data)
    save_user_data(user_data)


#BOT FUNCTION
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    with open('info', encoding='utf-8') as file:
        info_txt = file.read()

    user_data = open_data()
    user_id = str(update.effective_user.id)

    # IF THE USER USES AN OLD MESSAGE, IT WILL BE DELETED
    if not update.effective_message.id == user_data[user_id][0]:
        await context.bot.deleteMessage(chat_id=user_data[user_id][1], message_id=update.effective_message.id)

    button = [[InlineKeyboardButton('Назад >', callback_data='backflip')]]
    markup = InlineKeyboardMarkup(button)

    #SEND_INFO
    await context.bot.editMessageText(message_id=user_data[user_id][0],
                                      chat_id=user_data[user_id][1],
                                      text=info_txt,
                                      reply_markup=markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    #Getting all the necessary information
    user_data = open_data()
    user_id = str(update.effective_user.id)

    #Create Inline Buttons
    buttons = [[InlineKeyboardButton('Анекдот', callback_data='send_anecdote')],
               [InlineKeyboardButton('/info', callback_data='info')]]
    markup = InlineKeyboardMarkup(buttons)


    #REPLY MESSAGE
    if update.callback_query:
        #IF THE USER USES AN OLD MESSAGE, IT WILL BE DELETED
        if update.effective_message.id == user_data[user_id][0]:
            await context.bot.editMessageText(text='Смех и Грех - это бот, который... Ай ладно, жми уже 😍',
                                              message_id=user_data[user_id][0],
                                              chat_id=user_data[user_id][1], reply_markup=markup)
        else:
            await context.bot.deleteMessage(chat_id=user_data[user_id][1], message_id=update.effective_message.id)

    else:
        if user_id in user_data:
            try:
                await context.bot.deleteMessage(message_id=user_data[user_id][0],
                                          chat_id=user_data[user_id][1])
            except Exception:
                logging.warning(f'Упс, что-то пошло не так')
        else:
            # CREATE USER PROFILE
            user_data[user_id] = [None, None, {'Maxim': {}, "AnecdotovoStreet": {}}, ['-1', -1]]

            logging.info('User has registered')

        send_message = await update.message.reply_text('Смех и Грех - это бот, который... Ай ладно, жми уже 😍',
                                                       reply_markup=markup)

        # SAVE LAST MESSAGE_INFO IN USER PROFILE
        user_data[user_id][0] = send_message.message_id
        user_data[user_id][1] = send_message.chat_id

    #SAVE THE DATA
    save_user_data(user_data)

async def anecdotes_sender(update: Update, context: ContextTypes.DEFAULT_TYPE):

    #Getting all the necessary information
    user_data = open_data()
    anc_data = open_score()
    user_id = str(update.effective_user.id)

    # IF THE USER USES AN OLD MESSAGE, IT WILL BE DELETED
    if not update.effective_message.id == user_data[user_id][0]:
        await context.bot.deleteMessage(chat_id=user_data[user_id][1], message_id=update.effective_message.id)

    # ALERT
    print(datetime.datetime.today(), update.effective_user.first_name, user_id)


    # IT'S BETTER TO MAKE SURE THAT USER HAS A PROFILE :)
    if not user_id in user_data:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Бот не успел собраться с мыслями 🥴\nПросто введите /start')
        return

    chapters = ['Maxim', 'AnecdotovoStreet']

    #OPEN ANECDOTES
    anecdotes = open_anc()

    #GENERATING ANC AND PUTING THIS INFO INTO USER_DATA
    chapter_id = random.randint(0, 1)
    anc_id = random.randint(0, len(anecdotes[chapters[chapter_id]])- 1)

    user_data[user_id][3][0] = chapters[chapter_id]
    user_data[user_id][3][1] = anc_id

    #DID THE USER LIKE THIS ANC
    if str(anc_id) in user_data[user_id][2][chapters[chapter_id]]:
        pass
    else:
        user_data[user_id][2][chapters[chapter_id]][str(anc_id)] = False

    #SETUP NEW ANC_DATA IN DICT
    if not(str(anc_id) in anc_data[chapters[chapter_id]]):
        anc_data[chapters[chapter_id]][str(anc_id)] = 0

    #managing the request
    query = update.callback_query
    await query.answer()

    #YES/NO + #Create Inline Buttons
    if user_data[user_id][2][chapters[chapter_id]][str(anc_id)]:
        like_checker = 'Да'
        buttons = [
            [InlineKeyboardButton('Ещё', callback_data='send_anecdote'),
             InlineKeyboardButton('Назад >', callback_data='backflip')]
        ]
    else:
        buttons = [
            [InlineKeyboardButton('👍🏻', callback_data='like')],
            [InlineKeyboardButton('Ещё', callback_data='send_anecdote'),
             InlineKeyboardButton('Назад >', callback_data='backflip')]
        ]
        like_checker = 'Нет'

    markup = InlineKeyboardMarkup(buttons)

    await context.bot.editMessageText(message_id=user_data[user_id][0],
                                      chat_id=user_data[user_id][1],
                                      text=anecdotes[chapters[chapter_id]][anc_id]
                                           + f'\n\nЛюдей оценили: {anc_data[chapters[chapter_id]][str(anc_id)]}'
                                      , reply_markup=markup)

    #SAVE THE DATA
    save_anc_score(anc_data)
    save_user_data(user_data)


def setup():

    try:
        open_data()
    except FileNotFoundError:
        create_user_data_folder()

    try:
        open_score()
    except FileNotFoundError:
        create_anc_data_folder()

def main():

    application = Application.builder().token(bot_token).build()

    #CREATE ALL HANDLERS
    handler_start_query = CommandHandler('start', start)
    handler_anecdotes_inline_query = CallbackQueryHandler(anecdotes_sender, pattern='send_anecdote')
    handler_start_inline_query = CallbackQueryHandler(start, pattern='backflip')
    handler_like_inline_query = CallbackQueryHandler(increase_like_score, pattern='like')
    handler_info_inline_query = CallbackQueryHandler(info, pattern='info')

    #ADD ALL HANDLERS
    application.add_handler(handler_start_query)
    application.add_handler(handler_start_inline_query)
    application.add_handler(handler_info_inline_query)
    application.add_handler(handler_anecdotes_inline_query)
    application.add_handler(handler_like_inline_query)

    application.run_polling()


if __name__ == '__main__':
    setup()
    main()
