import telebot
import random
import funClasses
import sqlalchemy as sq
import json
import db_classes

from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from telebot import types
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from db_classes import Users, BasicWords, StudiedWords, WordsInStudy
from funClasses import get_word_to_learn, add_row_to_table, show_words_in_study, reg_user, remove_row_from_table, has_cyrillic, has_latin, get_new_word_pair, del_word, get_use_example, Command, InitialValues

TG_TOKEN = ''
FREE_DICT_API_HOST = 'https://api.dictionaryapi.dev/api/v2/entries/en'

if __name__ == '__main__':
    state_storage = StateMemoryStorage()
    bot = telebot.TeleBot(TG_TOKEN)

    Base = declarative_base()

    DBMS_name = 'postgresql'
    username = 'postgres'
    password = 'postgres'
    db_name = 'en_words_db'

    # create_db(username, password, db_name)

    DSN = "postgresql://postgres:postgres@localhost:5432/en_words_db"
    engine = sq.create_engine(DSN)
    # create_tables(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    class MyStates(StatesGroup):
        enru_target_word = State()
        enru_translated_word = State()
        enru_other_words = State()
        ruen_target_word = State()
        ruen_translated_word = State()
        ruen_other_words = State()     

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        InitialValues.current_user_id = reg_user(session, message.from_user.username)
        for row in session.query(BasicWords).all():
            add_row_to_table(session, 'WordsInStudy', {'en_word': row.en_word, 'ru_word': row.ru_word, 'correct_guesses': 0, 'user_id': InitialValues.current_user_id})
        reply = ''
        button_repl = ''
        for command, description in InitialValues.command_dict.items():
            reply += f'{command} - {description}\n'
        bot.send_message(message.chat.id, f'Тебя приветствует бот для изучения английского языка. Давай расскажу, какие команды я знаю:\n{reply}')
        for button, description in InitialValues.buttons.items():
            button_repl += f'{button} - {description}\n'
        bot.send_message(message.chat.id, f'Когда выберешь /enru или /ruen увидишь четыре варианта перевода загаданного слова и ещё {len(InitialValues.buttons)} кнопки:\n{button_repl}')
        
    @bot.message_handler(commands=['help'])
    def send_help(message):
        for command, description in InitialValues.command_dict.items():
            bot.send_message(message.chat.id, f'{command} - {description}')

    @bot.message_handler(commands=['enru'])
    def generate_enru_question(message):
        markup = types.ReplyKeyboardMarkup(row_width=2)
        question_list = get_word_to_learn(session)
        target_dict = question_list.pop(0)
        target_word = list(target_dict.keys())[0]
        translated_target_word = target_dict[target_word]
        target_word_button = types.KeyboardButton(translated_target_word)    
        other_words = []
        for w_pair in question_list:
            other_words.append(list(w_pair.values())[0])
        other_words_buttons = [types.KeyboardButton(word) for word in other_words]
        buttons = [target_word_button] + other_words_buttons
        random.shuffle(buttons)
        next_button = types.KeyboardButton(Command.USE_EXAMPLE)
        delete_button = types.KeyboardButton(Command.DELETE_WORD)
        add_button = types.KeyboardButton(Command.ADD_WORD)
        buttons.extend([next_button, delete_button, add_button])
        
        markup.add(*buttons)
        
        enru_question = f'Выбери перевод слова: {target_word}'
        bot.send_message(message.chat.id, enru_question, reply_markup=markup)
        
        bot.set_state(message.from_user.id, MyStates.enru_target_word, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['enru_target_word'] = target_word
            data['enru_translated_word'] = translated_target_word
            data['enru_other_words'] = other_words
            data['ruen_target_word'] = ''
            data['ruen_translated_word'] = ''
            data['ruen_other_words'] = ''
            
    @bot.message_handler(commands=['ruen'])
    def generate_ruen_question(message):
        markup = types.ReplyKeyboardMarkup(row_width=2)
        question_list = get_word_to_learn(session)
        target_dict = question_list.pop(0)
        for en_w, ru_w in target_dict.items():
            target_word = ru_w
            translated_target_word = en_w
        target_word_button = types.KeyboardButton(translated_target_word)    
        other_words = []
        for w_pair in question_list:
            for en_w, ru_w in w_pair.items():
                other_words.append(en_w)
        other_words_buttons = [types.KeyboardButton(word) for word in other_words]
        buttons = [target_word_button] + other_words_buttons
        random.shuffle(buttons)
        next_button = types.KeyboardButton(Command.USE_EXAMPLE)
        delete_button = types.KeyboardButton(Command.DELETE_WORD)
        add_button = types.KeyboardButton(Command.ADD_WORD)
        buttons.extend([next_button, delete_button, add_button])
        
        markup.add(*buttons)
        
        ruen_question = f'Выбери перевод слова: {target_word}'
        bot.send_message(message.chat.id, ruen_question, reply_markup=markup)
        
        bot.set_state(message.from_user.id, MyStates.ruen_target_word, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['ruen_target_word'] = target_word
            data['ruen_translated_word'] = translated_target_word
            data['ruen_other_words'] = other_words
            data['enru_target_word'] = ''
            data['enru_translated_word'] = ''
            data['enru_other_words'] = '' 

    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def message_reply(message):
        InitialValues.current_user_id = reg_user(session, message.from_user.username)
        session_name = session
        bot_name = bot
        user_id = InitialValues.current_user_id
        if message.text == Command.ADD_WORD:
            request_for_word = bot.send_message(message.chat.id, 'Введи (через пробел) ангилйское слово, которое хочешь учить, и есго перевод на русский')
            bot.register_next_step_handler(request_for_word, get_new_word_pair, session_name, bot_name, user_id)
        elif message.text == Command.DELETE_WORD:
            request_for_word = bot.send_message(message.chat.id, 'Введи английское слово, которое хочешь удалить')
            bot.register_next_step_handler(request_for_word, del_word, session_name, bot_name)
        elif message.text == Command.USE_EXAMPLE:
            if has_latin(message.text) == True:
                with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                    enru_target_word = data['enru_target_word']
                print(enru_target_word)
                for ex in get_use_example(enru_target_word, FREE_DICT_API_HOST):
                    bot.send_message(message.chat.id, f'{ex}')
            else:
                bot.send_message(message.chat.id, 'Не думаю, что тебе нужен пример использования русского слова :)')
        else:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                enru_target_word = data['enru_translated_word']
                ruen_target_word = data['ruen_translated_word']
            if has_latin(message.text) == True and message.text == ruen_target_word:
                cor_guess = session.query(WordsInStudy.correct_guesses).filter(WordsInStudy.en_word==message.text).all()
                session.commit()
                session.query(WordsInStudy).filter(WordsInStudy.en_word==message.text).update({'correct_guesses': cor_guess[0][0] + 1}, synchronize_session='fetch')
                generate_ruen_question(message)
                bot.send_message(message.chat.id, 'Всё правильно')
            elif has_cyrillic(message.text) == True and message.text == enru_target_word:
                cor_guess = session.query(WordsInStudy.correct_guesses).filter(WordsInStudy.ru_word==message.text).all()
                session.commit()
                session.query(WordsInStudy).filter(WordsInStudy.ru_word==message.text).update({'correct_guesses': cor_guess[0][0] + 1}, synchronize_session='fetch')
                generate_enru_question(message)
                bot.send_message(message.chat.id, 'Всё правильно')       
            else: 
                bot.send_message(message.chat.id, 'Не-а, попробуй ещё разок')
        return session.commit()
        
    print('Bot is running')
    for word in InitialValues.basic_words_list:
        add_row_to_table(session, 'BasicWords', word)
    bot.polling()  