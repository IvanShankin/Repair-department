import os
from kivy.app import App
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Set

from pydantic import BaseModel


def get_base_dir() -> Path:
    try:
        app = App.get_running_app()
        if app:
            return Path(app.user_data_dir)
    except Exception:
        pass

    # fallback для dev режима
    return Path(__file__).resolve().parents[2]


class Config(BaseModel):
    base: Path = get_base_dir()

    media: Path = base / "media"
    log_file: Path = media / "app.log"
    data_base_path: Path = media / "data_base.sqlite3"

    media.mkdir(parents=True, exist_ok=True)

    global_event_loop: AbstractEventLoop

    light_bg: Set = (0.95, 0.95, 0.95, 1)  # очень светлый фон (почти белый)
    input_bg: Set = (1, 1, 1, 1)  # белые поля ввода
    primary_btn: Set = (0.2, 0.5, 0.8, 1)  # более насыщенный синий (лучше виден на светлом)
    secondary_btn: Set = (0.85, 0.85, 0.85, 1)  # светло-серая второстепенная кнопка
    text_color: Set = (0.15, 0.15, 0.15, 1)  # темно-серый текст (почти черный)
    hint_color: Set = (0.5, 0.5, 0.5, 1)  # средне-серый для подсказок


    class Config:
        arbitrary_types_allowed = True

    @property
    def sqlite_url(self) -> str:
        return f"sqlite:///{self.data_base_path.as_posix()}"


# создаём папку media гарантированно
os.makedirs(get_base_dir() / "media", exist_ok=True)
