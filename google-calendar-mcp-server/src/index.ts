#!/usr/bin/env node
/**
 * Google Calendar MCP Server
 *
 * An MCP server for managing Google Calendar events using service account authentication.
 * Supports creating, listing, updating, and deleting calendar events.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { google, calendar_v3 } from "googleapis";
import { readFile } from "node:fs/promises";
import { z } from "zod";

// Types
type CalendarEvent = calendar_v3.Schema$Event;

// Environment variables
const SERVICE_ACCOUNT_KEY_PATH = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH;
const SERVICE_ACCOUNT_KEY_JSON = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
const DEFAULT_CALENDAR_ID = process.env.GOOGLE_CALENDAR_ID || "primary";

// Google Calendar client (initialized on first use)
let calendarClient: calendar_v3.Calendar | null = null;

/**
 * Initialize the Google Calendar client with service account credentials
 */
async function getCalendarClient(): Promise<calendar_v3.Calendar> {
  if (calendarClient) {
    return calendarClient;
  }

  let credentials: { client_email: string; private_key: string };

  if (SERVICE_ACCOUNT_KEY_JSON) {
    // Parse credentials from environment variable
    try {
      credentials = JSON.parse(SERVICE_ACCOUNT_KEY_JSON);
    } catch {
      throw new Error(
        "GOOGLE_SERVICE_ACCOUNT_KEY contains invalid JSON. " +
          "Ensure it contains the full service account key JSON."
      );
    }
  } else if (SERVICE_ACCOUNT_KEY_PATH) {
    // Load credentials from file
    try {
      const keyContent = await readFile(SERVICE_ACCOUNT_KEY_PATH, "utf-8");
      credentials = JSON.parse(keyContent);
    } catch (error) {
      throw new Error(
        `Failed to load service account key from ${SERVICE_ACCOUNT_KEY_PATH}: ` +
          `${error instanceof Error ? error.message : String(error)}`
      );
    }
  } else {
    throw new Error(
      "Google Calendar credentials not configured. " +
        "Set either GOOGLE_SERVICE_ACCOUNT_KEY_PATH (path to JSON file) or " +
        "GOOGLE_SERVICE_ACCOUNT_KEY (JSON content) environment variable."
    );
  }

  // Create JWT auth client
  const auth = new google.auth.JWT({
    email: credentials.client_email,
    key: credentials.private_key,
    scopes: ["https://www.googleapis.com/auth/calendar"],
  });

  calendarClient = google.calendar({ version: "v3", auth });
  return calendarClient;
}

/**
 * Format a calendar event for display
 */
function formatEvent(event: CalendarEvent): string {
  const lines: string[] = [];
  lines.push(`## ${event.summary || "(No title)"}`);
  lines.push(`- **ID**: ${event.id}`);

  if (event.status) {
    lines.push(`- **Status**: ${event.status}`);
  }

  // Handle all-day events vs timed events
  if (event.start?.date) {
    lines.push(`- **Date**: ${event.start.date}`);
    if (event.end?.date) {
      lines.push(`- **End Date**: ${event.end.date}`);
    }
  } else if (event.start?.dateTime) {
    lines.push(`- **Start**: ${new Date(event.start.dateTime).toLocaleString()}`);
    if (event.end?.dateTime) {
      lines.push(`- **End**: ${new Date(event.end.dateTime).toLocaleString()}`);
    }
  }

  if (event.location) {
    lines.push(`- **Location**: ${event.location}`);
  }

  if (event.description) {
    // Truncate long descriptions
    const desc =
      event.description.length > 200
        ? event.description.substring(0, 200) + "..."
        : event.description;
    lines.push(`- **Description**: ${desc}`);
  }

  if (event.htmlLink) {
    lines.push(`- **Link**: ${event.htmlLink}`);
  }

  return lines.join("\n");
}

/**
 * Handle Google API errors with helpful messages
 */
function handleApiError(error: unknown): string {
  if (error instanceof Error) {
    const message = error.message;

    if (message.includes("invalid_grant") || message.includes("Invalid JWT")) {
      return (
        "Error: Invalid service account credentials. " +
        "Verify your service account key is correct and not expired."
      );
    }

    if (message.includes("notFound") || message.includes("404")) {
      return "Error: Calendar or event not found. Check the calendar ID and ensure the service account has access.";
    }

    if (message.includes("forbidden") || message.includes("403")) {
      return (
        "Error: Access denied. Ensure the calendar is shared with the service account email " +
        "(found in your service account JSON as 'client_email')."
      );
    }

    if (message.includes("insufficientPermissions")) {
      return (
        "Error: Insufficient permissions. The service account needs 'Make changes to events' " +
        "permission on the calendar."
      );
    }

    return `Error: ${message}`;
  }

  return `Error: ${String(error)}`;
}

// Create MCP server
const server = new McpServer({
  name: "google-calendar-mcp-server",
  version: "1.0.0",
});

