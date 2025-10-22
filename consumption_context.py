import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# === Setup ===
input_file = "Untitled spreadsheet.xlsx"
output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# === Read all sheets ===
excel_file = pd.ExcelFile(input_file)
sheets = [s for s in excel_file.sheet_names if "sweet" in s.lower() or "mint" in s.lower() or "confection" in s.lower()]
df = pd.concat([pd.read_excel(input_file, sheet_name=s) for s in sheets], ignore_index=True)

# === Clean columns ===
df.columns = df.columns.str.strip().str.lower()

# Identify columns
age_col = [c for c in df.columns if "age" in c][0]
when_col = [c for c in df.columns if "when" in c and "popz" in c][0]

# Clean data
df[age_col] = df[age_col].astype(str).str.strip()
df[when_col] = df[when_col].astype(str).str.strip()

# === Matplotlib global style ===
plt.rcParams.update({
    "font.family": "Inter",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#EEEEEE",
    "axes.grid": False
})

# === 1. Bar Chart (When consumers eat) ===
context_counts = (
    df[when_col]
    .value_counts()
    .head(8)
    .sort_values(ascending=True)
)

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(context_counts.index, context_counts.values, color="#F57C00", height=0.5)
ax.bar_label(bars, fmt='%d', padding=4, fontsize=10, color="#333333")
ax.set_title("When Consumers Usually Eat Desi Popz", pad=15, weight="bold", color="#333333")
ax.set_xlabel("Number of Mentions")
ax.set_ylabel("")
sns.despine(left=True, bottom=True)
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "consumption_context_bar_clean.png"), dpi=300)
plt.close()

# === 2. Heatmap (Age × Context) ===
pivot = pd.crosstab(df[age_col], df[when_col])
plt.figure(figsize=(10, 5))
sns.heatmap(
    pivot,
    annot=True,
    fmt="g",
    cmap="YlOrBr",
    linewidths=0.4,
    cbar_kws={'label': 'Mentions'},
    annot_kws={"size": 9}
)
plt.title("Age Group × Consumption Context", pad=15, weight="bold", color="#333333")
plt.xlabel("Consumption Moment")
plt.ylabel("Age Group")
plt.xticks(rotation=30, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "consumption_context_heatmap_clean.png"), dpi=300)
plt.close()

print("✅ Saved clean visuals: consumption_context_bar_clean.png & consumption_context_heatmap_clean.png")
