from typing import Any
import copy
import time

import dearpygui.dearpygui as dpg

from ...item.workspace import Workspace

from ...item.representation import Item, ItemCategory, ItemProperty

from ...item.manager import ItemManager
from ..panel import Panel
from ..widgets import colored_button, error, modal, subtitle, title, help, ressources


def factory(fct, *args, **kwargs):
    def new_func():
        return fct(*args, **kwargs)

    return new_func


workspace = Workspace()


class ManagementPanel(Panel):
    def __init__(self, manager: ItemManager) -> None:
        super().__init__(manager)

        self.clean_memory_dict = {
            "desc": "",
            "name": "",
            "props": set(),
            "clean_memory": False,
        }
        self.memory = {"editing_status": dict()}
        self.cells = {}
        self.short_memory = copy.deepcopy(self.clean_memory_dict)

    def load_subpanel(self, name, no_back_button, *args):
        dpg.delete_item(self.parent, children_only=True)
        if not no_back_button:
            dpg.add_button(label="Retour", callback=self.build_main_window, parent=self.parent)
        self.__getattribute__(f"sub_{name}")(*args)

    def clean_memory(self):
        self.short_memory = copy.deepcopy(self.clean_memory_dict)
        # self.cells = {}

    def generate_prop_name(self, prop: ItemProperty):
        name = prop.name
        properties = []
        if prop.mandatory:
            properties.append("ne peut pas être vide")
        if prop.select:
            properties.append("liste à choix")
        if properties:
            name += f" ({', '.join(properties)})"
        return name

    def reload_chose_prop_popup(self):
        tag = self.short_memory["prop_popup_uuid"]

        def choose(s, u, d):
            self.short_memory["props"][d] = {}
            self.generate_props_widget()
            self.reload_chose_prop_popup()

        dpg.delete_item(tag, children_only=True)
        for prop, active in self.manager.properties.items():
            if active and prop not in self.short_memory["props"]:
                with dpg.group(horizontal=True, parent=tag):
                    dpg.add_button(label="Choisir", callback=choose, user_data=prop)
                    dpg.add_text(self.generate_prop_name(prop))

    def generate_props_widget(self):
        tag = self.short_memory["prop_uuid"]
        dpg.delete_item(tag, children_only=True)

        def remove(s, d, u):
            del self.short_memory["props"][u]
            self.reload_chose_prop_popup()
            self.generate_props_widget()

        def up(s, d, u):
            props = list(self.short_memory["props"].keys())
            props_config = list(self.short_memory["props"].values())
            prop_idx = props.index(u)
            props[prop_idx], props[prop_idx - 1] = props[prop_idx - 1], props[prop_idx]
            props_config[prop_idx], props_config[prop_idx - 1] = (
                props_config[prop_idx - 1],
                props_config[prop_idx],
            )
            self.short_memory["props"] = dict(zip(props, props_config))
            self.reload_chose_prop_popup()
            self.generate_props_widget()

        def down(s, d, u):
            props = list(self.short_memory["props"].keys())
            props_config = list(self.short_memory["props"].values())
            prop_idx = props.index(u)
            props[prop_idx], props[prop_idx + 1] = props[prop_idx + 1], props[prop_idx]
            props_config[prop_idx], props_config[prop_idx + 1] = (
                props_config[prop_idx + 1],
                props_config[prop_idx],
            )
            self.short_memory["props"] = dict(zip(props, props_config))
            self.reload_chose_prop_popup()
            self.generate_props_widget()

        if "props" not in self.short_memory or not self.short_memory["props"]:
            dpg.add_text("Veuillez sélectionner au moins une propriété", parent=tag)
            return

        for i, (prop, config) in enumerate(self.short_memory["props"].items()):
            name = self.generate_prop_name(prop)
            with dpg.group(parent=tag, horizontal=True):
                dpg.add_button(label="Enlever", callback=remove, user_data=prop)
                if i:
                    dpg.add_button(label="Haut", callback=up, user_data=prop)
                if i < len(self.short_memory["props"]) - 1:
                    dpg.add_button(label="Bas", callback=down, user_data=prop)
                dpg.add_text(name)

    def sub_category(self, cat: ItemCategory, no_reload=False):
        desc_tag = dpg.generate_uuid()
        name_tag = dpg.generate_uuid()

        self.short_memory["ok"] = True

        if cat and not no_reload:
            self.short_memory["desc"] = cat.description
            self.short_memory["name"] = cat.name
            self.short_memory["props"] = {prop: {} for prop in cat.properties_order}
            self.short_memory["clean_memory"] = True

        def _save():
            desc = dpg.get_value(desc_tag)
            name = dpg.get_value(name_tag)
            props = list(self.short_memory["props"].keys())

            if not desc:
                return
            if not name:
                return
            if not props:
                return
            if not self.short_memory["ok"]:
                return

            old_name = cat.name
            cat.name = name
            cat.description = desc
            self.manager.update_properties(cat, props)
            self.manager.update_category_key(cat, old_name)
            workspace.save()
            self.build_main_window()
            self.clean_memory()

        def _new():
            desc = dpg.get_value(desc_tag)
            name = dpg.get_value(name_tag)
            props = list(self.short_memory["props"].keys())

            if not desc:
                return
            if not name:
                return
            if not props:
                return
            if not self.short_memory["ok"]:
                return

            self.manager.add_category(name, desc, props)
            self.build_main_window()
            self.clean_memory()

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

        uuid = dpg.generate_uuid()
        with dpg.group(horizontal=True, parent=self.parent) as uid:
            if cat:
                title(f"Éditer la catégorie '{cat.name}'", uid)
                dpg.add_button(label="Enregistrer", callback=_save, height=40)
            else:
                title("Ajouter une nouvelle catégorie / type d'objet", uid)
                dpg.add_button(label="Ajouter catégorie", callback=_new, height=40)

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
            with dpg.group(horizontal=True) as g_uid:
                subtitle("Avec les propriétés", parent=g_uid)
                dpg.add_button(
                    label="Gérer les propriétés",
                    callback=factory(self.load_subpanel, "property_management", True, cat, True),
                )
            self.short_memory["prop_uuid"] = dpg.generate_uuid()
            with dpg.group(tag=self.short_memory["prop_uuid"]):
                pass

            self.generate_props_widget()
            dpg.add_button(label="+")
            self.short_memory["prop_popup_uuid"] = dpg.generate_uuid()
            with dpg.popup(
                dpg.last_item(),
                mousebutton=dpg.mvMouseButton_Left,
                tag=self.short_memory["prop_popup_uuid"],
            ):
                pass
            self.reload_chose_prop_popup()

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

                workspace.save()
                self.load_subpanel("property_management", True, cat, True)

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

                workspace.save()
                self.load_subpanel("property_management", True, cat, True)

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

    def sub_property_management(self, cat, reload):
        uuid = dpg.generate_uuid()
        with dpg.group(tag=uuid, parent=self.parent):
            dpg.add_button(
                label="Retour", callback=factory(self.load_subpanel, "category", False, cat, reload)
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
                    dpg.set_value(self.cells[cat]["items"][item]["checkbox"], True)
            else:
                dpg.set_item_label(select_tag, "Sélectionner tout")
                for item in cat.registered_items:
                    dpg.set_value(self.cells[cat]["items"][item]["checkbox"], False)

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
        with dpg.table_row(parent=self.cells[cat]["table_id"], tag=row_id):
            checkbox_uuid = dpg.generate_uuid()
            dpg.add_checkbox(label="", tag=checkbox_uuid, default_value=default_value)
            if not item in self.cells[cat]["items"]:
                self.cells[cat]["items"][item] = {}
            self.cells[cat]["items"][item]["row_id"] = row_id
            self.cells[cat]["items"][item]["checkbox"] = checkbox_uuid
            self.cells[cat]["items"][item]["is_new"] = is_new

            for prop in list(cat.properties_order):
                if not prop in item.properties:
                    item.add_property(prop)
                txt = item.properties[prop].value
                with dpg.group():
                    tag = dpg.last_item()
                    dpg.add_text(txt)
                    tag2 = dpg.last_item()
                    self.cells[cat]["items"][item][prop] = [tag, tag2]

    def remove_row(self, cat: ItemCategory, item: Item):
        dpg.delete_item(self.cells[cat]["items"][item]["row_id"])
        self.set_table_height(cat)

    def edit_callback_factory(self, cat: ItemCategory, items: list[Item]):
        return lambda *args, cat=cat, items=items: self.edit_all(cat)

    def delete_items_in_cat(self, cat: ItemCategory):
        to_remove = []
        for item in self.cells[cat]["items"].keys():
            if not dpg.get_value(self.cells[cat]["items"][item]["checkbox"]):
                continue

            to_remove.append(item)
            self.manager.retire_item(item)
            cat.unregister_item(item)
            self.remove_row(item.category, item)

        for item in to_remove:
            del self.cells[cat]["items"][item]

        workspace.save()

    def reset_edit_button(self, cat: ItemCategory, items: list[Item]):
        g_uuid = self.cells[cat]["group_id"]
        dpg.delete_item(g_uuid, children_only=True)
        dpg.add_button(
            label="Éditer",
            parent=g_uuid,
            callback=self.edit_callback_factory(cat, items),
        )
        colored_button("Supprimer", g_uuid, 0, lambda *args, cat=cat: self.delete_items_in_cat(cat))
        self.cells[cat]["is_editing"] = False

    def save_all(self, cat: ItemCategory, new_item=False) -> None:
        is_okay = True
        items = self.cells[cat]["items"]
        for item in items:
            if item not in self.memory["editing_status"]:
                continue

            tmp_ = True
            for prop in item.properties:
                tag = self.cells[cat]["items"][item][prop]
                value = dpg.get_value(dpg.get_item_children(tag[0], 1)[0])

                if not value and prop.mandatory:
                    is_okay = False
                    tmp_ = False
                else:
                    dpg.delete_item(tag[0], children_only=True)
                    dpg.add_text(value, parent=tag[0])
                    item.properties[prop].value = value

            if tmp_ and self.cells[cat]["items"][item]["is_new"]:
                self.manager.add_item(item)
                dpg.set_value(self.cells[cat]["items"][item]["checkbox"], False)
                self.cells[cat]["items"][item]["is_new"] = False
                cat.register_item(item)

        if is_okay:
            self.reset_edit_button(cat, items)
        else:
            modal(
                "Certaines propriétés n'ont pas pu être sauvegardées\n"
                "car elles ne peuvent pas être vide (colonnes indiquées par *)"
            )

        workspace.save()

        return

    def edit_all(self, cat: ItemCategory, new_item=False) -> None:
        items = self.cells[cat]["items"].keys()

        def cancel():
            to_del = []
            for item in items:
                if item not in self.memory["editing_status"]:
                    continue
                for prop in item.properties:
                    tag = self.cells[cat]["items"][item][prop][0]
                    dpg.delete_item(tag, children_only=True)
                    dpg.add_text(item.properties[prop].value, parent=tag)
                if self.cells[cat]["items"][item]["is_new"]:
                    self.manager.delete_item(item)
                    self.remove_row(cat, item)
                    to_del.append(item)

            for item in to_del:
                self.cells[cat]["items"].pop(item)
                self.set_table_height(cat)
            self.reset_edit_button(cat, items)

        def _set_value(_, value, data):
            data[0].properties[data[1]].value = value

        num_select = 0
        for item, item_dic in self.cells[cat]["items"].items():
            if not dpg.get_value(item_dic["checkbox"]):
                self.memory["editing_status"][item] = False
                continue
            self.memory["editing_status"][item] = True
            num_select += 1
            for prop in item.properties:
                tag = item_dic[prop]
                default_value = item.properties[prop].value
                dpg.delete_item(tag[0], children_only=True)
                if prop.select:
                    dpg.add_combo(
                        prop.select,
                        parent=tag[0],
                        label="",
                        default_value=default_value,
                        width=-1,
                        user_data=(item, prop),
                        callback=_set_value,
                    )
                else:
                    dpg.add_input_text(
                        parent=tag[0],
                        label="",
                        default_value=default_value,
                        width=-1,
                        user_data=(item, prop),
                        callback=_set_value,
                    )
                item_dic[prop] = [tag[0], dpg.last_item()]

        # Nothing has been selected
        if not num_select:
            return

        self.cells[cat]["is_editing"] = True

        # Update the Edit button group
        g_uuid = self.cells[cat]["group_id"]
        save_uuid = dpg.generate_uuid()
        self.cells[cat]["save_button"] = save_uuid
        dpg.delete_item(g_uuid, children_only=True)
        dpg.add_button(
            label="Sauvegarder",
            callback=lambda *args, cat=cat, items=items: self.save_all(cat, new_item),
            parent=g_uuid,
            tag=save_uuid,
        )
        dpg.add_button(label="Annuler", callback=cancel, parent=g_uuid)

    def add_item(self, cat: ItemCategory) -> None:
        items = self.cells[cat]["items"].keys()

        self.set_table_height(cat)
        for item in items:
            if not self.cells[cat]["items"][item]["is_new"]:
                dpg.set_value(self.cells[cat]["items"][item]["checkbox"], False)

        props = cat.properties_order
        new_item = Item(cat, __empty__=True, __no_registration__=True)
        self.cells[cat]["items"][new_item] = {}

        self.add_row(cat, new_item, props, True, True)

        self.edit_all(cat, True)

    def generate_height(self, num):
        return 30 * (num + 3)

    def set_table_height(self, cat: ItemCategory):
        dpg.configure_item(
            self.cells[cat]["window_id"],
            height=self.generate_height(len(self.cells[cat]["items"]) + 1),
        )

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
                    uuid = dpg.generate_uuid()
                    table_uuid = dpg.generate_uuid()
                    self.cells[cat] = {
                        "is_editing": False,
                        "window_id": uuid,
                        "table_id": table_uuid,
                        "group_id": g_uuid,
                        "items": {},
                    }

                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Ajouter objet",
                            tag=button_uuid,
                            callback=lambda *args, cat=cat: self.add_item(cat),
                        )
                        with dpg.group(horizontal=True, tag=g_uuid) as uid:
                            if items:
                                dpg.add_button(
                                    label="Éditer",
                                    callback=self.edit_callback_factory(cat, items),
                                )
                                colored_button(
                                    "Supprimer",
                                    uid,
                                    0,
                                    lambda *args, cat=cat: self.delete_items_in_cat(cat),
                                )

                    # approx_height = dpg.get_item_height(header_uuid)
                    # hard-coded value, approx_height does not work
                    with dpg.child_window(height=self.generate_height(len(items)), tag=uuid):
                        self.table(cat, items, table_uuid, uuid)
