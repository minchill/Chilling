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

# --- CẤU HÌNH DỮ LIỆU LỚN VÀ LOGIC GAME ---

# 1. Cấp bậc (Rarity) và Tỷ lệ random (Phần trăm)
RARITY_CONFIG = {
    "Hư Hại": 35, "Bình Thường": 30, "Hiếm Có": 20, "Sử Thi": 10, 
    "Bán Thần Thoại": 4, "Thần Thoại": 0.9, "Đấng Cứu Thế": 0.1,
}
RARITY_NAMES = list(RARITY_CONFIG.keys())
RARITY_WEIGHTS = list(RARITY_CONFIG.values())

# 2. DỮ LIỆU VŨ KHÍ (30 Loại)
WEAPON_TYPES = [
    "Kiếm Lưỡi Hái", "Kiếm Nhật Katana", "Kiếm Thiên Thần", "Song Kiếm", "Kiếm Lửa Địa Ngục", 
    "Trượng Bão Tuyết", "Trượng Sấm Sét", "Trượng Hồi Sinh", "Trượng Cổ Đại", "Trượng Lửa",
    "Súng Laser", "Súng Pháo Đài", "Súng Bắn Tỉa", "Súng Máy Mini", "Súng Lục",
    "Giáp Rồng", "Giáp Thép Titan", "Giáp Pha Lê", "Giáp Hộ Mệnh", "Giáp Bóng Đêm",
    "Cung Thần Gió", "Cung Băng Giá", "Cung Tinh Linh", "Nỏ Lớn", "Cung Ngắn",
    "Khiên Kim Cương", "Khiên Titan", "Khiên Phù Thủy", "Khiên Rồng", "Khiên Gỗ Cứng",
]

# 3. DỮ LIỆU KỸ NĂNG (50 Skill)
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

# 4. DỮ LIỆU PET (50 Loại)
PET_NAMES = [
    "Lân Sư Rồng (Tết)", "Chim Lạc (Giỗ Tổ)", "Cóc Thần (Mưa)", "Thiên Cẩu (Trung Thu)", "Rồng Vàng (Mùng 1)",
    "Hùng Vương Thần Lực", "Thánh Gióng", "Âu Cơ", "Lạc Long Quân", "Phù Đổng Thiên Vương",
    "Hổ Đông Dương", "Voi Rừng Tây Nguyên", "Sơn Tinh", "Thủy Tinh", "Sếu Đầu Đỏ",
    "Tinh Linh Ánh Sáng", "Bóng Ma Cổ", "Thần Tài Mini", "Tiên Nữ Hoa", "Quỷ Lửa",
    *[f"Pet Chiến Đấu {i}" for i in range(1, 31)]
]

# 5. Pet Ẩn Cực Kì Quan Trọng (Ngày Bác Hồ Sinh - 19/5)
HIDDEN_PET_NAME = "Hồ Chí Minh Bất Tử"
HIDDEN_PET_RARITY = "Đấng Cứu Thế"
HIDDEN_PET_DATE = (5, 19) # (Tháng, Ngày)

# 6. CẤU HÌNH CHÀO/TẠM BIỆT NGẪU NHIÊN (6 PHONG CÁCH)
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

# --- CẤU HÌNH BOT VÀ DATABASE ---

TOKEN = os.getenv('DISCORD_TOKEN') 
WELCOME_CHANNEL_ID = 123456789012345678 # <<< THAY ID KÊNH CỦA BẠN >>>

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

# --- DATABASE SETUP ---

