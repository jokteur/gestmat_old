from datetime import datetime

import dearpygui.dearpygui as dpg

from ...ui.panels.management import ManagementPanel

from ...item.workspace import Workspace
from ..widgets import help, item_info_box, subtitle, title, DateWidget, prepare_modal
from ...item.manager import ItemManager, Person
from ...util import strip_accents, factory, ProtectedDatetime
from ..panel import Panel


def factory(fct, *args, **kwargs):
    def new_func():
        return fct(*args, **kwargs)

    return new_func


workspace = Workspace()


class StatePanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)

        self.memory = dict()

    def load_subpanel(self, name, *args):
        dpg.delete_item(self.memory["view_uuid"], children_only=True)
        self.__getattribute__(f"sub_{name}")(*args)

        dpg.delete_item(self.memory["buttons_uuid"], children_only=True)

        if name == "table_view":
            dpg.add_button(
                label="Voir emprunts par personne",
                callback=lambda *args: self.load_subpanel("person_view"),
                parent=self.memory["buttons_uuid"],
            )
        else:
            dpg.add_button(
                label="Voir liste tous les emprunts",
                callback=lambda *args: self.load_subpanel("table_view"),
                parent=self.memory["buttons_uuid"],
            )

    def give_back(self):
        for loan, id in self.memory["checkbox"].items():
            if dpg.get_value(id):
                self.manager.give_back(loan, datetime.today())

        workspace.save()
        self.build_main_window()

    def build_main_window(self):
        dpg.delete_item(self.parent, children_only=True)

        self.memory = dict()

        self.main_window(self.parent)

    def sub_table_view(self):
        def _sort_callback(sender, sort_specs):

            # sort_specs scenarios:
            #   1. no sorting -> sort_specs == None
            #   2. single sorting -> sort_specs == [[column_id, direction]]
            #   3. multi sorting -> sort_specs == [[column_id, direction], [column_id, direction], ...]
            #
            # notes:
            #   1. direction is ascending if == 1
            #   2. direction is ascending if == -1

            # no sorting case
            if sort_specs is None:
                return

            headers = {num: i for i, num in enumerate(dpg.get_item_children(sender, 0))}

            rows = dpg.get_item_children(sender, 1)

            # create a list that can be sorted based on first cell
            # value, keeping track of row and value used to sort
            sortable_list = []
            for row in rows:
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

        parent = self.memory["view_uuid"]

        if not self.manager.loans:
            dpg.add_text("Rien en emprunt", parent=parent)
            return

        with dpg.group(parent=parent):
            dpg.add_button(
                label="Rendre les objets sélectionnés", callback=lambda *args: self.give_back()
            )

        with dpg.group(parent=parent, horizontal=True) as group:
            _filter_table_id = dpg.generate_uuid()
            dpg.add_input_text(
                label="Rechercher",
                user_data=_filter_table_id,
                callback=lambda s, a, u: dpg.set_value(u, strip_accents(dpg.get_value(s))),
            )
            help(
                "Tapez n'importe quel mot du tableau ou propriété dans le champ de recherche pour trouver une ligne.\n"
                "Cliquez sur les en-tête de colonnes pour trier.",
                group,
            )

        self.memory["checkbox"] = dict()

        with dpg.table(
            header_row=True,
            row_background=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True,
            scrollY=True,
            scrollX=True,
            delay_search=True,
            parent=parent,
            resizable=True,
            sortable=True,
            callback=_sort_callback,
            policy=dpg.mvTable_SizingStretchProp,
            tag=_filter_table_id,
        ) as table_id:
            # self.items.append("loan_table")
            dpg.add_table_column(label="", width=35, no_sort=True, width_fixed=True)
            dpg.add_table_column(label="Date d'emprunt")
            dpg.add_table_column(label="Type")
            # dpg.add_table_column(label="N°")
            dpg.add_table_column(label="Nom")
            dpg.add_table_column(label="Prénom")
            dpg.add_table_column(label="Date de naissance")
            dpg.add_table_column(label="Unité / Chambre")
            dpg.add_table_column(label="Remarque")

            for item, loans in self.manager.loans.items():
                for loan in loans:
                    prop_values = "".join(
                        [item._properties[prop].value for prop in item._properties]
                    )
                    strings = [
                        loan.date.strftime("%Y/%m/%d"),
                        item._category.description,
                        # item.n.value,
                        loan.person.surname,
                        loan.person.name,
                        loan.person.birthday.strftime("%Y/%m/%d"),
                        loan.person.place,
                        loan.person.note,
                        prop_values,
                    ]
                    strs = [strip_accents(string) for string in strings]
                    with dpg.table_row(filter_key=" ".join(strs)):
                        self.memory["checkbox"][loan] = dpg.generate_uuid()
                        dpg.add_checkbox(label="", tag=self.memory["checkbox"][loan])
                        dpg.add_text(strings[0])
                        with dpg.group(horizontal=True):
                            dpg.add_text("(infos)", color=(125, 125, 125))
                            with dpg.tooltip(dpg.last_item()) as tooltip_uid:
                                item_info_box(item, tooltip_uid)
                            dpg.add_text(strings[1])
                        dpg.add_text(strings[2])
                        dpg.add_text(strings[3])
                        dpg.add_text(strings[4])
                        dpg.add_text(strings[5])
                        dpg.add_text(strings[6])

    def edit_person(self, person: Person):
        name = person.name
        surname = person.surname
        birthday = person.birthday
        place = person.place
        note = person.note

        tag, configure_modal, stop_show = prepare_modal()
        name_uuid = dpg.generate_uuid()
        surname_uuid = dpg.generate_uuid()
        place_uuid = dpg.generate_uuid()
        note_uuid = dpg.generate_uuid()

        with dpg.group(horizontal=True, parent=tag):
            dpg.add_text("                  Nom:")
            dpg.add_input_text(width=200, tag=surname_uuid, default_value=surname)
        with dpg.group(horizontal=True, parent=tag):
            dpg.add_text("              Prénom:")
            dpg.add_input_text(width=200, tag=name_uuid, default_value=name)
        with dpg.group(horizontal=True, parent=tag) as birthday_uuid:
            dpg.add_text("Date de naissance:")
            date = DateWidget(tag, birthday)
        with dpg.group(horizontal=True, parent=tag):
            dpg.add_text("  Unité / Chambre:")
            dpg.add_input_text(width=200, tag=place_uuid, default_value=place)
        with dpg.group(horizontal=True, parent=tag):
            dpg.add_text("          Remarque:")
            dpg.add_input_text(
                width=200,
                height=50,
                multiline=True,
                tab_input=True,
                default_value=note,
                tag=note_uuid,
            )

        def _save():
            person.name = dpg.get_value(name_uuid)
            person.surname = dpg.get_value(surname_uuid)
            person.place = dpg.get_value(place_uuid)
            person.note = dpg.get_value(note_uuid)
            person.birthday = ProtectedDatetime(date.get_date())
            workspace.save()
            stop_show()
            self.load_subpanel("person_view")

        with dpg.group(horizontal=True, parent=tag):
            dpg.add_button(label="Enregistrer", callback=lambda s, u, d: _save())
            dpg.add_button(label="Annuler", callback=lambda s, u, d: stop_show())

        configure_modal()

    def sub_person_view(self):
        parent = self.memory["view_uuid"]

        persons = list(self.manager.persons)
        person_names = [person.surname for person in persons]
        sorted_list = [i[0] for i in sorted(enumerate(person_names), key=lambda x: x[1].lower())]

        for idx in sorted_list:
            with dpg.group(horizontal=True, parent=parent) as g_uid:
                dpg.add_button(label="Éditer", callback=factory(self.edit_person, persons[idx]))
                subtitle("Nom, Prénom:", parent=g_uid)
                surname = persons[idx].surname or "n/a"
                name = persons[idx].name or "n/a"
                if name == "n/a" and surname == "n/a":
                    name = ""
                dpg.add_text(f"{surname}, {name}")

                dpg.add_text(" (infos)", color=(125, 125, 125))
                with dpg.tooltip(dpg.last_item()) as tooltip_uid:
                    with dpg.group(parent=tooltip_uid, horizontal=True) as g:
                        subtitle("Date de naissance:", parent=g)
                        birthday = persons[idx].birthday
                        dpg.add_text(f"{birthday.strftime('%d/%m/%Y')}")
                    with dpg.group(parent=tooltip_uid, horizontal=True) as g:
                        subtitle("Unité - chambre:", parent=g)
                        place = persons[idx].place
                        dpg.add_text(f"{place}")
                    with dpg.group(parent=tooltip_uid, horizontal=True) as g:
                        subtitle("Remarque:", parent=g)
                        note = persons[idx].note
                        dpg.add_text(f"{note}")

    def main_window(self, parent) -> None:
        self.parent = parent

        title_uuid = dpg.generate_uuid()
        dpg.add_group(tag=title_uuid, horizontal=True, parent=parent)
        title("Matériel en emprunt", parent=title_uuid)

        self.memory["buttons_uuid"] = dpg.generate_uuid()
        with dpg.group(tag=self.memory["buttons_uuid"], parent=title_uuid, horizontal=True):
            dpg.add_button(
                label="Voir emprunts par personne",
                callback=lambda *args: self.load_subpanel("person_view"),
            )

        self.memory["view_uuid"] = dpg.generate_uuid()
        with dpg.group(tag=self.memory["view_uuid"], parent=parent):
            pass

        self.sub_table_view()
