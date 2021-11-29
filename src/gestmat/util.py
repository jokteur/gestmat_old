# -*- coding: utf-8 -*-
#
# MatGest

import datetime
import unicodedata
from datetime import date, datetime


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ProtectedDatetime:
    def __init__(self, date: datetime) -> None:
        self.date = date
        self.year, self.month, self.day = "", "", ""
        if date:
            self.year = date.year
            self.month = date.month
            self.day = date.day

    def strftime(self, format):
        if isinstance(self.date, datetime):
            return self.date.strftime(format)
        else:
            return ""


def strip_accents(text):
    try:
        text = unicode(text, "utf-8")
    except NameError:  # unicode is a default on python 3
        pass

    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")

    return str(text)


def strip_special_chars(text):
    text = "".join([char for char in text if char.isalnum() or char == "_"])
    return strip_accents(text)
