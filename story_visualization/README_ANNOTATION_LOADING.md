# 从 JSON v3 标注加载 Ground Truth 分割

本文档说明如何使用 JSON v3 标注文件自动加载 ground truth 分割。

## 功能说明

当选择故事时，系统会自动：
1. 加载对应的 JSON v3 标注文件（如果存在）
2. 从 `narrative_events` 中提取 `text_span`
3. 将每个 `text_span` 转换为 ground truth segment
4. 将字符偏移量转换为句子索引边界
5. 在文本上高亮显示不同的 segments

## 使用方法

### 1. 准备文件结构

确保文件夹结构如下：
```
ParentFolder/
├── texts/
│   ├── CH_002_牛郎织女.txt
│   └── ...
├── json_v3/
│   ├── CH_002_牛郎织女_v3.json
│   └── ...
```

### 2. 打开文件夹

1. 在左侧边栏点击 "Open Folder"
2. 选择包含 `texts` 和 `json_v3` 子文件夹的父文件夹

### 3. 选择故事

选择一个故事后：
- 如果存在对应的 `json_v3` 文件，会自动加载
- 如果 `narrative_events` 中有 `text_span`，会自动提取
- 文本会自动高亮显示不同的 segments

## Ground Truth Segments 可视化

### 文本高亮显示

当加载了标注后，文本会显示为：

```
[正常文本][高亮的 Segment 1][正常文本][高亮的 Segment 2]...
```

- 每个 segment 用不同的背景颜色高亮
- 鼠标悬停显示 segment 信息（Segment ID、Event Type、Description）
- 顶部图例显示所有 segments 及其句子范围

### 边界提取

系统会：
1. 从每个 `narrative_event.text_span` 提取字符偏移量
2. 将字符偏移量转换为句子索引
3. 在每个 segment 结束位置创建边界
4. 边界索引 `i` 表示句子 `i` 和 `i+1` 之间的边界

### 自动填充参考边界

- Ground truth boundaries 会自动填充到 "Reference Boundaries" 字段
- 这些边界会用于评估分割结果
- 在可视化图表中会显示（相似度矩阵中的青色虚线等）

## 数据流程

```
选择故事
  ↓
加载文本文件 (.txt)
  ↓
加载标注文件 (json_v3) (如果存在)
  ↓
解析 narrative_events
  ↓
提取 text_span (字符偏移量)
  ↓
转换为句子索引边界
  ↓
构建 ground truth segments
  ↓
高亮显示在文本上
  ↓
用于评估和可视化
```

## 技术细节

### 字符偏移到句子索引转换

`charOffsetToSentenceIndex()` 函数：
- 使用与 `splitSentences()` 相同的分割规则
- 通过在原始文本中查找句子分隔符来建立字符位置映射
- 处理字符偏移量与句子索引的对应关系

### Segment 数据结构

每个 ground truth segment 包含：
```javascript
{
  segmentId: 1,
  startChar: 0,           // 字符偏移量（开始）
  endChar: 214,           // 字符偏移量（结束）
  startSentenceIdx: 0,    // 句子索引（开始）
  endSentenceIdx: 1,      // 句子索引（结束）
  text: "...",            // Segment 文本
  eventId: "...",         // Event ID
  eventType: "OTHER",     // Event type
  description: "...",     // Event description
  timeOrder: 1            // Time order
}
```

### 边界索引说明

边界索引 `i` 表示：
- 位置：句子 `i` 和句子 `i+1` 之间
- 例如：边界 `5` 表示句子 5 和句子 6 之间的分割点

## 注意事项

1. **文件匹配**：JSON v3 文件名必须与文本文件名匹配（去掉扩展名）
   - 文本：`CH_002_牛郎织女.txt`
   - 标注：`CH_002_牛郎织女_v3.json` 或 `CH_002_牛郎织女.json`（在 json_v3 文件夹中）

2. **text_span 格式**：标注文件中的 `text_span` 必须包含：
   ```json
   {
     "text_span": {
       "start": 0,
       "end": 214,
       "text": "..."
     }
   }
   ```

3. **排序**：Segments 按 `time_order` 或 `text_span.start` 排序

4. **边界去重**：如果多个 segments 在同一位置结束，边界会被去重

## 故障排除

### Q: Segments 没有显示？

**检查：**
1. JSON v3 文件是否存在且名称匹配
2. `narrative_events` 数组中是否有 `text_span` 字段
3. 浏览器控制台是否有错误信息

### Q: 边界位置不准确？

**原因：** 可能是字符偏移量与句子分割不匹配

**解决：**
- 检查标注文件中的 `text_span` 是否正确
- 确认文本内容与标注时使用的文本一致

### Q: 没有加载标注？

**原因：**
- JSON v3 文件不在 `json_v3` 文件夹中
- 文件名不匹配（检查 ID 是否一致）
- 文件格式错误

## 未来增强

- [ ] 保存中间结果到 `post_jsons` 文件夹（需要后端 API）
- [ ] 支持手动调整边界位置
- [ ] 显示 segment 重叠或间隙的警告
- [ ] 导出 ground truth 数据为 JSON
