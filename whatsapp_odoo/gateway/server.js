const express = require("express");
const qrcode = require("qrcode");
const qrcodeTerminal = require("qrcode-terminal");
const { Client, LocalAuth } = require("whatsapp-web.js");

const app = express();
app.use(express.json({ limit: "2mb" }));
app.use(express.urlencoded({ extended: true }));

const port = Number(process.env.PORT || 3000);
const sessionName = process.env.SESSION_NAME || "odoo-whatsapp";

let lastQrBase64 = "";
let isReady = false;
let client;

/**
 * Create WhatsApp Client (LocalAuth manages session automatically)
 */
function createClient() {
  return new Client({
    authStrategy: new LocalAuth({ clientId: sessionName }),
    puppeteer: {
      executablePath: "/usr/bin/chromium-browser",
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    },
    takeoverOnConflict: true,
    disableSpins: true,
  });
}

/**
 * Initialize client and events
 */
function initClient() {
  client = createClient();

  client.on("qr", async (qr) => {
    console.log("📲 QR generated. Scan this now!");
    qrcodeTerminal.generate(qr, { small: true });
    const dataUrl = await qrcode.toDataURL(qr, { margin: 1 });
    lastQrBase64 = dataUrl.replace(/^data:image\/png;base64,/, "");
    isReady = false;
  });

  client.on("ready", () => {
    console.log("✅ WhatsApp client READY");
    lastQrBase64 = "";
    isReady = true;
  });

  client.on("disconnected", async (reason) => {
    console.log("❌ WhatsApp disconnected:", reason);
    isReady = false;

    // Recreate client after 5 sec
    setTimeout(() => {
      initClient();
      client.initialize();
    }, 5000);
  });

  client.on("auth_failure", (msg) => {
    console.log("❌ Auth failure:", msg);
    isReady = false;
  });

  client.initialize();
}

// Start client
initClient();

/**
 * API: GET QR
 */
app.get("/qr", (req, res) => {
  if (!lastQrBase64)
    return res.json({ qr_image_base64: "", status: "waiting" });
  return res.json({ qr_image_base64: lastQrBase64, status: "ok" });
});

/**
 * API: STATUS
 */
app.get("/status", (req, res) => {
  return res.json({ status: isReady ? "connected" : "disconnected" });
});

/**
 * API: SEND MESSAGE
 */
app.post("/send", async (req, res) => {
  const to = (req.body.to || "").toString();
  const message = (req.body.message || "").toString();

  if (!to || !message)
    return res.status(400).json({ error: "Missing to/message" });
  if (!isReady)
    return res.status(400).json({ error: "Client not connected" });

  const phone = to.replace(/[^\d]/g, "");
  const chatId = `${phone}@c.us`;

  try {
    const result = await client.sendMessage(chatId, message, { sendSeen: false });
    return res.json({ message_id: result.id.id });
  } catch (err) {
    console.error("❌ Send failed:", err);
    return res.status(500).json({ error: err.message || "Send failed" });
  }
});

/**
 * QR PAGE (browser view)
 */
app.get("/qr-page", (req, res) => {
  res.send(`
    <h2>WhatsApp Gateway QR Code</h2>
    <img src="data:image/png;base64,${lastQrBase64}" />
    <p>Status: ${isReady ? "Connected ✅" : "Disconnected ❌"}</p>
  `);
});

/**
 * SERVER START
 */
app.listen(port, () => console.log(`🚀 WhatsApp gateway listening on port ${port}`));
