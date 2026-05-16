class CRCEngine:
    """
    CRC (循环冗余校验) 核心算法引擎。
    
    该类负责执行 CRC 的数学运算逻辑，将其与 GUI 渲染层分离。
    主要任务是将原始二进制数据和生成多项式转换为结构化的运算步骤数据，以便后续可视化。
    """

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
                 - q: 商字符串 (str)
                 - rows: 包含运算步骤的字典列表 (list of dict)
                 - dividend: 补零后的被除数 (str)
        """
        # 基础输入验证
        if not data or not divisor or divisor[0] == '0':
            return "", [], ""

        n = len(divisor)
        pad_len = n - 1  # 需补零的长度
        dividend = data + "0" * pad_len  # 补零后的被除数
        q = ""  # 商
        rem = dividend  # 当前余数（迭代过程中不断更新）
        rows = []  # 记录每一行绘制信息
        last_i = 0  # 记录最后一次发生 XOR 的位置，用于确定最终余数行

        # 遍历被除数进行长除法
        for i in range(len(dividend) - n + 1):
            if rem[i] == '1':
                # 当前位为 1，上商 1
                q += '1'
                
                # 记录参与运算的行
                if i > 0:
                    # 记录从上方掉下来的数据行（当前运算的基数）
                    rows.append({'type': 'working', 'val': rem[i:i+n], 'offset': i})
                
                # 记录除数对齐行
                rows.append({'type': 'divisor', 'val': divisor, 'offset': i})
                
                # 记录减法横线（XOR 线）
                rows.append({'type': 'line', 'offset': i, 'len': n})

                # 执行 XOR 运算：二进制减法即异或
                xor_part = "".join('0' if rem[i+j] == divisor[j] else '1' for j in range(n))
                
                # 更新全局余数状态
                rem = rem[:i] + xor_part + rem[i+n:]
                last_i = i
            else:
                # 当前位为 0，上商 0，不做 XOR，直接看下一位
                q += '0'

        # 最终余数提取（除法结束后的最后结果）
        rows.append({
            'type': 'remainder',
            'val': rem[last_i:last_i+n],
            'offset': last_i
        })
        
        return q, rows, dividend
