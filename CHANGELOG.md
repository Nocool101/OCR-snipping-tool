# 更新日志

本文件记录 screenshot-ocr 的版本变更。

## v0.1.1 — 2026-09-24

### 新增

- **API Key 加密保存**：保存在 `%APPDATA%\screenshot-ocr\settings.json` 里的 API Key 不再明文，改用 Windows DPAPI（`CryptProtectData`）以当前 Windows 账户加密，写入 `api_key_enc` 字段。不新增任何依赖——直接调用系统 `crypt32.dll`。

### 变更

- 配置文件字段由 `api_key` 改为 `api_key_enc`。
- 首次读取到旧版明文 Key 时自动加密并回写，只迁移一次，无需手工操作。

### 说明与限制

- 密文绑定当前 Windows 账户：把 `settings.json` 复制到其他账户、其他机器或其他平台后都解不开，会被视为「未配置」，需要重新填写 Key。
- 只防「配置文件被直接查看，或被拷贝、进备份、进版本库」这类静态泄露；以当前用户身份运行的其他程序仍可解密——这是本机单用户工具的合理上限。
- 加密仅在 Windows 上生效；从源码在非 Windows 平台运行时会退回明文存储。

### 升级注意

- 从旧版本升级无需额外操作：替换 exe 后首次运行，旧明文 Key 会自动迁移为密文。
