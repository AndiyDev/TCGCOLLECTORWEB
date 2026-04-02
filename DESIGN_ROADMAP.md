# 🎴 TCG Collector Pro — Design Idé & Roadmap
> Version 0.0.4 → 1.0.0  
> Senast uppdaterad: 2026-04-02

---

## 📐 1. DESIGN IDÉ — "VAULT"

### Konceptnamn: **VAULT**
> *"Din samling är ett valv. Varje kort är ett mynt."*

Appens visuella identitet ska kännas som en **premium kortsamlare-app** — 
mörk, elegant och kraftfull. Inspirerad av:
- **TCGPlayer** och **PokeData** (professionell datadensitet)
- **Vault** och **Robinhood** (clean finansiell dashboard-känsla)
- **fysisk kortpärm** (grid-layout, bläddra = bläddra i pärmfickor)

---

## 🎨 2. VISUELL IDENTITET

### 2.1 Färgpalett

| Roll               | Hex       | Användning                              |
|--------------------|-----------|------------------------------------------|
| **Bakgrund**       | `#0A0E1A` | Sidor, sidomenyn                         |
| **Yta / Card**     | `#111827` | Kort-containrar, modaler                 |
| **Yta / Elevated** | `#1E2738` | Hover-state, tabbar, expanders           |
| **Accent / Grön**  | `#00FF88` | Primärknapp, positiv ROI, progress-bar   |
| **Accent / Guld**  | `#FFD700` | Holo-badge, önskelista-tagg, toppkort    |
| **Accent / Röd**   | `#FF4B4B` | Negativ ROI, varningar, radera           |
| **Accent / Blå**   | `#4F9EFF` | Info, länkar, chart-linje                |
| **Text / Primär**  | `#F0F4FF` | Rubriker, viktiga värden                 |
| **Text / Sekundär**| `#8892A4` | Captions, labels, datum                  |
| **Kant / Subtle**  | `#2A3347` | Borders på containrar                    |

### 2.2 Typografi

| Typ          | Font                        | Vikt     | Storlek  |
|--------------|-----------------------------|----------|----------|
| **Rubrik H1**| `Inter` / `Poppins`         | 700      | 28–32px  |
| **Rubrik H2**| `Inter`                     | 600      | 20–24px  |
| **Brödtext** | `Inter`                     | 400      | 14–16px  |
| **Siffror**  | `JetBrains Mono` / `tabular`| 500      | 14–18px  |
| **Badge**    | `Inter`                     | 700      | 10–12px  |

> **Rationale:** Monospace-font för priser/siffror ger kolumnkänsla och läsbarhet (som aktie-appar).

### 2.3 Ikonografi
- Primärt: **Streamlit-native** (st.metric, st.progress)  
- Emoji som ikon-ersättare i sidomenyn (nuvarande approach — behålls men förfinas)  
- Framtida: **Material Symbols** via `streamlit-extras` eller injicerad CSS

---

## 🗂️ 3. KOMPONENTBIBLIOTEK (UI Patterns)

### 3.1 Kortkomponent — "CardTile"
```
┌─────────────────────┐
│  ░░░░░░░░░░░░░░░░░  │  ← Kortbild (full-width, aspect 2.5:3.5)
│  ░░░░░░░░░░░░░░░░░  │
│  ░░░  HOLO ✨  ░░░  │  ← Animerat holo-overlay (om Holo/Reverse)
│  ░░░░░░░░░░░░░░░░░  │
├─────────────────────┤
│ Charizard           │  ← Kortnamn (bold)
│ #4 · Holo · NM      │  ← Metadata (caption, monospace)
│ ━━━━━━━━━━━━━━━━━━ │
│ 📈 2 450 kr  +12%  │  ← Marknadsvärde + ROI-delta (grön/röd)
│ [  Visa Detaljer  ] │  ← Primärknapp
└─────────────────────┘
```

### 3.2 Metric-kort — "StatBubble"
```
┌──────────────────────┐
│ 💰 TOTAL INVESTERAT  │
│  48 250 kr           │  ← Stor siffra, monospace
│  ▲ +3 200 kr (6.6%) │  ← Delta i grönt
└──────────────────────┘
```

