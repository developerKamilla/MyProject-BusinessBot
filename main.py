import telebot
from telebot import types
import json
from datetime import datetime
# для построения графика расходов
import matplotlib.pyplot as plt
# для Базы Данных
import sqlite3
import random
import atexit
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
# Для ORM модели
from sqlalchemy.orm import sessionmaker

# Инициализация базы данных: создание таблицы пользователей, если она еще не существует
engine = create_engine('sqlite:///users.db', echo=False)
Base = declarative_base()

# Устанавливаем соединение с базой данных SQLite для хранения информации о пользователях
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Список ссылок на изображения  для использования в боте
cat_pics = [
    'https://i.pinimg.com/736x/af/f0/1c/aff01cea24b478bec034cf412406dbe5.jpg',
    'https://i.pinimg.com/736x/b5/5b/5d/b55b5df98672c2df8d1f1098adaf6cb2.jpg',
    'https://i.pinimg.com/736x/92/24/c7/9224c73f577d398b338fd8e0ab03c91a.jpg',
    'https://i.pinimg.com/736x/63/e6/5c/63e65c9f222efd5f9a7656c00bd4de1a.jpg',
    'https://i.pinimg.com/736x/98/24/48/98244843072ce5f28b3512a2fbb2657b.jpg',
    'https://i.pinimg.com/736x/22/d2/63/22d26336c9ac88e7cad1efd24ea678ce.jpg',
    'https://i.pinimg.com/736x/65/90/5d/65905d14a7c80bc8ec2704fa03a2099b.jpg',
    'https://i.pinimg.com/736x/26/0d/bf/260dbf0233a6eefcf8f2228bb97c9b9c.jpg',
    'https://i.pinimg.com/736x/66/ee/54/66ee5421a7e39909287e4a23b2fae034.jpg',
    'https://i.pinimg.com/736x/34/b9/24/34b924da95a851485670954f037bfabe.jpg',
    'https://i.pinimg.com/736x/c0/0a/9e/c00a9ec8921a214b6f86ca07ecc0e54b.jpg',
    'https://i.pinimg.com/736x/63/d3/b2/63d3b2c7bc908c6183ccf4f399dcc1b8.jpg',
]


# Функция для сохранения данных пользователя в JSON-файл (используется для хранения настроек или статистики)
def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Регистрация функции закрытия соединения с базой при завершении работы программы
@atexit.register
def close_db():
    conn.close()


# Токен API бота Telegram
API_TOKEN = '7468399496:AAFZFj5tqxjTvT4HglQp9ULlv7V5WpW6xkw'

bot = telebot.TeleBot(API_TOKEN)

# Название файла для хранения пользовательских данных в JSON формате
DATA_FILE = 'userdata.json'

# Предопределенные категории расходов или деятельности пользователя
CATEGORIES = [
    "развлечения",
    "медицина",
    "такси",
    "магазины",
    "фудкорты",
    "рестораны",
    "другое"
]

# Основная структура данных пользователя (может расширяться по мере необходимости)
data = {
    "balance": 0,
    "expenses": {},          # словарь расходов по категориям или датам
    "allmoney": [],         # список всех транзакций или операций
    "financial_goals": {},  # цели по финансам (например, накопить сумму)
    "budget": 0,            # установленный бюджет
}


# Функция для отображения главного меню бота с кнопками для взаимодействия
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Добавить доход", "Добавить расход")
    markup.row("Показать баланс", "Показать цели")
    markup.row("Установить бюджет", "Установить цель")
    markup.row("Диаграмма расходов")
    return markup


# Словарь для отслеживания состояния пользователя (например, ожидает ли он ввод суммы или категории)
user_states = {}


# Через этот класс я добавляю, ищу и обновляю данные о пользователях без написания SQL-запросов вручную.
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    nickname = Column(String)


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


# Функция для сохранения никнейма пользователя в базу данных SQLite
def save_nickname(user_id, nickname):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user:
        user.nickname = nickname
    else:
        user = User(user_id=user_id, nickname=nickname)
        session.add(user)
    session.commit()


