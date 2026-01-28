"""
Модуль реализует простую файловую базу данных (bd.txt) на основе списков Python с кэшированием в памяти. 
"""
from array import array

# Глобальные переменные БД, не менять!
"""
Глобальные списки для хранения данных БД в памяти (переопределяют array).
Инициализируются с фиктивным нулевым элементом ['None'], чтобы избежать IndexError 
при обращении к id[0] во время загрузки или поиска.
"""

id = array('w',[]) # dict()#
company = array('w',[]) # dict() #
tmp_l = dict() #array('w',[])
company=['None'] #company=['Администрация','abcde']
id= ['None'] #id= ['111', '222', '333', '444']
fio= ['None']
phone= ['None']

sent_messages = {}

def find_in_bd(usr_id: str):
    z = -1
    print(usr_id)
    for j in range(len(id)):
        if str(id[j]) == str(usr_id):
            z = j
    if z == -1:
        c = "null"
    else:
        c = company[z]
    return c

def find_by_name(a: str):
    if len(id) == 0:
        print(id)
        load_bd()
    c = -1
    n = 0
    a = a.lower()
    for j in range(len(company)):
        b = company[j].lower()
        if b.find(a) > -1:
            c = j
            n = n + 1
    if c == -1:
        for j in range(len(id)):
            if id[j].find(a) > -1:
                c = j
                n = n + 1
    if n > 1:
        c = -2
    return c

def find_return_ID(usr_id: str):
    for j in range(len(id)):
        if str(id[j]) == str(usr_id):
            return j
    return -1

def input_bd(usr_id, company_usr, phone_contact):
    company_usr = company_usr.replace('\n', ' ')
    id.append(str(usr_id))
    company.append(str(company_usr))
    print(str(phone_contact))
    phone.append(str(phone_contact))
    return ()

def del_bd(a: int):
    if len(id) == 0:
        load_bd()
    id.pop(a)
    company.pop(a)
    phone.pop(a)
    save_bd()

def save_bd():
    with open('bd.txt', 'w', encoding='utf-8') as f:
        l = len(id)
        f.write(str(l - 1) + '\n')
        for i in range(1, l):
            f.write(str(id[i]) + ';')
            f.write(str(company[i]) + ';')
            f.write(str(phone[i]) + '\n')
    return

def load_bd():
    if len(id) > 1:
        return ()
    company[0] = "None"
    id[0] = "None"
    phone[0] = "None"
    try:
        f = open('bd.txt', 'r', encoding='utf-8')
        tmp_l = f.read().splitlines()
        f.close()
        print('База данных загружена из файла', len(tmp_l))
        ll = int(tmp_l[0])
        for i in range(ll):
            data = tmp_l[i + 1].split(";")
            id.append(data[0])
            company.append(data[1])
            phone.append(data[2])
    except FileNotFoundError:
        print("Файл БД не найден")
    return ()

