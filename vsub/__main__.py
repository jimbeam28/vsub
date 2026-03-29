"""Entry point for python -m vsub"""

import sys

from vsub.cli import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"致命错误: {e}", file=sys.stderr)
        sys.exit(1)