# Функция для получения никнейма пользователя из базы данных по его ID
def get_nickname(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user:
        return user.nickname
    return None


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id  # Получаем уникальный идентификатор чата пользователя
    nickname = message.from_user.username  # Получаем никнейм пользователя
    save_nickname(user_id, nickname)  # Добавляем никнейм в БД

    # Отправляем приветственное сообщение с описанием возможностей бота
    bot.send_message(
        user_id,
        f"Привет {nickname}👋! "
        f"Меня зовут Олег👻. Я буду рад помочь тебе в финансах💸.\n"
        f"Я умею строить диаграмму расходов📊,\n"
        f"Добавлять доход и расход💰,\n"
        f"Устанавливать цели и отслеживать существующие👑.\n"
        f"А еще, если напишешь 'пришли милую картинку' увидешь сюрприз :).\n"
        f"Если станет скучно, мы можем сыграть в камень-ножницы-бумагу, только напиши 'давай сыграем'.\n"
        f"А если захочешь поговорить, то просто напиши 'привет', и мы поболтаем.\n"
        f"Удачи!🫶"
        f":)",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: True)
def handle_actions(message):
    text = message.text.lower()

    # Обработка приветствия от пользователя
    if text == "привет":
        user_states[message.chat.id] = {"action": "greeting_response"}
        bot.send_message(message.chat.id, "Привет! Как у тебя дела?")
        return

    # Установка состояния
    state = user_states.get(message.chat.id)
    if state:
        action = state.get("action")

        # Состояние приветствия
        if action == "greeting_response":
            if any(word in text for word in ["отлично", "супер", "хорошо"]):
                bot.send_message(message.chat.id, "Это прекрасно! Рад за тебя!", reply_markup=main_menu())
            elif any(word in text for word in ["плохо", "ужасно"]):
                bot.send_message(message.chat.id, "Желаю тебе всего самого хорошего!", reply_markup=main_menu())
            elif any(word in text for word in ["норм", "окей", "ок"]):
                bot.send_message(message.chat.id, "Что у тебя сегодня случилось?", reply_markup=main_menu())
            else:
                bot.send_message(message.chat.id, "Понял. Чем могу помочь?", reply_markup=main_menu())
            user_states.pop(message.chat.id)
            return

    # Запуск навыка 'давай сыграем'
    if "давай сыграем" in text:
        user_states[message.chat.id] = {"action": "play_rps"}
        bot.send_message(message.chat.id,
                         "Да, давай сыграем в камень-ножницы-бумагу! Отправь мне один из эмодзи: ✂️, 🪨, 🗒")
        return

        # Проверка на состояние ожидания хода игры
    state = user_states.get(message.chat.id)
    if state:
        action = state.get("action")
        if action == "play_rps":

            # Пользователь отправил эмодзи
            user_choice_emoji = message.text.strip()
            options = {"✂️": "ножницы", "🪨": "камень", "🗒": "бумага"}
            if user_choice_emoji not in options:
                bot.send_message(message.chat.id, "Пожалуйста, отправьте один из эмодзи: ✂️, 🪨, 🗒")
                return

            # Рандомное определение эмодзи бота
            bot_choice_emoji = random.choice(list(options.keys()))
            bot_choice_name = options[bot_choice_emoji]
            user_choice_name = options[user_choice_emoji]

            # Определение победителя
            # В зависимости от эмодзи
            result_message = f"Ты выбрал {user_choice_name} {user_choice_emoji}\n" \
                             f"Я выбрал {bot_choice_name} {bot_choice_emoji}\n"

            # В случае ничьи
            if user_choice_emoji == bot_choice_emoji:
                result_message += "Ничья!"

            # В случае выигрыша пользователя
            elif (bot_choice_emoji == "✂️" and user_choice_emoji == "🪨") or \
                    (bot_choice_emoji == "🪨" and user_choice_emoji == "🗒") or \
                    (bot_choice_emoji == "🗒" and user_choice_emoji == "✂️"):
                result_message += "Ты выиграл! 🎉"

            # В случае выигрыша бота
            else:
                result_message += "Я выиграл! 😎"

            bot.send_message(message.chat.id, result_message)
            user_states.pop(message.chat.id)
            return
    text = message.text.lower()

    # Обработка команды про изображение
    if "пришли милую картинку" in text:
        # Рандомно выбирается картинка из списка
        # Используется randint, так как choice выбирает только из двух
        index = random.randint(0, len(cat_pics) - 1)
        pic_url = cat_pics[index]
        bot.send_photo(message.chat.id, pic_url)
        return
    text = message.text

    # Обработка команды добавить доход
    if text == "Добавить доход":
        user_states[message.chat.id] = {"action": "add_income"}
        bot.send_message(message.chat.id, "Укажите сумму дохода:")

    # Обработка команды добавить расход
    elif text == "Добавить расход":
        user_states[message.chat.id] = {"action": "add_expense"}
        bot.send_message(message.chat.id,
                         f"Укажите сумму расхода и категорию через пробел.\nДоступные категории:\n"
                         f"{', '.join(CATEGORIES)}\nПример: 500 медицина")

    # Обработка команды показать баланс
    elif text == "Показать баланс":
        bot.send_message(message.chat.id, f"Ваш текущий баланс: {data['balance']} руб", reply_markup=main_menu())

    # Обработка команды показать цели
    elif text == "Показать цели":
        # вывод целей
        if not data["financial_goals"]:
            bot.send_message(message.chat.id, "У вас нет установленных целей.", reply_markup=main_menu())
        else:
            # Состояние актуальных целей
            response = "Ваши цели:\n"
            for goal in data["financial_goals"].values():
                response += f"Цель: {goal['goal']}, Сумма: {goal['amount']}, Текущий прогресс: {goal['progress']}\n"
            bot.send_message(message.chat.id, response, reply_markup=main_menu())

    # Обработка команды установки бюджета
    elif text == "Установить бюджет":
        user_states[message.chat.id] = {"action": "set_budget"}
        bot.send_message(message.chat.id, "Введите сумму бюджета:")

    # Обработка команды установки цели
    elif text == "Установить цель":
        user_states[message.chat.id] = {"action": "set_goal"}
        bot.send_message(message.chat.id, "Введите сумму и название цели через пробел:")

    # Вывод графика с помощью matplotlib
    elif text == "Диаграмма расходов":
        # Создаем список всех категорий
        categories = CATEGORIES
        # Для каждой категории берем сумму расходов или 0, если расходов по ней нет
        amounts = [data["expenses"].get(cat, 0) for cat in categories]

        try:
            # Создаем новую фигуру для графика с заданным размером
            plt.figure(figsize=(10, 6))

            # Строим столбчатую диаграмму с категориями и их расходами
            plt.bar(categories, amounts, color='gold')

            # Устанавливаем подпись оси X
            plt.xlabel("Категории")

            # Устанавливаем подпись оси Y
            plt.ylabel("Расходы (в рублях)")

            # Устанавливаем заголовок графика
            plt.title("Расходы по категориям")

            # Поворачиваем подписи категорий по оси X для лучшей читаемости
            plt.xticks(rotation=45)

            # Подгоняем макет, чтобы все элементы поместились корректно
            plt.tight_layout()

            # Определяем имя файла для сохранения графика
            filename = "expense_chart.png"

            # Сохраняем график в файл
            plt.savefig(filename)

            # Закрываем текущую фигуру, чтобы освободить память
            plt.close()

            # Открываем сохраненный файл в бинарном режиме для отправки
            with open(filename, 'rb') as photo:
                # Отправляем изображение в чат бота
                bot.send_photo(message.chat.id, photo)
        except Exception as e:
            # В случае ошибки отправляем сообщение об ошибке пользователю
            bot.send_message(message.chat.id, f"Ошибка при создании диаграммы: {e}")
    else:
        state = user_states.get(message.chat.id)
        if state:
            action = state.get("action")

            if action == "add_income":
                try:
                    amount = float(message.text)
                    data["balance"] += amount
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data["allmoney"].append({"type": "income", "money": amount, "description": "", "date": now})
                    save_data()
                    bot.send_message(message.chat.id, f"Доход в размере {amount} руб добавлен.",
                                     reply_markup=main_menu())
                except:
                    bot.send_message(message.chat.id, "Некорректный ввод. Попробуйте снова.")
                finally:
                    user_states.pop(message.chat.id)

            elif action == "add_expense":

                try:

                    parts = message.text.split()
                    # Проверка на правильный ввод
                    if len(parts) < 2:
                        raise ValueError("Недостаточно данных")
                    # Сумма расхода
                    amount_str = parts[0]
                    # Категория расхода
                    category_input = ' '.join(parts[1:]).strip()

                    amount = float(amount_str)

                    # Приводим к нижнему регистру для сравнения

                    category_input_lower = category_input.lower()

                    # Проверяем наличие категории (учитываем регистр)

                    categories_lower = [cat.lower() for cat in CATEGORIES]

                    if category_input_lower not in categories_lower:
                        bot.send_message(

                            message.chat.id,

                            f"Категория '{category_input}' не распознана. Выберите категорию из списка:\n"

                            f"{', '.join(CATEGORIES)}",

                            reply_markup=main_menu()

                        )

                        return

                    # Находим оригинальную категорию из списка по совпадению

                    index = categories_lower.index(category_input_lower)

                    category_actual = CATEGORIES[index]

                    # Обновляем баланс и расходы

                    data["balance"] -= amount

                    # Проверяем, существует ли уже категория расходов в данных
                    if category_actual in data["expenses"]:
                        # Если да, увеличиваем сумму расходов по этой категории на текущий расход
                        data["expenses"][category_actual] += amount
                    else:
                        # Если нет, создаем новую запись для этой категории с текущим расходом
                        data["expenses"][category_actual] = amount

                    # Получаем текущую дату и время в формате "ГГГГ-ММ-ДД ЧЧ:ММ:СС"
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Добавляем запись о расходе в общий список всех транзакций
                    data["allmoney"].append({
                        "type": "expense",  # Тип транзакции — расход
                        "amount": amount,  # Сумма расхода
                        "description": category_actual,  # Категория расхода
                        "date": now  # Дата и время транзакции
                    })

                    # Сохраняем обновленные данные (например, в файл или базу данных)
                    save_data()

                    # Отправляем пользователю подтверждение о добавлении расхода
                    bot.send_message(
                        message.chat.id,
                        f"Расход в размере {amount} руб по категории '{category_actual}' добавлен.",
                        reply_markup=main_menu()
                    )
                except Exception as e:

                    print(f"Error: {e}")

                    bot.send_message(

                        message.chat.id,

                        "Некорректный ввод. Используйте формат: [сумма] [категория]",

                        reply_markup=main_menu()

                    )

                finally:

                    user_states.pop(message.chat.id)
            elif action == "set_budget":
                try:
                    budget_value = float(message.text)
                    data["budget"] = int(budget_value)
                    save_data()
                    bot.send_message(
                        message.chat.id,
                        f"Бюджет установлен: {budget_value} руб.",
                        reply_markup=main_menu()
                    )
                except:
                    bot.send_message(
                        message.chat.id,
                        "Некорректный ввод. Попробуйте снова.",
                        reply_markup=main_menu()
                    )
                finally:
                    user_states.pop(message.chat.id)

            elif action == "set_goal":
                try:
                    # Разделяем текст сообщения по пробелам
                    parts = message.text.split()
                    # Первое слово — это сумма цели, преобразуем его в число
                    amount = float(parts[0])
                    # Остальные слова объединяем в название цели
                    goal_name = ' '.join(parts[1:])

                    # Проверяем, существует ли уже такая цель
                    if goal_name not in data["financial_goals"]:
                        # Если нет, создаем новую цель с указанной суммой и прогрессом 0
                        data["financial_goals"][goal_name] = {
                            "goal": goal_name,
                            "amount": amount,
                            "progress": 0.0,
                        }
                        # Сохраняем обновленные данные
                        save_data()
                        # Отправляем сообщение о успешном создании цели с кнопками главного меню
                        bot.send_message(
                            message.chat.id,
                            f'Цель "{goal_name}" с суммой {amount} была установлена.',
                            reply_markup=main_menu()
                        )
                    else:
                        # Если цель уже существует, уведомляем пользователя
                        bot.send_message(
                            message.chat.id,
                            f'Цель "{goal_name}" уже существует.',
                            reply_markup=main_menu()
                        )
                except:
                    # В случае ошибки (например, неправильный формат ввода), уведомляем пользователя
                    bot.send_message(
                        message.chat.id,
                        'Некорректный формат. Используйте: [сумма] [название цели]',
                        reply_markup=main_menu()
                    )
                finally:
                    # После обработки независимо от результата удаляем состояние пользователя из словаря
                    user_states.pop(message.chat.id)


bot.polling(none_stop=True)