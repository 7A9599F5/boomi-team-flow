import com.boomi.execution.ExecutionUtil
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil
import java.util.Properties
import java.util.logging.Logger
import java.util.regex.Pattern

Logger logger = Logger.getLogger("strip-env-config")

// Component types that contain sensitive environment configuration
def sensitiveTypes = ['process', 'operation', 'connection', 'connector-action'] as Set

// Explicit element names to strip (case-sensitive match)
def stripElementNames = [
    'password', 'host', 'url', 'port',
    'EncryptedValue',
    'apiKey', 'apiToken', 'secretKey', 'clientSecret',
    'connectionString', 'jdbcUrl', 'privateKey',
    'keystorePassword', 'proxyPassword'
] as Set

// Regex catch-all for any element whose name contains sensitive keywords
def sensitiveNamePattern = Pattern.compile(/(?i)(password|secret|key|token|credential)/)

try {
    for (int i = 0; i < dataContext.getDataCount(); i++) {
        InputStream is = dataContext.getStream(i)
        Properties props = dataContext.getProperties(i)

        String xmlContent = is.getText("UTF-8")

        // Determine component type from DPP (set by upstream process)
        String componentType = ExecutionUtil.getDynamicProcessProperty("currentComponentType")?.toLowerCase() ?: ''

        // Only strip sensitive types — skip profiles, maps, processroutes, etc.
        if (!sensitiveTypes.contains(componentType)) {
            logger.info("Component type '${componentType}' is not sensitive — skipping stripping")
            ExecutionUtil.setDynamicProcessProperty("configStripped", "false", false)
            ExecutionUtil.setDynamicProcessProperty("strippedElements", "", false)
            dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
            continue
        }

        def root = new XmlSlurper(false, false).parseText(xmlContent)

        def strippedElements = []
        boolean configStripped = false

        // Strip all elements matching explicit names or the regex catch-all
        root.depthFirst().findAll { node ->
            String name = node.name()
            stripElementNames.contains(name) || sensitiveNamePattern.matcher(name).find()
        }.each { node ->
            String name = node.name()
            if (node.text()?.trim()) {
                node.replaceBody ''
                if (!strippedElements.contains(name)) {
                    strippedElements << name
                }
                configStripped = true
            }
        }

        // Set Dynamic Process Properties for downstream tracking
        ExecutionUtil.setDynamicProcessProperty("configStripped", configStripped.toString(), false)
        ExecutionUtil.setDynamicProcessProperty("strippedElements", strippedElements.join(','), false)

        if (configStripped) {
            logger.info("Stripped environment config: ${strippedElements.join(', ')}")
        } else {
            logger.info("No environment config to strip")
        }

        // Serialize and output
        String outputXml = XmlUtil.serialize(root)
        dataContext.storeStream(new ByteArrayInputStream(outputXml.getBytes("UTF-8")), props)
    }
} catch (Exception e) {
    // CRITICAL: Fail hard on any error — never pass through unstripped XML that might contain credentials
    logger.severe("strip-env-config FAILED: " + e.getMessage())
    throw new Exception("strip-env-config FAILED — refusing to pass through potentially unstripped XML: " + e.getMessage())
}
