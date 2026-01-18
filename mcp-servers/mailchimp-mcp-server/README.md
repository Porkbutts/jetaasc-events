# Mailchimp MCP Server

An MCP (Model Context Protocol) server for managing Mailchimp email campaigns. Enables AI assistants to create, manage, schedule, and send email campaigns through Mailchimp's API.

## Setup

### Prerequisites

- Node.js 18+
- Mailchimp account with API access

### Get Your API Key

1. Log into Mailchimp
2. Go to **Account** > **Extras** > **API keys**
3. Create or copy your API key (format: `abc123xyz-us6`)

### Installation

```bash
npm install
npm run build
```

### Configuration

Set the `MAILCHIMP_API_KEY` environment variable:

```bash
export MAILCHIMP_API_KEY="your-api-key-us6"
```

Or add to your Claude Code MCP config:

```json
{
  "mcpServers": {
    "mailchimp": {
      "command": "node",
      "args": ["/path/to/mcp-servers/mailchimp-mcp-server/dist/index.js"],
      "env": {
        "MAILCHIMP_API_KEY": "your-api-key-us6"
      }
    }
  }
}
```

## Available Tools

### Audience Management

| Tool | Description |
|------|-------------|
| `mailchimp_list_audiences` | List all audiences (lists) with IDs and subscriber counts |

### Campaign Management

| Tool | Description |
|------|-------------|
| `mailchimp_list_campaigns` | List campaigns (optionally filter by status) |
| `mailchimp_get_campaign` | Get campaign metadata (settings, recipients, status) |
| `mailchimp_create_campaign` | Create a new campaign |
| `mailchimp_delete_campaign` | Delete a draft/paused campaign (permanent) |

### Content Management

| Tool | Description |
|------|-------------|
| `mailchimp_get_content` | Get campaign HTML and plain text content |
| `mailchimp_set_content` | Set campaign content (HTML or template) |

### Sending & Scheduling

| Tool | Description |
|------|-------------|
| `mailchimp_send_test` | Send test email (up to 5 addresses) |
| `mailchimp_send_campaign` | Send campaign immediately to full audience |
| `mailchimp_schedule_campaign` | Schedule campaign for future send |
| `mailchimp_unschedule_campaign` | Cancel scheduled send, return to draft |

### File Management

| Tool | Description |
|------|-------------|
| `mailchimp_upload_image` | Upload image to File Manager (max 1MB) |
| `mailchimp_list_files` | List files in File Manager |

### Template Management

| Tool | Description |
|------|-------------|
| `mailchimp_list_templates` | List templates (filter by type: user, base, gallery) |
| `mailchimp_get_template` | Get template metadata |
| `mailchimp_create_template` | Create template from HTML |
| `mailchimp_update_template` | Update template name/HTML |
| `mailchimp_delete_template` | Delete a user-created template (permanent) |
| `mailchimp_get_template_default_content` | Get template's editable sections |

## Typical Workflow

### Create and Send a Campaign

```
1. mailchimp_list_audiences         → Get list_id
2. mailchimp_create_campaign        → Create campaign with audience, subject, from
3. mailchimp_set_content            → Set HTML content
4. mailchimp_send_test              → Verify with test email
5. mailchimp_send_campaign          → Send to full audience
   OR
   mailchimp_schedule_campaign      → Schedule for later
```

### Modify Existing Campaign Content

```
1. mailchimp_list_campaigns         → Find campaign ID
2. mailchimp_get_content            → Get current HTML
3. mailchimp_set_content            → Update with modified HTML
```

### Create and Use a Template

```
1. mailchimp_create_template        → Create template from HTML
2. mailchimp_create_campaign        → Create campaign
3. mailchimp_set_content            → Apply template using template_id
```

### Use Existing Template with Custom Sections

```
1. mailchimp_list_templates              → Find template ID
2. mailchimp_get_template_default_content → See editable sections
3. mailchimp_create_campaign             → Create campaign
4. mailchimp_set_content                 → Apply template with section overrides
```

## Tool Details

### mailchimp_schedule_campaign

Schedule a campaign for a specific date/time.

**Parameters:**
- `campaign_id` (required): Campaign ID
- `schedule_time` (required): ISO 8601 format (e.g., `2025-02-15T18:00:00+00:00`)
- `timewarp` (optional): Send based on subscriber timezone (paid plans)
- `batch_delivery` (optional): Spread delivery over batches
  - `batch_delay`: Hours between batches (1-24)
  - `batch_count`: Number of batches (2-26)

**Note:** Schedule time must be at least 15 minutes in the future.

### mailchimp_delete_campaign

Delete a campaign permanently.

**Limitations:**
- Only `save` (draft) or `paused` campaigns can be deleted
- Sent campaigns cannot be deleted
- This action is irreversible

### mailchimp_upload_image

Upload images to Mailchimp's File Manager for use in campaigns.

**Limitations:**
- Max file size: 1MB
- Supported formats: PNG, JPG, GIF, BMP

**Tip:** For larger images, compress them first (e.g., using `sips` on macOS).

### mailchimp_create_template

Create reusable email templates from HTML.

**Parameters:**
- `name` (required): Template name (max 100 characters)
- `html` (required): HTML content with Mailchimp merge tags
- `folder_id` (optional): Organize into a folder

**HTML Requirements:**
- Must include `*|UNSUB|*` merge tag for unsubscribe link
- Use `mc:edit="section_name"` attributes for editable sections

**Example editable section:**
```html
<div mc:edit="main_content">
  Default content here
</div>
```

### Template Types

| Type | Description |
|------|-------------|
| `user` | Custom templates you've created |
| `base` | Mailchimp's basic starter templates |
| `gallery` | Pre-designed templates from Mailchimp |

## Campaign Status Values

| Status | Description |
|--------|-------------|
| `save` | Draft - not sent |
| `paused` | Paused |
| `schedule` | Scheduled for future send |
| `sending` | Currently sending |
| `sent` | Sent to audience |

## Error Handling

The server provides helpful error messages for common issues:

- **401**: Invalid API key
- **403**: Access denied (check permissions)
- **404**: Campaign/resource not found
- **429**: Rate limit exceeded

## License

MIT
