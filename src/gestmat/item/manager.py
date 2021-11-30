# -*- coding: utf-8 -*-
#
# MatGest

import datetime
import time
import copy
from typing import Optional, Set, Any, Type, Union

from ..util import strip_special_chars

from .representation import Item, ItemCategory, ItemProperty, define_new_property


class Person:
    name: str
    surname: str
    birthday: datetime.date
    place: str
    note: str
    loans: Set["ItemLoan"]

    def __init__(
        self,
        name: str = "",
        surname: str = "",
        birthday: datetime.date = None,
        place: str = "",
        note: str = "",
    ):
        self.name = name
        self.surname = surname
        self.birthday = birthday
        self.place = place
        self.note = note
        self.loans = set()

        self.items = []

    def __repr__(self) -> str:
        return f"Person({self.name} {self.surname}/Birth: {self.birthday}/Place: {self.place})"

    def register_loan(self, loan: "ItemLoan"):
        self.loans.add(loan)

    def unregister_loan(self, loan: "ItemLoan"):
        if loan in self.loans:
            self.loans.remove(loan)


class ItemLoan:
    persons: Person
    date: datetime.date
    loan_back: datetime.date
    finished: bool = False
    item: Item
    timestamp: float
    note: str

    def __init__(self, item: Item, date: datetime.date, person: Person, note: str):
        """Represents a loan of an item"""
        self.item = item
        self.date = date
        self.person = person
        self.note = note
        self.timestamp = time.time()
        self.person.register_loan(self)

    def __repr__(self) -> str:
        return f"Loan({self.person.surname}, date={self.date})"

    def give_back(self, date: datetime.date = None):
        if date:
            self.loan_back = date
        self.finished = True
        self.person.unregister_loan(self)


def _add_to_dict_set(dict_set: dict, key: Any, element: Any):
    if key not in dict_set:
        dict_set[key] = set()
    dict_set[key].add(element)


class ItemManager:
    items: Set[Item]
    categories: dict[str, ItemCategory]
    properties: dict[ItemProperty, bool]
    loans: dict[Item, Set[ItemLoan]]
    grouped_loans: dict[Person, Set[ItemLoan]]
    persons: Set[Person]
    retired_items: Set[Person]
    retired_loans: dict[Item, Set[ItemLoan]]
    retired_persons: Set[Person]

    def __init__(self):
        self.categories = {}
        self.properties = (
            {}
        )  # Defines the list of properties. True = active, False = retired property
        self.loans = {}
        self.items = set()
        self.persons = set()
        self.retired_items = set()
        self.retired_loans = {}
        self.retired_persons = set()
        self.empty_person = Person()

    def add_category(self, name: str, description: str, properties: list):
        """
        Adds a category of items to the manager

        Arguments
        ---------
        name : str
            name of the category (identifies the category)
        description : str
            description of the category
        properties : list[Mixed]
            can be a list of string representing the properties or a list of types of ItemProperty
            or a list of both
            If the property does not exists in the list of existing properties, it is ignored
        """
        list_properties = []

        for prop in properties:
            if isinstance(prop, str):
                prop_type = ItemProperty.get(strip_special_chars(prop))
                if prop_type:
                    list_properties.append(prop_type)
            elif isinstance(prop, type):
                list_properties.append(prop)

        self.categories[name] = ItemCategory(name, description, list_properties)

    def update_category_key(self, category: ItemCategory, old_name: str):
        if old_name == category.name:
            return
        self.categories[category.name] = category
        del self.categories[old_name]

    def update_properties(self, category: ItemCategory, properties: list[ItemProperty]):
        """
        Updates the properties of a category
        """
        props = set(properties)
        # to_remove = category.properties.difference(props)
        to_add = props.difference(category.properties)
        category.properties_order = list(properties)

        for item in category.registered_items:
            for prop in to_add:
                item.add_property(prop)

        category.properties = properties
        category.properties_order = properties

    def create_property(
        self,
        name,
        value_type: str = "",
        unit: str = "",
        mandatory: bool = False,
        select: list = [],
        no_edit: bool = False,
    ):
        """Creates a property"""
        prop = define_new_property(name, value_type, unit, mandatory, select, no_edit)
        self.properties[prop] = True
        return prop

    def retire_property(self, prop: Union[str, type]):
        if isinstance(prop, str):
            prop = ItemProperty.get(prop)
        if prop in self.properties:
            self.properties[prop] = False

    def unretire_property(self, prop: Union[str, type]):
        if isinstance(prop, str):
            prop = ItemProperty.get(prop)
        if prop in self.properties:
            self.properties[prop] = True

    def add_item(self, item: Item):
        if item.category.name not in self.categories:
            self.categories[item.category.name] = item.category
        for prop in item.properties:
            if prop not in self.properties:
                self.properties[prop] = True

        self.items.add(item)

    def add_items(self, items: Any):
        for item in items:
            self.add_item(item)

    def delete_item(self, item: Item):
        """
        Deletes the item from the manager. Irreversible.
        """
        if item in self.items:
            self.items.remove(item)
            item.category.unregister_item(item)

    def retire_item(self, item: Item, retire_loans: bool = True):
        """
        Retires the item, and all the associated loans of the item
        """
        if item in self.items:
            self.retired_items.add(item)
            self.items.remove(item)
            if item in self.loans and retire_loans:
                if item not in self.retired_loans:
                    self.retired_loans[item] = set()
                for loan in self.loans[item]:
                    self.retired_loans[item].add(loan)
                    loan.give_back(datetime.datetime.now())

                self.loans.pop(item)

    def unretire_item(self, item: Item):
        if item in self.retired_items:
            self.retired_items.remove(item)
            self.items.add(item)

    def create_loan(self, item: Item, date: datetime.date, person: Person, note: str = ""):
        """Creates a loan.
        The item must already exist. If the person does not exists, it is added to the list of persons having a loan
        """
        if item not in self.items:
            raise KeyError(f"{item} is not in list of available items")

        loan = ItemLoan(item, date, person, note)

        self.persons.add(person)

        _add_to_dict_set(self.loans, item, loan)
        return loan

    def _give_back(self, loan: ItemLoan, date: datetime.date):
        """"""
        item = loan.item
        if loan.item in self.loans:
            if loan in self.loans[item]:
                loan.give_back(date)
                self.loans[item].remove(loan)
                _add_to_dict_set(self.retired_loans, item, loan)
                if not loan.person.loans:
                    self.persons.remove(loan.person)
                    self.retired_persons.add(loan.person)

    def is_item_loaned(self, item: Item) -> bool:
        if item in self.loans:
            if self.loans[item]:
                return True
        return False

    def give_back(self, loan_or_item: Union[Item, ItemLoan], date: datetime.date):
        """"""
        if isinstance(loan_or_item, Item):
            loans = list(self.loans[loan_or_item])
            for loan in loans:
                self._give_back(loan, date)
        elif isinstance(loan_or_item, ItemLoan):
            self._give_back(loan_or_item, date)
