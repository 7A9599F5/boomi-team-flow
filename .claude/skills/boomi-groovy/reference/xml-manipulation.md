# XML Manipulation in Boomi Groovy Scripts

## XmlSlurper — Parsing XML

`XmlSlurper` is Groovy's lazy XML parser. It's efficient for large documents and provides a simple API for traversing and modifying XML.

### Basic Parsing

```groovy
import groovy.xml.XmlSlurper

String xmlContent = is.getText("UTF-8")
def root = new XmlSlurper(false, false).parseText(xmlContent)
```

**Constructor Arguments:**
- First `false`: Disable XML validation
- Second `false`: Disable namespace awareness

**Why disable both?** Faster parsing and simpler API. Boomi component XML may include namespaces (`xmlns:bns="..."`), but disabling namespace awareness lets you access elements by local name only.

---

### Accessing Elements

#### Simple Element Access

```groovy
def root = new XmlSlurper(false, false).parseText(xmlContent)

// Access direct children
String componentId = root.componentId.text()
String name = root.name.text()
String type = root.type.text()

// Access nested elements
String folderPath = root.folderFullPath.text()
```

**Note:** `.text()` returns the element's text content as a String.

---

#### Depth-First Search

Find all elements with a specific name, regardless of depth:

```groovy
def passwords = root.depthFirst().findAll { it.name() == 'password' }
```

**Use Case:** Find all `<password>` elements anywhere in the XML (useful for environment config stripping).

**Example:**
```groovy
// Find all password elements and strip them
def passwords = root.depthFirst().findAll { it.name() == 'password' }
passwords.each { it.replaceBody('') }

// Find all host elements
def hosts = root.depthFirst().findAll { it.name() == 'host' }
hosts.each { it.replaceBody('') }
```

---

#### Find All Elements of Multiple Types

```groovy
// Find all reference fields (connectionId, operationId, mapId, profileId)
def references = root.depthFirst().findAll {
    it.name() in ['connectionId', 'operationId', 'mapId', 'profileId']
}

references.each { ref ->
    println "Found reference: ${ref.name()} = ${ref.text()}"
}
```

---

### Modifying Elements

#### Replace Element Content

```groovy
def passwords = root.depthFirst().findAll { it.name() == 'password' }
passwords.each { it.replaceBody('') }
```

**Effect:** Replaces the element's content with an empty string, but preserves the element itself.

**Before:**
```xml
<password>secret123</password>
```

**After:**
```xml
<password></password>
```

**Why preserve the element?** Deleting elements would break Boomi's XML schema validation. Empty elements preserve schema compliance while removing sensitive data.

---

#### Replace Multiple Element Types

```groovy
// Strip all environment-specific config
['password', 'host', 'url', 'port', 'EncryptedValue'].each { elemName ->
    def elements = root.depthFirst().findAll { it.name() == elemName }
    elements.each { it.replaceBody('') }
}
```

---

### Handling Namespaces

#### With Namespace Awareness Disabled

```groovy
def root = new XmlSlurper(false, false).parseText(xmlContent)

// Access elements by local name (ignore namespace prefix)
String componentId = root.componentId.text()  // Works for both <componentId> and <bns:componentId>
```

#### With Namespace Awareness Enabled

```groovy
def root = new XmlSlurper(true, true).parseText(xmlContent)

// Declare namespace
def bns = new groovy.xml.Namespace("http://api.platform.boomi.com/", "bns")

// Access with namespace
String componentId = root[bns.componentId].text()
```

**Recommendation:** Disable namespace awareness (`false, false`) for simpler code. Boomi accepts both namespaced and non-namespaced component XML.

---

## XmlUtil — Serialization

`XmlUtil.serialize()` converts an XmlSlurper result back into an XML string.

```groovy
import groovy.xml.XmlUtil

// Parse
def root = new XmlSlurper(false, false).parseText(xmlContent)

// Modify
def passwords = root.depthFirst().findAll { it.name() == 'password' }
passwords.each { it.replaceBody('') }

// Serialize back to XML
String outputXml = XmlUtil.serialize(root)
```

**Output Formatting:**
- XmlUtil adds pretty-printing (indentation, newlines)
- Whitespace may differ from original XML
- Functionally equivalent for Boomi Platform API

---

### Pretty-Printing for Diff Comparison

For consistent line-by-line diff rendering, use `XmlUtil.serialize()` on both XML documents before comparison.

**Example (Process G: generateComponentDiff):**
```groovy
import groovy.xml.XmlUtil
import groovy.xml.XmlSlurper

// Normalize both branch and main XML
def branchRoot = new XmlSlurper(false, false).parseText(branchXml)
def mainRoot = new XmlSlurper(false, false).parseText(mainXml)

String normalizedBranch = XmlUtil.serialize(branchRoot)
String normalizedMain = XmlUtil.serialize(mainRoot)

// Now both are consistently formatted for diff
```

---

## Boomi Component XML Structure

### Root Element

All Boomi components have a root element matching their type:

```xml
<bns:Process xmlns:bns="http://api.platform.boomi.com/">
  <bns:componentId>abc-123-def-456</bns:componentId>
  <bns:name>Order Processor</bns:name>
  <bns:type>process</bns:type>
  <bns:version>3</bns:version>
  <bns:currentVersion>true</bns:currentVersion>
  <bns:folderFullPath>/DevTeamA/Orders/Process/</bns:folderFullPath>
  <!-- ... component-specific configuration ... -->
</bns:Process>
```

