---
name: wix-blog-archiver
description: |
  Archive past JETAASC events by moving blog posts from "Upcoming" to "Past Events" category.
  Use when: user wants to archive events, move past events, clean up upcoming events,
  or asks to update event categories based on dates. Triggers: "archive events",
  "move past events", "update event categories", "clean up upcoming".
---

# Wix Blog Archiver

Move JETAASC blog posts from "Upcoming" to "Past Events" when the event date has passed.

## Configuration

- **Site ID**: `68b9accd-a629-4996-a8e3-bb4a7ed9a186`
- **Upcoming Category ID**: `b2dba553-f903-4dd8-859a-94afe80730e3`
- **Past Events Category ID**: `2f2e8635-319f-4213-8dd1-8f44bf1254b7`

## Workflow

### Step 1: List Upcoming Events

Query posts in "Upcoming" category with content text:

```
GET https://www.wixapis.com/blog/v3/posts?categoryIds=b2dba553-f903-4dd8-859a-94afe80730e3&fieldsets=CONTENT_TEXT
```

Use `mcp__wix__CallWixSiteAPI` with site ID above.

### Step 2: Extract Event Dates

For each post, analyze `contentText` to find the event date. Look for:
- Full dates: "Saturday, January 31, 2026", "December 13, 2025"
- Partial dates: "January 31" (infer year from context/post date)
- Keywords: "Date:", "When:" followed by date

Flag posts with unclear dates for manual review.

### Step 3: Show Preview

Display posts to be archived:

| Title | Event Date | Status |
|-------|------------|--------|
| ... | ... | PAST / UPCOMING / UNKNOWN |

**Ask user to confirm before making changes.**

### Step 4: Archive Confirmed Posts

For each past event:

1. Update draft category:
```
PATCH https://www.wixapis.com/blog/v3/draft-posts/{postId}
Body: {"draftPost": {"id": "{postId}", "categoryIds": ["2f2e8635-319f-4213-8dd1-8f44bf1254b7"]}}
```

2. Publish:
```
POST https://www.wixapis.com/blog/v3/draft-posts/{postId}/publish
Body: {}
```

### Step 5: Report Results

Summarize: posts archived, posts skipped (upcoming or unknown date).
