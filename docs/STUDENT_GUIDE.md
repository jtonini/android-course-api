# Android Course File API - Student Guide

## Overview

This API allows your Android app to upload and download files to/from the course server. Use this to practice HTTP POST and GET operations with input/output streams.

**Base URL:** `https://spiderweb.richmond.edu/android`

## Your Limits

- **Storage Quota:** 500 MB per student
- **Max File Size:** 50 MB per file
- **Max Files:** 100 files
- **Allowed Types:** `.txt`, `.log`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a file |
| GET | `/download/{student_id}/{filename}` | Download a file |
| GET | `/files/{student_id}` | List your files |
| GET | `/quota/{student_id}` | Check your quota |
| DELETE | `/delete/{student_id}/{filename}` | Delete a file |

---

## Android Code Examples

### 1. Upload a File (HTTP POST)

```java
import java.io.*;
import java.net.*;

public class FileUploader {
    
    private static final String BASE_URL = "https://spiderweb.richmond.edu/android";
    private static final String BOUNDARY = "----WebKitFormBoundary" + System.currentTimeMillis();
    
    public static String uploadFile(String studentId, File file) throws IOException {
        URL url = new URL(BASE_URL + "/upload");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + BOUNDARY);
            
            try (OutputStream os = conn.getOutputStream();
                 PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, "UTF-8"), true)) {
                
                // Add student_id field
                writer.append("--").append(BOUNDARY).append("\r\n");
                writer.append("Content-Disposition: form-data; name=\"student_id\"\r\n\r\n");
                writer.append(studentId).append("\r\n");
                
                // Add file field
                writer.append("--").append(BOUNDARY).append("\r\n");
                writer.append("Content-Disposition: form-data; name=\"file\"; filename=\"")
                      .append(file.getName()).append("\"\r\n");
                writer.append("Content-Type: text/plain\r\n\r\n");
                writer.flush();
                
                // Write file content
                try (FileInputStream fis = new FileInputStream(file)) {
                    byte[] buffer = new byte[4096];
                    int bytesRead;
                    while ((bytesRead = fis.read(buffer)) != -1) {
                        os.write(buffer, 0, bytesRead);
                    }
                }
                os.flush();
                
                writer.append("\r\n");
                writer.append("--").append(BOUNDARY).append("--\r\n");
            }
            
            // Read response
            int responseCode = conn.getResponseCode();
            InputStream is = (responseCode >= 200 && responseCode < 300) 
                ? conn.getInputStream() 
                : conn.getErrorStream();
            
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(is))) {
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                return response.toString();
            }
            
        } finally {
            conn.disconnect();
        }
    }
}
```

**Usage:**
```java
File myFile = new File(getFilesDir(), "mydata.txt");
String response = FileUploader.uploadFile("ab1cd", myFile);
Log.d("Upload", response);
```

---

### 2. Download a File (HTTP GET)

```java
import java.io.*;
import java.net.*;

public class FileDownloader {
    
    private static final String BASE_URL = "https://spiderweb.richmond.edu/android";
    
    public static void downloadFile(String studentId, String filename, File destination) 
            throws IOException {
        
        URL url = new URL(BASE_URL + "/download/" + studentId + "/" + filename);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            
            int responseCode = conn.getResponseCode();
            if (responseCode != 200) {
                throw new IOException("Download failed: HTTP " + responseCode);
            }
            
            try (InputStream is = conn.getInputStream();
                 FileOutputStream fos = new FileOutputStream(destination)) {
                
                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = is.read(buffer)) != -1) {
                    fos.write(buffer, 0, bytesRead);
                }
            }
            
        } finally {
            conn.disconnect();
        }
    }
}
```

**Usage:**
```java
File downloadedFile = new File(getFilesDir(), "downloaded.txt");
FileDownloader.downloadFile("ab1cd", "mydata.txt", downloadedFile);
```

---

### 3. List Your Files (HTTP GET)

