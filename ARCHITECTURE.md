# UnitCalc 技术架构文档

## 1. 系统概述

### 1.1 工具定位

UnitCalc 是一个基于 Python 实现的终端单位换算与物理常数查询工具，支持 REPL 交互模式和命令行单次执行模式。核心功能涵盖：长度、重量、体积、温度、速度、压力、时间、数据存储、带宽等多维度单位换算，货币汇率换算，物理常数查询，日期时间计算，以及自定义单位、历史记录、收藏夹等辅助功能。

### 1.2 支持的命令列表

| 命令 | 功能描述 |
|------|----------|
| `convert` | 单位换算（支持表达式、复合单位、加减运算） |
| `calc` | 带单位四则运算表达式求值 |
| `transfer` | 文件传输时间计算（数据大小 / 带宽） |
| `constants` | 物理常数库（列表/搜索/详情） |
| `define` | 定义自定义单位 |
| `list-custom` | 查看自定义单位列表 |
| `date` | 日期时间工具（差值、时间戳、工作日、时区转换） |
| `currency` | 货币汇率换算 |
| `history` | 历史记录查看与清空 |
| `favorite` | 命令收藏与快速运行 |
| `help` | 显示帮助信息 |

### 1.3 代码统计

- **总代码行数**：1656 行（含空行和注释）
- **函数数量**：40 个
- **文件大小**：单文件架构，所有逻辑集中于 `unitcalc.py`
- **依赖**：仅使用 Python 标准库（sys, json, os, math, re, datetime, pathlib）

---

## 2. 模块划分

代码按职责可划分为以下 7 个逻辑模块：

### 2.1 数据定义层

**职责**：定义所有静态数据常量，包括配置路径、默认汇率、各类单位字典、别名映射、物理常量表等。属于纯数据层，无业务逻辑。

**包含内容**：

| 变量/常量 | 行号范围 | 职责描述 |
|-----------|----------|----------|
| `CONFIG_DIR` / `CONFIG_FILE` / `RATES_FILE` / `HISTORY_FILE` / `FAVORITES_FILE` | L10-L14 | 配置文件路径定义 |
| `DEFAULT_RATES` | L16-L43 | 默认汇率数据（基准货币 USD，10 种常见货币） |
| `CURRENCY_CODES` | L45 | 货币代码集合 |
| `LENGTH_UNITS` | L47-L59 | 长度单位字典（12 种） |
| `WEIGHT_UNITS` | L61-L71 | 重量单位字典（9 种） |
| `VOLUME_UNITS` | L73-L84 | 体积单位字典（10 种） |
| `TEMPERATURE_UNITS` / `TEMP_NAMES` | L86-L90 | 温度单位集合及别名 |
| `SPEED_UNITS` | L92-L98 | 速度单位字典（5 种） |
| `PRESSURE_UNITS` | L100-L108 | 压力单位字典（7 种） |
| `DATA_UNITS_BASE2` | L110-L118 | 二进制数据存储单位（1024 进制） |
| `DATA_UNITS_BASE10` | L120-L128 | 十进制数据存储单位（1000 进制） |
| `BANDWIDTH_UNITS` | L130-L135 | 带宽单位字典（4 种） |
| `TIME_UNITS` | L137-L145 | 时间单位字典（7 种） |
| `UNIT_CATEGORIES` | L147-L154 | 单位类别总表（线性可换算的 6 大类） |
| `ALL_LINEAR_UNITS` | L156-L162 | 所有线性单位合并字典（便于统一查找） |
| `ALIAS_MAP` | L164-L193 | 单位别名映射表（别名 → 标准键名） |
| `PHYSICAL_CONSTANTS` | L436-L467 | 物理常量表（29 个常数，分 7 个领域） |

### 2.2 单位解析层

**职责**：负责单位名称的识别、别名解析、类别判定、复合单位拆解，以及单位因子的获取。

