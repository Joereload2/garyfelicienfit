const { api, json } = require("./lib");

function siteUrl() {
  return (process.env.URL || process.env.DEPLOY_PRIME_URL || "").replace(/\/$/, "");
}

function priceClp() {
  const n = parseInt(process.env.PRICE_CLP || "38000", 10);
  return Number.isFinite(n) && n >= 1000 ? n : 38000;
}

async function createMpPreference(email) {
  const token = process.env.MP_ACCESS_TOKEN || "";
  if (!token) return null;
  const site = siteUrl();
  if (!site.startsWith("https://")) {
    const err = new Error("Falta URL pública https para Mercado Pago (Netlify URL).");
    err.status = 503;
    throw err;
  }
  const success = site + "/gracias.html?paid=1";
  const failure = site + "/#guia";
  const notify = site + "/.netlify/functions/mp-webhook";
  const body = {
    items: [
      {
        id: "guia-12-semanas",
        title: "Guía 12 semanas — GaryFelicienFit",
        description: "Plan personalizado de nutrición y entrenamiento. Un solo uso.",
        quantity: 1,
        currency_id: "CLP",
        unit_price: priceClp(),
      },
    ],
    payer: { email },
    back_urls: { success, failure, pending: site + "/gracias.html?pending=1" },
    auto_return: "approved",
    binary_mode: true,
    external_reference: email,
    metadata: { email, product: "guia-12-semanas" },
    notification_url: notify,
    statement_descriptor: "GARYFELICIENFIT",
  };
  const res = await fetch("https://api.mercadopago.com/checkout/preferences", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      Accept: "application/json",
      "X-Idempotency-Key": Date.now().toString(36) + Math.random().toString(36).slice(2),
    },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(function () { return {}; });
  if (!res.ok) {
    const err = new Error((data.message || data.error || "Mercado Pago rechazó el pago") + "");
    err.status = 502;
    throw err;
  }
  const url = token.indexOf("TEST-") === 0
    ? (data.sandbox_init_point || data.init_point)
    : (data.init_point || data.sandbox_init_point);
  if (!url) {
    const err = new Error("Mercado Pago no devolvió URL de pago");
    err.status = 502;
    throw err;
  }
  return url;
}

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") return json(405, { ok: false, error: "Método no permitido" });
  let body = {};
  try { body = JSON.parse(event.body || "{}"); } catch (e) {
    return json(400, { ok: false, error: "JSON inválido" });
  }
  const email = String(body.email || "").trim().toLowerCase();
  if (!email || email.indexOf("@") < 1) {
    return json(400, { ok: false, error: "Introduce un email válido.", field: "email" });
  }
  try {
    if (process.env.MP_ACCESS_TOKEN) {
      const url = await createMpPreference(email);
      return json(200, { ok: true, mode: "mp", url });
    }
    const { status, data } = await api("/api/checkout", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    return json(status, data);
  } catch (err) {
    return json(err.status || 502, { ok: false, error: err.message });
  }
};
