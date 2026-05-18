# IMPLEMENTATION_PLAN

> 本文件是 `edu-data` 项目当前状态的盘点与后续执行计划。
> 配套阅读：[`README.md`](./README.md)（业务定义 + 接口）、[`CLAUDE.md`](./CLAUDE.md)（开发原则）。
> 原则：**不重写**、**按域改**、**按阶段验收**。

---

## 目录

- [1. 项目定位与现状速览](#1-项目定位与现状速览)
- [2. 业务域划分（12 域 / 66 表）](#2-业务域划分12-域--66-表)
- [3. 代码实现盘点](#3-代码实现盘点)
- [4. 数据生成依赖顺序（Layer1 → Layer7）](#4-数据生成依赖顺序layer1--layer7)
- [5. README 与代码差异分析](#5-readme-与代码差异分析)
- [6. 分阶段执行计划](#6-分阶段执行计划)
- [7. 风险点与改进建议](#7-风险点与改进建议)
- [8. 常用命令速查](#8-常用命令速查)
- [9. 文件目录索引](#9-文件目录索引)

---

## 1. 项目定位与现状速览

`edu-data` 是一个 **在线教育业务全链路样本数据 + REST API** 工程，目标是：

- 用 **一份 SQL** 定义 66 张业务表，覆盖维度/组织/课程/题库/营销/转化/交易/履约/学习/互动/服务/经营 12 个业务域。
- 用 **分层生成器**（Layer1–Layer7）按因果顺序造出可学习、可下单、可退款、可分析的样本数据。
- 用 **FastAPI** 暴露 12 个路由共 52 个端点，模拟学员视角的完整业务交互。

| 维度 | 现状 |
|---|---|
| 代码体量 | 约 11.7k 行（生成层 ~5.0k + 校验 ~2.6k + API ~3.5k + 其他） |
| 数据库 | MySQL 8.0（`docker/docker-compose.yaml` 内置） |
| 表数 | SQL 与 README 均为 **66 张**（一一对应） |
| 端点数 | 路由实现 **52 个**，与 README §接口定义 1.1–12.5 编号一致 |
| 测试 | 5 个 `pytest` 集成测试文件 |
| 静态扫描 | 全代码无 `TODO/FIXME`；`not_implemented` 帮助函数已定义但未被调用 |

> 结论：项目处于 **"实现已覆盖、待系统性验证"** 的阶段，后续工作主线是 **验证 → 加固 → 增量补齐**，不是从零实现。

---

## 2. 业务域划分（12 域 / 66 表）

| # | 业务域 | 主代表表 | 表数 | 所属 Layer |
|---|---|---|---|---|
| 1 | 基础维度 | `dim_channel` `dim_course_category` `dim_question_type` `dim_learner_identity` `dim_grade` `dim_education_level` `dim_learning_goal` | 7 | 1 |
| 2 | 用户与组织 | `sys_user` `org_institution` `org_campus` `org_department` `org_staff_role` `staff_profile` `org_*_manager` `org_classroom` `student_profile` | 11 | 1 |
| 3 | 课程 | `series` `series_category_rel` `series_cohort` `series_cohort_course` `series_cohort_session` `session_teacher_rel` `session_asset` `session_video` `session_video_chapter` `session_homework` `session_exam` | 11 | 2 |
| 4 | 题库 | `question_bank` `question` `session_homework_question_rel` `session_exam_question_rel` | 4 | 3 |
| 5 | 营销 | `coupon` `coupon_category_rel` `coupon_series_rel` | 3 | 3 |
| 6 | 转化 | `series_exposure_log` `series_visit_log` `series_search_log` `series_favorite` `shopping_cart_item` `consultation_record` `coupon_receive_record` | 7 | 3 |
| 7 | 交易 | `order` `order_item` `payment_record` `refund_request` | 4 | 4 |
| 8 | 履约 | `student_cohort_rel` | 1 | 4 |
| 9 | 学习 | `session_attendance` `session_video_play` `session_video_play_event` `session_homework_submission` `session_exam_submission` | 5 | 5 |
| 10 | 互动 | `cohort_discussion_topic` `cohort_discussion_post` `cohort_review` | 3 | 5 |
| 11 | 服务 | `service_ticket` `service_ticket_follow_record` `service_ticket_satisfaction_survey` | 3 | 5 |
| 12 | 经营衍生 | `teacher_compensation_bill` `teacher_compensation_item` `channel_commission_bill` `channel_commission_item` `risk_alert_event` `risk_disposal_record` `ugc_moderation_task` | 7 | 6 |

合计 **66 表**，与 [`sql/edu.sql`](./sql/edu.sql) 中 66 条 `CREATE TABLE` 一致。

---

## 3. 代码实现盘点

### 3.1 数据库初始化

| 文件 | 作用 |
|---|---|
| [`init_db.py`](./init_db.py) | `DBInit` 抽象基类 + `MyInit` MySQL 实现：drop → create → exec_sql；可选反射生成 ORM |
| [`docker/docker-compose.yaml`](./docker/docker-compose.yaml) | 单节点 `mysql:8.0`，端口 3306，编码 utf8mb4 |
| [`sql/edu.sql`](./sql/edu.sql) | 66 张表定义，含枚举注释与索引 |

> `DBInit` 中的 6 处 `raise NotImplementedError` 是抽象方法占位，`MyInit` 全部 override；非实现遗留。

### 3.2 Seed 数据

| 目录 | 文件数 | 用途 |
|---|---|---|
| `seeds/1_foundation/` | 10 | 维度表 + 机构/校区/部门 |
| `seeds/2_course/` | 2 | `series.csv` 课程模板、`series_course.csv` 模块模板 |
| `seeds/3_question/` | 2 | `question_bank.csv` + `question.csv`（题库与题目模板） |

由 [`generate/layers/seed_importer.py`](./generate/layers/seed_importer.py) 解析与外键解析。

### 3.3 数据生成器（7 层）

入口：[`generate/main.py`](./generate/main.py)，支持 `--profile smoke|full`、`--layers 1,2,3,4,5,6,7`。
配置：[`generate/config.py`](./generate/config.py) 中的 `GENERATION_PROFILES`（smoke ≈ 800 用户/900 订单，full ≈ 10w 用户/8w 订单）。

| Layer | 文件 | 行数 | 关键生成方法 |
|---|---|---|---|
| 1 | [`layer1.py`](./generate/layers/layer1.py) | 713 | `generate_users / staff_roles / staff_profiles / *_managers / classrooms / student_profiles` |
| 2 | [`layer2.py`](./generate/layers/layer2.py) | 904 | series → cohort → course → session → teacher_rel / asset / video / chapter / homework / exam |
| 3 | [`layer3.py`](./generate/layers/layer3.py) | 729 | 题库挂接、coupon 与适用范围、曝光 / 访问 / 搜索 / 收藏 / 加购 / 咨询 / 领券 |
| 4 | [`layer4.py`](./generate/layers/layer4.py) | 810 | order / order_item / payment_record / refund_request / student_cohort_rel |
| 5 | [`layer5.py`](./generate/layers/layer5.py) | 1059 | 考勤 / 视频播放 / 作业 / 考试 / 讨论 / 评价 / 工单 / 满意度 |
| 6 | [`layer6.py`](./generate/layers/layer6.py) | 799 | 教师课酬 / 渠道返佣 / 风险预警 / UGC 审核 |
| 7 | [`layer7.py`](./generate/layers/layer7.py) | 16 | 调用 `validate_layer7()` 做全库验收 |

校验：[`validations.py`](./generate/layers/validations.py)（2642 行）含 `validate_layer1..7()` 七套校验。

### 3.4 API 路由（12 路由 / 52 端点）

入口：[`app/main.py`](./app/main.py)。

| 域 | 文件 | 端点数 | 主要能力 |
|---|---|---|---|
| users | [`users.py`](./app/routers/users.py) | 3 | `/me`、学员档案、学习摘要 |
| courses | [`courses.py`](./app/routers/courses.py) | 4 | 公共：series 列表/详情、班次列表/详情 |
| favorites | [`favorites.py`](./app/routers/favorites.py) | 3 | 列表/收藏/取消 |
| consultations | [`consultations.py`](./app/routers/consultations.py) | 2 | 提交/我的咨询 |
| coupons | [`coupons.py`](./app/routers/coupons.py) | 3 | 可领/领取/我的券 |
| cart | [`cart.py`](./app/routers/cart.py) | 3 | 列表/加购/移除 |
| orders | [`orders.py`](./app/routers/orders.py) | 5 | quote/创建/列表/详情/取消 |
| payments | [`payments.py`](./app/routers/payments.py) | 8 | 发起/列表/详情/关闭/mock 回调/退款发起、退款列表/详情 |
| enrollments | [`enrollments.py`](./app/routers/enrollments.py) | 4 | 我的班次/详情/课次/进度 |
| study | [`study.py`](./app/routers/study.py) | 10 | session / video / chapters / 作业 / 考试 |
| interactions | [`interactions.py`](./app/routers/interactions.py) | 2 | 评价创建/列表 |
| tickets | [`tickets.py`](./app/routers/tickets.py) | 5 | 工单 CRUD + 跟进 + 满意度 |

公共设施：
- [`app/database.py`](./app/database.py)：PyMySQL 同步连接 + cursor 上下文
- [`app/dependencies.py`](./app/dependencies.py)：`X-User-Id` 鉴权
- [`app/errors.py`](./app/errors.py)：`AppError` + 400/401/403/404/409/501 工厂
- [`app/response.py`](./app/response.py)：统一 `{code, message, data}` 结构
- [`app/utils.py`](./app/utils.py)：分页、金额、日期、JSON 解析

### 3.5 测试

| 文件 | 覆盖 |
|---|---|
| `tests/conftest.py` | `SampleData` 从真实库里拉取可复用样本（学员、班次、订单、咨询等） |
| `tests/test_users_and_courses.py` | 用户与课程查询 |
| `tests/test_conversion.py` | 收藏/咨询/优惠券/购物车 |
| `tests/test_orders_and_payments.py` | 下单/支付/退款 |
| `tests/test_learning_and_interactions.py` | 学习与评价 |
| `tests/test_tickets.py` | 工单与满意度 |

---

## 4. 数据生成依赖顺序（Layer1 → Layer7）

```
[seeds CSV]                                         ─┐
   │                                                 │
   ▼                                                 │
Layer1: 基础维度 + 组织 + 账号 + 档案                │ 完全自洽
   │                                                ─┘
   ▼
Layer2: 课程系列 → 班次 → 模块 → 课次
        → 教师关系 / 资源 / 视频 / 章节
        → 作业 / 考试                                ← 依赖 Layer1（机构、职员、教室）
   │
   ▼
Layer3: 题库挂接 → 优惠券 + 适用范围
        → 曝光 / 访问 / 搜索 / 收藏 / 加购
        → 咨询 / 领券                                ← 依赖 Layer1+2
   │
   ▼
Layer4: order → order_item → payment_record
        → refund_request → student_cohort_rel       ← 依赖 Layer3（cart/coupon/consultation）
   │
   ▼
Layer5: 考勤 / 视频播放(+events)
        作业提交 / 考试提交
        讨论主题 + 回复 / 班次评价
        工单 / 跟进 / 满意度                          ← 必须建立在 student_cohort_rel 之上
   │
   ▼
Layer6: 教师课酬 / 渠道返佣
        风险预警 + 处置
        UGC 审核任务                                 ← 依赖 Layer4 金额 + Layer5 行为
   │
   ▼
Layer7: validate_layer7() 全库验收
```

### 时间窗（README §时间跨度口径）

- 组织 / 账号：`T-1460 → T-180`
- `series`：`T-730 → T`
- `series_cohort` / `series_cohort_course` / `series_cohort_session` / `session_homework` / `session_exam`：`T-730 → T+90`
- 后续业务（转化、交易、履约、学习、互动、服务、经营衍生）无统一窗口，但必须遵循 **"前序事件早于后续事件"**。

### 不可违反的规则

1. 后层只读前层落库数据，不反查前层
2. 学习 / 互动 / 服务必须建立在 `student_cohort_rel` 上
3. 经营衍生由交易 + 履约 + 学习反推，不独立造数
4. 未来班次不应提前生成真实学习行为

---

## 5. README 与代码差异分析

### 5.1 已对齐项

- [x] SQL 表数（66）= README 表数（66）
- [x] 路由端点数（52）= README §接口定义条目数（52）
- [x] 7 个 Layer 的 Checklist 在 README 中均已勾选
- [x] 路由编号 1.1–12.5 与代码端点 URL 一一可查
- [x] `generate/config.py:LAYERS` 中各 Layer 表清单与 README §数据生成阶段说明一致

### 5.2 已确认无 stub

- 全代码搜索 **无 `TODO` / `FIXME`**
- `init_db.py` 中 6 处 `NotImplementedError` 是 `DBInit` **抽象基类占位**，`MyInit` 已 override 全部 6 个方法
- `app/errors.py:34` 的 `not_implemented()` 帮助函数定义后 **未被调用**（属于历史占位，已无遗留 stub）

### 5.3 需运行时验证的语义点

> 这些项目无法通过静态扫描确认，只能在阶段 1–2 的 smoke 验证中抽样检查。

- **业务约束符合度**：README 每张表后定义了 5–15 条业务约束（如"录播班次 `end_date` 为空、`room_id` 为空、`checkin_required=0`"），需用 `validate_layer*()` 反演
- **金额闭环**：`order.payable_amount = Σ(order_item) - 优惠`；`refund_amount <= payment_amount`
- **金额计算一致性**：`POST /orders/quote` 与 `POST /orders` 必须产出相同金额
- **支付回调副作用**：`POST /payment-notifications/mock` 是否正确回写 `order` 状态与 `student_cohort_rel.enroll_status`
- **学员档案互斥字段**：在校生只填 `grade_id`、非在校生只填 `education_level_id`（layer1 与 user router 双侧）
- **公共查询免鉴权**：`GET /series` / `/series/{id}` / `/series/{id}/cohorts` / `/cohorts/{id}` 在不带 `X-User-Id` 时应能正常返回

---

## 6. 分阶段执行计划

主线：**验证 → 加固 → 增量补齐**。每阶段都有明确出口判据，未通过前不进入下一阶段。

### 阶段 0：环境就绪（预计 0.5 天）

目标：能在本机跑通 smoke profile 全链路。

- [ ] 0.1 启动 docker：`docker compose -f docker/docker-compose.yaml up -d`
- [ ] 0.2 校验 `.env`：`DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` / `APP_PORT` / `DEMO_PAYMENT_SIGNATURE`
- [ ] 0.3 `uv sync` 安装依赖（Python 3.12+）
- [ ] 0.4 `make init_db` 检查建库建表
- [ ] 0.5 `make smoke` 跑完 Layer1–7 全部 `[OK]`

**出口判据**：smoke 跑完，`validate_layer7()` 输出全部通过；终端无 ERROR 行。

---

### 阶段 1：smoke 期校验与修复（预计 1–2 天）

目标：所有 `validate_layer*` 报错清零，pytest 全绿。

- [ ] 1.1 收集 `validate_layer1..7` 全部失败用例
- [ ] 1.2 每条失败用例追到对应生成器（`layer1..6.py`）并修复
- [ ] 1.3 `uv run pytest tests/` 全绿
- [ ] 1.4 抽样 3–5 条 `student_cohort_rel`，确认下游 attendance / video_play / submission / review 链路时间严格落在课次范围内
- [ ] 1.5 抽样 3–5 个 `order`，确认金额闭环：
  - `order.payable_amount = SUM(order_item.payable_amount)`
  - `SUM(refund_request.refund_amount) <= SUM(payment_record.payment_amount)`
- [ ] 1.6 抽样 5 个 `student_profile`，确认在校生只填 `grade_id`、非在校生只填 `education_level_id`

**出口判据**：所有 validations 通过 + pytest 全绿 + 上述 3 项抽样无反例。

---

### 阶段 2：接口语义对齐（预计 2–3 天）

目标：52 个端点全部满足 happy path + error path。

按 README §接口定义顺序逐路由验证：

- [ ] 2.1 `users`（1.1–1.3）：3 个端点
- [ ] 2.2 `courses`（2.1–2.4）：4 个公共查询，**重点验不带 `X-User-Id` 也可访问**
- [ ] 2.3 `favorites`（3.1–3.3）：3 个端点，重复收藏需返回幂等结果
- [ ] 2.4 `consultations`（4.1–4.2）：渠道归因必须为 `dim_channel` 中真实存在
- [ ] 2.5 `coupons`（5.1–5.3）：`per_user_limit=1` 必须强约束
- [ ] 2.6 `cart`（6.1–6.3）：班次必须在售
- [ ] 2.7 `orders`（7.1–7.5）：**`quote` 与 `orders` 金额必须一致**
- [ ] 2.8 `payments`（8.1–8.8）：mock 回调副作用、退款金额上限、签名校验
- [ ] 2.9 `enrollments`（9.1–9.4）：`/progress` 进度口径需对照 README §9.4
- [ ] 2.10 `study`（10.1–10.10）：视频/作业/考试访问权限校验
- [ ] 2.11 `interactions`（11.1–11.2）：评价分数范围、唯一性约束
- [ ] 2.12 `tickets`（12.1–12.5）：退款类工单必须关联 `refund_request`，满意度仅对已关闭工单

**出口判据**：每个端点至少 1 例 happy + 1 例 error 已通过；不一致项已修复或登记为后续 issue。

---

### 阶段 3：full profile 全量回归（预计 0.5 天）

目标：在生产规模数据下确认无回归。

- [ ] 3.1 `make gen`（full：10w 用户、8w 订单）
- [ ] 3.2 记录每个 Layer 的生成耗时
- [ ] 3.3 监控 MySQL 内存与磁盘
- [ ] 3.4 `validate_layer7()` 全部通过
- [ ] 3.5 抽样 10 个端点跑全量数据下的查询，记录响应时间

**出口判据**：full 跑完 + 全量 validations 通过 + 抽样端点 p95 < 1s（或登记慢查询）。

---

### 阶段 4：增量加固（按需，无固定工期）

视阶段 3 的问题清单决定优先级。

- [ ] 4.1 索引补全（按慢查询日志定位）
- [ ] 4.2 分页响应一致性 review：`page_no` / `page_size` / `total` 字段命名口径
- [ ] 4.3 把 `app/routers/*.py` 中重复 SQL 抽离到 `app/sql/` 目录
- [ ] 4.4 给 `validations.py` 每条 check 加稳定 ID 前缀，便于失败定位
- [ ] 4.5 添加 `make check` 目标：`pytest + validate_layer7` 一键体检
- [ ] 4.6 可选：在 `init_db.py:prepare()` 中启用 `output_path`，用 `sqlacodegen` 反射生成 ORM 文件

**出口判据**：每项增量按 `修改文件 / 原因 / 验证方式 / 是否影响已有逻辑`（参见 `CLAUDE.md` §9）提交。

---

## 7. 风险点与改进建议

### 风险

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| `init_db.py` 把 SQL 文件按 `;` 拆分执行 | 若未来 SQL 中字符串字面量出现 `;`，会被错误切分 | 当前 SQL 已规避；引入新 DDL 时禁止裸 `;` 在字符串中 |
| `validations.py` 2642 行集中校验 | 失败时排查成本高，难以精确定位 | 阶段 4.4：每条 check 加稳定 ID 前缀 |
| 公共查询路由（`/series` `/cohorts`）未强校验 `X-User-Id` | 鉴权策略与受保护路由不一致，易遗漏 | 用 `get_optional_current_user_id` 替代裸跳过；测试覆盖两种 header 状态 |
| Layer3 `coupon` 默认 `per_user_limit=1` 写死 | 一旦未来生成多领券模板会失效 | 把规则下沉到 `generate/config.py` 而非硬编码 |
| `payment-notifications/mock` 用 env 中的固定签名 | 容易被误用为线上接口 | 路径 `/mock` 已暗示；可加 `ENV != prod` 守卫 |
| full profile 单 MySQL 8.0 容器 | 内存峰值可能压垮容器 | 阶段 3.3 监控；必要时调 `innodb_buffer_pool_size` |

### 建议

1. **执行节奏遵循 CLAUDE.md §开发原则**：每次只改一个域，先写计划再改代码，改完汇报"文件 / 原因 / 验证 / 影响"。
2. **保留 smoke 作为 CI 基线**：smoke 跑通 + pytest 全绿可作为合并标准。
3. **建立 issue 清单**：阶段 2 中发现的 README/代码语义差异，登记为单独 issue 而非阻塞当前阶段。
4. **数据生成的可回放性**：保持 `seed=1001` 不变，重复跑同 profile 应产出可比对的结果（README §生成原则）。

---

## 8. 常用命令速查

```bash
# 环境
uv sync                                  # 安装依赖
docker compose -f docker/docker-compose.yaml up -d   # 启动 MySQL
docker compose -f docker/docker-compose.yaml down    # 停止 MySQL

# 数据
make init_db                             # 仅建库建表
make smoke                               # init_db + 生成 smoke profile（小规模）
make gen                                 # init_db + 生成 full profile（全量）
uv run -m generate.main --profile smoke  # 直接调生成器（小规模）
uv run -m generate.main --layers 5,6     # 仅重跑指定层
uv run -m generate.main --layers 7       # 仅跑最终验收

# 服务
make run                                 # 启动 FastAPI（http://127.0.0.1:8000/docs）
uv run -m app.main                       # 等价命令

# 测试
uv run pytest tests/                     # 全量集成测试
uv run pytest tests/test_orders_and_payments.py -v   # 单文件

# 清理
make clean                               # 清理 __pycache__ / logs / .venv / 缓存目录
```

---

## 9. 文件目录索引

```
edu-data/
├─ docker/
│  └─ docker-compose.yaml           # MySQL 8.0 单机
├─ sql/
│  └─ edu.sql                        # 66 张表 DDL（1541 行）
├─ seeds/
│  ├─ 1_foundation/                  # 10 个维度/组织 CSV
│  ├─ 2_course/                      # series.csv + series_course.csv
│  └─ 3_question/                    # question_bank.csv + question.csv
├─ generate/
│  ├─ main.py                        # 生成入口（--profile / --layers）
│  ├─ config.py                      # LAYERS + GENERATION_PROFILES
│  ├─ db.py                          # PyMySQL 包装
│  ├─ insert_support.py              # 批量插入工具
│  ├─ progress.py                    # rich 进度条
│  └─ layers/
│     ├─ base.py                     # BaseGenerator 抽象
│     ├─ layer1.py ~ layer6.py       # 6 层生成器
│     ├─ layer7.py                   # 最终验收（调 validations）
│     ├─ seed_importer.py            # CSV 导入与外键解析
│     └─ validations.py              # validate_layer1..7（2642 行）
├─ app/
│  ├─ main.py                        # FastAPI 入口
│  ├─ config.py                      # APP_PORT / DB_CONFIG / 签名
│  ├─ database.py                    # 同步 PyMySQL 包装
│  ├─ dependencies.py                # X-User-Id 鉴权
│  ├─ errors.py / response.py / utils.py
│  └─ routers/                       # 12 个域路由 / 52 端点
├─ tests/
│  ├─ conftest.py                    # SampleData fixture
│  └─ test_*.py                      # 5 个集成测试
├─ init_db.py                        # MySQL 初始化器（drop/create/exec/反射）
├─ Makefile                          # init_db / gen / smoke / run / clean
├─ pyproject.toml                    # 依赖（fastapi / pymysql / asyncmy / sqlacodegen 等）
├─ README.md                         # 业务定义 + 数据生成 + 接口定义（5594 行）
├─ CLAUDE.md                         # 开发原则
└─ IMPLEMENTATION_PLAN.md            # ← 本文件
```

---

**下一步**：执行 [阶段 0](#阶段-0环境就绪预计-05-天)，逐项勾选 0.1–0.5。
