import os
import datetime
import json
import gzip
from ..util import Singleton
from .manager import ItemManager, Item, Person, ItemLoan, ItemCategory, ItemProperty


class Workspace(metaclass=Singleton):
    def __init__(self) -> None:
        pass

    def init(self, manager: ItemManager, path: str = "") -> None:
        self.current_manager = manager
        self.path = path
        self.valid = True

        if not os.path.exists(os.path.join(path, "sauvegardes")):
            try:
                os.mkdir(os.path.join(path, "sauvegardes"))
            except FileExistsError:
                pass
            except:
                self.valid = False

    def save(self) -> None:
        if not self.valid:
            return

        mega_dict = dict()

        mega_dict["properties"] = dict()
        for prop in self.current_manager.properties.keys():
            mega_dict["properties"][prop.special_name] = {
                "name": prop.name,
                "unit": prop.unit,
                "special_name": prop.special_name,
                "name": prop.name,
                "select": prop.select,
                "no_edit": prop.no_edit,
                "mandatory": prop.mandatory,
            }

        mega_dict["categories"] = dict()
        for name, category in self.current_manager.categories.items():
            mega_dict["categories"][name] = {
                "registered_items": [item.uuid for item in category.registered_items],
                "properties": [prop.special_name for prop in category.properties],
                "properties_order": [prop.name for prop in category.properties_order],
                "description": category.description,
            }

        def _get_item_dict_repr(item: Item):
            return {
                "properties": [
                    {prop.special_name: prop.value} for prop in item.properties.values()
                ],
                "notes": item.notes,
                "category": item.category.name,
            }

        def _get_person_dict_repr(person: Person):
            return {
                "name": person.name,
                "surname": person.surname,
                "birthday": person.birthday.strftime("%Y/%m/%d"),
                "place": person.place,
                "note": person.note,
                "loans": [loan.uuid for loan in person.loans],
            }

        def _get_loan_dict_repr(loan: ItemLoan):
            return {
                "person": loan.person.uuid,
                "date": loan.date.strftime("%Y/%m/%d"),
                "note": loan.note,
                "timestamp": loan.timestamp,
            }

        mega_dict["items"] = dict()
        for item in self.current_manager.items:
            mega_dict["items"][item.uuid] = _get_item_dict_repr(item)

        mega_dict["retired_items"] = dict()
        for item in self.current_manager.retired_items:
            mega_dict["retired_items"][item.uuid] = _get_item_dict_repr(item)

        mega_dict["persons"] = dict()
        for person in self.current_manager.persons:
            mega_dict["persons"][person.uuid] = _get_person_dict_repr(person)

        mega_dict["retired_persons"] = dict()
        for person in self.current_manager.retired_persons:
            mega_dict[person.uuid] = _get_person_dict_repr(person)

        mega_dict["loans"] = dict()
        for item, loans in self.current_manager.loans.items():
            mega_dict["loans"][item.uuid] = [_get_loan_dict_repr(loan) for loan in loans]

        mega_dict["retired_loans"] = dict()
        for item, loans in self.current_manager.retired_loans.items():
            mega_dict["retired_loans"][item.uuid] = [_get_loan_dict_repr(loan) for loan in loans]

        name = f"{datetime.datetime.today().strftime('%Y_%m_%d')}_save.json"
        json_str = json.dumps(mega_dict)
        json_bytes = json_str.encode("utf-8")

        try:
            with gzip.open(os.path.join(self.path, "sauvegardes", name), "w") as fout:
                fout.write(json_bytes)
        except:
            return False
        return True

    def loan_most_recent(self):
        files = os.listdir(os.path.join(self.path, "sauvegardes"))
        print(files)
