#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
 E6 控制器 注册码(E013/E014)计算器
 E6 Controller Registration Key Calculator
====================================================================

 输入: ① 机器码(设备屏幕 "您的机器码为: XXXX" 那个数)
       ② 芯片 96-bit UID (ID: xxxxxxxx xxxxxxxx xxxxxxxx)
 输出: E013(密码高段) / E014(密码低段) -> 填进参数设置程序即完成本地注册

 ------------------------------------------------------------------
 重要声明 (请务必阅读 DISCLAIMER.md):
   本项目仅用于安全研究与学习目的, 展示了针对 STM32 UID 绑定的
   注册校验算法的逆向分析结论。请在您自己拥有合法所有权的设备上
   使用, 并遵守您所在地区的法律法规。作者与任何设备厂商均无关联。
 ------------------------------------------------------------------

 算法来源 : 对参数设置程序(STM32F405RG 固件, 加载基址 0x080E0000)
           注册函数 @0x80F42A0 的逆向分析(capstone 反汇编 + Unicorn 仿真,
           与设备实际显示值双重比对验证)。

 用法:
   python e6_keygen.py                       交互模式(直接粘贴, 回车)
   python e6_keygen.py --mc 4653170          用机器码算
   python e6_keygen.py --mc "K 0x470072"
   python e6_keygen.py --uid 53483643 53303606 003F0037
   python e6_keygen.py --uid "ID:53483643 53303606 003F0037A"   (容忍杂质)
   python e6_keygen.py --file devices.txt    批量(每行: 名称 | UID或机器码)
   python e6_keygen.py --selftest            回归自检(两台已知设备)
   python e6_keygen.py --mc 4653170 --write-e 尝试写入 E:\注册码.txt
   python e6_keygen.py --uid 53483643 53303606 003F0037 \
       --firmware path/to/settings.bin         用真实固件仿真交叉验证
                                                (需要 pip install unicorn)
