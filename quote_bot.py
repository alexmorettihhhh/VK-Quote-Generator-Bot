# -*- coding: utf-8 -*-
import os
import io
import sys
import vk_api
import random
import json
from vk_api.longpoll import VkLongPoll, VkEventType
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import requests
import time
import traceback

if sys.platform == 'win32':
    import locale
    sys.stdout.reconfigure(encoding='utf-8')
    locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')

def log_message(message):

    print(f"[LOG] {message}")
    sys.stdout.flush()  

load_dotenv(encoding='utf-8')

vk_session = None
vk = None
longpoll = None
group_id = None

def init_vk():

    global vk_session, vk, longpoll, group_id
    
    token = os.getenv('VK_TOKEN')
    group_id = os.getenv('GROUP_ID')
    
    if not token or not group_id:
        print("Ошибка: Не найден токен VK или ID группы в файле .env")
        return False

    try:
        
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        
        group_info = vk.groups.getById(group_id=group_id)
        print(f"Подключено к группе: {group_info[0]['name']}")
        print(f"ID группы: {group_id}")
                
        longpoll = VkLongPoll(vk_session, group_id=int(group_id))
        print("LongPoll инициализирован")
        
        return True
    except Exception as e:
        print(f"Ошибка при инициализации: {e}")
        return False

def process_message(event, message_text):

    try:
        print("\n=== Анализ сообщения ===")
        print(f"Текст сообщения: {message_text}")
        print(f"ID пользователя: {event.user_id}")
        print(f"Peer ID: {event.peer_id}")
        print(f"Тип события: {event.type}")
        
        is_command = message_text.startswith('/')
        print(f"Является командой: {'✓' if is_command else '✗'}")
        
        return is_command
        
    except Exception as e:
        print(f"❌ Ошибка при обработке сообщения: {e}")
        return False


FAMOUS_QUOTES = [
    
    ("Единственный способ делать великие дела — любить то, что вы делаете", "Стив Джобс"),
    ("Успех — это способность шагать от одной неудачи к другой, не теряя энтузиазма", "Уинстон Черчилль"),
    ("Будущее зависит от того, что вы делаете сегодня", "Махатма Ганди"),
    ("Все наши мечты могут стать реальностью, если у нас хватит смелости их осуществить", "Уолт Дисней"),
    ("Жизнь — это то, что с тобой происходит, пока ты строишь другие планы", "Джон Леннон"),
    
    
    ("Неважно, насколько ты крут — найдется кто-то круче. Важно быть лучшей версией себя", "Джейсон Стэтхэм"),
    ("Если ты не рискуешь, ты не можешь создать будущее", "Джейсон Стэтхэм"),
    ("Я не боюсь смерти. Я боюсь жить жизнью, которая того не стоит", "Джейсон Стэтхэм"),
    ("Успех приходит к тем, кто слишком занят, чтобы искать его", "Джейсон Стэтхэм"),
    
    
    ("Никогда не сдавайся. Сегодня тяжело, завтра будет еще тяжелее, но послезавтра будет солнце", "Джек Ма"),
    ("Если тебе тяжело, значит ты поднимаешься в гору. Если тебе легко, значит ты летишь в пропасть", "Генри Форд"),
    ("Либо напиши что-то стоящее, либо делай что-то, о чем стоит написать", "Бенджамин Франклин"),
    
    
    ("Успех — это лестница, на которую не взобраться, держа руки в карманах", "Арнольд Шварценеггер"),
    ("Сложнее всего начать действовать, все остальное зависит только от упорства", "Амелия Эрхарт"),
    ("Если ты хочешь добиться успеха, ты должен верить в себя, даже когда никто другой в тебя не верит", "Конор Макгрегор"),
    
    
    ("Жизнь как фотография: используешь негатив, получаешь позитив", "Брюс Ли"),
    ("Не бойся, что не получится. Бойся, что не попробуешь", "Майкл Джордан"),
    ("Если ты не готов рисковать обычным, тебе придется довольствоваться обыденным", "Джим Рон"),
    
    
    ("Мечты не работают, пока не работаешь ты", "Джон Максвелл"),
    ("Никогда не поздно быть тем, кем ты мог бы быть", "Джордж Элиот"),
    ("Препятствия — это те страшные вещи, которые вы видите, когда отводите глаза от цели", "Генри Форд"),
    
    
    ("Сила не в том, чтобы бить сильно, а в том, чтобы подниматься, когда тебя бьют сильно", "Рокки Бальбоа"),
    ("Если ты устал бежать, иди. Если устал идти, ползи. Но не останавливайся", "Мать Тереза"),
    ("Каждая неудача — это шаг к успеху", "Уильям Уорд"),
    
    
    ("Самый тяжелый вес в спортзале — это вес входной двери", "Дуэйн Джонсон"),
    ("Не важно, как медленно ты продвигаешься, главное, что ты не останавливаешься", "Конфуций"),
    ("Лучше быть последним в списке орлов, чем первым в списке куриц", "Брюс Ли")
]

