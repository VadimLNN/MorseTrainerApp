from customtkinter.windows.widgets.font import CTkFont
import customtkinter as ctk
import random
from .utils import load_json
from .audio_player import AudioPlayer
from .morse_logic import MorseLogic
from PIL import Image

class MorseTrainerApp(ctk.CTk):
    def __init__(self):
        """Конструктор приложения."""
        super().__init__()
        # --- БЛОК 1: ЗАГРУЗКА КОНФИГУРАЦИЙ ---
        self.themes = load_json("config/themes.json")
        self.characters_data = load_json("config/characters.json")
        self.lessons_data = load_json("config/lessons.json")
        
        # --- БЛОК 2: АТРИБУТЫ СОСТОЯНИЯ ---
        self.current_theme = "Deep Space"
        self.fonts = {}
        self.current_char_pool = []
        self.current_correct_char = None
        self.rounds_left = 0
        
        # --- БЛОК 3: ИНИЦИАЛИЗАЦИЯ БЭКЕНДА ---
        self.audio_player = AudioPlayer()
        self.logic = MorseLogic(self.characters_data, self.lessons_data, self.audio_player)
        
        # --- БЛОК 4: ИНИЦИАЛИЗАЦИЯ ССЫЛОК НА ВИДЖЕТЫ ---
        self._initialize_widget_references()

        # --- БЛОК 5: НАСТРОЙКА ОКНА И СОЗДАНИЕ ИНТЕРФЕЙСА ---
        self.title("Morse Trainer NG")
        self.geometry("900x650")
        
        self._create_widgets()
        self._populate_lesson_menu()
        self.after(100, self._apply_theme)

    def _initialize_widget_references(self):
        """Объявляет все переменные для виджетов как None."""
        self.bg_label = None
        self.sidebar_frame, self.main_frame = None, None
        self.theme_label, self.theme_menu = None, None
        self.speed_label, self.wpm_slider = None, None
        self.tone_label, self.tone_slider = None, None
        self.volume_label, self.volume_slider = None, None
        self.lesson_label, self.lesson_optionmenu = None, None
        self.exercise_label, self.exercise_optionmenu = None, None
        self.groups_label, self.groups_optionmenu = None, None
        self.group_size_label, self.group_size_optionmenu = None, None
        self.keyboard_frame = None
        self.start_button, self.stop_button, self.sound_type_switch = None, None, None
        self.info_label = None
        self.output_textbox = None
        self.study_char_label, self.study_code_label, self.study_mnemonic_label = None, None, None
        self.keyboard_buttons = {}

    def _on_theme_selected(self, theme_name: str):
        if not isinstance(theme_name, str) or theme_name not in self.themes: return
        self.current_theme = theme_name
        self._apply_theme()
        
    def _apply_theme(self):
        """Применяет стили из текущей темы ко ВСЕМ существующим виджетам."""
        theme_data = self.themes.get(self.current_theme)
        if not theme_data: return

        print(f"Применение стилей из темы '{self.current_theme}'...")
        self._load_fonts()
        self._update_background(theme_data)

        card_bg = theme_data.get("card_bg", "#343638")
        text_color = theme_data.get("text_color", "#dce4ee")
        button_bg = theme_data.get("button_bg", "#565b5e")
        button_hover = theme_data.get("button_hover", "#656b6e")
        accent_color = theme_data.get("accent_color", "#4a90e2")

        # Панели
        self.sidebar_frame.configure(fg_color=card_bg)
        self.main_frame.configure(fg_color=card_bg)
        self.keyboard_frame.configure(fg_color=card_bg)
        
        # Сайдбар
        self.theme_label.configure(font=self.fonts["main_bold"], text_color=text_color)
        self.theme_menu.configure(font=self.fonts["main_font"], text_color=text_color, fg_color=button_bg, button_color=button_bg, button_hover_color=button_hover, dropdown_font=self.fonts["main_font"])
        self.speed_label.configure(font=self.fonts["main_font"], text_color=text_color)
        self.wpm_slider.configure(button_color=button_bg, progress_color=accent_color, button_hover_color=button_hover)
        self.tone_label.configure(font=self.fonts["main_font"], text_color=text_color)
        self.tone_slider.configure(button_color=button_bg, progress_color=accent_color, button_hover_color=button_hover)
        self.volume_label.configure(font=self.fonts["main_font"], text_color=text_color)
        self.volume_slider.configure(button_color=button_bg, progress_color=accent_color, button_hover_color=button_hover)
        
        # Основная панель - управление
        self.lesson_label.configure(font=self.fonts["main_font"], text_color=text_color)
        self.lesson_optionmenu.configure(font=self.fonts["main_font"], text_color=text_color, fg_color=button_bg, button_color=button_bg, button_hover_color=button_hover, dropdown_font=self.fonts["main_font"])
        self.exercise_label.configure(font=self.fonts["main_font"], text_color=text_color)
        self.exercise_optionmenu.configure(font=self.fonts["main_font"], text_color=text_color, fg_color=button_bg, button_color=button_bg, button_hover_color=button_hover, dropdown_font=self.fonts["main_font"])
        self.groups_label.configure(font=self.fonts["main_font"], text_color=text_color)
        self.groups_optionmenu.configure(font=self.fonts["main_font"], text_color=text_color, fg_color=button_bg, button_color=button_bg, button_hover_color=button_hover, dropdown_font=self.fonts["main_font"])
        self.group_size_label.configure(font=self.fonts["main_font"], text_color=text_color)
        self.group_size_optionmenu.configure(font=self.fonts["main_font"], text_color=text_color, fg_color=button_bg, button_color=button_bg, button_hover_color=button_hover, dropdown_font=self.fonts["main_font"])
        
        # Основная панель - подвал
        self.start_button.configure(font=self.fonts["title_font"], fg_color=accent_color, text_color=text_color)
        self.stop_button.configure(font=self.fonts["title_font"], text_color=text_color)
        self.sound_type_switch.configure(font=self.fonts["main_font"], text_color=text_color, progress_color=accent_color)

        # Перерисовываем текущий интерфейс упражнения
        self._on_exercise_selected(self.exercise_optionmenu.get())
    
    def _update_background(self, theme_data: dict):
        """Обновляет фон главного окна (изображение или сплошной цвет)."""
        bg_image_path = theme_data.get("background_image")

        if bg_image_path:
            try:
                # Получаем актуальный размер окна. Если 0, используем геометрию по умолчанию.
                win_width = self.winfo_width() or int(self.geometry().split('x')[0])
                win_height = self.winfo_height() or int(self.geometry().split('x')[1].split('+')[0])

                bg_image = ctk.CTkImage(Image.open(bg_image_path), size=(win_width, win_height))
                
                if self.bg_label is None:
                    self.bg_label = ctk.CTkLabel(self, text="", image=bg_image)
                    self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                else:
                    self.bg_label.configure(image=bg_image)
                
                self.bg_label.lower() # Всегда держим фон сзади
            except Exception as e:
                print(f"Ошибка загрузки фонового изображения '{bg_image_path}': {e}")
                if self.bg_label:
                    self.bg_label.destroy()
                    self.bg_label = None
                # В случае ошибки ставим сплошной цвет
                self.configure(fg_color=theme_data.get("main_bg", "#2B2B2B"))
        else:
            if self.bg_label:
                self.bg_label.destroy()
                self.bg_label = None
            # Если фон не указан, ставим сплошной цвет
            self.configure(fg_color=theme_data.get("main_bg", "#2B2B2B"))

    def _stylize_widget(self, widget, theme_data: dict):
        """
        Рекурсивно применяет стили к виджету и его дочерним элементам.
        
        Эта функция - "движок" стилизации. Она определяет тип виджета
        и применяет к нему соответствующие цвета и шрифты из темы.
        """
        # --- Извлекаем цвета из темы с запасными значениями ---
        card_bg = theme_data.get("card_bg", "#343638")
        text_color = theme_data.get("text_color", "#dce4ee")
        button_bg = theme_data.get("button_bg", "#565b5e")
        button_hover = theme_data.get("button_hover", "#656b6e")

        try:
            widget_class_name = widget.winfo_class()

            # Стили для контейнеров (наших "карточек")
            if widget_class_name == "CTkFrame" and widget not in (self, self.sidebar_frame, self.main_frame):
                 if widget.cget("fg_color") != "transparent":
                    widget.configure(fg_color=card_bg)

            # Общие стили для разных типов виджетов
            elif widget_class_name == "CTkLabel":
                widget.configure(font=self.fonts["main_font"], text_color=text_color)
            elif widget_class_name == "CTkButton":
                widget.configure(font=self.fonts["main_font"], text_color=text_color, fg_color=button_bg, hover_color=button_hover)
            elif widget_class_name == "CTkOptionMenu":
                widget.configure(font=self.fonts["main_font"], text_color=text_color, fg_color=button_bg, button_hover_color=button_hover)
            elif widget_class_name == "CTkSlider":
                widget.configure(button_color=button_bg, progress_color=text_color, button_hover_color=button_hover)
            elif widget_class_name == "CTkSwitch":
                widget.configure(font=self.fonts["main_font"], text_color=text_color, progress_color=theme_data.get("accent_color", "#4a90e2"))

        except Exception:
            # Игнорируем ошибки для виджетов, которые не поддерживают определенные атрибуты (например, корневое окно)
            pass

        # Рекурсивный вызов для всех дочерних элементов
        for child in widget.winfo_children():
            self._stylize_widget(child, theme_data)

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1, minsize=250)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)
        self._create_sidebar()
        self._create_main_panel()

    def _create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=15)
        self.sidebar_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        
        self.theme_label = ctk.CTkLabel(self.sidebar_frame, text="Тема оформления: DOOM")
        self.theme_label.pack(pady=(15, 5), padx=20, anchor="w")
        theme_names = list(self.themes.keys())
        self.theme_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=theme_names, command=self._on_theme_selected)
        self.theme_menu.pack(pady=5, padx=20, fill="x")

        self.speed_label = ctk.CTkLabel(self.sidebar_frame, text="Скорость (WPM):")
        self.speed_label.pack(pady=(20, 5), padx=20, anchor="w")
        self.wpm_slider = ctk.CTkSlider(self.sidebar_frame, from_=5, to=40, number_of_steps=35, command=self._update_wpm)
        self.wpm_slider.pack(pady=5, padx=20, fill="x")
        self.wpm_slider.set(10)

        self.tone_label = ctk.CTkLabel(self.sidebar_frame, text="Тон (Hz):")
        self.tone_label.pack(pady=(20, 5), padx=20, anchor="w")
        self.tone_slider = ctk.CTkSlider(self.sidebar_frame, from_=400, to=1000, command=self._update_tone)
        self.tone_slider.pack(pady=5, padx=20, fill="x")
        self.tone_slider.set(700)

        self.volume_label = ctk.CTkLabel(self.sidebar_frame, text="Громкость (%):")
        self.volume_label.pack(pady=(20, 5), padx=20, anchor="w")
        self.volume_slider = ctk.CTkSlider(self.sidebar_frame, from_=0, to=100, command=self._update_volume)
        self.volume_slider.pack(pady=5, padx=20, fill="x")
        self.volume_slider.set(20)

    def _create_main_panel(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        controls_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.lesson_label = ctk.CTkLabel(controls_frame, text="Урок:")
        self.lesson_label.grid(row=0, column=0, padx=5, sticky="w")
        self.lesson_optionmenu = ctk.CTkOptionMenu(controls_frame, values=["Загрузка..."])
        self.lesson_optionmenu.grid(row=1, column=0, padx=5, sticky="ew")

        self.exercise_label = ctk.CTkLabel(controls_frame, text="Упр.:")
        self.exercise_label.grid(row=0, column=1, padx=5, sticky="w")
        self.exercise_optionmenu = ctk.CTkOptionMenu(controls_frame, values=["Загрузка..."], command=self._on_exercise_selected)
        self.exercise_optionmenu.grid(row=1, column=1, padx=5, sticky="ew")

        self.groups_label = ctk.CTkLabel(controls_frame, text="Группы:")
        self.groups_label.grid(row=0, column=2, padx=5, sticky="w")
        self.groups_optionmenu = ctk.CTkOptionMenu(controls_frame, values=[str(i) for i in range(1, 21)])
        self.groups_optionmenu.grid(row=1, column=2, padx=5, sticky="ew")
        self.groups_optionmenu.set("10")

        self.group_size_label = ctk.CTkLabel(controls_frame, text="Знаков в группе:")
        self.group_size_label.grid(row=0, column=3, padx=5, sticky="w")
        self.group_size_optionmenu = ctk.CTkOptionMenu(controls_frame, values=[str(i) for i in range(2, 8)])
        self.group_size_optionmenu.grid(row=1, column=3, padx=5, sticky="ew")
        self.group_size_optionmenu.set("5")

        self.keyboard_frame = ctk.CTkFrame(self.main_frame)
        self.keyboard_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.grid(row=2, column=0, padx=15, pady=15, sticky="ew")
        footer_frame.grid_columnconfigure((0, 1), weight=2)
        footer_frame.grid_columnconfigure(2, weight=1)

        self.start_button = ctk.CTkButton(footer_frame, text="СТАРТ", height=40, command=self._on_start_click)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5)
        
        self.stop_button = ctk.CTkButton(footer_frame, text="СТОП", height=40, command=self._on_stop_click, fg_color="#D32F2F", hover_color="#B71C1C")
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=5)

        self.sound_type_switch = ctk.CTkSwitch(footer_frame, text="Дискретный звук", command=self._update_sound_type)
        self.sound_type_switch.grid(row=0, column=2, padx=10, sticky="e")
        """Создает и наполняет правую, основную панель приложения."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- Верхний блок управления уроками ---
        controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        controls_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        lesson_label = ctk.CTkLabel(controls_frame, text="Урок:")
        lesson_label.grid(row=0, column=0, padx=5, sticky="w")
        # ИСПРАВЛЕНО: СОХРАНЯЕМ ВИДЖЕТ В SELF
        self.lesson_optionmenu = ctk.CTkOptionMenu(controls_frame, values=["Загрузка..."])
        self.lesson_optionmenu.grid(row=1, column=0, padx=5, sticky="ew")

        exercise_label = ctk.CTkLabel(controls_frame, text="Упр.:")
        exercise_label.grid(row=0, column=1, padx=5, sticky="w")
        # ИСПРАВЛЕНО: СОХРАНЯЕМ ВИДЖЕТ В SELF
        self.exercise_optionmenu = ctk.CTkOptionMenu(controls_frame, values=["Загрузка..."], command=self._on_exercise_selected)
        self.exercise_optionmenu.grid(row=1, column=1, padx=5, sticky="ew")

        groups_label = ctk.CTkLabel(controls_frame, text="Группы:")
        groups_label.grid(row=0, column=2, padx=5, sticky="w")
        # ИСПРАВЛЕНО: СОХРАНЯЕМ ВИДЖЕТ В SELF
        self.groups_optionmenu = ctk.CTkOptionMenu(controls_frame, values=[str(i) for i in range(1, 21)])
        self.groups_optionmenu.grid(row=1, column=2, padx=5, sticky="ew")

        group_size_label = ctk.CTkLabel(controls_frame, text="Знаков в группе:")
        group_size_label.grid(row=0, column=3, padx=5, sticky="w")
        # ИСПРАВЛЕНО: СОХРАНЯЕМ ВИДЖЕТ В SELF
        self.group_size_optionmenu = ctk.CTkOptionMenu(controls_frame, values=[str(i) for i in range(2, 8)])
        self.group_size_optionmenu.grid(row=1, column=3, padx=5, sticky="ew")

        # --- Основной рабочий блок ---
        self.keyboard_frame = ctk.CTkFrame(self.main_frame)
        self.keyboard_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        # --- Нижний блок управления (подвал) ---
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.grid(row=2, column=0, padx=15, pady=15, sticky="ew")
        footer_frame.grid_columnconfigure((0, 1), weight=2)
        footer_frame.grid_columnconfigure(2, weight=1)

        # ИСПРАВЛЕНО: СОХРАНЯЕМ ВИДЖЕТЫ В SELF
        self.start_button = ctk.CTkButton(footer_frame, text="СТАРТ", height=40, command=self._on_start_click)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5)
        
        self.stop_button = ctk.CTkButton(footer_frame, text="СТОП", height=40, command=self._on_stop_click,
                                         fg_color="#D32F2F", hover_color="#B71C1C")
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=5)

        self.sound_type_switch = ctk.CTkSwitch(footer_frame, text="Дискретный звук", command=self._update_sound_type)
        self.sound_type_switch.grid(row=0, column=2, padx=10, sticky="e")
    
    def _load_fonts(self):
        """
        Создает словарь с набором стандартных, надежных системных шрифтов.
        """
        print("Загрузка стандартного набора шрифтов...")
        try:
            # Используем лучшие системные шрифты, которые точно есть
            # Segoe UI для интерфейса, Consolas для моноширинного текста
            self.fonts = {
                "main_font": CTkFont(family="Segoe UI", size=14),
                "main_bold": CTkFont(family="Segoe UI", size=14, weight="bold"),
                "title_font": CTkFont(family="Segoe UI", size=18, weight="bold"),
                "huge_char": CTkFont(family="Consolas", size=120, weight="bold"),
                "morse_code": CTkFont(family="Consolas", size=40),
                "mnemonic": CTkFont(family="Segoe UI", size=20, slant="italic"),
                "keyboard_button": CTkFont(family="Consolas", size=16, weight="bold"),
                "study_button": CTkFont(family="Consolas", size=24, weight="bold"),
            }
            print("Шрифты 'Segoe UI' и 'Consolas' успешно загружены.")
        except Exception as e:
            print(f"Не удалось загрузить стандартные шрифты. Используется Arial. Ошибка: {e}")
            # Аварийный вариант, если даже стандартных шрифтов нет
            self.fonts = {
                "main_font": CTkFont(family="Arial", size=14),
                "main_bold": CTkFont(family="Arial", size=14, weight="bold"),
                "title_font": CTkFont(family="Arial", size=18, weight="bold"),
                "huge_char": CTkFont(family="Arial", size=120, weight="bold"),
                "morse_code": CTkFont(family="Arial", size=40),
                "mnemonic": CTkFont(family="Arial", size=20, slant="italic"),
                "keyboard_button": CTkFont(family="Arial", size=16, weight="bold"),
                "study_button": CTkFont(family="Arial", size=24, weight="bold"),
            }
    
    def _populate_lesson_menu(self):
        """
        Заполняет выпадающий список уроков данными из конфигурации.
        
        Получает список всех уроков из логического модуля, форматирует их
        и устанавливает в виджет CTkOptionMenu. Автоматически выбирает
        первый урок в списке при запуске приложения.
        """
        lessons_info = self.logic.get_all_lessons_info()
        
        if not lessons_info:
            print("Предупреждение: Список уроков пуст. Проверьте config/lessons.json.")
            self.lesson_optionmenu.configure(values=["Нет уроков"], state="disabled")
            self.exercise_optionmenu.configure(values=["-"], state="disabled")
            return

        # --- Создаем список имен для отображения в меню ---
        lesson_names = [f"{lesson_id}: {name}" for lesson_id, name in lessons_info]
        
        # --- ИЗМЕНЕНИЕ: Временно отключаем command ---
        self.lesson_optionmenu.configure(values=lesson_names, command=None)
        self.lesson_optionmenu.set(lesson_names[0])
        # Возвращаем command на место
        self.lesson_optionmenu.configure(command=self._on_lesson_selected)
        
        # --- Искусственно вызываем обработчик ОДИН РАЗ ---
        # Так как .set() больше не вызывает command, нам нужно сделать это вручную.
        self._on_lesson_selected(lesson_names[0])

    def _on_lesson_selected(self, selected_lesson_name: str):
        """
        Обрабатывает выбор нового урока из выпадающего меню.
        
        Обновляет список доступных упражнений для выбранного урока
        и автоматически выбирает первое из них.
        
        Args:
            selected_lesson_name (str): Строка из меню, например "1: Основы".
        """
        # --- Безопасный парсинг ID урока ---
        try:
            lesson_id = int(selected_lesson_name.split(':')[0])
        except (ValueError, IndexError):
            print(f"Ошибка: Не удалось извлечь ID из строки урока '{selected_lesson_name}'")
            return

        exercises_info = self.logic.get_exercises_for_lesson(lesson_id)
        
        # --- Обработка случая, когда у урока нет упражнений ---
        if not exercises_info:
            print(f"Предупреждение: Для урока {lesson_id} не найдено упражнений.")
            self.exercise_optionmenu.configure(values=["-"], state="disabled")
            # Очищаем рабочую область
            for widget in self.keyboard_frame.winfo_children():
                widget.destroy()
            return
            
        # --- Включаем меню, если оно было выключено ---
        self.exercise_optionmenu.configure(state="normal")
        
        # --- Форматируем список и обновляем виджет ---
        exercise_names = [f"{ex_id}: {desc}" for ex_id, desc in exercises_info]

        # --- ИЗМЕНЕНИЕ: Точно такая же логика ---
        self.exercise_optionmenu.configure(values=exercise_names, command=None)
        self.exercise_optionmenu.set(exercise_names[0])
        self.exercise_optionmenu.configure(command=self._on_exercise_selected)

        # Искусственно вызываем обработчик
        self._on_exercise_selected(exercise_names[0])

    def _on_exercise_selected(self, selected_exercise_name: str):
        """
        Обрабатывает выбор нового упражнения и перерисовывает основной интерфейс.
        
        Вызывается автоматически при смене упражнения в меню. Получает
        необходимые данные из логического модуля и вызывает метод
        `_reconfigure_ui_for_exercise` для обновления GUI.
        
        Args:
            selected_exercise_name (str): Строка из меню, например "1: Изучение знаков".
        """
        # --- Получаем ID урока из уже выбранного значения ---
        selected_lesson_str = self.lesson_optionmenu.get()

        # --- Безопасный парсинг ID ---
        try:
            lesson_id = int(selected_lesson_str.split(':')[0])
            exercise_id = int(selected_exercise_name.split(':')[0])
        except (ValueError, IndexError, AttributeError):
            print(f"Ошибка: Не удалось извлечь ID из строки '{selected_lesson_str}' или '{selected_exercise_name}'")
            # Можно добавить очистку интерфейса, если что-то пошло не так
            for widget in self.keyboard_frame.winfo_children():
                widget.destroy()
            return
            
        # --- Получаем детали упражнения и пул символов ---
        exercise = self.logic.get_exercise_details(lesson_id, exercise_id)
        if not exercise:
            print(f"Ошибка: Не найдены детали для Урока {lesson_id}, Упр. {exercise_id}")
            return
        
        exercise_type = exercise['type']
        self.current_char_pool = self.logic.get_character_pool(lesson_id, exercise_type)
        
        print(f"Смена интерфейса на: Урок {lesson_id}, Упр. {exercise_id} (Тип: {exercise_type})")
        
        # --- Перерисовываем UI ---
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
        """
        Запускает активное действие для текущего выбранного упражнения.
        
        В зависимости от типа упражнения, эта функция либо запускает раунд
        распознавания, либо инициирует воспроизведение групп символов.
        Для режима "Изучение" кнопка неактивна.
        """
        # --- Используем уже сохраненный пул символов ---
        if not self.current_char_pool:
            print("Невозможно начать: пул символов для упражнения пуст.")
            return

        # --- Получаем тип упражнения более безопасным способом ---
        try:
            selected_exercise_str = self.exercise_optionmenu.get()
            exercise_id = int(selected_exercise_str.split(':')[0])
            # lesson_id нужен только для получения деталей, которые у нас уже есть
            # но для надежности получим и его
            selected_lesson_str = self.lesson_optionmenu.get()
            lesson_id = int(selected_lesson_str.split(':')[0])
            exercise_type = self.logic.get_exercise_details(lesson_id, exercise_id)['type']
        except (ValueError, IndexError, AttributeError, TypeError):
            print("Ошибка: не удалось определить тип текущего упражнения.")
            return

        print(f"СТАРТ для упражнения типа: '{exercise_type}'")

        # --- Разделение логики по типам упражнений ---
        if exercise_type == "study":
            print("В режиме изучения кнопка СТАРТ неактивна.")
            return
            
        # --- Общая логика для всех упражнений на прием ---
        try:
            num_groups = int(self.groups_optionmenu.get())
            group_size = int(self.group_size_optionmenu.get())
        except ValueError:
            print("Ошибка: неверные значения в меню групп или размера группы.")
            return

        if exercise_type in ["single_char_recognition_lesson", "single_char_recognition_cumulative"]:
            # Логика для режима распознавания
            self.rounds_left = num_groups * group_size
            if self.rounds_left > 0:
                self._start_recognition_round()
            else:
                print("Количество раундов должно быть больше 0.")
            
        elif exercise_type == "group_reception":
            # Логика для режима приема групп
            if self.output_textbox:
                self.output_textbox.delete("1.0", "end")
                self.output_textbox.insert("1.0", "Прием...")

            exercise_text = self.logic.generate_exercise_text(self.current_char_pool, num_groups, group_size)
            self.logic.start_playback(
                exercise_text, 
                on_complete=lambda text: self.after(10, self._on_playback_complete, text)
            )

    def _on_playback_complete(self, text: str):
        """
        Обрабатывает завершение воспроизведения для упражнений на прием групп.
        
        Вызывается безопасно из главного потока через `self.after`.
        Форматирует и выводит принятый текст в текстовое поле.
        
        Args:
            text (str): Текст, который был воспроизведен.
        """
        print(f"Воспроизведение завершено. Выводим текст: {text}")
        
        # Безопасно проверяем, существует ли еще виджет текстового поля
        if not self.output_textbox or not self.output_textbox.winfo_exists():
            print("Виджет для вывода текста уже не существует. Вывод отменен.")
            return

        # --- Более эффективное и "питоническое" форматирование ---
        words = text.split()
        
        # Разбиваем список слов на "чанки" по 5 элементов
        # Пример: [a, b, c, d, e, f, g] -> [[a, b, c, d, e], [f, g]]
        chunks = [words[i:i + 5] for i in range(0, len(words), 5)]
        
        # Соединяем каждый чанк в строку с пробелами,
        # а затем соединяем строки-чанки с переносами строк.
        formatted_text = "\n".join([" ".join(chunk) for chunk in chunks])

        # --- Обновляем виджет ---
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", formatted_text)

    def _reconfigure_ui_for_exercise(self, exercise_type: str):
        """
        Перестраивает основной рабочий блок в соответствии с типом упражнения.
        
        Это главный метод-диспетчер, который очищает рабочую область
        и вызывает соответствующий метод для построения нового интерфейса.
        
        Args:
            exercise_type (str): Тип упражнения ('study', 'recognition', и т.д.).
        """
        # --- Блок 1: Очистка и сброс состояния ---
        self._clear_workspace()
        
        # --- Блок 2: Вызов нужного конструктора UI ---
        if exercise_type == "study":
            self._build_study_ui()
        elif "recognition" in exercise_type:
            self._build_recognition_ui()
        elif exercise_type == "group_reception":
            self._build_group_reception_ui()
        else:
            print(f"Предупреждение: Неизвестный тип упражнения '{exercise_type}'. Интерфейс не будет построен.")

    def _clear_workspace(self):
        """Очищает рабочую область и сбрасывает все связанные атрибуты состояния."""
        for widget in self.keyboard_frame.winfo_children():
            widget.destroy()
        
        self.output_textbox = None
        self.study_char_label = None
        self.study_code_label = None
        self.study_mnemonic_label = None
        self.current_correct_char = None
        self.keyboard_buttons = {}
        self.info_label = None
        self.rounds_left = 0

    def _build_study_ui(self):
        """Строит интерфейс для режима 'Изучение' (Упр. 1)."""
        self.keyboard_frame.grid_rowconfigure(0, weight=3)
        self.keyboard_frame.grid_rowconfigure(1, weight=1)
        self.keyboard_frame.grid_columnconfigure(0, weight=1)

        # Создаем фрейм для дисплея
        display_frame = ctk.CTkFrame(self.keyboard_frame, corner_radius=10)
        display_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        display_frame.grid_propagate(False) # Запрещаем сжиматься

        # Размещаем элементы дисплея
        self.study_char_label = ctk.CTkLabel(display_frame, text="?", font=self.fonts.get("huge_char"))
        self.study_char_label.place(relx=0.5, rely=0.4, anchor="center")
        
        self.study_code_label = ctk.CTkLabel(display_frame, text="", font=self.fonts.get("morse_code"))
        self.study_code_label.place(relx=0.5, rely=0.7, anchor="center")

        self.study_mnemonic_label = ctk.CTkLabel(display_frame, text="", font=self.fonts.get("mnemonic"))
        self.study_mnemonic_label.place(relx=0.5, rely=0.85, anchor="center")

        # Создаем фрейм для кнопок
        buttons_frame = ctk.CTkFrame(self.keyboard_frame, fg_color="transparent")
        buttons_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Создаем кнопки
        for i, char in enumerate(self.current_char_pool):
            buttons_frame.grid_columnconfigure(i, weight=1)
            button = ctk.CTkButton(buttons_frame, text=char, font=self.fonts.get("study_button"),
                                   command=lambda c=char: self._on_study_button_click(c))
            button.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            button.bind("<Enter>", lambda event, c=char: self._on_study_button_enter(event, c))
            button.bind("<Leave>", self._on_study_button_leave)

    def _build_recognition_ui(self):
        """Строит интерфейс для режима 'Распознавание' (Упр. 2 и 3)."""
        self.info_label = ctk.CTkLabel(self.keyboard_frame, text="Нажмите 'СТАРТ', чтобы начать", font=self.fonts.get("title_font"))
        self.info_label.pack(pady=10)

        kb_frame = ctk.CTkFrame(self.keyboard_frame, fg_color="transparent")
        kb_frame.pack(expand=True, fill="both", padx=5, pady=5)

        layout = self.logic.get_keyboard_layout() # <-- Получаем раскладку из логики

        for row_idx, row_chars in enumerate(layout):
            kb_frame.rowconfigure(row_idx, weight=1)
            for col_idx, char in enumerate(row_chars):
                kb_frame.columnconfigure(col_idx, weight=1)
                
                is_active = char in self.current_char_pool
                button = ctk.CTkButton(kb_frame, text=char, font=self.fonts.get("keyboard_button"),
                                       command=lambda c=char: self._on_recognition_button_click(c))
                
                if not is_active:
                    button.configure(fg_color="gray20", text_color="gray50", hover=False)
                
                button.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")
                self.keyboard_buttons[char] = button

    def _build_group_reception_ui(self):
        """Строит интерфейс для режима 'Прием групп' (Упр. 4)."""
        self.output_textbox = ctk.CTkTextbox(self.keyboard_frame, font=self.fonts.get("main_bold"),
                                             corner_radius=10, wrap="word")
        self.output_textbox.pack(expand=True, fill="both", padx=5, pady=5)
        self.output_textbox.insert("1.0", "Готов к приему групп...\nНажмите 'СТАРТ'")

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
        """
        Запускает один раунд упражнения на распознавание.
        
        Обновляет информационную метку, выбирает случайный символ
        из текущего пула и запускает его воспроизведение.
        """
        # --- Проверка предусловий ---
        if self.rounds_left <= 0:
            print("Раунды закончились, новый не будет начат.")
            return
            
        if not self.current_char_pool:
            print("Ошибка: Пул символов пуст, раунд не может быть начат.")
            return

        # --- Обновление интерфейса ---
        # Используем сохраненную ссылку на виджет, а не ищем его заново
        if self.info_label and self.info_label.winfo_exists():
            self.info_label.configure(text=f"Прием... Осталось: {self.rounds_left}")
        
        # --- Логика раунда ---
        # Выбираем случайный символ из уже сохраненного пула
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

    


