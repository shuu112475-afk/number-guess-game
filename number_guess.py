import random

MAX_ATTEMPTS = 7

SPECIAL_HINTS = {
    3: lambda n: f"ヒント：答えは{'偶数' if n % 2 == 0 else '奇数'}です",
    5: lambda n: f"ヒント：答えは50より{'大きい' if n > 50 else '小さいか等しい'}です",
    7: lambda n: f"ヒント：答えは{_nearest_multiple(n)}に近いです",
}

def _nearest_multiple(n):
    lower = (n // 10) * 10
    upper = lower + 10
    nearest = lower if (n - lower) <= (upper - n) else upper
    return f"{nearest}（10の倍数）"

def show_rules():
    print("=== 数当てゲーム ===")
    print()
    print("【ルール】")
    print(f"  ・1～100の間の数字を{MAX_ATTEMPTS}回以内に当てればクリア")
    print("  ・「もっと大きい」「もっと小さい」のヒントが出ます")
    print("  ・3回・5回・7回間違えると特別ヒントが出ます")
    print()

def get_special_hint(attempts, secret):
    if attempts in SPECIAL_HINTS:
        return SPECIAL_HINTS[attempts](secret)
    return None

def main():
    show_rules()

    secret = random.randint(1, 100)
    attempts = 0

    while True:
        remaining = MAX_ATTEMPTS - attempts
        try:
            guess = int(input(f"数字を入力（残り{remaining}回）: "))

            if guess < 1 or guess > 100:
                print("1～100の間の数字を入力してください")
                continue

            attempts += 1

            if guess == secret:
                print(f"\n★ 正解！ {attempts}回で当たりました！ ★")
                if attempts <= 3:
                    print("素晴らしい！天才的な閃きです！")
                elif attempts <= 5:
                    print("お見事！効率よく絞り込みました！")
                else:
                    print("ギリギリクリア！粘り勝ちです！")
                break

            if guess < secret:
                print("→ もっと大きい")
            else:
                print("→ もっと小さい")

            hint = get_special_hint(attempts, secret)
            if hint:
                print(f"  ★ {hint}")

            if attempts >= MAX_ATTEMPTS:
                print(f"\nゲームオーバー... 正解は {secret} でした")
                break

        except ValueError:
            print("数字を入力してください")
        except KeyboardInterrupt:
            print(f"\n終了します（正解は {secret} でした）")
            break

if __name__ == "__main__":
    main()
