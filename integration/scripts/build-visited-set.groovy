import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import groovy.xml.XmlSlurper
import java.util.Properties
import java.util.logging.Logger

Logger logger = Logger.getLogger("build-visited-set")

try {
    for (int i = 0; i < dataContext.getDataCount(); i++) {
        InputStream is = dataContext.getStream(i)
        Properties props = dataContext.getProperties(i)

        String xmlContent = is.getText("UTF-8")

        // Load current visited set as Map for O(1) lookups instead of O(n) ArrayList
        String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
        def visitedSet = [:]
        if (visitedJson && visitedJson.trim()) {
            def parsed = new JsonSlurper().parseText(visitedJson)
            if (parsed instanceof Map) {
                visitedSet = parsed
            } else if (parsed instanceof List) {
                // Migrate from legacy ArrayList format
                parsed.each { visitedSet[it] = true }
            }
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
        if (visitedSet.containsKey(currentId)) {
            ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "true", false)
            logger.info("Component ${currentId} already visited - skipping")
        } else {
            // 200-component limit guard
            if (visitedSet.size() >= 200) {
                logger.severe("Traversal limit reached: visited set has ${visitedSet.size()} components (limit 200). Stopping traversal.")
                ExecutionUtil.setDynamicProcessProperty("traversalPartial", "true", false)
                ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "true", false)
            } else {
                // Add to visited set
                visitedSet[currentId] = true
                ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "false", false)
                logger.info("Component ${currentId} added to visited set (total: ${visitedSet.size()})")

                // Parse ComponentReference response to extract child component IDs
                try {
                    def root = new XmlSlurper(false, false).parseText(xmlContent)

                    // Boomi ComponentReference API returns references in <ComponentReference> elements
                    // Each has a <componentId> child with the referenced component ID
                    root.depthFirst().findAll { it.name() == 'componentId' || it.name() == 'referenceComponentId' }.each { ref ->
                        String childId = ref.text()?.trim()
                        if (childId && !visitedSet.containsKey(childId) && !queue.contains(childId)) {
                            queue << childId
                            logger.info("  Queued child component: ${childId}")
                        }
                    }
                } catch (Exception e) {
                    logger.severe("Could not parse ComponentReference XML: ${e.message}")
                    ExecutionUtil.setDynamicProcessProperty("traversalPartial", "true", false)
                }
            }
        }

        // Update Dynamic Process Properties
        // Store visited set as Map keys list for backward compatibility with downstream consumers
        ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet.keySet().toList()), false)
        ExecutionUtil.setDynamicProcessProperty("componentQueue", JsonOutput.toJson(queue), false)
        ExecutionUtil.setDynamicProcessProperty("visitedCount", visitedSet.size().toString(), false)
        ExecutionUtil.setDynamicProcessProperty("queueCount", queue.size().toString(), false)

        // Pass through the original document
        dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
    }
} catch (Exception e) {
    logger.severe("build-visited-set failed: " + e.getMessage())
    throw new Exception("build-visited-set failed: " + e.getMessage())
}
