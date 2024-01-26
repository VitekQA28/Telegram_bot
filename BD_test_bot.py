import telebot
import sqlite3

# Здесь нужно вставить токен, который дал BotFather при регистрации
# Пример: token = '2007628239:AAEF4ZVqLiRKG7j49EC4vaRwXjJ6DN6xng8'
token = '6741558043:AAEmwdMZ6FTEKn2UBp7TLw0iEaEqXhSjAUg'  # <<< Ваш токен

# В этой строчке мы заводим бота и даем ему запомнить токен
bot = telebot.TeleBot(token)
name = None

# Пишем первую функцию, которая отвечает "Привет" на команду /start
# Все функции общения приложения с ТГ спрятаны в функции под @
@bot.message_handler(commands=['start'])
def main(message):
    conn = sqlite3.connect('BD_users.sql') #Создаем файл с БД в формате sql
    cur = conn.cursor()
    #Создаём таблицу в БД, если её еще нет, и в ней будут следующие поля id, name, pass.
    cur.execute('CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(50), pass varchar(50))')
    conn.commit() #Синхронизируем комманду с файлом
    cur.close() 
    conn.close() #Закрываем соединение с базой данных

    bot.send_message(message.chat.id, 'Привет, сейчас тебя зарегистрируем! Введите ваше имя')
    bot.register_next_step_handler(message, user_name)

def user_name(message):
    global name
    name = message.text.strip()
    bot.send_message(message.chat.id, 'Введите пароль')
    bot.register_next_step_handler(message, user_pass)

def user_pass(message):
    password = message.text.strip()

    conn = sqlite3.connect('BD_users.sql') 
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, pass) VALUES (?, ?)", (name, password))
    conn.commit() 
    cur.close() 
    conn.close() 

    #Добавляем функциональную кнопку "Список пользователей"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Список пользователей', callback_data='users'))
    bot.send_message(message.chat.id, 'Пользователь зарегистрирован', reply_markup=markup)

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

# Запускаем бота. Он будет работать до тех пор, пока работает ячейка
# (крутится значок слева).
# Остановим ячейку - остановится бот
bot.infinity_polling()
