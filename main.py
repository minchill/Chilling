# main.py
import discord
from discord.ext import commands
import os
import sqlite3
import random
import asyncio
from datetime import datetime
from gtts import gTTS
import tempfile
import time
import logging

# ---------------------------
# CONFIG / LOGGING
# ---------------------------
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('yubabe_clone')

TOKEN = os.getenv('DISCORD_TOKEN')  # Railway env var
WELCOME_CHANNEL_ID = 123456789012345678  # <-- Thay bằng ID kênh welcome của bạn

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

# We'll keep Discord commands prefix as '!' internally, but allow users to type `b...`
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# ---------------------------
# GAME / DATA CONFIG
# ---------------------------
RARITY_CONFIG = {
    "Hư Hại": 35, "Bình Thường": 30, "Hiếm Có": 20, "Sử Thi": 10,
    "Bán Thần Thoại": 4, "Thần Thoại": 0.9, "Đấng Cứu Thế": 0.1,
}
RARITY_NAMES = list(RARITY_CONFIG.keys())
RARITY_WEIGHTS = list(RARITY_CONFIG.values())

WEAPON_TYPES = [
    "Kiếm Lưỡi Hái", "Kiếm Nhật Katana", "Kiếm Thiên Thần", "Song Kiếm", "Kiếm Lửa Địa Ngục",
    "Trượng Bão Tuyết", "Trượng Sấm Sét", "Trượng Hồi Sinh", "Trượng Cổ Đại", "Trượng Lửa",
    "Súng Laser", "Súng Pháo Đài", "Súng Bắn Tỉa", "Súng Máy Mini", "Súng Lục",
    "Giáp Rồng", "Giáp Thép Titan", "Giáp Pha Lê", "Giáp Hộ Mệnh", "Giáp Bóng Đêm",
    "Cung Thần Gió", "Cung Băng Giá", "Cung Tinh Linh", "Nỏ Lớn", "Cung Ngắn",
    "Khiên Kim Cương", "Khiên Titan", "Khiên Phù Thủy", "Khiên Rồng", "Khiên Gỗ Cứng",
]

SKILLS = [
    "Cú Đấm Sấm Sét", "Hơi Thở Rồng", "Lá Chắn Ánh Sáng", "Hồi Máu Diện Rộng", "Tăng Tốc Độ",
    "Chém Xuyên Giáp", "Bắn Tỉa Chí Mạng", "Triệu Hồi Thần", "Khóa Kỹ Năng", "Hút Hồn",
    "Độc Tố Lan Truyền", "Phục Kích", "Đỡ Đòn Hoàn Hảo", "Nộ Long", "Ám Ảnh",
    "Băng Giá Vĩnh Cửu", "Hỏa Diệm Sơn", "Tia Chớp Phẫn Nộ", "Kháng Ma Thuật", "Phá Vỡ Khiên",
    "Thao Túng Thời Gian", "Dịch Chuyển Tức Thời", "Hóa Đá Kẻ Thù", "Mưa Mũi Tên", "Bẫy Ngầm",
    "Gió Lốc Cuồng Nộ", "Tiếng Thét Hủy Diệt", "Lưỡi Cắt Không Gian", "Nguyền Rủa Sức Mạnh", "Gây Mù",
    "Tạo Vòng Bảo Vệ", "Lôi Đài Chiến Đấu", "Sức Mạnh Bất Diệt", "Cú Đấm Ngàn Cân", "Hào Quang Phép Thuật",
    "Phục Hồi Nhanh", "Tấn Công Liên Hoàn", "Hóa Giải Độc", "Tăng Sức Chịu Đựng", "Nước Mắt Thiên Thần",
    "Gia Tăng Tầm Đánh", "Cảm Tử", "Bóng Ma", "Khiên Phản Chiếu", "Tăng Tỷ Lệ Rớt Đồ",
    "Thu Phục Quái Vật", "Biến Hình", "Áp Chế", "Khóa Mục Tiêu", "Cơ Động Thần Tốc",
]

