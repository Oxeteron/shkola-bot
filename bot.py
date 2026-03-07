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
teacher_id = None

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start(message):
    global teacher_id
    user_id = message.from_user.id

    if teacher_id is None:
        teacher_id = user_id
        bot.send_message(message.chat.id, "✅ Вы учитель", reply_markup=teacher_menu())
        return

    if user_id == teacher_id:
        bot.send_message(message.chat.id, "👨‍🏫 Панель учителя", reply_markup=teacher_menu())
        return

    if user_id in parents:
        bot.send_message(message.chat.id, f"👤 {parents[user_id]}\nВыберите предмет:", reply_markup=parent_menu())
    else:
        bot.send_message(message.chat.id, "👪 Отправьте /connect Имя Фамилия")

# ================== МЕНЮ УЧИТЕЛЯ ==================
def teacher_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📚 Предметы", "👨‍🎓 Ученики")
    markup.row("👪 Запросы", "📋 Родители")
    return markup

# ================== УЧЕНИКИ ==================
@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text == "👨‍🎓 Ученики")
def show_students_list(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for s in STUDENTS:
        markup.row(s)
    markup.row("🔙 Назад")
    msg = bot.send_message(message.chat.id, "Выберите ученика:", reply_markup=markup)
    bot.register_next_step_handler(msg, show_student_grades)

def show_student_grades(message):
    if message.text == "🔙 Назад":
        bot.send_message(message.chat.id, "Панель учителя:", reply_markup=teacher_menu())
        return

    student = message.text
    if student not in STUDENTS:
        bot.send_message(message.chat.id, "❌ Ошибка", reply_markup=teacher_menu())
        return

    text = f"👤 {student}\n\n"
    has = False
    for subj in SUBJECTS:
        marks = grades.get(f"{student}_{subj}", [])
        if marks:
            has = True
            avg = sum(marks) / len(marks)
            text += f"📚 {subj}\n{', '.join(map(str, marks))}\nСредний: {avg:.2f}\n\n"
        else:
            text += f"📚 {subj}\nНет оценок\n\n"
    if not has:
        text += "Нет оценок."
    bot.send_message(message.chat.id, text, reply_markup=teacher_menu())

# ================== ПРЕДМЕТЫ ==================
@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text == "📚 Предметы")
def teacher_subjects(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for s in SUBJECTS:
        markup.row(s)
    markup.row("🔙 Назад")
    bot.send_message(message.chat.id, "Выберите предмет:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text in SUBJECTS)
def teacher_pick_student(message):
    subject = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for s in STUDENTS:
        markup.row(s)
    markup.row("🔙 Назад")
    msg = bot.send_message(message.chat.id, f"Выберите ученика для {subject}:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: get_grade_input(m, subject))

def get_grade_input(message, subject):
    if message.text == "🔙 Назад":
        bot.send_message(message.chat.id, "Панель учителя:", reply_markup=teacher_menu())
        return
    student = message.text
    if student not in STUDENTS:
        bot.send_message(message.chat.id, "❌ Ошибка", reply_markup=teacher_menu())
        return
    msg = bot.send_message(message.chat.id, "Введите оценки через запятую (например: 5,6,7):")
    bot.register_next_step_handler(msg, lambda m: save_grades(m, subject, student))

def save_grades(message, subject, student):
    try:
        nums = [int(x.strip()) for x in message.text.split(',')]
        avg = sum(nums) / len(nums)
        grades[f"{student}_{subject}"] = nums
        bot.send_message(message.chat.id, f"✅ Сохранено. Средний: {avg:.2f}", reply_markup=teacher_menu())

        for pid, child in parents.items():
            if child == student:
                try:
                    bot.send_message(pid, f"🔔 Новая оценка по {subject}: {nums[-1]}\nСредний: {avg:.2f}")
                except:
                    pass
    except:
        bot.send_message(message.chat.id, "❌ Ошибка", reply_markup=teacher_menu())

# ================== ЗАПРОСЫ ==================
@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text == "👪 Запросы")
def show_pending(message):
    if not pending:
        bot.send_message(message.chat.id, "Нет запросов")
        return
    for pid, student in pending.items():
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅", callback_data=f"app_{pid}"),
            types.InlineKeyboardButton("❌", callback_data=f"rej_{pid}")
        )
        bot.send_message(message.chat.id, f"@{pid} → {student}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.from_user.id == teacher_id)
def handle_approve(call):
    data = call.data
    if data.startswith("app_"):
        pid = int(data.split("_")[1])
        student = pending.pop(pid, None)
        if student:
            parents[pid] = student
            bot.answer_callback_query(call.id, "✅ Привязан")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ @{pid} привязан к {student}"
            )
            try:
                bot.send_message(pid, f"✅ Вы привязаны к {student}", reply_markup=parent_menu())
            except:
                pass
    elif data.startswith("rej_"):
        pid = int(data.split("_")[1])
        pending.pop(pid, None)
        bot.answer_callback_query(call.id, "❌ Отклонён")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"❌ Запрос от @{pid} отклонён"
        )
        try:
            bot.send_message(pid, "❌ Запрос отклонён")
        except:
            pass

