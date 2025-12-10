#!/usr/bin/env python3
"""
Local server for serving privacy policy, terms of service, and data deletion information.
Runs on localhost:8080
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse
import logging
from urllib.parse import parse_qs
from time import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

token_container = {"auth_code": None, "state": None, "timestamp": None}

class PolicyHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        logger.info(f"Received request for: {path}")
        
        # 路由处理
        if path == '/private' or path == '/privacy':
            self.serve_privacy_policy()
        elif path == '/rules' or path == '/terms':
            self.serve_terms_of_service()
        elif path == '/database' or path == '/data-deletion':
            self.serve_data_deletion_info()
        elif path == '/' or path == '/index':
            self.serve_index()
        elif path == '/callback':
            self.serve_oauth_callback()
        elif path == '/code':
            self.serve_auth_code()
        else:
            self.serve_404()
    
    def serve_privacy_policy(self):
        """返回隐私政策"""
        html_content = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>隐私政策 - Ithaca Marketing Platform</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    line-height: 1.6;
                    color: #333;
                }
                h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 30px; }
                .highlight { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; }
                .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>🔒 隐私政策</h1>
            
            <div class="highlight">
                <strong>生效日期：</strong>2024年12月2日<br>
                <strong>最后更新：</strong>2024年12月2日
            </div>
            
            <h2>1. 信息收集</h2>
            <p>Ithaca Marketing Platform 致力于保护您的隐私。我们收集以下类型的信息：</p>
            <ul>
                <li><strong>账户信息：</strong>用户名、邮箱地址、联系方式</li>
                <li><strong>营销数据：</strong>广告活动数据、预算信息、投放结果</li>
                <li><strong>使用数据：</strong>平台使用情况、功能偏好、操作日志</li>
                <li><strong>技术信息：</strong>IP地址、浏览器类型、设备信息</li>
            </ul>
            
            <h2>2. 信息使用</h2>
            <p>我们使用收集的信息用于：</p>
            <ul>
                <li>提供和改进营销服务</li>
                <li>生成营销分析报告</li>
                <li>优化广告投放效果</li>
                <li>提供技术支持和客户服务</li>
                <li>确保平台安全和防止滥用</li>
            </ul>
            
            <h2>3. 信息共享</h2>
            <p>我们不会向第三方出售、交易或转让您的个人信息，除非：</p>
            <ul>
                <li>获得您的明确同意</li>
                <li>法律法规要求</li>
                <li>保护我们的权利和安全</li>
                <li>与可信的服务提供商合作（如Meta Ads API）</li>
            </ul>
            
            <h2>4. 数据安全</h2>
            <p>我们采用行业标准的安全措施保护您的数据：</p>
            <ul>
                <li>数据加密传输和存储</li>
                <li>访问控制和身份验证</li>
                <li>定期安全审计和更新</li>
                <li>员工隐私培训</li>
            </ul>
            
            <h2>5. 您的权利</h2>
            <p>您有权：</p>
            <ul>
                <li>访问和查看您的个人数据</li>
                <li>更正不准确的信息</li>
                <li>删除您的账户和数据</li>
                <li>限制数据处理</li>
                <li>数据可携带性</li>
            </ul>
            
            <div class="highlight">
                <strong>联系我们：</strong><br>
                如有隐私相关问题，请联系：<br>
                📧 Email: privacy@ithaca-platform.com<br>
                📱 电话: +86-xxx-xxxx-xxxx
            </div>
            
            <div class="footer">
                <p><a href="/">← 返回首页</a> | <a href="/rules">服务条款</a> | <a href="/database">数据删除</a></p>
                <p>&copy; 2024 Ithaca Marketing Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_terms_of_service(self):
        """返回服务条款"""
        html_content = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>服务条款 - Ithaca Marketing Platform</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    line-height: 1.6;
                    color: #333;
                }
                h1 { color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 30px; }
                .highlight { background-color: #fff5f5; padding: 15px; border-left: 4px solid #e74c3c; margin: 20px 0; }
                .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; }
                a { color: #e74c3c; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>📋 服务条款</h1>
            
            <div class="highlight">
                <strong>生效日期：</strong>2024年12月2日<br>
                <strong>最后更新：</strong>2024年12月2日
            </div>
            
            <h2>1. 服务概述</h2>
            <p>Ithaca Marketing Platform（以下简称"本平台"）是一个基于AI的Meta Ads营销自动化平台，为用户提供：</p>
            <ul>
                <li>智能营销计划生成</li>
                <li>自动化广告投放管理</li>
                <li>营销效果分析和优化</li>
                <li>数据洞察和报告</li>
            </ul>
            
            <h2>2. 用户责任</h2>
            <p>使用本平台时，您需要：</p>
            <ul>
                <li>提供真实、准确的账户信息</li>
                <li>遵守相关法律法规和Meta Ads政策</li>
                <li>不得使用平台进行违法或有害活动</li>
                <li>保护您的账户安全和登录凭据</li>
                <li>及时更新您的联系信息</li>
            </ul>
            
            <h2>3. 服务限制</h2>
            <div class="warning">
                <strong>重要提醒：</strong>
                <ul>
                    <li>本平台依赖Meta Ads API，服务可用性受Meta政策影响</li>
                    <li>AI生成的营销建议仅供参考，最终决策由用户承担</li>
                    <li>我们不保证特定的营销效果或投资回报</li>
                </ul>
            </div>
            
            <h2>4. 费用和付款</h2>
            <p>关于平台使用费用：</p>
            <ul>
                <li>基础功能免费使用</li>
                <li>高级功能可能需要付费订阅</li>
                <li>广告投放费用直接由Meta收取</li>
                <li>费用变更将提前30天通知</li>
            </ul>
            
            <h2>5. 知识产权</h2>
            <p>本平台的所有内容和技术受知识产权保护：</p>
            <ul>
                <li>平台代码和算法归我们所有</li>
                <li>用户数据和营销内容归用户所有</li>
                <li>禁止未授权的复制、分发或修改</li>
            </ul>
            
            <h2>6. 免责声明</h2>
            <p>在法律允许的范围内：</p>
            <ul>
                <li>我们不对营销效果做任何保证</li>
                <li>不承担因第三方服务中断造成的损失</li>
                <li>用户需自行承担投资风险</li>
                <li>我们的责任限于平台服务费用</li>
            </ul>
            
            <h2>7. 服务终止</h2>
            <p>在以下情况下，我们可能终止服务：</p>
            <ul>
                <li>用户违反服务条款</li>
                <li>长期未使用账户</li>
                <li>技术或商业原因</li>
                <li>法律法规要求</li>
            </ul>
            
            <div class="highlight">
                <strong>争议解决：</strong><br>
                如有争议，优先通过友好协商解决。协商不成的，提交至平台所在地仲裁委员会仲裁。
            </div>
            
            <div class="footer">
                <p><a href="/">← 返回首页</a> | <a href="/private">隐私政策</a> | <a href="/database">数据删除</a></p>
                <p>&copy; 2024 Ithaca Marketing Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_data_deletion_info(self):
        """返回数据删除说明"""
        html_content = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>用户数据删除 - Ithaca Marketing Platform</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    line-height: 1.6;
                    color: #333;
                }
                h1 { color: #2c3e50; border-bottom: 2px solid #f39c12; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 30px; }
                .highlight { background-color: #fef9e7; padding: 15px; border-left: 4px solid #f39c12; margin: 20px 0; }
                .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; }
                a { color: #f39c12; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .steps { background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .step { margin: 15px 0; padding: 10px; border-left: 3px solid #f39c12; }
                .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>🗑️ 用户数据删除指南</h1>
            
            <div class="highlight">
                <strong>您的数据权利：</strong><br>
                根据相关法律法规，您有权要求删除您在本平台的所有个人数据。
            </div>
            
            <h2>1. 可删除的数据类型</h2>
            <p>我们可以为您删除以下数据：</p>
            <ul>
                <li><strong>账户信息：</strong>用户名、邮箱、个人资料</li>
                <li><strong>营销数据：</strong>广告活动记录、预算设置、投放历史</li>
                <li><strong>分析数据：</strong>效果报告、数据洞察、优化建议</li>
                <li><strong>系统日志：</strong>登录记录、操作日志、错误日志</li>
                <li><strong>缓存数据：</strong>临时文件、会话数据</li>
            </ul>
            
            <h2>2. 数据删除流程</h2>
            <div class="steps">
                <div class="step">
                    <strong>步骤 1：</strong> 提交删除请求<br>
                    发送邮件至 <strong>data-deletion@ithaca-platform.com</strong>
                </div>
                
                <div class="step">
                    <strong>步骤 2：</strong> 身份验证<br>
                    我们将验证您的身份以确保数据安全
                </div>
                
                <div class="step">
                    <strong>步骤 3：</strong> 确认删除范围<br>
                    我们会与您确认要删除的具体数据类型
                </div>
                
                <div class="step">
                    <strong>步骤 4：</strong> 执行删除<br>
                    在确认后的30天内完成数据删除
                </div>
                
                <div class="step">
                    <strong>步骤 5：</strong> 删除确认<br>
                    向您发送数据删除完成确认
                </div>
            </div>
            
            <h2>3. 删除请求邮件模板</h2>
            <div class="highlight">
                <strong>邮件主题：</strong>数据删除请求 - [您的用户名]<br><br>
                <strong>邮件内容：</strong><br>
                尊敬的Ithaca团队，<br><br>
                我是用户 [您的用户名]，注册邮箱 [您的邮箱]。<br>
                我希望删除我在Ithaca Marketing Platform上的所有个人数据。<br><br>
                请删除的数据包括：<br>
                □ 账户信息<br>
                □ 营销活动数据<br>
                □ 分析报告<br>
                □ 系统日志<br>
                □ 其他所有相关数据<br><br>
                请确认收到此请求并告知预计完成时间。<br><br>
                谢谢！<br>
                [您的姓名]<br>
                [日期]
            </div>
            
            <h2>4. 重要注意事项</h2>
            <div class="warning">
                <strong>⚠️ 删除前请注意：</strong>
                <ul>
                    <li>数据删除后无法恢复，请确保已备份重要信息</li>
                    <li>删除过程中您的账户将被暂停使用</li>
                    <li>某些法律要求保留的数据可能无法立即删除</li>
                    <li>第三方服务（如Meta Ads）的数据需要单独处理</li>
                </ul>
            </div>
            
            <h2>5. 删除时间表</h2>
            <ul>
                <li><strong>即时删除：</strong>缓存数据、会话信息</li>
                <li><strong>7天内：</strong>账户信息、个人资料</li>
                <li><strong>30天内：</strong>营销数据、分析报告</li>
                <li><strong>90天内：</strong>备份数据、日志文件</li>
            </ul>
            
            <h2>6. 部分删除选项</h2>
            <p>如果您不想删除所有数据，我们也支持：</p>
            <ul>
                <li>仅删除个人身份信息</li>
                <li>保留匿名化的营销数据用于研究</li>
                <li>删除特定时间段的数据</li>
                <li>删除特定类型的数据</li>
            </ul>
            
            <div class="highlight">
                <strong>联系我们：</strong><br>
                📧 数据删除专用邮箱: data-deletion@ithaca-platform.com<br>
                📧 一般咨询: support@ithaca-platform.com<br>
                📱 客服电话: +86-xxx-xxxx-xxxx<br>
                🕒 工作时间: 周一至周五 9:00-18:00
            </div>
            
            <div class="footer">
                <p><a href="/">← 返回首页</a> | <a href="/private">隐私政策</a> | <a href="/rules">服务条款</a></p>
                <p>&copy; 2024 Ithaca Marketing Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_index(self):
        """返回首页"""
        html_content = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ithaca Marketing Platform - 政策中心</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container { 
                    background: white; 
                    padding: 40px; 
                    border-radius: 15px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }
                h1 { 
                    color: #2c3e50; 
                    text-align: center; 
                    margin-bottom: 30px;
                    font-size: 2.5em;
                }
                .cards { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                    gap: 20px; 
                    margin: 30px 0;
                }
                .card { 
                    background: #f8f9fa; 
                    padding: 25px; 
                    border-radius: 10px; 
                    text-align: center;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    border: 2px solid transparent;
                }
                .card:hover { 
                    transform: translateY(-5px); 
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                    border-color: #3498db;
                }
                .card h3 { margin-top: 0; color: #34495e; }
                .card a { 
                    display: inline-block;
                    background: linear-gradient(45deg, #3498db, #2980b9);
                    color: white; 
                    padding: 12px 25px; 
                    text-decoration: none; 
                    border-radius: 25px;
                    margin-top: 15px;
                    transition: background 0.3s ease;
                }
                .card a:hover { 
                    background: linear-gradient(45deg, #2980b9, #1f4e79);
                }
                .footer { 
                    text-align: center; 
                    margin-top: 40px; 
                    padding-top: 20px; 
                    border-top: 1px solid #eee; 
                    color: #666; 
                }
                .emoji { font-size: 2em; margin-bottom: 15px; }
                .server-info {
                    background: #e8f5e8;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    text-align: center;
                    border: 1px solid #4caf50;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Ithaca Marketing Platform</h1>
                
                <div class="server-info">
                    <strong>🌐 本地服务器运行中</strong><br>
                    地址: <code>localhost:8080</code> | 状态: <span style="color: #4caf50;">●</span> 在线
                </div>
                
                <p style="text-align: center; font-size: 1.2em; color: #666;">
                    欢迎访问政策和条款中心
                </p>
                
                <div class="cards">
                    <div class="card">
                        <div class="emoji">🔒</div>
                        <h3>隐私政策</h3>
                        <p>了解我们如何收集、使用和保护您的个人信息</p>
                        <a href="/private">查看隐私政策</a>
                    </div>
                    
                    <div class="card">
                        <div class="emoji">📋</div>
                        <h3>服务条款</h3>
                        <p>使用本平台的规则、权利和责任说明</p>
                        <a href="/rules">查看服务条款</a>
                    </div>
                    
                    <div class="card">
                        <div class="emoji">🗑️</div>
                        <h3>数据删除</h3>
                        <p>如何请求删除您在平台上的所有数据</p>
                        <a href="/database">数据删除指南</a>
                    </div>
                </div>
                
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 30px 0; border: 1px solid #ffeaa7;">
                    <h3 style="margin-top: 0; color: #856404;">📞 需要帮助？</h3>
                    <p style="margin-bottom: 0;">
                        如有任何问题，请联系我们：<br>
                        📧 Email: support@ithaca-platform.com<br>
                        📱 电话: +86-xxx-xxxx-xxxx
                    </p>
                </div>
                
                <div class="footer">
                    <p>&copy; 2024 Ithaca Marketing Platform. All rights reserved.</p>
                    <p style="font-size: 0.9em; color: #999;">
                        基于AI的Meta Ads营销自动化平台 | 版本 1.0.0
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    # serve oauth callback in response['code']
    def serve_oauth_callback(self):
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]
        error = params.get('error', [None])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        global token_container

        if error:
            html = f"""
            <html>
            <head><title>Authorization Failed</title></head>
            <body>
                <h1>Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>The authorization was cancelled or failed. You can close this window.</p>
            </body>
            </html>
            """
            logger.error(f"OAuth authorization failed: {error}")
        elif code:
            logger.info(f"Received authorization code: {code[:10]}...")

            token_container.update({
                "auth_code": code,
                "state": state,
                "timestamp": time(),
            })

            html = """
            <html>
            <head><title>Authorization Successful</title></head>
            <body>
                <h1>Authorization Successful!</h1>
                <p>You have successfully authorized the Meta Ads application.</p>
                <p>You can now close this window and return to your application.</p>
                <script>
                    // Try to close the window automatically after 2 seconds
                    setTimeout(function() {
                        window.close();
                    }, 2000);
                </script>
            </body>
            </html>
            """
            logger.info("OAuth authorization successful")
        else:
            html = """
            <html>
            <head><title>Unexpected Response</title></head>
            <body>
                <h1>Unexpected Response</h1>
                <p>No authorization code or error received. Please try again.</p>
            </body>
            </html>
            """
            logger.warning("OAuth callback received without code or error")

        self.wfile.write(html.encode("utf-8"))

    # ✅ 新增：返回 auth_code，保证在 response['code'] 中
    def serve_auth_code(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()

        response_data = {
            "code": token_container.get("auth_code"),
            "state": token_container.get("state"),
            "timestamp": token_container.get("timestamp"),
        }
        self.wfile.write(json.dumps(response_data).encode("utf-8"))
    
    def serve_404(self):
        """返回404页面"""
        html_content = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>页面未找到 - Ithaca Marketing Platform</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 600px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    text-align: center;
                    color: #333;
                }
                h1 { color: #e74c3c; font-size: 3em; margin-bottom: 20px; }
                p { font-size: 1.2em; margin: 20px 0; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .links { margin-top: 30px; }
                .links a { 
                    display: inline-block; 
                    margin: 10px; 
                    padding: 10px 20px; 
                    background: #3498db; 
                    color: white; 
                    border-radius: 5px; 
                    text-decoration: none;
                }
                .links a:hover { background: #2980b9; }
            </style>
        </head>
        <body>
            <h1>404</h1>
            <p>🔍 抱歉，您访问的页面不存在</p>
            <p>请检查URL是否正确，或访问以下页面：</p>
            
            <div class="links">
                <a href="/">🏠 首页</a>
                <a href="/private">🔒 隐私政策</a>
                <a href="/rules">📋 服务条款</a>
                <a href="/database">🗑️ 数据删除</a>
            </div>
        </body>
        </html>
        """
        
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server(host='localhost', port=8080):
    """启动服务器"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, PolicyHandler)
    
    logger.info(f"🚀 Starting server on http://{host}:{port}")
    logger.info("📋 Available endpoints:")
    logger.info("   • http://localhost:8080/ - 首页")
    logger.info("   • http://localhost:8080/private - 隐私政策")
    logger.info("   • http://localhost:8080/rules - 服务条款")
    logger.info("   • http://localhost:8080/database - 数据删除指南")
    logger.info("   • http://localhost:8080/callback - oauth回调地址")
    logger.info("   • http://localhost:8080/code - get oauth authorization code in response['code']")
    logger.info("🛑 Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
        httpd.server_close()


if __name__ == '__main__':
    run_server()
