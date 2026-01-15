# V3 Narrative Events 保存问题检查报告

## 检查结果

### ✅ 保存逻辑验证
- **保存代码**: `src/App.jsx` 第 949-1010 行
- **状态**: 逻辑正确
- **验证**: 
  - 正确处理 `relationship_multi` → `relationships` 数组
  - 正确处理 `action_layer` 对象
  - 确保 `agents` 和 `targets` 始终是数组
  - 不保存 flat 字段（relationship_level1, relationship_level2, sentiment, action_category 等）

### ✅ 加载逻辑验证
- **加载代码**: `src/utils/fileHandler.js` 第 444-576 行
- **状态**: 逻辑正确
- **验证**:
  - 正确从 `relationships` 数组创建 `relationship_multi`
  - 正确从 `action_layer` 提取 action 字段
  - 确保 `agents` 和 `targets` 始终是数组（即使 JSON 中是 null）

### ⚠️ 发现的问题

#### 问题 1: 部分 JSON 文件中有 null 值
- **影响文件**: 8 个文件（jp_002, jp_005, jp_006, jp_007, jp_013, jp_015, jp_017, jp_018）
- **问题**: `agents` 和 `targets` 字段为 `null` 而不是数组
- **原因**: 可能是从旧版本保存的，或保存时出现了问题
- **状态**: ✅ 已修复（使用 `fix_v3_json_files.js` 脚本）

#### 问题 2: 字符串类型事件缺少字段
- **位置**: `src/App.jsx` 第 950-956 行
- **问题**: 当 narrative 是字符串时，返回的对象缺少 `id`, `time_order`, `agents`, `targets` 等字段
- **状态**: ✅ 已修复

#### 问题 3: 加载时可能保留冗余字段
- **位置**: `src/utils/fileHandler.js` 第 542-554 行
- **问题**: 加载时如果 JSON 中有 legacy 字段，会被保留在状态中
- **状态**: ✅ 已修复（明确排除 legacy 字段）

## 修复内容

### 1. 保存逻辑增强
```javascript
// 确保字符串类型事件包含所有必要字段
if (typeof n === "string") {
  return {
    id: generateUUID(),
    text_span: null,
    event_type: "OTHER",
    description: n,
    agents: [],
    targets: [],
    target_type: "character",
    object_type: "",
    instrument: "",
    time_order: index + 1,
    relationships: [],
    action_layer: buildActionLayerV3({})
  };
}

// 确保 id 和 time_order 存在
const eventId = n.id || generateUUID();
time_order: n.time_order ?? (index + 1),
```

### 2. 加载逻辑增强
```javascript
// 确保 agents 和 targets 始终是数组
agents: agents,  // 已在前面处理为数组
targets: targets,  // 已在前面处理为数组

// 明确排除 legacy 字段
const { 
  relationships, 
  relationship_level1: _rel1, 
  relationship_level2: _rel2, 
  sentiment: _sent,
  action_category: _actCat,
  action_type: _actType,
  action_context: _actCtx,
  action_status: _actStatus,
  narrative_function: _narrFn,
  ...evtWithoutRelationships 
} = evt;
```

### 3. JSON 文件修复
- 修复了 8 个文件中的 null `agents`/`targets` 字段
- 所有文件现在都符合 v3 格式规范

## 验证结果

### ✅ 格式验证
- 所有 20 个 v3 JSON 文件格式正确
- 没有 unwanted flat 字段
- 所有必需的嵌套结构都存在

### ✅ 往返测试
- 保存/加载往返测试通过
- 没有数据丢失
- relationships 数量匹配

### ✅ 字段完整性
- 所有事件都有必需的字段
- `agents` 和 `targets` 始终是数组
- `relationships` 和 `action_layer` 结构正确

## 建议

1. **定期验证**: 运行 `test_v3_save_validation.js` 检查 JSON 文件格式
2. **保存前检查**: 确保保存逻辑始终生成正确的格式
3. **加载时清理**: 继续在加载时清理 legacy 字段，确保数据一致性

## 测试命令

```bash
# 验证所有 v3 JSON 文件
node tests/integration/test_v3_save_validation.js

# 测试保存/加载往返
node tests/integration/test_v3_save_load_roundtrip.js

# 诊断 narrative 事件
node tests/integration/test_v3_narrative_diagnosis.js
```
