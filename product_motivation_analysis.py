import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

input_file = "Untitled spreadsheet.xlsx"
output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# Auto-detect sheets
excel_file = pd.ExcelFile(input_file)
sheets = [s for s in excel_file.sheet_names if "sweet" in s.lower() or "mint" in s.lower() or "confection" in s.lower()]
df = pd.concat([pd.read_excel(input_file, sheet_name=s) for s in sheets], ignore_index=True)

df.columns = df.columns.str.strip().str.lower()

age_col = [c for c in df.columns if "age" in c][0]
why_col = [c for c in df.columns if "why" in c and "choose" in c][0]

# --- Bar chart of reasons ---
motivation_counts = df[why_col].dropna().str.strip().value_counts().head(8)
plt.figure(figsize=(8,4))
motivation_counts.plot(kind="barh", color="#f57c00")
plt.gca().invert_yaxis()
plt.title("Top Reasons for Choosing Desi Popz")
plt.xlabel("Number of Mentions")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "motivation_bar.png"), dpi=300)
plt.close()

# --- Heatmap: Age vs Reason ---
pivot = pd.crosstab(df[age_col], df[why_col])
plt.figure(figsize=(10,5))
sns.heatmap(pivot, annot=True, cmap="YlGnBu", fmt="g")
plt.title("Age Group vs Purchase Motivation of Desi Popz")
plt.xlabel("Purchase Motivation")
plt.ylabel("Age Group")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "motivation_heatmap.png"), dpi=300)
plt.close()

print("✅ motivation_bar.png and motivation_heatmap.png saved in", output_folder)
