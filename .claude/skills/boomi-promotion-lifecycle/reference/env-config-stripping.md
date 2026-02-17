# Environment Configuration Stripping

## What Gets Stripped and Why

Component XML contains environment-specific values that must be removed before promoting to production.

| Element | Why Strip | Dev Example | After Stripping |
|---------|-----------|-------------|-----------------|
| `<password>` | Credentials differ across environments | `secret123` | ` ` (empty) |
| `<host>` | Server hostnames differ | `dev-server.example.com` | ` ` (empty) |
| `<url>` | Endpoint URLs differ | `https://dev-api.example.com/api` | ` ` (empty) |
| `<port>` | Port numbers may differ | `8080` | ` ` (empty) |
| `<EncryptedValue>` | Encrypted with account-specific keys | `[base64 encrypted]` | ` ` (empty) |

**Security:** Prevents dev credentials from leaking to prod.
**Configuration Management:** Prod environments have different hosts, URLs, passwords.
**Encrypted Values:** Cannot be decrypted in target account (account-specific encryption keys).

---

## Stripping Pattern (Groovy)

### Full Script

```groovy
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil

def root = new XmlSlurper(false, false).parseText(xmlContent)

def strippedElements = []

// Strip password elements
def passwords = root.depthFirst().findAll { it.name() == 'password' }
if (passwords.size() > 0) {
    passwords.each { it.replaceBody('') }
    strippedElements << 'password'
}

// Strip host elements
def hosts = root.depthFirst().findAll { it.name() == 'host' }
if (hosts.size() > 0) {
    hosts.each { it.replaceBody('') }
    strippedElements << 'host'
}

// Strip url elements
def urls = root.depthFirst().findAll { it.name() == 'url' }
if (urls.size() > 0) {
    urls.each { it.replaceBody('') }
    strippedElements << 'url'
}

// Strip port elements
def ports = root.depthFirst().findAll { it.name() == 'port' }
if (ports.size() > 0) {
    ports.each { it.replaceBody('') }
    strippedElements << 'port'
}

// Strip EncryptedValue elements
def encrypted = root.depthFirst().findAll { it.name() == 'EncryptedValue' }
if (encrypted.size() > 0) {
    encrypted.each { it.replaceBody('') }
    strippedElements << 'EncryptedValue'
}

// Serialize
String strippedXml = XmlUtil.serialize(root)
```

**Key Method:** `replaceBody('')` — replaces element content with empty string but preserves the element itself.

---

## Why Preserve Elements (Not Delete)?

**Before Stripping:**
```xml
<password>secret123</password>
```

**After Stripping (CORRECT):**
```xml
<password></password>
```

**If we deleted the element (WRONG):**
```xml
<!-- Element completely removed -->
```

**Why preserve?**
1. **Schema Validation:** Deleting elements would break Boomi's XML schema validation
2. **Post-Promotion Config:** Empty elements serve as placeholders for prod config
3. **Boomi Accepts Empty:** Boomi accepts empty `<password></password>` as valid

**Post-Promotion Workflow:** Admins configure production values via Boomi UI after promotion.

---

## Regex Patterns and Pitfalls

### Pitfall 1: Missing a Sensitive Field Type

If the script doesn't strip a field type (e.g., `<apiKey>`), sensitive data leaks to prod.

**Solution:** Review component XML for all credential-related fields before finalizing script.

**Example — Missing apiKey:**
```groovy
// BAD — apiKey not stripped
['password', 'host', 'url', 'port', 'EncryptedValue'].each { ... }

// GOOD — apiKey included
['password', 'host', 'url', 'port', 'apiKey', 'EncryptedValue'].each { ... }
```

---

### Pitfall 2: EncryptedValue Cannot Be Copied

Even if you try to copy `<EncryptedValue>`, it's encrypted with the source account's key.

**Problem:**
```groovy
// BAD — Trying to preserve EncryptedValue
def encrypted = root.depthFirst().findAll { it.name() == 'EncryptedValue' }
// Don't strip — leave as-is
```

**Why it fails:**
1. EncryptedValue is encrypted with dev account's encryption key
2. Prod account cannot decrypt it (different key)
3. Component will fail validation in prod account

**Solution:** Always strip EncryptedValue fields.

---

### Pitfall 3: Element Name is Case-Sensitive

```groovy
// BAD — Won't match <password>
def passwords = root.depthFirst().findAll { it.name() == 'Password' }

// GOOD — Matches <password>
def passwords = root.depthFirst().findAll { it.name() == 'password' }
```

**Boomi Convention:** Most element names are lowercase. Check actual component XML to confirm.

---

## Depth-First Search Explanation

```groovy
def passwords = root.depthFirst().findAll { it.name() == 'password' }
```

**depthFirst():** Traverses the entire XML tree, visiting every element at every depth level.

**Why depth-first?** Passwords can appear anywhere in the XML structure:

```xml
<bns:Component>
  <bns:name>My Connection</bns:name>
  <bns:connectionConfiguration>
    <bns:authentication>
      <password>secret123</password>  <!-- Nested deep -->
    </bns:authentication>
  </bns:connectionConfiguration>
  <bns:advancedSettings>
    <password>anotherSecret</password>  <!-- Different location -->
  </bns:advancedSettings>
</bns:Component>
```

**depthFirst()** finds both password elements, regardless of depth or path.

---

## Audit Tracking

Track what was stripped for debugging and audit purposes:

```groovy
def strippedElements = []
boolean configStripped = false

// ... strip each type and add to strippedElements ...

ExecutionUtil.setDynamicProcessProperty("configStripped", configStripped.toString(), false)
ExecutionUtil.setDynamicProcessProperty("strippedElements", strippedElements.join(','), false)

if (configStripped) {
    logger.info("Stripped environment config: ${strippedElements.join(', ')}")
} else {
    logger.info("No environment config to strip")
}
```

**Logs Example:**
```
Stripped environment config: password, host, url, EncryptedValue
```

---

## Complete Example with Audit

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

    // Strip each element type
    ['password', 'host', 'url', 'port', 'EncryptedValue'].each { elemName ->
        def elements = root.depthFirst().findAll { it.name() == elemName }
        if (elements.size() > 0) {
            elements.each { it.replaceBody('') }
            strippedElements << elemName
            configStripped = true
        }
    }

    // Track
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
