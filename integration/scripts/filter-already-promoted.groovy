import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.xml.XmlSlurper
import java.util.logging.Logger

Logger logger = Logger.getLogger("PROMO.E4.FilterAlreadyPromoted")

try {
    // Read the comma-separated list of testPromotionIds from production records.
    // This DPP is populated by a prior DataHub Query shape that queries:
    //   PromotionLog WHERE targetEnvironment = "PRODUCTION"
    //     AND testPromotionId IS NOT NULL
    //     AND status != "FAILED"
    // The query result is transformed into a comma-separated list of
    // testPromotionId values and stored in this DPP.
    String productionPromotionIds = ExecutionUtil.getDynamicProcessProperty("productionPromotionIds")

    // Build a Set for O(1) lookup of already-promoted testPromotionIds
    Set<String> promotedSet = new HashSet<>()
    if (productionPromotionIds && productionPromotionIds.trim()) {
        productionPromotionIds.split(",").each { id ->
            String trimmed = id.trim()
            if (trimmed) {
                promotedSet.add(trimmed)
            }
        }
    }

    logger.info("Loaded ${promotedSet.size()} already-promoted testPromotionIds for exclusion")

    int totalDocs = dataContext.getDataCount()
    int passedCount = 0
    int filteredCount = 0

    for (int i = 0; i < totalDocs; i++) {
        InputStream is = dataContext.getStream(i)
        Properties props = dataContext.getProperties(i)

        String docText = is.getText("UTF-8")
        def xml = new XmlSlurper(false, false).parseText(docText)
        String promotionId = xml.promotionId?.text() ?: ""

        if (promotionId && promotedSet.contains(promotionId)) {
            // This test deployment has already been promoted to production — exclude it
            filteredCount++
            logger.info("Excluding test deployment ${promotionId} — already promoted to production")
        } else {
            // This test deployment has NOT been promoted — keep it
            passedCount++
            dataContext.storeStream(
                new ByteArrayInputStream(docText.getBytes("UTF-8")), props)
        }
    }

    logger.info("Filter complete: ${passedCount} passed, ${filteredCount} excluded out of ${totalDocs} total")

} catch (Exception e) {
    logger.severe("filter-already-promoted failed: " + e.getMessage())
    throw new Exception("filter-already-promoted failed: " + e.getMessage())
}
