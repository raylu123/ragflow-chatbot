// 使用模块模式组织代码
const ChatApp = (function() {
  // 私有变量
  let currentSessionId = null;
  
  // DOM元素
  const elements = {
    chatBody: document.getElementById("chatBody"),
    chatInput: document.getElementById("chatInput"),
    sendBtn: document.getElementById("sendBtn"),
    menuBtn: document.getElementById("menuBtn"),
    sidebar: document.getElementById("sidebar"),
    newChatBtn: document.getElementById("newChatBtn"),
    historyList: document.getElementById("historyList"),
    searchHistory: document.getElementById("searchHistory"),
    overlay: document.getElementById("overlay"),
    deepThinkingToggle: document.getElementById("deepThinkingToggle"),
    exportBtn: document.getElementById("exportBtn")
  };
  
  // 初始化函数
  function init() {
      // 确保Array.prototype.at方法存在（为旧版本NW.js提供支持）
    if (!Array.prototype.at) {
      Array.prototype.at = function(index) {
        if (index >= 0) {
          return this[index];
        } else {
          return this[this.length + index];
        }
      };
    }
    // 配置Markdown渲染
    if (typeof marked !== 'undefined') {
      // 对于旧版本marked.js，使用旧的配置方式
      if (marked.setOptions) {
        marked.setOptions({
          highlight: function(code, lang) {
            if (lang && window.hljs && window.hljs.getLanguage(lang)) {
              try {
                return window.hljs.highlight(code, { language: lang }).value;
              } catch (err) {
                console.error('Highlight error:', err);
              }
            }
            return code;
          },
          breaks: true,
          gfm: true
        });
      } else if (marked.options) {
        // 更旧版本的marked.js配置方式
        marked.options = marked.options || {};
        marked.options.breaks = true;
        marked.options.gfm = true;
      }
    }
    
    adjustTextareaHeight();
    loadHistory();
    setupEventListeners();
    
    // 等待highlight.js加载完成后初始化
    if (typeof hljs !== 'undefined') {
      initHighlightJS();
    } else {
      // 如果hljs尚未加载，设置一个监听器
      const checkHljs = setInterval(() => {
        if (typeof hljs !== 'undefined') {
          clearInterval(checkHljs);
          initHighlightJS();
        }
      }, 100);
    }
  }
  
  // 设置事件监听器
  function setupEventListeners() {
    // 移除所有内联事件处理，改为事件监听器
    elements.menuBtn.addEventListener('click', toggleSidebar);
    elements.newChatBtn.addEventListener('click', startNewChat);
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.exportBtn.addEventListener('click', exportHistory);
    
    elements.chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    
    elements.chatInput.addEventListener('input', adjustTextareaHeight);
    elements.searchHistory.addEventListener('input', searchChatHistory);
    elements.overlay.addEventListener('click', toggleSidebar);
    
    // 为建议按钮添加事件委托
    elements.chatBody.addEventListener('click', (e) => {
      if (e.target.classList.contains('suggestion')) {
        insertSuggestion(e.target);
      }
    });
  }
  
  // 调整输入框高度
  function adjustTextareaHeight() {
    elements.chatInput.style.height = 'auto';
    elements.chatInput.style.height = `${Math.min(elements.chatInput.scrollHeight, 150)}px`;
  }
  
  // 切换侧边栏
  function toggleSidebar() {
    elements.sidebar.classList.toggle('open');
    elements.overlay.classList.toggle('active');
  }
  
  // 新建会话
  function startNewChat() {
    elements.chatBody.innerHTML = `
      <div class="welcome-message">
        <img src="/assets/avatar-big.png" alt="AI Avatar" class="welcome-avatar">
        <h2>欢迎使用CF AI知识库</h2>
        <p>我可以帮助您解答各种问题，请随时提问！</p>
        <div class="suggestions">
          <div class="suggestion" data-suggestion="CF 厂长是谁，他的具体信息？">CF 厂长是谁，他的具体信息？</div>
          <div class="suggestion" data-suggestion="我是一名Repair站点新人，该如何规划学习线路？">我是一名Repair站点新人，该如何规划学习线路？</div>
          <div class="suggestion" data-suggestion="BM1 Common Defect异常原因有哪些，如何改善？">BM1 Common Defect异常原因有哪些，如何改善？</div>
        </div>
      </div>
    `;
    elements.chatInput.value = '';
    adjustTextareaHeight();
    currentSessionId = null;
  }
  
  // 插入建议
  function insertSuggestion(element) {
    elements.chatInput.value = element.dataset.suggestion || element.textContent;
    elements.chatInput.focus();
    adjustTextareaHeight();
  }
  
  // 发送消息
  // 发送消息
  async function sendMessage() {
    const message = elements.chatInput.value.trim();
    if (!message) return;
    
    appendUserMessage(message);
    elements.chatInput.value = '';
    adjustTextareaHeight();
    elements.sendBtn.disabled = true;
    
    // 创建思考卡片和消息容器
    const thinkingCard = createThinkingCard();
    let answerPanel = null;
    let retryCount = 0;
    const maxRetries = 3;
    
    // 用于流式输出的缓冲区
    let thinkingBuffer = '';
    let answerBuffer = '';
    
    const connectEventSource = () => {
      const eventSource = new EventSource(`/chat?message=${encodeURIComponent(message)}&deep_thinking=${elements.deepThinkingToggle.checked}`);
      let fullResponse = '';
      let thinkingContent = '';
      
      // 设置超时计时器（30秒）
      const timeoutTimer = setTimeout(() => {
        eventSource.close();
        appendErrorMessage('请求超时，请重试');
      }, 300000);
      
      eventSource.onmessage = (event) => {
        // 收到数据时重置超时计时器
        clearTimeout(timeoutTimer);
        
        if (event.data === '[DONE]') {
          eventSource.close();
          finalizeResponse(thinkingCard, answerPanel);
          loadHistory(); // 重新加载历史记录
          return;
        }
        
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'thinking') {
            thinkingContent += data.content;
            // 实现真正的流式输出效果
            updateThinkingContent(thinkingCard, thinkingContent);
          } 
          else if (data.type === 'content') {
            if (!answerPanel) {
              answerPanel = createAssistantMessage();
              answerPanel.classList.add('typewriter'); // 手动添加打字机效果
            }
            fullResponse += data.content;
            // 实现真正的流式输出效果
            updateAssistantMessage(answerPanel, fullResponse, true);
          }
          else if (data.type === 'thinking_stage') {
            // 处理分阶段思考过程
            updateThinkingStage(thinkingCard, data.stage, data.content);
          }
          else if (data.type === 'complete') {
            // 完成信号
            thinkingContent = data.thinking_content || thinkingContent;
            fullResponse = data.response_content || fullResponse;
            currentSessionId = data.session_id || null;
          }
          else if (data.type === 'error') {
            appendErrorMessage(data.message || '发生未知错误');
            eventSource.close();
          }
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };
      
      eventSource.onerror = (err) => {
        clearTimeout(timeoutTimer);
        eventSource.close();
        
        if (retryCount < maxRetries) {
          retryCount++;
          setTimeout(connectEventSource, 1000 * retryCount);
        } else {
          appendErrorMessage('连接失败，请检查网络后重试');
          elements.sendBtn.disabled = false;
        }
      };
    };
    
    connectEventSource();
  }
  
  // 最终处理响应
  function finalizeResponse(thinkingCard, answerPanel) {
    elements.sendBtn.disabled = false;
    
    if (answerPanel) {
      answerPanel.classList.remove('typewriter');
      answerPanel.classList.add('no-cursor'); // 添加这行来清除光标
      addResponseEndMarker(answerPanel);
      // 确保回答内容在思考卡片下方
      answerPanel.closest('.message').style.zIndex = '5';
    }
    
    if (thinkingCard) {
      const progressStages = thinkingCard.querySelectorAll('.progress-stage');
      progressStages.forEach(stage => {
        stage.classList.add('completed');
        stage.classList.remove('active');
      });
      const header = thinkingCard.querySelector('.thinking-header');
      if (header) {
        // 确保按钮始终可见
        header.innerHTML = `
          <div class="thinking-title">思考过程</div>
          <button class="thinking-toggle-btn" aria-label="展开/折叠思考内容">
            <span class="toggle-icon">▲</span>
          </button>
        `;
        
        // 重新绑定点击事件
        header.querySelector('.thinking-toggle-btn').addEventListener('click', (e) => {
          e.stopPropagation();
          thinkingCard.classList.toggle('collapsed');
          const icon = header.querySelector('.toggle-icon');
          icon.textContent = thinkingCard.classList.contains('collapsed') ? '▼' : '▲';
        });
      }
      // 默认展开
      thinkingCard.classList.remove('collapsed');
    }
  }
  
  // 添加响应结束标记
  function addResponseEndMarker(element) {
    const marker = document.createElement('div');
    marker.className = 'response-end-marker';
    marker.textContent = '───── 回答结束，可进一步提问 ─────';
    element.appendChild(marker);
  }
  
  // 创建思考卡片
  function createThinkingCard() {
    try {
      const thinkingCard = document.createElement("div");
      thinkingCard.className = 'thinking-card';
      
      thinkingCard.innerHTML = `
        <div class="thinking-header">
          <div class="thinking-title">思考过程</div>
          <button class="thinking-toggle-btn">
            <span class="toggle-icon">▼</span>
          </button>
        </div>
        <div class="thinking-body">
          <div class="thinking-content"></div>
          <div class="thinking-progress">
            <div class="progress-stage">分析问题</div>
            <div class="progress-stage">检索知识</div>
            <div class="progress-stage">构建prompt</div>
            <div class="progress-stage">生成回答</div>
          </div>
        </div>
      `;
      
      // 初始化第一个阶段为active
      const firstStage = thinkingCard.querySelector('.progress-stage');
      if (firstStage) firstStage.classList.add('active');
      
      // 事件绑定
      const toggleBtn = thinkingCard.querySelector('.thinking-toggle-btn');
      if (toggleBtn) {
        toggleBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          thinkingCard.classList.toggle('collapsed');
          const icon = toggleBtn.querySelector('.toggle-icon');
          if (icon) {
            icon.textContent = thinkingCard.classList.contains('collapsed') ? '▼' : '▲';
          }
        });
      }
      
      elements.chatBody.appendChild(thinkingCard);
      return thinkingCard;
    } catch (error) {
      console.error('Error creating thinking card:', error);
      return null;
    }
  }
  
  // 初始化highlight.js
  function initHighlightJS() {
    if (typeof hljs === 'undefined') return;
    
    hljs.configure({
      ignoreUnescapedHTML: true,
      languages: ['javascript', 'python', 'sql', 'bash', 'json', 'mermaid']
    });
    
    document.querySelectorAll('pre code').forEach((block) => {
      // 处理mermaid代码块
      if (block.classList.contains('language-mermaid')) {
        block.classList.add('language-plaintext'); // 降级为纯文本
      }
      hljs.highlightElement(block);
    });
  }
  
  // 更新思考内容
