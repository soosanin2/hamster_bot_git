
import os.path
import requests
import telebot
import webbrowser
import sqlite3
import json

from dotenv import load_dotenv
from telebot import types, callback_data, callback_data
from telebot.types import WebAppInfo

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN) # ключ телеграм


# Функція повернення до головного меню
def button_back_to_menu(message):
    markup = types.InlineKeyboardMarkup()
    btn_menu = types.InlineKeyboardButton('МЕНЮ', callback_data='menu')
    markup.add(btn_menu)
    bot.send_message(message.chat.id, 'Натисніть "МЕНЮ" для повернення на головне меню.', reply_markup=markup)


# Функція при старті бота створюється база даних користувача
def start(message):
    user_id = message.chat.id
    create_user_database(user_id)
    bot.send_message(message.chat.id, f'Вітаю {message.from_user.first_name} {message.from_user.last_name}!')


# Функція для створення бази даних для нового користувача
def create_user_database(user_id):
    conn = sqlite3.connect(f'{user_id}_contacts.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS contacts (name TEXT, phone_number TEXT)')
    conn.commit()
    conn.close()


# Функція для переходу на сайт бота
def gosite(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Відкрити в Телеграм',
                                          web_app=WebAppInfo(url='https://soosanin2.github.io/')))
    bot.send_message(message.chat.id,
                     f"Відкрити у браузері \n \n https://soosanin2.github.io/ \n .",
                     reply_markup=markup)


# Функція для отримання id користувача
def id(message):
    bot.reply_to(message, f'Id: {message.from_user.id}')
    button_back_to_menu(message)


# Функція для отримання всіх команд
def help(message):
    bot.send_message(message.chat.id, '''
/start - Запуск бота, привітання
/menu - Меню бота
/site - Відкрити вебсайт 
/converter - Запустити конвертор валют
/phone_book_menu - Відкрити меню телефонної книги 
/add_contact - Додати контакт до телефонної книги 
/show_contacts - Показати всі контакти телефонної книги
/delete_contact - Видалити контакт з телефонної книги
/commands - Список усіх команд
/id - Дізнатися свій id у телеграмі
''')
    button_back_to_menu(message)