USER_DATA_FILE = 'user_data.json'

def load_user_data():

    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:

            empty_data = {}
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(empty_data, f, ensure_ascii=False, indent=2)
            return empty_data
    except Exception as e:
        print(f"Ошибка при загрузке данных пользователей: {e}")
        return {}

def save_user_data(data):
    
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении данных пользователей: {e}")

def get_user_info(user_id):
    
    try:
        user_info = vk.users.get(user_ids=user_id, fields=['photo_100'])[0]
        return user_info
    except Exception as e:
        print(f"Ошибка при получении информации о пользователе: {e}")
        return None

def download_image(url):
    
    response = requests.get(url)
    return Image.open(io.BytesIO(response.content))

def create_quote_image(text, user_info, author=None, bg_color='black'):

    width, height = 1200, 800  
    
    if isinstance(bg_color, str):
        try:
            bg_color = {
                'black': (0, 0, 0),
                'dark_blue': (0, 0, 139),
                'dark_green': (0, 100, 0),
                'dark_purple': (48, 25, 52),
                'dark_red': (139, 0, 0)
            }.get(bg_color, (0, 0, 0))
        except:
            bg_color = (0, 0, 0)
    
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Load fonts with fallback
    try:
        font_paths = [
            'C:\\Windows\\Fonts\\arial.ttf',
            'C:\\Windows\\Fonts\\calibri.ttf',
            'C:\\Windows\\Fonts\\segoeui.ttf'
        ]
        
        font_path = None
        for path in font_paths:
            if os.path.exists(path):
                font_path = path
                break
        
        if font_path:
            title_font = ImageFont.truetype(font_path, 72)  # Увеличенный размер
            name_font = ImageFont.truetype(font_path, 48)   # Увеличенный размер
            quote_font = ImageFont.truetype(font_path, 54)  # Увеличенный размер
            author_font = ImageFont.truetype(font_path, 42) # Увеличенный размер
            print(f"Используется шрифт: {font_path}")
        else:
            raise FileNotFoundError("Системные шрифты не найдены")
            
    except Exception as e:
        print(f"Ошибка загрузки шрифта: {e}. Используется шрифт по умолчанию.")
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        quote_font = ImageFont.load_default()
        author_font = ImageFont.load_default()

    # Draw title
    title_text = "Цитаты великих людей"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) // 2, 80), title_text, font=title_font, fill='white')

    # Функция для разбиения текста на строки
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            line = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), line, font=font)
            if bbox[2] - bbox[0] > max_width:
                if len(current_line) == 1:
                    lines.append(line)
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    # Draw quote with text wrapping
    quote_text = f'«{text}»'
    max_quote_width = width - 200  # Отступы по краям
    quote_lines = wrap_text(quote_text, quote_font, max_quote_width)
    
    # Вычисляем общую высоту текста
    line_height = quote_font.size + 20  # Добавляем отступ между строками
    total_height = len(quote_lines) * line_height
    
    # Начальная y-координата для центрирования текста по вертикали
    start_y = (height - total_height) // 2
    
    # Отрисовка строк текста
    for i, line in enumerate(quote_lines):
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        y = start_y + i * line_height
        draw.text((x, y), line, font=quote_font, fill='white')

    # Draw author if provided
    if author:
        author_text = f"— {author}"
        author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
        author_width = author_bbox[2] - author_bbox[0]
        author_y = start_y + total_height + 40  # Отступ от последней строки цитаты
        draw.text((width - author_width - 150, author_y), author_text, font=author_font, fill='white')

    try:
        # Download and paste user avatar
        avatar_size = 150  # Увеличенный размер аватара
        avatar_image = download_image(user_info['photo_100'])
        avatar_image = avatar_image.resize((avatar_size, avatar_size))
        
        # Create circular mask for avatar
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        
        # Apply circular mask to avatar
        output = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        output.paste(avatar_image, (0, 0))
        output.putalpha(mask)
        
        # Paste avatar
        image.paste(output, (80, height - 200), output)

        # Draw user name
        user_name = f"© {user_info['first_name']} {user_info['last_name']}"
        draw.text((80, height - 250), user_name, font=name_font, fill='white')
    except Exception as e:
        print(f"Ошибка при обработке аватара: {e}")
        # Если не удалось загрузить аватар, просто пропускаем его
        user_name = f"© {user_info['first_name']} {user_info['last_name']}"
        draw.text((80, height - 100), user_name, font=name_font, fill='white')

    # Save to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def upload_photo(vk, image_bytes, peer_id):
    """Upload photo to VK and get attachment string"""
    try:
        print("Получаем upload server...")
        upload_server = vk.photos.getMessagesUploadServer(peer_id=peer_id)
        upload_url = upload_server['upload_url']
        
        print(f"Отправляем фото на {upload_url}")
        files = {'photo': ('image.png', image_bytes.getvalue(), 'image/png')}
        response = requests.post(upload_url, files=files)
        
        # Добавляем проверку ответа
        print(f"Ответ сервера: {response.text}")
        response.raise_for_status()
        upload_data = response.json()
        
        print("Сохраняем фото...")
        photo = vk.photos.saveMessagesPhoto(
            photo=upload_data['photo'],
            server=upload_data['server'],
            hash=upload_data['hash']
        )[0]
        
        return f"photo{photo['owner_id']}_{photo['id']}"
    
    except Exception as e:
        print(f"❌ Critical upload error: {str(e)}")
        traceback.print_exc()
        return None

