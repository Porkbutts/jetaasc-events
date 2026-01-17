#!/usr/bin/env node
/**
 * Google Forms MCP Server
 *
 * An MCP server for creating Google Forms from templates using service account authentication.
 * Supports copying templates, updating title/description, publishing, and making forms public.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { google, forms_v1, drive_v3 } from "googleapis";
import { readFile } from "node:fs/promises";
import { z } from "zod";

// Environment variables
const SERVICE_ACCOUNT_KEY_PATH = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH;
const SERVICE_ACCOUNT_KEY_JSON = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
const DEFAULT_TEMPLATE_ID = process.env.GOOGLE_FORMS_TEMPLATE_ID;

// Google API clients (initialized on first use)
let formsClient: forms_v1.Forms | null = null;
let driveClient: drive_v3.Drive | null = null;
let authClient: InstanceType<typeof google.auth.JWT> | null = null;

/**
 * Initialize Google API clients with service account credentials
 */
async function getClients(): Promise<{
  forms: forms_v1.Forms;
  drive: drive_v3.Drive;
  auth: InstanceType<typeof google.auth.JWT>;
}> {
  if (formsClient && driveClient && authClient) {
    return { forms: formsClient, drive: driveClient, auth: authClient };
  }

  let credentials: { client_email: string; private_key: string };

  if (SERVICE_ACCOUNT_KEY_JSON) {
    try {
      credentials = JSON.parse(SERVICE_ACCOUNT_KEY_JSON);
    } catch {
      throw new Error(
        "GOOGLE_SERVICE_ACCOUNT_KEY contains invalid JSON. " +
          "Ensure it contains the full service account key JSON."
      );
    }
  } else if (SERVICE_ACCOUNT_KEY_PATH) {
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
      "Google credentials not configured. " +
        "Set either GOOGLE_SERVICE_ACCOUNT_KEY_PATH (path to JSON file) or " +
        "GOOGLE_SERVICE_ACCOUNT_KEY (JSON content) environment variable."
    );
  }

  // Create JWT auth client with required scopes
  authClient = new google.auth.JWT({
    email: credentials.client_email,
    key: credentials.private_key,
    scopes: [
      "https://www.googleapis.com/auth/forms.body",
      "https://www.googleapis.com/auth/drive",
    ],
  });

  formsClient = google.forms({ version: "v1", auth: authClient });
  driveClient = google.drive({ version: "v3", auth: authClient });

  return { forms: formsClient, drive: driveClient, auth: authClient };
}

/**
 * Format a form for display
 */
function formatForm(
  form: forms_v1.Schema$Form,
  responderUrl?: string
): string {
  const lines: string[] = [];
  lines.push(`## ${form.info?.title || "(No title)"}`);
  lines.push(`- **Form ID**: ${form.formId}`);

  if (form.info?.documentTitle) {
    lines.push(`- **Document Title**: ${form.info.documentTitle}`);
  }

  if (form.info?.description) {
    lines.push(`- **Description**: ${form.info.description}`);
  }

  if (responderUrl) {
    lines.push(`- **Responder URL**: ${responderUrl}`);
  } else if (form.responderUri) {
    lines.push(`- **Responder URL**: ${form.responderUri}`);
  }

  if (form.linkedSheetId) {
    lines.push(`- **Linked Sheet ID**: ${form.linkedSheetId}`);
  }

  const questionCount = form.items?.filter((item) => item.questionItem)?.length || 0;
  if (questionCount > 0) {
    lines.push(`- **Questions**: ${questionCount}`);
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
      return "Error: Form or template not found. Check the form ID and ensure the service account has access.";
    }

    if (message.includes("forbidden") || message.includes("403")) {
      return (
        "Error: Access denied. Ensure the template form is shared with the service account email " +
        "(found in your service account JSON as 'client_email')."
      );
    }

    if (message.includes("insufficientPermissions")) {
      return (
        "Error: Insufficient permissions. The service account needs Editor access " +
        "on the template form."
      );
    }

    return `Error: ${message}`;
  }

  return `Error: ${String(error)}`;
}