PET_NAMES = [
    "Lân Sư Rồng (Tết)", "Chim Lạc (Giỗ Tổ)", "Cóc Thần (Mưa)", "Thiên Cẩu (Trung Thu)", "Rồng Vàng (Mùng 1)",
    "Hùng Vương Thần Lực", "Thánh Gióng", "Âu Cơ", "Lạc Long Quân", "Phù Đổng Thiên Vương",
    "Hổ Đông Dương", "Voi Rừng Tây Nguyên", "Sơn Tinh", "Thủy Tinh", "Sếu Đầu Đỏ",
    "Tinh Linh Ánh Sáng", "Bóng Ma Cổ", "Thần Tài Mini", "Tiên Nữ Hoa", "Quỷ Lửa",
    *[f"Pet Chiến Đấu {i}" for i in range(1, 31)]
]

PET_ELEMENTS = ["Lửa", "Nước", "Gió", "Đất", "Ánh Sáng", "Bóng Tối"]

HIDDEN_PET_NAME = "Hồ Chí Minh Bất Tử"
HIDDEN_PET_RARITY = "Đấng Cứu Thế"
HIDDEN_PET_DATE = (5, 19)  # (month, day)

WELCOME_MESSAGES = [
    "🎉 Chào mừng **{name}** đến với bến đỗ mới! Đã tặng **100** xu khởi nghiệp.",
    "🥳 Woa! **{name}** đã xuất hiện! Sẵn sàng quẩy chưa? (100 xu đã vào ví)",
    "👋 Huhu, mừng **{name}** ghé thăm! Mau vào tìm đồng đội nào. (100 xu)",
    "👾 Thành viên mới **{name}** vừa hạ cánh. Cẩn thận, code bot tôi đã bị thay đổi! (100 xu)",
    "🔔 Thông báo: **{name}** đã gia nhập. Xin hãy giữ trật tự! (100 xu)",
    "😎 Một huyền thoại mới: **{name}**! Chào mừng! (100 xu khởi nghiệp)"
]

GOODBYE_MESSAGES = [
    "💔 **{name}** đã rời đi. Tạm biệt và hẹn gặp lại!",
    "👋 Cảm ơn **{name}** đã dành thời gian ở đây! Chúc may mắn.",
    "😭 Một chiến binh **{name}** đã ngã xuống. Thế giới game cần bạn trở lại!",
    "🚪 **{name}** thoát server. Chắc là đi ngủ sớm rồi! Bye!",
    "🚨 **{name}** đã bị hệ thống phát hiện và rời đi.",
    "✨ Chuyến đi bình an, **{name}**!"
]

# ---------------------------
# DATABASE SETUP (thread-safe conn)
# ---------------------------
DB_NAME = 'economy.db'
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

# users, inventory, pets
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS user_inventory (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_name TEXT,
    rarity TEXT,
    skin_percent INTEGER,
    skill_main TEXT,
    skill_sub1 TEXT, skill_sub2 TEXT, skill_sub3 TEXT, skill_sub4 TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS user_pets (
    pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    pet_name TEXT,
    rarity TEXT,
    pet_skill TEXT,
    is_hidden BOOLEAN,
    level INTEGER DEFAULT 1,
    element TEXT,
    is_team_slot INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
''')
conn.commit()

# ---------------------------
# DB helper functions
# ---------------------------
def get_balance(user_id):
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result:
        return result[0]
    c.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
    conn.commit()
    return 0

def update_balance(user_id, amount):
    c.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)', (user_id,))
    c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    return get_balance(user_id)

# ---------------------------
# Random generators (weapons, pets, skills)
# ---------------------------
def random_roll_rarity():
    return random.choices(RARITY_NAMES, weights=RARITY_WEIGHTS, k=1)[0]

def random_roll_skills(num_skills):
    return random.sample(SKILLS, k=min(num_skills, len(SKILLS)))

def random_roll_weapon():
    rarity = random_roll_rarity()
    weapon_type = random.choice(WEAPON_TYPES)
    skin_percent = random.randint(0, 100)
    skills = random_roll_skills(5)
    return {
        "name": f"[{rarity}] {weapon_type}",
        "rarity": rarity,
        "skin_percent": skin_percent,
        "skill_main": skills[0],
        "skill_sub1": skills[1],
        "skill_sub2": skills[2],
        "skill_sub3": skills[3],
        "skill_sub4": skills[4],
    }

def add_item_to_inventory(user_id, item):
    c.execute(
        '''INSERT INTO user_inventory (user_id, item_name, rarity, skin_percent, skill_main, skill_sub1, skill_sub2, skill_sub3, skill_sub4) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, item['name'], item['rarity'], item['skin_percent'], item['skill_main'], item['skill_sub1'], item['skill_sub2'], item['skill_sub3'], item['skill_sub4'])
    )
    conn.commit()

