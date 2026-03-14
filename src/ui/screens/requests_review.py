from kivy.graphics import Rectangle, Color, Line
from kivy.metrics import dp, sp
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

STATUS_RU = {
    RequestStatus.NEW: "Новая",
    RequestStatus.IN_PROGRESS: "В работе",
    RequestStatus.DONE: "Выполнена",
    RequestStatus.CANCELED: "Отменена",
}

RU_TO_STATUS = {value: key for key, value in STATUS_RU.items()}


class RequestsReviewScreen(LightScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "requests_review"
        self.target_user: Users | None = None
        self.requests_data = []

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))

        # ===== Header =====
        header = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(8))

        # Кнопка "Назад"
        btn_back = Button(
            text="Назад",
            size_hint=(None, 1),
            width=dp(120),
            font_size=sp(16),
            on_press=self.go_back
        )
        header.add_widget(btn_back)

        # Заголовок — занимает всё оставшееся пространство
        self.title_label = Label(
            text="Просмотр заявок",
            font_size=sp(18),
            color=(0, 0, 0, 1),
            size_hint_x=1,  # занимает свободное пространство
            halign="center",
            valign="middle",
            text_size=(None, dp(50)),  # высота = высота header, ширина вычисляется автоматически
            shorten=True,  # если не помещается, обрезаем и ставим "…"
            shorten_from="right"
        )
        header.add_widget(self.title_label)

        root.add_widget(header)

        # ===== Filters =====
        filters = BoxLayout(size_hint=(1, None), height=dp(40), spacing=dp(8))
        filters.add_widget(Label(text="Фильтр", size_hint=(None, 1), width=dp(70), color=(0, 0, 0, 1)))
        self.filter_spinner = Spinner(
            text="Невыполненные",
            values=["Невыполненные", "Все"],
            size_hint=(None, 1),
            width=dp(180),
            font_size=sp(16)
        )
        self.filter_spinner.bind(text=lambda *_: self.render_requests())
        filters.add_widget(self.filter_spinner)
        filters.add_widget(Widget())  # пустое место справа
        root.add_widget(filters)

        # ===== Список заявок =====
        self.requests_container = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.requests_container.bind(minimum_height=self.requests_container.setter("height"))
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.requests_container)
        root.add_widget(scroll)

        self.add_widget(root)

    # ================== USER TARGET ==================
    def set_target_user(self, user: Users):
        self.target_user = user
        self.filter_spinner.text = "Невыполненные"
        self.load_requests()

    def go_back(self, *_):
        if self.manager.current_role == UserRole.ADMIN:
            self.manager.safe_switch("admin_user_management")
        elif self.manager.current_role == UserRole.MASTER:
            self.manager.get_screen("master_dashboard").refresh()
            self.manager.safe_switch("master_dashboard")
        else:
            self.manager.get_screen("order_dashboard").refresh()
            self.manager.safe_switch("order_dashboard")

    # ================== LOAD DATA ==================
    def load_requests(self):
        if not self.target_user:
            return
        self.run_async(
            self._load_requests_async(self.target_user),
            self._set_requests,
            self._error,
        )

    async def _load_requests_async(self, user: Users):
        repo = get_repair_request_repository()
        if user.role == UserRole.WORKER:
            requests = repo.get_by_creator(user.id)
            title = f"Заявки рабочего"
        elif user.role == UserRole.MASTER:
            requests = repo.get_by_master(user.id)
            title = f"Заявки мастера"
        else:
            requests = repo.get_all()
            title = "Все заявки"
        return title, requests

    def _set_requests(self, payload):
        self.title_label.text, self.requests_data = payload
        self.render_requests()

    # ================== RENDER ==================
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
                Label(text="Нет заявок", size_hint=(1, None), height=dp(35), font_size=sp(16), color=(0, 0, 0, 1))
            )
            return
        for request in data:
            self.requests_container.add_widget(self._build_request_row(request))

    def _build_request_row(self, request: RepairRequests):
        row = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(150),
            spacing=dp(6),
            padding=dp(6)
        )

        # ===== Background =====
        with row.canvas.before:
            Color(0.85, 0.85, 0.85, 1)
            row.bg_rect = Rectangle(pos=row.pos, size=row.size)

        def update_bg(instance, _):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size

        row.bind(pos=update_bg, size=update_bg)

        # ===== Info =====
        row.add_widget(Label(
            text=f"[{request.id}] {request.equipment_name} | {STATUS_RU.get(request.status, request.status.value)}",
            size_hint=(1, None),
            height=dp(28),
            font_size=sp(16),
            color=(0, 0, 0, 1),
            halign="center",
            valign="middle",
            text_size=(self.width, None)
        ))
        row.add_widget(Label(
            text=f"Проблема: {request.description_problem}",
            size_hint=(1, None),
            height=dp(28),
            font_size=sp(16),
            color=(0, 0, 0, 1),
            halign="center",
            valign="middle",
            text_size=(self.width, None)
        ))

        # ===== Controls =====
        controls_container = ScrollView(size_hint=(1, None), height=dp(40), do_scroll_y=False)
        controls = BoxLayout(
            size_hint=(None, 1),
            spacing=dp(6),
            height=dp(40)
        )
        controls.bind(minimum_width=controls.setter('width'))

        current_role = self.manager.current_role

        # ===== Добавляем кнопки =====
        if current_role in (UserRole.MASTER, UserRole.ADMIN):
            # статус
            status_spinner = Spinner(
                text=STATUS_RU.get(request.status, request.status.value),
                values=list(RU_TO_STATUS.keys()),
                size_hint=(None, 1),
                width=dp(180),
                font_size=sp(14)
            )
            controls.add_widget(status_spinner)

            # смена статуса
            controls.add_widget(Button(
                text="Сменить статус",
                size_hint=(None, 1),
                width=dp(140),
                font_size=sp(14),
                on_press=lambda _, req=request, sp=status_spinner: self.update_status(req, sp.text)
            ))

            # взять заявку
            if request.assigned_master is None and current_role == UserRole.MASTER:
                controls.add_widget(Button(
                    text="Взяться за заявку",
                    size_hint=(None, 1),
                    width=dp(140),
                    font_size=sp(14),
                    on_press=lambda _, req=request: self.take_request(req)
                ))

            # удалить заявку
            if current_role == UserRole.ADMIN:
                controls.add_widget(Button(
                    text="Удалить заявку",
                    size_hint=(None, 1),
                    width=dp(140),
                    font_size=sp(14),
                    on_press=lambda _, req=request: self.delete_request(req)
                ))
        else:
            # просто просмотр
            controls.add_widget(Label(
                text="Только просмотр",
                font_size=sp(14),
                color=(0, 0, 0, 1),
                size_hint=(None, 1),
                width=dp(150),
                halign="center",
                valign="middle",
                text_size=(dp(150), None)
            ))

        controls_container.add_widget(controls)
        row.add_widget(controls_container)

        return row

    # ================== ACTIONS ==================
    def update_status(self, request, new_status_ru: str):
        status = RU_TO_STATUS.get(new_status_ru)
        if not status:
            show_modal("Неизвестный статус")
            return
        self.run_async(self._update_status_async(request.id, status), self._after_action, self._error)

    async def _update_status_async(self, request_id: int, status: RequestStatus):
        repo = get_repair_request_repository()
        fresh = repo.get_by_id(request_id)
        if not fresh:
            raise Exception("Заявка не найдена")
        repo.update_status(fresh, status)
        return "Статус успешно изменён"

    def take_request(self, request):
        self.run_async(self._take_request_async(request.id), self._after_action, self._error)

    async def _take_request_async(self, request_id: int):
        repo = get_repair_request_repository()
        fresh = repo.get_by_id(request_id)
        if not fresh:
            raise Exception("Заявка не найдена")
        if fresh.assigned_master is not None:
            raise Exception("Заявка уже закреплена за мастером")
        repo.update(fresh, assigned_master=self.manager.current_user_id)
        return "Заявка успешно прикреплена"

    def delete_request(self, request):
        self.run_async(self._delete_request_async(request.id), self._after_action, self._error)

    async def _delete_request_async(self, request_id: int):
        repo = get_repair_request_repository()
        fresh = repo.get_by_id(request_id)
        if not fresh:
            raise Exception("Заявка не найдена")
        repo.delete(request_id)
        return "Заявка успешно удалена"

    def _after_action(self, message: str):
        self.load_requests()
        show_modal(message)

    def _error(self, error, **kwargs):
        show_modal(str(error))