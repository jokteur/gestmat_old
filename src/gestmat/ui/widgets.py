import colorsys
import dearpygui.dearpygui as dpg

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
    dpg.configure_item(tag, show=True)
