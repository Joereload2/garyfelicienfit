const { api, json } = require("./lib");

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") return json(405, { ok: false, error: "Método no permitido" });
  let body = {};
  try {
    body = JSON.parse(event.body || "{}");
  } catch (e) {
    return json(400, { ok: false, error: "JSON inválido" });
  }
  try {
    const { status, data } = await api("/api/checkout-3meses", {
      method: "POST",
      body: JSON.stringify(body),
    });
    return json(status, data);
  } catch (err) {
    return json(err.status || 502, { ok: false, error: err.message });
  }
};