// Create MCP server
const server = new McpServer({
  name: "google-forms-mcp-server",
  version: "1.0.0",
});

// Zod Schemas
const CreateFromTemplateSchema = z
  .object({
    template_id: z
      .string()
      .optional()
      .describe(
        "Form ID of the template to copy. Uses GOOGLE_FORMS_TEMPLATE_ID env var if not provided."
      ),
    title: z
      .string()
      .min(1)
      .describe("Title of the new form (shown to responders)"),
    description: z
      .string()
      .optional()
      .describe("Description of the form (shown to responders)"),
    document_title: z
      .string()
      .optional()
      .describe(
        "Document title shown in Google Drive. Defaults to the form title if not provided."
      ),
    make_public: z
      .boolean()
      .default(true)
      .describe("Make the form accessible to anyone with the link (default: true)"),
  })
  .strict();

const GetFormSchema = z
  .object({
    form_id: z.string().describe("ID of the form to retrieve"),
  })
  .strict();

const UpdateFormSchema = z
  .object({
    form_id: z.string().describe("ID of the form to update"),
    title: z.string().optional().describe("New title for the form"),
    description: z.string().optional().describe("New description for the form"),
  })
  .strict();

const ListResponsesSchema = z
  .object({
    form_id: z.string().describe("ID of the form to get responses from"),
  })
  .strict();

// Register Tools

