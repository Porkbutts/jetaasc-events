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
| Google Calendar | API | Requires setup |
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
