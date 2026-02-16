import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.Properties
import java.util.regex.Pattern

def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String xmlContent = is.getText("UTF-8")

    // Load the in-memory mapping cache
    String mappingJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
    def mappingCache = [:]
    if (mappingJson && mappingJson.trim()) {
        mappingCache = new JsonSlurper().parseText(mappingJson)
    }

    int rewriteCount = 0
    def rewrittenIds = []

    // Replace each dev ID with its prod ID throughout the XML
    // Component IDs in Boomi are GUIDs like: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    mappingCache.each { devId, prodId ->
        if (xmlContent.contains(devId)) {
            xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
            rewriteCount++
            rewrittenIds << "${devId} -> ${prodId}"
            logger.info("Rewrote reference: ${devId} -> ${prodId}")
        }
    }

    ExecutionUtil.setDynamicProcessProperty("referencesRewritten", rewriteCount.toString(), false)

    if (rewriteCount > 0) {
        logger.info("Total references rewritten: ${rewriteCount}")
    } else {
        logger.info("No references to rewrite")
    }

    dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
}
