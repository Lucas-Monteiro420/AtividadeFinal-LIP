"""
Módulo de funções para a calculadora de consumo energético residencial.
Contém funções para adicionar aparelhos, calcular consumo e gerar gráficos.
"""

import matplotlib.pyplot as plt
import numpy as np

# Dados padrão de aparelhos comuns em residências brasileiras
APARELHOS_PADRAO = [
    {"nome": "Geladeira", "potencia": 250, "horas": 24, "quantidade": 1},
    {"nome": "Televisão LED 40\"", "potencia": 100, "horas": 5, "quantidade": 1},
    {"nome": "Chuveiro elétrico", "potencia": 5500, "horas": 0.5, "quantidade": 1},
    {"nome": "Micro-ondas", "potencia": 1200, "horas": 0.3, "quantidade": 1},
    {"nome": "Ar-condicionado 9000 BTU", "potencia": 1400, "horas": 8, "quantidade": 1},
    {"nome": "Máquina de lavar", "potencia": 1000, "horas": 1, "quantidade": 1},
    {"nome": "Lâmpada LED", "potencia": 9, "horas": 6, "quantidade": 5},
    {"nome": "Ventilador", "potencia": 80, "horas": 6, "quantidade": 2},
    {"nome": "Computador Desktop", "potencia": 300, "horas": 4, "quantidade": 1},
    {"nome": "Notebook", "potencia": 65, "horas": 6, "quantidade": 1},
    {"nome": "Ferro de passar", "potencia": 1000, "horas": 0.3, "quantidade": 1},
    {"nome": "Liquidificador", "potencia": 200, "horas": 0.1, "quantidade": 1}
]


def adicionarAparelho(lista, nome, potencia, horas, quantidade):
    """
    Adiciona um aparelho à lista de equipamentos

    Args:
        lista: Lista de aparelhos
        nome: Nome do aparelho
        potencia: Potência em watts
        horas: Tempo médio de uso diário em horas
        quantidade: Quantidade de aparelhos

    Returns:
        Lista atualizada de aparelhos
    """
    # Validação de dados
    if potencia <= 0:
        raise ValueError("A potência deve ser um valor positivo")
    if horas < 0 or horas > 24:
        raise ValueError("As horas de uso devem estar entre 0 e 24")
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser um valor positivo")

    # Adiciona o aparelho à lista
    novo_aparelho = {
        "nome": nome,
        "potencia": potencia,
        "horas": horas,
        "quantidade": quantidade
    }

    lista.append(novo_aparelho)
    return lista


def listarAparelhos(lista):
    """
    Lista todos os aparelhos cadastrados

    Args:
        lista: Lista de aparelhos

    Returns:
        String formatada com a listagem de aparelhos
    """
    if not lista:
        return "Nenhum aparelho cadastrado."

    resultado = "\n{:<30} {:<15} {:<15} {:<15}\n".format(
        "Nome do Aparelho", "Potência (W)", "Uso Diário (h)", "Quantidade")
    resultado += "-" * 75 + "\n"

    for aparelho in lista:
        resultado += "{:<30} {:<15} {:<15} {:<15}\n".format(
            aparelho["nome"],
            aparelho["potencia"],
            aparelho["horas"],
            aparelho["quantidade"]
        )

    return resultado


def calcularConsumoDiario(lista):
    """
    Calcula o consumo diário de energia para cada aparelho e o total

    Args:
        lista: Lista de aparelhos

    Returns:
        Dicionário com consumo individual e total diário em kWh
    """
    resultado = {"aparelhos": [], "total": 0}

    for aparelho in lista:
        # Consumo diário = potência (W) * horas * quantidade / 1000 (para converter para kWh)
        consumo = (aparelho["potencia"] * aparelho["horas"] * aparelho["quantidade"]) / 1000

        info_aparelho = {
            "nome": aparelho["nome"],
            "consumo": consumo,
            "percentual": 0  # Será calculado após obter o total
        }

        resultado["aparelhos"].append(info_aparelho)
        resultado["total"] += consumo

    # Calcular o percentual de cada aparelho
    for aparelho in resultado["aparelhos"]:
        if resultado["total"] > 0:
            aparelho["percentual"] = (aparelho["consumo"] / resultado["total"]) * 100
        else:
            aparelho["percentual"] = 0

    return resultado


