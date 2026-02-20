"""Tests for setup.generators.script_xml — Groovy-to-XML script wrapper."""
from __future__ import annotations

import pytest

from setup.generators.script_xml import (
    SCRIPT_NAME_MAP,
    generate_script_xml,
    script_stem_to_component_name,
)
from setup.templates.loader import load_template


class TestGenerateSimpleScript:
    def test_generate_simple_script(self) -> None:
        """Minimal Groovy content produces valid XML string."""
        xml = generate_script_xml("println 'hello'", "PROMO - Script - Test")

        assert xml.startswith("<?xml version=")
        assert "<bns:Component" in xml
        assert "println 'hello'" in xml


class TestCdataWrapping:
    def test_cdata_wrapping(self) -> None:
        """Script content is wrapped inside a CDATA section."""
        xml = generate_script_xml("def x = 1", "PROMO - Script - Test")

        assert "<![CDATA[" in xml
        assert "]]>" in xml

    def test_cdata_preserves_special_chars(self) -> None:
        """Characters <, >, & inside Groovy are preserved as-is inside CDATA."""
        groovy = 'if (a < b && c > d) { println "&amp;" }'
        xml = generate_script_xml(groovy, "PROMO - Script - Test")

        assert "a < b" in xml
        assert "c > d" in xml
        assert "&&" in xml
        assert '"&amp;"' in xml


class TestComponentEnvelope:
    def test_component_envelope(self) -> None:
        """bns:Component has correct name, type, and folderFullPath attributes."""
        xml = generate_script_xml(
            "def x = 1",
            "PROMO - Script - BuildVisitedSet",
            folder_full_path="Promoted/Scripts",
        )

        assert 'name="PROMO - Script - BuildVisitedSet"' in xml
        assert 'type="script.processing"' in xml
        assert 'folderFullPath="Promoted/Scripts"' in xml

    def test_xmlns_declarations(self) -> None:
        """XML includes bns and xsi namespace declarations."""
        xml = generate_script_xml("def x = 1", "PROMO - Script - Test")

        assert 'xmlns:bns="http://api.platform.boomi.com/"' in xml
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in xml


class TestScriptTypeAndLanguage:
    def test_script_type_and_language(self) -> None:
        """ProcessingScript element has language=groovy2 (no scriptType attribute)."""
        xml = generate_script_xml("def x = 1", "PROMO - Script - Test")

        assert "<ProcessingScript" in xml
        assert 'language="groovy2"' in xml
        assert "scriptType" not in xml


class TestStemToComponentName:
    def test_stem_to_component_name(self) -> None:
        """All 11 stem mappings resolve to correct component names."""
        expected = {
            "build-visited-set": "PROMO - Script - BuildVisitedSet",
            "sort-by-dependency": "PROMO - Script - SortByDependency",
            "strip-env-config": "PROMO - Script - StripEnvConfig",
            "validate-connection-mappings": "PROMO - Script - ValidateConnectionMappings",
            "rewrite-references": "PROMO - Script - RewriteReferences",
            "normalize-xml": "PROMO - Script - NormalizeXml",
            "filter-already-promoted": "PROMO - Script - FilterAlreadyPromoted",
            "build-extension-access-cache": "PROMO - Script - BuildExtensionAccessCache",
            "strip-connections-for-copy": "PROMO - Script - StripConnectionsForCopy",
            "merge-extension-data": "PROMO - Script - MergeExtensionData",
            "validate-script": "PROMO - Script - ValidateScript",
        }
        assert len(SCRIPT_NAME_MAP) == 11
        for stem, name in expected.items():
            assert script_stem_to_component_name(stem) == name

    def test_stem_to_component_name_unknown(self) -> None:
        """Unknown stem raises KeyError."""
        with pytest.raises(KeyError):
            script_stem_to_component_name("not-a-real-script")


class TestRealGroovyFile:
    def test_real_groovy_file(self) -> None:
        """Load actual build-visited-set.groovy and verify CDATA contains full content."""
        groovy_content = load_template("integration/scripts/build-visited-set.groovy")
        component_name = script_stem_to_component_name("build-visited-set")

        xml = generate_script_xml(groovy_content, component_name)

        assert groovy_content in xml
        assert "<![CDATA[" in xml
        assert "build-visited-set" in xml
        assert component_name in xml


class TestCustomFolderPath:
    def test_custom_folder_path(self) -> None:
        """Non-default folder path is reflected in the XML output."""
        xml = generate_script_xml(
            "def x = 1",
            "PROMO - Script - Test",
            folder_full_path="Custom/Folder/Path",
        )

        assert 'folderFullPath="Custom/Folder/Path"' in xml
        assert 'folderFullPath="Promoted/Scripts"' not in xml

    def test_default_folder_path(self) -> None:
        """Default folder path is Promoted/Scripts when not specified."""
        xml = generate_script_xml("def x = 1", "PROMO - Script - Test")

        assert 'folderFullPath="Promoted/Scripts"' in xml


class TestMultilineScript:
    def test_multiline_script(self) -> None:
        """Multi-line Groovy script is correctly wrapped in a single CDATA block."""
        groovy = (
            "import groovy.json.JsonSlurper\n"
            "def slurper = new JsonSlurper()\n"
            "for (int i = 0; i < dataContext.getDataCount(); i++) {\n"
            "    InputStream is = dataContext.getStream(i)\n"
            "    dataContext.storeStream(is, props)\n"
            "}"
        )
        xml = generate_script_xml(groovy, "PROMO - Script - Test")

        assert "import groovy.json.JsonSlurper" in xml
        assert "dataContext.storeStream" in xml
        # All lines present and only one CDATA block
        assert xml.count("<![CDATA[") == 1
        assert xml.count("]]>") == 1
