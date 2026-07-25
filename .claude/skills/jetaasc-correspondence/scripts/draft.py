#!/usr/bin/env python3
"""Create an unsent Gmail draft, signed, optionally threaded as a reply.

Reads a JSON spec and prints the new draft's id. Handles the three things that
are easy to get wrong by hand:

  multipart/alternative  a text/plain part alongside text/html, so the draft
                         reads correctly in clients that refuse HTML

  the signature          the Gmail API never applies it; only the web compose
                         window does. Pulled live from sendAs settings so an
                         edit made in Gmail is reflected here with no code change

  reply threading        a draft joins an existing thread only when threadId,
                         In-Reply-To, References, and a matching Re: subject all
                         line up. Any one missing and Gmail starts a new thread

Spec:
  {"to": ..., "subject": ..., "body": ...,
   "cc": optional, "reply_to_message_id": optional}

Body paragraphs are separated by blank lines. URLs are linkified in the HTML
part. Nothing is ever sent.
"""
import base64
import html
import json
import re
import subprocess
import sys
from email.message import EmailMessage

BODY_CSS = "font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.5;color:#202124;"

SIG_TEXT = ("Adrian Teng-Amnuay\n"
            "Chief Administrative Officer & Webmaster, JETAASC\n"
            "Ishikawa JET 2015-2016\n"
            "818-395-7261 | adrian@jetaasc.org | jetaasc.org")


def gws(*args):
    """Run gws and return parsed stdout.

    stderr is kept separate on purpose: gws prints 'Using keyring backend' there,
    and folding it into stdout is what breaks json.loads.
    """
    r = subprocess.run(["gws", *args], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit(f"gws {' '.join(args[:4])} failed:\n{r.stdout}{r.stderr}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"gws returned non-JSON:\n{r.stdout[:400]}")


def signature_html():
    for entry in gws("gmail", "users", "settings", "sendAs", "list",
                     "--params", '{"userId":"me"}').get("sendAs", []):
        if entry.get("sendAsEmail") == "adrian@jetaasc.org" and entry.get("signature"):
            return entry["signature"]
    sys.exit("No signature set on adrian@jetaasc.org. Set one in Gmail settings first.")


def to_html(text, sig):
    blocks = []
    for para in text.strip().split("\n\n"):
        esc = html.escape(para)
        esc = re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', esc)
        blocks.append('<div style="margin:0 0 12px;">' + esc.replace("\n", "<br>") + "</div>")
    return (f'<div style="{BODY_CSS}">' + "".join(blocks)
            + '<div style="margin-top:18px;">' + sig + "</div></div>")


def thread_context(message_id):
    """Message-ID header and threadId of the message being replied to."""
    msg = gws("gmail", "users", "messages", "get", "--params",
              json.dumps({"userId": "me", "id": message_id, "format": "metadata",
                          "metadataHeaders": ["Message-ID", "Subject"]}))
    headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}
    return headers.get("message-id"), msg["threadId"], headers.get("subject", "")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    spec = json.load(open(sys.argv[1]))
    for field in ("to", "subject", "body"):
        if not spec.get(field):
            sys.exit(f"spec is missing '{field}'")

    sig = signature_html()
    msg = EmailMessage()
    msg["To"] = spec["to"]
    if spec.get("cc"):
        msg["Cc"] = spec["cc"]

    thread_id = None
    if spec.get("reply_to_message_id"):
        orig_id, thread_id, orig_subject = thread_context(spec["reply_to_message_id"])
        # Gmail needs the subject to match the thread's, Re: prefix aside, or it
        # splits the draft off into a conversation of its own.
        subject = spec["subject"]
        if not subject.lower().startswith("re:"):
            subject = "Re: " + (orig_subject or subject)
        msg["Subject"] = subject
        if orig_id:
            msg["In-Reply-To"] = orig_id
            msg["References"] = orig_id
    else:
        msg["Subject"] = spec["subject"]

    msg.set_content(spec["body"].strip() + "\n\n" + SIG_TEXT + "\n")
    msg.add_alternative(to_html(spec["body"], sig), subtype="html")

    message = {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}
    if thread_id:
        message["threadId"] = thread_id

    created = gws("gmail", "users", "drafts", "create",
                  "--params", '{"userId":"me"}',
                  "--json", json.dumps({"message": message}))
    print(f"draft id : {created['id']}")
    print(f"thread   : {created['message'].get('threadId')}"
          + ("  (replied in thread)" if thread_id else "  (new thread)"))
    print("Unsent. Review it in Gmail before sending.")


if __name__ == "__main__":
    main()
