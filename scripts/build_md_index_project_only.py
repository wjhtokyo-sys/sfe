from pathlib import Path
from datetime import datetime

root = Path(r"C:/sfe-system")
exclude_prefix = (".venv/", "venv/", ".git/", ".pytest_cache/", "frontend/node_modules/")

all_md = sorted(root.rglob("*.md"))
files = []
for p in all_md:
    rel = p.relative_to(root).as_posix()
    if rel.startswith(exclude_prefix):
        continue
    files.append(p)

out = []
out.append("# SFE 项目 Markdown 内容清单（项目文件）")
out.append("")
out.append(f"统计时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Asia/Tokyo)")
out.append(f"总计：{len(files)} 个 MD 文件（已排除 .venv / venv / node_modules / .git / .pytest_cache）")
out.append("")

for p in files:
    rel = p.relative_to(root).as_posix()
    txt = p.read_text(encoding="utf-8", errors="ignore")
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]

    title = ""
    for ln in lines:
        if ln.startswith("#"):
            title = ln.lstrip("#").strip()
            break
    if not title and lines:
        title = lines[0][:80]

    preview = ""
    if lines:
        cand = [ln for ln in lines if not ln.startswith("#")][:2]
        preview = " | ".join(cand)[:180]

    out.append(f"- `{rel}`")
    out.append(f"  - 标题/首行：{title or '(空)'}")
    out.append(f"  - 内容摘要：{preview or '(无可提取摘要)'}")

(target := root / "docs" / "MD_CONTENT_INDEX_PROJECT_ONLY.md").write_text("\n".join(out), encoding="utf-8")
print(target)
