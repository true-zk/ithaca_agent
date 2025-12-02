import asyncio
import json
import sys
from pathlib import Path
import time
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.runnables import RunnableConfig

from ithaca.oauth.auth import auth_manager
from ithaca.agents.reactagent import ReactAgent


def extract_and_print_response(message):
    """提取并美化打印响应内容"""
    
    if hasattr(message, 'content'):
        content = message.content
    else:
        content = message
    
    # 处理列表格式的内容
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                text_parts.append(item.get('text', ''))
        text = '\n'.join(text_parts)
    else:
        text = str(content)
    
    # 清理和格式化
    clean_text = text.replace('\\n', '\n').replace("\\'", "'")
    
    # 美化输出
    print("\n" + "🤖 " + "="*50)
    print("AI Assistant Response:")
    print("="*55)
    
    # 按段落分割并格式化
    paragraphs = clean_text.split('\n\n')
    for para in paragraphs:
        if para.strip():
            # 处理 Markdown 样式的粗体
            formatted_para = para.replace('**', '').replace('*', '•')
            print(formatted_para)
            print()  # 段落间空行
    
    print("="*55 + "\n")


async def test_reactagent_chat(initial_prompt: str = None):
    """Test react agent"""
    if not auth_manager.get_access_token():
        auth_manager.authenticate(force_refresh=True)

    print("=" * 20)
    print("Testing react agent")
    print("=" * 20)

    config : RunnableConfig = {"configurable": {"thread_id": "4"}}
    reactagent = ReactAgent().agent

    while True:
        prompt = input("Enter your prompt: ")
        if prompt.lower() == "exit":
            break
        elif prompt.lower() == "prompt":
            prompt = initial_prompt
        try:
            # messages.append({"role": "user", "content": prompt})
            res = await reactagent.ainvoke({"messages": prompt}, config)
            extract_and_print_response(res["messages"][-1])
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    prompt = """
    You should think step by step and complete my tasks:  
    1. make a new marketing plan, to let users access the product (url), 
    this should contains details like campaigns / adsets / ads ... 
    that you will change or create. you should return the plan in a good format;;
    2. execute the marketing plan, if you find any error, you should retry in 3 times;; 
    3. give me the reason why you make such a plan.;; 
    
    Data: 
    the product is taptap app install website, 
    and app url is https://play.google.com/store/apps/details?id=com.taptap.global.lite , 
    If you want to create a new creative, 
    use the picture: https://play-lh.googleusercontent.com/k8vYThDw5A8sAbAVHQ1yUmO9UWCwrKDf3ggTxa4Pve8rRFquhU0a5hCFqalGTEoVKQ=w240-h480-rw , 
    upload it by url first and then create the creative with this image's hash ;; 

    IMPORTANT: you should create a traffic / link click campaign / adset / ad for the product.

    Suggestions:  
    If you need something additional to know, use web_search tool to search.  
    If you find some tool args you need is not provided, you should use other tools to get them.  
    If you find some tools return None response, just skip them. 
    If you find errors when creating adsets or ads, try to create other types.
    """
    # asyncio.run(test_reactagent_chat())
    asyncio.run(test_reactagent_chat(prompt))