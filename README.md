# 失物招领系统（Lost & Found）· 后端

一个基于 **FastAPI + SQLAlchemy 2.0 Async + JWT** 的失物招领后端服务，提供用户认证、物品发布与筛选搜索、认领与结案、图片上传等能力，并统一 API 响应格式，方便前端快速对接。

---

## 功能特性（Features）

- ✅ **用户注册/登录**（OAuth2 Password + JWT）
- ✅ **密码安全**（`bcrypt` 哈希）
- ✅ **物品发布/编辑/删除**（发布者权限校验）
- ✅ **公开列表筛选 + 分页**（类型/分类/地点模糊/日期范围/关键词）
- ✅ **搜索增强**：关键词同时检索 `title/description/location`
- ✅ **排序**：最新/最早/按事件日期；可选 `near` 简易地点排序（字符串匹配，便于后续升级真实距离）
- ✅ **认领流程**：`open → claimed`，记录 `claimant_id`
- ✅ **发布者结案**：将已认领物品标记 `resolved`
- ✅ **我的列表**：我的发布、我认领的物品（登录后分页）
- ✅ **图片上传**：严格类型/大小校验（5MB），返回可访问 URL（本地静态目录占位）
- ✅ **统一 API 响应**：成功/失败统一 JSON 结构
- ✅ **CORS 开启**：开发期允许任意来源
- ✅ **Alembic 迁移**：支持 SQLite（开发）/ PostgreSQL（生产）切换

---

## 技术栈

| 分类 | 技术 |
|---|---|
| 语言 | Python 3.12 |
| Web 框架 | FastAPI（最新版） |
| ORM | SQLAlchemy 2.0（AsyncSession / async engine） |
| 迁移 | Alembic |
| 数据校验 | Pydantic v2 + pydantic-settings |
| 认证 | PyJWT + OAuth2PasswordBearer |
| 密码哈希 | passlib[bcrypt] |
| 上传 | python-multipart |
| 数据库 | PostgreSQL（推荐）/ SQLite（开发） |

---

## 项目结构说明

```text
lost-found/
├── README.md                  # 你正在看的文档（根目录）
├── alembic.ini                # Alembic 配置（根目录执行）
├── .env                       # 环境变量（根目录）
├── app/
│   ├── main.py                # FastAPI 入口：路由注册/中间件/全局异常
│   ├── requirements.txt       # 依赖列表
│   ├── .env.example           # 环境变量示例
│   ├── core/                  # 配置、数据库连接、统一响应
│   ├── models/                # SQLAlchemy ORM 模型
│   ├── schemas/               # Pydantic Schema（含统一响应）
│   ├── crud/                  # 数据访问层（含筛选/分页/排序/我的列表查询）
│   ├── routers/               # API 路由：auth/items
│   ├── dependencies/          # 依赖注入：get_current_user
│   ├── utils/                 # 工具：分页解析
│   └── alembic/               # 迁移脚本目录（versions 在此）
└── uploads/                   # 上传目录（运行后自动创建）
```

---

## 快速启动（Windows / PowerShell）

> ⚠️ 注意：PowerShell 激活 venv 的命令是 `.\.venv\Scripts\Activate.ps1`，中间**不能有空格**。

在 **项目根目录**（`lost-found/`）执行：

```powershell
cd C:\Users\jia\Desktop\lost-found

# 1) 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) 安装依赖
pip install -r app/requirements.txt

# 3) 配置环境变量
Copy-Item -Force app\.env.example .env

# 4) 初始化/升级数据库（SQLite 默认 dev.db）
alembic upgrade head

# 5) 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

---

## 环境变量说明（`.env` 全字段）

> `.env` 位于 **项目根目录**（与 `alembic.ini` 同级）。`pydantic-settings` 会自动加载。

| 变量名 | 示例值 | 必填 | 说明 |
|---|---:|:---:|---|
| `APP_NAME` | `失物招领系统` | 否 | OpenAPI 标题/应用名 |
| `DEBUG` | `false` | 否 | 调试模式（建议生产 `false`） |
| `SECRET_KEY` | `please-change-me...` | ✅ | JWT 签名密钥（生产务必更换） |
| `ALGORITHM` | `HS256` | 否 | JWT 算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 否 | Token 过期时间（分钟） |
| `DATABASE_URL` | `sqlite+aiosqlite:///dev.db` | ✅ | 异步数据库 URL（SQLite/PG） |
| `UPLOAD_DIR` | `./uploads` | 否 | 上传文件落盘目录（占位实现） |
| `PUBLIC_UPLOAD_BASE_URL` | `http://127.0.0.1:8000/static/uploads` | 否 | 上传文件对外访问 URL 前缀 |

### `DATABASE_URL` 示例

