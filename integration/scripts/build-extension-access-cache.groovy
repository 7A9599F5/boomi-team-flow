import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.logging.Logger

Logger logger = Logger.getLogger("build-extension-access-cache")

try {
    for (int i = 0; i < dataContext.getDataCount(); i++) {
        InputStream is = dataContext.getStream(i)
        Properties props = dataContext.getProperties(i)

        String inputJson = is.getText("UTF-8")
        def slurper = new JsonSlurper()
        def input = slurper.parseText(inputJson)

        String environmentId = input.environmentId
        def extensions = input.extensions
        def componentMappings = input.componentMappings ?: []
        def devAccountAccessRecords = input.devAccountAccessRecords ?: []

        // Build lookup maps
        // prodComponentId -> list of { devAccountId, devAccountName }
        def compMappingByProd = [:].withDefault { [] }
        componentMappings.each { mapping ->
            compMappingByProd[mapping.prodComponentId] << [
                devAccountId: mapping.devAccountId,
                devAccountName: mapping.devAccountName ?: mapping.devAccountId
            ]
        }

        // devAccountId -> list of SSO group IDs
        def ssoGroupsByAccount = [:].withDefault { [] }
        devAccountAccessRecords.each { access ->
            if (access.isActive == "true") {
                ssoGroupsByAccount[access.devAccountId] << access.ssoGroupId
            }
        }

        def accessMappings = []
        String timestamp = new Date().format("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", TimeZone.getTimeZone("UTC"))

        // Process each extension type
        def extensionComponents = []

        // Connections
        extensions?.connections?.connection?.each { conn ->
            extensionComponents << [
                prodComponentId: conn.id,
                componentName: conn.name ?: "Unknown Connection",
                componentType: "connection",
                isConnectionExtension: "true"
            ]
        }

        // Operations
        extensions?.operations?.operation?.each { op ->
            extensionComponents << [
                prodComponentId: op.id,
                componentName: op.name ?: "Unknown Operation",
                componentType: "operation",
                isConnectionExtension: "false"
            ]
        }

        // Process Properties
        extensions?.processProperties?.ProcessProperty?.each { pp ->
            extensionComponents << [
                prodComponentId: pp.id,
                componentName: pp.name ?: "Unknown Process Property",
                componentType: "processProperty",
                isConnectionExtension: "false"
            ]
        }

        // Trading Partners
        extensions?.tradingPartners?.tradingPartner?.each { tp ->
            extensionComponents << [
                prodComponentId: tp.id,
                componentName: tp.name ?: "Unknown Trading Partner",
                componentType: "tradingPartner",
                isConnectionExtension: "false"
            ]
        }

        // Shared Communications
        extensions?.sharedCommunications?.sharedCommunication?.each { sc ->
            extensionComponents << [
                prodComponentId: sc.id,
                componentName: sc.name ?: "Unknown Shared Communication",
                componentType: "sharedCommunication",
                isConnectionExtension: "false"
            ]
        }

        // Build access mapping for each component
        extensionComponents.each { comp ->
            def mappings = compMappingByProd[comp.prodComponentId]
            def authorizedGroups = [] as Set
            def devAccountId = ""
            def devAccountName = ""
            def isShared = "false"
            String ownerProcessId = ExecutionUtil.getDynamicProcessProperty("currentProcessId") ?: ""
            String ownerProcessName = ExecutionUtil.getDynamicProcessProperty("currentProcessName") ?: ""

            if (mappings.size() > 1) {
                isShared = "true"
                // Union of all SSO groups from all originating dev accounts
                mappings.each { m ->
                    authorizedGroups.addAll(ssoGroupsByAccount[m.devAccountId] ?: [])
                    devAccountId = m.devAccountId // Use first for record
                    devAccountName = m.devAccountName
                }
            } else if (mappings.size() == 1) {
                def m = mappings[0]
                devAccountId = m.devAccountId
                devAccountName = m.devAccountName
                authorizedGroups.addAll(ssoGroupsByAccount[m.devAccountId] ?: [])
            } else {
                // No ComponentMapping found — default to admin-only
                logger.info("No ComponentMapping for prodComponentId=${comp.prodComponentId} — defaulting to admin-only")
            }

            accessMappings << [
                environmentId: environmentId,
                prodComponentId: comp.prodComponentId,
                componentName: comp.componentName,
                componentType: comp.componentType,
                ownerProcessId: ownerProcessId,
                ownerProcessName: ownerProcessName,
                devAccountId: devAccountId,
                devAccountName: devAccountName,
                authorizedSsoGroups: JsonOutput.toJson(authorizedGroups.toList()),
                isConnectionExtension: comp.isConnectionExtension,
                isSharedComponent: isShared,
                lastUpdatedAt: timestamp,
                lastUpdatedBy: "PROCESS_D_DEPLOY"
            ]
        }

        logger.info("Built ${accessMappings.size()} ExtensionAccessMapping records for environment ${environmentId}")
        ExecutionUtil.setDynamicProcessProperty("extensionAccessMappingCount", accessMappings.size().toString(), false)

        String outputJson = JsonOutput.prettyPrint(JsonOutput.toJson(accessMappings))
        dataContext.storeStream(new ByteArrayInputStream(outputJson.getBytes("UTF-8")), props)
    }
} catch (Exception e) {
    logger.severe("build-extension-access-cache FAILED: " + e.getMessage())
    throw new Exception("Failed to build extension access cache: " + e.getMessage())
}
