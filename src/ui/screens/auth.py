from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window

from src.database.models import Users, UserRole
from src.service.config.core import get_config
from src.repository.users import get_user_repository
from src.ui.screens.base import LightScreen
from src.ui.screens.modal_window.modal_with_ok import show_modal
from src.ui.screens.screen_manager import RootScreenManager

Window.clearcolor = (0.95, 0.95, 0.95, 1)


class StyledTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conf = get_config()

        self.padding = [12, 12, 12, 12]
        self.font_size = 16
        self.background_color = self.conf.input_bg
        self.foreground_color = (0, 0, 0, 1)
        self.hint_text_color = (0.6, 0.6, 0.6, 1)
        self.multiline = False
        self.cursor_color = (0, 0, 0, 1)
        self.background_normal = ""
        self.background_active = ""


class AuthScreen(LightScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "auth"
        self.conf = get_config()

        anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        self.add_widget(anchor)

        form = BoxLayout(
            orientation="vertical",
            spacing=12,
            padding=30,
            size_hint=(0.6, None),
        )
        form.bind(minimum_height=form.setter("height"))
        anchor.add_widget(form)

        form.add_widget(
            Label(
                text="Авторизация",
                font_size=26,
                size_hint_y=None,
                height=40,
                color=(0, 0, 0, 1),
            )
        )

        form.add_widget(
            Label(
                text="Логин",
                size_hint_y=None,
                height=25,
                color=(0, 0, 0, 1),
            )
        )

        self.login = StyledTextInput(
            hint_text="Введите логин",
            size_hint_y=None,
            height=45,
        )
        form.add_widget(self.login)

        form.add_widget(
            Label(
                text="Пароль",
                size_hint_y=None,
                height=25,
                color=(0, 0, 0, 1),
            )
        )

        self.password = StyledTextInput(
            password=True,
            hint_text="Введите пароль",
            size_hint_y=None,
            height=45,
        )
        form.add_widget(self.password)

        form.add_widget(
            Button(
                text="Войти",
                size_hint_y=None,
                height=45,
                background_color=self.conf.primary_btn,
                color=(1, 1, 1, 1),
                on_press=self.do_login,
            )
        )

    def do_login(self, *_):
        self.run_async(
            self._login_async(),
            self._after_login,
            self._error_login
        )

    async def _login_async(self):
        repo = await get_user_repository()
        user = await repo.get_by_login(self.login.text.strip())

        if not user:
            raise Exception("Пользователь не найден")

        if not repo.verify_password(self.password.text, user.hash_password):
            raise Exception("Неверный пароль")

        return user

    def _after_login(self, user: Users):
        sm: RootScreenManager = self.manager
        sm.current_user_id = user.id
        sm.current_role = user.role

        if user.role in (UserRole.ADMIN, UserRole.WORKER):
            sm.get_screen("admin_dashboard").refresh()
            sm.safe_switch("admin_dashboard")
        elif user.role == UserRole.MASTER:
            sm.get_screen("requests_review").set_target_user(user)
            sm.safe_switch("requests_review")

    def _error_login(self, error, **kwargs):
        show_modal(str(error))
