#Уязвимости

1. XSS — A03:2021 Injection
Где: `render_game_page()`, вывод `{{name}}` без `html.escape`.
Эксплойт: имя `<img src=x onerror=alert(1)>` => скрипт исполняется.
Патч: `html.escape(name)` при выводе (и в рейтинге тоже).

2. IDOR — A01:2021 Broken Access Control
Где: `/game?g=<id>`, нет проверки владельца игры.
Эксплойт: перебор `g` => чтение/изменение чужой игры.
Патч: привязать `g` к сессии/куке, проверять владельца.

3. Path Traversal — A03:2021 Injection
Где: `/static/`, нет проверки `startswith(static_dir)`.
Эксплойт: `GET /static/../server.py` => отдаёт исходник.
Патч: `resolve()` + `startswith(static_dir)`.
