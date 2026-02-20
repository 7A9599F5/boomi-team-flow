import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.Properties
import java.util.logging.Logger

Logger logger = Logger.getLogger("sort-by-dependency")

try {
    // Normalize raw Boomi API type values to canonical internal names
    def normalizeType = { String t ->
        if (t == "connector-settings") return "connection"
        if (t == "connector-action") return "operation"
        if (t?.startsWith("profile.")) return "profile"
        if (t == "scripting") return "script"
        return t ?: ""
    }

    // Type priority mapping (lower = promoted first)
    def typePriority = { String type, String componentId, String rootId ->
        type = normalizeType(type)?.toLowerCase() ?: ''
        if (type.contains('profile')) return 1
        if (type == 'connection') return 2
        if (type.contains('operation')) return 3
        if (type == 'map') return 4
        if (type == 'process' && componentId == rootId) return 7  // Root process last
        if (type == 'process') return 5  // Sub-processes before root
        if (type == 'processroute') return 6
        // Unknown types sort last (safer than middle)
        logger.warning("Unknown component type '${type}' for component ${componentId} - defaulting to priority 5 (last)")
        return 5
    }

    for (int i = 0; i < dataContext.getDataCount(); i++) {
        InputStream is = dataContext.getStream(i)
        Properties props = dataContext.getProperties(i)

        String jsonContent = is.getText("UTF-8")
        def components = new JsonSlurper().parseText(jsonContent)

        String rootComponentId = ExecutionUtil.getDynamicProcessProperty("rootComponentId") ?: ''

        // Sort by type hierarchy
        components.sort { a, b ->
            int priorityA = typePriority(a.type, a.devComponentId, rootComponentId)
            int priorityB = typePriority(b.type, b.devComponentId, rootComponentId)
            priorityA <=> priorityB
        }

        logger.info("Sorted ${components.size()} components by dependency order")
        components.eachWithIndex { comp, idx ->
            logger.info("  ${idx + 1}. [${comp.type}] ${comp.name} (${comp.devComponentId})")
        }

        String output = JsonOutput.prettyPrint(JsonOutput.toJson(components))
        dataContext.storeStream(new ByteArrayInputStream(output.getBytes("UTF-8")), props)
    }
} catch (Exception e) {
    logger.severe("sort-by-dependency failed: " + e.getMessage())
    throw new Exception("sort-by-dependency failed: " + e.getMessage())
}
