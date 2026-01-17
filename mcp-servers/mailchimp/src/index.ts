#!/usr/bin/env node
/**
 * Mailchimp MCP Server
 *
 * An MCP server for managing Mailchimp email campaigns.
 * Supports creating campaigns, setting content, uploading images,
 * sending test emails, and sending campaigns.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import axios, { AxiosError } from "axios";
import { z } from "zod";

// Environment variables
const MAILCHIMP_API_KEY = process.env.MAILCHIMP_API_KEY;

// Extract data center from API key (e.g., "xxx-us6" -> "us6")
function getDataCenter(): string {
  if (!MAILCHIMP_API_KEY) {
    throw new Error("MAILCHIMP_API_KEY environment variable is required");
  }
  const parts = MAILCHIMP_API_KEY.split("-");
  if (parts.length < 2) {
    throw new Error(
      "Invalid MAILCHIMP_API_KEY format. Expected format: 'apikey-dc' (e.g., 'abc123-us6')"
    );
  }
  return parts[parts.length - 1];
}

// Get base URL for Mailchimp API
function getBaseUrl(): string {
  const dc = getDataCenter();
  return `https://${dc}.api.mailchimp.com/3.0`;
}

// Types
interface MailchimpCampaign {
  id: string;
  type: string;
  status: string;
  create_time: string;
  send_time?: string;
  emails_sent?: number;
  recipients?: {
    list_id: string;
    list_name?: string;
    segment_text?: string;
  };
  settings?: {
    subject_line?: string;
    preview_text?: string;
    title?: string;
    from_name?: string;
    reply_to?: string;
  };
  archive_url?: string;
}

interface MailchimpAudience {
  id: string;
  name: string;
  stats?: {
    member_count: number;
    unsubscribe_count: number;
  };
}

interface MailchimpFile {
  id: number;
  name: string;
  full_size_url: string;
  type: string;
  size: number;
}

/**
 * Make authenticated API request to Mailchimp
 */
