const { api, json } = require("./lib");

exports.handler = async () => {
  try {
    const { status, data } = await api("/api/product");
    return json(status, data);
  } catch (err) {
    const clp = parseInt(process.env.PRICE_CLP || "38000", 10);
    return json(200, {
      ok: true,
      price_usd: 40,
      price_clp: Number.isFinite(clp) ? clp : 38000,
      stripe: Boolean(process.env.STRIPE_SECRET_KEY),
      mp: Boolean(process.env.MP_ACCESS_TOKEN),
      test_checkout: false,
    });
  }
};
