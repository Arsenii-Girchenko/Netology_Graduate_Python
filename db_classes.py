import psycopg2
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class BasicWords(Base):
    __tablename__ = 'BasicWords'
    
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    en_word = sq.Column(sq.String(length=34), unique=True)
    ru_word = sq.Column(sq.String(length=37))
    
    word_in_study = relationship("WordsInStudy", back_populates="word")
    studied_word = relationship("StudiedWords", back_populates="word")

class Users(Base):
    __tablename__ = 'Users'
    
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    username = sq.Column(sq.String(length=100), unique=True)
    
    word_in_study = relationship("WordsInStudy", back_populates="user")
    studied_word = relationship("StudiedWords", back_populates="user")
    
class WordsInStudy(Base):
    __tablename__ = 'WordsInStudy'
    
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    correct_guesses = sq.Column(sq.Integer)
    word_id = sq.Column(sq.Integer, sq.ForeignKey(BasicWords.id))
    user_id = sq.Column(sq.Integer, sq.ForeignKey(Users.id))
    
    user = relationship("Users", back_populates="word_in_study")
    word = relationship("BasicWords", back_populates="word_in_study")

class StudiedWords(Base):
    __tablename__ = 'StudiedWords'
    
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    word_id = sq.Column(sq.Integer, sq.ForeignKey(BasicWords.id))
    user_id = sq.Column(sq.Integer, sq.ForeignKey(Users.id))
    
    word = relationship("BasicWords", back_populates="studied_word")
    user = relationship("Users", back_populates="studied_word")

def create_db(username, password, db_name):
    try:
        connection = psycopg2.connect(user=username, password=password)
        connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        with connection.cursor() as cursor:
            cursor.execute('CREATE DATABASE %s' % (db_name, ))
    finally:
        if connection:
            connection.close()
            return print('Database created')

def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print('tables created')
    return