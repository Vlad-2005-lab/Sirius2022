import sqlite3
import time
import datetime
import threading

import sqlalchemy.exc
import telebot
from flask import Flask, request, abort
from telebot import types
from data import db_session
from data.device import Device
from data.task import Task
from data.employee import Employee
from emoji import emojize
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my the best secret key'

bot_jun = telebot.TeleBot(open('data/token_jun.txt').read())
bot_master = telebot.TeleBot(open('data/token_master.txt').read())
LAST_UID = ""
ADMIN_ID = [852437633, 271668384]
SMILE = [emojize("🟩"),
         emojize("🟧"),
         emojize("🟥"),
         emojize("⬛"),
         emojize(":left_arrow:"),
         emojize(":right_arrow:"),
         emojize("↩")]
try:
    db_session.global_init("bd/data.sqlite")
except sqlite3.OperationalError:
    db_session.global_init("/home/AVI2005/Сириус_2022/bd/data.sqlite")
except sqlalchemy.exc.OperationalError:
    db_session.global_init("/home/AVI2005/Сириус_2022/bd/data.sqlite")


# telegram bot

def keyboard_creator(list_of_names: list, one_time=True):
    """
    :param list_of_names: list; это список с именами кнопок(['1', '2'] будет каждая кнопка в ряд)
    [['1', '2'], '3'] первые 2 кнопки будут на 1 линии, а 3 снизу).
    :param one_time: bool; скрыть клавиатуру после нажатия или нет.
    :return: готовый класс клавиатуры внизу экрана.
    """
    returned_k = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=one_time)
    for i in list_of_names:
        if isinstance(i, list):
            string = ""
            for o in range(len(i) - 1):
                string += f"'{i[o]}', "
            string += f"'{i[-1]}'"
            exec(f"""returned_k.row({string})""")
            continue
        exec(f"""returned_k.row('{i}')""")
    return returned_k


def buttons_creator(dict_of_names: dict, how_many_rows=8):
    """
    :param dict_of_names: dict; это словарь, первые ключи могут быть любыми, они разделяют кнопки на ряды, а значениями
        этих ключей являются другие словари. Первый их аргумент это текст кнопки, а 2 это callback_data(то что будет
        передаваться в колл бек). Например: {
                                   '1': {
                                       'текст первой кнопки': 'нажали на кнопку 1',
                                       'текст второй кнопки': 'нажали на кнопку 2'
                                       },
                                   '2': {
                                       'текст третьей кнопки': 'нажали на кнопку 3'
                                       }
                               }
    :param how_many_rows: int; это максимальное количество кнопок в ряду.
    :return: готовый класс кнопок под сообщением
    """
    returned_k = types.InlineKeyboardMarkup(row_width=how_many_rows)
    for i in dict_of_names.keys():
        if type(dict_of_names[i]) is dict:
            count = 0
            for o in dict_of_names[i].keys():
                count += 1
                exec(f"""button{count} = types.InlineKeyboardButton(text='{o}',""" +
                     f""" callback_data='{dict_of_names[i][o]}')""")
            s = []
            for p in range(1, count + 1):
                s.append(f"button{p}")
            exec(f"""returned_k.add({', '.join(s)})""")
        else:
            exec(f"""button = types.InlineKeyboardButton(text='{i}', callback_data='{dict_of_names[i]}')""")
            exec(f"""returned_k.add(button)""")
    return returned_k


def get_buttons(devices: list, start=0) -> dict:
    buttons = {}
    if len(devices) == 0:
        buttons["нет устройств"] = "nope"
        buttons["Обновить"] = "update 0"
        return buttons
    for i in range(start, len(devices), 1):
        if i - start == 5:
            break
        device: Device = devices[i]
        box = SMILE[3]
        if not device.working and len(device.queue) == 0:
            box = SMILE[0]
        elif not device.working and len(device.queue) > 0:
            box = SMILE[1]
        elif device.working:
            box = SMILE[2]
        if not device.okey:
            box = SMILE[3]
        buttons[f"{i + 1}. {box} {device.name}"] = f"device {device.id} {start}"
    if len(devices) != 0 and len(devices) > 5:
        buttons["1"] = {SMILE[4]: f"left {start}",
                        "Обновить": f"update {start}",
                        SMILE[5]: f"right {start}"}
    if len(devices) != 0 and len(devices) <= 5:
        buttons["Обновить"] = "update 0"
    return buttons


