# AI Trader Telegram Bot

该项目实现了一个可扩展的 Telegram 报警机器人，可以自动识别 BTC 与 ETH 在日线、4 小时线与 1 小时线的关键支撑和阻力位，并在价格触及/突破关键位或者短时出现大幅波动时推送消息提醒。

## 功能简介

- **多时间框架关键位识别**：默认监控 BTC/ETH 在日线、4 小时线与 1 小时线的数据，自动提取支撑与阻力位。
- **实时价格触发提醒**：当最新价格触及或明显突破关键位时推送提醒。
- **波动性监控**：基于更短时间窗口（默认 15 分钟）的价格变化检测巨大波动。
- **Telegram 推送**：自动向配置的多个群组或用户推送提醒消息。
- **高可扩展性**：所有核心组件（数据源、分析器、提醒逻辑）都以类的形式实现，便于后续替换或扩展。

## 环境准备

1. 安装 Python 3.10 或更高版本。
2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 配置

机器人通过环境变量进行配置，必填与可选项如下：

| 变量名 | 是否必填 | 说明 | 默认值 |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token | - |
| `TELEGRAM_CHAT_IDS` | ✅ | 逗号分隔的聊天 ID 列表 | - |
| `PRICE_ALERT_TOLERANCE` | ⭕ | 价格触及关键位的容忍度（比例） | `0.002` |
| `VOLATILITY_WINDOW_MINUTES` | ⭕ | 波动性检测窗口（分钟） | `15` |
| `VOLATILITY_THRESHOLD` | ⭕ | 波动性阈值（比例） | `0.01` |
| `VOLATILITY_INTERVAL` | ⭕ | 波动性数据采样的 K 线周期 | `1m` |
| `VOLATILITY_LOOKBACK` | ⭕ | 波动性检测使用的 K 线数量 | `120` |
| `DATA_SOURCE_URL` | ⭕ | 行情数据源（默认 Binance 公共接口） | `https://api.binance.com` |
| `REQUEST_TIMEOUT` | ⭕ | 网络请求超时（秒） | `10` |
| `POLL_INTERVAL_SECONDS` | ⭕ | 主循环轮询间隔（秒） | `300` |

## 运行

设置好环境变量后，使用以下命令启动机器人：

```bash
python -m ai_trader
```

程序将按照指定的轮询间隔抓取行情数据，检测关键位与波动情况，一旦触发条件即向 Telegram 推送提示。

## Docker 部署

若希望在 Docker 中运行机器人，可按以下步骤操作：

1. **准备配置文件**：在项目根目录创建 `.env` 文件，填入上文列出的环境变量，例如：

   ```env
   TELEGRAM_BOT_TOKEN=xxx
   TELEGRAM_CHAT_IDS=123456789,-987654321
   PRICE_ALERT_TOLERANCE=0.002
   ```

2. **构建镜像**：在项目根目录执行：

   ```bash
   docker build -t ai-trader .
   ```

3. **启动容器**：使用刚才准备的 `.env` 文件为容器提供配置：

   ```bash
   docker run --rm --env-file .env ai-trader
   ```

容器会在前台运行主循环，需要停止时直接 `Ctrl + C` 即可。若要在后台运行，可添加 `-d` 参数，并通过 `docker logs` 查看输出。

## 拓展建议

- **新增币种**：在 `ai_trader.config.BotConfig` 中调整默认的 `symbols` 列表即可。
- **替换数据源**：实现新的数据客户端并注入 `MarketMonitor`。
- **自定义提醒逻辑**：可以根据自己的策略修改 `SupportResistanceAnalyzer`、`VolatilityAnalyzer` 或者添加新的提醒模块。

如需进一步的功能扩展，可以基于当前代码结构继续迭代。欢迎提出更多需求！
