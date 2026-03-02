from typing import List

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from src.database.models import UserRole, Users
from src.repository.users import get_user_repository
from src.ui.screens.base import LightScreen
from src.ui.screens.modal_window.modal_with_ok import show_modal


class AdminUserManagementScreen(LightScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "admin_user_management"
        self.selected_user = None

        root = BoxLayout(orientation="vertical", padding=15, spacing=12)

        header = BoxLayout(size_hint=(1, None), height=40, spacing=8)
        header.add_widget(Label(text="Управление пользователями", color=(0, 0, 0, 1)))
        header.add_widget(Button(text="Назад", size_hint=(None, 1), width=120, on_press=self.go_back))
        root.add_widget(header)

        content = BoxLayout(spacing=12)

        left = BoxLayout(orientation="vertical", spacing=8, size_hint=(0.45, 1))
        left.add_widget(Label(text="Пользователи", size_hint=(1, None), height=25, color=(0, 0, 0, 1)))

        self.users_list_container = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.users_list_container.bind(minimum_height=self.users_list_container.setter("height"))
        user_scroll = ScrollView()
        user_scroll.add_widget(self.users_list_container)
        left.add_widget(user_scroll)

        right = BoxLayout(orientation="vertical", spacing=8, size_hint=(0.55, 1))
        right.add_widget(Label(text="Данные пользователя", size_hint=(1, None), height=25, color=(0, 0, 0, 1)))

        self.edit_login = TextInput(hint_text="Логин", multiline=False, size_hint=(1, None), height=36)
        self.edit_full_name = TextInput(hint_text="ФИО", multiline=False, size_hint=(1, None), height=36)
        self.edit_password = TextInput(hint_text="Пароль (для обновления)", multiline=False, password=True, size_hint=(1, None), height=36)
        self.edit_department = TextInput(hint_text="Отдел", multiline=False, size_hint=(1, None), height=36)
        self.edit_role = Spinner(text=UserRole.WORKER.value, values=[role.value for role in UserRole], size_hint=(1, None), height=36)

        right.add_widget(self.edit_login)
        right.add_widget(self.edit_full_name)
        right.add_widget(self.edit_password)
        right.add_widget(self.edit_department)
        right.add_widget(self.edit_role)

        actions = BoxLayout(size_hint=(1, None), height=40, spacing=8)
        actions.add_widget(Button(text="Добавить", on_press=self.add_user))
        actions.add_widget(Button(text="Сохранить", on_press=self.save_user))
        actions.add_widget(Button(text="Удалить", on_press=self.delete_user))
        right.add_widget(actions)

        self.user_requests_title = Label(text="Заявки пользователя", size_hint=(1, None), height=25, color=(0, 0, 0, 1))
        right.add_widget(self.user_requests_title)

        self.view_requests_button = Button(
            text="Просмотреть все заявки",
            size_hint=(1, None),
            height=40,
            on_press=self.open_requests_review,
            disabled=True,
        )
        right.add_widget(self.view_requests_button)

        content.add_widget(left)
        content.add_widget(right)
        root.add_widget(content)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.load_users()

    def go_back(self, *_):
        self.manager.get_screen("admin_dashboard").refresh()
        self.manager.safe_switch("admin_dashboard")

    def load_users(self):
        self.run_async(self._load_users_async(), self._set_users, self._error)

    async def _load_users_async(self):
        repo = await get_user_repository()
        return await repo.get_all()

    def _set_users(self, users: List[Users]):
        self.users_list_container.clear_widgets()

        for user in users:
            btn = Button(
                text=f"{user.full_name} ({user.role.value})",
                size_hint=(1, None),
                height=40,
                halign="left",
                background_color=(0.88, 0.88, 0.88, 1),
            )
            btn.text_size = (btn.width - 10, None)
            btn.bind(size=lambda inst, _: setattr(inst, "text_size", (inst.width - 10, None)))
            btn.bind(on_press=lambda _, u=user: self.select_user(u))
            self.users_list_container.add_widget(btn)

    def select_user(self, user: Users):
        self.selected_user = user
        self.edit_login.text = user.login
        self.edit_full_name.text = user.full_name
        self.edit_password.text = ""
        self.edit_department.text = user.department or ""
        self.edit_role.text = user.role.value
        self.user_requests_title.text = "Просмотр заявок выбранного пользователя"
        self.view_requests_button.disabled = False

    def open_requests_review(self, *_):
        if not self.selected_user:
            show_modal("Сначала выберите пользователя")
            return

        review_screen = self.manager.get_screen("requests_review")
        review_screen.set_target_user(self.selected_user)
        self.manager.safe_switch("requests_review")


    def add_user(self, *_):
        self.run_async(self._add_user_async(), self._after_user_updated, self._error)

    async def _add_user_async(self):
        login = self.edit_login.text.strip()
        full_name = self.edit_full_name.text.strip()
        password = self.edit_password.text.strip()

        if not login or not full_name or not password:
            raise Exception("Логин, ФИО и пароль обязательны")

        repo = await get_user_repository()
        exists = await repo.get_by_login(login)
        if exists:
            raise Exception("Пользователь с таким логином уже существует")

        return await repo.create(
            login=login,
            password=password,
            full_name=full_name,
            role=UserRole(self.edit_role.text),
            department=self.edit_department.text.strip() or None,
        )

    def save_user(self, *_):
        self.run_async(self._save_user_async(), self._after_user_updated, self._error)

    async def _save_user_async(self):
        if not self.selected_user:
            raise Exception("Сначала выберите пользователя")

        repo = await get_user_repository()
        fresh_user = await repo.get_by_id(self.selected_user.id)
        if not fresh_user:
            raise Exception("Пользователь не найден")

        update_data = {
            "login": self.edit_login.text.strip(),
            "full_name": self.edit_full_name.text.strip(),
            "role": UserRole(self.edit_role.text),
            "department": self.edit_department.text.strip() or None,
        }

        password = self.edit_password.text.strip()
        if password:
            update_data["password"] = password

        return await repo.update(fresh_user, **update_data)

    def delete_user(self, *_):
        self.run_async(self._delete_user_async(), self._after_delete_user, self._error)

    async def _delete_user_async(self):
        if not self.selected_user:
            raise Exception("Сначала выберите пользователя")

        repo = await get_user_repository()
        fresh_user = await repo.get_by_id(self.selected_user.id)
        if not fresh_user:
            raise Exception("Пользователь не найден")

        return await repo.soft_delete(fresh_user)

    def _after_delete_user(self, _):
        self.selected_user = None
        self.edit_login.text = ""
        self.edit_full_name.text = ""
        self.edit_password.text = ""
        self.edit_department.text = ""
        self.edit_role.text = UserRole.WORKER.value
        self.user_requests_title.text = "Заявки пользователя"
        self.view_requests_button.disabled = True
        self._after_user_updated(_)

    def _after_user_updated(self, _):
        self.load_users()

    def _error(self, error, **kwargs):
        show_modal(str(error))
