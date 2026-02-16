import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import groovy.xml.XmlSlurper
import java.util.Properties

def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String xmlContent = is.getText("UTF-8")

    // Load current visited set
    String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
    def visitedSet = []
    if (visitedJson && visitedJson.trim()) {
        visitedSet = new JsonSlurper().parseText(visitedJson)
    }

    // Load current queue
    String queueJson = ExecutionUtil.getDynamicProcessProperty("componentQueue")
    def queue = []
    if (queueJson && queueJson.trim()) {
        queue = new JsonSlurper().parseText(queueJson)
    }

    // Get current component ID being processed
    String currentId = ExecutionUtil.getDynamicProcessProperty("currentComponentId")

    // Check if already visited
    if (visitedSet.contains(currentId)) {
        ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "true", false)
        logger.info("Component ${currentId} already visited - skipping")
    } else {
        // Add to visited set
        visitedSet << currentId
        ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "false", false)
        logger.info("Component ${currentId} added to visited set (total: ${visitedSet.size()})")

        // Parse ComponentReference response to extract child component IDs
        try {
            def root = new XmlSlurper(false, false).parseText(xmlContent)

            // Boomi ComponentReference API returns references in <ComponentReference> elements
            // Each has a <componentId> child with the referenced component ID
            root.depthFirst().findAll { it.name() == 'componentId' || it.name() == 'referenceComponentId' }.each { ref ->
                String childId = ref.text()?.trim()
                if (childId && !visitedSet.contains(childId) && !queue.contains(childId)) {
                    queue << childId
                    logger.info("  Queued child component: ${childId}")
                }
            }
        } catch (Exception e) {
            logger.warning("Could not parse ComponentReference XML: ${e.message}")
        }
    }

    // Update Dynamic Process Properties
    ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
    ExecutionUtil.setDynamicProcessProperty("componentQueue", JsonOutput.toJson(queue), false)
    ExecutionUtil.setDynamicProcessProperty("visitedCount", visitedSet.size().toString(), false)
    ExecutionUtil.setDynamicProcessProperty("queueCount", queue.size().toString(), false)

    // Pass through the original document
    dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
}