def calcularConsumoMensal(lista):
    """
    Calcula o consumo mensal de energia para cada aparelho e o total

    Args:
        lista: Lista de aparelhos

    Returns:
        Dicionário com consumo individual e total mensal em kWh
    """
    resultado_diario = calcularConsumoDiario(lista)
    resultado = {"aparelhos": [], "total": resultado_diario["total"] * 30}

    for aparelho in resultado_diario["aparelhos"]:
        info_aparelho = {
            "nome": aparelho["nome"],
            "consumo": aparelho["consumo"] * 30,
            "percentual": aparelho["percentual"]  # O percentual permanece o mesmo
        }

        resultado["aparelhos"].append(info_aparelho)

    return resultado


def calcularCustoMensal(consumo_mensal, tarifa):
    """
    Calcula o custo mensal baseado no consumo e na tarifa de energia

    Args:
        consumo_mensal: Resultado do calcularConsumoMensal
        tarifa: Valor da tarifa de energia em R$/kWh

    Returns:
        Dicionário com custo individual e total mensal em R$
    """
    resultado = {"aparelhos": [], "total": consumo_mensal["total"] * tarifa}

    for aparelho in consumo_mensal["aparelhos"]:
        info_aparelho = {
            "nome": aparelho["nome"],
            "custo": aparelho["consumo"] * tarifa,
            "percentual": aparelho["percentual"]
        }

        resultado["aparelhos"].append(info_aparelho)

    return resultado


import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Shadow
import seaborn as sns