// Zod Schemas
const CreateEventSchema = z
  .object({
    calendar_id: z
      .string()
      .optional()
      .describe(
        "Calendar ID. Uses GOOGLE_CALENDAR_ID env var if not provided, or 'primary' as fallback"
      ),
    summary: z
      .string()
      .min(1)
      .max(1024)
      .describe("Event title/summary (1-1024 characters)"),
    description: z
      .string()
      .max(8192)
      .optional()
      .describe("Event description (max 8192 characters)"),
    location: z
      .string()
      .max(1024)
      .optional()
      .describe("Event location (e.g., 'Little Tokyo, Los Angeles')"),
    start_time: z
      .string()
      .describe(
        "Start time as ISO8601 timestamp (e.g., '2025-02-15T18:00:00-08:00') or date for all-day events (e.g., '2025-02-15')"
      ),
    end_time: z
      .string()
      .describe(
        "End time as ISO8601 timestamp or date. Required for all events."
      ),
    timezone: z
      .string()
      .optional()
      .describe(
        "Timezone for the event (e.g., 'America/Los_Angeles'). Only needed if start/end times don't include timezone offset."
      ),
  })
  .strict();

const ListEventsSchema = z
  .object({
    calendar_id: z
      .string()
      .optional()
      .describe("Calendar ID. Uses GOOGLE_CALENDAR_ID env var if not provided"),
    max_results: z
      .number()
      .int()
      .min(1)
      .max(250)
      .default(10)
      .describe("Maximum number of events to return (1-250, default: 10)"),
    time_min: z
      .string()
      .optional()
      .describe(
        "Lower bound for event start time (ISO8601). Defaults to now."
      ),
    time_max: z
      .string()
      .optional()
      .describe("Upper bound for event start time (ISO8601)"),
    query: z
      .string()
      .optional()
      .describe("Free text search terms to filter events"),
  })
  .strict();

const GetEventSchema = z
  .object({
    calendar_id: z
      .string()
      .optional()
      .describe("Calendar ID. Uses GOOGLE_CALENDAR_ID env var if not provided"),
    event_id: z.string().describe("ID of the event to retrieve"),
  })
  .strict();

const UpdateEventSchema = z
  .object({
    calendar_id: z
      .string()
      .optional()
      .describe("Calendar ID. Uses GOOGLE_CALENDAR_ID env var if not provided"),
    event_id: z.string().describe("ID of the event to update"),
    summary: z
      .string()
      .min(1)
      .max(1024)
      .optional()
      .describe("New event title/summary"),
    description: z
      .string()
      .max(8192)
      .optional()
      .describe("New event description"),
    location: z.string().max(1024).optional().describe("New event location"),
    start_time: z
      .string()
      .optional()
      .describe("New start time (ISO8601 timestamp or date)"),
    end_time: z
      .string()
      .optional()
      .describe("New end time (ISO8601 timestamp or date)"),
    timezone: z.string().optional().describe("Timezone for the event"),
    status: z
      .enum(["confirmed", "tentative", "cancelled"])
      .optional()
      .describe("New event status"),
  })
  .strict();

const DeleteEventSchema = z
  .object({
    calendar_id: z
      .string()
      .optional()
      .describe("Calendar ID. Uses GOOGLE_CALENDAR_ID env var if not provided"),
    event_id: z.string().describe("ID of the event to delete"),
  })
  .strict();

// Helper to determine if a datetime string is a date-only format
function isDateOnly(dateStr: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(dateStr);
}

// Register Tools

server.registerTool(
  "gcal_create_event",
  {
    title: "Create Google Calendar Event",
    description: `Create a new event on a Google Calendar.

For timed events:
- Provide start_time and end_time as ISO8601 timestamps (e.g., '2025-02-15T18:00:00-08:00')
- Include timezone offset in the timestamp OR provide the timezone parameter

For all-day events:
- Provide start_time and end_time as dates (e.g., '2025-02-15')
- End date should be the day AFTER the last day of the event (exclusive)

Returns the created event details including its ID and link.`,
    inputSchema: CreateEventSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const calendar = await getCalendarClient();
      const calendarId = params.calendar_id || DEFAULT_CALENDAR_ID;

      const eventBody: CalendarEvent = {
        summary: params.summary,
      };

      if (params.description) {
        eventBody.description = params.description;
      }

      if (params.location) {
        eventBody.location = params.location;
      }

      // Handle start/end times
      if (isDateOnly(params.start_time)) {
        // All-day event
        eventBody.start = { date: params.start_time };
        eventBody.end = { date: params.end_time };
      } else {
        // Timed event
        eventBody.start = {
          dateTime: params.start_time,
          timeZone: params.timezone,
        };
        eventBody.end = {
          dateTime: params.end_time,
          timeZone: params.timezone,
        };
      }

      const response = await calendar.events.insert({
        calendarId,
        requestBody: eventBody,
      });

      const event = response.data;

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
            text: handleApiError(error),
          },
        ],
      };
    }
  }
);

