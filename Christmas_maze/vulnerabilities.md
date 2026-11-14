#Уязвимости

1. XSS — A03:2021 Injection
Где: render_game_page(), вывод {{name}} без html.escape.
Эксплойт: имя "<img src=x onerror=alert(1)>" => атака удалась => при каждом прохождении/поражении вместо рейтинга выводится localhost:8000 \n 1=>
=> уязвимость
Патч: сначала удаляем данные пользователя с ником "<img src=x onerror=alert(1)>"
в scores.json, затем добавляем в server.py: html.escape(name) при выводе (и в рейтинге тоже)

2. IDOR — A01:2021 Broken Access Control
Где: /game?g=<id>, нет проверки владельца игры
Эксплойт: перебор g => чтение/изменение чужой игры; 
Патч: привязать g к сессии/куке, проверять владельца

3. Path Traversal — A03:2021 Injection
Где: /static/, нет проверки startswith(static_dir)
Эксплойт: прописываем путь к Christmas_maze, потом пишем
curl.exe --path-as-is "http://localhost:8000/static/../server.py"`GET /static/../server.py` => отдал исходник server.py => уязвимость
Патч: resolve() + startswith(static_dir)
