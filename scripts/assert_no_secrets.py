#!/usr/bin/env python3
"""公開される静的HTMLにAPIキーが含まれていないことを、デプロイ前に強制する（2026-07-17）。

なぜ要るか:
  GitHub Pages は静的配信＝HTMLに書いた値は view-source で誰でも読める。
  旧 deploy.yml は "Inject API Keys" で実キーを index.html へ焼き込んでおり、
  Gemini の実キーが公開・かつ有効なまま放置されていた（実測で確認）。
  コメントで「鍵を置くな」と書いても、次に触る者がプレースホルダーを足せば再発する。
  ＝人間の記憶でなく、デプロイを落とすことで止める。

このガードが見るのは「公開される実ファイル」であって、設計意図ではない。
rc=1 でデプロイを止める。
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 実キーの形（プレースホルダー `__..._API_KEY__` は実害が無いので対象外＝誤検知で
# デプロイを止めない。ただし注入ステップを復活させれば実キーになり、ここで捕まる）。
PATTERNS = [
    ("Google APIキー", re.compile(r"AIzaSy[A-Za-z0-9_\-]{20,}")),
    ("OpenAI APIキー", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("Anthropic APIキー", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("GitHub PAT", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("Cloudflare APIトークン", re.compile(r"cfut_[A-Za-z0-9]{30,}")),
    ("Slack トークン", re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}")),
]


def main():
    targets = sorted(ROOT.glob("*.html"))
    if not targets:
        print("🔴 検査対象のHTMLが0件＝ガードが空振りしている（緑を出さない）")
        return 1

    hits = []
    for path in targets:
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pat in PATTERNS:
            for m in pat.finditer(text):
                line = text[: m.start()].count("\n") + 1
                masked = m.group(0)[:8] + "…<REDACTED>"
                hits.append(f"  {path.name}:{line}  {label}  {masked}")

    print(f"検査: {len(targets)}ファイル（{', '.join(p.name for p in targets)}）")
    if hits:
        print("🔴 公開HTMLにAPIキーが含まれています。デプロイを中止します:")
        print("\n".join(hits))
        print("\n  → 鍵はブラウザへ配らず、Cloudflare Worker 等のサーバー側へ置くこと。")
        print("     deploy.yml へ鍵注入ステップを復活させない（それが露出源だった）。")
        return 1

    print("🟢 公開HTMLにAPIキーなし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
