from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

from src.ui.screens.base import LightScreen


class DashboardScreen(LightScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dashboard"

        layout = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20,
        )

        self.info_label = Label(
            text="Добро пожаловать",
            font_size=22,
            color=(0, 0, 0, 1),
        )

        logout_btn = Button(
            text="Выйти",
            size_hint=(1, None),
            height=45,
            on_press=self.logout,
        )

        layout.add_widget(self.info_label)
        layout.add_widget(logout_btn)

        self.add_widget(layout)

    def refresh(self):
        sm = self.manager
        self.info_label.text = f"Пользователь ID: {sm.current_user_id}"

    def logout(self, *_):
        sm = self.manager
        sm.current_user_id = None
        sm.current_role = None
        sm.safe_switch("auth")