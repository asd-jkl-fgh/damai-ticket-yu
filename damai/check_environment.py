#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
环境检查脚本（跨平台：Windows / macOS / Linux）
在运行抢票脚本前，使用此脚本检查环境是否配置正确
"""

import os
import platform
import re
import shutil
import subprocess
import sys


IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"


# Windows 控制台默认 GBK，强制 UTF-8 以显示 ✓/✗ 等符号
if IS_WINDOWS:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _get_version_from_output(output):
    """从命令输出中提取主版本号"""
    match = re.search(r'(\d+)\.', output)
    return match.group(1) if match else None


def _run_command_get_version(command):
    """运行命令并获取版本信息"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _candidate_chrome_paths():
    """返回当前平台上 Chrome 可能的安装位置"""
    if IS_WINDOWS:
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    elif IS_MAC:
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        ]
    else:  # Linux
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]

    # 再补上 PATH 中的 chrome
    path_hit = shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chromium")
    if path_hit:
        candidates.append(path_hit)
    return [p for p in candidates if p]


def _candidate_chromedriver_paths():
    """返回当前平台上 ChromeDriver 可能的位置"""
    if IS_WINDOWS:
        candidates = [
            r"C:\chromedriver\chromedriver.exe",
            r"C:\Program Files\chromedriver\chromedriver.exe",
            os.path.join(os.getcwd(), "chromedriver.exe"),
        ]
    elif IS_MAC:
        candidates = [
            "/opt/homebrew/bin/chromedriver",
            "/usr/local/bin/chromedriver",
        ]
    else:  # Linux
        candidates = [
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
            "/snap/bin/chromedriver",
        ]

    path_hit = shutil.which("chromedriver") or shutil.which("chromedriver.exe")
    if path_hit:
        candidates.append(path_hit)
    return [p for p in candidates if p]


def _find_chrome():
    """找到第一个存在的 Chrome 路径"""
    for p in _candidate_chrome_paths():
        if os.path.exists(p):
            return p
    return None


def _find_chromedriver():
    """找到第一个存在的 ChromeDriver 路径"""
    for p in _candidate_chromedriver_paths():
        if os.path.exists(p) or os.path.islink(p):
            return p
    return None