### 3.3 Booster-komponent — "PackCard"
```
╔══════════════════════╗
║  ████████████████    ║  ← Booster-omslagsbild (set-logga)
║  CROWN ZENITH        ║
║  Öppnad: 2026-03-15  ║
║  Kostnad: 65 kr      ║
║  Värde:   112 kr     ║
║  ROI: ▲ +47 kr  ✅   ║
╚══════════════════════╝
```

### 3.4 Sidomeny — "NavVault"
```
🛡️ VAULT
─────────────────────
👤 AndiyDev
   Level 4 Collector
[████████░░] 78 kort
─────────────────────
📈 Dashboard
🎴 Min Samling
📦 Pack Opening
📸 Scanner
─────────────────────
⚙️ Admin
🛠️  Systemvård
👤 Profil
─────────────────────
🚪 Logga ut
```

---

## 🏗️ 4. SIDLAYOUT — DESIGNSKISSER

### 4.1 Dashboard (Ny design)
```
┌────────────────────────────────────────────────────────────┐
│  📈  48 250 kr    📦  61 500 kr    💵  12 000 kr    🚀 ROI │
│  Investerat       Marknadsvärde    Sålt             +25.3% │
├──────────────────────────────┬─────────────────────────────┤
│  📊 Värde över tid (30 dagar)│  🏆 Top 5 Kort              │
│  ┌─ chart ──────────────┐   │  1. Charizard HOLO  4 500kr │
│  │ ╭──╮                 │   │  2. Blastoise       3 200kr │
│  │╭╯  ╰──╮    ╭──╮     │   │  3. Mewtwo          2 800kr │
│  │╯       ╰───╯  ╰─    │   │  4. Venusaur        2 100kr │
│  └──────────────────────┘   │  5. Raichu          1 750kr │
├──────────────────────────────┴─────────────────────────────┤
│  🧪 Booster Pack Luck (senaste 10 öppningar)               │
│  [Crown Zenith ▲+47kr] [SWSH ▲+12kr] [Base ▼-15kr] ...   │
└────────────────────────────────────────────────────────────┘
```

### 4.2 Portfolio (Ny design)
```
┌────────────────────────────────────────────────────────────┐
│  [📖 Min Pärm (58)] [⭐ Önskelista (12)] [📈 Sold (7)]    │
├──────────────┬──────────────────────────┬───────────────── ┤
│ 🔍 Sök...   │ Set: [Alla ▾]  Sort:[▾] │ [Grid] [Lista]   │
├──────────────┴──────────────────────────┴──────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │ 🃏  │ │✨HOLO│ │ 🃏  │ │ ⭐  │ │ 🃏  │ │ 🃏  │   │
│ │      │ │      │ │      │ │WISH │ │      │ │      │   │
│ │Name  │ │Name  │ │Name  │ │Name  │ │Name  │ │Name  │   │
│ │NM·⬆️ │ │NM·✨ │ │EX·─  │ │ ?kr  │ │NM·⬆️ │ │GD·⬇️ │   │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
└────────────────────────────────────────────────────────────┘
```

### 4.3 Pack Opening (Ny design — "Reveal"-animering)
```
┌────────────────────────────────────────────────────────────┐
│  CROWN ZENITH · 65 kr · [✨ ÖPPNA PACK]                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│    🎴  🎴  🎴  🎴  🎴  🎴  🎴  🎴  🎴  🎴              │
│   [1] [2] [3] [4] [5] [6] [7] [8] [9][10]               │
│       ↑ Klicka för att "vända" varje kort (flip-anim)     │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  Kostnad: 65 kr  │  Värde: 112 kr  │  ROI: ▲ +47 kr 🎉   │
└────────────────────────────────────────────────────────────┘
```

---

## 🗺️ 5. ROADMAP

### Versionsöversikt

```
v0.0.4 (NU) ──► v0.1 ──► v0.2 ──► v0.3 ──► v0.5 ──► v1.0
   Bugfixes    Design   Data     Social   Mobile   Launch
```

---

### 🟢 v0.1 — "FOUNDATION" *(1–2 veckor)*
**Mål: Städa upp koden och ge appen ett professionellt utseende.**

