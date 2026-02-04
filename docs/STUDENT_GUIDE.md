# Android Course File Upload/Download API - Student Guide

## Welcome!

This guide will help you use the University's file upload/download API in your Android Programming assignments. The API allows your Android app to practice HTTP POST and GET operations with real file transfers.

---

## Your Authentication Token

**Your unique token:** `[INSTRUCTOR WILL PROVIDE]`

**Important:**
- Keep your token private - don't share it with other students
- Don't hardcode it in submitted code - use a config file or BuildConfig field
- Your token is tied to your NetID and gives access only to your files

---

## API Endpoints

**Base URL:** `https://spiderweb.richmond.edu/android`

### 1. Upload a File (HTTP POST)

**Endpoint:** `POST /android/upload`

**Headers:**
```
X-Auth-Token: YOUR_TOKEN_HERE
Content-Type: multipart/form-data
```

**Body:** Multipart form with field name `file`

**Example (Java):**
```java
public class FileUploader {
    private static final String BASE_URL = "https://spiderweb.richmond.edu/android";
    private static final String AUTH_TOKEN = "YOUR_TOKEN_HERE";
    
    public static String uploadFile(File file) throws IOException {
        URL url = new URL(BASE_URL + "/upload");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        String boundary = "===" + System.currentTimeMillis() + "===";
        
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("X-Auth-Token", AUTH_TOKEN);
        conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
        
        try (DataOutputStream out = new DataOutputStream(conn.getOutputStream());
             FileInputStream fileIn = new FileInputStream(file)) {
            
            // Write file part
            out.writeBytes("--" + boundary + "\r\n");
            out.writeBytes("Content-Disposition: form-data; name=\"file\"; filename=\"" + 
                          file.getName() + "\"\r\n");
            out.writeBytes("Content-Type: application/octet-stream\r\n\r\n");
            
            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = fileIn.read(buffer)) != -1) {
                out.write(buffer, 0, bytesRead);
            }
            
            out.writeBytes("\r\n--" + boundary + "--\r\n");
            out.flush();
        }
        
        int responseCode = conn.getResponseCode();
        BufferedReader in = new BufferedReader(
            new InputStreamReader(
                responseCode >= 400 ? conn.getErrorStream() : conn.getInputStream()
            )
        );
        
        StringBuilder response = new StringBuilder();
        String line;
        while ((line = in.readLine()) != null) {
            response.append(line);
        }
        in.close();
        
        return response.toString();
    }
}
```

**Success Response (201):**
```json
{
  "message": "File uploaded successfully",
  "filename": "myfile.txt",
  "size_bytes": 1024,
  "current_usage_mb": 2.5,
  "quota_mb": 500
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `400` - No file provided or empty filename
- `413` - File too large (max 50 MB)
- `507` - Quota exceeded (max 500 MB total storage)
- `429` - Rate limit exceeded (max 10 uploads/minute)

---

### 2. Download a File (HTTP GET)

**Endpoint:** `GET /android/download/<filename>`

**Headers:**
```
X-Auth-Token: YOUR_TOKEN_HERE
```

**Example (Java):**
```java
public class FileDownloader {
    private static final String BASE_URL = "https://spiderweb.richmond.edu/android";
    private static final String AUTH_TOKEN = "YOUR_TOKEN_HERE";
    
    public static void downloadFile(String filename, File outputFile) throws IOException {
        URL url = new URL(BASE_URL + "/download/" + filename);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        conn.setRequestMethod("GET");
        conn.setRequestProperty("X-Auth-Token", AUTH_TOKEN);
        
        int responseCode = conn.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            try (InputStream in = conn.getInputStream();
                 FileOutputStream out = new FileOutputStream(outputFile)) {
                
                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = in.read(buffer)) != -1) {
                    out.write(buffer, 0, bytesRead);
                }
            }
        } else {
            throw new IOException("Download failed: " + responseCode);
        }
    }
}
```

**Success Response:** File binary data

**Error Responses:**
- `401` - Missing or invalid token
- `404` - File not found
- `403` - Invalid file path

---

### 3. List Your Files (HTTP GET)

**Endpoint:** `GET /android/list`

**Headers:**
```
X-Auth-Token: YOUR_TOKEN_HERE
```

**Example (Java):**
```java
public static String listFiles() throws IOException {
    URL url = new URL(BASE_URL + "/list");
    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
    
    conn.setRequestMethod("GET");
    conn.setRequestProperty("X-Auth-Token", AUTH_TOKEN);
    
    BufferedReader in = new BufferedReader(
        new InputStreamReader(conn.getInputStream())
    );
    
    StringBuilder response = new StringBuilder();
    String line;
    while ((line = in.readLine()) != null) {
        response.append(line);
    }
    in.close();
    
    return response.toString();
}
```

**Success Response (200):**
```json
{
  "files": [
    {
      "filename": "photo1.jpg",
      "size_bytes": 204800,
      "modified": "2026-01-20T14:30:00"
    },
    {
      "filename": "data.json",
      "size_bytes": 1024,
      "modified": "2026-01-20T15:45:00"
    }
  ],
  "total_files": 2,
  "total_usage_mb": 0.2,
  "quota_mb": 500,
  "remaining_mb": 499.8
}
```

---

### 4. Delete a File (HTTP DELETE)

**Endpoint:** `DELETE /android/delete/<filename>`

**Headers:**
```
X-Auth-Token: YOUR_TOKEN_HERE
```

**Example (Java):**
```java
public static String deleteFile(String filename) throws IOException {
    URL url = new URL(BASE_URL + "/delete/" + filename);
    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
    
    conn.setRequestMethod("DELETE");
    conn.setRequestProperty("X-Auth-Token", AUTH_TOKEN);
    
    BufferedReader in = new BufferedReader(
        new InputStreamReader(conn.getInputStream())
    );
    
    StringBuilder response = new StringBuilder();
    String line;
    while ((line = in.readLine()) != null) {
        response.append(line);
    }
    in.close();
    
    return response.toString();
}
```

**Success Response (200):**
```json
{
  "message": "File deleted successfully",
  "filename": "data.json",
  "current_usage_mb": 0.2,
  "quota_mb": 500
}
```

---

## Allowed File Types

The following file extensions are supported:
- Documents: `txt`, `pdf`, `doc`, `docx`, `csv`, `json`, `xml`
- Images: `png`, `jpg`, `jpeg`, `gif`
- Media: `mp3`, `mp4`
- Archives: `zip`

---

## Limits and Quotas

| Limit | Value |
|-------|-------|
| Max file size | 50 MB |
| Total storage per student | 500 MB |
| Upload rate limit | 10 uploads/minute |

---

## Important Notes

### 1. Network Operations on Background Thread

**ALWAYS** run network operations on a background thread in Android. The UI thread will throw `NetworkOnMainThreadException` if you don't:

```java
// Good - using a background thread
new Thread(() -> {
    try {
        String result = FileUploader.uploadFile(file);
        runOnUiThread(() -> {
            // Update UI with result
            Toast.makeText(this, "Upload success!", Toast.LENGTH_SHORT).show();
        });
    } catch (IOException e) {
        runOnUiThread(() -> {
            Toast.makeText(this, "Upload failed: " + e.getMessage(), 
                         Toast.LENGTH_SHORT).show();
        });
    }
}).start();

