import os
import requests
from urllib.parse import urlparse
import shutil

# 创建目录结构
def create_directory_structure():
    dirs = [
        'assets',
        'static/css',
        'static/js',
        'vendor/fonts/inter/woff2',
        'vendor/fonts/font-awesome/css',
        'vendor/fonts/font-awesome/webfonts',
        'vendor/css/highlight',
        'vendor/js',
        'vendor/js/highlight/languages'
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"创建目录: {dir_path}")

# 下载文件
def download_file(url, dest_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"下载成功: {url} -> {dest_path}")
        return True
    except Exception as e:
        print(f"下载失败: {url} - {str(e)}")
        return False

# 下载所有资源
def download_all_resources():
    # Inter字体
    inter_fonts = {
        'vendor/fonts/inter/woff2/inter-300.woff2': 'https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa2JL7SUc.woff2',
        'vendor/fonts/inter/woff2/inter-400.woff2': 'https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa1ZL7SUc.woff2',
        'vendor/fonts/inter/woff2/inter-500.woff2': 'https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa2pL7SUc.woff2',
        'vendor/fonts/inter/woff2/inter-600.woff2': 'https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa25L7SUc.woff2',
        'vendor/fonts/inter/woff2/inter-700.woff2': 'https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa1pL7SUc.woff2'
    }
    
    # Font Awesome
    font_awesome = {
        'vendor/fonts/font-awesome/css/all.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
        'vendor/fonts/font-awesome/webfonts/fa-solid-900.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2',
        'vendor/fonts/font-awesome/webfonts/fa-regular-400.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2',
        'vendor/fonts/font-awesome/webfonts/fa-brands-400.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff2',
        'vendor/fonts/font-awesome/webfonts/fa-v4compatibility.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-v4compatibility.woff2'
    }
    
    # Highlight.js
    highlight_css = {
        'vendor/css/highlight/default.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/default.min.css'
    }
    
    # JavaScript库
    js_libs = {
        'vendor/js/marked.min.js': 'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
        'vendor/js/highlight/highlight.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js',
        'vendor/js/highlight/languages/javascript.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/javascript.min.js',
        'vendor/js/highlight/languages/python.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/python.min.js',
        'vendor/js/highlight/languages/sql.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/sql.min.js',
        'vendor/js/highlight/languages/bash.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/bash.min.js',
        'vendor/js/highlight/languages/json.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/json.min.js',
        'vendor/js/highlight/languages/mermaid.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/mermaid.min.js'
    }
    
    # 下载所有文件
    all_files = {**inter_fonts, **font_awesome, **highlight_css, **js_libs}
    
    for dest_path, url in all_files.items():
        download_file(url, dest_path)

# 创建Inter字体CSS文件
def create_inter_css():
    css_content = """/* inter-300 - latin */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 300;
  font-display: swap;
  src: url('./woff2/inter-300.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

/* inter-400 - latin */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('./woff2/inter-400.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

/* inter-500 - latin */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url('./woff2/inter-500.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

/* inter-600 - latin */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url('./woff2/inter-600.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

/* inter-700 - latin */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('./woff2/inter-700.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}"""
    
    with open('vendor/fonts/inter/inter.css', 'w') as f:
        f.write(css_content)
    print("创建Inter字体CSS文件: vendor/fonts/inter/inter.css")

# 创建修改后的HTML文件
def create_html_file():
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>CTC CF AI知识库 - 人工智能助手</title>
  <link rel="icon" href="/assets/icon.ico" type="image/x-icon"/>
  <link rel="stylesheet" href="/static/css/style.css"/>
  <link href="/vendor/fonts/inter/inter.css" rel="stylesheet">
  <link rel="stylesheet" href="/vendor/fonts/font-awesome/css/all.min.css">
  <link rel="stylesheet" href="/vendor/css/highlight/default.min.css">
  
  <!-- 优化资源加载顺序 -->
  <script src="/vendor/js/marked.min.js"></script>
  <script src="/vendor/js/highlight/highlight.min.js" defer></script>
  <script src="/vendor/js/highlight/languages/javascript.min.js" defer></script>
  <script src="/vendor/js/highlight/languages/python.min.js" defer></script>
  <script src="/vendor/js/highlight/languages/sql.min.js" defer></script>
  <script src="/vendor/js/highlight/languages/bash.min.js" defer></script>
  <script src="/vendor/js/highlight/languages/json.min.js" defer></script>
  <script src="/vendor/js/highlight/languages/mermaid.min.js" defer></script>
  <script type="module" src="/static/js/app.js" defer></script>
</head>
<body>
  <header class="top-bar">
    <button class="menu-btn" id="menuBtn">
      <i class="fas fa-bars"></i>
    </button>
    <div class="title">
      <img src="/assets/icon.ico" alt="Logo" class="logo">
      <span>CTC CF AI知识库</span>
    </div>
    <button class="new-chat-btn" id="newChatBtn">
      <i class="fas fa-plus"></i> 新建会话
    </button>
  </header>
  
  <!-- 侧边抽屉 -->
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div class="search-container">
        <i class="fas fa-search search-icon"></i>
        <input type="text" id="searchHistory" placeholder="搜索会话..." />
      </div>
      <button class="export-btn" id="exportBtn">
        <i class="fas fa-download"></i> 导出记录
      </button>
    </div>
    <ul id="historyList"></ul>
  </aside>
  
  <div class="overlay" id="overlay"></div>
  
  <main class="chat-container">
    <div class="chat-body" id="chatBody">
      <div class="welcome-message">
        <img src="/assets/avatar-big.png" alt="AI Avatar" class="welcome-avatar">
        <h2>欢迎使用CF AI知识库</h2>
        <p>我可以帮助您解答各种问题，请随时提问！</p>
        <div class="suggestions">
          <div class="suggestion" data-suggestion="CF 厂长是谁，他的具体信息？">CF 厂长是谁，他的具体信息？</div>
          <div class="suggestion" data-suggestion="我是一名Repair站点新人，该如何规划学习线路？">我是一名Repair站点新人，该如何规划学习线路？</div>
          <div class="suggestion" data-suggestion="BM1 Common Defect白缺陷异常原因有哪些，如何改善？">BM1 Common Defect异常原因有哪些，如何改善？</div>
        </div>
      </div>
    </div>
    
    <div class="chat-input-area">
      <div class="input-container">
        <textarea id="chatInput" placeholder="输入你的问题..." rows="1"></textarea>
        <button id="sendBtn" class="send-btn">
          <i class="fas fa-paper-plane"></i>
        </button>
      </div>
      <div class="input-footer">
        <label class="deep-thinking-toggle">
          <input type="checkbox" id="deepThinkingToggle">
          <span class="toggle-slider"></span>
          <span class="toggle-label">深度思考</span>
        </label>
        <small>CF AI知识库 v1.0 · 基于RAGFlow技术 · 路武雷</small>
      </div>
    </div>
  </main>
</body>
</html>"""
    
    with open('index.html', 'w') as f:
        f.write(html_content)
    print("创建修改后的HTML文件: index.html")

# 主函数
def main():
    print("开始创建目录结构...")
    create_directory_structure()
    
    print("\n开始下载所有资源...")
    download_all_resources()
    
    print("\n创建Inter字体CSS文件...")
    create_inter_css()
    
    print("\n创建修改后的HTML文件...")
    create_html_file()
    
    print("\n所有资源已准备完成！")
    print("请确保您有以下本地文件：")
    print("- assets/icon.ico")
    print("- assets/avatar-big.png")
    print("- static/css/style.css")
    print("- static/js/app.js")

if __name__ == "__main__":
    main()