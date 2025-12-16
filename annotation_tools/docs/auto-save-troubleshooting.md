# Auto-Save Troubleshooting Guide

## 问题：刷新页面后没有自动保存

### 解决步骤

#### 1. 重启服务器 ⚠️ **必须**

服务器代码已经更新，需要重启才能生效：

```bash
# 停止当前服务器 (Ctrl+C)
# 然后重新启动
cd annotation_tools
node server.js
```

或者如果使用 npm script：
```bash
npm run server
```

#### 2. 检查服务器是否运行

确保服务器在 `http://localhost:3001` 上运行。打开浏览器访问：
```
http://localhost:3001/api/save
```
应该看到错误信息（这是正常的，因为需要 POST 请求）。

#### 3. 测试自动保存

**方法 1：使用浏览器控制台**

1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签
3. 编辑一些内容
4. 刷新页面（F5）
5. 查看控制台输出，应该看到：
   ```
   Before unload triggered, attempting to save...
   ✓ Auto-saved v1 before page unload
   ✓ Auto-saved v2 before page unload
   ```

**方法 2：检查网络请求**

1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 刷新页面（F5）
4. 查找 `/api/save` 请求
5. 检查请求状态：
   - ✅ 200: 保存成功
   - ❌ 其他状态码: 查看错误信息

**方法 3：检查文件系统**

1. 编辑一些内容
2. 刷新页面
3. 检查对应的 JSON 文件是否更新了时间戳

#### 4. 常见问题排查

**问题：控制台没有输出**

可能原因：
- `beforeunload` 事件没有触发
- 事件监听器没有正确绑定
- `selectedStoryIndex === -1`（没有选择故事）

**解决方法**：
- 确保已经选择了一个故事
- 检查浏览器控制台是否有 JavaScript 错误

**问题：看到错误信息**

**错误：`Failed to fetch` 或 `Network Error`**
- 服务器没有运行
- 服务器地址不正确
- CORS 问题

**解决方法**：
- 确认服务器在 `http://localhost:3001` 运行
- 检查服务器控制台是否有错误

**错误：`400 Bad Request`**
- 请求格式不正确
- 服务器无法解析数据

**解决方法**：
- 检查服务器代码是否正确
- 确认服务器已重启

**错误：`500 Internal Server Error`**
- 服务器内部错误
- 文件写入失败

**解决方法**：
- 检查服务器控制台错误信息
- 确认文件路径和权限正确

#### 5. 手动测试自动保存功能

在浏览器控制台中运行以下代码来测试：

```javascript
// 模拟 beforeunload 事件
const testAutoSave = () => {
  const event = new Event('beforeunload');
  window.dispatchEvent(event);
};

// 运行测试
testAutoSave();
```

注意：这不会真正触发页面卸载，但可以测试事件监听器是否工作。

#### 6. 验证服务器代码

确认 `server.js` 包含以下代码：

```javascript
// 在 /api/save 端点中
app.post('/api/save', (req, res) => {
  // Handle both JSON object (from XHR) and JSON string (from sendBeacon Blob)
  let body = req.body;
  if (typeof body === 'string') {
    try {
      body = JSON.parse(body);
    } catch (err) {
      console.error('Failed to parse request body as JSON:', err);
      return res.status(400).json({ error: 'Invalid JSON in request body' });
    }
  }
  // ... rest of the code
});
```

#### 7. 浏览器兼容性

不同浏览器的行为可能不同：

- **Chrome/Edge**: 通常最可靠
- **Firefox**: 可能取消长时间运行的请求
- **Safari**: 有更严格的时间限制

如果在一个浏览器中不工作，尝试其他浏览器。

#### 8. 调试技巧

**启用详细日志**：

在 `App.jsx` 的 `handleBeforeUnload` 函数中，已经有详细的日志输出。如果看不到日志，说明事件没有触发。

**检查事件监听器**：

在浏览器控制台运行：
```javascript
// 检查事件监听器
getEventListeners(window).beforeunload
```

**强制触发保存**：

在控制台运行：
```javascript
// 直接调用保存函数（需要先选择故事）
handleSave("v1", true);
handleSave("v2", true);
```

### 如果仍然不工作

1. **检查服务器日志**：查看服务器控制台的输出
2. **检查浏览器控制台**：查看是否有 JavaScript 错误
3. **检查网络请求**：在 Network 标签中查看请求详情
4. **尝试手动保存**：确认手动保存功能正常
5. **清除浏览器缓存**：有时缓存可能导致问题

### 联系支持

如果以上步骤都无法解决问题，请提供：
- 浏览器类型和版本
- 服务器控制台输出
- 浏览器控制台错误信息
- Network 标签中的请求详情