| 函数名 | 行号范围 | 职责描述 |
|--------|----------|----------|
| `resolve_unit` | L519-L521 | 通过别名映射查找单位标准键名 |
| `find_unit_category` | L524-L534 | 查找单位所属类别（长度/重量/温度/数据/带宽等） |
| `parse_compound_unit` | L210-L222 | 解析复合单位（如 km/h），拆解为分子和分母单位 |
| `get_unit_factor_and_cat` | L225-L243 | 获取单位的换算因子及类别（支持自定义单位、线性单位、温度、数据、带宽） |
| `get_unit_display_name` | L246-L254 | 获取单位的中文显示名称 |

### 2.3 换算引擎层

**职责**：实现各类单位之间的实际换算逻辑，包括线性换算、温度特殊换算、复合单位换算等。

| 函数名 | 行号范围 | 职责描述 |
|--------|----------|----------|
| `convert_temperature` | L487-L504 | 温度单位转换（摄氏度/华氏度/开尔文） |
| `get_temp_formula` | L507-L516 | 获取温度换算的公式描述文本 |
| `convert_compound` | L257-L271 | 复合单位换算（如 km/h → m/s） |
| `do_convert_simple` | L553-L692 | 单一单位换算的核心实现（处理自定义单位、温度、数据、带宽、普通线性单位），并负责输出格式化 |
| `format_number` | L470-L484 | 数值格式化（根据大小自动选择科学计数法/千分位/小数位数） |
| `format_duration` | L1219-L1238 | 时间时长格式化（微秒/毫秒/秒/分/时/天） |

### 2.4 表达式求值引擎层

**职责**：解析并计算带单位的数学表达式，支持四则运算、括号、正负号。

| 函数名 | 行号范围 | 职责描述 |
|--------|----------|----------|
| `safe_eval_expr` | L196-L207 | 安全的纯数值表达式求值（白名单字符过滤 + 受限 eval） |
| `tokenize_expr` | L287-L326 | 表达式分词器，将字符串拆分为 token 列表 |
| `parse_value_with_unit` | L274-L284 | 解析带单位的 token（数值+单位组合） |
| `eval_unit_expr` | L329-L433 | 带单位表达式求值器（基于栈的运算符优先级算法） |

### 2.5 命令处理层

**职责**：各个子命令的具体实现，负责参数解析、业务逻辑编排、结果输出。

| 函数名 | 行号范围 | 职责描述 |
|--------|----------|----------|
| `dispatch_command` | L1143-L1168 | 命令分发器，根据命令名路由到对应处理函数 |
| `do_convert` | L695-L827 | convert 命令处理（表达式换算 + 简单换算双路径） |
| `do_calc` | L830-L880 | calc 命令处理（带单位表达式计算） |
| `do_transfer_time` | L1171-L1216 | transfer 命令处理（传输时间计算） |
| `do_currency` | L903-L985 | currency 命令处理（汇率换算/汇率表/更新） |
| `do_constants` | L1241-L1286 | constants 命令处理（列表/搜索/详情） |
| `do_define` | L1289-L1317 | define 命令处理（自定义单位定义） |
| `do_list_custom` | L1320-L1336 | list-custom 命令处理（自定义单位列表） |
| `do_date` | L1339-L1478 | date 命令处理（差值/时间戳/工作日/时区转换） |
| `parse_date` | L1481-L1490 | 日期字符串解析 |
| `parse_datetime` | L1493-L1499 | 日期时间字符串解析 |
| `parse_tz_offset` | L1502-L1513 | 时区偏移量解析 |
| `do_history` | L1011-L1043 | history 命令处理（查看/清空） |
| `do_favorite` | L1062-L1140 | favorite 命令处理（列表/添加/删除/运行） |
| `do_help` | L1516-L1577 | help 命令处理（帮助信息输出） |

### 2.6 持久化层

**职责**：所有与文件读写相关的操作，包括自定义单位、汇率、历史记录、收藏夹的持久化。

