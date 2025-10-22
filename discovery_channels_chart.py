import pandas as pd
import matplotlib.pyplot as plt
import os

input_file = "Untitled spreadsheet.xlsx"
output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# Detect sheet names automatically
excel_file = pd.ExcelFile(input_file)
sheet_names = [s for s in excel_file.sheet_names if "sweet" in s.lower() or "mint" in s.lower() or "confection" in s.lower()]
combined = pd.concat([pd.read_excel(input_file, sheet_name=s) for s in sheet_names], ignore_index=True)

combined.columns = combined.columns.str.strip().str.lower()
col = [c for c in combined.columns if "hear" in c and "popz" in c][0]

# Count frequency of discovery sources
counts = combined[col].dropna().str.strip().value_counts().head(10)

plt.figure(figsize=(8,4))
counts.plot(kind="barh", color="#f57c00")
plt.gca().invert_yaxis()
plt.title("Where Consumers First Heard About GO DESi")
plt.xlabel("Number of Mentions")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "discovery_channels.png"), dpi=300)
plt.close()

print("✅ discovery_channels.png generated in", output_folder)
