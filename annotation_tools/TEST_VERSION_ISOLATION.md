# Version Isolation Test Documentation

## 测试目的

验证 v1、v2、v3 三个版本的 JSON 生成逻辑完全隔离，确保：
1. v1 JSON 不包含任何 v3 特定字段
2. v2 JSON 不包含任何 v3 特定字段
3. v3 JSON 不包含任何 v1/v2 扁平字段
4. 每个版本的生成逻辑完全独立

## 测试逻辑

### 1. v1 JSON 生成测试

**测试数据**：包含混合字段的事件对象（既有 v1/v2 扁平字段，也有 v3 嵌套字段）

**验证点**：
- ✅ **不应包含** v3 字段：
  - `relationship_multi` ❌
  - `relationships` ❌
  - `action_layer` ❌
- ✅ **应包含** v1 扁平字段：
  - `relationship_level1` ✅
  - `relationship_level2` ✅
  - `sentiment` ✅
  - `action_category` ✅
  - `action_type` ✅
  - `action_context` ✅
  - `action_status` ✅
  - `narrative_function` ✅

**生成逻辑**：
```javascript
const v1Result = {
  id: n.id,
  text_span: n.text_span,
  event_type: n.event_type || "",
  // ... 只使用扁平字段
  relationship_level1: n.relationship_level1 || "",
  relationship_level2: n.relationship_level2 || "",
  sentiment: n.sentiment || "",
  action_category: n.action_category || "",
  // ... 不访问任何 v3 字段
};
```

### 2. v2 JSON 生成测试

**测试数据**：与 v1 相同

**验证点**：
- ✅ **不应包含** v3 字段：
  - `relationship_multi` ❌
  - `relationships` ❌
  - `action_layer` ❌
- ✅ **应包含** v2 扁平字段（与 v1 相同）：
  - `relationship_level1` ✅
  - `relationship_level2` ✅
  - `sentiment` ✅
  - `action_category` ✅
  - `action_type` ✅
  - `action_context` ✅
  - `action_status` ✅
  - `narrative_function` ✅

**生成逻辑**：
```javascript
const v2Result = {
  id: n.id,
  text_span: n.text_span,
  event_type: n.event_type || "",
  // ... 只使用扁平字段
  relationship_level1: n.relationship_level1 || "",
  relationship_level2: n.relationship_level2 || "",
  sentiment: n.sentiment || "",
  action_category: n.action_category || "",
  // ... 不访问任何 v3 字段
};
```

### 3. v3 JSON 生成测试

**测试数据**：与 v1/v2 相同

**验证点**：
- ✅ **应包含** v3 嵌套结构：
  - `relationships` 数组 ✅
  - `action_layer` 对象 ✅
- ✅ **不应包含** v1/v2 扁平字段：
  - `relationship_level1` ❌
  - `relationship_level2` ❌
  - `sentiment` ❌
  - `action_category` ❌
  - `action_type` ❌
  - `action_context` ❌
  - `action_status` ❌
  - `narrative_function` ❌
  - `relationship_multi` ❌

**生成逻辑**：
```javascript
// v3 从 UI 状态提取数据（可能来自 relationship_multi 或扁平字段）
const existingMultiList = Array.isArray(n.relationship_multi) ? n.relationship_multi : [];
let relList = [];
if (existingMultiList.length > 0) {
  relList = existingMultiList.map(normalizeRelEntry);
} else if (n.relationship_level1 || n.relationship_level2 || n.sentiment) {
  // 从扁平字段提取（仅用于转换，不保存在输出中）
  relList = [normalizeRelEntry({...})];
}

const v3Result = {
  id: n.id,
  text_span: n.text_span,
  event_type: n.event_type || "",
  // ... 只使用嵌套结构
  relationships: relList,  // ✅ v3 嵌套结构
  action_layer: buildActionLayerV3(n)  // ✅ v3 嵌套结构
  // 不包含任何扁平字段
};
```

