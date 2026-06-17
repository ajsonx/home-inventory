# Home Inventory

家庭物品管理小工具，用来记录家里的物品、图片、分类、存放位置、归属人、有效期、价格和使用次数。

项目是前后端分离结构：

- `backend/`：Flask API，同时在生产模式托管前端构建产物
- `frontend/`：Vue 3 + Vite 前端
- `start.sh`：一键准备环境、构建前端、启动后端
- `stop.sh`：停止后台运行的服务

## 常用命令

首次启动或普通启动：

```bash
./start.sh
```

后台启动：

```bash
./start.sh -d
```

强制重新构建前端后启动：

```bash
./start.sh --rebuild
```

停止后台服务：

```bash
./stop.sh
```

启动后默认访问：

- 本机：`http://localhost:8000`
- 局域网设备：启动脚本会打印当前内网访问地址

## 数据位置

这些目录是本地运行数据，不提交 Git：

- `backend/data/`：物品、用户、分类、成就配置等 JSON 数据
- `backend/uploads/`：上传后的物品图片
- `backend/backups/`：自动备份 zip
- `backend/server.log`：后台运行日志
- `backend/server.pid`：后台进程 PID

重要数据主要在：

- `backend/data/items.json`
- `backend/data/users.json`
- `backend/data/meta.json`
- `backend/data/achievements.json`
- `backend/data/achievements_config.json`

## 备份

后端启动时会启动备份调度：

- 每月 1 号 03:00 自动备份一次
- 如果距离上次备份超过 `BACKUP_INTERVAL_DAYS`，启动时会补一次备份
- 备份内容包含 `backend/data/` 和 `backend/uploads/`
- 备份文件输出到 `backend/backups/backup_*.zip`

如果要迁移到新机器，重点带走：

```text
backend/data/
backend/uploads/
```

## 开发方式

后端单独启动：

```bash
cd backend
source .venv/bin/activate
python app.py
```

前端开发服务：

```bash
cd frontend
npm install
npm run dev
```

Vite 开发服务默认端口是 `5173`，并把 `/api`、`/uploads` 代理到 Flask 的 `8000` 端口。

前端生产构建：

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist/`，由 Flask 托管。

## 配置

主要配置在 `backend/config.py`：

- `HOST` / `PORT`：服务监听地址和端口
- `SECRET_KEY`：Flask session 密钥，可用环境变量 `HOME_ANALY_SECRET` 覆盖
- `DATA_DIR` / `UPLOAD_DIR` / `BACKUP_DIR`：数据、图片、备份目录
- `DEFAULT_LOCATIONS`：默认存放位置
- `DEFAULT_OWNERS`：默认归属人
- `DEFAULT_CATEGORIES`：默认物品分类
- `BACKUP_INTERVAL_DAYS`：启动补偿备份间隔

部署或长期使用时，建议设置自己的 session 密钥：

```bash
export HOME_ANALY_SECRET='换成自己的随机字符串'
./start.sh -d
```

## 功能备忘

- 首次使用需要创建家庭成员账号和密码
- 支持新增、编辑、删除物品
- 支持批量新增物品
- 支持上传图片，后端会压缩为缩略图
- 支持按名称、分类、位置搜索筛选
- 支持记录有效期和临期/过期物品
- 支持使用次数快捷调整
- 支持统计页
- 支持成就和维护基金领取
- 删除临期或过期物品时，会记录清理成就进度

## Git 忽略规则

已忽略依赖、构建产物和运行数据：

- `frontend/node_modules/`
- `frontend/dist/`
- `backend/.venv/`
- `backend/__pycache__/`
- `backend/data/`
- `backend/uploads/`
- `backend/backups/`
- `*.log`
- `*.pid`
- `.env*`

所以仓库只保存代码和必要配置，本地真实数据靠备份目录或手动迁移保留。
