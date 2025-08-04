import random
import threading
import time

class MorseLogic:
    """Управляет логикой уроков, генерацией упражнений и воспроизведением."""
    def __init__(self, characters_data: dict, lessons_data: dict, audio_player):
        self.audio_player = audio_player
        self.lessons_structure = lessons_data.get("course", [])
        self.char_map = {}
        # Объединяем все словари из characters_data в один для удобного поиска
        self.char_map.update(characters_data.get("alphabet", {}))
        self.char_map.update(characters_data.get("digits", {}))
        self.char_map.update(characters_data.get("signs", {}))

        self.is_playing = False
        self.playback_thread = None

    def get_lesson_chars(self, lesson_id: int):
        """Возвращает список символов для указанного урока."""
        for lesson in self.lessons_structure:
            if lesson['lesson_id'] == lesson_id:
                return lesson['chars']
        return []

    def generate_exercise_text(self, chars: list, num_groups: int, group_size=5):
        """Генерирует случайный текст для упражнения."""
        text = ""
        for _ in range(num_groups):
            group = "".join(random.choices(chars, k=group_size))
            text += group + " "
        return text.strip()

    def _play_morse_thread_target(self, text: str):
        """Целевая функция для потока воспроизведения."""
        self.is_playing = True
        print(f"Воспроизведение: {text}")
        for char in text:
            if not self.is_playing:
                print("Воспроизведение прервано.")
                break
                
            if char == ' ':
                self.audio_player.play_char_pause() # Дополнительная пауза для пробела
                continue

            morse_code = self.char_map.get(char.upper(), {}).get('code')
            if morse_code:
                for symbol in morse_code:
                    if symbol == '.':
                        self.audio_player.play_dot()
                    elif symbol == '-':
                        self.audio_player.play_dash()
                self.audio_player.play_char_pause()
            time.sleep(0.1) # Небольшая задержка, чтобы не нагружать CPU
        
        self.is_playing = False
        print("Воспроизведение завершено.")

    def start_playback(self, text: str):
        """Запускает воспроизведение Морзе в отдельном потоке."""
        if self.is_playing:
            print("Уже идет воспроизведение. Сначала остановите.")
            return

        self.playback_thread = threading.Thread(target=self._play_morse_thread_target, args=(text,))
        self.playback_thread.daemon = True # Поток завершится, если закроется основное приложение
        self.playback_thread.start()

    def stop_playback(self):
        """Останавливает текущее воспроизведение."""
        self.is_playing = False