| 函数名 | 行号范围 | 职责描述 |
|--------|----------|----------|
| `load_custom_units` | L537-L544 | 加载自定义单位配置 |
| `save_custom_units` | L547-L550 | 保存自定义单位配置 |
| `load_rates` | L883-L894 | 加载汇率数据 |
| `save_rates` | L897-L900 | 保存汇率数据 |
| `record_history` | L988-L1008 | 记录命令历史（最多 50 条） |
| `load_favorites` | L1046-L1053 | 加载收藏夹 |
| `save_favorites` | L1056-L1059 | 保存收藏夹 |

### 2.7 入口层

**职责**：程序入口、交互模式循环、输入解析。

| 函数名 | 行号范围 | 职责描述 |
|--------|----------|----------|
| `main` | L1629-L1652 | 主入口函数（判断命令行/REPL 模式） |
| `repl_mode` | L1616-L1626 | REPL 交互模式主循环 |
| `parse_repl_input` | L1579-L1612 | REPL 输入解析与分发 |

---

## 3. 核心数据流

### 3.1 以 "convert 100 cm + 2 m to inches" 为例的完整调用链路

```
命令行输入: "convert 100 cm + 2 m to inches"
    │
    ▼
main()  [L1629]
    │  sys.argv 解析：cmd="convert", args=["100","cm","+","2","m","to","inches"]
    ▼
dispatch_command(cmd, args)  [L1143]
    │  路由到 do_convert
    ▼
do_convert(args)  [L695]
    │
    ├─ 1. 加载自定义单位: load_custom_units()  [L537]
    │
    ├─ 2. 查找 "to" 分隔符位置 (sep_idx=5)
    │   from_part_str = "100 cm + 2 m"
    │   to_name = "inches"
    │
    ├─ 3. 解析目标单位
    │   ▼
    │   parse_compound_unit("inches")  [L210]
    │       │  非复合单位，走 single 分支
    │       ▼
    │       resolve_unit("inches")  [L519]
    │           │  ALIAS_MAP["inches"] → "in"
    │           ▼
    │       返回 ("single", "in", "inches")
    │
    ├─ 4. 表达式求值（核心路径）
    │   ▼
    │   eval_unit_expr("100 cm + 2 m", custom, use_base10)  [L329]
    │       │
    │       ├─ 4.1 分词
    │       │   ▼
    │       │   tokenize_expr("100 cm + 2 m")  [L287]
    │       │       │  逐字符扫描
    │       │       │  - "100" → 数字 token
    │       │       │  - "cm"  → 字母 token
    │       │       │  - "+"   → 运算符 token
    │       │       │  - "2"   → 数字 token
    │       │       │  - "m"   → 字母 token
    │       │       ▼
    │       │   返回 tokens = ["100", "cm", "+", "2", "m"]
    │       │
    │       ├─ 4.2 Token 合并（数字+单位合并）
    │       │   │  遍历 tokens：
    │       │   │  - "100" 是数字，"cm" 是单位 → 合并为 "100cm"
    │       │   │  - "+"   跳过
    │       │   │  - "2"   是数字，"m"  是单位 → 合并为 "2m"
    │       │   ▼
    │       │   merged = ["100cm", "+", "2m"]
    │       │
    │       └─ 4.3 栈式求值（运算符优先级算法）
    │           │
    │           │  初始化: values=[], operators=[]
    │           │
    │           │  处理 "100cm":
    │           │     parse_value_with_unit("100cm") → (100, ("single","cm","cm"))
    │           │     get_unit_factor_and_cat("cm") → (0.01, "length")
    │           │     base_val = 100 * 0.01 = 1.0
    │           │     values.append( (uinfo, "single", 1.0) )
    │           │
    │           │  处理 "+":
    │           │     operators 为空，直接入栈
    │           │     operators = ["+"]
    │           │
    │           │  处理 "2m":
    │           │     parse_value_with_unit("2m") → (2, ("single","m","m"))
    │           │     get_unit_factor_and_cat("m") → (1.0, "length")
    │           │     base_val = 2 * 1.0 = 2.0
    │           │     values.append( (uinfo, "single", 2.0) )
    │           │
    │           │  遍历结束，清空 operators:
    │           │     弹出 "+"，弹出两个值
    │           │     检查类别都是 "length" → 可相加
    │           │     result_val = 1.0 + 2.0 = 3.0 (基准值，单位: 米)
    │           │     values = [ (uinfo, "single", 3.0) ]
    │           ▼
    │       返回 (src_info, "single", 3.0)
    │       src_info[1] = "cm"  (表达式第一个项的单位)
    │
    ├─ 5. 执行换算
    │   ▼
    │   do_convert_simple(
    │       value = 3.0 / 0.01 = 300,    ← 基准值还原为源单位数值
    │       from_key = "cm",
    │       to_key = "in",
    │       ...
    │   )  [L553]
    │       │
    │       │  from_cat="length", to_cat="length" → 同类可转
    │       │  base_val = 300 * 0.01 = 3.0  (米基准值)
    │       │  result = 3.0 / 0.0254 ≈ 118.110236  (英寸)
    │       │
    │       ▼
    │       输出: "300 厘米 = 118.110236 英寸"
    │       输出: "  换算公式: 1 厘米 = 0.3937007874 英寸"
    │
    └─ 6. 记录历史
        ▼
        record_history("convert 100 cm + 2 m to inches")  [L988]
```

