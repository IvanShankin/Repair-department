from typing import Callable, Optional

from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.metrics import dp, sp


def show_confirm_modal(
    text: str,
    on_yes: Optional[Callable[[], None]] = None,
    on_no: Optional[Callable[[], None]] = None,
):
    modal = ModalView(
        size_hint=(0.8, 0.6),
        auto_dismiss=False,
        background_color=(0, 0, 0, 0.7)
    )

    root = BoxLayout(
        orientation="vertical",
        padding=dp(20),
        spacing=dp(15)
    )

    # ===== Scrollable текст =====
    scroll = ScrollView(size_hint=(1, 1))

    label = Label(
        text=text,
        size_hint_y=None,
        font_size=sp(16),
        halign="left",
        valign="top",
        color=(1, 1, 1, 1)
    )
    label.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1]))
    scroll.bind(width=lambda inst, val: setattr(label, "text_size", (val - dp(20), None)))
    scroll.add_widget(label)

    # ===== Кнопки =====
    buttons = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(50),
        spacing=dp(15)
    )

    btn_yes = Button(
        text="Да",
        font_size=sp(16),
        background_normal='',
        background_color=(0.2, 0.6, 0.2, 1),
        color=(1, 1, 1, 1)
    )

    btn_no = Button(
        text="Нет",
        font_size=sp(16),
        background_normal='',
        background_color=(0.8, 0.2, 0.2, 1),
        color=(1, 1, 1, 1)
    )

    def yes_handler(*_):
        modal.dismiss()
        if on_yes:
            on_yes()

    def no_handler(*_):
        modal.dismiss()
        if on_no:
            on_no()

    btn_yes.bind(on_release=yes_handler)
    btn_no.bind(on_release=no_handler)

    # Добавляем кнопки в контейнер
    buttons.add_widget(btn_yes)
    buttons.add_widget(btn_no)

    root.add_widget(scroll)
    root.add_widget(buttons)
    modal.add_widget(root)

    # Обновление текста после отрисовки
    Clock.schedule_once(lambda dt: setattr(label, "text_size", (scroll.width - dp(20), None)))

    modal.open()