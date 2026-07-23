# Wix Blog Publishing

## Site ID
`68b9accd-a629-4996-a8e3-bb4a7ed9a186`

## Category ID for "Upcoming"
`b2dba553-f903-4dd8-859a-94afe80730e3`

## Common Tags
| Tag | ID |
|-----|-----|
| shinnenkai | a93eb3fa-3212-4058-abca-9168f0e9de6f |
| bonenkai | 6b7de19c-0aed-477c-80b2-48a2ff277f0d |
| networking | f06e35c4-925c-4049-9a36-822f3175e952 |
| Japanese | a257ee18-8ee3-44e5-83e3-5b72995c7ffb |
| los angeles | 8787c4f7-f690-4785-9382-fd8b89439a34 |
| orange county | bd21c0d1-659e-40c4-9d12-663b11a5c489 |
| san diego | e058cb3c-3073-4b67-8434-3713167e939e |
| little tokyo | e5adf867-9283-4d80-8b08-a52ef97c3f75 |
| karaoke | 8098c398-8293-46f2-b365-e4019223c64e |
| movie night | 5f49e036-7f64-4714-950c-857ab3f5aa0d |
| natsukashii-kai | bcad48d3-a0a9-4e18-bd3d-7181af411a6d |
| nihongo dake dinner | 0c38eb38-27e2-475c-999f-dd01291a5434 |
| boba banter | 4e6e89fd-adb1-48e6-bc2a-dba8e34155c3 |
| welcome back | 91b5fce7-7329-4332-a776-5521fca53b12 |
| online event | 36942460-f118-4126-9ba0-59bed75c4db8 |
| virtual | 82463a96-f9da-4061-b0a1-cffdc0f03cea |

### Creating New Tags
If the event needs a tag that doesn't exist, create it first:
```
POST https://www.wixapis.com/blog/v3/tags
Body: {"tag": {"label": "new tag name", "language": "en"}}
```
The response includes the new tag's `id` to use in the blog post's `tagIds` array.

### Listing All Tags
To find existing tags or check if a tag exists:
```
GET https://www.wixapis.com/blog/v3/tags
```

## Uploading Images
Before creating a blog post, upload the event flyer to Wix Media Manager:
```
POST https://www.wixapis.com/site-media/v1/files/import
Body: {"url": "<image-url>", "displayName": "<filename>.png", "mimeType": "image/png"}
```
Use the returned `file.id` in the blog post.

## API Endpoints

**Create Draft:**
```
POST https://www.wixapis.com/blog/v3/draft-posts
```

**Update Draft:**
```
PATCH https://www.wixapis.com/blog/v3/draft-posts/{draftPostId}
Body: {"draftPost": {"id": "{draftPostId}", "richContent": {...}}}
```
Use this to apply user feedback/changes before publishing.

**Publish Draft:**
```
POST https://www.wixapis.com/blog/v3/draft-posts/{draftPostId}/publish
```

## Draft Preview Link
After creating a draft, share this link for review:
```
https://manage.wix.com/dashboard/68b9accd-a629-4996-a8e3-bb4a7ed9a186/blog/{draftPostId}/edit
```

## Publishing Steps

1. Upload flyer to Wix Media Manager (Import File endpoint)
2. Select appropriate tags by analyzing event title, description, and location
3. Create draft post with title, image, richContent, category, and tags
4. Share draft preview link for user confirmation
5. If user has feedback, update draft via PATCH endpoint. Repeat until approved.
6. On approval, publish draft
7. Return published post URL: `https://www.jetaasc.org/post/{slug}`

## Ricos JSON Format

Blog post rich content uses the Ricos JSON structure.

### Node Examples

#### Image Node
```json
{
  "type": "IMAGE",
  "id": "img1",
  "nodes": [],
  "imageData": {
    "containerData": {
      "width": {"size": "CONTENT"},
      "alignment": "CENTER"
    },
    "image": {
      "src": {"id": "wix-media-file-id"},
      "width": 800,
      "height": 600
    },
    "altText": "Event flyer description"
  }
}
```

#### Paragraph with Plain Text
```json
{
  "type": "PARAGRAPH",
  "id": "p1",
  "nodes": [
    {
      "type": "TEXT",
      "id": "t1",
      "textData": {
        "text": "Your text here",
        "decorations": []
      }
    }
  ],
  "paragraphData": {}
}
```

#### Bold Text
```json
{
  "type": "TEXT",
  "id": "t1",
  "textData": {
    "text": "Bold text",
    "decorations": [{"type": "BOLD"}]
  }
}
```

#### Italic Text
```json
{
  "type": "TEXT",
  "id": "t1",
  "textData": {
    "text": "Italic text",
    "decorations": [{"type": "ITALIC"}]
  }
}
```

