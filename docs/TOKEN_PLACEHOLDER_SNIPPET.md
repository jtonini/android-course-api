# Token Placeholder for Android Starter Code

## For Professor Ware to Include in Her Starter Code

Add this section to your Android app's configuration:

```java
/**
 * API Configuration for File Upload/Download
 */
public class ApiConfig {
    // Base URL for the file upload API
    private static final String BASE_URL = "https://spiderweb.richmond.edu/android";
    
    // TODO: Replace with your personal token from João
    // DO NOT share your token with other students
    // DO NOT submit assignments with your token hardcoded
    // Consider using BuildConfig or a local properties file for production code
    private static final String API_TOKEN = "PASTE_YOUR_TOKEN_HERE";
    
    public static String getBaseUrl() {
        return BASE_URL;
    }
    
    public static String getApiToken() {
        return API_TOKEN;
    }
}
```

## Instructions for Students

Include these instructions with the starter code:

### Step 1: Get Your Token
Your instructor will email you a unique API token. It will look like:
```
kH7jP9xQ2mN8vL3wR6tY4sF1dA9cB3eX5gH8jK2mL7nP6qR4sT9uV1wX3yZ6
```

### Step 2: Add Your Token
1. Open `ApiConfig.java` (or wherever the API_TOKEN is defined)
2. Find the line:
   ```java
   private static final String API_TOKEN = "PASTE_YOUR_TOKEN_HERE";
   ```
3. Replace `"PASTE_YOUR_TOKEN_HERE"` with your actual token:
   ```java
   private static final String API_TOKEN = "kH7jP9xQ2mN8vL3wR6tY4sF1dA9cB3eX5gH8jK2mL7nP6qR4sT9uV1wX3yZ6";
   ```

### Step 3: Using the Token in HTTP Requests
Add the token to your HTTP request headers:

```java
HttpURLConnection conn = (HttpURLConnection) url.openConnection();
conn.setRequestProperty("X-Auth-Token", ApiConfig.getApiToken());
```

### ⚠️ IMPORTANT Security Notes

**Before submitting assignments:**
- Remove your token from the code
- Use `BuildConfig` fields or resource files instead
- Never commit your token to version control
- Never share your token with other students

**Example of proper token management:**

```java
// In build.gradle
android {
    defaultConfig {
        buildConfigField "String", "API_TOKEN", "\"${project.findProperty('api.token') ?: 'PASTE_YOUR_TOKEN_HERE'}\""
    }
}

// In gradle.properties (NOT committed to git)
api.token=your_actual_token_here

// In your code
private static final String API_TOKEN = BuildConfig.API_TOKEN;
```

## Alternative: Using Headers in Different HTTP Libraries

### Using OkHttp:
```java
OkHttpClient client = new OkHttpClient();
Request request = new Request.Builder()
    .url(BASE_URL + "/upload")
    .addHeader("X-Auth-Token", ApiConfig.getApiToken())
    .post(requestBody)
    .build();
```

### Using Retrofit:
```java
public interface ApiService {
    @Headers("X-Auth-Token: " + ApiConfig.API_TOKEN)  // Not ideal
    @POST("/upload")
    Call<ResponseBody> uploadFile(@Body RequestBody file);
    
    // Better approach - add header dynamically with interceptor:
    // See STUDENT_GUIDE.md for details
}
```

## Testing Your Token

To verify your token is working:

1. **Test the health endpoint (no auth required):**
   ```java
   URL url = new URL("https://spiderweb.richmond.edu/android/health");
   // Should return: {"status":"healthy","timestamp":"..."}
   ```

2. **Test list endpoint (requires auth):**
   ```java
   URL url = new URL("https://spiderweb.richmond.edu/android/list");
   HttpURLConnection conn = (HttpURLConnection) url.openConnection();
   conn.setRequestProperty("X-Auth-Token", ApiConfig.getApiToken());
   // Should return your file list (empty initially)
   ```

## Troubleshooting

**Error: "Missing authentication token" (401)**
- Check that you added the `X-Auth-Token` header
- Verify your token string is correct (no extra spaces or quotes)

**Error: "Invalid authentication token" (401)**
- Your token may be incorrect
- Contact João (jtonini@richmond.edu) or Professor Ware for a new token

**Error: "NetworkOnMainThreadException"**
- You're running network code on the UI thread
- Move network operations to a background thread (see STUDENT_GUIDE.md)

---

## For Professor Ware

**Token Distribution:**
You'll receive a CSV file with format:
```csv
NetID,Token
student1,token1...
student2,token2...
```

You can:
1. Email each student their individual token
2. Post tokens as private messages in Blackboard
3. Provide tokens during lab sessions

**Support:**
- Technical issues: jtonini@richmond.edu
- Lost/compromised tokens: Contact João for regeneration

---

**Note:** This is a simplified example. See `docs/STUDENT_GUIDE.md` for complete API documentation with full code examples.
