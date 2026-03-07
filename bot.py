import telebot
from telebot import types
import json
import os
import time

TOKEN = "8708884664:AAEBTT0XXXHdAu0titi59DGc7VTyUSNMpKA"
bot = telebot.TeleBot(TOKEN)

SUBJECTS = ["Русский язык", "Русская литература", "Белорусский язык", "Белорусская литература", "Математика", "Человек и мир"]

STUDENTS = [
    "Абрамчик Андрей", "Башура Тимофей", "Богдан Милана", "Бородько Артём", "Бурблис Анастасия",
    "Ватыль Полина", "Гончаревич Владислав", "Грицук Илья", "Грохольская Мила", "Жешко Егор",
    "Кравчук Милана", "Кривошей Константин", "Кухта Арсений", "Литвин Полина", "Лукашенко Арина",
    "Максимчик Матвей", "Мысливец Роман", "Назаренко Давид", "Ольховик Глеб", "Павлюковский Артём",
    "Райдюк Александр", "Русак Дарина", "Рябов Алексей", "Савоневич Арина", "Тесловский Артём",
    "Трипутько Михаил", "Цуприк Артур", "Чепко Арина", "Чиж София", "Юрса Давид", "Ясюлевич Алина"
]

grades = {}
parents = {}
pending = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📚 Предметы", "👨‍🎓 Ученики")
    markup.row("👪 Родители")
    bot.send_message(message.chat.id, "📚 Школьный журнал. Выберите действие:", reply_markup=markup)

@bot.message_handler(commands=['connect'])
def connect(message):
    msg = bot.send_message(message.chat.id, "Введите имя ученика (например: Абрамчик Андрей):")
    bot.register_next_step_handler(msg, process_connect)

def process_connect(message):
    name = message.text.strip()
    if name in STUDENTS:
        pending[message.from_user.id] = name
        bot.send_message(message.chat.id, f"✅ Запрос отправлен учителю для {name}")
    else:
        bot.send_message(message.chat.id, "❌ Ученик не найден. Проверьте имя.")

@bot.message_handler(func=lambda m: True)
def handle(message):
    if message.text == "📚 Предметы":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in SUBJECTS:
            markup.row(s)
        markup.row("🔙 Назад")
        bot.send_message(message.chat.id, "Выберите предмет:", reply_markup=markup)
    elif message.text in SUBJECTS:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in STUDENTS:
            markup.row(s)
        markup.row("🔙 Назад")
        bot.send_message(message.chat.id, f"Выберите ученика для {message.text}:", reply_markup=markup)
        bot.register_next_step_handler(message, lambda m: get_grades(m, message.text))
    elif message.text == "🔙 Назад":
        start(message)

def get_grades(message, subject):
    student = message.text
    if student == "🔙 Назад":
        start(message)
        return
    msg = bot.send_message(message.chat.id, f"Введите оценки для {student} по {subject} через запятую\nНапример: 5,6,7,8")
    bot.register_next_step_handler(msg, lambda m: save_grades(m, subject, student))

def save_grades(message, subject, student):
    try:
        nums = [int(x.strip()) for x in message.text.split(',')]
        avg = sum(nums) / len(nums)
        key = f"{student}_{subject}"
        grades[key] = nums
        bot.send_message(message.chat.id, f"✅ Оценки сохранены!\nСредний балл: {avg:.2f}", reply_markup=main_menu())
        # Уведомление родителю
        for uid, data in parents.items():
            if data == student:
                try:
                    bot.send_message(uid, f"🔔 Новая оценка!\n👤 {student}\n📚 {subject}\n➕ {nums[-1]}\nТеперь: {', '.join(map(str, nums))}\nСредний: {avg:.2f}")
                except:
                    pass
    except:
        bot.send_message(message.chat.id, "❌ Ошибка. Введите числа через запятую.", reply_markup=main_menu())

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📚 Предметы", "👨‍🎓 Ученики")
    markup.row("👪 Родители")
    return markup

if __name__ == "__main__":
    print("✅ Бот запущен")
    while True:
        try:
            bot.polling(non_stop=True)
        except:
            time.sleep(3)