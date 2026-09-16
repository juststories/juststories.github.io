#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「✍️ 发新文章」issue 转成 _posts/ 里的 Jekyll 文章。

由 .github/workflows/publish.yml 调用。

输入（环境变量）：
  ISSUE_TITLE   issue 标题 = 文章标题
  ISSUE_BODY    issue 正文（表单各栏内容）
  ISSUE_NUMBER  issue 编号
  ISSUE_ACTION  opened / edited / closed / reopened / labeled / unlabeled
  ISSUE_STATE   open / closed
  ISSUE_LABEL   本次增删的标签名（仅 labeled / unlabeled 事件有值）
  ISSUE_LABELS  issue 当前全部标签（逗号分隔）
  POST_DATE     今天日期（YYYY-MM-DD，工作流已按北京时间算好）
  POST_DATETIME 现在时刻（YYYY-MM-DD HH:MM:SS +0800，北京时间）
  COMMENTS_FILE 保存了 issue 评论 JSON 的文件路径（可为空）

管理方式（对应 issue 操作）：
  编辑 issue 再提交      → 更新文章（日期栏留空则保留原日期，网址不变）
  打「隐藏」标签         → 文章移出网站（文件挪到 _drafts，内容保留）
  去掉「隐藏」标签       → 恢复显示
  关闭 issue             → 删除文章（重新打开可按原日期恢复）

输出：
  - stdout：POST_STATUS / POST_PATH / POST_URL（key=value，供写入 GITHUB_ENV）
  - /tmp/comment.md：要回复到 issue 里的内容（POST_STATUS=none 时不生成）
  - 直接在仓库工作区创建 / 更新 / 移动 / 删除 _posts、_drafts 下的文章文件
"""

import glob
import json
import os
import re
import sys
from urllib.parse import quote

SITE = "https://juststories.work"
HIDE_LABEL = "隐藏"


def fail(msg):
    """解析出错：生成错误评论，状态置 error（workflow 不显示红叉，评论里说人话）。"""
    with open("/tmp/comment.md", "w", encoding="utf-8") as f:
        f.write("⚠️ 这篇没能发布：%s\n\n请重新编辑这个 issue、改好后提交，会自动重试。\n" % msg)
    print("POST_STATUS=error")
    sys.exit(0)


def section(body, label):
    """取表单某一栏的值：栏目标题之后的文字，到下一个 ### 栏目为止。
       表单里留空的选填项会显示成 _No response_，一律当作没填。"""
    m = re.search(r"^### " + re.escape(label) + r"[ \t]*\n+(.*?)(?=^### |\Z)", body, re.M | re.S)
    v = (m.group(1) if m else "").strip()
    return "" if v == "_No response_" else v


def last_section(body, label):
    """取表单最后一栏（正文）：从这里到结尾，
       正文里自己写的 ### 小标题也不会被切掉。"""
    m = re.search(r"^### " + re.escape(label) + r"[ \t]*\n+(.*)\Z", body, re.M | re.S)
    return (m.group(1) if m else "").strip()


def slugify(text):
    """与 Jekyll 的文章地址规则对齐：字母数字和中文保留，其余折叠成 -。"""
    text = re.sub(r"[^\w]+", "-", text, flags=re.UNICODE)
    return text.strip("-")[:100]


def find_marker(comments_file):
    """在 issue 评论里找发布成功时埋下的标记：
       <!-- post: 文件路径 --> 和 <!-- postdate: 日期时间 -->，各取最后一次。"""
    path = date = None
    if not comments_file or not os.path.exists(comments_file):
        return None, None
    try:
        with open(comments_file, encoding="utf-8") as f:
            for c in json.load(f):
                body = c.get("body", "")
                m = re.search(r"<!--\s*post:\s*(\S+?)\s*-->", body)
                if m:
                    path = m.group(1)
                d = re.search(r"<!--\s*postdate:\s*(.+?)\s*-->", body)
                if d:
                    date = d.group(1).strip()
    except Exception:
        pass
    return path, date


