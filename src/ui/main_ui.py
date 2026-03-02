import asyncio
import threading
from asyncio import AbstractEventLoop

from kivy.app import App
from kivy.uix.screenmanager import FadeTransition

from src.service.utils.event_loop import start_loop
from src.ui.screens.auth import AuthScreen
from src.ui.screens.dashboard import DashboardScreen
from src.ui.screens.screen_manager import RootScreenManager



class RepairApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loop: AbstractEventLoop | None = None

    def build(self):
        sm = RootScreenManager(
            transition=FadeTransition(duration=0.15)
        )

        self.loop = asyncio.new_event_loop()

        t = threading.Thread(
            target=start_loop,
            args=(self.loop,),
            daemon=True,
        )
        t.start()


        sm.add_widget(AuthScreen())
        sm.add_widget(DashboardScreen())

        sm.current = "auth"

        return sm