from kivy.graphics import Rectangle, Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget

from src.database.models import RequestStatus, UserRole, Users, RepairRequests
from src.repository.repair_requests import get_repair_request_repository
from src.ui.screens.base import LightScreen
from src.ui.screens.modal_window.modal_with_ok import show_modal


class RequestsReviewScreen(LightScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "requests_review"
        self.target_user: Users | None = None
        self.requests_data = []

        root = BoxLayout(orientation="vertical", padding=15, spacing=10)

        header = BoxLayout(size_hint=(1, None), height=40, spacing=8)
        self.title_label = Label(text="Просмотр заявок", color=(0, 0, 0, 1))
        header.add_widget(self.title_label)
        header.add_widget(Button(text="Назад", size_hint=(None, 1), width=120, on_press=self.go_back))
        root.add_widget(header)

        filters = BoxLayout(size_hint=(1, None), height=40, spacing=8)
        filters.add_widget(Label(text="Фильтр", size_hint=(None, 1), width=70, color=(0, 0, 0, 1)))
        self.filter_spinner = Spinner(
            text="Невыполненные",
            values=["Невыполненные", "Все"],
            size_hint=(None, 1),
            width=200,
        )
        self.filter_spinner.bind(text=lambda *_: self.render_requests())
        filters.add_widget(self.filter_spinner)
        filters.add_widget(Label())
        root.add_widget(filters)

        self.requests_container = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.requests_container.bind(minimum_height=self.requests_container.setter("height"))

        scroll = ScrollView()
        scroll.add_widget(self.requests_container)
        root.add_widget(scroll)

        self.add_widget(root)

    def set_target_user(self, user: Users):
        self.target_user = user
        self.filter_spinner.text = "Невыполненные"
        self.load_requests()

    def go_back(self, *_):
        self.manager.safe_switch("admin_user_management")

    def load_requests(self):
        if not self.target_user:
            return

        self.run_async(
            self._load_requests_async(self.target_user),
            self._set_requests,
            self._error,
        )

    async def _load_requests_async(self, user: Users):
        repo = await get_repair_request_repository()

        if user.role == UserRole.WORKER:
            requests = await repo.get_by_creator(user.id)
            title = f"Заявки рабочего: {user.full_name}"
        elif user.role == UserRole.MASTER:
            requests = await repo.get_by_master(user.id)
            title = f"Заявки мастера: {user.full_name}"
        else:
            requests = await repo.get_all()
            title = "Все заявки (ADMIN)"

        return title, requests

    def _set_requests(self, payload):
        self.title_label.text, self.requests_data = payload
        self.render_requests()

    def render_requests(self):
        self.requests_container.clear_widgets()

        unresolved_statuses = {RequestStatus.NEW, RequestStatus.IN_PROGRESS}
        only_unresolved = self.filter_spinner.text == "Невыполненные"
        data = [
            request for request in self.requests_data
            if not only_unresolved or request.status in unresolved_statuses
        ]

        if not data:
            self.requests_container.add_widget(
                Label(text="Нет заявок", size_hint=(1, None), height=35, color=(0, 0, 0, 1))
            )
            return

        for request in data:
            self.requests_container.add_widget(self._build_request_row(request))

    def _build_request_row(self, request: RepairRequests):
        row = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=150,
            spacing=6,
        )

        # Рисуем серый фон
        with row.canvas.before:
            Color(0.8, 0.8, 0.8, 1)  # серый
            row.bg_rect = Rectangle(pos=row.pos, size=row.size)

        # Обновляем фон при изменении размера / позиции
        def update_bg(instance, value):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size

        row.bind(pos=update_bg, size=update_bg)

        row.add_widget(
            Label(
                text=f"[{request.id}] {request.equipment_name} | {request.status.value}",
                size_hint=(1, None),
                height=30,
                color=(0, 0, 0, 1),
                halign="center",
                text_size=(1000, None),
            )
        )

        row.add_widget(
            Label(
                text=f"Проблема: {request.description_problem}",
                size_hint=(1, None),
                height=30,
                color=(0, 0, 0, 1),
                halign="center",
                text_size=(1000, None),
            )
        )


        controls = BoxLayout(size_hint=(1, None), height=35, spacing=6)
        current_role = self.manager.current_role

        # Добавляем пустой виджет слева для центрирования
        controls.add_widget(Widget(size_hint_x=1))

        if current_role in (UserRole.MASTER, UserRole.ADMIN):
            status_spinner = Spinner(
                text=request.status.value,
                values=[status.value for status in RequestStatus],
                size_hint=(None, 1),
                width=180,
            )
            controls.add_widget(status_spinner)
            controls.add_widget(
                Button(
                    text="Сменить статус",
                    size_hint=(None, 1),
                    width=180,
                    on_press=lambda _, req=request, sp=status_spinner: self.update_status(req, sp.text),
                )
            )

            if request.assigned_master is None and current_role == UserRole.MASTER:
                controls.add_widget(
                    Button(
                        text="Взяться за заявку",
                        on_press=lambda _, req=request: self.take_request(req),
                    )
                )

        else:
            controls.add_widget(Label(text="Только просмотр", color=(0, 0, 0, 1)))

        # Добавляем пустой виджет слева для центрирования
        controls.add_widget(Widget(size_hint_x=1))

        row.add_widget(controls)
        return row

    def update_status(self, request, new_status: str):
        self.run_async(
            self._update_status_async(request.id, RequestStatus(new_status)),
            self._after_action,
            self._error,
        )

    async def _update_status_async(self, request_id: int, status: RequestStatus):
        repo = await get_repair_request_repository()
        fresh = await repo.get_by_id(request_id)
        if not fresh:
            raise Exception("Заявка не найдена")

        return await repo.update_status(fresh, status)

    def take_request(self, request):
        self.run_async(
            self._take_request_async(request.id),
            self._after_action,
            self._error,
        )

    async def _take_request_async(self, request_id: int):
        repo = await get_repair_request_repository()
        fresh = await repo.get_by_id(request_id)

        if not fresh:
            raise Exception("Заявка не найдена")

        if fresh.assigned_master is not None:
            raise Exception("Заявка уже закреплена за мастером")

        return await repo.update(fresh, assigned_master=self.manager.current_user_id)

    def _after_action(self, _):
        self.load_requests()

    def _error(self, error, **kwargs):
        show_modal(str(error))