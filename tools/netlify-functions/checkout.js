const { api, json } = require("./lib");

// Dos planes, los dos de 3 meses (12 semanas). La única diferencia es el contacto 1 a 1.
//   personalizado  -> cuestionario + PDF por correo. USD 30.
//   acompanamiento -> lo mismo + contacto 1 a 1 con Gary. USD 400, en promoción USD 150.
// Mercado Pago cobra en pesos chilenos: los montos en CLP se fijan en Netlify (variables de entorno).
const PLANES = {
  personalizado: {
    id: "plan-personalizado-3-meses",
    product: "plan-personalizado",
    title: "Plan personalizado 3 meses — GaryFelicienFit",
    description: "Cuestionario + plan de alimentación y entrenamiento en PDF. Un solo uso.",
    envClp: "PRICE_CLP",
    defaultClp: 28500,
  },
  acompanamiento: {
    id: "acompanamiento-3-meses",
    product: "3meses",
    title: "Acompañamiento 1 a 1, 3 meses — GaryFelicienFit",
    description: "Plan personalizado + seguimiento 1 a 1 con Gary durante 3 meses.",
    envClp: "COURSE_SALE_CLP",
    defaultClp: 142500,
  },
};

function siteUrl() {
  return (process.env.URL || process.env.DEPLOY_PRIME_URL || "").replace(/\/$/, "");
}

function priceClp(plan) {
  const n = parseInt(process.env[plan.envClp] || String(plan.defaultClp), 10);
  return Number.isFinite(n) && n >= 1000 ? n : plan.defaultClp;
}

async function createMpPreference(email, key) {
  const plan = PLANES[key];
  const token = process.env.MP_ACCESS_TOKEN || "";
  if (!token) return null;
  const site = siteUrl();
  if (!site.startsWith("https://")) {
    const err = new Error("Falta URL pública https para Mercado Pago (Netlify URL).");
    err.status = 503;
    throw err;
  }
  const success = site + "/gracias.html?paid=1&plan=" + key;
  const failure = site + "/#planes";
  const notify = site + "/.netlify/functions/mp-webhook";
  const body = {
    items: [
      {
        id: plan.id,
        title: plan.title,
        description: plan.description,
        quantity: 1,
        currency_id: "CLP",
        unit_price: priceClp(plan),
      },
    ],
    payer: { email },
    back_urls: { success, failure, pending: site + "/gracias.html?pending=1&plan=" + key },
    auto_return: "approved",
    binary_mode: true,
    external_reference: email,
    metadata: { email, product: plan.product, plan: key },
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
  const key = PLANES[body.plan] ? body.plan : "personalizado";
  try {
    if (process.env.MP_ACCESS_TOKEN) {
      const url = await createMpPreference(email, key);
      return json(200, { ok: true, mode: "mp", plan: key, url });
    }
    if (key === "personalizado" && process.env.PLANFIT_API_URL) {
      const { status, data } = await api("/api/checkout", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      return json(status, data);
    }
    return json(503, {
      ok: false,
      offline: true,
      error: "El pago en línea todavía no está activo. Escríbenos por WhatsApp y te lo dejamos listo.",
    });
  } catch (err) {
    return json(err.status || 502, { ok: false, error: err.message });
  }
};
