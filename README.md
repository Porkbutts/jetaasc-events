# JETAASC Events

Tools for publishing JETAASC (JET Alumni Association of Southern California) events to multiple platforms.

## Components

### Claude Code Skill

Located in `.claude/skills/jetaasc-event-publisher/`

A Claude Code skill that automates event publishing workflow:

1. Collect event details (title, date, location, description, cost, RSVP link, flyer)
2. Confirm details and select target platforms
3. Publish to selected platforms in parallel or sequentially

**Supported Platforms:**

| Platform | Method | Status |
|----------|--------|--------|
| Wix Blog | Wix MCP | Ready |
| Discord | Discord MCP | Ready |
| Google Calendar | Google Calendar MCP | Ready |
| Facebook | Manual | Copy/paste |

### Discord Events MCP Server

Located in `discord-events-mcp-server/`

An MCP server for managing Discord Guild Scheduled Events.

**Tools provided:**
- `discord_create_event` - Create a new scheduled event
- `discord_list_events` - List all scheduled events
- `discord_get_event` - Get details of a specific event
- `discord_update_event` - Update an existing event
- `discord_delete_event` - Delete an event

### Google Calendar MCP Server

Located in `google-calendar-mcp-server/`

An MCP server for managing Google Calendar events using service account authentication.

**Tools provided:**
- `gcal_create_event` - Create a new calendar event
- `gcal_list_events` - List upcoming events
- `gcal_get_event` - Get details of a specific event
- `gcal_update_event` - Update an existing event
- `gcal_delete_event` - Delete an event

### Google Forms MCP Server

Located in `google-forms-mcp-server/`

An MCP server for creating Google Forms from templates using service account authentication.

**Tools provided:**
- `gforms_create_from_template` - Copy a template form, set title/description, publish, and make public
- `gforms_get_form` - Get form details including responder URL
- `gforms_update_form` - Update a form's title and description
- `gforms_list_responses` - List form responses

## Setup

### Discord MCP Server

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot and copy the bot token
3. Enable "Create Events" and "Manage Events" permission
4. Invite bot to your Discord server

5. Build the server:
   ```bash
   cd discord-events-mcp-server
   npm install
   npm run build
   ```

6. Add to your Claude Code MCP config (`~/.claude/mcp.json`):
   ```json
   {
     "mcpServers": {
       "discord-events": {
         "command": "node",
         "args": ["/path/to/discord-events-mcp-server/dist/index.js"],
         "env": {
           "DISCORD_BOT_TOKEN": "your-bot-token",
           "DISCORD_GUILD_ID": "your-guild-id"
         }
       }
     }
   }
   ```

### Google Calendar MCP Server

1. Create a Google Cloud project at https://console.cloud.google.com
2. Enable the Google Calendar API
3. Create a Service Account (APIs & Services → Credentials → Create Credentials → Service Account)
4. Create and download a JSON key for the service account
5. Share your Google Calendar with the service account email (found in the JSON as `client_email`)
   - Give it "Make changes to events" permission

6. Build the server:
   ```bash
   cd google-calendar-mcp-server
   npm install
   npm run build
   ```

7. Configure in `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "google-calendar": {
         "command": "node",
         "args": ["google-calendar-mcp-server/dist/index.js"],
         "env": {
           "GOOGLE_SERVICE_ACCOUNT_KEY_PATH": "/path/to/service-account-key.json",
           "GOOGLE_CALENDAR_ID": "your-calendar-id@group.calendar.google.com"
         }
       }
     }
   }
   ```

**Environment Variables:**
- `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` - Path to the service account JSON key file
- `GOOGLE_SERVICE_ACCOUNT_KEY` - Alternative: JSON content directly (useful for CI/CD)
- `GOOGLE_CALENDAR_ID` - Calendar ID to use (defaults to "primary")

### Google Forms MCP Server

Uses the same service account as the Calendar server. Additional setup:

1. Enable the Google Forms API in your Google Cloud project
2. Enable the Google Drive API (for copying templates)
3. Create a template form in Google Forms with your standard questions
4. Share the template form with the service account email (give it Editor access)

5. Build the server:
   ```bash
   cd google-forms-mcp-server
   npm install
   npm run build
   ```

6. Configure in `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "google-forms": {
         "command": "node",
         "args": ["google-forms-mcp-server/dist/index.js"],
         "env": {
           "GOOGLE_SERVICE_ACCOUNT_KEY_PATH": "/path/to/service-account-key.json",
           "GOOGLE_FORMS_TEMPLATE_ID": "your-template-form-id"
         }
       }
     }
   }
   ```

**Environment Variables:**
- `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` - Path to the service account JSON key file
- `GOOGLE_SERVICE_ACCOUNT_KEY` - Alternative: JSON content directly (useful for CI/CD)
- `GOOGLE_FORMS_TEMPLATE_ID` - Form ID of the template to copy (optional, can be passed per-call)

**Finding the Form ID:**
The form ID is in the URL when editing a form: `https://docs.google.com/forms/d/{FORM_ID}/edit`

### Wix MCP

The skill uses the Wix MCP server. Follow Wix's setup instructions to configure it.

### Using the Skill

Once MCP servers are configured, invoke the skill in Claude Code:

```
/jetaasc-event-publisher
```

Or simply ask Claude to "publish an event" or "create an event post".

## License

MIT