# Configurar estilo global
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def gerarGraficoBarrasDiario(lista):
    """
    Gera um gráfico de barras elegante com o consumo diário de cada aparelho
    """
    dados = calcularConsumoDiario(lista)
    dados["aparelhos"].sort(key=lambda x: x["consumo"], reverse=True)

    nomes = [a["nome"] for a in dados["aparelhos"]]
    consumos = [a["consumo"] for a in dados["aparelhos"]]

    # Criar figura com melhor resolução
    fig, ax = plt.subplots(figsize=(12, 8), dpi=100)

    # Configurar posição da janela
    manager = plt.get_current_fig_manager()
    if hasattr(manager, 'window'):
        try:
            manager.window.wm_geometry("+200+100")
        except:
            pass

    # Criar gradiente de cores
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(nomes)))

    # Criar barras com sombra
    barras = ax.bar(nomes, consumos, color=colors, alpha=0.8,
                    edgecolor='white', linewidth=1.5)

    # Adicionar sombra às barras
    for barra in barras:
        shadow = Shadow(barra, 0.02, 0.02)
        ax.add_patch(shadow)

    # Rotacionar rótulos com melhor formatação
    plt.xticks(rotation=45, ha='right', fontsize=11, fontweight='bold')
    plt.yticks(fontsize=11)

    # Adicionar valores nas barras com melhor formatação
    for i, barra in enumerate(barras):
        altura = barra.get_height()
        ax.text(barra.get_x() + barra.get_width() / 2., altura + max(consumos) * 0.01,
                f'{altura:.2f} kWh', ha='center', va='bottom',
                fontweight='bold', fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

    # Melhorar títulos e labels
    ax.set_title('Consumo Diário de Energia por Aparelho',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Aparelhos', fontsize=12, fontweight='bold')
    ax.set_ylabel('Consumo (kWh)', fontsize=12, fontweight='bold')

    # Adicionar grid personalizado
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Melhorar layout
    plt.tight_layout()

    # Adicionar total no canto
    total = sum(consumos)
    ax.text(0.85, 0.98, f'Total: {total:.2f} kWh/dia',
            transform=ax.transAxes, fontsize=11, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.8),
            verticalalignment='top')

    return plt


def gerarGraficoBarrasMensal(lista):
    """
    Gera um gráfico de barras elegante com o consumo mensal de cada aparelho
    """
    dados = calcularConsumoMensal(lista)
    dados["aparelhos"].sort(key=lambda x: x["consumo"], reverse=True)

    nomes = [a["nome"] for a in dados["aparelhos"]]
    consumos = [a["consumo"] for a in dados["aparelhos"]]

    # Criar figura com melhor resolução
    fig, ax = plt.subplots(figsize=(12, 8), dpi=100)

    # Configurar posição da janela
    manager = plt.get_current_fig_manager()
    if hasattr(manager, 'window'):
        try:
            manager.window.wm_geometry("+200+100")
        except:
            pass

    # Criar gradiente de cores
    colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(nomes)))

    # Criar barras com sombra
    barras = ax.bar(nomes, consumos, color=colors, alpha=0.8,
                    edgecolor='white', linewidth=1.5)

    # Adicionar sombra às barras
    for barra in barras:
        shadow = Shadow(barra, 0.02, 0.02)
        ax.add_patch(shadow)

    # Rotacionar rótulos com melhor formatação
    plt.xticks(rotation=45, ha='right', fontsize=11, fontweight='bold')
    plt.yticks(fontsize=11)

    # Adicionar valores nas barras
    for i, barra in enumerate(barras):
        altura = barra.get_height()
        ax.text(barra.get_x() + barra.get_width() / 2., altura + max(consumos) * 0.01,
                f'{altura:.1f} kWh', ha='center', va='bottom',
                fontweight='bold', fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

    # Melhorar títulos e labels
    ax.set_title('Consumo Mensal de Energia por Aparelho',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Aparelhos', fontsize=12, fontweight='bold')
    ax.set_ylabel('Consumo (kWh)', fontsize=12, fontweight='bold')

    # Adicionar grid personalizado
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Melhorar layout
    plt.tight_layout()

    # Adicionar total no canto
    total = sum(consumos)
    ax.text(0.85, 0.98, f'Total: {total:.1f} kWh/mês',
            transform=ax.transAxes, fontsize=11, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', alpha=0.8),
            verticalalignment='top')

    return plt


def gerarGraficoPizzaDiario(lista, tarifa=0.65):
    """
    Gera um gráfico de pizza elegante e organizado com o consumo diário e gasto em reais

    Args:
        lista: Lista de aparelhos
        tarifa: Tarifa de energia em R$/kWh (padrão: R$ 0,65)
    """
    dados = calcularConsumoDiario(lista)

    # Filtrar aparelhos significativos (mais de 2% do total para melhor visualização)
    aparelhos_significativos = []
    outros_consumo = 0

    for aparelho in dados["aparelhos"]:
        if aparelho["percentual"] > 2:
            aparelhos_significativos.append(aparelho)
        else:
            outros_consumo += aparelho["consumo"]

    # Adicionar categoria "Outros" se necessário
    if outros_consumo > 0:
        aparelhos_significativos.append({
            "nome": "Outros",
            "consumo": outros_consumo,
            "percentual": (outros_consumo / dados["total"]) * 100
        })

    aparelhos_significativos.sort(key=lambda x: x["consumo"], reverse=True)

    nomes = [a["nome"] for a in aparelhos_significativos]
    consumos = [a["consumo"] for a in aparelhos_significativos]
    percentuais = [a["percentual"] for a in aparelhos_significativos]
    custos = [consumo * tarifa for consumo in consumos]  # Calcular custos em reais

    # Criar figura maior e mais elegante
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), dpi=100)

    # Configurar posição da janela
    manager = plt.get_current_fig_manager()
    if hasattr(manager, 'window'):
        try:
            manager.window.wm_geometry("+100+50")
        except:
            pass

    # Cores mais elegantes
    colors = plt.cm.Set3(np.linspace(0, 1, len(nomes)))

    # GRÁFICO DE PIZZA PRINCIPAL
    wedges, texts, autotexts = ax1.pie(consumos, labels=None, autopct='%1.1f%%',
                                       shadow=True, startangle=90,
                                       colors=colors, textprops={'fontsize': 10, 'fontweight': 'bold'})

    # Melhorar aparência das porcentagens
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)

    ax1.set_title('Distribuição do Consumo Diário\n',
                  fontsize=14, fontweight='bold', pad=20)

    # LEGENDA ELEGANTE NO SEGUNDO SUBPLOT
    ax2.axis('off')

    # Criar legenda com informações detalhadas incluindo gasto em reais
    legend_data = []
    for i, (nome, consumo, perc, custo) in enumerate(zip(nomes, consumos, percentuais, custos)):
        legend_data.append(f"{nome}: {consumo:.2f} kWh ({perc:.1f}%) - R$ {custo:.2f}")

    # Adicionar legenda organizada
    ax2.text(0.1, 0.9, 'Detalhamento por Aparelho:',
             fontsize=14, fontweight='bold', transform=ax2.transAxes)

    for i, item in enumerate(legend_data):
        ax2.text(0.05, 0.8 - i * 0.08, f"• {item}",
                 fontsize=11, transform=ax2.transAxes,
                 bbox=dict(boxstyle="round,pad=0.3",
                           facecolor=colors[i], alpha=0.3))

    # Adicionar total com consumo e gasto
    total_consumo = sum(consumos)
    total_custo = sum(custos)
    ax2.text(0.65, 0.50, f'Total Diário: {total_consumo:.2f} kWh',
             fontsize=13, fontweight='bold', transform=ax2.transAxes,
             bbox=dict(boxstyle="round,pad=0.5", facecolor='gold', alpha=0.7))

    ax2.text(0.65, 0.43, f'Gasto Diário: R$ {total_custo:.2f}',
             fontsize=13, fontweight='bold', transform=ax2.transAxes,
             bbox=dict(boxstyle="round,pad=0.5", facecolor='lightcoral', alpha=0.7))
    plt.tight_layout()
    return plt


