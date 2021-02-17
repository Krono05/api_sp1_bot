import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
VERDICTS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': ('Ревьюеру всё понравилось, можно приступать к следующему'
                 ' уроку.'),
    'reviewing': 'Работа взята в ревью'
}
UNEXPECTED_STATUS = 'Неожиданный статус: {status}'
APPROVED_HOMEWORK = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
RESPONSE_PARAMS = (
    'параметры запроса {params}, URL: {url}, заголовок: {headers}'
)
EXCEPTION_APPEARED = (
    'Обнаружена ошибка соединения: {exception},' + RESPONSE_PARAMS
)
MESSAGE = 'Отправка сообщения в телеграм: {message}'
BOT_EXCEPTION = 'Бот столкнулся с ошибкой: {exception}'
START = 'Запуск бота-ассистента'
MESSAGE_SENT = 'Сообщение отправлено'
RESPONSES = {
    'error': 'Ошибка: {error}, ' + RESPONSE_PARAMS,
    'code': 'Код ответа: {code}, ' + RESPONSE_PARAMS
}


def parse_homework_status(homework):
    name = homework['homework_name']
    status = homework['status']
    if status in VERDICTS:
        verdict = VERDICTS[status].format(homework_name=name)
    else:
        raise KeyError(UNEXPECTED_STATUS.format(status=status))
    return APPROVED_HOMEWORK.format(
        homework_name=name,
        verdict=verdict
    )


def get_homework_statuses(current_timestamp):
    request_params = {
        'headers': HEADERS,
        'params': {'from_date': current_timestamp},
        'url': URL
    }
    try:
        response = requests.get(**request_params)
    except requests.exceptions.ConnectionError as exception:
        raise ConnectionError(EXCEPTION_APPEARED.format(
            exception=exception,
            **request_params
        ))
    response_json = response.json()
    for response_name, response_value in RESPONSES.items():
        if response_name in response_json:
            raise RuntimeError(response_value.format(
                response_name=response_value,
                status=response.status_code,
                **request_params
            ))
    return response.json()


def send_message(message, bot_client):
    logging.info(MESSAGE.format(message=message))
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug(START)
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client)
                logging.info(MESSAGE_SENT)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as exceptions:
            logging.error(BOT_EXCEPTION.format(exception=exceptions))
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        format='%(asctime)s %(name)s %(levelname)s: %(message)s'
    )
    main()
