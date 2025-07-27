#!/bin/bash

# Script to copy generated MLB watchability markdown files to blog directory
# Usage: ./copy-to-blog.sh 2025-07-28

# Check if date argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <date>"
    echo "Example: $0 2025-07-28"
    exit 1
fi

DATE="$1"
SOURCE_FILE="mlb_what_to_watch_${DATE//-/_}.md"
BLOG_DIR="../blog-eleventy/content/blog/mlbw"
TARGET_FILE="$BLOG_DIR/$SOURCE_FILE"

# Check if source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "Error: Source file '$SOURCE_FILE' not found in current directory"
    exit 1
fi

# Check if blog directory exists
if [ ! -d "$BLOG_DIR" ]; then
    echo "Error: Blog directory '$BLOG_DIR' not found"
    echo "Make sure the blog-eleventy repository is in the parent directory"
    exit 1
fi

# Copy the file
cp "$SOURCE_FILE" "$TARGET_FILE"

if [ $? -eq 0 ]; then
    echo "Successfully copied '$SOURCE_FILE' to '$TARGET_FILE'"
else
    echo "Error: Failed to copy file"
    exit 1
fi