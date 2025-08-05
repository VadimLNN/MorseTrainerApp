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
        self.wpm_slider.set(20)
        self.wpm_slider.pack(pady=5, padx=20, fill="x")

        tone_label = ctk.CTkLabel(sidebar_frame, text="Тон (Hz)", font=("Fira Code", 14))
        tone_label.pack(pady=(20, 5), padx=20, anchor="w")
        self.tone_slider = ctk.CTkSlider(sidebar_frame, from_=400, to=1000, command=self._update_tone)
        self.tone_slider.set(700)
        self.tone_slider.pack(pady=5, padx=20, fill="x")

        volume_label = ctk.CTkLabel(sidebar_frame, text="Громкость (%)", font=("Fira Code", 14))
        volume_label.pack(pady=(20, 5), padx=20, anchor="w")
        self.volume_slider = ctk.CTkSlider(sidebar_frame, from_=0, to=100, command=self._update_volume)
        self.volume_slider.set(50) # Ставим громкость по умолчанию
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
        self.exercise_optionmenu = ctk.CTkOptionMenu(controls_frame, values=["Загрузка..."])
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
        footer_frame.grid_columnconfigure(1, weight=1)
        
        footer_frame.grid_columnconfigure(0, weight=1) # Левый переключатель
        footer_frame.grid_columnconfigure(1, weight=2) # Кнопка СТАРТ
        footer_frame.grid_columnconfigure(2, weight=2) # Кнопка СТОП
        footer_frame.grid_columnconfigure(3, weight=1) # Правый переключатель

        self.mnemonics_switch = ctk.CTkSwitch(footer_frame, text="Напевы")
        self.mnemonics_switch.grid(row=0, column=0, padx=10)
        
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
            self.exercise_optionmenu.set(exercise_names[0])

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
        selected_lesson_str = self.lesson_optionmenu.get()
        selected_exercise_str = self.exercise_optionmenu.get()
        if not selected_lesson_str or not selected_exercise_str:
            return

        lesson_id = int(selected_lesson_str.split(':')[0])
        exercise_id = int(selected_exercise_str.split(':')[0])
        
        exercise = self.logic.get_exercise_details(lesson_id, exercise_id)
        if not exercise:
            return

        exercise_type = exercise['type']
        char_pool = self.logic.get_character_pool(lesson_id, exercise_type)
        
        print(f"Запуск: Урок {lesson_id}, Упр. {exercise_id}, Тип: {exercise_type}")
        print(f"Доступные символы: {char_pool}")
        
        self._reconfigure_ui_for_exercise(exercise_type, char_pool)
        
        if exercise_type == "study":
            pass
            
        elif exercise_type in ["single_char_recognition_lesson", "single_char_recognition_cumulative"]:
            if char_pool:
                random_char = random.choice(char_pool)
                self.logic.start_playback(random_char)
            
        elif exercise_type == "group_reception":
            num_groups = int(self.groups_optionmenu.get())
            group_size = int(self.group_size_optionmenu.get())
            
            if char_pool:
                exercise_text = self.logic.generate_exercise_text(char_pool, num_groups, group_size)
                self.logic.start_playback(exercise_text)

    def _on_stop_click(self):
        """Обрабатывает нажатие на кнопку СТОП."""
        print("Нажата кнопка СТОП.")
        self.logic.stop_playback()

    def _reconfigure_ui_for_exercise(self, exercise_type: str, char_pool: list):
        for widget in self.keyboard_frame.winfo_children():
            widget.destroy()
        
        # Заглушки для разных режимов
        if exercise_type == "study":
            label = ctk.CTkLabel(self.keyboard_frame, text="Режим изучения. (Интерфейс в разработке)")
            label.pack(pady=20, padx=10)

        elif "recognition" in exercise_type:
            label = ctk.CTkLabel(self.keyboard_frame, text="Режим распознавания. (Интерфейс в разработке)")
            label.pack(pady=20, padx=10)

        elif exercise_type == "group_reception":
            label = ctk.CTkLabel(self.keyboard_frame, text="Прием групп. Слушайте внимательно...")
            label.pack(pady=50, padx=10)

    def on_closing(self):
        print("Закрытие приложения...")
        self.logic.stop_playback()
        self.audio_player.stop()
        self.destroy()