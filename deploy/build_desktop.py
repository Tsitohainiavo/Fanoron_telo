# deploy/build_desktop.py
"""Build de l'exécutable standalone avec PyInstaller (Windows, macOS, Linux)."""

import PyInstaller.__main__
import os
import shutil
import sys
from pathlib import Path

APP_NAME = "FanoronTelo"

def build():
    # Nettoyage
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)
    spec_file = f"{APP_NAME}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # Chemin racine du projet (là où se trouve fanorontelo.py)
    root_dir = Path(__file__).parent.parent

    # Arguments de PyInstaller
    args = [
        str(root_dir / "fanorontelo.py"),  # script principal
        "--name", APP_NAME,
        "--onedir",
        "--windowed",                     # sans console sur Windows
        "--clean",
    ]

    # Ajout de tous les modules Python du projet
    for module in [
        "constants.py",
        "engine.py",
        "buttons.py",
        "game_view.py",
        "accueil.py",
        "alphabeta.py",
        "moteur_ia.py"
    ]:
        src = str(root_dir / module)
        args += ["--add-data", f"{src}{os.pathsep}."]

    # Icône selon la plateforme
    if sys.platform == "win32":
        icon = root_dir / "icon.ico"
        if icon.exists():
            args += ["--icon", str(icon)]
    elif sys.platform == "darwin":
        icon = root_dir / "icon.icns"
        if icon.exists():
            args += ["--icon", str(icon)]
    else:
        icon = root_dir / "icon.png"
        if icon.exists():
            args += ["--icon", str(icon)]

    PyInstaller.__main__.run(args)
    print(f"\nBuild terminé ! L'application se trouve dans dist/{APP_NAME}/")

if __name__ == "__main__":
    build()