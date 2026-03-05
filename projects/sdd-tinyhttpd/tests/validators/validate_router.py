"""
tests/validators/validate_router.py
校验 router 模块输出与fixture基准一致

注意：router依赖文件系统（htdocs/），需在项目根目录运行。
"""
import os, pickle, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

MODULE_NAME = "router"
FIXTURES = Path(__file__).parent.parent / "fixtures"

# 切换到项目根目录确保htdocs路径正确
PROJECT_ROOT = Path(__file__).parent.parent.parent
os.chdir(PROJECT_ROOT)


def main():
    print(f"{'='*50}\n校验器: {MODULE_NAME}\n{'='*50}")

    ref = pickle.loads((FIXTURES / f"reference_{MODULE_NAME}_output.pkl").read_bytes())
    cases = ref["cases"]

    from modules.router.router import resolve_path, should_use_cgi, route

    errs = []

    # 校验 resolve_path
    for key in ["resolve_root", "resolve_file", "resolve_subdir"]:
        c = cases[key]
        actual = resolve_path(c["url"])
        expected = c["expected_path"]
        if actual != expected:
            errs.append(f"resolve_path({c['url']!r}): 期望 {expected!r}，实际 {actual!r}")

    # 校验 should_use_cgi（不依赖文件存在性）
    for key in ["cgi_post", "cgi_query"]:
        c = cases[key]
        actual = should_use_cgi(c["path"], c["method"], c["qs"])
        if actual != c["expected_cgi"]:
            errs.append(f"should_use_cgi({key}): 期望 {c['expected_cgi']}，实际 {actual}")

    # 校验 path traversal 防护（route返回exists=False）
    c = cases["path_traversal"]
    result = route("GET", c["url"], "")
    if result.get("exists") is not False:
        errs.append(f"path_traversal: 期望 exists=False，实际 {result}")

    # 校验 static case（使用临时文件）
    c = cases["static"]
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        htdocs = Path(tmpdir) / "htdocs"
        htdocs.mkdir()
        # 创建无执行权限的普通文件
        test_file = htdocs / "index.html"
        test_file.write_text("<html>test</html>")
        os.chmod(test_file, 0o644)
        actual = should_use_cgi(str(test_file), "GET", "")
        os.chdir(old_cwd)
        if actual != c["expected_cgi"]:
            errs.append(f"should_use_cgi(static): 期望 {c['expected_cgi']}，实际 {actual}")

    if not errs:
        print(f"✅ 通过 — 全部路由规则验证通过")
        sys.exit(0)
    else:
        print(f"❌ 失败 {len(errs)} 处:")
        for e in errs:
            print(f"  • {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
