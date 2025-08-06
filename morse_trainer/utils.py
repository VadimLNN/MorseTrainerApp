import sys
import json
import os

def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсу, работает как для скрипта, так и для .exe """
    try:
        # PyInstaller создает временную папку и кладет путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_json(file_path: str):
    """Безопасно загружает JSON файл."""
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл конфигурации не найден по пути {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")
        return None

def save_json(data, file_path: str):
    """Безопасно сохраняет данные в JSON файл."""
    try:
        # Убедимся, что директория существует
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении файла {file_path}: {e}")
        return False

    