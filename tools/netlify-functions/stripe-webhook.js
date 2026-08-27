const { api, json } = require("./lib");

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") return json(405, { ok: false });
  try {
    const { status, data } = await api("/webhooks/stripe", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Stripe-Signature": event.headers["stripe-signature"] || event.headers["Stripe-Signature"] || "",
      },
      body: event.body,
    });
    return json(status, data);
  } catch (err) {
    return json(err.status || 502, { ok: false, error: err.message });
  }
};