# Pet helpers
def add_pet_to_db(user_id, pet_name, rarity, pet_skill, is_hidden):
    element = random.choice(PET_ELEMENTS)
    c.execute(
        '''INSERT INTO user_pets (user_id, pet_name, rarity, pet_skill, is_hidden, element) 
           VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, pet_name, rarity, pet_skill, is_hidden, element)
    )
    conn.commit()

def calculate_pet_power(pet_row):
    # pet_row tuple from SELECT: (pet_id, pet_name, rarity, pet_skill, is_hidden, level, element, is_team_slot)
    # But depending on SELECT order we will handle appropriately; here we'll rely on our SELECTs producing:
    # SELECT pet_id, pet_name, rarity, level, element, pet_skill, is_team_slot
    # So indices: 0 pet_id, 1 name, 2 rarity, 3 level, 4 element, 5 pet_skill, 6 is_team_slot
    level = pet_row[3]
    rarity = pet_row[2]
    rarity_multipliers = {"Hư Hại": 1, "Bình Thường": 1.2, "Hiếm Có": 1.5, "Sử Thi": 2,
                          "Bán Thần Thoại": 3, "Thần Thoại": 5, "Đấng Cứu Thế": 10}
    base_power = level * 10
    return base_power * rarity_multipliers.get(rarity, 1)

# ---------------------------
# Blackjack helper
# ---------------------------
SUITS = ['♠️', '♥️', '♦️', '♣️']
RANKS = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

def create_deck():
    return [{'rank': rank, 'suit': suit} for rank in RANKS for suit in SUITS]

def calculate_hand_value(hand):
    value = sum(RANKS[card['rank']] for card in hand)
    num_aces = sum(1 for card in hand if card['rank'] == 'A')
    while value > 21 and num_aces > 0:
        value -= 10
        num_aces -= 1
    return value

def card_to_string(card):
    return f"{card['rank']}{card['suit']}"

# ---------------------------
# on_message: convert 'b...' -> '!...' to allow bdaily/bzoo etc.
# ---------------------------
@bot.event
async def on_message(message):
    # ignore other bots
    if message.author.bot:
        return

    # If message starts with 'b' followed by letters (no space), convert to internal !command
    # Examples:
    # bdaily  -> !daily
    # bdaily args... -> !daily args...
    # btts hello -> !tts hello
    if message.content and message.content.startswith('b') and len(message.content) > 1:
        # protect if user typed mention like <@...> (starts with '<') -> we won't convert
        # but since message starts with 'b' safe to convert
        # convert "bxyz" to "!xyz"
        message.content = '!' + message.content[1:]

    await bot.process_commands(message)

# ---------------------------
# Commands (core)
# ---------------------------
@bot.command(name='balance', aliases=['bal', 'tien', 'bbal'])
async def balance_command(ctx, member: discord.Member = None):
    member = member or ctx.author
    bal = get_balance(member.id)
    await ctx.send(f"💰 Số dư hiện tại của **{member.display_name}** là: **{bal}** xu.")

@bot.command(name='daily', aliases=['bdaily'])
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily_command(ctx):
    user_id = ctx.author.id
    DAILY_REWARD = 500
    item = random_roll_weapon()
    add_item_to_inventory(user_id, item)
    update_balance(user_id, DAILY_REWARD)
    await ctx.send(f"🎁 **{ctx.author.display_name}** hoàn thành **Nhiệm Vụ Ngày**! Nhận **{DAILY_REWARD}** xu và 1 Hòm Gacha Vũ khí: **{item['name']}**!")
    await balance_command(ctx)

@daily_command.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        remaining_seconds = int(error.retry_after)
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60
        await ctx.send(f"⏰ **{ctx.author.display_name}** ơi, Nhiệm Vụ Ngày sẽ tái tạo sau **{hours} giờ, {minutes} phút, {seconds} giây** nữa.")

@bot.command(name='gacha', aliases=['mohòm'])
async def open_gacha_box(ctx):
    COST = 500
    user_id = ctx.author.id
    if get_balance(user_id) < COST:
        await ctx.send(f"❌ Bạn cần **{COST}** xu để mở hòm Gacha vũ khí.")
        return
    update_balance(user_id, -COST)
    item = random_roll_weapon()
    add_item_to_inventory(user_id, item)
    details = (
        f"Cấp độ: **{item['rarity']}**\n"
        f"Chỉ số: Skin **{item['skin_percent']}%**\n"
        f"Kỹ năng Chính: **{item['skill_main']}**\n"
        f"Kỹ năng Phụ: {item['skill_sub1']}, {item['skill_sub2']}, {item['skill_sub3']}, {item['skill_sub4']}"
    )
    await ctx.send(f"📦 **{ctx.author.display_name}** mở hòm và nhận được **{item['name']}**!\n{details}")
    await balance_command(ctx)

@bot.command(name='hunt', aliases=['bhunt'])
@commands.cooldown(1, 60, commands.BucketType.user)
async def hunt_command(ctx):
    user_id = ctx.author.id
    if random.random() < 0.30:
        today = datetime.now()
        rarity = random_roll_rarity()
        is_hidden = False
        if today.month == HIDDEN_PET_DATE[0] and today.day == HIDDEN_PET_DATE[1] and random.random() < 0.01:
            pet_name = HIDDEN_PET_NAME
            rarity = HIDDEN_PET_RARITY
            is_hidden = True
            message = f"🌟🌟 **Kỳ Tích!** Bạn đã tìm thấy {pet_name} - Pet **{rarity}** cực phẩm!"
        else:
            pet_name = random.choice(PET_NAMES)
            message = f"🎉 **Chúc mừng!** Bạn đã bắt được Pet: **{pet_name}** ({rarity})!"
        pet_skill = random.choice(SKILLS)
        add_pet_to_db(user_id, pet_name, rarity, pet_skill, is_hidden)
        await ctx.send(f"{message}\nKỹ năng Pet: **{pet_skill}**")
    else:
        update_balance(user_id, 50)
        await ctx.send("💔 Bạn đi săn nhưng không thấy Pet nào. Nhận **50** xu an ủi.")
    await balance_command(ctx)

# Pet storage (bzoo)
@bot.command(name='bzoo', aliases=['bz', 'bpet', 'pet'])
async def pet_zoo_command(ctx):
    user_id = ctx.author.id
    c.execute('SELECT pet_id, pet_name, rarity, level, element, is_team_slot FROM user_pets WHERE user_id = ? ORDER BY is_team_slot DESC, pet_id ASC', (user_id,))
    pets = c.fetchall()
    if not pets:
        return await ctx.send("😔 Kho Pet của bạn đang trống. Hãy dùng `bhunt` để đi săn!")
    embed = discord.Embed(title=f"🦴 Kho Pet của {ctx.author.display_name} ({len(pets)} Pet)", color=0xFEE3F5)
    description = []
    for pet in pets:
        pet_id, name, rarity, level, element, team_slot = pet
        status = f" | **[SLOT {team_slot}]** 🛡️" if team_slot > 0 else ""
        rarity_emoji = "🌟" if rarity in ["Thần Thoại", "Đấng Cứu Thế"] else "✨" if rarity in ["Sử Thi", "Bán Thần Thoại"] else ""
        description.append(f"`#{pet_id}`{status} **{name}** ({rarity_emoji}{rarity})\n   Lv: **{level}** | Thuộc tính: **{element}**")
    embed.description = "\n".join(description)
    embed.set_footer(text="Dùng bteam add <ID Pet> <Slot 1-3> để thêm Pet vào đội.")
    await ctx.send(embed=embed)

# bteam group
@bot.group(name='bteam', invoke_without_command=True)
async def pet_team_group(ctx):
    user_id = ctx.author.id
    c.execute('SELECT pet_id, pet_name, rarity, level, element, pet_skill, is_team_slot FROM user_pets WHERE user_id = ? AND is_team_slot > 0 ORDER BY is_team_slot ASC', (user_id,))
    team_pets_data = c.fetchall()
    embed = discord.Embed(title=f"🛡️ Đội Pet Chiến Đấu của {ctx.author.display_name}", description="Đội hình hiện tại:\n", color=0x40E0D0)
    if not team_pets_data:
        embed.description += "Chưa có Pet nào trong đội. Dùng `bteam add <ID> <Slot 1-3>`."
    team_slots = {i: None for i in range(1, 4)}
    for pet in team_pets_data:
        pet_id, name, rarity, level, element, skill, slot_num = pet
        team_slots[slot_num] = (pet_id, name, rarity, level, element, skill)
    for slot, pet_data in team_slots.items():
        if pet_data:
            pet_id, name, rarity, level, element, skill = pet_data
            embed.add_field(name=f"SLOT {slot} (ID: #{pet_id})", value=f"**{name}** ({rarity})\nLv: **{level}** | **{element}** | Skill: *{skill}*", inline=False)
        else:
            embed.add_field(name=f"SLOT {slot}", value=f"[Trống] - Dùng `bteam add <ID> {slot}`", inline=False)
    await ctx.send(embed=embed)

@pet_team_group.command(name='add')
async def pet_team_add(ctx, pet_id: int, slot: int):
    user_id = ctx.author.id
    if slot not in [1,2,3]:
        return await ctx.send("❌ Slot đội phải là số **1, 2, hoặc 3**.")
    c.execute('SELECT pet_name, is_team_slot FROM user_pets WHERE user_id = ? AND pet_id = ?', (user_id, pet_id))
    pet_data = c.fetchone()
    if not pet_data:
        return await ctx.send(f"❌ Không tìm thấy Pet có ID `#{pet_id}` trong kho của bạn.")
    pet_name, current_slot = pet_data
    # Bỏ pet cũ ở slot mục tiêu
    c.execute('UPDATE user_pets SET is_team_slot = 0 WHERE user_id = ? AND is_team_slot = ?', (user_id, slot))
    # Nếu pet đang ở slot khác, clear
    if current_slot != 0:
        c.execute('UPDATE user_pets SET is_team_slot = 0 WHERE user_id = ? AND pet_id = ?', (user_id, pet_id))
    # Đặt pet vào slot
    c.execute('UPDATE user_pets SET is_team_slot = ? WHERE user_id = ? AND pet_id = ?', (slot, user_id, pet_id))
    conn.commit()
    await ctx.send(f"✅ Pet **{pet_name}** (`#{pet_id}`) đã được thêm vào **SLOT {slot}** của đội hình chiến đấu!")

@pet_team_group.command(name='remove', aliases=['rm'])
async def pet_team_remove(ctx, slot: int):
    user_id = ctx.author.id
    if slot not in [1,2,3]:
        return await ctx.send("❌ Slot đội phải là số **1, 2, hoặc 3**.")
    c.execute('SELECT pet_name FROM user_pets WHERE user_id = ? AND is_team_slot = ?', (user_id, slot))
    pet_data = c.fetchone()
    if not pet_data:
        return await ctx.send(f"❌ Slot {slot} đã trống.")
    pet_name = pet_data[0]
    c.execute('UPDATE user_pets SET is_team_slot = 0 WHERE user_id = ? AND is_team_slot = ?', (user_id, slot))
    conn.commit()
    await ctx.send(f"✅ Đã loại Pet **{pet_name}** khỏi **SLOT {slot}**.")

# bbattle
@bot.command(name='bbattle', aliases=['bb'])
async def battle_command(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.send("❌ Bạn không thể chiến đấu với chính mình.")
    user_id = ctx.author.id
    opponent_id = member.id
    c.execute('SELECT pet_id, pet_name, rarity, level, element, pet_skill, is_team_slot FROM user_pets WHERE user_id = ? AND is_team_slot > 0 ORDER BY is_team_slot ASC', (user_id,))
    my_team = c.fetchall()
    c.execute('SELECT pet_id, pet_name, rarity, level, element, pet_skill, is_team_slot FROM user_pets WHERE user_id = ? AND is_team_slot > 0 ORDER BY is_team_slot ASC', (opponent_id,))
    opponent_team = c.fetchall()
    if len(my_team) != 3 or len(opponent_team) != 3:
        return await ctx.send("❌ Cả bạn và đối thủ phải có đủ **3 Pet** trong đội hình chiến đấu (`bteam add`).")
    my_power = sum(calculate_pet_power(p) for p in my_team)
    opponent_power = sum(calculate_pet_power(p) for p in opponent_team)
    WIN_AMOUNT = 300
    LOSE_AMOUNT = -100
    if my_power > opponent_power:
        update_balance(user_id, WIN_AMOUNT)
        battle_result = f"🎉 **Chiến Thắng!** Đội của bạn mạnh hơn đội {member.display_name}. Bạn nhận được **{WIN_AMOUNT}** xu!"
        color = 0x00FF00
    elif opponent_power > my_power:
        update_balance(user_id, LOSE_AMOUNT)
        battle_result = f"💔 **Thất Bại!** Đội của {member.display_name} mạnh hơn đội của bạn. Bạn bị trừ **100** xu."
        color = 0xFF0000
    else:
        battle_result = "🤝 **Hòa!** Sức mạnh cân bằng. Không ai thắng thua."
        color = 0xFFFF00
    embed = discord.Embed(title="⚔️ KẾT QUẢ ĐẠI CHIẾN PET ⚔️", description=battle_result, color=color)
    embed.add_field(name=f"{ctx.author.display_name}", value=f"Tổng Sức Mạnh: **{int(my_power)}**", inline=True)
    embed.add_field(name=f"{member.display_name}", value=f"Tổng Sức Mạnh: **{int(opponent_power)}**", inline=True)
    await ctx.send(embed=embed)

# Blackjack (bj / blackjack)
# ------------------------------
# Blackjack (bj / blackjack)
# ------------------------------
@bot.command(name="blackjack", aliases=["bj"])
async def blackjack(ctx, bet: int = 0):
    """Chơi bài blackjack kiếm xu"""
    if bet <= 0:
        await ctx.send("💸 Dùng: `bbj <số xu cược>`.")
        return

    bal = get_balance(ctx.author.id)
    if bal < bet:
        await ctx.send("❌ Bạn không đủ xu để cược.")
        return

    update_balance(ctx.author.id, -bet)

    cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    def card_value(c): return 10 if c in ["J", "Q", "K"] else (11 if c == "A" else int(c))

    player = [random.choice(cards), random.choice(cards)]
    dealer = [random.choice(cards), random.choice(cards)]

    def total(hand):
        t = sum(card_value(c) for c in hand)
        aces = hand.count("A")
        while t > 21 and aces:
            t -= 10
            aces -= 1
        return t

    await ctx.send(f"🃏 **Bài của bạn:** {', '.join(player)} (Tổng {total(player)})\n💀 **Bài Dealer:** {dealer[0]}, ?")

    while total(player) < 21:
        await ctx.send("➡️ Gõ `rút` để rút thêm, hoặc `dừng` để đứng.")
        try:
            msg = await bot.wait_for(
                "message",
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["rút", "rut", "dừng", "dung"],
                timeout=30
            )
        except asyncio.TimeoutError:
            await ctx.send("⌛ Hết thời gian! Tính là dừng.")
            break

        if msg.content.lower() in ["rút", "rut"]:
            player.append(random.choice(cards))
            await ctx.send(f"🃏 Bạn rút được {player[-1]} (Tổng {total(player)})")
        else:
            break

    player_total = total(player)
    if player_total > 21:
        await ctx.send(f"💥 Bạn quắc rồi ({player_total}) 😭 Mất {bet} xu.")
        return

    # Dealer rút
    while total(dealer) < 17:
        dealer.append(random.choice(cards))

    dealer_total = total(dealer)
    await ctx.send(f"💀 Dealer có {', '.join(dealer)} (Tổng {dealer_total})")

    if dealer_total > 21 or player_total > dealer_total:
        await ctx.send(f"🏆 Bạn thắng! Nhận {bet * 2} xu 🎉")
        update_balance(ctx.author.id, bet * 2)
    elif player_total == dealer_total:
        await ctx.send("😐 Hòa, hoàn tiền cược.")
        update_balance(ctx.author.id, bet)
    else:
        await ctx.send(f"💔 Dealer thắng! Bạn mất {bet} xu.")


# ------------------------------
# Hunt (bhunt)
# ------------------------------
@bot.command(name="hunt", aliases=["bhunt"])
async def hunt(ctx):
    """Đi săn thú rừng nhận xu"""
    animals = ["🐗", "🐻", "🐇", "🦌", "🐍", "🐊", "🐒"]
    animal = random.choice(animals)
    reward = random.randint(50, 200)
    await ctx.send(f"🏹 {ctx.author.display_name} đã săn được {animal} và nhận {reward} xu!")
    update_balance(ctx.author.id, reward)


# ------------------------------
# PVP (bpvp)
# ------------------------------
@bot.command(name="pvp", aliases=["bpvp"])
async def pvp(ctx, member: discord.Member = None, bet: int = 0):
    """Đấu người chơi khác"""
    if not member:
        await ctx.send("⚔️ Dùng: `bpvp @người_chơi <xu_cược>`.")
        return
    if member == ctx.author:
        await ctx.send("😅 Không thể tự đấu chính mình.")
        return
    if bet <= 0:
        await ctx.send("💸 Cược phải > 0 xu.")
        return

    bal1 = get_balance(ctx.author.id)
    bal2 = get_balance(member.id)
    if bal1 < bet or bal2 < bet:
        await ctx.send("❌ Một trong hai người không đủ xu.")
        return

    await ctx.send(f"⚔️ {ctx.author.mention} thách đấu {member.mention} với **{bet} xu**! Gõ `chấp nhận` để đồng ý.")

    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author == member and m.channel == ctx.channel and m.content.lower() == "chấp nhận",
            timeout=30
        )
    except asyncio.TimeoutError:
        await ctx.send("⌛ Hết thời gian, trận đấu bị hủy.")
        return

    await ctx.send("🎲 Đang tung xúc xắc quyết định thắng thua...")
    await asyncio.sleep(2)

    winner = random.choice([ctx.author, member])
    loser = member if winner == ctx.author else ctx.author

    update_balance(winner.id, bet)
    update_balance(loser.id, -bet)

    await ctx.send(f"🏆 {winner.mention} thắng và nhận **{bet} xu!** 💰")


# ------------------------------
# Team (bteam)
# ------------------------------
teams = {}

@bot.command(name="team", aliases=["bteam"])
async def team(ctx, action=None, *, name=None):
    """Tạo hoặc xem team"""
    uid = ctx.author.id
    if action == "tạo" and name:
        if uid in teams:
            await ctx.send("❌ Bạn đã có team rồi.")
            return
        teams[uid] = {"name": name, "members": [ctx.author.id]}
        await ctx.send(f"👥 Team **{name}** được tạo thành công!")
    elif action == "mời" and name:
        target = ctx.message.mentions[0] if ctx.message.mentions else None
        if not target:
            await ctx.send("⚠️ Dùng: `bteam mời @tên`.")
            return
        for t in teams.values():
            if ctx.author.id in t["members"]:
                t["members"].append(target.id)
                await ctx.send(f"✅ {target.display_name} đã được mời vào team **{t['name']}**!")
                return
        await ctx.send("❌ Bạn chưa có team để mời người khác.")
    elif action == "xem":
        for t in teams.values():
            if uid in t["members"]:
                member_names = []
                for m in t["members"]:
                    member_obj = ctx.guild.get_member(m)
                    if member_obj:
                        member_names.append(member_obj.display_name)
                await ctx.send(f"👥 Team **{t['name']}** gồm: {', '.join(member_names)}")
                return
        await ctx.send("😅 Bạn chưa ở trong team nào.")
    else:
        await ctx.send("📘 Dùng: `bteam tạo <tên>` | `bteam mời @ai` | `bteam xem`.")


# ------------------------------
# Kết thúc
# ------------------------------
print("[✅ TẢI TOÀN BỘ MODULE THÀNH CÔNG]")
def get_game_status_embed(show_dealer_card=False, is_game_over=False):
        player_cards_str = ", ".join(card_to_string(c) for c in player_hand)
        player_score = calculate_hand_value(player_hand)
        if show_dealer_card or is_game_over:
            dealer_cards_str = ", ".join(card_to_string(c) for c in dealer_hand)
            dealer_score = calculate_hand_value(dealer_hand)
            dealer_display = f"**{dealer_score}** ({dealer_cards_str})"
    
