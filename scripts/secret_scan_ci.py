#!/usr/bin/env python3
"""公開リポの鍵検査（CI 用・単体で動く）。作業ツリーと履歴全体の両方を見る。

なぜ CI に置くか（2026-11-23 の流出の経路を塞ぐ）:
  - ローカルの pre-commit は `--no-verify` や bot のコミットで素通りする。
  - 作業ツリーだけの検査は、消したファイルの鍵が履歴に残るのを見逃す。
  → push のたびに GitHub 側で、ツリーと履歴の両方を検査し、1つでも候補があれば失敗させる。

値は一切表示しない（候補はファイル名・行番号・種類・先頭4字だけ）。
使い方: python3 scripts/secret_scan_ci.py            # 0=無し／1=候補あり
"""
import re
import subprocess
import sys

# 種類, パターン。鍵名つきの形を優先し、base64 の画像データなど偽陽性が出やすい素の形は避ける。
PATTERNS = [
    ("Lark/Feishu App Secret",
     re.compile(r"(?i)app_secret[\\\"'\s:=]+[A-Za-z0-9_\-]{28,}")),
    ("OpenAI API Key (sk- / sk-proj-)", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("Meta(Facebook) Access Token",
     re.compile(r"(?i)(access[_-]?token|fb[_-]?token|meta[_-]?token)[\\\"'\s:=]+EAA[A-Za-z0-9]{60,}")),
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("Telegram Bot Token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_\-]{35}\b")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}")),
    ("Private Key 本体", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----")),
]


def _mask(s):
    return (s[:4] + "…") if s else ""


def scan_text(text, where):
    """(where, 行番号, 種類, 先頭4字) のリスト。値は返さない。"""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, rx in PATTERNS:
            m = rx.search(line)
            if m:
                hits.append((where, n, kind, _mask(m.group(0))))
    return hits


def scan_tree(repo="."):
    files = subprocess.run(["git", "-C", repo, "ls-files"], capture_output=True, text=True).stdout.split("\n")
    hits = []
    for f in files:
        if not f:
            continue
        try:
            with open(f"{repo}/{f}", encoding="utf-8") as fh:
                hits += scan_text(fh.read(), f"ツリー:{f}")
        except (OSError, UnicodeDecodeError):
            continue
    return hits


def scan_history(repo="."):
    out = subprocess.run(["git", "-C", repo, "log", "--all", "-p", "--no-color", "--format=COMMIT %H"],
                         capture_output=True, text=True).stdout
    hits, commit, file_ = [], "", ""
    for ln in out.splitlines():
        if ln.startswith("COMMIT "):
            commit, file_ = ln.split()[1][:8], ""
            continue
        if ln.startswith("diff --git "):
            m = re.search(r" b/(.+)$", ln)
            file_ = m.group(1) if m else "?"
            continue
        if ln.startswith("+") and not ln.startswith("+++"):
            for h in scan_text(ln[1:], f"履歴:{commit}:{file_}"):
                hits.append((h[0], 0, h[2], h[3]))
    return list(dict.fromkeys(hits))


def main(argv):
    repo = argv[0] if argv else "."
    hits = scan_tree(repo) + scan_history(repo)
    if not hits:
        print("鍵検査（ツリー＋履歴）: 候補 0件")
        return 0
    print(f"鍵検査（ツリー＋履歴）: 候補 {len(hits)}件（値は表示しない）")
    for where, n, kind, head in hits[:50]:
        print(f"  {where}  行{n}  {kind}  先頭={head}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
