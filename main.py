import os.path
import requests
import telebot
import webbrowser
import sqlite3
import json
import time


from telebot import types, callback_data, callback_data

bot = telebot.TeleBot('6089179411:AAG_SgFgx2wbcyDWHJX093G__19XJ_ArSJo') # ключ телеграм
API = 'a455439cb8ea542bbe57143066b6990a' # ключ погоди

name = None

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f'Вітаю {message.from_user.first_name} {message.from_user.last_name}')


#  ! робоче меню
@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(f"пгода\n(смартфон)")
    markup.row(btn1)
    btn2 = types.KeyboardButton(f"пгода\n(комп'ютер)")
    btn3 = types.KeyboardButton('закрити меню')
    markup.row(btn2, btn3)
    header_text = "--- МЕНЮ ---"
    bot.send_message(message.chat.id, header_text, reply_markup=markup)
    # отправка файлов
    # file = open('./static/img1.jpg', 'rb')
    # bot.send_photo(message.chat.id, file,
    #                # по желанию можно добавить кновки
    #                reply_markup=markup
    #                )

    # кнопка работает 1 раз
    bot.register_next_step_handler(message, on_click)


def on_click(message):
    print(f"Користувач {message.from_user.username} натиснув кнопку: {message.text}")
    if message.text == 'пгода\n(смартфон)':
        start_weather(message)

    elif message.text == "пгода\n(комп'ютер)":
        webbrowser.open('https://ua.sinoptik.ua/')
        menu(message)
    elif message.text == 'закрити меню':
        hide_buttons(message)

def menu_to_weather(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Погода на сьогодні", reply_markup=markup)

def hide_buttons(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "меню закрите", reply_markup=markup)

# ! погода
@bot.message_handler(commands=['weather'])
def start_weather(message):
    menu_to_weather(message)
    bot.send_message(message.chat.id, 'вкажіть назву міста')
    bot.register_next_step_handler(message, get_city_for_weather)


def get_city_for_weather(message):
    city = message.text.strip().lower()
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API}&lang=ua&units=metric'
    res = requests.get(url)
    data = res.json()

    if data['cod'] == '404':
        bot.reply_to(message, 'Місто не знайдено')
        return

    temperature = data['main']['temp']
    feels_like = data['main']['feels_like']
    wind_speed = data['wind']['speed']
    wind_deg = data['wind']['deg']
    clouds = data['weather'][0]['description']

    bot.reply_to(message, f"""
    ---Погода зараз---\n
    Температура зараз: {temperature}°C\n
    Відчувається як: {feels_like}°C\n
    Сила вітру: {wind_speed} м/с\n
    Напрям вітру: {get_wind_direction(wind_deg)}\n
    Умови: {clouds}
    """)


def get_wind_direction(degrees):
    if degrees < 0 or degrees > 360:
        return 'Невідомий'
    directions = ['Північний', 'Північно-східний', 'Східний', 'Південно-східний',
                  'Південний', 'Південно-західний', 'Західний', 'Північно-західний']
    index = round(degrees / 45) % 8
    return directions[index]


#     додавання зображень выдносно погоди

# ! регістрація юзерів
@bot.message_handler(commands=['new_user'])
def new_user(message):
    # создание и подключение бази данных
    conn = sqlite3.connect('hamster.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS user (id int auto_increment primary key, name varchar(50), pass varchar(50))')

    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, "Введіть ім'я для реєстрації")
    bot.register_next_step_handler(message, user_name)

def user_name(message):
    global name
    name = message.text.strip()
    bot.send_message(message.chat.id, "Введіть пароль")
    bot.register_next_step_handler(message, user_password)

def user_password(message):
    password = message.text.strip()

# внесение изменений в базу данных
    conn = sqlite3.connect('hamster.sql')
    cur = conn.cursor()

    cur.execute("INSERT INTO user(name, pass) VALUES ('%s', '%s')" % (name, password))

    conn.commit()
    cur.close()
    conn.close()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('список користувачів', callback_data='users'))
    #                                                                     это значит что кнопка будет вмест с сообщением
    bot.send_message(message.chat.id, f"Вітаю {name}, ви зареєстровані", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    conn = sqlite3.connect('hamster.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM user')
    users = cur.fetchall()

    info =''
    for el in users:
        info += f"Ім'я: {el[1]}, пароль: {el[2]}\n"

    cur.close()
    conn.close()

    bot.send_message(call.message.chat.id, info)

# ! інші команди
# перехід на сайт бота
@bot.message_handler(commands=['site'])
def gosite(message):
    webbrowser.open('https://soosanin2.github.io/')

@bot.message_handler(commands=['sitem'])
def gosite_mobile(message):
    bot.reply_to(message, f'https://soosanin2.github.io/')


# отримання всіх команд
@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '''start - Запуск бота, привітання
menu - Меню бота
new_user - Додавання нового користувача
site - Відкрити вебсайт (для десктопу)
sitem - Посилання на сайт (для мобільного)
id - Дізнатися свій id у телеграмі''')


# отримати id користувача
@bot.message_handler()
def id(message):
    if message.text.lower() == 'id':
        bot.reply_to(message, f'Id: {message.from_user.id}')
    else:
        pass


# картинки, звуки, відео
# @bot.message_handler(content_types=['photo'])
# def get_photo(message):
#     bot.reply_to(message, 'Фото отримав')

@bot.message_handler(content_types=['document'])
def handle_document(message):
    bot.reply_to(message, 'Документ отримав')

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    bot.reply_to(message, 'Аудіо отримав')

@bot.message_handler(content_types=['video'])
def handle_video(message):
    bot.reply_to(message, 'Відео отримав')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.reply_to(message, 'Геолокацію отримав')

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    bot.reply_to(message, 'Кконтакт отримав')

@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    bot.reply_to(message, 'Стикер отримав')

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    bot.reply_to(message, 'Голосове повідомлення отримав')


# кнопка привязана до отриманної фото
# @bot.message_handler(content_types=['photo'])
# def get_photo(message):
#     markup = types.InlineKeyboardMarkup()
#     markup.add(types.InlineKeyboardButton('сайт погоди', url='https://ua.sinoptik.ua/'))
#     markup.add(types.InlineKeyboardButton('видалити фото', callback_data='delete'))
#     markup.add(types.InlineKeyboardButton('змінити фото', callback_data='edit'))
#     bot.reply_to(message, 'погода тут', reply_markup=markup)

# винесення створенноъ кнопки
@bot.message_handler(content_types=['photo'])
def get_photo(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('сайт погоди', url='https://ua.sinoptik.ua/')
    btn2 = types.InlineKeyboardButton('видалити фото', callback_data='delate')
    btn3 = types.InlineKeyboardButton('змінити фото', callback_data='edit')
    markup.row(btn1)
    markup.row(btn2, btn3)
    bot.reply_to(message, 'погода тут', reply_markup=markup)

# обробка кнопок
@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'delate':
        bot.delete_message(callback.message.chat.id, callback.message.message_id - 1)
    elif callback.data == 'edit':
        bot.edit_message_text('новий текст', callback.message.chat.id, callback.message.message_id - 1)














# бескінечно запущено програму
bot.polling(none_stop=True)