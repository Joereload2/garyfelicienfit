const { api, json } = require("./lib");

function paymentIdFrom(event) {
  const params = event.queryStringParameters || {};
  let id = params["data.id"] || "";
  if (!id && (params.topic === "payment" || params.type === "payment")) {
    id = params.id || "";
  }
  if (event.body) {
    try {
      const body = JSON.parse(event.body);
      const data = body.data || {};
      const topic = String(body.type || body.topic || "");
      if (!topic || topic === "payment") {
        id = String(data.id || body.id || id);
      }
    } catch (e) { /* ignore */ }
  }
  return String(id || "").trim();
}

async function fetchPayment(id) {
  const token = process.env.MP_ACCESS_TOKEN || "";
  const res = await fetch("https://api.mercadopago.com/v1/payments/" + encodeURIComponent(id), {
    headers: { Authorization: "Bearer " + token, Accept: "application/json" },
  });
  const data = await res.json().catch(function () { return {}; });
  if (!res.ok) {
    const err = new Error(data.message || "No se pudo leer el pago");
    err.status = 502;
    throw err;
  }
  return data;
}

function emailFromPayment(payment) {
  const meta = payment.metadata || {};
  const payer = payment.payer || {};
  return String(meta.email || payer.email || payment.external_reference || "").trim().toLowerCase();
}

exports.handler = async (event) => {
  if (event.httpMethod !== "POST" && event.httpMethod !== "GET") {
    return json(405, { ok: false, error: "Método no permitido" });
  }
  const id = paymentIdFrom(event);
  if (!id) return json(200, { ok: true, ignored: "no-id" });
  if (!process.env.MP_ACCESS_TOKEN) {
    return json(503, { ok: false, error: "Falta MP_ACCESS_TOKEN" });
  }
  try {
    const payment = await fetchPayment(id);
    if (payment.status !== "approved") {
      return json(200, { ok: true, ignored: payment.status || "unknown" });
    }
    const email = emailFromPayment(payment);
    if (!email || email.indexOf("@") < 1) {
      return json(400, { ok: false, error: "El pago no trajo email" });
    }
    const payment_ref = "mp_" + payment.id;
    const { status, data } = await api("/internal/entitlements", {
      method: "POST",
      body: JSON.stringify({ email, payment_ref }),
    });
    if (status === 409) return json(200, { ok: true, duplicate: true, payment_ref });
    return json(status === 201 || status === 200 ? 200 : status, data);
  } catch (err) {
    return json(err.status || 502, { ok: false, error: err.message });
  }
};