### 3.2 数据变换节点总结

| 阶段 | 数据形态 | 所在函数 |
|------|----------|----------|
| 原始输入 | 命令行字符串 `sys.argv` | `main` |
| 命令拆分 | (cmd, args) 元组 | `main` / `dispatch_command` |
| 表达式拆分 | from_part_str / to_name | `do_convert` |
| 分词结果 | token 列表 `["100","cm","+","2","m"]` | `tokenize_expr` |
| 合并 token | `["100cm", "+", "2m"]` | `eval_unit_expr` |
| 带单位值元组 | `(uinfo, "single", base_val)` | `eval_unit_expr` / `parse_value_with_unit` |
| 基准值（SI） | 浮点数 `3.0`（米） | `eval_unit_expr` |
| 最终结果 | 浮点数 `≈ 118.11`（英寸） | `do_convert_simple` |

---

## 4. 单位解析机制

### 4.1 ALIAS_MAP 的构建过程

ALIAS_MAP 是单位别名到标准键名的映射字典，构建分为三个阶段：

**阶段 1：线性单位类别遍历**（L165-L168）
- 遍历 `UNIT_CATEGORIES` 中的 6 大类（长度、重量、体积、速度、压力、时间）
- 每个单位的 `names` 列表中的所有名称都作为 key，value 为单位标准键名
- 统一转为小写存储，实现大小写不敏感的查找

**阶段 2：温度单位补充**（L169-L174）
- 手动添加温度单位别名（celsius→c, fahrenheit→f, kelvin→k）
- 以及标准键名自身的映射（c→c, f→f, k→k）

**阶段 3：数据单位与带宽单位**（L176-L193）
- 数据单位：bit、byte 及 KB/MB/GB/TB/PB 的别名（使用 base2 的 names）
- 带宽单位：bps、Kbps、Mbps、Gbps 的别名
- 注意：bit/byte 的别名使用 `if _name.lower() not in ALIAS_MAP` 判断，避免覆盖已映射项

### 4.2 resolve_unit 的查找优先级

`resolve_unit(name)` 函数逻辑非常简洁（L519-L521）：
```python
def resolve_unit(name):
    key = ALIAS_MAP.get(name.lower())
    return key
```

查找规则：
1. **统一小写化**：输入名称先转为小写，实现大小写不敏感
2. **直接查表**：在 ALIAS_MAP 中进行 O(1) 查找
3. **未找到返回 None**：由调用方处理未知单位的错误

