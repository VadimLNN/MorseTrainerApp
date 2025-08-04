from morse_trainer.app import MorseTrainerApp

if __name__ == "__main__":
    app = MorseTrainerApp()
    # Привязываем нашу функцию к событию закрытия окна
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()