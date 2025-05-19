#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora de Consumo Energético Residencial
Módulo principal que implementa a interface de usuário e fluxo lógico do programa.
Este módulo utiliza as funções definidas no módulo 'funcoes_energia.py'.

Autores: [Seus nomes aqui]
Data: 19/05/2025
"""

import os
import time
import matplotlib.pyplot as plt
from Defs import (
    APARELHOS_PADRAO,
    adicionarAparelho,
    listarAparelhos,
    calcularConsumoDiario,
    calcularConsumoMensal,
    calcularCustoMensal,
    gerarGraficoBarrasDiario,
    gerarGraficoBarrasMensal,
    gerarGraficoPizzaDiario,
    gerarGraficoPizzaMensal,
    estimarClassificacao,
    gerarDicasEconomia
)

# Configurações globais
TARIFA_PADRAO = 0.75  # Valor em R$ por kWh (média Brasil)
PASTA_GRAFICOS = "graficos"


def limpar_tela():
    """Limpa a tela do terminal para melhor visualização"""
    # Comando para Windows
    if os.name == 'nt':
        os.system('cls')
    # Comando para Unix/Linux/MacOS
    else:
        os.system('clear')


def exibir_cabecalho():
    """Exibe o cabeçalho do programa"""
    print("=" * 80)
    print("📊 CALCULADORA DE CONSUMO ENERGÉTICO RESIDENCIAL 📊".center(80))
    print("=" * 80)
    print("Entenda seu consumo de energia e economize na conta de luz!\n")


def exibir_menu_principal():
    """Exibe o menu principal do programa"""
    print("\n" + "-" * 40)
    print("MENU PRINCIPAL".center(40))
    print("-" * 40)
    print("[1] Usar lista padrão de aparelhos")
    print("[2] Começar com lista vazia")
    print("[3] Carregar lista salva")
    print("[4] Sobre o programa")
    print("[0] Sair")
    print("-" * 40)


def exibir_menu_operacoes(lista_aparelhos):
    """Exibe o menu de operações quando uma lista está ativa"""
    print("\n" + "-" * 40)
    print("GERENCIAMENTO DE APARELHOS".center(40))
    print("-" * 40)
    print(f"Total de aparelhos cadastrados: {len(lista_aparelhos)}")
    print("-" * 40)
    print("[1] Listar aparelhos")
    print("[2] Adicionar novo aparelho")
    print("[3] Remover aparelho")
    print("[4] Visualizar consumo diário")
    print("[5] Visualizar consumo mensal")
    print("[6] Calcular custo mensal (R$)")
    print("[7] Gerar gráficos")
    print("[8] Dicas de economia")
    print("[9] Salvar lista")
    print("[0] Voltar ao menu principal")
    print("-" * 40)


def exibir_menu_graficos():
    """Exibe o menu de opções de gráficos"""
    print("\n" + "-" * 40)
    print("GERAÇÃO DE GRÁFICOS".center(40))
    print("-" * 40)
    print("[1] Gráfico de barras - Consumo diário")
    print("[2] Gráfico de barras - Consumo mensal")
    print("[3] Gráfico de pizza - Distribuição diária")
    print("[4] Gráfico de pizza - Distribuição mensal")
    print("[5] Gerar todos os gráficos")
    print("[0] Voltar")
    print("-" * 40)


def adicionar_novo_aparelho(lista_aparelhos):
    """Solicita dados ao usuário e adiciona um novo aparelho à lista"""
    limpar_tela()
    exibir_cabecalho()
    print("📝 ADICIONAR NOVO APARELHO\n")

    nome = input("Nome do aparelho: ")

    try:
        potencia = float(input("Potência (em Watts): "))
        horas = float(input("Tempo médio de uso diário (em horas): "))
        quantidade = int(input("Quantidade deste aparelho: "))

        lista_aparelhos = adicionarAparelho(lista_aparelhos, nome, potencia, horas, quantidade)
        print("\n✅ Aparelho adicionado com sucesso!")

    except ValueError as erro:
        print(f"\n❌ Erro: {erro}")

    input("\nPressione ENTER para continuar...")
    return lista_aparelhos


def remover_aparelho(lista_aparelhos):
    """Remove um aparelho da lista"""
    limpar_tela()
    exibir_cabecalho()
    print("🗑️ REMOVER APARELHO\n")

    if not lista_aparelhos:
        print("Não há aparelhos cadastrados.")
        input("\nPressione ENTER para continuar...")
        return lista_aparelhos

    print(listarAparelhos(lista_aparelhos))

    try:
        indice = int(input("\nDigite o número do aparelho que deseja remover (1-" +
                           str(len(lista_aparelhos)) + "): ")) - 1

        if 0 <= indice < len(lista_aparelhos):
            aparelho_removido = lista_aparelhos.pop(indice)
            print(f"\n✅ Aparelho '{aparelho_removido['nome']}' removido com sucesso!")
        else:
            print("\n❌ Índice inválido!")

    except ValueError:
        print("\n❌ Por favor, digite um número válido.")

    input("\nPressione ENTER para continuar...")
    return lista_aparelhos


def mostrar_consumo_diario(lista_aparelhos):
    """Exibe o consumo diário de energia dos aparelhos"""
    limpar_tela()
    exibir_cabecalho()
    print("📈 CONSUMO DIÁRIO DE ENERGIA\n")

    if not lista_aparelhos:
        print("Não há aparelhos cadastrados.")
        input("\nPressione ENTER para continuar...")
        return

    dados = calcularConsumoDiario(lista_aparelhos)
    aparelhos = sorted(dados["aparelhos"], key=lambda x: x["consumo"], reverse=True)

    print("{:<30} {:<15} {:<15}".format("Aparelho", "Consumo (kWh)", "Percentual (%)"))
    print("-" * 60)

    for aparelho in aparelhos:
        print("{:<30} {:<15.2f} {:<15.2f}".format(
            aparelho["nome"],
            aparelho["consumo"],
            aparelho["percentual"]
        ))

    print("-" * 60)
    print("{:<30} {:<15.2f}".format("TOTAL:", dados["total"]))
    print("-" * 60)
    print(f"Classificação: {estimarClassificacao(dados['total'] * 30)}")

    input("\nPressione ENTER para continuar...")


def mostrar_consumo_mensal(lista_aparelhos):
    """Exibe o consumo mensal de energia dos aparelhos"""
    limpar_tela()
    exibir_cabecalho()
    print("📊 CONSUMO MENSAL DE ENERGIA\n")

    if not lista_aparelhos:
        print("Não há aparelhos cadastrados.")
        input("\nPressione ENTER para continuar...")
        return

    dados = calcularConsumoMensal(lista_aparelhos)
    aparelhos = sorted(dados["aparelhos"], key=lambda x: x["consumo"], reverse=True)

    print("{:<30} {:<15} {:<15}".format("Aparelho", "Consumo (kWh)", "Percentual (%)"))
    print("-" * 60)

    for aparelho in aparelhos:
        print("{:<30} {:<15.2f} {:<15.2f}".format(
            aparelho["nome"],
            aparelho["consumo"],
            aparelho["percentual"]
        ))

    print("-" * 60)
    print("{:<30} {:<15.2f}".format("TOTAL:", dados["total"]))
    print("-" * 60)
    print(f"Classificação: {estimarClassificacao(dados['total'])}")

    input("\nPressione ENTER para continuar...")


def calcular_custo_mensal(lista_aparelhos):
    """Calcula e exibe o custo mensal de energia dos aparelhos"""
    limpar_tela()
    exibir_cabecalho()
    print("💰 CÁLCULO DE CUSTO MENSAL\n")

    if not lista_aparelhos:
        print("Não há aparelhos cadastrados.")
        input("\nPressione ENTER para continuar...")
        return

    try:
        tarifa = float(
            input(f"Digite o valor da tarifa de energia (R$/kWh) [padrão: R$ {TARIFA_PADRAO:.2f}]: ") or TARIFA_PADRAO)

        consumo_mensal = calcularConsumoMensal(lista_aparelhos)
        custo = calcularCustoMensal(consumo_mensal, tarifa)
        aparelhos = sorted(custo["aparelhos"], key=lambda x: x["custo"], reverse=True)

        print("\n{:<30} {:<15} {:<15}".format("Aparelho", "Custo (R$)", "Percentual (%)"))
        print("-" * 60)

        for aparelho in aparelhos:
            print("{:<30} {:<15.2f} {:<15.2f}".format(
                aparelho["nome"],
                aparelho["custo"],
                aparelho["percentual"]
            ))

        print("-" * 60)
        print("{:<30} {:<15.2f}".format("TOTAL:", custo["total"]))
        print("-" * 60)

        # Adicionar informações extras
        bandeira = "Verde"
        print(f"Estimativa com bandeira tarifária: {bandeira}")
        print(f"Tarifa utilizada: R$ {tarifa:.4f}/kWh")
        print(f"Consumo total: {consumo_mensal['total']:.2f} kWh/mês")
        print(f"Classificação: {estimarClassificacao(consumo_mensal['total'])}")

    except ValueError:
        print("\n❌ Por favor, digite um valor numérico válido para a tarifa.")

    input("\nPressione ENTER para continuar...")


def gerar_salvar_grafico(plt_objeto, nome_arquivo):
    """Exibe e salva um gráfico gerado"""
    try:
        # Criar pasta de gráficos se não existir
        if not os.path.exists(PASTA_GRAFICOS):
            os.makedirs(PASTA_GRAFICOS)

        # Caminho completo do arquivo
        caminho_arquivo = os.path.join(PASTA_GRAFICOS, nome_arquivo)

        # Salvar gráfico
        plt_objeto.savefig(caminho_arquivo, dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico salvo em: {caminho_arquivo}")

        # Mostrar gráfico de forma não bloqueante
        plt_objeto.show(block=False)
        plt.pause(0.5)  # Pequena pausa para garantir que o gráfico apareça

    except Exception as e:
        print(f"❌ Erro ao gerar ou salvar o gráfico: {e}")


def menu_graficos(lista_aparelhos):
    """Gerencia o menu de geração de gráficos"""
    while True:
        limpar_tela()
        exibir_cabecalho()
        exibir_menu_graficos()

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            plt_grafico = gerarGraficoBarrasDiario(lista_aparelhos)
            gerar_salvar_grafico(plt_grafico, "grafico_barras_diario.png")

        elif opcao == "2":
            plt_grafico = gerarGraficoBarrasMensal(lista_aparelhos)
            gerar_salvar_grafico(plt_grafico, "grafico_barras_mensal.png")

        elif opcao == "3":
            plt_grafico = gerarGraficoPizzaDiario(lista_aparelhos)
            gerar_salvar_grafico(plt_grafico, "grafico_pizza_diario.png")

        elif opcao == "4":
            plt_grafico = gerarGraficoPizzaMensal(lista_aparelhos)
            gerar_salvar_grafico(plt_grafico, "grafico_pizza_mensal.png")


        elif opcao == "5":

            print("\nGerando todos os gráficos...")

            try:

                # Gerar gráficos um por um para evitar conflitos

                plt_grafico = gerarGraficoBarrasDiario(lista_aparelhos)

                gerar_salvar_grafico(plt_grafico, "grafico_barras_diario.png")

                time.sleep(15)
                plt.close()  # Fecha o gráfico atual antes de criar o próximo

                plt_grafico = gerarGraficoBarrasMensal(lista_aparelhos)

                gerar_salvar_grafico(plt_grafico, "grafico_barras_mensal.png")
                time.sleep(15)
                plt.close()

                plt_grafico = gerarGraficoPizzaDiario(lista_aparelhos)

                gerar_salvar_grafico(plt_grafico, "grafico_pizza_diario.png")
                time.sleep(15)
                plt.close()

                plt_grafico = gerarGraficoPizzaMensal(lista_aparelhos)

                gerar_salvar_grafico(plt_grafico, "grafico_pizza_mensal.png")
                time.sleep(15)
                plt.close()

                print("\n✅ Todos os gráficos foram gerados na pasta 'graficos'!")

            except Exception as e:

                print(f"\n❌ Erro ao gerar gráficos: {e}")

        input("\nPressione ENTER para continuar...")


def mostrar_dicas_economia(lista_aparelhos):
    """Exibe dicas personalizadas para economia de energia"""
    limpar_tela()
    exibir_cabecalho()
    print("💡 DICAS DE ECONOMIA DE ENERGIA\n")

    if not lista_aparelhos:
        print("Não há aparelhos cadastrados.")
        input("\nPressione ENTER para continuar...")
        return

    consumo_mensal = calcularConsumoMensal(lista_aparelhos)
    dicas = gerarDicasEconomia(consumo_mensal, lista_aparelhos)

    for dica in dicas:
        print(dica)

    # Adicionar mais informações úteis
    print("\n📊 Informações sobre seu consumo:")
    print(f"   → Consumo mensal total: {consumo_mensal['total']:.2f} kWh")
    print(f"   → Classificação: {estimarClassificacao(consumo_mensal['total'])}")

    # Calcular estimativa de economia
    economia_estimada = consumo_mensal['total'] * 0.15  # Estimativa de 15% de economia
    print(f"\n💰 Se você seguir estas dicas, poderá economizar aproximadamente:")
    print(f"   → {economia_estimada:.2f} kWh por mês")
    print(f"   → R$ {economia_estimada * TARIFA_PADRAO:.2f} por mês")
    print(f"   → R$ {economia_estimada * TARIFA_PADRAO * 12:.2f} por ano")

    input("\nPressione ENTER para continuar...")


def salvar_lista(lista_aparelhos):
    """Salva a lista de aparelhos em um arquivo de texto"""
    limpar_tela()
    exibir_cabecalho()
    print("💾 SALVAR LISTA DE APARELHOS\n")

    if not lista_aparelhos:
        print("Não há aparelhos para salvar.")
        input("\nPressione ENTER para continuar...")
        return

    try:
        nome_arquivo = input("Digite o nome do arquivo (sem extensão): ") or "aparelhos"
        nome_arquivo = nome_arquivo.strip()
        if not nome_arquivo:
            nome_arquivo = "aparelhos"

        # Adicionar extensão .txt se não fornecida
        if not nome_arquivo.endswith('.txt'):
            nome_arquivo += '.txt'

        with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
            arquivo.write("Nome,Potência(W),Horas,Quantidade\n")

            for aparelho in lista_aparelhos:
                linha = f"{aparelho['nome']},{aparelho['potencia']},{aparelho['horas']},{aparelho['quantidade']}\n"
                arquivo.write(linha)

        print(f"\n✅ Lista salva com sucesso no arquivo: {nome_arquivo}")

    except Exception as erro:
        print(f"\n❌ Erro ao salvar arquivo: {erro}")

    input("\nPressione ENTER para continuar...")


def carregar_lista():
    """Carrega uma lista de aparelhos de um arquivo de texto"""
    limpar_tela()
    exibir_cabecalho()
    print("📂 CARREGAR LISTA DE APARELHOS\n")

    lista_aparelhos = []

    try:
        # Listar arquivos .txt no diretório atual
        arquivos_txt = [arquivo for arquivo in os.listdir() if arquivo.endswith('.txt')]

        if not arquivos_txt:
            print("Não foram encontrados arquivos .txt no diretório atual.")
            input("\nPressione ENTER para continuar...")
            return None

        print("Arquivos disponíveis:")
        for i, arquivo in enumerate(arquivos_txt, 1):
            print(f"[{i}] {arquivo}")

        escolha = input("\nDigite o número do arquivo a carregar (ou 0 para cancelar): ")

        if escolha == "0":
            return None

        indice = int(escolha) - 1
        if 0 <= indice < len(arquivos_txt):
            nome_arquivo = arquivos_txt[indice]

            with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
                linhas = arquivo.readlines()

                # Pular cabeçalho
                for i in range(1, len(linhas)):
                    linha = linhas[i].strip()
                    if linha:
                        campos = linha.split(',')
                        if len(campos) >= 4:
                            nome = campos[0]
                            potencia = float(campos[1])
                            horas = float(campos[2])
                            quantidade = int(campos[3])

                            aparelho = {
                                "nome": nome,
                                "potencia": potencia,
                                "horas": horas,
                                "quantidade": quantidade
                            }

                            lista_aparelhos.append(aparelho)

            print(f"\n✅ Lista carregada com sucesso do arquivo: {nome_arquivo}")
            print(f"   Total de aparelhos carregados: {len(lista_aparelhos)}")

        else:
            print("\n❌ Índice inválido!")

    except Exception as erro:
        print(f"\n❌ Erro ao carregar arquivo: {erro}")

    input("\nPressione ENTER para continuar...")
    return lista_aparelhos


def exibir_sobre():
    """Exibe informações sobre o programa"""
    limpar_tela()
    exibir_cabecalho()
    print("ℹ️ SOBRE O PROGRAMA\n")

    print("Calculadora de Consumo Energético Residencial")
    print("Versão: 1.0.0")
    print("Desenvolvido por: [Seus nomes aqui]")
    print("Data: 19/05/2025")
    print("\nEsta ferramenta permite calcular e visualizar o consumo de energia")
    print("elétrica em residências, auxiliando na economia e uso consciente.")
    print("\nFuncionalidades:")
    print("- Cadastro e gerenciamento de aparelhos elétricos")
    print("- Cálculo de consumo diário e mensal de energia")
    print("- Estimativa de custo na conta de luz")
    print("- Geração de gráficos para análise visual")
    print("- Dicas personalizadas para economia de energia")

    input("\nPressione ENTER para voltar ao menu principal...")


def menu_operacoes(lista_aparelhos):
    """Gerencia o menu de operações com a lista de aparelhos"""
    while True:
        limpar_tela()
        exibir_cabecalho()
        exibir_menu_operacoes(lista_aparelhos)

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            limpar_tela()
            exibir_cabecalho()
            print("📋 LISTA DE APARELHOS\n")
            print(listarAparelhos(lista_aparelhos))
            input("\nPressione ENTER para continuar...")

        elif opcao == "2":
            lista_aparelhos = adicionar_novo_aparelho(lista_aparelhos)

        elif opcao == "3":
            lista_aparelhos = remover_aparelho(lista_aparelhos)

        elif opcao == "4":
            mostrar_consumo_diario(lista_aparelhos)

        elif opcao == "5":
            mostrar_consumo_mensal(lista_aparelhos)

        elif opcao == "6":
            calcular_custo_mensal(lista_aparelhos)

        elif opcao == "7":
            menu_graficos(lista_aparelhos)

        elif opcao == "8":
            mostrar_dicas_economia(lista_aparelhos)

        elif opcao == "9":
            salvar_lista(lista_aparelhos)

        elif opcao == "0":
            return

        else:
            print("\n❌ Opção inválida. Tente novamente.")
            time.sleep(1)


def principal():
    """Função principal que inicia o programa"""
    while True:
        limpar_tela()
        exibir_cabecalho()
        exibir_menu_principal()

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            lista_aparelhos = APARELHOS_PADRAO.copy()
            print("\n✅ Lista padrão de aparelhos carregada!")
            time.sleep(1)
            menu_operacoes(lista_aparelhos)

        elif opcao == "2":
            lista_aparelhos = []
            print("\n✅ Nova lista vazia criada!")
            time.sleep(1)
            menu_operacoes(lista_aparelhos)

        elif opcao == "3":
            lista_aparelhos = carregar_lista()
            if lista_aparelhos:
                menu_operacoes(lista_aparelhos)

        elif opcao == "4":
            exibir_sobre()

        elif opcao == "0":
            limpar_tela()
            print("\n" + "=" * 80)
            print("Obrigado por usar a Calculadora de Consumo Energético!".center(80))
            print("Até a próxima! 👋".center(80))
            print("=" * 80)
            time.sleep(1)
            return

        else:
            print("\n❌ Opção inválida. Tente novamente.")
            time.sleep(1)


# Executar o programa principal se este arquivo for o principal
if __name__ == "__main__":
    principal()