async function makeApiRequest<T>(
  endpoint: string,
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" = "GET",
  data?: unknown
): Promise<T> {
  const response = await axios({
    method,
    url: `${getBaseUrl()}${endpoint}`,
    data,
    timeout: 120000, // Mailchimp has 120s timeout
    auth: {
      username: "anystring",
      password: MAILCHIMP_API_KEY!,
    },
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  return response.data;
}

/**
 * Handle Mailchimp API errors with helpful messages
 */
function handleApiError(error: unknown): string {
  if (error instanceof AxiosError) {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;
      const detail = data?.detail || data?.title || "";

      switch (status) {
        case 401:
          return (
            "Error: Invalid API key. Verify your MAILCHIMP_API_KEY is correct " +
            "and includes the data center suffix (e.g., 'xxx-us6')."
          );
        case 403:
          return `Error: Access denied. ${detail}`;
        case 404:
          return `Error: Resource not found. ${detail}`;
        case 400:
          return `Error: Bad request. ${detail}`;
        case 429:
          return "Error: Rate limit exceeded. Please wait before making more requests.";
        default:
          return `Error: API request failed (${status}). ${detail}`;
      }
    } else if (error.code === "ECONNABORTED") {
      return "Error: Request timed out. Please try again.";
    }
  }
  return `Error: ${error instanceof Error ? error.message : String(error)}`;
}

/**
 * Format a campaign for display
 */
function formatCampaign(campaign: MailchimpCampaign): string {
  const lines: string[] = [];
  lines.push(`## ${campaign.settings?.title || campaign.settings?.subject_line || "(No title)"}`);
  lines.push(`- **ID**: ${campaign.id}`);
  lines.push(`- **Type**: ${campaign.type}`);
  lines.push(`- **Status**: ${campaign.status}`);

  if (campaign.settings?.subject_line) {
    lines.push(`- **Subject**: ${campaign.settings.subject_line}`);
  }

  if (campaign.settings?.from_name) {
    lines.push(`- **From**: ${campaign.settings.from_name}`);
  }

  if (campaign.recipients?.list_name) {
    lines.push(`- **Audience**: ${campaign.recipients.list_name}`);
  }

  if (campaign.create_time) {
    lines.push(`- **Created**: ${new Date(campaign.create_time).toLocaleString()}`);
  }

  if (campaign.send_time) {
    lines.push(`- **Sent**: ${new Date(campaign.send_time).toLocaleString()}`);
  }

  if (campaign.emails_sent) {
    lines.push(`- **Emails Sent**: ${campaign.emails_sent}`);
  }

  if (campaign.archive_url) {
    lines.push(`- **Archive URL**: ${campaign.archive_url}`);
  }

  return lines.join("\n");
}

// Create MCP server
const server = new McpServer({
  name: "mailchimp-mcp-server",
  version: "1.0.0",
});

// ============================================================================
// Zod Schemas
// ============================================================================

const ListAudiencesSchema = z
  .object({
    count: z
      .number()
      .int()
      .min(1)
      .max(1000)
      .default(10)
      .describe("Number of audiences to return (default: 10)"),
  })
  .strict();

const ListCampaignsSchema = z
  .object({
    count: z
      .number()
      .int()
      .min(1)
      .max(1000)
      .default(10)
      .describe("Number of campaigns to return (default: 10)"),
    status: z
      .enum(["save", "paused", "schedule", "sending", "sent"])
      .optional()
      .describe("Filter by campaign status"),
  })
  .strict();

const GetCampaignSchema = z
  .object({
    campaign_id: z.string().describe("The unique ID of the campaign"),
  })
  .strict();

const CreateCampaignSchema = z
  .object({
    type: z
      .enum(["regular", "plaintext", "rss", "variate"])
      .default("regular")
      .describe("Campaign type (default: 'regular')"),
    list_id: z.string().describe("The unique ID of the audience/list to send to"),
    subject_line: z.string().max(150).describe("The subject line for the campaign"),
    preview_text: z
      .string()
      .max(150)
      .optional()
      .describe("Preview text shown in email clients"),
    title: z.string().max(100).optional().describe("Internal title for the campaign"),
    from_name: z.string().max(100).describe("The 'from' name on the campaign"),
    reply_to: z.string().email().describe("The reply-to email address"),
  })
  .strict();

const SetContentSchema = z
  .object({
    campaign_id: z.string().describe("The unique ID of the campaign"),
    html: z.string().optional().describe("The raw HTML content for the campaign"),
    plain_text: z
      .string()
      .optional()
      .describe("Plain text content (auto-generated from HTML if omitted)"),
    template_id: z
      .number()
      .int()
      .optional()
      .describe("Use a saved template by ID instead of raw HTML"),
  })
  .strict();

const SendTestSchema = z
  .object({
    campaign_id: z.string().describe("The unique ID of the campaign"),
    test_emails: z
      .array(z.string().email())
      .min(1)
      .max(5)
      .describe("Email addresses to send test to (max 5)"),
    send_type: z
      .enum(["html", "plaintext"])
      .default("html")
      .describe("Type of test email to send (default: 'html')"),
  })
  .strict();

const SendCampaignSchema = z
  .object({
    campaign_id: z.string().describe("The unique ID of the campaign to send"),
  })
  .strict();

const UploadImageSchema = z
  .object({
    name: z.string().describe("Filename for the image (e.g., 'header.png')"),
    file_data: z
      .string()
      .describe("Base64-encoded image data (PNG, JPG, GIF, or BMP, max 1MB)"),
    folder_id: z
      .number()
      .int()
      .optional()
      .describe("Optional folder ID to upload to"),
  })
  .strict();

const ListFilesSchema = z
  .object({
    count: z
      .number()
      .int()
      .min(1)
      .max(1000)
      .default(25)
      .describe("Number of files to return (default: 25)"),
  })
  .strict();

// ============================================================================
// Tool Implementations
// ============================================================================

server.registerTool(
  "mailchimp_list_audiences",
  {
    title: "List Mailchimp Audiences",
    description: `List all audiences (lists) in your Mailchimp account.

Use this to find the list_id needed when creating campaigns.

Returns audience names, IDs, and subscriber counts.`,
    inputSchema: ListAudiencesSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const data = await makeApiRequest<{ lists: MailchimpAudience[] }>(
        `/lists?count=${params.count}`
      );

      const audiences = data.lists || [];

      if (audiences.length === 0) {
        return {
          content: [{ type: "text", text: "No audiences found in your Mailchimp account." }],
        };
      }

      const lines = ["# Mailchimp Audiences\n"];
      for (const audience of audiences) {
        lines.push(`## ${audience.name}`);
        lines.push(`- **ID**: ${audience.id}`);
        if (audience.stats) {
          lines.push(`- **Members**: ${audience.stats.member_count}`);
        }
        lines.push("");
      }

      return {
        content: [{ type: "text", text: lines.join("\n") }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: handleApiError(error) }],
      };
    }
  }
);

