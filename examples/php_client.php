<?php
/**
 * Android Course File API - PHP Client Example
 * 
 * Demonstrates how to interact with the Android Course REST API from PHP
 * This can be used for:
 * - Server-side file uploads
 * - Admin dashboards
 * - Integration with other systems
 * - Batch operations
 */

// Configuration
define('API_BASE_URL', 'https://still.richmond.edu/android');
define('STUDENT_TOKEN', 'your_token_here'); // Replace with actual student token

/**
 * Make API request
 */
function apiRequest($endpoint, $method = 'GET', $data = null, $file = null) {
    $url = API_BASE_URL . $endpoint;
    $ch = curl_init();
    
    // Set common options
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'X-Auth-Token: ' . STUDENT_TOKEN
    ]);
    
    // Handle different HTTP methods
    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        
        if ($file) {
            // File upload
            $postData = [
                'file' => new CURLFile($file, mime_content_type($file), basename($file))
            ];
            curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
        } elseif ($data) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
        }
    }
    
    // Execute request
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        return ['error' => $error, 'http_code' => 0];
    }
    
    return [
        'data' => json_decode($response, true),
        'http_code' => $httpCode,
        'raw' => $response
    ];
}

/**
 * Check API health
 */
function checkHealth() {
    echo "=== Checking API Health ===\n";
    $result = apiRequest('/health');
    
    if ($result['http_code'] === 200) {
        echo "[OK] API is healthy\n";
        echo "Response: " . json_encode($result['data'], JSON_PRETTY_PRINT) . "\n";
    } else {
        echo "[FAIL] API health check failed\n";
        echo "HTTP Code: " . $result['http_code'] . "\n";
    }
    echo "\n";
}

/**
 * Upload a file
 */
function uploadFile($filepath) {
    echo "=== Uploading File ===\n";
    
    if (!file_exists($filepath)) {
        echo "[FAIL] File not found: $filepath\n\n";
        return false;
    }
    
    echo "File: " . basename($filepath) . "\n";
    echo "Size: " . filesize($filepath) . " bytes\n";
    
    $result = apiRequest('/upload', 'POST', null, $filepath);
    
    if ($result['http_code'] === 201) {
        echo "[OK] Upload successful\n";
        echo "Response: " . json_encode($result['data'], JSON_PRETTY_PRINT) . "\n";
        return true;
    } else {
        echo "[FAIL] Upload failed\n";
        echo "HTTP Code: " . $result['http_code'] . "\n";
        echo "Response: " . $result['raw'] . "\n";
        return false;
    }
    echo "\n";
}

/**
 * List files
 */
function listFiles() {
    echo "=== Listing Files ===\n";
    $result = apiRequest('/list');
    
    if ($result['http_code'] === 200) {
        $files = $result['data']['files'];
        echo "[OK] Found " . count($files) . " files\n\n";
        
        if (count($files) > 0) {
            printf("%-30s %-15s %-20s\n", "Filename", "Size (bytes)", "Modified");
            echo str_repeat("-", 70) . "\n";
            
            foreach ($files as $file) {
                printf("%-30s %-15d %-20s\n", 
                    $file['name'], 
                    $file['size'],
                    date('Y-m-d H:i:s', $file['modified'])
                );
            }
        } else {
            echo "No files uploaded yet.\n";
        }
    } else {
        echo "[FAIL] Failed to list files\n";
        echo "HTTP Code: " . $result['http_code'] . "\n";
    }
    echo "\n";
}

/**
 * Download a file
 */
function downloadFile($filename, $savePath = null) {
    echo "=== Downloading File ===\n";
    echo "Filename: $filename\n";
    
    $url = API_BASE_URL . '/download/' . urlencode($filename);
    $ch = curl_init();
    
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'X-Auth-Token: ' . STUDENT_TOKEN
    ]);
    
    $content = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode === 200) {
        if ($savePath) {
            file_put_contents($savePath, $content);
            echo "[OK] Downloaded to: $savePath\n";
            echo "Size: " . strlen($content) . " bytes\n";
        } else {
            echo "[OK] Downloaded (not saved)\n";
            echo "Size: " . strlen($content) . " bytes\n";
        }
        return true;
    } else {
        echo "[FAIL] Download failed\n";
        echo "HTTP Code: $httpCode\n";
        return false;
    }
    echo "\n";
}

