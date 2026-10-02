const { api, json } = require("./lib");

exports.handler = async (event) => {
  if (event.httpMethod !== "GET") return json(405, { ok: false, error: "Método no permitido" });
  const token = String((event.queryStringParameters || {}).token || "").trim();
  try {
    const { status, data } = await api("/api/oferta-estado?token=" + encodeURIComponent(token), {
      method: "GET",
    });
    return json(status, data);
  } catch (err) {
    return json(err.status || 502, { ok: false, error: err.message });
  }
};
