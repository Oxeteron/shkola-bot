import telebot
from telebot import types
import json
import os
import time

TOKEN = "8708884664:AAEBTT0XXXHdAu0titi59DGc7VTyUSNMpKA"
bot = telebot.TeleBot(TOKEN)

# Предметы
SUBJECTS = ["Русский язык", "Русская литература", "Белорусский язык", "Белорусская литература", "Математика", "Человек и мир"]

# Ученики
STUDENTS = [
    "Абрамчик Андрей", "Башура Тимофей", "Богдан Милана", "Бородько Артём", "Бурблис Анастасия",
    "Ватыль Полина", "Гончаревич Владислав", "Грицук Илья", "Грохольская Мила", "Жешко Егор",
    "Кравчук Милана", "Кривошей Константин", "Кухта Арсений", "Литвин Полина", "Лукашенко Арина",
    "Максимчик Матвей", "Мысливец Роман", "Назаренко Давид", "Ольховик Глеб", "Павлюковский Артём",
    "Райдюк Александр", "Русак Дарина", "Рябов Алексей", "Савоневич Арина", "Тесловский Артём",
    "Трипутько Михаил", "Цуприк Артур", "Чепко Арина", "Чиж София", "Юрса Давид", "Ясюлевич Алина"
]

# Данные
grades = {}
parents = {}
pending = {}
teacher_id = None

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start(message):
    global teacher_id
    user_id = message.from_user.id
    
    # Первый, кто запустил бота — учитель
    if teacher_id is None:
        teacher_id = user_id
        bot.send_message(
            message.chat.id,
            "✅ Вы назначены учителем. Используйте меню для управления.",
            reply_markup=teacher_menu()
        )
        return
    
    # Если это учитель
    if user_id == teacher_id:
        bot.send_message(
            message.chat.id,
            "👨‍🏫 Панель учителя:",
            reply_markup=teacher_menu()
        )
        return
    
    # Если это родитель
    if user_id in parents:
        # Уже привязан — показываем оценки
        show_parent_grades(message, user_id)
    else:
        # Не привязан — просто текст, кнопок нет
        bot.send_message(
            message.chat.id,
            "👪 Чтобы подключиться к ребёнку, отправьте команду:\n"
            "/connect Имя Фамилия\n\n"
            "Например: /connect Абрамчик Андрей"
        )

# ================== МЕНЮ УЧИТЕЛЯ ==================
def teacher_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📚 Предметы", "👨‍🎓 Ученики")
    markup.row("👪 Запросы", "📋 Родители")
    return markup

@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text == "📚 Предметы")
def teacher_subjects(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for s in SUBJECTS:
        markup.row(s)
    markup.row("🔙 Назад")
    bot.send_message(message.chat.id, "Выберите предмет:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text in SUBJECTS)
def teacher_students(message):
    subject = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for s in STUDENTS:
        markup.row(s)
    markup.row("🔙 Назад")
    msg = bot.send_message(message.chat.id, f"Выберите ученика для {subject}:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: enter_grade(m, subject))

def enter_grade(message, subject):
    if message.text == "🔙 Назад":
        bot.send_message(message.chat.id, "Панель учителя:", reply_markup=teacher_menu())
        return
    
    student = message.text
    if student not in STUDENTS:
        bot.send_message(message.chat.id, "❌ Ошибка", reply_markup=teacher_menu())
        return
    
    msg = bot.send_message(message.chat.id, f"Введите оценки через запятую\nНапример: 5,6,7,8")
    bot.register_next_step_handler(msg, lambda m: save_grade(m, subject, student))

def save_grade(message, subject, student):
    try:
        nums = [int(x.strip()) for x in message.text.split(',')]
        avg = sum(nums) / len(nums)
        key = f"{student}_{subject}"
        grades[key] = nums
        
        bot.send_message(message.chat.id, f"✅ Сохранено!\nСредний: {avg:.2f}", reply_markup=teacher_menu())
        
        # Уведомляем родителя
        for parent_id, child in parents.items():
            if child == student:
                try:
                    marks = ', '.join(map(str, nums))
                    bot.send_message(
                        parent_id,
                        f"🔔 Новая оценка!\n👤 {student}\n📚 {subject}\n➕ {nums[-1]}\n"
                        f"Теперь: {marks}\nСредний: {avg:.2f}"
                    )
                except:
                    pass
    except:
        bot.send_message(message.chat.id, "❌ Ошибка. Введите числа через запятую", reply_markup=teacher_menu())

@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text == "👪 Запросы")
def show_requests(message):
    if not pending:
        bot.send_message(message.chat.id, "Нет ожидающих запросов")
        return
    
    for parent_id, student in list(pending.items()):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{parent_id}"),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{parent_id}")
        )
        bot.send_message(message.chat.id, f"Запрос от @{parent_id} для {student}", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text == "📋 Родители")
