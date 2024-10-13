import tkinter as tk
import numpy as np
import cv2
from tkinter import filedialog
from tkinter import *
import utils
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QPixmap, QImage
import sys

root = None

def desenharRetangulo(img, contornos):
    for contorno in contornos:
        peri = cv2.arcLength(contorno, True)
        approx = cv2.approxPolyDP(contorno, 0.02 * peri, True)
        if len(approx) == 4:
            cv2.drawContours(img, [approx], -1, (0, 0, 255), 5)
    return img

def upload_imagem():
    global questions, answers
    questions = int(questions_entry.get())
    answers = answers_text.get("1.0", "end-1c").split('\n')
    answers = [ord(a.upper()) - 65 for a in answers]
    file_path = filedialog.askopenfilename()
    processar_imagem(file_path)

def processar_imagem(path):
    global questions, answers
    widthImg = 700
    heightImg = 900

    img = cv2.imread(path)

    img = cv2.resize(img, (widthImg, heightImg))
    imgContours = img.copy()
    imgBiggestContours = img.copy()
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    imgCanny = cv2.Canny(imgBlur, 10, 50)

    contornos, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(imgContours, contornos, -1, (0, 255, 0), 10)

    imgContours = desenharRetangulo(imgContours, contornos)
    exibir_imagem("Retângulo Detectado!", imgContours)

    rectCon = utils.contorno_retangulo(contornos)

    if len(rectCon) > 3:
        rectCon = rectCon[1:4]

    rectCon = sorted(rectCon, key=lambda x: cv2.boundingRect(x)[0])

    allScores = []
    allResults = []

    questions_per_column = 15

    for i in range(len(rectCon)):
        contour = rectCon[i]
        cornerPoints = utils.obter_pontos_cantos(contour)

        if cornerPoints.size != 0:
            cv2.drawContours(imgBiggestContours, [cornerPoints], -1, (0, 255, 0), 20)
            cornerPoints = utils.reordenar(cornerPoints)

            pt1 = np.float32(cornerPoints)
            pt2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
            matrix = cv2.getPerspectiveTransform(pt1, pt2)
            imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))

            imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
            imgThresh = cv2.threshold(imgWarpGray, 150, 255, cv2.THRESH_BINARY_INV)[1]

            boxes = utils.dividir_caixas(imgThresh, questions_per_column, 5)
            myPixelVal = np.zeros((questions_per_column, 5))
            countC = 0
            countR = 0

            for image in boxes:
                totalPixels = cv2.countNonZero(image)
                myPixelVal[countR][countC] = totalPixels
                countC += 1
                if (countC == 5):
                    countC = 0
                    countR += 1

            myIndex = []
            for x in range(0, questions_per_column):
                arr = myPixelVal[x]
                myIndexVal = np.where(arr == np.amax(arr))
                myIndex.append(myIndexVal[0][0])

            grading = []
            for x in range(0, questions_per_column):
                if answers[x + i * questions_per_column] == myIndex[x]:
                    grading.append(1)
                else:
                    grading.append(0)
            score = (sum(grading) / questions_per_column) * 100

            allScores.append(score)
            allResults.append((imgWarpColored, myIndex, grading))

            imgResult = imgWarpColored.copy()
            imgResult = utils.mostrar_respostas(imgResult, myIndex, grading, answers[i * questions_per_column:(i + 1) * questions_per_column], questions_per_column, 5)
            imgRawDrawing = np.zeros_like(imgWarpColored)
            imgRawDrawing = utils.mostrar_respostas(imgRawDrawing, myIndex, grading, answers[i * questions_per_column:(i + 1) * questions_per_column], questions_per_column, 5)
            invmatrix = cv2.getPerspectiveTransform(pt2, pt1)
            imgInvWarp = cv2.warpPerspective(imgRawDrawing, invmatrix, (widthImg, heightImg))

            imgFinal = cv2.addWeighted(img, 1, imgInvWarp, 1, 0)
            exibir_imagem(f"Final Result {i+1}", imgFinal)  # Exibe com PyQt

    mostrar_todos_resultados(allScores, allResults)
    cv2.waitKey(0)  # Mantém as janelas abertas

def exibir_imagem(titulo, imagem):
    app = QApplication(sys.argv)
    label = QLabel()
    imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
    altura, largura, canal = imagem_rgb.shape
    bytes_por_linha = 3 * largura
    q_imagem = QImage(imagem_rgb.data, largura, altura, bytes_por_linha, QImage.Format_RGB888)
    label.setPixmap(QPixmap.fromImage(q_imagem))
    label.setWindowTitle(titulo)
    label.show()
    app.exec_()  # Inicia o loop de eventos PyQt

def mostrar_todos_resultados(scores, results):
    text_area.delete('1.0', END)
    for idx, (score, (img, myIndex, grading)) in enumerate(zip(scores, results)):
        for i in range(len(myIndex)):
            text_area.insert(END, f"{chr(65 + myIndex[i])}\n")

def voltar_ao_gerador(root_gerador):  # Recebe a referência da janela principal
    """Fecha a janela do Leitor de Cartão e mostra a janela do Gerador de Simulados."""
    global root
    root.destroy()
    root_gerador.deiconify()


def iniciar_leitor(root_gerador):
    global questions_entry, answers_text, text_area, questions, answers, root

    root = tk.Tk()
    root.title("SimuladoApp - Leitor de Cartão Resposta")
    root.geometry("500x400")
    root.configure(bg="#333333")

    questions_label = Label(root, text="Número de Questões:", bg="#333333", fg="#FFFFFF")
    questions_label.pack()
    questions_entry = Entry(root, bg="#555555", fg="#FFFFFF", insertbackground="#FFFFFF")
    questions_entry.pack()

    answers_label = tk.Label(root, text="Gabarito (uma por linha, ex: A\nB\nC\nD\nE):\n(Deixe em branco para ler do arquivo)", bg="#333333", fg="#FFFFFF")
    answers_label.pack()
    answers_text = tk.Text(root, height=5, width=20, bg="#555555", fg="#FFFFFF", insertbackground="#FFFFFF")
    answers_text.pack()

    upload_button = tk.Button(root, text="Carregar Imagem", command=upload_imagem, bg="#007BFF", fg="#FFFFFF")
    upload_button.pack(pady=20)

    text_area = tk.Text(root, height=10, width=50, bg="#555555", fg="#FFFFFF", insertbackground="#FFFFFF")
    text_area.pack()

    voltar_button = tk.Button(root, text="Voltar", command=lambda: voltar_ao_gerador(root_gerador),  # Passe root_gerador para a função lambda
                             bg="#FF5733", fg="#FFFFFF")
    voltar_button.pack(pady=10)

    root.mainloop()
