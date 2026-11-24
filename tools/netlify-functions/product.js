const { api, json } = require("./lib");

function clp(name, def) {
  const n = parseInt(process.env[name] || String(def), 10);
  return Number.isFinite(n) ? n : def;
}

exports.handler = async () => {
  try {
    const { status, data } = await api("/api/product");
    return json(status, data);
  } catch (err) {
    return json(200, {
      ok: true,
      price_usd: 30,
      price_clp: clp("PRICE_CLP", 28500),
      course_list_usd: 400,
      course_sale_usd: 150,
      course_sale_clp: clp("COURSE_SALE_CLP", 142500),
      stripe: Boolean(process.env.STRIPE_SECRET_KEY),
      mp: Boolean(process.env.MP_ACCESS_TOKEN),
      test_checkout: false,
    });
  }
};
