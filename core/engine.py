class CRCEngine:
    """
    CRC (循环冗余校验) 核心算法引擎。

    该类负责执行 CRC 的数学运算逻辑，将其与 GUI 渲染层分离。
    主要任务是将原始二进制数据和生成多项式转换为结构化的运算步骤数据，以便后续可视化。
    """

    @staticmethod
    def _process_xor_step(rem, i, n, divisor, rows):
        """
        处理单步二进制除法的异或（XOR）运算及绘图信息收集。

        提取此函数以将 calculate 主干业务与具体的步骤生成逻辑解耦，
        提高代码的可读性。
        """
        # 1. 记录从上方移位下落的数据行（仅在非首步时需要，作为当前运算的基数）
        if i > 0:
            rows.append({"type": "working", "val": rem[i : i + n], "offset": i})

        # 2. 记录除数对齐行与减法横线
        rows.append({"type": "divisor", "val": divisor, "offset": i})
        rows.append({"type": "line", "offset": i, "len": n})

        # 3. 执行 XOR 运算：二进制减法即异或
        xor_part = "".join("0" if rem[i + j] == divisor[j] else "1" for j in range(n))

        # 4. 返回拼接后的新全局余数
        return rem[:i] + xor_part + rem[i + n :]

    @staticmethod
    def calculate(data, divisor):
        """
        执行二进制 CRC 长除法计算。

        计算过程遵循以下标准步骤：
        1. 补零：在原始数据末尾附加 (n-1) 个零，其中 n 是多项式长度。
        2. 移位对齐：寻找第一个 '1'，与其对齐多项式进行 XOR 运算。
        3. 迭代：重复 XOR 过程直到处理完所有数据位。
        4. 提取余数：最终剩余的 (n-1) 位即为 CRC 校验码。

        :param data: 原始二进制字符串 (例如 "110101")
        :param divisor: 生成多项式字符串 (例如 "1011")
        :return: 元组 (q, rows, dividend)
        """
        # 基础输入验证
        if not data or not divisor or divisor[0] == "0":
            return "", [], ""

        n = len(divisor)
        dividend = data + "0" * (n - 1)  # 补零后的被除数
        q = ""  # 商
        rem = dividend  # 当前余数（迭代过程中不断更新）
        rows = []  # 记录每一行绘制信息
        last_i = 0  # 记录最后一次发生 XOR 的位置

        # 遍历被除数进行长除法
        for i in range(len(dividend) - n + 1):
            if rem[i] == "1":
                q += "1"
                rem = CRCEngine._process_xor_step(rem, i, n, divisor, rows)
                last_i = i
            else:
                q += "0"

        # 最终余数提取（除法结束后的最后结果，获取自 last_i 至被除数末尾的全部余数）
        rows.append({"type": "remainder", "val": rem[last_i:], "offset": last_i})

        # 优化减法横线的长度，使其自动适应并向右延伸覆盖下方被拉下来的数字
        for idx, row in enumerate(rows):
            if row["type"] == "line" and idx + 1 < len(rows):
                next_row = rows[idx + 1]
                if next_row["type"] in ("working", "remainder"):
                    end_col = max(row["offset"] + n, next_row["offset"] + len(next_row["val"]))
                    row["len"] = end_col - row["offset"]

        return q, rows, dividend

    @staticmethod
    def verify(frame, divisor):
        """
        执行接收端的二进制 CRC 校验计算（无需补零）。

        接收端将收到的完整数据帧 (包含数据位 + 校验码) 直接除以生成多项式：
        - 若传输无误，模二长除法余数全为 0 (可整除)；
        - 若发生传输错误，余数不为 0 (不可整除)，能有效发现错误。

        :param frame: 接收到的二进制数据帧字符串 (例如 "1101010110" 或带错的 "1101011100")
        :param divisor: 生成多项式字符串 (例如 "1011")
        :return: 元组 (q, rows, frame, remainder_bits, is_valid)
        """
        if not frame or not divisor or divisor[0] == "0" or len(frame) < len(divisor):
            return "", [], frame, "", False

        n = len(divisor)
        q = ""
        rem = frame
        rows = []
        last_i = 0

        for i in range(len(frame) - n + 1):
            if rem[i] == "1":
                q += "1"
                rem = CRCEngine._process_xor_step(rem, i, n, divisor, rows)
                last_i = i
            else:
                q += "0"

        # 最终余数行
        rows.append({"type": "remainder", "val": rem[last_i:], "offset": last_i})

        # 横线长度调整
        for idx, row in enumerate(rows):
            if row["type"] == "line" and idx + 1 < len(rows):
                next_row = rows[idx + 1]
                if next_row["type"] in ("working", "remainder"):
                    end_col = max(row["offset"] + n, next_row["offset"] + len(next_row["val"]))
                    row["len"] = end_col - row["offset"]

        # 提取固定长度 (n - 1 位) 的最终余数
        rem_raw = rem[last_i:]
        n_bits = n - 1
        remainder_bits = rem_raw[-n_bits:] if len(rem_raw) >= n_bits else rem_raw.zfill(n_bits)
        is_valid = all(c == "0" for c in remainder_bits)

        return q, rows, frame, remainder_bits, is_valid
