import py_compile
import traceback

try:
    py_compile.compile("chat/views.py", doraise=True)
    print("chat/views.py syntax is OK")
except py_compile.PyCompileError as e:
    print("SyntaxError in chat/views.py:")
    print(e)
except Exception as e:
    print("Other error:")
    traceback.print_exc()
