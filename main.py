import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json
import os
import random

# ========== НАСТРОЙКИ ==========
TOKEN = 'vk1.a.7kHhQS3rw_butjsXff5mqR565t7Rw42DFXT2zf4vVqmIa2ViyRR9DPxOwWyxxa3NxCzoIlJ0ffoM7tjoDyNsROqCQWaZzcUce9_2CwKQWnnnpFuqMB4k_diWLdK1GJm4bZvz1XMwa-ZjhuU-icoSR_umOwsPngxT_W0rhqkzzBm2TbDsi8DXlfdw9q8bB-xolV0cAYFA7hov8Kf9k0J8Iw'          # Токен сообщества VK (длинная строка)
ADMIN_USER_ID = 608713399            # Ваш VK ID (число)
# ================================

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# Состояния пользователей
user_states = {}          # ключ: user_id, значение: None или 'waiting_question'
user_lang = {}            # ключ: user_id, значение: 'ru' или 'en'

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
        'enter_question': "✏️ Напишите ваш вопрос простым текстом.\n\nЯ передам его разработчику. Чтобы отменить, отправьте 'отмена'.",
        'question_sent': "✅ Спасибо! Ваш вопрос передан разработчику. Он будет рассмотрен и, возможно, добавлен в базу.",
        'cancel': "❌ Ввод вопроса отменён.",
        'no_active_input': "Нет активного ввода вопроса.",
        'invalid_request': "❌ Некорректный запрос",
        'topic_not_found': "❌ Тема не найдена!",
        'question_not_found': "❌ Вопрос не найден!",
        'unknown_command': "❓ Неизвестная команда",
        'finish_input_first': "Сначала завершите ввод вопроса (отправьте 'отмена' для отмены).",
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
        'enter_question': "✏️ Write your question in plain text.\n\nI will forward it to the developer. To cancel, send 'cancel'.",
        'question_sent': "✅ Thank you! Your question has been sent to the developer. It will be reviewed and possibly added to the database.",
        'cancel': "❌ Question input cancelled.",
        'no_active_input': "No active question input.",
        'invalid_request': "❌ Invalid request",
        'topic_not_found': "❌ Topic not found!",
        'question_not_found': "❌ Question not found!",
        'unknown_command': "❓ Unknown command",
        'finish_input_first': "Please finish entering your question first (send 'cancel' to cancel).",
        'please_write_question': "Please write your question.",
        'back_to_questions': "◀ Back to questions",
    }
}

def get_text(user_id, key, **kwargs):
    lang = user_lang.get(user_id, 'ru')
    text = TEXTS[lang].get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text

