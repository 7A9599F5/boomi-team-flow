"""Groovy-to-XML script wrapper — generates Boomi Component XML for process scripts."""
from __future__ import annotations

SCRIPT_NAME_MAP: dict[str, str] = {
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
}

_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:bns="http://api.platform.boomi.com/"
    folderFullPath="{folder_full_path}"
    name="{component_name}"
    type="scripting">
    <bns:object>
        <scripting xmlns="" scriptType="processscript" language="groovy2">
            <script><![CDATA[{groovy_content}]]></script>
        </scripting>
    </bns:object>
</bns:Component>"""


def generate_script_xml(
    groovy_content: str,
    component_name: str,
    folder_full_path: str = "Promoted/Scripts",
) -> str:
    """Generate Boomi Component XML for a process script.

    Args:
        groovy_content: Raw Groovy source code
        component_name: e.g. "PROMO - Script - BuildVisitedSet"
        folder_full_path: Boomi folder path

    Returns:
        Complete XML string ready for POST to Component API
    """
    return _TEMPLATE.format(
        folder_full_path=folder_full_path,
        component_name=component_name,
        groovy_content=groovy_content,
    )


def script_stem_to_component_name(stem: str) -> str:
    """Convert a script file stem to its Boomi component name.

    Args:
        stem: e.g. "build-visited-set"

    Returns:
        e.g. "PROMO - Script - BuildVisitedSet"

    Raises:
        KeyError: if stem not in SCRIPT_NAME_MAP
    """
    return SCRIPT_NAME_MAP[stem]
