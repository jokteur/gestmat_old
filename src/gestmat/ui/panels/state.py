from datetime import datetime

import dearpygui.dearpygui as dpg

from ...item.workspace import Workspace
from ..widgets import help, title
from ...item.manager import ItemManager
from ...util import strip_accents
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
                "Tapez n'importe quel mot du tableau dans le champ de recherche pour trouver une ligne.\n"
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
            dpg.add_table_column(label="N°", width=50)
            dpg.add_table_column(label="Nom")
            dpg.add_table_column(label="Prénom")
            dpg.add_table_column(label="Date de naissance")
            dpg.add_table_column(label="Unité / Chambre")
            dpg.add_table_column(label="Remarque")

            for item, loans in self.manager.loans.items():
                for loan in loans:
                    strings = {
                        loan.date.strftime("%Y/%m/%d"): dict(),
                        item.category.description: dict(),
                        item.id.value: dict(),
                        loan.person.surname: dict(),
                        loan.person.name: dict(),
                        loan.person.birthday.strftime("%Y/%m/%d"): dict(),
                        loan.person.place: dict(),
                        loan.person.note: dict(wrap=0),
                    }
                    strs = [strip_accents(string) for string in strings.keys()]
                    with dpg.table_row(filter_key=" ".join(strs)):
                        self.memory["checkbox"][loan] = dpg.generate_uuid()
                        dpg.add_checkbox(label="", tag=self.memory["checkbox"][loan])
                        for text, prop in strings.items():
                            dpg.add_text(text, **prop)

    def sub_person_view(self):
        pass

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
