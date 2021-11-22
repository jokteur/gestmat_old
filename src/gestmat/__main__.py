import datetime
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

from .item.representation import define_new_property, Item, ItemCategory
from .item.manager import ItemManager, Person

from .ui.manager import UIManager


def hello_world():
    manager = ItemManager()
    IDProp = define_new_property("ID", value_type=str, mandatory=True, no_edit=True)
    LengthProp = define_new_property("length", value_type=int, unit="cm")
    HeightProp = define_new_property("height", value_type=int, unit="cm")

    sideProp = define_new_property("side", value_type=str)

    manager.add_category("FR", "Fauteuil roulant", [IDProp, "length", "side"])
    manager.add_category("CP", "Cale-pied", ["id", "side"])
    manager.add_category("COUSS", "Coussin VICAIR", ["id", "length"])
    manager.add_category("ROHO", "Coussin ROHO", ["id", "side"])
    manager.add_category("PANNEAU", "Panneau d'orientation", ["id", "side"])

    manager.categories["FR"].add_property("height")
    manager.categories["FR"].remove_property("side")

    fr1 = Item(manager.categories["FR"], id="FR 103", length=45, height=46)
    fr2 = Item(manager.categories["FR"], id="FR 105", length=48, height=47)
    fr3 = Item(manager.categories["FR"], id="FR 106", length=50, height=48)

    # fr = Item(manager.categories["FR"], )
    frs = []
    prps = []
    # for i in range(24):
    #     frs.append(Item(manager.categories["FR"], id=f"FR {107+i}"))
    #     prps.append(define_new_property(str(i), value_type=str))
    # manager.update_properties(
    #     manager.categories["FR"], manager.categories["FR"].properties_order + prps
    # )

    cp1 = Item(manager.categories["CP"], id="CP 1", side="G")
    cp2 = Item(manager.categories["CP"], id="CP 2", side="D")
    cp3 = Item(manager.categories["CP"], id="CP 3", side="D")

    manager.add_items([fr1, fr2, fr3, cp1, cp2, cp3] + frs)

    manager.unretire_item(fr2)

    # manager.retire_item(fr2)

    john = Person("John", "Smith", datetime.datetime(1974, 4, 5), "J13 / 543")
    name = Person("Bob", "Family Name", datetime.datetime(1956, 9, 12), "H34 / 923")
    name2 = Person("Alice", "Something", datetime.datetime(1996, 11, 29), "D3 / 435")
    loan1 = manager.create_loan(
        fr1,
        datetime.datetime.now(),
        name,
        "À rendre au plus vite. Ceci est un long texte exprès pour dépasser dans les champs.",
    )
    loan2 = manager.create_loan(fr3, datetime.datetime.now(), john)
    loan3 = manager.create_loan(cp1, datetime.datetime(2021, 10, 19), name)
    loan2 = manager.create_loan(fr2, datetime.datetime.now(), name2, "test 1 2")

    return manager


def main():

    manager = hello_world()

    ui = UIManager(manager)

    ui.init()
