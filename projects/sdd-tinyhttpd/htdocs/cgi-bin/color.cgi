#!/usr/bin/env python3
# CGI 示例：回显 POST 参数中的 color 字段
import sys, urllib.parse

print("Content-Type: text/html\r")
print("\r")
print("<html><body>")

body = sys.stdin.read()
params = urllib.parse.parse_qs(body)
color = params.get("color", ["unknown"])[0]
print(f"<h1 style='color:{color}'>Color: {color}</h1>")
print("</body></html>")
