import os
import datetime
import json
import gzip
from ..util import Singleton, to_date
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

    def load(self, file) -> ItemManager:
        try:
            with gzip.open(file, "r") as fin:
                json_bytes = fin.read()
                json_dict = json.loads(json_bytes.decode("utf-8"))
        except:
            return False, ItemManager()

        def _check_and_load(key_dic: dict, to_check: dict):
            for key, value in key_dic.items():
                if key in to_check:
                    key_dic[key] = to_check[key]

        manager = ItemManager()

        properties = dict()
        if "properties" in json_dict and isinstance(json_dict["properties"], dict):
            for name, prop in json_dict["properties"].items():
                kwargs = dict(
                    name="", unit="", value_type=str, select=[], no_edit=False, mandatory=False
                )

                if "name" not in prop:
                    continue
                _check_and_load(kwargs, prop)
                properties[name] = manager.create_property(**kwargs)

        categories = dict()
        if "categories" in json_dict and isinstance(json_dict["categories"], dict):
            for name, cat in json_dict["categories"].items():
                kwargs = dict(name=name, description="", properties=[])

                _check_and_load(kwargs, cat)
                manager.add_category(**kwargs)

                categories[name] = cat

        def _make_items(items: dict[str, dict]):
            item_dict = dict()
            for ID, item in items.items():
                kwargs = dict(properties=[], notes="", category="")

                if "category" not in item:
                    continue
                _check_and_load(kwargs, item)
                if kwargs["category"] not in manager.categories:
                    continue

                cat = manager.categories[kwargs["category"]]

                # Check if all indicated properties are valid
                props_kwargs = dict()
                for prop in kwargs["properties"]:
                    name, value = list(prop.items())[0]
                    if name not in properties:
                        continue
                    props_kwargs[name] = value

                item_dict[ID] = Item(cat, **props_kwargs)
                item_dict[ID].notes = kwargs["notes"]
            return item_dict

        items = {}
        if "items" in json_dict and isinstance(json_dict["items"], dict):
            items = _make_items(json_dict["items"])
            for item in items.values():
                manager.add_item(item)

        retired_items = {}
        if "retired_items" in json_dict and isinstance(json_dict["retired_items"], dict):
            retired_items = _make_items(json_dict["retired_items"])
            manager.retired_items = set(retired_items.values())

        def _make_persons(persons: dict[str, dict]):
            persons_ret = dict()
            for ID, person in persons.items():
                kwargs = dict(name="", surname="", birthday="", place="", note="", loans=[])
                _check_and_load(kwargs, person)

                kwargs["birthday"] = to_date(kwargs["birthday"])

                loans = kwargs["loans"]
                del kwargs["loans"]
                persons_ret[ID] = (Person(**kwargs), loans)
            return persons_ret

        persons = dict()
        if "persons" in json_dict and isinstance(json_dict["persons"], dict):
            persons = _make_persons(json_dict["persons"])

        retired_persons = dict()
        if "retired_persons" in json_dict and isinstance(json_dict["retired_persons"], dict):
            retired_persons = _make_persons(json_dict["retired_persons"])

        def _make_loans(loans: dict[str, dict], persons_dic, item_dic):
            loan_ret = dict()
            for item_id, item_loans in loans.items():
                if item_id not in items:
                    continue
                valid_loans = []
                for loan in item_loans:
                    kwargs = dict(person="", date="", note="", timestamp=0, item="")
                    _check_and_load(kwargs, loan)
                    if kwargs["person"] not in persons_dic:
                        continue
                    item = item_dic[item_id]
                    person = persons_dic[kwargs["person"]][0]
                    valid_loans.append(
                        {
                            "item": item,
                            "person": person,
                            "date": to_date(kwargs["date"]),
                            "note": kwargs["note"],
                            "timestamp": kwargs["timestamp"],
                        }
                    )

                loan_ret[item_id] = valid_loans
            return loan_ret

        if "loans" in json_dict and isinstance(json_dict["loans"], dict):
            loans = _make_loans(json_dict["loans"], persons, items)

            to_add = {}
            for item_id, item_loans in loans.items():
                for loan in item_loans:
                    manager.create_loan(**loan)

        if "retired_loans" in json_dict and isinstance(json_dict["loans"], dict):
            loans = _make_loans(json_dict["retired_loans"], retired_persons, retired_items)

            to_add = {}
            for item_id, item_loans in loans.items():
                for loan in item_loans:
                    to_add[loan["item"]] = ItemLoan(**loan)
            manager.retired_loans = to_add

        self.current_manager = manager

        return True, self.current_manager

    def new_clean_manager(self) -> ItemManager:
        self.current_manager = ItemManager()
        self.current_manager.create_property("N°", no_edit=True)
        return self.current_manager

    def loan_most_recent(self):
        files = os.listdir(os.path.join(self.path, "sauvegardes"))
        files.sort()

        if not len(files):
            return True, self.new_clean_manager()

        return self.load(os.path.join(self.path, "sauvegardes", files[-1]))
