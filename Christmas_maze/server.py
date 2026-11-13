from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import mimetypes
import uuid
from urllib.parse import urlparse, parse_qs
import random
import json

# УЯЗВИМОСТИ
# XSS — имя в /game без html.escape;
# IDOR — /game?g=<id> открывает любую игру;
# Path Traversal — /static/../server.py читает server.py (уберём startswith — позже).



HOST = "localhost"
PORT = 8000
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

TOTAL_ROOMS = 15
EASY_ROOMS_UNTIL = 10
START_PRESENTS = 3

games ={}

SCORES_FILE = BASE_DIR / "scores.json"


def load_scores():
    if not SCORES_FILE.exists():
        return []
    try:
        with SCORES_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_score(name, rooms, presents, result):
    scores = load_scores()
    scores.append({
        "name": name,
        "rooms": rooms,
        "presents": presents,
        "result": result,
    })
    with SCORES_FILE.open("w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


def top10():
    scores = load_scores()
    scores.sort(key=lambda s: (s["rooms"], s["presents"]), reverse=True)
    return scores[:10]


def generate_special_door(room):
    door = random.choice([1, 2, 3])
    if room <= EASY_ROOMS_UNTIL:
        return ("bad", door)
    else:
        return ("good", door)

def is_door_good(game, door):  #door — 1/2/3. True, если ведёт дальше
    if game["special_type"] == "bad":
        return door != game["special_door"]
    else: 
        return door == game["special_door"]


def new_game(name):  #Создаёт игру, возвращает (game_id, game)
    game_id = uuid.uuid4().hex
    stype, sdoor = generate_special_door(1)
    game = {
        "name": name,             # !!! XSS: выводится без html.escape
        "presents": START_PRESENTS,
        "room": 1,
        "special_type": stype,
        "special_door": sdoor,
    }
    games[game_id] = game
    return game_id, game


def step(game, door):   #Обрабатывает клик, меняет game, возвращает 'win'|'lose'|'continue'
    if is_door_good(game, door):
        game["room"] += 1
        if game["room"] > TOTAL_ROOMS:
            return "win"

        #новая комната — новая особая дверь
        stype, sdoor = generate_special_door(game["room"])
        game["special_type"] = stype
        game["special_door"] = sdoor
        return "good"
    else:
        game["presents"] -= 1
        if game["presents"] <= 0:
            return "lose"
        return "bad"

def render_game_page(game_id, game):
    template = (TEMPLATES_DIR / "game.html").read_text(encoding="utf-8")
    presents_icons = ("🎁" * game["presents"]
                      + "🖤" * (START_PRESENTS - game["presents"]))
    return (template
            .replace("{{room}}", str(game["room"]))
            .replace("{{total}}", str(TOTAL_ROOMS))
            .replace("{{name}}", game["name"])     #!!!!!!!!!!!!!!! XSS name без html.escape!!!!!!!!!!!!!!!!!!!//
            .replace("{{g}}", game_id)
            .replace("{{presents}}", str(game["presents"]))
            .replace("{{presents_icons}}", presents_icons))

def render_bad_door_page(game_id, game):
    template = (TEMPLATES_DIR / "bad_door.html").read_text(encoding="utf-8")
    return (template
            .replace("{{g}}", game_id)
            .replace("{{presents}}", str(game["presents"])))

def render_end_page(result, game):
    scores = top10()
    rows = "".join(       #XSS (A03:2021): s['name'] без html.escape (stored XSS)
        f"<li>{s['name']} — {s['rooms']} комнат "
        f"({s['presents']} 🎁) [{s['result']}]</li>"
        for s in scores
    )
    scores_html = f"<div class='scores'><h2>Топ-10</h2><ol>{rows}</ol></div>"

    if result == "win":
        body = (f"<h1>Поздравляю!</h1>"
                f"<p>Ты прошёл все {TOTAL_ROOMS} комнат "
                f"с {game['presents']} подарками!</p>"
                f"<img src='/static/img/win.jpg' alt='Победа' width='300'>")
    else:
        body = ("<h1>Вы затерялись в лабиринте...</h1>"
                "<p>Все подарки потеряны. Удачи в следующий раз!</p>"
                "<img src='/static/img/lose.jpg' alt='Поражение' width='300'>")

    return ("<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'>"
            "<link rel='stylesheet' href='/static/style.css'></head><body>"
            f"{body}{scores_html}"
            "<p><a href='/start' class='btn'>Играть снова</a></p>"
            "</body></html>")

class Handler(BaseHTTPRequestHandler):

    def _send_html(self, html, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


    def do_GET(self):
        if self.path == "/":
            html = (TEMPLATES_DIR / "menu.html").read_text(encoding="utf-8")
            self._send_html(html)
            return

        if self.path == "/start":
            html = (TEMPLATES_DIR / "start.html").read_text(encoding="utf-8")
            self._send_html(html)
            return

        if self.path.startswith("/game"):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            #создание игры
            if "name" in query:
                name = query["name"][0].strip()
                if not name:
                    self.send_error(400, "Empty name")
                    return
                game_id, game = new_game(name)
                self.send_response(302)
                self.send_header("Location", f"/game?g={game_id}")
                self.end_headers()
                return

            #достать игру !!!!!!!!!!!!!!!!!!!!IDOR: любой g открывает чужую игру!!!!!!!!!!!!!!!!!!!!!!!!!!
            g = query.get("g", [""])[0]
            if g not in games:
                self.send_error(404, "Game not found")
                return
            game = games[g]

            #клик по двери
            if "door" in query:
                d = query["door"][0]
                if d not in ("1", "2", "3"):
                    self.send_error(400, "Bad door")
                    return
                result = step(game, int(d))

                if result == "win":
                    save_score(game["name"], TOTAL_ROOMS, game["presents"], "win")
                    self._send_html(render_end_page("win", game))
                    return
                if result == "lose":
                    rooms_passed = game["room"] - 1   # 1-based → сколько ПРОЙДЕНО
                    save_score(game["name"], rooms_passed, 0, "lose")
                    self._send_html(render_end_page("lose", game))
                    return
                if result == "bad":
                    self._send_html(render_bad_door_page(g, game))
                    return
                
                #result == "good": PRG — редирект, чтобы F5 не повторял клик
                self.send_response(302)
                self.send_header("Location", f"/game?g={g}")
                self.end_headers()
                return

            #показ страницы (проверка конца — для F5 после конца)
            if game["presents"] <= 0:
                self._send_html(render_end_page("lose", game))
            elif game["room"] > TOTAL_ROOMS:
                self._send_html(render_end_page("win", game))
            else:
                self._send_html(render_game_page(g, game))
            return

        #/static/ !!!!!!!!!!!!!!!!!!11!!! Path Traversal: не проверки startswith!!!!!!!!!!!!!!!!!
        if self.path.startswith("/static/"):
            rel_path = self.path[len("/static/"):]
            file_path = (BASE_DIR / "static" / rel_path).resolve()
            if not file_path.is_file():
                self.send_error(404, "File not found")
                return
            content_type, _ = mimetypes.guess_type(str(file_path))
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type",
                             content_type or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_error(404, "Not found")

if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Сервер запущен: http://{HOST}:{PORT}")
    print("Остановить: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
        server.server_close()