def find_scanned_path(number):
    """兜底：直接扫 _posts 和 _drafts 找 front matter 里 issue_number 对应的文章。
       评论被误删时靠它仍能正确更新 / 撤下，不会产生重复文章。"""
    for p in glob.glob("_posts/*.md") + glob.glob("_drafts/*.md"):
        try:
            t = open(p, encoding="utf-8").read()
        except OSError:
            continue
        if re.search(r"^issue_number:\s*%s\s*$" % re.escape(number), t, re.M):
            return p
    return None


def resolve(path):
    """把标记/扫描到的路径解析成实际存在的文件（可能被挪进 _drafts）。"""
    if path and os.path.exists(path):
        return path
    if path:
        base = os.path.basename(path)
        for d in ("_posts", "_drafts"):
            cand = os.path.join(d, base)
            if os.path.exists(cand):
                return cand
    return None


def write_comment(text):
    with open("/tmp/comment.md", "w", encoding="utf-8") as f:
        f.write(text)


def main():
    title = os.environ.get("ISSUE_TITLE", "").strip()
    body = os.environ.get("ISSUE_BODY", "")
    number = os.environ.get("ISSUE_NUMBER", "0")
    action = os.environ.get("ISSUE_ACTION", "opened")
    state = os.environ.get("ISSUE_STATE", "open")
    today = os.environ.get("POST_DATE", "")
    now = os.environ.get("POST_DATETIME", "").strip() or today

    labels = [s.strip() for s in os.environ.get("ISSUE_LABELS", "").split(",") if s.strip()]
    label_event = os.environ.get("ISSUE_LABEL", "").strip()
    hidden = HIDE_LABEL in labels

    marker_path, marker_date = find_marker(os.environ.get("COMMENTS_FILE", ""))
    old_path = resolve(marker_path) or find_scanned_path(number)

    # ── 打「隐藏」标签：文章移出网站（文件挪到 _drafts，内容保留） ──
    if action == "labeled" and label_event == HIDE_LABEL:
        if old_path:
            os.makedirs("_drafts", exist_ok=True)
            dest = os.path.join("_drafts", os.path.basename(old_path))
            if os.path.abspath(old_path) != os.path.abspath(dest):
                os.rename(old_path, dest)
            print("POST_STATUS=hidden")
            print("POST_PATH=%s" % dest)
            write_comment("🙈 已隐藏，网站上不再显示（内容已保留）。在右侧 Labels 里去掉「隐藏」即可恢复。\n")
        else:
            print("POST_STATUS=none")
        return

    # ── 去掉「隐藏」标签：恢复显示 ──
    if action == "unlabeled" and label_event == HIDE_LABEL:
        if old_path and old_path.startswith("_drafts" + os.sep):
            dest = os.path.join("_posts", os.path.basename(old_path))
            os.rename(old_path, dest)
            print("POST_STATUS=unhidden")
            print("POST_PATH=%s" % dest)
            write_comment("✅ 已恢复显示：%s\n\n（网站约 1–2 分钟后生效。）\n" % title)
        else:
            print("POST_STATUS=none")
        return

    # ── 其他标签增删（如「发文章」）→ 不处理 ──
    if action in ("labeled", "unlabeled"):
        print("POST_STATUS=none")
        return

    # ── 关闭 issue = 删除文章（重新打开可按原日期恢复） ──
    if action == "closed" or state == "closed":
        if old_path:
            os.remove(old_path)
            print("POST_STATUS=removed")
            print("POST_PATH=%s" % old_path)
            write_comment("🗑 已删除这篇文章。如果是误删，重新打开这个 issue 会按原日期恢复。\n")
        else:
            print("POST_STATUS=none")
        return

    # ── 发布 / 更新 ──
    category = section(body, "分类")
    content = last_section(body, "正文")
    if not title or title == "文章标题写在这里":
        fail("标题是空的（顶部标题栏没填）。")
    if not category:
        fail("没有选分类。")
    if not content:
        fail("正文是空的。")

    # 日期 / 时间（两个都是选填）：
    #   日期 + 时间都填 → 精确到分（补写旧日记的完整时刻）
    #   只填日期       → 只定到这一天（和以前行为一致）
    #   只填时间       → 沿用原本该用的日期（新文章=提交那天；编辑/恢复=原日期），只指定时刻
    #   都留空         → 编辑保留原日期；恢复用评论标记里的原日期；全新发布用提交此刻
    date = section(body, "发布日期")
    hm = section(body, "发布时间")
    if hm:
        mt = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", hm)
        if not mt:
            fail("「发布时间」的格式不太对（应像 23:05 这样，24 小时制），改一下再提交。")
        hm = "%02d:%s" % (int(mt.group(1)), mt.group(2))
    if hm and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        date_fm = "%s %s:00 +0800" % (date, hm)
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        date_fm = date
    elif old_path:
        m = re.search(r"^date:[ \t]*(.+)$", open(old_path, encoding="utf-8").read(), re.M)
        date_fm = m.group(1).strip() if m else now
        if hm:
            date_fm = "%s %s:00 +0800" % (date_fm[:10], hm)
    elif marker_date:
        date_fm = marker_date
        if hm:
            date_fm = "%s %s:00 +0800" % (date_fm[:10], hm)
    else:
        date_fm = now
        if hm:
            date_fm = "%s %s:00 +0800" % (date_fm[:10], hm)
    day = date_fm[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        date_fm = day = today

    tags = [t for t in (s.strip() for s in re.split(r"[，,、;；]+", section(body, "标签"))) if t]
    excerpt = section(body, "摘要")

    slug = slugify(title) or ("issue-" + number)
    # 隐藏中的文章更新 → 仍写进 _drafts（不重新出现在网站上）
    target_dir = "_drafts" if hidden else "_posts"
    new_path = os.path.join(target_dir, "%s-%s.md" % (day, slug))

    # 标题或日期改了 → 文件名会变，删掉旧文件（相当于改名）
    if old_path and old_path != new_path and os.path.exists(old_path):
        os.remove(old_path)

    # 撞名保护：不同文章同标题同日期 → 自动加 issue 号后缀，不互相覆盖
    if new_path != old_path and os.path.exists(new_path):
        new_path = os.path.join(target_dir, "%s-%s-%s.md" % (day, slug, number))

    fm = ["---"]
    fm.append("title: %s" % json.dumps(title, ensure_ascii=False))
    fm.append("date: %s" % date_fm)
    fm.append("layout: post")
    fm.append("issue_number: %s" % number)
    fm.append("categories:")
    fm.append("  - %s" % json.dumps(category, ensure_ascii=False))
    if tags:
        fm.append("tags:")
        fm.extend("  - %s" % json.dumps(t, ensure_ascii=False) for t in tags)
    if excerpt:
        fm.append("excerpt: %s" % json.dumps(excerpt, ensure_ascii=False))
    fm.append("---")
    fm.append("")

    with open(new_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fm) + content + "\n")

    # 线上地址（Jekyll 默认：/分类/年/月/日/标题.html）
    y, m, d = day.split("-")
    url = "%s/%s/%s/%s/%s/%s.html" % (SITE, quote(category), y, m, d, quote(slug))

    if action == "edited":
        status = "updated"
        verb = "✏️ 文章已更新："
    elif action == "reopened":
        status = "published"
        verb = "♻️ 已按原日期重新发布："
    else:
        status = "published"
        verb = "✅ 发布成功："
    if hidden:
        tail = "（当前处于隐藏状态，在右侧 Labels 里去掉「隐藏」即可恢复显示。）"
    else:
        tail = "（网站约 1–2 分钟后生效，刷新即可看到。）"
    write_comment("%s[%s](%s)\n\n%s\n\n以后修改这篇文章：直接编辑本 issue 再提交。隐藏：右侧 Labels 加「隐藏」。删除：关闭本 issue。\n\n<!-- post: %s -->\n<!-- postdate: %s -->\n"
                  % (verb, title, url, tail, new_path, date_fm))
    print("POST_STATUS=%s" % status)
    print("POST_PATH=%s" % new_path)
    print("POST_URL=%s" % url)


main()