def show_parents_list(message):
    if not parents:
        bot.send_message(message.chat.id, "Нет привязанных родителей")
        return
    
    text = "📋 Привязанные родители:\n"
    for parent_id, student in parents.items():
        text += f"@{parent_id} → {student}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text == "🔙 Назад")
def teacher_back(message):
    bot.send_message(message.chat.id, "Панель учителя:", reply_markup=teacher_menu())

# ================== ОБРАБОТКА ЗАПРОСОВ (для учителя) ==================
@bot.callback_query_handler(func=lambda call: call.from_user.id == teacher_id)
def handle_callbacks(call):
    data = call.data
    if data.startswith("approve_"):
        parent_id = int(data.split("_")[1])
        student = pending.pop(parent_id, None)
        if student:
            parents[parent_id] = student
            bot.send_message(call.message.chat.id, f"✅ Родитель привязан к {student}")
            try:
                # Отправляем родителю приветствие с оценками
                bot.send_message(
                    parent_id,
                    f"✅ Вы привязаны к {student}. Теперь вы будете получать уведомления и видеть оценки."
                )
                # Сразу показываем оценки
                show_parent_grades(call.message, parent_id)
            except:
                pass
    
    elif data.startswith("reject_"):
        parent_id = int(data.split("_")[1])
        pending.pop(parent_id, None)
        bot.send_message(call.message.chat.id, "❌ Запрос отклонён")
        try:
            bot.send_message(parent_id, "❌ Запрос отклонён. Проверьте имя или свяжитесь с учителем.")
        except:
            pass

# ================== РОДИТЕЛИ ==================
@bot.message_handler(commands=['connect'])
def connect_request(message):
    user_id = message.from_user.id
    
    # Учитель не может подключиться как родитель
    if user_id == teacher_id:
        bot.send_message(message.chat.id, "❌ Вы учитель")
        return
    
    # Если уже привязан
    if user_id in parents:
        bot.send_message(message.chat.id, "❌ Вы уже привязаны к ребёнку")
        return
    
    try:
        student = message.text.replace('/connect', '').strip()
        if not student or student not in STUDENTS:
            bot.send_message(
                message.chat.id,
                "❌ Ошибка. Используйте: /connect Имя Фамилия\n"
                "Например: /connect Абрамчик Андрей"
            )
            return
        
        pending[user_id] = student
        bot.send_message(message.chat.id, f"✅ Запрос для {student} отправлен учителю")
        
        if teacher_id:
            try:
                bot.send_message(teacher_id, f"🔔 Новый запрос от @{user_id} для {student}")
            except:
                pass
    except:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка. Используйте: /connect Имя Фамилия"
        )

def show_parent_grades(message, user_id):
    student = parents.get(user_id)
    if not student:
        return
    
    text = f"👤 {student}\n\n"
    has_grades = False
    
    for subject in SUBJECTS:
        key = f"{student}_{subject}"
        marks = grades.get(key, [])
        if marks:
            has_grades = True
            avg = sum(marks) / len(marks)
            text += f"📚 {subject}\n"
            text += f"{', '.join(map(str, marks))}\n"
            text += f"Средний: {avg:.2f}\n\n"
        else:
            text += f"📚 {subject}\nНет оценок\n\n"
    
    if not has_grades:
        text += "Пока нет оценок. Как только появятся — вы получите уведомление."
    
    bot.send_message(message.chat.id, text)

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    print("✅ Бот запущен с правильным разделением")
    while True:
        try:
            bot.polling(non_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(3)
