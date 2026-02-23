"""
Windows计划任务管理器
用于设置公众号文章自动写作计划任务
"""
import subprocess
import os
import sys
from pathlib import Path

# 确保可以导入同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))

def setup_scheduled_task():
    """设置Windows计划任务，每天早上9点自动运行写作脚本"""
    script_dir = Path(__file__).parent
    python_exe = "python"
    script_path = script_dir / "execute_test_run.py"
    task_name = "WeChatArticleWriter"

    # 构建PowerShell命令
    ps_command = f'''
$taskName = "{task_name}"
$scriptPath = "{script_path}"
$pythonPath = "{python_exe}"

# 检查任务是否已存在
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {{
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}}

# 创建触发器 - 每天早上9点
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00AM"

# 创建操作
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath

# 创建设置
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 创建主体
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

# 注册任务
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Principal $principal -Description "公众号文章自动写作任务"

Write-Host "计划任务创建成功！"
'''

    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("   [计划任务] Windows计划任务已设置完成！")
            print("   [计划任务] 任务名称: WeChatArticleWriter")
            print("   [计划任务] 执行时间: 每天 09:00")
            return True
        else:
            print(f"   [计划任务] 设置失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"   [计划任务] 设置失败: {e}")
        return False

def remove_scheduled_task():
    """移除计划任务"""
    task_name = "WeChatArticleWriter"
    ps_command = f'Unregister-ScheduledTask -TaskName "{task_name}" -Confirm:$false -ErrorAction SilentlyContinue'

    try:
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
        print("   [计划任务] 已移除计划任务")
        return True
    except:
        return False

if __name__ == "__main__":
    setup_scheduled_task()
