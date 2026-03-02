from typing import List

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

from src.database.models import Users, UserRole
from src.repository.repair_requests import get_repair_request_repository
from src.ui.screens.base import LightScreen
from src.repository.users import get_user_repository
from src.ui.screens.modal_window.modal_with_ok import show_modal


class AdminDashboardScreen(LightScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "admin_dashboard"

        root = BoxLayout(orientation="vertical", padding=20, spacing=15)

        header = BoxLayout(size_hint=(1, None), height=40)

        header.add_widget(Label(
            text="Панель администратора",
            font_size=22,
            color=(0, 0, 0, 1),
        ))

        logout_btn = Button(
            text="Выйти",
            size_hint=(None, 1),
            width=120,
            on_press=self.logout
        )

        header.add_widget(logout_btn)
        root.add_widget(header)

        # ===== Создание заявки =====
        create_box = BoxLayout(orientation="vertical", spacing=10, size_hint=(1, None))
        create_box.bind(minimum_height=create_box.setter("height"))

        create_box.add_widget(Label(
            text="Создать заявку",
            size_hint=(1, None),
            height=30,
            color=(0, 0, 0, 1)
        ))

        self.user_spinner = Spinner(
            text="Выберите пользователя",
            size_hint=(1, None),
            height=40
        )

        self.equipment_input = TextInput(
            hint_text="Оборудование",
            multiline=False,
            size_hint=(1, None),
            height=40
        )

        self.problem_input = TextInput(
            hint_text="Описание проблемы",
            multiline=False,
            size_hint=(1, None),
            height=40
        )

        create_btn = Button(
            text="Создать",
            size_hint=(1, None),
            height=40,
            on_press=self.create_request
        )

        create_box.add_widget(self.user_spinner)
        create_box.add_widget(self.equipment_input)
        create_box.add_widget(self.problem_input)
        create_box.add_widget(create_btn)

        root.add_widget(create_box)

        # ===== Список заявок =====
        root.add_widget(Label(
            text="Все заявки",
            size_hint=(1, None),
            height=30,
            color=(0, 0, 0, 1)
        ))

        self.requests_container = GridLayout(
            cols=1,
            spacing=10,
            size_hint_y=None
        )
        self.requests_container.bind(
            minimum_height=self.requests_container.setter("height")
        )

        scroll = ScrollView()
        scroll.add_widget(self.requests_container)

        root.add_widget(scroll)

        # ===== Управление пользователями =====
        manage_users_btn = Button(
            text="Управление пользователями",
            size_hint=(1, None),
            height=40,
            on_press=self.open_user_management
        )

        root.add_widget(manage_users_btn)

        self.add_widget(root)

    # ================= REFRESH =================

    def refresh(self):
        self.load_users()
        self.load_requests()

    # ================= LOAD DATA =================

    def load_users(self):
        self.run_async(self._load_users_async(), self._set_users, self._error)

    async def _load_users_async(self):
        repo = await get_user_repository()
        return await repo.get_all()

    def _set_users(self, users: List[Users]):
        self.users_map = {u.full_name: u.id for u in users}
        self.user_spinner.values = list(self.users_map.keys())

    def load_requests(self):
        self.run_async(self._load_requests_async(), self._set_requests, self._error)

    async def _load_requests_async(self):
        repo = await get_repair_request_repository()
        return await repo.get_all()

    def _set_requests(self, requests):
        self.requests_container.clear_widgets()

        for r in requests:
            self.requests_container.add_widget(
                Label(
                    text=f"[{r.id}] {r.equipment_name} | {r.status.name}",
                    size_hint_y=None,
                    height=30,
                    color=(0, 0, 0, 1)
                )
            )

    # ================= CREATE REQUEST =================

    def create_request(self, *_):
        self.run_async(self._create_request_async(), self._after_create, self._error)

    async def _create_request_async(self):
        if self.user_spinner.text not in self.users_map:
            raise Exception("Выберите пользователя")

        repo = await get_repair_request_repository()

        return await repo.create(
            created_by=self.users_map[self.user_spinner.text],
            equipment_name=self.equipment_input.text.strip(),
            description_problem=self.problem_input.text.strip(),
        )

    def _after_create(self, _):
        self.equipment_input.text = ""
        self.problem_input.text = ""
        self.load_requests()

    def _error(self, error, **kwargs):
        show_modal(str(error))

    # ================= USERS =================

    def open_user_management(self, *_):
        self.manager.safe_switch("admin_user_management")

    # ================= LOGOUT =================

    def logout(self, *_):
        sm = self.manager
        sm.current_user_id = None
        sm.current_role = None
        sm.safe_switch("auth")