```java
import java.io.*;
import java.net.*;

public class FileList {
    
    private static final String BASE_URL = "https://spiderweb.richmond.edu/android";
    
    public static String listFiles(String studentId) throws IOException {
        URL url = new URL(BASE_URL + "/files/" + studentId);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(conn.getInputStream()))) {
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                return response.toString();
            }
            
        } finally {
            conn.disconnect();
        }
    }
}
```

**Example Response:**
```json
{
  "success": true,
  "student_id": "ab1cd",
  "files": [
    {
      "filename": "mydata.txt",
      "size": 1024,
      "size_formatted": "1.0 KB",
      "uploaded": "2026-01-15T10:30:00"
    }
  ],
  "file_count": 1,
  "total_size_formatted": "1.0 KB"
}
```

---

### 4. Check Your Quota (HTTP GET)

```java
public static String checkQuota(String studentId) throws IOException {
    URL url = new URL(BASE_URL + "/quota/" + studentId);
    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
    
    try {
        conn.setRequestMethod("GET");
        
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getInputStream()))) {
            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            return response.toString();
        }
        
    } finally {
        conn.disconnect();
    }
}
```

**Example Response:**
```json
{
  "success": true,
  "student_id": "ab1cd",
  "quota": {
    "used_formatted": "1.0 KB",
    "limit_formatted": "500.0 MB",
    "available_formatted": "499.9 MB",
    "percentage_used": 0.0
  },
  "files": {
    "count": 1,
    "limit": 100
  }
}
```

---

### 5. Delete a File (HTTP DELETE)

```java
public static String deleteFile(String studentId, String filename) throws IOException {
    URL url = new URL(BASE_URL + "/delete/" + studentId + "/" + filename);
    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
    
    try {
        conn.setRequestMethod("DELETE");
        
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getInputStream()))) {
            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            return response.toString();
        }
        
    } finally {
        conn.disconnect();
    }
}
```

---

## Testing with curl (Command Line)

You can test the API from your computer using curl:

```bash
# Upload a file
curl -X POST \
  -F "student_id=ab1cd" \
  -F "file=@myfile.txt" \
  https://spiderweb.richmond.edu/android/upload

# Download a file
curl -O https://spiderweb.richmond.edu/android/download/ab1cd/myfile.txt

# List files
curl https://spiderweb.richmond.edu/android/files/ab1cd

# Check quota
curl https://spiderweb.richmond.edu/android/quota/ab1cd

# Delete a file
curl -X DELETE https://spiderweb.richmond.edu/android/delete/ab1cd/myfile.txt
```

---

## Error Handling

Always check the `success` field in responses:

```java
// Parse JSON response
JSONObject json = new JSONObject(response);
if (json.getBoolean("success")) {
    // Operation succeeded
    String filename = json.getString("filename");
} else {
    // Operation failed
    String error = json.getString("error");
    Log.e("API", "Error: " + error);
}
```

**Common Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid student_id" | NetID format wrong | Use your UR NetID (alphanumeric) |
| "File type not allowed" | Wrong extension | Use .txt or .log files only |
| "Quota exceeded" | Out of space | Delete old files |
| "File too large" | File > 50 MB | Use smaller files |

---

## Important Notes

1. **Use Your NetID:** Your `student_id` must be your University of Richmond NetID (e.g., "ab1cd")

2. **Network Thread:** Always run network operations on a background thread in Android:
   ```java
   new Thread(() -> {
       try {
           String result = FileUploader.uploadFile("ab1cd", file);
           runOnUiThread(() -> updateUI(result));
       } catch (IOException e) {
           e.printStackTrace();
       }
   }).start();
   ```

3. **VPN Required:** If you're off-campus, connect to the University VPN first.

4. **Data Retention:** Files are deleted at the end of the semester. Download anything you need to keep!

---

## Need Help?

- **Technical Issues:** Contact João Tonini (jtonini@richmond.edu)
- **Course Questions:** Contact Prof. Ware (sware@richmond.edu)
