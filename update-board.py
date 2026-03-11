#!/usr/bin/env python3
"""
游戏动态看板生成器
从 games.json 生成 Markdown 和 HTML 看板
"""

import json
from datetime import datetime
from pathlib import Path

CATEGORY_ICONS = {
    "tactical-shooter": "🎯",
    "br": "🪂",
    "extraction": "💼",
    "hero-shooter": "🦸"
}

CATEGORY_NAMES = {
    "tactical-shooter": "战术射击",
    "br": "大逃杀",
    "extraction": "搜打撤",
    "hero-shooter": "英雄射击"
}

def load_games():
    with open(Path(__file__).parent / "games.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_markdown(data):
    """生成 Markdown 看板"""
    games = data["games"]
    last_update = data["lastUpdate"][:10]
    
    md = f"""# 🎮 游戏动态看板

> 最后更新：{last_update}

## 监控列表

| 游戏 | 类型 | 状态 | 最后检查 | 当前版本/赛季 |
|------|------|------|----------|---------------|
"""
    for g in games:
        icon = CATEGORY_ICONS.get(g["category"], "🎮")
        status = "🟢 正常" if g["status"] == "active" else "⚪ 暂停"
        check = g.get("lastCheck") or "-"
        season = g.get("currentSeason", {})
        season_info = f"**{season.get('name', 'N/A')}**" if season else "待检测"
        md += f"| {icon} {g['name']} | {CATEGORY_NAMES.get(g['category'], g['category'])} | {status} | {check} | {season_info} |\n"
    
    md += "\n---\n\n## 最近动态\n\n"
    
    # 有数据的放在前面
    for g in games:
        season = g.get("currentSeason")
        if not season:
            continue
        
        md += f"### {g['name']}\n"
        md += f"- **{season.get('name')}** ({season.get('startDate', 'Unknown')})\n"
        for h in season.get("highlights", []):
            md += f"- {h}\n"
        md += f"\n[查看官网更新 →]({g['source']})\n\n"
    
    md += "\n---\n\n## 待办 / 待检测\n\n"
    
    for g in games:
        if not g.get("currentSeason"):
            md += f"- [ ] **{g['name']}** - 需要检测最新版本\n"
    
    md += """
---

## 使用说明

1. 运行 `python3 update-board.py` 更新看板
2. 看 `game-board.md` - Markdown 版
3. 看 `dashboard.html` - 网页版（浏览器打开）
"""
    
    return md

def generate_html(data):
    """生成 HTML 看板"""
    games = data["games"]
    last_update = data["lastUpdate"][:10]
    
    active_games = [g for g in games if g.get("currentSeason")]
    pending_games = [g for g in games if not g.get("currentSeason")]
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 游戏动态看板</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .update-time {{ color: #888; font-size: 0.9em; }}
        
        .board {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }}
        .card-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }}
        .card-icon {{ font-size: 2em; }}
        .card-title {{ font-size: 1.3em; font-weight: 600; }}
        .card-subtitle {{ color: #888; font-size: 0.85em; margin-top: 4px; }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75em;
            margin-bottom: 12px;
        }}
        .badge-active {{ background: #22c55e; color: #000; }}
        .badge-pending {{ background: #f59e0b; color: #000; }}
        
        .highlights {{
            list-style: none;
            margin-top: 16px;
        }}
        .highlights li {{
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            color: #ccc;
        }}
        .highlights li:last-child {{ border-bottom: none; }}
        
        .card-footer {{
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        .card-footer a {{
            color: #60a5fa;
            text-decoration: none;
            font-size: 0.9em;
        }}
        .card-footer a:hover {{ text-decoration: underline; }}
        
        .pending-section {{
            background: rgba(245, 158, 11, 0.1);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}
        .pending-section h2 {{
            color: #f59e0b;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .pending-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
        }}
        .pending-item {{
            background: rgba(0,0,0,0.2);
            padding: 12px 16px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        footer {{
            text-align: center;
            padding: 40px 0;
            color: #666;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎮 游戏动态看板</h1>
            <p class="update-time">最后更新: {last_update} | 监控 {len(games)} 款游戏</p>
        </header>
        
        <div class="board">
"""
    
    # 活跃的卡片
    for g in active_games:
        icon = CATEGORY_ICONS.get(g["category"], "🎮")
        season = g.get("currentSeason", {})
        season_name = season.get("name", "Unknown")
        highlights = season.get("highlights", [])
        
        highlights_html = "".join([f"<li>{h}</li>" for h in highlights[:3]])
        
        html += f"""
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">{icon}</span>
                    <div>
                        <div class="card-title">{g['name']}</div>
                        <div class="card-subtitle">{CATEGORY_NAMES.get(g['category'], g['category'])}</div>
                    </div>
                </div>
                <span class="badge badge-active">🟢 已更新</span>
                <div style="font-size:1.1em;margin:8px 0;">{season_name}</div>
                <ul class="highlights">
                    {highlights_html}
                </ul>
                <div class="card-footer">
                    <a href="{g['source']}" target="_blank">查看官网更新 →</a>
                </div>
            </div>
"""
    
    html += """        </div>
        
        <div class="pending-section">
            <h2>⏳ 待检测</h2>
            <div class="pending-list">
"""
    
    # 待检测的游戏
    for g in pending_games:
        icon = CATEGORY_ICONS.get(g["category"], "🎮")
        html += f"""                <div class="pending-item">
                    <span>{icon}</span>
                    <span>{g['name']}</span>
                </div>
"""
    
    html += """            </div>
        </div>
        
        <footer>
            <p>射击游戏关卡策划专用看板 | 自动生成于 {last_update}</p>
        </footer>
    </div>
</body>
</html>
"""
    
    return html

def main():
    data = load_games()
    
    # 生成 Markdown
    md = generate_markdown(data)
    with open(Path(__file__).parent / "game-board.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("✓ game-board.md 已更新")
    
    # 生成 HTML
    html = generate_html(data)
    with open(Path(__file__).parent / "dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✓ dashboard.html 已更新")

if __name__ == "__main__":
    main()
