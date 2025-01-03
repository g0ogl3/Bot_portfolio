from logic import DB_Manager
from config import DATABASE, TOKEN
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove()

cancel_button = "Отмена 🚫"

# Callback for canceling and hiding keyboard
def cansel(message):
    '''Бот отправляет текст, как посмотреть инфо + удаляет клавиатуру'''
    bot.send_message(message.chat.id, "Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)

# Message if no projects exist
def no_projects(message):
    '''Бот говорит, что у пользователя нет проектов'''
    bot.send_message(message.chat.id, 'У тебя пока нет проектов! 😢\nМожешь добавить их с помощью команды /new_project')

# Inline keyboard generation
def gen_inline_markup(rows):
    '''Генерация инлайн-клавиатуры'''
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup

# Reply keyboard generation with one-time use
def gen_markup(rows):
    '''Генерация реплай-клавиатуры с сокрытием после нажатия'''
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

# Project attributes for updates
attributes_of_projects = {'Имя проекта' : ["Введите новое имя проекта", "project_name"],
                          "Описание" : ["Введите новое описание проекта", "description"],
                          "Ссылка" : ["Введите новую ссылку на проект", "url"],
                          "Статус" : ["Выберите новый статус задачи", "status_id"]}

# Handler to provide info about a specific project
def info_project(message, user_id, project_name):
    '''
    Получает на вход id пользователя и имя проекта
    Возвращает информацию о проекте
    '''
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = 'Навыки пока не добавлены😥'
    bot.send_message(message.chat.id, f"""Project name: {info[0]}
Description: {info[1]}
Link: {info[2]}
Status: {info[3]}
Skills: {skills}
""")

# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    '''Бот отправляет приветствие и инфо о себе'''
    bot.send_message(message.chat.id, "Привет! Я бот-менеджер проектов 🎉\nПомогу тебе сохранить твои проекты и информацию о них!)")
    info(message)

# Info command - shows all available commands with emojis
@bot.message_handler(commands=['info'])
def info(message):
    '''Отправляет информацию о командах бота'''
    bot.send_message(message.chat.id,
"""
Вот команды, которые могут помочь:

/start - начать работу с ботом 🤖
/info - показать информацию о командах ℹ️
/new_project - добавить новый проект ➕
/projects - посмотреть все проекты 📂
/skills - добавить навыки к проекту 🛠️
/delete - удалить проект ❌
/update_projects - изменить проект 🔄

Также ты можешь ввести имя проекта и узнать информацию о нем! 📋
""")

# New project command
@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    '''Запрашивает название проекта и регистрирует следующий хэндлер для ввода описания'''
    bot.send_message(message.chat.id, "Введите название проекта:")
    bot.register_next_step_handler(message, name_project)

# Collects the name of the project and asks for description
def name_project(message):
    '''Получает название проекта, запрашивает описание и регистрирует следующий хэндлер'''
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "Введите описание проекта:")
    bot.register_next_step_handler(message, description_project, data=data)

# Collects description and asks for the project link
def description_project(message, data):
    '''Сохраняет описание проекта и продолжает сбор данных'''
    description = message.text
    data.append(description)
    bot.send_message(message.chat.id, "Введите ссылку на проект:")
    bot.register_next_step_handler(message, link_project, data=data)

# Collects project link, asks for the status
def link_project(message, data):
    '''Принимает на вход список данных и запрашивает статус проекта'''
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()]
    bot.send_message(message.chat.id, "Введите текущий статус проекта:", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

# Callback after selecting the project status
def callback_project(message, data, statuses):
    '''Обрабатывает выбор статуса проекта и сохраняет проект в БД'''
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in statuses:
        bot.send_message(message.chat.id, "Ты выбрал статус не из списка, попробуй еще раз!", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    bot.send_message(message.chat.id, "Проект сохранен! 🎉")

# Projects command - shows list of all projects
@bot.message_handler(commands=['projects'])
def get_projects(message):
    '''по id пользователя берем его проекты и выводим краткую информацию о проектах + кнопки для детального инфо'''
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
        bot.send_message(message.chat.id, text, reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)

# Skills command - allows user to add skills to a project
@bot.message_handler(commands=['skills'])
def skill_handler(message):
    '''Запрашивает для какого проекта добавить скиллы и регистрирует следующий хэндлер'''
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект, для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)

# Collects project name and asks for skills
def skill_project(message, projects):
    '''Получает проект и запрашивает навык для добавления к проекту'''
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(message.chat.id, 'Выбери навык:', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

# Adds skill to the project
def set_skill(message, project_name, skills):
    '''получаем навык из сообщения пользователя и добавляем этот навык к навыкам проекта'''
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
    if skill not in skills:
        bot.send_message(message.chat.id, 'Навык не из списка, попробуй еще раз!', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill)
    bot.send_message(message.chat.id, f'Навык {skill} добавлен проекту {project_name} 🛠️')

# Delete project command
@bot.message_handler(commands=['delete'])
def delete_handler(message):
    '''Вывод названий проектов для последующего удаления'''
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
    else:
        no_projects(message)

# Deletes project after confirmation
def delete_project(message, projects):
    '''Удаление проекта по id пользователя и названию проекта'''
    project = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
    if project not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй выбрать еще раз!', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'Проект {project} удален! ❌')

# Updates a project - starts by showing the list of projects
@bot.message_handler(commands=['update_projects'])
def update_project(message):
    '''Вывод названий проектов для последующего обновления'''
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "Выбери проект, который хочешь изменить", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
    else:
        no_projects(message)

# After project selection, asks which attribute to update
def update_project_step_2(message, projects):
    '''Выбор того, что нужно изменить в проекте'''
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "Что-то пошло не так! Выбери проект, который хочешь изменить ещё раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
        return
    bot.send_message(message.chat.id, "Выбери, что требуется изменить в проекте", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

# Collects new data for the selected attribute
def update_project_step_3(message, project_name):
    '''Если меняем статус или другие атрибуты проекта'''
    attribute = message.text
    reply_markup = None
    if message.text == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "Кажется, ты ошибся, попробуй ещё раз!", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup = gen_markup([x[0] for x in rows])
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup=reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

# Updates the project with the new attribute value
def update_project_step_4(message, project_name, attribute):
    '''Изменение статуса или другого атрибута проекта'''
    update_info = message.text
    if attribute == "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cansel(message)
        else:
            bot.send_message(message.chat.id, "Был выбран неверный статус, попробуй ещё раз!", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "Готово! Обновления внесены! 🔄")

# Text handler for any project-related queries
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    '''Обработка всех текстовых сообщений'''
    user_id = message.from_user.id
    projects = [x[2] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "Тебе нужна помощь? ℹ️")
    info(message)

# Start the bot's polling
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()
