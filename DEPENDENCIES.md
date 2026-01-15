# 依赖清单 (Dependencies)

本文档列出项目的所有依赖，确保在新机器上安装时不会遗漏。

## Python 依赖

### 后端服务 (backend/requirements.txt)

#### 核心框架依赖
```
fastapi>=0.115.0          # Web 框架
uvicorn[standard]>=0.30.0 # ASGI 服务器
pydantic>=2.8.0           # 数据验证
```

#### HTTP 和数据
```
requests>=2.32.0          # HTTP 客户端（用于调用 Ollama API 等）
python-dotenv>=1.0.0      # 环境变量管理（.env 文件）
```

#### 数值计算
```
numpy>=1.24.0             # 数值计算（文本分割、向量计算）
```

#### 文本分割依赖
```
scipy>=1.10.0             # 科学计算（Magnetic Clustering 使用 gaussian_filter1d）
networkx>=3.0             # 图论库（GraphSegSM 算法需要）
scikit-learn>=1.3.0       # 机器学习库（cosine_similarity 等）
```

#### 向量数据库（可选）
```
hnswlib>=0.8.0            # 高性能向量索引（用于 Motif/ATU 检索）
```

#### 可视化（可选，后端不直接使用，但 text_segmentation 模块需要）
```
matplotlib>=3.7.0         # 绘图库（Python 可视化模块）
seaborn>=0.12.0           # 统计可视化（Python 可视化模块）
```

### 文本分割模块 (llm_model/text_segmentation/requirements.txt)

```
numpy>=1.24.0
scipy>=1.10.0
networkx>=3.0
scikit-learn>=1.3.0
pytest>=7.4.0             # 仅用于测试
matplotlib>=3.7.0         # 可选：可视化
seaborn>=0.12.0           # 可选：可视化
```

### 项目根 (pyproject.toml)

#### 最小依赖
- `setuptools>=69` (build-system)
- `wheel` (build-system)

#### 可选依赖（vector-db）
```
requests>=2.32.0
numpy>=1.24.0
hnswlib>=0.8.0
tqdm>=4.66.0
```

## Node.js 依赖

### 前端项目 (story_visualization/package.json)

#### 运行时依赖
```json
{
  "d3": "^7.8.5",              // 数据可视化（用于图表绘制）
  "react": "^18.2.0",          // React 框架
  "react-dom": "^18.2.0",      // React DOM 渲染
  "react-router-dom": "^6.21.0" // 路由管理
}
```

#### 开发依赖
```json
{
  "@vitejs/plugin-react": "^4.2.1",  // Vite React 插件
  "vite": "^5.0.8",                  // 构建工具和开发服务器
  "vitest": "^1.6.0",                // 测试框架
  "jsdom": "^24.0.0",                // DOM 环境（用于测试）
  "@types/react": "^18.2.43",        // TypeScript 类型定义
  "@types/react-dom": "^18.2.17"     // TypeScript 类型定义
}
```

## 外部服务依赖

### Ollama（本地 LLM 服务器）

#### 必需模型
- `qwen3:8b` - LLM 模型（用于文本生成、标注等）
- `qwen3-embedding:4b` 或 `nomic-embed-text` - Embedding 模型（用于文本分割）

#### 安装
```bash
# 安装 Ollama
curl https://ollama.ai/install.sh | sh  # Linux/Mac
# 或从 https://ollama.ai 下载安装包

# 拉取模型
ollama pull qwen3:8b
ollama pull qwen3-embedding:4b
# 或
ollama pull nomic-embed-text
```

## 依赖关系图

```
项目根目录
├── Python 包 (llm_model/)
│   ├── 核心依赖
│   │   ├── requests (HTTP 客户端)
│   │   ├── python-dotenv (环境变量)
│   │   └── numpy (数值计算)
│   ├── 文本分割模块
│   │   ├── scipy (Magnetic Clustering)
│   │   ├── networkx (GraphSegSM)
│   │   ├── scikit-learn (相似度计算)
│   │   ├── matplotlib (可选：可视化)
│   │   └── seaborn (可选：可视化)
│   └── 向量数据库（可选）
│       ├── hnswlib (向量索引)
│       └── tqdm (进度条)
├── 后端服务 (backend/)
│   ├── fastapi (Web 框架)
│   ├── uvicorn (ASGI 服务器)
│   ├── pydantic (数据验证)
│   └── 继承所有 llm_model 依赖
└── 前端项目 (story_visualization/)
    ├── react + react-dom (UI 框架)
    ├── react-router-dom (路由)
    └── d3 (数据可视化)
```

