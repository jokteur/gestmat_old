# -*- coding: utf-8 -*-
#
# MatGest

from ..util import strip_special_chars

import time
import uuid
from dataclasses import dataclass
from collections import defaultdict
from typing import Optional, Set, Any, Type, Union


class ItemProperty:
    value: str
    unit: Optional[str] = None
    mandatory: bool = False
    name: str = ""
    special_name: str = ""
    select: list[str]
    no_edit: bool = False
    retired: bool = False
    _property_types: dict[str, Type["ItemProperty"]] = {}
    registered_items: Set["Item"]

    def __init__(self, value):
        self.value = value

    def __init_subclass__(cls) -> None:
        cls._property_types = {}
        cls.registered_items = set()
        ItemProperty._property_types[cls.__name__[8:].lower()] = cls

    @classmethod
    def get(cls, prop_name: str) -> Type["ItemProperty"]:
        prop_name = prop_name.lower()
        if prop_name in cls._property_types:
            return cls._property_types[prop_name]
        else:
            return None

    @classmethod
    def filter(cls, value) -> list["ItemProperty"]:
        return cls.registered_items[value]

    @classmethod
    def remove_property(cls):
        parents = []
        for item in cls.registered_items:
            parents.append(item.category)
            item.remove_property(cls, True)

    def register_item(self, item: "Item"):
        self.registered_items.add(item)

    def unregister_item(self, item: "Item"):
        if item in self.registered_items:
            self.registered_items.remove(item)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value}, unit={self.unit}, mandatory={self.mandatory})"

    def get_name(self) -> str:
        return self.__class__.__name__[8:]


def define_new_property(
    name: str,
    value_type: Type,
    unit: str = "",
    mandatory: bool = False,
    select: list = [],
    no_edit=False,
):
    special_name = strip_special_chars(name)
    name = name.replace("'", "\\'")

    prop_class_name = f"Property{special_name[0].upper()}{special_name[1:]}"
    value_type_str = {int: "int", float: "float", str: "str"}[value_type]
    cls_str = (
        f"class {prop_class_name}(ItemProperty):\n"
        f"    value : {value_type_str}\n"
        f"    unit : str = '{unit}'\n"
        f"    special_name : str = '{special_name}'\n"
        f"    name : str = '{name}'\n"
        f"    select : list = {select}\n"
        f"    no_edit : bool = {no_edit}\n"
        f"    mandatory : bool = " + ("True" if mandatory else "False")
    )
    scope = dict(ItemProperty=ItemProperty)
    exec(cls_str, scope)
    return scope[prop_class_name]


def _return_prop_type(prop):
    if isinstance(prop, str):
        return ItemProperty.get(strip_special_chars(prop))
    elif isinstance(prop, type):
        return prop
    else:
        return None


class ItemCategory:
    name: str
    description: str
    properties: Set[type[ItemProperty]]
    properties_order: list[ItemProperty]
    registered_items: Set["Item"]

    def __init__(self, name: str, description: str, properties: list[Any]):
        """Class for defining types or categories of items, for e.g. chairs, computer, etc."""
        self.registered_items = set()
        self.properties = set(properties)
        self.name = name
        self.description = description
        self.properties_order = list(properties)

    def __repr__(self):
        text = ""
        for i, p in enumerate(self.properties):
            if i:
                text += ", "
            text += f"{p.name}"
        return f"Category(name='{self.name}', properties: {text})"

    def get_mandatory_props(self):
        props = []
        for prop in self.properties:
            if prop.mandatory:
                props.append(prop)

        return props

    def register_item(self, item: "Item"):
        self.registered_items.add(item)

    def unregister_item(self, item: "Item"):
        if item in self.registered_items:
            self.registered_items.remove(item)

    def add_property(self, prop: type):
        prop = _return_prop_type(prop)
        if prop:
            if prop in self.properties:
                return
            self.properties.add(prop)
            self.properties_order.append(prop)

    def remove_property(self, prop: type, remove_in_children: bool = True):
        prop = _return_prop_type(prop)
        if prop:
            if prop not in self.properties:
                return
            self.properties.remove(prop)
            if remove_in_children:
                for item in self.registered_items:
                    item.remove_property(prop, True)
            self.properties_order.remove(prop)


class Item:
    properties: dict[type, ItemProperty]
    notes: list[dict]
    category: ItemCategory
    uuid: str

    def __init__(self, category: ItemCategory, __empty__=False, **props):
        """
        Create a new item.

        Arguments
        ---------
        category : ItemCategory
            category of Item
        **props : dict
            properties of the Item (should correspond to the properties defined in ItemCategory)
            Raise an error if a mandatory property is not defined.
            Properties that are not defined in ItemCategory are ignored.
        """
        self.properties = {}

        if __empty__:
            for prop in category.properties:
                self.properties[prop] = prop("")
        else:
            self.properties = {}
            for k, v in props.items():
                self.properties[type(ItemProperty.get(k)(v))] = ItemProperty.get(k)(v)

            # Check for mandatory properties that have not been defined
            undefined_list = []
            for prop in category.properties:
                if prop.mandatory and prop not in self.properties.keys():
                    undefined_list.append(prop.__name__.replace("Property", "").lower())

            if undefined_list:
                raise ValueError(
                    f"When defining Item of category '{category.name}', the following mandatory properties have not been defined:\n"
                    f"{undefined_list}"
                )

            # Register the item at all defined properties
            to_remove = []
            for prop_type, prop in self.properties.items():
                if prop_type in category.properties:
                    prop.register_item(self)
                else:
                    to_remove.append(prop_type)

            # Remove undesired properties
            for prop in to_remove:
                self.properties.pop(prop, None)

        self.category = category
        self.category.register_item(self)

        self.notes = {}
        self.uuid = str(uuid.uuid4())

    def __repr__(self) -> str:
        properties = ""
        for p in self.properties.values():
            properties += f", {p.get_name().lower()}={p.value}"
            if p.unit is not None and p.unit != "":
                properties += f"({p.unit})"
        return f"Item(type={self.category.name}{properties})"

    def __getattr__(self, key) -> ItemProperty:
        prop_type = ItemProperty.get(key)
        for prop_type, prop in self.properties.items():
            if isinstance(prop, prop_type):
                return prop
        raise AttributeError(f"No attribute named {key!r}")

    def unregister_item(self) -> None:
        for prop_type, prop in self.properties.items():
            prop.unregister_item(self)
        self.category.unregister_item(self)

    def __del__(self) -> None:
        self.unregister_item()

    def add_note(self, text, timestamp=None) -> None:
        """Adds a note / remark to the item"""
        if not timestamp:
            timestamp = time.time()

        self.notes[timestamp] = text

    def remove_note(self, timestamp) -> None:
        """Removes a note / remark from the item"""
        if timestamp in self.notes:
            del self.notes[timestamp]

    def add_property(self, property: type, erase=False) -> None:
        """
        Adds a property to the item
        """
        if property in self.properties and not erase:
            return
        self.properties[property] = property("")

    def remove_property(self, property: type, ignore_mandatory=False) -> None:
        """Removes a property from the item.

        Arguments
        ---------
        property : ItemProperty
            property to remove from Item
        ignore_mandatory : bool
            if True, removes property even if mandatory"""
        if property in self.properties:
            if not self.properties[property].mandatory or ignore_mandatory:
                self.properties.pop(property, None)
            else:
                raise KeyError(
                    f"Cannot remove the property '{property.name}' because it is mandatory"
                )
