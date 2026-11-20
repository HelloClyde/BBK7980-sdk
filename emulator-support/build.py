"""Build the portable native CPU/board library without changing machine settings."""
from pathlib import Path
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def build():
    compiler = shutil.which("gcc")
    if not compiler:
        raise RuntimeError("GCC not found. Install MSYS2 UCRT64 GCC or add gcc to PATH.")
    out = ROOT / "bbk7980.dll"
    env = os.environ.copy()
    env["PATH"] = str(Path(compiler).parent) + os.pathsep + env.get("PATH", "")
    subprocess.run([compiler, "-O2", "-std=gnu11", "-shared", "-static-libgcc",
                    "-Wall", "-Wextra", str(ROOT / "src/machine.c"), "-o", str(out)],
                   check=True, cwd=ROOT, env=env)
    print(out)


if __name__ == "__main__":
    build()