**Common Root Elements:**
- `<bns:Process>` — Integration process
- `<bns:Connection>` — Connection component
- `<bns:Map>` — Map component
- `<bns:ProcessObject>` — Profile component
- `<bns:Operation>` — Operation component

---

### Common Metadata Fields

| Element | Type | Description |
|---------|------|-------------|
| `<componentId>` | UUID | Unique component identifier |
| `<name>` | String | Human-readable component name |
| `<type>` | String | Component type (process, connection, map, etc.) |
| `<version>` | Integer | Current version number |
| `<currentVersion>` | Boolean | `true` if this is the latest version |
| `<folderFullPath>` | String | Folder location (e.g., `/DevTeamA/Orders/Process/`) |
| `<createdDate>` | DateTime | Creation timestamp |
| `<modifiedDate>` | DateTime | Last modified timestamp |

---

### Environment-Specific Configuration Fields

These fields contain environment-specific values that must be stripped during promotion:

| Element | Description | Example |
|---------|-------------|---------|
| `<password>` | Connection passwords, API keys | `secret123` |
| `<host>` | Server hostnames, IP addresses | `dev-server.example.com` |
| `<url>` | Endpoint URLs | `https://dev-api.example.com/api` |
| `<port>` | Port numbers | `8080` |
| `<EncryptedValue>` | Boomi-encrypted sensitive values | (base64-encoded encrypted string) |

**Why strip these?**
1. **Security:** Prevent dev credentials from leaking to prod
2. **Configuration Management:** Prod environments have different hosts, URLs, passwords
3. **Encrypted Values:** Encrypted with account-specific keys — cannot be decrypted in target account

---

### Component Reference Fields

These fields embed references to other components (as UUIDs) that must be rewritten during promotion:

| Element | References | Example |
|---------|-----------|---------|
| `<connectionId>` | Connection components | `abc-123-def-456` |
| `<operationId>` | Operation components | `def-456-ghi-789` |
| `<mapId>` | Map components | `ghi-789-jkl-012` |
| `<profileId>` | Profile components | `jkl-012-mno-345` |
| `<processId>` | Sub-process components | `mno-345-pqr-678` |

**Why rewrite these?**
- Dev component IDs are different from prod component IDs
- After promotion, prod components must reference other prod components
- Mapping cache (from DataHub) provides dev → prod ID translation

---

## Complete Example: Environment Config Stripping

This script strips all environment-specific config from component XML:

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil
import java.util.Properties

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
        passwords.each { it.replaceBody('') }
        strippedElements << 'password'
        configStripped = true
    }

    // Strip host elements
    def hosts = root.depthFirst().findAll { it.name() == 'host' }
    if (hosts.size() > 0) {
        hosts.each { it.replaceBody('') }
        strippedElements << 'host'
        configStripped = true
    }

    // Strip url elements
    def urls = root.depthFirst().findAll { it.name() == 'url' }
    if (urls.size() > 0) {
        urls.each { it.replaceBody('') }
        strippedElements << 'url'
        configStripped = true
    }

    // Strip port elements
    def ports = root.depthFirst().findAll { it.name() == 'port' }
    if (ports.size() > 0) {
        ports.each { it.replaceBody('') }
        strippedElements << 'port'
        configStripped = true
    }

    // Strip EncryptedValue elements
    def encrypted = root.depthFirst().findAll { it.name() == 'EncryptedValue' }
    if (encrypted.size() > 0) {
        encrypted.each { it.replaceBody('') }
        strippedElements << 'EncryptedValue'
        configStripped = true
    }

    // Track what was stripped (for audit)
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
```

---

## Pitfalls and Best Practices

### Pitfall: Element Name is Case-Sensitive

```groovy
// BAD
def passwords = root.depthFirst().findAll { it.name() == 'Password' }  // Won't match <password>

// GOOD
def passwords = root.depthFirst().findAll { it.name() == 'password' }
```

**Boomi convention:** Most element names are lowercase.

---

### Pitfall: Namespace Prefix Changes

When serializing, namespace prefixes may change:

**Before:**
```xml
<bns:Component xmlns:bns="http://api.platform.boomi.com/">
  <bns:componentId>abc-123</bns:componentId>
</bns:Component>
```

**After XmlUtil.serialize():**
```xml
<Component xmlns="http://api.platform.boomi.com/">
  <componentId>abc-123</componentId>
</Component>
```

**Is this a problem?** No. Boomi Platform API accepts both forms.

---

### Best Practice: Use XmlSlurper(false, false)

```groovy
// Recommended
def root = new XmlSlurper(false, false).parseText(xmlContent)
```

**Benefits:**
1. Faster parsing (no validation)
2. Simpler element access (no namespace handling)
3. Works for all Boomi component XML

---

### Best Practice: Always Serialize Before Output

```groovy
// Parse, modify, serialize
def root = new XmlSlurper(false, false).parseText(xmlContent)
// ... modify ...
String outputXml = XmlUtil.serialize(root)
dataContext.storeStream(new ByteArrayInputStream(outputXml.getBytes("UTF-8")), props)
```

**Why?** XmlSlurper returns a lazy-evaluated object. You must serialize it to get a proper XML string.
