# 前端对接指南（失物招领系统后端）

本文面向前端开发者，包含统一响应格式、认证方式、常用接口示例、图片上传、分页筛选、状态流转等说明。

> 文档入口：Swagger `GET /docs`（本地默认 `http://127.0.0.1:8000/docs`）

---

## 1. 统一响应格式

### 1.1 成功响应

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

### 1.2 失败响应

```json
{
  "success": false,
  "code": 400,
  "message": "参数错误",
  "data": null
}
```

### 1.3 常见错误场景示例

- **未登录 / Token 无效**（通常 401）

```json
{
  "success": false,
  "code": 401,
  "message": "无法验证凭据",
  "data": null
}
```

- **权限不足**（通常 403）

```json
{
  "success": false,
  "code": 403,
  "message": "只有发布者可以修改物品",
  "data": null
}
```

- **资源不存在**（通常 404）

```json
{
  "success": false,
  "code": 404,
  "message": "物品不存在",
  "data": null
}
```

- **参数校验失败**（422）

```json
{
  "success": false,
  "code": 422,
  "message": "参数错误",
  "data": null
}
```

---

## 2. 认证方式（Bearer Token）

### 2.1 登录获取 Token

接口：`POST /auth/login`  
注意：此接口是 **表单提交**（`application/x-www-form-urlencoded`），不是 JSON。

请求示例：

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=u1&password=secret12
```

响应示例：

```json
{
  "success": true,
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "xxx.yyy.zzz",
    "token_type": "bearer"
  }
}
```

### 2.2 在需要登录的接口带上 Header

```http
Authorization: Bearer <access_token>
```

---

## 3. 常用接口请求/响应示例（JSON）

> 以下 `BASE_URL` 默认 `http://127.0.0.1:8000`

### 3.1 注册

`POST /auth/register`

请求：

```json
{
  "username": "u1",
  "email": "u1@example.com",
  "password": "secret12",
  "phone": "13800000000"
}
```

响应（示例）：

```json
{
  "success": true,
  "code": 201,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "u1",
    "email": "u1@example.com",
    "phone": "13800000000",
    "is_active": true,
    "created_at": "2026-04-13T12:00:00Z"
  }
}
```

### 3.2 获取当前用户

`GET /auth/me`（需要 Bearer）

响应：

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {
    "id": 1,
    "username": "u1",
    "email": "u1@example.com",
    "phone": null,
    "is_active": true,
    "created_at": "2026-04-13T12:00:00Z"
  }
}
```

### 3.3 发布物品

`POST /items`（需要 Bearer）

请求：

```json
{
  "title": "校园卡",
  "description": "在食堂附近丢失",
  "item_type": "lost",
  "location": "一食堂门口",
  "event_date": "2026-04-02",
  "category": "id_document",
  "image_url": null
}
```

响应：

```json
{
  "success": true,
  "code": 201,
  "message": "发布成功",
  "data": {
    "id": 1,
    "title": "校园卡",
    "description": "在食堂附近丢失",
    "item_type": "lost",
    "location": "一食堂门口",
    "event_date": "2026-04-02",
    "category": "id_document",
    "image_url": null,
    "status": "open",
    "user_id": 1,
    "claimant_id": null,
    "created_at": "2026-04-13T12:00:00Z"
  }
}
```

### 3.4 公开列表（分页 + 筛选 + 搜索 + 排序）

`GET /items`

常用查询参数：

| 参数 | 类型 | 示例 | 说明 |
|---|---|---|---|
| `page` | int | 1 | 页码，从 1 开始 |
| `page_size` | int | 20 | 每页条数（≤100） |
| `item_type` | enum | `lost`/`found` | 丢失/招领 |
| `category` | enum | `electronics` | 分类 |
| `location` | str | `图书馆` | 地点模糊搜索 |
| `event_date_from` | str | `2026-04-01` | 事件日期起 |
| `event_date_to` | str | `2026-04-30` | 事件日期止 |
| `keyword` | str | `钱包` | 关键词（同时检索 title/description/location） |
| `sort_by` | enum | `newest` | `newest/oldest/event_date` |
| `near` | str | `图书馆` | 可选：地点字符串“简易距离排序” |

响应：

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

### 3.5 我的发布

`GET /items/my/published`（需要 Bearer）

响应（示例）：

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {
    "items": [],
    "total": 0
  }
}
```

### 3.6 我认领的物品

`GET /items/my/claimed`（需要 Bearer）

响应（示例）：

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {
    "items": [],
    "total": 0
  }
}
```

---

## 4. 图片上传流程

接口：`POST /items/upload/image`（需要 Bearer）

要点：

- 请求类型：`multipart/form-data`
- 文件字段名：`file`
- 类型限制：`Content-Type` 需为 `image/*`
- 扩展名白名单：`.jpg/.jpeg/.png/.gif/.webp`
- 大小限制：≤ 5MB

响应：

```json
{
  "success": true,
  "code": 200,
  "message": "上传成功",
  "data": {
    "url": "http://127.0.0.1:8000/static/uploads/<uuid>.png"
  }
}
```

前端建议：

1. 先调用上传接口拿到 `url`
2. 再在发布物品时把 `image_url` 填为该 `url`

---

## 5. 状态流转（文字图）

物品状态 `status`：

- `open`（初始）：发布后默认状态
- `claimed`：有人认领后进入该状态（`POST /items/{id}/claim`）
- `resolved`：发布者确认已解决/已归还（`PATCH /items/{id}` 且 `status=resolved`）

流转规则：

```text
open --(任意登录用户认领 /claim)--> claimed --(发布者标记 resolved)--> resolved
```

约束：

- 不能认领自己发布的物品
- 只有发布者能将状态更新为 `resolved`
- 只有 `claimed` 的物品可以被标记为 `resolved`