server.registerTool(
  "gcal_list_events",
  {
    title: "List Google Calendar Events",
    description: `List upcoming events from a Google Calendar.

Returns events sorted by start time, with details including:
- Event ID, title, and description
- Start and end times
- Location
- Link to the event

By default, returns upcoming events starting from now.`,
    inputSchema: ListEventsSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const calendar = await getCalendarClient();
      const calendarId = params.calendar_id || DEFAULT_CALENDAR_ID;

      const response = await calendar.events.list({
        calendarId,
        maxResults: params.max_results,
        timeMin: params.time_min || new Date().toISOString(),
        timeMax: params.time_max,
        q: params.query,
        singleEvents: true,
        orderBy: "startTime",
      });

      const events = response.data.items || [];

      if (events.length === 0) {
        return {
          content: [
            {
              type: "text",
              text: "No upcoming events found.",
            },
          ],
        };
      }

      const formatted = events.map(formatEvent).join("\n\n---\n\n");
      return {
        content: [
          {
            type: "text",
            text: `# Calendar Events (${events.length})\n\n${formatted}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: handleApiError(error),
          },
        ],
      };
    }
  }
);

server.registerTool(
  "gcal_get_event",
  {
    title: "Get Google Calendar Event",
    description: `Get details of a specific calendar event by its ID.

Returns complete event information including title, description,
times, location, and link.`,
    inputSchema: GetEventSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const calendar = await getCalendarClient();
      const calendarId = params.calendar_id || DEFAULT_CALENDAR_ID;

      const response = await calendar.events.get({
        calendarId,
        eventId: params.event_id,
      });

      return {
        content: [
          {
            type: "text",
            text: `# Event Details\n\n${formatEvent(response.data)}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: handleApiError(error),
          },
        ],
      };
    }
  }
);

server.registerTool(
  "gcal_update_event",
  {
    title: "Update Google Calendar Event",
    description: `Update an existing calendar event.

Can modify: title, description, location, start/end times, status.

To cancel an event: set status to "cancelled"

Only provide the fields you want to change. Existing values for
unprovided fields will be preserved.`,
    inputSchema: UpdateEventSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const calendar = await getCalendarClient();
      const calendarId = params.calendar_id || DEFAULT_CALENDAR_ID;

      // First, get the existing event
      const existingResponse = await calendar.events.get({
        calendarId,
        eventId: params.event_id,
      });

      const existingEvent = existingResponse.data;
      const eventBody: CalendarEvent = { ...existingEvent };

      // Update provided fields
      if (params.summary !== undefined) {
        eventBody.summary = params.summary;
      }
      if (params.description !== undefined) {
        eventBody.description = params.description;
      }
      if (params.location !== undefined) {
        eventBody.location = params.location;
      }
      if (params.status !== undefined) {
        eventBody.status = params.status;
      }

      // Handle time updates
      if (params.start_time) {
        if (isDateOnly(params.start_time)) {
          eventBody.start = { date: params.start_time };
        } else {
          eventBody.start = {
            dateTime: params.start_time,
            timeZone: params.timezone || existingEvent.start?.timeZone,
          };
        }
      }

      if (params.end_time) {
        if (isDateOnly(params.end_time)) {
          eventBody.end = { date: params.end_time };
        } else {
          eventBody.end = {
            dateTime: params.end_time,
            timeZone: params.timezone || existingEvent.end?.timeZone,
          };
        }
      }

      const response = await calendar.events.update({
        calendarId,
        eventId: params.event_id,
        requestBody: eventBody,
      });

      return {
        content: [
          {
            type: "text",
            text: `# Event Updated Successfully\n\n${formatEvent(response.data)}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: handleApiError(error),
          },
        ],
      };
    }
  }
);

server.registerTool(
  "gcal_delete_event",
  {
    title: "Delete Google Calendar Event",
    description: `Delete an event from the calendar.

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
    try {
      const calendar = await getCalendarClient();
      const calendarId = params.calendar_id || DEFAULT_CALENDAR_ID;

      await calendar.events.delete({
        calendarId,
        eventId: params.event_id,
      });

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
            text: handleApiError(error),
          },
        ],
      };
    }
  }
);

// Main
async function main() {
  if (!SERVICE_ACCOUNT_KEY_PATH && !SERVICE_ACCOUNT_KEY_JSON) {
    console.error(
      "WARNING: No Google service account credentials configured.\n" +
        "Set GOOGLE_SERVICE_ACCOUNT_KEY_PATH or GOOGLE_SERVICE_ACCOUNT_KEY.\n" +
        "The server will start but API calls will fail."
    );
  }

  if (!process.env.GOOGLE_CALENDAR_ID) {
    console.error(
      "NOTE: GOOGLE_CALENDAR_ID environment variable is not set.\n" +
        "Using 'primary' as default. You can provide calendar_id in each tool call."
    );
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Google Calendar MCP Server running via stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
