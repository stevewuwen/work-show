#!/usr/bin/env python3
"""
项目初始化脚本
检查环境、安装依赖、初始化数据库等
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
from typing import Dict, Any
import shutil

# 检查当前是否为 root 用户运行（如果是，则发出警告并退出，因为这会破坏文件权限）
if os.geteuid() == 0:
    print("\n[!] 警告: 请不要使用 sudo 运行此脚本！")
    print("    这会导致虚拟环境和数据库文件的所有者变为 root，导致后续无法运行。")
    print("    安装 Chrome 时，脚本会自动请求 sudo 权限。")
    print(f"    请直接运行: python3 {sys.argv[0]}\n")
    sys.exit(1)


def run_command(
    cmd: list | str,
    check: bool = True,
    shell: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """运行命令并返回结果的通用封装"""
    cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"执行命令: {cmd_str}")

    try:
        # 如果是字符串且shell=True，直接运行；如果是列表，shell通常设为False
        result = subprocess.run(
            cmd, shell=shell, check=check, capture_output=capture_output, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {cmd_str}")
        print(f"错误输出: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def install_chrome_wsl():
    """
    在 WSL2 (Ubuntu/Debian) 上检查并安装 Google Chrome。
    """
    CHROME_EXEC = "google-chrome"
    DOWNLOAD_URL = (
        "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    )
    DEB_FILENAME = "google-chrome-stable_current_amd64.deb"

    print(f"[*] 正在检查 {CHROME_EXEC} 是否存在...")

    if shutil.which(CHROME_EXEC):
        print(f"[√] Chrome 已安装，跳过。")
        return True

    print("[-] 未检测到 Chrome，准备开始安装（需要 sudo 密码）...")

    try:
        # 1. 检查并安装 wget (使用 sudo)
        if not shutil.which("wget"):
            print("[*] 系统缺少 wget，正在安装...")
            run_command(
                ["sudo", "apt-get", "update"],
                check=True,
                shell=False,
                capture_output=False,
            )
            run_command(
                ["sudo", "apt-get", "install", "-y", "wget"],
                check=True,
                shell=False,
                capture_output=False,
            )

        # 2. 下载安装包 (不需要 sudo，下载到当前目录即可)
        print(f"\n[*] 正在下载安装包: {DEB_FILENAME} ...")
        if os.path.exists(DEB_FILENAME):
            os.remove(DEB_FILENAME)
        run_command(["wget", "-O", DEB_FILENAME, DOWNLOAD_URL], check=True, shell=False)

        # 3. 安装 (使用 sudo apt install)
        print("\n[*] 正在安装 Chrome (需要 sudo 权限)...")
        # 这里 capture_output=False 以便用户能看到 sudo 密码提示和安装进度
        run_command(
            ["sudo", "apt-get", "update"],
            check=False,
            shell=False,
            capture_output=False,
        )
        run_command(
            ["sudo", "apt-get", "install", "-y", f"./{DEB_FILENAME}"],
            check=True,
            shell=False,
            capture_output=False,
        )

        # 4. 验证
        version_check = run_command(
            [CHROME_EXEC, "--version"], check=False, shell=False
        )
        if version_check.returncode == 0:
            print(f"[√] 安装成功！版本: {version_check.stdout.strip()}")
        else:
            print("[!] 安装似乎完成了，但无法启动检查版本。")

    except Exception as e:
        print(f"\n[!] Chrome 安装失败: {e}")
        return False
    finally:
        if os.path.exists(DEB_FILENAME):
            os.remove(DEB_FILENAME)

    return True


def check_uv() -> bool:
    """检查uv是否已安装"""
    # 检查 PATH 中是否有 uv，或者用户主目录下是否有 uv
    if shutil.which("uv"):
        return True

    cargo_bin = os.path.expanduser("~/.cargo/bin/uv")
    local_bin = os.path.expanduser("~/.local/bin/uv")
    if os.path.exists(cargo_bin) or os.path.exists(local_bin):
        return True

    return False


def install_uv() -> None:
    """安装uv"""
    print("正在安装uv...")
    run_command("curl -LsSf https://astral.sh/uv/install.sh | sh")
    # 重新加载PATH
    os.environ["PATH"] = (
        f"{os.path.expanduser('~/.cargo/bin')}:{os.environ.get('PATH', '')}"
    )


def check_python_version() -> bool:
    """检查Python版本是否满足要求"""
    try:
        result = run_command("python3 --version", check=False)
        if result.returncode != 0:
            return False

        version_str = result.stdout.strip().split()[-1]
        version_tuple = tuple(map(int, version_str.split(".")))
        return version_tuple >= (3, 12)
    except:
        return False


def setup_python_environment() -> None:
    """设置Python环境"""
    print("正在设置Python环境...")

    # 检查Python版本
    if not check_python_version():
        print("Python 3.12+ 未安装，正在通过uv安装Python...")
        run_command("uv python install 3.12", shell=True)

    # 创建虚拟环境
    if not Path(".venv").exists():
        print("正在创建虚拟环境...")
        run_command("uv venv")

    # 激活虚拟环境并安装依赖
    print("正在安装依赖...")
    run_command("uv pip install -e .")


def init_database() -> None:
    db_url = "job_info.sqlite"
    table_name = "jobs"

    print(f"正在初始化数据库: {db_url}")

    # 确保数据库目录存在
    db_path = Path(db_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 读取SQL文件
    sql_file = Path("sql/create_table.sql")
    if not sql_file.exists():
        print(f"SQL文件不存在: {sql_file}")
        return

    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # 替换表名（如果SQL中使用了占位符）
    sql_content = sql_content.replace("jobs", table_name)

    # 执行SQL
    conn = sqlite3.connect(db_url)
    try:
        conn.executescript(sql_content)
        conn.commit()
        print(f"数据库初始化完成: {db_url}")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)
    finally:
        conn.close()


def create_config_file():
    """创建settings.yaml文件模板"""
    env_file = Path("./config/settings.yaml")
    if not env_file.exists():
        print("正在创建config/settings.yaml文件模板...")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(open("./config/settings.yaml.example", encoding="utf-8").read())
    print("请编辑config/settings.yaml文件并填入实际的API密钥")
    return


def install_chinese_font():
    """
    在 WSL2 上安装轻量级中文字体 (文泉驿微米黑)。
    这解决了 Chrome 无头模式下中文显示为方框乱码的问题。
    """
    # 定义字体包名称 (Debian/Ubuntu)
    FONT_PACKAGE = "fonts-wqy-microhei"

    print(f"[*] 正在检查中文字体支持...")

    # 1. 检查 fontconfig 是否安装 (fc-list 命令)
    if not shutil.which("fc-list"):
        print("[-] 系统缺少 fontconfig，准备安装...")
        run_command("sudo apt-get update", check=False)
        run_command("sudo apt-get install -y fontconfig", check=True)

    # 2. 检查是否已经存在中文字体
    # 使用 fc-list :lang=zh 检查是否有任何中文字体
    try:
        result = subprocess.run(
            "fc-list :lang=zh", shell=True, capture_output=True, text=True
        )
        if "wqy-microhei" in result.stdout or len(result.stdout.strip()) > 0:
            print("[√] 检测到系统中已安装中文字体，跳过安装。")
            return
    except Exception:
        pass  # 如果检查失败，默认继续尝试安装

    print(f"[-] 未检测到中文字体，准备安装 {FONT_PACKAGE} (需要 sudo 权限)...")

    # 3. 安装字体
    try:
        # 建议先 update
        run_command("sudo apt-get update", check=False)
        run_command("sudo apt-get install -y" + " " + FONT_PACKAGE, check=True)

        # 4. 刷新字体缓存
        print("[*] 刷新字体缓存...")
        run_command("fc-cache -fv", check=False)

        print(f"[√] 中文字体 {FONT_PACKAGE} 安装完成！")

    except Exception as e:
        print(f"[!] 字体安装失败: {e}")
        print("    如果是在极简 Docker 容器中，请确保已安装 fontconfig 包。")


def main() -> None:
    print("=== Work-Show 项目初始化 ===")

    # 1. 检查安装 uv
    if not check_uv():
        install_uv()

    # 2. 设置环境
    setup_python_environment()

    # 3. 创建配置和目录
    create_config_file()

    # 4. 初始化数据库
    init_database()

    # 5. 安装字体
    install_chinese_font()

    # 6. 安装 Chrome (会请求 sudo)
    install_chrome_wsl()

    print("\n=== 初始化完成 ===")
    print("重要提示：如果刚才安装了 uv，请执行以下命令刷新环境变量，或重新打开终端：")
    print("source $HOME/.cargo/env  (或者 source $HOME/.local/bin/env)")
    print("注意修改config下面的配置文件")
    print("\n启动项目:")
    print("uv run python main.py")


if __name__ == "__main__":
    main()
