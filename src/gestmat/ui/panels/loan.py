from datetime import datetime
import dearpygui.dearpygui as dpg

from ...item.workspace import Workspace
from ...util import ProtectedDatetime
from ...item.representation import ItemCategory, Item
from ...item.manager import ItemManager, Person
from ..panel import Panel
from ..widgets import DateWidget, error, item_info_box, modal, title, subtitle, help

workspace = Workspace()


class LoanPanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)
        self.memory = dict(objects=dict(), loan_date=datetime.today(), chosen_items=set())

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

        self.memory["chosen_items"].add(item)

        with dpg.group(parent=tag, horizontal=True) as g_uid:

            def _remove_item():
                self.memory["chosen_items"].remove(item)
                dpg.delete_item(tag, children_only=True)

            dpg.add_button(label="Enlever", callback=lambda *args: _remove_item())
            subtitle(cat.description, g_uid)
            if self.manager.is_item_loaned(item):
                dpg.add_text(" (déjà emprunté ")
                help(
                    "L'objet déjà emprunté va être rendu, puis réemprunté avec la nouvelle personne.",
                    g_uid,
                )
                dpg.add_text(" )")
            dpg.add_text(" (infos)", color=(125, 125, 125))
            with dpg.tooltip(dpg.last_item()) as tooltip_uid:
                item_info_box(item, tooltip_uid)

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
            item
            for item in cat.registered_items
            if not self.manager.is_item_loaned(item) or all_items
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
                    if item in self.memory["chosen_items"]:
                        continue
                    with dpg.table_row():
                        dpg.add_button(
                            label="Choisir",
                            callback=lambda *args, item=item: self.choose_item(obj_num, item),
                        )
                        if all_items:
                            if self.manager.is_item_loaned(item):
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
            name_uuid=dpg.generate_uuid(),
            surname_uuid=dpg.generate_uuid(),
            place_uuid=dpg.generate_uuid(),
            note_uuid=dpg.generate_uuid(),
        )
        dpg.delete_item(self.memory["loan_info_uuid"], children_only=True)
        self.memory["person"] = person

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
            with dpg.group(horizontal=True, parent=g_uuid) as birthday_uuid:
                dpg.add_text("Date de naissance:")
                date = DateWidget(birthday_uuid)
                self.memory["birthday"] = date
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

    def reset(self):
        dpg.configure_item(self.memory["save_modal"], show=False)
        self.memory = dict(objects=dict(), loan_date=datetime.today(), chosen_items=set())
        dpg.delete_item(self.parent, children_only=True)
        self.main_window(self.parent)

    def save_loan(self):
        tag = self.memory["save_modal"]
        dpg.configure_item(tag, show=False)
        dpg.delete_item(tag, children_only=True)
        loan_date = ProtectedDatetime(self.memory["loan_date_widget"].get_date())

        person = self.memory["person"]
        if not person:
            name = dpg.get_value(self.memory["name_uuid"])
            surname = dpg.get_value(self.memory["surname_uuid"])
            place = dpg.get_value(self.memory["place_uuid"])
            birthday = ProtectedDatetime(self.memory["birthday"].get_date())
            note = dpg.get_value(self.memory["note_uuid"])

            person = Person(name, surname, birthday, place, note)
            if not name and not surname and not place and not birthday and not note:
                person = self.manager.empty_person

        items = list(self.memory["chosen_items"])
        if not items:
            modal("Veuillez choisir au minimum un objet à emprunter")

        borrowed_items = []
        for item in items:
            borrowed_items.append(item)

        def _save():
            dpg.delete_item(tag, children_only=True)
            dpg.add_text(
                "L'emprunt a bien été enregistré. Vous le trouverez listé dans l'onglet 'État'",
                parent=tag,
            )
            dpg.add_button(label="Ok", parent=tag, callback=lambda *args: self.reset())
            for item in items:
                if item in self.manager.loans:
                    if self.manager.loans[item]:
                        self.manager.give_back(item, loan_date)
                self.manager.create_loan(item, loan_date, person)

            # Save the state of the loans
            workspace.save()

        if not person.birthday.date:
            dpg.add_text(
                "Vous êtes sur le point de faire un emprunt sans indiquer une date\n"
                "de naissance valide. Voulez-vous continuer ?",
                parent=tag,
            )
            with dpg.group(horizontal=True, parent=tag):
                dpg.add_button(label="Oui", callback=lambda *args: _save())
                dpg.add_button(
                    label="Non", callback=lambda *args: dpg.configure_item(tag, show=False)
                )
        else:
            _save()

        # if borrowed_items:
        #     if len(borrowed_items) == 1:
        #         dpg.add_text(
        #             "Un objet sélectionné est déjà en emprunt.\n",
        #             parent=tag,
        #         )
        #     else:
        #         dpg.add_text(
        #             "Les objets suivant sont déjà en emprunt.\nVeuillez indiquer pour chaque objet ce qu'il faut faire:",
        #             parent=tag,
        #         )
        #     for item in borrowed_items:
        #         pass

        dpg.configure_item(tag, show=True)
        popup_width = dpg.get_item_width(tag)
        popup_height = dpg.get_item_height(tag)
        window_width = dpg.get_item_width("primary_window")
        window_height = dpg.get_item_height("primary_window")
        if popup_width < window_width and popup_height < window_height:
            dpg.set_item_pos(
                tag, [(window_width - popup_width) / 2, (window_height - popup_height) / 2]
            )

    def main_window(self, parent) -> None:
        self.parent = parent
        with dpg.group(horizontal=True, parent=parent) as g_uid:
            title("Faire un nouveau prêt", g_uid)
            dpg.add_button(height=40, label="Sauvegarder", callback=self.save_loan)
            tag = dpg.generate_uuid()
            self.memory["save_modal"] = tag
            with dpg.popup(
                dpg.last_item(),
                tag=tag,
                mousebutton=dpg.mvMouseButton_X1,
                modal=True,
            ):
                pass

        subtitle("Informations sur la personne", parent)
        self.memory["loan_info_uuid"] = dpg.generate_uuid()
        with dpg.group(parent=parent, tag=self.memory["loan_info_uuid"]):
            pass
        self.build_loan_info_widget()

        with dpg.group(parent=parent, horizontal=True) as g_uid:
            subtitle("Date d'emprunt: ", g_uid)
            tag = dpg.generate_uuid()
            dpg.add_text(f"{self.memory['loan_date'].strftime('%d/%m/%Y')}  ", tag=tag)

            dpg.add_button(label="Changer")
            with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left) as popup:
                datewidget = DateWidget(popup, self.memory["loan_date"])
                self.memory["loan_date_widget"] = datewidget

                def _change_date():
                    date = datewidget.get_date()
                    if date:
                        dpg.set_value(tag, date.strftime("%d/%m/%Y"))
                        dpg.configure_item(popup, show=False)

                dpg.add_button(label="OK", callback=_change_date)

        subtitle("Objet(s)", parent)

        new_obj_uuid = dpg.generate_uuid()
        with dpg.group(parent=parent, tag=new_obj_uuid):
            self.new_object(new_obj_uuid)
        dpg.add_button(label="+", parent=parent, callback=lambda: self.new_object(new_obj_uuid))

        g_uuid = dpg.generate_uuid()
        with dpg.group(tag=g_uuid, parent=parent):
            pass