server.registerTool(
  "gforms_create_from_template",
  {
    title: "Create Form from Template",
    description: `Create a new Google Form by copying a template.

This tool performs the following steps:
1. Copies the template form (via Drive API)
2. Updates the title and description (via Forms API)
3. Publishes the form and enables responses (via Forms API)
4. Optionally makes it public (anyone with link can respond)

Returns the new form's ID and responder URL.

Note: The template form must be shared with the service account email.`,
    inputSchema: CreateFromTemplateSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: true,
    },
  },
  async (params) => {
    const templateId = params.template_id || DEFAULT_TEMPLATE_ID;
    if (!templateId) {
      return {
        content: [
          {
            type: "text",
            text: "Error: No template_id provided and GOOGLE_FORMS_TEMPLATE_ID environment variable is not set.",
          },
        ],
      };
    }

    try {
      const { forms, drive, auth } = await getClients();

      // Step 1: Copy the template form via Drive API
      const copyResponse = await drive.files.copy({
        fileId: templateId,
        requestBody: {
          name: params.document_title || params.title,
        },
      });

      const newFormId = copyResponse.data.id;
      if (!newFormId) {
        throw new Error("Failed to copy template: no form ID returned");
      }

      // Step 2: Update title and description via Forms API
      const updateRequests: forms_v1.Schema$Request[] = [];

      // Always update the title
      updateRequests.push({
        updateFormInfo: {
          info: {
            title: params.title,
            description: params.description || undefined,
          },
          updateMask: params.description ? "title,description" : "title",
        },
      });

      await forms.forms.batchUpdate({
        formId: newFormId,
        requestBody: {
          requests: updateRequests,
        },
      });

      // Step 3: Publish the form and enable responses
      // Note: setPublishSettings is a newer API method - use raw request since SDK may not have it
      try {
        const tokens = await auth.authorize();
        const accessToken = tokens.access_token;

        const publishResponse = await fetch(
          `https://forms.googleapis.com/v1/forms/${newFormId}:setPublishSettings`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${accessToken}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              publishSettings: {
                publishState: {
                  isPublished: true,
                  isAcceptingResponses: true,
                },
              },
            }),
          }
        );

        if (!publishResponse.ok) {
          // This is expected for forms copied before March 2026 - they're already published
          console.error("Note: Could not set publish settings:", await publishResponse.text());
        }
      } catch (publishError) {
        // Older forms may not support publish settings - that's OK, they're published by default
        console.error("Note: Could not set publish settings:", publishError);
      }

      // Step 4: Make the form public (anyone with link) if requested
      if (params.make_public) {
        await drive.permissions.create({
          fileId: newFormId,
          requestBody: {
            type: "anyone",
            role: "reader",
          },
        });
      }

      // Get the final form details
      const formResponse = await forms.forms.get({
        formId: newFormId,
      });

      const form = formResponse.data;
      const responderUrl = form.responderUri || `https://docs.google.com/forms/d/e/${newFormId}/viewform`;

      return {
        content: [
          {
            type: "text",
            text: `# Form Created Successfully\n\n${formatForm(form, responderUrl)}\n\n` +
              `**Edit URL**: https://docs.google.com/forms/d/${newFormId}/edit`,
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
  "gforms_get_form",
  {
    title: "Get Form Details",
    description: `Get details of a Google Form including its title, description, and responder URL.`,
    inputSchema: GetFormSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const { forms } = await getClients();

      const response = await forms.forms.get({
        formId: params.form_id,
      });

      return {
        content: [
          {
            type: "text",
            text: `# Form Details\n\n${formatForm(response.data)}\n\n` +
              `**Edit URL**: https://docs.google.com/forms/d/${params.form_id}/edit`,
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
  "gforms_update_form",
  {
    title: "Update Form",
    description: `Update a form's title and/or description.

Only provide the fields you want to change.`,
    inputSchema: UpdateFormSchema,
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    if (!params.title && !params.description) {
      return {
        content: [
          {
            type: "text",
            text: "Error: No fields provided to update. Provide title and/or description.",
          },
        ],
      };
    }

    try {
      const { forms } = await getClients();

      const updateMaskParts: string[] = [];
      const info: forms_v1.Schema$Info = {};

      if (params.title) {
        info.title = params.title;
        updateMaskParts.push("title");
      }

      if (params.description !== undefined) {
        info.description = params.description;
        updateMaskParts.push("description");
      }

      await forms.forms.batchUpdate({
        formId: params.form_id,
        requestBody: {
          requests: [
            {
              updateFormInfo: {
                info,
                updateMask: updateMaskParts.join(","),
              },
            },
          ],
        },
      });

      // Get the updated form
      const response = await forms.forms.get({
        formId: params.form_id,
      });

      return {
        content: [
          {
            type: "text",
            text: `# Form Updated Successfully\n\n${formatForm(response.data)}`,
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
  "gforms_list_responses",
  {
    title: "List Form Responses",
    description: `List all responses submitted to a form.

Returns response IDs, submission times, and answer summaries.`,
    inputSchema: ListResponsesSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async (params) => {
    try {
      const { forms } = await getClients();

      const response = await forms.forms.responses.list({
        formId: params.form_id,
      });

      const responses = response.data.responses || [];

      if (responses.length === 0) {
        return {
          content: [
            {
              type: "text",
              text: "No responses found for this form.",
            },
          ],
        };
      }

      const lines: string[] = [`# Form Responses (${responses.length})\n`];

      for (const resp of responses) {
        lines.push(`## Response ${resp.responseId}`);
        lines.push(`- **Submitted**: ${resp.lastSubmittedTime || "Unknown"}`);

        if (resp.answers) {
          const answerCount = Object.keys(resp.answers).length;
          lines.push(`- **Answers**: ${answerCount}`);
        }

        lines.push("");
      }

      return {
        content: [
          {
            type: "text",
            text: lines.join("\n"),
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

  if (!DEFAULT_TEMPLATE_ID) {
    console.error(
      "NOTE: GOOGLE_FORMS_TEMPLATE_ID environment variable is not set.\n" +
        "You will need to provide template_id in each gforms_create_from_template call."
    );
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Google Forms MCP Server running via stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
