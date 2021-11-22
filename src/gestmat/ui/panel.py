import dearpygui.dearpygui as dpg

from matgest.item.representation import Item

from ..item.manager import ItemManager


class Panel:
    items: list[str]
    manager: ItemManager

    def __init__(self, manager: ItemManager) -> None:
        self.items = []
        self.manager = manager

    def delete_items(self) -> None:
        for item in self.items:
            dpg.delete_item(item)

    def main_window(self, parent) -> None:
        pass

    def nav_window(self, parent) -> None:
        pass
