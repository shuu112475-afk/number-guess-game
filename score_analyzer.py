import csv
import sys
from statistics import mean, stdev


# ANSI カラーコード
class C:
    GOLD   = '\033[38;5;220m'
    SILVER = '\033[38;5;248m'
    BRONZE = '\033[38;5;130m'
    GREEN  = '\033[92m'
    RED    = '\033[91m'
    CYAN   = '\033[96m'
    YELLOW = '\033[93m'
    BOLD   = '\033[1m'
    DIM    = '\033[2m'
    RESET  = '\033[0m'

RANK_COLORS = {1: C.GOLD, 2: C.SILVER, 3: C.BRONZE}


def _fmt_num(n: float) -> str:
    """整数っぽい値は .0 を落として表示する。"""
    try:
        if float(n).is_integer():
            return str(int(n))
    except Exception:
        pass
    return str(n)


def _load_wide_csv(reader: csv.DictReader) -> tuple[list[dict], list[str]]:
    """横持ち: 名前 + (任意の科目列...)"""
    fieldnames = reader.fieldnames or []
    score_cols = [col for col in fieldnames if col != '名前']

    participants = []
    for row in reader:
        scores = [float(row[col]) for col in score_cols]
        participants.append({
            'name':    row['名前'],
            'scores':  scores,
            'avg':     round(mean(scores), 1),
            'max':     max(scores),
            'min':     min(scores),
            'total':   sum(scores),
        })

    return participants, score_cols


def _load_long_csv(reader: csv.DictReader) -> tuple[list[dict], list[dict]]:
    """
    縦持ち: 名前,日付,科目,スコア
    各レコードを個別に保持する（同一科目・複数日付でも平均しない）
    """
    required = {'名前', '科目', 'スコア'}
    fieldnames = set(reader.fieldnames or [])
    missing = required - fieldnames
    if missing:
        raise KeyError(f"縦持ちCSVに必要な列が不足しています: {', '.join(sorted(missing))}")

    has_date = '日付' in fieldnames
    records: list[dict] = []
    by_name: dict[str, list[tuple[float, str]]] = {}

    for row in reader:
        name = row['名前']
        score = float(row['スコア'])
        subject = row['科目']
        records.append({
            'name':    name,
            'date':    row.get('日付', '') if has_date else '',
            'subject': subject,
            'score':   score,
        })
        by_name.setdefault(name, []).append((score, subject))

    participants = []
    for name, score_subj_list in by_name.items():
        scores = [s for s, _ in score_subj_list]
        max_score = max(scores)
        min_score = min(scores)
        participants.append({
            'name':        name,
            'scores':      scores,
            'avg':         round(mean(scores), 1),
            'max':         max_score,
            'min':         min_score,
            'max_subject': next(subj for s, subj in score_subj_list if s == max_score),
            'min_subject': next(subj for s, subj in score_subj_list if s == min_score),
            'total':       sum(scores),
            'count':       len(scores),
        })

    return records, participants


def load_csv(filepath: str):
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        if {'科目', 'スコア'}.issubset(fieldnames):
            records, participants = _load_long_csv(reader)
            return 'long', records, participants
        participants, score_cols = _load_wide_csv(reader)
        return 'wide', participants, score_cols


def assign_ranks(participants: list[dict]) -> list[dict]:
    ranked = sorted(participants, key=lambda x: x['avg'], reverse=True)
    for i, p in enumerate(ranked):
        p['rank'] = i + 1
    return ranked


def col_width(header: str, values: list[str]) -> int:
    return max(len(header), *(len(v) for v in values))


def pad(text: str, width: int, align: str = 'right') -> str:
    """ANSI エスケープを含む文字列でも width 分パディングする。"""
    visible = len(text.encode('utf-8').decode('utf-8'))
    # ANSI コードの長さを除外して可視文字幅を計算
    ansi_len = sum(len(seq) for seq in _extract_ansi(text))
    visible = len(text) - ansi_len
    pad_n = width - visible
    spaces = ' ' * max(pad_n, 0)
    return (spaces + text) if align == 'right' else (text + spaces)


def _extract_ansi(text: str) -> list[str]:
    import re
    return re.findall(r'\033\[[0-9;]*m', text)


def colorize(text: str, color: str) -> str:
    return f"{color}{text}{C.RESET}"


def build_score_cell(score: int, row_max: int, row_min: int,
                     global_max: int, global_min: int) -> str:
    # NaN は縦持ちCSVの「科目データ無し」扱い
    if score != score:
        return '-'
    s = _fmt_num(score)
    if score == global_max:
        return colorize(s, C.BOLD + C.GREEN)
    if score == global_min:
        return colorize(s, C.BOLD + C.RED)
    if score == row_max:
        return colorize(s, C.GREEN)
    if score == row_min:
        return colorize(s, C.RED)
    return s


def print_separator(widths: list[int], style: str = 'mid') -> None:
    chars = {'top': ('╔', '╦', '╗', '═'),
             'mid': ('╠', '╬', '╣', '═'),
             'bot': ('╚', '╩', '╝', '═'),
             'sub': ('├', '┼', '┤', '─')}
    L, M, R, H = chars[style]
    parts = [H * (w + 2) for w in widths]
    print(L + M.join(parts) + R)


