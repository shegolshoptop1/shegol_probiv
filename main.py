import json
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '8021838868:AAG6LItOBlTDCBeYPtIAu5ISJjZMmpYZmCw'
bot = telebot.TeleBot(TOKEN)

user_states = {}
fields = ['ФИО', 'Телефон', 'Тег', 'Адрес', 'Учебное заведение', 'Другое']

# 🔘 Главное меню
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('/newpost'), KeyboardButton('/search'), KeyboardButton('/start'))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет, щегол! Выбери действие:", reply_markup=main_menu())

@bot.message_handler(commands=['newpost'])
def newpost(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'data': {field: None for field in fields}, 'step': None}
    send_form(chat_id)

def send_form(chat_id):
    data = user_states[chat_id]['data']
    text = "✍️ Введите информацию о пользователе:\n\n"
    for i, field in enumerate(fields, start=1):
        value = data[field] or "❌"
        text += f"{i}. {field}: {value}\n"

    markup = InlineKeyboardMarkup()
    for i in range(len(fields)):
        markup.add(InlineKeyboardButton(f"✏️ {i+1}", callback_data=f"edit_{i}"))
    if all(data.values()):
        markup.add(InlineKeyboardButton("✅ Готово", callback_data="save"))
    markup.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_') or call.data in ['save', 'cancel'])
def handle_callback(call):
    chat_id = call.message.chat.id
    if call.data.startswith('edit_'):
        index = int(call.data.split('_')[1])
        field = fields[index]
        user_states[chat_id]['step'] = field
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        cancel_markup.add(KeyboardButton("❌ Отмена"))
        bot.send_message(chat_id, f"Введите значение для {field}:", reply_markup=cancel_markup)
    elif call.data == 'save':
        save_data(chat_id)
        bot.send_message(chat_id, "✅ Данные сохранены!", reply_markup=main_menu())
        user_states.pop(chat_id)
    elif call.data == 'cancel':
        bot.send_message(chat_id, "🚫 Ввод отменён.", reply_markup=main_menu())
        user_states.pop(chat_id, None)

def save_data(chat_id):
    data = user_states[chat_id]['data']
    try:
        with open('db.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
    except:
        db = []
    db.append(data)
    with open('db.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

@bot.message_handler(func=lambda m: m.chat.id in user_states and user_states[m.chat.id]['step'])
def handle_input(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if text.lower() == "отмена" or text == "❌ Отмена":
        bot.send_message(chat_id, "🚫 Ввод отменён.", reply_markup=main_menu())
        user_states.pop(chat_id, None)
        return

    step = user_states[chat_id]['step']
    user_states[chat_id]['data'][step] = text
    user_states[chat_id]['step'] = None
    send_form(chat_id)

@bot.message_handler(commands=['search'])
def ask_search(message):
    bot.send_message(message.chat.id, "🔍 Введите запрос (ФИО, тег, номер, адрес и т.д.):", reply_markup=main_menu())

@bot.message_handler(func=lambda message: True and message.text != "❌ Отмена")
def search(message):
    query = message.text.strip().lower()
    try:
        with open('db.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
    except:
        db = []

    results = [entry for entry in db if any(query in str(value).lower() for value in entry.values())]
    if not results:
        bot.send_message(message.chat.id, "❌ Ничего не найдено.")
        return

    for entry in results:
        preview = f"👤 {entry.get('ФИО', '-')}, {entry.get('Тег', '-')}, 📍 {entry.get('Адрес', '-')}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📖 Читать", callback_data=f"show_{db.index(entry)}"))
        bot.send_message(message.chat.id, preview, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_'))
def show_full(call):
    index = int(call.data.split('_')[1])
    try:
        with open('db.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        entry = db[index]
        full_text = "\n".join([f"{k}: {v}" for k, v in entry.items()])
        bot.send_message(call.message.chat.id, f"📘 Полная информация:\n\n{full_text}", reply_markup=main_menu())
    except:
        bot.send_message(call.message.chat.id, "⚠️ Ошибка при открытии данных.")
    bot.answer_callback_query(call.id)

bot.infinity_polling()
