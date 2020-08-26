import os
import discord
from discord import Embed
from discord.ext import tasks
import re
import datetime
import time
import io
import aiohttp
import asyncio


# BOTのトークン
TOKEN = os.environ['DISCORD_BOT_TOKEN']
# 接続に必要なオブジェクトを生成
client = discord.Client()

# オプション ################
pants_url = [
    "https://media.discordapp.net/attachments/599780162313256961/721356052083245086/127_20200613223037.png",
    "https://media.discordapp.net/attachments/599780162313256961/721356018789122104/127_20200613222952.png"
]
# 変数 ######################
kick_cmd = False
clan_battle_days = ["2020/08/26 05:00", "2020/08/31 00:00"]
BOSS_Ch = [680753487629385739, 680753616965206016, 680753627433795743, 680753699152199680, 680754056477671439]
BOSS_name = ["BOSS_1", "BOSS_2", "BOSS_3", "BOSS_4", "BOSS_5"]
#############################
# メッセージリンク検知
regex_discord_message_url = (
    'https://(ptb.|canary.)?discord(app)?.com/channels/'
    '(?P<guild>[0-9]{18})/(?P<channel>[0-9]{18})/(?P<message>[0-9]{18})'
)


# パンツ交換
async def pants_trade(message):
    if "パンツ交換" in message.content or "パンツ" in message.content:
        if "パンツ交換" in message.content:
            x = 0

        elif "パンツ" in message.content:
            x = 1
            pass

        my_url = pants_url[x]
        async with aiohttp.ClientSession() as session:
            async with session.get(my_url) as resp:
                if resp.status != 200:
                    return await message.channel.send('Could not download file...')

                data = io.BytesIO(await resp.read())
                await message.channel.send(file=discord.File(data, 'cool_image.png'))

# メンバー追放
async def member_kick(message):
    global kick_cmd
    kick_cmd = True
    user = message.raw_mentions[0]

    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    if user == 490682682880163850:
        return

    kick_user = discord.utils.get(message.guild.members, id=user)
    member_log_ch = 741851689916825630
    channel = client.get_channel(member_log_ch)
    embed = discord.Embed(title="【下記のメンバーはサーバーから追放されました。】", color=0xff0000)
    embed.set_thumbnail(url=kick_user.avatar_url)
    embed.add_field(name="アカウント名≫", value=kick_user.mention, inline=False)
    embed.add_field(name="ニックネーム》", value=kick_user.display_name, inline=False)
    embed.add_field(name="ユーザーID》", value=kick_user.id, inline=False)
    embed.add_field(name="サーバー追放日時》", value=f"{now_ymd} {now_hms}", inline=False)

    await kick_user.kick()
    await channel.send(embed=embed)


# ボスの登録
async def boss_ch_neme(message):
    global BOSS_name
    r = message.content
    role_m = discord.utils.get(message.guild.roles, name="クランメンバー")
    M = datetime.datetime.now().strftime("%m")
    BOSS_name.clear()
    BOSS_name = r.split()
    BOSS_name.pop(0)
    BOSS_names = "各ボスのチャンネル名を変更しました。\n\n"
    x = 0

    # チャンネル名の変更
    while x <= 4:
        channel = client.get_channel(BOSS_Ch[x])
        r = str(x + 1) + "ボス》" + BOSS_name[x] + "\n"
        await channel.edit(name=r)
        await channel.send(f"{role_m.mention}\n\n> {int(M)}月の{x + 1}ボスは『{BOSS_name[x]}』です。\nよろしくお願いします。")
        BOSS_names += channel.mention + "\n"
        x += 1

    await message.delete()
    await message.channel.send(BOSS_names)


# ロールメンバーリスト
async def role_member_list(message):
    role = message.role_mentions[0].name
    role_m = message.role_mentions[0].mention
    member_list = message.role_mentions[0].members
    # 《.display_name》ニックネームの取得
    member_names = '\n'.join([member.display_name for member in member_list])

    # 埋め込みリスト作成
    embed = discord.Embed(title=f"『{role}』ロール情報", description=f"【ロールメンション】\n{role_m}", color=0x00ff00)
    embed.add_field(name="【現在の人数】", value=f"{len(member_list)}人", inline=False)
    embed.add_field(name="【メンバーリスト】", value=member_names, inline=False)
    # 直前のメッセージを削除
    await message.delete()
    await message.channel.send(embed=embed)


