import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

input_file = "Untitled spreadsheet.xlsx"
output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# Read data
excel_file = pd.ExcelFile(input_file)
sheets = [s for s in excel_file.sheet_names if "sweet" in s.lower() or "mint" in s.lower() or "confection" in s.lower()]
df = pd.concat([pd.read_excel(input_file, sheet_name=s) for s in sheets], ignore_index=True)
df.columns = df.columns.str.strip().str.lower()

# Identify columns
why_col = [c for c in df.columns if "why" in c and "popz" in c][0]
age_col = [c for c in df.columns if "age" in c][0]

df[why_col] = df[why_col].astype(str).str.lower().str.strip()
df[age_col] = df[age_col].astype(str).str.strip()

# --- Categorize motives ---
def categorize(reason):
    if any(k in reason for k in ["taste", "chatpata", "flavour", "flavor"]):
        return "Taste / Flavour"
    elif any(k in reason for k in ["ingredient", "quality", "natural", "homemade"]):
        return "Ingredients / Quality"
    elif any(k in reason for k in ["nostalgic", "childhood", "memory"]):
        return "Emotion / Nostalgia"
    elif any(k in reason for k in ["fun", "unique", "format", "experience", "lollipop"]):
        return "Format / Experience"
    elif any(k in reason for k in ["packaging", "gift", "present"]):
        return "Packaging / Gift"
    elif "not" in reason or "none" in reason or "no" in reason or "nan" in reason:
        return "Other / Non-motivational"
    else:
        return "Other / Non-motivational"

df["motivation_category"] = df[why_col].apply(categorize)

# --- 1. Motivation Bar Chart ---
motivation_counts = df["motivation_category"].value_counts().sort_values(ascending=True)
plt.figure(figsize=(8,4))
bars = plt.barh(motivation_counts.index, motivation_counts.values, color="#F57C00", height=0.5)
plt.bar_label(bars, fmt='%d', padding=4, fontsize=10, color="#333")
plt.title("Why Do Consumers Choose Desi Popz?", pad=15, weight="bold", color="#333")
plt.xlabel("Number of Mentions")
plt.ylabel("")
sns.despine(left=True, bottom=True)
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "purchase_motivation_bar.png"), dpi=300)
plt.close()

# --- 2. Heatmap: Age × Motivation ---
pivot = pd.crosstab(df[age_col], df["motivation_category"])
plt.figure(figsize=(9,5))
sns.heatmap(pivot, annot=True, fmt="g", cmap="YlOrBr", linewidths=0.4, annot_kws={"size":9})
plt.title("Age Group × Motivation Theme", pad=15, weight="bold", color="#333")
plt.xlabel("Motivation Theme")
plt.ylabel("Age Group")
plt.xticks(rotation=30, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "purchase_motivation_heatmap.png"), dpi=300)
plt.close()

print("✅ Saved: purchase_motivation_bar.png & purchase_motivation_heatmap.png")
