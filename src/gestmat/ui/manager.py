import os
import tempfile
import dearpygui.dearpygui as dpg
import dearpygui_ext.themes as dpg_ext
import dearpygui.demo as demo

from ..ui.widgets import modal

from .panel import Panel
from .panels.management import ManagementPanel
from .panels.loan import LoanPanel
from .panels.state import StatePanel
from .panels.back import ReturnPanel
from .panels.welcome import WelcomePanel
from ..item.manager import ItemManager
from .themes import create_theme_imgui_light
from .res import Ressources, Singleton

ressources = Ressources()


class UIManager(metaclass=Singleton):
    panels: dict[str, Panel]
    current_item_manager: ItemManager
    buttons: list[dict]
    current_panel: Panel = None

    def __init__(self, item_manager: ItemManager) -> None:
        """Class that manages the UI of the program"""
        self.current_item_manager = item_manager
        self.panels = {
            "management": ManagementPanel,
            "loan": LoanPanel,
            "return": ReturnPanel,
            "welcome": WelcomePanel,
            "state": StatePanel,
        }

        # Menu buttons

        opts = {"width": 100, "height": 40}
        self.buttons = {}
        self.buttons["loan"] = dict(label="Prêt", callback=lambda: self.load_panel("loan"), **opts)
        # self.buttons["return"] = dict(
        #     label="Retour", callback=lambda: self.load_panel("return"), **opts
        # )
        self.buttons["state"] = dict(
            label="État", callback=lambda: self.load_panel("state"), **opts
        )
        self.buttons["management"] = dict(
            label="Gestion", callback=lambda: self.load_panel("management"), **opts
        )
        self.uuids = dict()

    def init(self) -> None:
        """Initializes the window and launches the app."""

        dpg.create_context()
        light_theme = create_theme_imgui_light()

        dpg.bind_theme(light_theme)

        with dpg.font_registry():
            ressources.set_attr(
                "fonts",
                {
                    "default": dpg.add_font("assets/verdana.ttf", 19),
                    "big": dpg.add_font("assets/verdana.ttf", 30),
                    "bold": dpg.add_font("assets/verdanab.ttf", 19),
                },
            )

        with dpg.window(tag="primary_window"):
            dpg.bind_font(ressources.fonts["default"])

            with dpg.menu_bar(tag="menu_top"):
                dpg.add_menu(label="Options")

            with dpg.group(horizontal=True, width=0):
                with dpg.child_window(tag="nav_menu", width=120):
                    pass
                with dpg.child_window(tag="panels", width=-1, height=0):
                    pass
            dpg.add_button(
                label="", pos=[500, 250], width=0, height=0, show=False, tag="modal_button_popup"
            )
            with dpg.popup("modal_button_popup", modal=True, tag="modal_popup"):
                pass

        dpg.create_viewport(title="Gestion materiel", width=1100, height=700)

        self.load_panel("loan")
        # demo.show_demo()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary_window", True)

        # Remove splash screen
        # if "NUITKA_ONEFILE_PARENT" in os.environ:
        #     splash_filename = os.path.join(
        #         tempfile.gettempdir(),
        #         "onefile_%d_splash_feedback.tmp" % int(os.environ["NUITKA_ONEFILE_PARENT"]),
        #     )

        #     if os.path.exists(splash_filename):
        #         os.unlink(splash_filename)

        dpg.start_dearpygui()
        dpg.destroy_context()

    def load_panel(self, name: str) -> None:
        dpg.delete_item("nav_menu", children_only=True)
        dpg.delete_item("panels", children_only=True)
        dpg.add_text("Matériel", parent="nav_menu")

        if self.current_panel:
            self.current_panel.delete_items()

        self.current_panel = self.panels[name](self.current_item_manager)

        for key, value in self.buttons.items():
            if key == name:
                dpg.add_button(parent="nav_menu", indent=10, **value)
            else:
                dpg.add_button(parent="nav_menu", **value)

        self.current_panel.main_window("panels")

        # dpg.delete_item("panels")