def print_row(cells: list[str], widths: list[int],
              aligns: list[str], border: str = '║') -> None:
    padded = [pad(c, w, a) for c, w, a in zip(cells, widths, aligns)]
    print(border + border.join(f' {p} ' for p in padded) + border)


def print_table(participants: list[dict], score_cols: list[str]) -> None:
    all_scores = [s for p in participants for s in p['scores'] if s == s]
    global_max = max(all_scores)
    global_min = min(all_scores)

    # --- ヘッダー定義 ---
    headers = ['順位', '名前'] + score_cols + ['合計', '平均', '最高', '最低']
    aligns  = ['right', 'left'] + ['right'] * len(score_cols) + ['right', 'right', 'right', 'right']

    # --- 各列の最大幅を算出 ---
    rows_plain: list[list[str]] = []
    for p in participants:
        rank_str = f"{'🥇' if p['rank']==1 else '🥈' if p['rank']==2 else '🥉' if p['rank']==3 else str(p['rank'])}"
        score_strs = [_fmt_num(s) if s == s else '-' for s in p['scores']]
        rows_plain.append(
            [str(p['rank']), p['name']] + score_strs +
            [_fmt_num(p['total']), _fmt_num(p['avg']), _fmt_num(p['max']), _fmt_num(p['min'])]
        )

    widths = [col_width(h, [r[i] for r in rows_plain]) for i, h in enumerate(headers)]

    # --- テーブル描画 ---
    print()
    print(C.BOLD + C.CYAN + '  ═══ スコア分析レポート ═══' + C.RESET)
    print()

    print_separator(widths, 'top')
    print_row([C.BOLD + h + C.RESET for h in headers], widths, aligns)
    print_separator(widths, 'mid')

    for p, plain_row in zip(participants, rows_plain):
        rank_color = RANK_COLORS.get(p['rank'], '')
        cells = []
        cells.append(colorize(plain_row[0], rank_color + C.BOLD) if rank_color else plain_row[0])
        cells.append(colorize(plain_row[1], rank_color + C.BOLD) if rank_color else plain_row[1])

        for i, score in enumerate(p['scores']):
            cells.append(build_score_cell(score, p['max'], p['min'], global_max, global_min))

        avg_color = C.GOLD if p['rank'] == 1 else (C.RED if p['rank'] == len(participants) else '')
        cells.append(plain_row[-4])  # 合計
        cells.append(colorize(plain_row[-3], avg_color + C.BOLD) if avg_color else plain_row[-3])
        cells.append(plain_row[-2])
        cells.append(plain_row[-1])

        print_row(cells, widths, aligns)

    # --- サマリー行 ---
    print_separator(widths, 'sub')
    avg_per_col = []
    for i in range(len(score_cols)):
        col_scores = [p['scores'][i] for p in participants if p['scores'][i] == p['scores'][i]]
        avg_per_col.append(round(mean(col_scores), 1) if col_scores else float('nan'))
    total_avgs  = [p['avg'] for p in participants]
    summary_cells = (
        [C.BOLD + '平均' + C.RESET, C.BOLD + '全員' + C.RESET]
        + [colorize(_fmt_num(a) if a == a else '-', C.DIM) for a in avg_per_col]
        + [colorize(_fmt_num(round(mean(p['total'] for p in participants), 1)), C.BOLD),
           colorize(_fmt_num(round(mean(total_avgs), 1)), C.BOLD),
           colorize(_fmt_num(round(mean(p['max'] for p in participants), 1)), C.BOLD),
           colorize(_fmt_num(round(mean(p['min'] for p in participants), 1)), C.BOLD)]
    )
    print_row(summary_cells, widths, aligns)
    print_separator(widths, 'bot')


def print_long_detail_table(records: list[dict], global_max: float, global_min: float) -> None:
    print()
    print(C.BOLD + C.CYAN + '  ═══ スコア詳細レポート ═══' + C.RESET)
    print()

    has_date = any(r['date'] for r in records)
    headers = ['名前', '日付', '科目', 'スコア'] if has_date else ['名前', '科目', 'スコア']
    aligns  = ['left', 'left', 'left', 'right'] if has_date else ['left', 'left', 'right']

    rows_plain = []
    for r in records:
        row = [r['name'], r['date'], r['subject'], _fmt_num(r['score'])] if has_date \
              else [r['name'], r['subject'], _fmt_num(r['score'])]
        rows_plain.append(row)

    widths = [col_width(h, [row[i] for row in rows_plain]) for i, h in enumerate(headers)]

    print_separator(widths, 'top')
    print_row([C.BOLD + h + C.RESET for h in headers], widths, aligns)
    print_separator(widths, 'mid')

    prev_name = None
    for row, r in zip(rows_plain, records):
        if prev_name is not None and prev_name != r['name']:
            print_separator(widths, 'sub')

        score_str = row[-1]
        if r['score'] == global_max:
            score_cell = colorize(score_str, C.BOLD + C.GREEN)
        elif r['score'] == global_min:
            score_cell = colorize(score_str, C.BOLD + C.RED)
        else:
            score_cell = score_str

        cells = list(row)
        cells[-1] = score_cell
        print_row(cells, widths, aligns)
        prev_name = r['name']

    print_separator(widths, 'bot')


