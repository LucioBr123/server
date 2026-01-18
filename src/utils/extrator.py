import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import os
import re

# Caminho do executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocessar_nota_fiscal(imagem, modo="otimizado_nf"):
    """Pré-processamento específico para notas fiscais"""
    
    if modo == "original":
        return imagem
    
    elif modo == "otimizado_nf":
        # Pipeline otimizado para notas fiscais
        # 1. Redimensiona significativamente (crucial para OCR)
        altura, largura = imagem.shape[:2]
        fator_escala = 4  # Aumenta 4x
        img = cv2.resize(imagem, (largura * fator_escala, altura * fator_escala), 
                        interpolation=cv2.INTER_LANCZOS4)
        
        # 2. Converte para cinza
        if len(img.shape) == 3:
            cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            cinza = img
        
        # 3. Equalização de histograma para melhorar contraste
        cinza = cv2.equalizeHist(cinza)
        
        # 4. Desfoque gaussiano leve para suavizar
        cinza = cv2.GaussianBlur(cinza, (3, 3), 0)
        
        # 5. Binarização adaptativa mais agressiva
        binarizada = cv2.adaptiveThreshold(cinza, 255, 
                                         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, 15, 8)
        
        # 6. Operação morfológica para conectar caracteres quebrados
        kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
        binarizada = cv2.morphologyEx(binarizada, cv2.MORPH_CLOSE, kernel_horizontal)
        
        # 7. Remove ruído pequeno
        kernel_noise = np.ones((2, 2), np.uint8)
        binarizada = cv2.morphologyEx(binarizada, cv2.MORPH_OPEN, kernel_noise)
        
        return binarizada
    
    elif modo == "super_resolucao":
        # Aumenta resolução com interpolação cúbica
        altura, largura = imagem.shape[:2]
        img = cv2.resize(imagem, (largura * 6, altura * 6), interpolation=cv2.INTER_CUBIC)
        
        # Aplica filtro de nitidez
        kernel_sharp = np.array([[-1,-1,-1,-1,-1],
                               [-1, 2, 2, 2,-1],
                               [-1, 2, 8, 2,-1],
                               [-1, 2, 2, 2,-1],
                               [-1,-1,-1,-1,-1]]) / 8.0
        img = cv2.filter2D(img, -1, kernel_sharp)
        
        # Converte e binariza
        if len(img.shape) == 3:
            cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            cinza = img
            
        _, binarizada = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binarizada
    
    elif modo == "contraste_extremo":
        # Aumenta contraste drasticamente
        altura, largura = imagem.shape[:2]
        img = cv2.resize(imagem, (largura * 3, altura * 3), interpolation=cv2.INTER_CUBIC)
        
        if len(img.shape) == 3:
            cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            cinza = img
        
        # Contraste muito alto
        contraste = cv2.convertScaleAbs(cinza, alpha=3.0, beta=0)
        
        # Binarização com threshold fixo alto
        _, binarizada = cv2.threshold(contraste, 200, 255, cv2.THRESH_BINARY)
        return binarizada

def preprocessar_com_pil_avancado(imagem_path):
    """Pré-processamento avançado com PIL para notas fiscais"""
    img = Image.open(imagem_path)
    
    # Redimensiona com alta qualidade
    largura, altura = img.size
    img = img.resize((largura * 4, altura * 4), Image.Resampling.LANCZOS)
    
    # Converte para RGB se necessário
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Aumenta contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.5)
    
    # Aumenta nitidez
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(3.0)
    
    # Aplica filtro de nitidez adicional
    img = img.filter(ImageFilter.SHARPEN)
    
    # Converte para escala de cinza
    img = img.convert('L')
    
    return np.array(img)

def pos_processar_texto(texto):
    """Pós-processa o texto para corrigir erros comuns em notas fiscais"""
    if not texto.strip():
        return texto
    
    # Correções específicas para notas fiscais
    correcoes = {
        # Números comuns mal reconhecidos
        'O': '0', 'o': '0', 'I': '1', 'l': '1', 'S': '5', 'B': '8',
        # Palavras comuns
        'DESCRICAO': 'DESCRIÇÃO',
        'QTD': 'QTD',
        'UNID': 'UNID',
        'TOTAL': 'TOTAL',
        'ITEM': 'ITEM',
        'COD': 'COD',
        # Unidades
        'KGR': 'KG',
        'MCO': 'MCO',
        'GF': 'GF',
        'ML': 'ML',
        'UNID': 'UNID'
    }
    
    texto_corrigido = texto
    for erro, correcao in correcoes.items():
        texto_corrigido = texto_corrigido.replace(erro, correcao)
    
    # Remove caracteres estranhos no início das linhas
    linhas = texto_corrigido.split('\n')
    linhas_limpas = []
    
    for linha in linhas:
        # Remove caracteres não ASCII no início
        linha_limpa = re.sub(r'^[^\w\d\s]+', '', linha.strip())
        if linha_limpa:
            linhas_limpas.append(linha_limpa)
    
    return '\n'.join(linhas_limpas)