#### Design & UI
- [ ] Ny global CSS-komponent — `vault_theme.py` injiceras på alla sidor
  - Ny bakgrundsfärg `#0A0E1A`, kortcontainrar med `border: 1px solid #2A3347`
  - Siffror i `font-family: 'JetBrains Mono'` via Google Fonts
  - Animerat gradient-glow på holo-kort (förbättrad `holo-effect`)
- [ ] Sidomeny-omdesign: Lägg till samlingsstorlek + "Level"-system (t.ex. Level 4 Collector om 50+ kort)
- [ ] Ny startsida/login: Centrerat logotyp-kort med splash-animation
- [ ] Responsiv grid: 2 kolumner på mobil, 4 på desktop

#### Funktioner
- [ ] Implementera `currency_utils.format_price()` på Dashboard och Portfolio
- [ ] "Sök + filtrera" toolbar i Portfolio (efter set, skick, variant)
- [ ] Lista-vy i Portfolio som alternativ till grid (kompakt tabell)
- [ ] Korrekta ROI-färger: grön `#00FF88`, röd `#FF4B4B` på alla metrics

#### Tekniskt
- [ ] Skapa `utils/theme.py` — central CSS-injektion + helper-funktion `inject_theme()`
- [ ] `requirements.txt`: lägg till `streamlit-extras` för avancerade komponenter
- [ ] Flytta alla auth-guards till en decorator-funktion `require_login()`

---

### 🟡 v0.2 — "DATA POWER" *(2–4 veckor)*
**Mål: Gör dashboarden till ett riktigt analytiskt verktyg.**

#### Dashboard
- [ ] **Prishistorik-graf** — Linjediagram (Altair/Plotly) som visar samlingens totala värde de senaste 30/90/365 dagarna
  - Kräver daglig snapshot-logik i `price_history`-tabellen
- [ ] **Top 10 Kort** — Ranked lista, sorterat på marknadsvärde
- [ ] **Förlustkort** — Lista på kort vars värde sjunkit mest (bra att sälja)
- [ ] **Set-completion meter** — Progress-bar per set (t.ex. "Base Set: 24/102 kort")
- [ ] **Booster ROI-historik** — Stacked bar chart: kostnad vs värde per öppnat paket

#### Priser
- [ ] **Cardmarket-integration** — Skrapa NM-snittpriser från Cardmarket.com
  - Funktion `scrape_cardmarket_price(card_name, set_id)` i `price_updater.py`
  - "Uppdatera Priser"-knappen i Sets Manager ska faktiskt fungera
- [ ] **Automatisk prisuppdatering** — Bakgrundsjobb (APScheduler) som uppdaterar priser varje natt
- [ ] **Condition multipliers** — Visa EX/GD/LP-priser baserat på NM * multiplier i kortdetaljer

#### Databas
- [ ] `price_history` snapshots — Cron-jobb (eller manuell trigger) sparar dagens NM-priser
- [ ] `user_items.sale_price` — Implementera "Sälj kort"-flöde fullt ut med `log_transaction`

---

### 🟠 v0.3 — "EXPERIENCE" *(4–6 veckor)*
**Mål: Gör det roligt att använda appen.**

#### Pack Opening — "Reveal Mode"
- [ ] **Kortvänd-animering** — CSS 3D flip animation (kort visas med baksida → vänder upp → namn + glow avslöjas)
- [ ] **Rarity-system** — Automatisk detektering baserat på `is_holo` + pris:
  - ⬜ Common / ♦️ Uncommon / ⭐ Rare / 🌟 Holo Rare / 💎 Ultra Rare
- [ ] **Pack Luck Score** — Beräknat 0–100 per öppning (värde/medelvärde per pack i setet)
- [ ] **Konfetti + ljud** *(valfritt)* — st.balloons() ersätts med `confetti.js` via HTML-komponent vid Ultra Rare

#### Portfolio
- [ ] **Drag & drop** sortering av samlingsordning (streamlit-sortables)
- [ ] **Bulk-åtgärder** — Välj flera kort → "Flytta till Sålt" / "Ändra skick"
- [ ] **Delbar länk** — Generera en read-only URL till din samling (t.ex. `?user=andiy&token=XYZ`)
- [ ] **Bild-upload** — Ladda upp eget kortfoto istället för API-bild (Streamlit file_uploader → spara URL)

