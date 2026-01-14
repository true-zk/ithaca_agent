# Ithaca Local Policy Server

*This is for Meta ads app requirements.*

本地政策服务器，用于提供隐私政策、服务条款和数据删除指南。

## 🚀 快速启动

### 方法1：直接运行Python脚本
```bash
cd /Users/zhongken/ithaca
python auxiliary/localserver.py
```

### 方法2：使用启动脚本
```bash
cd /Users/zhongken/ithaca
./auxiliary/start_server.sh
```

## 📍 访问地址

服务器启动后，可以通过以下地址访问：

- **首页**: http://localhost:8001/
- **隐私政策**: http://localhost:8001/private
- **服务条款**: http://localhost:8001/rules  
- **数据删除指南**: http://localhost:8001/database

## 🔧 功能特性

### ✅ 已实现功能
- [x] 响应式网页设计
- [x] 美观的UI界面
- [x] 完整的隐私政策内容
- [x] 详细的服务条款说明
- [x] 用户数据删除指南
- [x] 404错误页面处理
- [x] 服务器日志记录
- [x] 多路由支持

### 📋 页面内容

#### 1. 隐私政策 (`/private`)
- 信息收集说明
- 信息使用方式
- 数据共享政策
- 安全保护措施
- 用户权利说明

#### 2. 服务条款 (`/rules`)
- 服务概述
- 用户责任
- 服务限制
- 费用说明
- 知识产权
- 免责声明
- 争议解决

#### 3. 数据删除指南 (`/database`)
- 可删除数据类型
- 删除流程步骤
- 邮件模板
- 注意事项
- 删除时间表
- 联系方式

## 🛠️ 技术实现

- **语言**: Python 3
- **框架**: 内置 `http.server`
- **端口**: 8001
- **编码**: UTF-8
- **响应格式**: HTML

## 📝 日志功能

服务器会记录以下信息：
- 访问请求日志
- 错误信息
- 服务器状态

## 🔄 停止服务器

在终端中按 `Ctrl+C` 停止服务器。

## 📞 联系信息

如需修改页面内容或添加新功能，请联系开发团队。

---

*最后更新: 2024年12月2日*
