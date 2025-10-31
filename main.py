# ------------------ PART 1/6: INIT & DB ------------------
import discord
from discord.ext import commands
import os, random, sqlite3, asyncio, tempfile, time
from datetime import datetime
from gtts import gTTS

# CONFIG
TOKEN = os.getenv("DISCORD_TOKEN")
WELCOME_CHANNEL_ID = 123456789012345678  # <-- đổi ID kênh ở đây
intents = discord.Intents.all()
# nội bộ vẫn dùng prefix '!' nhưng người dùng gõ 'b...' (on_message chuyển)
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# DATABASE (thread-safe)
DB_PATH = "yubabe_clone.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# tạo bảng nếu chưa có
c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)''')

c.execute('''CREATE TABLE IF NOT EXISTS user_inventory (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_name TEXT,
    rarity TEXT,
    skin_percent INTEGER,
    skill_main TEXT,
    skill_sub1 TEXT,
    skill_sub2 TEXT,
    skill_sub3 TEXT,
    skill_sub4 TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS user_pets (
    pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    pet_name TEXT,
    rarity TEXT,
    pet_skill TEXT,
    is_hidden BOOLEAN,
    level INTEGER DEFAULT 1,
    element TEXT,
    is_team_slot INTEGER DEFAULT 0
)''')
conn.commit()

# Helpers: balance
def get_balance(user_id):
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    r = c.fetchone()
    if r:
        return r[0]
    c.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
    conn.commit()
    return 0

def update_balance(user_id, amount):
    c.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
    c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    return get_balance(user_id)

# Random data
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
    "Lân Sư Rồng", "Chim Lạc", "Cóc Thần", "Thiên Cẩu", "Rồng Vàng",
    "Hùng Vương", "Thánh Gióng", "Âu Cơ", "Lạc Long Quân", "Phù Đổng",
    *[f"Pet Chiến Đấu {i}" for i in range(1, 31)]
]

PET_ELEMENTS = ["Lửa", "Nước", "Gió", "Đất", "Ánh Sáng", "Bóng Tối"]
HIDDEN_PET_NAME = "Hồ Chí Minh Bất Tử"
HIDDEN_PET_RARITY = "Đấng Cứu Thế"
HIDDEN_PET_DATE = (5, 19)

WELCOME_MESSAGES = [
    "🎉 Chào mừng **{name}** đến với bến đỗ mới! Đã tặng **100** xu khởi nghiệp.",
    "🥳 Woa! **{name}** đã xuất hiện! (100 xu đã vào ví)",
    "👋 Mừng **{name}** ghé thăm! Mau vào tìm đồng đội nào. (100 xu)",
]
GOODBYE_MESSAGES = [
    "💔 **{name}** đã rời đi. Tạm biệt!",
    "👋 Cảm ơn **{name}** đã ở lại!",
]
# ------------------ PART 2/6: ITEM, PET HELPERS, DAILY, GACHA, BALANCE ------------------

# random helpers
def random_roll_rarity():
    return random.choices(RARITY_NAMES, weights=RARITY_WEIGHTS, k=1)[0]

def random_roll_skills(k):
    return random.sample(SKILLS, k=min(k, len(SKILLS)))

def random_roll_weapon():
    rarity = random_roll_rarity()
    w = random.choice(WEAPON_TYPES)
    skin = random.randint(0, 100)
    skills = random_roll_skills(5)
    return {
        "name": f"[{rarity}] {w}",
        "rarity": rarity,
        "skin_percent": skin,
        "skill_main": skills[0],
        "skill_sub1": skills[1],
        "skill_sub2": skills[2],
        "skill_sub3": skills[3],
        "skill_sub4": skills[4],
    }

def add_item_to_inventory(user_id, item):
    c.execute('''INSERT INTO user_inventory (user_id, item_name, rarity, skin_percent, skill_main, skill_sub1, skill_sub2, skill_sub3, skill_sub4)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id, item['name'], item['rarity'], item['skin_percent'],
               item['skill_main'], item['skill_sub1'], item['skill_sub2'], item['skill_sub3'], item['skill_sub4']))
    conn.commit()

