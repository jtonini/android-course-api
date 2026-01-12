#!/bin/bash
#
# Android Course API - Cleanup Script
# Removes student data at end of semester
#
# Usage: ./cleanup.sh [--dry-run] [--backup] [--force]
#   --dry-run : Show what would be deleted without actually deleting
#   --backup  : Create backup before deleting
#   --force   : Skip confirmation prompt
#
# Recommended workflow:
#   1. Run with --dry-run first to see what will be deleted
#   2. Run with --backup to archive data before deletion
#   3. Run with --force for automated cron jobs
#

# Configuration
UPLOAD_DIR="/scratch/android_course/uploads"
BACKUP_DIR="/scratch/android_course/backups"
LOG_DIR="/scratch/android_course/logs"

# Parse arguments
DRY_RUN=false
BACKUP=false
FORCE=false

for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --backup) BACKUP=true ;;
        --force) FORCE=true ;;
    esac
done

# Calculate current usage
if [ -d "$UPLOAD_DIR" ]; then
    TOTAL_SIZE=$(du -sh "$UPLOAD_DIR" 2>/dev/null | cut -f1)
    STUDENT_COUNT=$(find "$UPLOAD_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
    FILE_COUNT=$(find "$UPLOAD_DIR" -type f | wc -l)
else
    echo "Upload directory does not exist: $UPLOAD_DIR"
    exit 1
fi

echo "=========================================="
echo "Android Course API - Cleanup Script"
echo "=========================================="
echo ""
echo "Current Status:"
echo "  Upload Directory: $UPLOAD_DIR"
echo "  Total Size: $TOTAL_SIZE"
echo "  Students: $STUDENT_COUNT"
echo "  Files: $FILE_COUNT"
echo ""

# List students and their usage
if [ "$STUDENT_COUNT" -gt 0 ]; then
    echo "Student Usage:"
    for student_dir in "$UPLOAD_DIR"/*/; do
        if [ -d "$student_dir" ]; then
            student=$(basename "$student_dir")
            size=$(du -sh "$student_dir" 2>/dev/null | cut -f1)
            files=$(find "$student_dir" -type f | wc -l)
            echo "  $student: $size ($files files)"
        fi
    done
    echo ""
fi

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would delete:"
    echo "  - All files in $UPLOAD_DIR"
    echo "  - $FILE_COUNT files from $STUDENT_COUNT students"
    echo ""
    echo "To actually delete, run without --dry-run"
    exit 0
fi

# Confirmation prompt (unless --force)
if [ "$FORCE" = false ]; then
    echo "WARNING: This will permanently delete all student data!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
fi

# Create backup if requested
if [ "$BACKUP" = true ]; then
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/android_course_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    echo "Creating backup: $BACKUP_FILE"
    tar -czf "$BACKUP_FILE" -C "$UPLOAD_DIR" . 2>/dev/null
    
    if [ $? -eq 0 ]; then
        BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
        echo "Backup created successfully ($BACKUP_SIZE)"
    else
        echo "ERROR: Backup failed!"
        exit 1
    fi
fi

# Delete student data
echo ""
echo "Deleting student data..."
rm -rf "$UPLOAD_DIR"/*

if [ $? -eq 0 ]; then
    echo "All student data deleted successfully."
else
    echo "ERROR: Failed to delete some files!"
    exit 1
fi

# Rotate log file
if [ -f "$LOG_DIR/api.log" ]; then
    ARCHIVE_LOG="$LOG_DIR/api_$(date +%Y%m%d_%H%M%S).log"
    mv "$LOG_DIR/api.log" "$ARCHIVE_LOG"
    gzip "$ARCHIVE_LOG"
    echo "Log file archived to ${ARCHIVE_LOG}.gz"
    touch "$LOG_DIR/api.log"
fi

echo ""
echo "Cleanup complete!"
echo ""
echo "Summary:"
echo "  Students removed: $STUDENT_COUNT"
echo "  Files deleted: $FILE_COUNT"
echo "  Space freed: $TOTAL_SIZE"
if [ "$BACKUP" = true ]; then
    echo "  Backup location: $BACKUP_FILE"
fi
