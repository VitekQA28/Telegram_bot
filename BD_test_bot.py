import telebot
import sqlite3
from telebot import types

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

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtn1 = types.KeyboardButton('Регистрация')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtn2 = types.KeyboardButton('Забыли пароль?')
    itembtn3 = types.KeyboardButton('Авторизоваться')
    markup.add(itembtn3)
    markup.add(itembtn1)
    markup.add(itembtn2)
    bot.send_message(message.chat.id, 'Привет, для регистрации нажми на кнопку "Регистрация"', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Регистрация')
def reg(message):
    bot.send_message(message.chat.id, 'Сейчас тебя зарегистрируем! Введите ваше имя')
    bot.register_next_step_handler(message, user_name)
 
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

    '''
    #Добавляем функциональную кнопку "Список пользователей"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Список пользователей', callback_data='users'))
    #bot.send_message(message.chat.id, 'Пользователь зарегистрирован', reply_markup=markup)
    '''
#Функция для вывода информации после нажатия на кнопку "Список пользователей"
@bot.callback_query_handler(func=lambda call: True) 
def callback(call):
    conn = sqlite3.connect('BD_users.sql') 
    cur = conn.cursor()
    cur.execute("SELECT * FROM users") #Отправляем запрос в таблицу
    users = cur.fetchall() #Возвращает все записанные данные в базу данных

    info = '' 
    for el in users:
        info += f'Имя: {el[1]}, пароль: {el[2]}\n'
    
    cur.close() 
    conn.close() 
    #Выводим в чат информацию о пользоваетлях
    bot.send_message(call.message.chat.id, info) 
'''
@bot.message_handler(func=lambda message: message.text == 'Забыли пароль?')
def ask_for_username(message):
    bot.send_message(message.chat.id, "Введите имя пользователя:")
    bot.register_next_step_handler(message, get_password)
'''
#Запрашиваем пороль по имени
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


# Запускаем бота. Он будет работать до тех пор, пока работает ячейка
# (крутится значок слева).
# Остановим ячейку - остановится бот
bot.infinity_polling()
