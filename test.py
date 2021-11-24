import dearpygui.dearpygui as dpg

dpg.create_context()

first_run = False


def input_callback(sender, data):
    global first_run
    if not first_run:
        dpg.set_value(uuid, "text replacement from input callback")
        print("I am replacing the text")  # Show in the console that the replacement is called
        first_run = True
    else:
        first_run = False


with dpg.window() as main_window:
    uuid = dpg.generate_uuid()

    dpg.add_input_text(label="Input", tag=uuid, callback=input_callback)
    dpg.add_button(label="Click me", callback=lambda: dpg.set_value(uuid, "text replacement"))

    dpg.add_date_picker()

dpg.create_viewport(title="Custom Title", width=600, height=400)
dpg.setup_dearpygui()
dpg.set_primary_window(main_window, True)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
