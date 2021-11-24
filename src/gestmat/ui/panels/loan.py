import dearpygui.dearpygui as dpg

from ...item.representation import ItemCategory, Item

from ...item.manager import ItemManager, Person
from ..panel import Panel
from ..widgets import title, subtitle


class LoanPanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)
        self.memory = dict(objects=dict())

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

        def _choose_person(s, d, person):
            self.build_loan_info_widget(person)
            dpg.configure_item(self.memory["person_popup"], show=False)

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
            dpg.add_table_column(label="Action", no_sort=True)
            dpg.add_table_column(label="Nom")
            dpg.add_table_column(label="Prénom")
            dpg.add_table_column(label="Date de naissance")
            dpg.add_table_column(label="Unité / Chambre")
            dpg.add_table_column(label="Remarque")
            for person in persons:
                with dpg.table_row():
                    dpg.add_button(
                        label="Choisir",
                        callback=_choose_person,
                        user_data=person,
                    )
                    dpg.add_text(person.surname)
                    dpg.add_text(person.name)
                    dpg.add_text(person.birthday.strftime("%Y/%m/%d"))
                    dpg.add_text(person.place)
                    dpg.add_text(person.note)

    def choose_item(self, obj_num, item: Item):
        tag = self.memory["objects"][obj_num]
        dpg.delete_item(tag, children_only=True)
        cat = item.category
        props = list(cat.properties_order)

        with dpg.group(parent=tag, horizontal=True) as g_uid:
            dpg.add_button(
                label="Enlever", callback=lambda *args: dpg.delete_item(tag, children_only=True)
            )
            subtitle(cat.description, g_uid)
            if item in self.manager.loans:
                dpg.add_text(" (déjà emprunté) ")
            for i, prop in enumerate(props):
                value = item.properties[prop].value
                if not value:
                    continue
                if i:
                    dpg.add_text(" / ")
                dpg.add_text(f"{prop.name} : {item.properties[prop].value}")

    def build_object_table(self, cat: ItemCategory, obj_num, parent, all_items=False) -> None:
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

        dpg.delete_item(parent, children_only=True)

        items = [
            item for item in cat.registered_items if item not in self.manager.loans or all_items
        ]

        def _set_items(s, d, u):
            self.build_object_table(cat, obj_num, parent, d)

        dpg.add_checkbox(
            label="Inclure les objets déjà empruntés",
            callback=_set_items,
            parent=parent,
            default_value=all_items,
        )

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

                dpg.add_table_column(
                    label="Action",
                    no_sort=True,
                    width=50,
                    width_fixed=True,
                )
                if all_items:
                    dpg.add_table_column(
                        label="Emprunté?", width=70, no_sort=True, width_fixed=True
                    )
                for prop in props:
                    dpg.add_table_column(label=prop.name)

                for item in items:
                    with dpg.table_row():
                        dpg.add_button(
                            label="Choisir",
                            callback=lambda *args, item=item: self.choose_item(obj_num, item),
                        )
                        if all_items:
                            if item in self.manager.loans:
                                dpg.add_text("Oui")
                            else:
                                dpg.add_text("Non")
                        for prop in props:
                            if not prop in item.properties:
                                item.add_property(prop)
                            dpg.add_text(item.properties[prop].value)
        else:
            dpg.add_text("Pas d'objets disponible", parent=parent)

    def new_object(self, parent) -> None:
        cat_names = {cat.description: cat for cat in self.manager.categories.values()}

        num = len(self.memory["objects"].keys())
        tag = dpg.generate_uuid()
        self.memory["objects"][num] = tag
        with dpg.group(tag=tag, parent=parent):
            g_uuid = dpg.generate_uuid()

            def _replace_objects(s, a, u):
                nonlocal cat_names
                dpg.delete_item(g_uuid, children_only=True)
                cat = cat_names[a]
                self.build_object_table(cat, num, g_uuid)

            dpg.add_combo(
                list(cat_names.keys()),
                label="Choisir une catégorie d'objet",
                width=150,
                callback=_replace_objects,
            )

            with dpg.group(tag=g_uuid):
                pass
            with dpg.child_window(height=1):
                pass

    def build_loan_info_widget(self, person: Person = None):
        g_uuid = self.memory["loan_info_uuid"]
        self.memory.update(
            day_uuid=dpg.generate_uuid(),
            month_uuid=dpg.generate_uuid(),
            year_uuid=dpg.generate_uuid(),
            birthday_error_g=dpg.generate_uuid(),
            name_uuid=dpg.generate_uuid(),
            surname_uuid=dpg.generate_uuid(),
            place_uuid=dpg.generate_uuid(),
            note_uuid=dpg.generate_uuid(),
        )
        dpg.delete_item(self.memory["loan_info_uuid"], children_only=True)
        self.memory["person"] = person

        local_memory = dict()

        def _birthday_callback(sender, data):
            max_length = 2
            if sender == self.memory["year_uuid"]:
                max_length = 4

            # Verify if callback not called twice
            if sender not in local_memory:
                local_memory[sender] = False

            set_data = None

            if not local_memory[sender]:
                unauthorized_chars = [s for s in [".", "+", "-", "*", "/"] if s in data]
                if unauthorized_chars:
                    set_data = "".join([s for s in data if s.isdigit()])
                if len(data) == 2:
                    if sender == self.memory["day_uuid"]:
                        dpg.focus_item(self.memory["month_uuid"])
                    elif sender == self.memory["month_uuid"]:
                        dpg.focus_item(self.memory["year_uuid"])
            else:
                local_memory[sender] = False

            if isinstance(set_data, str):
                local_memory[sender] = True
                dpg.set_value(self.memory["day_uuid"], set_data)

        if person:
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_button(
                    label="Retour nouvelle personne", callback=lambda: self.build_loan_info_widget()
                )
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("                  Nom:")
                dpg.add_text(person.surname, tag=self.memory["name_uuid"])
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("              Prénom:")
                dpg.add_text(person.name, tag=self.memory["surname_uuid"])
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("Date de naissance:")
                dpg.add_text(person.birthday.strftime("%d/%m/%Y"))
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("  Unité / Chambre:")
                dpg.add_text(person.place, tag=self.memory["place_uuid"])
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("          Remarque:")
                dpg.add_text(person.note, tag=self.memory["note_uuid"])
        else:
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_button(label="Déjà existant ?")

            with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left) as popup:
                self.table_person(self.manager.persons, popup)
                self.memory["person_popup"] = popup

            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("                  Nom:")
                dpg.add_input_text(width=200, tag=self.memory["name_uuid"])
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("              Prénom:")
                dpg.add_input_text(width=200, tag=self.memory["surname_uuid"])
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("Date de naissance:")
                dpg.add_input_text(
                    decimal=True,
                    no_spaces=True,
                    width=30,
                    tag=self.memory["day_uuid"],
                    callback=_birthday_callback,
                    hint="Jour",
                )
                dpg.add_text("/")
                dpg.add_input_text(
                    decimal=True,
                    no_spaces=True,
                    width=30,
                    tag=self.memory["month_uuid"],
                    callback=_birthday_callback,
                    hint="Mois",
                )
                dpg.add_text("/")
                dpg.add_input_text(
                    decimal=True,
                    no_spaces=True,
                    width=60,
                    tag=self.memory["year_uuid"],
                    callback=_birthday_callback,
                    hint="Année",
                )
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("  Unité / Chambre:")
                dpg.add_input_text(width=200, tag=self.memory["place_uuid"])
            with dpg.group(horizontal=True, parent=g_uuid):
                dpg.add_text("          Remarque:")
                dpg.add_input_text(
                    width=200,
                    height=50,
                    multiline=True,
                    tab_input=True,
                    tag=self.memory["note_uuid"],
                )

    def main_window(self, parent) -> None:
        self.parent = parent
        title("Faire un nouveau prêt", parent)

        subtitle("Informations sur le patient", parent)
        self.memory["loan_info_uuid"] = dpg.generate_uuid()
        with dpg.group(parent=parent, tag=self.memory["loan_info_uuid"]):
            pass
        self.build_loan_info_widget()

        subtitle("Objet(s)", parent)

        new_obj_uuid = dpg.generate_uuid()
        with dpg.group(parent=parent, tag=new_obj_uuid):
            self.new_object(new_obj_uuid)
        dpg.add_button(label="+", parent=parent, callback=lambda: self.new_object(new_obj_uuid))

        g_uuid = dpg.generate_uuid()
        with dpg.group(tag=g_uuid, parent=parent):
            pass
        # self.table_person(self.manager.persons, g_uuid)