def get_text_info(device: Device):
    session = db_session.create_session()
    status = ""
    if not device.working and len(device.queue) == 0:
        status = f"{SMILE[0]} свободен"
    elif not device.working and len(device.queue) > 0:
        status = f"{SMILE[1]} свободен, но имеется очередь"
    elif device.working:
        status = f"{SMILE[2]} занят"
    if not device.okey:
        status = f"{SMILE[3]} не работает"
    text = f"""{device.name}:\n\n""" + \
           f"""ID: {device.id}\n""" + \
           f"""состояние: {status}"""
    if device.working:
        text += "\n"
        task: Task = session.query(Task).filter(Task.id == device.queue[0]).first()
        text += f"""начало печати: {task.datetime[:-7]}\n"""
        text += f"""длительность печати: {task.duration}"""
    elif not device.working and len(device.queue) > 0:
        text += "\n"
        text += f"""в очереди: {len(device.queue[1:])}"""
    session.close()
    return text


def print_menu(message: telebot.types.Message):
    session = db_session.create_session()
    devices = session.query(Device).all()
    session.close()
    buttons = get_buttons(devices)
    bot_jun.send_message(message.from_user.id, f"Список устройств:", reply_markup=buttons_creator(buttons))


def get_seconds(date: datetime.timedelta):
    return date.days * 24 * 60 * 60 + date.seconds


@bot_jun.message_handler(content_types=['text'])
def get_text_messages(message: telebot.types.Message):
    text = "Здравствуйте, здесь вы можете посмотреть занятость принтеров.\n"
    bot_jun.send_message(message.from_user.id, text)
    text = "Для обозначения состояния принтера используются разные цвета:\n\n" \
           f"{SMILE[0]} - свободен\n" \
           f"{SMILE[1]} - печать закончена, но есть очередь на печать\n" \
           f"{SMILE[2]} - печатает\n" \
           f"{SMILE[3]} - не работает"
    bot_jun.send_message(message.from_user.id, text)
    print_menu(message)
    return bot_jun.register_next_step_handler(message, main_menu)


def main_menu(message: telebot.types.Message):
    session = db_session.create_session()
    employee = session.query(Employee).filter(Employee.tg_id == message.from_user.id).first()
    if employee:
        if employee.creating_task:
            id_device = message.text
            if message.text == "Отмена":
                print_menu(message)
                employee.creating_task = False
                session.commit()
                session.close()
                return bot_jun.register_next_step_handler(message, main_menu)
            if not id_device.isdigit():
                bot_jun.send_message(message.from_user.id, "Такого ID нет, попробуйте снова:",
                                     reply_markup=keyboard_creator(["Отмена"]))
                session.close()
                return bot_jun.register_next_step_handler(message, main_menu)
            id_device = int(id_device)
            employee = session.query(Employee).filter(Employee.tg_id == message.from_user.id).first()

            device = session.query(Device).filter(Device.id == id_device).first()
            if device.working:
                session.close()
                bot_jun.send_message(message.from_user.id,
                                     "Это устройство занято, используйте другое. Введите новое ID:",
                                     reply_markup=keyboard_creator(["Отмена"]))
                return bot_jun.register_next_step_handler(message, main_menu)
            if not device.okey:
                session.close()
                bot_jun.send_message(message.from_user.id,
                                     "Это устройство неготово, используйте другое. Введите новое ID:",
                                     reply_markup=keyboard_creator(["Отмена"]))
                return bot_jun.register_next_step_handler(message, main_menu)

            task = Task()
            task.id_employee = employee.id
            task.id_device = id_device
            task.datetime = str(datetime.datetime.now())
            session.add(task)
            session.commit()
            session.close()
            bot_jun.send_message(message.from_user.id,
                                 "На сколько по времени вы занимаете устройство(введите в формате ЧЧ:ММ:СС):",
                                 reply_markup=keyboard_creator(["Отмена"]))
            return bot_jun.register_next_step_handler(message, task_ask_2)
    if message.text == "/my_id":
        bot_jun.send_message(message.from_user.id, f"Ваш Tg_ID: {message.from_user.id}")
    else:
        print_menu(message)
    return bot_jun.register_next_step_handler(message, main_menu)


