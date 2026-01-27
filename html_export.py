"""
HTML экспорт - генерация журнала пропусков в index.html
"""
from datetime import datetime

def to_html(new_propusk: str):
    rez = 6 
    d = str(datetime.now())[0:10]
    if new_propusk.find('дминистрация') > -1:
        new_propusk = '<font color="#ff0e0e">' + new_propusk + '</font>'
    try:
        f = open('index.html', 'r')
        tmp_l = f.read().splitlines()
        f.close()
        dd = str(tmp_l[0])
        l = len(tmp_l)
        if d != dd:
            l = rez - 1
            dd = d

        f = open('index.html', 'w')
        tmp_l[0] = dd
        for i in range(0, (rez - 1)):
            f.write(str(tmp_l[i]) + '\n')

        f.write("<p>" + str(new_propusk) + "</p>" + '\n')

        if l >= rez:
            for i in range((rez - 1), l):
                f.write(str(tmp_l[i]) + '\n')
        f.close()
    except Exception as e:
        print(f"Ошибка HTML экспорта: {e}")
    return ()