# ================== РОДИТЕЛИ (ОТВЯЗЫВАНИЕ) ==================
@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text == "📋 Родители")
def list_parents(message):
    if not parents:
        bot.send_message(message.chat.id, "Нет привязанных родителей")
        return

    for pid, student in list(parents.items()):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отвязать", callback_data=f"unlink_{pid}"))
        bot.send_message(message.chat.id, f"@{pid} → {student}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.from_user.id == teacher_id and call.data.startswith("unlink_"))
def unlink_parent(call):
    pid = int(call.data.split("_")[1])
    student = parents.pop(pid, None)
    if student:
        bot.answer_callback_query(call.id, "✅ Родитель отвязан")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"❌ Родитель @{pid} отвязан от {student}"
        )
        try:
            bot.send_message(pid, "❌ Вы отвязаны от ученика. Свяжитесь с учителем.")
        except:
            pass

# ================== РОДИТЕЛИ (ПРОСМОТР) ==================
def parent_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for s in SUBJECTS:
        markup.row(s)
    return markup

@bot.message_handler(func=lambda m: m.from_user.id in parents and m.text in SUBJECTS)
def parent_show_grades(message):
    student = parents[message.from_user.id]
    marks = grades.get(f"{student}_{message.text}", [])
    if marks:
        avg = sum(marks) / len(marks)
        bot.send_message(message.chat.id, f"📚 {message.text}\n{', '.join(map(str, marks))}\nСредний: {avg:.2f}")
    else:
        bot.send_message(message.chat.id, f"По {message.text} пока нет оценок")

@bot.message_handler(commands=['connect'])
def connect_request(message):
    if message.from_user.id == teacher_id:
        bot.send_message(message.chat.id, "❌ Вы учитель")
        return
    if message.from_user.id in parents:
        bot.send_message(message.chat.id, "❌ Уже привязаны")
        return
    try:
        name = message.text.replace('/connect', '').strip()
        if name not in STUDENTS:
            bot.send_message(message.chat.id, "❌ Ученик не найден. Пример: /connect Абрамчик Андрей")
            return
        pending[message.from_user.id] = name
        bot.send_message(message.chat.id, f"✅ Запрос для {name} отправлен учителю")
        if teacher_id:
            bot.send_message(teacher_id, f"🔔 Запрос от @{message.from_user.id} для {name}")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка. Используйте: /connect Имя Фамилия")

@bot.message_handler(func=lambda m: True)
def back(message):
    if message.from_user.id == teacher_id:
        bot.send_message(message.chat.id, "Панель учителя:", reply_markup=teacher_menu())
    elif message.from_user.id in parents:
        bot.send_message(message.chat.id, f"👤 {parents[message.from_user.id]}", reply_markup=parent_menu())

if __name__ == "__main__":
    print("✅ Бот запущен. Ученики работают. Отвязывание работает.")
    while True:
        try:
            bot.polling(non_stop=True)
        except:
            time.sleep(3)
