import dearpygui.dearpygui as dpg

from ...item.manager import ItemManager
from ..panel import Panel


class LoanPanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)

    def nav_window(self, parent) -> None:
        dpg.add_text("Retour", parent=parent)
