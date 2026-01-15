# 测试文件组织说明

## 目录结构

测试文件现在统一组织在 `src/__tests__/` 目录下，保持与源文件相同的目录结构：

```
src/
├── components/
│   ├── narrativeSectionLogic.js
│   └── ...
├── utils/
│   ├── fileHandler.js
│   └── ...
└── __tests__/
    ├── components/
    │   └── narrativeSectionLogic.test.js
    └── utils/
        └── fileHandler.test.js
```

## 组织原则

1. **集中管理**: 所有测试文件放在 `__tests__` 目录下，与源代码分离
2. **镜像结构**: 测试目录结构镜像源代码目录结构，便于查找对应关系
3. **清晰命名**: 测试文件使用 `.test.js` 后缀，与被测试文件同名

## 导入路径

从 `__tests__` 目录导入源文件时，使用相对路径：

- `__tests__/components/` → `../../components/`
- `__tests__/utils/` → `../../utils/`

## 运行测试

```bash
npm test
```

## 添加新测试

1. 在 `src/__tests__/` 下创建对应的目录结构
2. 创建 `*.test.js` 文件
3. 使用正确的相对路径导入源文件

## 优势

- ✅ 测试文件与源代码分离，代码更整洁
- ✅ 目录结构清晰，易于维护
- ✅ 符合 React 社区最佳实践
- ✅ 便于扩展和重构
