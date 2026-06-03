class BaseExporter:
    """
    所有导出格式处理器的抽象基类。
    
    统一约束了物理写盘 (save) 与文件体积粗估/精算 (estimate_size) 的核心接口，
    为 CRC 导出引擎提供可插拔式的插件机制。
    """
    @staticmethod
    def save(app, out_path, show_border, color_mode, **kwargs):
        """
        物理写盘保存的核心入口方法。
        
        参数:
            app: 主应用程序实例对象。
            out_path: 目标导出的物理存储路径。
            show_border: 是否在图表周边绘制一圈黑色纸张边框线。
            color_mode: 导出的色彩模式（彩色、灰度、黑白）。
            kwargs: 其他可选的多格式差异化配置参数。
        """
        raise NotImplementedError("子导出器必须实现此 save 方法。")

    @staticmethod
    def estimate_size(app, data, dividend, divisor, q, rows, ctx, color_mode, show_border, **kwargs):
        """
        测算并估计最终物理文件字节大小的入口方法。
        
        参数:
            app: 主应用程序实例对象。
            data: 用户输入的数据位二进制字串。
            dividend: 内部补零后的被除数字串。
            divisor: 内部除数字串。
            q: 长除法计算结果商。
            rows: 长除法各步骤对应的结构化渲染数据。
            ctx: 当前视图的绘制排版缩放上下文。
            color_mode: 导出的色彩模式。
            show_border: 是否显示纸张边框。
            kwargs: 差异化参数（如 multipliers、dpis 等）。
            
        返回:
            str: 格式化后的文件大小估计文本（例如 "12.45 KB" 或 "无法估计"）。
        """
        raise NotImplementedError("子导出器必须实现此 estimate_size 方法。")