# Pet DB helpers
def add_pet_to_db(user_id, pet_name, rarity, pet_skill, is_hidden=False):
    element = random.choice(PET_ELEMENTS)
    c.execute('''INSERT INTO user_pets (user_id, pet_name, rarity, pet_skill, is_hidden, element)
                 VALUES (?, ?, ?, ?, ?, ?)''', (user_id, pet_name, rarity, pet_skill, is_hidden, element))
    conn.commit()

def calculate_pet_power(pet_row):
    # Expected SELECT: pet_id, pet_name, rarity, level, element, pet_skill, is_team_slot
    # indices: 0 id,1 name,2 rarity,3 level,4 element,5 skill,6 slot
    try:
        level = pet_row[3]
        rarity = pet_row[2]
    except:
        return 0
    multipliers = {"Hư Hại":1, "Bình Thường":1.2, "Hiếm Có":1.5, "Sử Thi":2, "Bán Thần Thoại":3, "Thần Thoại":5, "Đấng Cứu Thế":10}
    base = level * 10
    return base * multipliers.get(rarity, 1)

# COMMANDS: balance/daily/gacha
@bot.command(name='balance', aliases=['bal','bbal','tien'])
async def balance_command(ctx, member: discord.Member=None):
    member = member or ctx.author
    bal = get_balance(member.id)
    await ctx.send(f"💰 Số dư của **{member.display_name}**: **{bal}** xu.")

@bot.command(name='daily', aliases=['bdaily'])
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily_command(ctx):
    uid = ctx.author.id
    reward = 500
    item = random_roll_weapon()
    add_item_to_inventory(uid, item)
    update_balance(uid, reward)
    await ctx.send(f"🎁 **{ctx.author.display_name}** nhận **{reward}** xu và 1 hòm: **{item['name']}**.")
    await balance_command(ctx)

@daily_command.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        secs = int(error.retry_after)
        h = secs // 3600; m = (secs%3600)//60; s = secs%60
        await ctx.send(f"⏰ Nhiệm vụ hàng ngày tái tạo sau **{h}g {m}p {s}s**.")

@bot.command(name='gacha', aliases=['mohom','mohòm'])
async def gacha_command(ctx):
    COST = 500
    uid = ctx.author.id
    if get_balance(uid) < COST:
        await ctx.send(f"❌ Cần **{COST}** xu để mở hòm.")
        return
    update_balance(uid, -COST)
    item = random_roll_weapon()
    add_item_to_inventory(uid, item)
    await ctx.send(f"📦 **{ctx.author.display_name}** mở hòm và nhận **{item['name']}** (R: {item['rarity']}, Skin {item['skin_percent']}%).")
    await balance_command(ctx)
    # ------------------ PART 3/6: HUNT, BZOO, BTEAM ------------------

@bot.command(name='hunt', aliases=['bhunt'])
@commands.cooldown(1, 60, commands.BucketType.user)
async def hunt_command(ctx):
    uid = ctx.author.id
    if random.random() < 0.30:
        today = datetime.now()
        rarity = random_roll_rarity()
        is_hidden = False
        if (today.month, today.day) == HIDDEN_PET_DATE and random.random() < 0.01:
            pet_name = HIDDEN_PET_NAME; rarity = HIDDEN_PET_RARITY; is_hidden = True
            msg = f"🌟 **Kỳ tích!** Bạn tìm thấy **{pet_name}** ({rarity})!"
        else:
            pet_name = random.choice(PET_NAMES)
            msg = f"🎉 Bạn bắt được Pet **{pet_name}** ({rarity})!"
        pet_skill = random.choice(SKILLS)
        add_pet_to_db(uid, pet_name, rarity, pet_skill, is_hidden)
        await ctx.send(f"{msg}\nKỹ năng pet: **{pet_skill}**")
    else:
        update_balance(uid, 50)
        await ctx.send("💔 Không thấy pet. Nhận 50 xu an ủi.")
    await balance_command(ctx)

