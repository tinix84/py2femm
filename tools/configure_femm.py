"""Interactive FEMM path configuration (called by setup_femm.bat)."""

from pathlib import Path

import yaml

FEMM_SEARCH_PATHS = [
    Path(r"C:\femm42\bin\femm.exe"),
    Path(r"C:\Program Files\femm42\bin\femm.exe"),
    Path(r"C:\Program Files (x86)\femm42\bin\femm.exe"),
]

CONFIG_PATH = Path("config/default.yml")


def main():
    # Auto-detect
    femm_path = None
    for candidate in FEMM_SEARCH_PATHS:
        if candidate.exists():
            femm_path = candidate
            print(f"  [OK] FEMM found: {femm_path}")
            break

    if femm_path is None:
        print("  FEMM not found in standard locations.")
        user_path = input("  Enter path to femm.exe: ").strip()
        if not user_path:
            print("  [ERROR] No path provided.")
            raise SystemExit(1)
        femm_path = Path(user_path)
        if not femm_path.exists():
            print(f"  [ERROR] File not found: {femm_path}")
            raise SystemExit(1)

    # Workspace
    default_ws = r"C:\femm_workspace"
    ws = input(f"  Workspace directory [{default_ws}]: ").strip() or default_ws

    # Save config
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if CONFIG_PATH.exists():
        cfg = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    cfg.setdefault("femm", {})
    cfg["femm"]["path"] = str(femm_path)
    cfg.setdefault("agent", {})
    cfg["agent"]["workspace"] = ws

    CONFIG_PATH.write_text(yaml.dump(cfg, default_flow_style=False, sort_keys=False))
    print(f"  Configuration saved to {CONFIG_PATH}")


if __name__ == "__main__":
    main()
