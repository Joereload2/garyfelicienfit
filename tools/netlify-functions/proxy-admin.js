const { API, json } = require("./lib");

exports.handler = async () => {
  if (!API) return json(503, { ok: false, error: "Falta PLANFIT_API_URL." });
  return { statusCode: 302, headers: { Location: API + "/admin" }, body: "" };
};
