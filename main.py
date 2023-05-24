import os.path
import requests
import telebot
import webbrowser
import sqlite3
import json
import time
from currency_converter import CurrencyConverter
# from forex_python.converter import CurrencyRates
from telebot import types, callback_data, callback_data

bot = telebot.TeleBot('6089179411:AAG_SgFgx2wbcyDWHJX093G__19XJ_ArSJo') # ключ телеграм
API = 'a455439cb8ea542bbe57143066b6990a' # ключ погоди

name = None     # Глобальна змінна для збереження імені контакта
# currency_converter = CurrencyRates()  # Об'єкт конвертора
currency = CurrencyConverter()          # Об'єкт конвертора
amount = 0      # Глобальна змінна для збереження суми
city_data = {}  # Глобальна змінна для збереження даних про міста


# ! конвертор валют
# Хендлер для запуску ковертора
@bot.message_handler(commands=['converter'])
def start(message):
    bot.send_message(message.chat.id, 'Введіть суму')
    bot.register_next_step_handler(message, summa)

# Функція для отримання введеної суми
def summa(message):
    global amount
    try:
        amount = float(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, 'Невірний формат. Будь ласка, спробуйте ще раз.')
        bot.register_next_step_handler(message, summa)
        return

    if amount > 0:
        markup = types.InlineKeyboardMarkup(row_width=2)  # кількість кнопок у ряд

        btn1 = types.InlineKeyboardButton('USD/EUR', callback_data='USD/EUR')
        btn2 = types.InlineKeyboardButton('EUR/USD', callback_data='EUR/USD')
        btn3 = types.InlineKeyboardButton('EUR/GBP ', callback_data='EUR/GBP')
        btn4 = types.InlineKeyboardButton('GBP/EUR', callback_data='GBP/EUR')
        btn5 = types.InlineKeyboardButton('Свій варіант', callback_data='else')
        markup.add(btn1, btn2, btn3, btn4, btn5)
        bot.send_message(message.chat.id, 'Оберіть умови конвертації', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Сума має бути більше нуля. Будь ласка, спробуйте ще раз.')
        bot.register_next_step_handler(message, summa)
        return

# Обробник обраних користувачем кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data != 'else':
        values_btn = call.data.split('/')
        source_currency = values_btn[0]
        target_currency = values_btn[1]
        converted_amount = currency.convert(amount, source_currency, target_currency)
        bot.send_message(call.message.chat.id, f'{amount} {source_currency} = {round(converted_amount, 2)} {target_currency}')
        return
    elif call.data == 'else':
        bot.send_message(call.message.chat.id, 'введіть свій варіант конвертації валют, за зразком "CNY/EUR"')
        bot.register_next_step_handler(call.message, my_carrency)

# Обробник введених користувачем варіантів конвертаціїї
def my_carrency(message):
    try:
        values_btn = message.text.upper().split('/')
        source_currency = values_btn[0]
        target_currency = values_btn[1]
        converted_amount = currency.convert(amount, source_currency, target_currency)
        bot.send_message(message.chat.id, f'{amount} {source_currency} = {round(converted_amount, 2)} {target_currency}')
    except Exception:
        bot.send_message(message.chat.id, 'Щось пішло не так. Будь ласка, введіть суму ще раз.')
        bot.register_next_step_handler(message, summa)
        return



# ! телефонна книга

# При старті бота створюється база даних користувача
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    create_user_database(user_id)
    bot.send_message(message.chat.id, f'Вітаю {message.from_user.first_name} {message.from_user.last_name}!')

# Функція приймає ім'я та запитує номеру контакту
def ask_contact_name(message):
    global name
    name = message.text.strip()
    bot.reply_to(message, 'Введіть номер контакту:')
    bot.register_next_step_handler(message, ask_contact_number)

# Функція приймає номер контакту
def ask_contact_number(message):
    phone_number = message.text.strip()
    user_id = message.chat.id
    conn = sqlite3.connect(f'{user_id}_contacts.db')
    c = conn.cursor()
    c.execute('INSERT INTO contacts (name, phone_number) VALUES (?, ?)', (name, phone_number))
    conn.commit()
    conn.close()

    # Повідомлення про успішне додавання контакту
    bot.reply_to(message, f'Контакт {name} з номером {phone_number} успішно доданий.')


# Хендлер для додавання контакту
@bot.message_handler(commands=['add_contact'])
def handle_add_contact(message):
    bot.reply_to(message, 'Введіть ім\'я та призвище контакту:')
    bot.register_next_step_handler(message, ask_contact_name)

# Функція для додавання контакту до телефонної книги користувача
def add_contact(message):
    user_id = message.chat.id
    name = message.text.strip()
    phone_number = message.text.strip()  # Отримайте номер телефону від користувача

    conn = sqlite3.connect(f'{user_id}_contacts.db')
    c = conn.cursor()
    c.execute('INSERT INTO contacts (name, phone_number) VALUES (?, ?)', (name, phone_number))
    conn.commit()
    conn.close()

    # Повідомлення про успішне додавання контакту
    bot.reply_to(message, f'Контакт {name} з номером {phone_number} успішно доданий.')


# Хендлер для відображення контактів
@bot.message_handler(commands=['show_contacts'])
def handle_show_contacts(message):
    show_contacts(message)

# Функція для відображення контактів з телефонної книги користувача
def show_contacts(message):
    user_id = message.chat.id

    conn = sqlite3.connect(f'{user_id}_contacts.db')
    c = conn.cursor()
    c.execute('SELECT name, phone_number FROM contacts')
    contacts = c.fetchall()
    conn.close()

    if not contacts:
        bot.reply_to(message, 'Ваша телефонна книга порожня.')
    else:
        response = 'Контакти:\n'
        for contact in contacts:
            response += f'Ім\'я: {contact[0]}, Номер телефону: {contact[1]}\n'
        bot.reply_to(message, response)


# # Хендлер для видалення контакту
@bot.message_handler(commands=['delete_contact'])
def handle_delete_contact(message):
    bot.reply_to(message, 'Введіть ім\'я контакту, який потрібно видалити:')
    bot.register_next_step_handler(message, delete_contact)

# Функція для видалення контакту з телефонної книги користувача
def delete_contact(message):
    user_id = message.chat.id
    name = message.text.strip()

    conn = sqlite3.connect(f'{user_id}_contacts.db')
    c = conn.cursor()
    c.execute('SELECT name FROM contacts')
    contacts = c.fetchall()

    found = False
    for contact in contacts:
        if name.lower() == contact[0].lower():
            c.execute('DELETE FROM contacts WHERE name = ?', (contact[0],))
            conn.commit()
            bot.reply_to(message, f'Контакт {contact[0]} успішно видалений.')
            found = True
            break

    if not found:
        bot.reply_to(message, f'Контакт з ім\'ям {name} не знайдений.')

    conn.close()


# Функція для створення бази даних для нового користувача
def create_user_database(user_id):
    conn = sqlite3.connect(f'{user_id}_contacts.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS contacts (name TEXT, phone_number TEXT)')
    conn.commit()
    conn.close()


# перехід на сайт бота
@bot.message_handler(commands=['site'])
def gosite(message):
    webbrowser.open('https://soosanin2.github.io/')

@bot.message_handler(commands=['sitem'])
def gosite_mobile(message):
    bot.reply_to(message, f'https://soosanin2.github.io/')


# отримання всіх команд
@bot.message_handler(commands=['commands'])
def help(message):
    bot.send_message(message.chat.id, '''start - Запуск бота, привітання
menu - Меню бота
new_user - Додавання нового користувача
site - Відкрити вебсайт (для десктопу)
sitem - Посилання на сайт (для мобільного)
id - Дізнатися свій id у телеграмі''')


# отримати id користувача
@bot.message_handler(commands=['id'])
def id(message):
    bot.reply_to(message, f'Id: {message.from_user.id}')


#  ! робоче меню
@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(f"пгода\n(смартфон)")
    btn4 = types.KeyboardButton('Погода на сьогодні')
    markup.row(btn1, btn4)
    btn2 = types.KeyboardButton(f"пгода\n(комп'ютер)")
    btn3 = types.KeyboardButton('закрити меню')
    markup.row(btn2, btn3)
    header_text = "--- МЕНЮ ---"
    bot.send_message(message.chat.id, header_text, reply_markup=markup)
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
    elif message.text == 'обрати місто':
        bot.send_message(message.chat.id, 'Введіть назву міста англійською мовою:')
        bot.register_next_step_handler(message, search_cities)

def menu_to_weather(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Погода на сьогодні", reply_markup=markup)

def hide_buttons(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "меню закрите", reply_markup=markup)


# # ! отримання координат



def search_cities(message):
    city_name = message.text.strip()
    url = f'https://geocoding-api.open-meteo.com/v1/search?name={city_name}'
    response = requests.get(url)
    data = response.json()
    print(data)
    if 'generationtime_ms' in data and not data.get('results'):
        bot.reply_to(message, 'Міста не знайдено5')
        return

    cities = data.get('results')
    if not cities:
        bot.reply_to(message, 'Міста не знайдено3')
        return

    markup = types.ReplyKeyboardMarkup()

    for city in cities:
        btn_text = f"{city['name']} \n {city['country']}, {city.get('admin1', '-')}"
        btn = types.KeyboardButton(btn_text)
        markup.add(btn)

        city_data[btn_text] = {
            'latitude': city['latitude'],
            'longitude': city['longitude'],
            'country': city['country'],
            'admin1': city.get('admin1', '-')
        }

    bot.send_message(message.chat.id, 'Оберіть місто зі списку:', reply_markup=markup)

    bot.register_next_step_handler(message, get_city_coordinates)


def get_city_coordinates(message):
    selected_city = message.text.strip()

    if selected_city not in city_data:
        bot.reply_to(message, 'Помилка отримання координат')
        return

    latitude = city_data[selected_city]['latitude']
    longitude = city_data[selected_city]['longitude']
    get_weather_forecast(message, latitude, longitude)

# отримання погоди

def get_weather_forecast(message, latitude, longitude):
    url = f'http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={API}&lang=ua&units=metric'

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

    bot.send_message(message.chat.id, f"""
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




#     додавання зображень вiдносно погоди

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

# внесення змін до бази даних
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