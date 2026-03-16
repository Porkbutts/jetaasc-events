# Google Form RSVP Creation

Create forms from scratch (not from template) to avoid org-only access restrictions.

## RSVP Forms Folder
`1FclzeLnrIzuMUDFLi05wTqjPV7LMQ4kw`

### Year Subfolders
| Year | Folder ID |
|------|-----------|
| 2026 | `1s5wfZK_vr1sU2dLh6qdCbnJLFiLJ3e2g` |
| 2025 | `1e0mJVwelsCzGcF2YRA6ij1lvUzRlZGq7` |
| 2024 | `1jvCTFXdjnEiUdhDeW_-suTG0_tQvSMtB` |
| 2023 | `10ss9tQS9KWkScjQ8CDI7IzAI7XVYgb1f` |

## Naming Convention
`MM-DD-YYYY Event Name at Venue, City`

Example: `03-28-2026 Spring Social at Far Bar, Little Tokyo`

## Steps

### 1. Create empty form
```bash
gws forms forms create --json '{"info": {"title": "EVENT_NAME RSVP", "documentTitle": "MM-DD-YYYY Event Name at Venue, City"}}'
```
The response includes `formId` and `responderUri`.

### 2. Add description, header image, and questions
Use a single `batchUpdate` call with all requests:

```bash
gws forms forms batchUpdate --params '{"formId": "NEW_FORM_ID"}' --json '{"requests": [
  {"updateFormInfo": {"info": {"description": "What: ...\nWhen: ...\nWhere: ...\nCost: ...\nContact: events@jetaasc.org"}, "updateMask": "description"}},
  {"createItem": {"item": {"title": "Event Flyer", "imageItem": {"image": {"sourceUri": "FLYER_PUBLIC_URL", "altText": "Event flyer"}}}, "location": {"index": 0}}},
  {"createItem": {"item": {"title": "First Name", "questionItem": {"question": {"required": true, "textQuestion": {}}}}, "location": {"index": 1}}},
  ...
]}'
```

#### Full question list
| Index | Title | Type | Required | Notes |
|-------|-------|------|----------|-------|
| 0 | Event Flyer | Image item | — | `imageItem` with `sourceUri` pointing to public flyer URL. Use creative `altText`. |
| 1 | First Name | Text | Yes | |
| 2 | Last Name | Text | Yes | |
| 3 | Can you attend? | Radio: Yes / Maybe / No | Yes | |
| 4 | Are you a JET alum or friend of JET? | Radio: JET Alum / Friend of JET | Yes | |
| 5 | Where was your JET placement prefecture? | Text | Yes | Description: `Enter "n/a" if you were not on JET` |
| 6 | What years were you on JET? | Text | Yes | Description: `Format your answer like "2015-2018" or enter "n/a" if you were not on JET` |
| 7 | Bringing any additional people? | Scale 1-5 | No | Description: `If not, please leave this field blank.` |
| 8 | Any dietary restrictions we should be aware of? | Text | No | |
| 9 | How did you hear about this event? | Radio: Website / Facebook / Newsletter / Discord / Other | No | |
| 10 | Comments and/or questions | Paragraph text | No | |

### 3. Move to year folder
```bash
gws drive files get --params '{"fileId": "FORM_ID", "fields": "id,parents", "supportsAllDrives": true}'
gws drive files update --params '{"fileId": "FORM_ID", "addParents": "YEAR_FOLDER_ID", "removeParents": "CURRENT_PARENT", "supportsAllDrives": true, "fields": "id,name,parents"}'
```

### 4. Open access (required — Workspace defaults to org-only)
```bash
gws drive permissions create --params '{"fileId": "FORM_ID", "supportsAllDrives": true}' --json '{"type": "anyone", "role": "writer"}'
```

### 5. Publish
```bash
gws forms forms setPublishSettings --params '{"formId": "FORM_ID"}' --json '{"publishSettings": {"publishState": {"isPublished": true, "isAcceptingResponses": true}}, "updateMask": "*"}'
```

### 6. Remind user
Remind the user to verify the form is open to anyone (not just the org). The Google Workspace domain may restrict forms by default. The user must manually check: Form Settings > Responses > uncheck "Restrict to users in [org]".

### 7. Use the RSVP link
Use the `responderUri` from step 1 as the RSVP link across all other platforms.
