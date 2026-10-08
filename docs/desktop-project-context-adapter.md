# 桌面端项目上下文适配器

## 作用

适配器按项目目录启动一个本地端口。它读取该目录的 `AGENTS.md` 元信息，使用 Codex 请求中的 Gateway API Key 调用 `/v4/projects/{project_id}/context/client`，缓存短期令牌，并在剩余五分钟时自动续期。转发到个人 API 的每一条请求都会带上 `X-SmartBrain-Project-Context`，提示词不需要写请求头。

## 多项目同时开发

每个项目使用自己的适配器端口和 Codex Provider 地址，不共享一个全局活动项目。例如：

```powershell
python smartbrain_codex_adapter.py --api-base-url "https://brain.example" --project-dir "D:\\ProjectA" --listen-port 30101
python smartbrain_codex_adapter.py --api-base-url "https://brain.example" --project-dir "D:\\ProjectB" --listen-port 30102
```

两个项目可以同时打开。每个 Codex 项目的 Provider `base_url` 分别指向对应的 `http://127.0.0.1:<端口>/v1`。适配器会拒绝项目目录中 `AGENTS.md` 的项目 ID 与自身不一致的请求。

## Codex Provider 配置

在使用的 Codex 配置或独立配置档中设置：

```toml
model_provider = "smartbrain"

[model_providers.smartbrain]
name = "smartbrain"
wire_api = "responses"
base_url = "http://127.0.0.1:30101/v1"
requires_openai_auth = false
```

启动 PowerShell 脚本时如果没有通过 `-ApiKey` 传入密钥，会交互式提示输入；密钥只放在适配器进程环境中，不写入项目文件。也可以让 Codex Provider 发送你已经配置在本机用户配置中的 Gateway API Key，适配器会优先使用请求中的 `Authorization`。

如果多个桌面项目需要同时运行，请为每个项目使用独立的 Codex 配置档/`CODEX_HOME`，让每个档案的 `base_url` 指向自己的端口。不要把项目令牌写进提示词、`AGENTS.md` 或提交到仓库。

## 一键启动（推荐）

项目页面的“下载一键启动器”会生成一个当前项目专用 `.cmd` 文件。双击即可；如果文件不在项目目录，启动器会弹出项目文件夹选择。启动器随后自动识别 `AGENTS.md`、临时解包内置 PowerShell 逻辑、下载 Python 适配器、选择本项目端口、启动令牌续期服务，并执行 `codex app <项目目录>` 注入本项目 Provider 配置。首次运行提示输入一次 API Key，之后使用当前 Windows 用户 DPAPI 加密缓存，不需要重复输入，也不会写入项目文件。

## 页面操作

1. 在项目页面下载 `AGENTS.md` 到项目根目录。
2. 点击“下载一键启动器”，把生成的 `.cmd` 放进项目根目录。
3. 双击 `.cmd`，按提示输入一次 API Key。
4. 点击页面“检测本机适配器”，确认显示“已连接”。
5. 以后直接双击该项目的 `.cmd` 即可打开对应 Codex 项目；请求会自动获取、续期和携带令牌。

页面不会展示原始令牌，也不会要求用户复制令牌到提示词。API Key 只用于适配器向 Gateway 换取项目令牌，服务端仍会校验用户、Key、项目成员关系和 `AGENTS.md` 摘要。
