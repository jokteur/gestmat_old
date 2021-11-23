import dearpygui.dearpygui as dpg

from ...item.representation import ItemCategory, Item

from ...item.manager import ItemManager, Person
from ..panel import Panel
from ..widgets import title, subtitle


class LoanPanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)
        self.memory = dict()

    def generate_height(self, num):
        return 30 * (num + 1)

    def table_person(self, persons: list[Person], parent):
        def _sort_callback(sender, sort_specs):
            if sort_specs is None:
                return

            headers = {num: i for i, num in enumerate(dpg.get_item_children(sender, 0))}

            rows = dpg.get_item_children(sender, 1)

            # create a list that can be sorted based on first cell
            # value, keeping track of row and value used to sort
            sortable_list = []
            for row in rows:
                cell = dpg.get_item_children(row, 1)[headers[sort_specs[0][0]]]
                # cell = dpg.get_item_children(cell, 1)[0]
                sortable_list.append([row, dpg.get_value(cell)])

            def _sorter(e):
                return e[1]

            sortable_list.sort(key=_sorter, reverse=sort_specs[0][1] < 0)

            # create list of just sorted row ids
            new_order = []
            for pair in sortable_list:
                new_order.append(pair[0])

            dpg.reorder_items(sender, 1, new_order)

        with dpg.table(
            header_row=True,
            row_background=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True,
            resizable=True,
            scrollY=True,
            scrollX=True,
            delay_search=True,
            parent=parent,
            sortable=True,
            callback=_sort_callback,
            height=self.generate_height(len(persons)),
            policy=dpg.mvTable_SizingStretchProp,
        ) as table_id:
            dpg.add_table_column(label="Nom")
            dpg.add_table_column(label="Prénom")
            dpg.add_table_column(label="Date de naissance")
            dpg.add_table_column(label="Unité / Chambre")
            dpg.add_table_column(label="Remarque")
            for person in persons:
                with dpg.table_row():
                    dpg.add_text(person.surname)
                    dpg.add_text(person.name)
                    dpg.add_text(person.birthday.strftime("%Y/%m/%d"))
                    dpg.add_text(person.place)
                    dpg.add_text(person.note)

    def build_object_table(self, cat: ItemCategory, items: list[Item], parent) -> None:
        def _sort_callback(sender, sort_specs):
            if sort_specs is None:
                return

            headers = {num: i for i, num in enumerate(dpg.get_item_children(sender, 0))}

            rows = dpg.get_item_children(sender, 1)

            # create a list that can be sorted based on first cell
            # value, keeping track of row and value used to sort
            sortable_list = []
            for row in rows:
                # print(row)
                cell = dpg.get_item_children(row, 1)[headers[sort_specs[0][0]]]
                sortable_list.append([row, dpg.get_value(cell)])

            def _sorter(e):
                return e[1]

            sortable_list.sort(key=_sorter, reverse=sort_specs[0][1] < 0)

            # create list of just sorted row ids
            new_order = []
            for pair in sortable_list:
                new_order.append(pair[0])

            dpg.reorder_items(sender, 1, new_order)

        items = [item for item in items if item not in self.manager.loans]

        if items:
            table_id = dpg.generate_uuid()
            with dpg.table(
                header_row=True,
                row_background=True,
                borders_innerH=True,
                borders_outerH=True,
                borders_innerV=True,
                borders_outerV=True,
                resizable=True,
                scrollY=True,
                scrollX=True,
                delay_search=True,
                parent=parent,
                sortable=True,
                callback=_sort_callback,
                policy=dpg.mvTable_SizingStretchProp,
                height=self.generate_height(len(items)),
                tag=table_id,
            ):
                props = list(cat.properties_order)
                # dpg.add_table_column(
                #     label="", no_sort=True, width=10, width_fixed=True, no_resize=True
                # )

                for prop in props:
                    dpg.add_table_column(label=prop.name)

                for item in items:
                    with dpg.table_row():
                        for prop in props:
                            if not prop in item.properties:
                                item.add_property(prop)
                            dpg.add_text(item.properties[prop].value)
        else:
            dpg.add_text("Pas d'objets disponible", parent=parent)

    def new_object(self, parent) -> None:
        cat_names = {cat.description: cat for cat in self.manager.categories.values()}
        g_uuid = dpg.generate_uuid()

        def _replace_objects(s, a, u):
            nonlocal cat_names
            dpg.delete_item(g_uuid, children_only=True)
            cat = cat_names[a]
            self.build_object_table(cat, cat.registered_items, g_uuid)

        dpg.add_combo(
            list(cat_names.keys()),
            label="Choisir une catégorie d'objet",
            width=150,
            callback=_replace_objects,
        )
        with dpg.group(tag=g_uuid):
            pass

    def build_loan_info_widget(self, g_uuid):
        day_uuid = dpg.generate_uuid()
        month_uuid = dpg.generate_uuid()
        year_uuid = dpg.generate_uuid()
        birthday_error_g = dpg.generate_uuid()

        memory = dict()

        def _birthday_callback(sender, data):
            max_length = 2
            if sender == year_uuid:
                max_length = 4

            # Verify if callback not called twice
            if sender not in memory:
                memory[sender] = False

            set_data = None

            if not memory[sender]:
                # unauthorized_chars = [s for s in [".", "+", "-", "*", "/"] if s in data]
                # if unauthorized_chars:
                #     set_data = "".join([s for s in data if s.isdigit()])
                set_data = "123"
            else:
                memory[sender] = False

            if isinstance(set_data, str):
                memory[sender] = True
                print("setting")
                dpg.set_value(day_uuid, "blabla")

        dpg.add_button(
            label="click", callback=lambda: dpg.set_value(day_uuid, "test"), parent=g_uuid
        )

        with dpg.group(horizontal=True, parent=g_uuid):
            dpg.add_text("Nom:")
            dpg.add_input_text(width=200)
        with dpg.group(horizontal=True, parent=g_uuid):
            dpg.add_text("Prénom:")
            dpg.add_input_text(width=200)
        with dpg.group(horizontal=True, parent=g_uuid):
            dpg.add_text("Date de naissance:")
            dpg.add_input_text(
                decimal=True, no_spaces=True, width=30, tag=day_uuid, callback=_birthday_callback
            )
            dpg.add_text("/")
            dpg.add_input_text(
                decimal=True, no_spaces=True, width=30, tag=month_uuid, callback=_birthday_callback
            )
            dpg.add_text("/")
            dpg.add_input_text(
                decimal=True, no_spaces=True, width=60, tag=year_uuid, callback=_birthday_callback
            )
            with dpg.group(tag=birthday_error_g):
                pass

    def main_window(self, parent) -> None:
        self.parent = parent
        title("Faire un nouveau prêt", parent)

        subtitle("Informations pour le prêt", parent)
        loan_info_uuid = dpg.generate_uuid()
        with dpg.group(parent=parent, tag=loan_info_uuid):
            pass
        self.build_loan_info_widget(loan_info_uuid)

        subtitle("Objet(s)", parent)

        new_obj_uuid = dpg.generate_uuid()
        with dpg.group(parent=parent, tag=new_obj_uuid):
            self.new_object(new_obj_uuid)
        dpg.add_button(label="+", parent=parent)

        g_uuid = dpg.generate_uuid()
        with dpg.group(tag=g_uuid, parent=parent):
            pass
        # self.table_person(self.manager.persons, g_uuid)
