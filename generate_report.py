#!/usr/bin/env python3
"""
营销周报生成器
抓取 wewe-rss 订阅内容，生成 HTML 周报并推送到 GitHub Pages
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
import os
import base64

# 配置
WEWE_RSS_BASE = "https://wewe-rss-production-7352.up.railway.app"
WEWE_RSS_TOKEN = os.environ.get("WEWE_RSS_TOKEN", "hyxhs2026")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = "zmillie97-lab/marketing-weekly"

CST = timezone(timedelta(hours=8))

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "marketing-weekly-bot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def fetch_all_articles():
    url = f"{WEWE_RSS_BASE}/feeds/all.json?token={WEWE_RSS_TOKEN}"
    data = fetch_json(url)
    return data.get("items", [])

def filter_this_week(articles):
    now = datetime.now(CST)
    # 上周一到本周一（生成周报时是周一，取上一整周）
    this_monday = now - timedelta(days=now.weekday())
    last_monday = this_monday - timedelta(days=7)
    result = []
    for a in articles:
        raw = a.get("date_modified") or a.get("date_published", "")
        if not raw:
            continue
        try:
            pub = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(CST)
        except Exception:
            continue
        if last_monday <= pub < this_monday:
            result.append({**a, "_pub": pub})
    return result

def group_by_author(articles):
    groups = {}
    for a in articles:
        name = a.get("author", {}).get("name", "未知")
        groups.setdefault(name, []).append(a)
    return groups

def render_html(groups, week_label):
    sources = {
        "小红书商业动态": {"color": "#FF2442", "icon": "📕", "desc": "小红书商业化最新动态"},
        "巨量引擎营销观察": {"color": "#1C1F4A", "icon": "🎯", "desc": "抖音巨量引擎营销洞察"},
    }

    cards_html = ""
    total = 0
    for author, articles in sorted(groups.items(), key=lambda x: -len(x[1])):
        meta = sources.get(author, {"color": "#666", "icon": "📰", "desc": author})
        total += len(articles)
        items_html = ""
        for a in sorted(articles, key=lambda x: x["_pub"], reverse=True):
            pub_str = a["_pub"].strftime("%m/%d %H:%M")
            img_html = f'<img src="{a["image"]}" onerror="this.style.display=\'none\'" />' if a.get("image") else ""
            items_html += f"""
            <a href="{a['url']}" target="_blank" class="article-card">
              {img_html}
              <div class="article-body">
                <div class="article-title">{a['title']}</div>
                <div class="article-meta">{pub_str}</div>
              </div>
            </a>"""

        cards_html += f"""
        <section class="source-section">
          <div class="source-header" style="border-left: 4px solid {meta['color']}">
            <span class="source-icon">{meta['icon']}</span>
            <div>
              <div class="source-name">{author}</div>
              <div class="source-desc">{meta['desc']} · 本周 {len(articles)} 篇</div>
            </div>
          </div>
          <div class="articles-grid">{items_html}</div>
        </section>"""

    generated_at = datetime.now(CST).strftime("%Y-%m-%d %H:%M")
    empty_tip = "" if total > 0 else '<div class="empty-tip">本周暂无新文章 📭</div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>营销周报 · {week_label}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; background: #f5f5f7; color: #1d1d1f; }}
  .hero {{ background: linear-gradient(135deg, #FF2442 0%, #1C1F4A 100%); color: white; padding: 48px 24px 36px; text-align: center; }}
  .hero h1 {{ font-size: 28px; font-weight: 700; letter-spacing: 1px; }}
  .hero .week {{ font-size: 15px; opacity: 0.8; margin-top: 8px; }}
  .hero .stats {{ display: inline-block; background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 18px; margin-top: 16px; font-size: 14px; }}
  .container {{ max-width: 860px; margin: 32px auto; padding: 0 16px 48px; }}
  .source-section {{ background: white; border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
  .source-header {{ display: flex; align-items: center; gap: 12px; padding-left: 12px; margin-bottom: 20px; }}
  .source-icon {{ font-size: 28px; }}
  .source-name {{ font-size: 17px; font-weight: 600; }}
  .source-desc {{ font-size: 13px; color: #888; margin-top: 2px; }}
  .articles-grid {{ display: flex; flex-direction: column; gap: 12px; }}
  .article-card {{ display: flex; gap: 12px; align-items: flex-start; text-decoration: none; color: inherit; padding: 12px; border-radius: 10px; transition: background 0.15s; }}
  .article-card:hover {{ background: #f5f5f7; }}
  .article-card img {{ width: 80px; height: 60px; object-fit: cover; border-radius: 8px; flex-shrink: 0; }}
  .article-body {{ flex: 1; }}
  .article-title {{ font-size: 14px; font-weight: 500; line-height: 1.5; color: #1d1d1f; }}
  .article-meta {{ font-size: 12px; color: #aaa; margin-top: 4px; }}
  .empty-tip {{ text-align: center; padding: 48px; color: #aaa; font-size: 15px; }}
  .footer {{ text-align: center; font-size: 12px; color: #aaa; padding: 24px; }}
</style>
</head>
<body>
<div class="hero">
  <h1>📊 营销行业周报</h1>
  <div class="week">{week_label}</div>
  <div class="stats">本周共 {total} 篇文章</div>
</div>
<div class="container">
  {empty_tip}
  {cards_html}
</div>
<div class="footer">由 wewe-rss + OpenClaw 自动生成 · {generated_at} CST</div>
</body>
</html>"""