## 完整安装命令

### Python 依赖

```bash
# 激活环境
conda activate nlp  # 或 source .venv/bin/activate

# 安装项目（包含最小依赖）
pip install -e .

# 安装后端依赖（包含文本分割依赖）
pip install -r backend/requirements.txt

# 验证安装
python -c "from llm_model.text_segmentation import TextSegmenter; print('OK')"
python -c "import scipy, networkx, sklearn; print('OK')"
```

### Node.js 依赖

```bash
cd story_visualization

# 安装依赖
npm install

# 验证安装
npm run build
```

## 版本兼容性

### Python
- **最低版本**: 3.9
- **推荐版本**: 3.10 或 3.11
- **测试版本**: 3.9, 3.10, 3.11

### Node.js
- **最低版本**: 18
- **推荐版本**: 20 LTS
- **测试版本**: 18, 20

### 依赖版本
所有依赖都使用 `>=` 指定最低版本，允许使用更新的版本（通常向后兼容）。

## 常见依赖问题

### Q: ImportError: No module named 'scipy'

**解决：**
```bash
pip install scipy>=1.10.0
```

### Q: ImportError: No module named 'networkx'

**解决：**
```bash
pip install networkx>=3.0
```

### Q: ImportError: No module named 'sklearn'

**解决：**
```bash
pip install scikit-learn>=1.3.0
```

### Q: Cannot find module 'd3'

**解决：**
```bash
cd story_visualization
npm install
```

### Q: Vitest tests fail with jsdom error

**解决：**
```bash
cd story_visualization
npm install --save-dev jsdom
```

## 依赖更新

### 更新 Python 依赖

```bash
# 更新所有依赖到最新兼容版本
pip install --upgrade -r backend/requirements.txt

# 或更新特定包
pip install --upgrade scipy networkx scikit-learn
```

### 更新 Node.js 依赖

```bash
cd story_visualization

# 更新到最新兼容版本（根据 package.json 的版本范围）
npm update

# 或更新特定包
npm install d3@latest react@latest
```

## 依赖锁定（生产环境）

### Python

生成依赖锁定文件：
```bash
pip freeze > requirements-lock.txt
```

使用锁定文件安装：
```bash
pip install -r requirements-lock.txt
```

### Node.js

项目已包含 `package-lock.json`，使用以下命令安装精确版本：
```bash
npm ci  # 使用 package-lock.json
```

## 最小化安装（仅核心功能）

如果不需要某些功能，可以只安装核心依赖：

### Python（最小化）

```bash
# 仅后端核心功能（不包括文本分割）
pip install fastapi uvicorn pydantic requests python-dotenv numpy

# 仅文本分割（不包括可视化）
pip install numpy scipy networkx scikit-learn
```

### Node.js（最小化）

```bash
# 仅运行时依赖（不包括测试）
npm install --production
```

## 验证清单

安装完成后，运行以下命令验证所有依赖：

```bash
# Python 依赖
python -c "import fastapi, uvicorn, pydantic, requests, numpy, scipy, networkx, sklearn; print('All Python deps OK')"

# Node.js 依赖（在 story_visualization 目录）
cd story_visualization
npm list --depth=0

# 测试后端启动
python -c "from llm_model.text_segmentation import TextSegmenter; print('TextSegmenter OK')"

# 测试前端构建
npm run build
```

## 相关文档

- [INSTALL.md](INSTALL.md) - 完整安装指南
- [README.md](README.md) - 项目总览
- [backend/README.md](backend/README.md) - 后端文档
- [story_visualization/README.md](story_visualization/README.md) - 前端文档
