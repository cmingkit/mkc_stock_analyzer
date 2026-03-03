#!/usr/bin/env python3
"""
驗證 HTML 報告模板修復的腳本
"""

import os
import sys
from pathlib import Path

def verify_fix():
    """驗證修復是否成功"""
    project_root = Path(__file__).parent
    
    print("=" * 60)
    print("驗證 HTML 報告模板修復")
    print("=" * 60)
    
    # 1. 檢查模板文件
    template_path = project_root / 'templates' / 'report.html'
    print(f"\n1. 檢查模板文件: {template_path}")
    
    if not template_path.exists():
        print("   ❌ 模板文件不存在")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # 檢查是否包含動態路徑
    if '{{ css_path | default(' in template_content:
        print("   ✅ 模板使用動態 CSS 路徑")
    else:
        print("   ❌ 模板未使用動態 CSS 路徑")
        return False
    
    # 檢查 Chart.js 引用
    if 'chart.js@4.4.0/dist/chart.umd.min.js' in template_content:
        print("   ✅ Chart.js 引用正確")
    else:
        print("   ❌ Chart.js 引用缺失或版本錯誤")
        return False
    
    # 2. 檢查 CSS 文件
    css_path = project_root / 'static' / 'css' / 'report.css'
    print(f"\n2. 檢查 CSS 文件: {css_path}")
    
    if css_path.exists():
        file_size = css_path.stat().st_size
        print(f"   ✅ CSS 文件存在 ({file_size} bytes)")
    else:
        print("   ❌ CSS 文件不存在")
        return False
    
    # 3. 檢查最新報告
    reports_dir = project_root / 'reports' / 'html'
    print(f"\n3. 檢查報告目錄: {reports_dir}")
    
    if not reports_dir.exists():
        print("   ⚠️  報告目錄不存在")
        return True  # 這不是錯誤，只是還沒生成報告
    
    # 獲取最新的報告
    reports = sorted(reports_dir.glob('report_*.html'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not reports:
        print("   ⚠️  沒有找到報告文件")
        return True
    
    latest_report = reports[0]
    print(f"   📄 最新報告: {latest_report.name}")
    
    # 檢查報告中的路徑
    with open(latest_report, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    # 檢查 CSS 路徑
    if '../../static/css/report.css' in report_content:
        print("   ✅ 報告使用正確的 CSS 路徑")
    elif '../static/css/report.css' in report_content:
        print("   ⚠️  報告使用舊的 CSS 路徑（這可能是舊報告）")
    else:
        print("   ❌ 報告中找不到 CSS 路徑")
        return False
    
    # 檢查 Chart.js
    if 'chart.js@4.4.0/dist/chart.umd.min.js' in report_content:
        print("   ✅ 報告包含 Chart.js 引用")
    else:
        print("   ❌ 報告缺少 Chart.js 引用")
        return False
    
    # 4. 驗證相對路徑
    print(f"\n4. 驗證相對路徑")
    os.chdir(reports_dir)
    
    css_relative_path = '../../static/css/report.css'
    if os.path.exists(css_relative_path):
        abs_path = os.path.abspath(css_relative_path)
        print(f"   ✅ CSS 路徑正確: {abs_path}")
    else:
        print(f"   ❌ CSS 路徑錯誤")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 所有檢查通過！修復成功！")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = verify_fix()
    sys.exit(0 if success else 1)