# 持ち越し時間用ＴＬ改変
async def ok_tl_edit(message):
    r = message.content
    if r.startswith(r"/tl "):
        tl = r.split("\n", 1)
        ok_time_sec = re.sub(r"\D", "", tl[0])
        tl.pop(0)

        # 持ち越しTL計算
        ok_time = 90 - int(ok_time_sec)
        tl_times = []
        ok_tl_edit = []
        time_min = []
        ok_tl_sec = []

        # テキストの記載時間のリスト化
        for tl_time in re.findall(r"[0-9]:[0-9]{2}", tl[0]):
            tl_times.append(tl_time)

        # 「分」値抽出
        for tl_m in re.findall(r"[0-9]:", tl[0]):
            tl_m = tl_m.replace(':', '')
            tl_min = int(tl_m)
            time_min.append(tl_min)

        # 「秒」値抽出、秒数化
        for tl_x, tl_y in zip(re.findall(r":[0-9]{2}", tl[0]), time_min):
            tl_x = tl_x.replace(':', '')
            tl_sec = int(tl_x) + (int(tl_y) * 60)
            ok_tl_sec.append(tl_sec)

        # 持ち越しTL修正
        for times in ok_tl_sec:
            edit_time_sec = times - ok_time if times - ok_time >= 0 else 0
            edit_time = edit_time_sec // 60 if edit_time_sec // 60 >= 0 else 0
            edit_time_sec = edit_time_sec - 60 if edit_time_sec >= 60 else edit_time_sec
            # 0:00形式に直す
            edit_t = f"{edit_time}:{str(edit_time_sec).zfill(2)}"
            ok_tl_edit.append(edit_t)

        # リストのリバース
        tl_times.reverse()
        ok_tl_edit.reverse()
        tl_1 = tl[0]
        for time_x, time_y in zip(tl_times, ok_tl_edit):
            tl_2 = tl_1.replace(time_x, time_y)
            tl_1 = tl_2

        tl_message = f"持ち越し時間「{ok_time_sec}秒」のTLに改変しました。\n\n{tl_1}"
        await message.channel.send(tl_message)


# 未3凸ロール解除
async def noattack_role_remove(message):
    channel = message.channel.id
    guild = message.author.guild
    role = guild.get_role(715250107058094100)  # 未3凸ロール
    clan_member_role = guild.get_role(687433139345555456)  # クラメンロール
    clan_member = clan_member_role.members
    if channel == 695958348264374343:
        # ロールの判定
        userrole = False
        for role in message.author.roles:
            if role.id == 715250107058094100:
                userrole = True
                break

        if userrole is True:
            await message.author.remove_roles(role)
            await asyncio.sleep(0.5)
            noattack_member = role.members
            x = len(clan_member) - len(noattack_member)
            i = ("本日の3凸お疲れ様です。\n"
                 f"{message.author.mention} さんは本日「{x}人目」です。\n\n")
            i += "本日の凸は全員終了しました。" if len(noattack_member) == 0 else f"残りメンバーは「{len(noattack_member)}人」です。"

            if len(noattack_member) <= 10 and len(noattack_member) > 0:
                noattack_member_list = '\n'.join([member.display_name for member in noattack_member])
                embed = discord.Embed(title="【未3凸メンバー状況】", color=0x00ff00)
                embed.add_field(name="【残り人数】", value=f"{len(noattack_member)}人", inline=False)
                embed.add_field(name="【残りメンバー】", value=noattack_member_list, inline=False)
                await message.channel.send(i, embed=embed)

            else:
                await message.channel.send(i)

        else:
            await message.channel.send(f"{message.author.mention}さんは本日の凸はもう終わってるみたいですね。\n"
                                       "いたずらはダメですよ？")


# メッセージリンクの展開
async def dispand(message):
    messages = await extract_messsages(message)
    for m in messages:
        if message.content:
            await message.channel.send(embed=compose_embed(m))
        for embed in m.embeds:
            await message.channel.send(embed=embed)


async def extract_messsages(message):
    messages = []
    for ids in re.finditer(regex_discord_message_url, message.content):
        if message.guild.id != int(ids['guild']):
            return
        fetched_message = await fetch_message_from_id(
            guild=message.guild,
            channel_id=int(ids['channel']),
            message_id=int(ids['message']),
        )
        messages.append(fetched_message)
    return messages


async def fetch_message_from_id(guild, channel_id, message_id):
    channel = guild.get_channel(channel_id)
    message = await channel.fetch_message(message_id)
    return message


