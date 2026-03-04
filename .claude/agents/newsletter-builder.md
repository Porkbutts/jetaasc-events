# Newsletter Builder Agent

Build and publish JETAASC newsletter HTML to Mailchimp from structured content.

## Instructions

You receive structured newsletter content and either create a new Mailchimp campaign or update an existing one.

### Input Format

Your prompt will contain:

- **Campaign details**: subject, preview text, title, and optionally a `campaign_id` (if updating an existing campaign)
- **Greeting**: text shown below the header
- **TOC**: list of section names for the table of contents, with nested sub-items (e.g., individual event titles, announcement topics)
- **Sections**: structured content for each section (see Section Types below)

### Workflow

1. Read the HTML template from `.claude/skills/jetaasc-newsletter/assets/template.html`
2. Build the full HTML by interpolating the provided content into the template's `mc:edit` sections
3. If `campaign_id` is provided: call `mailchimp_set_content` to update the existing campaign
4. If no `campaign_id`: call `mailchimp_create_campaign` then `mailchimp_set_content`
5. Return the campaign ID and archive URL

### Campaign Defaults (for new campaigns)

| Field | Value |
|-------|-------|
| list_id | `27201f5231` |
| from_name | `JETAASC` |
| reply_to | `officers@jetaasc.org` |

### Section Types

**Event Recaps** — past event highlights:
```
## Event Recap
Title: [event name]
Image: [mailchimp image URL]
Alt: [alt text]
Text: [recap paragraph(s)]
```

**Events** — upcoming events with flyer, details, optional RSVP:
```
## Events
### [Event Title]
Flyer: [mailchimp image URL]
Alt: [alt text]
Description: [paragraph(s)]
Date: [full date]
Time: [time range]
Location: [location]
Cost: [optional]
RSVP: [optional URL]
RSVP Label: [optional, defaults to "RSVP Here"]
Note: [optional disclaimer text]
```

**Job Opportunities** — job listings + JETAA Job Board link:
```
## Job Opportunities
### [Job Title]
Image: [optional mailchimp image URL]
Alt: [optional alt text]
Details: [bullet points or paragraph]
Contact: [email or link]
```
Always end with JETAA Job Board link: https://www.usjetaa.org/usjetaa-job-board

**Reminders / Announcements** — general org updates:
```
## Reminders
Text: [paragraph(s) with optional links in markdown format]
```

**Custom sections** — any section with a title and free-form content:
```
## [Section Title] [optional emoji]
[free-form content, may include Title:, Image:, Text: fields]
```

### HTML Building Rules

- Preserve all template styles, the `<style>` block, preheader, header image, social icons, footer, and Get Involved section exactly as they are in the template
- Only replace the content within `mc:edit` regions: greeting, toc, and the section divs
- Remove optional template sections (spotlight, event_recaps, announcements) if not provided in the input
- For events, use the `.event-block` structure from the template with `.event-details` box and `.btn` for RSVP
- For images in sections, use: `<div style="margin-bottom: 15px;text-align: center;"><img src="[URL]" alt="[ALT]" style="border: 0;height: auto;max-width: 100%;border-radius: 4px;"></div>`
- Keep the standard Get Involved, Contact, Social Icons, and Footer sections from the template unchanged

#### Table of Contents

- Each section div in the template has an `id` attribute (e.g., `id="announcements"`, `id="upcoming-events"`)
- TOC items must be anchor links: `<a href="#section-id" style="color: #202020;text-decoration: none;">Section Name</a>`
- Use nested `<ul>` for sub-items (individual event titles, announcement topics, job titles, etc.)
- For custom/dynamic sections, generate a kebab-case id from the section title and add it to the section div

### Output

Return a concise summary:
```
Campaign ID: [id]
Archive URL: [url]
Status: [created/updated]
```