**优先级说明**：由于 ALIAS_MAP 是顺序构建的字典，后写入的同名 key 会覆盖先写入的。当前代码中数据单位的 bit/byte 别名使用了 `not in` 保护，不会覆盖线性单位中已存在的同名映射。但对于线性单位内部的同名冲突（如果有的话），后遍历的类别会覆盖先遍历的。

### 4.3 自定义单位与内置单位的冲突解决策略

在 `do_define` 函数（L1289-L1317）中：

```python
custom[unit_name] = {"factor": factor, "base": base_key, "display_name": unit_name}
ALIAS_MAP[unit_name] = unit_name
```

**冲突处理**：
1. **ALIAS_MAP 覆盖**：自定义单位直接写入 ALIAS_MAP，如果与内置单位同名，会覆盖内置的映射
2. **查找顺序**：在 `get_unit_factor_and_cat`（L225-L243）中，自定义单位优先级最高，首先检查 `if unit_key in custom`
3. **换算影响**：如果自定义单位名与内置单位同名，自定义单位会"遮蔽"内置单位，所有换算将使用自定义定义

**运行时加载**：
- `main()` 启动时会遍历 `load_custom_units()` 结果，将所有自定义单位名注册到 ALIAS_MAP（L1630-L1632）
- `do_define()` 动态添加时也会同步更新 ALIAS_MAP（L1309）

### 4.4 复合单位的拆解逻辑

`parse_compound_unit(unit_str)` 函数（L210-L222）负责解析复合单位（如 km/h、m/s）：

**拆解步骤**：
1. **检测分隔符**：检查字符串中是否包含 `/`
2. **单次分割**：使用 `split("/", 1)` 只分割一次，确保只取第一个 `/` 作为分子分母分隔
3. **分别解析**：分子部分和分母部分各自调用 `resolve_unit` 解析为标准键名
4. **结果校验**：分子和分母都解析成功才返回复合单位信息

**返回格式**：
- 复合单位：`("compound", numer_key, denom_key, numer_orig, denom_orig)`
- 单一单位：`("single", unit_key, unit_str)`
- 解析失败：`None`

**设计限制**：
- 只支持单层复合（一个 `/`），不支持 `m/s²` 或 `kg·m/s²` 等更复杂形式
- 乘法形式的复合单位（如 `kW·h`）不被支持

---

## 5. 表达式求值引擎

### 5.1 tokenize_expr 的分词规则

`tokenize_expr(s)` 函数（L287-L326）是一个手动实现的有限状态机分词器，按以下规则处理：

**Token 类型**：
1. **数字+单位组合 token**：数字开头，后接字母或 `/`
   - 数字部分支持：`0-9`、`.`、`e`、`E`、`+`、`-`（科学计数法）
   - 单位部分支持：`a-zA-Z`、`/`
2. **纯运算符 token**：`+`、`-`、`*`、`/`、`(`、`)`
3. **纯字母 token**：字母开头，后接字母或 `/`

**特殊处理 - 正负号判断**（L295-L304）：
- 当遇到 `+` 或 `-` 时，判断它是运算符还是正负号：
  - 如果是第一个字符，或前一个字符是 `+`、`-`、`*`、`/`、`(` → 视为正负号，与后续数字/单位合并为一个 token
  - 否则视为二元运算符

**示例**：
```
输入: "100 cm + 2 m"
输出: ["100", "cm", "+", "2", "m"]

输入: "-5km + -3*m"
输出: ["-5km", "+", "-3", "*", "m"]

输入: "2*(3m+5ft)"
输出: ["2", "*", "(", "3m", "+", "5ft", ")"]
```

### 5.2 eval_unit_expr 中 token 合并策略的设计意图

在 `eval_unit_expr` 中（L334-L348），有一个将分离的数字 token 和单位 token 合并的步骤。

