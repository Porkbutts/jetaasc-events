#!/usr/bin/env node
/**
 * Discord Events MCP Server
 *
 * An MCP server for managing Discord Guild Scheduled Events.
 * Supports creating, listing, updating, and deleting events.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { readFile } from "node:fs/promises";
import { extname } from "node:path";
import { z } from "zod";

// Constants
const DISCORD_API_BASE = "https://discord.com/api/v10";

// Environment variables
const BOT_TOKEN = process.env.DISCORD_BOT_TOKEN;
const DEFAULT_GUILD_ID = process.env.DISCORD_GUILD_ID;

// Entity types for Discord events
enum EntityType {
  STAGE_INSTANCE = 1,
  VOICE = 2,
  EXTERNAL = 3,
}

// Event status
enum EventStatus {
  SCHEDULED = 1,
  ACTIVE = 2,
  COMPLETED = 3,
  CANCELED = 4,
}

// Privacy level (currently only GUILD_ONLY is supported)
const PRIVACY_LEVEL_GUILD_ONLY = 2;

// Types
interface DiscordScheduledEvent {
  id: string;
  guild_id: string;
  channel_id: string | null;
  creator_id?: string;
  name: string;
  description?: string;
  scheduled_start_time: string;
  scheduled_end_time?: string;
  privacy_level: number;
  status: number;
  entity_type: number;
  entity_id?: string;
  entity_metadata?: {
    location?: string;
  };
  user_count?: number;
  image?: string;
}

interface ApiError {
  code: number;
  message: string;
  errors?: Record<string, unknown>;
}

// API helper
async function discordRequest<T>(
  endpoint: string,
  method: "GET" | "POST" | "PATCH" | "DELETE" = "GET",
  body?: Record<string, unknown>
): Promise<T> {
  if (!BOT_TOKEN) {
    throw new Error(
      "DISCORD_BOT_TOKEN environment variable is required. " +
        "Create a bot at https://discord.com/developers/applications"
    );
  }

  const url = `${DISCORD_API_BASE}${endpoint}`;
  const options: RequestInit = {
    method,
    headers: {
      Authorization: `Bot ${BOT_TOKEN}`,
      "Content-Type": "application/json",
    },
  };

  if (body && (method === "POST" || method === "PATCH")) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);

  if (!response.ok) {
    let errorMessage = `Discord API error: ${response.status} ${response.statusText}`;
    try {
      const errorData = (await response.json()) as ApiError;
      errorMessage = `Discord API error: ${errorData.message} (code: ${errorData.code})`;
      if (errorData.errors) {
        errorMessage += `\nDetails: ${JSON.stringify(errorData.errors, null, 2)}`;
      }
    } catch {
      // Use default error message
    }
    throw new Error(errorMessage);
  }

  // DELETE returns 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

// MIME type mapping for images
const MIME_TYPES: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
};

// Convert image file to data URI
async function imageToDataUri(filePath: string): Promise<string> {
  const ext = extname(filePath).toLowerCase();
  const mimeType = MIME_TYPES[ext];

  if (!mimeType) {
    throw new Error(
      `Unsupported image format: ${ext}. Supported formats: ${Object.keys(MIME_TYPES).join(", ")}`
    );
  }

  const buffer = await readFile(filePath);
  const base64 = buffer.toString("base64");
  return `data:${mimeType};base64,${base64}`;
}

// Format event for display
function formatEvent(event: DiscordScheduledEvent): string {
  const lines: string[] = [];
  lines.push(`## ${event.name}`);
  lines.push(`- **ID**: ${event.id}`);
  lines.push(`- **Status**: ${EventStatus[event.status] || event.status}`);
  lines.push(`- **Start**: ${new Date(event.scheduled_start_time).toLocaleString()}`);
  if (event.scheduled_end_time) {
    lines.push(`- **End**: ${new Date(event.scheduled_end_time).toLocaleString()}`);
  }
  lines.push(`- **Type**: ${EntityType[event.entity_type] || event.entity_type}`);
  if (event.entity_metadata?.location) {
    lines.push(`- **Location**: ${event.entity_metadata.location}`);
  }
  if (event.description) {
    lines.push(`- **Description**: ${event.description}`);
  }
  if (event.user_count !== undefined) {
    lines.push(`- **Interested**: ${event.user_count} users`);
  }
  return lines.join("\n");
}

// Create MCP server
const server = new McpServer({
  name: "discord-events-mcp-server",
  version: "1.0.0",
});

// Zod Schemas
const CreateEventSchema = z
  .object({
    guild_id: z
      .string()
      .optional()
      .describe("Discord guild/server ID. Uses DISCORD_GUILD_ID env var if not provided"),
    name: z
      .string()
      .min(1)
      .max(100)
      .describe("Name of the event (1-100 characters)"),
    description: z
      .string()
      .max(1000)
      .optional()
      .describe("Description of the event (max 1000 characters)"),
    scheduled_start_time: z
      .string()
      .describe("ISO8601 timestamp for event start (e.g., '2025-02-15T18:00:00')"),
    scheduled_end_time: z
      .string()
      .optional()
      .describe("ISO8601 timestamp for event end. Required for EXTERNAL events"),
    location: z
      .string()
      .max(100)
      .optional()
      .describe("Location for EXTERNAL events (e.g., 'Little Tokyo, Los Angeles')"),
    entity_type: z
      .enum(["STAGE_INSTANCE", "VOICE", "EXTERNAL"])
      .default("EXTERNAL")
      .describe("Type of event: STAGE_INSTANCE (1), VOICE (2), or EXTERNAL (3)"),
    channel_id: z
      .string()
      .optional()
      .describe("Channel ID for STAGE_INSTANCE or VOICE events"),
    image_path: z
      .string()
      .optional()
      .describe("File path to cover image (PNG, JPG, GIF, or WebP). Server will read and encode it."),
  })
  .strict();

const ListEventsSchema = z
  .object({
    guild_id: z
      .string()
      .optional()
      .describe("Discord guild/server ID. Uses DISCORD_GUILD_ID env var if not provided"),
    with_user_count: z
      .boolean()
      .default(true)
      .describe("Include number of users interested in each event"),
  })
  .strict();

const GetEventSchema = z
  .object({
    guild_id: z
      .string()
      .optional()
      .describe("Discord guild/server ID. Uses DISCORD_GUILD_ID env var if not provided"),
    event_id: z.string().describe("ID of the scheduled event to retrieve"),
    with_user_count: z
      .boolean()
      .default(true)
      .describe("Include number of users interested"),
  })
  .strict();

const UpdateEventSchema = z
  .object({
    guild_id: z
      .string()
      .optional()
      .describe("Discord guild/server ID. Uses DISCORD_GUILD_ID env var if not provided"),
    event_id: z.string().describe("ID of the scheduled event to update"),
    name: z
      .string()
      .min(1)
      .max(100)
      .optional()
      .describe("New name for the event"),
    description: z
      .string()
      .max(1000)
      .optional()
      .describe("New description for the event"),
    scheduled_start_time: z
      .string()
      .optional()
      .describe("New ISO8601 start time"),
    scheduled_end_time: z
      .string()
      .optional()
      .describe("New ISO8601 end time"),
    location: z
      .string()
      .max(100)
      .optional()
      .describe("New location for EXTERNAL events"),
    status: z
      .enum(["SCHEDULED", "ACTIVE", "COMPLETED", "CANCELED"])
      .optional()
      .describe("New status. Use to start (ACTIVE) or cancel (CANCELED) events"),
    image_path: z
      .string()
      .optional()
      .describe("File path to new cover image (PNG, JPG, GIF, or WebP). Server will read and encode it."),
  })
  .strict();

const DeleteEventSchema = z
  .object({
    guild_id: z
      .string()
      .optional()
      .describe("Discord guild/server ID. Uses DISCORD_GUILD_ID env var if not provided"),
    event_id: z.string().describe("ID of the scheduled event to delete"),
  })
  .strict();

// Register Tools

server.registerTool(
  "discord_create_event",
  {
    title: "Create Discord Event",
    description: `Create a new scheduled event in a Discord guild/server.

For EXTERNAL events (in-person meetups, online events outside Discord):
- Set entity_type to "EXTERNAL"
- Provide a location (e.g., "Little Tokyo, Los Angeles")
- scheduled_end_time is REQUIRED

For VOICE/STAGE events:
- Set entity_type to "VOICE" or "STAGE_INSTANCE"
- Provide the channel_id

For cover images:
- Provide image_path with a local file path (PNG, JPG, GIF, or WebP)
- The server will read and encode the image automatically

Returns the created event details including its ID.`,
    inputSchema: CreateEventSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: true,
    },
  },
  async (params) => {
    const guildId = params.guild_id || DEFAULT_GUILD_ID;
    if (!guildId) {
      return {
        content: [
          {
            type: "text",
            text: "Error: No guild_id provided and DISCORD_GUILD_ID environment variable is not set.",
          },
        ],
      };
    }

    const entityTypeMap: Record<string, number> = {
      STAGE_INSTANCE: EntityType.STAGE_INSTANCE,
      VOICE: EntityType.VOICE,
      EXTERNAL: EntityType.EXTERNAL,
    };

    const body: Record<string, unknown> = {
      name: params.name,
      privacy_level: PRIVACY_LEVEL_GUILD_ONLY,
      scheduled_start_time: params.scheduled_start_time,
      entity_type: entityTypeMap[params.entity_type],
    };

    if (params.description) {
      body.description = params.description;
    }

    if (params.scheduled_end_time) {
      body.scheduled_end_time = params.scheduled_end_time;
    }

    if (params.entity_type === "EXTERNAL") {
      if (!params.location) {
        return {
          content: [
            {
              type: "text",
              text: "Error: location is required for EXTERNAL events.",
            },
          ],
        };
      }
      if (!params.scheduled_end_time) {
        return {
          content: [
            {
              type: "text",
              text: "Error: scheduled_end_time is required for EXTERNAL events.",
            },
          ],
        };
      }
      body.entity_metadata = { location: params.location };
    } else {
      if (!params.channel_id) {
        return {
          content: [
            {
              type: "text",
              text: `Error: channel_id is required for ${params.entity_type} events.`,
            },
          ],
        };
      }
      body.channel_id = params.channel_id;
    }

    if (params.image_path) {
      try {
        body.image = await imageToDataUri(params.image_path);
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error reading image: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    }

    try {
      const event = await discordRequest<DiscordScheduledEvent>(
        `/guilds/${guildId}/scheduled-events`,
        "POST",
        body
      );

      return {
        content: [
          {
            type: "text",
            text: `# Event Created Successfully\n\n${formatEvent(event)}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error creating event: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
      };
    }
  }
);

server.registerTool(
  "discord_list_events",
  {
    title: "List Discord Events",
    description: `List all scheduled events in a Discord guild/server.

Returns upcoming and active events with their details including:
- Event ID, name, and description
- Start and end times
- Location (for external events)
- Number of interested users`,
    inputSchema: ListEventsSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    const guildId = params.guild_id || DEFAULT_GUILD_ID;
    if (!guildId) {
      return {
        content: [
          {
            type: "text",
            text: "Error: No guild_id provided and DISCORD_GUILD_ID environment variable is not set.",
          },
        ],
      };
    }

    try {
      const queryParams = params.with_user_count ? "?with_user_count=true" : "";
      const events = await discordRequest<DiscordScheduledEvent[]>(
        `/guilds/${guildId}/scheduled-events${queryParams}`
      );

      if (events.length === 0) {
        return {
          content: [
            {
              type: "text",
              text: "No scheduled events found in this guild.",
            },
          ],
        };
      }

      const formatted = events.map(formatEvent).join("\n\n---\n\n");
      return {
        content: [
          {
            type: "text",
            text: `# Scheduled Events (${events.length})\n\n${formatted}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error listing events: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
      };
    }
  }
);

server.registerTool(
  "discord_get_event",
  {
    title: "Get Discord Event",
    description: `Get details of a specific scheduled event by its ID.

Returns complete event information including name, description,
times, location, and number of interested users.`,
    inputSchema: GetEventSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    const guildId = params.guild_id || DEFAULT_GUILD_ID;
    if (!guildId) {
      return {
        content: [
          {
            type: "text",
            text: "Error: No guild_id provided and DISCORD_GUILD_ID environment variable is not set.",
          },
        ],
      };
    }

    try {
      const queryParams = params.with_user_count ? "?with_user_count=true" : "";
      const event = await discordRequest<DiscordScheduledEvent>(
        `/guilds/${guildId}/scheduled-events/${params.event_id}${queryParams}`
      );

      return {
        content: [
          {
            type: "text",
            text: `# Event Details\n\n${formatEvent(event)}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error getting event: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
      };
    }
  }
);

server.registerTool(
  "discord_update_event",
  {
    title: "Update Discord Event",
    description: `Update an existing scheduled event.

Can modify: name, description, start/end times, location, status, cover image.

To start an event: set status to "ACTIVE"
To cancel an event: set status to "CANCELED"
To update cover image: provide image_path with a local file path

Only provide the fields you want to change.`,
    inputSchema: UpdateEventSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    const guildId = params.guild_id || DEFAULT_GUILD_ID;
    if (!guildId) {
      return {
        content: [
          {
            type: "text",
            text: "Error: No guild_id provided and DISCORD_GUILD_ID environment variable is not set.",
          },
        ],
      };
    }

    const body: Record<string, unknown> = {};

    if (params.name) body.name = params.name;
    if (params.description !== undefined) body.description = params.description;
    if (params.scheduled_start_time) body.scheduled_start_time = params.scheduled_start_time;
    if (params.scheduled_end_time) body.scheduled_end_time = params.scheduled_end_time;
    if (params.location) body.entity_metadata = { location: params.location };

    if (params.image_path) {
      try {
        body.image = await imageToDataUri(params.image_path);
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error reading image: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    }

    if (params.status) {
      const statusMap: Record<string, number> = {
        SCHEDULED: EventStatus.SCHEDULED,
        ACTIVE: EventStatus.ACTIVE,
        COMPLETED: EventStatus.COMPLETED,
        CANCELED: EventStatus.CANCELED,
      };
      body.status = statusMap[params.status];
    }

    if (Object.keys(body).length === 0) {
      return {
        content: [
          {
            type: "text",
            text: "Error: No fields provided to update.",
          },
        ],
      };
    }

    try {
      const event = await discordRequest<DiscordScheduledEvent>(
        `/guilds/${guildId}/scheduled-events/${params.event_id}`,
        "PATCH",
        body
      );

      return {
        content: [
          {
            type: "text",
            text: `# Event Updated Successfully\n\n${formatEvent(event)}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error updating event: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
      };
    }
  }
);

server.registerTool(
  "discord_delete_event",
  {
    title: "Delete Discord Event",
    description: `Delete a scheduled event from the guild.

This action is irreversible. The event will be permanently removed.`,
    inputSchema: DeleteEventSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    const guildId = params.guild_id || DEFAULT_GUILD_ID;
    if (!guildId) {
      return {
        content: [
          {
            type: "text",
            text: "Error: No guild_id provided and DISCORD_GUILD_ID environment variable is not set.",
          },
        ],
      };
    }

    try {
      await discordRequest(
        `/guilds/${guildId}/scheduled-events/${params.event_id}`,
        "DELETE"
      );

      return {
        content: [
          {
            type: "text",
            text: `Event ${params.event_id} has been deleted successfully.`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error deleting event: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
      };
    }
  }
);

// Main
async function main() {
  if (!BOT_TOKEN) {
    console.error(
      "WARNING: DISCORD_BOT_TOKEN environment variable is not set.\n" +
        "The server will start but API calls will fail.\n" +
        "Create a bot at https://discord.com/developers/applications"
    );
  }

  if (!DEFAULT_GUILD_ID) {
    console.error(
      "NOTE: DISCORD_GUILD_ID environment variable is not set.\n" +
        "You will need to provide guild_id in each tool call."
    );
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Discord Events MCP Server running via stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