def get_help_message():
    return """Доступные команды:
/gen текст - Создать изображение с вашей цитатой
/random - Случайная цитата известного человека
/bg цвет - Изменить цвет фона (доступные цвета: black, dark_blue, dark_green, dark_purple, dark_red)
/save текст - Сохранить вашу любимую цитату
/mysave - Показать вашу сохраненную цитату
/help - Показать это сообщение"""

def send_message(peer_id, message=None, attachment=None):
    """Отправка сообщения"""
    try:
        vk.messages.send(
            peer_id=peer_id,
            message=message if message else "",
            attachment=attachment,
            random_id=random.randint(1, 1000000),
            disable_mentions=1
        )
        return True
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        return False

def main():
    load_dotenv()
    
    if not init_vk():
        print("Не удалось инициализировать бота")
        return
    
    print("Бот успешно запущен")
    user_data = load_user_data()
    
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    message_text = event.text.strip()
                    user_id = event.user_id
                    peer_id = event.peer_id
                    
                    print(f"\n=== New Message ===")
                    print(f"Raw message: {event.text}")
                    print(f"User ID: {user_id}, Peer ID: {peer_id}")

                    if peer_id != user_id:
                        mention = f"[id{group_id}|"
                        if mention not in event.text:
                            continue
                            
                        start_index = event.text.find(mention)
                        end_index = event.text.find(']', start_index) + 1
                        message_text = (event.text[:start_index] + event.text[end_index:]).strip()

                    if not message_text or not message_text.startswith('/'):
                        continue

                    user_id = str(user_id)
                    if user_id not in user_data:
                        user_data[user_id] = {'bg_color': 'black'}
                    
                    if message_text == '/help':
                        send_message(peer_id, get_help_message())
                    
                    elif message_text.startswith('/gen'):
                        try:
                            parts = message_text.split(' ', 1)
                            if len(parts) < 2:
                                raise ValueError("Нет текста для цитаты")
                            
                            user_info = get_user_info(user_id)
                            if not user_info:
                                raise ValueError("Ошибка получения данных пользователя")
                            
                            image_bytes = create_quote_image(
                                text=parts[1].strip(),
                                user_info=user_info,
                                bg_color=user_data[user_id].get('bg_color', 'black')
                            )
                            
                            attachment = upload_photo(vk, image_bytes, peer_id)
                            if not send_message(peer_id, attachment=attachment):
                                raise ValueError("Ошибка отправки сообщения")
                            
                        except Exception as e:
                            error_msg = f"Ошибка: {str(e)}"
                            print(error_msg)
                            send_message(peer_id, error_msg)
                    
                    elif message_text == '/random':
                        try:
                            quote, author = random.choice(FAMOUS_QUOTES)
                            user_info = get_user_info(user_id)
                            if not user_info:
                                send_message(peer_id, "Не удалось получить информацию о пользователе")
                                continue
                            
                            image_bytes = create_quote_image(quote, user_info, author=author, bg_color=user_data[user_id]['bg_color'])
                            attachment = upload_photo(vk, image_bytes, peer_id)
                            send_message(peer_id, attachment=attachment)
                        except Exception as e:
                            send_message(peer_id, f"Ошибка при создании изображения: {str(e)}")
                    
                    elif message_text == '/bg':
                        color = message_text.strip().lower()
                        available_colors = ['black', 'dark_blue', 'dark_green', 'dark_purple', 'dark_red']
                        if color in available_colors:
                            user_data[user_id]['bg_color'] = color
                            save_user_data(user_data)
                            send_message(peer_id, f"Цвет фона изменен на {color}")
                        else:
                            send_message(peer_id, f"Доступные цвета: {', '.join(available_colors)}")
                    
                    else:
                        send_message(peer_id, "Неизвестная команда. Используйте /help для просмотра списка команд")
                        
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(3)
            
            try:
                if init_vk():
                    print("Переподключение успешно")
                else:
                    print("Не удалось переподключиться")
            except:
                print("Ошибка при переподключении")

if __name__ == "__main__":
    main() 