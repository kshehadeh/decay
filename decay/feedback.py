
def generic_msg(msg, indent=0):
    print((indent * 2) * ' ' + msg)


def info(msg, indent=0):
    if indent == 0:
        generic_msg("🚩 " + msg, 0)
    else:
        generic_msg("→ " + msg, indent)


def success(msg, indent=0):
    generic_msg("✅ " + msg, indent)


def warning(msg, indent=0):
    generic_msg("⚠️ " + msg, indent)


def error(msg, indent=0):
    generic_msg("❌ " + msg, indent)

