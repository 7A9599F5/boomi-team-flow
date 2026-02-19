"""Tests for DataHubApi XML builders — model spec to CreateModelRequest XML."""
from __future__ import annotations

from setup.api.datahub_api import DataHubApi


class TestModelSpecToXml:
    """Verify _model_spec_to_xml produces valid CreateModelRequest XML."""

    MINIMAL_SPEC = {
        "modelName": "TestModel",
        "fields": [
            {"name": "id", "type": "String", "required": False, "matchField": False},
            {"name": "myDate", "type": "Date", "required": True, "matchField": False},
            {"name": "count", "type": "Number", "required": False, "matchField": False},
            {"name": "active", "type": "Boolean", "required": False, "matchField": False},
        ],
        "matchRules": [{"type": "EXACT", "fields": ["id"]}],
        "sources": [{"name": "TEST_SOURCE", "type": "contribute-only"}],
    }

    def test_datetime_field_uses_correct_type(self) -> None:
        """Date fields must map to type='DATETIME' (no underscore).

        Boomi valid types: BOOLEAN, CLOB, DATE, DATETIME, ENUMERATION,
        FLOAT, INTEGER, REFERENCE, STRING, TIME.
        'DATE_TIME' (with underscore) is NOT valid and causes
        'Missing required properties' API errors.
        """
        xml = DataHubApi._model_spec_to_xml(self.MINIMAL_SPEC)
        assert 'type="DATETIME"' in xml
        assert 'type="DATE_TIME"' not in xml

    def test_string_field_type(self) -> None:
        xml = DataHubApi._model_spec_to_xml(self.MINIMAL_SPEC)
        assert 'type="STRING"' in xml

    def test_integer_field_type(self) -> None:
        xml = DataHubApi._model_spec_to_xml(self.MINIMAL_SPEC)
        assert 'type="INTEGER"' in xml

    def test_boolean_field_type(self) -> None:
        xml = DataHubApi._model_spec_to_xml(self.MINIMAL_SPEC)
        assert 'type="BOOLEAN"' in xml

    def test_unique_id_upper_snake_case(self) -> None:
        """uniqueId must be UPPER_SNAKE_CASE (e.g. myDate → MY_DATE)."""
        xml = DataHubApi._model_spec_to_xml(self.MINIMAL_SPEC)
        assert 'uniqueId="MY_DATE"' in xml
        assert 'uniqueId="ID"' in xml

    def test_model_name_in_output(self) -> None:
        xml = DataHubApi._model_spec_to_xml(self.MINIMAL_SPEC)
        assert "<mdm:name>TestModel</mdm:name>" in xml

    def test_source_id_in_output(self) -> None:
        xml = DataHubApi._model_spec_to_xml(self.MINIMAL_SPEC)
        assert 'id="TEST_SOURCE"' in xml

    def test_match_rule_field_uid(self) -> None:
        xml = DataHubApi._model_spec_to_xml(self.MINIMAL_SPEC)
        assert "<mdm:fieldUniqueId>ID</mdm:fieldUniqueId>" in xml

    def test_component_mapping_spec_datetime(self) -> None:
        """Verify the actual ComponentMapping spec produces DATETIME for lastPromotedAt."""
        from setup.templates.loader import load_model_spec

        spec = load_model_spec("ComponentMapping")
        xml = DataHubApi._model_spec_to_xml(spec)
        # lastPromotedAt is the Date field that caused the original API error
        assert 'name="lastPromotedAt"' in xml
        assert 'type="DATETIME"' in xml
        assert 'type="DATE_TIME"' not in xml