def _get_chrome_version(chrome_path):
    """获取 Chrome 主版本号（跨平台）"""
    if IS_WINDOWS:
        # Windows 上 chrome.exe --version 通常无输出，使用 PowerShell 读取文件版本
        try:
            ps_cmd = [
                "powershell", "-NoProfile", "-Command",
                f"(Get-Item '{chrome_path}').VersionInfo.ProductVersion"
            ]
            result = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return _get_version_from_output(result.stdout.strip()), result.stdout.strip()
        except Exception:
            pass
        # 备用：注册表
        try:
            reg_cmd = [
                "reg", "query",
                r"HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon",
                "/v", "version"
            ]
            result = subprocess.run(reg_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                match = re.search(r'REG_SZ\s+([\d.]+)', result.stdout)
                if match:
                    return _get_version_from_output(match.group(1)), match.group(1)
        except Exception:
            pass
        return None, None

    version_str = _run_command_get_version([chrome_path, "--version"])
    if version_str:
        return _get_version_from_output(version_str), version_str
    return None, None


def check_python_version():
    """检查 Python 版本"""
    print("Python 版本检查...")
    version = sys.version_info
    print(f"  当前版本: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("  ✗ 需要 Python 3.7 或更高版本")
        return False
    print("  ✓ Python 版本符合要求\n")
    return True


def check_dependencies():
    """检查依赖包"""
    print("依赖包检查...")
    dependencies = {
        'selenium': 'Selenium WebDriver',
        'chromedriver_autoinstaller': 'ChromeDriver Auto Installer',
    }

    missing = []
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"  ✓ {description} ({package})")
        except ImportError:
            print(f"  ✗ {description} ({package}) 未安装")
            missing.append(package.replace('_', '-'))

    if missing:
        print(f"\n  安装命令: pip install {' '.join(missing)}\n")
        return False
    print()
    return True


def check_chrome():
    """检查 Chrome 浏览器"""
    print("Chrome 浏览器检查...")
    chrome_path = _find_chrome()
    if not chrome_path:
        print("  ✗ 未找到 Chrome 浏览器")
        print("  请安装 Chrome: https://www.google.com/chrome/")
        print()
        return False

    chrome_version, version_str = _get_chrome_version(chrome_path)
    if chrome_version:
        print(f"  ✓ Chrome 路径: {chrome_path}")
        print(f"  ✓ 版本: {version_str}")
        print(f"  ✓ 主版本号: {chrome_version}")
        print()
        return True

    print(f"  ✓ Chrome 路径: {chrome_path}")
    print("  ⚠ 无法获取版本号")
    print()
    return False


def check_chromedriver():
    """检查 ChromeDriver"""
    print("ChromeDriver 检查...")
    driver_path = _find_chromedriver()
    if not driver_path:
        print("  ⚠ 未找到 ChromeDriver")
        print("  脚本会在首次运行时自动安装 chromedriver-autoinstaller")
        print()
        return False

    version_str = _run_command_get_version([driver_path, "--version"])
    if version_str:
        driver_version = _get_version_from_output(version_str)
        print(f"  ✓ ChromeDriver: {version_str}")
        print(f"  ✓ 主版本号: {driver_version}")
        print(f"  ✓ 路径: {driver_path}")
        print()
        return True

    print(f"  ✓ 路径: {driver_path}")
    print("  ⚠ 无法获取版本号")
    print()
    return False


def check_version_match():
    """检查 Chrome 和 ChromeDriver 版本是否匹配"""
    print("版本匹配检查...")

    chrome_path = _find_chrome()
    driver_path = _find_chromedriver()

    if not chrome_path or not driver_path:
        print("  ⚠ Chrome 或 ChromeDriver 未找到，跳过匹配检查")
        print()
        return False

    chrome_version, _ = _get_chrome_version(chrome_path)

    driver_version_str = _run_command_get_version([driver_path, "--version"])
    driver_version = _get_version_from_output(driver_version_str) if driver_version_str else None

    if not chrome_version or not driver_version:
        print("  ⚠ 无法获取版本信息")
        print()
        return False

    print(f"  Chrome 版本: {chrome_version}")
    print(f"  ChromeDriver 版本: {driver_version}")

    if chrome_version == driver_version:
        print("  ✓ 版本匹配")
        print()
        return True

    print(f"  ✗ 版本不匹配！(差距: {abs(int(chrome_version) - int(driver_version))} 个主版本)")
    print("\n  解决方案:")
    print("  方案1: 更新 Chrome 浏览器到最新版本（推荐）")
    print("  方案2: 删除旧 ChromeDriver，让脚本自动重新安装")
    print("         pip install chromedriver-autoinstaller")
    print()
    return False


def get_chromedriver_path():
    """
    获取 ChromeDriver 路径，如果不存在或版本不匹配则自动安装
    供其他脚本导入使用
    :return: ChromeDriver 可执行文件路径
    """
    chrome_path = _find_chrome()
    if not chrome_path:
        raise RuntimeError("未找到 Chrome 浏览器，请先安装 Chrome")

    chrome_version, _ = _get_chrome_version(chrome_path)
    if not chrome_version:
        raise RuntimeError("无法获取 Chrome 版本")

    # 检查已安装的 ChromeDriver 是否匹配
    driver_path = _find_chromedriver()
    if driver_path:
        driver_version_str = _run_command_get_version([driver_path, "--version"])
        if driver_version_str:
            driver_version = _get_version_from_output(driver_version_str)
            if driver_version == chrome_version:
                return driver_path

    # 版本不匹配或不存在，使用自动安装器
    print(f"  Chrome 版本: {chrome_version}")
    print("  正在自动安装匹配的 ChromeDriver...")
    try:
        import chromedriver_autoinstaller
        chromedriver_path = chromedriver_autoinstaller.install()

        result = _run_command_get_version([chromedriver_path, "--version"])
        if not result:
            raise RuntimeError("ChromeDriver 无法执行")

        print(f"  ✓ ChromeDriver 安装成功: {result}")
        return chromedriver_path
    except ImportError:
        raise RuntimeError(
            "未安装 chromedriver-autoinstaller，请运行: pip install chromedriver-autoinstaller"
        )
    except Exception as e:
        raise RuntimeError(f"ChromeDriver 安装失败: {e}")


def check_config_file():
    """检查配置文件"""
    print("配置文件检查...")
    config_file = 'config.json'

    if not os.path.exists(config_file):
        print(f"  ✗ 未找到配置文件: {config_file}")
        print(f"  请先创建配置文件")
        print()
        return False

    try:
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"  ✓ 配置文件存在: {config_file}")

        required_fields = ['index_url', 'login_url', 'target_url', 'users']
        missing_fields = [field for field in required_fields if field not in config]

        if missing_fields:
            print(f"  ✗ 缺少必需字段: {', '.join(missing_fields)}")
            print()
            return False

        print(f"  ✓ 必需字段完整")
        print(f"  ✓ 观众人数: {len(config['users'])} 人")
        print()
        return True
    except Exception as e:
        print(f"  ✗ 配置文件错误: {e}")
        print()
        return False


def main():
    print("\n" + "=" * 60)
    print(f"大麦抢票脚本 - 环境检查工具 ({platform.system()})")
    print("=" * 60)
    print()

    checks = [
        ("Python 版本", check_python_version),
        ("依赖包", check_dependencies),
        ("Chrome 浏览器", check_chrome),
        ("ChromeDriver", check_chromedriver),
        ("版本匹配", check_version_match),
        ("配置文件", check_config_file),
    ]

    results = []
    for name, check_func in checks:
        try:
            results.append((name, check_func()))
        except Exception as e:
            print(f"  ✗ 检查出错: {e}\n")
            results.append((name, False))

    print("=" * 60)
    print("检查结果汇总")
    print("=" * 60)

    all_passed = all(result for _, result in results)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")

    print("=" * 60)

    if all_passed:
        print("\n✓ 所有检查通过！可以运行抢票脚本了。")
        print("  运行命令: python damai.py\n")
        return 0
    print("\n✗ 部分检查未通过，请根据上述提示修复问题。\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
