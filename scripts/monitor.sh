#!/bin/bash
#
# Android Course API - Monitoring Script
# Checks disk usage and sends email alerts if thresholds are exceeded
#
# Usage: ./monitor.sh [--email] [--quiet]
#   --email  : Send email alert if thresholds exceeded
#   --quiet  : Only output if there are warnings
#
# Recommended cron entry (daily at 8am):
#   0 8 * * * /scratch/android_course/app/scripts/monitor.sh --email
#

# Configuration
UPLOAD_DIR="/scratch/android_course/uploads"
LOG_FILE="/scratch/android_course/logs/api.log"

# Thresholds (percentage)
COURSE_WARN_THRESHOLD=80
STUDENT_WARN_THRESHOLD=90

# Email settings
ADMIN_EMAIL="jtonini@richmond.edu"
INSTRUCTOR_EMAIL="sware@richmond.edu"

# Quotas (must match app.py)
PER_STUDENT_QUOTA_MB=500
TOTAL_COURSE_QUOTA_GB=15

# Parse arguments
SEND_EMAIL=false
QUIET=false
for arg in "$@"; do
    case $arg in
        --email) SEND_EMAIL=true ;;
        --quiet) QUIET=true ;;
    esac
done

# Calculate sizes
TOTAL_COURSE_QUOTA_BYTES=$((TOTAL_COURSE_QUOTA_GB * 1024 * 1024 * 1024))
PER_STUDENT_QUOTA_BYTES=$((PER_STUDENT_QUOTA_MB * 1024 * 1024))

# Get current usage
if [ -d "$UPLOAD_DIR" ]; then
    TOTAL_USAGE=$(du -sb "$UPLOAD_DIR" 2>/dev/null | cut -f1)
    STUDENT_COUNT=$(find "$UPLOAD_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
else
    TOTAL_USAGE=0
    STUDENT_COUNT=0
fi

# Calculate percentage
if [ "$TOTAL_COURSE_QUOTA_BYTES" -gt 0 ]; then
    COURSE_PERCENT=$((TOTAL_USAGE * 100 / TOTAL_COURSE_QUOTA_BYTES))
else
    COURSE_PERCENT=0
fi

# Format sizes for display
format_size() {
    local bytes=$1
    if [ "$bytes" -ge 1073741824 ]; then
        echo "$(echo "scale=1; $bytes / 1073741824" | bc) GB"
    elif [ "$bytes" -ge 1048576 ]; then
        echo "$(echo "scale=1; $bytes / 1048576" | bc) MB"
    elif [ "$bytes" -ge 1024 ]; then
        echo "$(echo "scale=1; $bytes / 1024" | bc) KB"
    else
        echo "$bytes B"
    fi
}

# Build report
WARNINGS=""
REPORT="Android Course API - Storage Report
Generated: $(date)
========================================

Course Storage:
  Total Used: $(format_size $TOTAL_USAGE) / ${TOTAL_COURSE_QUOTA_GB} GB (${COURSE_PERCENT}%)
  Students: $STUDENT_COUNT

"

# Check course threshold
if [ "$COURSE_PERCENT" -ge "$COURSE_WARN_THRESHOLD" ]; then
    WARNINGS="${WARNINGS}WARNING: Course storage at ${COURSE_PERCENT}% (threshold: ${COURSE_WARN_THRESHOLD}%)\n"
fi

# Check individual students
if [ -d "$UPLOAD_DIR" ] && [ "$STUDENT_COUNT" -gt 0 ]; then
    REPORT="${REPORT}Per-Student Usage (sorted by size):
----------------------------------------
"
    
    # Get student usage, sorted by size
    while IFS= read -r line; do
        SIZE=$(echo "$line" | cut -f1)
        STUDENT=$(basename "$(echo "$line" | cut -f2)")
        
        if [ "$PER_STUDENT_QUOTA_BYTES" -gt 0 ]; then
            PERCENT=$((SIZE * 100 / PER_STUDENT_QUOTA_BYTES))
        else
            PERCENT=0
        fi
        
        FILE_COUNT=$(find "$UPLOAD_DIR/$STUDENT" -type f 2>/dev/null | wc -l)
        
        REPORT="${REPORT}  $STUDENT: $(format_size $SIZE) (${PERCENT}%) - $FILE_COUNT files\n"
        
        # Check student threshold
        if [ "$PERCENT" -ge "$STUDENT_WARN_THRESHOLD" ]; then
            WARNINGS="${WARNINGS}WARNING: Student '$STUDENT' at ${PERCENT}% quota\n"
        fi
        
    done < <(du -sb "$UPLOAD_DIR"/*/ 2>/dev/null | sort -rn)
fi

# Add log file info
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(stat -c%s "$LOG_FILE" 2>/dev/null || echo "0")
    REPORT="${REPORT}
Log File:
  Size: $(format_size $LOG_SIZE)
  Location: $LOG_FILE
"
fi

# Add warnings to report
if [ -n "$WARNINGS" ]; then
    REPORT="${REPORT}
========================================
ALERTS:
$(echo -e "$WARNINGS")
"
fi

# Output report
if [ "$QUIET" = false ] || [ -n "$WARNINGS" ]; then
    echo -e "$REPORT"
fi

# Send email if requested and there are warnings
if [ "$SEND_EMAIL" = true ] && [ -n "$WARNINGS" ]; then
    SUBJECT="[ALERT] Android Course API - Storage Warning"
    echo -e "$REPORT" | mail -s "$SUBJECT" "$ADMIN_EMAIL" "$INSTRUCTOR_EMAIL"
    echo "Alert email sent to $ADMIN_EMAIL and $INSTRUCTOR_EMAIL"
fi

# Exit with warning code if thresholds exceeded
if [ -n "$WARNINGS" ]; then
    exit 1
fi

exit 0
