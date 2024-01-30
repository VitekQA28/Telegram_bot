import telebot
import sqlite3
from telebot import types
import os
from datetime import datetime
import random
from time import sleep

# Здесь нужно вставить токен, который дал BotFather при регистрации
# Пример: token = '2007628239:AAEF4ZVqLiRKG7j49EC4vaRwXjJ6DN6xng8'
token = '6741558043:AAEmwdMZ6FTEKn2UBp7TLw0iEaEqXhSjAUg'  # <<< Ваш токен

# В этой строчке мы заводим бота и даем ему запомнить токен
bot = telebot.TeleBot(token)
name = None

# Пишем первую функцию, которая отвечает "Привет" на команду /start
# Все функции общения приложения с ТГ спрятаны в функции под @
@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('BD_users.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(50) UNIQUE, pass VARCHAR(50), user_id INTEGER UNIQUE)')
    conn.commit()
    cur.close()
    conn.close()

    buttons = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    reg_button = types.KeyboardButton('Регистрация')
    auth_button = types.KeyboardButton('Авторизация')
    forgot_button = types.KeyboardButton('Забыли пароль?')
    restart_button = types.KeyboardButton('Перезапустить')
    draw_button = types.KeyboardButton('Участвовать в розыгрыше')
    buttons.add(reg_button)
    buttons.row(auth_button, forgot_button)
    buttons.row(draw_button, restart_button)
    bot.send_message(message.chat.id, 'Привет, для регистрации нажми на кнопку "Регистрация"', reply_markup=buttons)


@bot.message_handler(func=lambda message: message.text == 'Регистрация')
def reg(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('BD_users.sql')
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cur.fetchone()
    if existing_user:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы.')
    else:
        bot.send_message(message.chat.id, 'Сейчас тебя зарегистрируем! Введите ваше имя')
        bot.register_next_step_handler(message, user_name)
    cur.close()
    conn.close()

 
def user_name(message):
    global name
    name = message.text.strip()
    bot.send_message(message.chat.id, 'Введите пароль')
    bot.register_next_step_handler(message, user_pass)

def user_pass(message):
    password = message.text.strip()
    user_id = message.from_user.id

    conn = sqlite3.connect('BD_users.sql')
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cur.fetchone()
    if existing_user:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы.')
    else:
        cur.execute("INSERT INTO users (name, pass, user_id) VALUES (?, ?, ?)", (name, password, user_id))
        conn.commit()
        bot.send_message(message.chat.id, 'Регистрация завершена.')
    cur.close()
    conn.close()

#Запрашиваем пороль, если забыли
@bot.message_handler(func=lambda message: message.text == 'Забыли пароль?')
def get_password(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('BD_users.sql')
    cur = conn.cursor()
    cur.execute('SELECT pass FROM users WHERE user_id = ?', (user_id,))
    password = cur.fetchone()
    if password:
        bot.send_message(message.chat.id, f"Ваш пароль: {password[0]}")
    else:
        bot.send_message(message.chat.id, "Пароль не найден")
    cur.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == 'Авторизоваться')
def auth(message):
    markup = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton('Отмена', callback_data='cancel')
    btn_send = types.InlineKeyboardButton('Передать', callback_data='send_contact')
    markup.row(btn_cancel, btn_send)
    bot.send_message(message.chat.id, "Хотите передать свой номер телефона боту?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Перезапустить')
def restart_bot(message):
    bot.send_message(message.chat.id, "Бот перезапущен.")
    start(message)

# Создание базы данных, если она не существует для розыгрыша

connt = sqlite3.connect('rozigr_bd.sqlite', check_same_thread=False)
cursor = connt.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS rozigr_users (user_id INTEGER UNIQUE, phone_number TEXT, event_id INTEGER UNIQUE, date TEXT)")

# Функция для добавления пользователя в БД
def add_user_to_db(user_id, phone_number):
    conn = sqlite3.connect('rozigr_bd.sqlite') 
    cursor = conn.cursor()
    event_id = generate_event_id()  # Генерация уникального номера розыгрыша
    cursor.execute("INSERT INTO rozigr_users (user_id, phone_number, event_id) VALUES (?, ?, ?)", (user_id, phone_number, event_id))
    conn.commit()
    conn.close()
    return event_id  # Возвращаем event_id после добавления пользователя в БД
    
# Функция для проверки пользователя в БД
def check_user_in_db(user_id):
    connt = sqlite3.connect('rozigr_bd.sqlite')
    cursor.execute("SELECT * FROM rozigr_users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    connt.close()
    return result is not None    

# Генерация уникального event_id (пример)
def generate_event_id():
    return random.randint(1000, 9999)

# Обработчик кнопки "Участвовать в розыгрыше"
@bot.message_handler(func=lambda message: message.text == 'Участвовать в розыгрыше')
def participate_in_raffle(message):
# Создание таблицы, если она не существует
    user_id = message.from_user.id
    if not check_user_in_db(user_id):
        bot.send_message(message.chat.id, "Условия розыгрыша...\nДата проведения розыгрыша: 01.01.24 (например)")
        bot.send_message(message.chat.id, "Желаете участвовать?", reply_markup=generate_inline_button())
        # Добавление пользователя в базу данных
        add_user_to_db(user_id, "phone_number_here")  
        bot.send_message(message.chat.id, "Вы успешно зарегистрированы в розыгрыше.")
        bot.register_next_step_handler(message, handle_participate_button)
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы в розыгрыше.")
        bot.register_next_step_handler(message, handle_participate_button)


# Генерация инлайн-кнопки "участвовать"
def generate_inline_button():
    keyboard = types.InlineKeyboardMarkup()
    participate_button = types.InlineKeyboardButton("Участвовать", callback_data='participate')
    keyboard.add(participate_button)
    return keyboard
     
#Выводим после подтверждения об участии номер розыгрыша
def handle_participate_button(user_id, phone_number):
    event_id = add_user_to_db(user_id, phone_number)  
    bot.send_message(user_id, f"Ваш уникальный номер розыгрыша: {event_id}")    



# Запускаем бота. Он будет работать до тех пор, пока работает ячейка
# (крутится значок слева).
# Остановим ячейку - остановится бот
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as _ex:
        print(_ex)
        sleep(2, 4)
        
