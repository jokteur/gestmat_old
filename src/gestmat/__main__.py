import datetime
import random
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

from .item.representation import define_new_property, Item, ItemCategory
from .item.manager import ItemManager, Person

from .ui.manager import UIManager


def hello_world():
    manager = ItemManager()
    IDProp = define_new_property("ID", value_type=str, mandatory=True, no_edit=True)
    LengthProp = define_new_property("largeur", value_type=int, unit="cm")
    HeightProp = define_new_property("hauteur", value_type=int, unit="cm")

    sideProp = define_new_property("Côté", value_type=str, select=["gauche", "droite"])

    manager.add_category("FR", "Fauteuil roulant", [IDProp, "largeur", "Côté"])
    manager.add_category("PE", "Planche d'extension", ["id", "Côté"])
    manager.add_category("COUSS", "Coussin VICAIR", ["id", "largeur"])
    manager.add_category("ROHO", "Coussin ROHO", ["id", "Côté"])
    manager.add_category("PANNEAU", "Panneau d'orientation", ["id", "Côté"])

    manager.categories["FR"].add_property("hauteur")
    manager.categories["FR"].remove_property("Côté")

    fr1 = Item(manager.categories["FR"], id="FR 103", largeur=45, hauteur=46)
    fr2 = Item(manager.categories["FR"], id="FR 105", largeur=48, hauteur=47)
    fr3 = Item(manager.categories["FR"], id="FR 106", largeur=50, hauteur=48)

    # fr = Item(manager.categories["FR"], )
    frs = []
    prps = []
    for i in range(8):
        frs.append(
            Item(
                manager.categories["FR"],
                id=f"FR {107+i}",
                largeur=random.randint(40, 50),
                hauteur=random.randint(40, 55),
            )
        )
        prps.append(define_new_property(str(i), value_type=str))
    # manager.update_properties(
    #     manager.categories["FR"], manager.categories["FR"].properties_order + prps
    # )

    cp1 = Item(manager.categories["PE"], id="PE 1", cote="gauche")
    cp2 = Item(manager.categories["PE"], id="PE 2", cote="droite")
    cp3 = Item(manager.categories["PE"], id="PE 3", cote="droite")

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
