const { API, json } = require("./lib");

exports.handler = async (event) => {
  if (!API) return json(503, { ok: false, error: "Falta PLANFIT_API_URL para el formulario." });
  const path = event.path || "";
  return {
    statusCode: 302,
    headers: { Location: API + path + (event.rawQuery ? "?" + event.rawQuery : "") },
    body: "",
  };
};
