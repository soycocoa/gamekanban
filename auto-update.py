#!/usr/bin/env python3
"""
看板全自动更新 - 爬取数据 + 生成看板 + 推送到 GitHub
"""

import subprocess
import sys
from pathlib import Path

def run(cmd, cwd=None):
    """运行命令"""
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0

def main():
    kanban_dir = Path(__file__).parent
    
    print("🎮 看板全自动更新开始...")
    print("-" * 50)
    
    # 1. 爬取游戏数据
    print("\n📡 步骤 1: 爬取游戏数据...")
    if not run("python3 crawl-games.py", cwd=kanban_dir):
        print("⚠️ 爬虫部分失败，继续...")
    
    # 2. 生成看板
    print("\n🎨 步骤 2: 生成看板...")
    if not run("python3 update-board.py", cwd=kanban_dir):
        print("❌ 生成看板失败!")
        return
    
    # 3. 推送到 GitHub
    print("\n🚀 步骤 3: 推送到 GitHub...")
    
    # 获取环境变量中的 token
    import os
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("❌ GH_TOKEN 未设置!")
        return
    
    files_to_upload = ["games.json", "dashboard.html", "game-board.md"]
    
    for filename in files_to_upload:
        print(f"\n  上传 {filename}...")
        
        # 获取当前文件 SHA
        import urllib.request
        import urllib.error
        import json
        import base64
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # 获取 SHA
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
        
        # 上传内容
        file_path = kanban_dir / filename
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        
        payload = {
            "message": f"Auto update: {filename}",
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
        except urllib.error.HTTPError as e:
            print(f"  ❌ 上传失败: {e}")
    
    print("\n" + "-" * 50)
    print("✅ 全自动更新完成!")
    print("🌐 访问: https://soycocoa.github.io/gamekanban/")

if __name__ == "__main__":
    main()