#### Link
```json
{
  "type": "TEXT",
  "id": "t1",
  "textData": {
    "text": "Click here",
    "decorations": [
      {
        "type": "LINK",
        "linkData": {
          "link": {"url": "https://example.com"}
        }
      }
    ]
  }
}
```

#### Heading Node
```json
{
  "type": "HEADING",
  "id": "h1",
  "nodes": [
    {
      "type": "TEXT",
      "id": "t1",
      "textData": {
        "text": "Section Title",
        "decorations": []
      }
    }
  ],
  "headingData": {
    "level": 2
  }
}
```

#### Empty Paragraph (Visual Break / Spacing)
To add visual spacing between sections, use an empty paragraph node with no text nodes:
```json
{
  "type": "PARAGRAPH",
  "id": "spacer1",
  "nodes": [],
  "paragraphData": {}
}
```

**Important:** Without empty paragraphs between sections, content will appear "squished" with no visual separation. Add empty paragraphs:
- After the image
- Between description paragraphs
- Before the What/When/Where/Cost section
- After the What/When/Where/Cost section (before closing text)

### Example: Complete Event Post

```json
{
  "draftPost": {
    "title": "JETAASC Shinenkai 2026",
    "categoryIds": ["b2dba553-f903-4dd8-859a-94afe80730e3"],
    "tagIds": ["a93eb3fa-3212-4058-abca-9168f0e9de6f"],
    "richContent": {
      "nodes": [
        {
          "type": "IMAGE",
          "id": "img1",
          "nodes": [],
          "imageData": {
            "containerData": {"width": {"size": "CONTENT"}, "alignment": "CENTER"},
            "image": {"src": {"id": "media-file-id"}, "width": 800, "height": 600},
            "altText": "JETAASC Shinenkai 2026 Event Flyer"
          }
        },
        {"type": "PARAGRAPH", "id": "spacer1", "nodes": [], "paragraphData": {}},
        {
          "type": "PARAGRAPH",
          "id": "p1",
          "nodes": [
            {"type": "TEXT", "id": "t1", "textData": {"text": "Join us for our annual New Year celebration!", "decorations": []}}
          ],
          "paragraphData": {}
        },
        {"type": "PARAGRAPH", "id": "spacer2", "nodes": [], "paragraphData": {}},
        {
          "type": "PARAGRAPH",
          "id": "p2",
          "nodes": [
            {"type": "TEXT", "id": "t2", "textData": {"text": "What: ", "decorations": [{"type": "BOLD"}]}},
            {"type": "TEXT", "id": "t3", "textData": {"text": "Shinenkai (New Year Party)", "decorations": []}}
          ],
          "paragraphData": {}
        },
        {
          "type": "PARAGRAPH",
          "id": "p3",
          "nodes": [
            {"type": "TEXT", "id": "t4", "textData": {"text": "When: ", "decorations": [{"type": "BOLD"}]}},
            {"type": "TEXT", "id": "t5", "textData": {"text": "Saturday, January 25, 2026 at 6:00 PM", "decorations": []}}
          ],
          "paragraphData": {}
        },
        {
          "type": "PARAGRAPH",
          "id": "p4",
          "nodes": [
            {"type": "TEXT", "id": "t6", "textData": {"text": "Where: ", "decorations": [{"type": "BOLD"}]}},
            {"type": "TEXT", "id": "t7", "textData": {"text": "Little Tokyo, Los Angeles", "decorations": []}}
          ],
          "paragraphData": {}
        },
        {
          "type": "PARAGRAPH",
          "id": "p5",
          "nodes": [
            {"type": "TEXT", "id": "t8", "textData": {"text": "Cost: ", "decorations": [{"type": "BOLD"}]}},
            {"type": "TEXT", "id": "t9", "textData": {"text": "$25 members / $30 non-members", "decorations": []}}
          ],
          "paragraphData": {}
        },
        {
          "type": "PARAGRAPH",
          "id": "p6",
          "nodes": [
            {"type": "TEXT", "id": "t10", "textData": {"text": "RSVP: ", "decorations": [{"type": "BOLD"}]}},
            {"type": "TEXT", "id": "t11", "textData": {"text": "Click here to register", "decorations": [{"type": "LINK", "linkData": {"link": {"url": "https://forms.google.com/..."}}}]}}
          ],
          "paragraphData": {}
        },
        {"type": "PARAGRAPH", "id": "spacer3", "nodes": [], "paragraphData": {}},
        {
          "type": "PARAGRAPH",
          "id": "p7",
          "nodes": [
            {"type": "TEXT", "id": "t12", "textData": {"text": "We hope to see you there!", "decorations": []}}
          ],
          "paragraphData": {}
        }
      ]
    }
  }
}
```
