import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.logging.Logger

Logger logger = Logger.getLogger("strip-connections-for-copy")

try {
    for (int i = 0; i < dataContext.getDataCount(); i++) {
        InputStream is = dataContext.getStream(i)
        Properties props = dataContext.getProperties(i)

        String inputJson = is.getText("UTF-8")
        def slurper = new JsonSlurper()
        def extensions = slurper.parseText(inputJson)

        String targetEnvironmentId = ExecutionUtil.getDynamicProcessProperty("targetEnvironmentId")
        if (!targetEnvironmentId) {
            throw new Exception("targetEnvironmentId DPP is required but not set")
        }

        // Track what was excluded
        def sectionsExcluded = []
        int encryptedFieldsSkipped = 0

        // Remove connection extensions (admin-only, different credentials per env)
        if (extensions.connections) {
            sectionsExcluded << "connections"
            extensions.remove("connections")
        }

        // Remove PGP certificate extensions (environment-specific)
        if (extensions.PGPCertificates) {
            sectionsExcluded << "PGPCertificates"
            extensions.remove("PGPCertificates")
        }

        // Count encrypted fields that cannot be copied (value not in GET response)
        def countEncrypted
        countEncrypted = { obj ->
            if (obj instanceof Map) {
                if (obj.encryptedValueSet == true && obj.usesEncryption == true) {
                    encryptedFieldsSkipped++
                }
                obj.values().each { countEncrypted(it) }
            } else if (obj instanceof List) {
                obj.each { countEncrypted(it) }
            }
        }
        countEncrypted(extensions)

        // Swap environment ID to target
        extensions.environmentId = targetEnvironmentId
        extensions.id = targetEnvironmentId

        // Force partial update mode
        extensions.partial = true

        // Remove @type annotations that may cause issues
        // (keep them - Boomi API expects them for typed objects)

        // Count remaining copyable fields
        int fieldsCopied = 0
        def countFields
        countFields = { obj ->
            if (obj instanceof Map) {
                if (obj.containsKey("value") && obj.value != null) {
                    fieldsCopied++
                }
                obj.values().each { countFields(it) }
            } else if (obj instanceof List) {
                obj.each { countFields(it) }
            }
        }
        countFields(extensions)

        // Set DPPs for response
        ExecutionUtil.setDynamicProcessProperty("sectionsExcluded", sectionsExcluded.join(","), false)
        ExecutionUtil.setDynamicProcessProperty("fieldsCopied", fieldsCopied.toString(), false)
        ExecutionUtil.setDynamicProcessProperty("encryptedFieldsSkipped", encryptedFieldsSkipped.toString(), false)

        logger.info("Strip for copy: excluded=${sectionsExcluded.join(',')}, copied=${fieldsCopied} fields, encrypted skipped=${encryptedFieldsSkipped}")

        String outputJson = JsonOutput.prettyPrint(JsonOutput.toJson(extensions))
        dataContext.storeStream(new ByteArrayInputStream(outputJson.getBytes("UTF-8")), props)
    }
} catch (Exception e) {
    logger.severe("strip-connections-for-copy FAILED: " + e.getMessage())
    throw new Exception("Failed to strip connections for copy: " + e.getMessage())
}
