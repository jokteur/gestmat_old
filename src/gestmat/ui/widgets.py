import colorsys
from datetime import datetime
import dearpygui.dearpygui as dpg

from ..item.representation import Item
from .res import Ressources

ressources = Ressources()


def _hsv_to_rgb(h, s, v):
    if s == 0.0:
        return (v, v, v)
    i = int(h * 6.0)  # XXX assume int() truncates!
    f = (h * 6.0) - i
    p, q, t = v * (1.0 - s), v * (1.0 - s * f), v * (1.0 - s * (1.0 - f))
    i %= 6
    if i == 0:
        return (255 * v, 255 * t, 255 * p)
    if i == 1:
        return (255 * q, 255 * v, 255 * p)
    if i == 2:
        return (255 * p, 255 * v, 255 * t)
    if i == 3:
        return (255 * p, 255 * q, 255 * v)
    if i == 4:
        return (255 * t, 255 * p, 255 * v)
    if i == 5:
        return (255 * v, 255 * p, 255 * q)


def colored_button(text, parent, hue, callback=lambda *args: None, rounding=0, padding=3):
    if not ressources.counter:
        ressources.counter = 1

    with dpg.theme(tag=f"_colored_button{ressources.counter}"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(hue, 0.9, 0.9))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(hue, 0.7, 0.7))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(hue, 0.8, 0.8))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, rounding)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, padding, padding)

    dpg.add_button(label=text, callback=callback, parent=parent)
    dpg.bind_item_theme(dpg.last_item(), f"_colored_button{ressources.counter}")

    ressources.counter += 1


def error(text: str, parent):
    tag = dpg.generate_uuid()
    with dpg.popup(
        dpg.last_item(),
        mousebutton=dpg.mvMouseButton_Middle,
        modal=True,
        tag="popup_error_msg",
    ):
        dpg.add_text(text)
        dpg.add_button(label="OK", callback=lambda: dpg.configure_item(tag, show=False))
    dpg.configure_item("popup_error_msg", show=True)


def help(text: str, parent, color=(125, 125, 125)):
    dpg.add_text("(?)", color=color, parent=parent)
    with dpg.tooltip(dpg.last_item()):
        dpg.add_text(text)


def title(text: str, parent, color=(70, 70, 70)):
    item = dpg.add_text(text, parent=parent, color=color)

    if ressources.fonts and "big" in ressources.fonts:
        dpg.bind_item_font(item, ressources.fonts["big"])


def subtitle(text: str, parent, color=(10, 10, 10)):
    item = dpg.add_text(text, parent=parent, color=color)

    if ressources.fonts and "bold" in ressources.fonts:
        dpg.bind_item_font(item, ressources.fonts["bold"])


def modal(text: str):
    tag = "modal_popup"

    def stop_show():
        dpg.configure_item(tag, show=False)

    dpg.delete_item(tag, children_only=True)
    dpg.add_text(text, parent=tag)
    dpg.add_button(label="OK", callback=stop_show, parent=tag)

    popup_width = dpg.get_item_width("modal_popup")
    popup_height = dpg.get_item_height("modal_popup")
    window_width = dpg.get_item_width("primary_window")
    window_height = dpg.get_item_height("primary_window")
    if popup_width < window_width and popup_height < window_height:
        dpg.set_item_pos(
            "modal_popup", [(window_width - popup_width) / 2, (window_height - popup_height) / 2]
        )
    dpg.configure_item(tag, show=True)


class DateWidget:
    def __init__(self, parent, date: datetime = None) -> None:
        self.memory = dict(
            day_uuid=dpg.generate_uuid(),
            month_uuid=dpg.generate_uuid(),
            year_uuid=dpg.generate_uuid(),
        )
        self.parent = parent

        def callback(sender, data):
            max_length = 2
            if sender == self.memory["year_uuid"]:
                max_length = 4

            # Verify if callback not called twice
            if sender not in self.memory:
                self.memory[sender] = False

            set_data = None

            if not self.memory[sender]:
                unauthorized_chars = [s for s in [".", "+", "-", "*", "/"] if s in data]
                if unauthorized_chars:
                    set_data = "".join([s for s in data if s.isdigit()])
                if len(data) == 2:
                    if sender == self.memory["day_uuid"]:
                        dpg.focus_item(self.memory["month_uuid"])
                    elif sender == self.memory["month_uuid"]:
                        dpg.focus_item(self.memory["year_uuid"])
            else:
                self.memory[sender] = False

            if isinstance(set_data, str):
                self.memory[sender] = True
                dpg.set_value(self.memory["day_uuid"], set_data)

        with dpg.group(horizontal=True, parent=parent):
            dpg.add_input_text(
                decimal=True,
                no_spaces=True,
                width=30,
                tag=self.memory["day_uuid"],
                callback=callback,
                default_value=date.day if date else "",
                hint="Jour",
            )
            dpg.add_text("/")
            dpg.add_input_text(
                decimal=True,
                no_spaces=True,
                width=30,
                tag=self.memory["month_uuid"],
                callback=callback,
                default_value=date.month if date else "",
                hint="Mois",
            )
            dpg.add_text("/")
            dpg.add_input_text(
                decimal=True,
                no_spaces=True,
                width=60,
                tag=self.memory["year_uuid"],
                callback=callback,
                default_value=date.year if date else "",
                hint="Année",
            )

    def get_date(self) -> datetime:
        year = dpg.get_value(self.memory["year_uuid"])
        month = dpg.get_value(self.memory["month_uuid"])
        day = dpg.get_value(self.memory["day_uuid"])
        try:
            date = datetime(int(year), int(month), int(day))
        except ValueError:
            return None
        return date


def item_info_box(item: Item, parent: int):
    for prop in item._category.properties_order:
        with dpg.group(horizontal=True, parent=parent) as g_uid:
            subtitle(f"{item._properties[prop].name}", g_uid)
            dpg.add_text(f"{item._properties[prop].value}")
