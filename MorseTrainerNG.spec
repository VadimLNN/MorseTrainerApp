# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# --- БЛОК 1: ДАННЫЕ И РЕСУРСЫ ---
# Здесь мы говорим PyInstaller, какие папки с файлами нужно включить в сборку.
datas = [
    ('config', 'config'), # Копировать папку 'config' в папку 'config' в сборке
    ('assets', 'assets')  # Копировать папку 'assets' в папку 'assets' в сборке
]

# --- БЛОК 2: АНАЛИЗ ПРОЕКТА ---
# PyInstaller анализирует импорты, начиная с main.py.
# Мы явно указываем "скрытые" импорты, которые он может не найти сам.
a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=datas, # <-- Используем наш список данных
             hiddenimports=['Pillow', 'pyglet', 'scipy'], # <-- Явно перечисляем важные библиотеки
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# --- БЛОК 3: СБОРКА .PYZ (архив с Python-кодом) ---
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

# --- БЛОК 4: СБОРКА .EXE (исполняемый файл) ---
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='MorseTrainerNG',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True, # Включаем сжатие для уменьшения размера
          console=False, # <-- Убирает черное консольное окно
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='assets/icons/app.ico') # <-- Путь к нашей иконке

# --- БЛОК 5: СБОРКА .COLLECT (вспомогательные файлы) ---
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='MorseTrainerNG')