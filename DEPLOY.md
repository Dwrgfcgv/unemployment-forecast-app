# Размещение приложения онлайн

## Рекомендуемый способ: Streamlit Community Cloud + GitHub

GitHub нужен как репозиторий с кодом, а Streamlit Community Cloud запускает само Python-приложение и дает публичную ссылку.

### 1. Подготовить проект

В репозиторий нужно загрузить:

- `app.py`
- `requirements.txt`
- `README.md`
- `.streamlit/config.toml`
- папку `src/`
- папку `data/`, если нужна стартовая локальная копия данных

Не нужно загружать:

- `.venv/`
- `__pycache__/`
- `outputs/`
- локальные служебные файлы macOS

Эти исключения уже добавлены в `.gitignore`.

### 2. Создать репозиторий на GitHub

1. Зайти на https://github.com.
2. Нажать `New repository`.
3. Назвать репозиторий, например `unemployment-forecast-app`.
4. Выбрать `Public`, если приложение должно быть удобно деплоить и показывать по ссылке.
5. Нажать `Create repository`.

### 3. Загрузить код в репозиторий

В терминале из папки проекта выполнить:

```bash
git init
git add .
git commit -m "Initial Streamlit app"
git branch -M main
git remote add origin https://github.com/USERNAME/unemployment-forecast-app.git
git push -u origin main
```

`USERNAME` нужно заменить на имя аккаунта GitHub.

### 4. Развернуть на Streamlit Community Cloud

1. Открыть https://share.streamlit.io.
2. Войти через GitHub.
3. Нажать `Create app`.
4. Выбрать репозиторий `unemployment-forecast-app`.
5. Branch: `main`.
6. Main file path: `app.py`.
7. Python version: лучше выбрать `3.12`, если доступно.
8. Нажать `Deploy`.

После сборки Streamlit выдаст ссылку вида:

```text
https://your-app-name.streamlit.app
```

Эту ссылку можно отправлять научному руководителю, комиссии или другим пользователям.

## Почему не GitHub Pages

GitHub Pages подходит для статических сайтов: HTML, CSS и JavaScript. Streamlit-приложение запускается на Python и требует серверного процесса, поэтому для него нужен Streamlit Community Cloud, Render, Railway, Hugging Face Spaces или другой сервис, который умеет запускать Python-приложения.
