import PyInstaller.__main__
import customtkinter
import os
import sys

# 1. Identifica o caminho da biblioteca CustomTkinter
ctk_path = os.path.dirname(customtkinter.__file__)

# 2. Define o separador correto (Ponto e vírgula para Windows, Dois pontos para Linux/Mac)
separator = ';' if sys.platform.startswith("win") else ':'

# 3. Configurações do PyInstaller
print("Iniciando a criação do executável...")
print(f"Incluindo arquivos do CustomTkinter de: {ctk_path}")

PyInstaller.__main__.run([
    'APP Cobrança parcelada.py',  # Nome do seu arquivo principal
    '--name=JPY_System_2026',  # Nome do Executável que será gerado
    '--onefile',  # Gera um único arquivo .exe (não uma pasta cheia de arquivos)
    '--noconsole',  # Não abre a tela preta (cmd) ao fundo
    '--windowed',  # Modo janela (igual ao noconsole)
    '--clean',  # Limpa caches antigos

    # Esta linha é CRUCIAL para o CustomTkinter funcionar:
    f'--add-data={ctk_path}{separator}customtkinter/',

    # Opcional: Se você tiver um ícone .ico, descomente a linha abaixo e coloque o nome do arquivo
    # '--icon=seu_icone.ico',
])

print("\n---------------------------------------------------------")
print("SUCESSO! O executável foi criado.")
print("Verifique a pasta 'dist' que apareceu no diretório.")
print("---------------------------------------------------------")