# Importamos a biblioteca pandas, essencial para ler ficheiros CSV
import pandas as pd
import os

# 1. Atualizámos os caminhos exatos onde os teus ficheiros CSV realmente estão (no OneDrive)
# Usamos o 'r' antes das aspas para o Python ler as barras invertidas (\) corretamente no Windows
caminho_sources = r'C:\Users\Lenovo\OneDrive\Documents\INITIUM\Master IR & GE\Final Master Thesis\_DATABASE\csv_exports\_sources.csv'
caminho_relatorio_saida = r'C:\Users\Lenovo\OneDrive\Documents\INITIUM\Master IR & GE\Final Master Thesis\_DATABASE\csv_exports\documentos_sem_licenca.csv'

def auditar_licencas():
    print("A iniciar auditoria de licenças pelo agente SCOUT...")
    
    try:
        # 2. Lemos o ficheiro CSV a partir da nova morada correta
        df = pd.read_csv(caminho_sources)
        
        # 3. Verificamos se a coluna 'license' (licença) já existe.
        if 'license' not in df.columns:
            print("Aviso: Coluna 'license' não encontrada. A criar coluna vazia no ficheiro...")
            # Criamos a coluna com valores vazios (None)
            df['license'] = None 
            # Guardamos o CSV original atualizado com a nova coluna
            df.to_csv(caminho_sources, index=False)
            
        # 4. Agora procuramos quem não tem licença (valores nulos ou vazios)
        sem_licenca = df[df['license'].isna() | (df['license'] == '')]
        total_faltosos = len(sem_licenca)
        
        print(f"Foram encontrados {total_faltosos} documentos sem licença registada.")
        
        # 5. Se houver documentos sem licença, guardamos uma lista à parte
        if total_faltosos > 0:
            sem_licenca.to_csv(caminho_relatorio_saida, index=False)
            print(f"Relatório de ação gerado com sucesso em:")
            print(caminho_relatorio_saida)
            print("Por favor, abre este ficheiro gerado e preenche as licenças manualmente.")
            
    except FileNotFoundError:
        print(f"Erro Crítico: O ficheiro não foi encontrado em: {caminho_sources}")
    except PermissionError:
        print("Erro de Permissão: O ficheiro CSV está aberto noutro programa (ex: Excel). Fecha-o e tenta novamente.")

# Executar a função principal
if __name__ == "__main__":
    auditar_licencas()