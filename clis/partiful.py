#!/usr/bin/env python3
"""CLI to create, update, and delete Partiful events."""

import argparse
import json
import mimetypes
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import uuid
from datetime import datetime, timezone

THEMES = [
    "aquamarine", "aquatica", "aurora", "beach", "beer", "blacklight", "bokeh",
    "bubblegum", "candy", "champagne", "cloudflow", "crystal", "customColor",
    "darkSky", "daybreak", "forest", "galaxy", "girlyMac", "golden", "grass",
    "ice", "ink", "kaleidoscope", "karaoke", "komorebi", "lavaRave", "lofiGrass",
    "meadows", "midday", "midnight", "oxblood", "parchment", "phantom", "pool",
    "rainbowGlitter", "rush", "shroomset", "ski", "slate", "snowPaws", "starburst",
    "storybloom", "sunrise", "sunset", "toile", "twilight", "watercolor", "whisky",
    "winterWonderland",
]
EFFECTS = [
    "none", "balloons", "basketball", "beachballs", "beerPong", "bows", "bubbles",
    "bunnies", "cascade", "cash", "christmasLights", "confetti", "confettiExplosion",
    "crayons", "dandelions", "disco", "doge", "fireCannons", "fireflies", "fireworks",
    "foils", "football", "gelt", "ghosts", "gingerbread", "ginkgo", "glowbugs",
    "graduation", "handprints", "hearts", "kisses", "lasers", "leaves", "lightning",
    "lights", "magnolias", "pizzaToppings", "presents", "sakura", "shadowBats",
    "shamrock", "smoke", "snowflakes", "snowman", "spaceInvaders", "sparkles",
    "spiders", "spiderwebs", "starrySky", "stars", "sunbeams", "tennis",
    "thanksgivingFood", "winterCreatures",
]
QUESTION_TYPES = [
    "short_answer", "select", "email", "instagram", "twitter", "tiktok",
    "snapchat", "linkedin",
]
QUESTION_HELP = (
    'Add an RSVP questionnaire question. Repeatable. Format: "TEXT[|attr]..." '
    'where each attr is a type (' + ", ".join(QUESTION_TYPES) + '), the '
    'literal "required", or "options:A,B,C" for a dropdown. Defaults to an '
    'optional short answer; "options:" implies select. e.g. '
    '--question "T-shirt size|options:S,M,L|required"'
)
QUESTIONS_JSON_HELP = (
    'Questions as a JSON array, for text awkward to inline: '
    '[{"text": "...", "type": "short_answer", "required": false, '
    '"options": []}]. Mutually exclusive with --question.'
)
CREATE_EPILOG = """\
Times are UTC. --timezone only labels how the event page displays them, it does
not convert --date/--time. To convert from a UTC offset, add the offset back:
6pm at UTC-8 is 02:00 the next day; 6pm at UTC-7 is 01:00 the next day.

Location: a full "Venue, Street, City, ST ZIP" (3+ comma-separated parts) gets a
structured location, meaning the map pin and Apple/Google Maps links on the event
page. A plainer string only sets the display name, and the page reads "no location
set". No Google API key is needed either way.

Questions (--question) are asked when a guest RSVPs. The spec is TEXT followed by
optional |-separated attributes:

  --question "Any dietary restrictions?"
  --question "T-shirt size|options:S,M,L|required"
  --question "Best email|email|required"

Prints JSON: eventId, url, image, public, questions."""

UPDATE_EPILOG = """\
Only the fields you pass are changed. --date and --time must be given together,
and are UTC (see 'create --help').

Questions replace the whole set, so pass every question you want to keep. They are
stored as an append-only list of versions: Partiful asks the newest version, and
each guest's answers record which version they answered, so earlier versions and
their responses survive an update. --no-questionnaire stops the questions being
asked without discarding any of it.

Prints JSON: the event id and which fields were touched."""

