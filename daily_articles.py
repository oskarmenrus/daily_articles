import fake_useragent
import requests
import random
import smtplib
import auth_data
import datetime
import logging

from time import sleep
from urllib.parse import unquote
from email.mime.text import MIMEText


def remove_bad_proxy(random_proxy: dict, proxy_file: str) -> None:
    """Функция удаляет не рабочие прокси из соотвествующего файла"""
    with open(proxy_file) as file:
        proxy_list = file.read().split('\n')[:-1]

    proxy_list.remove(random_proxy['https'][7:])

    with open(proxy_file, 'w') as file:
        for ip in proxy_list:
            file.write(ip + '\n')

    logging.debug(f'BAD proxy was removed!: {random_proxy}')


def add_new_proxies(url: str, file: str) -> None:
    """Функция добавляет новые прокси в файл"""
    r = requests.get(url, headers=headers)

    ip_list = []
    for i, ip in enumerate(r.json()["response"]["items"]):
        ip_list.append(r.json()["response"]["items"][i]["ip"] + ':' + str(r.json()["response"]["items"][i]["port"]))

    with open(file, 'a') as file:
        for ip in ip_list:
            file.write(ip + '\n')

    logging.debug('New proxies was added!')


def proxies_list(proxies_file: str) -> list:
    """Функция считывает прокси из файла и возвращает их в виде списка из словарей"""
    with open(proxies_file) as file:
        proxies_dict = file.read().split('\n')[:-1]

    proxies_dict = [{'https': 'http://{}'.format(proxy)} for proxy in proxies_dict]
    return proxies_dict


def check_proxy(proxy_dict: list) -> dict:
    """Функция проверяет доступность прокси, записывает новые прокси в файл, если он пустой,
    а так же удаляет не рабочие."""
    while True:
        if not proxy_dict:
            add_new_proxies(api_url, file_with_proxies)
            proxy_dict = proxies_list(file_with_proxies)

        random_proxy = random.choice(proxy_dict)
        try:
            requests.get('https://www.google.ru', headers=headers, proxies=random_proxy)
        except requests.exceptions.ProxyError:
            remove_bad_proxy(random_proxy, file_with_proxies)
            proxy_dict = proxies_list(file_with_proxies)
            continue
        except Exception as err:
            logging.debug(f'Something going wrong... {err.__repr__()}, {err.__doc__}')
            continue
        else:
            return random_proxy


def send_mail(message: str) -> None:
    """Функция отправляет сообщение на почту"""
    message = MIMEText(f'Here some links for you:\n\n{message}'.encode('UTF-8'), _charset='UTF-8')
    try:
        smtp_obj = smtplib.SMTP("smtp.gmail.com", 587)
        smtp_obj.starttls()
        smtp_obj.login(auth_data.gmail_login, auth_data.gmail_password)
        smtp_obj.sendmail(auth_data.gmail_login, auth_data.send_to, message.as_string())
        smtp_obj.quit()
    except smtplib.SMTPException as smtp_err:
        logging.debug(f'Error SMTP. Сделай что-то: {smtp_err.__repr__()}, {smtp_err.__doc__}')


def get_random_article(url: str) -> str:
    """Функция получает случайную ссылку на статью"""
    proxies = proxies_list(file_with_proxies)  # Словарь прокси
    session = requests.Session()
    while True:
        proxy = check_proxy(proxies)  # Проверка прокси на работоспособность

        # Запрос статьи и обработка исключений
        try:
            r = session.get(url, headers=headers, proxies=proxy)
            return unquote(r.url)
        except requests.exceptions.ProxyError:
            remove_bad_proxy(proxy, file_with_proxies)
            proxies = proxies_list(file_with_proxies)
            continue
        except requests.exceptions.ConnectionError as req_err:
            logging.debug(f'Something wrong with connection: {req_err.__repr__()}, {req_err.__doc__}, url: {url}')
            continue


# Ссылки на сайты с возможностью получить рандомные статьи #
lurkmore_link = 'https://lurkmore.to/Служебная:Random'
wikipedia_link = 'https://ru.wikipedia.org/wiki/Служебная:Случайная_страница'
absurdopedia_link = 'http://absurdopedia.net/wiki/Служебная:RandomInCategory/Абсурдопедия:Случайные_статьи'

# Ссылка на API для получения новых прокси и основной файл с прокси #
api_url = 'http://api.foxtools.ru/v2/Proxy?type=https&free=yes&available=yes'
file_with_proxies = 'proxies.txt'

# Хэдер со случайным юзер-агентом и файл с логами #
headers = {'User-Agent': fake_useragent.UserAgent(verify_ssl=False).random}
logging.basicConfig(filename='logs.log', level=logging.DEBUG)
# ------------------- #


def main() -> None:
    """Функция запускает работу скрипта"""
    links = [lurkmore_link, wikipedia_link, absurdopedia_link]
    message = '\n'.join([get_random_article(link) for link in links])
    send_mail(message)
    return logging.debug(f'Function {main.__name__} successfully completed!')


if __name__ == '__main__':
    logging.debug('Program started work...')
    hour_and_one_minute_in_seconds = 3660

    while True:
        hour = datetime.datetime.now().time().hour
        minute = datetime.datetime.now().time().minute

        if hour == 22 and minute == 59:
            try:
                main()
            except Exception as e:
                logging.debug(f'Error in main! {e.__repr__()}, {e.__doc__}')

            sleep(hour_and_one_minute_in_seconds)
