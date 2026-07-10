# Google Sheet logging (optional, ~5 minutes)

Logs every item the digest finds to a Google Sheet — a running archive
volunteers can filter, and a record of what was announced when. No
Google Cloud account or API keys needed.

## 1. Create the Sheet

New Google Sheet → name it e.g. "EA Weekly Digest Log". Add a header
row:

```
run_date | type | section | title | date | org | location | url | source
```

## 2. Add the Apps Script

Extensions → Apps Script → delete the sample code and paste:

```javascript
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var payload = JSON.parse(e.postData.contents);
  payload.rows.forEach(function (row) { sheet.appendRow(row); });
  return ContentService.createTextOutput(
    JSON.stringify({ok: true, appended: payload.rows.length})
  ).setMimeType(ContentService.MimeType.JSON);
}
```

## 3. Deploy as a web app

Deploy → New deployment → type **Web app** →
Execute as: **Me** · Who has access: **Anyone** → Deploy.
Copy the web app URL (`https://script.google.com/macros/s/…/exec`).

> "Anyone" means anyone *with this URL* can append rows to the sheet —
> they can't read it, edit anything else, or see your account. Treat
> the URL like a semi-secret.

## 4. Give the URL to the digest

- **GitHub Actions:** repo → Settings → Secrets and variables → Actions
  → New repository secret → name `SHEET_WEBHOOK_URL`, value = the URL.
- **Local runs:** `export SHEET_WEBHOOK_URL="https://…/exec"`

Next run, `health.md` will show `Google Sheet log | ✅ ok | N rows appended`.
