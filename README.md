<a id="top"></a>

<p align="center">
  <img src="https://img.shields.io/badge/E6-RegKey%20Calculator-blue?style=flat-square" alt="E6 RegKey Calculator"/>
</p>

<h1 align="center">E6 控制器注册码计算器</h1>
<p align="center"><em>E6 Controller Registration Key Calculator — a reverse-engineering research artifact</em></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="license MIT"></a>
  <img src="https://img.shields.io/badge/python-3.6%2B-blue?style=flat-square" alt="python 3.6+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat-square" alt="platform">
  <img src="https://img.shields.io/badge/release-v1.0.0-orange?style=flat-square" alt="release v1.0.0">
  <img src="https://img.shields.io/badge/use-research%20%2F%20education%20only-red?style=flat-square" alt="research / education only">
  <a href=".github/workflows/selftest.yml"><img src="https://github.com/<your-name>/E6-RegKey-Calculator/actions/workflows/selftest.yml/badge.svg" alt="selftest CI"></a>
</p>

<p align="center">
  <a href="#about">About</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#getting-started">Getting started</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#faq">FAQ</a> ·
  <a href="#disclaimer">Disclaimer</a> ·
  <a href="#license">License</a>
</p>

<p align="center">
  🌐 <a href="docs/methodology.md">破译方法论 (RE write-up)</a> ·
  <a href="DISCLAIMER.md">完整免责声明 (Full disclaimer)</a> ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

<br>

> [!IMPORTANT]
> **本项目仅用于安全研究与技术学习**，展示对 STM32 UID 绑定注册校验算法的逆向分析结论。
> **请仅在您拥有合法所有权的设备上使用**，并遵守所在地区法律法规。
> 本项目与任何硬件厂商均**无任何关联**。
> **使用即视为您已阅读并同意 [DISCLAIMER.md](DISCLAIMER.md) 的全部条款。**

---

<a id="about"></a>

## About / 关于

一个**零依赖**的 Python 小工具：填入 E6 控制器屏幕上的**机器码**，或芯片的 **96-bit UID**，
直接算出本地注册参数 **E013（密码高段）/ E014（密码低段）**，用于解锁被 UID 绑定加密的参数区
（如循迹卡 PID 参数 E033/E034/E035）。

**特性**

- 零第三方依赖，纯标准库，Python 3.6+，单文件即拷即用
- 机器码 / UID 两种输入；UID 字序自动判别，容忍 `ID:` 前缀与转录杂字符
- 批量模式：一个清单文件算多台设备
- 内置两台已知设备回归自检（`--selftest`）
- 可选 `--firmware` 真实固件仿真交叉验证（Unicorn）
- 完整破译方法论文档：[docs/methodology.md](docs/methodology.md)

**本仓库不包含**任何厂商固件、厂商源代码或专有数据——只包含逆向分析得出的算法描述与本项目的原创实现。

---

<a id="how-it-works"></a>

## How it works / 破译原理

```
┌─ 芯片 96-bit UID (STM32 系统内存 0x1FFF7A10 / 14 / 18) ─────────────┐
│   UID0 = 0x00XX00YY (晶圆坐标)   UID1   UID2                        │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  三字异或(顺序无关)
                                ▼
                    机器码 = UID0 ^ UID1 ^ UID2      ← 设备屏幕显示的就是它
                                │
                                ▼  浮点流水线(固件 @0x80F42A0 逆出)
        d = (double)机器码 × 11.0 ÷ 7.0 + 11160725.0
        n = (int64)d            R = n mod 100000000
        v = R div 10 + (R mod 10) × 10000000     ← 末位数字搬到最前
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
     E013 = int((v div 10000) / 2.5)   E014 = int((v mod 10000) / 2.5)
             密码高段                        密码低段
```

**为什么可信（验证方法）**

1. 用 capstone 反汇编定位注册函数（`0x80F42A0`），顺着 `E013 密码高段` / `E014 密码低段`
   字符串交叉引用找到输入比较指令（`0x80F4522`）；
2. 用 Unicorn CPU 模拟器**逐条执行真实固件指令**（灌入真实 UID），与公式结果逐位对照；
3. 设备未注册时屏幕显示的"您的机器码为: XXXX"即 `UID0^UID1^UID2`，
   与仿真输出**逐位一致**——输入侧闭环后，输出侧即确定性正确；
4. 两台已知设备回归测试全部 PASS（`--selftest`）。

方法论的完整记录见 [docs/methodology.md](docs/methodology.md)。

---

<a id="getting-started"></a>

## Getting started / 快速开始

**环境要求：** Python 3.6+（核心功能无任何第三方依赖）

```bash
git clone https://github.com/<your-name>/E6-RegKey-Calculator.git
cd E6-RegKey-Calculator

# 跑回归自检，确认一切正常
python e6_keygen.py --selftest
```

