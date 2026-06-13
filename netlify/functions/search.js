// NEONEX Search — Netlify serverless function
// Proxies search requests to Brave Search API server-side.
//
// Deploy:
//   1. Push to GitHub, connect to Netlify
//   2. Set env var: BRAVE_API_KEY in Netlify dashboard (Site Settings → Environment)
//   3. Trigger deploy
//
// Local dev:  npx netlify-cli dev

exports.handler = async (event) => {
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
  };

  // CORS preflight
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers, body: "" };
  }

  const query = event.queryStringParameters?.q;
  const count = event.queryStringParameters?.count || "12";

  if (!query) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: "Missing ?q= parameter" }),
    };
  }

  const apiKey = process.env.BRAVE_API_KEY;
  if (!apiKey) {
    return {
      statusCode: 401,
      headers,
      body: JSON.stringify({ error: "BRAVE_API_KEY not set in Netlify environment variables" }),
    };
  }

  const braveUrl = `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(query)}&count=${count}`;

  try {
    // Node 18+ has global fetch built in
    const braveRes = await fetch(braveUrl, {
      headers: {
        "Accept": "application/json",
        "X-Subscription-Token": apiKey,
      },
    });

    const data = await braveRes.json();

    if (!braveRes.ok) {
      return {
        statusCode: braveRes.status,
        headers,
        body: JSON.stringify({ error: `Brave API error ${braveRes.status}: ${JSON.stringify(data)}` }),
      };
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(data),
    };
  } catch (err) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: `Search request failed: ${err.message}` }),
    };
  }
};
