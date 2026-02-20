import telebot
from telebot import types
import json
import os

TOKEN = '8220423257:AAFk0zQ35uNJXYHxzvVgudyb-_nzu4OsePU'
ADMIN_CHAT_ID = 1913203736

bot = telebot.TeleBot(TOKEN)

waiting_for_question = {}

# ---------- Загрузка базы из JSON ----------
def load_questions_db():
    json_path = os.path.join(os.path.dirname(__file__), 'questions.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл questions.json не найден! Будет использована пустая база.")
        return {}
    except json.JSONDecodeError:
        print("❌ Ошибка чтения JSON. Проверьте синтаксис файла.")
        return {}

questions_db = load_questions_db()
# -------------------------------------------

def get_topics_keyboard():
    """Инлайн-клавиатура со списком тем + кнопка 'Задать свой вопрос'."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for topic_id, topic_data in questions_db.items():
        button = types.InlineKeyboardButton(
            text=topic_data["name"],
            callback_data=f"topic_{topic_id}"
        )
        keyboard.add(button)
    # Добавляем кнопку для отправки вопроса разработчику
    ask_button = types.InlineKeyboardButton(
        text="✏️ Задать свой вопрос",
        callback_data="ask_question"
    )
    keyboard.add(ask_button)
    return keyboard

def get_questions_keyboard(topic_id):
    """Инлайн-клавиатура со списком вопросов для темы."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    topic = questions_db[topic_id]
    for question in topic["questions"]:
        button = types.InlineKeyboardButton(
            text=question["text"],
            callback_data=f"q_{topic_id}_{question['id']}"
        )
        keyboard.add(button)
    # Кнопка "Назад"
    back_button = types.InlineKeyboardButton(
        text="◀ Назад к темам",
        callback_data="back_to_topics"
    )
    keyboard.add(back_button)
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id in waiting_for_question:
        del waiting_for_question[chat_id]
    welcome_text = "👋 Привет! Я — бот-помогатор.\nВыберите интересующую вас тему:"
    bot.send_message(
        chat_id,
        welcome_text,
        reply_markup=get_topics_keyboard()
    )

@bot.message_handler(commands=['cancel'])
def cancel_input(message):
    chat_id = message.chat.id
    if waiting_for_question.get(chat_id):
        del waiting_for_question[chat_id]
        bot.send_message(
            chat_id,
            "❌ Ввод вопроса отменён.",
            reply_markup=get_topics_keyboard()
        )
    else:
        bot.send_message(chat_id, "Нет активного ввода вопроса.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    if waiting_for_question.get(chat_id):
        question_text = message.text.strip()
        if not question_text:
            bot.send_message(chat_id, "Пожалуйста, напишите ваш вопрос.")
            return

        user = message.from_user
        user_info = f"@{user.username}" if user.username else f"{user.first_name} (id: {user.id})"
        full_info = f"✉️ Новый вопрос от {user_info}:\n\n{question_text}"

        try:
            bot.send_message(ADMIN_CHAT_ID, full_info)
        except Exception as e:
            print(f"Не удалось отправить сообщение: {e}")

        bot.send_message(
            chat_id,
            "✅ Спасибо! Ваш вопрос передан разработчику. Он будет рассмотрен и, возможно, добавлен в базу.",
            reply_markup=get_topics_keyboard()
        )
        del waiting_for_question[chat_id]
    else:
        # Можно добавить ответ на любые другие сообщения
        pass

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if waiting_for_question.get(chat_id) and call.data != "ask_question":
        bot.answer_callback_query(
            call.id,
            "Сначала завершите ввод вопроса (отправьте /cancel для отмены).",
            show_alert=True
        )
        return

    if call.data.startswith("topic_"):
        topic_id = call.data.replace("topic_", "")
        topic = questions_db.get(topic_id)
        if not topic:
            bot.answer_callback_query(call.id, "❌ Тема не найдена!")
            return

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"Вы выбрали тему: {topic['name']}\n\nВыберите вопрос:",
            reply_markup=get_questions_keyboard(topic_id)
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("q_"):
        parts = call.data.split("_", 2)
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "❌ Некорректный запрос")
            return
        _, topic_id, question_id = parts
        topic = questions_db.get(topic_id)
        if not topic:
            bot.answer_callback_query(call.id, "❌ Тема не найдена!")
            return

        question_obj = next((q for q in topic["questions"] if q["id"] == question_id), None)
        if not question_obj:
            bot.answer_callback_query(call.id, "❌ Вопрос не найден!")
            return

        bot.send_message(
            chat_id,
            f"❓ *{question_obj['text']}*\n\n💬 {question_obj['answer']}",
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀ К вопросам", callback_data=f"topic_{topic_id}")
            )
        )
        bot.answer_callback_query(call.id)

    elif call.data == "back_to_topics":
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="Выберите интересующую вас тему:",
            reply_markup=get_topics_keyboard()
        )
        bot.answer_callback_query(call.id)

    elif call.data == "ask_question":
        waiting_for_question[chat_id] = True
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✏️ Напишите ваш вопрос простым текстом.\n\n"
                 "Я передам его разработчику. Чтобы отменить, отправьте /cancel.",
            reply_markup=None
        )
        bot.answer_callback_query(call.id)

    else:
        bot.answer_callback_query(call.id, "❓ Неизвестная команда")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()