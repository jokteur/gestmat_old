import dearpygui.dearpygui as dpg

from ..widgets import help, title
from ...item.manager import ItemManager
from ...util import strip_accents
from ..panel import Panel


class StatePanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)

    def main_window(self, parent) -> None:
        super().main_window(parent)

        title_uuid = dpg.generate_uuid()
        dpg.add_group(tag=title_uuid, horizontal=True, parent=parent)
        title("Matériel en emprunt", parent=title_uuid)

        help(
            "Tapez n'importe quel mot du tableau dans le champ de recherche pour trouver une ligne.\n"
            "Cliquez sur les en-tête de colonnes pour trier.",
            title_uuid,
        )

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

        if not self.manager.loans:
            dpg.add_text("Rien en emprunt")
            return

        _filter_table_id = dpg.generate_uuid()
        dpg.add_input_text(
            label="Rechercher",
            user_data=_filter_table_id,
            callback=lambda s, a, u: dpg.set_value(u, strip_accents(dpg.get_value(s))),
            parent=parent,
        )

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
            sortable=True,
            callback=_sort_callback,
            policy=dpg.mvTable_SizingStretchProp,
            tag=_filter_table_id,
        ) as table_id:
            # self.items.append("loan_table")
            dpg.add_table_column(label="Type")
            dpg.add_table_column(label="N°", width=50)
            dpg.add_table_column(label="Date d'emprunt")
            dpg.add_table_column(label="Nom")
            dpg.add_table_column(label="Prénom")
            dpg.add_table_column(label="Date de naissance")
            dpg.add_table_column(label="Unité / Chambre")
            dpg.add_table_column(label="Remarque")

            for item, loans in self.manager.loans.items():
                for loan in loans:
                    strings = {
                        item.category.description: dict(),
                        item.id.value: dict(),
                        loan.date.strftime("%Y/%m/%d"): dict(),
                        loan.person.surname: dict(),
                        loan.person.name: dict(),
                        loan.person.birthday.strftime("%Y/%m/%d"): dict(),
                        loan.person.place: dict(),
                        loan.note: dict(wrap=0),
                    }
                    strs = [strip_accents(string) for string in strings.keys()]
                    with dpg.table_row(filter_key=" ".join(strs)):
                        for text, prop in strings.items():
                            dpg.add_text(text, **prop)
