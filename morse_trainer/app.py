import customtkinter as ctk
from .utils import load_json
from .audio_player import AudioPlayer
from .morse_logic import MorseLogic

class MorseTrainerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Загрузка конфигурации ---
        self.themes = load_json("config/themes.json")
        self.lessons_config = load_json("config/lessons.json")
        
        # --- Инициализация бэкенда ---
        self.audio_player = AudioPlayer()
        self.logic = MorseLogic(self.lessons_config, self.audio_player)
        
        # --- Настройка окна ---
        self.title("Morse Trainer NG")
        self.geometry("900x650")
        self.current_theme = "Deep Space" # Тема по умолчанию
        self._apply_theme()

        # --- Создание виджетов ---
        self._create_widgets()

    def _apply_theme(self):
        """Применяет выбранную цветовую тему."""
        theme_data = self.themes.get(self.current_theme, {})
        ctk.set_appearance_mode("dark")
        
        # Устанавливаем цвета для CustomTkinter.
        # Это упрощенный пример, можно сделать более детальную настройку
        ctk.set_default_color_theme("blue") # Базовая тема, на которую накладываются наши цвета
        self.configure(fg_color=theme_data.get("bg_color", "#2B2B2B"))

    def _create_widgets(self):
        """Создает и размещает все виджеты в окне."""
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        # --- Левая панель (сайдбар) ---
        sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=15)
        sidebar_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        sidebar_frame.pack_propagate(False) # Чтобы фрейм не сжимался

        # Блок выбора знаков
        signs_label = ctk.CTkLabel(sidebar_frame, text="CW Знаки", font=("Fira Code", 16, "bold"))
        signs_label.pack(pady=10, padx=10)
        
        # TODO: Добавить RadioButton для выбора знаков

        # Блок настроек скорости
        speed_label = ctk.CTkLabel(sidebar_frame, text="Скорость (WPM)", font=("Fira Code", 14))
        speed_label.pack(pady=(20, 5), padx=10)
        self.wpm_slider = ctk.CTkSlider(sidebar_frame, from_=5, to=40, number_of_steps=35, command=self._update_wpm)
        self.wpm_slider.set(20)
        self.wpm_slider.pack(pady=5, padx=20, fill="x")

        # Блок настроек тона
        tone_label = ctk.CTkLabel(sidebar_frame, text="Тон (Hz)", font=("Fira Code", 14))
        tone_label.pack(pady=(20, 5), padx=10)
        self.tone_slider = ctk.CTkSlider(sidebar_frame, from_=400, to=1000, command=self._update_tone)
        self.tone_slider.set(700)
        self.tone_slider.pack(pady=5, padx=20, fill="x")

        # --- Правая панель (основная) ---
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Верхний блок управления уроками
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        
        # TODO: Добавить выпадающие списки для урока и упражнения

        # Основной блок (для клавиатуры или текста)
        self.keyboard_frame = ctk.CTkFrame(main_frame)
        self.keyboard_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        # Нижний блок с кнопкой Старт
        start_button = ctk.CTkButton(main_frame, text="СТАРТ", font=("Fira Code", 18, "bold"),
                                     command=self._on_start_click, height=40)
        start_button.grid(row=2, column=0, padx=15, pady=15, sticky="ew")

    def _update_wpm(self, value):
        self.audio_player.set_wpm(int(value))

    def _update_tone(self, value):
        self.audio_player.set_tone(int(value))

    def _on_start_click(self):
        # Пример: берем символы из первого урока и генерируем текст
        lesson_chars = self.logic.get_lesson_chars(1)
        if lesson_chars:
            exercise_text = self.logic.generate_exercise_text(lesson_chars, num_groups=3)
            self.logic.start_playback(exercise_text)
        else:
            print("Урок не найден!")

    def on_closing(self):
        """Корректное завершение работы при закрытии окна."""
        print("Закрытие приложения...")
        self.logic.stop_playback()
        self.audio_player.stop()
        self.destroy()