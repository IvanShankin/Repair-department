from typing import List

from kivy.graphics import Color, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from src.database.models import RequestStatus, Users, UserRole
from src.repository.repair_requests import get_repair_request_repository
from src.repository.users import get_user_repository
from src.ui.screens.base import LightScreen
from src.ui.screens.modal_window.modal_with_ok import show_modal


STATUS_RU = {
    RequestStatus.NEW: "Новая",
    RequestStatus.IN_PROGRESS: "В работе",
    RequestStatus.DONE: "Выполнена",
    RequestStatus.CANCELED: "Отменена",
}


class OrdersDashboardScreen(LightScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "order_dashboard"

        root = BoxLayout(orientation="vertical", padding=20, spacing=15)

        header = BoxLayout(size_hint=(1, None), height=40)

        header.add_widget(Label(
            text="Панель заявок",
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

        # ===== Список заявок =====
        root.add_widget(Label(text="Заявки", size_hint=(1, None), height=30, color=(0, 0, 0, 1)))

        self.requests_container = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.requests_container.bind(minimum_height=self.requests_container.setter("height"))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.requests_container)
        root.add_widget(scroll)

        # ===== Создание заявки =====
        create_box = BoxLayout(orientation="vertical", spacing=10, size_hint=(1, None), height=280)

        self.mode_label = Label(text="Создать заявку", size_hint=(1, None), height=30, color=(0, 0, 0, 1))
        create_box.add_widget(self.mode_label)

        self.user_spinner = Spinner(
            text="Выберите пользователя",
            size_hint=(1, None),
            height=40
        )
        create_box.add_widget(self.user_spinner)

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

        create_box.add_widget(self.equipment_input)
        create_box.add_widget(self.problem_input)
        create_box.add_widget(create_btn)

        # ===== Управление пользователями =====
        self.review_requests_btn = Button(
            text="Просмотреть все мои заявки",
            size_hint=(1, None),
            height=40,
            on_press=self.open_my_requests,
        )
        create_box.add_widget(self.review_requests_btn)

        self.manage_users_btn = Button(
            text="Управление пользователями",
            size_hint=(1, None),
            height=40,
            on_press=self.open_user_management
        )
        create_box.add_widget(self.manage_users_btn)

        root.add_widget(create_box)

        self.add_widget(root)
        self.current_user: Users | None = None
        self.users_map = {}

    # ================= REFRESH =================

    def refresh(self):
        self.run_async(self._refresh_async(), self._after_refresh, self._error)

    async def _refresh_async(self):
        user_repo = get_user_repository()
        current_user = user_repo.get_by_id(self.manager.current_user_id)

        users = []
        if self.manager.current_role == UserRole.ADMIN:
            users = user_repo.get_all()

        requests_repo = get_repair_request_repository()
        if self.manager.current_role == UserRole.ADMIN:
            requests = requests_repo.get_all()
        else:
            requests = requests_repo.get_by_creator(self.manager.current_user_id)

        return current_user, users, requests

    def _after_refresh(self, payload):
        self.current_user, users, requests = payload
        self._set_users(users)
        self._set_mode()
        self._set_requests(requests)

    def _set_mode(self):
        is_admin = self.manager.current_role == UserRole.ADMIN
        self.user_spinner.disabled = not is_admin
        self.user_spinner.opacity = 1 if is_admin else 0
        self.user_spinner.height = 40 if is_admin else 0
        self.manage_users_btn.disabled = not is_admin
        self.manage_users_btn.opacity = 1 if is_admin else 0
        self.manage_users_btn.height = 40 if is_admin else 0

        if is_admin:
            self.mode_label.text = "Создать заявку (режим администратора)"
            self.review_requests_btn.disabled = True
            self.review_requests_btn.opacity = 0
            self.review_requests_btn.height = 0
            if self.users_map and self.user_spinner.text not in self.users_map:
                self.user_spinner.text = "Выберите пользователя"
        else:
            self.mode_label.text = "Создать заявку (режим рабочего)"
            self.review_requests_btn.disabled = False
            self.review_requests_btn.opacity = 1
            self.review_requests_btn.height = 40
            if self.current_user:
                self.user_spinner.text = self.current_user.full_name

    # ================= LOAD DATA =================

    def _set_users(self, users: List[Users]):
        self.users_map = {u.full_name: u.id for u in users}
        self.user_spinner.values = list(self.users_map.keys())

    def _set_requests(self, requests):
        self.requests_container.clear_widgets()

        if not requests:
            self.requests_container.add_widget(
                Label(text="Нет заявок", size_hint_y=None, height=35, color=(0, 0, 0, 1))
            )
            return

        for r in requests:
            self.requests_container.add_widget(self._build_request_card(r))

    def _build_request_card(self, request):
        card = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=95,
            padding=8,
            spacing=4,
        )

        with card.canvas.before:
            Color(0.92, 0.92, 0.92, 1)
            card.bg_rect = Rectangle(pos=card.pos, size=card.size)
            Color(0.62, 0.62, 0.62, 1)
            card.border = Line(rectangle=(card.x, card.y, card.width, card.height), width=1.2)

        def update_graphics(instance, _):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
            instance.border.rectangle = (instance.x, instance.y, instance.width, instance.height)

        card.bind(pos=update_graphics, size=update_graphics)

        card.add_widget(Label(text=f"[{request.id}] {request.equipment_name}", size_hint_y=None, height=28, color=(0, 0, 0, 1)))
        card.add_widget(Label(text=f"Статус: {STATUS_RU.get(request.status, request.status.value)}", size_hint_y=None, height=26, color=(0, 0, 0, 1)))
        card.add_widget(Label(text=f"Проблема: {request.description_problem}", size_hint_y=None, height=26, color=(0, 0, 0, 1)))
        return card

    # ================= CREATE REQUEST =================

    def create_request(self, *_):
        self.run_async(self._create_request_async(), self._after_create, self._error)

    async def _create_request_async(self):
        if self.manager.current_role == UserRole.ADMIN:
            if self.user_spinner.text not in self.users_map:
                raise Exception("Выберите пользователя")
            created_by = self.users_map[self.user_spinner.text]
        else:
            created_by = self.manager.current_user_id

        repo = get_repair_request_repository()

        if not self.equipment_input.text.strip():
            raise Exception("Заполните имя инструмента")

        if not self.problem_input.text.strip():
            raise Exception("Заполните проблему")

        return repo.create(
            created_by=created_by,
            equipment_name=self.equipment_input.text.strip(),
            description_problem=self.problem_input.text.strip(),
        )

    def _after_create(self, _):
        self.equipment_input.text = ""
        self.problem_input.text = ""
        self.refresh()

    def _error(self, error, **kwargs):
        show_modal(str(error))

    # ================= USERS =================

    def open_user_management(self, *_):
        self.manager.safe_switch("admin_user_management")

    def open_my_requests(self, *_):
        if not self.current_user:
            show_modal("Пользователь не найден")
            return
        review_screen = self.manager.get_screen("requests_review")
        review_screen.set_target_user(self.current_user)
        self.manager.safe_switch("requests_review")

    # ================= LOGOUT =================

    def logout(self, *_):
        sm = self.manager
        sm.current_user_id = None
        sm.current_role = None
        sm.safe_switch("auth")