@bot.command(name='bzoo', aliases=['bz','bpet'])
async def pet_zoo_command(ctx):
    uid = ctx.author.id
    c.execute('SELECT pet_id, pet_name, rarity, level, element, is_team_slot FROM user_pets WHERE user_id = ? ORDER BY is_team_slot DESC, pet_id ASC', (uid,))
    pets = c.fetchall()
    if not pets:
        await ctx.send("😔 Kho pet trống. Dùng `bhunt` để đi săn.")
        return
    embed = discord.Embed(title=f"🦴 Kho Pet của {ctx.author.display_name} ({len(pets)} pet)", color=0xFEE3F5)
    lines = []
    for pet in pets:
        pet_id, name, rarity, level, element, team_slot = pet
        slot_text = f" | [SLOT {team_slot}]" if team_slot and team_slot>0 else ""
        emoji = "🌟" if rarity in ["Thần Thoại","Đấng Cứu Thế"] else "✨" if rarity in ["Sử Thi","Bán Thần Thoại"] else ""
        lines.append(f"`#{pet_id}`{slot_text} **{name}** ({emoji}{rarity}) — Lv: **{level}** | {element}")
    embed.description = "\n".join(lines)
    embed.set_footer(text="Dùng bteam add <ID> <Slot 1-3> để đưa pet vào đội.")
    await ctx.send(embed=embed)

# bteam group: xem/add/remove
@bot.group(name='bteam', invoke_without_command=True)
async def bteam_group(ctx):
    uid = ctx.author.id
    c.execute('SELECT pet_id, pet_name, rarity, level, element, pet_skill, is_team_slot FROM user_pets WHERE user_id = ? AND is_team_slot > 0 ORDER BY is_team_slot ASC', (uid,))
    team = c.fetchall()
    embed = discord.Embed(title=f"🛡️ Đội Pet của {ctx.author.display_name}", color=0x40E0D0)
    if not team:
        embed.description = "Chưa có pet trong đội. Dùng `bteam add <ID> <1-3>`."
    else:
        for pet in team:
            pid, name, rarity, level, element, skill, slot = pet
            embed.add_field(name=f"SLOT {slot} — #{pid}", value=f"**{name}** ({rarity}) Lv{level} | {element} | {skill}", inline=False)
    await ctx.send(embed=embed)

@bteam_group.command(name='add')
async def bteam_add(ctx, pet_id: int, slot: int):
    uid = ctx.author.id
    if slot not in [1,2,3]:
        await ctx.send("❌ Slot phải là 1,2 hoặc 3.")
        return
    c.execute('SELECT pet_name, is_team_slot FROM user_pets WHERE user_id = ? AND pet_id = ?', (uid, pet_id))
    row = c.fetchone()
    if not row:
        await ctx.send("❌ Không tìm thấy pet ID này.")
        return
    pet_name, current = row
    # clear target slot
    c.execute('UPDATE user_pets SET is_team_slot = 0 WHERE user_id = ? AND is_team_slot = ?', (uid, slot))
    # clear current slot of this pet if any
    if current and current>0:
        c.execute('UPDATE user_pets SET is_team_slot = 0 WHERE user_id = ? AND pet_id = ?', (uid, pet_id))
    # set new slot
    c.execute('UPDATE user_pets SET is_team_slot = ? WHERE user_id = ? AND pet_id = ?', (slot, uid, pet_id))
    conn.commit()
    await ctx.send(f"✅ Đã thêm **{pet_name}** vào SLOT {slot}.")

@bteam_group.command(name='remove', aliases=['rm'])
async def bteam_remove(ctx, slot: int):
    uid = ctx.author.id
    if slot not in [1,2,3]:
        await ctx.send("❌ Slot phải là 1,2 hoặc 3.")
        return
    c.execute('SELECT pet_name FROM user_pets WHERE user_id = ? AND is_team_slot = ?', (uid, slot))
    r = c.fetchone()
    if not r:
        await ctx.send("❌ Slot trống.")
        return
    pet_name = r[0]
    c.execute('UPDATE user_pets SET is_team_slot = 0 WHERE user_id = ? AND is_team_slot = ?', (uid, slot))
    conn.commit()
    await ctx.send(f"✅ Đã loại **{pet_name}** khỏi SLOT {slot}.")
    # ------------------ PART 4/6: BBATTLE (3v3) + INVENTORY/SHOP ------------------

