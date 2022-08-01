# PythonMeetup Bot
 
Проект содержит телеграмм-бота для митапов, в котором можно задать вопрос спикеру, получить ответ, а также посмотреть расписание.
A convention bot that helps users get up-to-date event schedules, send their questions to speakers and get answers sent back in text format if the question has not been answered by the speaker on stage. 

Test bot: https://t.me/meetup_andrinho_bot

Admin page: https://meetup-bot-a.herokuapp.com/admin

### Installation
Create a Telegram bot with @BotFather.

Create a file called `.env` for environment variables in the project's root directory. Put the following variables into it:

- `TG_TOKEN` — your bot's token, obtained from BotFather
- `SECRET_KEY` — Django secret key.

This project requires Python3. It is recommended to use [venv](https://docs.python.org/3/library/venv.html) to set up a virtual environment.

Use `pip` to install dependencies:
```console
$ . venv/bin/activate
$ python3 -m pip install -r requirements.txt
```

After that, execute the following commands in the terminal in your project's virtual environment:
```console
$ python3 manage.py migrate
$ python3 manage.py createsuperuser
```

Run Django development server for previewing changes or debugging:
```console
$ python3 manage.py runserver
```

Or run your production server according to your hosting's instructions.

The file `meetup_bot/settings.py` has some code for deploying on Heroku:
```python3
# Configure Django App for Heroku.
import django_heroku
django_heroku.settings(locals())
```

Remove them if you are using a different hosting.

---

# Бот для сервиса PythonMeetup
 
Проект содержит телеграмм-бота для митапов, в котором можно задать вопрос спикеру, получить ответ, а также посмотреть расписание.

Тестовый бот: https://t.me/meetup_andrinho_bot

Админка: https://meetup-bot-a.herokuapp.com/admin

### Как установить
Необходимо создать телеграм-бота с помощью отца ботов @BotFather.

В проекте используются переменные окружения, необходимо создать файл `.env` для их хранения и положить туда следующие значения:

- `TG_TOKEN` — токен вашего телеграм-бота, полученный от BotFather
- `SECRET_KEY` — ключ для настройки джанго.

Python3 должен быть уже установлен. Рекомендуется использовать [venv](https://docs.python.org/3/library/venv.html) для создания виртуального окружения.

Используйте `pip` для установки зависимостей:
```console
$ . venv/bin/activate
$ python3 -m pip install -r requirements.txt
```

Далее последовательно выполните следующие команды:
```console
$ python3 manage.py migrate
$ python3 manage.py createsuperuser
```

Для запуска админки в режиме разработки:
```console
$ python3 manage.py runserver
```

Либо запустите сервер в соответствии с инструкцией хостинга в режиме продакшен.

В конце файла `meetup_bot/settings.py` есть команды для функционирования сайта на сервисе Heroku:
```python3
# Configure Django App for Heroku.
import django_heroku
django_heroku.settings(locals())
```

Уберите их, если размещаете сайт на другом хостинге.