LOGIN_EPILOG = """\
Without --code this prompts for the code on stdin, so it needs a terminal. When
scripting, or from a tool that cannot answer a prompt, use the two-step flow:

  partiful send-code 8185551234
  partiful login 8185551234 --code 123456

Auth is saved to .partiful-auth.json next to this script (override with
PARTIFUL_AUTH). The refresh token is renewed on every command, so logging in
again is only needed if that file is lost or the token is revoked."""

GET_EPILOG = """\
Prints the event document's top-level fields as JSON. Nested values (maps and
arrays, e.g. displaySettings or questionnaireVersions) are printed in Firestore's
typed form rather than flattened."""

FIREBASE_API_KEY = "AIzaSyCky6PJ7cHRdBKk5X7gjuWERWaKWBHr4_k"
FIRESTORE_BASE = "https://firestore.googleapis.com/v1/projects/getpartiful/databases/(default)/documents"
# Resolve symlinks so the auth file is found next to the real script, not next
# to a `partiful` symlink sitting on PATH.
CONFIG_PATH = os.environ.get("PARTIFUL_AUTH") or os.path.join(
    os.path.dirname(os.path.realpath(__file__)), ".partiful-auth.json")


def load_auth():
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: No auth config found at {CONFIG_PATH}", file=sys.stderr)
        print("Run: partiful login <phone_number>", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_auth(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_fresh_token(refresh_token):
    """Exchange refresh token for a fresh Firebase JWT."""
    url = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://partiful.com/",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["id_token"], data["refresh_token"]


def get_token():
    """Load auth, refresh token, save new refresh token, return JWT."""
    auth = load_auth()
    token, new_refresh = get_fresh_token(auth["refresh_token"])
    auth["refresh_token"] = new_refresh
    save_auth(auth)
    return token, auth["uid"]


def api_call(endpoint, params, auth_token, uid):
    """Make an authenticated call to api.partiful.com."""
    url = f"https://api.partiful.com/{endpoint}"
    body = json.dumps({
        "data": {
            "params": params,
            "userId": uid,
        }
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def upload_image(file_path, token, uid):
    """Upload an image to Partiful and return the upload data."""
    content_type = mimetypes.guess_type(file_path)[0] or "image/png"
    filename = os.path.basename(file_path)
    boundary = uuid.uuid4().hex

    with open(file_path, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        "https://api.partiful.com/uploadPhoto?uploadType=event_poster",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "x-user-id": uid,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["uploadData"]


def set_event_image(event_id, upload_data, token):
    """Set the image field on an event document via Firestore PATCH."""
    image_fields = {
        "image": {"mapValue": {"fields": {
            "type": {"stringValue": upload_data["type"]},
            "name": {"stringValue": upload_data["name"]},
            "source": {"stringValue": "upload"},
            "url": {"stringValue": upload_data["url"]},
            "width": {"integerValue": str(upload_data["width"])},
            "height": {"integerValue": str(upload_data["height"])},
            "contentType": {"stringValue": upload_data["contentType"]},
            "crop": {"nullValue": None},
            "upload": {"mapValue": {"fields": {
                "type": {"stringValue": upload_data["type"]},
                "name": {"stringValue": upload_data["name"]},
                "path": {"stringValue": upload_data["path"]},
                "url": {"stringValue": upload_data["url"]},
                "storageUri": {"stringValue": upload_data["storageUri"]},
                "contentType": {"stringValue": upload_data["contentType"]},
                "size": {"integerValue": str(upload_data["size"])},
                "width": {"integerValue": str(upload_data["width"])},
                "height": {"integerValue": str(upload_data["height"])},
                "fileCreatedAt": {"stringValue": upload_data["fileCreatedAt"]},
                "uploadedAt": {"stringValue": upload_data["uploadedAt"]},
            }}},
        }}}
    }
    url = f"{FIRESTORE_BASE}/events/{event_id}?updateMask.fieldPaths=image"
    body = json.dumps({"fields": image_fields}).encode()
    req = urllib.request.Request(url, data=body, method="PATCH", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        json.loads(resp.read())


def firestore_delete(event_id, token):
    """Delete event via Firestore REST API."""
    url = f"{FIRESTORE_BASE}/events/{event_id}"
    req = urllib.request.Request(url, method="DELETE", headers={
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(req) as resp:
        return resp.status


def firestore_get(event_id, token):
    """Read event from Firestore."""
    url = f"{FIRESTORE_BASE}/events/{event_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _fs_str(v):
    return {"stringValue": v}


def _fs_arr(vals):
    return {"arrayValue": {"values": [{"stringValue": v} for v in vals]}}


def location_fs_fields(location_str):
    """Build Firestore-typed fields for a location.

    Always sets locationName + location (plain display strings). When the
    string has enough comma-separated parts to look like a real address
    ("Venue, Street, City, ST ZIP"), also builds the structured locationInfo
    map that Partiful needs to show a proper location (map pin, maps links)
    instead of "no location set". Maps URLs are built from the address text,
    so no Google API key is required.
    """
    fields = {
        "locationName": _fs_str(location_str),
        "location": _fs_str(location_str),
    }
    parts = [p.strip() for p in location_str.split(",") if p.strip()]
    if len(parts) >= 3:
        name = parts[0]
        street = parts[1]
        rest = parts[2:]
        if len(rest) >= 2:
            city = rest[0]
            state_zip = rest[-1]
            state = state_zip.split()[0] if state_zip.split() else state_zip
            line2_full = f"{city}, {state_zip}"
            line2_disp = f"{city}, {state}"
            approx = f"{city}, {state}"
        else:
            city = rest[0]
            line2_full = city
            line2_disp = city
            approx = city
        has_zip = bool(re.search(r"\b\d{5}(?:-\d{4})?\b", location_str))
        query = urllib.parse.quote(f"{street}, {line2_full}")
        fields["locationInfo"] = {"mapValue": {"fields": {
            "type": _fs_str("structured"),
            "hasPostCode": {"booleanValue": has_zip},
            "mapsInfo": {"mapValue": {"fields": {
                "name": _fs_str(name),
                "addressLines": _fs_arr([street, line2_full]),
                "approximateLocation": _fs_str(approx),
                "appleMapsUrl": _fs_str(f"http://maps.apple.com/?address={query}"),
                "googleMapsUrl": _fs_str(
                    f"https://www.google.com/maps/search/?api=1&query={query}"),
            }}},
            "displayAddressLines": _fs_arr([street, line2_disp]),
        }}}
    return fields


def parse_question(spec):
    """Parse a --question spec into a question dict.

    Format: "TEXT[|attr][|attr]..." where each attr is a type name
    (short_answer, select, email, instagram, twitter, tiktok, snapchat,
    linkedin), the literal "required", or "options:A,B,C" for a dropdown.
    Defaults to an optional short answer; "options:" implies type select.
    """
    parts = [p.strip() for p in spec.split("|")]
    text = parts[0]
    if not text:
        print(f"Error: question spec has no text: {spec!r}", file=sys.stderr)
        sys.exit(1)

    qtype = None
    required = False
    options = []
    for attr in parts[1:]:
        low = attr.lower()
        if low == "required":
            required = True
        elif low.startswith("options:"):
            options = [o.strip() for o in attr[len("options:"):].split(",") if o.strip()]
        elif low in QUESTION_TYPES:
            qtype = low
        else:
            print(f"Error: unknown question attribute {attr!r} in {spec!r}.",
                  file=sys.stderr)
            print(f"Expected 'required', 'options:A,B,C', or a type: "
                  f"{', '.join(QUESTION_TYPES)}", file=sys.stderr)
            sys.exit(1)

    return validate_question({
        "text": text,
        "type": qtype or ("select" if options else "short_answer"),
        "required": required,
        "options": options,
    })


def validate_question(q):
    """Normalize and sanity-check one question dict."""
    text = str(q.get("text") or "").strip()
    if not text:
        print(f"Error: question is missing text: {q!r}", file=sys.stderr)
        sys.exit(1)
    qtype = q.get("type") or "short_answer"
    if qtype not in QUESTION_TYPES:
        print(f"Error: unknown question type {qtype!r}. Valid types: "
              f"{', '.join(QUESTION_TYPES)}", file=sys.stderr)
        sys.exit(1)
    options = [str(o).strip() for o in (q.get("options") or []) if str(o).strip()]
    if qtype == "select" and not options:
        print(f"Error: question {text!r} is a dropdown but has no options. "
              f"Add 'options:A,B,C'.", file=sys.stderr)
        sys.exit(1)
    if options and qtype != "select":
        print(f"Error: question {text!r} has options but type is {qtype!r}. "
              f"Only 'select' takes options.", file=sys.stderr)
        sys.exit(1)
    return {"text": text, "type": qtype, "required": bool(q.get("required")),
            "options": options}


def collect_questions(args):
    """Build the question list from --question / --questions-json, or None."""
    if args.question and args.questions_json:
        print("Error: use either --question or --questions-json, not both.",
              file=sys.stderr)
        sys.exit(1)
    if args.question:
        return [parse_question(spec) for spec in args.question]
    if args.questions_json:
        try:
            raw = json.loads(args.questions_json)
        except json.JSONDecodeError as e:
            print(f"Error: --questions-json is not valid JSON: {e}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(raw, list) or not raw:
            print("Error: --questions-json must be a non-empty JSON array of "
                  "objects like {\"text\": ..., \"type\": ..., \"required\": ..., "
                  "\"options\": [...]}.", file=sys.stderr)
            sys.exit(1)
        return [validate_question(q) for q in raw]
    return None


def question_fs(q, qid):
    """Firestore-typed value for one question."""
    fields = {
        "id": _fs_str(qid),
        "text": _fs_str(q["text"]),
        "required": {"booleanValue": q["required"]},
        "type": _fs_str(q["type"]),
    }
    if q["options"]:
        fields["options"] = _fs_arr(q["options"])
    return {"mapValue": {"fields": fields}}


def questionnaire_fs_fields(questions, uid, existing_versions):
    """Append a new questionnaire version and enable the questionnaire.

    Partiful reads the *last* entry of questionnaireVersions as the live
    questionnaire, and guest responses store the index of the version they
    answered, so old versions are kept rather than overwritten.
    """
    now_ms = int(time.time() * 1000)
    version = {"mapValue": {"fields": {
        "questions": {"arrayValue": {"values": [
            question_fs(q, str(now_ms + i)) for i, q in enumerate(questions)
        ]}},
        "createdAt": {"timestampValue": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"},
        "createdBy": {"referenceValue":
                      f"projects/getpartiful/databases/(default)/documents/users/{uid}"},
    }}}
    return {
        "questionnaireEnabled": {"booleanValue": True},
        "questionnaireVersions": {"arrayValue": {
            "values": list(existing_versions) + [version]}},
    }


def existing_questionnaire_versions(event_id, token):
    """Read the current questionnaireVersions array off an event."""
    doc = firestore_get(event_id, token)
    field = doc.get("fields", {}).get("questionnaireVersions", {})
    return field.get("arrayValue", {}).get("values", [])


def patch_event(event_id, fs_fields, token):
    """PATCH a set of Firestore-typed fields onto an event document."""
    mask = "&".join(f"updateMask.fieldPaths={k}" for k in fs_fields)
    url = f"{FIRESTORE_BASE}/events/{event_id}?{mask}"
    body = json.dumps({"fields": fs_fields}).encode()
    req = urllib.request.Request(url, data=body, method="PATCH", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def normalize_phone(phone):
    if not phone.startswith("+"):
        phone = "+1" + phone
    return phone


def send_sms(phone):
    """Send SMS auth code."""
    url = "https://api.partiful.com/sendAuthCodeTrusted"
    body = json.dumps({"data": {"params": {"phoneNumber": phone}}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        json.loads(resp.read())


def complete_login(phone, code):
    """Exchange SMS code for auth tokens and save."""
    # Exchange code for custom token
    url = "https://api.partiful.com/getLoginToken"
    body = json.dumps({"data": {"params": {"phoneNumber": phone, "authCode": code}}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    custom_token = result["result"]["data"]["token"]

    # Exchange custom token for Firebase JWT
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_API_KEY}"
    body = json.dumps({"token": custom_token, "returnSecureToken": True}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Referer": "https://partiful.com/",
    })
    with urllib.request.urlopen(req) as resp:
        firebase_data = json.loads(resp.read())

    # Get UID via token refresh (signIn response doesn't include it)
    refresh_token = firebase_data["refreshToken"]
    url = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://partiful.com/",
    })
    with urllib.request.urlopen(req) as resp:
        token_data = json.loads(resp.read())

    save_auth({
        "refresh_token": token_data["refresh_token"],
        "uid": token_data["user_id"],
    })
    print(f"Logged in as {token_data['user_id']}")
    print(f"Auth saved to {CONFIG_PATH}")


def cmd_send_code(args):
    """Send SMS code (non-interactive step 1)."""
    phone = normalize_phone(args.phone)
    send_sms(phone)
    print(f"SMS code sent to {phone}")


def cmd_login(args):
    """Log in interactively, or complete login with --code."""
    phone = normalize_phone(args.phone)

    if args.code:
        # Non-interactive: code provided, just complete login
        complete_login(phone, args.code)
        return

    # Prompting needs a terminal. Without one, input() would block forever with
    # no output, which looks like a hang rather than a usage error, so say so.
    if not sys.stdin.isatty():
        print("Error: 'login' without --code prompts for the code on stdin, "
              "but stdin is not a terminal.", file=sys.stderr)
        print("Use the two-step flow instead:", file=sys.stderr)
        print(f"  partiful send-code {args.phone}", file=sys.stderr)
        print(f"  partiful login {args.phone} --code <CODE>", file=sys.stderr)
        sys.exit(1)

    # Interactive: send SMS, wait for input, complete login
    send_sms(phone)
    print(f"SMS code sent to {phone}")
    code = input("Enter the code: ").strip()
    complete_login(phone, code)


def cmd_create(args):
    """Create a Partiful event."""
    questions = collect_questions(args)
    token, uid = get_token()

    start_dt = datetime.strptime(f"{args.date} {args.time}", "%Y-%m-%d %H:%M")
    start_utc = start_dt.isoformat() + ".000Z"

    end_utc = None
    if args.end_date and args.end_time:
        end_dt = datetime.strptime(f"{args.end_date} {args.end_time}", "%Y-%m-%d %H:%M")
        end_utc = end_dt.isoformat() + ".000Z"

    event = {
        "title": args.title,
        "startDate": start_utc,
        "endDate": end_utc,
        "timezone": args.timezone,
        "status": "UNSAVED",
        "visibility": "public",
        "displaySettings": {
            "theme": args.theme,
            "effect": args.effect,
            "titleFont": "display",
        },
        "showHostList": True,
        "showGuestCount": True,
        "showGuestList": True,
        "showActivityTimestamps": True,
        "displayInviteButton": True,
        "allowGuestPhotoUpload": True,
        "enableGuestReminders": True,
        "rsvpsEnabled": True,
        "allowGuestsToInviteMutuals": True,
        "rsvpButtonGlyphType": "emojis",
        "guestStatusCounts": {
            "READY_TO_SEND": 0, "SENDING": 0, "SENT": 0,
            "SEND_ERROR": 0, "DELIVERY_ERROR": 0, "INTERESTED": 0,
            "MAYBE": 0, "GOING": 0, "DECLINED": 0, "WAITLIST": 0,
            "PENDING_APPROVAL": 0, "APPROVED": 0, "WITHDRAWN": 0,
            "RESPONDED_TO_FIND_A_TIME": 0, "WAITLISTED_FOR_APPROVAL": 0,
            "REJECTED": 0,
        },
    }

    if args.description:
        event["description"] = args.description

    result = api_call("createEvent", {"event": event, "cohostIds": []}, token, uid)
    event_id = result["result"]["data"]

    if args.location:
        patch_event(event_id, location_fs_fields(args.location), token)

    if questions:
        patch_event(event_id, questionnaire_fs_fields(questions, uid, []), token)

    if args.image:
        upload_data = upload_image(args.image, token, uid)
        set_event_image(event_id, upload_data, token)

    if args.public:
        url = f"{FIRESTORE_BASE}/events/{event_id}?updateMask.fieldPaths=isPublic"
        body = json.dumps({"fields": {"isPublic": {"booleanValue": True}}}).encode()
        req = urllib.request.Request(url, data=body, method="PATCH", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req) as resp:
            json.loads(resp.read())

    print(json.dumps({
        "eventId": event_id,
        "url": f"https://partiful.com/e/{event_id}",
        "image": bool(args.image),
        "public": args.public,
        "questions": len(questions) if questions else 0,
    }, indent=2))


def cmd_update(args):
    """Update a Partiful event."""
    questions = collect_questions(args)
    if questions and args.no_questionnaire:
        print("Error: --no-questionnaire cannot be combined with --question / "
              "--questions-json.", file=sys.stderr)
        sys.exit(1)
    token, uid = get_token()

    fields = {}
    if args.title:
        fields["title"] = args.title
    if args.description:
        fields["description"] = args.description
    if args.date and args.time:
        start_dt = datetime.strptime(f"{args.date} {args.time}", "%Y-%m-%d %H:%M")
        fields["startDate"] = start_dt.isoformat() + "Z"

    if args.image:
        upload_data = upload_image(args.image, token, uid)
        set_event_image(args.event_id, upload_data, token)
        fields["image"] = upload_data["name"]

    if args.public:
        fields["isPublic"] = True

    if not fields and not args.location and not questions and not args.no_questionnaire:
        print("No fields to update. Use --title, --description, --location, "
              "--date + --time, --image, --public, --question, --questions-json, "
              "or --no-questionnaire.", file=sys.stderr)
        sys.exit(1)

    # Build Firestore fields for non-image updates
    fs_fields = {}
    for k, v in fields.items():
        if k == "image":
            continue  # already handled above
        if k == "startDate":
            fs_fields[k] = {"timestampValue": v}
        elif isinstance(v, bool):
            fs_fields[k] = {"booleanValue": v}
        elif isinstance(v, str):
            fs_fields[k] = {"stringValue": v}

    # Location (may add structured locationInfo alongside locationName/location)
    if args.location:
        fs_fields.update(location_fs_fields(args.location))
        fields["location"] = args.location

    # Questionnaire: append a new version, keeping prior ones intact
    if questions:
        existing = existing_questionnaire_versions(args.event_id, token)
        fs_fields.update(questionnaire_fs_fields(questions, uid, existing))
        fields["questionnaire"] = f"{len(questions)} question(s)"
    elif args.no_questionnaire:
        fs_fields["questionnaireEnabled"] = {"booleanValue": False}
        fields["questionnaire"] = "disabled"

    if fs_fields:
        mask = "&".join(f"updateMask.fieldPaths={k}" for k in fs_fields)
        url = f"{FIRESTORE_BASE}/events/{args.event_id}?{mask}"
        body = json.dumps({"fields": fs_fields}).encode()
        req = urllib.request.Request(url, data=body, method="PATCH", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req) as resp:
            json.loads(resp.read())

    print(json.dumps({"updated": args.event_id, "fields": list(fields.keys())}, indent=2))


def cmd_delete(args):
    """Delete a Partiful event."""
    token, _ = get_token()
    status = firestore_delete(args.event_id, token)
    print(json.dumps({"deleted": args.event_id, "status": status}))


def cmd_get(args):
    """Get event details."""
    token, _ = get_token()
    doc = firestore_get(args.event_id, token)
    fields = doc.get("fields", {})
    out = {}
    for k, v in fields.items():
        out[k] = list(v.values())[0]
    print(json.dumps(out, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(
        prog="partiful",
        description="Unofficial CLI for Partiful event management.",
        epilog="Run 'partiful <command> --help' for command-specific options; "
               "the create/update/login help includes the non-obvious parts "
               "(UTC handling, structured locations, RSVP questions, "
               "non-interactive login).",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>", required=True)

    # send-code (non-interactive step 1)
    send_p = sub.add_parser("send-code", help="Send SMS code")
    send_p.add_argument("phone", help="Phone number (e.g. 8185551234 or +18185551234)")

    # login (interactive, or non-interactive step 2 with --code)
    login_p = sub.add_parser(
        "login", help="Log in with phone number", epilog=LOGIN_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    login_p.add_argument("phone", help="Phone number (e.g. 8185551234 or +18185551234)")
    login_p.add_argument("--code", help="SMS code (non-interactive)")

    # create
    create_p = sub.add_parser(
        "create", help="Create an event", epilog=CREATE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    create_p.add_argument("--title", required=True)
    create_p.add_argument("--date", required=True, help="Start date YYYY-MM-DD")
    create_p.add_argument("--time", required=True, help="Start time HH:MM (24h, UTC)")
    create_p.add_argument("--end-date", help="End date YYYY-MM-DD")
    create_p.add_argument("--end-time", help="End time HH:MM (24h, UTC)")
    create_p.add_argument("--timezone", default="America/Los_Angeles")
    create_p.add_argument("--location", help="Location. Pass a full address "
                          "\"Venue, Street, City, ST ZIP\" to set a structured "
                          "location (map pin); a plain string sets just the name.")
    create_p.add_argument("--description", help="Event description")
    create_p.add_argument("--theme", default="champagne", choices=THEMES,
                          help="Theme name")
    create_p.add_argument("--effect", default="none", choices=EFFECTS,
                          help="Animation effect")
    create_p.add_argument("--image", help="Path to image file (PNG, JPG, GIF, WebP)")
    create_p.add_argument("--public", action="store_true", help="Make event publicly discoverable")
    create_p.add_argument("--question", action="append", metavar="SPEC",
                          help=QUESTION_HELP)
    create_p.add_argument("--questions-json", metavar="JSON", help=QUESTIONS_JSON_HELP)

    # update
    update_p = sub.add_parser(
        "update", help="Update an event", epilog=UPDATE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    update_p.add_argument("event_id", help="Event ID")
    update_p.add_argument("--title", help="New title")
    update_p.add_argument("--description", help="New description")
    update_p.add_argument("--location", help="New location. Pass a full address "
                          "\"Venue, Street, City, ST ZIP\" to set a structured "
                          "location (map pin); a plain string sets just the name.")
    update_p.add_argument("--date", help="New start date YYYY-MM-DD")
    update_p.add_argument("--time", help="New start time HH:MM (24h, UTC)")
    update_p.add_argument("--image", help="Path to image file (PNG, JPG, GIF, WebP)")
    update_p.add_argument("--public", action="store_true", help="Make event publicly discoverable")
    update_p.add_argument("--question", action="append", metavar="SPEC",
                          help=QUESTION_HELP + " Replaces the current question set "
                          "(as a new version; earlier versions and their responses "
                          "are kept).")
    update_p.add_argument("--questions-json", metavar="JSON", help=QUESTIONS_JSON_HELP)
    update_p.add_argument("--no-questionnaire", action="store_true",
                          help="Turn the questionnaire off (existing questions and "
                               "responses are retained, just not asked)")

    # delete
    del_p = sub.add_parser(
        "delete", help="Delete an event (permanent, not undoable)")
    del_p.add_argument("event_id", help="Event ID to delete")

    # get
    get_p = sub.add_parser(
        "get", help="Get event details", epilog=GET_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    get_p.add_argument("event_id", help="Event ID")

    args = parser.parse_args()
    cmds = {"send-code": cmd_send_code, "login": cmd_login, "create": cmd_create,
            "update": cmd_update, "delete": cmd_delete, "get": cmd_get}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
