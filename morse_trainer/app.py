import customtkinter as ctk
import random
from .utils import load_json
from .audio_player import AudioPlayer
from .morse_logic import MorseLogic

class MorseTrainerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Загрузка конфигурации ---
        self.themes = load_json("config/themes.json")
        self.characters_data = load_json("config/characters.json")
        self.lessons_data = load_json("config/lessons.json")
        
        # --- Инициализация бэкенда ---
        self.audio_player = AudioPlayer()
        self.logic = MorseLogic(self.characters_data, self.lessons_data, self.audio_player)

        self.output_textbox = None
        self.study_char_label = None
        self.study_code_label = None
        self.study_mnemonic_label = None
        self.current_correct_char = None
        self.keyboard_buttons = {}
        self.rounds_left = 0
        self.current_char_pool = []
        self.info_label = None

        # --- Настройка окна ---
        self.title("Morse Trainer NG")
        self.geometry("900x650")
        self.current_theme = "Deep Space"
        self._apply_theme()

        # --- Создание виджетов ---
        self._create_widgets()
        self._populate_lesson_menu() # Заполняем меню уроками при старте

    def _apply_theme(self):
        theme_data = self.themes.get(self.current_theme, {})
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=theme_data.get("bg_color", "#2B2B2B"))

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1, minsize=220)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        # --- Левая панель (сайдбар) ---
        sidebar_frame = ctk.CTkFrame(self, corner_radius=15)
        sidebar_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        # Настройки звука и скорости
        speed_label = ctk.CTkLabel(sidebar_frame, text="Скорость (WPM)", font=("Fira Code", 14))
        speed_label.pack(pady=(15, 5), padx=20, anchor="w")
        self.wpm_slider = ctk.CTkSlider(sidebar_frame, from_=5, to=40, number_of_steps=35, command=self._update_wpm)
        self.wpm_slider.set(10)
        self.wpm_slider.pack(pady=5, padx=20, fill="x")

        tone_label = ctk.CTkLabel(sidebar_frame, text="Тон (Hz)", font=("Fira Code", 14))
        tone_label.pack(pady=(20, 5), padx=20, anchor="w")
        self.tone_slider = ctk.CTkSlider(sidebar_frame, from_=400, to=1000, command=self._update_tone)
        self.tone_slider.set(700)
        self.tone_slider.pack(pady=5, padx=20, fill="x")

        volume_label = ctk.CTkLabel(sidebar_frame, text="Громкость (%)", font=("Fira Code", 14))
        volume_label.pack(pady=(20, 5), padx=20, anchor="w")
        self.volume_slider = ctk.CTkSlider(sidebar_frame, from_=0, to=100, command=self._update_volume)
        self.volume_slider.set(20) # Ставим громкость по умолчанию
        self.volume_slider.pack(pady=5, padx=20, fill="x")

        # --- Правая панель (основная) ---
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Верхний блок управления
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        controls_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        lesson_label = ctk.CTkLabel(controls_frame, text="Урок:")
        lesson_label.grid(row=0, column=0, padx=5, sticky="w")
        self.lesson_optionmenu = ctk.CTkOptionMenu(controls_frame, values=["Загрузка..."])
        self.lesson_optionmenu.grid(row=1, column=0, padx=5, sticky="ew")

        exercise_label = ctk.CTkLabel(controls_frame, text="Упр.:")
        exercise_label.grid(row=0, column=1, padx=5, sticky="w")
        self.exercise_optionmenu = ctk.CTkOptionMenu(controls_frame, values=["Загрузка..."],
            command=self._on_exercise_selected)
        self.exercise_optionmenu.grid(row=1, column=1, padx=5, sticky="ew")

        groups_label = ctk.CTkLabel(controls_frame, text="Группы:")
        groups_label.grid(row=0, column=2, padx=5, sticky="w")
        self.groups_optionmenu = ctk.CTkOptionMenu(controls_frame, values=[str(i) for i in range(1, 21)])
        self.groups_optionmenu.set("10")
        self.groups_optionmenu.grid(row=1, column=2, padx=5, sticky="ew")

        group_size_label = ctk.CTkLabel(controls_frame, text="Знаков в группе:")
        group_size_label.grid(row=0, column=3, padx=5, sticky="w")
        self.group_size_optionmenu = ctk.CTkOptionMenu(controls_frame, values=[str(i) for i in range(2, 8)])
        self.group_size_optionmenu.set("5")
        self.group_size_optionmenu.grid(row=1, column=3, padx=5, sticky="ew")

        # Основной рабочий блок
        self.keyboard_frame = ctk.CTkFrame(main_frame)
        self.keyboard_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        # Нижний блок управления
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_frame.grid(row=2, column=0, padx=15, pady=15, sticky="ew")
        
        footer_frame.grid_columnconfigure(0, weight=2) # Кнопка СТАРТ
        footer_frame.grid_columnconfigure(1, weight=2) # Кнопка СТОП
        footer_frame.grid_columnconfigure(2, weight=1) # Правый переключатель

        start_button = ctk.CTkButton(footer_frame, text="СТАРТ", font=("Fira Code", 18, "bold"),
                                     command=self._on_start_click, height=40)
        start_button.grid(row=0, column=1, sticky="ew", padx=10)
        
        stop_button = ctk.CTkButton(footer_frame, text="СТОП", font=("Fira Code", 18, "bold"),
                                    command=self._on_stop_click, height=40,
                                    fg_color="#D32F2F", hover_color="#B71C1C") # Красный цвет для стоп-кнопки
        stop_button.grid(row=0, column=2, sticky="ew", padx=5)

        self.sound_type_switch = ctk.CTkSwitch(footer_frame, text="Дискретный звук",
                                               command=self._update_sound_type)
        self.sound_type_switch.grid(row=0, column=3, padx=10)

    def _populate_lesson_menu(self):
        lessons_info = self.logic.get_all_lessons_info()
        lesson_names = [f"{lid}: {name}" for lid, name in lessons_info]
        self.lesson_optionmenu.configure(values=lesson_names, command=self._on_lesson_selected)
        if lesson_names:
            self.lesson_optionmenu.set(lesson_names[0])
            self._on_lesson_selected(lesson_names[0])

    def _on_lesson_selected(self, selected_lesson_name: str):
        lesson_id = int(selected_lesson_name.split(':')[0])
        exercises_info = self.logic.get_exercises_for_lesson(lesson_id)
        exercise_names = [f"{eid}: {desc}" for eid, desc in exercises_info]
        self.exercise_optionmenu.configure(values=exercise_names)
        if exercise_names:
            exercise_to_select = exercise_names[0]
            self.exercise_optionmenu.set(exercise_to_select)
            self._on_exercise_selected(exercise_to_select)

    def _on_exercise_selected(self, selected_exercise_name: str):
        """Вызывается при выборе упражнения. СРАЗУ меняет интерфейс."""
        selected_lesson_str = self.lesson_optionmenu.get()
        if not selected_lesson_str or not selected_exercise_name:
            return

        lesson_id = int(selected_lesson_str.split(':')[0])
        exercise_id = int(selected_exercise_name.split(':')[0])

        exercise = self.logic.get_exercise_details(lesson_id, exercise_id)
        if not exercise:
            return

        exercise_type = exercise['type']

        self.current_char_pool = self.logic.get_character_pool(lesson_id, exercise_type)

        self._reconfigure_ui_for_exercise(exercise_type)

    def _update_wpm(self, value):
        self.audio_player.set_wpm(int(value))

    def _update_tone(self, value):
        self.audio_player.set_tone(int(value))

    def _update_volume(self, value):
        self.audio_player.set_volume(int(value))

    def _update_sound_type(self):
        """Обновляет тип звука в плеере в зависимости от состояния переключателя."""
        if self.sound_type_switch.get() == 1: # 1 - переключатель включен
            self.audio_player.set_sound_type("discrete")
        else: # 0 - переключатель выключен
            self.audio_player.set_sound_type("analog")

    def _on_start_click(self):
        """Запускает ДЕЙСТВИЕ для текущего выбранного упражнения."""
        selected_lesson_str = self.lesson_optionmenu.get()
        selected_exercise_str = self.exercise_optionmenu.get()
        if not selected_lesson_str or not selected_exercise_str:
            return

        lesson_id = int(selected_lesson_str.split(':')[0])
        exercise_id = int(selected_exercise_str.split(':')[0])
        
        exercise = self.logic.get_exercise_details(lesson_id, exercise_id)
        if not exercise: return

        exercise_type = exercise['type']
        char_pool = self.logic.get_character_pool(lesson_id, exercise_type)
        
        print(f"СТАРТ для: Урок {lesson_id}, Упр. {exercise_id}, Тип: {exercise_type}")
        
        if exercise_type == "study":
            # В этом режиме кнопка СТАРТ ничего не делает, т.к. все по клику/наведению
            print("В режиме изучения кнопка СТАРТ неактивна.")
            pass
            
        elif "recognition" in exercise_type:
            # ИСПРАВЛЕНО: Инициализируем счетчик раундов
            num_groups = int(self.groups_optionmenu.get())
            group_size = int(self.group_size_optionmenu.get())
            self.rounds_left = num_groups * group_size
            
            if self.rounds_left > 0:
                self._start_recognition_round()
            else:
                print("Количество раундов должно быть больше 0.")
            
        elif exercise_type == "group_reception":
            if self.output_textbox:
                self.output_textbox.delete("1.0", "end")
                self.output_textbox.insert("1.0", "Прием...")

            num_groups = int(self.groups_optionmenu.get())
            group_size = int(self.group_size_optionmenu.get())
            
            if char_pool:
                exercise_text = self.logic.generate_exercise_text(char_pool, num_groups, group_size)
                self.logic.start_playback(
                    exercise_text, 
                    on_complete=lambda text: self.after(10, self._on_playback_complete, text)
                )

    def _on_playback_complete(self, text: str):
        """Этот метод будет вызван БЕЗОПАСНО из главного потока."""
        print(f"Воспроизведение завершено. Выводим текст: {text}")
        
        if self.output_textbox:
            # Вставляем текст, отформатированный в группы по 5 знаков
            formatted_text = ""
            words = text.split()
            for i, word in enumerate(words):
                formatted_text += word + " "
                if (i + 1) % 5 == 0: # Перенос строки каждые 5 групп
                    formatted_text += "\n"
            
            self.output_textbox.delete("1.0", "end") # Очищаем
            self.output_textbox.insert("1.0", formatted_text.strip())

    def _reconfigure_ui_for_exercise(self, exercise_type: str):
        """Перестраивает основной рабочий блок (keyboard_frame) под тип упражнения."""
        # Очищаем старые виджеты
        for widget in self.keyboard_frame.winfo_children():
            widget.destroy()
        
        # Обнуляем ссылки на старые виджеты
        self.output_textbox = None
        self.study_char_label = None
        self.study_code_label = None
        self.study_mnemonic_label = None
        self.current_correct_char = None
        self.keyboard_buttons = {}

        self.info_label = None

        if exercise_type == "study":
            # --- РЕАЛИЗАЦИЯ РЕЖИМА ИЗУЧЕНИЯ ---
            self.keyboard_frame.grid_rowconfigure(0, weight=3) # Дисплей занимает больше места
            self.keyboard_frame.grid_rowconfigure(1, weight=1) # Кнопки занимают меньше
            self.keyboard_frame.grid_columnconfigure(0, weight=1)

            # 1. Создаем фрейм для центрального дисплея
            display_frame = ctk.CTkFrame(self.keyboard_frame, corner_radius=10)
            display_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            
            display_frame.grid_rowconfigure(0, weight=1)
            display_frame.grid_columnconfigure(0, weight=1)

            self.study_char_label = ctk.CTkLabel(display_frame, text="?", font=("JetBrains Mono", 120, "bold"))
            self.study_char_label.place(relx=0.5, rely=0.35, anchor="center")
            
            self.study_code_label = ctk.CTkLabel(display_frame, text="", font=("JetBrains Mono", 40))
            self.study_code_label.place(relx=0.5, rely=0.65, anchor="center")

            self.study_mnemonic_label = ctk.CTkLabel(display_frame, text="", font=("Fira Code", 20, "italic"))
            self.study_mnemonic_label.place(relx=0.5, rely=0.85, anchor="center")

            # 2. Создаем фрейм для кнопок
            buttons_frame = ctk.CTkFrame(self.keyboard_frame, fg_color="transparent")
            buttons_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

            # 3. Создаем сами кнопки и привязываем события
            for i, char in enumerate(self.current_char_pool):
                buttons_frame.grid_columnconfigure(i, weight=1)
                
                button = ctk.CTkButton(
                    buttons_frame, text=char,
                    font=("Fira Code", 24, "bold"),
                    command=lambda c=char: self._on_study_button_click(c)
                )
                button.grid(row=0, column=i, padx=5, pady=5, sticky="ew")

                button.bind("<Enter>", lambda event, c=char: self._on_study_button_enter(event, c))
                button.bind("<Leave>", self._on_study_button_leave)

        elif exercise_type == "group_reception":
            self.output_textbox = ctk.CTkTextbox(self.keyboard_frame, 
                                                 font=("JetBrains Mono", 18),
                                                 corner_radius=10,
                                                 wrap="word")
            self.output_textbox.pack(expand=True, fill="both", padx=5, pady=5)
            self.output_textbox.insert("1.0", "Готов к приему групп...\nНажмите 'СТАРТ'")

        elif "recognition" in exercise_type:
            self.info_label = ctk.CTkLabel(self.keyboard_frame, text="Нажмите 'СТАРТ', чтобы начать", font=("Fira Code", 16))
            self.info_label.pack(pady=10)

            # Создаем фрейм для самой клавиатуры
            kb_frame = ctk.CTkFrame(self.keyboard_frame, fg_color="transparent")
            kb_frame.pack(expand=True, fill="both", padx=5, pady=5)

            # Определяем раскладку клавиатуры
            layout = [
                "ЙЦУКЕНГШЩЗХЪ",
                "ФЫВАПРОЛДЖЭ",
                "ЯЧСМИТЬБЮ",
                "1234567890",
                ".,?/+="
            ]
            
            # Создаем кнопки для всей раскладки
            for row_idx, row_chars in enumerate(layout):
                kb_frame.rowconfigure(row_idx, weight=1)
                for col_idx, char in enumerate(row_chars):
                    kb_frame.columnconfigure(col_idx, weight=1)
                    
                    is_active = char in self.current_char_pool
                    
                    button = ctk.CTkButton(
                        kb_frame, text=char,
                        font=("Fira Code", 16, "bold"),
                        # Привязываем команду ко всем кнопкам
                        command=lambda c=char: self._on_recognition_button_click(c)
                    )
                    
                    # Визуально "выключаем" неактивные, но оставляем их рабочими
                    if not is_active:
                        # Убираем state="disabled"
                        button.configure(fg_color="gray20", text_color="gray50", hover=False)
                    
                    button.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")
                    self.keyboard_buttons[char] = button
                    
                    button.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")
                    self.keyboard_buttons[char] = button 

    def _on_stop_click(self):
        """Обрабатывает нажатие на кнопку СТОП."""
        print("Нажата кнопка СТОП.")
        self.logic.stop_playback()
    
    def on_closing(self):
        print("Закрытие приложения...")
        self.logic.stop_playback()
        self.audio_player.stop()
        self.destroy()

    def _on_study_button_enter(self, event, char: str):
        """Вызывается при наведении мыши на кнопку символа."""
        char_details = self.logic.get_char_details(char)
        if not char_details:
            return

        # Обновляем центральный дисплей
        if self.study_char_label:
            self.study_char_label.configure(text=char)
        if self.study_code_label:
            self.study_code_label.configure(text=char_details.get('code', ''))
        if self.study_mnemonic_label:
            self.study_mnemonic_label.configure(text=char_details.get('mnemonic', ''))

    def _on_study_button_leave(self, event):
        """Вызывается, когда мышь уходит с кнопки."""
        # Очищаем дисплей
        if self.study_char_label:
            self.study_char_label.configure(text="?")
        if self.study_code_label:
            self.study_code_label.configure(text="")
        if self.study_mnemonic_label:
            self.study_mnemonic_label.configure(text="")

    def _on_study_button_click(self, char: str):
        """Вызывается при клике на кнопку. ТОЛЬКО ПРОИГРЫВАЕТ ЗВУК."""
        self.logic.start_playback(char)

    def _start_recognition_round(self):
        """Запускает один раунд игры в распознавание."""
        if self.rounds_left <= 0: return

        if self.info_label: # Безопасная проверка
            self.info_label.configure(text=f"Прием... Осталось знаков: {self.rounds_left}")

        info_label = self.keyboard_frame.winfo_children()[0]
        info_label.configure(text=f"Прием... Осталось знаков: {self.rounds_left}")

        selected_lesson_str = self.lesson_optionmenu.get()
        exercise = self.logic.get_exercise_details(int(selected_lesson_str.split(':')[0]), int(self.exercise_optionmenu.get().split(':')[0]))
        char_pool = self.logic.get_character_pool(int(selected_lesson_str.split(':')[0]), exercise['type'])
        
        if not char_pool: return

        self.current_correct_char = random.choice(self.current_char_pool)
        print(f"Новый раунд. Загадан знак: '{self.current_correct_char}'")
        self.logic.start_playback(self.current_correct_char)
    
    def _on_recognition_button_click(self, char: str):
        """
        Обрабатывает нажатие на кнопку в режиме распознавания.
        Эта функция теперь быстрая, чистая и занимается только своим делом.
        """
        # 1. Проверяем, активна ли кнопка (не делаем лишних вычислений)
        if char not in self.current_char_pool:
            print(f"Нажата неактивная кнопка: {char}")
            return
        
        # 2. Проверяем, идет ли сейчас раунд
        if not self.current_correct_char:
            print("Нет активного знака для угадывания. Нажмите СТАРТ.")
            return

        # 3. Получаем виджет кнопки
        button = self.keyboard_buttons.get(char)
        if not button: return

        original_color = button.cget("fg_color")

        # 4. Сравниваем ответ и даем обратную связь
        if char == self.current_correct_char:
            # --- ВЕТКА ПРАВИЛЬНОГО ОТВЕТА ---
            print(f"Правильно! Это была '{char}'")
            self.rounds_left -= 1
            print(f"Раундов осталось: {self.rounds_left}")

            button.configure(fg_color="green")
            self.after(200, lambda: button.configure(fg_color=original_color))
            
            if self.rounds_left > 0:
                self.after(300, self._start_recognition_round)
            else:
                print("Упражнение завершено!")
                self.current_correct_char = None
                if self.info_label:
                    self.info_label.configure(text="Упражнение завершено! Нажмите 'СТАРТ' для начала.")
        else:
            # --- ВЕТКА НЕПРАВИЛЬНОГО ОТВЕТА ---
            print(f"Неправильно. Вы нажали '{char}', а было '{self.current_correct_char}'")
            self.show_error_and_replay(self.current_correct_char, start_new_round=True)
    
    def show_error_and_replay(self, correct_char: str, start_new_round: bool = False):
        """Показывает модальное окно с правильным ответом и проигрывает его 3 раза."""
        error_window = ctk.CTkToplevel(self)
        error_window.title("Ошибка")
        error_window.geometry("300x150")
        error_window.transient(self)
        error_window.grab_set()
        error_window.resizable(False, False)

        label = ctk.CTkLabel(error_window, text=f"Ошибка!\nПравильный знак: {correct_char}", font=("Fira Code", 20))
        label.pack(expand=True, pady=20)

        def replay_and_close(count=3):
            if count > 0:
                self.logic.start_playback(correct_char, on_complete=lambda text: error_window.after(300, replay_and_close, count - 1))
            else:
                error_window.grab_release()
                error_window.destroy()
                # ИСПРАВЛЕНО: Запускаем новый раунд, если нужно
                if start_new_round and self.rounds_left > 0:
                    self.after(100, self._start_recognition_round)

        replay_and_close()