@bot_jun.callback_query_handler(func=lambda call: call.data.split()[0] == "left")
def callback_worker_left(call: telebot.types.CallbackQuery):
    session = db_session.create_session()
    devices = session.query(Device).all()
    if int(call.data.split()[1]) == 0:
        n = len(devices)
        if n % 5 == 0:
            buttons = get_buttons(devices, (n // 5 - 1) * 5)
        else:
            buttons = get_buttons(devices, n // 5 * 5)
    else:
        buttons = get_buttons(devices, int(call.data.split()[1]) - 5)
    bot_jun.edit_message_text("Список устройств:", call.message.chat.id, call.message.message_id,
                              reply_markup=buttons_creator(buttons))
    session.close()


@bot_jun.callback_query_handler(func=lambda call: call.data.split()[0] == "right")
def callback_worker_right(call: telebot.types.CallbackQuery):
    session = db_session.create_session()
    devices = session.query(Device).all()
    n = len(devices)
    if int(call.data.split()[1]) + 5 + 1 > n:
        buttons = get_buttons(devices, 0)
    else:
        buttons = get_buttons(devices, int(call.data.split()[1]) + 5)
    bot_jun.edit_message_text("Список устройств:", call.message.chat.id, call.message.message_id,
                              reply_markup=buttons_creator(buttons))
    session.close()


@bot_jun.callback_query_handler(func=lambda call: call.data.split()[0] == "update")
def callback_worker_update(call: telebot.types.CallbackQuery):
    session = db_session.create_session()
    devices = session.query(Device).all()
    n = len(devices)
    if int(call.data.split()[1]) + 1 > n:
        buttons = get_buttons(devices, 0)
    else:
        buttons = get_buttons(devices, int(call.data.split()[1]))
    try:
        bot_jun.edit_message_text("Список устройств:", call.message.chat.id, call.message.message_id,
                                  reply_markup=buttons_creator(buttons))
    except telebot.apihelper.ApiTelegramException:
        pass
    session.close()


@bot_jun.callback_query_handler(func=lambda call: call.data.split()[0] == "device")
def callback_worker_info(call: telebot.types.CallbackQuery):
    session = db_session.create_session()
    device: Device = session.query(Device).filter(Device.id == int(call.data.split()[1])).first()
    text = get_text_info(device)
    buttons = {"1": {
        "обновить": f"device {call.data.split()[1]} {call.data.split()[2]}",
        SMILE[6]: f"back {call.data.split()[2]}"
    }}
    try:
        bot_jun.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                  reply_markup=buttons_creator(buttons))
    except telebot.apihelper.ApiTelegramException:
        pass
    session.close()


@bot_jun.callback_query_handler(func=lambda call: call.data.split()[0] == "back")
def callback_worker_back(call: telebot.types.CallbackQuery):
    session = db_session.create_session()
    devices = session.query(Device).all()
    n = len(devices)
    if int(call.data.split()[1]) + 1 <= n:
        buttons = get_buttons(devices, int(call.data.split()[1]))
    else:
        buttons = get_buttons(devices)
    bot_jun.edit_message_text("Список устройств:", call.message.chat.id, call.message.message_id,
                              reply_markup=buttons_creator(buttons))
    session.close()


def task_ask_2(message: telebot.types.Message):
    session = db_session.create_session()
    employee = session.query(Employee).filter(Employee.tg_id == message.from_user.id).first()
    tasks = session.query(Task).filter(Task.id_employee == employee.id).all()
    if message.text == "Отмена":
        for task in tasks:
            if task.duration == "":
                session.delete(task)
        employee.creating_task = False
        session.commit()
        session.close()
        print_menu(message)
        return bot_jun.register_next_step_handler(message, main_menu)
    pattern = r"\d+:\d+:\d+"
    if not re.match(pattern, message.text):
        session.close()
        bot_jun.send_message(message.from_user.id, "Вы ввели время в неправильном формате, попробуйте снова(ЧЧ:ММ:СС):",
                             reply_markup=keyboard_creator(["Отмена"]))
        return bot_jun.register_next_step_handler(message, task_ask_2)
    task = None
    for i in tasks:
        i: Task
        if i.duration == "":
            task = i
    task.duration = message.text
    device = session.query(Device).filter(Device.id == task.id_device).first()
    device.working = True
    device.queue = device.queue + [task.id]
    session.commit()
    session.close()
    print_menu(message)
    return bot_jun.register_next_step_handler(message, main_menu)


# Telegram admin bot


def print_help(message: telebot.types.Message):
    text = ""
    text += "/add_device - добавить устройство\n"
    text += "/update_device - обновить информацию об устройстве\n"
    text += "/delete_device - удалить устройство\n"
    text += "/create_employee - создать сотрудника\n"
    text += "/update_employee - обновить информацию об сотруднике\n"
    text += "/delete_employee - удалить сотрудника\n"
    text += "/get_all_devices - получить все устройства\n"
    text += "/get_all_employees - получить всех сотрудников\n"
    bot_master.send_message(message.from_user.id, text)


@bot_master.message_handler(content_types=['text'])
def get_text_messages_master(message: telebot.types.Message):
    if message.from_user.id not in ADMIN_ID:
        bot_master.send_message(message.from_user.id,
                                "Вы не администратор")
        return bot_master.register_next_step_handler(message, get_text_messages_master)
    match message.text:
        case "/add_device":
            bot_master.send_message(message.from_user.id,
                                    "Введите данные(name;okey):",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, add_device)
        case "/update_device":
            bot_master.send_message(message.from_user.id,
                                    "Введите данные(id;name;okey):",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, update_device)
        case "/delete_device":
            bot_master.send_message(message.from_user.id,
                                    "Введите данные(id):",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, delete_device)
        case "/create_employee":
            bot_master.send_message(message.from_user.id,
                                    "Введите данные(tg_id;name;uid;valid_from;valid_to):",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, delete_device)
        case "/update_employee":
            bot_master.send_message(message.from_user.id,
                                    "Введите данные(id;tg_id;name;uid;valid_from;valid_to):",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, delete_device)
        case "/delete_employee":
            bot_master.send_message(message.from_user.id,
                                    "Введите данные(id):",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, delete_device)
        case "/get_all_devices":
            pass
        case "/get_all_employees":
            pass
        case _:
            print_help(message)
    return bot_master.register_next_step_handler(message, get_text_messages_master)


def add_device(message: telebot.types.Message):
    args = message.text.split(";")
    if message.text == "Отмена":
        print_help(message)
        return bot_master.register_next_step_handler(message, get_text_messages_master)
    if len(args) != 2:
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, add_device)
    name = args[0]
    okey = True if args[1].lower() in ["true", "1"] else False
    device = Device()
    device.name = name
    device.okey = okey
    session = db_session.create_session()
    session.add(device)
    session.commit()
    session.close()
    bot_master.send_message(message.from_user.id, "Успешно создано")
    return bot_master.register_next_step_handler(message, get_text_messages_master)


def update_device(message: telebot.types.Message):
    args = message.text.split(";")
    if message.text == "Отмена":
        print_help(message)
        return bot_master.register_next_step_handler(message, get_text_messages_master)
    if len(args) != 3:
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, update_device)
    if not args[0].isdigit():
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, update_device)
    device_id = int(args[0])
    name = args[1]
    okey = True if args[2].lower() in ["true", "1"] else False
    session = db_session.create_session()
    device = session.query(Device).filter(Device.id == device_id).first()
    if device is None:
        bot_master.send_message(message.from_user.id, "Такого id нет, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, update_device)
    if name != "":
        device.name = name
    if args[2] != "":
        device.okey = okey
    session.commit()
    session.close()
    bot_master.send_message(message.from_user.id, "Успешно обновлено")
    return bot_master.register_next_step_handler(message, get_text_messages_master)


def delete_device(message: telebot.types.Message):
    if message.text == "Отмена":
        print_help(message)
        return bot_master.register_next_step_handler(message, get_text_messages_master)
    if not message.text.isdigit():
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, delete_device)
    session = db_session.create_session()
    device = session.query(Device).filter(Device.id == int(message.text)).first()
    if device is None:
        bot_master.send_message(message.from_user.id, "Такого id нет, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, delete_device)
    session.delete(device)
    session.commit()
    session.close()
    bot_master.send_message(message.from_user.id, "Успешно удалено")
    return bot_master.register_next_step_handler(message, get_text_messages_master)


def create_employee(message: telebot.types.Message):
    global LAST_UID
    session = db_session.create_session()
    # Введите данные(tg_id; name; uid; valid_from; valid_to)
    args = message.text.split(";")
    if message.text == "Отмена":
        print_help(message)
        return bot_master.register_next_step_handler(message, get_text_messages_master)
    if len(args) != 5:
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, create_employee)
    employee = Employee()
    tg_id, name, uid, valid_from, valid_to = None, None, LAST_UID, None, None
    if args[0] == "":
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, create_employee)
    tg_id = int(args[0])
    if args[1] == "":
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, create_employee)
    name = args[1]
    pattern = "%Y-%m-%d %H:%M:%S.%f"
    if args[2] != "":
        uid = args[2]
    if args[3] != "":
        try:
            valid_from = datetime.datetime.strptime(args[3], pattern)
        except Exception as err:
            bot_master.send_message(message.from_user.id, f"{err}, попробуйте снова:",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, add_device)
    if args[4] != "":
        try:
            valid_to = datetime.datetime.strptime(args[4], pattern)
        except Exception as err:
            bot_master.send_message(message.from_user.id, f"{err}, попробуйте снова:",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, add_device)
    employee.tg_id = tg_id
    employee.name = name
    employee.uid = uid
    employee.valid_from = valid_from
    employee.valid_to = valid_to
    try:
        session.add(employee)
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        session.close()
    session.close()
    bot_master.send_message(message.from_user.id, "Успешно создан")
    return bot_master.register_next_step_handler(message, get_text_messages_master)


