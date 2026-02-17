import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.logging.Logger

Logger logger = Logger.getLogger("merge-extension-data")

try {
    for (int i = 0; i < dataContext.getDataCount(); i++) {
        InputStream is = dataContext.getStream(i)
        Properties props = dataContext.getProperties(i)

        String inputJson = is.getText("UTF-8")
        def slurper = new JsonSlurper()
        def input = slurper.parseText(inputJson)

        // Input contains three data sets passed via DPPs or combined upstream
        def envExtensions = input.envExtensions      // EnvironmentExtensions API response
        def mapSummaries = input.mapSummaries ?: []   // EnvironmentMapExtensionsSummary results
        def accessMappings = input.accessMappings ?: [] // ExtensionAccessMapping DataHub records

        String environmentId = envExtensions?.environmentId ?: ExecutionUtil.getDynamicProcessProperty("environmentId") ?: ""
        String userEmail = ExecutionUtil.getDynamicProcessProperty("userEmail") ?: ""

        // Build access lookup: prodComponentId -> access mapping record
        def accessByComponent = [:]
        accessMappings.each { mapping ->
            accessByComponent[mapping.prodComponentId] = mapping
        }

        // Serialize extension data and access mappings as JSON strings
        // (Flow profiles handle them as opaque strings; custom component parses client-side)
        def response = [
            success: true,
            environmentId: environmentId,
            extensionData: JsonOutput.toJson(envExtensions),
            accessMappings: JsonOutput.toJson(accessMappings),
            mapExtensionSummaries: JsonOutput.toJson(mapSummaries),
            componentCount: 0,
            connectionCount: 0,
            processPropertyCount: 0,
            dynamicPropertyCount: 0,
            mapExtensionCount: mapSummaries.size()
        ]

        // Count components by type for summary
        if (envExtensions?.connections?.connection) {
            response.connectionCount = envExtensions.connections.connection.size()
            response.componentCount += response.connectionCount
        }
        if (envExtensions?.processProperties?.ProcessProperty) {
            response.processPropertyCount = envExtensions.processProperties.ProcessProperty.size()
            response.componentCount += response.processPropertyCount
        }
        if (envExtensions?.properties?.property) {
            response.dynamicPropertyCount = envExtensions.properties.property.size()
            response.componentCount += response.dynamicPropertyCount
        }

        logger.info("Merged extension data: ${response.componentCount} components, ${response.mapExtensionCount} map extensions for env ${environmentId}")

        String outputJson = JsonOutput.prettyPrint(JsonOutput.toJson(response))
        dataContext.storeStream(new ByteArrayInputStream(outputJson.getBytes("UTF-8")), props)
    }
} catch (Exception e) {
    logger.severe("merge-extension-data FAILED: " + e.getMessage())
    throw new Exception("Failed to merge extension data: " + e.getMessage())
}
