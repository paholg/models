"""ElementTree lookups that say what is missing, where its own return None."""

import xml.etree.ElementTree as ET


def child(
    parent: ET.Element, path: str, ns: dict[str, str] | None = None
) -> ET.Element:
    found = parent.find(path, ns)
    if found is None:
        raise ValueError(f"no {path} in <{parent.tag}>")
    return found


def attr(element: ET.Element, name: str) -> str:
    value = element.get(name)
    if value is None:
        raise ValueError(f"no {name} on <{element.tag}>")
    return value
