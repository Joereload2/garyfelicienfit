const API = (process.env.PLANFIT_API_URL || "").replace(/\/$/, "");
const SECRET = process.env.ADMIN_SECRET || "";

async function api(path, opts = {}) {
  if (!API) {
    const err = new Error("Falta PLANFIT_API_URL");
    err.status = 503;
    throw err;
  }
  const headers = Object.assign(
    { "Content-Type": "application/json" },
    opts.headers || {}
  );
  if (SECRET) headers["X-Admin-Secret"] = SECRET;
  const res = await fetch(API + path, Object.assign({}, opts, { headers }));
  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch (e) { data = { raw: text }; }
  return { status: res.status, data };
}

function json(status, data) {
  return {
    statusCode: status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
    body: JSON.stringify(data),
  };
}

module.exports = { API, SECRET, api, json };
