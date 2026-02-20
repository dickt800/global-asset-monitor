#!/bin/bash
# 全球资产监控系统 - 快速启动脚本

echo "🌍 全球资产监控系统 - 快速启动"
echo "================================"

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python 3"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，从模板创建..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件，填入你的 API Key"
    exit 0
fi

# 显示菜单
echo ""
echo "请选择运行模式："
echo "1) 运行一次监控"
echo "2) 强制运行（忽略静默模式）"
echo "3) 发送测试邮件"
echo "4) 启动 Streamlit Dashboard"
echo "5) 运行定时任务（每小时）"
read -p "输入选项 [1-5]: " choice

case $choice in
    1)
        echo "🚀 运行监控..."
        python main.py
        ;;
    2)
        echo "🚀 强制运行监控..."
        python main.py --force
        ;;
    3)
        echo "📧 发送测试邮件..."
        python main.py --test-email
        ;;
    4)
        echo "🌐 启动 Dashboard..."
        streamlit run app.py
        ;;
    5)
        echo "⏰ 启动定时任务（每小时检查一次）..."
        echo "按 Ctrl+C 停止"
        while true; do
            python main.py
            echo "⏳ 等待 1 小时..."
            sleep 3600
        done
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
