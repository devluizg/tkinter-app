import cv2  # Importa a biblioteca OpenCV para processamento de imagens
import numpy as np  # Importa a biblioteca NumPy para operações numéricas

def empilhar_imagens(matriz_imagens, escala, rotulos=[]):
    """Empilha várias imagens horizontalmente e verticalmente."""
    linhas = len(matriz_imagens)
    colunas = len(matriz_imagens[0])
    linhas_disponiveis = isinstance(matriz_imagens[0], list)
    largura = matriz_imagens[0][0].shape[1]
    altura = matriz_imagens[0][0].shape[0]

    if linhas_disponiveis:
        for x in range(0, linhas):
            for y in range(0, colunas):
                matriz_imagens[x][y] = cv2.resize(matriz_imagens[x][y], (0, 0), None, escala, escala)
                if len(matriz_imagens[x][y].shape) == 2:
                    matriz_imagens[x][y] = cv2.cvtColor(matriz_imagens[x][y], cv2.COLOR_GRAY2BGR)
        imagem_vazia = np.zeros((altura, largura, 3), np.uint8)
        horizontal = [imagem_vazia] * linhas
        horizontal_concatenada = [imagem_vazia] * linhas
        for x in range(0, linhas):
            horizontal[x] = np.hstack(matriz_imagens[x])
            horizontal_concatenada[x] = np.concatenate(matriz_imagens[x])
        vertical = np.vstack(horizontal)
        vertical_concatenada = np.concatenate(horizontal)
    else:
        for x in range(0, linhas):
            matriz_imagens[x] = cv2.resize(matriz_imagens[x], (0, 0), None, escala, escala)
            if len(matriz_imagens[x].shape) == 2:
                matriz_imagens[x] = cv2.cvtColor(matriz_imagens[x], cv2.COLOR_GRAY2BGR)
        horizontal = np.hstack(matriz_imagens)
        horizontal_concatenada = np.concatenate(matriz_imagens)
        vertical = horizontal
    if len(rotulos) != 0:
        largura_imagem = int(vertical.shape[1] / colunas)
        altura_imagem = int(vertical.shape[0] / linhas)
        for d in range(0, linhas):
            for c in range(0, colunas):
                cv2.rectangle(vertical, (c * largura_imagem, altura_imagem * d), (c * largura_imagem + len(rotulos[d][c]) * 13 + 27, 30 + altura_imagem * d), (255, 255, 255), cv2.FILLED)
                cv2.putText(vertical, rotulos[d][c], (largura_imagem * c + 10, altura_imagem * d + 20), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 0), 2)
    return vertical

def contorno_retangulo(contornos):
    """Encontra e retorna contornos retangulares com base na área."""
    contorno_ret = []
    for i in contornos:
        area = cv2.contourArea(i)
        if area > 50:
            peri = cv2.arcLength(i, True)
            aprox = cv2.approxPolyDP(i, 0.02 * peri, True)
            # print("Pontos de Canto", len(aprox))
            if len(aprox) == 4:
                contorno_ret.append(i)
    contorno_ret = sorted(contorno_ret, key=cv2.contourArea, reverse=True)

    return contorno_ret

def obter_pontos_cantos(contorno):
    """Obtém os pontos dos cantos de um contorno."""
    peri = cv2.arcLength(contorno, True)
    aprox = cv2.approxPolyDP(contorno, 0.02 * peri, True)
    return aprox

def reordenar(meus_pontos):
    """Reordena os pontos dos cantos para que estejam na ordem:
        superior esquerdo, inferior esquerdo, inferior direito, superior direito."""
    meus_pontos = meus_pontos.reshape((4, 2))
    meus_novos_pontos = np.zeros((4, 1, 2), np.int32)
    soma = meus_pontos.sum(1)
    # print(meus_pontos)
    # print(soma)
    meus_novos_pontos[0] = meus_pontos[np.argmin(soma)]  # [0, 0]
    meus_novos_pontos[3] = meus_pontos[np.argmax(soma)]  # [l, a]
    dif = np.diff(meus_pontos, axis=1)
    meus_novos_pontos[1] = meus_pontos[np.argmin(dif)]  # [l, 0]
    meus_novos_pontos[2] = meus_pontos[np.argmax(dif)]  # [a, 0]
    # print(dif)

    return meus_novos_pontos

def criar_mascara_circular(a, l, centro, raio):
    """Cria uma máscara circular."""
    Y, X = np.ogrid[:a, :l]
    distancia_centro = np.sqrt((X - centro[0]) ** 2 + (Y - centro[1]) ** 2)
    mascara = distancia_centro <= raio
    return mascara

def dividir_caixas(img, questoes, alternativas):
    """Divide a imagem em várias caixas (uma para cada alternativa)."""
    linhas = np.vsplit(img, questoes)
    caixas = []
    for linha in linhas:
        colunas = np.hsplit(linha, alternativas)
        for caixa in colunas:
            a, l = caixa.shape
            centro = (l // 2, a // 2)
            raio = min(l, a) // 4  # Ajuste este valor para mudar o tamanho do círculo
            mascara = criar_mascara_circular(a, l, centro, raio)
            caixa_circular = caixa * mascara
            caixas.append(caixa_circular)
    return caixas

def mostrar_respostas(img, meus_indices, avaliacao, respostas, questoes, alternativas):
    """Mostra as respostas corretas e incorretas na imagem."""
    largura_secao = int(img.shape[1] / alternativas)  # Largura de cada célula
    altura_secao = int(img.shape[0] / questoes)  # Altura de cada célula

    # Definir o raio como uma fração do menor lado para evitar distorção
    raio_circulo = min(largura_secao, altura_secao) // 3  # Ajustar o raio para manter a proporção circular

    for x in range(0, questoes):
        minha_resposta = meus_indices[x]
        # Calcular o centro da célula para desenhar o círculo
        centro_x = int((minha_resposta * largura_secao) + largura_secao / 2)  # Centro horizontal
        centro_y = int((x * altura_secao) + altura_secao / 2)  # Centro vertical

        if avaliacao[x] == 1:
            # Resposta correta, círculo verde
            cv2.circle(img, (centro_x, centro_y), raio_circulo, (0, 255, 0), cv2.FILLED)
        else:
            # Resposta incorreta, círculo vermelho
            cv2.circle(img, (centro_x, centro_y), raio_circulo, (0, 0, 255), cv2.FILLED)

    return img
