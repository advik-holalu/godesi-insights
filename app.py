# streamlit run app.py
# expects "Untitled spreadsheet.xlsx" in the same folder

import os, re
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

# -----------------------------
# PAGE CONFIG & GLOBAL STYLE
# -----------------------------
st.set_page_config(page_title="GO DESi Insights", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top:1.0rem; padding-bottom:1.25rem;}
      h1, h2 { color:#F59E0B !important; }
      .insight { 
        background: rgba(245,158,11,0.08);
        border: 1px solid rgba(245,158,11,0.25);
        padding: 10px 12px; border-radius: 10px; margin: 10px 0 16px 0;
      }
      .muted { color:#A0AEC0; font-size:0.9rem; }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown("<h1 style='margin-bottom:0.15rem'>GO DESi Consumer Insights</h1>", unsafe_allow_html=True)
st.caption(f"Last refreshed: {pd.Timestamp.now().strftime('%d %b %Y, %I:%M %p')}")
st.caption("Dark-mode · Interactive Altair charts · Master for common insights; Confectionery/Sweets for category specifics")

PALETTE = ["#F59E0B","#8B5CF6","#22D3EE","#34D399","#F472B6","#60A5FA","#F97316","#EAB308","#06B6D4","#A3E635"]

alt.themes.enable('none')
def style_chart(c):
    return (c
        .configure(background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(
            domain=False, tickColor="#2A2F3A",
            labelColor="#CBD5E1", titleColor="#E5E7EB",
            grid=True, gridColor="#1F2430"
        )
        .configure_legend(labelColor="#CBD5E1", titleColor="#E5E7EB")
    )

# -----------------------------
# HELPERS
# -----------------------------
def _normalize(s):
    if pd.isna(s): return ""
    return re.sub(r"\s+"," ", str(s).strip())

def _lower(s): return _normalize(s).lower()

@st.cache_data(show_spinner=False)
def list_sheets(path:str):
    if not os.path.exists(path):
        st.error(f"Excel file not found: {path}")
        st.stop()
    return pd.ExcelFile(path).sheet_names

@st.cache_data(show_spinner=False)
def read_sheet(path:str, name:str):
    try: return pd.read_excel(path, sheet_name=name)
    except: return pd.DataFrame()

def _find_sheet(sheets, *keys):
    for s in sheets:
        low = s.lower()
        if all(k.lower() in low for k in keys): return s
    return None

def _clean(df):
    if df is None or df.empty: return df
    df = df.copy()
    df.columns = df.columns.map(lambda c: _normalize(c).lower())
    for c in df.columns:
        if df[c].dtype == "O":
            df[c] = df[c].map(_normalize)
    return df

def _map_cols(df, spec:dict):
    out = {k: None for k in spec.keys()}
    if df is None or df.empty: return out
    cols = list(df.columns)
    for key, patt in spec.items():
        patt = [p.lower() for p in patt]
        # all tokens
        for c in cols:
            lc = c.lower()
            if all(p in lc for p in patt):
                out[key]=c; break
        # any token (fallback)
        if out[key] is None:
            for c in cols:
                lc = c.lower()
                if any(p in lc for p in patt):
                    out[key]=c; break
    return out

def _vc(series):
    if series is None: return pd.DataFrame(columns=["label","count"])
    s = series.dropna().astype(str).map(_normalize); s = s[s!=""]
    vc = s.value_counts()
    if vc.empty: return pd.DataFrame(columns=["label","count"])
    return vc.rename_axis("label").reset_index(name="count")

def _hbar(df_counts, title, xlabel="Count"):
    if df_counts.empty:
        st.info("No data available.", icon="ℹ️"); return
    base = alt.Chart(df_counts)
    bars = base.mark_bar(color=PALETTE[0]).encode(
        y=alt.Y("label:N", sort="-x", title=""),
        x=alt.X("count:Q", title=xlabel),
        tooltip=["label:N","count:Q"]
    )
    text = base.mark_text(align="left", dx=4).encode(
        y="label:N", x="count:Q", text="count:Q"
    )
    st.altair_chart(style_chart(bars + text).properties(title=title), use_container_width=True)

def _donut(df_counts, title):
    if df_counts.empty:
        st.info("No data available.", icon="ℹ️"); return
    total = df_counts["count"].sum()
    df_counts = df_counts.assign(pct=lambda d: (100*d["count"]/total).round(1))
    pie = alt.Chart(df_counts).mark_arc(innerRadius=80).encode(
        theta="count:Q",
        color=alt.Color("label:N", scale=alt.Scale(range=PALETTE), legend=None),
        tooltip=["label:N","count:Q","pct:Q"]
    )
    st.altair_chart(style_chart(pie).properties(width=320, height=320, title=title), use_container_width=False)

def _heatmap(ct, title, xlabel="", ylabel=""):
    if ct is None or ct.size==0:
        st.info("No data available.", icon="ℹ️"); return
    tidy = ct.copy(); tidy.index.name, tidy.columns.name = "row","col"
    tidy = tidy.reset_index().melt("row", var_name="col", value_name="value")
    hm = alt.Chart(tidy).mark_rect().encode(
        x=alt.X("col:N", title=xlabel, sort=list(ct.columns)),
        y=alt.Y("row:N", title=ylabel, sort=list(ct.index)),
        color=alt.Color("value:Q", scale=alt.Scale(scheme="goldorange"), title="Mentions"),
        tooltip=["row:N","col:N","value:Q"]
    )
    st.altair_chart(style_chart(hm).properties(height=300, title=title), use_container_width=True)

def _xtab(df, r, c):
    if df is None or df.empty or r is None or c is None: return pd.DataFrame()
    try: return pd.crosstab(df[r].astype(str), df[c].astype(str))
    except: return pd.DataFrame()

# -----------------------------
# LOAD SHEETS
# -----------------------------
xlsx = "Untitled spreadsheet.xlsx"
sheets = list_sheets(xlsx)
st.caption(f"Loaded sheets: {', '.join(sheets)}")

sheet_master = _find_sheet(sheets, "master")
sheet_conf   = _find_sheet(sheets, "confectionery") or _find_sheet(sheets, "mint")
sheet_sweets = _find_sheet(sheets, "sweet")

df_master = _clean(read_sheet(xlsx, sheet_master)) if sheet_master else pd.DataFrame()
df_conf   = _clean(read_sheet(xlsx, sheet_conf)) if sheet_conf else pd.DataFrame()
df_sweets = _clean(read_sheet(xlsx, sheet_sweets)) if sheet_sweets else pd.DataFrame()

if df_master.empty and df_conf.empty and df_sweets.empty:
    st.error("No usable sheets found. Ensure Master / Confectionery / Sweets exist."); st.stop()

# Column maps
master_map = _map_cols(df_master, {
    "age":["age"],
    "gender":["gender"],
    "discover":["how","hear","popz","discover"],
    "when":["when","eat","popz","moment"],
    "why":["why","choose","popz","reason"],
})
conf_map = _map_cols(df_conf, {
    "age":["age"], "gender":["gender"],
    "discover":["how","hear","popz"],
    "when":["when","eat","popz"],
    "what":["what","desi","popz"],
    "why":["why","choose","popz"],
    "freq":["how often","desi","popz"],
    "know":["did","know","make","sweet"],
})
sweets_map = _map_cols(df_sweets, {
    "age":["age"],
    "prefer":["which","packaged","prefer"],
    "topmind":["which","other","top"],
    "top3":["top","3","spont"],
    "freq":["how","often","packaged","sweet"],
    "occasion":["on","what","occasion","packaged"],
})

# -----------------------------
# FILTERS (Master first)
# -----------------------------
with st.sidebar:
    st.header("Filters")
    ages = []
    for (df, col) in [(df_master, master_map.get("age")),
                      (df_conf, conf_map.get("age")),
                      (df_sweets, sweets_map.get("age"))]:
        if df is not None and not df.empty and col:
            ages += list(df[col].dropna().astype(str).unique())
    ages = sorted(set(ages))
    sel_ages = st.multiselect("Age groups", ages, default=ages)

def _apply_age(df, col):
    if df is None or df.empty or not col or not sel_ages: return df
    return df[df[col].astype(str).isin(sel_ages)]

df_master_f = _apply_age(df_master, master_map.get("age"))
df_conf_f   = _apply_age(df_conf, conf_map.get("age"))
df_sweets_f = _apply_age(df_sweets, sweets_map.get("age"))

# -----------------------------
# TABS (10 sections)
# -----------------------------
tabs = st.tabs([
    "1) Demographics", "2) Discovery", "3) Consumption Context",
    "4) Perception (What is Popz?)", "5) Purchase Motivation",
    "6) Sweets: Awareness", "7) Sweets: Preference & Occasion",
    "8) Brand Linkage (Popz → Sweets)", "9) Journey", "10) Strategy"
])

# 1) Demographics — Master
with tabs[0]:
    st.subheader("Respondent Profile (Master)")
    c1, c2 = st.columns(2)
    src = df_master_f if not df_master_f.empty else df_conf_f  # fallback
    age_col = master_map.get("age") or conf_map.get("age")
    gen_col = master_map.get("gender") or conf_map.get("gender")
    if age_col and not src.empty: _hbar(_vc(src[age_col]), "Age Distribution", "Respondents")
    if gen_col and not src.empty: _donut(_vc(src[gen_col]), "Gender Split")

    st.markdown("""
<div class="insight"><b>What we see:</b> Younger cohorts (20–39) dominate; male share is slightly higher.<br/>
<b>Why it matters:</b> Creative, format-first messages land well with a younger base.<br/>
<b>Next:</b> Let’s see <i>where</i> they hear about Popz to target discovery.</div>
""", unsafe_allow_html=True)

# 2) Discovery — Master (fallback Confectionery)
with tabs[1]:
    st.subheader("Discovery Channels (Desi Popz)")
    src = df_master_f if master_map.get("discover") and not df_master_f.empty else df_conf_f
    dcol = master_map.get("discover") or conf_map.get("discover")
    if dcol and not src.empty:
        _hbar(_vc(src[dcol]), "How did consumers hear about Desi Popz?")
        a_col = (master_map.get("age") if src is df_master_f else conf_map.get("age"))
        if a_col: _heatmap(_xtab(src, a_col, dcol), "Age Group × Discovery Channel of Desi Popz", "Discovery Channel", "Age Group")
    st.markdown("""
<div class="insight"><b>What we see:</b> Instagram dominates across ages; some mention Shark Tank/Amazon/Facebook.<br/>
<b>Implication:</b> Entry is social-first → double down on short-form + micro-influencer trials.<br/>
<b>Connects to next:</b> If discovery is curiosity-led, <i>trial</i> will hinge on flavour/format — check consumption contexts.</div>
""", unsafe_allow_html=True)

# 3) Consumption Context — When they eat Popz
with tabs[2]:
    st.subheader("When Consumers Usually Eat Desi Popz")
    wcol = "when does the customer usually eat desi popz"
    src = df_master_f if wcol in df_master_f.columns else df_conf_f

    if wcol in src.columns and not src.empty:
        _hbar(_vc(src[wcol]), "Consumption Moments", "Mentions")
        a_col = (master_map.get("age") if src is df_master_f else conf_map.get("age"))
        if a_col:
            _heatmap(_xtab(src, a_col, wcol),
                     "Age Group × Consumption Context",
                     "Consumption Moment", "Age Group")

    st.markdown("""
<div class="insight">
<b>What we see:</b> Popz is most often eaten after meals, while bored, or to satisfy sudden cravings.<br/>
<b>Implication:</b> Popz sits in an indulgent, post-meal space rather than health snacking — position it as a <i>chatpata digestif</i>.<br/>
<b>Connects to next:</b> If consumption is driven by flavour and habit cues, <i>taste</i> and <i>ingredients</i> should anchor purchase motivation.
</div>
""", unsafe_allow_html=True)


# 4) Perception (What is Popz?) — Confectionery
with tabs[3]:
    st.subheader("Perception: What is Desi Popz? (Confectionery)")
    if conf_map.get("what") and not df_conf_f.empty:
        ser = df_conf_f[conf_map["what"]].map(_lower)
        def map_perc(x):
            if any(k in x for k in ["candy","lollipop","both"]): return "Candy / Lollipop"
            if any(k in x for k in ["churan","fresh","digestive"]): return "Digestive / Mouth Freshener"
            if any(k in x for k in ["tamarind","popz","unique"]): return "Novelty / Tamarind Pop"
            if "not" in x or "no idea" in x or x in ["nan",""]: return "Unclear"
            return "Other"
        cats = ser.fillna("").apply(map_perc)
        _donut(cats.value_counts().rename_axis("label").reset_index(name="count"),
               "Consumer Perception of Popz")
    st.markdown("""
<div class="insight"><b>What we see:</b> Majority think Popz is candy/lollipop; a smaller set see tamarind/digestive.<br/>
<b>Implication:</b> There’s category ambiguity → clarify “chatpata candy with post-meal friendly vibe”.<br/>
<b>Connects to next:</b> If candy cues dominate, <i>taste</i> & <i>ingredients</i> should lead motivations.</div>
""", unsafe_allow_html=True)

# 5) Purchase Motivation — robust version
with tabs[4]:
    st.subheader("Why Consumers Choose Desi Popz")

    src = df_master_f if not df_master_f.empty else df_conf_f
    ycol = "why do you choose desi popz over other candies?"

    if ycol in src.columns:
        ser = src[ycol].fillna("").astype(str).map(str.lower)

        # --- comprehensive mapping ---
        def map_motive(x):
            x = x.strip()
            if x == "" or x in ["nan", "na", "none", "no"]:
                return "Other / Non-motivational"

            taste_kw = [
                "taste", "tasty", "chatpata", "flavour", "flavor", "sweet",
                "spicy", "yummy", "delicious", "nice", "good"
            ]
            ingr_kw = [
                "ingredient", "natural", "quality", "authentic", "pure",
                "homemade", "clean", "real", "no preservative", "healthy"
            ]
            nost_kw = [
                "nostalg", "memory", "child", "school", "old days",
                "remember", "feel", "retro"
            ]
            fmt_kw = [
                "fun", "unique", "format", "experience", "shape", "design",
                "stick", "lollipop", "pop", "look", "feel", "different"
            ]
            pack_kw = [
                "pack", "gift", "wrapper", "box", "cover", "colour",
                "color", "packaging", "looks"
            ]

            if any(k in x for k in taste_kw): return "Taste / Flavour"
            if any(k in x for k in ingr_kw):  return "Ingredients / Quality"
            if any(k in x for k in nost_kw):  return "Emotion / Nostalgia"
            if any(k in x for k in fmt_kw):   return "Format / Experience"
            if any(k in x for k in pack_kw):  return "Packaging / Gift"
            return "Other / Non-motivational"

        cats = ser.apply(map_motive)

        # --- show diagnostic counts for debugging ---
        counts = cats.value_counts().rename_axis("label").reset_index(name="count")
        st.write("### Counts")
        st.dataframe(counts)

        # --- reorder for chart ---
        order = [
            "Taste / Flavour", "Ingredients / Quality",
            "Emotion / Nostalgia", "Format / Experience",
            "Packaging / Gift", "Other / Non-motivational"
        ]
        counts = counts.set_index("label").reindex(order).dropna().reset_index()

        # --- horizontal bar ---
        bar = alt.Chart(counts).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, size=28).encode(
            y=alt.Y("label:N", sort="-x", title=""),
            x=alt.X("count:Q", title="Number of Mentions"),
            color=alt.value("#F59E0B"),
            tooltip=["label:N", "count:Q"]
        )
        text = alt.Chart(counts).mark_text(align="left", dx=5, color="#E5E7EB").encode(
            y="label:N", x="count:Q", text="count:Q"
        )
        st.altair_chart(style_chart(bar + text).properties(height=280, title="Purchase Motivation"), use_container_width=True)

        # --- Heatmap by Age Group ---
        a_col = master_map.get("age") if "age" in master_map else conf_map.get("age")
        if a_col and a_col in src.columns:
            ct = pd.crosstab(src[a_col].astype(str), cats)
            tidy = ct.reset_index().melt(a_col, var_name="Motivation", value_name="Mentions")
            hm = alt.Chart(tidy).mark_rect().encode(
                x=alt.X("Motivation:N", title="Motivation Theme", sort=order),
                y=alt.Y(f"{a_col}:N", title="Age Group"),
                color=alt.Color("Mentions:Q", scale=alt.Scale(scheme="goldorange"), title="Mentions"),
                tooltip=[f"{a_col}:N", "Motivation:N", "Mentions:Q"]
            )
            st.altair_chart(style_chart(hm).properties(height=320, title="Purchase Motivation × Age Group"), use_container_width=True)

        # --- insight text ---
        st.markdown("""
<div class="insight">
<b>What we see:</b> Chatpata taste and better ingredients drive most trials, while nostalgia and playful format sustain repeat interest.<br/>
<b>Implication:</b> Communicate <i>flavour impact</i> and <i>ingredient quality</i> as key differentiators, wrapped in a fun nostalgic format.<br/>
<b>Connects to next:</b> Examine how these motivations extend to the sweets category to build stronger master-brand linkage.
</div>
""", unsafe_allow_html=True)
    else:
        st.warning("‘Why choose Desi Popz’ column not found in this sheet.")


# 6) Sweets: Awareness / Landscape — Sweets
with tabs[5]:
    st.subheader("Packaged Sweets Landscape & Brand Awareness")
    if not df_sweets_f.empty:
        cols = [c for c in [sweets_map.get("topmind"), sweets_map.get("top3"), sweets_map.get("prefer")] if c]
        if cols:
            brands = pd.concat([df_sweets_f[c].astype(str).map(_lower) for c in cols], ignore_index=True)
            def simplify(b):
                if "haldiram" in b: return "Haldiram"
                if "bikan" in b or "bhikha" in b: return "Bikaner/Bhikharam"
                if "godesi" in b: return "GO DESi"
                if any(k in b for k in ["local","homemade","store"]): return "Local/Homemade"
                if any(k in b for k in ["amul","anand","rajpurohit","kanthi","nandhini","gulab","astha","asha","open secret"]): return "Other Branded"
                if any(k in b for k in ["not","none","no idea","dont"]): return "Unaware/NA"
                return "Misc"
            brands = brands.fillna("").apply(simplify)
            _hbar(brands.value_counts().rename_axis("label").reset_index(name="count"),
                  "Brand Mentions (top-of-mind + top3 + preference)", "Mentions")
    st.markdown("""
<div class="insight"><b>What we see:</b> Haldiram/Bikaner dominate recall; “Local/Homemade” is sizable; GO DESi appears but seldom first.<br/>
<b>Implication:</b> The category is fragmented with regional loyalty; authenticity cues matter.<br/>
<b>Connects to next:</b> Let’s see preference & occasions to place GO DESi where it wins.</div>
""", unsafe_allow_html=True)

# 7) Sweets: Preference & Occasion — Final Version
with tabs[6]:
    st.subheader("Sweets Preference & Consumption Occasion")

    # Always use sweets sheet
    src = df_sweets_f.copy()
    if src.empty:
        st.warning("No sweets data available.")
    else:
        # --- Detect relevant columns automatically ---
        prefer_col = next((c for c in src.columns if "prefer" in c.lower() and "sweet" in c.lower()), None)
        occasion_col = next((c for c in src.columns if "occasion" in c.lower()), None)
        age_col = next((c for c in src.columns if "age" in c.lower()), None)

        # ---------- 1. Donut: Brand Preference ----------
        if prefer_col:
            pref = src[prefer_col].fillna("").astype(str).str.lower()

            def map_brand(x):
                if "haldiram" in x: return "Haldiram"
                if "bikan" in x or "bhikha" in x: return "Bikaner/Bhikharam"
                if "godesi" in x: return "GO DESi"
                if any(k in x for k in ["local", "home", "store"]): return "Local/Homemade"
                if any(k in x for k in ["amul", "rajpurohit", "nandhini", "gulab", "anand", "open secret"]):
                    return "Other Branded"
                return "Other / Unclear"

            brands = pref.apply(map_brand)
            b_counts = brands.value_counts().rename_axis("Brand").reset_index(name="Mentions")

            donut = alt.Chart(b_counts).mark_arc(innerRadius=80).encode(
                theta="Mentions:Q",
                color=alt.Color("Brand:N", scale=alt.Scale(scheme="tableau10")),
                tooltip=["Brand:N", "Mentions:Q"]
            )
            st.altair_chart(
                style_chart(donut).properties(title="Packaged Sweets Brand Preference"),
                use_container_width=True
            )

        # ---------- 2. Bar: Occasions When Consumers Eat Packaged Sweets ----------
        if occasion_col:
            occ = src[occasion_col].fillna("").astype(str).str.lower()

            def map_occ(o: str) -> str:
                if any(k in o for k in ["fest", "festival", "diwali", "holi", "eid", "rakhi", "celebrat"]):
                    return "Festive / Celebration"
                if any(k in o for k in ["dessert", "meal", "dinner", "lunch", "after", "post meal", "sweet dish"]):
                    return "Dessert / After Meals"
                if any(k in o for k in ["crav", "impulse", "snack", "bored", "anytime", "evening", "timepass"]):
                    return "Craving / Snack"
                return "Other / NA"

            occ_cats = occ.apply(map_occ)
            order = ["Festive / Celebration", "Dessert / After Meals", "Craving / Snack", "Other / NA"]

            occ_counts = (
                occ_cats.value_counts()
                .reindex(order)
                .dropna()
                .rename_axis("Occasion")
                .reset_index(name="Mentions")
            )
            total = int(occ_counts["Mentions"].sum()) if not occ_counts.empty else 0
            if total > 0:
                occ_counts["Pct"] = (occ_counts["Mentions"] * 100.0 / total).round(0).astype(int)
                occ_counts["Label"] = occ_counts.apply(lambda r: f"{int(r['Mentions'])}  ({r['Pct']}%)", axis=1)

            # Horizontal bar chart with counts + %
            bar = (
                alt.Chart(occ_counts)
                .mark_bar(size=38, cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
                .encode(
                    y=alt.Y("Occasion:N", sort="-x", title=""),
                    x=alt.X("Mentions:Q", title="Mentions"),
                    color=alt.value("#F59E0B"),
                    tooltip=["Occasion:N", "Mentions:Q", "Pct:Q"],
                )
            )
            text = (
                alt.Chart(occ_counts)
                .mark_text(align="left", dx=8)
                .encode(y="Occasion:N", x="Mentions:Q", text="Label:N", color=alt.value("#E5E7EB"))
            )

            st.altair_chart(
                style_chart(bar + text).properties(
                    title="Occasions When Consumers Eat Packaged Sweets", height=280
                ),
                use_container_width=True,
            )

        # ---------- 3. Heatmap: Age Group × Occasion ----------
        if age_col and occasion_col:
            occ_map = occ.apply(map_occ)
            age_vals = src[age_col].fillna("").astype(str)
            df_heat = pd.DataFrame({"Age Group": age_vals, "Occasion": occ_map})

            ctab = pd.crosstab(df_heat["Age Group"], df_heat["Occasion"])
            tidy = ctab.reset_index().melt("Age Group", var_name="Occasion", value_name="Mentions")

            heat = (
                alt.Chart(tidy)
                .mark_rect()
                .encode(
                    x=alt.X(
                        "Occasion:N",
                        sort=["Festive / Celebration", "Dessert / After Meals", "Craving / Snack", "Other / NA"],
                        title="Occasion",
                    ),
                    y=alt.Y("Age Group:N", title="Age Group"),
                    color=alt.Color("Mentions:Q", scale=alt.Scale(scheme="goldorange"), title="Mentions"),
                    tooltip=["Age Group:N", "Occasion:N", "Mentions:Q"],
                )
                .properties(height=350, title="Age Group × Occasion of Sweet Consumption")
            )

            st.altair_chart(style_chart(heat), use_container_width=True)

        # ---------- Insight Box ----------
        st.markdown("""
<div class="insight">
<b>What we see:</b> Haldiram dominates packaged sweet preference, followed by Local/Homemade and GO DESi.<br/>
<b>Occasions peak during festivals and post-meal desserts, with emerging snack-time usage.</b><br/>
<b>Implication:</b> GO DESi can strengthen festive authenticity and everyday dessert positioning while growing awareness among younger audiences.<br/>
<b>Connects to next:</b> Let's check whether Popz buyers associate GO DESi with sweets too.
</div>
""", unsafe_allow_html=True)


# 8) Brand Linkage (Popz → Sweets) — Confectionery
with tabs[7]:
    st.subheader("Do Popz Consumers Know GO DESi Also Makes Sweets?")
    if conf_map.get("know") and not df_conf_f.empty:
        aware = df_conf_f[conf_map["know"]].map(_normalize).str.title().replace(
            {"Y":"Yes","N":"No","Na":"No","Nan":"No","": "No"}
        )
        _donut(_vc(aware), "Awareness of GO DESi Sweets (among Popz buyers)")
        if conf_map.get("age"):
            mapped = df_conf_f[[conf_map["age"], conf_map["know"]]].copy()
            mapped[conf_map["know"]] = mapped[conf_map["know"]].map(_normalize).str.title().replace(
                {"Y":"Yes","N":"No","Na":"No","Nan":"No","": "No"})
            _heatmap(pd.crosstab(mapped[conf_map["age"]].astype(str),
                                 mapped[conf_map["know"]].astype(str)),
                     "Age Group × Awareness of GO DESi Sweets", "Awareness", "Age Group")
    st.markdown("""
<div class="insight"><b>What we see:</b> Cross-category brand linkage is weak; awareness improves slightly with age.<br/>
<b>Implication:</b> Add “GO DESi makes Popz <i>and</i> Sweets” master-brand banner; cross-promote in both packs.<br/>
<b>Connects to next:</b> Overall funnel: where do we leak — discovery, trial, habit, or advocacy?</div>
""", unsafe_allow_html=True)

# 9) Journey — blended (Master + Sweets/Conf proxies)
with tabs[8]:
    st.subheader("Consumer Journey: Discovery → Trial → Habit → Advocacy")
    # Discovery proxy = rows in Master/Conf
    n_disc = len(df_master_f) if not df_master_f.empty else len(df_conf_f)
    # Trial proxy = “why” present in same src
    if not df_master_f.empty and master_map.get("why"):
        n_trial = int((~df_master_f[master_map["why"]].isna()).sum())
    elif not df_conf_f.empty and conf_map.get("why"):
        n_trial = int((~df_conf_f[conf_map["why"]].isna()).sum())
    else:
        n_trial = int(n_disc * 0.7)
    # Habit proxy = weekly/daily frequency (Conf if available)
    if not df_conf_f.empty and conf_map.get("freq"):
        f = df_conf_f[conf_map["freq"]].map(_lower)
        n_habit = int(f.str.contains("daily", na=False).sum() + f.str.contains("week", na=False).sum())
        n_habit = max(n_habit, int(n_trial*0.4))
    else:
        n_habit = int(n_trial*0.4)
    # Advocacy proxy = “godesi” in Sweets top3
    if not df_sweets_f.empty and sweets_map.get("top3"):
        n_adv = int(df_sweets_f[sweets_map["top3"]].astype(str).str.contains("godesi", case=False, na=False).sum())
    else:
        n_adv = int(n_habit * 0.3)

    stages = ["Discovery","Trial","Habit","Advocacy"]
    values = [n_disc, n_trial, n_habit, n_adv]
    df_line = pd.DataFrame({"stage": stages, "value": values})
    line = alt.Chart(df_line).mark_line(point=True, color=PALETTE[0]).encode(
        x=alt.X("stage:N", title="Stage", sort=stages),
        y=alt.Y("value:Q", title="Consumers (approx.)"),
        tooltip=["stage:N","value:Q"]
    )
    st.altair_chart(style_chart(line).properties(height=340, title="GO DESi Consumer Journey Funnel"), use_container_width=True)

    st.markdown("""
<div class="insight"><b>What we see:</b> Strong discovery and trial, leakage before habit; advocacy is low (recall gap).<br/>
<b>Implication:</b> Create habit hooks (post-meal minis, resealable pouches) and advocacy loops (refer-a-friend, UGC nostalgia).<br/>
<b>Connects to next:</b> Concrete comms pillars and actions to fix each leakage point.</div>
""", unsafe_allow_html=True)

# 10) Strategy — crisp actions
with tabs[9]:
    st.subheader("Communication Pillars & Action Plan")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
**Pillars**
- **Taste First** — lead with chatpata flavour cues.
- **Better Ingredients** — clean, trustworthy, Indian-first.
- **Nostalgia × Fun** — childhood taste in a playful format.
- **Post-Meal Friendly** — position as light, digestif-like candy.
- **Master-Brand Linkage** — “GO DESi makes Popz **and** Sweets”.
""")
    with c2:
        st.markdown("""
**Action Plan**
- **Social-first sampling**: reels + micro-influencer trials; track “discovered via Instagram”.
- **Trial SKUs**: small packs at cash tills + QR to subscribe.
- **Habit hooks**: after-meal minis, resealable pouches, counters in dine-outs.
- **Advocacy loop**: refer-a-friend; UGC around nostalgia moments.
- **Cross-promos**: Popz in Sweets & vice-versa; master-brand banner on PDPs.
- **Sweets playbook**: focus on festive/dessert occasions; lean into authenticity vs Local/Homemade.
""")
