# 测试文件组织说明

## 目录结构

```
annotation_tools/
├── src/
│   ├── __tests__/              # 单元测试（Vitest）
│   │   ├── components/
│   │   │   └── narrativeSectionLogic.test.js
│   │   ├── utils/
│   │   │   └── fileHandler.test.js
│   │   └── README.md
│   ├── components/
│   ├── utils/
│   └── ...
└── tests/
    ├── integration/            # 集成测试（Node.js）
    │   ├── test_api.js
    │   ├── test_save_load.js
    │   ├── test_merge_v2_v3.js
    │   ├── test_functionality.js
    │   └── ...
    └── README.md
```

## 测试类型

### 单元测试 (Unit Tests)
- **位置**: `src/__tests__/`
- **框架**: Vitest
- **运行**: `npm test` 或 `npm run test:unit`
- **特点**: 
  - 测试单个函数/组件
  - 快速执行
  - 与源代码目录结构镜像

### 集成测试 (Integration Tests)
- **位置**: `tests/integration/`
- **框架**: Node.js (原生)
- **运行**: `npm run test:integration` 或 `npm run test:save-load`
- **特点**:
  - 测试完整功能流程
  - 可能需要服务器运行
  - 测试 API 端点、文件操作等

## 运行测试

```bash
# 运行所有单元测试
npm test
# 或
npm run test:unit

# 运行集成测试
npm run test:integration

# 运行特定集成测试
npm run test:save-load
npm run test:api

# 运行所有测试
npm run test:all
```

## 添加新测试

### 添加单元测试
1. 在 `src/__tests__/` 下创建对应的目录结构
2. 创建 `*.test.js` 文件
3. 使用相对路径导入源文件（如 `../../components/Component.jsx`）

### 添加集成测试
1. 在 `tests/integration/` 下创建测试文件
2. 使用 `path.resolve(__dirname, '..', '..')` 获取项目根目录
3. 更新 `package.json` 中的测试脚本（如需要）

## 路径引用

### 单元测试中的路径
```javascript
// 从 __tests__/components/ 导入源文件
import { function } from "../../components/Component.jsx";
```

### 集成测试中的路径
```javascript
// 获取项目根目录
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

// 访问源文件
const srcPath = path.join(PROJECT_ROOT, 'src', 'file.js');

// 访问数据集
const dataPath = path.join(PROJECT_ROOT, 'datasets', 'folder');
```

## 优势

- ✅ **清晰分离**: 单元测试和集成测试分开管理
- ✅ **结构一致**: 测试目录结构镜像源代码结构
- ✅ **易于维护**: 测试文件集中管理，便于查找和维护
- ✅ **符合最佳实践**: 遵循 React 和 Node.js 社区标准
