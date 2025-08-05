import random
import threading
import time

class MorseLogic:
    """Управляет логикой уроков, генерацией упражнений и воспроизведением."""
    def __init__(self, characters_data: dict, lessons_data: dict, audio_player):
        self.audio_player = audio_player
        self.course_data = lessons_data.get("course", [])
        self.char_map = {}

        self.exercise_types = lessons_data.get("exercise_types", {})

        # Объединяем все словари из characters_data в один для удобного поиска
        self.char_map.update(characters_data.get("alphabet", {}))
        self.char_map.update(characters_data.get("digits", {}))
        self.char_map.update(characters_data.get("signs", {}))

        self.is_playing = False
        self.playback_thread = None

    def get_all_lessons_info(self):
        """Возвращает список ID и имен всех уроков для GUI."""
        return [(lesson['lesson_id'], lesson['name']) for lesson in self.course_data]

    def get_exercises_for_lesson(self, lesson_id: int):
        """Возвращает список ID и описаний упражнений для урока."""
        for lesson in self.course_data:
            if lesson['lesson_id'] == lesson_id:
                # Новая логика: ищем описания в глобальном списке по ID
                exercise_ids = lesson.get('exercise_ids', [])
                return [(eid, self.exercise_types.get(str(eid), {}).get('description', 'Неизвестное упр.')) for eid in exercise_ids]
        return []

    def get_exercise_details(self, lesson_id: int, exercise_id: int):
        """Возвращает полный объект упражнения по его ID."""
        # Теперь просто ищем описание в глобальном списке
        exercise_info = self.exercise_types.get(str(exercise_id))
        if not exercise_info:
            return None
        # Возвращаем копию, чтобы случайно не изменить оригинал
        return exercise_info.copy()

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

    def get_character_pool(self, lesson_id: int, exercise_type: str):
        """Определяет набор символов для упражнения в зависимости от его типа."""
        
        # Упражнение 1 и 2: только новые знаки текущего урока
        if exercise_type in ["study", "single_char_recognition_lesson"]:
            for lesson in self.course_data:
                if lesson['lesson_id'] == lesson_id:
                    return lesson.get('new_chars', [])
            return []
            
        # Упражнение 3 и 4: все изученные знаки (текущий урок + все предыдущие)
        elif exercise_type in ["single_char_recognition_cumulative", "group_reception"]:
            cumulative_chars = []
            for lesson in self.course_data:
                # Добавляем знаки, если урок не "старше" текущего
                if lesson['lesson_id'] <= lesson_id:
                    cumulative_chars.extend(lesson.get('new_chars', []))
            return list(dict.fromkeys(cumulative_chars)) # Удаляем дубликаты, сохраняя порядок
            
        return []