server.registerTool(
  "mailchimp_list_campaigns",
  {
    title: "List Mailchimp Campaigns",
    description: `List campaigns in your Mailchimp account.

Returns campaign IDs, titles, status, and other details.
Use this to find campaign IDs for other operations.`,
    inputSchema: ListCampaignsSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      let endpoint = `/campaigns?count=${params.count}`;
      if (params.status) {
        endpoint += `&status=${params.status}`;
      }

      const data = await makeApiRequest<{ campaigns: MailchimpCampaign[] }>(endpoint);

      const campaigns = data.campaigns || [];

      if (campaigns.length === 0) {
        return {
          content: [{ type: "text", text: "No campaigns found." }],
        };
      }

      const formatted = campaigns.map(formatCampaign).join("\n\n---\n\n");
      return {
        content: [{ type: "text", text: `# Mailchimp Campaigns (${campaigns.length})\n\n${formatted}` }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: handleApiError(error) }],
      };
    }
  }
);

server.registerTool(
  "mailchimp_get_campaign",
  {
    title: "Get Mailchimp Campaign",
    description: `Get details of a specific campaign by ID.

Returns full campaign information including settings, recipients, and status.`,
    inputSchema: GetCampaignSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const campaign = await makeApiRequest<MailchimpCampaign>(
        `/campaigns/${params.campaign_id}`
      );

      return {
        content: [{ type: "text", text: `# Campaign Details\n\n${formatCampaign(campaign)}` }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: handleApiError(error) }],
      };
    }
  }
);

server.registerTool(
  "mailchimp_create_campaign",
  {
    title: "Create Mailchimp Campaign",
    description: `Create a new email campaign in Mailchimp.

This creates the campaign structure. After creation, you need to:
1. Set content using mailchimp_set_content
2. Optionally send a test using mailchimp_send_test
3. Send the campaign using mailchimp_send_campaign

Required fields: list_id, subject_line, from_name, reply_to

Returns the created campaign ID and details.`,
    inputSchema: CreateCampaignSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const requestBody = {
        type: params.type,
        recipients: {
          list_id: params.list_id,
        },
        settings: {
          subject_line: params.subject_line,
          preview_text: params.preview_text,
          title: params.title || params.subject_line,
          from_name: params.from_name,
          reply_to: params.reply_to,
        },
      };

      const campaign = await makeApiRequest<MailchimpCampaign>(
        "/campaigns",
        "POST",
        requestBody
      );

      return {
        content: [
          {
            type: "text",
            text: `# Campaign Created Successfully\n\n${formatCampaign(campaign)}\n\n` +
              `**Next steps:**\n` +
              `1. Set content: mailchimp_set_content(campaign_id="${campaign.id}", html="...")\n` +
              `2. Send test: mailchimp_send_test(campaign_id="${campaign.id}", test_emails=[...])\n` +
              `3. Send: mailchimp_send_campaign(campaign_id="${campaign.id}")`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: handleApiError(error) }],
      };
    }
  }
);

server.registerTool(
  "mailchimp_set_content",
  {
    title: "Set Campaign Content",
    description: `Set the HTML and/or plain text content for a campaign.

You can provide:
- html: Raw HTML content for the email
- plain_text: Plain text version (auto-generated from HTML if omitted)
- template_id: Use a saved Mailchimp template instead

For images, either:
- Upload via mailchimp_upload_image and use the returned URL
- Use externally hosted image URLs directly in your HTML`,
    inputSchema: SetContentSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const requestBody: Record<string, unknown> = {};

      if (params.template_id) {
        requestBody.template = { id: params.template_id };
      } else {
        if (params.html) {
          requestBody.html = params.html;
        }
        if (params.plain_text) {
          requestBody.plain_text = params.plain_text;
        }
      }

      if (!params.html && !params.template_id) {
        return {
          content: [
            {
              type: "text",
              text: "Error: You must provide either 'html' content or a 'template_id'.",
            },
          ],
        };
      }

      await makeApiRequest(
        `/campaigns/${params.campaign_id}/content`,
        "PUT",
        requestBody
      );

      return {
        content: [
          {
            type: "text",
            text: `# Content Set Successfully\n\n` +
              `Campaign ${params.campaign_id} content has been updated.\n\n` +
              `**Next steps:**\n` +
              `1. Send test: mailchimp_send_test(campaign_id="${params.campaign_id}", test_emails=[...])\n` +
              `2. Send: mailchimp_send_campaign(campaign_id="${params.campaign_id}")`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: handleApiError(error) }],
      };
    }
  }
);

