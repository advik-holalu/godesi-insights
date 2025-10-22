import matplotlib.pyplot as plt
import os

output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# Define approximate funnel values (you can adjust based on dataset counts)
stages = ["Discovery", "Trial", "Habit", "Advocacy"]
values = [60, 45, 25, 10]  # number of consumers at each stage

plt.figure(figsize=(6,5))
plt.plot(stages, values, marker="o", color="#EF6C00", linewidth=3)
plt.fill_between(stages, values, color="#FFE0B2", alpha=0.7)
for i, v in enumerate(values):
    plt.text(i, v + 2, f"{v}", ha="center", fontweight="bold", color="#333")
plt.title("GO DESi Consumer Journey Funnel", pad=15, weight="bold", color="#333")
plt.xlabel("Journey Stage")
plt.ylabel("Number of Consumers (approx.)")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "consumer_journey_funnel.png"), dpi=300)
plt.close()

print("✅ Saved: consumer_journey_funnel.png")
