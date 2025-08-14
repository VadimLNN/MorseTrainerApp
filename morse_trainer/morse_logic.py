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

        self.keyboard_layout = characters_data.get("keyboard_layout", ["ABC", "123"])

        self.char_map = {
            "alphabet": characters_data.get("alphabet", {}),
            "digits": characters_data.get("digits", {}),
            "signs": characters_data.get("signs", {})
        }
        # Создаем "плоскую" версию только для быстрого поиска кода/напева
        self._flat_char_map = {}
        self._flat_char_map.update(self.char_map["alphabet"])
        self._flat_char_map.update(self.char_map["digits"])
        self._flat_char_map.update(self.char_map["signs"])

        self.is_playing = False
        self.playback_thread = None

    def get_keyboard_layout(self):
        """
        Возвращает раскладку клавиатуры, загруженную из файла конфигурации.
        """
        return self.keyboard_layout

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

    def _play_morse_thread_target(self, text: str, on_complete_callback=None):
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

            morse_code = self._flat_char_map.get(char.upper(), {}).get('code')
            if morse_code:
                for symbol in morse_code:
                    if symbol == '•':
                        self.audio_player.play_dot()
                    elif symbol == '–':
                        self.audio_player.play_dash()
                self.audio_player.play_char_pause()
            time.sleep(0.1) # Небольшая задержка, чтобы не нагружать CPU
        
        self.is_playing = False
        print("Воспроизведение завершено.")

        if on_complete_callback:
            on_complete_callback(text)

    def start_playback(self, text: str, on_complete=None):
        """Запускает воспроизведение Морзе в отдельном потоке."""
        if self.is_playing:
            print("Уже идет воспроизведение. Сначала остановите.")
            return
        
        self.playback_thread = threading.Thread(
            target=self._play_morse_thread_target, 
            args=(text, on_complete) # <-- Передаем callback в поток
        )
        self.playback_thread.daemon = True # Поток завершится, если закроется основное приложение
        self.playback_thread.start()

    def stop_playback(self):
        """Останавливает текущее воспроизведение."""
        self.is_playing = False

    def get_char_details(self, char: str):
        """Возвращает детали для одного символа (код и напев)."""
        return self._flat_char_map.get(char.upper())

    def get_character_pool(self, mode: str, lesson_id: int, exercise_type: str, custom_list: list):
        """
        Определяет набор символов для упражнения в зависимости от режима тренировки.
        
        Args:
            mode (str): Текущий режим ('base', 'letters', 'digits', 'custom').
            lesson_id (int): ID текущего урока (используется только в режиме 'base').
            exercise_type (str): Тип упражнения.
            custom_list (list): Список символов, выбранных пользователем.
        
        Returns:
            list: Список символов для текущего упражнения.
        """
        if mode == "letters":
            return self.get_all_letters()
            
        elif mode == "digits":
            return self.get_all_digits()
            
        elif mode == "custom":
            return custom_list
            
        elif mode == "base":
            # --- Старая логика для режима "База" ---
            if exercise_type in ["study", "single_char_recognition_lesson"]:
                for lesson in self.course_data:
                    if lesson['lesson_id'] == lesson_id:
                        return lesson.get('new_chars', [])
                return []
            
            elif exercise_type in ["single_char_recognition_cumulative", "group_reception"]:
                cumulative_chars = []
                for lesson in self.course_data:
                    if lesson['lesson_id'] <= lesson_id:
                        cumulative_chars.extend(lesson.get('new_chars', []))
                return list(dict.fromkeys(cumulative_chars))
            
        return []

    def get_all_letters(self):
        """Возвращает список всех букв из конфигурации."""
        return list(self.char_map.get("alphabet", {}).keys())

    def get_all_digits(self):
        """Возвращает список всех цифр из конфигурации."""
        return list(self.char_map.get("digits", {}).keys())
    