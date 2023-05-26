
import os.path
import requests
import telebot
import webbrowser
import sqlite3
import json
import time

from dotenv import load_dotenv
from currency_converter import CurrencyConverter
# from forex_python.converter import CurrencyRates
from telebot import types, callback_data, callback_data
from telebot.types import WebAppInfo

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN) # ключ телеграм

API = 'a455439cb8ea542bbe57143066b6990a' # ключ погоди

name = None     # Глобальна змінна для збереження імені контакта
# currency_converter = CurrencyRates()  # Об'єкт конвертора
currency = CurrencyConverter()          # Об'єкт конвертора
amount = 0      # Глобальна змінна для збереження суми
city_data = {}  # Глобальна змінна для збереження даних про міста


# ! При старті бота створюється база даних користувача
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    create_user_database(user_id)
    bot.send_message(message.chat.id, f'Вітаю {message.from_user.first_name} {message.from_user.last_name}!')


#  ! Головне меню
@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    btn1 = types.KeyboardButton("Телефонна книга")
    btn2 = types.KeyboardButton('Погода на сьогодні')
    btn3 = types.KeyboardButton("Конвертор валют")
    btn4 = types.KeyboardButton('Закрити меню')
    btn5 = types.KeyboardButton('Мій ID')
    btn6 = types.KeyboardButton('Список усіх команд')
    btn7 = types.KeyboardButton('Сайт бота')
    markup.row(btn1, btn2)
    markup.row(btn3, btn7)
    markup.row(btn5, btn6)
    markup.row(btn4)
    header_text = "--- МЕНЮ ---"
    bot.send_message(message.chat.id, header_text, reply_markup=markup)
    bot.register_next_step_handler(message, on_click_menu)


def on_click_menu(message):
    print(f"Користувач {message.from_user.username} натиснув кнопку: {message.text}")
    if message.text == 'Телефонна книга':
        phone_book_menu(message)

    elif message.text == "Погода на сьогодні":
        bot.send_message(message.chat.id, 'Введіть назву міста англійською мовою:')
        bot.register_next_step_handler(message, search_cities)

    elif message.text == 'Конвертор валют':
        start_converter(message)

    elif message.text == 'Закрити меню':
        hide_buttons(message)

    elif message.text == 'Мій ID':
        id(message)

    elif message.text == 'Список усіх команд':
        help(message)

    elif message.text == 'Сайт бота':
        gosite(message)

# до кнопка повернення до головного меню
def button_back_to_menu(message):
    markup = types.InlineKeyboardMarkup()
    btn_menu = types.InlineKeyboardButton('МЕНЮ', callback_data='menu')
    markup.add(btn_menu)
    bot.send_message(message.chat.id, 'Натисніть "МЕНЮ" для повернення на головне меню.', reply_markup=markup)