可选（仅 `--firmware` 仿真交叉验证需要）：

```bash
pip install -r requirements.txt
```

---

<a id="usage"></a>

## Usage / 用法

```bash
# 交互模式（直接粘贴，回车即算）
python e6_keygen.py

# 用机器码算
python e6_keygen.py --mc 4653170
python e6_keygen.py --mc "K 4653170"        # 屏幕原样粘贴也行
python e6_keygen.py --mc 0x470072           # 十六进制也行

# 用 UID 算（自动识别字序，容忍 ID: 前缀和末尾杂字符）
python e6_keygen.py --uid 53483643 53303606 003F0037
python e6_keygen.py --uid "ID:53483643 53303606 003F0037A"

# 批量（每行: 名称 | UID 或 机器码，见 examples/devices.txt）
python e6_keygen.py --file examples/devices.txt

# 用你合法持有的固件做仿真交叉验证（需 pip install unicorn）
python e6_keygen.py --uid 53483643 53303606 003F0037 --firmware settings.bin

# 写入机器人 E 盘的 注册码.txt（中间两个空格）
python e6_keygen.py --mc 4653170 --write-e
```

输出示例：

```
--------------------------------------------------------------
  UID 顺序识别 : 高字在前(标准格式)
  机器码        : 4653170   (0x00470072)
  计算过程      : 18472849.2857 -> n=18472849 -> R=18472849 -> v=91847284
  >>> E013 密码高段 = 3673
  >>> E014 密码低段 = 2913
  注册写法      : E013 = 3673 , E014 = 2913
```

然后在控制器 `机器设置 → 数据修改` 填入 **E013=3673、E014=2913**，保存确认。

**输入格式宽容度**

| 你能拿到的 | 直接粘贴 | 示例 |
|:--|:--|:--|
| 屏幕机器码 | 数字 | `4653170`、`K 4653170` |
| 十六进制机器码 | `0x` 开头 | `0x470072` |
| UID（高字在前） | 三个字，可带 `ID:` 前缀 | `ID:53483643 53303606 003F0037A` |
| UID（低字在前） | 自动识别 | `003F0037 53303606 53483643` |
| UID（24 位连续 hex） | 自动识别 | `5348364353303606003F0037` |

字序靠"晶圆坐标字"（形如 `00XX00YY`）自动判别，无需记忆格式。

**打包为 Windows exe（绿色单文件）**

```bash
pip install pyinstaller
pyinstaller --onefile --console --name E6注册码计算器 e6_keygen.py
# 产物在 dist/ 下, 拷贝即用, 无需 Python 环境
```

> [!NOTE]
> `.bat` 启动器必须写成**纯 ASCII**（cmd 按 ANSI 代码页解析，中文会崩），
> 用 `for %%F in ("%~dp0*.exe")` 通配符定位 exe 可避开中文文件名匹配问题。

---

<a id="faq"></a>

## FAQ

**Q: 提示密码错误？**
A: ① 确认两段没填反（E013=高段）；② 确认保存/确认步骤已执行；③ 重发机器码或 UID 重算——
屏幕显示值与 `UID0^UID1^UID2` 必须逐位一致，不一致说明 UID 转录有误。

**Q: 支持其他型号 / 固件版本吗？**
A: 本算法与固件版本绑定。换了固件版本（加载基址、常量、比较地址可能变化）需重新分析，
方法论见 [docs/methodology.md](docs/methodology.md)。

**Q: 为什么算法里有个浮点流水线？**
A: 作者刻意用软浮点运算 + 数字旋转做混淆，阻止肉眼直读。逆向时只要逐条仿真即可精确复现，
这也是本项目"不猜公式、直接跑机器码"方法论的由来。

---

<a id="disclaimer"></a>

## Disclaimer / 免责声明

This project is intended **solely for lawful security research, education, and interoperability testing on systems that you own or have explicit authorization to assess**.

**Unauthorized access, circumvention of licensing, disruption, or any other use against devices you do not own is strictly prohibited.** Users are solely responsible for complying with applicable laws and regulations. The maintainers accept **no liability** for misuse of this project or for any resulting damage or legal consequences.

本项目与任何设备厂商及其关联公司、销售商**不存在任何关联、雇佣、赞助或背书关系**，未获得上述任何主体的授权。

**完整条款（中英双语）请阅读 [DISCLAIMER.md](DISCLAIMER.md)。**

---

<a id="license"></a>

## License

本项目原创代码以 [MIT](LICENSE) 发布。**注意**：MIT 许可仅覆盖本仓库内的原创代码，
不包括任何第三方固件、算法专利或厂商知识产权。

---

<p align="center"><sub>An independent security research project · not affiliated with any manufacturer · <a href="#top">back to top</a></sub></p>