def update_employee(message: telebot.types.Message):
    # Введите данные(id;tg_id;name;uid;valid_from;valid_to):
    session = db_session.create_session()
    args = message.text.split(";")
    if message.text == "Отмена":
        print_help(message)
        return bot_master.register_next_step_handler(message, get_text_messages_master)
    if len(args) != 6:
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, update_employee)
    if not args[0].isdigit():
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, update_employee)
    employee = session.query(Employee).filter(Employee.id == int(args[0])).first()
    if employee is None:
        bot_master.send_message(message.from_user.id, "Такого id нет, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, update_employee)
    args = args[1:]
    tg_id = employee.tg_id
    name = employee.name
    uid = employee.uid
    valid_from = employee.valid_from
    valid_to = employee.valid_to
    if args[0] != "":
        tg_id = int(args[0])
    if args[1] != "":
        name = args[1]
    pattern = "%Y-%m-%d %H:%M:%S.%f"
    if args[2] != "":
        uid = args[2]
    if args[3] != "":
        try:
            valid_from = datetime.datetime.strptime(args[3], pattern)
        except Exception as err:
            bot_master.send_message(message.from_user.id, f"{err}, попробуйте снова:",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, update_employee)
    if args[4] != "":
        try:
            valid_to = datetime.datetime.strptime(args[4], pattern)
        except Exception as err:
            bot_master.send_message(message.from_user.id, f"{err}, попробуйте снова:",
                                    reply_markup=keyboard_creator(["Отмена"]))
            return bot_master.register_next_step_handler(message, update_employee)
    employee.tg_id = tg_id
    employee.name = name
    employee.uid = uid
    employee.valid_from = valid_from
    employee.valid_to = valid_to
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        session.close()
    session.close()
    bot_master.send_message(message.from_user.id, "Успешно обновлен")
    return bot_master.register_next_step_handler(message, get_text_messages_master)


def delete_employee(message: telebot.types.Message):
    if message.text == "Отмена":
        print_help(message)
        return bot_master.register_next_step_handler(message, get_text_messages_master)
    if not message.text.isdigit():
        bot_master.send_message(message.from_user.id, "Неверно введены данные, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, delete_employee)
    session = db_session.create_session()
    employee = session.query(Employee).filter(Employee.id == int(message.text)).first()
    if employee is None:
        bot_master.send_message(message.from_user.id, "Такого id нет, попробуйте снова:",
                                reply_markup=keyboard_creator(["Отмена"]))
        return bot_master.register_next_step_handler(message, delete_employee)
    session.delete(employee)
    session.commit()
    session.close()
    bot_master.send_message(message.from_user.id, "Успешно удалено")
    return bot_master.register_next_step_handler(message, get_text_messages_master)


def get_all_devices(message: telebot.types.Message):
    pass


def get_all_employees(message: telebot.types.Message):
    pass


# Telegram bot checker
def checker():
    pattern = "%Y-%m-%d %H:%M:%S.%f"
    while True:
        time_now = datetime.datetime.now()
        session = db_session.create_session()
        tasks = session.query(Task).all()
        for task in tasks:
            task: Task
            try:
                task_datetime = datetime.datetime.strptime(task.datetime, pattern)
                hh, mm, ss = map(int, task.duration.split(":"))
                task_end_datetime = task_datetime + datetime.timedelta(hours=hh, minutes=mm, seconds=ss)
                if get_seconds(task_end_datetime - time_now) < 0:
                    # уведомление
                    employee = session.query(Employee).filter(Employee.id == task.id_employee).first()
                    device = session.query(Device).filter(Device.id == task.id_device).first()
                    bot_jun.send_message(employee.tg_id,
                                         f"""Устройство "{device.name}" с ID: {device.id} завершило работу""")
                    device.queue = []
                    device.working = False
                    session.delete(task)
                    session.commit()
            except Exception as err:
                print(err)
        session.close()
        time.sleep(60)


# Flask api


@app.route('/api/get_all_devices', methods=['GET'])
def get_all_devices():
    session = db_session.create_session()
    devices = session.query(Device).all()
    ans = []
    for device in devices:
        device: Device
        js = {"id": device.id,
              "name": device.name,
              "working": device.working,
              "okey": device.okey,
              "queue": device.queue}
        ans.append(js)
    return ans


@app.route('/api/add', methods=['POST'])
def add():
    if not request.json:
        abort(500)
    session = db_session.create_session()
    device = Device()
    device.name = request.json["name"]
    device.okey = request.json["okey"]
    session.add(device)
    session.commit()
    session.close()
    return "ok"


@app.route('/api/update', methods=['POST'])
def update():
    if not request.json:
        abort(500)
    session = db_session.create_session()
    try:
        update_id = request.json["id"]
        device = session.query(Device).filter(Device.id == update_id).first()
        name = request.json.get("name")
        working = request.json.get("working")
        okey = request.json.get("okey")
        queue = request.json.get("queue")
        if not (name is None):
            device.name = name
        if not (working is None):
            device.working = working
        if not (okey is None):
            device.okey = okey
        if not (queue is None):
            device.queue = queue
    except KeyError:
        session.close()
        abort(500)
    session.commit()
    session.close()
    return "ok"


@app.route('/api/delete', methods=['POST'])
def delete():
    if not request.json:
        abort(500)
    session = db_session.create_session()
    try:
        delete_id = request.json["id"]
        device = session.query(Device).filter(Device.id == delete_id).first()
        session.delete(device)
    except KeyError:
        session.close()
        abort(500)
    session.commit()
    session.close()
    return "ok"


@app.route('/api/get_all_employees', methods=['GET'])
def get_all_employees():
    session = db_session.create_session()
    employees = session.query(Employee).all()
    ans = []
    for employee in employees:
        employee: Employee
        js = {"id": employee.id,
              "name": employee.name,
              "tg_id": employee.tg_id,
              "uid": employee.uid,
              "creating_task": employee.creating_task}
        ans.append(js)
    return ans


@app.route('/api/create_employee', methods=['POST'])
def create_employee():
    global LAST_UID
    if not request.json:
        abort(500)
    session = db_session.create_session()
    try:
        employee = Employee()
        employee.tg_id = request.json.get("tg_id")
        employee.name = request.json.get("name")
        employee.uid = request.json.get("uid")
        if request.json.get("uid") == "":
            employee.uid = LAST_UID
        session.add(employee)
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        session.close()
        abort(500)
    session.close()
    return "created"


@app.route('/api/update_employee', methods=['POST'])
def update_employee():
    if not request.json:
        abort(500)
    session = db_session.create_session()
    employee_id = request.json.get("id")
    employee_tg_id = request.json.get("tg_id")
    employee_name = request.json.get("name")
    employee_uid = request.json.get("uid")
    if employee_id == "":
        abort(500)
    try:
        employee_id = int(employee_id)
        employee = session.query(Employee).filter(Employee.id == employee_id).first()
        if employee is None:
            abort(500)
        employee.name = employee_name
        employee.tg_id = employee_tg_id
        employee.uid = employee_uid
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        session.close()
        abort(500)
    session.close()
    return "updated"


@app.route('/api/delete_employee', methods=['POST'])
def delete_employee():
    if not request.json:
        abort(500)
    session = db_session.create_session()
    employee_id = request.json.get("id")
    if employee_id == "":
        abort(500)
    employee_id = int(employee_id)
    employee = session.query(Employee).filter(Employee.id == employee_id).first()
    if employee is None:
        abort(500)
    session.delete(employee)
    session.commit()
    session.close()
    return "deleted"


@app.route('/api/check_uid', methods=['POST'])
def check_uid():
    global LAST_UID
    if not request.json:
        abort(500)
    session = db_session.create_session()
    uid = request.json.get("uid")
    if uid == "":
        abort(500)
    LAST_UID = uid
    employees = session.query(Employee).all()
    pattern = "%Y-%m-%d %H:%M:%S.%f"
    for employee in employees:
        employee: Employee
        if employee.uid == uid:
            valid_from = employee.valid_from
            valid_to = employee.valid_to
            today = datetime.datetime.now()
            if valid_from:
                try:
                    valid_from = datetime.datetime.strptime(valid_from, pattern)
                except Exception as err:
                    print(err)
                    session.close()
                    return "closed"
                if get_seconds(today - valid_from) < 0:
                    bot_jun.send_message(employee.tg_id, "У вас недостаточно прав.")
                    session.close()
                    return "closed"
            if valid_to:
                try:
                    valid_to = datetime.datetime.strptime(valid_to, pattern)
                except Exception as err:
                    print(err)
                    session.close()
                    return "closed"
                if get_seconds(valid_to - today) < 0:
                    bot_jun.send_message(employee.tg_id, "У вас недостаточно прав.")
                    session.close()
                    return "closed"
            bot_jun.send_message(employee.tg_id,
                                 "Введите ID устройства(можно узнать, если нажать на устройство в списке):",
                                 reply_markup=keyboard_creator(["Отмена"]))
            employee.creating_task = True
            session.commit()
            session.close()
            return "ok"
    session.commit()
    session.close()
    return "closed"


# Starting functions


def start_bot():
    while True:
        try:
            print('\033[0mStarting.....')
            bot_jun.infinity_polling()
        except Exception as err:
            print('\033[31mCrashed.....')
            print(f"Error: {err}")
            time.sleep(5)
            print('\033[35mRestarting.....')


def start_bot_master():
    while True:
        try:
            print('\033[0mStarting.....')
            bot_master.infinity_polling()
        except Exception as err:
            print('\033[31mCrashed.....')
            print(f"Error: {err}")
            time.sleep(5)
            print('\033[35mRestarting.....')


def start_checker():
    while True:
        try:
            checker()
        except Exception as err:
            print(f"Error: {err}")
            time.sleep(5)


def start_api():
    app.run(port=8080)


thread_bot = threading.Thread(target=start_bot)
thread_bot_master = threading.Thread(target=start_bot_master)
thread_checker = threading.Thread(target=start_checker)
thread_api = threading.Thread(target=start_api)
thread_bot.start()
thread_bot_master.start()
thread_checker.start()
thread_api.start()