def print_long_summary_table(participants: list[dict]) -> None:
    global_max_score = max(p['max'] for p in participants)
    global_min_score = min(p['min'] for p in participants)

    print()
    print(C.BOLD + C.CYAN + '  ═══ 参加者別スコアサマリー ═══' + C.RESET)
    print()

    headers = ['順位', '名前', '受験回数', '合計', '平均', '最高', '最低']
    aligns  = ['right', 'left', 'right', 'right', 'right', 'right', 'right']

    rows_plain = [[
        str(p['rank']), p['name'], str(p['count']),
        _fmt_num(p['total']), _fmt_num(p['avg']),
        f"{_fmt_num(p['max'])}({p['max_subject']})",
        f"{_fmt_num(p['min'])}({p['min_subject']})",
    ] for p in participants]

    widths = [col_width(h, [r[i] for r in rows_plain]) for i, h in enumerate(headers)]

    print_separator(widths, 'top')
    print_row([C.BOLD + h + C.RESET for h in headers], widths, aligns)
    print_separator(widths, 'mid')

    for p, plain_row in zip(participants, rows_plain):
        rank_color = RANK_COLORS.get(p['rank'], '')
        avg_color  = C.GOLD if p['rank'] == 1 else (C.RED if p['rank'] == len(participants) else '')
        cells = [
            colorize(plain_row[0], rank_color + C.BOLD) if rank_color else plain_row[0],
            colorize(plain_row[1], rank_color + C.BOLD) if rank_color else plain_row[1],
            plain_row[2],
            plain_row[3],
            colorize(plain_row[4], avg_color + C.BOLD) if avg_color else plain_row[4],
            colorize(plain_row[5], C.BOLD + C.GREEN) if p['max'] == global_max_score else plain_row[5],
            colorize(plain_row[6], C.BOLD + C.RED)   if p['min'] == global_min_score else plain_row[6],
        ]
        print_row(cells, widths, aligns)

    print_separator(widths, 'bot')


def print_ranking(participants: list[dict]) -> None:
    print()
    print(C.BOLD + C.CYAN + '  ═══ ランキング TOP 3 ═══' + C.RESET)
    print()
    medals = ['🥇', '🥈', '🥉']
    for i, p in enumerate(participants[:3]):
        color = list(RANK_COLORS.values())[i]
        bar = '█' * int(p['avg'] / 5)
        print(f"  {medals[i]}  {colorize(p['name'], color + C.BOLD):<12}"
              f"  平均 {colorize(str(p['avg']), color + C.BOLD):>5}点  "
              f"{colorize(bar, color)}")
    print()
    print(C.DIM + '  ▼ 最下位' + C.RESET)
    last = participants[-1]
    bar = '█' * int(last['avg'] / 5)
    print(f"  {last['rank']:>2}位  {colorize(last['name'], C.RED):<12}"
          f"  平均 {colorize(str(last['avg']), C.RED):>5}点  "
          f"{colorize(bar, C.DIM)}")


def print_summary_stats(participants: list[dict]) -> None:
    avgs = [p['avg'] for p in participants]
    print()
    print(C.BOLD + C.CYAN + '  ═══ 全体サマリー ═══' + C.RESET)
    print()
    stats = [
        ('参加者数',       f"{len(participants)} 名"),
        ('全体平均',       f"{round(mean(avgs), 1)} 点"),
        ('標準偏差',       f"{round(stdev(avgs), 2)}"),
        ('最高得点者',     f"{participants[0]['name']}  ({participants[0]['avg']} 点)"),
        ('最低得点者',     f"{participants[-1]['name']}  ({participants[-1]['avg']} 点)"),
        ('80点以上(人数)', f"{sum(1 for p in participants if p['avg'] >= 80)} 名"),
        ('60点未満(人数)', f"{sum(1 for p in participants if p['avg'] < 60)} 名"),
    ]
    for label, value in stats:
        print(f"  {C.DIM}{label:<16}{C.RESET}  {C.BOLD}{value}{C.RESET}")
    print()


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'scores.csv'

    try:
        result = load_csv(filepath)
    except FileNotFoundError:
        print(f"エラー: '{filepath}' が見つかりません。")
        sys.exit(1)
    except (KeyError, ValueError) as e:
        print(f"CSVの読み込みエラー: {e}")
        sys.exit(1)

    if result[0] == 'long':
        _, records, participants = result
        ranked = assign_ranks(participants)
        all_scores = [r['score'] for r in records]
        print_long_detail_table(records, max(all_scores), min(all_scores))
        print_long_summary_table(ranked)
        print_ranking(ranked)
        print_summary_stats(ranked)
    else:
        _, participants, score_cols = result
        ranked = assign_ranks(participants)
        print_table(ranked, score_cols)
        print_ranking(ranked)
        print_summary_stats(ranked)


if __name__ == '__main__':
    main()