====================================================================
"""
import sys
import os
import re
import argparse

__version__ = "1.0.0"

# ---------- 核心算法(逆自固件 @0x80F42A0) ----------
MAGIC = 11160725.0          # 固件 VA 0x80F4700 处的 double 常量
MOD = 100000000             # 固件中的 64 位常量


def calc(machine_code):
    """machine_code(int) -> (E013, E014, 中间过程dict)"""
    x = int(machine_code)
    d = float(x) * 11.0          # 软浮点双精度乘法
    d = d / 7.0                  # 软浮点双精度除法
    d = d + MAGIC                # 加固件常量
    n = int(d)                   # (int64) 截断
    R = n % MOD                  # 64 位除法取余
    v = (R // 10) + (R % 10) * 10000000      # 末位数字旋转到最高位
    hi = int((v // 10000) / 2.5)             # E013 密码高段
    lo = int((v % 10000) / 2.5)              # E014 密码低段
    steps = {"d": d, "n": n, "R": R, "v": v}
    return hi, lo, steps


def uid_to_machine_code(w0, w1, w2):
    """三个 32 位 UID 字(内存序) -> 机器码"""
    return (w0 ^ w1 ^ w2) & 0xFFFFFFFF


# ---------- 输入解析 ----------
def _is_wafer_word(g):
    """UID0 是晶圆坐标, 形如 0x00XX00YY"""
    return (g >> 24) == 0 and ((g >> 8) & 0xFF) == 0


def parse_uid(text):
    """
    接受任意粘贴格式, 返回 (UID0, UID1, UID2, 顺序说明)
    自动识别 高字在前 / 低字在前:
      UID0 = 长得像晶圆坐标 0x00XX00YY 的那个字
    """
    s = text or ""
    # 去掉 ID / UID 之类前缀词('I' 不是 hex, 但 'D' 是, 必须先删)
    s = re.sub(r"(?i)^\s*(uid|id)\s*[:：]?\s*", "", s)
    s = re.sub(r"(?i)[\s,:：;；\-]+(uid|id)\s*[:：]?\s*", " ", s)
    runs = re.findall(r"[0-9A-Fa-f]+", s)
    words = []
    for r in runs:
        if len(r) < 4:            # 滤掉 ID/I/D/单个字母 之类的碎片
            continue
        if len(r) >= 24:          # 24 位连续 hex 串, 按 8 字符切开
            for i in range(0, len(r) - 7, 8):
                words.append(r[i:i + 8])
                if len(words) == 3:
                    break
            break
        if len(r) > 8:            # 粘连了杂质(如 003F0037A), 取前 8 位
            r = r[:8]
        words.append(r)
        if len(words) == 3:
            break
    if len(words) < 3:
        raise ValueError("UID 至少需要 3 个 32 位字(共 24 个十六进制字符)")
    g = [int(x, 16) for x in words[:3]]
    wafer = [i for i, x in enumerate(g) if _is_wafer_word(x)]
    if len(wafer) == 1:
        i0 = wafer[0]
        if i0 == 2:      # 晶圆字在最后 -> 高字在前(常见显示格式)
            w0, w1, w2 = g[2], g[1], g[0]
            order = "高字在前(标准格式)"
        elif i0 == 0:    # 晶圆字在最前 -> 低字在前
            w0, w1, w2 = g[0], g[1], g[2]
            order = "低字在前(已自动识别)"
        else:
            w0, w1, w2 = g[2], g[1], g[0]
            order = "中间字像晶圆坐标, 按标准格式处理"
    else:
        w0, w1, w2 = g[2], g[1], g[0]
        order = "无明显晶圆坐标字, 按标准格式(高字在前)处理"
    return w0, w1, w2, order


def parse_machine_code(text):
    """'K 4653170' / '4653170' / '0x470072' / '机器码:4653170' -> int"""
    t = (text or "").strip()
    if re.match(r"(?i)^\s*0x", t):
        h = re.sub(r"[^0-9A-Fa-f]", "", t[2:])
        if not h:
            raise ValueError("0x 后面没有十六进制数字")
        return int(h, 16)
    d = re.sub(r"[^0-9]", "", t)
    if not d:
        raise ValueError("没有找到数字")
    return int(d)


def looks_like_uid(s):
    """判断一行输入是 UID 还是机器码"""
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", s)
    if len(cleaned) >= 16:                 # 机器码最多 8 位 hex / 10 位十进制
        return True
    if re.search(r"[A-Fa-f]", s) and re.search(r"[\s:：,，]", s):
        return True
    return False


# ---------- 输出 ----------
def show(label, machine_code, hi, lo, steps=None, order=None):
    print("-" * 62)
    if label:
        print(f"  {label}")
    if order:
        print(f"  UID 顺序识别 : {order}")
    print(f"  机器码        : {machine_code}   (0x{machine_code:08X})")
    if steps:
        print(f"  计算过程      : {steps['d']:.4f} -> n={steps['n']} "
              f"-> R={steps['R']} -> v={steps['v']}")
    print(f"  >>> E013 密码高段 = {hi}")
    print(f"  >>> E014 密码低段 = {lo}")
    print(f"  注册写法      : E013 = {hi} , E014 = {lo}")


def write_e_drive(hi, lo):
    """写入 E:\\注册码.txt (格式: 高段  低段, 两个空格)"""
    if not os.path.isdir("E:\\"):
        print("  [提示] 当前没有 E 盘(机器人未连接), 跳过写入")
        return False
    path = os.path.join("E:\\", "注册码.txt")
    with open(path, "w", encoding="gbk") as f:
        f.write(f"{hi}  {lo}\n")
    print(f"  已写入: {path}   内容: {hi}  {lo}")
    return True


def handle_line(line):
    """处理一行输入(UID 或 机器码), 返回 False 表示退出"""
    s = (line or "").strip()
    if not s or s.lower() in ("q", "quit", "exit"):
        return False
    name = None
    if "|" in s:
        name, s = [x.strip() for x in s.split("|", 1)]
    tag = f"[{name}] " if name else ""
    if looks_like_uid(s):
        w0, w1, w2, order = parse_uid(s)
        mc = uid_to_machine_code(w0, w1, w2)
        hi, lo, st = calc(mc)
        show(tag, mc, hi, lo, st, order)
    else:
        try:
            mc = parse_machine_code(s)
        except ValueError:
            w0, w1, w2, order = parse_uid(s)
            mc = uid_to_machine_code(w0, w1, w2)
            hi, lo, st = calc(mc)
            show(tag, mc, hi, lo, st, order)
            return True
        hi, lo, st = calc(mc)
        show(tag, mc, hi, lo, st)
    return True


def selftest():
    ok = True
    cases = [
        ("设备1", (0x000E002D, 0x37303808, 0x43485943), 1953915238, 2726, 3958),
        ("设备2", (0x003F0037, 0x53303606, 0x53483643), 4653170, 3673, 2913),
    ]
    print("=" * 62)
    print(" 回归自检 (两台已知设备)")
    for name, (w0, w1, w2), mc_exp, hi_exp, lo_exp in cases:
        mc = uid_to_machine_code(w0, w1, w2)
        hi, lo, _ = calc(mc)
        good = (mc == mc_exp and hi == hi_exp and lo == lo_exp)
        ok &= good
        print(f"  {name}: 机器码 {mc} (期望 {mc_exp}) "
              f"E013={hi} E014={lo} (期望 {hi_exp}/{lo_exp})  "
              f"{'PASS' if good else 'FAIL'}")
    print(" 自检结果:", "全部通过 ✓" if ok else "存在失败 ✗")
    return ok


# ---------- 可选: 真实固件仿真交叉验证 ----------
def emu_check(uid_words, firmware_path):
    """有 unicorn + 固件文件时, 用真实指令再算一遍与公式对照。
       需要: pip install unicorn ; 固件请使用你合法持有的设备固件。"""
    if not firmware_path:
        print("  [跳过交叉验证] 未提供 --firmware (公式结果本身已经双重验证)")
        return None
    try:
        import struct
        from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS,
                             UC_HOOK_CODE, UcError)
        from unicorn.arm_const import (UC_ARM_REG_SP, UC_ARM_REG_R8,
                                       UC_ARM_REG_R9, UC_ARM_REG_R5, UC_ARM_REG_R0)
    except ImportError:
        print("  [跳过交叉验证] 未安装 unicorn (pip install unicorn 后可用)")
        return None
    if not os.path.isfile(firmware_path):
        print(f"  [跳过交叉验证] 固件文件不存在: {firmware_path}")
        return None
    d = open(firmware_path, "rb").read()
    base, size = 0x080E0000, (len(d) + 0xFFF) & ~0xFFF
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(base, size)
    uc.mem_write(base, d + b"\x00" * (size - len(d)))
    uc.mem_map(0x1FFF7000, 0x2000)
    uc.mem_write(0x1FFF7A10, struct.pack("<III", *uid_words))
    uc.mem_map(0x20000000, 0x20000)
    uc.reg_write(UC_ARM_REG_SP, 0x2001FF00)
    uc.reg_write(UC_ARM_REG_R8, 0x1FFF7A18)   # 跳过加载指令, 预设 r8
    got = {}

    def hook(uc, addr, size_, ud):
        if addr == 0x80f4492:
            got["mc"] = uc.reg_read(UC_ARM_REG_R9)     # sb = UID2^UID1^UID0
        if addr == 0x80f4522:                          # 与 E013/E014 比较处
            got["hi"] = uc.reg_read(UC_ARM_REG_R5)
            got["lo"] = uc.reg_read(UC_ARM_REG_R0)
            uc.emu_stop()

    uc.hook_add(UC_HOOK_CODE, hook)
    try:
        uc.emu_start(0x080F43C0 | 1, 0, count=500000)
    except UcError as e:
        print("  [交叉验证] 仿真出错:", e)
        return None
    if "hi" in got and "lo" in got:
        print(f"  [交叉验证] 固件仿真: 机器码={got.get('mc')} "
              f"E013={got['hi']} E014={got['lo']}")
        return got["hi"], got["lo"]
    return None


def _fix_console():
    """Windows 控制台中文输出适配(双击直接运行时也不乱码)"""
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    _fix_console()
    ap = argparse.ArgumentParser(
        description="E6 注册码(E013/E014)计算器 — 仅供学习研究, 见 DISCLAIMER.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例: python e6_keygen.py --mc 4653170")
    ap.add_argument("--mc", help="机器码(设备屏幕显示的数, 支持 'K 4653170'/'0x...')")
    ap.add_argument("--uid", nargs="*", help="UID 三个字, 可带 ID: 前缀, 可只给一整串")
    ap.add_argument("--file", help="批量文件, 每行: 名称 | UID 或 机器码")
    ap.add_argument("--firmware", help="(可选) 你合法持有的设置程序固件路径, 用于仿真交叉验证")
    ap.add_argument("--selftest", action="store_true", help="回归自检")
    ap.add_argument("--write-e", action="store_true", help="写入 E:\\注册码.txt")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    a = ap.parse_args()

    print("=" * 62)
    print("  E6 注册码计算器   填机器码或UID -> 出 E013/E014")
    print("  仅用于学习研究, 请在自有设备上使用 — 详见 DISCLAIMER.md")
    print("=" * 62)

    if a.selftest:
        selftest()
        return
    if a.file:
        with open(a.file, "r", encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
        for l in lines:
            try:
                handle_line(l)
            except Exception as e:
                print(f"  [解析失败] {l!r}: {e}")
        return
    if a.mc:
        mc = parse_machine_code(a.mc)
        hi, lo, st = calc(mc)
        show("", mc, hi, lo, st)
        if a.write_e:
            write_e_drive(hi, lo)
        return
    if a.uid:
        w0, w1, w2, order = parse_uid(" ".join(a.uid))
        mc = uid_to_machine_code(w0, w1, w2)
        hi, lo, st = calc(mc)
        show("", mc, hi, lo, st, order)
        emu = emu_check((w0, w1, w2), a.firmware)
        if emu and emu != (hi, lo):
            print("  [警告] 交叉验证不一致, 以仿真结果为准:", emu)
        if a.write_e:
            write_e_drive(hi, lo)
        return

    # 交互模式
    print("  直接粘贴即可(机器码 或 ID: xxx xxx xxx), q 退出")
    while True:
        try:
            s = input("\n  机器码/UID> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if s.lower() in ("q", "quit", "exit", ""):
            break
        try:
            handle_line(s)
        except Exception as e:
            print(f"  [解析失败] {e}   请检查输入")


if __name__ == "__main__":
    main()
