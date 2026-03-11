#!/usr/bin/env python3
"""
看板全自动更新 - 爬取数据 + 生成看板 + 推送到 GitHub + 提醒用户
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

def run(cmd, cwd=None):
    """运行命令"""
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0

def send_notification(message):
    """发送 QQ 消息提醒用户"""
    import urllib.request
    import urllib.error
    
    # 使用 OpenClaw 内部 API 发送消息
    # 通过写入一个标记文件，让主进程检测并发送消息
    notify_file = Path(__file__).parent / ".notify"
    with open(notify_file, "w", encoding="utf-8") as f:
        f.write(message)
    
    print(f"\n📱 已设置提醒: {message[:50]}...")

def main():
    kanban_dir = Path(__file__).parent
    
    print("=" * 50)
    print("🎮 游戏动态看板自动更新")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 1. 爬取游戏数据
    print("\n📡 步骤 1: 爬取游戏数据...")
    crawl_result = run("python3 crawl-games.py", cwd=kanban_dir)
    
    # 统计更新了哪些游戏
    games_file = kanban_dir / "games.json"
    with open(games_file, "r", encoding="utf-8") as f:
        games_data = json.load(f)
    
    updated_games = [g["name"] for g in games_data["games"] if g.get("currentSeason")]
    
    # 2. 生成看板
    print("\n🎨 步骤 2: 生成看板...")
    if not run("python3 update-board.py", cwd=kanban_dir):
        print("❌ 生成看板失败!")
        send_notification("❌ 游戏看板更新失败，请检查日志")
        return
    
    # 3. 推送到 GitHub
    print("\n🚀 步骤 3: 推送到 GitHub...")
    
    import os
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("❌ GH_TOKEN 未设置!")
        send_notification("❌ GitHub Token 未设置")
        return
    
    import urllib.request
    import urllib.error
    import base64
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    files_to_upload = ["games.json", "dashboard.html", "game-board.md"]
    upload_success = 0
    
    for filename in files_to_upload:
        print(f"\n  上传 {filename}...")
        
        sha_url = f"https://api.github.com/repos/soycocoa/gamekanban/contents/{filename}"
        req = urllib.request.Request(sha_url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                sha = data.get("sha")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                sha = None
            else:
                print(f"  ❌ 获取 SHA 失败: {e}")
                continue
        
        file_path = kanban_dir / filename
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        
        payload = {
            "message": f"Auto update {datetime.now().strftime('%Y-%m-%d %H:%M')}: {filename}",
            "content": content
        }
        if sha:
            payload["sha"] = sha
        
        req = urllib.request.Request(
            sha_url,
            data=json.dumps(payload).encode(),
            headers=headers,
            method="PUT"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                print(f"  ✅ 上传成功")
                upload_success += 1
        except urllib.error.HTTPError as e:
            print(f"  ❌ 上传失败: {e}")
    
    # 4. 发送提醒
    print("\n" + "=" * 50)
    print("✅ 全自动更新完成!")
    print("=" * 50)
    
    # 构建提醒消息
    if upload_success == len(files_to_upload):
        notification = f"""🎮 游戏动态看板已更新！

📊 已更新 {len(updated_games)} 款游戏:
{chr(10).join(['• ' + g for g in updated_games[:5]])}
{'...' if len(updated_games) > 5 else ''}

🌐 查看看板:
https://soycocoa.github.io/gamekanban/
"""
    else:
        notification = f"""⚠️ 游戏看板更新部分失败

✅ 成功上传: {upload_success}/{len(files_to_upload)} 个文件
📊 已获取: {len(updated_games)} 款游戏数据

🌐 查看看板:
https://soycocoa.github.io/gamekanban/
"""
    
    send_notification(notification)

if __name__ == "__main__":
    main()
