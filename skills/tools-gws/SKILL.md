---
name: tools-gws
description: >
  Google Workspace CLI (gws) patterns, syntax, and conventions.
  Triggers when running gws commands, accessing Google Drive, Gmail, Calendar,
  Docs, Sheets, or Slides, exporting Google Docs, uploading files to Drive,
  reading emails, checking calendar agenda, or processing GWS JSON output with jq.
user-invocable: false
---

# GWS CLI Guidelines

## CLI syntax

All API parameters go through `--params` as a JSON string with quoted keys. There are no named flags like `--fileId`.

```bash
gws <service> <resource> <method> --params '{"key": "value"}'
```

Common mistakes:
- Do NOT use `--fileId`, `--mimeType`, or other API parameter names as CLI flags
- Do NOT use unquoted keys (`{fileId: "..."}`) — always use `{"fileId": "..."}`
- In zsh, double-quote sheet ranges: `--range "Sheet1!A1:D10"` (bare `!` triggers history expansion)

## Extracting IDs from Google URLs

| Service | URL pattern | ID location |
|---------|------------|-------------|
| Docs | `docs.google.com/document/d/<ID>/...` | between `/d/` and next `/` |
| Sheets | `docs.google.com/spreadsheets/d/<ID>/...` | between `/d/` and next `/` |
| Slides | `docs.google.com/presentation/d/<ID>/...` | between `/d/` and next `/` |
| Drive file | `drive.google.com/file/d/<ID>/...` | between `/d/` and next `/` |
| Drive folder | `drive.google.com/drive/folders/<ID>` | after `/folders/` |

```bash
ID=$(echo "$URL" | sed -E 's|.*/d/([A-Za-z0-9_-]+).*|\1|')
FOLDER_ID=$(echo "$URL" | sed -E 's|.*folders/([A-Za-z0-9_-]+).*|\1|')
```

## Output processing

- Always use `jq` for JSON processing — never python, awk, or grep on JSON output
- Use `--format table` for human-readable output, `--format json` (default) for piping to jq
- Stderr may show `Using keyring backend: keyring` — harmless, does not affect jq piping

## Export conventions

- Use markdown (`text/markdown`) as the mimeType for Google Docs export
- Export to `.context/tmp/` using `--output`:

```bash
gws drive files export --params '{"fileId": "FILE_ID", "mimeType": "text/markdown"}' --output .context/tmp/filename.md
```

Other export formats:

| Source | Format | mimeType |
|--------|--------|----------|
| Docs | Plain text | `text/plain` |
| Docs | Markdown | `text/markdown` |
| Sheets | CSV | `text/csv` |
| Slides | PDF | `application/pdf` |

## Pagination

- `--page-all` auto-paginates, outputs one JSON line per page (NDJSON)
- `--page-limit N` caps pages (default 10)
- Process NDJSON: `gws ... --page-all | jq -s '[.[].files[]]'`

---

## Helper commands

Prefer `+helper` commands over raw API calls. They handle parameter formatting, MIME encoding, and pagination automatically.

### Gmail

| Command | Purpose | Example |
|---------|---------|---------|
| `+triage` | Unread inbox summary | `gws gmail +triage --max 10 --query 'from:boss'` |
| `+read` | Read a message body | `gws gmail +read --id MSG_ID --headers` |
| `+send` | Send an email | `gws gmail +send --to a@b.com --subject 'Hi' --body 'text'` |
| `+reply` | Reply to a message | `gws gmail +reply --id MSG_ID --body 'thanks'` |
| `+reply-all` | Reply-all | `gws gmail +reply-all --id MSG_ID --body 'noted'` |
| `+forward` | Forward a message | `gws gmail +forward --id MSG_ID --to c@d.com` |

`+send` flags: `--cc`, `--bcc`, `--from` (alias), `-a FILE` (attach, repeatable), `--html`, `--draft`

Gmail query patterns for `+triage --query`:
- `label:my-label` — messages in a label
- `from:alice@example.com` — from a sender
- `label:updates is:unread` — unread in a label
- `subject:report newer_than:7d` — recent by subject
- `has:attachment larger:5M` — large attachments

### Calendar

| Command | Purpose | Example |
|---------|---------|---------|
| `+agenda` | Upcoming events | `gws calendar +agenda --today --format table` |
| `+insert` | Create an event | `gws calendar +insert --summary 'Standup' --start '2026-05-15T09:00:00+02:00' --end '2026-05-15T09:30:00+02:00'` |