def gerarGraficoPizzaMensal(lista):
    """
    Gera um gráfico de pizza elegante e organizado com o consumo mensal
    """
    dados = calcularConsumoMensal(lista)

    # Filtrar aparelhos significativos
    aparelhos_significativos = []
    outros_consumo = 0

    for aparelho in dados["aparelhos"]:
        if aparelho["percentual"] > 2:
            aparelhos_significativos.append(aparelho)
        else:
            outros_consumo += aparelho["consumo"]

    # Adicionar categoria "Outros" se necessário
    if outros_consumo > 0:
        aparelhos_significativos.append({
            "nome": "Outros",
            "consumo": outros_consumo,
            "percentual": (outros_consumo / dados["total"]) * 100
        })

    aparelhos_significativos.sort(key=lambda x: x["consumo"], reverse=True)

    nomes = [a["nome"] for a in aparelhos_significativos]
    consumos = [a["consumo"] for a in aparelhos_significativos]
    percentuais = [a["percentual"] for a in aparelhos_significativos]

    # Criar figura maior e mais elegante
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), dpi=100)

    # Configurar posição da janela
    manager = plt.get_current_fig_manager()
    if hasattr(manager, 'window'):
        try:
            manager.window.wm_geometry("+100+50")
        except:
            pass

    # Cores mais elegantes
    colors = plt.cm.tab20(np.linspace(0, 1, len(nomes)))

    # Explode para destacar as fatias maiores

    # GRÁFICO DE PIZZA PRINCIPAL
    wedges, texts, autotexts = ax1.pie(consumos, labels=None, autopct='%1.1f%%',
                                       shadow=True, startangle=90,
                                       colors=colors, textprops={'fontsize': 10, 'fontweight': 'bold'})

    # Melhorar aparência das porcentagens
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)

    ax1.set_title('Distribuição do Consumo Mensal\n',
                  fontsize=14, fontweight='bold', pad=20)

    # LEGENDA ELEGANTE NO SEGUNDO SUBPLOT
    ax2.axis('off')

    # Criar legenda com informações detalhadas
    legend_data = []
    for i, (nome, consumo, perc) in enumerate(zip(nomes, consumos, percentuais)):
        legend_data.append(f"{nome}: {consumo:.1f} kWh ({perc:.1f}%)")

    # Adicionar legenda organizada
    ax2.text(0.1, 0.9, 'Detalhamento por Aparelho:',
             fontsize=14, fontweight='bold', transform=ax2.transAxes)

    for i, item in enumerate(legend_data):
        ax2.text(0.1, 0.8 - i * 0.08, f"• {item}",
                 fontsize=12, transform=ax2.transAxes,
                 bbox=dict(boxstyle="round,pad=0.3",
                           facecolor=colors[i], alpha=0.3))

    # Adicionar total
    total = sum(consumos)
    ax2.text(0.65, 0.50, f'Total Mensal: {total:.1f} kWh',
             fontsize=13, fontweight='bold', transform=ax2.transAxes,
             bbox=dict(boxstyle="round,pad=0.5", facecolor='gold', alpha=0.7))

    # Adicionar estimativa de custo (considerando R$ 0,65/kWh como exemplo)
    custo_estimado = total * 0.65
    ax2.text(0.65, 0.43, f'Custo Estimado: R$ {custo_estimado:.2f}',
             fontsize=13, fontweight='bold', transform=ax2.transAxes,
             bbox=dict(boxstyle="round,pad=0.5", facecolor='lightcoral', alpha=0.7))

    plt.tight_layout()
    return plt