/**
 * Get storage quota information
 */
function getQuotaInfo() {
    echo "=== Storage Quota ===\n";
    $result = apiRequest('/list');
    
    if ($result['http_code'] === 200 && isset($result['data']['files'])) {
        $files = $result['data']['files'];
        $totalSize = array_sum(array_column($files, 'size'));
        $quotaMB = 500; // Default quota
        
        echo "Files: " . count($files) . "\n";
        echo "Used: " . number_format($totalSize / 1024 / 1024, 2) . " MB\n";
        echo "Quota: $quotaMB MB\n";
        echo "Available: " . number_format(($quotaMB * 1024 * 1024 - $totalSize) / 1024 / 1024, 2) . " MB\n";
        
        $percentage = ($totalSize / ($quotaMB * 1024 * 1024)) * 100;
        echo "Usage: " . number_format($percentage, 1) . "%\n";
    }
    echo "\n";
}

// ============================================================================
// MAIN PROGRAM - Examples of API usage
// ============================================================================

echo "\n";
echo "================================================================\n";
echo "  Android Course File API - PHP Client Example\n";
echo "================================================================\n";
echo "\n";

// Check if token is set
if (STUDENT_TOKEN === 'your_token_here') {
    echo "WARNING: Please set your student token in the script!\n";
    echo "Edit this file and replace 'your_token_here' with your actual token.\n\n";
    exit(1);
}

// Example 1: Check API Health
checkHealth();

// Example 2: List existing files
listFiles();

// Example 3: Get quota information
getQuotaInfo();

// Example 4: Upload a file (uncomment to test)
/*
// Create a test file
$testFile = '/tmp/test_upload.txt';
file_put_contents($testFile, "Hello from PHP! Uploaded at " . date('Y-m-d H:i:s'));
uploadFile($testFile);
unlink($testFile);
*/

// Example 5: Download a file (uncomment to test)
/*
downloadFile('test.txt', '/tmp/downloaded_test.txt');
*/

echo "================================================================\n";
echo "  Complete! Check the examples above.\n";
echo "================================================================\n";
echo "\n";

// ============================================================================
// INTEGRATION EXAMPLES
// ============================================================================

/**
 * Example: Batch upload files
 */
function batchUpload($directory) {
    echo "=== Batch Upload from Directory ===\n";
    $files = glob($directory . '/*');
    $uploaded = 0;
    $failed = 0;
    
    foreach ($files as $file) {
        if (is_file($file)) {
            echo "Uploading: " . basename($file) . "... ";
            if (uploadFile($file)) {
                $uploaded++;
            } else {
                $failed++;
            }
        }
    }
    
    echo "\nSummary:\n";
    echo "Uploaded: $uploaded\n";
    echo "Failed: $failed\n";
    echo "\n";
}

/**
 * Example: Create backup of all files
 */
function backupAllFiles($backupDir) {
    echo "=== Backing Up All Files ===\n";
    
    if (!is_dir($backupDir)) {
        mkdir($backupDir, 0755, true);
    }
    
    $result = apiRequest('/list');
    if ($result['http_code'] !== 200) {
        echo "[FAIL] Failed to list files\n";
        return;
    }
    
    $files = $result['data']['files'];
    echo "Found " . count($files) . " files to backup\n";
    
    foreach ($files as $file) {
        $savePath = $backupDir . '/' . $file['name'];
        echo "Downloading: " . $file['name'] . "... ";
        if (downloadFile($file['name'], $savePath)) {
            echo "[OK]\n";
        } else {
            echo "[FAIL]\n";
        }
    }
    
    echo "Backup complete!\n\n";
}

/**
 * Example: Check file exists before upload
 */
function safeUpload($filepath) {
    // First, list existing files
    $result = apiRequest('/list');
    if ($result['http_code'] !== 200) {
        return uploadFile($filepath);
    }
    
    $filename = basename($filepath);
    $existingFiles = array_column($result['data']['files'], 'name');
    
    if (in_array($filename, $existingFiles)) {
        echo "WARNING: File '$filename' already exists. ";
        echo "Overwriting...\n";
    }
    
    return uploadFile($filepath);
}

?>
