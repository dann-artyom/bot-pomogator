import telebot
from telebot import types
import json
import os

TOKEN = '8220423257:AAFk0zQ35uNJXYHxzvVgudyb-_nzu4OsePU'
ADMIN_CHAT_ID = 1913203736

bot = telebot.TeleBot(TOKEN)

waiting_for_question = {}   # состояние ожидания вопроса
user_lang = {}              # язык пользователя: 'ru' или 'en' (по умолчанию 'ru')

# ---------- Переводы ----------
TEXTS = {
    'ru': {
        'welcome': "👋 Привет! Я — бот-помогатор.\nВыберите интересующую вас тему:",
        'choose_topic': "Выберите интересующую вас тему:",
        'topic_chosen': "Вы выбрали тему: {name}\n\nВыберите вопрос:",
        'back_to_topics': "◀ Назад к темам",
        'ask_question': "✏️ Задать свой вопрос",
        'language': "🌐 Язык / Language",
        'choose_language': "Выберите язык:",
        'russian': "Русский",
        'english': "English",
        'language_changed': "Язык изменён на русский.",
        'enter_question': "✏️ Напишите ваш вопрос простым текстом.\n\nЯ передам его разработчику. Чтобы отменить, отправьте /cancel.",
        'question_sent': "✅ Спасибо! Ваш вопрос передан разработчику. Он будет рассмотрен и, возможно, добавлен в базу.",
        'cancel': "❌ Ввод вопроса отменён.",
        'no_active_input': "Нет активного ввода вопроса.",
        'invalid_request': "❌ Некорректный запрос",
        'topic_not_found': "❌ Тема не найдена!",
        'question_not_found': "❌ Вопрос не найден!",
        'unknown_command': "❓ Неизвестная команда",
        'finish_input_first': "Сначала завершите ввод вопроса (отправьте /cancel для отмены).",
        'please_write_question': "Пожалуйста, напишите ваш вопрос.",
        'back_to_questions': "◀ К вопросам",
    },
    'en': {
        'welcome': "👋 Hello! I'm a helper bot.\nChoose a topic:",
        'choose_topic': "Choose a topic:",
        'topic_chosen': "You selected: {name}\n\nChoose a question:",
        'back_to_topics': "◀ Back to topics",
        'ask_question': "✏️ Ask your question",
        'language': "🌐 Language",
        'choose_language': "Choose language:",
        'russian': "Russian",
        'english': "English",
        'language_changed': "Language changed to English.",
        'enter_question': "✏️ Write your question in plain text.\n\nI will forward it to the developer. To cancel, send /cancel.",
        'question_sent': "✅ Thank you! Your question has been sent to the developer. It will be reviewed and possibly added to the database.",
        'cancel': "❌ Question input cancelled.",
        'no_active_input': "No active question input.",
        'invalid_request': "❌ Invalid request",
        'topic_not_found': "❌ Topic not found!",
        'question_not_found': "❌ Question not found!",
        'unknown_command': "❓ Unknown command",
        'finish_input_first': "Please finish entering your question first (send /cancel to cancel).",
        'please_write_question': "Please write your question.",
        'back_to_questions': "◀ Back to questions",
    }
}

def get_text(user_id, key, **kwargs):
    """Возвращает перевод для указанного ключа и пользователя."""
    lang = user_lang.get(user_id, 'ru')
    text = TEXTS[lang].get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text

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

def get_question_text(question_obj, lang):
    """Возвращает текст вопроса в зависимости от языка: если есть text_en и язык en, то его, иначе text."""
    if lang == 'en' and 'text_en' in question_obj:
        return question_obj['text_en']
    return question_obj['text']

def get_answer_text(question_obj, lang):
    """Возвращает ответ в зависимости от языка: если есть answer_en и язык en, то его, иначе answer."""
    if lang == 'en' and 'answer_en' in question_obj:
        return question_obj['answer_en']
    return question_obj['answer']

def get_topics_keyboard(chat_id):
    """Инлайн-клавиатура со списком тем + кнопки 'Задать вопрос' и 'Язык'."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    lang = user_lang.get(chat_id, 'ru')
    for topic_id, topic_data in questions_db.items():
        # Выбираем название темы в зависимости от языка
        topic_name = topic_data.get(f"name_{lang}", topic_data.get("name_ru", topic_id))
        button = types.InlineKeyboardButton(
            text=topic_name,
            callback_data=f"topic_{topic_id}"
        )
        keyboard.add(button)
    # Кнопка "Задать свой вопрос"
    ask_button = types.InlineKeyboardButton(
        text=get_text(chat_id, 'ask_question'),
        callback_data="ask_question"
    )
    keyboard.add(ask_button)
    # Кнопка выбора языка
    lang_button = types.InlineKeyboardButton(
        text=get_text(chat_id, 'language'),
        callback_data="choose_lang"
    )
    keyboard.add(lang_button)
    return keyboard

def get_questions_keyboard(chat_id, topic_id):
    """Инлайн-клавиатура со списком вопросов для темы. Текст вопроса показывается на выбранном языке."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    topic = questions_db[topic_id]
    lang = user_lang.get(chat_id, 'ru')
    for question in topic["questions"]:
        # Показываем текст вопроса на нужном языке (для кнопки)
        button_text = get_question_text(question, lang)
        button = types.InlineKeyboardButton(
            text=button_text,
            callback_data=f"q_{topic_id}_{question['id']}"
        )
        keyboard.add(button)
    # Кнопка "Назад к темам"
    back_button = types.InlineKeyboardButton(
        text=get_text(chat_id, 'back_to_topics'),
        callback_data="back_to_topics"
    )
    keyboard.add(back_button)
    return keyboard

