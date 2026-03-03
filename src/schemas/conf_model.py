import os
import sys
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Set

from pydantic import BaseModel


def get_base_dir() -> Path:
    """
    Возвращает правильную базовую директорию:
    - dev режим → root_dir
    - exe режим → папка где лежит exe
    """
    if getattr(sys, "frozen", False):
        # exe режим
        return Path(sys.executable).parent
    else:
        # dev режим
        return Path(__file__).resolve().parents[2]


class Config(BaseModel):
    base: Path = get_base_dir()

    media: Path = base / "media"
    log_file: Path = media / "app.log"
    data_base_path: Path = media / "data_base.sqlite3"

    global_event_loop: AbstractEventLoop

    light_bg: Set = (0.95, 0.95, 0.95, 1)  # очень светлый фон (почти белый)
    input_bg: Set = (1, 1, 1, 1)  # белые поля ввода
    primary_btn: Set = (0.2, 0.5, 0.8, 1)  # более насыщенный синий (лучше виден на светлом)
    secondary_btn: Set = (0.85, 0.85, 0.85, 1)  # светло-серая второстепенная кнопка
    text_color: Set = (0.15, 0.15, 0.15, 1)  # темно-серый текст (почти черный)
    hint_color: Set = (0.5, 0.5, 0.5, 1)  # средне-серый для подсказок


    model_config = {
        "arbitrary_types_allowed": True,
    }

    @property
    def sqlite_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.data_base_path}"


# создаём папку media гарантированно
os.makedirs(get_base_dir() / "media", exist_ok=True)