`+agenda` flags: `--today`, `--tomorrow`, `--week`, `--days N`, `--calendar NAME`, `--timezone TZ`
`+insert` flags: `--attendee EMAIL` (repeatable), `--meet` (add Google Meet link), `--location`, `--description`

### Drive

| Command | Purpose | Example |
|---------|---------|---------|
| `+upload` | Upload a file | `gws drive +upload ./report.pdf --parent FOLDER_ID` |

### Sheets

| Command | Purpose | Example |
|---------|---------|---------|
| `+read` | Read cell values | `gws sheets +read --spreadsheet ID --range "Sheet1!A1:D10"` |
| `+append` | Append a row | `gws sheets +append --spreadsheet ID --range 'Sheet1' --values '["a","b"]'` |

### Docs

| Command | Purpose | Example |
|---------|---------|---------|
| `+write` | Append text | `gws docs +write --document DOC_ID --text 'Hello'` |

### Workflow (cross-service)

| Command | Purpose |
|---------|---------|
| `+standup-report` | Today's meetings + open tasks |
| `+meeting-prep` | Next meeting: agenda, attendees, linked docs |
| `+weekly-digest` | Weekly summary: meetings + unread count |
| `+email-to-task` | Convert a Gmail message into a Google Tasks entry |
| `+file-announce` | Announce a Drive file in a Chat space |

---

## Raw API patterns

Use raw API calls when helpers don't cover the operation.

### Drive — search files

Use `fields` to limit response size:

```bash
gws drive files list --params '{"q": "name contains '\''term'\''", "pageSize": 10, "fields": "files(id,name,mimeType,webViewLink)"}' | jq '.files[] | {id, name}'

# only Google Docs
gws drive files list --params '{"q": "mimeType='\''application/vnd.google-apps.document'\''", "pageSize": 5, "fields": "files(id,name,webViewLink)"}' | jq '.files[]'

# files in a folder
gws drive files list --params '{"q": "'\''FOLDER_ID'\'' in parents and trashed=false", "pageSize": 20, "fields": "files(id,name,mimeType,webViewLink)"}' | jq '.files[]'
```

### Gmail — raw message list

```bash
gws gmail users messages list --params '{"userId": "me", "q": "after:2026/04/22", "maxResults": 25}' | jq '.messages[] | .id'
```

### Gmail — raw message get (metadata only)

```bash
gws gmail users messages get --params '{"userId": "me", "id": "MSG_ID", "format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]}'
```

### Calendar — raw event list

```bash
gws calendar events list --params '{"calendarId": "primary", "timeMin": "2026-05-14T00:00:00Z", "maxResults": 10, "singleEvents": true, "orderBy": "startTime"}' | jq '.items[] | {summary, start: .start.dateTime}'
```

### Docs — read as plain text

```bash
gws docs documents get --params '{"documentId": "DOC_ID"}' \
  | jq -r '[.. | .textRun? // empty | .content] | join("")'
```

### Slides — extract text from all slides

```bash
gws slides presentations get --params '{"presentationId": "PRES_ID"}' \
  | jq -r '.slides[] | [.pageElements[]? | .shape?.textContent?.textElements[]? | .textRun?.content? // empty] | join("")'
```

### Sheets — resolve gid= to tab name

When a URL contains `gid=`, resolve it to a tab name before reading:

```bash
GID=$(echo "$URL" | sed -E 's|.*gid=([0-9]+).*|\1|')
SHEET_ID=$(echo "$URL" | sed -E 's|.*/d/([A-Za-z0-9_-]+).*|\1|')
TAB=$(gws sheets spreadsheets get \
  --params "{\"spreadsheetId\": \"$SHEET_ID\", \"fields\": \"sheets.properties\"}" \
  | jq -r ".sheets[] | select(.properties.sheetId == $GID) | .properties.title")
gws sheets +read --spreadsheet "$SHEET_ID" --range "$TAB"
```

### Sheets — raw read

```bash
gws sheets spreadsheets values get --params '{"spreadsheetId": "ID", "range": "Sheet1!A1:D10"}' | jq '.values'
```

## Common MIME types

| Type | MIME |
|------|------|
| Google Docs | `application/vnd.google-apps.document` |
| Google Sheets | `application/vnd.google-apps.spreadsheet` |
| Google Slides | `application/vnd.google-apps.presentation` |
| Folder | `application/vnd.google-apps.folder` |

## Schema discovery

Use `gws schema` to discover API parameters for any method:

```bash
gws schema drive.files.list
gws schema gmail.users.messages.get
gws schema calendar.events.insert
```