def get_lang_keyboard(chat_id):
    """Клавиатура для выбора языка."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    ru_button = types.InlineKeyboardButton(
        text=get_text(chat_id, 'russian'),
        callback_data="lang_ru"
    )
    en_button = types.InlineKeyboardButton(
        text=get_text(chat_id, 'english'),
        callback_data="lang_en"
    )
    keyboard.add(ru_button, en_button)
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    # Сбрасываем состояние ожидания
    if chat_id in waiting_for_question:
        del waiting_for_question[chat_id]
    # Устанавливаем язык по умолчанию, если ещё не выбран
    if chat_id not in user_lang:
        user_lang[chat_id] = 'ru'   # можно также определить из message.from_user.language_code
    bot.send_message(
        chat_id,
        get_text(chat_id, 'welcome'),
        reply_markup=get_topics_keyboard(chat_id)
    )

@bot.message_handler(commands=['cancel'])
def cancel_input(message):
    chat_id = message.chat.id
    if waiting_for_question.get(chat_id):
        del waiting_for_question[chat_id]
        bot.send_message(
            chat_id,
            get_text(chat_id, 'cancel'),
            reply_markup=get_topics_keyboard(chat_id)
        )
    else:
        bot.send_message(chat_id, get_text(chat_id, 'no_active_input'))

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    if waiting_for_question.get(chat_id):
        question_text = message.text.strip()
        if not question_text:
            bot.send_message(chat_id, get_text(chat_id, 'please_write_question'))
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
            get_text(chat_id, 'question_sent'),
            reply_markup=get_topics_keyboard(chat_id)
        )
        del waiting_for_question[chat_id]
    else:
        # Можно проигнорировать или дать подсказку
        pass

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    lang = user_lang.get(chat_id, 'ru')

    # Если пользователь в режиме ожидания вопроса и нажал не на разрешённые кнопки
    if waiting_for_question.get(chat_id) and call.data not in ["ask_question", "choose_lang", "lang_ru", "lang_en"]:
        bot.answer_callback_query(
            call.id,
            get_text(chat_id, 'finish_input_first'),
            show_alert=True
        )
        return

    # ---------- Выбор языка ----------
    if call.data == "choose_lang":
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=get_text(chat_id, 'choose_language'),
            reply_markup=get_lang_keyboard(chat_id)
        )
        bot.answer_callback_query(call.id)
        return

    elif call.data == "lang_ru":
        user_lang[chat_id] = 'ru'
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=get_text(chat_id, 'language_changed'),
            reply_markup=get_topics_keyboard(chat_id)
        )
        bot.answer_callback_query(call.id)
        return

    elif call.data == "lang_en":
        user_lang[chat_id] = 'en'
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=get_text(chat_id, 'language_changed'),
            reply_markup=get_topics_keyboard(chat_id)
        )
        bot.answer_callback_query(call.id)
        return

    # ---------- Обработка нажатия на тему ----------
    if call.data.startswith("topic_"):
        topic_id = call.data.replace("topic_", "")
        topic = questions_db.get(topic_id)
        if not topic:
            bot.answer_callback_query(call.id, get_text(chat_id, 'topic_not_found'))
            return

        # Название темы на нужном языке
        topic_name = topic.get(f"name_{lang}", topic.get("name_ru", topic_id))

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=get_text(chat_id, 'topic_chosen', name=topic_name),
            reply_markup=get_questions_keyboard(chat_id, topic_id)
        )
        bot.answer_callback_query(call.id)

    # ---------- Обработка нажатия на вопрос ----------
    elif call.data.startswith("q_"):
        parts = call.data.split("_", 2)
        if len(parts) != 3:
            bot.answer_callback_query(call.id, get_text(chat_id, 'invalid_request'))
            return
        _, topic_id, question_id = parts
        topic = questions_db.get(topic_id)
        if not topic:
            bot.answer_callback_query(call.id, get_text(chat_id, 'topic_not_found'))
            return

        question_obj = next((q for q in topic["questions"] if q["id"] == question_id), None)
        if not question_obj:
            bot.answer_callback_query(call.id, get_text(chat_id, 'question_not_found'))
            return

        # Получаем текст вопроса и ответа в зависимости от языка
        question_text = get_question_text(question_obj, lang)
        answer_text = get_answer_text(question_obj, lang)

        bot.send_message(
            chat_id,
            f"❓ *{question_text}*\n\n💬 {answer_text}",
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    text=get_text(chat_id, 'back_to_questions'),
                    callback_data=f"topic_{topic_id}"
                )
            )
        )
        bot.answer_callback_query(call.id)

    # ---------- Назад к темам ----------
    elif call.data == "back_to_topics":
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=get_text(chat_id, 'choose_topic'),
            reply_markup=get_topics_keyboard(chat_id)
        )
        bot.answer_callback_query(call.id)

    # ---------- Задать свой вопрос ----------
    elif call.data == "ask_question":
        waiting_for_question[chat_id] = True
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=get_text(chat_id, 'enter_question'),
            reply_markup=None
        )
        bot.answer_callback_query(call.id)

    else:
        bot.answer_callback_query(call.id, get_text(chat_id, 'unknown_command'))

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()