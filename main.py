import telebot
import funClasses
import sqlalchemy as sq
import tg_bot_funcs

from sqlalchemy.orm import declarative_base, sessionmaker
from telebot import types
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from funClasses import add_row_to_table, InitialValues
from tg_bot_funcs import *


TG_TOKEN = ''
FREE_DICT_API_HOST = 'https://api.dictionaryapi.dev/api/v2/entries/en'

DBMS_name = 'postgresql'
username = 'postgres'
password = 'postgres'
db_name = 'en_words_db'


def start_program(bot, session):
    
    @bot.message_handler(commands=['start'])
    def start_bot(message):
        reply_on_start(bot, message, session)
        
    @bot.message_handler(commands=['help'])
    def send_help_bot(message):
        send_help(bot, message)
    
    @bot.message_handler(commands=['getwords'])
    def get_nesw_words_bot(message):
        get_new_words(bot, message, session)

    @bot.message_handler(commands=['enru'])
    def generate_enru_question_bot(message):
        generate_enru_question(bot, message, session)
        
    @bot.message_handler(commands=['ruen'])
    def generate_ruen_question_bot(message):
        generate_ruen_question(bot, message, session)
        
    @bot.message_handler(commands=['mywords'])
    def show_my_words_bot(message):
        show_my_words(bot, message, session)
    
    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def user_choice_reply_bot(message):
        user_choice_reply(bot, message, session)
  
    print('Bot is running')
    
    return bot.polling(none_stop=True)

if __name__ == '__main__':
    state_storage = StateMemoryStorage()
    bot = telebot.TeleBot(TG_TOKEN)

    Base = declarative_base() 

    # create_db(username, password, db_name)
    DSN = "postgresql://postgres:postgres@localhost:5432/en_words_db"
    engine = sq.create_engine(DSN)
    # create_tables(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
        
    # for word in InitialValues.basic_words_list:
    #     add_row_to_table(session, 'BasicWords', word)
    
    start_program(bot, session)