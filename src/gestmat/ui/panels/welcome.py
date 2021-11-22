from ...item.manager import ItemManager
from ..panel import Panel


class WelcomePanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)