# ! конвертор валют
# Хендлер для запуску ковертора
@bot.message_handler(commands=['converter'])
def start_converter(message):
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
        btn6 = types.InlineKeyboardButton('Головне меню', callback_data='menu')
        markup.add(btn1, btn2, btn3, btn4)
        markup.add(btn5)
        markup.add(btn6)
        bot.send_message(message.chat.id, 'Оберіть умови конвертації', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Сума має бути більше нуля. Будь ласка, спробуйте ще раз.')
        bot.register_next_step_handler(message, summa)
        return

# Обробник обраних користувачем кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "menu":
        menu(call.message)

    elif call.data != 'else':
        values_btn = call.data.split('/')
        source_currency = values_btn[0]
        target_currency = values_btn[1]
        converted_amount = currency.convert(amount, source_currency, target_currency)
        bot.send_message(call.message.chat.id,
                         f'{amount} {source_currency} = {round(converted_amount, 2)} {target_currency}')

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
        bot.send_message(message.chat.id,
                         f'{amount} {source_currency} = {round(converted_amount, 2)} {target_currency}')

    except Exception:
        bot.send_message(message.chat.id, 'Щось пішло не так. Будь ласка, введіть суму ще раз.')
        bot.register_next_step_handler(message, summa)



# ! телефонна книга
# меню телефонної книги
@bot.message_handler(commands=['phone_book_menu'])
def phone_book_menu(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    btn1 = types.KeyboardButton("Список контактів")
    btn4 = types.KeyboardButton('Додати контакт')
    markup.row(btn1, btn4)
    btn2 = types.KeyboardButton("Видалити контакт")
    btn3 = types.KeyboardButton('Закрити меню')
    btn5 = types.KeyboardButton('Голомне меню')
    markup.row(btn2, btn3)
    header_text = "--- ТЕЛФОННА КНИГА ---"
    bot.send_message(message.chat.id, header_text, reply_markup=markup)
    bot.register_next_step_handler(message, on_click)

# Обробник кнопок
def on_click(message):
    print(f"Користувач {message.from_user.username} натиснув кнопку: {message.text}")
    if message.text == 'Список контактів':
        handle_show_contacts(message)

    elif message.text == "Додати контакт":
        handle_add_contact(message)

    elif message.text == 'Видалити контакт':
        handle_delete_contact(message)

    elif message.text == 'Закрити меню':
        hide_buttons(message)

    elif message.text == 'Голомне меню':
        menu(message)

# Функція закриття меню
def hide_buttons(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "меню закрите", reply_markup=markup)

# Функція приймає ім'я та запитує номеру контакту
def ask_contact_name(message):
    global name
    name = message.text.strip()

    # Перевірка наявності імені в базі даних
    user_id = message.chat.id
    conn = sqlite3.connect(f'{user_id}_contacts.db')
    c = conn.cursor()
    c.execute('SELECT name FROM contacts WHERE name = ?', (name,))
    existing_name = c.fetchone()
    conn.close()

    if existing_name:
        bot.reply_to(message, f'Контакт з ім\'ям {name} вже існує. Будь ласка, введіть інше ім\'я.')
        bot.register_next_step_handler(message, ask_contact_name)
    else:
        bot.reply_to(message, 'Введіть номер контакту:')
        bot.register_next_step_handler(message, ask_contact_number)

# Функція приймає номер контакту
def ask_contact_number(message):
    phone_number = message.text.strip()

    # Перевірка, чи введений номер складається лише з цифр
    if not phone_number.isdigit():
        bot.reply_to(message, 'Номер контакту повинен містити лише цифри. Будь ласка, введіть коректний номер.')
        bot.register_next_step_handler(message, ask_contact_number)
    else:
        user_id = message.chat.id
        conn = sqlite3.connect(f'{user_id}_contacts.db')
        c = conn.cursor()
        c.execute('INSERT INTO contacts (name, phone_number) VALUES (?, ?)', (name, phone_number))
        conn.commit()
        conn.close()

        bot.reply_to(message, f'Контакт {name} з номером {phone_number} успішно доданий.')
        phone_book_menu(message)

# Хендлер для додавання контакту
@bot.message_handler(commands=['add_contact'])
def handle_add_contact(message):
    bot.reply_to(message, 'Введіть ім\'я та призвище контакту:')
    bot.register_next_step_handler(message, ask_contact_name)

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
        phone_book_menu(message)
    else:
        response = 'Контакти:\n'
        for contact in contacts:
            response += f'Ім\'я: {contact[0]}, Номер телефону: {contact[1]}\n'
        bot.reply_to(message, response)
        phone_book_menu(message)

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
            phone_book_menu(message)

    if not found:
        bot.reply_to(message, f'Контакт з ім\'ям {name} не знайдений.')
        phone_book_menu(message)

    conn.close()

# Функція для створення бази даних для нового користувача
def create_user_database(user_id):
    conn = sqlite3.connect(f'{user_id}_contacts.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS contacts (name TEXT, phone_number TEXT)')
    conn.commit()
    conn.close()


# ! Хендлер для переходу на сайт бота
@bot.message_handler(commands=['site'])
def gosite(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Відкрити в Телеграм',
                                          web_app=WebAppInfo(url='https://soosanin2.github.io/')))
    bot.send_message(message.chat.id,
                     f"Відкрити у браузері \n \n https://soosanin2.github.io/ \n .",
                     reply_markup=markup)


# ! Хендлер для отримання всіх команд
@bot.message_handler(commands=['commands'])
def help(message):
    bot.send_message(message.chat.id, '''
/start - Запуск бота, привітання
/menu - Меню бота
/site - Відкрити вебсайт (для десктопу)
/converter - Запустити конвертор валют
/phone_book_menu - Відкрити меню телефонної книги 
/add_contact - Додати контакт до телефонної книги 
/show_contacts - Показати всі контакти
/delete_contact - Видалити контакт
/sitem - Посилання на сайт бота
/commands - Список усіх команд
/id - Дізнатися свій id у телеграмі
''')
    button_back_to_menu(message)


# ! Хендлер для отримання id користувача
@bot.message_handler(commands=['id'])
def id(message):
    bot.reply_to(message, f'Id: {message.from_user.id}')
    button_back_to_menu(message)



# ! погода
#  отримання координат
def search_cities(message):
    city_name = message.text.strip()
    url = f'https://geocoding-api.open-meteo.com/v1/search?name={city_name}'
    response = requests.get(url)
    data = response.json()
    # print(data)
    if 'generationtime_ms' in data and not data.get('results'):
        bot.reply_to(message, 'Міста не знайдено5')
        return

    cities = data.get('results')
    if not cities:
        bot.reply_to(message, 'Міста не знайдено3')
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)

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

# отримання довготи та широти
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
    url = f'http://api.openweathermap.org/data/2.5/weather?lat={latitude}&' \
          f'lon={longitude}&appid={API}&lang=ua&units=metric'

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
    button_back_to_menu(message)

# розшифровка напряму вітру
def get_wind_direction(degrees):
    if degrees < 0 or degrees > 360:
        return 'Невідомий'
    directions = ['Північний', 'Північно-східний', 'Східний', 'Південно-східний',
                  'Південний', 'Південно-західний', 'Західний', 'Північно-західний']
    index = round(degrees / 45) % 8
    return directions[index]



# бескінечно запущено програму
bot.polling(none_stop=True)