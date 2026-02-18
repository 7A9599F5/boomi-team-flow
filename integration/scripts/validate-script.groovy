import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.logging.Logger
import org.codehaus.groovy.control.CompilerConfiguration
import org.codehaus.groovy.control.customizers.SecureASTCustomizer
import org.codehaus.groovy.control.MultipleCompilationErrorsException
import org.codehaus.groovy.syntax.SyntaxException
import javax.script.ScriptEngineManager
import javax.script.ScriptException
import javax.script.Compilable

Logger logger = Logger.getLogger("validate-script")

// --- Security Configuration ---
def BLOCKED_IMPORTS = [
    "java.lang.Runtime", "java.lang.ProcessBuilder",
    "java.io.File", "java.io.FileInputStream", "java.io.FileOutputStream",
    "java.net.Socket", "java.net.ServerSocket", "java.net.URL", "java.net.HttpURLConnection",
    "java.lang.reflect.Method", "java.lang.reflect.Field",
    "groovy.lang.GroovyShell", "groovy.lang.GroovyClassLoader",
    "java.lang.ClassLoader", "java.lang.Thread"
]

def BLOCKED_STAR_IMPORTS = [
    "java.lang.reflect", "java.net", "groovy.lang"
]

def BLOCKED_RECEIVERS = [
    "java.lang.Runtime", "java.lang.ProcessBuilder",
    "java.lang.System", "java.lang.ClassLoader",
    "groovy.lang.GroovyShell", "groovy.lang.GroovyClassLoader"
]

int MAX_SCRIPT_SIZE = 10240  // 10 KB

try {
    for (int i = 0; i < dataContext.getDataCount(); i++) {
        InputStream is = dataContext.getStream(i)
        Properties props = dataContext.getProperties(i)

        String inputJson = is.getText("UTF-8")
        def slurper = new JsonSlurper()
        def input = slurper.parseText(inputJson)

        String language = (input.language ?: "").toUpperCase().trim()
        String scriptContent = input.scriptContent ?: ""
        String functionName = input.functionName ?: ""

        def response = [
            success: true,
            errorCode: "",
            errorMessage: "",
            language: language,
            functionName: functionName,
            isValid: false,
            errors: [],
            warningCount: 0,
            validatedAt: new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone("UTC"))
        ]

        // --- Input Validation ---
        if (!language || !(language in ["GROOVY", "JAVASCRIPT"])) {
            response.success = true
            response.errorCode = "INVALID_LANGUAGE"
            response.errorMessage = "Unsupported language: '${input.language ?: ''}'. Must be GROOVY or JAVASCRIPT."
            String outputJson = JsonOutput.prettyPrint(JsonOutput.toJson(response))
            dataContext.storeStream(new ByteArrayInputStream(outputJson.getBytes("UTF-8")), props)
            continue
        }

        if (!scriptContent.trim()) {
            response.success = true
            response.errorCode = "SCRIPT_EMPTY"
            response.errorMessage = "Script content is empty or whitespace only."
            String outputJson = JsonOutput.prettyPrint(JsonOutput.toJson(response))
            dataContext.storeStream(new ByteArrayInputStream(outputJson.getBytes("UTF-8")), props)
            continue
        }

        if (scriptContent.getBytes("UTF-8").length > MAX_SCRIPT_SIZE) {
            response.success = true
            response.errorCode = "SCRIPT_TOO_LARGE"
            response.errorMessage = "Script exceeds maximum size of ${MAX_SCRIPT_SIZE} bytes."
            String outputJson = JsonOutput.prettyPrint(JsonOutput.toJson(response))
            dataContext.storeStream(new ByteArrayInputStream(outputJson.getBytes("UTF-8")), props)
            continue
        }

        // --- Validation ---
        if (language == "GROOVY") {
            try {
                def secureAst = new SecureASTCustomizer()
                secureAst.setImportsBlacklist(BLOCKED_IMPORTS)
                secureAst.setStarImportsBlacklist(BLOCKED_STAR_IMPORTS)
                secureAst.setReceiversBlackList(BLOCKED_RECEIVERS)

                def config = new CompilerConfiguration()
                config.addCompilationCustomizers(secureAst)

                def shell = new GroovyShell(config)
                shell.parse(scriptContent)

                response.isValid = true
                logger.info("Groovy validation PASSED for function '${functionName}'")
            } catch (MultipleCompilationErrorsException mce) {
                mce.getErrorCollector().getErrors().each { error ->
                    def cause = error.getCause()
                    String errorType = "SYNTAX"
                    if (cause?.getMessage()?.contains("import") || cause?.getMessage()?.contains("receiver")) {
                        errorType = "SECURITY"
                    }
                    response.errors << [
                        line: cause instanceof SyntaxException ? cause.getLine() : 0,
                        column: cause instanceof SyntaxException ? cause.getStartColumn() : 0,
                        message: cause?.getMessage() ?: error.toString(),
                        type: errorType
                    ]
                }
                response.errorCode = response.errors.any { it.type == "SECURITY" } ? "GROOVY_SECURITY_VIOLATION" : "GROOVY_SYNTAX_ERROR"
                response.errorMessage = "Groovy validation failed with ${response.errors.size()} error(s)."
                logger.warning("Groovy validation FAILED for function '${functionName}': ${response.errors.size()} errors")
            }
        } else if (language == "JAVASCRIPT") {
            try {
                def engineManager = new ScriptEngineManager()
                def engine = engineManager.getEngineByName("nashorn")
                if (engine instanceof Compilable) {
                    ((Compilable) engine).compile(scriptContent)
                }
                response.isValid = true
                logger.info("JavaScript validation PASSED for function '${functionName}'")
            } catch (ScriptException se) {
                response.errors << [
                    line: se.getLineNumber() >= 0 ? se.getLineNumber() : 0,
                    column: se.getColumnNumber() >= 0 ? se.getColumnNumber() : 0,
                    message: se.getMessage() ?: "JavaScript syntax error",
                    type: "SYNTAX"
                ]
                response.errorCode = "JAVASCRIPT_SYNTAX_ERROR"
                response.errorMessage = "JavaScript validation failed with 1 error(s)."
                logger.warning("JavaScript validation FAILED for function '${functionName}': ${se.getMessage()}")
            }
        }

        String outputJson = JsonOutput.prettyPrint(JsonOutput.toJson(response))
        dataContext.storeStream(new ByteArrayInputStream(outputJson.getBytes("UTF-8")), props)
    }
} catch (Exception e) {
    logger.severe("validate-script FAILED: " + e.getMessage())

    def errorResponse = [
        success: false,
        errorCode: "VALIDATION_INTERNAL_ERROR",
        errorMessage: "Internal validation error: " + e.getMessage(),
        language: "",
        functionName: "",
        isValid: false,
        errors: [],
        warningCount: 0,
        validatedAt: new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone("UTC"))
    ]
    String errorJson = JsonOutput.prettyPrint(JsonOutput.toJson(errorResponse))
    // Re-throw to signal process failure after storing error response
    throw new Exception("Failed to validate script: " + e.getMessage())
}
