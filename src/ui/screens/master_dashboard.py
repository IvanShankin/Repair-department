from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from src.database.models import RepairRequests, RequestStatus, UserRole, Users
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


class MasterDashboardScreen(LightScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "master_dashboard"

        self.current_user: Users | None = None
        self.requests_data: list[RepairRequests] = []
        self.selected_request_id: int | None = None
        self.row_by_request_id: dict[int, BoxLayout] = {}

        root = BoxLayout(orientation="vertical", padding=15, spacing=10)

        header = BoxLayout(size_hint=(1, None), height=45)
        self.title_label = Label(
            text="Нераспределённые заявки",
            font_size=20,
            color=(0, 0, 0, 1),
        )
        header.add_widget(self.title_label)
        header.add_widget(
            Button(
                text="Выйти",
                size_hint=(None, 1),
                width=120,
                on_press=self.logout,
            )
        )
        root.add_widget(header)

        self.requests_container = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.requests_container.bind(minimum_height=self.requests_container.setter("height"))

        scroll = ScrollView()
        scroll.add_widget(self.requests_container)
        root.add_widget(scroll)

        actions = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        actions.add_widget(
            Button(
                text="Взяться за заявку",
                on_press=self.take_selected_request,
            )
        )
        actions.add_widget(
            Button(
                text="Мои заявки",
                on_press=self.open_my_requests,
            )
        )
        root.add_widget(actions)

        self.add_widget(root)

    def refresh(self):
        self.selected_request_id = None
        self.row_by_request_id = {}
        self.run_async(self._refresh_async(), self._after_refresh, self._error)

    async def _refresh_async(self):
        user_repo = await get_user_repository()
        requests_repo = await get_repair_request_repository()

        current_user = await user_repo.get_by_id(self.manager.current_user_id)
        requests = await requests_repo.get_all()
        unassigned = [request for request in requests if request.assigned_master is None]
        return current_user, unassigned

    def _after_refresh(self, payload):
        self.current_user, self.requests_data = payload
        self.render_requests()

    def render_requests(self):
        self.requests_container.clear_widgets()
        self.row_by_request_id = {}

        if not self.requests_data:
            self.requests_container.add_widget(
                Label(text="Нет нераспределённых заявок", size_hint=(1, None), height=40, color=(0, 0, 0, 1))
            )
            return

        for request in self.requests_data:
            row = self._build_request_row(request)
            self.row_by_request_id[request.id] = row
            self.requests_container.add_widget(row)

    def _build_request_row(self, request: RepairRequests):
        row = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=90,
            padding=8,
            spacing=4,
        )

        with row.canvas.before:
            row.bg_color = Color(0.82, 0.82, 0.82, 1)
            row.bg_rect = Rectangle(pos=row.pos, size=row.size)

        def update_bg(instance, _):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size

        row.bind(pos=update_bg, size=update_bg)

        row.add_widget(
            Label(
                text=f"[{request.id}] {request.equipment_name}",
                color=(0, 0, 0, 1),
                halign="left",
                text_size=(1000, None),
            )
        )
        row.add_widget(
            Label(
                text=f"Статус: {STATUS_RU.get(request.status, request.status.value)} | Проблема: {request.description_problem}",
                color=(0, 0, 0, 1),
                halign="left",
                text_size=(1000, None),
            )
        )

        row.add_widget(
            Button(
                text="Выбрать",
                size_hint=(1, None),
                height=34,
                on_press=lambda *_: self.select_request(request.id),
            )
        )
        return row

    def select_request(self, request_id: int):
        self.selected_request_id = request_id
        for row_request_id, row in self.row_by_request_id.items():
            color = (0.55, 0.80, 0.55, 1) if row_request_id == request_id else (0.82, 0.82, 0.82, 1)
            row.bg_color.rgba = color

    def take_selected_request(self, *_):
        if not self.selected_request_id:
            show_modal("Сначала выберите заявку")
            return

        self.run_async(
            self._take_request_async(self.selected_request_id),
            self._after_take,
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

    def _after_take(self, _):
        self.refresh()

    def open_my_requests(self, *_):
        if not self.current_user or self.current_user.role != UserRole.MASTER:
            show_modal("Пользователь мастера не найден")
            return

        review_screen = self.manager.get_screen("requests_review")
        review_screen.set_target_user(self.current_user)
        self.manager.safe_switch("requests_review")

    def logout(self, *_):
        sm = self.manager
        sm.current_user_id = None
        sm.current_role = None
        sm.safe_switch("auth")

    def _error(self, error, **kwargs):
        show_modal(str(error))
