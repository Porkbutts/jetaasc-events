#!/usr/bin/env python3
"""CLI to create, update, and delete Partiful events."""

import argparse
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.parse
import uuid
from datetime import datetime

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
FIREBASE_API_KEY = "AIzaSyCky6PJ7cHRdBKk5X7gjuWERWaKWBHr4_k"
FIRESTORE_BASE = "https://firestore.googleapis.com/v1/projects/getpartiful/databases/(default)/documents"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), ".partiful-auth.json")


def load_auth():
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: No auth config found at {CONFIG_PATH}", file=sys.stderr)
        print("Run: python3 clis/partiful.py login <phone_number>", file=sys.stderr)
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
    else:
        # Interactive: send SMS, wait for input, complete login
        send_sms(phone)
        print(f"SMS code sent to {phone}")
        code = input("Enter the code: ").strip()
        complete_login(phone, code)


def cmd_create(args):
    """Create a Partiful event."""
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
    if args.location:
        event["locationName"] = args.location

    result = api_call("createEvent", {"event": event, "cohostIds": []}, token, uid)
    event_id = result["result"]["data"]

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
    }, indent=2))


def cmd_update(args):
    """Update a Partiful event."""
    token, uid = get_token()

    fields = {}
    if args.title:
        fields["title"] = args.title
    if args.description:
        fields["description"] = args.description
    if args.location:
        fields["locationName"] = args.location
    if args.date and args.time:
        start_dt = datetime.strptime(f"{args.date} {args.time}", "%Y-%m-%d %H:%M")
        fields["startDate"] = start_dt.isoformat() + "Z"

    if args.image:
        upload_data = upload_image(args.image, token, uid)
        set_event_image(args.event_id, upload_data, token)
        fields["image"] = upload_data["name"]

    if args.public:
        fields["isPublic"] = True

    if not fields:
        print("No fields to update. Use --title, --description, --location, --date + --time, --image, --public.", file=sys.stderr)
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
    parser = argparse.ArgumentParser(description="Partiful CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # send-code (non-interactive step 1)
    send_p = sub.add_parser("send-code", help="Send SMS code")
    send_p.add_argument("phone", help="Phone number (e.g. 8185551234 or +18185551234)")

    # login (interactive, or non-interactive step 2 with --code)
    login_p = sub.add_parser("login", help="Log in with phone number")
    login_p.add_argument("phone", help="Phone number (e.g. 8185551234 or +18185551234)")
    login_p.add_argument("--code", help="SMS code (non-interactive)")

    # create
    create_p = sub.add_parser("create", help="Create an event")
    create_p.add_argument("--title", required=True)
    create_p.add_argument("--date", required=True, help="Start date YYYY-MM-DD")
    create_p.add_argument("--time", required=True, help="Start time HH:MM (24h, UTC)")
    create_p.add_argument("--end-date", help="End date YYYY-MM-DD")
    create_p.add_argument("--end-time", help="End time HH:MM (24h, UTC)")
    create_p.add_argument("--timezone", default="America/Los_Angeles")
    create_p.add_argument("--location", help="Location name")
    create_p.add_argument("--description", help="Event description")
    create_p.add_argument("--theme", default="champagne", choices=THEMES,
                          help="Theme name")
    create_p.add_argument("--effect", default="none", choices=EFFECTS,
                          help="Animation effect")
    create_p.add_argument("--image", help="Path to image file (PNG, JPG, GIF, WebP)")
    create_p.add_argument("--public", action="store_true", help="Make event publicly discoverable")

    # update
    update_p = sub.add_parser("update", help="Update an event")
    update_p.add_argument("event_id", help="Event ID")
    update_p.add_argument("--title", help="New title")
    update_p.add_argument("--description", help="New description")
    update_p.add_argument("--location", help="New location")
    update_p.add_argument("--date", help="New start date YYYY-MM-DD")
    update_p.add_argument("--time", help="New start time HH:MM (24h, UTC)")
    update_p.add_argument("--image", help="Path to image file (PNG, JPG, GIF, WebP)")
    update_p.add_argument("--public", action="store_true", help="Make event publicly discoverable")

    # delete
    del_p = sub.add_parser("delete", help="Delete an event")
    del_p.add_argument("event_id", help="Event ID to delete")

    # get
    get_p = sub.add_parser("get", help="Get event details")
    get_p.add_argument("event_id", help="Event ID")

    args = parser.parse_args()
    cmds = {"send-code": cmd_send_code, "login": cmd_login, "create": cmd_create,
            "update": cmd_update, "delete": cmd_delete, "get": cmd_get}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
