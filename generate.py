import qrcode
from PIL import Image
from io import BytesIO
import base64
import json
from http.server import BaseHTTPRequestHandler


# 处理请求的主类
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 解析 URL 查询参数（如 ?content=xxx&size=300）
        from urllib.parse import urlparse, parse_qs
        params = parse_qs(urlparse(self.path).query)

        # 提取参数（默认值处理）
        content = params.get('content', ['https://vercel.com'])[0]
        size = int(params.get('size', [300])[0])
        fg_color = params.get('fg_color', ['#000000'])[0]
        bg_color = params.get('bg_color', ['#FFFFFF'])[0]
        border = int(params.get('border', [4])[0])

        # 参数校验
        error_msg = None
        if not content.strip():
            error_msg = "二维码内容不能为空"
        elif size < 100 or size > 1000:
            error_msg = "尺寸必须在 100-1000px 之间"

        if error_msg:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": error_msg}).encode())
            return

        try:
            # 生成二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=border
            )
            qr.add_data(content)
            qr.make(fit=True)

            # 处理 Pillow 版本兼容的缩放算法
            if hasattr(Image, 'Resampling'):
                resize_method = Image.Resampling.LANCZOS
            else:
                resize_method = Image.LANCZOS

            img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert('RGB')
            img = img.resize((size, size), resize_method)

            # 转换为 Base64 图片
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # 返回响应（支持跨域）
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # 允许跨域
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "data": f"data:image/png;base64,{img_base64}"
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"生成失败：{str(e)}"}).encode())