"""Tests for setup.generators.profile_xml — JSON-to-Boomi-XML profile generator."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from setup.generators.profile_xml import generate_profile_xml, infer_data_type
from setup.templates.loader import load_profile_schema

# ---------------------------------------------------------------------------
# Namespace map used throughout for XPath queries
# ---------------------------------------------------------------------------
_NS = {
    "bns": "http://api.platform.boomi.com/",
}


def _parse(xml_str: str) -> ET.Element:
    """Parse generated XML, stripping the declaration line if present."""
    lines = xml_str.strip().split("\n")
    if lines[0].strip().startswith("<?xml"):
        xml_str = "\n".join(lines[1:])
    return ET.fromstring(xml_str)


# ---------------------------------------------------------------------------
# infer_data_type tests
# ---------------------------------------------------------------------------

class TestInferDataType:
    def test_infer_type_string(self) -> None:
        data_type, fmt = infer_data_type("string")
        assert data_type == "character"
        assert "ProfileCharacterFormat" in fmt

    def test_infer_type_integer(self) -> None:
        data_type, fmt = infer_data_type(0)
        assert data_type == "number"
        assert "ProfileNumberFormat" in fmt

    def test_infer_type_boolean(self) -> None:
        data_type, fmt = infer_data_type(True)
        assert data_type == "boolean"
        assert fmt == ""

    def test_infer_type_datetime(self) -> None:
        data_type, fmt = infer_data_type("2026-01-01T00:00:00.000Z")
        assert data_type == "datetime"
        assert "ProfileDateFormat" in fmt

    def test_infer_type_datetime_with_offset(self) -> None:
        data_type, fmt = infer_data_type("2026-01-01T00:00:00+05:30")
        assert data_type == "datetime"
        assert "ProfileDateFormat" in fmt

    def test_infer_type_plain_string_not_datetime(self) -> None:
        data_type, fmt = infer_data_type("hello world")
        assert data_type == "character"

    def test_infer_type_float(self) -> None:
        data_type, fmt = infer_data_type(3.14)
        assert data_type == "number"
        assert "ProfileNumberFormat" in fmt


# ---------------------------------------------------------------------------
# generate_profile_xml structural tests
# ---------------------------------------------------------------------------

class TestComponentEnvelope:
    def test_component_envelope(self) -> None:
        """Outer bns:Component wrapper has correct attributes."""
        xml_str = generate_profile_xml(
            {"field": "string"},
            "Test Profile",
            "PROMO/Profiles",
        )
        root = _parse(xml_str)

        assert root.tag == "{http://api.platform.boomi.com/}Component"
        assert root.get("type") == "profile.json"
        assert root.get("name") == "Test Profile"
        assert root.get("folderFullPath") == "PROMO/Profiles"
        # bns:object child
        bns_object = root.find("bns:object", _NS)
        assert bns_object is not None
        # JSONProfile grandchild
        json_profile = bns_object.find("JSONProfile")
        assert json_profile is not None
        assert json_profile.get("strict") == "false"

    def test_default_folder_path(self) -> None:
        xml_str = generate_profile_xml({"f": "string"}, "MyProfile")
        root = _parse(xml_str)
        assert root.get("folderFullPath") == "PROMO/Profiles"

    def test_xml_declaration_present(self) -> None:
        xml_str = generate_profile_xml({"f": "string"}, "X")
        assert xml_str.strip().startswith("<?xml")
        assert 'encoding="UTF-8"' in xml_str
        assert 'standalone="yes"' in xml_str


class TestSimpleFlatObject:
    def test_simple_flat_object(self) -> None:
        """Single string field generates correct JSONObjectEntry."""
        xml_str = generate_profile_xml({"field": "string"}, "Simple")
        root = _parse(xml_str)

        json_profile = root.find("bns:object/JSONProfile", _NS)
        entry = json_profile.find(
            ".//JSONRootValue/JSONObject/JSONObjectEntry"
        )
        assert entry is not None
        assert entry.get("name") == "field"
        assert entry.get("dataType") == "character"
        assert entry.get("isMappable") == "true"
        assert entry.get("isNode") == "true"

    def test_data_format_character(self) -> None:
        xml_str = generate_profile_xml({"f": "string"}, "X")
        root = _parse(xml_str)
        entry = root.find(".//JSONRootValue/JSONObject/JSONObjectEntry")
        df = entry.find("DataFormat")
        assert df is not None
        fmt_child = list(df)
        assert len(fmt_child) == 1
        assert "ProfileCharacterFormat" in fmt_child[0].tag


class TestMixedTypes:
    def test_mixed_types(self) -> None:
        """Object with string, int, bool fields maps to correct dataTypes."""
        schema = {
            "name": "string",
            "count": 0,
            "active": True,
        }
        xml_str = generate_profile_xml(schema, "Mixed")
        root = _parse(xml_str)

        entries = root.findall(".//JSONRootValue/JSONObject/JSONObjectEntry")
        by_name = {e.get("name"): e for e in entries}

        assert by_name["name"].get("dataType") == "character"
        assert by_name["count"].get("dataType") == "number"
        assert by_name["active"].get("dataType") == "boolean"

    def test_boolean_empty_data_format(self) -> None:
        """Boolean fields have empty <DataFormat/>."""
        xml_str = generate_profile_xml({"flag": True}, "BoolTest")
        root = _parse(xml_str)
        entry = root.find(".//JSONRootValue/JSONObject/JSONObjectEntry[@name='flag']")
        df = entry.find("DataFormat")
        assert df is not None
        assert list(df) == []  # no children


class TestNestedObject:
    def test_nested_object(self) -> None:
        """Object containing a sub-object generates JSONObject nesting."""
        schema = {
            "meta": {
                "processName": "string",
                "requestedBy": "string",
            }
        }
        xml_str = generate_profile_xml(schema, "Nested")
        root = _parse(xml_str)

        # top-level entry for "meta"
        meta_entry = root.find(
            ".//JSONRootValue/JSONObject/JSONObjectEntry[@name='meta']"
        )
        assert meta_entry is not None
        assert meta_entry.get("dataType") == "character"

        # inner JSONObject
        inner_obj = meta_entry.find("JSONObject")
        assert inner_obj is not None
        assert inner_obj.get("name") == "Object"

        # children of inner object
        children = inner_obj.findall("JSONObjectEntry")
        child_names = {c.get("name") for c in children}
        assert "processName" in child_names
        assert "requestedBy" in child_names


class TestArrayOfObjects:
    def test_array_of_objects(self) -> None:
        """Array of objects generates JSONArray > JSONArrayElement > JSONObject."""
        schema = {
            "items": [
                {"id": "string", "label": "string"}
            ]
        }
        xml_str = generate_profile_xml(schema, "ArrObj")
        root = _parse(xml_str)

        arr_entry = root.find(
            ".//JSONRootValue/JSONObject/JSONObjectEntry[@name='items']"
        )
        assert arr_entry is not None

        arr = arr_entry.find("JSONArray")
        assert arr is not None
        assert arr.get("elementType") == "repeating"

        arr_elem = arr.find("JSONArrayElement")
        assert arr_elem is not None
        assert arr_elem.get("maxOccurs") == "-1"
        assert arr_elem.get("minOccurs") == "0"

        inner_obj = arr_elem.find("JSONObject")
        assert inner_obj is not None
        child_names = {e.get("name") for e in inner_obj.findall("JSONObjectEntry")}
        assert "id" in child_names
        assert "label" in child_names

    def test_array_of_strings(self) -> None:
        """Array of strings generates JSONArray > JSONArrayElement (no inner JSONObject)."""
        schema = {"tags": ["string"]}
        xml_str = generate_profile_xml(schema, "ArrStr")
        root = _parse(xml_str)

        arr_entry = root.find(
            ".//JSONRootValue/JSONObject/JSONObjectEntry[@name='tags']"
        )
        arr = arr_entry.find("JSONArray")
        assert arr is not None

        arr_elem = arr.find("JSONArrayElement")
        assert arr_elem is not None
        # no JSONObject for scalar arrays
        assert arr_elem.find("JSONObject") is None


class TestKeyNumbering:
    def test_key_numbering_flat(self) -> None:
        """Keys are sequential starting from 1; Root=1, Object=2, fields start at 3."""
        schema = {"a": "string", "b": "string"}
        xml_str = generate_profile_xml(schema, "Keys")
        root = _parse(xml_str)

        root_val = root.find(".//JSONRootValue")
        assert root_val.get("key") == "1"

        inner_obj = root_val.find("JSONObject")
        assert inner_obj.get("key") == "2"

        entries = inner_obj.findall("JSONObjectEntry")
        assert entries[0].get("key") == "3"
        assert entries[1].get("key") == "4"

    def test_key_numbering_sequential_across_nesting(self) -> None:
        """Keys don't reset or skip across nested structures."""
        schema = {
            "items": [{"id": "string"}],
            "name": "string",
        }
        xml_str = generate_profile_xml(schema, "SeqKeys")
        root = _parse(xml_str)

        # Collect ALL key attributes in document order
        all_keys = [
            int(el.get("key"))
            for el in root.iter()
            if el.get("key") is not None
        ]
        # Must be strictly sequential starting at 1
        assert all_keys == list(range(1, len(all_keys) + 1))


