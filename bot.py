import telebot
from telebot import types
import time
from datetime import datetime, timedelta

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
    bot.register_next_step_handler(msg, lambda m: choose_mode(m, subject))

# ================== ВЫБОР РЕЖИМА ==================
def choose_mode(message, subject):
    if message.text == "🔙 Назад":
        bot.send_message(message.chat.id, "Панель учителя:", reply_markup=teacher_menu())
        return

    student = message.text
    if student not in STUDENTS:
        bot.send_message(message.chat.id, "❌ Ошибка", reply_markup=teacher_menu())
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 Ввести все оценки", "➕ Добавить одну оценку")
    markup.row("🔙 Назад")
    msg = bot.send_message(message.chat.id, f"👤 {student}\n📚 {subject}\nВыберите режим:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_mode(m, subject, student))

def process_mode(message, subject, student):
    if message.text == "🔙 Назад":
        bot.send_message(message.chat.id, "Панель учителя:", reply_markup=teacher_menu())
        return

    if message.text == "📝 Ввести все оценки":
        msg = bot.send_message(message.chat.id, "Введите все оценки через запятую\n(например: 5,6,7,8):")
        bot.register_next_step_handler(msg, lambda m: save_all_grades(m, subject, student))

    elif message.text == "➕ Добавить одну оценку":
        msg = bot.send_message(message.chat.id, "Введите одну новую оценку (например: 7):")
        bot.register_next_step_handler(msg, lambda m: add_one_grade(m, subject, student))

# ================== СОХРАНИТЬ ВСЕ ОЦЕНКИ (БЕЗ УВЕДОМЛЕНИЙ) ==================
def save_all_grades(message, subject, student):
    try:
        nums = [int(x.strip()) for x in message.text.split(',')]
        avg = sum(nums) / len(nums)
        grades[f"{student}_{subject}"] = nums
        bot.send_message(message.chat.id, f"✅ Сохранено. Средний: {avg:.2f}", reply_markup=teacher_menu())
        # Уведомлений НЕТ
    except:
        bot.send_message(message.chat.id, "❌ Ошибка. Введите числа через запятую", reply_markup=teacher_menu())

# ================== ДОБАВИТЬ ОДНУ ОЦЕНКУ (С УВЕДОМЛЕНИЕМ) ==================
def add_one_grade(message, subject, student):
    try:
        new = int(message.text.strip())
        key = f"{student}_{subject}"
        current = grades.get(key, [])
        current.append(new)
        grades[key] = current
        avg = sum(current) / len(current)
        # Правильное время для Беларуси (UTC+3)
        now = (datetime.now() + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")
        bot.send_message(message.chat.id, f"✅ Оценка {new} добавлена\nТеперь: {', '.join(map(str, current))}\nСредний: {avg:.2f}", reply_markup=teacher_menu())

        for pid, child in parents.items():
            if child == student:
                try:
                    bot.send_message(pid, 
                        f"🔔 Новая оценка\n\n"
                        f"👤 {student}\n"
                        f"📚 {subject}\n\n"
                        f"➕ Оценка: {new}\n"
                        f"📊 Средний балл: {avg:.2f}\n\n"
                        f"Теперь оценки по предмету:\n"
                        f"{', '.join(map(str, current))}\n\n"
                        f"🕒 {now}"
                    )
                except:
                    pass
    except:
        bot.send_message(message.chat.id, "❌ Ошибка. Введите одно число", reply_markup=teacher_menu())

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
        bot.send_message(message.chat.id, f"Запрос от {get_user_link(pid)} для {student}", reply_markup=markup, parse_mode="HTML")

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
                text=f"✅ {get_user_link(pid)} привязан к {student}",
                parse_mode="HTML"
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
            text=f"❌ Запрос от {get_user_link(pid)} отклонён",
            parse_mode="HTML"
        )
        try:
            bot.send_message(pid, "❌ Запрос отклонён")
        except:
            pass

# ================== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ==================
def get_user_link(user_id):
    try:
        chat = bot.get_chat(user_id)
        if chat.username:
            return f"@{chat.username}"
        else:
            return f"<a href='tg://user?id={user_id}'>пользователь</a>"
    except:
        return f"ID: {user_id}"

# ================== РОДИТЕЛИ (ТОЛЬКО СПИСОК) ==================
@bot.message_handler(func=lambda m: m.from_user.id == teacher_id and m.text == "📋 Родители")
def list_parents(message):
    if not parents:
        bot.send_message(message.chat.id, "Нет привязанных родителей")
        return

    text = "📋 Список родителей:\n\n"
    for pid, student in parents.items():
        user_link = get_user_link(pid)
        text += f"{user_link} → {student}\n"
    text += "\n❌ Чтобы отвязать, напишите:\n/unlink @username"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ================== КОМАНДА ДЛЯ ОТВЯЗЫВАНИЯ ==================
@bot.message_handler(commands=['unlink'])
def unlink_by_username(message):
    if message.from_user.id != teacher_id:
        return

    try:
        username = message.text.split()[1].replace('@', '')
        found = False
        for pid, student in list(parents.items()):
            try:
                chat = bot.get_chat(pid)
                if chat.username and chat.username.lower() == username.lower():
                    parents.pop(pid)
                    bot.send_message(message.chat.id, f"❌ Родитель @{username} отвязан от {student}")
                    try:
                        bot.send_message(pid, "❌ Вы отвязаны от ученика. Свяжитесь с учителем.")
                    except:
                        pass
                    found = True
                    break
            except:
                continue
        if not found:
            bot.send_message(message.chat.id, "❌ Родитель с таким username не найден")
    except:
        bot.send_message(message.chat.id, "❌ Используйте: /unlink @username")

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
            bot.send_message(teacher_id, f"🔔 Запрос от {get_user_link(message.from_user.id)} для {name}", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка. Используйте: /connect Имя Фамилия")

@bot.message_handler(func=lambda m: True)
def back(message):
    if message.from_user.id == teacher_id:
        bot.send_message(message.chat.id, "Панель учителя:", reply_markup=teacher_menu())
    elif message.from_user.id in parents:
        bot.send_message(message.chat.id, f"👤 {parents[message.from_user.id]}", reply_markup=parent_menu())

if __name__ == "__main__":
    print("✅ Бот запущен. Время правильное (UTC+3).")
    while True:
        try:
            bot.polling(non_stop=True)
        except:
            time.sleep(3)
