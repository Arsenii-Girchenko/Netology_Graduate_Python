# import telebot
import random
import funClasses
import db_classes
import API_funcs

from telebot import types
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from db_classes import *
from funClasses import *
from API_funcs import *

TG_TOKEN = '5915102486:AAH4hXOms9V0cojJLfYRMDrzaNboxOfZRIM'
FREE_DICT_API_HOST = 'https://api.dictionaryapi.dev/api/v2/entries/en'

state_storage = StateMemoryStorage()

class MyStates(StatesGroup):
    enru_target_word = State()
    enru_translated_word = State()
    enru_other_words = State()
    ruen_target_word = State()
    ruen_translated_word = State()
    ruen_other_words = State()

def reply_on_start(bot, message, session_name):
    new_user = check_and_reg_user(session_name, message.from_user.username)
    print(new_user)
    if new_user == None:
        print('user already exists')
        bot.send_message(message.chat.id, f'Круто, ты снова тут!')
        send_help(bot, message)
    else:
        reply = ''
        button_repl = ''
        for command, description in InitialValues.command_dict.items():
            reply += f'{command} - {description}\n'
        bot.send_message(message.chat.id, f'Тебя приветствует бот для изучения английского языка. Давай расскажу, какие команды я знаю:\n{reply}')
        for button, description in InitialValues.buttons.items():
            button_repl += f'{button} - {description}\n'
        bot.send_message(message.chat.id, f'Когда выберешь /enru или /ruen, увидишь четыре варианта перевода загаданного слова и ещё {len(InitialValues.buttons)} кнопки:\n{button_repl}')

def get_new_words(bot, message, session_name):
    InitialValues.current_user_id = check_and_reg_user(session_name, message.from_user.username)
    words_id_in_study = session_name.query(WordsInStudy.word_id
                                      ).filter(WordsInStudy.user_id==InitialValues.current_user_id
                                               )
    all_words_id = session_name.query(BasicWords.id)
    print(all_words_id.all())
    print(words_id_in_study.all())
    words_id_not_in_study = set(all_words_id) - set(words_id_in_study)
    print(words_id_not_in_study)
    if words_id_in_study.all() == []:
        for row in session_name.query(BasicWords).all():
            add_row_to_table(session_name, 'WordsInStudy', {'correct_guesses': 0, 'word_id': row.id, 'user_id': InitialValues.current_user_id})
        session_name.commit()
    else:
        for word_id in words_id_not_in_study:
            print(word_id[0])
            add_row_to_table(session_name, 'WordsInStudy', {'correct_guesses': 0, 'word_id': word_id[0], 'user_id': InitialValues.current_user_id})
            bot.send_message(message.chat_id, f'Новые слова добавлены в твой словарь')
    return
   
def send_help(bot, message):
    for command, description in InitialValues.command_dict.items():
        bot.send_message(message.chat.id, f'{command} - {description}')

def generate_enru_question(bot, message, session_name):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    question_list = get_word_to_learn(session_name)
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
    global word_suggestion
    word_suggestion = target_word
    bot.send_message(message.chat.id, enru_question, reply_markup=markup)
    
    bot.set_state(message.from_user.id, MyStates.enru_target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['enru_target_word'] = target_word
        data['enru_translated_word'] = translated_target_word
        data['enru_other_words'] = other_words
        data['ruen_target_word'] = ''
        data['ruen_translated_word'] = ''
        data['ruen_other_words'] = ''
     
def generate_ruen_question(bot, message, session_name):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    question_list = get_word_to_learn(session_name)
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
    global word_suggestion
    word_suggestion = target_word
    bot.send_message(message.chat.id, ruen_question, reply_markup=markup)
    
    bot.set_state(message.from_user.id, MyStates.ruen_target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['ruen_target_word'] = target_word
        data['ruen_translated_word'] = translated_target_word
        data['ruen_other_words'] = other_words
        data['enru_target_word'] = ''
        data['enru_translated_word'] = ''
        data['enru_other_words'] = '' 

def user_choice_reply(bot, message, session_name):
    InitialValues.current_user_id = check_and_reg_user(session_name, message.from_user.username)
    bot_name = bot
    user_id = InitialValues.current_user_id
    if message.text == Command.ADD_WORD:
        request_for_word = bot.send_message(message.chat.id, 'Введи (через пробел) английское слово, которое хочешь учить, и его перевод на русский')
        bot.register_next_step_handler(request_for_word, get_new_word_pair, session_name, bot_name, user_id)
    elif message.text == Command.DELETE_WORD:
        request_for_word = bot.send_message(message.chat.id, 'Введи английское слово, которое хочешь удалить')
        bot.register_next_step_handler(request_for_word, del_word, session_name, bot_name)
    elif message.text == Command.USE_EXAMPLE:
        if has_latin(word_suggestion):
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                enru_target_word = data['enru_target_word']
            for ex in get_use_example(enru_target_word, FREE_DICT_API_HOST):
                bot.send_message(message.chat.id, f'{ex}')
        else:
            bot.send_message(message.chat.id, 'Не думаю, что тебе нужен пример использования русского слова :)')
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            enru_target_word = data['enru_translated_word']
            ruen_target_word = data['ruen_translated_word']
        if has_latin(message.text) and message.text == ruen_target_word:
            cor_guess = session_name.query(WordsInStudy.correct_guesses
                                           ).join(BasicWords, WordsInStudy.word_id==BasicWords.id
                                                  ).filter(BasicWords.en_word==message.text
                                                           ).all()
            session_name.query(WordsInStudy
                               ).filter(WordsInStudy.word_id==BasicWords.id
                                        ).where(BasicWords.en_word==message.text
                                                ).update({'correct_guesses': cor_guess[0][0] + 1}, synchronize_session='fetch')
            bot.send_message(message.chat.id, 'Всё правильно')            
            send_word_to_studied(bot, session_name, message, user_id)
            generate_ruen_question(bot, message, session_name)
        elif has_cyrillic(message.text) and message.text == enru_target_word:
            cor_guess = session_name.query(WordsInStudy.correct_guesses
                                           ).join(BasicWords, WordsInStudy.word_id==BasicWords.id
                                                  ).filter(BasicWords.ru_word==message.text
                                                           ).all()
            session_name.query(WordsInStudy
                               ).filter(WordsInStudy.word_id==BasicWords.id
                                        ).where(BasicWords.ru_word==message.text
                                                ).update({'correct_guesses': cor_guess[0][0] + 1}, synchronize_session='fetch')
            bot.send_message(message.chat.id, 'Всё правильно')             
            send_word_to_studied(bot, session_name, message, user_id)
            generate_enru_question(bot, message, session_name)
        else: 
            bot.send_message(message.chat.id, 'Не-а, попробуй ещё разок')
    return session_name.commit()

def show_my_words(bot, message, session_name):
    words_list = session_name.query(BasicWords.en_word, BasicWords.ru_word
                              ).join(WordsInStudy, BasicWords.id==WordsInStudy.word_id
                                     ).join(Users, WordsInStudy.user_id==Users.id
                                         ).filter(Users.username==message.from_user.username
                                              ).all()
    session_name.commit()
    for word_pair in words_list:
        reply = f'{word_pair[0]} - {word_pair[1]}'
        bot.send_message(message.chat.id, reply)
    return 