def compose_embed(message):
    embed = Embed(
        description=message.content,
        timestamp=message.created_at,
        color=0x3ccbfb,
    )
    embed.set_author(
        name=message.author.display_name,
        icon_url=message.author.avatar_url,
    )
    embed.set_footer(
        text=message.channel.name,
        icon_url=message.guild.icon_url,
    )
    if message.attachments and message.attachments[0].proxy_url:
        embed.set_image(
            url=message.attachments[0].proxy_url
        )
    return embed

# メッセージログ
# 書き込み
async def new_message(message):

    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    CHANNEL_ID = 741851542503817226
    channel = client.get_channel(CHANNEL_ID)
    embed = discord.Embed(title="【メッセージログ】", color=0x00ffee)
    embed.add_field(name="イベント内容≫", value="書き込み", inline=False)
    embed.add_field(name="アカウント名≫", value=message.author.mention, inline=False)
    embed.add_field(name="ニックネーム》", value=message.author.display_name, inline=False)
    embed.add_field(name="ユーザーID》", value=message.author.id, inline=False)
    embed.add_field(name="日時》", value=f"{now_ymd} {now_hms}", inline=False)
    embed.add_field(name="チャンネル》", value=message.channel.mention, inline=False)
    embed.add_field(name="メッセージID》", value=message.id, inline=False)

    if message.content:
        embed.add_field(name="メッセージ内容》", value=message.content, inline=False)

    if message.attachments and message.attachments[0].proxy_url:
        img_urls = []
        x = 1
        for img in message.attachments:
            img_urls.append(f"[ファイル {x}]({img.proxy_url})")
            x += 1

        embed.set_image(
            url=message.attachments[0].proxy_url
        )

        embed.add_field(name="添付ファイル一覧》", value="\n".join(img_urls), inline=False)

    await channel.send(embed=embed)


# メッセージ編集
@client.event
async def on_raw_message_edit(payload):
    global start_time
    global new_message_id

    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    CHANNEL_ID = 741851542503817226
    channel_1 = client.get_channel(payload.channel_id)
    message = await channel_1.fetch_message(payload.message_id)

    now_time = time.time() - start_time

    if message.author.bot:
        return

    elif now_time < 3 and new_message_id == payload.message_id:
        return

    channel = client.get_channel(CHANNEL_ID)
    embed = discord.Embed(title="【メッセージログ】", color=0xffd700)
    embed.add_field(name="イベント内容≫", value="メッセージ編集", inline=False)
    embed.add_field(name="アカウント名≫", value=message.author.mention, inline=False)
    embed.add_field(name="ニックネーム》", value=message.author.display_name, inline=False)
    embed.add_field(name="ユーザーID》", value=message.author.id, inline=False)
    embed.add_field(name="日時》", value=f"{now_ymd} {now_hms}", inline=False)
    embed.add_field(name="チャンネル》", value=message.channel.mention, inline=False)
    embed.add_field(name="メッセージID》", value=message.id, inline=False)

    if message.content:
        embed.add_field(name="メッセージ内容》", value=message.content, inline=False)

    if message.attachments and message.attachments[0].proxy_url:
        img_urls = []
        x = 1
        for img in message.attachments:
            img_urls.append(f"[ファイル {x}]({img.proxy_url})")
            x += 1

        embed.set_image(
            url=message.attachments[0].proxy_url
        )
        embed.add_field(name="添付ファイル一覧》", value="\n".join(img_urls), inline=False)

    await channel.send(embed=embed)


# メッセージ削除
@client.event
async def on_raw_message_delete(payload):

    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    message_delete_channel = client.get_channel(payload.channel_id)

    CHANNEL_ID = 741851542503817226
    channel = client.get_channel(CHANNEL_ID)
    embed = discord.Embed(title="【メッセージログ】", color=0xff0000)
    embed.add_field(name="イベント内容≫", value="メッセージ削除", inline=False)
    embed.add_field(name="アカウント名≫", value=payload.author.mention, inline=False)
    embed.add_field(name="ニックネーム》", value=payload.author.display_name, inline=False)
    embed.add_field(name="ユーザーID》", value=payload.author.id, inline=False)
    embed.add_field(name="日時》", value=f"{now_ymd} {now_hms}", inline=False)
    embed.add_field(name="チャンネル》", value=message_delete_channel.mention, inline=False)
    embed.add_field(name="メッセージID》", value=payload.message_id, inline=False)
    embed.add_field(name="メッセージ内容》", value="このメッセージは、削除されました。", inline=False)

    await channel.send(embed=embed)


