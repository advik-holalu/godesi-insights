import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Setup ---
input_file = "Untitled spreadsheet.xlsx"
output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# --- Auto-detect correct sheet name ---
xls = pd.ExcelFile(input_file)
print("Available sheets:", xls.sheet_names)
sheet_name = [s for s in xls.sheet_names if "confectionery" in s.lower()][0]
print(f"✅ Using sheet: {sheet_name}")

# --- Load Data ---
df = pd.read_excel(xls, sheet_name=sheet_name)
df.columns = df.columns.str.strip().str.lower()

# --- Identify columns ---
aware_col = [c for c in df.columns if "did you know" in c][0]
age_col = [c for c in df.columns if "age" in c][0]

# --- Clean & standardize awareness data ---
df[aware_col] = df[aware_col].astype(str).str.strip().str.title()
df[aware_col] = df[aware_col].replace({
    "Y": "Yes", "N": "No", 
    "Nan": "No", "": "No", 
    "Na": "No", "None": "No"
})

# --- Donut Chart: Overall Awareness ---
awareness_counts = df[aware_col].value_counts()
plt.figure(figsize=(5,5))
colors = ["#8E24AA", "#CE93D8"]
wedges, texts, autotexts = plt.pie(
    awareness_counts, labels=awareness_counts.index,
    colors=colors, autopct="%1.0f%%", startangle=90,
    wedgeprops=dict(width=0.45)
)
plt.setp(autotexts, size=11, weight="bold", color="white")
plt.title("Awareness That GO DESi Also Makes Sweets", pad=20, weight="bold", color="#333")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "brand_linkage_awareness_donut.png"), dpi=300)
plt.close()

# --- Heatmap: Age Group vs Awareness ---
pivot = pd.crosstab(df[age_col], df[aware_col])
plt.figure(figsize=(6,4))
sns.heatmap(pivot, annot=True, fmt="g", cmap="Purples", linewidths=0.5, cbar=False)
plt.title("Age Group vs Awareness of GO DESi Sweets", pad=15, weight="bold", color="#333")
plt.xlabel("Awareness Response")
plt.ylabel("Age Group")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "brand_linkage_awareness_heatmap.png"), dpi=300)
plt.close()

print("✅ Saved: brand_linkage_awareness_donut.png & brand_linkage_awareness_heatmap.png")