server.registerTool(
  "mailchimp_send_test",
  {
    title: "Send Test Email",
    description: `Send a test email for a campaign before sending to the full list.

The campaign must have content set before sending a test.
You can send to up to 5 email addresses.

Note: Merge tags (like *|FNAME|*) won't populate in test emails
since they're not sent to actual contacts.`,
    inputSchema: SendTestSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const requestBody = {
        test_emails: params.test_emails,
        send_type: params.send_type,
      };

      await makeApiRequest(
        `/campaigns/${params.campaign_id}/actions/test`,
        "POST",
        requestBody
      );

      return {
        content: [
          {
            type: "text",
            text: `# Test Email Sent Successfully\n\n` +
              `Test email sent to: ${params.test_emails.join(", ")}\n` +
              `Type: ${params.send_type}\n\n` +
              `Check your inbox to verify the email looks correct.\n\n` +
              `**When ready to send:**\n` +
              `mailchimp_send_campaign(campaign_id="${params.campaign_id}")`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: handleApiError(error) }],
      };
    }
  }
);

server.registerTool(
  "mailchimp_send_campaign",
  {
    title: "Send Campaign",
    description: `Send a campaign to its full audience.

WARNING: This sends the campaign immediately to all recipients.
Make sure you have:
1. Set the campaign content
2. Verified with a test email
3. Confirmed the audience is correct

This action cannot be undone.`,
    inputSchema: SendCampaignSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: false,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      await makeApiRequest(
        `/campaigns/${params.campaign_id}/actions/send`,
        "POST"
      );

      return {
        content: [
          {
            type: "text",
            text: `# Campaign Sent Successfully\n\n` +
              `Campaign ${params.campaign_id} has been sent to its audience.\n\n` +
              `The campaign is now being processed by Mailchimp and will be delivered shortly.`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: handleApiError(error) }],
      };
    }
  }
);

server.registerTool(
  "mailchimp_upload_image",
  {
    title: "Upload Image to File Manager",
    description: `Upload an image to Mailchimp's File Manager.

The image must be base64-encoded. Supported formats: PNG, JPG, GIF, BMP.
Maximum file size: 1MB.

Returns the full URL of the uploaded image, which you can use in campaign HTML content.`,
    inputSchema: UploadImageSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const requestBody: Record<string, unknown> = {
        name: params.name,
        file_data: params.file_data,
      };

      if (params.folder_id) {
        requestBody.folder_id = params.folder_id;
      }

      const file = await makeApiRequest<MailchimpFile>(
        "/file-manager/files",
        "POST",
        requestBody
      );

      return {
        content: [
          {
            type: "text",
            text: `# Image Uploaded Successfully\n\n` +
              `- **Name**: ${file.name}\n` +
              `- **ID**: ${file.id}\n` +
              `- **URL**: ${file.full_size_url}\n` +
              `- **Size**: ${file.size} bytes\n\n` +
              `Use this URL in your campaign HTML:\n` +
              `\`<img src="${file.full_size_url}" alt="${file.name}" />\``,
          },
        ],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: handleApiError(error) }],
      };
    }
  }
);

server.registerTool(
  "mailchimp_list_files",
  {
    title: "List Files in File Manager",
    description: `List images and files in your Mailchimp File Manager.

Returns file names, IDs, and URLs that can be used in campaign content.`,
    inputSchema: ListFilesSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const data = await makeApiRequest<{ files: MailchimpFile[] }>(
        `/file-manager/files?count=${params.count}`
      );

      const files = data.files || [];

      if (files.length === 0) {
        return {
          content: [{ type: "text", text: "No files found in File Manager." }],
        };
      }

      const lines = ["# File Manager Files\n"];
      for (const file of files) {
        lines.push(`## ${file.name}`);
        lines.push(`- **ID**: ${file.id}`);
        lines.push(`- **URL**: ${file.full_size_url}`);
        lines.push(`- **Type**: ${file.type}`);
        lines.push(`- **Size**: ${file.size} bytes`);
        lines.push("");
      }

      return {
        content: [{ type: "text", text: lines.join("\n") }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: handleApiError(error) }],
      };
    }
  }
);

// ============================================================================
// Main
// ============================================================================

async function main() {
  if (!MAILCHIMP_API_KEY) {
    console.error(
      "ERROR: MAILCHIMP_API_KEY environment variable is required.\n" +
        "Get your API key from: Account > Extras > API keys\n" +
        "Format should be: 'apikey-dc' (e.g., 'abc123xyz-us6')"
    );
    process.exit(1);
  }

  // Validate API key format
  try {
    getDataCenter();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Mailchimp MCP Server running via stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
