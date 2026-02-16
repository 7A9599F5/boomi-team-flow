import com.boomi.execution.ExecutionUtil
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil
import groovy.xml.StreamingMarkupBuilder
import java.util.Properties

// Logger
def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String xmlContent = is.getText("UTF-8")
    def root = new XmlSlurper(false, false).parseText(xmlContent)

    def strippedElements = []
    boolean configStripped = false

    // Strip password elements
    def passwords = root.depthFirst().findAll { it.name() == 'password' }
    if (passwords.size() > 0) {
        passwords.each { it.replaceBody '' }
        strippedElements << 'password'
        configStripped = true
    }

    // Strip host elements
    def hosts = root.depthFirst().findAll { it.name() == 'host' }
    if (hosts.size() > 0) {
        hosts.each { it.replaceBody '' }
        strippedElements << 'host'
        configStripped = true
    }

    // Strip url elements
    def urls = root.depthFirst().findAll { it.name() == 'url' }
    if (urls.size() > 0) {
        urls.each { it.replaceBody '' }
        strippedElements << 'url'
        configStripped = true
    }

    // Strip port elements
    def ports = root.depthFirst().findAll { it.name() == 'port' }
    if (ports.size() > 0) {
        ports.each { it.replaceBody '' }
        strippedElements << 'port'
        configStripped = true
    }

    // Strip EncryptedValue elements
    def encrypted = root.depthFirst().findAll { it.name() == 'EncryptedValue' }
    if (encrypted.size() > 0) {
        encrypted.each { it.replaceBody '' }
        strippedElements << 'EncryptedValue'
        configStripped = true
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
