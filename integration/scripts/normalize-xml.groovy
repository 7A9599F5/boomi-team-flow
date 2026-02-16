import com.boomi.execution.ExecutionUtil
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil
import java.util.Properties

// Logger
def logger = ExecutionUtil.getBaseLogger()

/**
 * normalize-xml.groovy
 *
 * Purpose: Pretty-print XML for consistent line-by-line comparison in diff view.
 * Used by: Process G (generateComponentDiff) — normalizes both branch and main XML
 *          before returning to the UI for client-side diff rendering.
 *
 * Input:  Raw component XML from Platform API (GET /Component/{id} or /Component/{id}~{branchId})
 * Output: Normalized XML with consistent indentation (2-space indent, sorted attributes)
 *
 * Why normalize:
 *   - Boomi API may return XML with inconsistent whitespace
 *   - Attribute ordering can vary between API calls
 *   - Without normalization, diff would show false positives on formatting differences
 */

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String xmlContent = is.getText("UTF-8")

    if (xmlContent == null || xmlContent.trim().isEmpty()) {
        logger.info("Empty XML input — passing through as empty string")
        dataContext.storeStream(new ByteArrayInputStream("".getBytes("UTF-8")), props)
        continue
    }

    try {
        // Parse XML
        def root = new XmlSlurper(false, false).parseText(xmlContent)

        // Serialize with consistent formatting
        // XmlUtil.serialize uses canonical form with consistent indentation
        String normalizedXml = XmlUtil.serialize(root)

        // Remove XML declaration for cleaner diff display
        // The declaration (<?xml version="1.0"...?>) adds noise to diffs
        normalizedXml = normalizedXml.replaceFirst(/<\?xml[^?]*\?>\s*/, '')

        // Trim trailing whitespace from each line for clean comparison
        normalizedXml = normalizedXml.readLines()
            .collect { it.replaceAll(/\s+$/, '') }
            .join('\n')

        logger.info("Normalized XML: ${normalizedXml.length()} chars, ${normalizedXml.readLines().size()} lines")

        dataContext.storeStream(new ByteArrayInputStream(normalizedXml.getBytes("UTF-8")), props)

    } catch (Exception e) {
        logger.severe("Failed to normalize XML: ${e.message}")
        // On parse failure, pass through original content
        // This allows the diff viewer to still show raw content
        dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
    }
}