### 4. 实际保存文件测试

**测试方法**：
- 读取实际保存的 JSON 文件
- 检查文件中的事件对象字段
- 验证是否符合对应版本的规范

**测试文件**：
- `datasets/ChineseTales/json/CH_003_孟姜女哭长城.json` (v1)
- `datasets/ChineseTales/json_v2/CH_003_孟姜女哭长城_v2.json` (v2)
- `datasets/ChineseTales/json_v3/CH_003_孟姜女哭长城_v3.json` (v3)

## 隔离保证

### v1/v2 生成逻辑隔离

**关键点**：
1. **显式构造对象**：不使用 `{ ...n }` 复制所有字段
2. **只访问扁平字段**：只读取 `n.relationship_level1`, `n.relationship_level2` 等
3. **不访问 v3 字段**：不读取 `n.relationship_multi`, `n.relationships`, `n.action_layer`
4. **删除保护**：即使意外包含，也会显式删除

```javascript
// v1/v2 生成逻辑（完全隔离）
const result = {
  // 显式列出所有需要的字段
  relationship_level1: n.relationship_level1 || "",
  relationship_level2: n.relationship_level2 || "",
  // ... 不访问 n.relationship_multi 或 n.relationships
};

// 显式删除 v3 字段（双重保护）
delete result.relationship_multi;
delete result.relationships;
delete result.action_layer;
```

### v3 生成逻辑隔离

**关键点**：
1. **显式构造对象**：不使用 `{ ...n }` 复制所有字段
2. **只包含嵌套结构**：只保存 `relationships` 和 `action_layer`
3. **不包含扁平字段**：不保存 `relationship_level1`, `action_category` 等

```javascript
// v3 生成逻辑（完全隔离）
const v3Result = {
  // 显式列出所有需要的字段
  relationships: relList,  // ✅ 嵌套结构
  action_layer: actionLayer  // ✅ 嵌套结构
  // 不包含任何扁平字段
};
```

## 运行测试

```bash
cd annotation_tools
node test_version_isolation.js
```

## 测试结果示例

```
============================================================
Testing Version Isolation Logic
============================================================

=== Testing v1 JSON Generation ===
v1 Result keys: ['id', 'text_span', 'event_type', ..., 'relationship_level1', 'relationship_level2', ...]
Has relationship_multi: false ✅ PASS
Has relationships: false ✅ PASS
Has action_layer: false ✅ PASS
Has required flat fields: true ✅ PASS

=== Testing v2 JSON Generation ===
v2 Result keys: ['id', 'text_span', 'event_type', ..., 'relationship_level1', 'relationship_level2', ...]
Has relationship_multi: false ✅ PASS
Has relationships: false ✅ PASS
Has action_layer: false ✅ PASS
Has required flat fields: true ✅ PASS

=== Testing v3 JSON Generation ===
v3 Result keys: ['id', 'text_span', 'event_type', ..., 'relationships', 'action_layer']
Has relationships: true ✅ PASS
Has action_layer: true ✅ PASS
Has relationship_level1: false ✅ PASS
Has relationship_level2: false ✅ PASS
Has sentiment: false ✅ PASS
Has action_category: false ✅ PASS
Has action_type: false ✅ PASS
Has relationship_multi: false ✅ PASS

============================================================
Test Results Summary
============================================================
v1 Generation Test: ✅ PASS
v2 Generation Test: ✅ PASS
v3 Generation Test: ✅ PASS
Saved Files Test: ✅ PASS

Overall: ✅ ALL TESTS PASSED
```

## 关键隔离机制

1. **显式字段构造**：每个版本只构造自己需要的字段，不使用展开运算符复制所有字段
2. **字段访问限制**：v1/v2 不访问 v3 字段，v3 不保存 v1/v2 字段
3. **双重保护**：即使意外包含，也会显式删除
4. **独立逻辑**：每个版本的生成逻辑完全独立，不共享代码