def estimarClassificacao(consumo_mensal):
    """
    Estima a classificação do consumo residencial

    Args:
        consumo_mensal: Consumo total mensal em kWh

    Returns:
        String com a classificação de consumo
    """
    if consumo_mensal < 100:
        return "Consumo muito baixo (< 100 kWh/mês)"
    elif consumo_mensal < 200:
        return "Consumo baixo (100-200 kWh/mês)"
    elif consumo_mensal < 300:
        return "Consumo médio-baixo (200-300 kWh/mês)"
    elif consumo_mensal < 400:
        return "Consumo médio (300-400 kWh/mês)"
    elif consumo_mensal < 500:
        return "Consumo médio-alto (400-500 kWh/mês)"
    else:
        return "Consumo alto (> 500 kWh/mês)"


def gerarDicasEconomia(consumo_mensal, aparelhos):
    """
    Gera dicas personalizadas para economia de energia com base no consumo

    Args:
        consumo_mensal: Resultado do calcularConsumoMensal
        aparelhos: Lista de aparelhos

    Returns:
        Lista de dicas personalizadas
    """
    dicas = []

    # Ordenar aparelhos por consumo
    aparelhos_por_consumo = sorted(consumo_mensal["aparelhos"],
                                   key=lambda x: x["consumo"],
                                   reverse=True)

    # Aparelhos de maior consumo (top 3)
    maiores_consumidores = aparelhos_por_consumo[:3]

    # Dicas gerais
    dicas.append("🔍 Dicas Gerais de Economia:")
    dicas.append("   → Apague as luzes ao sair dos ambientes")
    dicas.append("   → Aproveite a luz natural durante o dia")
    dicas.append("   → Evite deixar aparelhos em modo standby")
    dicas.append("   → Faça manutenção periódica dos equipamentos")

    # Dicas específicas baseadas nos aparelhos de maior consumo
    dicas.append("\n⚡ Dicas para seus maiores consumidores de energia:")

    for aparelho in maiores_consumidores:
        nome = aparelho["nome"]

        if "Ar-condicionado" in nome:
            dicas.append(f"   → {nome}: Mantenha na temperatura de 23-24°C, que oferece conforto com menor consumo")
            dicas.append(f"   → {nome}: Faça limpeza regular dos filtros para manter a eficiência")

        elif "Chuveiro" in nome:
            dicas.append(f"   → {nome}: Reduza o tempo de banho e evite o uso na posição 'Inverno' em dias quentes")
            dicas.append(f"   → {nome}: Considere instalar aquecimento solar para reduzir o consumo elétrico")

        elif "Geladeira" in nome:
            dicas.append(f"   → {nome}: Não coloque alimentos quentes e mantenha afastada de fontes de calor")
            dicas.append(f"   → {nome}: Verifique as borrachas de vedação regularmente")

        elif "Máquina de lavar" in nome:
            dicas.append(f"   → {nome}: Utilize sempre com capacidade máxima para otimizar o consumo")
            dicas.append(f"   → {nome}: Opte por ciclos econômicos ou rápidos quando possível")

        elif "Televisão" in nome or "TV" in nome:
            dicas.append(f"   → {nome}: Reduza o brilho da tela para economizar energia")
            dicas.append(f"   → {nome}: Desligue completamente ao invés de deixar em standby")

        elif "Computador" in nome or "Desktop" in nome:
            dicas.append(f"   → {nome}: Configure as opções de economia de energia")
            dicas.append(f"   → {nome}: Desligue completamente quando não estiver em uso")

        elif "Lâmpada" in nome:
            dicas.append(f"   → {nome}: Substitua por modelos ainda mais eficientes se possível")
            dicas.append(f"   → {nome}: Organize interruptores para ligar apenas as necessárias")

        else:
            dicas.append(f"   → {nome}: Otimize o tempo de uso para reduzir o consumo")

    return dicas
