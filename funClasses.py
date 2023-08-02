import random
import requests
import json
import re
import db_classes
import telebot

import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.dialects import postgresql
from sqlalchemy import (Column, Index, Date, DateTime, Numeric, BigInteger, String, ForeignKey, Boolean)

from db_classes import BasicWords, Users, StudiedWords, WordsInStudy, create_db, create_tables

def get_word_to_learn(session_name):
    words_list = []
    words_amount = session_name.query(WordsInStudy).count()
    for id in random.sample(range(1, words_amount), 4):
        en_word = session_name.query(WordsInStudy.en_word).filter(WordsInStudy.id == int(id)).all()
        ru_word = session_name.query(WordsInStudy.ru_word).filter(WordsInStudy.id == int(id)).all()
        words_list.append({en_word[0][0]: ru_word[0][0]})
    return words_list
    
def add_row_to_table(session_name, table_name: str, content_dict: dict):
        if table_name == 'BasicWords':
            row = session_name.query(BasicWords).filter(BasicWords.en_word==content_dict['en_word'], 
                                                        BasicWords.ru_word==content_dict['ru_word']).all()
            if not row:
                session_name.add(BasicWords(en_word=content_dict['en_word'], 
                                            ru_word=content_dict['ru_word']))
        elif table_name == 'Users':
            row = session_name.query(Users).filter(Users.username==content_dict['username']).all()
            if not row:
                session_name.add(Users(username=content_dict['username']))
        elif table_name == 'WordsInStudy':
            row = session_name.query(WordsInStudy).filter(WordsInStudy.en_word==content_dict['en_word'], 
                                                          WordsInStudy.ru_word==content_dict['ru_word'], 
                                                          WordsInStudy.correct_guesses==content_dict['correct_guesses'],
                                                          WordsInStudy.user_id==content_dict['user_id']).all()
            if not row:
                session_name.add(WordsInStudy(en_word=content_dict['en_word'], 
                                              ru_word=content_dict['ru_word'], 
                                              correct_guesses=content_dict['correct_guesses'], 
                                              user_id=content_dict['user_id']))
        elif table_name == 'StudiedWords':
            row = session_name.query(StudiedWords).filter(StudiedWords.en_word==content_dict['en_word'], 
                                                          StudiedWords.id_users==content_dict['id_users']).all()
            if not row:
                session_name.add(StudiedWords(en_word=content_dict['en_word'], 
                                              id_users=content_dict['id_users']))
        # elif table_name == "AllWordsSet":
        #     session_name.add(AllWordsSet(en_word=content_dict['en_word'], ru_word=content_dict['ru_word'], id_users=content_dict['id_users']))
        return session_name.commit()

def show_words_in_study(session_name, current_user_id):
    res = session_name.query(WordsInStudy).filter(WordsInStudy.user_id==current_user_id).count()
    return res

def reg_user(session_name, username: str):
    res = session_name.query(Users.id).filter(Users.username==username).all()
    if len(res) != 0:
        session_name.commit()
        return res[0][0]
    else:
        add_row_to_table(session_name, 'Users', {'username': username})
        session_name.commit()
        # print(res)
        return res[0][0]

def remove_row_from_table(session_name, word_to_remove):
    session_name.query(WordsInStudy).filter(WordsInStudy.en_word==word_to_remove).delete()
    return session_name.commit()

def has_cyrillic(text):
    return bool(re.search('[а-яА-Я]', text))

def has_latin(text):
    return bool(re.search('[a-zA-Z]', text))

def get_new_word_pair(message, session_name, bot_name, user_id):
    word_to_add = message.text.split()
    add_row_to_table(session_name, 'WordsInStudy', {'en_word':word_to_add[0], 'ru_word': word_to_add[1], 'correct_guesses': 0, 'user_id': user_id})
    bot_name.send_message(message.chat.id, f'Отлично, теперь ты изучаешь {show_words_in_study(session_name, user_id)} слов')
    return word_to_add

def del_word(message, session_name, bot_name):
    word_to_del = message.text
    print(word_to_del)
    remove_row_from_table(session_name, word_to_del)
    bot_name.send_message(message.chat.id, 'Как скажешь, больше не будем иметь дела с этим словом')
    return

def get_use_example(word, dictionary_api_url):
    url = dictionary_api_url
    example_list = []
    req_url = f'{url}/{str(word)}'
    response = json.loads(requests.get(req_url).text)
    for param in response:
        for category in param.keys():
            if category == 'meanings':
                for content in param[category]:
                    for criterion in content.keys():
                        if criterion == 'definitions':
                            for facts in content[criterion]:
                                for k in facts.keys():
                                    if k == 'example':
                                        example_list.append(facts[k])
    return example_list

def send_word_to_studied(session_name, message, bot, en_word, user_id):
        if session_name.query(WordsInStudy.correct_guesses).filter(WordsInStudy.en_word==en_word).all() >= 10:
            ru_word = session_name.query(WordsInStudy.ru_word).filter(WordsInStudy.en_word==en_word)        
            add_row_to_table(session_name, 'StudiedWords', {'en_word': en_word, 'ru_word': ru_word, 'user_id': user_id})
            remove_row_from_table(session_name, en_word)
            bot.send_message(message.chat.id, 'Ура! Ты выучил это слово. Я отправлю его в твою базу изученных слов и больше не буду предлагать')

class Command:
    ADD_WORD = 'ДОБАВЬ СЛОВО'
    DELETE_WORD = 'УДАЛИ СЛОВО'
    USE_EXAMPLE = 'ПОКАЖИ ПРИМЕР'

class InitialValues:
    basic_words_list = [
    {'en_word': 'muck', 'ru_word': 'грязь'},
    {'en_word': 'duck', 'ru_word': 'утка'},
    {'en_word': 'buck', 'ru_word': 'самец'},
    {'en_word': 'suck', 'ru_word': 'сосать'},
    {'en_word': 'luck', 'ru_word': 'удача',},
    {'en_word': 'puck', 'ru_word': 'шайба',},
    {'en_word': 'ruck', 'ru_word': 'толчея'},
    {'en_word': 'mass', 'ru_word': 'масса',},
    {'en_word': 'mess', 'ru_word': 'беспорядок'},
    {'en_word': 'bass', 'ru_word': 'бас',}
    ]
    current_user_id = 0
    command_dict = {
    '/enru': 'Предложу тебе слово на английском языке и четыре варианта перевода на русский. Когда выберешь правильный перевод - получишь новое слово. Прогресс сохраняется',
    '/ruen': 'Предложу тебе слово на русском языке и четыре варианта перевода на английский. Когда выберешь правильный перевод - получишь новое слово. Прогресс сохраняется',
    '/stop': 'Остановлюсь, если ты пока больше не хочешь учить английский',
    '/mywords': 'Покажу тебе список слов, которые ты изучаешь',
    '/allwords': 'Покажу тебе список слов, которые изучают все пользователи',
    '/help': 'Напомню тебе, что я умею',
    }
    buttons = {
        f'Кнопка {Command.ADD_WORD}': 'Добавлю в твой словарь новое слово',
        f'Кнопка {Command.DELETE_WORD}': 'Удалю слово, которое ты уже хорошо знаешь',
        f'Кнопка {Command.USE_EXAMPLE}': 'Покажу тебе пример использовfния слова, которое тебе нужно перевести'
    }