# BOTの起動
@client.event
async def on_ready():
    global BOSS_name
    BOSS_name.clear()

    for channel_id in BOSS_Ch:
        channel = client.get_channel(channel_id)
        BOSS_name.append(re.sub(r"[0-9]ボス》", "", channel.name))

    CHANNEL_ID = 741851480868519966
    channel = client.get_channel(CHANNEL_ID)

    now = datetime.datetime.now()

    clan_battle_start_day = datetime.datetime.strptime(clan_battle_days[0], "%Y/%m/%d %H:%M")
    clan_battle_end_day = datetime.datetime.strptime(clan_battle_days[1], "%Y/%m/%d %H:%M")
    if clan_battle_start_day.strftime('%Y-%m-%d %H:%M') <= now.strftime('%Y-%m-%d %H:%M') < clan_battle_end_day.strftime('%Y-%m-%d %H:%M'):
        text_1 = "現在クランバトル開催中です。"

    else:
        text_1 = "現在クランバトル期間外です。"

    BOSS_names = "【現在のボス名】"
    for name in BOSS_name:
        BOSS_names += f"\n{name}"

    await channel.send(f"ミネルヴァ起動しました。\n\n{text_1}\n\n{BOSS_names}")


@client.event
async def on_member_join(member):

    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    member_log_ch = 741851689916825630
    channel = client.get_channel(member_log_ch)
    embed = discord.Embed(title="【新メンバー情報】", color=0x00ffee)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name="アカウント名≫", value=member.mention, inline=False)
    embed.add_field(name="ニックネーム》", value=member.display_name, inline=False)
    embed.add_field(name="ユーザーID》", value=member.id, inline=False)
    embed.add_field(name="サーバー入室日時》", value=f"{now_ymd} {now_hms}", inline=False)
    await channel.send(embed=embed)


@client.event
async def on_member_remove(member):
    global kick_cmd

    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    if kick_cmd is True:
        kick_cmd = False
        return

    member_log_ch = 741851689916825630
    channel = client.get_channel(member_log_ch)
    embed = discord.Embed(title="【サーバー退室者情報】", color=0xffea00)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name="アカウント名≫", value=member.mention, inline=False)
    embed.add_field(name="ニックネーム》", value=member.display_name, inline=False)
    embed.add_field(name="ユーザーID》", value=member.id, inline=False)
    embed.add_field(name="サーバー退室日時》", value=f"{now_ymd} {now_hms}", inline=False)
    await channel.send(embed=embed)


# 未3凸ロール初期化
@tasks.loop(seconds=30)
async def loop():
    guild = client.get_guild(599780162309062706)
    channel = client.get_channel(741851480868519966)
    role = guild.get_role(715250107058094100)  # 未3凸ロール
    clan_member_role = guild.get_role(687433139345555456)  # クラメンロール

    now = datetime.datetime.now()

    clan_battle_start_day = datetime.datetime.strptime(clan_battle_days[0], "%Y/%m/%d %H:%M")
    clan_battle_end_day = datetime.datetime.strptime(clan_battle_days[1], "%Y/%m/%d %H:%M")
    if clan_battle_start_day.strftime('%Y-%m-%d %H:%M') > now.strftime('%Y-%m-%d %H:%M') >= clan_battle_start_day.strftime('%Y-%m-%d %H:%M'):
        return

    if now.strftime('%H:%M') == '05:05':
        clan_member = clan_member_role.members

        for member in clan_member:
            await member.add_roles(role)

        await channel.send("クランメンバーに「未3凸」ロールを付与しました。")

loop.start()


@client.event
async def on_message(message):
    global start_time
    global new_message_id

    # BOT無視
    if message.author.bot:
        return

    start_time = time.time()
    new_message_id = message.id

    # ロールの判定
    userrole = False
    for role in message.author.roles:
        if role.id == 691179302024118282:
            userrole = True
            break

    # 管理者専用コマンド
    if userrole is True:
        r = message.content
        if r.startswith("/ボス名登録\n"):
            # ボスの登録
            await boss_ch_neme(message)

        # メンバーリスト取得
        if r.startswith(("/list\n", "/list ")):
            await role_member_list(message)

        if r.startswith(("/kick\n", "/kick ")):
            await member_kick(message)

    # メッセージリンク展開
    await dispand(message)

    # 持ち越し時間用ＴＬ改変
    await ok_tl_edit(message)

    # 未3凸ロール解除
    await noattack_role_remove(message)

    # パンツ交換
    await pants_trade(message)

    # メッセージログ
    await new_message(message)


client.run(TOKEN)
