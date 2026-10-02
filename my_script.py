import json                     # Сериализация словаря в JSON
import os                       # Основной источник данных об ОС, путях, окружении
import platform                 # Дополняет os там, где os не даёт данных (ядро, arch, processor)
import socket                   # hostname и FQDN
import sys                      # sys.platform, sys.maxsize, sys.executable, sys.getfilesystemencoding
from datetime import datetime   # Метка времени


def detect_os() -> str:
    if os.name == "nt":   # os.name == 'nt' — это Windows
        return "Windows"
    if os.name == "posix" and sys.platform.startswith("linux"):  # posix + префикс linux => Linux
        return "Linux"


def collect_os_info() -> dict: #Собирает словарь с параметрами текущей ОС и окружения
    info = {                                                          # Итоговый словарь
        "os": collect_os_block(),                                     # Группа: сама ОС
        "host": collect_host_block(),                                 # Группа: хост
        "timestamp": datetime.now().isoformat(timespec="seconds"),    # Метка времени
    }
    return info


def collect_os_block() -> dict: #Информация о самой ОС: собираем всё, что даёт os, и добираем через platform
    return {
        "name": detect_os(),                                   # 'Windows' или 'Linux'
        "os_name": os.name,                                    # 'nt' или 'posix' — прямо из os
        "sys_platform": sys.platform,                          # 'win32' или 'linux' — прямо из sys
        "release": platform.release(),                         # Версия ядра/релиза (os этого не даёт)
        "version": platform.version(),                         # Детальная версия ОС
        "machine": platform.machine(),                         # Архитектура (os.uname() на Linux дал бы то же)
        "architecture": platform.architecture()[0],            # Разрядность интерпретатора
        "processor": platform.processor(),                     # Имя процессора (не всегда заполнено)
        "is_64bit": sys.maxsize > 2 ** 32,                     # True для 64-битного Python
        "cpu_count_logical": os.cpu_count(),                   # Число логических CPU — из os
        "cpu_count_available": len(os.sched_getaffinity(0))    # Доступные текущему процессу CPU (только Linux)
            if hasattr(os, "sched_getaffinity") else None,     # На Windows такого атрибута нет → None
        "path_separator": os.sep,                              # Разделитель пути ('/' или '\\') — из os
        "path_sep_in_PATH": os.pathsep,                        # Разделитель в PATH (':' или ';') — из os
        "line_separator": repr(os.linesep),                    # Символ перевода строки — из os
    }

#host
def collect_host_block() -> dict: #Имя хоста — через os.uname() на Linux, через socket на Windows
    result = {
        "hostname": socket.gethostname(),                      # Короткое сетевое имя
        "fqdn": socket.getfqdn(),                              # Полное доменное имя
    }
    # На Linux os.uname() даёт дополнительную информацию о ядре.
    if hasattr(os, "uname"):                                   # Атрибут есть только на Unix
        u = os.uname()                                         # Получаем именованный кортеж
        result["uname"] = {                                    # Складываем поля в под-словарь
            "sysname": u.sysname,                              # Имя системы (Linux)
            "nodename": u.nodename,                            # Сетевое имя узла
            "release": u.release,                              # Версия ядра
            "version": u.version,                              # Сборка ядра
            "machine": u.machine,                              # Аппаратная платформа
        }
    return result

#Запись в JSON
def save_to_json(data: dict, filename: str = "os_info.json") -> str: #Сохраняет словарь в JSON-файл и возвращает абсолютный путь
    path = os.path.abspath(filename)                           # Абсолютный путь к файлу
    with open(path, "w", encoding="utf-8") as f:               # Открываем на запись в UTF-8
        json.dump(data, f, indent=4, ensure_ascii=False)       # Пишем JSON с отступами
    return path                                                # Возвращаем путь


#Выход
def main() -> None:
    os_name = detect_os()                                      # Определяем ОС
    print(f"Обнаружена ОС: {os_name}")                     # Пишем в консоль

    data = collect_os_info()                                   # Собираем данные
    out_path = save_to_json(data)                              # Сохраняем в JSON

    print(f"Данные сохранены в: {out_path}")               # Сообщаем путь


if __name__ == "__main__":                                     # Только при прямом запуске
    main()                                                     # Вызываем main()