// Better - using AsyncTask or modern alternatives (Kotlin Coroutines, RxJava)
```

### 2. Error Handling

Always handle errors gracefully:

```java
try {
    String response = FileUploader.uploadFile(file);
    JSONObject json = new JSONObject(response);
    
    if (json.has("error")) {
        // Handle error
        String error = json.getString("error");
        Log.e("Upload", "Error: " + error);
    } else {
        // Handle success
        String filename = json.getString("filename");
        Log.i("Upload", "Uploaded: " + filename);
    }
} catch (IOException e) {
    Log.e("Upload", "Network error", e);
} catch (JSONException e) {
    Log.e("Upload", "JSON parsing error", e);
}
```

### 3. Testing from Campus

- **On campus:** API should work directly
- **Off campus:** Connect to University VPN first

### 4. Data Privacy

- You can only access files in your own directory
- Other students cannot see your files
- Files are deleted at the end of the semester (download anything you want to keep!)

---

## Example: Complete Android Activity

```java
public class FileActivity extends AppCompatActivity {
    private static final String BASE_URL = "https://spiderweb.richmond.edu/android";
    private static final String AUTH_TOKEN = BuildConfig.API_TOKEN; // From gradle
    
    private Button uploadButton;
    private Button listButton;
    private TextView resultText;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_file);
        
        uploadButton = findViewById(R.id.uploadButton);
        listButton = findViewById(R.id.listButton);
        resultText = findViewById(R.id.resultText);
        
        uploadButton.setOnClickListener(v -> uploadFile());
        listButton.setOnClickListener(v -> listFiles());
    }
    
    private void uploadFile() {
        // Get file from app's cache or user selection
        File file = new File(getCacheDir(), "test.txt");
        
        new Thread(() -> {
            try {
                String response = doUpload(file);
                runOnUiThread(() -> resultText.setText(response));
            } catch (Exception e) {
                runOnUiThread(() -> 
                    resultText.setText("Error: " + e.getMessage())
                );
            }
        }).start();
    }
    
    private void listFiles() {
        new Thread(() -> {
            try {
                String response = doList();
                runOnUiThread(() -> resultText.setText(response));
            } catch (Exception e) {
                runOnUiThread(() -> 
                    resultText.setText("Error: " + e.getMessage())
                );
            }
        }).start();
    }
    
    private String doUpload(File file) throws IOException {
        // Implementation from earlier example
        // ...
        return response;
    }
    
    private String doList() throws IOException {
        // Implementation from earlier example
        // ...
        return response;
    }
}
```

---

## Troubleshooting

### "Missing authentication token"
- Check that you're setting the `X-Auth-Token` header
- Verify your token value is correct

### "NetworkOnMainThreadException"
- You're running network code on the UI thread
- Move the code to a background thread

### "Connection refused" or timeout
- Check your internet connection
- If off-campus, connect to University VPN
- Verify the URL is correct

### "File too large"
- File exceeds 50 MB limit
- Compress or split the file

### "Quota exceeded"
- You've used all 500 MB of storage
- Delete old files using the `/delete` endpoint
- Use `/list` to see your current usage

---

## Need Help?

- **Technical Issues:** Contact João Tonini (jtonini@richmond.edu)
- **Course Questions:** Contact Prof. Ware (sware@richmond.edu)
- **Lost Token:** Contact your instructor for a new token

---

**Remember:** This is a learning environment. The focus is on understanding HTTP operations and input/output streams in Android, not on building a production file storage system!

Happy coding! 🚀
