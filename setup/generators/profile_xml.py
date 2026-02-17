"""Generate Boomi Component XML for JSON profiles from schema dicts.

Reads a JSON profile spec (as parsed dict) and emits well-formed XML ready
for POST to the Boomi Component API (type="profile.json").

XML structure reference: integration/api-requests/component-types/profile-json.xml
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


# ---------------------------------------------------------------------------
# Type inference
# ---------------------------------------------------------------------------

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T.+(Z|[+-]\d{2}:\d{2})$")


def infer_data_type(value) -> tuple[str, str]:
    """Infer Boomi dataType and DataFormat inner XML from a JSON example value.

    Args:
        value: A representative JSON value (the "example" from the schema).

    Returns:
        (data_type, format_element) where format_element is the inner XML
        string placed inside <DataFormat>, e.g. "<ProfileCharacterFormat/>"
        or "" for boolean (empty DataFormat).
    """
    if isinstance(value, bool):
        return ("boolean", "")
    if isinstance(value, int):
        return ("number", "<ProfileNumberFormat/>")
    if isinstance(value, float):
        return ("number", "<ProfileNumberFormat/>")
    if isinstance(value, str):
        if _ISO_DATE_RE.match(value):
            return ("datetime", "<ProfileDateFormat/>")
        return ("character", "<ProfileCharacterFormat/>")
    # Fallback for anything else (null, nested, etc.)
    return ("character", "<ProfileCharacterFormat/>")


# ---------------------------------------------------------------------------
# Internal key counter (mutable container for closure-like use)
# ---------------------------------------------------------------------------

class _KeyCounter:
    def __init__(self, start: int = 1) -> None:
        self._value = start

    def next(self) -> int:
        v = self._value
        self._value += 1
        return v


# ---------------------------------------------------------------------------
# XML builders
# ---------------------------------------------------------------------------

def _data_format_element(parent: ET.Element, format_inner: str) -> None:
    """Append a <DataFormat> child to *parent*, with optional inner element."""
    df = ET.SubElement(parent, "DataFormat")
    if format_inner:
        # Parse the inner element and append it
        inner_el = ET.fromstring(format_inner)
        df.append(inner_el)


def _build_object_entries(
    parent: ET.Element,
    schema: dict,
    counter: _KeyCounter,
) -> None:
    """Append <JSONObjectEntry> children to *parent* for each key in *schema*."""
    for field_name, field_value in schema.items():
        if isinstance(field_value, list):
            _build_array_entry(parent, field_name, field_value, counter)
        elif isinstance(field_value, dict):
            _build_nested_object_entry(parent, field_name, field_value, counter)
        else:
            _build_leaf_entry(parent, field_name, field_value, counter)


def _build_leaf_entry(
    parent: ET.Element,
    name: str,
    value,
    counter: _KeyCounter,
) -> None:
    """Append a simple <JSONObjectEntry> (scalar leaf) to *parent*."""
    data_type, format_inner = infer_data_type(value)
    entry = ET.SubElement(
        parent,
        "JSONObjectEntry",
        {
            "dataType": data_type,
            "isMappable": "true",
            "isNode": "true",
            "key": str(counter.next()),
            "name": name,
        },
    )
    _data_format_element(entry, format_inner)


def _build_nested_object_entry(
    parent: ET.Element,
    name: str,
    sub_schema: dict,
    counter: _KeyCounter,
) -> None:
    """Append a <JSONObjectEntry> that wraps a <JSONObject> (nested object)."""
    entry = ET.SubElement(
        parent,
        "JSONObjectEntry",
        {
            "dataType": "character",
            "isMappable": "true",
            "isNode": "true",
            "key": str(counter.next()),
            "name": name,
        },
    )
    _data_format_element(entry, "<ProfileCharacterFormat/>")
    obj = ET.SubElement(
        entry,
        "JSONObject",
        {
            "isMappable": "false",
            "isNode": "true",
            "key": str(counter.next()),
            "name": "Object",
        },
    )
    _build_object_entries(obj, sub_schema, counter)


def _build_array_entry(
    parent: ET.Element,
    name: str,
    array_value: list,
    counter: _KeyCounter,
) -> None:
    """Append a <JSONObjectEntry> that wraps a <JSONArray>."""
    entry = ET.SubElement(
        parent,
        "JSONObjectEntry",
        {
            "dataType": "character",
            "isMappable": "true",
            "isNode": "true",
            "key": str(counter.next()),
            "name": name,
        },
    )
    _data_format_element(entry, "<ProfileCharacterFormat/>")

    arr = ET.SubElement(
        entry,
        "JSONArray",
        {
            "elementType": "repeating",
            "isMappable": "false",
            "isNode": "true",
            "key": str(counter.next()),
            "name": "Array",
        },
    )

    arr_elem = ET.SubElement(
        arr,
        "JSONArrayElement",
        {
            "dataType": "character",
            "isMappable": "true",
            "isNode": "true",
            "key": str(counter.next()),
            "maxOccurs": "-1",
            "minOccurs": "0",
            "name": "ArrayElement1",
        },
    )
    _data_format_element(arr_elem, "<ProfileCharacterFormat/>")

    # Determine element type from first item in the array
    first_item = array_value[0] if array_value else "string"
    if isinstance(first_item, dict):
        # Array of objects: add JSONObject with entries
        obj = ET.SubElement(
            arr_elem,
            "JSONObject",
            {
                "isMappable": "false",
                "isNode": "true",
                "key": str(counter.next()),
                "name": "Object",
            },
        )
        _build_object_entries(obj, first_item, counter)
    # else: array of scalars — no inner JSONObject needed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_profile_xml(
    json_schema: dict | list,
    component_name: str,
    folder_full_path: str = "PROMO/Profiles",
) -> str:
    """Generate Boomi Component XML for a JSON profile from a schema dict.

    Args:
        json_schema: Parsed JSON schema (the profile spec dict/list).
        component_name: e.g. "PROMO - Profile - ExecutePromotionRequest"
        folder_full_path: Boomi folder path, default "PROMO/Profiles"

    Returns:
        Complete XML string ready for POST to Component API.
    """
    # Register namespaces to get clean output
    ET.register_namespace("bns", "http://api.platform.boomi.com/")
    ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

    # Build root element
    component = ET.Element(
        "bns:Component",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:bns": "http://api.platform.boomi.com/",
            "folderFullPath": folder_full_path,
            "name": component_name,
            "type": "profile.json",
        },
    )

    bns_object = ET.SubElement(component, "bns:object")

    json_profile = ET.SubElement(
        bns_object,
        "JSONProfile",
        {"xmlns": "", "strict": "false"},
    )

    data_elements = ET.SubElement(json_profile, "DataElements")

    counter = _KeyCounter(1)

    root_value = ET.SubElement(
        data_elements,
        "JSONRootValue",
        {
            "dataType": "character",
            "isMappable": "true",
            "isNode": "true",
            "key": str(counter.next()),  # key=1
            "name": "Root",
        },
    )
    _data_format_element(root_value, "<ProfileCharacterFormat/>")

    inner_object = ET.SubElement(
        root_value,
        "JSONObject",
        {
            "isMappable": "false",
            "isNode": "true",
            "key": str(counter.next()),  # key=2
            "name": "Object",
        },
    )

    # Normalise schema to dict if top-level is a list
    if isinstance(json_schema, list):
        schema_dict = json_schema[0] if json_schema else {}
    else:
        schema_dict = json_schema

    _build_object_entries(inner_object, schema_dict, counter)

    qualifiers = ET.SubElement(root_value, "Qualifiers")
    ET.SubElement(qualifiers, "QualifierList")

    ET.SubElement(json_profile, "tagLists")

    # Pretty-print via minidom
    raw = ET.tostring(component, encoding="unicode", xml_declaration=False)
    dom = minidom.parseString(raw)
    pretty = dom.toprettyxml(indent="    ", encoding=None)
    # minidom adds its own XML declaration; replace with the canonical one
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    return "\n".join(lines)
