import os
import time
import logging
import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG, filename='telegram_bot.log',
                    format='%(asctime)s %(name)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if status == "rejected":
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = (
            'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
        )
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=headers, params=params)
        return homework_statuses.json()
    except requests.RequestException as error:
        return logging.error(error, exc_info=True)


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    # проинициализировать бота здесь
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Запуск бота-ассистента')
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client)
                logging.info('Сообщение отправлено')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            logging.error(f'Бот столкнулся с ошибкой: {e}')
            send_message('Бот столкнулся с ошибкой', bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
