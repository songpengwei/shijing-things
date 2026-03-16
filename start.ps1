# 诗经事物 - Windows 本地一键启动脚本

$ErrorActionPreference = "Stop"

# 颜色定义
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[34m"
$NC = "`e[0m"

Write-Host "$Blue==============================================$NC"
Write-Host "$Blue      诗经事物 - 本地开发环境启动$NC"
Write-Host "$Blue==============================================$NC"
Write-Host ""

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"

Set-Location $ScriptDir

# 1. 检查并激活 conda 环境
Write-Host "$Yellow[1/4] 检查 conda 环境...$NC"

# 检查 conda 是否可用
$condaCmd = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaCmd) {
    # 尝试常见的 conda 安装路径
    $possibleCondaPaths = @(
        "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
        "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
        "C:\ProgramData\miniconda3\Scripts\conda.exe",
        "C:\ProgramData\anaconda3\Scripts\conda.exe"
    )
    
    foreach ($path in $possibleCondaPaths) {
        if (Test-Path $path) {
            $condaCmd = $path
            break
        }
    }
}

if (-not $condaCmd) {
    Write-Host "  $Red✗ 未找到 conda，请确保已安装 Anaconda 或 Miniconda$NC"
    exit 1
}

# 检查环境是否存在
$envExists = & $condaCmd env list | Select-String "^shijing"

if (-not $envExists) {
    Write-Host "  $Red✗ 未找到 shijing 环境$NC"
    Write-Host ""
    Write-Host "请使用以下命令创建环境:"
    Write-Host "  conda create -n shijing python=3.11"
    Write-Host ""
    exit 1
}

# 激活环境
Write-Host "  正在激活 shijing 环境..."
& $condaCmd activate shijing
Write-Host "  $Green✓ conda 环境已激活$NC"

# 2. 安装依赖
Write-Host ""
Write-Host "$Yellow[2/4] 安装依赖...$NC"
Set-Location $BackendDir

if (Test-Path "requirements.txt") {
    pip install -q -r requirements.txt
    Write-Host "  $Green✓ 依赖安装完成$NC"
} else {
    Write-Host "  $Red✗ 未找到 requirements.txt$NC"
    exit 1
}

# 3. 初始化数据库
Write-Host ""
Write-Host "$Yellow[3/4] 初始化数据库...$NC"

if (Test-Path "shijing.db") {
    Write-Host "  数据库文件已存在"
    $reinit = Read-Host "  是否重新初始化数据库? (y/N)"
    if ($reinit -eq "y" -or $reinit -eq "Y") {
        Remove-Item "shijing.db" -Force
        Write-Host "  已删除旧数据库"
        echo "y" | python init_db.py
    } else {
        Write-Host "  跳过数据库初始化"
    }
} else {
    echo "y" | python init_db.py
}

if (-not (Test-Path "shijing.db")) {
    Write-Host "  $Red✗ 数据库初始化失败$NC"
    exit 1
}

Write-Host "  $Green✓ 数据库准备就绪$NC"

# 4. 启动服务
Write-Host ""
Write-Host "$Yellow[4/4] 启动服务...$NC"
Write-Host ""
Write-Host "$Green==============================================$NC"
Write-Host "$Green  服务即将启动$NC"
Write-Host "$Green==============================================$NC"
Write-Host ""
Write-Host "  访问地址:"
Write-Host "    - 首页:       http://localhost:8000"
Write-Host "    - API 文档:   http://localhost:8000/api/docs"
Write-Host "    - 管理页面:   http://localhost:8000/manage"
Write-Host ""
Write-Host "  快捷键:"
Write-Host "    - Ctrl+C 停止服务"
Write-Host ""
Write-Host "$Green==============================================$NC"
Write-Host ""

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