**合并逻辑**：
```python
if (i + 1 < len(tokens) and
        safe_eval_expr(t) is not None and       # 当前 token 是纯数字
        re.match(r'^[a-zA-Z/]+$', tokens[i+1]) and  # 下一个 token 是纯字母/斜杠
        tokens[i + 1] not in ("to", "in")):     # 排除关键字
    unit_key = resolve_unit(tokens[i + 1])
    if unit_key or parse_compound_unit(tokens[i + 1]):
        merged.append(t + tokens[i + 1])        # 合并为 "数字+单位"
        i += 2
        continue
```

**设计意图**：

1. **容错处理**：用户输入时可能在数字和单位之间加空格（如 `100 cm`），也可能不加空格（如 `100cm`）。合并策略让两种写法都能正常工作。

2. **统一处理路径**：合并后所有带单位的值都以 `数字+单位` 形式存在，后续的 `parse_value_with_unit` 可以统一处理，不需要额外处理分离的数字和单位。

3. **表达式语法灵活性**：在带单位表达式中，数字和单位既可以连写也可以分开写，提升用户体验。

4. **关键字避让**：排除 "to" 和 "in" 是为了避免在 `do_convert` 的上下文中误将分隔关键字当作单位处理。

### 5.3 safe_eval_expr 的安全边界

`safe_eval_expr(expr)` 函数（L196-L207）是一个受控的表达式求值器，用于安全地计算纯数值表达式。

**安全机制**：

1. **字符白名单**（L197-L200）：
   - 只允许字符：`0123456789.+-*/() `
   - 任何不在白名单中的字符直接返回 `None`
   - 这阻止了所有字母、特殊符号、转义序列等的注入

2. **受限执行环境**（L202）：
   - `eval(expr, {"__builtins__": {}}, {})`
   - `__builtins__` 设为空字典，完全禁用内置函数
   - 全局和局部命名空间都为空，无法访问任何外部变量
   - 即使攻击者绕过白名单，也无法调用危险函数

3. **结果类型校验**（L203-L204）：
   - 只接受 `int` 或 `float` 类型的结果
   - 其他类型（如字符串、列表、函数等）均返回 `None`

4. **异常捕获**（L205-L206）：
   - 任何异常都被捕获并返回 `None`
   - 不会因非法输入导致程序崩溃

**安全边界总结**：
- ✅ 支持：纯数值的四则运算、括号、科学计数法、正负号
- ❌ 禁止：变量、函数调用、字符串、列表、字典、属性访问等
- ❌ 禁止：`__import__`、`eval`、`exec` 等危险操作

---

## 6. 扩展性分析

### 6.1 新增"面积"单位类别需要修改的位置

要新增面积单位类别（如平方米、平方千米、公顷、英亩等），需要在以下位置进行修改：

| 位置 | 变量/函数名 | 行号 | 需要添加的内容 |
|------|------------|------|----------------|
| 1 | `AREA_UNITS` 字典 | 新增（建议在 `LENGTH_UNITS` 之后） | 定义面积单位字典，格式与 LENGTH_UNITS 等一致，每个单位包含 `factor`（换算为基准单位的因子）、`name`（中文名）、`names`（别名列表）。基准单位建议用 `m²` 或 `m2` |
| 2 | `UNIT_CATEGORIES` 字典 | L147-L154 | 添加 `"area": AREA_UNITS` 条目，将面积类别纳入线性单位体系 |
| 3 | `ALL_LINEAR_UNITS` 合并 | L156-L162 | 添加 `ALL_LINEAR_UNITS.update(AREA_UNITS)`，使面积单位参与全局线性单位查找 |
| 4 | ALIAS_MAP 构建 | L165-L168 | 无需额外修改，因为 ALIAS_MAP 通过遍历 `UNIT_CATEGORIES` 自动构建 |
| 5 | `find_unit_category` 函数 | L524-L534 | 无需额外修改，因为该函数通过遍历 `UNIT_CATEGORIES` 自动查找 |
| 6 | `get_unit_factor_and_cat` 函数 | L225-L243 | 无需额外修改，面积单位会通过 `ALL_LINEAR_UNITS` 路径自动处理 |
| 7 | `get_unit_display_name` 函数 | L246-L254 | 无需额外修改，通过 `UNIT_CATEGORIES.values()` 遍历自动包含 |
| 8 | `do_convert_simple` 输出 | L651 | 无需额外修改，会自动归为 "普通线性单位" 类输出换算公式 |
| 9 | `do_calc` 中的"其他单位"展示 | L853-L866 | 无需额外修改，通过 `UNIT_CATEGORIES[cat]` 自动遍历同类单位 |
| 10 | `do_help` 帮助文本 | L1516-L1577 | 建议在示例中添加面积单位的使用示例 |

