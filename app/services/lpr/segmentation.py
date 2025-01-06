import cv2
import numpy as np
import imutils

def normalizar(gradiente):
    '''
    Normaliza os valores do gradiente da imagem binarizada
    :param gradiente: Imagem binarizada após aplicação do cv2.Sobel() na direção x
    :return: Gradiente normalizado em uint8 com valores entre [0-255]
    '''
    gradiente=np.absolute(gradiente)
    (min, max)=np.min(gradiente), np.max(gradiente)
    gradiente=255*((gradiente-min)/(max-min))
    gradiente=gradiente.astype('uint8')
    return gradiente

def preprocessing(path):
    #Lendo imagem
    img=cv2.imread(path)

    # Cropping the top and bottom parts
    height, width, _ = img.shape
    top_crop = int(height * 0.2)  # Adjust the percentage as needed
    bottom_crop = int(height * 0.8)  # Adjust the percentage as needed
    cropped_img = img[top_crop:bottom_crop, :]

    #Convertendo para GrayScale
    gray= cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    #Reduzindo ruídos
    blur=cv2.bilateralFilter(gray, 9,75,75)
    # cv2.imshow('image',blur)
    # cv2.waitKey(0)
    #Operação morfologica Black-hat
    kernel= cv2.getStructuringElement(cv2.MORPH_RECT, (10,3))
    black_hat=cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, kernel)
    # cv2.imshow('image',black_hat)
    # cv2.waitKey(0)
    #Operação de fechamento
    kernel2=cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
    close = cv2.morphologyEx(black_hat, cv2.MORPH_CLOSE, kernel2)
    # cv2.imshow('image',close)
    # cv2.waitKey(0)
    #Binarização
    thresh= cv2.threshold(close,0 , 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    #Gradiente na Direção x
    gradient_x = cv2.Sobel(thresh, cv2.CV_64F, dx=1, dy=0, ksize=-1)
    gradient_x=normalizar(gradient_x)
    # cv2.imshow('image',gradient_x)
    # cv2.waitKey(0)
    #Redução de ruidos
    blur=cv2.GaussianBlur(gradient_x, (9,9), 0)
    #Operação de Fechamento
    close2=cv2.morphologyEx(blur,cv2.MORPH_CLOSE,kernel2)
    thresh2=cv2.threshold(close2,0,255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    #Erosão+Dilatação
    erode=cv2.erode(thresh2,None, iterations=3)#2
    dilate=cv2.dilate(erode, None, iterations=9)#1
    # cv2.imshow('image', dilate) # Mostra imagem dilatada
    # cv2.waitKey(0)
    croped=crop(dilate, gray)
    if croped is not None:
        # cv2.imshow('image', croped) # Mostra imagem cortada
        cv2.waitKey(0)
        cv2.imwrite('app\\services\\lpr\\croped\\crop01.jpg', croped)
        return 'app\\services\\lpr\\croped\\crop01.jpg'
    else:
        print('Placa não encontrada!')
        return None

def crop(img, gray):
    contornos = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cont = imutils.grab_contours(contornos)
    cnts = sorted(cont, key=cv2.contourArea, reverse=True)[:10]  # Aumentar o número de contornos analisados

    # Remover pequenos contornos (ruído)
    cnts = [c for c in cnts if cv2.contourArea(c) > 500] # Adicionei um filtro para remover contornos muito pequenos

    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        p = w / h

        # Ajustar os limites de proporção e área - mais flexíveis
        if 1.8 <= p <= 7 and 500 <= area <= 50000:  # Limites mais amplos para maior tolerância
            # Adicionando uma verificação para evitar proporções muito extremas
            if h > 10 and w > 10: # Verifica se a altura e largura são maiores que 10 pixels
                crop = gray[y:y + h, x:x + w]
                return crop

    return None # Retorna None se nenhum contorno adequado for encontrado

