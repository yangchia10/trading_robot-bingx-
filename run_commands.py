import subprocess
import os

def run_commands_from_file(file_path):
    # 讀取命令文件
    with open(file_path, 'r') as file:
        commands = file.read()

    # 創建臨時批處理文件
    bat_file_path = 'temp_run_commands.bat'
    with open(bat_file_path, 'w') as bat_file:
        bat_file.write(commands)
    
    try:
        # 使用 PowerShell 以管理員身份運行批處理文件
        ps_command = f'Start-Process cmd -ArgumentList "/c {bat_file_path}" -Verb runAs'
        subprocess.run(['powershell', '-Command', ps_command], check=True)
    finally:
        # 為了安全和清理，可以選擇在這裏刪除批處理文件
        # os.remove(bat_file_path)
        pass

