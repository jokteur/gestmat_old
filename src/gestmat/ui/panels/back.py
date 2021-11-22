import dearpygui.dearpygui as dpg
from ...item.manager import ItemManager
from ..panel import Panel


class ReturnPanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)
