import pyaudio
import numpy as np
import time

class AudioPlayer:
    """Генерирует и воспроизводит звуки Морзе."""
    def __init__(self, wpm=20, tone=700, sample_rate=44100):
        self.sample_rate = sample_rate
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=1,
                                  rate=self.sample_rate,
                                  output=True)
        self.set_wpm(wpm)
        self.set_tone(tone)
        self.attack_decay_ms = 5 # "Фронт" в мс для мягкости звука

    def set_wpm(self, wpm: int):
        """Устанавливает скорость и пересчитывает длительности."""
        # Стандарт PARIS: слово "PARIS" содержит 50 "точек"
        self.dot_duration = 1.2 / wpm
        self.dash_duration = 3 * self.dot_duration
        self.inter_element_pause = self.dot_duration
        self.inter_char_pause = 3 * self.dot_duration
        self.inter_word_pause = 7 * self.dot_duration
        print(f"Скорость установлена на {wpm} WPM. Длительность точки: {self.dot_duration:.2f} сек.")

    def set_tone(self, tone: int):
        """Устанавливает тон (частоту) звука."""
        self.tone = tone
        print(f"Тон установлен на {self.tone} Гц.")

    def _generate_wave(self, duration: float):
        """Генерирует волну синусоиды с плавной атакой/затуханием."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sin(self.tone * t * 2 * np.pi)

        # Применяем огибающую (envelope) для сглаживания "щелчков"
        attack_decay_samples = int(self.sample_rate * (self.attack_decay_ms / 1000.0))
        if len(wave) > 2 * attack_decay_samples:
            attack = np.linspace(0, 1, attack_decay_samples)
            decay = np.linspace(1, 0, attack_decay_samples)
            wave[:attack_decay_samples] *= attack
            wave[-attack_decay_samples:] *= decay
        
        return wave.astype(np.float32)

    def play_dot(self):
        wave = self._generate_wave(self.dot_duration)
        self.stream.write(wave.tobytes())
        time.sleep(self.inter_element_pause)

    def play_dash(self):
        wave = self._generate_wave(self.dash_duration)
        self.stream.write(wave.tobytes())
        time.sleep(self.inter_element_pause)

    def play_char_pause(self):
        time.sleep(self.inter_char_pause - self.inter_element_pause)

    def stop(self):
        """Останавливает аудиопоток."""
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()