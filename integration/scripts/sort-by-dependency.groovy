import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.Properties

def logger = ExecutionUtil.getBaseLogger()

// Type priority mapping (lower = promoted first)
def typePriority = { String type, String componentId, String rootId ->
    type = type?.toLowerCase() ?: ''
    if (type.contains('profile')) return 1
    if (type == 'connection') return 2
    if (type.contains('operation')) return 3
    if (type == 'map') return 4
    if (type == 'process' && componentId == rootId) return 6  // Root process last
    if (type == 'process') return 5  // Sub-processes before root
    return 3  // Default: middle of the pack
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
