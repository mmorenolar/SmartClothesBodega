"""Arranque de la aplicación de escritorio."""

import tkinter as tk
from tkinter import messagebox

from smartclothes.modelo.errores import PersistenciaError


def main() -> None:
    try:
        from smartclothes.vista.aplicacion import iniciar

        iniciar()
    except PersistenciaError as error:
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror("Smart Clothes", str(error))
        raiz.destroy()


if __name__ == "__main__":
    main()