// 更新思考内容
function updateThinkingContent(thinkingCard, content) {
  if (!thinkingCard) {
    console.error('Thinking card element is null');
    return;
  }
  
  const contentElement = thinkingCard.querySelector('.thinking-content');
  if (!contentElement) {
    console.error('Thinking content element not found');
    return;
  }
  
  try {
    // 使用逐步更新的方式实现流式输出效果
    let i = 0;
    const speed = 1; // 控制流式输出速度
    
    // 清空现有内容
    contentElement.innerHTML = '';
    
    // 如果已经有内容，直接显示
    if (content) {
      // 使用一个简单的流式输出模拟
      contentElement.innerHTML = marked.parse(content);
    }
    
    thinkingCard.classList.remove('collapsed');
    
    const body = thinkingCard.querySelector('.thinking-body');
    if (body) body.scrollTop = body.scrollHeight;
    
    // 只有在生成过程中才更新进度
    if (!thinkingCard.classList.contains('completed')) {
      const progressStages = thinkingCard.querySelectorAll('.progress-stage');
      if (progressStages.length === 4) { // 确保有4个阶段
        const contentLength = content.length;
        
        progressStages[0].classList.toggle('completed', contentLength > 0);
        progressStages[1].classList.toggle('active', contentLength > 100);
        progressStages[1].classList.toggle('completed', contentLength > 200);
        progressStages[2].classList.toggle('active', contentLength > 200);
        progressStages[2].classList.toggle('completed', contentLength > 300);
        progressStages[3].classList.toggle('active', contentLength > 300);
      }
    }
  } catch (error) {
    console.error('Error updating thinking content:', error);
  }
}
  
  // 更新思考阶段
  function updateThinkingStage(thinkingCard, stage, content) {
    if (!thinkingCard) return;
    
    const progressStages = thinkingCard.querySelectorAll('.progress-stage');
    if (progressStages && progressStages[stage]) {
      progressStages[stage].classList.add('active');
      if (stage > 0) {
        progressStages[stage - 1].classList.remove('active');
        progressStages[stage - 1].classList.add('completed');
      }
    }
  }
  
  // 创建助手消息
  function createAssistantMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
      <img class="avatar" src="/assets/avatar.png"/>
      <div class="bubble"></div>  <!-- 移除了typewriter类 -->
    `;
    elements.chatBody.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv.querySelector('.bubble');
  }
  
  // 添加用户消息
  function appendUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
      <img class="avatar" src="/assets/user.jpg"/>
      <div class="bubble">${marked.parse(text)}</div>
    `;
    elements.chatBody.appendChild(messageDiv);
    
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
      welcomeMessage.remove();
    }
    
    scrollToBottom();
  }
  
  // 更新助手消息
  // 更新助手消息
  function updateAssistantMessage(panel, content, isStreaming = false) {
    // 保存当前类状态
    const isTypewriter = panel.classList.contains('typewriter');
    const hasNoCursor = panel.classList.contains('no-cursor');
    
    // 如果是流式输出，逐字符更新以获得更好的效果
    if (isStreaming) {
      panel.innerHTML = marked.parse(content);
    } else {
      panel.innerHTML = marked.parse(content);
    }
    
    // 恢复类状态
    if (isTypewriter) {
      panel.classList.add('typewriter');
    }
    if (hasNoCursor) {
      panel.classList.add('no-cursor');
    }
    
    // 高亮代码块
    if (typeof hljs !== 'undefined') {
      document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
      });
    }
    
    scrollToBottom();
  }
  // 添加错误消息
  function appendErrorMessage(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message assistant error';
    errorDiv.innerHTML = `
      <img class="avatar" src="/assets/avatar.png"/>
      <div class="bubble no-cursor">❌ ${message}</div>  <!-- 添加no-cursor类 -->
    `;
    elements.chatBody.appendChild(errorDiv);
    elements.sendBtn.disabled = false;
    scrollToBottom();
  }
  
  // 滚动到底部
  function scrollToBottom() {
    elements.chatBody.scrollTo({
      top: elements.chatBody.scrollHeight,
      behavior: 'smooth'
    });
  }
  
  // 加载历史记录
  async function loadHistory() {
    try {
      const response = await fetch('/history');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const history = await response.json();
      renderHistoryList(Array.isArray(history) ? history : []);
    } catch (error) {
      console.error('Error loading history:', error);
      renderHistoryList([]); // 确保总是传递一个数组
    }
  }
  
  // 渲染历史记录列表
  function renderHistoryList(history = []) {
    elements.historyList.innerHTML = '';
    
    if (history.length === 0) {
      const emptyItem = document.createElement('li');
      emptyItem.textContent = '暂无历史记录';
      elements.historyList.appendChild(emptyItem);
      return;
    }
    
    // 添加历史记录项
    history.forEach(chat => {
      // 确保 chat 存在
      if (!chat) {
        console.warn('Invalid chat item:', chat);
        return;
      }
      
      const listItem = document.createElement('li');
      
      listItem.innerHTML = `
        <div class="history-item" data-session-id="${chat.session_id}">
          <div class="history-content">${truncateText(chat.title, 40)}</div>
          <div class="history-preview">${chat.preview || ''}</div>
          <div class="history-time">${formatTime(chat.timestamp)}</div>
        </div>
        <button class="delete-btn" data-chat-id="${chat.id}">
          <i class="fas fa-trash"></i>
        </button>
      `;
      elements.historyList.appendChild(listItem);
    });
    
    // 在最后添加删除所有按钮
    const deleteAllItem = document.createElement('li');
    deleteAllItem.className = 'delete-all-item';
    deleteAllItem.innerHTML = `
      <button class="delete-all-btn">
        <i class="fas fa-trash"></i> 删除所有记录
      </button>
    `;
    elements.historyList.appendChild(deleteAllItem);
    
    // 添加事件委托
    elements.historyList.addEventListener('click', handleHistoryListClick);
  }
  
  // 处理历史记录列表点击事件
  function handleHistoryListClick(e) {
    if (e.target.classList.contains('delete-btn') || e.target.closest('.delete-btn')) {
      const btn = e.target.classList.contains('delete-btn') ? e.target : e.target.closest('.delete-btn');
      const chatId = btn.dataset.chatId;
      deleteChatHistory(e, chatId);
    } else if (e.target.classList.contains('delete-all-btn') || e.target.closest('.delete-all-btn')) {
      deleteAllChatHistory();
    } else if (e.target.closest('.history-item')) {
      const historyItem = e.target.closest('.history-item');
      const sessionId = historyItem.dataset.sessionId;
      viewChatHistory(sessionId);
    }
  }
  
  // 查看聊天历史
  async function viewChatHistory(sessionUuid) {
    try {
      const response = await fetch(`/history/${sessionUuid}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const chat = await response.json();
      
      if (!chat || !Array.isArray(chat.messages)) {
        throw new Error('Invalid chat data structure');
      }
      
      startNewChat();
      currentSessionId = sessionUuid;
      
      chat.messages.forEach(msg => {
        if (!msg || !msg.role || !msg.content) {
          console.warn('Invalid message:', msg);
          return;
        }
        
        if (msg.role === 'user') {
          appendUserMessage(msg.content);
        } else {
          // 修复思考卡片初始化
          if (msg.thinking_content) {
            const thinkingCard = createThinkingCard();
            if (thinkingCard) { // 确保卡片创建成功
              updateThinkingContent(thinkingCard, msg.thinking_content);
              thinkingCard.classList.remove('collapsed');
              // 标记为已完成状态
              const progressStages = thinkingCard.querySelectorAll('.progress-stage');
              progressStages.forEach(stage => stage.classList.add('completed'));
            }
          }
          
          const assistantDiv = createAssistantMessage();
          assistantDiv.classList.add('no-cursor'); // 添加no-cursor类
          updateAssistantMessage(assistantDiv, msg.content);
          addResponseEndMarker(assistantDiv);
        }
      });
      
      toggleSidebar();
      scrollToBottom();
    } catch (error) {
      console.error('Error viewing chat history:', error);
      appendErrorMessage('加载历史记录失败: ' + error.message);
    }
  }
  
  // 删除历史记录
  async function deleteChatHistory(event, chatId) {
    event.stopPropagation();
    
    if (!confirm('确定要删除这条记录吗？')) return;
    
    try {
      const response = await fetch(`/history/${chatId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        loadHistory();
      }
    } catch (error) {
      console.error('Error deleting chat history:', error);
    }
  }
  
  // 删除所有历史记录
  async function deleteAllChatHistory() {
    if (!confirm('确定要删除所有历史记录吗？此操作不可撤销！')) return;
    
    try {
      const response = await fetch('/history', {
        method: 'DELETE'
      });
      
      if (response.ok) {
        loadHistory();
      } else {
        alert('删除失败，请重试');
      }
    } catch (error) {
      console.error('Error deleting all chat history:', error);
      alert('删除失败，请检查网络连接');
    }
  }
  
  // 搜索聊天历史
  function searchChatHistory() {
    const searchTerm = elements.searchHistory.value.toLowerCase();
    const items = elements.historyList.querySelectorAll('li:not(.delete-all-item)');
    
    items.forEach(item => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(searchTerm) ? 'flex' : 'none';
    });
  }
  
  // 导出历史记录
  async function exportHistory() {
    try {
      const response = await fetch('/export');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cf-ai-history-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting history:', error);
      alert('导出历史记录失败');
    }
  }
  
  // 辅助函数
  function truncateText(text, maxLength) {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  }
  
  function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).replace(/\//g, '-');
  }
  
  // 返回公共API
  return {
    init,
    insertSuggestion,
    viewChatHistory,
    deleteChatHistory,
    deleteAllChatHistory,
    exportHistory
  };
})();

// 初始化应用
document.addEventListener('DOMContentLoaded', ChatApp.init);