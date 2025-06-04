import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os

class BuscadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador Inteligente com Edição")
        self.root.geometry("1000x600")

        self.files = []
        self.busca_count = {}
        self.result_refs = {}

        busca_frame = tk.Frame(root)
        busca_frame.pack(pady=5, fill=tk.X)

        tk.Label(busca_frame, text="Palavra-chave:").pack(side=tk.LEFT, padx=5)
        self.keyword_entry = tk.Entry(busca_frame, width=50)
        self.keyword_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(busca_frame, text="Buscar", command=self.buscar).pack(side=tk.LEFT, padx=5)

        botoes_frame = tk.Frame(root)
        botoes_frame.pack(pady=5, fill=tk.X)

        tk.Button(botoes_frame, text="Selecionar Arquivos", command=self.selecionar_arquivos).pack(side=tk.LEFT, padx=5)
        tk.Button(botoes_frame, text="Criar Novo Campo", command=self.criar_novo_campo).pack(side=tk.LEFT, padx=5)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

    def selecionar_arquivos(self):
        arquivos = filedialog.askopenfilenames(filetypes=[("Excel files", "*.xlsx *.xls")])
        if arquivos:
            for arq in arquivos:
                if arq not in self.files:
                    self.files.append(arq)
                    self.criar_tabela(arq)

    def criar_tabela(self, arquivo):
        try:
            df = pd.read_excel(arquivo, engine='openpyxl')
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir o arquivo {arquivo}:\n{e}")
            return

        frame = tk.Frame(self.notebook)
        self.notebook.add(frame, text=os.path.basename(arquivo))

        tree = ttk.Treeview(frame, columns=list(df.columns), show='headings')
        tree.pack(fill=tk.BOTH, expand=True)

        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')

        for _, row in df.iterrows():
            tree.insert('', 'end', values=list(row))

    def criar_novo_campo(self):
        janela = tk.Toplevel(self.root)
        janela.title("Criar Novo Campo")
        janela.geometry("300x200")
        janela.grab_set()

        tk.Label(janela, text="Selecione o tipo do formulário:", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Button(janela, text="Contatos das Operadoras", width=30,
                  command=lambda: [self.abrir_form_contatos(), janela.destroy()]).pack(pady=5)

        tk.Button(janela, text="Designações dos Links", width=30,
                  command=lambda: [self.abrir_form_designacoes(), janela.destroy()]).pack(pady=5)

        tk.Button(janela, text="Chamados de Operadoras Abertas/Fechados", width=30,
                  command=lambda: [self.abrir_form_chamados(), janela.destroy()]).pack(pady=5)

    def abrir_form_contatos(self):
        campos = [
            "Operadora", "Links", "User", "Senha",
            "E-mail", "Telefone", "OBS", "CNPJ", "Pontos importantes"
        ]
        self.abrir_formulario("Contatos das Operadoras", campos, r"C:\Script\Operadoras.xlsx")

    def abrir_form_designacoes(self):
        campos = [
            "Operadora", "Unidade", "Link",
            "Designação", "Geo"
        ]
        self.abrir_formulario("Designações dos Links", campos, r"C:\Script\Circuitos e Designações.xlsx")

    def abrir_form_chamados(self):
        campos = [
            "Analista", "Unidade", "Protocolo", "Incidente", "Causa",
            "Operadora", "Data/Hora de Abertura", "Data/Hora de Encerramento",
            "SLA", "Ponto Importantes"
        ]
        self.abrir_formulario("Chamados de Operadoras Abertas/Fechados", campos, r"C:\Script\Chamados de Operadoras Abertas Fechados.xlsx")

    def abrir_formulario(self, titulo, campos, caminho_arquivo):
        form = tk.Toplevel(self.root)
        form.title(f"Formulário: {titulo}")
        form.geometry("500x500")
        form.grab_set()

        canvas = tk.Canvas(form)
        scrollbar = ttk.Scrollbar(form, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.entries = {}

        for i, campo in enumerate(campos):
            tk.Label(scroll_frame, text=campo + ":").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            if campo.lower() in ["obs", "pontos importantes", "ponto importantes"]:
                txt = tk.Text(scroll_frame, width=40, height=4)
                txt.grid(row=i, column=1, padx=5, pady=5)
                self.entries[campo] = txt
            else:
                ent = tk.Entry(scroll_frame, width=50)
                ent.grid(row=i, column=1, padx=5, pady=5)
                self.entries[campo] = ent

        btn_salvar = tk.Button(scroll_frame, text="Salvar",
                               command=lambda: self.salvar_em_excel(form, caminho_arquivo, campos))
        btn_salvar.grid(row=len(campos), column=0, columnspan=2, pady=10)

    def salvar_em_excel(self, form, caminho_arquivo, campos):
        dados = {}
        for campo, widget in self.entries.items():
            if isinstance(widget, tk.Text):
                dados[campo] = widget.get("1.0", "end").strip()
            else:
                dados[campo] = widget.get().strip()

        pasta = os.path.dirname(caminho_arquivo)
        if not os.path.exists(pasta):
            os.makedirs(pasta)

        if os.path.exists(caminho_arquivo):
            try:
                df = pd.read_excel(caminho_arquivo, engine='openpyxl')
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler arquivo Excel:\n{e}")
                return
        else:
            df = pd.DataFrame(columns=campos)

        nova_linha = {campo: dados.get(campo, "") for campo in campos}
        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)

        try:
            df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
            messagebox.showinfo("Sucesso", f"Dados salvos em:\n{caminho_arquivo}")
            form.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar arquivo Excel:\n{e}")

    def buscar(self):
        palavra_chave = self.keyword_entry.get().strip().lower()

        if not palavra_chave:
            messagebox.showwarning("Aviso", "Por favor, digite uma palavra-chave para buscar.")
            return

        for i, arquivo in enumerate(self.files):
            try:
                df = pd.read_excel(arquivo, engine='openpyxl')
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler {arquivo}:\n{e}")
                continue

            resultados = df.applymap(lambda x: palavra_chave in str(x).lower() if pd.notnull(x) else False)
            linhas_encontradas = df[resultados.any(axis=1)]

            aba = self.notebook.tabs()[i]
            self.notebook.select(i)

            if linhas_encontradas.empty:
                messagebox.showinfo("Busca", f"Nenhum resultado encontrado em: {os.path.basename(arquivo)}")
            else:
                frame = self.notebook.nametowidget(aba)
                tree = frame.winfo_children()[0]
                tree.delete(*tree.get_children())

                for _, row in linhas_encontradas.iterrows():
                    tree.insert('', 'end', values=list(row))

                messagebox.showinfo("Busca", f"{len(linhas_encontradas)} resultado(s) encontrado(s) em {os.path.basename(arquivo)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BuscadorApp(root)
    root.mainloop()
