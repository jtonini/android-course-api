# Sample Test Files for Android Course

These files are provided for students to test their file upload/download implementations.

## Files Included

### 1. sample_test.txt
- **Type:** Plain text file
- **Size:** < 1 KB
- **Purpose:** Basic text upload testing
- **Use case:** First upload test, verifying successful POST operation

### 2. test_data.json
- **Type:** JSON structured data
- **Size:** < 2 KB
- **Purpose:** Testing structured data uploads
- **Use case:** Practicing with JSON data, learning to handle different file types

### 3. sensor_data.csv
- **Type:** CSV (Comma-Separated Values)
- **Size:** < 1 KB
- **Purpose:** Testing tabular data uploads
- **Use case:** Simulating sensor readings, data logging scenarios

### 4. test_image.png
- **Type:** PNG image
- **Size:** < 50 KB
- **Purpose:** Testing binary file uploads
- **Use case:** Practicing with images, understanding binary vs. text uploads

## How to Use These Files

### In Your Android App

1. **Copy files to your project:**
   ```
   app/src/main/assets/
   ├── sample_test.txt
   ├── test_data.json
   ├── sensor_data.csv
   └── test_image.png
   ```

2. **Load from assets in your code:**
   ```java
   InputStream is = getAssets().open("sample_test.txt");
   File file = new File(getCacheDir(), "sample_test.txt");
   FileOutputStream fos = new FileOutputStream(file);
   
   byte[] buffer = new byte[1024];
   int length;
   while ((length = is.read(buffer)) > 0) {
       fos.write(buffer, 0, length);
   }
   
   fos.close();
   is.close();
   ```

3. **Use for testing:**
   - Upload each file type
   - Verify successful upload via response JSON
   - List files to confirm they are on the server
   - Download them back to verify round-trip
   - Compare downloaded vs. original to ensure integrity

## Testing Checklist

Use these files to verify your implementation handles:

- [x] Small text files (< 1 KB)
- [x] JSON structured data
- [x] CSV tabular data  
- [x] Binary files (images)
- [x] Different file extensions
- [x] Successful upload confirmation
- [x] File listing after upload
- [x] Download and verification
- [x] Error handling for invalid files

## Creating Your Own Test Files

Feel free to create additional test files following these guidelines:

**DO:**
- Create dummy/synthetic data
- Use generic names (test_*, sample_*, dummy_*)
- Keep files small (< 10 MB for testing)
- Document what each file tests

**DON'T:**
- Include any personal information
- Use real names, emails, phone numbers
- Include actual academic records
- Upload copyrighted material

## Example Test Scenarios

### Scenario 1: Basic Upload Test
1. Upload `sample_test.txt`
2. Check response for success message
3. Verify filename and size in response

### Scenario 2: Multiple File Types
1. Upload `sample_test.txt`, `test_data.json`, `sensor_data.csv`
2. Call `/list` endpoint
3. Verify all 3 files appear in the list

### Scenario 3: Binary File Upload
1. Upload `test_image.png`
2. Download it back
3. Compare file sizes to verify integrity

### Scenario 4: Error Handling
1. Try uploading a large file (> 50 MB) - should fail
2. Try uploading invalid file type - should fail
3. Try uploading without token - should fail (401)
4. Verify your app handles errors gracefully

## File Size Reference

| File | Type | Size | Upload Time (est.) |
|------|------|------|-------------------|
| sample_test.txt | Text | < 1 KB | < 1 second |
| test_data.json | JSON | < 2 KB | < 1 second |
| sensor_data.csv | CSV | < 1 KB | < 1 second |
| test_image.png | Image | < 50 KB | 1-2 seconds |

*Upload times assume good WiFi connection*

## Important Reminders

⚠️ **These are TEST files only**
- Never modify to include real personal data
- Never upload files with sensitive information
- Always use dummy/synthetic data for learning

✅ **Good practices:**
- Test with these files first before creating your own
- Verify uploads using multiple methods (response, /list, download)
- Delete test files when done to free up your quota
- Report any issues to João or Professor Ware

---

**Questions?**
- Technical issues: jtonini@richmond.edu
- Course questions: sware@richmond.edu

Happy testing! 🚀