@bot.command(name='bbattle', aliases=['bb'])
async def bbattle(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        await ctx.send("❌ Không thể chiến đấu chính mình.")
        return
    uid = ctx.author.id; oid = member.id
    c.execute('SELECT pet_id, pet_name, rarity, level, element, pet_skill, is_team_slot FROM user_pets WHERE user_id = ? AND is_team_slot > 0 ORDER BY is_team_slot ASC', (uid,))
    my_team = c.fetchall()
    c.execute('SELECT pet_id, pet_name, rarity, level, element, pet_skill, is_team_slot FROM user_pets WHERE user_id = ? AND is_team_slot > 0 ORDER BY is_team_slot ASC', (oid,))
    op_team = c.fetchall()
    if len(my_team) != 3 or len(op_team) != 3:
        await ctx.send("❌ Cả hai phải có đủ 3 pet trong đội (bteam add).")
        return
    my_power = sum(calculate_pet_power(p) for p in my_team)
    op_power = sum(calculate_pet_power(p) for p in op_team)
    WIN = 300; LOSE = -100
    if my_power > op_power:
        update_balance(uid, WIN); res = f"🎉 Bạn thắng! +{WIN} xu."
        color = 0x00FF00
    elif op_power > my_power:
        update_balance(uid, LOSE); res = f"💔 Thua! {LOSE} xu."
        color = 0xFF0000
    else:
        res = "🤝 Hòa! Không ai đổi xu."; color = 0xFFFF00
    em = discord.Embed(title="⚔️ Kết quả chiến đấu Pet", description=res, color=color)
    em.add_field(name=ctx.author.display_name, value=f"Sức mạnh: {int(my_power)}", inline=True)
    em.add_field(name=member.display_name, value=f"Sức mạnh: {int(op_power)}", inline=True)
    await ctx.send(embed=em)

# Inventory: xem item
@bot.command(name='inv', aliases=['inventory','bag'])
async def inventory(ctx):
    uid = ctx.author.id
    c.execute('SELECT item_id, item_name, rarity, skin_percent FROM user_inventory WHERE user_id = ? ORDER BY item_id DESC', (uid,))
    items = c.fetchall()
    if not items:
        await ctx.send("🎒 Kho đồ trống.")
        return
    lines = []
    for it in items:
        iid, name, rarity, skin = it
        lines.append(f"`#{iid}` **{name}** ({rarity}) - Skin {skin}%")
    txt = "\n".join(lines[:20])
    await ctx.send(f"🎒 Kho đồ của {ctx.author.display_name}:\n{txt}")

# Simple shop: đổi xu lấy hộp gacha (dùng bshop mua gacha)
@bot.command(name='bshop', aliases=['shop'])
async def shop(ctx, item: str = None):
    if not item:
        return await ctx.send("🛒 Shop: `bshop gacha` (500 xu) hoặc `bshop info`")
    if item.lower() == 'gacha':
        COST = 500
        uid = ctx.author.id
        if get_balance(uid) < COST:
            return await ctx.send("❌ Không đủ xu để mua.")
        update_balance(uid, -COST)
        item = random_roll_weapon()
        add_item_to_inventory(uid, item)
        return await ctx.send(f"📦 Mua gacha thành công: **{item['name']}** ({item['rarity']})")
    if item.lower() == 'info':
        return await ctx.send("🛒 Gacha: 500 xu -> Có thể nhận vũ khí ngẫu nhiên.")
        # ------------------ PART 5/6: BLACKJACK + on_message + events ------------------

# Blackjack (simple text-controlled version)
@bot.command(name='blackjack', aliases=['bj','bbj'])
async def blackjack_cmd(ctx, bet: int = 0):
    uid = ctx.author.id
    if bet <= 0:
        return await ctx.send("💸 Dùng: bbj <số xu cược>")
    if get_balance(uid) < bet:
        return await ctx.send("❌ Không đủ xu.")
    update_balance(uid, -bet)
    # deck simplified: use ranks
    ranks = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    def val(r):
        if r in ['J','Q','K']: return 10
        if r == 'A': return 11
        return int(r)
    def total(hand):
        s = sum(val(x) for x in hand)
        aces = hand.count('A')
        while s > 21 and aces:
            s -= 10; aces -= 1
        return s
    player = [random.choice(ranks), random.choice(ranks)]
    dealer = [random.choice(ranks), random.choice(ranks)]
    await ctx.send(f"🃏 Bài bạn: {', '.join(player)} (Tổng {total(player)})\n💀 Dealer: {dealer[0]}, ?")
    while total(player) < 21:
        await ctx.send("➡️ Gõ `rút` để rút thêm hoặc `dừng` để kết thúc.")
        try:
            msg = await bot.wait_for('message', check=lambda m: m.author==ctx.author and m.channel==ctx.channel and m.content.lower() in ['rút','rut','dừng','dung'], timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("⌛ Hết thời gian, tự động dừng.")
            break
        if msg.content.lower() in ['rút','rut']:
            player.append(random.choice(ranks))
            await ctx.send(f"🃏 Bạn rút {player[-1]} (Tổng {total(player)})")
        else:
            break
    pt = total(player)
    if pt > 21:
        return await ctx.send(f"💥 Quắc rồi! Mất {bet} xu.")
    while total(dealer) < 17:
        dealer.append(random.choice(ranks))
    dt = total(dealer)
    await ctx.send(f"💀 Dealer: {', '.join(dealer)} (Tổng {dt})")
    if dt>21 or pt>dt:
        update_balance(uid, bet*2)
        await ctx.send(f"🏆 Bạn thắng! Nhận {bet*2} xu.")
    elif pt==dt:
        update_balance(uid, bet)
        await ctx.send("😐 Hòa, hoàn lại cược.")
    else:
        await ctx.send(f"💔 Dealer thắng, bạn mất {bet} xu.")

# on_message converter b... -> !...
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # nếu message dạng "bcmd" hoặc "bcmd args..." thì chuyển nội bộ thành !cmd
    if message.content and message.content.startswith('b') and len(message.content) > 1:
        # tránh khi người dùng gõ bắt đầu b và theo sau là space (vd: "b hello") => không đổi
        if not message.content.startswith('b '):
            message.content = '!' + message.content[1:]
    await bot.process_commands(message)

# welcome & goodbye
@bot.event
async def on_member_join(member):
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if ch:
        try:
            update_balance(member.id, 100)
        except:
            pass
        await ch.send(random.choice(WELCOME_MESSAGES).format(name=member.mention))

@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if ch:
        await ch.send(random.choice(GOODBYE_MESSAGES).format(name=member.display_name))
        # ------------------ PART 6/6: TTS, ADMIN, PING, RUN ------------------
import io, aiohttp

# TTS command (btts)
@bot.command(name='tts', aliases=['btts','b'])
async def tts_cmd(ctx, *, text: str = None):
    if not text:
        return await ctx.send("🗣️ Dùng: btts <nội dung>")
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("🔊 Bạn phải ở trong kênh voice để dùng lệnh.")
    voice_channel = ctx.author.voice.channel
    # đảm bảo bot vào đúng kênh
    if ctx.voice_client is None:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)
    # tạo tts file tạm
    try:
        tts = gTTS(text=text, lang='vi', slow=False)
        tmp = tempfile.gettempdir()
        fp = os.path.join(tmp, f"tts_{ctx.message.id}_{int(time.time())}.mp3")
        tts.save(fp)
    except Exception as e:
        return await ctx.send(f"❌ Lỗi tạo TTS: {e}")
    try:
        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()
        source = discord.FFmpegPCMAudio(fp)
        vc.play(source)
        await ctx.send(f"🔊 Đang đọc: `{text}`")
        while vc.is_playing():
            await asyncio.sleep(0.5)
        await vc.disconnect()
    except Exception as e:
        await ctx.send(f"❌ Lỗi phát: {e}")
    finally:
        if os.path.exists(fp):
            try: os.remove(fp)
            except: pass

# stop/leave
@bot.command(name='stoptts', aliases=['bstop','bleave'])
async def stop_tts(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Đã rời kênh voice.")
    else:
        await ctx.send("🚫 Bot không ở kênh voice.")

# admin give
@bot.command(name='admingive')
@commands.has_permissions(administrator=True)
async def admin_give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("Số tiền phải > 0.")
    update_balance(member.id, amount)
    await ctx.send(f"✅ Đã cộng {amount} xu cho {member.display_name}.")

# ping
@bot.command(name='ping', aliases=['lat'])
async def ping_cmd(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms")

# finalize and run
print("[✅ TẢI TOÀN BỘ MODULE THÀNH CÔNG]")
# ------------------------------
# PHẦN 6: PVP / PROFILE / GIFT / RANK / EVENT / WELCOME
# ------------------------------

@bot.command(name="bpvp")
async def pvp(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("🤨 Bạn không thể đánh chính mình được.")
        return
    user = get_user(ctx.author.id)
    target = get_user(member.id)
    if user["coin"] < 50 or target["coin"] < 50:
        await ctx.send("💸 Cả hai người cần ít nhất 50 xu để tham gia trận đấu.")
        return
    winner = random.choice([ctx.author, member])
    loser = member if winner == ctx.author else ctx.author
    user_w = get_user(winner.id)
    user_l = get_user(loser.id)
    reward = random.randint(50, 150)
    user_w["coin"] += reward
    user_l["coin"] -= 50
    save_data(users)
    await ctx.send(f"⚔️ **{winner.name}** đã thắng và nhận được **{reward} 💰**!")

@bot.command(name="bprofile")
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = get_user(member.id)
    pets = ", ".join(data.get("pets", [])) or "Không có"
    inv = len(data.get("inventory", []))
    embed = discord.Embed(title=f"👤 Hồ sơ của {member.name}", color=0xaaaaee)
    embed.add_field(name="💰 Tiền:", value=f"{data['coin']} xu", inline=False)
    embed.add_field(name="🐾 Pet:", value=pets, inline=False)
    embed.add_field(name="🎒 Túi đồ:", value=f"{inv} món", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="bgift")
async def gift(ctx, member: discord.Member, amount: int):
    sender = get_user(ctx.author.id)
    receiver = get_user(member.id)
    if sender["coin"] < amount:
        await ctx.send("💸 Bạn không đủ tiền để tặng.")
        return
    sender["coin"] -= amount
    receiver["coin"] += amount
    save_data(users)
    await ctx.send(f"🎁 {ctx.author.name} đã tặng {member.name} **{amount} 💰**!")

@bot.command(name="brank")
async def rank(ctx):
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("coin", 0), reverse=True)
    top = ""
    for i, (uid, data) in enumerate(sorted_users[:10], start=1):
        member = await bot.fetch_user(int(uid))
        top += f"{i}. {member.name} - {data['coin']} 💰\n"
    embed = discord.Embed(title="🏆 Bảng xếp hạng top 10", description=top, color=0xffd700)
    await ctx.send(embed=embed)

# ------------------------------
# AUTO EVENT - RANDOM COIN KHI CHAT
# ------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    user = get_user(message.author.id)
    gain = random.randint(1, 5)
    user["coin"] += gain
    save_data(users)
    await bot.process_commands(message)

# ------------------------------
# AUTO WELCOME
# ------------------------------
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="chào-mừng")
    if channel:
        await channel.send(f"👋 Chào mừng {member.mention} đến với server! 💖")
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Vui lòng đặt DISCORD_TOKEN env var.")
    else:
        bot.run(TOKEN)
        
