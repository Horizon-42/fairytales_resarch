# 文件夹路径逻辑检查清单

## 核心原则
1. **不依赖文件夹名称假设** - 不硬编码检查 "texts"
2. **简单逻辑** - 如果 folderPath 有多个部分，使用父文件夹创建/查找 json 文件夹
3. **一致性** - 保存和载入使用相同的路径解析逻辑

## 检查点

### 1. 前端路径提取 (`extractFolderPath`)
- ✅ 从文件路径中提取文件夹路径
- ✅ 不依赖特定文件夹名称
- ✅ 返回相对路径（如 "Japanese_test2/texts2"）

### 2. 前端保存路径设置 (`loadFilesFromFolderSelection`)
- ✅ 使用 `extractFolderPath` 提取路径
- ✅ 直接设置为 `selectedFolderPath`
- ✅ 不进行额外处理

### 3. 前端保存逻辑 (`handleSave`)
- ✅ 使用 `selectedFolderPath` 和 `fileName`
- ✅ 传递给后端 `/api/save`

### 4. 前端自动保存 (`performAutoSave`)
- ✅ 使用 `selectedFolderPath` 和 `fileName`
- ✅ 依赖项包含 `selectedFolderPath`

### 5. 前端载入逻辑 (`selectStoryWithData`)
- ✅ 优先使用 `selectedFolderPath` 和 `fileName`
- ✅ Fallback 到 `originalPath`（向后兼容）

### 6. 后端路径解析 (`resolveFolderPath`)
- ✅ 处理空路径
- ✅ 处理以 "datasets/" 开头的路径
- ✅ 处理相对路径（自动添加 "datasets/" 前缀）

### 7. 后端保存逻辑 (`/api/save`)
- ✅ 如果 `folderPath` 有多个部分，使用父文件夹
- ✅ 如果 `folderPath` 只有一个部分，直接使用
- ✅ 在父文件夹中创建 json_v3/json_v2/json 文件夹

### 8. 后端载入逻辑 (`/api/load`)
- ✅ 如果 `folderPath` 有多个部分，使用父文件夹
- ✅ 如果 `folderPath` 只有一个部分，直接使用
- ✅ `originalPath` fallback 也使用相同的逻辑

## 测试场景

### 场景 1: 多级文件夹（自定义名称）
- folderPath: `Japanese_test2/texts2`
- 预期: 使用 `Japanese_test2` 作为父文件夹
- ✅ 通过测试

### 场景 2: 多级文件夹（标准名称）
- folderPath: `Japanese_test/texts`
- 预期: 使用 `Japanese_test` 作为父文件夹
- ✅ 通过测试

### 场景 3: 单文件夹
- folderPath: `MyFolder`
- 预期: 直接使用 `MyFolder`
- ✅ 通过测试

### 场景 4: 完整路径（带 datasets 前缀）
- folderPath: `datasets/Japanese_test2/texts2`
- 预期: 使用 `datasets/Japanese_test2` 作为父文件夹
- ✅ 通过测试

### 场景 5: 深层嵌套
- folderPath: `Category/SubCategory/texts`
- 预期: 使用 `Category/SubCategory` 作为父文件夹
- ✅ 通过测试

## 一致性检查

- ✅ 保存和载入使用相同的路径解析逻辑
- ✅ 自动保存使用相同的路径
- ✅ 所有路径处理都遵循相同的规则

## 潜在问题

### 已修复
- ❌ ~~硬编码检查 "texts"~~ → ✅ 已修复：使用路径部分数量判断
- ❌ ~~不一致的路径处理~~ → ✅ 已修复：统一使用父文件夹逻辑

### 注意事项
- 当 `folderPath` 只有一个部分时，json 文件夹会创建在该文件夹内部
- 当 `folderPath` 有多个部分时，json 文件夹会创建在父文件夹中
- `originalPath` fallback 主要用于向后兼容，新代码应使用 `folderPath` + `fileName`