def push_to_github(html_content, filename, commit_message):
    """推送文件到 GitHub 仓库"""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    # 检查文件是否存在（获取 sha）
    sha = None
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            existing = json.loads(r.read().decode())
            sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    content_b64 = base64.b64encode(html_content.encode()).decode()
    payload = {"message": commit_message, "content": content_b64}
    if sha:
        payload["sha"] = sha

    data = json.dumps(payload).encode()
    req = urllib.request.Request(api_url, data=data, headers=headers, method="PUT")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def update_index(weeks_index):
    """更新首页 index.html"""
    rows = ""
    for w in weeks_index[:20]:
        rows += f'<li><a href="{w["file"]}">{w["label"]}</a> <span>({w["count"]} 篇)</span></li>\n'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>营销周报归档</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 600px; margin: 60px auto; padding: 0 20px; }}
  h1 {{ font-size: 24px; margin-bottom: 8px; }}
  p {{ color: #888; margin-bottom: 24px; font-size: 14px; }}
  ul {{ list-style: none; }}
  li {{ padding: 12px 0; border-bottom: 1px solid #eee; }}
  a {{ text-decoration: none; color: #FF2442; font-weight: 500; }}
  span {{ color: #aaa; font-size: 13px; }}
</style>
</head>
<body>
<h1>📊 营销周报归档</h1>
<p>自动聚合 · 小红书商业动态 & 巨量引擎营销观察</p>
<ul>{rows}</ul>
</body>
</html>"""
    return html

def main():
    print("🚀 开始生成营销周报...")
    now = datetime.now(CST)
    this_monday = now - timedelta(days=now.weekday())
    last_monday = this_monday - timedelta(days=7)
    week_label = f"{last_monday.strftime('%Y/%m/%d')} - {(this_monday - timedelta(days=1)).strftime('%m/%d')}"
    filename = f"weekly/{last_monday.strftime('%Y-%m-%d')}.html"

    print("📡 抓取文章...")
    all_articles = fetch_all_articles()
    print(f"   共 {len(all_articles)} 篇")

    week_articles = filter_this_week(all_articles)
    print(f"   本周 {len(week_articles)} 篇")

    groups = group_by_author(week_articles)
    html = render_html(groups, week_label)

    print(f"📤 推送到 GitHub: {filename}")
    push_to_github(html, filename, f"📊 周报 {week_label}")

    # 更新 index
    # 简单起见，直接读取已有列表（实际可从 API 获取目录）
    total = sum(len(v) for v in groups.values())
    index_entry = {"file": filename, "label": week_label, "count": total}

    # 获取已有 weekly 目录
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/weekly"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            files = json.loads(r.read().decode())
            weeks_index = [
                {"file": f["path"], "label": f["name"].replace(".html", ""), "count": 0}
                for f in sorted(files, key=lambda x: x["name"], reverse=True)
                if f["name"].endswith(".html")
            ]
    except Exception:
        weeks_index = [index_entry]

    index_html = update_index(weeks_index)
    print("📤 更新首页 index.html")
    push_to_github(index_html, "index.html", f"🔄 更新归档首页 {week_label}")

    pages_url = f"https://zmillie97-lab.github.io/marketing-weekly/{filename}"
    print(f"✅ 完成！周报地址: {pages_url}")
    return pages_url

if __name__ == "__main__":
    main()