#### Scanner
- [ ] **Multi-scale template matching** — Testa symbolen i 3–5 olika skalor för bättre träffsäkerhet
- [ ] **ORB/SIFT-baserad matchning** — Mer robust mot rotation och ljusförhållanden
- [ ] **Manuell override** — Om scannern är osäker, visa Top 3 kandidater att välja mellan

---

### 🔵 v0.5 — "PLATFORM" *(2–3 månader)*
**Mål: Från hobby-app till plattform.**

#### Multi-user & Socialt
- [ ] **Email-verifiering** vid registrering
- [ ] **Offentliga profiler** — Visa andras samlingar (om de satt dem till publika)
- [ ] **Handelslistor** — "Jag har: X, söker: Y" — matchning mellan användare
- [ ] **Kommentarsfält** på booster-öppningar ("Drömöppning!")

#### Mobile PWA
- [ ] **Bättre mobilrespons** — Streamlit PWA-meta + touch-friendly knappar (min 44px tap target)
- [ ] **Offline-visning** — Service Worker cacher senaste portfolio för visning utan nät
- [ ] **Kamera-permission** — Snabbare tillgång till scanner på mobil (deep link till Scanner-sidan)

#### Import/Export
- [ ] **CSV-import** — Ladda upp befintlig samling från Excel/CSV
- [ ] **TCGPlayer-import** — Parsar exportfil från TCGPlayer
- [ ] **Backup till Google Drive** *(stretch)* — OAuth + Drive API

---

### 🚀 v1.0 — "LAUNCH" *(3–4 månader)*
**Mål: Produktionsklar, stabil, säker, skalbar.**

#### Infrastruktur
- [ ] **Migrera från Streamlit Community Cloud → egen VPS** (t.ex. Hetzner CX21) bakom Caddy
- [ ] **MySQL → PostgreSQL** (bättre concurrency för multi-user)
- [ ] **Alembic migrations** — Versionshantera databasschema istället för `CREATE TABLE IF NOT EXISTS`
- [ ] **Redis-cache** — Cacha API-anrop och prissökningar (minska DB-last)
- [ ] **Logging** — Centraliserad loggning med `loguru` + roterande loggfiler
- [ ] **Hälso-endpoint** — `/health` som Docker/load balancer kan pinga

#### Säkerhet
- [ ] **JWT-tokens** — Ersätt Streamlit session_state-auth med ordentlig token-hantering
- [ ] **HTTPS/TLS** — Caddy auto-cert via Let's Encrypt
- [ ] **Rate limiting** — Nginx/Caddy-nivå (inte bara app-nivå)
- [ ] **Password reset** — "Glömt lösenord?" via email
- [ ] **GDPR** — Cookie-banner + möjlighet att exportera/radera all data (redan delvis implementerat)

#### Kvalitet
- [ ] **Unit tests** — `pytest` + `pytest-mock` för database.py och currency_utils.py
- [ ] **Integration tests** — Testa hela inloggningsflödet och CRUD-operationer
- [ ] **CI/CD pipeline** — GitHub Actions: lint (flake8) → test → deploy vid merge till main
- [ ] **Error tracking** — Sentry.io integration (gratis tier räcker)

---

## 📊 6. TEKNISK SKULD — PRIORITERINGSLISTA

| # | Problem                                 | Allvarlighet | Insats | Sprint |
|---|-----------------------------------------|:------------:|:------:|:------:|
| 1 | Priser uppdateras aldrig automatiskt    | 🔴 Kritisk   | Stor   | v0.2   |
| 2 | Ingen e-post-validering vid registrering| 🟠 Hög      | Liten  | v0.5   |
| 3 | Scanner fungerar dåligt i praktiken     | 🟠 Hög      | Stor   | v0.3   |
| 4 | Ingen testsvit alls                     | 🟠 Hög      | Stor   | v1.0   |
| 5 | `init_db()` körs på varje page-laddning | 🟡 Medium    | Liten  | v0.1   |
| 6 | Cardmarket-skrapning saknas             | 🟡 Medium    | Stor   | v0.2   |
| 7 | Sälj-flöde loggar ingen transaktion     | 🟡 Medium    | Liten  | v0.2   |
| 8 | Sessionens `member_since` hårdkodad     | 🟢 Låg       | Liten  | v0.1   |
| 9 | Ingen paginering i Portfolio-grid       | 🟢 Låg       | Liten  | v0.2   |

