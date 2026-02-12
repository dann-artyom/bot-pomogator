import telebot
import time
import webbrowser
from telebot import types
bot=telebot.TeleBot('8220423257:AAFk0zQ35uNJXYHxzvVgudyb-_nzu4OsePU')
questions_db = {
    "Общежития в НГТУ": {
        "name": "Общежития в НГТУ",
        "questions": [
            {"id": "ob10", "text": "Что нужно сделать чтобы попасть в 10 общежитие НГТУ?", "answer": "Если вы поступающий, то необходимо набрать >=250 баллов, проходное количество балов может меняться каждый год\nЕсли вы студент, то для заселения в 10 общежитие вам необходимо стать отсличником(сочувствую)"},
            {"id": "venv", "text": "Как пропустить гостя в общежитие", "answer": "Для этого студенту необходимо иметь студенческий билет, а гостю паспорт(или другой документ удостоверяющий личность)\nГостей можно приводить с 10 до 22"},
            {"id": "listcomp", "text": "Если я живу в одном общежитии, могу ли я попасть в другое?", "answer": "Самостоятельно пройти в другое общежитие вы не можете, вы можете пройти только как гость"}
        ]
    },
    "Процесс поступления в НГТУ": {
        "name": "Процесс поступления в НГТУ",
        "questions": [
            {"id": "token", "text": "Как встать на миграционный учёт?", "answer": "После пересечения границы, необходимо подать документы в личном кабинете абитуриента в разделе миграционный учет, а поле следить за статусом заявки."},
            {"id": "lib", "text": "Какая библиотека лучше?", "answer": "Для Python популярны pyTelegramBotAPI (telebot) и python-telegram-bot."},
            
        ]
    },
    "Кафе и магазины": {
        "name": "Кафе и магазины",
        "questions": [
            {"id": "undo", "text": "Где можно купить лучшую шаурму?", "answer": "В высоком ценовом сегменте лучшая шаурму в районе метро студенческая «Jungle Chef» в низшим ценовом сегменте «Шаурма на студенческой»"},
            {"id": "conflict", "text": "Сколько столовых на территории НГТУ? Какая самая лучшая?", "answer": "В каждом корпусе НГТУ есть своя столовая. По статистике люди предпочитают столовую в 6-ом корпусе «Яблоко Ньютона»"},
            {"id": "branch", "text": "Какие самые ближайшие продуктовые магазины?", "answer": "Два ближайших продуктовых ммагазина это Лента и Мария-ра, но если пройти дальше, в сторону реки, то можно найти Ярче!"}
        ]
    },
    "Библиотека":{
        "name": "Библиотека",
        "questions":[
            {"id": "empty", "text":"Empty", "answer":"empty"}
        ]
    },
    "Учёба в НГТУ":{
        "name": "Учёба в НГТУ",
        "questions":[
            {"id": "control", "text":"Что такое контрольные недели и зачем они нужны?", "answer":"Всего в семестре 3 контрольных недели (на 5,9 и 13 неделях)\nБольшинство преподавателей проводят контрольные в это время, по каждому предмету выставляется 0-2 баллов, однако это лишь формальность, эти баллы практически не на что не влияют\nНо если у вас будет много нулей, то вас могут вызвать в деканат :)"}
        ]
    },
    "Преподаватели":{
        "name": "Преподаватели",
        "questions":[
            {"id": "OVCH", "text":"Овчинникова Елена Владимировна", "answer":"Преподаватель по линейной алгебре и дискретной математике. Очень интересно и понятно ведет семинары и лекции, на ее парах ты понимаешь абсолютно все. Если это твой семинарист - это победа.  Уважайте и любите .  Пишите лекции, на экзамене можно воспользоваться ими в течение 10 минут."},
            {"id": "PLV", "text":"Павшок Людмила Викторовнана", "answer":"преподаватель по матанализу. Требовательная и строгая, но справедливая. На ее парах нельзя отвлекаться и обязательно писать все, что она говорит. Лекции, которые она давала, можно использовать на экзамене (10 минут) поэтому пишите понятно и разборчиво. Если хотите автомат , получайте на семинарах максимально много баллов, делайте курс в dispace и доработки."},
            {"id": "FVV", "text":"Филатов Владимир Викторович", "answer":"Преподаватель по матанализу. Выглядит строгим, любит ворчать, но в конце всегда без проблем ставит 3 автоматом(примерно от 30 баллов), на лекции можно не ходить, все презентации есть у него в курсе.\nНо вот если вам нужна 4 или 5, то тут будет тяжеловато, билеты там трудные, ищите сливы, на самом экзамене списать довольно легко, главное потом объяснить что написал."}
            
        ]
    },
}

def get_topics_keyboard():
    """Инлайн-клавиатура со списком тем."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for topic_id, topic_data in questions_db.items():
        button = types.InlineKeyboardButton(
            text=topic_data["name"],
            callback_data=f"topic_{topic_id}"   
        )
        keyboard.add(button)
    return keyboard

def get_questions_keyboard(topic_id):
    """Инлайн-клавиатура со списком вопросов для темы."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    topic = questions_db[topic_id]
    for question in topic["questions"]:
        # В callback_data передаём только идентификатор вопроса (буквы, цифры, подчёркивание)
        button = types.InlineKeyboardButton(
            text=question["text"],
            callback_data=f"q_{topic_id}_{question['id']}"   # q_<topic_id>_<question_id>
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
    welcome_text = "👋 Привет! Я — бот-помогатор.\nВыберите интересующую вас тему:"
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=get_topics_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # ---------- Обработка нажатия на тему ----------
    if call.data.startswith("topic_"):
        topic_id = call.data.replace("topic_", "")
        topic = questions_db.get(topic_id)
        if not topic:
            bot.answer_callback_query(call.id, "❌ Тема не найдена!")
            return

        # Редактируем сообщение: показываем вопросы
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"Вы выбрали тему: {topic['name']}\n\nВыберите вопрос:",
            reply_markup=get_questions_keyboard(topic_id)
        )
        bot.answer_callback_query(call.id)

    # ---------- Обработка нажатия на вопрос ----------
    elif call.data.startswith("q_"):
        # Формат: q_<topic_id>_<question_id>
        parts = call.data.split("_", 2)  # ['q', topic_id, question_id]
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "❌ Некорректный запрос")
            return
        _, topic_id, question_id = parts
        topic = questions_db.get(topic_id)
        if not topic:
            bot.answer_callback_query(call.id, "❌ Тема не найдена!")
            return

        # Ищем вопрос по id
        question_obj = next((q for q in topic["questions"] if q["id"] == question_id), None)
        if not question_obj:
            bot.answer_callback_query(call.id, "❌ Вопрос не найден!")
            return

        # Отправляем ответ
        bot.send_message(
            chat_id,
            f"❓ *{question_obj['text']}*\n\n💬 {question_obj['answer']}",
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀ К вопросам", callback_data=f"topic_{topic_id}")
            )
        )
        bot.answer_callback_query(call.id)

    # ---------- Назад к темам ----------
    elif call.data == "back_to_topics":
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="Выберите интересующую вас тему:",
            reply_markup=get_topics_keyboard()
        )
        bot.answer_callback_query(call.id)

    else:
        bot.answer_callback_query(call.id, "❓ Неизвестная команда")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()