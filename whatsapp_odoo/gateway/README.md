# Free WhatsApp Web Gateway

This is a simple, self-hosted WhatsApp Web gateway that provides:
- `/qr` (fetch QR to scan)
- `/status` (connected/disconnected)
- `/send` (send message)

## Requirements
- Node.js 18+

## Install & Run
```bash
cd gateway
npm install
npm start
```

By default it runs on `http://localhost:3000`.

### Environment (optional)
- `PORT` (default 3000)
- `SESSION_NAME` (default `odoo-whatsapp`)
- `CHROME_PATH` (custom Chrome binary path)
- `WEB_VERSION_URL` (pin WhatsApp Web version HTML)

## Odoo Settings
In `WhatsApp → Settings`:
- Provider: **WhatsApp QR Gateway**
- Gateway Base URL: `http://<your-server-ip>:3000`
- QR Endpoint: `/qr`
- Status Endpoint: `/status`
- Send Endpoint: `/send`

Then go to `WhatsApp → Device` and click **Fetch QR**.

## If send fails after updates
WhatsApp Web changes sometimes break message sending. Pin a known web version:
```bash
export WEB_VERSION_URL="https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html"
npm start
```