---

## 🧩 7. MODULSTRUKTUR — MÅL v1.0

```
TCGCOLLECTORWEB/
│
├── app.py                    # Entry point, auth, navigation
├── requirements.txt
├── .streamlit/
│   └── config.toml
│
├── core/                     # ← NY: Affärslogik separerad från UI
│   ├── database.py           # SQLAlchemy models + CRUD
│   ├── auth.py               # Login, register, JWT
│   ├── price_updater.py      # Cardmarket scraper + scheduler
│   └── currency_utils.py     # Valutakonvertering
│
├── utils/                    # ← NY: Helpers
│   ├── theme.py              # inject_theme(), CSS-komponenter
│   ├── validators.py         # Input sanitering & validering
│   └── export.py             # Excel/CSV/JSON export-logik
│
├── pages/                    # Streamlit-sidor (tunna UI-lager)
│   ├── dashboard.py
│   ├── portfolio.py
│   ├── add_item.py
│   ├── scanner.py
│   ├── sets_manager.py
│   ├── maintenance.py
│   └── profile.py
│
├── tests/                    # ← NY: Testsvit
│   ├── test_database.py
│   ├── test_currency.py
│   └── test_auth.py
│
├── images/
│   └── Logos/                # 147 set-loggor (befintliga)
│
└── static/
    ├── manifest.json
    └── sw.js
```

---

## 🎯 8. FEATURE FLAGS — PRIORITERING FÖR NÄSTA SPRINT

Välj 3 features att bygga härnäst baserat på impact vs insats:

```
HIGH IMPACT, LOW EFFORT (Gör Nu 🚀)
├── Sök + filter-toolbar i Portfolio
├── Lista-vy i Portfolio (kompakt tabell)
└── inject_theme() — global CSS-komponent

HIGH IMPACT, HIGH EFFORT (Planera 📅)
├── Cardmarket prisuppdatering
├── Prishistorik-graf (Dashboard)
└── Pack-reveal animation (flip)

LOW IMPACT, LOW EFFORT (Fyll på 🪣)
├── member_since från DB istället för hårdkodat datum
├── Paginering i portfolio-grid
└── Toast-notifikation vid kortläggning

LOW IMPACT, HIGH EFFORT (Skippa ⛔)
└── Google Drive backup
```

---

## 📅 9. SPRINT-PLAN (Agil, 2-veckors sprints)

| Sprint | Period       | Fokus                                        | Leverabler                          |
|--------|--------------|----------------------------------------------|-------------------------------------|
| **S1** | v1 → v15 Apr | Tema + Grunddesign                           | `theme.py`, ny login-sida, ny nav   |
| **S2** | v16 → v30 Apr| Portfolio v2                                 | Sök/filter, lista-vy, bulk-actions  |
| **S3** | v1 → v15 Maj | Data & Priser                                | Cardmarket scraper, prishistorik    |
| **S4** | v16 → v31 Maj| Pack Experience                              | Flip-animation, Pack Luck Score     |
| **S5** | v1 → v15 Jun | Scanner v2                                  | Multi-scale matching, Top 3 match   |
| **S6** | v16 → v30 Jun| Plattform prep                               | Offentliga profiler, CSV-import     |
| **S7** | v1 → v31 Jul | Stabilitet & Säkerhet                        | Tests, CI/CD, Sentry, JWT           |
| **S8** | v1 → v15 Aug | Launch prep                                  | Deploy VPS, HTTPS, performance      |
| **🚀** | **v15 Aug**  | **v1.0 LAUNCH**                              | **Produktionssläpp**                |

---

*Dokumentet uppdateras i takt med att features levereras.*  
*Roadmap är ett levande dokument — prioriteringar kan ändras.*
