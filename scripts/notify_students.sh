#!/bin/bash
#
# Android Course API - Student Notification Script
# Sends email notifications to students about data deletion
#
# Usage: ./notify_students.sh [--dry-run] [--days N]
#   --dry-run : Show what emails would be sent without sending
#   --days N  : Days until deletion (default: 30)
#
# This script requires a student list file with format:
#   netid,email
#
# Example cron entries:
#   # 30 days before deletion
#   0 9 15 5 * /scratch/android_course/app/scripts/notify_students.sh --days 30
#   # 7 days before deletion  
#   0 9 8 6 * /scratch/android_course/app/scripts/notify_students.sh --days 7
#

# Configuration
UPLOAD_DIR="/scratch/android_course/uploads"
STUDENT_LIST="/scratch/android_course/students.csv"
COURSE_NAME="CS XXX - Android Programming"
INSTRUCTOR_NAME="Prof. Ware"
INSTRUCTOR_EMAIL="sware@richmond.edu"
ADMIN_EMAIL="jtonini@richmond.edu"
API_URL="https://spiderweb.richmond.edu/android"

# Parse arguments
DRY_RUN=false
DAYS_UNTIL_DELETE=30

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --days) DAYS_UNTIL_DELETE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Calculate deletion date
DELETE_DATE=$(date -d "+${DAYS_UNTIL_DELETE} days" "+%B %d, %Y")

echo "=========================================="
echo "Android Course API - Student Notification"
echo "=========================================="
echo ""
echo "Deletion Date: $DELETE_DATE ($DAYS_UNTIL_DELETE days)"
echo ""

# Check if upload directory exists
if [ ! -d "$UPLOAD_DIR" ]; then
    echo "No upload directory found. Nothing to notify about."
    exit 0
fi

# Get list of students with data
STUDENTS_WITH_DATA=$(find "$UPLOAD_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)

if [ -z "$STUDENTS_WITH_DATA" ]; then
    echo "No student data found. Nothing to notify about."
    exit 0
fi

echo "Students with data:"
for student in $STUDENTS_WITH_DATA; do
    size=$(du -sh "$UPLOAD_DIR/$student" 2>/dev/null | cut -f1)
    files=$(find "$UPLOAD_DIR/$student" -type f | wc -l)
    echo "  $student: $size ($files files)"
done
echo ""

# Function to send notification email
send_notification() {
    local netid=$1
    local email=$2
    local size=$3
    local file_count=$4
    
    local subject="[ACTION REQUIRED] Your Android Course Files Will Be Deleted on $DELETE_DATE"
    
    local body="Dear Student,

This is a reminder that your files stored on the Android Course server will be permanently deleted on $DELETE_DATE ($DAYS_UNTIL_DELETE days from now).

YOUR DATA:
  - Student ID: $netid
  - Files stored: $file_count
  - Total size: $size

ACTION REQUIRED:
Please download any files you wish to keep before the deletion date.

To download your files, you can use the course API:
  GET $API_URL/files/$netid     (list your files)
  GET $API_URL/download/$netid/<filename>  (download a file)

If you have any questions, please contact:
  - Instructor: $INSTRUCTOR_NAME ($INSTRUCTOR_EMAIL)
  - Technical Support: $ADMIN_EMAIL

This is an automated message from the $COURSE_NAME file server.
"
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would send email to: $email"
        echo "  Subject: $subject"
        echo ""
    else
        echo "$body" | mail -s "$subject" "$email"
        echo "Email sent to: $email ($netid)"
    fi
}

# Process each student
echo "Sending notifications..."
echo ""

# If student list file exists, use it for email addresses
if [ -f "$STUDENT_LIST" ]; then
    for student in $STUDENTS_WITH_DATA; do
        # Look up email in student list (format: netid,email)
        email=$(grep "^${student}," "$STUDENT_LIST" | cut -d',' -f2)
        
        if [ -z "$email" ]; then
            # Default to netid@richmond.edu if not in list
            email="${student}@richmond.edu"
        fi
        
        size=$(du -sh "$UPLOAD_DIR/$student" 2>/dev/null | cut -f1)
        file_count=$(find "$UPLOAD_DIR/$student" -type f | wc -l)
        
        send_notification "$student" "$email" "$size" "$file_count"
    done
else
    echo "Note: Student list file not found ($STUDENT_LIST)"
    echo "Using default email format: netid@richmond.edu"
    echo ""
    
    for student in $STUDENTS_WITH_DATA; do
        email="${student}@richmond.edu"
        size=$(du -sh "$UPLOAD_DIR/$student" 2>/dev/null | cut -f1)
        file_count=$(find "$UPLOAD_DIR/$student" -type f | wc -l)
        
        send_notification "$student" "$email" "$size" "$file_count"
    done
fi

echo ""
echo "Notification complete!"

# Send summary to admin
if [ "$DRY_RUN" = false ]; then
    STUDENT_COUNT=$(echo "$STUDENTS_WITH_DATA" | wc -w)
    SUMMARY="Android Course Notification Summary

Date: $(date)
Deletion Date: $DELETE_DATE
Students Notified: $STUDENT_COUNT

Students with data:
$(for s in $STUDENTS_WITH_DATA; do
    size=$(du -sh "$UPLOAD_DIR/$s" 2>/dev/null | cut -f1)
    echo "  - $s: $size"
done)
"
    echo "$SUMMARY" | mail -s "[INFO] Android Course - Deletion Notifications Sent" "$ADMIN_EMAIL"
    echo "Summary sent to admin: $ADMIN_EMAIL"
fi
