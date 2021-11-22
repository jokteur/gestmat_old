from typing import Any
import copy
import time

import dearpygui.dearpygui as dpg

from matgest.item.representation import Item, ItemCategory

from ...item.manager import ItemManager
from ..panel import Panel
from ..widgets import colored_button, error, modal, subtitle, title, help, ressources


def factory(fct, *args, **kwargs):
    def new_func():
        return fct(*args, **kwargs)

    return new_func


class ManagementPanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)

        self.clean_memory_dict = {
            "desc": "",
            "name": "",
            "props": set(),
            "clean_memory": False,
        }
        self.memory = {"table_cells": dict(), "editing_status": dict()}
        self.short_memory = copy.deepcopy(self.clean_memory_dict)

    def load_subpanel(self, name, no_back_button, *args):
        dpg.delete_item(self.parent, children_only=True)
        if not no_back_button:
            dpg.add_button(label="Retour", callback=self.build_main_window, parent=self.parent)
        self.__getattribute__(f"sub_{name}")(*args)

    def clean_memory(self):
        self.short_memory = copy.deepcopy(self.clean_memory_dict)

    def sub_category(self, cat):
        desc_tag = dpg.generate_uuid()
        name_tag = dpg.generate_uuid()

        self.short_memory["ok"] = True

        if cat:
            self.short_memory["desc"] = cat.description
            self.short_memory["name"] = cat.name
            self.short_memory["props"] = set(cat.properties)
            self.short_memory["clean_memory"] = True

        def set_desc(s, a, u):
            self.short_memory["desc"] = a

            names = [n.description.lower() for n in self.manager.categories.values()]
            if cat and a.lower() == cat.description.lower():
                names.remove(a.lower())
            if a.lower() in names:
                dpg.set_item_label(
                    desc_tag, "Nom du type d'objet (existe déjà, merci d'en choisir un autre)"
                )
                self.short_memory["ok"] = False
            else:
                self.short_memory["ok"] = True
                dpg.set_item_label(desc_tag, "Nom du type d'objet")

        def set_name(s, a, u):
            self.short_memory["name"] = a

            names = [n.lower() for n in self.manager.categories.keys()]

            if cat and a.lower() == cat.name.lower():
                names.remove(a.lower())
            if a.lower() in names:
                self.short_memory["ok"] = False
                dpg.set_item_label(name_tag, "Nom court (existe déjà, merci d'en choisir un autre)")
            else:
                self.short_memory["ok"] = True
                dpg.set_item_label(name_tag, "Nom court")

        def set_prop(s, a, u):
            if a:
                self.short_memory["props"].add(u)
            else:
                self.short_memory["props"].remove(u)

        uuid = dpg.generate_uuid()
        if cat:
            title(f"Éditer la catégorie '{cat.name}'", parent=self.parent)
        else:
            title("Ajouter une nouvelle catégorie / type d'objet", parent=self.parent)
        with dpg.group(tag=uuid, parent=self.parent):
            dpg.add_input_text(
                label="Nom du type d'objet",
                default_value=self.short_memory["desc"],
                tag=desc_tag,
                width=250,
                callback=set_desc,
            )
            dpg.add_input_text(
                label="Nom court",
                tag=name_tag,
                width=250,
                default_value=self.short_memory["name"],
                callback=set_name,
            )
            local_uuid = dpg.generate_uuid()
            with dpg.group(tag=local_uuid, horizontal=True):
                subtitle("Avec les propriétés", parent=local_uuid)
                dpg.add_button(
                    label="Gérer les propriétés",
                    callback=factory(
                        self.load_subpanel,
                        "property_management",
                        True,
                        cat,
                    ),
                )
            for prop in self.manager.properties.keys():
                name = prop.name
                properties = []
                if prop.mandatory:
                    properties.append("ne peut pas être vide")
                if prop.select:
                    properties.append("liste à choix")
                if properties:
                    name += f" ({', '.join(properties)})"
                dpg.add_checkbox(
                    label=name,
                    user_data=prop,
                    callback=set_prop,
                    default_value=(True if prop in self.short_memory["props"] else False),
                )

            def _save():
                desc = dpg.get_value(desc_tag)
                name = dpg.get_value(name_tag)
                props = self.short_memory["props"]

                if not desc:
                    return
                if not name:
                    return
                if not props:
                    return
                if not self.short_memory["ok"]:
                    return

                props_in_order = []
                for prop in self.manager.properties.keys():
                    if prop in props:
                        props_in_order.append(prop)

                old_name = cat.name
                cat.name = name
                cat.description = desc
                self.manager.update_properties(cat, props_in_order)
                self.manager.update_category_key(cat, old_name)
                self.build_main_window()
                self.clean_memory()

            def _new():
                desc = dpg.get_value(desc_tag)
                name = dpg.get_value(name_tag)
                props = self.short_memory["props"]

                props_in_order = []
                for prop in self.manager.properties.keys():
                    if prop in props:
                        props_in_order.append(prop)

                if not desc:
                    return
                if not name:
                    return
                if not props:
                    return
                if not self.short_memory["ok"]:
                    return

                self.manager.add_category(name, desc, props_in_order)
                self.build_main_window()
                self.clean_memory()

            if cat:
                dpg.add_button(label="Enregistrer", callback=_save)
            else:
                dpg.add_button(label="Ajouter catégorie", callback=_new)

    def prop_popup(self, parent, cat, prop=False):
        popup_uuid = dpg.generate_uuid()

        prop_name = ""
        prop_mandatory = False
        prop_select = []
        if prop:
            prop_name = prop.name
            prop_mandatory = prop.mandatory
            prop_select = prop.select
        with dpg.popup(
            parent,
            mousebutton=dpg.mvMouseButton_Left,
            modal=True,
            tag=popup_uuid,
        ):
            name_uuid = dpg.generate_uuid()
            save_uuid = dpg.generate_uuid()
            list_uuid = dpg.generate_uuid()
            type_uuid = dpg.generate_uuid()
            radio_uuid = dpg.generate_uuid()

            current_list_input_uuid = dpg.generate_uuid()

            def verify(s, a, u):
                names = set([n.name for n in self.manager.properties.keys()])
                if prop:
                    names.remove(prop_name)
                if a in names:
                    dpg.set_item_label(name_uuid, "Nom (déjà existant)")
                    dpg.set_item_label(save_uuid, "")
                elif not a:
                    dpg.set_item_label(name_uuid, "Nom (ne peut pas être vide)")
                    dpg.set_item_label(save_uuid, "")
                else:
                    dpg.set_item_label(name_uuid, "Nom")
                    dpg.set_item_label(save_uuid, "Enregistrer")

            def list_edit(s, a, u):
                nonlocal current_list_input_uuid
                if a == "libre":
                    dpg.delete_item(type_uuid, children_only=True)
                else:
                    current_list_input_uuid = dpg.generate_uuid()
                    dpg.add_text("Choix :", parent=type_uuid)
                    help("Séparez les éléments de la liste avec des ;;", parent=type_uuid)
                    dpg.add_input_text(
                        tag=current_list_input_uuid, default_value=u, parent=type_uuid
                    )

            dpg.add_input_text(label="Nom", default_value=prop_name, tag=name_uuid, callback=verify)
            local_uuid = dpg.generate_uuid()
            with dpg.group(horizontal=True, tag=local_uuid):
                dpg.add_text("Obligatoire ?")
                help(
                    "Si la propriété est obligatoire, alors ce champ devra être obligatoirement rempli\n"
                    "lors de l'insertion d'un nouvel objet",
                    parent=local_uuid,
                )
            dpg.add_radio_button(
                ["oui", "non"],
                horizontal=True,
                tag=radio_uuid,
                default_value=("oui" if prop_mandatory else "non"),
            )
            with dpg.group(horizontal=True):
                dpg.add_text("Type:")
                dpg.add_combo(
                    ["libre", "liste à choix"],
                    tag=list_uuid,
                    width=150,
                    default_value=("liste à choix" if prop_select else "libre"),
                    user_data=" ;; ".join(prop_select),
                    callback=list_edit,
                )
            with dpg.group(tag=type_uuid, horizontal=True):
                pass
            if prop_select:
                list_edit(None, "liste à choix", " ;; ".join(prop_select))

            def _edit():
                name = dpg.get_value(name_uuid)
                radio = dpg.get_value(radio_uuid)
                list_choice = dpg.get_value(list_uuid)
                choices = []
                if not name:
                    return
                if list_choice == "liste à choix":
                    choices = dpg.get_value(current_list_input_uuid)
                    choices = [choice.strip() for choice in choices.split(";;")]
                    if not choices:
                        return
                prop.name = name
                prop.select = choices
                radio = True if radio == "oui" else False
                prop.mandatory = radio
                dpg.configure_item(popup_uuid, show=False)
                self.load_subpanel("property_management", True, cat)

            def _new():
                name = dpg.get_value(name_uuid)
                radio = dpg.get_value(radio_uuid)
                mandatory = True if radio == "oui" else False
                list_choice = dpg.get_value(list_uuid)
                choices = []
                if not name:
                    return
                if list_choice == "liste à choix":
                    choices = dpg.get_value(current_list_input_uuid)
                    choices = [choice.strip() for choice in choices.split(";;")]
                    if not choices:
                        return

                prop = self.manager.create_property(name, str, mandatory=mandatory, select=choices)
                dpg.configure_item(popup_uuid, show=False)
                self.load_subpanel("property_management", True, cat)

            _save_edit = _edit if prop else _new

            with dpg.group(horizontal=True):
                dpg.add_button(label="Enregistrer", tag=save_uuid, callback=_save_edit)
                dpg.add_button(
                    label="Annuler", callback=lambda: dpg.configure_item(popup_uuid, show=False)
                )

    def edit_prop(self, prop, cat):
        g_uuid = dpg.generate_uuid()
        with dpg.group(tag=g_uuid, horizontal=True):
            name = prop.name
            properties = []
            if prop.mandatory:
                properties.append("ne peut pas être vide")
            if prop.select:
                properties.append("liste à choix")
            if prop.no_edit:
                properties.append("non éditable")
            if properties:
                name += f" ({', '.join(properties)})"

            dpg.add_text(name)
            if not prop.no_edit:
                tag = dpg.generate_uuid()
                dpg.add_button(label="Éditer", tag=tag)
                self.prop_popup(tag, cat, prop)

    def sub_property_management(self, cat):
        uuid = dpg.generate_uuid()
        print(cat)
        with dpg.group(tag=uuid, parent=self.parent):
            dpg.add_button(
                label="Retour", callback=factory(self.load_subpanel, "category", False, cat)
            )

            g_uuid = dpg.generate_uuid()
            with dpg.group(tag=g_uuid, horizontal=True):
                title("Propriétés existantes", parent=g_uuid)

                tag = dpg.generate_uuid()
                dpg.add_button(label="Nouvelle propriété", tag=tag)
                self.prop_popup(tag, cat)

            for prop in self.manager.properties.keys():
                self.edit_prop(prop, cat)

    def build_main_window(self):
        dpg.delete_item(self.parent, children_only=True)

        if self.short_memory["clean_memory"]:
            self.clean_memory()

        self.main_window(self.parent)

    def table(self, cat: ItemCategory, items: list[Item], table_id, parent):
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
                # print(row)
                cell = dpg.get_item_children(row, 1)[headers[sort_specs[0][0]]]
                cell = dpg.get_item_children(cell, 1)[0]
                sortable_list.append([row, dpg.get_value(cell)])

            def _sorter(e):
                return e[1]

            sortable_list.sort(key=_sorter, reverse=sort_specs[0][1] < 0)

            # create list of just sorted row ids
            new_order = []
            for pair in sortable_list:
                new_order.append(pair[0])

            dpg.reorder_items(sender, 1, new_order)

        select_tag = dpg.generate_uuid()

        def _select_all(*args):
            nonlocal cat
            if dpg.get_value(select_tag):
                dpg.set_item_label(select_tag, "Désélectionner tout")
                for item in cat.registered_items:
                    dpg.set_value(self.memory["table_cells"][item]["checkbox"], True)
            else:
                dpg.set_item_label(select_tag, "Sélectionner tout")
                for item in cat.registered_items:
                    dpg.set_value(self.memory["table_cells"][item]["checkbox"], False)

        dpg.add_checkbox(
            label="Sélectionner tout", parent=parent, callback=_select_all, tag=select_tag
        )

        items = list(items)
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
            tag=table_id,
        ) as table_id:
            props = list(cat.properties_order)
            dpg.add_table_column(label="", no_sort=True, width=10, width_fixed=True, no_resize=True)

            for prop in props:
                addamentum = "*" if prop.mandatory else ""
                dpg.add_table_column(label=f"{prop.name}{addamentum}")

            for i, item in enumerate(items):
                self.add_row(cat, item, props)

    def add_row(self, cat: ItemCategory, item: Item, props, default_value=False, is_new=False):
        row_id = dpg.generate_uuid()
        with dpg.table_row(parent=self.memory["table_cells"][cat]["table_id"], tag=row_id):
            checkbox_uuid = dpg.generate_uuid()
            dpg.add_checkbox(label="", tag=checkbox_uuid, default_value=default_value)
            if not item in self.memory["table_cells"]:
                self.memory["table_cells"][item] = {}
            self.memory["table_cells"][item]["row_id"] = row_id
            self.memory["table_cells"][item]["checkbox"] = checkbox_uuid
            self.memory["table_cells"][item]["is_new"] = is_new

            for prop in props:
                if not prop in item.properties:
                    item.add_property(prop)
                txt = item.properties[prop].value
                with dpg.group():
                    tag = dpg.last_item()
                    dpg.add_text(txt)

                self.memory["table_cells"][item][prop] = tag

    def remove_row(self, cat: ItemCategory, item: Item):
        dpg.delete_item(self.memory["table_cells"][item]["row_id"])
        dpg.configure_item(
            self.memory["table_cells"][cat]["window_id"],
            height=self.generate_height(len(cat.registered_items) + 1),
        )

    def edit_callback_factory(self, cat: ItemCategory, items: list[Item]):
        return lambda *args, cat=cat, items=items: self.edit_all(cat, items)

    def reset_edit_button(self, cat: ItemCategory, items: list[Item]):
        g_uuid = self.memory["table_cells"][cat]["group_id"]
        dpg.delete_item(g_uuid, children_only=True)
        dpg.add_button(
            label="Éditer",
            parent=g_uuid,
            callback=self.edit_callback_factory(cat, items),
        )
        self.memory["table_cells"][cat]["is_editing"] = False

    def save_all(self, cat: ItemCategory, items: list[Item], new_item=False) -> None:
        is_okay = True
        for item in items:
            if item not in self.memory["editing_status"]:
                continue
            for prop in item.properties:
                tag = self.memory["table_cells"][item][prop]
                child = dpg.get_item_children(tag, 1)[0]
                value = dpg.get_value(child)

                if not value and prop.mandatory:
                    is_okay = False
                else:
                    dpg.delete_item(tag, children_only=True)
                    dpg.add_text(value, parent=tag)
                    item.properties[prop].value = value
        if is_okay:
            self.reset_edit_button(cat, items)
            self.memory["table_cells"][item]["is_new"] = False
            # dpg.configure_item(self.memory["table_cells"][cat])
        else:
            modal(
                "Certaines propriétés n'ont pas pu être sauvegardées\n"
                "car elles ne peuvent pas être vide (colonnes indiquées par *)"
            )
        # else:

        return

    def edit_all(self, cat: ItemCategory, items: list[Item], new_item=False) -> None:
        g_uuid = self.memory["table_cells"][cat]["group_id"]

        def cancel():
            for item in items:
                if item not in self.memory["editing_status"]:
                    continue
                for prop in item.properties:
                    tag = self.memory["table_cells"][item][prop]
                    dpg.delete_item(tag, children_only=True)
                    dpg.add_text(item.properties[prop].value, parent=tag)
                if self.memory["table_cells"][item]["is_new"]:
                    self.manager.delete_item(item)
                    self.remove_row(cat, item)
            self.reset_edit_button(cat, items)

        num_select = 0
        for item in items:
            if not dpg.get_value(self.memory["table_cells"][item]["checkbox"]):
                self.memory["editing_status"][item] = False
                continue

            self.memory["editing_status"][item] = True
            num_select += 1
            for prop in item.properties:
                tag = self.memory["table_cells"][item][prop]
                dpg.delete_item(tag, children_only=True)
                if prop.select:
                    dpg.add_combo(prop.select, parent=tag, label="", default_value=item.properties[prop].value, width=-1)
                else:
                    dpg.add_input_text(
                        parent=tag,
                        label="",
                        default_value=item.properties[prop].value,
                        width=-1,
                    )

        # Nothing has been selected
        if not num_select:
            return

        self.memory["table_cells"][cat]["is_editing"] = True
        items = list(items)

        # Update the Edit button group
        save_uuid = dpg.generate_uuid()
        self.memory["table_cells"][cat]["save_button"] = save_uuid
        dpg.delete_item(g_uuid, children_only=True)
        dpg.add_button(
            label="Sauvegarder",
            callback=lambda *args, cat=cat, items=items: self.save_all(cat, items, new_item),
            parent=g_uuid,
            tag=save_uuid,
        )
        dpg.add_button(label="Annuler", callback=cancel, parent=g_uuid)

    def add_item(self, cat: ItemCategory) -> None:
        items = cat.registered_items

        dic = self.memory["table_cells"]
        dpg.configure_item(
            dic[cat]["window_id"],
            height=self.generate_height(len(items) + 1),
        )
        for item in items:
            if not self.memory["table_cells"][item]["is_new"]:
                dpg.set_value(dic[item]["checkbox"], False)

        props = cat.properties_order
        new_item = Item(cat, __empty__=True)
        dic[new_item] = {}

        self.add_row(cat, new_item, props, True, True)

        self.manager.add_item(new_item)

        self.edit_all(cat, cat.registered_items, True)

    def generate_height(self, num):
        return 30 * (num + 3)

    def main_window(self, parent) -> None:
        self.manager.categories
        self.parent = parent

        title("Gestion des objets", parent)

        dpg.add_button(
            label="Nouvelle catégorie",
            parent=parent,
            callback=factory(self.load_subpanel, "category", False, False),
        )

        for key, cat in self.manager.categories.items():
            with dpg.group(parent=parent):
                group_tag = dpg.generate_uuid()
                with dpg.group(tag=group_tag, horizontal=True):
                    subtitle(cat.description, parent=group_tag)
                    colored_button(
                        "Éditer catégorie",
                        group_tag,
                        0.1,
                        factory(self.load_subpanel, "category", False, cat),
                    )

                header_uuid = dpg.generate_uuid()
                with dpg.collapsing_header(label="Ouvrir liste", tag=header_uuid):
                    items = cat.registered_items
                    button_uuid = dpg.generate_uuid()
                    g_uuid = dpg.generate_uuid()
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Ajouter objet",
                            tag=button_uuid,
                            callback=lambda *args, cat=cat: self.add_item(cat),
                        )
                        with dpg.group(horizontal=True, tag=g_uuid):
                            if items:
                                dpg.add_button(
                                    label="Éditer",
                                    callback=self.edit_callback_factory(cat, items),
                                )

                    uuid = dpg.generate_uuid()
                    table_uuid = dpg.generate_uuid()
                    self.memory["table_cells"][cat] = {
                        "is_editing": False,
                        "window_id": uuid,
                        "table_id": table_uuid,
                        "group_id": g_uuid,
                    }
                    # approx_height = dpg.get_item_height(header_uuid)
                    # hard-coded value, approx_height does not work
                    with dpg.child_window(height=self.generate_height(len(items)), tag=uuid):
                        self.table(cat, items, table_uuid, uuid)