**关键修改点总结**：仅需 3 处核心修改（新增字典 + 加入 UNIT_CATEGORIES + 加入 ALL_LINEAR_UNITS），其余逻辑均可自动适配，体现了良好的可扩展性设计。

### 6.2 支持 "convert 100 km to all" 输出所有同类单位结果

要支持 `convert 100 km to all` 功能，需要在 `do_convert` 函数中添加逻辑。

**具体修改位置**：

**位置：`do_convert` 函数，目标单位解析之后**（L727-L732 附近）

当前代码：
```python
to_info = parse_compound_unit(to_name)
if to_info is None and to_name.lower() in custom:
    to_info = ("single", to_name.lower(), to_name)
if to_info is None:
    print(f"错误: 未知目标单位 '{to_name}'")
    return
```

需要添加的分支逻辑（插入到 `parse_compound_unit` 之后，判断 `to_name == "all"`）：

```python
# 新增：处理 "to all" 情况
if to_name.lower() == "all":
    # 先求值源表达式
    expr_val = eval_unit_expr(from_part_str, custom, use_base10)
    if expr_val is not None and expr_val[1] == "single":
        base_val = expr_val[2]
        src_info = expr_val[0]
        from_key = src_info[1]
        cat = find_unit_category(from_key)
        if cat and cat in UNIT_CATEGORIES:
            units = UNIT_CATEGORIES[cat]
            from_display = get_unit_display_name(from_key, custom)
            orig_val = base_val / get_unit_factor_and_cat(from_key, custom, use_base10)[0]
            print(f"{format_number(orig_val)} {from_display} 换算为所有{cat}单位:")
            print("-" * 50)
            for key, info in units.items():
                if key == from_key:
                    continue
                f = get_unit_factor_and_cat(key, custom, use_base10)
                if f:
                    v = base_val / f[0]
                    print(f"  {format_number(v)} {info['name']}")
            record_history("convert " + from_part_str + " to all")
            return
    # 如果表达式不是单一单位类型，走错误处理
    print("错误: 'to all' 仅支持单一单位类型的换算")
    return
```

**修改位置总结**：
- **函数**：`do_convert` [unitcalc.py:695-827](file:///Users/huwenjie/项目/胡文杰题目汇总/项目/hwj-00433/unitcalc.py#L695-L827)
- **分支位置**：L727-L732 之间（目标单位解析后，表达式求值前）
- **依赖函数**：`find_unit_category`、`get_unit_factor_and_cat`、`get_unit_display_name`、`format_number`

**设计思路**：
1. 检测目标单位是否为 "all"（不区分大小写）
2. 如果是，先对源表达式求值，得到基准值和单位类别
3. 如果是单一单位类型，遍历该类别下所有单位进行换算输出
4. 跳过源单位自身，输出其他所有同类单位的换算结果
5. 同时记录历史

类似地，对于 `do_convert_simple` 之外的简单换算路径（非表达式路径，L811 之后），也需要添加对应的 "all" 分支处理，以覆盖 `convert 100 km to all` 这种不带表达式的简单调用形式。
