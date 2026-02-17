/**
 * validate-connection-mappings.groovy
 *
 * Pre-promotion connection validation and filtering.
 * Runs after sort-by-dependency.groovy and before the main promotion loop.
 *
 * Reads DPPs:
 *   - connectionMappingCache: JSON object of pre-loaded connection mappings
 *     (batch-queried from DataHub; keys = dev connection IDs, values = prod connection IDs)
 *
 * Writes DPPs:
 *   - missingConnectionMappings: JSON array of objects for connections without mappings
 *   - missingConnectionCount: count of missing mappings
 *   - connectionMappingsValid: "true" if all connections have mappings, "false" otherwise
 *   - componentMappingCache: updated with found connection mappings (pre-loaded for rewrite-references.groovy)
 *
 * Input document: JSON array of sorted components (from sort-by-dependency.groovy)
 * Output document: JSON array of NON-connection components only (connections filtered out)
 */
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.Properties
import java.util.logging.Logger

Logger logger = Logger.getLogger("validate-connection-mappings")

try {
    if (dataContext.getDataCount() > 1) {
        logger.warning("validate-connection-mappings expects a single document but received ${dataContext.getDataCount()} — processing first document only")
    }

    // Read the sorted components from the document stream
    InputStream is = dataContext.getStream(0)
    Properties props = dataContext.getProperties(0)
    def components = new JsonSlurper().parseText(is.text)

    // Read the pre-loaded connection mapping cache (batch-queried from DataHub)
    String connCacheJson = ExecutionUtil.getDynamicProcessProperty("connectionMappingCache")
    def connCache = new JsonSlurper().parseText(connCacheJson ?: "{}")

    // Read existing component mapping cache
    String compCacheJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
    def compCache = new JsonSlurper().parseText(compCacheJson ?: "{}")

    // Separate connections from non-connections
    def connections = components.findAll { it.type == "connection" }
    def nonConnections = components.findAll { it.type != "connection" }

    // Validate ALL connections have mappings — collect ALL missing, don't stop on first
    def missingMappings = []

    connections.each { conn ->
        String devId = conn.devComponentId
        if (connCache.containsKey(devId)) {
            // Found — pre-load into componentMappingCache for rewrite-references.groovy
            compCache[devId] = connCache[devId]
        } else {
            // Missing — add to error report
            missingMappings << [
                devComponentId: conn.devComponentId,
                name: conn.name,
                type: conn.type,
                devAccountId: ExecutionUtil.getDynamicProcessProperty("devAccountId")
            ]
        }
    }

    // Log validation summary
    int foundCount = connections.size() - missingMappings.size()
    logger.info("Validated ${connections.size()} connection mappings: ${foundCount} found, ${missingMappings.size()} missing")

    // Write results to DPPs
    ExecutionUtil.setDynamicProcessProperty("missingConnectionMappings",
        JsonOutput.toJson(missingMappings), false)
    ExecutionUtil.setDynamicProcessProperty("missingConnectionCount",
        missingMappings.size().toString(), false)
    ExecutionUtil.setDynamicProcessProperty("connectionMappingsValid",
        missingMappings.isEmpty() ? "true" : "false", false)

    // Update the component mapping cache with found connection mappings
    ExecutionUtil.setDynamicProcessProperty("componentMappingCache",
        JsonOutput.toJson(compCache), false)

    // Output ONLY non-connection components for the downstream promotion loop
    dataContext.storeStream(
        new ByteArrayInputStream(JsonOutput.toJson(nonConnections).getBytes("UTF-8")),
        props
    )
} catch (Exception e) {
    logger.severe("validate-connection-mappings failed: " + e.getMessage())
    throw new Exception("validate-connection-mappings failed: " + e.getMessage())
}
