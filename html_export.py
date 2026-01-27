"""
HTML экспорт - генерация журнала пропусков в index.html
"""
from datetime import datetime


def to_html(new_propusk: str):
    """
    Заполняет html файл пропусками за текущий день.
    rez = 6 - количество строк зарезервированных под заголовок
    """
    rez = 6  # количество строк под заголовок
    d = str(datetime.now())[0:10]  # текущая дата
    
    if new_propusk.find('дминистрация') > -1:
        new_propusk = '<span style="color:#FF0000;">' + new_propusk + '</span>'
    
    f = open('index.html', 'r')
    tmp_l = f.read().splitlines()
    f.close()
    
    dd = str(tmp_l[0])  # дата которая записана в файле
    l = len(tmp_l)
    
    if d != dd:  # если новый день - новый файл
        l = rez - 1
        dd = d
        f = open('index.html', 'w')
        tmp_l[0] = dd
        for i in range(0, (rez - 1)):  # переносим шапку
            f.write(str(tmp_l[i]) + '\n')
        f.write("<tr><td colspan=\"3\">" + new_propusk + "</td></tr>\n")
        for i in range((rez - 1), l):
            f.write(str(tmp_l[i]) + '\n')
        f.close()
    else:  # в файл текущего дня добавляем строку
        f = open('index.html', 'w')
        for i in range(0, l):
            f.write(str(tmp_l[i]) + '\n')
        f.write("<tr><td colspan=\"3\">" + new_propusk + "</td></tr>\n")
        f.close()
    
    return ()
