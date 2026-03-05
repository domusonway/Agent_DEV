#!/usr/bin/env python3
import os
qs = os.environ.get('QUERY_STRING', '')
print("Content-Type: text/html")
print()
print(f"<html><body><h1>CGI Hello!</h1><p>query={qs}</p></body></html>")
