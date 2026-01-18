# JETAASC Events

Tools for publishing JETAASC (JET Alumni Association of Southern California) events to multiple platforms.

## Components

### Claude Code Skills

#### Event Publisher

Located in `.claude/skills/jetaasc-event-publisher/`

Automates event publishing workflow:

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

**Trigger:** `/jetaasc-event-publisher` or ask to "publish an event"

#### Newsletter

Located in `.claude/skills/jetaasc-newsletter/`

Creates monthly JETAASC newsletter campaigns in Mailchimp:

1. Gather content for each section (announcements, events, spotlight, etc.)
2. Process and upload images to Mailchimp
3. Build HTML from template
4. Create draft campaign and send test email

**Trigger:** `/jetaasc-newsletter` or ask to "create a newsletter"

#### Wix Blog Archiver

Located in `.claude/skills/wix-blog-archiver/`

Archives past JETAASC events by moving blog posts from "Upcoming" to "Past Events" category:

1. List posts in "Upcoming" category
2. Parse event dates from post content
3. Preview which posts will be archived
4. Move past events to "Past Events" category

**Trigger:** `/wix-blog-archiver` or ask to "archive past events"

### Discord Events MCP Server

Located in `mcp-servers/discord-events-mcp-server/`

An MCP server for managing Discord Guild Scheduled Events.

**Tools provided:**
- `discord_create_event` - Create a new scheduled event
- `discord_list_events` - List all scheduled events
- `discord_get_event` - Get details of a specific event
- `discord_update_event` - Update an existing event
- `discord_delete_event` - Delete an event

### Google Calendar MCP Server

Located in `mcp-servers/google-calendar-mcp-server/`

An MCP server for managing Google Calendar events using service account authentication.

**Tools provided:**
- `gcal_create_event` - Create a new calendar event
- `gcal_list_events` - List upcoming events
- `gcal_get_event` - Get details of a specific event
- `gcal_update_event` - Update an existing event
- `gcal_delete_event` - Delete an event

### Mailchimp MCP Server

Located in `mcp-servers/mailchimp/`

An MCP server for managing Mailchimp email campaigns.

**Tools provided:**
- `mailchimp_list_audiences` - List audiences to get list_id
- `mailchimp_list_campaigns` - List existing campaigns
- `mailchimp_get_campaign` - Get campaign details
- `mailchimp_create_campaign` - Create a new campaign
- `mailchimp_set_content` - Set HTML/template content for a campaign
- `mailchimp_send_test` - Send a test email
- `mailchimp_send_campaign` - Send campaign to full audience
- `mailchimp_upload_image` - Upload image to File Manager
- `mailchimp_list_files` - List files in File Manager

## Setup

### Discord MCP Server

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot and copy the bot token
3. Enable "Create Events" and "Manage Events" permission
4. Invite bot to your Discord server

5. Build the server:
   ```bash
   cd mcp-servers/discord-events-mcp-server
   npm install
   npm run build
   ```

6. Add to your Claude Code MCP config (`~/.claude/mcp.json`):
   ```json
   {
     "mcpServers": {
       "discord-events": {
         "command": "node",
         "args": ["/path/to/mcp-servers/discord-events-mcp-server/dist/index.js"],
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
   cd mcp-servers/google-calendar-mcp-server
   npm install
   npm run build
   ```

7. Configure in `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "google-calendar": {
         "command": "node",
         "args": ["/path/to/mcp-servers/google-calendar-mcp-server/dist/index.js"],
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

### Mailchimp MCP Server

1. Log into Mailchimp at https://mailchimp.com
2. Go to **Account > Extras > API keys**
3. Click "Create A Key" and copy the key (format: `abc123xyz-us6`)

4. Build the server:
   ```bash
   cd mcp-servers/mailchimp
   npm install
   npm run build
   ```

5. Configure in `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "mailchimp": {
         "command": "node",
         "args": ["mcp-servers/mailchimp/dist/index.js"],
         "env": {
           "MAILCHIMP_API_KEY": "your-api-key-us6"
         }
       }
     }
   }
   ```

**Environment Variables:**
- `MAILCHIMP_API_KEY` - Your Mailchimp API key (includes data center suffix, e.g., `abc123-us6`)


### Wix MCP

The skill uses the Wix MCP server. Follow Wix's setup instructions to configure it.

### Using the Skills

Once MCP servers are configured, invoke skills in Claude Code:

```
/jetaasc-event-publisher   # Publish events to multiple platforms
/jetaasc-newsletter        # Create monthly newsletter campaigns
/wix-blog-archiver         # Archive past events on Wix blog
```

Or simply describe what you want to do (e.g., "publish an event", "create a newsletter", "archive past events").

## License

MIT
