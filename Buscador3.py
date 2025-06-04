import pandas as pd

def carregar_dados(arquivo):
    try:
        df = pd.read_excel(arquivo)
        print(f"\n✅ {len(df)} registros carregados com sucesso.")
        return df
    except Exception as e:
        print(f"❌ Erro ao carregar o arquivo: {e}")
        return None

def buscar(df, termo):
    termo = termo.lower()
    resultados = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(termo).any(), axis=1)]
    return resultados

def menu_busca(df):
    while True:
        termo = input("\n🔍 Digite um termo para buscar (ou 'sair' para encerrar): ").strip()
        if termo.lower() == 'sair':
            print("Encerrando busca.")
            break
        resultados = buscar(df, termo)
        if resultados.empty:
            print("⚠️ Nenhum resultado encontrado.")
        else:
            print(f"\n🔎 {len(resultados)} resultado(s) encontrado(s):\n")
            print(resultados.to_string(index=False))

if __name__ == "__main__":
    arquivo_excel = "Operadoras.xlsx"
    df_dados = carregar_dados(arquivo_excel)
    
    if df_dados is not None:
        menu_busca(df_dados)