DB_NAME = 'economy.db'
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

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
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
''')
conn.commit()

# --- HÀM HỖ TRỢ DATABASE VÀ ITEM ---

def get_balance(user_id):
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result: return result[0]
    c.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
    conn.commit()
    return 0

def update_balance(user_id, amount):
    balance = get_balance(user_id)
    new_balance = balance + amount
    c.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
    conn.commit()
    return new_balance

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

# Hàm chuyển tiền giữa người dùng (BGIVE - Vẫn dùng hàm thường để xử lý trong on_message)
async def bgive_money(ctx, member: discord.Member, amount: int):
    user_id = ctx.author.id; sender_balance = get_balance(user_id)
    if member.id == user_id or amount <= 0 or sender_balance < amount:
        if member.id == user_id: await ctx.send("❌ Bạn không thể tự chuyển tiền cho chính mình.")
        elif amount <= 0: await ctx.send("❌ Số tiền chuyển phải lớn hơn 0.")
        else: await ctx.send(f"❌ Bạn không đủ **{amount}** xu. Số dư hiện tại của bạn là: **{sender_balance}** xu.")
        return
    update_balance(user_id, -amount); update_balance(member.id, amount)
    await ctx.send(f"✅ **{ctx.author.display_name}** đã chuyển **{amount}** xu cho **{member.display_name}** thành công!")
    await balance_command(ctx) 


# --- LOGIC BLACKJACK (Đã thêm) ---

# Định nghĩa Bộ Bài và Giá Trị
SUITS = ['♠️', '♥️', '♦️', '♣️']
RANKS = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11 # Ace ban đầu là 11
}

def create_deck():
    """Tạo bộ bài 52 lá."""
    return [{'rank': rank, 'suit': suit} for rank in RANKS for suit in SUITS]

def calculate_hand_value(hand):
    """Tính giá trị bài, xử lý Ace (11 hoặc 1)."""
    value = sum(RANKS[card['rank']] for card in hand)
    num_aces = sum(1 for card in hand if card['rank'] == 'A')
    
    # Xử lý Ace: Giảm giá trị của Ace từ 11 xuống 1 nếu tổng điểm vượt quá 21
    while value > 21 and num_aces > 0:
        value -= 10
        num_aces -= 1
    return value

def card_to_string(card):
    """Chuyển lá bài thành chuỗi hiển thị (ví dụ: A♠️)"""
    return f"{card['rank']}{card['suit']}"


# --- LỆNH BLACKJACK ---

@bot.command(name="blackjack", aliases=["bj", "bbj"])
async def blackjack_command(ctx, bet: int):
    """Bắt đầu trò chơi Blackjack. Dùng !bj <số tiền cược>"""
    user_id = ctx.author.id
    
    # Kiểm tra tiền cược
    if bet <= 0:
        return await ctx.send("❌ Số tiền cược phải lớn hơn 0.")
    if get_balance(user_id) < bet:
        return await ctx.send(f"❌ Bạn không đủ **{bet}** xu. Số dư hiện tại là: **{get_balance(user_id)}** xu.")
    
    # Khởi tạo trò chơi
    deck = create_deck()
    random.shuffle(deck)
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    # Trừ tiền cược
    update_balance(user_id, -bet)
    
    def get_game_status_embed(show_dealer_card=False, is_game_over=False):
        """Tạo Embed hiển thị trạng thái game"""
        player_cards_str = ", ".join(card_to_string(c) for c in player_hand)
        player_score = calculate_hand_value(player_hand)
        
        if show_dealer_card or is_game_over:
            dealer_cards_str = ", ".join(card_to_string(c) for c in dealer_hand)
            dealer_score = calculate_hand_value(dealer_hand)
            dealer_display = f"**{dealer_score}** ({dealer_cards_str})"
        else:
            dealer_cards_str = f"{card_to_string(dealer_hand[0])}, [Lá Ẩn]"
            dealer_display = f"**{calculate_hand_value([dealer_hand[0]])}** ({dealer_cards_str})"

        embed = discord.Embed(
            title="♠️ BLACKJACK - Thử vận may! ♣️",
            description=f"**Cược:** {bet} xu",
            color=0x2ECC71
        )
        embed.add_field(name=f"{ctx.author.display_name} (Bạn)", value=f"Điểm: **{player_score}**\nBài: {player_cards_str}", inline=True)
        embed.add_field(name="Bot (Dealer)", value=f"Điểm: {dealer_display}", inline=True)
        return embed, player_score, dealer_score

    # Xử lý Blackjack ngay lập tức
    initial_embed, player_score, dealer_score_initial = get_game_status_embed(is_game_over=False)
    
    if player_score == 21:
        # Nếu người chơi Blackjack, Dealer kiểm tra bài ẩn
        if calculate_hand_value(dealer_hand) == 21:
            # PUSH - Hòa
            update_balance(user_id, bet) 
            final_embed, _, _ = get_game_status_embed(is_game_over=True)
            final_embed.add_field(name="--- KẾT QUẢ ---", value=f"🤝 **HÒA (PUSH)!** Cả hai đều Blackjack. Hoàn lại **{bet}** xu.", inline=False)
            return await ctx.send(embed=final_embed)
        else:
            # Thắng Blackjack (1.5 lần)
            win_amount = int(bet * 2.5) # Cược 1, thắng 1.5, nhận lại tổng 2.5
            update_balance(user_id, win_amount) 
            final_embed, _, _ = get_game_status_embed(is_game_over=True)
            final_embed.add_field(name="--- KẾT QUẢ ---", value=f"🎉 **BLACKJACK!** Bạn thắng **{win_amount}** xu.", inline=False)
            return await ctx.send(embed=final_embed)

    # Nút bấm tương tác
    hit_button = discord.ui.Button(label="Hit (Rút thêm)", style=discord.ButtonStyle.green, custom_id="hit")
    stand_button = discord.ui.Button(label="Stand (Dừng)", style=discord.ButtonStyle.red, custom_id="stand")
    
    view = discord.ui.View(timeout=60)
    view.add_item(hit_button)
    view.add_item(stand_button)
    
    message = await ctx.send(embed=initial_embed, view=view)

    # Logic chơi game (Sử dụng Event Listener)
    async def interaction_check(interaction):
        return interaction.user == ctx.author and interaction.message.id == message.id

    try:
        while player_score < 21:
            interaction, button_id = await bot.wait_for(
                "interaction", 
                check=interaction_check, 
                timeout=60.0
            )
            
            await interaction.response.defer() # Xác nhận tương tác để tránh lỗi

            if interaction.custom_id == "hit":
                player_hand.append(deck.pop())
                player_score = calculate_hand_value(player_hand)
                current_embed, _, _ = get_game_status_embed(is_game_over=False)
                
                if player_score > 21:
                    # BUST - THUA
                    view.clear_items()
                    final_embed, _, _ = get_game_status_embed(is_game_over=True)
                    final_embed.add_field(name="--- KẾT QUẢ ---", value=f"💔 **BÙNG!** (Bust - {player_score}). Bot thắng. Bạn mất **{bet}** xu.", inline=False)
                    await message.edit(embed=final_embed, view=view)
                    return
                
                await message.edit(embed=current_embed, view=view)

            elif interaction.custom_id == "stand":
                # Người chơi dừng, bắt đầu lượt Bot (Dealer)
                break
        
        # --- Lượt Bot (Dealer) ---
        view.clear_items()
        
        final_embed, player_score, dealer_score = get_game_status_embed(is_game_over=True)
        await message.edit(embed=final_embed, view=view) # Cập nhật để hiển thị bài ẩn của Dealer

        while dealer_score < 17:
            await asyncio.sleep(1.5) # Tạo độ trễ như đang chia bài
            dealer_hand.append(deck.pop())
            dealer_score = calculate_hand_value(dealer_hand)
            
            final_embed, _, _ = get_game_status_embed(is_game_over=True)
            await message.edit(embed=final_embed, view=view)

        # Xử lý kết quả cuối cùng
        result_message = ""
        win_amount = 0
        
        if dealer_score > 21:
            # Dealer BUST
            win_amount = bet * 2 # Cược 1, thắng 1, nhận lại tổng 2
            update_balance(user_id, win_amount)
            result_message = f"✅ **BOT BÙNG!** ({dealer_score}). Bạn thắng **{bet}** xu. Tổng nhận: **{win_amount}** xu."
        elif dealer_score > player_score:
            # Dealer thắng
            result_message = f"❌ **DEALER THẮNG** ({dealer_score} > {player_score}). Bạn mất **{bet}** xu."
        elif player_score > dealer_score:
            # Người chơi thắng
            win_amount = bet * 2
            update_balance(user_id, win_amount)
            result_message = f"🎉 **BẠN THẮNG!** ({player_score} > {dealer_score}). Bạn thắng **{bet}** xu. Tổng nhận: **{win_amount}** xu."
        else:
            # Hòa
            update_balance(user_id, bet) # Hoàn lại tiền cược
            result_message = f"🤝 **HÒA (PUSH)!** ({player_score} = {dealer_score}). Hoàn lại **{bet}** xu."

        final_embed.add_field(name="--- KẾT QUẢ CHUNG CUỘC ---", value=result_message, inline=False)
        await message.edit(embed=final_embed)

    except asyncio.TimeoutError:
        view.clear_items()
        update_balance(user_id, bet) # Hoàn lại tiền cược nếu hết giờ
        timeout_embed, _, _ = get_game_status_embed(is_game_over=True)
        timeout_embed.add_field(name="--- KẾT QUẢ ---", value=f"⏰ **Hết giờ!** Hoàn lại **{bet}** xu cược.", inline=False)
        await message.edit(embed=timeout_embed, view=view)
    
    await balance_command(ctx)


# --- LỆNH GAME VỚI PREFIX VÀ ALIAS ---

@bot.command(name="daily", aliases=["bdaily"])
@commands.cooldown(1, 86400, commands.BucketType.user) 
async def daily_command(ctx):
    """Nhận thưởng hàng ngày (Nhiệm vụ ngày) - Dùng !daily hoặc bdaily"""
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


@bot.command(name="hunt", aliases=["bhunt"])
@commands.cooldown(1, 60, commands.BucketType.user) 
async def hunt_command(ctx):
    """Trò chơi BẮT THÚ (bhunt) - Dùng !hunt hoặc bhunt"""
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
        c.execute('INSERT INTO user_pets (user_id, pet_name, rarity, pet_skill, is_hidden) VALUES (?, ?, ?, ?, ?)',
                  (user_id, pet_name, rarity, pet_skill, is_hidden))
        conn.commit()
        await ctx.send(f"{message}\nKỹ năng Pet: **{pet_skill}**")
    else:
        update_balance(user_id, 50)
        await ctx.send("💔 Bạn đi săn nhưng không thấy Pet nào. Nhận **50** xu an ủi.")
    await balance_command(ctx)

@hunt_command.error
async def hunt_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ **{ctx.author.display_name}** ơi, bạn phải chờ **{int(error.retry_after)}** giây nữa mới có thể đi săn tiếp.")


# --- LỆNH MỚI: TRÌNH ĐỌC TIN NHẮN (TTS) ---

@bot.command(name="b", aliases=["tts", "speak"]) # Đã sửa tên lệnh thành "b"
async def speak_command(ctx, *, text: str):
    """Lệnh !b <tin nhắn> để bot đọc tin nhắn trong kênh thoại."""
    
    if not ctx.message.author.voice:
        await ctx.send("❌ Bạn phải ở trong một kênh thoại để sử dụng lệnh này.")
        return
        
    voice_channel = ctx.message.author.voice.channel
    
    # Giới hạn độ dài tin nhắn để tránh quá tải
    if len(text) > 100: text = text[:100] + "..."

    mp3_filepath = None
    try:
        # Lang='vi' (Tiếng Việt), slow=False (Tốc độ thường)
        tts = gTTS(text=text, lang='vi', slow=False) 
        
        # Sử dụng thư mục tạm thời và quản lý file bằng os
        tmp_dir = tempfile.gettempdir()
        mp3_filepath = os.path.join(tmp_dir, f"tts_{ctx.message.id}.mp3")
        
        tts.save(mp3_filepath) 
            
    except Exception as e:
        await ctx.send(f"❌ Lỗi tạo file âm thanh (TTS). Lỗi chi tiết: {e}")
        return

    try:
        # Lấy/Kết nối Voice Client
        if ctx.voice_client:
            # Nếu bot đang ở kênh thoại khác, di chuyển đến kênh của người dùng
            if ctx.voice_client.channel != voice_channel:
                vc = await ctx.voice_client.move_to(voice_channel)
            else:
                vc = ctx.voice_client
        else:
            # Kết nối mới
            vc = await voice_channel.connect()
            
        if vc.is_playing():
            vc.stop()
        
        # Phát file .mp3 đã tạo (Yêu cầu FFmpeg hoạt động)
        audio_source = discord.FFmpegPCMAudio(mp3_filepath)
        vc.play(audio_source, after=lambda e: print(f'Player error: {e}') if e else None)
        
        await ctx.send(f"🔊 Đã phát tin nhắn của **{ctx.author.display_name}**: **{text}**")
        
        # Chờ bot phát xong
        while vc.is_playing():
             await asyncio.sleep(0.5)
        
        # Tùy chọn ngắt kết nối sau khi phát
        await vc.disconnect() 

    except discord.ClientException:
        await ctx.send("❌ Bot đang bận hoặc có lỗi kết nối kênh thoại. Hãy thử lại sau.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi phát âm thanh: Vui lòng kiểm tra đã cài đặt **FFmpeg** chưa. Lỗi chi tiết: {e}")
    finally:
        # Quan trọng: Đảm bảo file tạm thời được xóa
        if mp3_filepath and os.path.exists(mp3_filepath):
            os.remove(mp3_filepath)

# --- SỰ KIỆN CHÀO MỪNG & TẠM BIỆT (6 PHONG CÁCH) ---

@bot.event
async def on_member_join(member):
    """Chào mừng thành viên với 6 phong cách ngẫu nhiên."""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        message_template = random.choice(WELCOME_MESSAGES)
        
        try:
             # Đảm bảo người dùng có trong DB và nhận 100 xu khởi nghiệp
             get_balance(member.id) 
             update_balance(member.id, 100) 
        except:
             pass 
             
        final_message = message_template.format(name=member.mention)
        await channel.send(final_message)

@bot.event
async def on_member_remove(member):
    """Tạm biệt thành viên với 6 phong cách ngẫu nhiên."""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        message_template = random.choice(GOODBYE_MESSAGES)
        final_message = message_template.format(name=member.display_name)
        await channel.send(final_message)


# --- CÁC LỆNH KHÁC ---

@bot.command(name="balance", aliases=["bal", "tien"])
async def balance_command(ctx, member: discord.Member = None):
    member = member or ctx.author; balance = get_balance(member.id)
    await ctx.send(f"💰 Số dư hiện tại của **{member.display_name}** là: **{balance}** xu.")

@bot.command(name="admingive")
@commands.has_permissions(administrator=True) 
async def admin_give_money(ctx, member: discord.Member, amount: int):
    if amount <= 0: await ctx.send("Số tiền phải lớn hơn 0."); return
    update_balance(member.id, amount)
    await ctx.send(f"✅ Đã chuyển **{amount}** xu cho **{member.display_name}**.")
    await balance_command(ctx, member=member)

@bot.command(name="ping", aliases=["lat"])
async def ping_command(ctx):
    latency = round(ctx.bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Độ trễ hiện tại là: **{latency}ms**")

@bot.command(name="gacha", aliases=["mohòm"])
async def open_gacha_box(ctx):
    COST = 500; user_id = ctx.author.id
    if get_balance(user_id) < COST: await ctx.send(f"❌ Bạn cần **{COST}** xu để mở hòm Gacha vũ khí."); return
    update_balance(user_id, -COST); item = random_roll_weapon(); add_item_to_inventory(user_id, item)
    # Lấy thông tin đã mở hộp để gửi thông báo cuối cùng
    message = f"📦 **{ctx.author.display_name}** mở hòm và nhận được **{item['name']}**!"
    
    # Tiếp tục thêm thông báo chi tiết
    details = (
        f"Cấp độ: **{item['rarity']}**\n"
        f"Chỉ số: Skin **{item['skin_percent']}%**\n"
        f"Kỹ năng Chính: **{item['skill_main']}**\n"
        f"Kỹ năng Phụ: {item['skill_sub1']}, {item['skill_sub2']}, {item['skill_sub3']}, {item['skill_sub4']}"
    )
    
    await ctx.send(f"{message}\n{details}")
    await balance_command(ctx)

# --- KHỞI CHẠY BOT ---

if __name__ == "__main__":
    bot.run(TOKEN)
