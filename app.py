# streamlit run app.py
# expects "Untitled spreadsheet.xlsx" in the same folder

import os, re
import pandas as pd
import altair as alt
import streamlit as st

# =========================================================
# PAGE CONFIG + STYLE
# =========================================================
st.set_page_config(page_title="GO DESi Insights", layout="wide")

st.markdown("""
<style>
  .block-container { padding-top:0.8rem; }
  h1, h2 { color:#F59E0B !important; }
  .insight {
      background: rgba(245,158,11,0.08);
      border: 1px solid rgba(245,158,11,0.25);
      padding: 10px 12px; border-radius: 10px;
      margin: 10px 0 16px 0;
  }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>GO DESi Consumer Insights</h1>", unsafe_allow_html=True)
st.caption(f"Last refreshed: {pd.Timestamp.now().strftime('%d %b %Y, %I:%M %p')}")
st.caption("All insights derived from a single Master sheet")

PALETTE = ["#F59E0B","#8B5CF6","#22D3EE","#34D399","#F472B6"]

# =========================================================
# CORE HELPERS
# =========================================================
def norm(x):
    if pd.isna(x): return ""
    return re.sub(r"\s+"," ", str(x).strip())

def lower(x): return norm(x).lower()

def load_sheet(path):
    xl = pd.ExcelFile(path)
    sheet = next((s for s in xl.sheet_names if "master" in s.lower()), None)
    if not sheet:
        st.error("No sheet containing 'Master' found.")
        st.stop()
    return pd.read_excel(path, sheet_name=sheet)

def clean_df(df):
    df = df.copy()
    df.columns = [lower(c) for c in df.columns]
    for c in df.columns:
        if df[c].dtype == "O":
            df[c] = df[c].map(norm)
    return df

def map_cols(df, spec):
    out = {k: None for k in spec}
    for key, tokens in spec.items():
        for col in df.columns:
            if all(t in col for t in tokens):
                out[key] = col
                break
    return out

def vc(series):
    s = (
        series.dropna()
        .astype(str)
        .map(norm)
    )

    # remove non-responses
    s = s[~s.str.lower().isin([
        "not responded",
        "not response",
        "no response",
        "na",
        "n/a",
        "none",
        ""
    ])]

    if s.empty:
        return pd.DataFrame(columns=["label", "count"])

    return s.value_counts().rename_axis("label").reset_index(name="count")

# ---------- Charts ----------
def chart(c):
    return (c.configure(background="transparent")
             .configure_axis(labelColor="#d1d5db", titleColor="#e5e7eb", gridColor="#1f2937")
             .configure_view(strokeWidth=0))

def hbar(df, title):
    if df.empty:
        st.info("No data"); return
    base = alt.Chart(df)
    bars = base.mark_bar(color=PALETTE[0]).encode(
        y=alt.Y("label:N", sort="-x", title=""),
        x=alt.X("count:Q", title="Count"),
        tooltip=["label:N","count:Q"]
    )
    txt = base.mark_text(align="left", dx=4).encode(
        y="label:N", x="count:Q", text="count:Q"
    )
    st.altair_chart(chart(bars + txt).properties(title=title), use_container_width=True)

def donut(df, title):
    if df.empty:
        st.info("No data"); return
    total = df["count"].sum()
    df["pct"] = (df["count"] * 100 / total).round(1)
    d = (
        alt.Chart(df)
        .mark_arc(innerRadius=70)
        .encode(
            theta="count:Q",
            color=alt.Color("label:N", scale=alt.Scale(range=PALETTE)),
            tooltip=["label:N","count:Q","pct:Q"]
        )
    )
    st.altair_chart(chart(d).properties(title=title, height=300), use_container_width=False)

def heatmap(ct, title, xlab, ylab):
    if ct.empty:
        st.info("No data"); return
    tidy = ct.reset_index().melt(ct.index.name, var_name="col", value_name="value")
    hm = (
        alt.Chart(tidy)
        .mark_rect()
        .encode(
            x=alt.X("col:N", title=xlab),
            y=alt.Y(f"{ct.index.name}:N", title=ylab),
            color=alt.Color("value:Q", scale=alt.Scale(scheme="goldorange")),
            tooltip=[f"{ct.index.name}:N","col:N","value:Q"]
        )
    )
    st.altair_chart(chart(hm).properties(title=title, height=300), use_container_width=True)

# =========================================================
# LOAD MASTER
# =========================================================
FILE = "Untitled spreadsheet.xlsx"
if not os.path.exists(FILE):
    st.error("File not found"); st.stop()

df = clean_df(load_sheet(FILE))

cols = map_cols(df, {
    "age":      ["age"],
    "gender":   ["gender"],
    "discover": ["how","hear","popz"],
    "when":     ["when","eat","popz"],
    "why":      ["why","choose","popz"],
    "what":     ["what","popz","is"],
    "freq":     ["how often","popz"],
    "know":     ["did","know","sweet"],
    "prefer":   ["prefer","sweet"],
    "topmind":  ["top","mind"],
    "top3":     ["top","3"],
    "occasion": ["occasion","sweet"]
})

# =========================================================
# SIDEBAR FILTERS
# =========================================================
with st.sidebar:
    st.header("Filters")
    if cols["age"]:
        all_age = sorted(df[cols["age"]].dropna().astype(str).unique())
        sel_age = st.multiselect("Age group", all_age, default=all_age)
    else:
        sel_age = []

df_f = df if not sel_age else df[df[cols["age"]].astype(str).isin(sel_age)]

# =========================================================
# MULTI-SELECT EXPLODER (FIXED)
# =========================================================
def explode_multiselect_df(df, col, extra_cols=None):
    if extra_cols is None:
        extra_cols = []
    tmp = df[[col] + extra_cols].dropna(subset=[col]).copy()
    tmp[col] = tmp[col].astype(str).str.split(",")
    tmp = tmp.explode(col)
    tmp[col] = tmp[col].str.strip()
    tmp = tmp[tmp[col] != ""]
    return tmp.reset_index(drop=True)

# =========================================================
# TABS
# =========================================================
tabs = st.tabs([
    "Demographics","Discovery","Consumption",
    "Perception","Motivation","Sweets Awareness",
    "Sweets Preference","Brand Linkage","Journey","Strategy"
])

# =========================================================
# TAB 1 — Demographics
# =========================================================
with tabs[0]:
    st.subheader("Respondent Profile")

    if cols["age"]:
        hbar(vc(df_f[cols["age"]]), "Age Distribution")

    if cols["gender"]:
        donut(vc(df_f[cols["gender"]]), "Gender Split")

    st.markdown("""
    <div class='insight'>
    Respondent distribution by age and gender.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 2 — Discovery
# =========================================================
with tabs[1]:
    st.subheader("Discovery Channels")

    col = cols["discover"]
    if col:
        hbar(vc(df_f[col]), "How they heard about Popz")

        if cols["age"]:
            ct = pd.crosstab(
                df_f[cols["age"]].astype(str),
                df_f[col].astype(str)
            )
            heatmap(ct, "Age × Discovery", "Channel", "Age")

    st.markdown("""
    <div class='insight'>
    Discovery sources vary by age cohort.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 3 — Consumption
# =========================================================
with tabs[2]:
    st.subheader("Consumption Context")

    col = cols["when"]
    if col:
        hbar(vc(df_f[col]), "When Consumers Eat Popz")

        if cols["age"]:
            ct = pd.crosstab(
                df_f[cols["age"]].astype(str),
                df_f[col].astype(str)
            )
            heatmap(ct, "Age × Consumption", "Moment", "Age")

    st.markdown("""
    <div class='insight'>
    Consumption moments highlight usage context.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 4 — Perception
# =========================================================
with tabs[3]:
    st.subheader("What is Popz?")

    col = cols["what"]
    if col:
        donut(vc(df_f[col]), "Consumer Perception (As Reported)")

    st.markdown("""
    <div class='insight'>
    Perception reflects raw consumer language.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 5 — Motivation (MULTI-SELECT SAFE)
# =========================================================
with tabs[4]:
    st.subheader("Why Consumers Choose Popz")

    col = cols["why"]
    if col:
        long = explode_multiselect_df(df_f, col, [cols["age"]])
        hbar(vc(long[col]), "Purchase Motivation")

        ct = pd.crosstab(
            long[cols["age"]],
            long[col]
        )
        heatmap(ct, "Age × Purchase Motivation", "Motivation", "Age")

    st.markdown("""
    <div class='insight'>
    Each selected motivation is counted independently.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 6 — Sweets Awareness (MULTI-SELECT SAFE)
# =========================================================
with tabs[5]:
    st.subheader("Packaged Sweets Awareness")

    cols_used = [cols["topmind"], cols["top3"], cols["prefer"]]
    cols_used = [c for c in cols_used if c]

    if cols_used:
        long_all = pd.concat([
            explode_multiselect_df(df_f, c)
            for c in cols_used
        ])

        hbar(vc(long_all.iloc[:, 0]), "Sweet Brand Mentions")

    st.markdown("""
    <div class='insight'>
    Awareness captured across multiple survey questions.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 7 — Sweets Preference & Occasion (MULTI-SELECT SAFE)
# =========================================================
with tabs[6]:
    st.subheader("Sweets Preference & Occasions")

    # Preference
    if cols["prefer"]:
        pref = explode_multiselect_df(df_f, cols["prefer"])
        donut(vc(pref[cols["prefer"]]), "Preferred Sweet Brands")

    # Occasion
    if cols["occasion"]:
        occ = explode_multiselect_df(df_f, cols["occasion"], [cols["age"]])
        hbar(vc(occ[cols["occasion"]]), "Occasions")

        ct = pd.crosstab(
            occ[cols["age"]],
            occ[cols["occasion"]]
        )
        heatmap(ct, "Age × Occasion", "Occasion", "Age")

    st.markdown("""
    <div class='insight'>
    Preferences and occasions reflect multi-select behavior.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 8 — Brand Linkage
# =========================================================
with tabs[7]:
    st.subheader("Do Popz Buyers Know GO DESi Makes Sweets?")

    col = cols["know"]
    if col:
        donut(vc(df_f[col]), "Awareness")

        if cols["age"]:
            ct = pd.crosstab(
                df_f[cols["age"]],
                df_f[col]
            )
            heatmap(ct, "Age × Awareness", "Awareness", "Age")

    st.markdown("""
    <div class='insight'>
    Cross-category brand linkage awareness.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 9 — Journey Funnel
# =========================================================
with tabs[8]:
    st.subheader("Consumer Journey Funnel")

    n1 = len(df_f)
    n2 = df_f[cols["why"]].notna().sum() if cols["why"] else 0
    n3 = df_f[cols["freq"]].notna().sum() if cols["freq"] else 0
    n4 = df_f[cols["top3"]].notna().sum() if cols["top3"] else 0

    df_j = pd.DataFrame({
        "Stage": ["Discovery", "Trial", "Habit", "Advocacy"],
        "Value": [n1, n2, n3, n4]
    })

    line = (
        alt.Chart(df_j)
        .mark_line(point=True, color=PALETTE[0])
        .encode(
            x="Stage:N",
            y="Value:Q",
            tooltip=["Stage", "Value"]
        )
    )

    st.altair_chart(chart(line).properties(height=320), use_container_width=True)

    st.markdown("""
    <div class='insight'>
    Funnel derived strictly from response availability.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 10 — Strategy
# =========================================================
with tabs[9]:
    st.subheader("Communication Strategy")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### Pillars
        - Taste First  
        - Better Ingredients  
        - Nostalgia × Fun  
        - Post-Meal Friendly  
        - Strong Master Branding
        """)

    with col2:
        st.markdown("""
        ### Actions
        - Reels + micro-influencers  
        - Trial packs at checkout  
        - Post-meal minis  
        - Cross-promos: Popz ↔ Sweets  
        - UGC + nostalgia loops
        """)