# ---------- Загрузка базы ----------
def load_questions_db():
    json_path = os.path.join(os.path.dirname(__file__), 'questions.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл questions.json не найден!")
        return {}
    except json.JSONDecodeError:
        print("❌ Ошибка чтения JSON.")
        return {}

questions_db = load_questions_db()

def get_question_text(question_obj, lang):
    if lang == 'en' and 'text_en' in question_obj:
        return question_obj['text_en']
    return question_obj['text']

def get_answer_text(question_obj, lang):
    if lang == 'en' and 'answer_en' in question_obj:
        return question_obj['answer_en']
    return question_obj['answer']

# ---------- Построители клавиатур ----------
def get_topics_keyboard(user_id):
    keyboard = VkKeyboard(one_time=False, inline=False)
    lang = user_lang.get(user_id, 'ru')
    for topic_id, topic_data in questions_db.items():
        topic_name = topic_data.get(f"name_{lang}", topic_data.get("name_ru", topic_id))
        payload = json.dumps({"command": "topic", "topic_id": topic_id}, ensure_ascii=False)
        keyboard.add_button(topic_name, color=VkKeyboardColor.PRIMARY, payload=payload)
        keyboard.add_line()
    ask_payload = json.dumps({"command": "ask"}, ensure_ascii=False)
    keyboard.add_button(get_text(user_id, 'ask_question'), color=VkKeyboardColor.POSITIVE, payload=ask_payload)
    keyboard.add_line()
    lang_payload = json.dumps({"command": "choose_lang"}, ensure_ascii=False)
    keyboard.add_button(get_text(user_id, 'language'), color=VkKeyboardColor.SECONDARY, payload=lang_payload)
    return keyboard

def get_questions_keyboard(user_id, topic_id):
    keyboard = VkKeyboard(one_time=False, inline=False)
    lang = user_lang.get(user_id, 'ru')
    topic = questions_db[topic_id]
    for question in topic["questions"]:
        q_text = get_question_text(question, lang)
        payload = json.dumps({"command": "question", "topic_id": topic_id, "q_id": question["id"]}, ensure_ascii=False)
        keyboard.add_button(q_text, color=VkKeyboardColor.PRIMARY, payload=payload)
        keyboard.add_line()
    back_payload = json.dumps({"command": "back_to_topics"}, ensure_ascii=False)
    keyboard.add_button(get_text(user_id, 'back_to_topics'), color=VkKeyboardColor.NEGATIVE, payload=back_payload)
    return keyboard

def get_lang_keyboard(user_id):
    keyboard = VkKeyboard(one_time=False, inline=False)
    ru_payload = json.dumps({"command": "lang", "lang": "ru"}, ensure_ascii=False)
    en_payload = json.dumps({"command": "lang", "lang": "en"}, ensure_ascii=False)
    keyboard.add_button(get_text(user_id, 'russian'), color=VkKeyboardColor.PRIMARY, payload=ru_payload)
    keyboard.add_line()
    keyboard.add_button(get_text(user_id, 'english'), color=VkKeyboardColor.PRIMARY, payload=en_payload)
    return keyboard

def send_message(user_id, text, keyboard=None):
    """Утилита для отправки сообщения с клавиатурой (исправлено)."""
    params = {
        'user_id': user_id,
        'message': text,
        'random_id': random.randint(0, 2**30),
    }
    if keyboard:
        params['keyboard'] = keyboard.get_keyboard()
    vk.messages.send(**params)

# ---------- Обработчик сообщений ----------
print("✅ Бот запущен и ожидает сообщения...")
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        msg_text = event.text.strip()
        payload = None
        if event.extra_values.get('payload'):
            try:
                payload = json.loads(event.extra_values['payload'])
            except:
                payload = None

        # Если пользователь в режиме ожидания вопроса – обрабатываем текст
        if user_states.get(user_id) == 'waiting_question':
            if msg_text.lower() in ['отмена', 'cancel']:
                user_states.pop(user_id, None)
                send_message(user_id, get_text(user_id, 'cancel'), keyboard=get_topics_keyboard(user_id))
                continue

            if not msg_text:
                send_message(user_id, get_text(user_id, 'please_write_question'))
                continue

            # Пересылка админу
            user_info = f"id{user_id}"
            full_info = f"✉️ Новый вопрос от {user_info}:\n\n{msg_text}"
            try:
                vk.messages.send(
                    user_id=ADMIN_USER_ID,
                    message=full_info,
                    random_id=random.randint(0, 2**30)
                )
            except Exception as e:
                print(f"Ошибка отправки админу: {e}")

            send_message(user_id, get_text(user_id, 'question_sent'), keyboard=get_topics_keyboard(user_id))
            user_states.pop(user_id, None)
            continue

        # Если есть payload – обрабатываем команду
        if payload and 'command' in payload:
            cmd = payload['command']

            if cmd == 'choose_lang':
                send_message(user_id, get_text(user_id, 'choose_language'), keyboard=get_lang_keyboard(user_id))

            elif cmd == 'lang':
                new_lang = payload.get('lang', 'ru')
                user_lang[user_id] = new_lang
                send_message(user_id, get_text(user_id, 'language_changed'), keyboard=get_topics_keyboard(user_id))

            elif cmd == 'topic':
                topic_id = payload['topic_id']
                topic = questions_db.get(topic_id)
                if not topic:
                    send_message(user_id, get_text(user_id, 'topic_not_found'))
                else:
                    topic_name = topic.get(f"name_{user_lang.get(user_id, 'ru')}", topic.get("name_ru", topic_id))
                    send_message(user_id, get_text(user_id, 'topic_chosen', name=topic_name),
                                 keyboard=get_questions_keyboard(user_id, topic_id))

            elif cmd == 'back_to_topics':
                send_message(user_id, get_text(user_id, 'choose_topic'), keyboard=get_topics_keyboard(user_id))

            elif cmd == 'ask':
                user_states[user_id] = 'waiting_question'
                send_message(user_id, get_text(user_id, 'enter_question'), keyboard=None)

            elif cmd == 'question':
                topic_id = payload['topic_id']
                q_id = payload['q_id']
                topic = questions_db.get(topic_id)
                if not topic:
                    send_message(user_id, get_text(user_id, 'topic_not_found'))
                else:
                    question_obj = next((q for q in topic["questions"] if q["id"] == q_id), None)
                    if not question_obj:
                        send_message(user_id, get_text(user_id, 'question_not_found'))
                    else:
                        lang = user_lang.get(user_id, 'ru')
                        q_text = get_question_text(question_obj, lang)
                        a_text = get_answer_text(question_obj, lang)
                        # Клавиатура для возврата к вопросам этой темы
                        back_keyboard = VkKeyboard(one_time=False, inline=False)
                        back_payload = json.dumps({"command": "topic", "topic_id": topic_id}, ensure_ascii=False)
                        back_keyboard.add_button(get_text(user_id, 'back_to_questions'), color=VkKeyboardColor.PRIMARY, payload=back_payload)
                        send_message(user_id, f"❓ {q_text}\n\n💬 {a_text}", keyboard=back_keyboard)

        else:
            # Нет payload – приветствие и меню
            if user_id not in user_lang:
                user_lang[user_id] = 'ru'
            send_message(user_id, get_text(user_id, 'welcome'), keyboard=get_topics_keyboard(user_id))