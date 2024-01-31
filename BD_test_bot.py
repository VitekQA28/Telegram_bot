import telebot
import sqlite3
from telebot import types
import os
from datetime import datetime
import random
from time import sleep
#import emoji

# Здесь нужно вставить токен, который дал BotFather при регистрации
# Пример: token = '2007628239:AAEF4ZVqLiRKG7j49EC4vaRwXjJ6DN6xng8'
token = '6741558043:AAEmwdMZ6FTEKn2UBp7TLw0iEaEqXhSjAUg'  # <<< Ваш токен

# В этой строчке мы заводим бота и даем ему запомнить токен
bot = telebot.TeleBot(token)

buttons = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
reg_button = types.KeyboardButton('Регистрация')
#auth_button = types.KeyboardButton('Авторизация')
forgot_button = types.KeyboardButton('Забыли пароль?')
restart_button = types.KeyboardButton('Перезапустить')
draw_button = types.KeyboardButton('Участвовать в розыгрыше')
reg_list_button = types.KeyboardButton('Показать участников розыгрыша')
#buttons.add(reg_button)
buttons.row(reg_button, forgot_button)
buttons.row(draw_button, restart_button)
buttons.row(reg_list_button)

# Создаем базу данных для пользователей
conn = sqlite3.connect('BD_users.sql')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(50) UNIQUE, pass VARCHAR(50), user_id INTEGER UNIQUE)')
conn.commit()
cur.close()
conn.close()

# Создаем базу данных для розыгрыша
conn_raffle = sqlite3.connect('rozigr_bd.sqlite')
cursor_raffle = conn_raffle.cursor()
cursor_raffle.execute("CREATE TABLE IF NOT EXISTS rozigr_users (user_id INTEGER UNIQUE, phone_number TEXT, event_id INTEGER UNIQUE, date TEXT)")
conn_raffle.commit()
cursor_raffle.close()
conn_raffle.close()

# Функция для добавления пользователя в базу данных
def add_user_to_db(user_id, phone_number):
    conn = sqlite3.connect('rozigr_bd.sqlite')
    cursor = conn.cursor()
    event_id = generate_event_id()
    cursor.execute("INSERT INTO rozigr_users (user_id, phone_number, event_id, date) VALUES (?, ?, ?, ?)", (user_id, phone_number, event_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return event_id

# Функция для проверки пользователя в базе данных
def check_user_in_db(user_id):
    conn = sqlite3.connect('rozigr_bd.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rozigr_users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Генерация уникального event_id
def generate_event_id():
    return random.randint(1000, 9999)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет, для регистрации нажми на кнопку "Регистрация"',  reply_markup=buttons)
# Обработчик кнопки "Регистрация"
@bot.message_handler(func=lambda message: message.text == 'Регистрация')
def reg(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('BD_users.sql')
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cur.fetchone()
    if existing_user:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы. 👌')
    else:
        bot.send_message(message.chat.id, 'Сейчас тебя зарегистрируем! Введите ваше имя', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, user_name)
    cur.close()
    conn.close()

# Обработчик ввода имени
def user_name(message):
    global name
    name = message.text.strip()
    bot.send_message(message.chat.id, 'Введите пароль', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, user_pass)

# Обработчик ввода пароля
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
    bot.send_message(message.chat.id, 'Вы успешно зарегистрированы. 🚀', reply_markup=buttons)
    cur.close()
    conn.close()

#Перезапустить бота
@bot.message_handler(func=lambda message: message.text == 'Перезапустить')
def restart_bot(message):
    bot.send_message(message.chat.id, "Бот перезапущен.")
    start(message)

# Обработчик кнопки "Авторизация"
@bot.message_handler(func=lambda message: message.text == 'Авторизация')
def auth(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, 'Введите ваше имя', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, check_user)

# Обработчик проверки пользователя
def check_user(message):
    name = message.text.strip()
    user_id = message.from_user.id
    conn = sqlite3.connect('BD_users.sql')
    cur = conn.cursor()
    cur.execute("SELECT pass FROM users WHERE name=? AND user_id=?", (name, user_id))
    password = cur.fetchone()
    if password:
        bot.send_message(message.chat.id, 'Вы успешно авторизованы.')
    else:
        bot.send_message(message.chat.id, 'Пользователь с таким именем не найден.')
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

# Обработчик кнопки "Участвовать в розыгрыше"
@bot.message_handler(func=lambda message: message.text == 'Участвовать в розыгрыше')
def participate_raffle(message):
    user_id = message.from_user.id
    if check_user_in_db(user_id):
        conn = sqlite3.connect('rozigr_bd.sqlite')
        cur = conn.cursor()
        cur.execute("SELECT event_id FROM rozigr_users WHERE user_id=?", (user_id,))
        event_id = cur.fetchone()[0]
        bot.send_message(message.chat.id, f'Вы уже участвуете в розыгрыше. 🤑\nВаш уникальный ID для участия: {event_id}')
        cur.close()
        conn.close()
    else:
        bot.send_message(message.chat.id, 'Введите свой номер телефона', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, add_user_to_raffle)

# Обработчик ввода номера телефона для участия в розыгрыше
def add_user_to_raffle(message):
    phone_number = message.text.strip()
    user_id = message.from_user.id
    event_id = add_user_to_db(user_id, phone_number)
    bot.send_message(message.chat.id, f'🎉Вы успешно зарегистрированы для участия в розыгрыше🎉.\nВаш уникальный ID для участия: {event_id}', reply_markup=buttons)
    
    

# Add a new message handler for the button "Показать участников розыгрыша"
@bot.message_handler(func=lambda message: message.text == 'Показать участников розыгрыша')
def show_raffle_participants(message):
    participants = get_raffle_participants()
    if participants:
        response = "Участники розыгрыша:\n"
        for participant in participants:
            response += f"User ID: {participant[0]}, Event ID: {participant[1]}, Phone Number: {participant[2]}\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "На данный момент нет участников в розыгрыше.")

def get_raffle_participants():
    conn = sqlite3.connect('rozigr_bd.sqlite')
    cur = conn.cursor()
    cur.execute("SELECT user_id, event_id, phone_number FROM rozigr_users")
    participants = cur.fetchall()
    cur.close()
    conn.close()
    return participants
        
bot.infinity_polling()