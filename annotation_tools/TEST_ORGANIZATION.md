# 测试文件重组完成

## 新的组织结构

### 目录结构

```
annotation_tools/
├── src/
│   ├── __tests__/                    # 单元测试（Vitest）
│   │   ├── components/
│   │   │   └── narrativeSectionLogic.test.js
│   │   ├── utils/
│   │   │   └── fileHandler.test.js
│   │   └── README.md
│   ├── components/
│   │   └── narrativeSectionLogic.js
│   └── utils/
│       └── fileHandler.js
│
└── tests/
    ├── integration/                  # 集成测试（Node.js）
    │   ├── test_api.js
    │   ├── test_save_load.js
    │   ├── test_merge_v2_v3.js
    │   ├── test_functionality.js
    │   ├── test_complete_load.js
    │   ├── test_simple_paths.js
    │   ├── test_version_isolation.js
    │   ├── test_load_paths.js
    │   ├── test_arbitrary_paths.js
    │   ├── test_arbitrary_folder.js
    │   ├── test_load_texts_folder.js
    │   └── test_all_paths.js
    └── README.md
```

## 重组内容

### ✅ 单元测试（已重组）
- **原位置**: `src/components/narrativeSectionLogic.test.js`
- **新位置**: `src/__tests__/components/narrativeSectionLogic.test.js`
- **原位置**: `src/utils/fileHandler.test.js`
- **新位置**: `src/__tests__/utils/fileHandler.test.js`

### ✅ 集成测试（已重组）
- **原位置**: 根目录下的 `test_*.js` 文件
- **新位置**: `tests/integration/test_*.js`
- **已更新**: 所有路径引用已修复

## 测试命令

### 单元测试
```bash
npm test              # 运行所有单元测试
npm run test:unit     # 同上
```

### 集成测试
```bash
npm run test:integration    # 运行所有集成测试
npm run test:save-load      # 运行保存/加载测试
npm run test:api            # 运行 API 测试
```

### 所有测试
```bash
npm run test:all      # 运行所有测试（单元 + 集成）
```

## 验证结果

### ✅ 单元测试
- 27 个测试全部通过
- 导入路径已更新
- 测试文件与源代码分离

### ✅ 集成测试
- 路径引用已更新
- 功能测试通过
- 所有测试文件已正确组织

## 优势

1. **清晰分离**: 单元测试和集成测试分开管理
2. **结构一致**: 测试目录结构镜像源代码结构
3. **易于维护**: 测试文件集中管理，便于查找
4. **符合标准**: 遵循 React 和 Node.js 社区最佳实践
5. **路径清晰**: 所有路径引用已更新，测试可正常运行

## 下一步

添加新测试时：
- **单元测试**: 放在 `src/__tests__/` 对应目录下
- **集成测试**: 放在 `tests/integration/` 目录下
- 记得更新 `package.json` 中的测试脚本（如需要）