class TestRealProfile:
    def test_real_profile_executePromotion(self) -> None:
        """Load actual executePromotion-request.json and verify XML generation."""
        schema = load_profile_schema("executePromotion-request")
        xml_str = generate_profile_xml(
            schema,
            "PROMO - Profile - ExecutePromotionRequest",
        )
        root = _parse(xml_str)

        # Outer envelope
        assert root.get("type") == "profile.json"
        assert root.get("name") == "PROMO - Profile - ExecutePromotionRequest"

        # Top-level fields present
        entries = root.findall(".//JSONRootValue/JSONObject/JSONObjectEntry")
        field_names = {e.get("name") for e in entries}
        assert "devAccountId" in field_names
        assert "components" in field_names
        assert "promotionMetadata" in field_names
        assert "userSsoGroups" in field_names

        # components is an array entry
        comp_entry = root.find(
            ".//JSONRootValue/JSONObject/JSONObjectEntry[@name='components']"
        )
        assert comp_entry.find("JSONArray") is not None

        # promotionMetadata is a nested object
        meta_entry = root.find(
            ".//JSONRootValue/JSONObject/JSONObjectEntry[@name='promotionMetadata']"
        )
        assert meta_entry.find("JSONObject") is not None

        # Keys are strictly sequential
        all_keys = [
            int(el.get("key"))
            for el in root.iter()
            if el.get("key") is not None
        ]
        assert all_keys == list(range(1, len(all_keys) + 1))
