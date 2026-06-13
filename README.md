# NEONEX — Vaporwave Search Engine (Netlify Edition)

Fully self-contained vaporwave search engine powered by Brave Search API.
Works on both **localhost** (Python proxy) and **Netlify** (serverless function).

```
neonex-netlify/
├── index.html                    ← The search engine
├── netlify.toml                  ← Netlify config (functions, redirects)
└── netlify/
    └── functions/
        └── search.js             ← Serverless search proxy
```

## 🚀 Deploy to Netlify

### 1. Push to GitHub
```bash
cd neonex-netlify
git init
git add -A
git commit -m "NEONEX v4 — Netlify-ready"
git remote add origin git@github.com:YOUR_USER/neonex.git
git push -u origin main
```

### 2. Connect Netlify
- Go to https://app.netlify.com
- "Add new site" → "Import an existing project" → Connect GitHub
- Select the repo, leave build settings as-is (no build step)

### 3. Set API Key
In Netlify dashboard:
- **Site Settings → Environment variables**
- Add: `BRAVE_API_KEY` = `BSAljOHalG4Fb3svssjzzzPWqaOfz_ _`
- Redeploy (Deploys → Trigger deploy)

### 4. Done
Open your `.netlify.app` URL and search the grid.

## 🖥️ Local Development
```bash
cd ~/neonex-netlify
python3 ../neonex-proxy.py   # Start the proxy
# Open http://localhost:8777 in browser
```

Or use Netlify CLI:
```bash
netlify dev   # Runs function + static site locally
```

## 🔑 How It Works

The HTML auto-detects where it's running:

| Environment    | Search endpoint                      | API key source     |
|----------------|--------------------------------------|---------------------|
| `localhost`    | Local Python proxy (port 8777)       | localStorage or env |
| Netlify        | `/.netlify/functions/search`         | `BRAVE_API_KEY` env |
| Fallback       | Direct Brave API                     | localStorage key    |