- **SQLite（开发）**

```ini
DATABASE_URL=sqlite+aiosqlite:///dev.db
```

- **PostgreSQL（生产/联调）**

```ini
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/lost_found
```

> Alembic 会自动将 `postgresql+asyncpg` 推导为 `postgresql+psycopg` 来执行迁移（同步驱动）。

---

## 统一 API 响应格式

所有接口（含 `auth`、`items`）都遵循：

成功：

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": { }
}
```

失败：

```json
{
  "success": false,
  "code": 400,
  "message": "参数错误",
  "data": null
}
```

> 校验失败（422）会返回 `code=422`，并统一 `message=参数错误`。

---

## API 接口文档（主要接口 + 示例）

### 在线文档

- Swagger：`GET /docs`
- OpenAPI JSON：`GET /openapi.json`

### 认证与用户

- `POST /auth/register`：注册
- `POST /auth/login`：登录（表单提交，返回 JWT）
- `GET /auth/me`：当前用户信息（需要 Bearer）

**示例：注册**

```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"u1","email":"u1@example.com","password":"secret12","phone":null}'
```

**示例：登录（拿 token）**

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=u1&password=secret12"
```

返回 `data.access_token` 后，用于：

```text
Authorization: Bearer <access_token>
```

### 物品（Items）

- `POST /items`：发布物品（登录）
- `GET /items`：公开列表（筛选 + 搜索 + 排序 + 分页）
- `GET /items/{item_id}`：物品详情
- `PATCH /items/{item_id}`：更新（仅发布者；可将 `status` 设为 `resolved`）
- `DELETE /items/{item_id}`：删除（仅发布者）
- `POST /items/{item_id}/claim`：认领（登录；不可认领自己发布的）
- `GET /items/my/published`：我的发布（登录；分页）
- `GET /items/my/claimed`：我认领的物品（登录；分页）

**示例：公开列表查询（带排序与关键词）**

```bash
curl "http://127.0.0.1:8000/items?page=1&page_size=20&keyword=钱包&sort_by=newest"
```

**示例：按事件日期排序 + 简易地点 near**

```bash
curl "http://127.0.0.1:8000/items?sort_by=event_date&near=图书馆"
```

**示例：我的发布（需要 token）**

```bash
curl "http://127.0.0.1:8000/items/my/published?page=1&page_size=20" \
  -H "Authorization: Bearer <access_token>"
```

### 图片上传

- `POST /items/upload/image`（登录，`multipart/form-data`，字段名 `file`）
- 限制：**只允许 `image/*`，扩展名白名单，最大 5MB**

上传成功会返回图片 URL（可回填到 `image_url`）：

```json
{
  "success": true,
  "code": 200,
  "message": "上传成功",
  "data": { "url": "http://127.0.0.1:8000/static/uploads/xxx.png" }
}
```

---

## 数据库迁移命令（Alembic）

在 **根目录**执行：

```bash
# 升级到最新
alembic upgrade head

# 生成迁移（模型变更后）
alembic revision --autogenerate -m "your message"

# 回退一个版本
alembic downgrade -1
```

> ⚠️ 建议：提交代码前确保迁移脚本内容不是空的（避免出现只有 `pass` 的迁移文件）。

---

## 部署建议（Docker 预告）

> 目前项目已为 Docker 化做好准备（环境变量集中在 `.env`、数据库 URL 可切换）。

建议后续加入：

- `Dockerfile`（生产镜像，使用 `uvicorn`/`gunicorn`）
- `docker-compose.yml`（FastAPI + PostgreSQL + 管理工具）
- 反向代理：Nginx / Caddy
- 持久化：挂载 `UPLOAD_DIR`（或接入对象存储）

---

## 前端对接注意事项

- **统一响应**：前端建议封装一个通用解析器，只读 `success/code/message/data`。
- **鉴权**：需要登录的接口统一使用 `Authorization: Bearer <token>`。
- **登录接口**：`/auth/login` 是 **表单提交**（`application/x-www-form-urlencoded`），不是 JSON。
- **上传接口**：`multipart/form-data`，字段名必须是 `file`。
- **CORS**：开发期已放开 `*`，生产建议收敛 `allow_origins`。

---

## 后续计划（Roadmap）

- [ ] Docker / Compose 一键启动（FastAPI + PostgreSQL）
- [ ] 更真实的“距离排序”（地理坐标 / PostGIS / 地图服务）
- [ ] 图片存储对接：S3/OSS/Cloudinary（替换本地静态目录）
- [ ] 物品状态流转更完善（例如撤销认领、管理员审核等）
- [ ] 接口测试与 CI（pytest + httpx + GitHub Actions）
- [ ] 性能与索引优化（关键词索引、全文检索）

