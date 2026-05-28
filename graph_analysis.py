import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.rcParams['font.family'] = ['Hiragino Sans', 'Hiragino Maru Gothic Pro', 'AppleGothic', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('/Users/makinoshuuhei/Desktop/課題3.csv')

COLORS = ['#4C72B0', '#DD8452', '#55A868', '#C44E52']
AFFILIATIONS = df['所属'].unique()
color_map = {aff: COLORS[i] for i, aff in enumerate(AFFILIATIONS)}

# ─── 円グラフ：所属ごとの参加者数 ────────────────────────────────
affil_counts = df['所属'].value_counts()

fig1, ax1 = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax1.pie(
    affil_counts,
    labels=affil_counts.index,
    autopct='%1.1f%%',
    startangle=90,
    colors=[color_map[a] for a in affil_counts.index],
    wedgeprops={'edgecolor': 'white', 'linewidth': 2},
    textprops={'fontsize': 13}
)
for at in autotexts:
    at.set_fontsize(12)
    at.set_fontweight('bold')
ax1.set_title('所属ごとの参加者数', fontsize=16, pad=20)
plt.tight_layout()
plt.savefig('/Users/makinoshuuhei/Desktop/test/pie_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print('pie_chart.png を保存しました')

# ─── 棒グラフ：所属ごとの平均・最高・最低スコア ─────────────────────
affil_stats = df.groupby('所属')['スコア'].agg(
    平均=('mean'), 最高=('max'), 最低=('min')
).reset_index()

x = np.arange(len(affil_stats))
width = 0.25

fig2, ax2 = plt.subplots(figsize=(10, 6))
b1 = ax2.bar(x - width, affil_stats['平均'], width, label='平均', color='#4C72B0', edgecolor='white')
b2 = ax2.bar(x,          affil_stats['最高'], width, label='最高', color='#55A868', edgecolor='white')
b3 = ax2.bar(x + width,  affil_stats['最低'], width, label='最低', color='#C44E52', edgecolor='white')

for bars in [b1, b2, b3]:
    for bar in bars:
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f'{bar.get_height():.1f}',
            ha='center', va='bottom', fontsize=9
        )

ax2.set_title('所属ごとのスコア比較（平均・最高・最低）', fontsize=15)
ax2.set_xlabel('所属', fontsize=13)
ax2.set_ylabel('スコア（点）', fontsize=13)
ax2.set_xticks(x)
ax2.set_xticklabels(affil_stats['所属'], fontsize=12)
ax2.set_ylim(0, 110)
ax2.legend(fontsize=11)
ax2.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('/Users/makinoshuuhei/Desktop/test/bar_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print('bar_chart.png を保存しました')

# ─── ヒストグラム：全参加者のスコア分布 ──────────────────────────────
fig3, ax3 = plt.subplots(figsize=(9, 6))
n, bins, patches = ax3.hist(
    df['スコア'],
    bins=8,
    range=(65, 100),
    color='#4C72B0',
    edgecolor='white',
    linewidth=0.8,
    alpha=0.85
)

mean_val   = df['スコア'].mean()
median_val = df['スコア'].median()
ax3.axvline(mean_val,   color='red',    linestyle='--', linewidth=2, label=f'平均: {mean_val:.1f}点')
ax3.axvline(median_val, color='orange', linestyle='--', linewidth=2, label=f'中央値: {median_val:.1f}点')

ax3.set_title('全参加者のスコア分布', fontsize=16)
ax3.set_xlabel('スコア（点）', fontsize=13)
ax3.set_ylabel('人数', fontsize=13)
ax3.legend(fontsize=11)
ax3.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('/Users/makinoshuuhei/Desktop/test/histogram.png', dpi=150, bbox_inches='tight')
plt.close()
print('histogram.png を保存しました')

print('\n--- 基本統計 ---')
print(f'総参加者数: {len(df)}人')
print(f'平均スコア: {mean_val:.2f}点')
print(f'最高: {df["スコア"].max()}点  最低: {df["スコア"].min()}点')
print(f'標準偏差: {df["スコア"].std():.2f}')
print('\n所属別参加者数:')
print(df['所属'].value_counts().to_string())
