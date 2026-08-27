const { api, json } = require("./lib");

exports.handler = async () => {
  try {
    const { status, data } = await api("/api/product");
    return json(status, data);
  } catch (err) {
    return json(200, { ok: true, price_usd: 40, stripe: false, test_checkout: false });
  }
};
