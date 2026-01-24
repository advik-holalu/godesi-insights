# streamlit run app.py
# expects "Untitled spreadsheet.xlsx" in same folder

import pandas as pd
import streamlit as st
import altair as alt
import re
import os

# =====================================================
# PAGE CONFIG + THEME
# =====================================================
st.set_page_config(page_title="GO DESi – Consumer Insights", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 0.8rem; }
h1, h2 { color: #F59E0B !important; }
</style>
""", unsafe_allow_html=True)

st.title("GO DESi – Consumer Insights")
st.caption("Source: Master Survey Sheet")

PALETTE = ["#F59E0B", "#22D3EE", "#8B5CF6", "#34D399", "#F472B6"]

# =====================================================
# DATA LOADING
# =====================================================
FILE = "Untitled spreadsheet.xlsx"
if not os.path.exists(FILE):
    st.error("Master file not found")
    st.stop()

@st.cache_data
def load_master():
    xl = pd.ExcelFile(FILE)
    sheet = next(s for s in xl.sheet_names if "master" in s.lower())
    df = pd.read_excel(FILE, sheet_name=sheet)
    df.columns = [c.strip().lower() for c in df.columns]
    return df

df_raw = load_master()

# =====================================================
# COLUMN MAPPING (BUSINESS MEANING)
# =====================================================
COLS = {
    "customer_name": "customer name",
    "age": "age",
    "gender": "gender",

    # Column D (note: “here” typo in sheet)
    "heard_when": "first here about go desi",

    # Column E
    "product_category": "product category",

    # Column F
    "discovery": "how did the customer hear about desi popz",

    # Column G
    "frequency": "how often does the customer eat desi popz",

    # Column H
    "consumption_moment": "when does the customer usually eat desi popz",

    # Column I
    "perception": "what is desi popz",

    # Column J
    "motivation": "why do you choose desi popz",

    # Column K
    "brand_linkage": "did you know we also make indian sweets",

    # Column L
    "other_packaged_brands": "which other packaged indian sweet brand",

    # Column M
    "top_3_packaged_brands": "top 3 packaged indian sweet brands",

    # Column N
    "brand_preference": "which packaged sweets brand you prefer",

    # Column O
    "consumption_frequency": "how often do you consume packaged indian sweets",

    # Column P
    "consumption_occasion": "on what occasions you consume packaged indian sweets"
}

def find_col(key):
    token = COLS[key]
    matches = [c for c in df_raw.columns if token in c]
    if not matches:
        raise ValueError(f"Column not found for key='{key}' using token='{token}'")
    return matches[0]

age_col = find_col("age")
gender_col = find_col("gender")
heard_when_col = find_col("heard_when")
product_col = find_col("product_category")
discovery_col = find_col("discovery")
frequency_col = find_col("frequency")
moment_col = find_col("consumption_moment")
perception_col = find_col("perception")
motivation_col = find_col("motivation")
linkage_col = find_col("brand_linkage")
other_brand_col = find_col("other_packaged_brands")
top3_col = find_col("top_3_packaged_brands")
preference_col = find_col("brand_preference")
freq_col = find_col("consumption_frequency")
occasion_col = find_col("consumption_occasion")

# =====================================================
# GENERIC HELPERS
# =====================================================
def clean_text(x):
    if pd.isna(x):
        return None
    return re.sub(r"\s+", " ", str(x)).strip()

def safe_text(x):
    """
    Converts anything into a safe lowercase trimmed string.
    - NaN/None -> ""
    - numbers -> "123"
    - normal string -> "clean lowercase string"
    """
    if pd.isna(x):
        return ""
    return str(x).strip().lower()

def explode_multiselect(df, col):
    """
    Handles comma-separated multiselect answers safely.
    Example: "Instagram, Friend" -> 2 rows.
    """
    tmp = df.copy()
    tmp[col] = tmp[col].dropna().astype(str).str.split(",")
    tmp = tmp.explode(col)
    tmp[col] = tmp[col].astype(str).str.strip()
    return tmp[tmp[col] != ""]

# =====================================================
# UNMAPPED AUDIT (TERMINAL)
# =====================================================

def print_unmapped_report(df_src, raw_col, norm_col, label, id_cols=None, top_n=20):
    """
    Prints unmapped responses to terminal.
    Unmapped = raw has value but norm is NaN/None.
    """
    if id_cols is None:
        id_cols = []

    tmp = df_src.copy()

    # keep only rows with non-empty raw value
    tmp = tmp[tmp[raw_col].notna()]
    tmp = tmp[tmp[raw_col].astype(str).str.strip() != ""]

    # unmapped = norm is null
    unmapped = tmp[tmp[norm_col].isna()].copy()

    if unmapped.empty:
        print(f"✅ [{label}] No unmapped responses.")
        return

    print("\n" + "=" * 80)
    print(f"❗ UNMAPPED REPORT: {label}")
    print(f"Raw column: {raw_col}")
    print(f"Total unmapped rows: {len(unmapped)}")
    print("=" * 80)

    # print top unmapped values
    value_counts = (
        unmapped[raw_col]
        .astype(str)
        .str.strip()
        .value_counts()
        .head(top_n)
    )

    print("\nTop Unmapped Responses:")
    for val, cnt in value_counts.items():
        print(f"  ({cnt}) {val}")

    # print row-level details
    print("\nSample Row-level Unmapped Entries (first 50):")
    cols_to_print = id_cols + [raw_col]
    cols_to_print = [c for c in cols_to_print if c in unmapped.columns]

    for idx, row in unmapped[cols_to_print].head(50).iterrows():
        row_meta = " | ".join([f"{c}={row[c]}" for c in cols_to_print if c != raw_col])
        print(f"RowIndex={idx} | {row_meta} | UNMAPPED_VALUE={row[raw_col]}")

    # export all unmapped rows to CSV
    out_csv = f"unmapped_{label.lower().replace(' ', '_')}.csv"
    unmapped[cols_to_print].to_csv(out_csv, index=True)
    print(f"\n📁 Exported unmapped rows to: {out_csv}")


# =====================================================
# NORMALIZATION RULES
# =====================================================

# ---- Column D: When first heard ----
INVALID_HEARD_WHEN = {
    "not responded",
    "i don't remember",
    "dont remember",
    ""
}

# ---- Column F: Discovery Channel ----
DISCOVERY_MAP = {
    # Word of mouth
    "a friend or a family": "Word of Mouth",
    "a friend or family member": "Word of Mouth",
    "friend / family recommendation": "Word of Mouth",
    "received it as a gift": "Word of Mouth",

    # Corporate gifting
    "got it as gift from his company": "Corporate Gifting",

    # Social media
    "instagram": "Social Media",
    "facebook": "Social Media",
    "whatsapp": "Social Media",
    "youtube": "Social Media",

    # E-commerce
    "amazon": "E-commerce",
    "amazon/flipkart": "E-commerce",

    # Quick commerce
    "blinkit/instamart/zepto": "Quick Commerce",
    "swiggy instamart": "Quick Commerce",
    "online grocery app (blinkit, instamart, zepto, etc.)": "Quick Commerce",

    # Offline
    "saw it in a store": "In-store / Offline",
    "spotted in a store": "In-store / Offline",
    "shillong shop": "In-store / Offline",

    # Brand
    "go desi website": "Brand Website",

    # Media
    "shark tank": "Shark Tank",
    "sharktank india by my daughter": "Shark Tank",

    # Paid
    "ad": "Paid Advertising",
}

INVALID_DISCOVERY = {
    "not responded",
    "not sure",
    "dont know",
    "other",
    ""
}

# ---- Column H: Consumption Moment ----
CONSUMPTION_MOMENT_MAP = {
    # After meals
    "after lunch": "After meals",
    "after dinner": "After meals",
    "after meals": "After meals",

    # Evening snack
    "as an evening snack": "Evening snack",

    # Work / study
    "during work/study breaks": "During work / study breaks",

    # Watching content
    "while watching content": "While watching content (OTT / YouTube)",
    "while watching content (youtube/ott)": "While watching content (OTT / YouTube)",

    # Cravings
    "whenever i crave something sweet": "Whenever I crave something sweet",
    "to curb chatpata cravings": "Whenever I crave something sweet",
    "to curb my chatpata cravings": "Whenever I crave something sweet",
    "to curb chatpata cravings / craving": "Whenever I crave something sweet",

    # Festivals
    "only during festivals/special occasions": "Only during festivals / special occasions",

    # Travel
    "while traveling": "While travelling",
    "while travelling": "While travelling",

    # Bored / free time
    "when bored / free time / leisure": "When bored / free time",
    "when i'm bored": "When bored / free time",

    # Party
    "party": "Party / social occasions",

    # Any time
    "any time": "Any time",
    "anytime": "Any time",
    "all time": "Any time"
}

INVALID_CONSUMPTION_MOMENTS = {
    "not responded",
    "other",
    "none of the above",
    "it depends on mood",
    "when will get mood",
    "stopped eating / didn't like / not a regular consumer",
    "ocassionally",
    ""
}

# ---- Column I: Perception ----
PERCEPTION_MAP = {
    # Candy / Lollipop
    "candy": "Candy",
    "lollipop": "Lollipop",

    # Tangy / Chatpata
    "tangy": "Tangy / Chatpata Treat",
    "chatak chussa": "Tangy / Chatpata Treat",
    "tamarind": "Tangy / Chatpata Treat",
    "imli": "Tangy / Chatpata Treat",
    "mango": "Tangy / Chatpata Treat",

    # Nostalgia
    "nostalgic": "Nostalgic Snack",
    "bachpan": "Nostalgic Snack",

    # Craving / Time pass
    "craving": "Craving / Time-pass Snack",
    "time pass": "Craving / Time-pass Snack",
    "break time": "Craving / Time-pass Snack",

    # Unique / Variety
    "unique": "Flavour Variety / Unique Taste",
    "variety": "Flavour Variety / Unique Taste",

    # Refreshment
    "refreshment": "Refreshment / Mouth Freshener",
    "mouth": "Refreshment / Mouth Freshener",

    # Digestive
    "churan": "Digestive / Churan-like",
    "chavanprash": "Digestive / Churan-like",

    # Quality
    "quality": "Quality / Premium",

    # Indian
    "indian": "Indian / Desi Snack",

    # Treat
    "treat": "Occasional Treat",

    # Negative
    "pathetic": "Negative Feedback",
    "didn't like": "Negative Feedback",
    "not a regular": "Negative Feedback",
}

INVALID_PERCEPTION = {
    "not responded",
    "",
}

# ---- Column J: Motivation ----
MOTIVATION_MAP = {
    "better ingredient": "Better Ingredients",
    "natural": "Natural / Clean Label",

    "guilt free": "Guilt-free Snacking",

    "nostalgic": "Nostalgic Vibes",

    "chatpata": "Chatpata / Tangy Taste",
    "chapati": "Chatpata / Tangy Taste",

    "fun to eat": "Fun to Eat",

    "unique format": "Unique Format",

    "taste": "Good Taste",

    "quality": "Quality",

    "wanted to try": "Curiosity / Trial",
    "just tried": "Curiosity / Trial",
    "curiosity": "Curiosity / Trial",

    "gift": "Gifting",

    "kids": "Kids Like It",

    "no one else": "Availability / No Alternatives",

    "don't like": "Negative Experience",
    "never ordered": "Negative Experience",
}

INVALID_MOTIVATION = {
    "not responded",
    "",
}

# ---- Column L: Other Packaged Indian Sweet Brands ----
BRAND_AWARENESS_MAP = {
    "haldiram": "Haldiram",
    "haldirams": "Haldiram",
    "halidiram": "Haldiram",

    "bikaji": "Bikaji",
    "bikaaji": "Bikaji",

    "bikanervala": "Bikanervala",
    "bikaner": "Bikanervala",

    "amul": "Amul",
    "farmley": "Farmley",

    "go desi": "GO DESi",
    "godesi": "GO DESi",
    "only go desi": "GO DESi",

    "anand sweets": "Anand Sweets",
    "anand": "Anand Sweets",

    "bhikharam": "Bhikharam Chandmal",
    "bhikharam chandmal": "Bhikharam Chandmal",

    "nandini": "Nandini Sweets",
    "nandini sweets": "Nandini Sweets",

    "karachi": "Karachi Bakery",
    "jabson": "Jabsons",
    "canbox": "Canbox",
    "daadi": "Daadi’s",
    "namaste india": "Namaste India",
}

LOCAL_BRAND_KEYWORDS = [
    "local",
    "sweet shop",
    "sweet stall",
    "almond house",
    "rajpurohit",
    "kanthi",
    "asha",
    "kranthi",
    "tiwari",
    "tewari",
    "vijaya",
]

INVALID_BRAND_RESPONSES = {
    "not responded",
    "not sure",
    "depends",
    "disconnected in mid of the call",
    "doesnt prefer packaged sweets",
    "dont prefer packaged sweets",
    "not aware of brands",
    "dont remember any brands",
    "manufacturer of sweets",
    "prefers home made sweets",
    "prefers whatever's convenient",
    ""
}

PRODUCT_ONLY_KEYWORDS = [
    "kaju",
    "katli",
    "laddu",
    "barfi",
    "barfis",
    "roll",
    "snack",
    "sweetcorn",
]

# ---- Column M: Top 3 Brands ----
SPONTANEOUS_BRAND_MAP = {
    "haldiram": "Haldiram",
    "haldirams": "Haldiram",
    "halidiram": "Haldiram",

    "bikaji": "Bikaji",
    "bikaaji": "Bikaji",

    "bikanervala": "Bikanervala",
    "bikaner": "Bikanervala",
    "bikano": "Bikanervala",

    "amul": "Amul",
    "farmley": "Farmley",

    "go desi": "GO DESi",
    "godesi": "GO DESi",

    "anand sweets": "Anand Sweets",
    "anand": "Anand Sweets",

    "bhikharam": "Bhikharam Chandmal",
    "nandini": "Nandini Sweets",

    "a2b": "A2B",
    "mtr": "MTR",

    "jabson": "Jabsons",
    "canbox": "Canbox",
    "daadi": "Daadi’s",
    "namaste india": "Namaste India",
    "karachi": "Karachi Bakery",
}

SPONTANEOUS_LOCAL_KEYWORDS = [
    "local",
    "sweet shop",
    "sweet stall",
    "almond house",
    "agarwal",
    "kanthi",
    "asha",
    "kranthi",
    "tiwari",
    "rajpurohit",
]

SPONTANEOUS_INVALID = {
    "not responded",
    "many",
    "all good",
    "all the sweets category",
    "prefers whatever's convenient",
    "dont prefer packaged sweets",
    "disconnected in mid of the call",
    ""
}

SPONTANEOUS_PRODUCT_KEYWORDS = [
    "kaju",
    "katli",
    "laddu",
    "barfi",
    "rasgulla",
    "jalebi",
    "peda",
    "milk",
]

# ---- Column N: Brand Preference ----
PREFERENCE_BRAND_MAP = {
    "haldiram": "Haldiram",
    "haldirams": "Haldiram",

    "go desi": "GO DESi",
    "godesi": "GO DESi",

    "bikaji": "Bikaji",
    "bikaaji": "Bikaji",

    "anand sweets": "Anand Sweets",
    "anand": "Anand Sweets",

    "daadi": "Daadi’s",
    "lal": "Lal Sweets",

    "local": "Local / Unbranded Sweets",
    "generic": "Local / Unbranded Sweets",
}

INVALID_PREFERENCE = {
    "not responded",
    "no preference / doesn’t consume",
    "no preference",
    ""
}

# ---- Column O: Consumption Frequency ----
FREQUENCY_MAP = {
    "daily": "Daily",
    "2-3 times a week": "2–3 times a week",
    "once a week": "Once a week",
    "a few times a month": "A few times a month",
    "occasionally": "Occasionally",
    "rarely": "Rarely",
}

INVALID_FREQUENCY = {
    "dont consume sweets",
    "do not consume sweets",
    "never",
    "not responded",
    ""
}

# ---- Column P: Consumption Occasions ----
OCCASION_MAP = {
    "after meals": "After meals / dessert",
    "dessert": "After meals / dessert",

    "tea": "Snack with tea / coffee",
    "coffee": "Snack with tea / coffee",
    "snack": "Snack with tea / coffee",

    "craving": "Cravings / impulse eating",
    "impulse": "Cravings / impulse eating",

    "bored": "Boredom / leisure",

    "festival": "Festivals",
    "festive": "Festivals",

    "special": "Special occasions",

    "travel": "Travel",
}

INVALID_OCCASIONS = {
    "does not consume",
    "not responded",
    ""
}

# =====================================================
# DATA TRANSFORMATION PIPELINE
# =====================================================

df = df_raw.copy()

# ---- Age ----
df[age_col] = df[age_col].map(clean_text)
df = df[df[age_col].notna()]
df = df[~df[age_col].astype(str).str.strip().str.lower().isin(["n/a", "not responded", ""])]

# ---- Gender ----
df[gender_col] = df[gender_col].map(clean_text)
df = df[df[gender_col].notna()]
df = df[~df[gender_col].astype(str).str.strip().str.lower().isin(["not responded", ""])]

# ---- When first heard ----
df[heard_when_col] = df[heard_when_col].map(clean_text)
df = df[df[heard_when_col].notna()]
df = df[~df[heard_when_col].astype(str).str.strip().str.lower().isin(INVALID_HEARD_WHEN)]

# ---- Product Category (explode BOTH) ----
def expand_product(x):
    x = clean_text(x)
    if x is None:
        return None
    if str(x).strip().lower() == "both":
        return ["Sweets", "Confectionery and Mints"]
    return [x]

df_product = df.copy()
df_product[product_col] = df_product[product_col].apply(expand_product)
df_product = df_product.dropna(subset=[product_col])
df_product = df_product.explode(product_col)

# ---- Discovery Channel ----
df_disc = df.copy()
df_disc[discovery_col] = df_disc[discovery_col].map(clean_text)

df_disc = explode_multiselect(df_disc, discovery_col)
df_disc["discovery_norm"] = (
    df_disc[discovery_col]
    .astype(str)
    .str.lower()
    .map(DISCOVERY_MAP)
)

df_disc = df_disc[
    ~df_disc[discovery_col].astype(str).str.lower().isin(INVALID_DISCOVERY)
]
df_disc = df_disc.dropna(subset=["discovery_norm"])

# ---- Consumption Frequency (Column G) ----
df[frequency_col] = df[frequency_col].map(clean_text)
df = df[df[frequency_col].notna()]
df = df[
    ~df[frequency_col].astype(str).str.strip().str.lower().isin(
        ["not responded", "not sure", ""]
    )
]

# ---- Consumption Moment (Column H) ----
df_moment = df.copy()
df_moment[moment_col] = df_moment[moment_col].map(clean_text)

df_moment = explode_multiselect(df_moment, moment_col)

df_moment["moment_norm"] = (
    df_moment[moment_col]
    .astype(str)
    .str.lower()
    .map(CONSUMPTION_MOMENT_MAP)
)

df_moment = df_moment[
    ~df_moment[moment_col].astype(str).str.lower().isin(INVALID_CONSUMPTION_MOMENTS)
]
df_moment = df_moment.dropna(subset=["moment_norm"])

# ---- Perception (Column I) ----
df_perception = df.copy()
df_perception[perception_col] = df_perception[perception_col].map(clean_text)

df_perception = explode_multiselect(df_perception, perception_col)

def map_perception(x):
    x_low = safe_text(x)
    if x_low == "":
        return None

    for k, v in PERCEPTION_MAP.items():
        if k in x_low:
            return v

    return None

df_perception["perception_norm"] = df_perception[perception_col].apply(map_perception)

df_perception = df_perception[
    ~df_perception[perception_col].astype(str).str.lower().isin(INVALID_PERCEPTION)
]
df_perception = df_perception.dropna(subset=["perception_norm"])

# ---- Motivation (Column J) ----
df_motivation = df.copy()
df_motivation[motivation_col] = df_motivation[motivation_col].map(clean_text)

df_motivation = explode_multiselect(df_motivation, motivation_col)

def map_motivation(x):
    x_low = safe_text(x)
    if x_low == "":
        return None

    for k, v in MOTIVATION_MAP.items():
        if k in x_low:
            return v

    return None

df_motivation["motivation_norm"] = df_motivation[motivation_col].apply(map_motivation)

df_motivation = df_motivation[
    ~df_motivation[motivation_col].astype(str).str.lower().isin(INVALID_MOTIVATION)
]
df_motivation = df_motivation.dropna(subset=["motivation_norm"])

# ---- Brand Linkage (Column K) ----
df_linkage = df.copy()
df_linkage[linkage_col] = df_linkage[linkage_col].map(clean_text)
df_linkage = df_linkage[df_linkage[linkage_col].isin(["Yes", "No"])]

# ---- Column L: Brand Awareness ----
df_brand = df.copy()
df_brand[other_brand_col] = df_brand[other_brand_col].map(clean_text)

df_brand = explode_multiselect(df_brand, other_brand_col)

def map_brand_awareness(x):
    x_low = safe_text(x)
    if x_low == "":
        return None

    if x_low in INVALID_BRAND_RESPONSES:
        return None

    for p in PRODUCT_ONLY_KEYWORDS:
        if p in x_low:
            return None

    for k, v in BRAND_AWARENESS_MAP.items():
        if k in x_low:
            return v

    for kw in LOCAL_BRAND_KEYWORDS:
        if kw in x_low:
            return "Local / Unbranded Sweets"

    return None

df_brand["brand_awareness_norm"] = df_brand[other_brand_col].apply(map_brand_awareness)
df_brand = df_brand.dropna(subset=["brand_awareness_norm"])

# ---- Column M: Spontaneous Recall (Top 3) ----
df_top3 = df.copy()
df_top3[top3_col] = df_top3[top3_col].map(clean_text)

df_top3 = explode_multiselect(df_top3, top3_col)

def map_spontaneous_brand(x):
    x_low = safe_text(x)
    if x_low == "":
        return None

    if x_low in SPONTANEOUS_INVALID:
        return None

    for p in SPONTANEOUS_PRODUCT_KEYWORDS:
        if p in x_low:
            return None

    for k, v in SPONTANEOUS_BRAND_MAP.items():
        if k in x_low:
            return v

    for kw in SPONTANEOUS_LOCAL_KEYWORDS:
        if kw in x_low:
            return "Local / Unbranded Sweets"

    return None

df_top3["spontaneous_brand_norm"] = df_top3[top3_col].apply(map_spontaneous_brand)
df_top3 = df_top3.dropna(subset=["spontaneous_brand_norm"])

# ---- Column N: Brand Preference ----
df_pref = df.copy()
df_pref[preference_col] = df_pref[preference_col].map(clean_text)

def map_preference_brand(x):
    x_low = safe_text(x)
    if x_low == "":
        return None

    if x_low in INVALID_PREFERENCE:
        return None

    for k, v in PREFERENCE_BRAND_MAP.items():
        if k in x_low:
            return v

    return None

df_pref["preferred_brand_norm"] = df_pref[preference_col].apply(map_preference_brand)
df_pref = df_pref.dropna(subset=["preferred_brand_norm"])

# ---- Column O: Consumption Frequency (Packaged sweets) ----
df_freq = df.copy()
df_freq[freq_col] = df_freq[freq_col].map(clean_text)

def map_frequency(x):
    x_low = safe_text(x)
    if x_low == "":
        return None

    if x_low in INVALID_FREQUENCY:
        return None

    for k, v in FREQUENCY_MAP.items():
        if k in x_low:
            return v

    return None

df_freq["consumption_frequency_norm"] = df_freq[freq_col].apply(map_frequency)
df_freq = df_freq.dropna(subset=["consumption_frequency_norm"])

# ---- Column P: Consumption Occasions ----
df_occ = df.copy()
df_occ[occasion_col] = df_occ[occasion_col].map(clean_text)
df_occ = explode_multiselect(df_occ, occasion_col)

def map_occasion(x):
    x_low = safe_text(x)
    if x_low == "":
        return None

    if x_low in INVALID_OCCASIONS:
        return None

    for k, v in OCCASION_MAP.items():
        if k in x_low:
            return v

    return None

df_occ["occasion_norm"] = df_occ[occasion_col].apply(map_occasion)
df_occ = df_occ.dropna(subset=["occasion_norm"])


# =====================================================
# KPI (ONLY TOTAL RESPONDENTS)
# =====================================================
total_respondents = df.shape[0]

st.metric(
    label="Total Respondents",
    value=f"{total_respondents}"
)

st.markdown("---")


# =====================================================
# APPLY SIDEBAR FILTERS CONSISTENTLY
# =====================================================
with st.sidebar:
    st.header("Filters")

    age_values = (
        df[age_col]
        .dropna()
        .astype(str)
        .unique()
    )

    age_filter = st.multiselect(
        "Age group",
        sorted(age_values),
        default=sorted(age_values)
    )

# denominator after filters (this will be used later for % charts)
total_respondents_filtered = df.loc[df[age_col].isin(age_filter)].shape[0]

# apply filter to ALL derived dfs
df_freq = df_freq.loc[df_freq[age_col].isin(age_filter)].copy()
df_brand = df_brand.loc[df_brand[age_col].isin(age_filter)].copy()
df_top3 = df_top3.loc[df_top3[age_col].isin(age_filter)].copy()
df_pref = df_pref.loc[df_pref[age_col].isin(age_filter)].copy()
df_disc = df_disc.loc[df_disc[age_col].isin(age_filter)].copy()
df_occ = df_occ.loc[df_occ[age_col].isin(age_filter)].copy()
df_perception = df_perception.loc[df_perception[age_col].isin(age_filter)].copy()
df_motivation = df_motivation.loc[df_motivation[age_col].isin(age_filter)].copy()
df_moment = df_moment.loc[df_moment[age_col].isin(age_filter)].copy()
df_linkage = df_linkage.loc[df_linkage[age_col].isin(age_filter)].copy()
df_product = df_product.loc[df_product[age_col].isin(age_filter)].copy()

# =====================================================
# TABS
# =====================================================
tabs = st.tabs([
    "Demographics",
    "Discovery",
    "Consumption",
    "Perception",
    "Motivation",
    "Sweets Awareness",
    "Sweets Preference",
    "Brand Linkage"
])

# =====================================================
# COMMON CHART HELPERS
# =====================================================
def bar_chart_with_pct_labels(df_counts, y_col, x_col="Pct", color="#22D3EE", title="% of Total Respondents"):
    """
    Horizontal bar chart with % labels at end of each bar.
    Expects df_counts columns:
      - y_col: category
      - Pct
      - Count (optional but recommended for tooltip)
    """

    bars = alt.Chart(df_counts).mark_bar(color=color).encode(
        x=alt.X(f"{x_col}:Q", title=title),
        y=alt.Y(f"{y_col}:N", sort="-x"),
        tooltip=[
            alt.Tooltip(f"{y_col}:N", title=y_col),
            alt.Tooltip("Pct:Q", format=".1f", title="%"),
            alt.Tooltip("Count:Q", title="Count")
        ] if "Count" in df_counts.columns else [
            alt.Tooltip(f"{y_col}:N", title=y_col),
            alt.Tooltip("Pct:Q", format=".1f", title="%")
        ]
    )

    labels = alt.Chart(df_counts).mark_text(
        align="left",
        baseline="middle",
        dx=6,
        fontSize=12,
        color="white"
    ).encode(
        x=f"{x_col}:Q",
        y=alt.Y(f"{y_col}:N", sort="-x"),
        text=alt.Text("Pct:Q", format=".1f")
    ).transform_calculate(
        PctLabel="format(datum.Pct, '.1f') + '%'"
    ).encode(
        text="PctLabel:N"
    )

    return bars + labels


# =====================================================
# TAB 1 — DEMOGRAPHICS
# =====================================================
with tabs[0]:
    st.subheader("Respondent Profile")

    demo_df = df.loc[df[age_col].isin(age_filter)].copy()

    age_counts = demo_df[age_col].value_counts().reset_index()
    age_counts.columns = ["Age", "Count"]

    if total_respondents_filtered > 0:
        age_counts["Pct"] = (age_counts["Count"] / total_respondents_filtered) * 100
    else:
        age_counts["Pct"] = 0

    chart = bar_chart_with_pct_labels(
        df_counts=age_counts,
        y_col="Age",
        color=PALETTE[0]
    )

    st.altair_chart(chart, use_container_width=True)


# =====================================================
# TAB 2 — DISCOVERY
# =====================================================
with tabs[1]:
    st.subheader("How customers discovered GO DESi")

    disc_counts = df_disc["discovery_norm"].value_counts().reset_index()
    disc_counts.columns = ["Channel", "Count"]

    if total_respondents_filtered > 0:
        disc_counts["Pct"] = (disc_counts["Count"] / total_respondents_filtered) * 100
    else:
        disc_counts["Pct"] = 0

    chart = bar_chart_with_pct_labels(
        df_counts=disc_counts,
        y_col="Channel",
        color=PALETTE[1]
    )

    st.altair_chart(chart, use_container_width=True)
    st.caption("Note: Discovery is multi-select, so totals can exceed 100%.")


# =====================================================
# TAB 3 — CONSUMPTION
# =====================================================
with tabs[2]:
    st.subheader("Packaged Sweets Consumption Behaviour")

    c1, c2 = st.columns(2)

    # ---- Frequency of Consumption ----
    with c1:
        st.markdown("**How often consumers eat packaged sweets**")

        freq_counts = df_freq["consumption_frequency_norm"].value_counts().reset_index()
        freq_counts.columns = ["Frequency", "Count"]

        if total_respondents_filtered > 0:
            freq_counts["Pct"] = (freq_counts["Count"] / total_respondents_filtered) * 100
        else:
            freq_counts["Pct"] = 0

        chart_freq = bar_chart_with_pct_labels(
            df_counts=freq_counts,
            y_col="Frequency",
            color=PALETTE[2]
        )

        st.altair_chart(chart_freq, use_container_width=True)

    # ---- Consumption Occasions ----
    with c2:
        st.markdown("**When consumers eat packaged sweets**")

        occ_counts = df_occ["occasion_norm"].value_counts().reset_index()
        occ_counts.columns = ["Occasion", "Count"]

        if total_respondents_filtered > 0:
            occ_counts["Pct"] = (occ_counts["Count"] / total_respondents_filtered) * 100
        else:
            occ_counts["Pct"] = 0

        chart_occ = bar_chart_with_pct_labels(
            df_counts=occ_counts,
            y_col="Occasion",
            color=PALETTE[3]
        )

        st.altair_chart(chart_occ, use_container_width=True)

    st.markdown("---")
    st.subheader("Age Group vs Consumption Context")

    heat_df = (
        df_moment
        .groupby([age_col, "moment_norm"])
        .size()
        .reset_index(name="Count")
    )

    if total_respondents_filtered > 0:
        heat_df["Pct"] = (heat_df["Count"] / total_respondents_filtered) * 100
    else:
        heat_df["Pct"] = 0

    heatmap = alt.Chart(heat_df).mark_rect().encode(
        x=alt.X("moment_norm:N", title="Consumption Moment"),
        y=alt.Y(f"{age_col}:N", title="Age Group"),
        color=alt.Color("Pct:Q", title="%", scale=alt.Scale(scheme="yelloworangebrown")),
        tooltip=[
            alt.Tooltip(f"{age_col}:N", title="Age Group"),
            alt.Tooltip("moment_norm:N", title="Moment"),
            alt.Tooltip("Pct:Q", format=".1f", title="%"),
            alt.Tooltip("Count:Q", title="Count")
        ]
    )

    heat_text = alt.Chart(heat_df).mark_text(baseline="middle", fontSize=11).encode(
        x="moment_norm:N",
        y=alt.Y(f"{age_col}:N"),
        text=alt.Text("Pct:Q", format=".0f"),
        color=alt.condition(
            alt.datum.Pct > 8,
            alt.value("black"),
            alt.value("white")
        )
    ).transform_calculate(
        Label="format(datum.Pct, '.0f') + '%'"
    ).encode(
        text="Label:N"
    )

    st.altair_chart((heatmap + heat_text), use_container_width=True)

    st.caption("Note: Consumption moments are multi-select, so totals can exceed 100%.")


# =====================================================
# TAB 4 — PERCEPTION
# =====================================================
with tabs[3]:
    st.subheader("How consumers perceive GO DESi (Desi Popz)")

    perception_counts = df_perception["perception_norm"].value_counts().reset_index()
    perception_counts.columns = ["Perception", "Count"]

    if total_respondents_filtered > 0:
        perception_counts["Pct"] = (perception_counts["Count"] / total_respondents_filtered) * 100
    else:
        perception_counts["Pct"] = 0

    chart = bar_chart_with_pct_labels(
        df_counts=perception_counts,
        y_col="Perception",
        color=PALETTE[4]
    )

    st.altair_chart(chart, use_container_width=True)
    st.caption("Note: Perception can be multi-select, so totals can exceed 100%.")


# =====================================================
# TAB 5 — MOTIVATION
# =====================================================
with tabs[4]:
    st.subheader("Why consumers choose GO DESi")

    motivation_counts = df_motivation["motivation_norm"].value_counts().reset_index()
    motivation_counts.columns = ["Motivation", "Count"]

    if total_respondents_filtered > 0:
        motivation_counts["Pct"] = (motivation_counts["Count"] / total_respondents_filtered) * 100
    else:
        motivation_counts["Pct"] = 0

    chart = bar_chart_with_pct_labels(
        df_counts=motivation_counts,
        y_col="Motivation",
        color=PALETTE[2]
    )

    st.altair_chart(chart, use_container_width=True)

    st.markdown("---")
    st.subheader("Age Group vs Purchase Motivation")

    mot_heat_df = (
        df_motivation
        .groupby([age_col, "motivation_norm"])
        .size()
        .reset_index(name="Count")
    )

    if total_respondents_filtered > 0:
        mot_heat_df["Pct"] = (mot_heat_df["Count"] / total_respondents_filtered) * 100
    else:
        mot_heat_df["Pct"] = 0

    mot_heatmap = alt.Chart(mot_heat_df).mark_rect().encode(
        x=alt.X("motivation_norm:N", title="Motivation"),
        y=alt.Y(f"{age_col}:N", title="Age Group"),
        color=alt.Color("Pct:Q", title="%", scale=alt.Scale(scheme="tealblues")),
        tooltip=[
            alt.Tooltip(f"{age_col}:N", title="Age Group"),
            alt.Tooltip("motivation_norm:N", title="Motivation"),
            alt.Tooltip("Pct:Q", format=".1f", title="%"),
            alt.Tooltip("Count:Q", title="Count")
        ]
    )

    mot_text = alt.Chart(mot_heat_df).mark_text(baseline="middle", fontSize=11).encode(
        x="motivation_norm:N",
        y=alt.Y(f"{age_col}:N"),
        text=alt.Text("Pct:Q", format=".0f"),
        color=alt.condition(
            alt.datum.Pct > 8,
            alt.value("black"),
            alt.value("white")
        )
    ).transform_calculate(
        Label="format(datum.Pct, '.0f') + '%'"
    ).encode(
        text="Label:N"
    )

    st.altair_chart((mot_heatmap + mot_text), use_container_width=True)

    st.caption("Note: Motivation is multi-select, so totals can exceed 100%.")


# =====================================================
# TAB 6 — SWEETS AWARENESS
# =====================================================
with tabs[5]:
    st.subheader("Other packaged Indian sweet brands consumers are aware of")

    awareness_counts = df_brand["brand_awareness_norm"].value_counts().reset_index()
    awareness_counts.columns = ["Brand", "Mentions"]

    awareness_counts["Count"] = awareness_counts["Mentions"]

    if total_respondents_filtered > 0:
        awareness_counts["Pct"] = (awareness_counts["Mentions"] / total_respondents_filtered) * 100
    else:
        awareness_counts["Pct"] = 0

    chart = bar_chart_with_pct_labels(
        df_counts=awareness_counts,
        y_col="Brand",
        color=PALETTE[3]
    )

    st.altair_chart(chart, use_container_width=True)
    st.caption("Note: Awareness is multi-select, so totals can exceed 100%.")


# =====================================================
# TAB 7 — SWEETS PREFERENCE
# =====================================================
with tabs[6]:
    st.subheader("Preferred packaged Indian sweets brand")

    pref_counts = df_pref["preferred_brand_norm"].value_counts().reset_index()
    pref_counts.columns = ["Brand", "Count"]

    if total_respondents_filtered > 0:
        pref_counts["Pct"] = (pref_counts["Count"] / total_respondents_filtered) * 100
    else:
        pref_counts["Pct"] = 0

    chart = bar_chart_with_pct_labels(
        df_counts=pref_counts,
        y_col="Brand",
        color=PALETTE[4]
    )

    st.altair_chart(chart, use_container_width=True)


# =====================================================
# TAB 8 — BRAND LINKAGE
# =====================================================
with tabs[7]:
    st.subheader("Awareness of GO DESi’s Indian sweets portfolio")

    linkage_counts = df_linkage[linkage_col].value_counts().reset_index()
    linkage_counts.columns = ["Response", "Count"]

    if total_respondents_filtered > 0:
        linkage_counts["Pct"] = (linkage_counts["Count"] / total_respondents_filtered) * 100
    else:
        linkage_counts["Pct"] = 0

    chart = bar_chart_with_pct_labels(
        df_counts=linkage_counts,
        y_col="Response",
        color=PALETTE[1]
    )

    st.altair_chart(chart, use_container_width=True)

    yes_count = (df_linkage[linkage_col] == "Yes").sum()
    no_count = (df_linkage[linkage_col] == "No").sum()
    total_linkage = yes_count + no_count

    pct_yes = round((yes_count / total_linkage) * 100, 1) if total_linkage else 0

    st.markdown("---")
    st.markdown(
        f"**{pct_yes}%** of respondents know that **GO DESi also makes Indian sweets** "
        f"(Yes: {yes_count}, No: {no_count})"
    )