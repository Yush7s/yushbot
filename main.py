import tkinter as tk
from tkinter import ttk, messagebox

from osint_logic import resolve_dns, get_ip_info, search_username, phone_lookup

# ---------------- GUI HELPERS ---------------- #


def limpar_resultado():
    resultado.delete("1.0", tk.END)


def dns_lookup():
    dominio = entrada.get()
    if not dominio:
        messagebox.showerror("Erro", "Digite um dominio")
        return
    try:
        ip = resolve_dns(dominio)
        limpar_resultado()
        resultado.insert(tk.END, f"IP encontrado: {ip}")
    except Exception:
        messagebox.showerror("Erro", "Falha ao resolver DNS")


def ip_info():
    ip = entrada.get()
    if not ip:
        messagebox.showerror("Erro", "Digite um IP")
        return
    try:
        info = get_ip_info(ip)
        limpar_resultado()
        for k, v in info.items():
            resultado.insert(tk.END, f"{k}: {v}\n")
    except Exception:
        messagebox.showerror("Erro", "Falha na consulta")


def username_search():
    username = entrada.get()
    if not username:
        messagebox.showerror("Erro", "Digite um username")
        return

    limpar_resultado()
    resultado.insert(tk.END, f"Resultados para username: {username}\n\n")

    results = search_username(username)
    for r in results:
        if r["status"] == "found":
            resultado.insert(tk.END, f"[+] {r['site']}: {r['url']}\n")
        elif r["status"] == "not_found":
            resultado.insert(tk.END, f"[-] {r['site']}: nao encontrado\n")
        else:
            resultado.insert(tk.END, f"[!] {r['site']}: erro na requisicao\n")


def phone_search():
    number = entrada.get()
    if not number:
        messagebox.showerror("Erro", "Digite um numero de telefone")
        return
    try:
        info = phone_lookup(number)
        limpar_resultado()
        resultado.insert(tk.END, f"Resultados para numero: {number}\n\n")
        for k, v in info.items():
            resultado.insert(tk.END, f"{k}: {v}\n")
    except ValueError as e:
        messagebox.showerror("Erro", str(e))
    except Exception:
        messagebox.showerror("Erro", "Falha na consulta do numero")


# ---------------- INTERFACE ---------------- #

janela = tk.Tk()
janela.title("Painel OSINT! Github: NicholasDev01")
janela.geometry("760x540")
janela.configure(bg="#1e1e2f")

style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure(
    "TLabel", background="#1e1e2f", foreground="white", font=("Segoe UI", 11)
)

titulo = ttk.Label(
    janela,
    text="Painel OSINT! Github: NicholasDev01",
    font=("Segoe UI", 16, "bold"),
)
titulo.pack(pady=10)

frame_input = tk.Frame(janela, bg="#1e1e2f")
frame_input.pack(pady=5)

ttk.Label(frame_input, text="Dominio / IP / Username / Telefone:").pack(
    side=tk.LEFT, padx=5
)
entrada = ttk.Entry(frame_input, width=42)
entrada.pack(side=tk.LEFT, padx=5)

frame_botoes = tk.Frame(janela, bg="#1e1e2f")
frame_botoes.pack(pady=10)

ttk.Button(frame_botoes, text="DNS Lookup", command=dns_lookup).pack(
    side=tk.LEFT, padx=4
)
ttk.Button(frame_botoes, text="IP Info", command=ip_info).pack(side=tk.LEFT, padx=4)
ttk.Button(frame_botoes, text="Username", command=username_search).pack(
    side=tk.LEFT, padx=4
)
ttk.Button(frame_botoes, text="Telefone", command=phone_search).pack(
    side=tk.LEFT, padx=4
)

resultado = tk.Text(
    janela,
    width=90,
    height=20,
    bg="#041225",
    fg="#38bdf8",
    insertbackground="white",
    font=("Consolas", 10),
)
resultado.pack(padx=10, pady=10)

rodape = ttk.Label(
    janela, text="OSINT - Uso educacional e legal! Github: NicholasDev01"
)
rodape.pack(pady=5)

janela.mainloop()