def testar_ocr_nota_fiscal(imagem_path):
    """Teste de OCR específico para notas fiscais"""
    if not os.path.exists(imagem_path):
        print(f"❌ Arquivo não encontrado: {imagem_path}")
        return
    
    print(f"🧾 Testando OCR para NOTA FISCAL: {imagem_path}")
    print("="*80)
    
    # Configurações específicas para notas fiscais
    configs_nf = [
        # PSM 6 (bloco uniforme) com configurações otimizadas
        "--oem 3 --psm 6 -c preserve_interword_spaces=1",
        "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÁÂÃÇÉÊÍÓÔÕÚàáâãçéêíóôõú.,;:()[]{}+-*/%=$@# ",
        "--oem 3 --psm 4 -c preserve_interword_spaces=1 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÁÂÃÇÉÊÍÓÔÕÚàáâãçéêíóôõú.,;:()[]{}+-*/%=$@# ",
        "--oem 3 --psm 3 -c preserve_interword_spaces=1",
        # Configuração específica para números e códigos
        "--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789",
        # Para texto misto
        "--oem 3 --psm 11 -c preserve_interword_spaces=1"
    ]
    
    resultados_finais = []
    
    # 1. Teste com PIL avançado
    try:
        print("\n🎨 Testando com PIL avançado...")
        img_pil = preprocessar_com_pil_avancado(imagem_path)
        
        for i, config in enumerate(configs_nf[:3]):  # Primeiras 3 configs
            texto = pytesseract.image_to_string(img_pil, lang="por+eng", config=config)
            if texto.strip():
                texto_limpo = pos_processar_texto(texto)
                qualidade = calcular_qualidade_nf(texto_limpo)
                resultados_finais.append((f"PIL_Config_{i+1}", texto_limpo, qualidade))
                
                print(f"\n✨ PIL - Config {i+1} (Qualidade: {qualidade:.1f})")
                print("-" * 50)
                print(texto_limpo[:400] + ("..." if len(texto_limpo) > 400 else ""))
    except Exception as e:
        print(f"⚠️ Erro no PIL: {e}")
    
    # 2. Teste com OpenCV otimizado
    imagem = cv2.imread(imagem_path)
    modos = ["otimizado_nf", "super_resolucao", "contraste_extremo"]
    
    for modo in modos:
        print(f"\n🔧 Testando modo: {modo}")
        try:
            img_proc = preprocessar_nota_fiscal(imagem, modo)
            
            for i, config in enumerate(configs_nf):
                texto = pytesseract.image_to_string(img_proc, lang="por+eng", config=config)
                if texto.strip():
                    texto_limpo = pos_processar_texto(texto)
                    qualidade = calcular_qualidade_nf(texto_limpo)
                    resultados_finais.append((f"{modo}_Config_{i+1}", texto_limpo, qualidade))
                    
                    if qualidade > 70:  # Só mostra resultados bons
                        print(f"\n🎯 {modo} - Config {i+1} (Qualidade: {qualidade:.1f})")
                        print("-" * 50)
                        print(texto_limpo[:400] + ("..." if len(texto_limpo) > 400 else ""))
        except Exception as e:
            print(f"⚠️ Erro no modo {modo}: {e}")
    
    # Mostra os melhores resultados
    if resultados_finais:
        resultados_finais.sort(key=lambda x: x[2], reverse=True)
        
        print("\n" + "="*80)
        print("🏆 TOP 5 MELHORES RESULTADOS PARA NOTA FISCAL:")
        print("="*80)
        
        for i, (config, texto, qualidade) in enumerate(resultados_finais[:5], 1):
            print(f"\n🥇 #{i} - {config} (Qualidade: {qualidade:.1f}%)")
            print("-" * 60)
            print(texto)
            print()
    
    # Salva o melhor resultado
    if resultados_finais:
        melhor_config, melhor_texto, melhor_qualidade = resultados_finais[0]
        with open("melhor_resultado_ocr.txt", "w", encoding="utf-8") as f:
            f.write(f"Configuração: {melhor_config}\n")
            f.write(f"Qualidade: {melhor_qualidade:.1f}%\n")
            f.write("-" * 50 + "\n")
            f.write(melhor_texto)
        print(f"💾 Melhor resultado salvo em: melhor_resultado_ocr.txt")

def calcular_qualidade_nf(texto):
    """Calcula qualidade específica para notas fiscais"""
    if not texto.strip():
        return 0
    
    pontuacao = 0
    texto_upper = texto.upper()
    
    # Palavras-chave de notas fiscais (peso 20)
    palavras_chave = ['ITEM', 'DESCRIÇÃO', 'DESCRICAO', 'QTD', 'UNID', 'TOTAL', 'COD', 'VALOR']
    for palavra in palavras_chave:
        if palavra in texto_upper:
            pontuacao += 20
    
    # Padrões de código de barras (peso 15)
    codigos_barras = re.findall(r'\b\d{13}\b|\b\d{14}\b', texto)
    pontuacao += len(codigos_barras) * 15
    
    # Valores monetários (peso 10)
    valores = re.findall(r'\b\d+,\d{2}\b', texto)
    pontuacao += len(valores) * 10
    
    # Quantidades com KG, MCO, etc (peso 10)
    unidades = re.findall(r'\d+,\d{3}\s*(KG|MCO|GF|UNID)', texto_upper)
    pontuacao += len(unidades) * 10
    
    # Densidade de caracteres alfanuméricos (peso 5)
    chars_validos = len([c for c in texto if c.isalnum() or c.isspace()])
    densidade = chars_validos / len(texto) if texto else 0
    pontuacao += densidade * 5
    
    return min(pontuacao, 100)

if __name__ == "__main__":
    imagem_path = "src/utils/nf_teste.jpg"
    testar_ocr_nota_fiscal(imagem_path)