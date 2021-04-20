import os
import traceback
import discord
from discord import Embed
from discord.ext import tasks
import re
import datetime
from datetime import timedelta
import calendar
import io
import aiohttp
import asyncio
import math
import matplotlib.pyplot as plt
import numpy as np

# BOTのトークン
TOKEN = os.environ['DISCORD_BOT_TOKEN']
# 接続に必要なオブジェクトを生成
client = discord.Client(intents=discord.Intents.all())

# オプション ################
pants_url = [
    "https://media.discordapp.net/attachments/599780162313256961/721356018789122104/127_20200613222952.png",
    "https://media.discordapp.net/attachments/599780162313256961/721356052083245086/127_20200613223037.png"
]
# 変数 ######################
kick_cmd = False
clan_battle_attack_role_id = [
    688651850513252353,  # 持ち越しロール
    715250107058094100,  # 残り3凸
    731746802499453049,  # 残り2凸
    731746926067974214  # 残り1凸
]

clan_battle_tutorial_days = True
clan_battle_channel_id = [
    # [チュートリアルCh_ID , クランバトル期間Ch_ID]
    [750345928678047744, 599784283359674379],  # 進捗状況,凸宣言チャンネル
    [750345732497735782, 599782273792999435],  # 凸相談
    [750351148841566248, 599792931674521600],  # タスキル状況
    [750345983661047949, 772305554009620480],  # バトルログ
    [774871889843453962, 599785761587331092],  # 持ち越しメモ
    [750346096156344450, 695958348264374343],  # 残り凸状況
    [811023367011303464, 811059306392715325]  # ミッション情報
]
boss_ch = [680753487629385739, 680753616965206016, 680753627433795743, 680753699152199680, 680754056477671439]
boss_name = ["BOSS_1", "BOSS_2", "BOSS_3", "BOSS_4", "BOSS_5"]
clan_battle_days = 5
clan_battle_start_date = ""
clan_battle_end_date = ""
boss_img_url = ["BOSS_1", "BOSS_2", "BOSS_3", "BOSS_4", "BOSS_5"]
boss_lv = [1, 4, 11, 35, 45]
boss_hp = [
    [6000000, 6000000, 7000000, 17000000, 85000000],
    [8000000, 8000000, 9000000, 18000000, 90000000],
    [10000000, 10000000, 13000000, 20000000, 95000000],
    [12000000, 12000000, 15000000, 21000000, 100000000],
    [15000000, 15000000, 20000000, 23000000, 110000000]
]
now_boss_data = {
    "now_lap": 1,
    "now_boss_level": 1,
    "now_boss": 0,
    "now_boss_hp": 6000000
}
ok_plyer_list = []
ok_attack_list = {}
p_attack_list = {}
m_attack_list = {}
now_attack_list = {}
reac_member = []
boss_hp_check = 0
now_clan_battl_message = None
new_boss_check = False
ok_member = False
no_attack_role_reset = True
add_role_check = False
rollover_time = "05:00"
fast_attack_check = False


# 凸宣言絵文字リスト
emoji_list = {
    "attack_p": "\U00002694\U0000fe0f",
    "attack_m": "\U0001f9d9",
    "T_kill": "\U0001f502",
    "SOS": "\U0001f198",
    "attack_end": "\U00002705"
}

number_emoji = [
    "\U00000031\U0000fe0f\U000020e3",
    "\U00000032\U0000fe0f\U000020e3",
    "\U00000033\U0000fe0f\U000020e3",
    "\U00000034\U0000fe0f\U000020e3",
    "\U00000035\U0000fe0f\U000020e3"
]

# 絵文字ヘルプ
help_emoji = f"""
__凸前宣言__
__(もう一度押すとキャンセル）__
┣{emoji_list["attack_p"]} 》物理編成
┗{emoji_list["attack_m"]} 》魔法編成

__オプション__
┣{emoji_list["T_kill"]} 》タスキル使用
┗{emoji_list["SOS"]} 》救援要請

__凸終了宣言__
__リアクション後に、「与えたダメージ」と「持ち越し時間」の入力があります。__
┗{emoji_list["attack_end"]} 》本戦終了"""

# タイムアウトエラーテキスト
timeouterror_text = """
```py
\"\"\"
長時間入力が無くタイムアウトになりました。
再度、リアクションをお願いします。
\"\"\"
```"""

boss_edit_message = (
    """/edit_boss
(?P<now_lap>[0-9]+)
(?P<now_boss>[1-5])
(?P<now_hp>[0-9]+)"""
)

#############################
# メッセージリンク検知
regex_discord_message_url = (
    'https://(ptb.|canary.)?discord(app)?.com/channels/'
    '(?P<guild>[0-9]{18})/(?P<channel>[0-9]{18})/(?P<message>[0-9]{18})'
)


# エラーログ
async def error_log(e_name, e_log):
    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    guild = client.get_guild(599780162309062706)
    error_log_channel = guild.get_channel(823188130252718100)  # エラーログ

    embed = discord.Embed(
        title=f"**{e_name}**",
        description=f"```py\n{e_log}\n```",
        color=0xff0000
    )
    embed.set_author(name="\U000026a0\U0000fe0f 例外が発生しました \U000026a0\U0000fe0f")
    embed.set_footer(text=f"エラー発生日時｜{now_ymd} {now_hms}")
    await error_log_channel.send(embed=embed)


# クラバト開催日時
def get_clanbattle_date(year, month):
    get_data = datetime.date(year, month, calendar.monthrange(year, month)[1])
    clan_battle_start_date = f"{get_data - datetime.timedelta(days=clan_battle_days)} 05:00"
    clan_battle_end_date = f"{get_data} 00:00"
    return clan_battle_start_date, clan_battle_end_date


# パンツ交換
async def pants_trade(message):
    if any([
        "パンツ" in message.content,
        "ぱんつ" in message.content
    ]):

        img_files = []
        n = 0
        async with aiohttp.ClientSession() as session:
            for img_url in pants_url:
                async with session.get(img_url) as resp:

                    if resp.status != 200:
                        return await message.channel.send('Could not download file...')

                    data = io.BytesIO(await resp.read())
                    img_files.append(discord.File(data, f'image_{n}.png'))
                    n += 1

        await message.channel.send(files=img_files)


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
    global boss_name
    r = message.content
    role_m = discord.utils.get(message.guild.roles, name="クランメンバー")
    M = datetime.datetime.now().strftime("%m")
    boss_name.clear()
    boss_name = r.split()
    boss_name.pop(0)
    boss_names = "各ボスのチャンネル名を変更しました。\n\n"
    x = 0

    # チャンネル名の変更
    while x <= 4:
        channel = client.get_channel(boss_ch[x])
        r = str(x + 1) + "ボス》" + boss_name[x] + "\n"
        boss = boss_name[x]

        message_description = f"{role_m.mention}\n\n {int(M)}月の{x + 1}ボスは『{boss_name[x]}』です。\nよろしくお願いします。"
        embed = await boss_description(boss)
        await channel.edit(name=r)
        await channel.send(message_description, embed=embed)
        boss_names += channel.mention + "\n"
        x += 1

    await message.delete()
    await message.channel.send(boss_names)

# ボス説明
async def boss_description(boss):
    global boss_img_url

    boss_data_ch = 784763031946264576
    channel_0 = client.get_channel(boss_data_ch)
    boss_img_url.clear()

    ln = "\n"
    embed_name = ""
    embed_value = []
    in_field = False
    embed = discord.Embed(
        title=boss,
        color=0x00b4ff
    )

    async for message in channel_0.history():
        if f"\n{boss}\n" in message.content:
            boss_text_message = message
            boss_img_url.append(boss_text_message.attachments[0].proxy_url)
            break

    boss_text = re.findall('(.*)\n', boss_text_message.content)
    for text in boss_text:
        if all([re.match("【(.*)】", text), "【ボス名】" != text]):
            if in_field:
                embed.add_field(
                    name=embed_name,
                    value=f"```py\n{ln.join([value_text for value_text in embed_value])}\n```",
                    inline=False
                )
                embed_value.clear()

            embed_name = text
            in_field = False

        elif all([
            text,
            text != boss,
            text != "【ボス名】",
            "```py" not in text,
            "```" not in text
        ]):
            embed_value.append(text)
            in_field = True

    embed.add_field(
        name=embed_name,
        value=f"```py\n{ln.join([value_text for value_text in embed_value])}\n```",
        inline=False)

    embed.set_thumbnail(url=boss_text_message.attachments[0].proxy_url)
    if len(message.attachments) == 2:
        embed.set_image(url=boss_text_message.attachments[1].proxy_url)

    return embed


# クラバト凸管理 ###########################
# 持ち越し時間算出
async def ok_time_plt(message):
    if "/持ち越しグラフ" not in message.content:
        return

    await message.delete()
    if re.search("(?<=/持ち越しグラフ )[0-9]+", message.content):
        now_hp = int(re.search("(?<=/持ち越しグラフ )[0-9]+", message.content).group())
    else:
        now_hp = int(now_boss_data["now_boss_hp"]) // 10000

    m_content = f"ボスの残り「`{now_hp} 万`」を同時凸したときのダメージと持ち越せる時間をグラフにしました。"
    add_damage = now_hp * 4.6
    n = 1 / 10000
    nx = now_hp * 4.3 / 17
    x = np.arange(now_hp, add_damage, n)  # linspace(min, max, N) で範囲 min から max を N 分割します
    y = 90 - (now_hp * 90 / x - 20)

    def f(y):
        if math.ceil(y) >= 90:
            return 90
        else:
            return math.ceil(y)

    plt.figure(figsize=(18, 9.5), dpi=200)
    plt.rcParams["font.size"] = 20
    plt.plot(x, [f(y[k]) for k in range(len(x))])
    plt.xlabel("dmage")
    plt.ylabel("second")
    plt.xticks(np.arange(now_hp, add_damage, nx))
    plt.yticks(np.arange(20, 91, 5))
    plt.minorticks_on()
    plt.grid(which="major", color="black", alpha=1)
    plt.grid(which="minor", color="gray", linestyle=":")

    plt_image = io.BytesIO()
    plt.savefig(plt_image, format="png", facecolor="azure", edgecolor="azure", bbox_inches='tight', pad_inches=0.5)

    plt_image.seek(0)
    plt_image_file = discord.File(plt_image, filename='image.png')

    await message.channel.send(m_content, file=plt_image_file)
    del plt_image


# スタートアップ
async def clan_battl_start_up():
    global now_boss_data

    now = datetime.datetime.now()
    now_boss_data["now_lap"] = 1
    now_boss_data["now_boss_level"] = 1
    now_boss_data["now_boss"] = 0
    now_boss_data["now_boss_hp"] = int(boss_hp[0][0])

    await clan_battl_role_reset(now)


# 進捗状況の編集
async def clan_battl_edit_progress(message):
    global now_boss_data
    guild = client.get_guild(599780162309062706)
    clan_member_mention = "クランメンバー" if clan_battle_tutorial_days is True else guild.get_role(687433139345555456).mention  # クランメンバーロール
    edit_message = now_clan_battl_message
    embed = edit_message.embeds[0]

    attack_3 = len(guild.get_role(clan_battle_attack_role_id[1]).members) * 3
    attack_2 = len(guild.get_role(clan_battle_attack_role_id[2]).members) * 2
    attack_1 = len(guild.get_role(clan_battle_attack_role_id[3]).members)
    OK_n = len(guild.get_role(clan_battle_attack_role_id[0]).members)
    attack_n = attack_3 + attack_2 + attack_1

    for ids in re.finditer(boss_edit_message, message.content):
        now_boss_data["now_lap"] = int(ids["now_lap"])
        now_boss_data["now_boss"] = int(ids["now_boss"]) - 1
        now_boss_data["now_boss_hp"] = int(ids["now_hp"])

    # 段階取得
    if 1 <= int(now_boss_data["now_lap"]) < 4:
        now_boss_data["now_boss_level"] = 1

    elif 4 <= int(now_boss_data["now_lap"]) < 11:
        now_boss_data["now_boss_level"] = 2

    elif 11 <= int(now_boss_data["now_lap"]) < 35:
        now_boss_data["now_boss_level"] = 3

    elif 35 <= int(now_boss_data["now_lap"]) < 45:
        now_boss_data["now_boss_level"] = 4

    elif 45 <= int(now_boss_data["now_lap"]):
        now_boss_data["now_boss_level"] = 5

    now_lap = now_boss_data["now_lap"]
    now_boss_level = now_boss_data["now_boss_level"]
    boss_name_index = int(now_boss_data["now_boss"])

    now_hp = "{:,}".format(int(now_boss_data["now_boss_hp"]))
    x = int(now_boss_data["now_boss"])
    y = int(now_boss_data["now_boss_level"]) - 1
    boss_max_hp = "{:,}".format(int(boss_hp[x][y]))

    description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
━━━━━━━━━━━━━━━━━━━
{now_lap}週目
{now_boss_level}段階目
{boss_name[boss_name_index]}
{now_hp}/{boss_max_hp}
━━━━━━━━━━━━━━━━━━━"""

    mention_text = f"{clan_member_mention}\n{now_lap}週目 {boss_name[boss_name_index]}"
    embed.description = description_text
    embed.set_thumbnail(url=boss_img_url[boss_name_index])

    await message.delete()
    await edit_message.edit(content=mention_text, embed=embed)


# 編成登録
async def battle_log_add_information(payload):
    guild = client.get_guild(599780162309062706)
    add_information_reaction_name = "\U0001f4dd"  # メモ絵文字
    channel = guild.get_channel(payload.channel_id)

    now = datetime.datetime.now()
    clear_missions = []

    y = 0 if clan_battle_tutorial_days is True else 1
    battle_log_channel = guild.get_channel(int(clan_battle_channel_id[3][y]))  # バトルログ
    reaction_message = await channel.fetch_message(payload.message_id)

    if any([
        payload.member.bot,
        not reaction_message.mentions
    ]):
        return

    # ミッション達成チェック
    # 編成情報チェック
    if not reaction_message.embeds[0].fields:
        clear_missions.append("m_011")
    # スクショチェック
    if not reaction_message.embeds[0].image:
        clear_missions.append("m_012")

    if all([
        payload.emoji.name == add_information_reaction_name,
        payload.channel_id == battle_log_channel.id,
        payload.member.id == reaction_message.mentions[0].id,
        reaction_message.embeds
    ]):

        await channel.set_permissions(payload.member, send_messages=True)
        battle_log_announce_message = await channel.send(f"""
{payload.member.mention}》
リアクションしたログに編成情報を反映します。

①ログのスクショ
②コメント

※①か②のどちらか、または①と②両方の書き込みができます。""")

        def battle_log_message_check(message):
            return all([
                message.channel == channel,
                message.author.id == payload.user_id,
                not message.author.bot
            ])

        try:
            battle_log_check_message = await client.wait_for('message', check=battle_log_message_check, timeout=90)

            # ミッションクリア判定
            if all([
                not battle_log_check_message.content,
                "m_009" in clear_missions
            ]):
                clear_missions.remove("m_009")

            if all([
                not battle_log_check_message.attachments,
                "m_010" in clear_missions
            ]):
                clear_missions.remove("m_010")

        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="タイムアウトエラー",
                description=timeouterror_text,
                colour=0xff0000
            )
            await battle_log_announce_message.delete()
            await channel.set_permissions(payload.member, overwrite=None)
            timeout_message = await channel.send(payload.member.mention, embed=embed)
            # リアクションリセット
            for reaction in reaction_message.reactions:
                if reaction.emoji == add_information_reaction_name:
                    async for user in reaction.users():
                        if user == payload.member:
                            await reaction.remove(user)

            await asyncio.sleep(10)
            await timeout_message.delete()
            return

        await channel.set_permissions(payload.member, overwrite=None)
        await asyncio.sleep(1.5)
        async for message in channel.history(limit=10):
            if not message.embeds:
                await message.delete()

            else:
                break

        embed = reaction_message.embeds[0]
        if battle_log_check_message.content:
            if reaction_message.embeds[0].fields:
                embed.set_field_at(
                    0,
                    name="【編成情報】",
                    value=battle_log_check_message.content,
                    inline=False
                )
            else:
                embed.add_field(
                    name="【編成情報】",
                    value=battle_log_check_message.content,
                    inline=False
                )

        if battle_log_check_message.attachments:
            embed.set_image(
                url=battle_log_check_message.attachments[0].proxy_url
            )

        # リアクションリセット
        for reaction in reaction_message.reactions:
            if reaction.emoji == add_information_reaction_name:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)

        await reaction_message.edit(embed=embed)

        # ミッション達成処理
        if clear_missions:
            await cb_mission(clear_missions, user=payload.member, clear_time=now)


# 残り凸メンバーリスト
async def clan_battl_no_attack_member_list(no_attack_member_list_ch):
    guild = client.get_guild(599780162309062706)
    channel = no_attack_member_list_ch

    nl = "\n"
    now = datetime.datetime.now()
    set_rollover_time = rollover_time

    start_y = clan_battle_start_date.year
    start_m = clan_battle_start_date.month
    start_d = clan_battle_start_date.day
    now_y = now.year
    now_m = now.month
    now_d = now.day
    cb_day = (datetime.date(now_y, now_m, now_d) - datetime.date(start_y, start_m, start_d) + timedelta(days=1)).days

    if cb_day <= 0:
        if any([
            datetime.datetime.now().strftime("%H:%M") < set_rollover_time,
            not no_attack_role_reset
        ]):
            cb_day = cb_day - 1

        cb_day_text = f"(開催**__{abs(cb_day)}日前__**)"

    else:
        if any([
            datetime.datetime.now().strftime("%H:%M") < set_rollover_time,
            not no_attack_role_reset
        ]):
            cb_day = cb_day - 1

        cb_day_text = f"__**{abs(cb_day)}日目**__"

    OK_n = guild.get_role(clan_battle_attack_role_id[0]).members
    noattack_member_list_0 = f"```{nl}{nl.join([member.display_name for member in OK_n])}{nl}```"

    attack_3 = guild.get_role(clan_battle_attack_role_id[1]).members
    noattack_member_list_3 = f"```{nl}{nl.join([member.display_name for member in attack_3])}{nl}```"

    attack_2 = guild.get_role(clan_battle_attack_role_id[2]).members
    noattack_member_list_2 = f"```{nl}{nl.join([member.display_name for member in attack_2])}{nl}```"

    attack_1 = guild.get_role(clan_battle_attack_role_id[3]).members
    noattack_member_list_1 = f"```{nl}{nl.join([member.display_name for member in attack_1])}{nl}```"

    attack_members = (len(attack_3) * 3) + (len(attack_2) * 2) + len(attack_1)

    if attack_members == 0 and len(OK_n) == 0:
        description_text = "本日のクランバトルは全員終了しました。"

    else:
        description_text = f"残り凸数》\n{attack_members} 凸\n持ち越し残り凸》\n{len(OK_n)} 人"

    embed = discord.Embed(
        title=f"【{now.month}月度クランバトル {cb_day_text}】",
        description=description_text,
        color=0x00b4ff
    )

    if len(OK_n) > 0:
        embed.add_field(name=f"持ち越し》{len(OK_n)} 人", value=noattack_member_list_0, inline=False)
    if len(attack_3) > 0:
        embed.add_field(name=f"残り3凸》{len(attack_3)} 人", value=noattack_member_list_3, inline=True)
    if len(attack_2) > 0:
        embed.add_field(name=f"残り2凸》{len(attack_2)} 人", value=noattack_member_list_2, inline=True)
    if len(attack_1) > 0:
        embed.add_field(name=f"残り1凸》{len(attack_1)} 人", value=noattack_member_list_1, inline=True)

    if attack_members == 0 and len(OK_n) == 0:
        now = datetime.datetime.now()
        now_ymd = f"{now.year}年{now.month}月{now.day}日"
        now_hms = f"{now.hour}時{now.minute}分{now.second}秒"
        embed.add_field(name="【全員３凸終了時間】", value=f"{now_ymd}\n{now_hms}", inline=False)

    await channel.send(embed=embed)


# 未凸ロールチェック
def no_attack_role_check(payload):
    guild = client.get_guild(599780162309062706)
    member = guild.get_member(payload.user_id)

    # ロールの判定
    ok_role_check = False
    attack_role_check = False
    for role in member.roles:
        if role.id == clan_battle_attack_role_id[0]:
            ok_role_check = True

        elif role.id == clan_battle_attack_role_id[1]:
            attack_role_check = True

        elif role.id == clan_battle_attack_role_id[2]:
            attack_role_check = True

        elif role.id == clan_battle_attack_role_id[3]:
            attack_role_check = True

    return attack_role_check, ok_role_check


# 未凸ロールの更新
async def add_attack_role(boss_hp_check_message):
    guild = client.get_guild(599780162309062706)
    boss_hp_check_member = boss_hp_check_message.author

    for role in boss_hp_check_member.roles:
        if role.id == clan_battle_attack_role_id[1]:
            attak_role = guild.get_role(clan_battle_attack_role_id[1])
            await boss_hp_check_member.remove_roles(attak_role)

            attak_role = guild.get_role(clan_battle_attack_role_id[2])
            await boss_hp_check_member.add_roles(attak_role)
            break

        elif role.id == clan_battle_attack_role_id[2]:
            attak_role = guild.get_role(clan_battle_attack_role_id[2])
            await boss_hp_check_member.remove_roles(attak_role)

            attak_role = guild.get_role(clan_battle_attack_role_id[3])
            await boss_hp_check_member.add_roles(attak_role)
            break

        elif role.id == clan_battle_attack_role_id[3]:
            attak_role = guild.get_role(clan_battle_attack_role_id[3])
            await boss_hp_check_member.remove_roles(attak_role)
            break


# 残り凸ロールリセット
async def clan_battl_role_reset(now):
    global add_role_check
    global no_attack_role_reset
    global now_attack_list
    global fast_attack_check

    guild = client.get_guild(599780162309062706)
    channel = client.get_channel(741851480868519966)  # ミネルヴァ・動作ログ
    now_attack_list.clear()

    fast_attack_check = True

    y = 0 if clan_battle_tutorial_days is True else 1
    no_attack_member_list_ch = guild.get_channel(int(clan_battle_channel_id[5][y]))  # 残り凸状況
    channel_4 = guild.get_channel(int(clan_battle_channel_id[4][y]))  # 持ち越しメモ

    if add_role_check:
        add_role_check = False
        return
    elif not add_role_check:
        add_role_check = True

    if not no_attack_role_reset:
        no_attack_role_reset = True

    if now_clan_battl_message:
        edit_message = now_clan_battl_message
        embed = edit_message.embeds[0]

        if not any([
            "【終了時間】" in embed.fields[0].name,
            "【本日の完凸時間】" in embed.fields[0].name
        ]):

            # 埋め込み情報の編集
            attack_3 = len(guild.get_role(clan_battle_attack_role_id[1]).members) * 3
            attack_2 = len(guild.get_role(clan_battle_attack_role_id[2]).members) * 2
            attack_1 = len(guild.get_role(clan_battle_attack_role_id[3]).members)
            OK_n = len(guild.get_role(clan_battle_attack_role_id[0]).members)
            attack_n = attack_3 + attack_2 + attack_1

            now_lap = now_boss_data["now_lap"]
            now_boss_level = now_boss_data["now_boss_level"]
            boss_name_index = int(now_boss_data["now_boss"])

            now_hp = "{:,}".format(int(now_boss_data["now_boss_hp"]))
            x = int(now_boss_data["now_boss"])
            y = int(now_boss_data["now_boss_level"]) - 1
            boss_max_hp = "{:,}".format(int(boss_hp[x][y]))

            description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
━━━━━━━━━━━━━━━━━━━
{now_lap}週目
{now_boss_level}段階目
{boss_name[boss_name_index]}
{now_hp}/{boss_max_hp}
━━━━━━━━━━━━━━━━━━━"""

            now_ymd = f"{now.year}年{now.month}月{now.day}日"
            now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

            embed.description = description_text
            embed.clear_fields()
            embed.add_field(name="【終了時間】", value=f"{now_ymd}\n{now_hms}", inline=False)

            # 終了したボス情報メッセージのリアクション削除
            await edit_message.clear_reactions()
            await edit_message.edit(embed=embed)

            # 持ち越しメッセージの削除
            async for message in channel_4.history():
                if not message.embeds:
                    await message.delete()

                elif message.embeds:
                    break

        # 凸漏れチェック
        if any([
            not clan_battle_tutorial_days,
            now.strftime('%Y-%m-%d') == clan_battle_end_date.strftime('%Y-%m-%d')
        ]):
            for role_id in clan_battle_attack_role_id:
                members = guild.get_role(role_id).members
                if members:
                    for member in members:
                        if role_id == clan_battle_attack_role_id[0]:
                            for count in range(1):
                                await cb_mission(clear_missions=["m_999"], user=member, clear_time=now)
                        elif role_id == clan_battle_attack_role_id[1]:
                            for count in range(3):
                                await cb_mission(clear_missions=["m_999"], user=member, clear_time=now)
                        elif role_id == clan_battle_attack_role_id[2]:
                            for count in range(2):
                                await cb_mission(clear_missions=["m_999"], user=member, clear_time=now)
                        elif role_id == clan_battle_attack_role_id[3]:
                            for count in range(1):
                                await cb_mission(clear_missions=["m_999"], user=member, clear_time=now)

        # クラバト終了処理
        if any([
            all([
                now.strftime('%Y-%m-%d %H:%M') >= clan_battle_start_date.strftime('%Y-%m-%d 00:00'),
                now.strftime('%Y-%m-%d %H:%M') < clan_battle_start_date.strftime('%Y-%m-%d %H:%M')
            ]),
            now.strftime('%Y-%m-%d %H:%M') >= clan_battle_end_date.strftime('%Y-%m-%d %H:%M')
        ]):
            await no_attack_role_remove()
            return

    embed = discord.Embed(
        description="残り凸情報のリセット処理中です。\nしばらくお待ちください。",
        colour=0xffff00
    )
    reset_role_text = await edit_message.channel.send(embed=embed)

    clan_member_role = guild.get_role(687433139345555456)   # クラメンロール
    clan_member = clan_member_role.members
    for member in clan_member:
        await member.add_roles(guild.get_role(clan_battle_attack_role_id[1]))

    if guild.get_role(clan_battle_attack_role_id[0]).members:
        for member in guild.get_role(clan_battle_attack_role_id[0]).members:
            await member.remove_roles(guild.get_role(clan_battle_attack_role_id[0]))

    if guild.get_role(clan_battle_attack_role_id[2]).members:
        for member in guild.get_role(clan_battle_attack_role_id[2]).members:
            await member.remove_roles(guild.get_role(clan_battle_attack_role_id[2]))

    if guild.get_role(clan_battle_attack_role_id[3]).members:
        for member in guild.get_role(clan_battle_attack_role_id[3]).members:
            await member.remove_roles(guild.get_role(clan_battle_attack_role_id[3]))

    await channel.send(f"クランメンバーに「未3凸」ロールを付与しました。\n{now}")
    await clan_battl_no_attack_member_list(no_attack_member_list_ch)
    await clan_battle_event()
    await reset_role_text.delete()


# 残り凸ロール全削除
async def no_attack_role_remove():
    global no_attack_role_reset

    guild = client.get_guild(599780162309062706)

    if not no_attack_role_reset:
        no_attack_role_reset = True

    if guild.get_role(clan_battle_attack_role_id[0]).members:
        for member in guild.get_role(clan_battle_attack_role_id[0]).members:
            await member.remove_roles(guild.get_role(clan_battle_attack_role_id[0]))

    if guild.get_role(clan_battle_attack_role_id[1]).members:
        for member in guild.get_role(clan_battle_attack_role_id[1]).members:
            await member.remove_roles(guild.get_role(clan_battle_attack_role_id[1]))

    if guild.get_role(clan_battle_attack_role_id[2]).members:
        for member in guild.get_role(clan_battle_attack_role_id[2]).members:
            await member.remove_roles(guild.get_role(clan_battle_attack_role_id[2]))

    if guild.get_role(clan_battle_attack_role_id[3]).members:
        for member in guild.get_role(clan_battle_attack_role_id[3]).members:
            await member.remove_roles(guild.get_role(clan_battle_attack_role_id[3]))


# 進捗状況更新
async def clan_battle_event():
    global now_clan_battl_message
    global boss_name
    global boss_hp
    global new_boss_check
    global now_boss_data
    global now_attack_list
    global p_attack_list
    global ok_plyer_list
    global ok_attack_list
    global p_attack_list
    global m_attack_list

    set_rollover_time = rollover_time
    now = datetime.datetime.now()

    start_y = clan_battle_start_date.year
    start_m = clan_battle_start_date.month
    start_d = clan_battle_start_date.day
    now_y = now.year
    now_m = now.month
    now_d = now.day
    cb_day = (datetime.date(now_y, now_m, now_d) - datetime.date(start_y, start_m, start_d) + timedelta(days=1)).days

    if cb_day <= 0:
        if any([
            datetime.datetime.now().strftime("%H:%M") < set_rollover_time,
            not no_attack_role_reset
        ]):
            cb_day = cb_day - 1

        cb_day_text = f"(開催**__{abs(cb_day)}日前__**)"

    else:
        if any([
            datetime.datetime.now().strftime("%H:%M") < set_rollover_time,
            not no_attack_role_reset
        ]):
            cb_day = cb_day - 1

        cb_day_text = f"__**{abs(cb_day)}日目**__"

    guild = client.get_guild(599780162309062706)

    y = 0 if clan_battle_tutorial_days is True else 1
    channel = guild.get_channel(int(clan_battle_channel_id[0][y]))  # 進捗状況

    clan_member_mention = "クランメンバー" if clan_battle_tutorial_days is True else guild.get_role(687433139345555456).mention  # クランメンバーロール

    attack_3 = len(guild.get_role(clan_battle_attack_role_id[1]).members) * 3
    attack_2 = len(guild.get_role(clan_battle_attack_role_id[2]).members) * 2
    attack_1 = len(guild.get_role(clan_battle_attack_role_id[3]).members)
    OK_n = len(guild.get_role(clan_battle_attack_role_id[0]).members)
    attack_n = attack_3 + attack_2 + attack_1

    now_lap = now_boss_data["now_lap"]
    now_boss_level = now_boss_data["now_boss_level"]
    boss_name_index = int(now_boss_data["now_boss"])

    now_hp = "{:,}".format(int(now_boss_data["now_boss_hp"]))
    x = int(now_boss_data["now_boss"])
    y = int(now_boss_data["now_boss_level"]) - 1
    boss_max_hp = "{:,}".format(int(boss_hp[x][y]))

    description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
━━━━━━━━━━━━━━━━━━━
{now_lap}週目
{now_boss_level}段階目
{boss_name[boss_name_index]}
{now_hp}/{boss_max_hp}
━━━━━━━━━━━━━━━━━━━"""

    # メッセージを書きます
    nl = "\n"
    embed = discord.Embed(
        title=f"【{now.month}月度クランバトル {cb_day_text}】",
        description=description_text,
        color=0x00b4ff
    )
    embed.set_thumbnail(url=boss_img_url[boss_name_index])

    if len(ok_plyer_list) != 0:
        for ok_list in ok_plyer_list:
            ok = ok_list

        embed.add_field(name="【持ち越し凸】", value=f"{ok.display_name}\n", inline=True)

    if len(p_attack_list) != 0:
        for p_list in p_attack_list:
            p = p_list
        embed.add_field(name="【物理編成】", value=f"{p.display_name}\n", inline=True)

    if len(m_attack_list) != 0:
        for m_list in m_attack_list:
            m = m_list

        embed.add_field(name="【魔法編成】", value=f"{m.display_name}\n", inline=True)

    if len(now_attack_list) != 0:
        embed.add_field(
            name="【現在本戦中メンバー】",
            value=f"```{nl}{nl.join([member for member in now_attack_list.values()])}{nl}```",
            inline=False
        )

    else:
        embed.add_field(name="【現在本戦中メンバー】", value=f"```py{nl}\"本戦中のメンバーは現在いません。\"{nl}```", inline=False)

    embed.add_field(name="【リアクション（スタンプ）説明】", value=help_emoji, inline=False)

    mention_text = f"{clan_member_mention}\n{now_lap}週目 {boss_name[boss_name_index]}"
    now_clan_battl_message = await channel.send(mention_text, embed=embed)

    for reactiones in emoji_list.values():
        await now_clan_battl_message.add_reaction(reactiones)


# 凸宣言キャンセルリアクションイベント
async def clan_battl_clear_reaction(payload):
    global now_attack_list

    nl = "\n"
    guild = client.get_guild(payload.guild_id)
    reac_member = guild.get_member(payload.user_id)
    channel = guild.get_channel(payload.channel_id)
    edit_message = now_clan_battl_message

    ch_id_index_y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][ch_id_index_y]))  # 進捗状況
    channel_1 = guild.get_channel(int(clan_battle_channel_id[1][ch_id_index_y]))  # 凸相談

    if any([
        reac_member.bot,
        reac_member not in now_attack_list,
        channel.id != int(clan_battle_channel_id[0][ch_id_index_y]),  # 進捗状況
    ]):
        return

    if payload.emoji.name == emoji_list["attack_p"]:
        for reaction in now_clan_battl_message.reactions:
            if reaction.emoji == emoji_list["attack_m"]:
                async for user in reaction.users():
                    member = guild.get_member(user.id)
                    if member == reac_member:
                        return

    if payload.emoji.name == emoji_list["attack_m"]:
        for reaction in now_clan_battl_message.reactions:
            if reaction.emoji == emoji_list["attack_p"]:
                async for user in reaction.users():
                    member = guild.get_member(user.id)
                    if member == reac_member:
                        return

    if any([
        payload.emoji.name == emoji_list["T_kill"],
        payload.emoji.name == emoji_list["SOS"],
        payload.emoji.name == emoji_list["attack_end"],
    ]):
        return

    embed = discord.Embed(
        description=f"{reac_member.display_name}》\n凸宣言がキャンセルされました。",
        color=0xff0000
    )
    now_attack_list.pop(reac_member)
    message_1 = await channel_1.send(embed=embed)
    message_2 = await channel_0.send(f"{reac_member.mention}》\n凸宣言をキャンセルしました。")

    if len(now_attack_list) != 0:
        member_list = ""
        for member, pt in zip(now_attack_list.keys(), now_attack_list.values()):
            member_list += f"{member.display_name}{pt}\n"
    else:
        member_list = f"```py{nl}\"本戦中のメンバーは現在いません。\"{nl}```"

    embed = edit_message.embeds[0]
    embed.set_field_at(
        0,
        name="【現在本戦中メンバー】",
        value=member_list,
        inline=False
    )
    await edit_message.edit(embed=embed)

    delete_time = 3
    await message_time_delete(message_2, delete_time)

    if not clan_battle_tutorial_days:
        if message_1:
            delete_time = 60
            await message_time_delete(message_1, delete_time)


# 凸管理リアクションイベント
async def clan_battl_call_reaction(payload):
    global boss_hp_check
    global now_attack_list
    global now_clan_battl_message
    global now_boss_data
    global new_boss_check
    global ok_member

    global fast_attack_check

    now = datetime.datetime.now()
    nl = "\n"
    hp_fomat = "{:,}"
    ok_attack_text = ""
    ok_attack_check = False
    la_mission = False
    true_dmg = ""
    last_attack_text = ""
    carry_over_time_message = ""
    carry_over_time = ""
    message_1 = ""
    message_2 = ""
    message_3 = ""

    reset_reaction = ["\U00002705", "\U0000274c"]

    guild = client.get_guild(599780162309062706)
    clan_member_role = guild.get_role(687433139345555456)  # クランメンバーロール
    ch_id_index_y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][ch_id_index_y]))  # 進捗状況
    channel_1 = guild.get_channel(int(clan_battle_channel_id[1][ch_id_index_y]))  # 凸相談
    channel_2 = guild.get_channel(int(clan_battle_channel_id[2][ch_id_index_y]))  # タスキル状況
    channel_3 = guild.get_channel(int(clan_battle_channel_id[3][ch_id_index_y]))  # バトルログ
    channel_4 = guild.get_channel(int(clan_battle_channel_id[4][ch_id_index_y]))  # 持ち越しメモ
    no_attack_member_list_ch = guild.get_channel(int(clan_battle_channel_id[5][ch_id_index_y]))  # 残り凸状況

    # 現在ボス
    now_lap = now_boss_data["now_lap"]
    now_boss_level = now_boss_data["now_boss_level"]
    boss_name_index = int(now_boss_data["now_boss"])
    now_hp = "{:,}".format(int(now_boss_data["now_boss_hp"]))
    last_hp = int(now_boss_data["now_boss_hp"])
    x = int(now_boss_data["now_boss"])
    y = int(now_boss_data["now_boss_level"]) - 1
    boss_max_hp_now = "{:,}".format(int(boss_hp[x][y]))

    edit_message = now_clan_battl_message
    reac_member = payload.member
    guild = client.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    reaction_message = await channel.fetch_message(payload.message_id)

    if reac_member.bot:
        return

    if channel.id == int(clan_battle_channel_id[0][ch_id_index_y]):  # 進捗状況
        attack_role_check, ok_role_check = no_attack_role_check(payload)

        if not attack_role_check and not ok_role_check:
            message_content = f"{payload.member.mention}》\n本日の3凸は終了してます。"
            if clan_battle_tutorial_days:
                embed = discord.Embed(
                    description=f"もう一度3凸する場合は「{reset_reaction[0]}」を、キャンセルする場合は「{reset_reaction[1]}」を押してください。",
                    color=0xffff00
                )

                reset_message = await channel_0.send(message_content, embed=embed)

                for reactiones in reset_reaction:
                    await reset_message.add_reaction(reactiones)

                def role_reset_check(reaction, user):

                    return all([
                        any([
                            reaction.emoji == reset_reaction[0],
                            reaction.emoji == reset_reaction[1]
                        ]),
                        reaction.message.id == reset_message.id,
                        user.id == payload.member.id,
                        not user.bot

                    ])

                try:
                    reaction, user = await client.wait_for('reaction_add', check=role_reset_check, timeout=30)

                except asyncio.TimeoutError:
                    for reaction in reaction_message.reactions:
                        async for user in reaction.users():
                            if user == payload.member:
                                await reaction.remove(user)

                    await reset_message.delete()
                    return

                if reaction.emoji == reset_reaction[1]:
                    for reaction in reaction_message.reactions:
                        async for user in reaction.users():
                            if user == payload.member:
                                await reaction.remove(user)

                    await reset_message.delete()
                    return

                elif reaction.emoji == reset_reaction[0]:
                    await payload.member.add_roles(guild.get_role(clan_battle_attack_role_id[1]))
                    await reset_message.delete()

            else:
                delete_message = await channel_0.send(message_content)
                delete_time = 10
                await message_time_delete(delete_message, delete_time)

        if ok_role_check:
            # 持ち越し時間
            async for message in channel_4.history():
                if payload.member.mention in message.content:
                    carry_over_time = re.search(r"[0-9]:[0-9]{2}", message.content).group()
                    break

            ok_attack_text = f"__**（持ち越し凸）{carry_over_time}**__"

        # 物理リアクション
        if payload.emoji.name == emoji_list["attack_p"]:
            now_attack_list[payload.member] = f"《物理編成》{ok_attack_text}"

            for reaction in reaction_message.reactions:
                if reaction.emoji == emoji_list["attack_m"]:
                    async for user in reaction.users():
                        if user == payload.member:
                            await reaction.remove(user)

            embed = discord.Embed(
                description=f"{reac_member.display_name}》\n「物理編成」{ok_attack_text}で入りました。",
                color=0x00b4ff
            )
            message_1 = await channel_1.send(embed=embed)
            add_attack_message = await channel_0.send(f"{reac_member.mention}》\n凸宣言を受け付けました。")

        # 魔法リアクション
        elif payload.emoji.name == emoji_list["attack_m"]:
            now_attack_list[payload.member] = f"《魔法編成》{ok_attack_text}"

            for reaction in reaction_message.reactions:
                if reaction.emoji == emoji_list["attack_p"]:
                    async for user in reaction.users():
                        if user == payload.member:
                            await reaction.remove(user)

            embed = discord.Embed(
                description=f"{reac_member.display_name}》\n「魔法編成」{ok_attack_text}で入りました。",
                color=0x00b4ff
            )
            message_2 = await channel_1.send(embed=embed)
            add_attack_message = await channel_0.send(f"{reac_member.mention}》\n凸宣言を受け付けました。")

        # タスキルリアクション
        elif payload.emoji.name == emoji_list["T_kill"]:
            await channel_2.send(f"{reac_member.display_name}》\nタスキルしました。")
            return

        elif payload.emoji.name == emoji_list["SOS"]:
            clan_member_mention = "クランメンバー" if clan_battle_tutorial_days is True else clan_member_role.mention
            await channel_1.send(f"{clan_member_mention}\n「{reac_member.display_name}」さんが救援を求めてます。")
            return

        # 凸終了リアクション
        elif payload.emoji.name == emoji_list["attack_end"]:
            if not now_attack_list.get(payload.member):
                # 凸宣言リアクションリセット
                for reaction in reaction_message.reactions:
                    # 凸終了宣言リアクションリセット
                    if reaction.emoji == emoji_list["attack_end"]:
                        async for user in reaction.users():
                            if user == reac_member:
                                await reaction.remove(user)

                not_reaction_message = await channel_0.send(f"{reac_member.mention}》\n凸宣言が有りません。")
                delete_time = 10
                await message_time_delete(not_reaction_message, delete_time)
                return

            await channel_0.set_permissions(reac_member, send_messages=True)
            m_content = f"""
{reac_member.mention}》
ボスに与えたダメージを「半角数字」のみで入力してください。

※ボスを倒した場合は「__{hp_fomat.format(int(now_boss_data['now_boss_hp']))}__」以上で入力してください。
※ボスの最大HP「__{boss_max_hp_now}__」以上は入力できません。
`スマホの場合、下の数字を長押しする事でコピーできます。`"""

            embed = discord.Embed(
                title="ラスアタ時は、下の数字をコピペしてください。",
                description=int(now_boss_data['now_boss_hp']),
                colour=0xffea00
            )
            dmg_input_announce_message_1 = await channel_0.send(m_content)
            dmg_input_announce_message_2 = await channel_0.send(int(now_boss_data['now_boss_hp']), embed=embed)

            def attack_dmg_message_check(message):
                if message.content.isdecimal():
                    damage = int(message.content)
                else:
                    return False

                return all([
                    message.content.isdecimal(),
                    int(damage) <= int(boss_hp[x][y]),
                    message.channel == channel_0,
                    message.author.id == payload.user_id,
                    not message.author.bot
                ])

            try:
                boss_hp_check_message = await client.wait_for('message', check=attack_dmg_message_check, timeout=90)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="タイムアウトエラー",
                    description=timeouterror_text,
                    colour=0xff0000
                )
                await dmg_input_announce_message_1.delete()
                await dmg_input_announce_message_2.delete()
                await channel_0.set_permissions(reac_member, overwrite=None)
                timeout_message = await channel_0.send(reac_member.mention, embed=embed)
                # 凸宣言リアクションリセット
                for reaction in reaction_message.reactions:
                    # 凸終了宣言リアクションリセット
                    if reaction.emoji == emoji_list["attack_end"]:
                        async for user in reaction.users():
                            if user == reac_member:
                                await reaction.remove(user)

                await asyncio.sleep(10)
                await timeout_message.delete()
                return

            async for message in channel_0.history(limit=20):
                if any([
                    message.id == dmg_input_announce_message_1.id,
                    message.id == dmg_input_announce_message_2.id,
                    message.id == boss_hp_check_message.id
                ]):
                    await message.delete()

                elif message.id == now_clan_battl_message.id:
                    break

            # 残り体力計算
            boss_hp_percentage = int(now_boss_data["now_boss_hp"]) / int(boss_hp[x][y]) * 100
            if round(boss_hp_percentage, 2) <= 25.00:
                la_mission = True

            last_boss_hp = int(now_boss_data["now_boss_hp"]) - int(boss_hp_check_message.content)
            if 0 >= last_boss_hp:
                last_hp = 0
                now_hp = 0
                ok_attack_check = True
                true_dmg = "" if last_boss_hp == 0 else f"\n　　({hp_fomat.format(int(now_boss_data['now_boss_hp']))})"
                if not ok_role_check:

                    time_input_announce_message = await channel_0.send(f"""
{reac_member.mention}》
持ち越し時間を入力してください、持ち越しメモに反映します。

※入力は全て「半角」にて「__**1:30～0:21**__」の範囲でお願いします。
【記入例】
1:30
0:25""")

                    def carry_over_time_message_check(message):
                        time_message = False
                        time_format = "(?P<min>[0-9]):(?P<sec>[0-9]{2})"

                        for times in re.finditer(time_format, message.content):
                            if any([
                                all([int(times["min"]) == 1, 0 <= int(times["sec"]) <= 30]),
                                all([int(times["min"]) == 0, 21 <= int(times["sec"]) <= 59])
                            ]):
                                time_message = True

                        return all([
                            time_message,
                            message.channel == channel_0,
                            message.author.id == payload.user_id,
                            not message.author.bot
                        ])

                    try:
                        carry_over_time_message = await client.wait_for('message', check=carry_over_time_message_check, timeout=90)
                        carry_over_time = re.search(r"[0-9]:[0-9]{2}", carry_over_time_message.content).group()

                    except asyncio.TimeoutError:
                        embed = discord.Embed(
                            title="タイムアウトエラー",
                            description=timeouterror_text,
                            colour=0xff0000
                        )
                        await time_input_announce_message.delete()
                        await channel_0.set_permissions(reac_member, overwrite=None)
                        timeout_message = await channel_0.send(reac_member.mention, embed=embed)
                        # 凸宣言リアクションリセット
                        for reaction in reaction_message.reactions:
                            # 凸終了宣言リアクションリセット
                            if reaction.emoji == emoji_list["attack_end"]:
                                async for user in reaction.users():
                                    if user == reac_member:
                                        await reaction.remove(user)

                        delete_time = 10
                        await message_time_delete(timeout_message, delete_time)
                        return

                async for message in channel_0.history(limit=20):
                    if message.id != now_clan_battl_message.id:
                        await message.delete()

                    elif message.id == now_clan_battl_message.id:
                        break

                if all([
                    ok_attack_check,
                    not ok_role_check
                ]):
                    last_attack_text = f"\n┣ラスアタ》\n┃┗__**持ち越し時間 ＝ {carry_over_time}**__"

                elif all([
                    ok_attack_check,
                    ok_role_check
                ]):
                    last_attack_text = "\n┣ラスアタ》\n┃┗__**持ち越し不可**__"

                nwe_lap_check = True if int(now_boss_data["now_boss"]) == 4 else False
                now_boss_data["now_boss"] = 0 if int(now_boss_data["now_boss"]) + 1 == 5 else int(now_boss_data["now_boss"]) + 1

                # ボス段階取得
                if nwe_lap_check:
                    now_boss_data["now_lap"] = int(now_boss_data["now_lap"]) + 1

                    if 1 <= int(now_boss_data["now_lap"]) < 4:
                        now_boss_data["now_boss_level"] = 1

                    elif 4 <= int(now_boss_data["now_lap"]) < 11:
                        now_boss_data["now_boss_level"] = 2

                    elif 11 <= int(now_boss_data["now_lap"]) < 35:
                        now_boss_data["now_boss_level"] = 3

                    elif 35 <= int(now_boss_data["now_lap"]) < 45:
                        now_boss_data["now_boss_level"] = 4

                    elif 45 <= int(now_boss_data["now_lap"]):
                        now_boss_data["now_boss_level"] = 5

                x = int(now_boss_data["now_boss"])
                y = int(now_boss_data["now_boss_level"]) - 1
                now_boss_data["now_boss_hp"] = int(boss_hp[x][y])

            for role in boss_hp_check_message.author.roles:
                if role.id == int(clan_battle_attack_role_id[0]):
                    ok_role_check = True
                    attak_role = guild.get_role(int(clan_battle_attack_role_id[0]))

                    # 持ち越しメッセージの削除
                    async for message in channel_4.history():
                        if boss_hp_check_message.author.mention in message.content:
                            carry_over_time = re.search(r"[0-9]:[0-9]{2}", message.content).group()

                            await message.delete()
                            break

                    await boss_hp_check_message.author.remove_roles(attak_role)
                    break

            if all([
                ok_attack_check,
                not ok_role_check
            ]):

                attak_role = guild.get_role(int(clan_battle_attack_role_id[0]))
                await boss_hp_check_message.author.add_roles(attak_role)

            if 0 < last_boss_hp:
                now_boss_data["now_boss_hp"] = last_boss_hp
                now_hp = "{:,}".format(int(now_boss_data["now_boss_hp"]))

            dmg = "{:,}".format(int(boss_hp_check_message.content))
            battle_log = f"""
{now_lap}週目・{now_boss_level}段階目
{boss_name[boss_name_index]}
{boss_hp_check_message.author.mention}
({boss_hp_check_message.author.display_name})
┣{now_attack_list[boss_hp_check_message.author]}{last_attack_text}
┗ダメージ》
　┗{dmg}{true_dmg}"""

            embed = discord.Embed(
                description=battle_log,
                color=0x00b4ff
            )
            embed.set_thumbnail(url=boss_img_url[boss_name_index])

            if carry_over_time_message:
                attak_type = re.sub(r"[《》]", "", now_attack_list[boss_hp_check_message.author])
                carry_over_time = re.match(r"[0-9]:[0-9]{2}", carry_over_time_message.content).group()

                last_attack_message = f"""
{boss_hp_check_message.author.mention}》
{now_lap}週目・{now_boss_level}段階目
{boss_name[boss_name_index]}
┃
┣┳ラスアタ時の編成
┃┗{attak_type}
┃
┗┳持ち越し時間
　┗__**{carry_over_time}**__"""

            if ok_attack_check:
                now_attack_list.clear()
            elif not ok_attack_check:
                del now_attack_list[boss_hp_check_message.author]

            # 凸宣言リアクションリセット
            for reaction in reaction_message.reactions:
                # 物理編成、凸宣言リアクションリセット
                if reaction.emoji == emoji_list["attack_p"]:
                    async for user in reaction.users():
                        if user == boss_hp_check_message.author:
                            await reaction.remove(user)

                # 魔法編成、凸宣言リアクションリセット
                if reaction.emoji == emoji_list["attack_m"]:
                    async for user in reaction.users():
                        if user == boss_hp_check_message.author:
                            await reaction.remove(user)

                # 凸終了宣言リアクションリセット
                if reaction.emoji == emoji_list["attack_end"]:
                    async for user in reaction.users():
                        if user == boss_hp_check_message.author:
                            await reaction.remove(user)

            if not ok_role_check:
                await add_attack_role(boss_hp_check_message)

            embed_end = discord.Embed(
                description=f"{boss_hp_check_message.author.display_name}》\n凸が終了しました。",
                color=0x00b4ff
            )
            now = datetime.datetime.now()
            await channel_0.set_permissions(boss_hp_check_message.author, overwrite=None)
            await clan_battl_no_attack_member_list(no_attack_member_list_ch)
            message_3 = await channel_1.send(embed=embed_end)
            battl_log_message = await channel_3.send(boss_hp_check_message.author.mention, embed=embed)
            await battl_log_message.add_reaction("\U0001f4dd")

            if carry_over_time_message:
                await channel_4.send(last_attack_message)

        if len(now_attack_list) != 0:
            member_list = ""
            for member, pt in zip(now_attack_list.keys(), now_attack_list.values()):
                member_list += f"{member.display_name}{pt}\n"
        else:
            member_list = f"```py{nl}\"本戦中のメンバーは現在いません。\"{nl}```"

        # 埋め込み情報の編集
        attack_3 = len(guild.get_role(clan_battle_attack_role_id[1]).members) * 3
        attack_2 = len(guild.get_role(clan_battle_attack_role_id[2]).members) * 2
        attack_1 = len(guild.get_role(clan_battle_attack_role_id[3]).members)
        OK_n = len(guild.get_role(clan_battle_attack_role_id[0]).members)
        attack_n = attack_3 + attack_2 + attack_1
        attack_total = attack_n + OK_n

        description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
━━━━━━━━━━━━━━━━━━━
{now_lap}週目
{now_boss_level}段階目
{boss_name[boss_name_index]}
{now_hp}/{boss_max_hp_now}
━━━━━━━━━━━━━━━━━━━"""

        embed = edit_message.embeds[0]
        embed.description = description_text
        embed.set_field_at(
            0,
            name="【現在本戦中メンバー】",
            value=member_list,
            inline=False
        )

        if 0 == last_hp or 0 == attack_total:
            now_ymd = f"{now.year}年{now.month}月{now.day}日"
            now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

            field_name = (
                "【本日の完凸時間】" if 0 >= attack_total else "【終了時間】"
            )

            if any([
                all([0 == last_hp, 0 == attack_total]),
                all([0 == last_hp, 0 <= attack_total]),
                all([0 <= last_hp, 0 == attack_total])
            ]):

                embed.clear_fields()
                embed.add_field(name=field_name, value=f"{now_ymd}\n{now_hms}", inline=False)

                # 終了したボス情報メッセージのリアクション削除
                await edit_message.clear_reactions()

            if all([0 == last_hp, 0 <= attack_total]):
                await clan_battle_event()

        await edit_message.edit(embed=embed)

        # クラバトミッション
        # ファーストアタック
        clear_missions = []
        attack_role_check, ok_role_check = no_attack_role_check(payload)
        if all([
            fast_attack_check,
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            fast_attack_check = False
            clear_missions.append("m_001")

        # ラスアタ
        if all([
            last_hp == 0,
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            clear_missions.append("m_002")

        # 残飯処理
        if all([
            last_hp == 0,
            la_mission,
            not true_dmg,
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            clear_missions.append("m_003")

        # 同時凸
        if all([
            last_hp == 0,
            true_dmg,
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            clear_missions.append("m_004")

        # ラス凸
        if all([
            attack_total == 0,
            now.strftime('%H:%M') >= "05:00",
            now.strftime('%H:%M') <= "23:59",
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            clear_missions.append("m_005")

        # 朝活
        if all([
            all([
                now.strftime('%H:%M') >= "05:00",
                now.strftime('%H:%M') < "11:00"
            ]),
            any([
                last_hp > 0,
                all([
                    last_hp == 0,
                    not ok_role_check
                ])
            ]),
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            clear_missions.append("m_006")

        # 朝活マスター
        if all([
            all([
                now.strftime('%H:%M') >= "05:00",
                now.strftime('%H:%M') < "11:00"
            ]),
            not attack_role_check,
            not ok_role_check,
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            clear_missions.append("m_007")

        # 昼活
        if all([
            all([
                now.strftime('%H:%M') >= "11:00",
                now.strftime('%H:%M') < "16:00"
            ]),
            any([
                last_hp > 0,
                all([
                    last_hp == 0,
                    not ok_role_check
                ])
            ]),
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            clear_missions.append("m_008")

        # 昼活マスター
        if all([
            all([
                now.strftime('%H:%M') >= "11:00",
                now.strftime('%H:%M') < "16:00"
            ]),
            not attack_role_check,
            not ok_role_check,
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            clear_missions.append("m_009")

        # 早寝早起き
        if all([
            all([
                now.strftime('%H:%M') >= "05:00",
                now.strftime('%H:%M') <= "23:59"
            ]),
            not attack_role_check,
            not ok_role_check,
            payload.emoji.name == emoji_list["attack_end"]
        ]):
            clear_missions.append("m_010")

        # ミッション達成処理
        if clear_missions:
            await cb_mission(clear_missions, user=payload.member, clear_time=now)

        # クロスデイcheck
        if not no_attack_role_reset:
            if not now_attack_list:

                if any([
                    all([
                        now.strftime('%Y-%m-%d %H:%M') >= clan_battle_start_date.strftime("%Y-%m-%d 00:00"),
                        now.strftime('%Y-%m-%d %H:%M') < clan_battle_end_date.strftime('%Y-%m-%d %H:%M')
                    ]),
                    now.strftime('%Y-%m-%d %H:%M') >= clan_battle_end_date.strftime('%Y-%m-%d %H:%M')
                ]):

                    await no_attack_role_remove()

                else:
                    await clan_battl_role_reset(now)

        if any([
                payload.emoji.name == emoji_list["attack_p"],
                payload.emoji.name == emoji_list["attack_m"]
        ]):
            if add_attack_message:
                delete_time = 3
                await message_time_delete(add_attack_message, delete_time)

        if not clan_battle_tutorial_days:
            if message_1:
                delete_time = 60
                await message_time_delete(message_1, delete_time)

            if message_2:
                delete_time = 60
                await message_time_delete(message_2, delete_time)

            if message_3:
                delete_time = 60
                await message_time_delete(message_3, delete_time)


#########################################
# クラバトミッション
async def cb_mission(clear_missions, user, clear_time):
    guild = client.get_guild(599780162309062706)
    y = 0 if clan_battle_tutorial_days is True else 1
    mission_log_channel = guild.get_channel(int(clan_battle_channel_id[6][y]))  # ミッション情報

    now = clear_time
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    # 現在のクラバト開催日数
    set_rollover_time = rollover_time

    start_y = clan_battle_start_date.year
    start_m = clan_battle_start_date.month
    start_d = clan_battle_start_date.day
    now_y = now.year
    now_m = now.month
    now_d = now.day
    cb_day = (datetime.date(now_y, now_m, now_d) - datetime.date(start_y, start_m, start_d) + timedelta(days=1)).days

    if cb_day <= 0:
        if any([
            datetime.datetime.now().strftime("%H:%M") < set_rollover_time,
            not no_attack_role_reset
        ]):
            cb_day = cb_day - 1

        cb_days = f"```\n開催{abs(cb_day)}日前\n```"

    else:
        if any([
            datetime.datetime.now().strftime("%H:%M") < set_rollover_time,
            not no_attack_role_reset
        ]):
            cb_day = cb_day - 1

        cb_days = f"```\n{abs(cb_day)}日目\n```"

    mission_logs = []
    for mission in clear_missions:
        # ファーストアタック
        if mission == "m_001":
            add_pt = 30
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n30人中のその日の1凸目になる\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # ラスアタ
        if mission == "m_002":
            add_pt = 10
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\nラスアタする\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 残飯処理
        if mission == "m_003":
            add_pt = 15
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n残り25％以下の体力のボスをラスアタする\n（同時凸による処理は不可）\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 同時凸
        if mission == "m_004":
            add_pt = 20
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n同時凸する\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # ラス凸
        if mission == "m_005":
            add_pt = 100
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n0時までにその日の90凸目になる\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 朝活
        if mission == "m_006":
            add_pt = 10
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n5時～11時の間に1凸する\n（ラスアタ時は持ち越し消化後に付与）\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 朝活マスター
        if mission == "m_007":
            add_pt = 20
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n11時までに3凸終了する\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 昼活
        if mission == "m_008":
            add_pt = 5
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n11時～16時の間に1凸する\n（ラスアタ時は持ち越し消化後に付与）\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 昼活マスター
        if mission == "m_009":
            add_pt = 10
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n16時までに3凸終了する\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 早寝早起き
        if mission == "m_010":
            add_pt = 5 * (20 - (int(now.hour) - 5))
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n0時までに3凸終了する\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # バトルログ
        # 編成情報
        if mission == "m_011":
            add_pt = 5
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\nバトルログに編成の詳細を書き込む\n（ラスアタ、持ち越しそれぞれ有効）\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # スクショ
        if mission == "m_012":
            add_pt = 5
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\nバトルログに編成のスクショをアップロード\n（ラスアタ、持ち越しそれぞれ有効)\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 凸漏れ
        if mission == "m_999":
            add_pt = -50
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n凸漏れしたのでポイントが減点されました\n```",
                color=0xff0000
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # ボス別編成共有
        # 1ボス編成
        if mission == "mb_001":
            add_pt = 10
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n1ボスの編成を上げる\n（クラマス判断で付与）\n（スクショのみは無効）\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 2ボス編成
        if mission == "mb_002":
            add_pt = 10
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n2ボスの編成を上げる\n（クラマス判断で付与）\n（スクショのみは無効）\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 3ボス編成
        if mission == "mb_003":
            add_pt = 10
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n3ボスの編成を上げる\n（クラマス判断で付与）\n（スクショのみは無効）\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 4ボス編成
        if mission == "mb_004":
            add_pt = 10
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n4ボスの編成を上げる\n（クラマス判断で付与）\n（スクショのみは無効）\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

        # 5ボス編成
        if mission == "mb_005":
            add_pt = 10
            embed = discord.Embed(
                title="以下のミッションを達成しました。》",
                description="```py\n5ボスの編成を上げる\n（クラマス判断で付与）\n（スクショのみは無効）\n```",
                color=0x00ffff
            )
            embed.add_field(name="【獲得ポイント】", value=f"```py\n\"{add_pt} pt\"\n```", inline=False)
            mission_logs.append(embed)

    # ミッションログ送信
    for embed in mission_logs:
        embed.set_author(
            name=user.display_name,
            icon_url=user.avatar_url,
        )
        embed.add_field(name="【クラバト日数】", value=cb_days, inline=False)
        embed.add_field(name="【達成日時】", value=f"```\n{now_ymd}\n{now_hms}\n```", inline=False)
        await mission_log_channel.send(user.mention, embed=embed)


#########################################
# ポイント集計
async def point_total(message):

    now = datetime.datetime.now()

    guild = client.get_guild(599780162309062706)
    mission_log_channel = guild.get_channel(811059306392715325)  # ミッションログ
    mission_total_channel = guild.get_channel(813091110401605652)  # 集計チャンネル

    clan_member = []
    mission_log_list = []
    mission_point_list = {}
    point_rank_list = []

    if re.search("[0-9]+年[0-9]+月", message.content):
        y = int(re.search("[0-9]+(?=年)", message.content).group())
        m = int(re.search("(?<=年)[0-9]+(?=月)", message.content).group())

    else:
        y = now.year
        m = now.month

    # 集計アナウンス
    embed = discord.Embed(
        title="貢献度ポイントの集計を開始します。",
        description="```py\n\"貢献度ポイント集計中.........\"\n```",
        color=0xffff00
    )
    await message.delete()
    delete_message = await message.channel.send(embed=embed)

    async for message in mission_log_channel.history(limit=5000):
        message_embed = message.embeds[0]
        if f"{y}年{m}月" in message_embed.fields[2].value:
            mission_log_list.append(message)
            member = guild.get_member(message.mentions[0].id)
            if member not in clan_member:
                clan_member.append(member)
        elif any([
            y > int(re.search("[0-9]+(?=年)", message_embed.fields[2].value).group()),
            y > int(re.search("(?<=年)[0-9]+(?=月)", message_embed.fields[2].value).group())
        ]):
            break

    for member in clan_member:
        points = 0
        mission_point_list[member] = points
        for mission_message in mission_log_list:
            message_embed = mission_message.embeds[0]

            if all([
                member.id == mission_message.mentions[0].id,
                f"{y}年{m}月" in message_embed.fields[2].value,
                re.search("(?<=\")[0-9]+(?= )|(?<=\")-[0-9]+(?= )", message_embed.fields[0].value)
            ]):
                get_point = re.search("(?<=\")[0-9]+(?= )|(?<=\")-[0-9]+(?= )", message_embed.fields[0].value).group()
                points += int(get_point)

        mission_point_list[member] = points

    # 集計結果
    rank = 0
    point_x = 0
    count = 0
    for member, point in sorted(mission_point_list.items(), key=lambda i: i[1], reverse=True):
        rank += 1
        if point_x == point:
            rank -= 1
            count += 1
        elif point_x != point:
            rank += count
            count = 0

        embed = discord.Embed(
            title=f"{y}年{m}月の累計ポイントはこちらです》",
            description=f"【クラン内ランキング】\n```py\n{rank}位\n```\n【累計ポイント】\n```py\n{point} pt\n```",
            color=0x00ffff
        )
        embed.set_author(
            name=member.display_name,
            icon_url=member.avatar_url,
        )
        point_x = point
        point_rank_list.append([member, embed])

    for point_total_list in reversed(point_rank_list):
        member, embed = point_total_list
        await mission_total_channel.send(member.mention, embed=embed)

    await asyncio.sleep(180)
    embed = discord.Embed(
        description="全ての集計が完了しました。",
        color=0xffff00
    )
    await delete_message.delete()
    await delete_message.channel.send(embed=embed)


#########################################
# 不人気ボス投票
async def boss_election(payload):
    guild = client.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)

    async for message in channel.history(limit=10):
        if "不人気ボス" in message.content:
            reaction_message = message
            break
    else:
        return

    if payload.member.bot:
        return

    if payload.message_id != reaction_message.id:
        return

    emoji_check = False
    for reaction_emoji in number_emoji:
        if payload.emoji.name == reaction_emoji:
            emoji_check = True
            break

    if not emoji_check:
        return

    if payload.emoji.name == number_emoji[0]:
        for reaction in reaction_message.reactions:
            if reaction.emoji != number_emoji[0]:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)

    if payload.emoji.name == number_emoji[1]:
        for reaction in reaction_message.reactions:
            if reaction.emoji != number_emoji[1]:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)

    if payload.emoji.name == number_emoji[2]:
        for reaction in reaction_message.reactions:
            if reaction.emoji != number_emoji[2]:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)

    if payload.emoji.name == number_emoji[3]:
        for reaction in reaction_message.reactions:
            if reaction.emoji != number_emoji[3]:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)

    if payload.emoji.name == number_emoji[4]:
        for reaction in reaction_message.reactions:
            if reaction.emoji != number_emoji[4]:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)


#########################################
# メッセージの時間削除
async def message_time_delete(delete_message, delete_time):
    await asyncio.sleep(delete_time)
    await delete_message.delete()


#########################################
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
    await message.channel_0.send(embed=embed)


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

    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    channel = client.get_channel(741851542503817226)  # メッセージログ
    channel_1 = client.get_channel(payload.channel_id)
    edit_message = await channel_1.fetch_message(payload.message_id)

    if edit_message.author.bot:
        return

    async for message in channel.history(limit=50):
        if message.embeds:
            embed = message.embeds[0]

            if any([
                "書き込み" == embed.fields[0].value,
                "メッセージ編集" == embed.fields[0].value
            ]):

                try:
                    if all([
                        int(edit_message.id) == int(embed.fields[6].value),
                        edit_message.content == embed.fields[7].value
                    ]):
                        return

                    elif all([
                        int(edit_message.id) == int(embed.fields[6].value),
                        edit_message.content != embed.fields[7].value
                    ]):
                        break
                except (IndexError):
                    pass

                else:
                    pass

    embed = discord.Embed(title="【メッセージログ】", color=0xffd700)
    embed.add_field(name="イベント内容≫", value="メッセージ編集", inline=False)
    embed.add_field(name="アカウント名≫", value=edit_message.author.mention, inline=False)
    embed.add_field(name="ニックネーム》", value=edit_message.author.display_name, inline=False)
    embed.add_field(name="ユーザーID》", value=edit_message.author.id, inline=False)
    embed.add_field(name="日時》", value=f"{now_ymd} {now_hms}", inline=False)
    embed.add_field(name="チャンネル》", value=edit_message.channel.mention, inline=False)
    embed.add_field(name="メッセージID》", value=edit_message.id, inline=False)

    if edit_message.content:
        embed.add_field(name="メッセージ内容》", value=edit_message.content, inline=False)

    if edit_message.attachments and edit_message.attachments[0].proxy_url:
        img_urls = []
        x = 1
        for img in edit_message.attachments:
            img_urls.append(f"[ファイル {x}]({img.proxy_url})")
            x += 1

        embed.set_image(
            url=edit_message.attachments[0].proxy_url
        )
        embed.add_field(name="添付ファイル一覧》", value="\n".join(img_urls), inline=False)

    await channel.send(embed=embed)


# メッセージ削除
@client.event
async def on_raw_message_delete(payload):
    await message_delete_event(payload)

async def message_delete_event(payload):
    CHANNEL_ID = 741851542503817226
    channel = client.get_channel(CHANNEL_ID)
    delete_message_channel = client.get_channel(payload.channel_id)
    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    delete_message_id = payload.message_id

    async for message in channel.history(limit=1000):
        get_messeag_log = False
        if message.embeds:
            embed = message.embeds[0]

            try:
                if int(delete_message_id) == int(embed.fields[6].value):
                    get_messeag_log = True
                    embed.color = 0xff0000
                    embed.set_field_at(
                        0,
                        name="イベント内容≫",
                        value="```py\n\"このメッセージは削除されました。\"\n```",
                        inline=False
                    )
                    embed.set_field_at(
                        4,
                        name="日時》",
                        value=f"{now_ymd} {now_hms}",
                        inline=False
                    )
                    break
            except (AttributeError, IndexError):
                pass

    if not get_messeag_log:
        embed = discord.Embed(title="【メッセージログ】", color=0xff0000)
        embed.add_field(name="イベント内容≫", value="```py\n\"bot自身のメッセージが削除されました。\"\n```", inline=False)
        embed.add_field(name="日時》", value=f"{now_ymd} {now_hms}", inline=False)
        embed.add_field(name="チャンネル》", value=delete_message_channel.mention, inline=False)
        embed.add_field(name="メッセージID》", value=payload.message_id, inline=False)

    await channel.send(embed=embed)


# BOTの起動
@client.event
async def on_ready():
    global clan_battle_start_date
    global clan_battle_end_date
    global now_boss_data
    global now_clan_battl_message
    global boss_name
    global boss_img_url

    boss_name.clear()
    boss_img_url.clear()
    guild = client.get_guild(599780162309062706)
    channel_bot_log = guild.get_channel(741851480868519966)  # 動作ログ
    boss_data_channel = guild.get_channel(784763031946264576)  # ボス情報

    now = datetime.datetime.now()
    clan_battle_start_date, clan_battle_end_date = get_clanbattle_date(now.year, now.month)
    clan_battle_start_date = datetime.datetime.strptime(clan_battle_start_date, "%Y-%m-%d %H:%M")
    clan_battle_end_date = datetime.datetime.strptime(clan_battle_end_date, "%Y-%m-%d %H:%M")

    if all([
        now.strftime('%Y-%m-%d %H:%M') >= clan_battle_start_date.strftime('%Y-%m-%d %H:%M'),
        now.strftime('%Y-%m-%d %H:%M') < clan_battle_end_date.strftime('%Y-%m-%d %H:%M')
    ]):
        clan_battle_tutorial_days = False
        text_1 = "現在クランバトル開催中です。"

    else:
        clan_battle_tutorial_days = True
        text_1 = "現在クランバトル期間外です。"

    for channel_id in boss_ch:
        channel = client.get_channel(channel_id)
        boss_name.append(re.sub(r"[0-9]ボス》", "", channel.name))

    boss_names = "【現在のボス名】"
    for name in boss_name:
        boss_names += f"\n{name}"

        async for message in boss_data_channel.history():
            if f"\n{name}\n" in message.content:
                boss_img_url.append(message.attachments[0].proxy_url)
                break

    ch_id_index_y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][ch_id_index_y]))  # 進捗状況

    async for message in channel_0.history(limit=10):
        if message.embeds:
            if re.search(r"[0-9]+月度クランバトル", message.embeds[0].title):
                now_clan_battl_message = message
                text = message.embeds[0].description

                # 現在ボスインデックス取得
                x = 0
                for boss in boss_name:

                    if boss in text:
                        now_boss_data["now_boss"] = x
                        break
                    x += 1

                text = text.replace(",", "")
                now_boss_data["now_lap"] = re.search(r"[0-9]+週目", text).group().replace("週目", "")
                now_boss_data["now_boss_hp"] = re.search(r"[0-9]+/", text).group().replace("/", "")

                break

    # ボス段階取得
    if 1 <= int(now_boss_data["now_lap"]) < 4:
        now_boss_data["now_boss_level"] = 1

    elif 4 <= int(now_boss_data["now_lap"]) < 11:
        now_boss_data["now_boss_level"] = 2

    elif 11 <= int(now_boss_data["now_lap"]) < 35:
        now_boss_data["now_boss_level"] = 3

    elif 35 <= int(now_boss_data["now_lap"]) < 45:
        now_boss_data["now_boss_level"] = 4

    elif 45 <= int(now_boss_data["now_lap"]):
        now_boss_data["now_boss_level"] = 5

    async for message in channel_0.history(limit=20):
        if message.id == now_clan_battl_message.id:
            break
        else:
            await message.delete()

    text_2 = f"{clan_battle_start_date.strftime('%Y-%m-%d %H:%M')}\n{clan_battle_end_date.strftime('%Y-%m-%d %H:%M')}"
    await channel_bot_log.send(f"ミネルヴァ起動しました。\n\n{text_1}\n{text_2}\n\n{boss_names}")


@client.event
async def on_member_join(member):

    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    guild = client.get_guild(599780162309062706)
    new_member_role = guild.get_role(741896658408964108)

    member_log_ch = 741851689916825630
    channel = client.get_channel(member_log_ch)
    embed = discord.Embed(title="【新メンバー情報】", color=0x00ffee)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name="アカウント名≫", value=member.mention, inline=False)
    embed.add_field(name="ニックネーム》", value=member.display_name, inline=False)
    embed.add_field(name="ユーザーID》", value=member.id, inline=False)
    embed.add_field(name="サーバー入室日時》", value=f"{now_ymd} {now_hms}", inline=False)
    await channel.send(embed=embed)
    await member.add_roles(new_member_role)


# サーバー案内ルール既読チェック
async def server_rule_reaction_check(payload):
    guild = client.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    general_member_role = guild.get_role(687433546775789770)  # 一般メンバーロール

    # サーバー案内
    if channel.id == 749511208104755241:
        if payload.emoji.name == "\U00002705":

            delete_message = await channel.send(f"""
{payload.member.mention} さん　こんにちわ。
黒猫魔法学院への加入ありがとうございます。

リアクションの確認が取れましたので、各種機能の制限を解除しました。
改めまして今月よりよろしくお願いします。""")

            await payload.member.add_roles(general_member_role)

            await asyncio.sleep(60)
            await delete_message.delete()


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


# 時間処理
@tasks.loop(seconds=30)
async def loop():
    try:
        global no_attack_role_reset
        global clan_battle_tutorial_days
        global now_boss_data

        await client.wait_until_ready()

        set_rollover_time = rollover_time
        now = datetime.datetime.now()

        guild = client.get_guild(599780162309062706)
        announce_channel = guild.get_channel(599784496866263050)  # 連絡事項

        if "" != clan_battle_start_date and "" != clan_battle_end_date:
            if all([
                now.strftime('%Y-%m-%d %H:%M') >= clan_battle_start_date.strftime('%Y-%m-%d %H:%M'),
                now.strftime('%Y-%m-%d %H:%M') < clan_battle_end_date.strftime('%Y-%m-%d %H:%M')
            ]):
                clan_battle_tutorial_days = False

            else:
                clan_battle_tutorial_days = True

        else:
            return

        if all([
            now.day == 5,
            now.strftime('%H:%M') == "00:00",
            now.strftime('%H:%M:%S') <= "00:00:30"
        ]):

            t_start_date = datetime.datetime.strptime(clan_battle_start_date.strftime('%Y-%m-5 %H:%M'), "%Y-%m-%d %H:%M")
            t_end_date = datetime.datetime.strptime(clan_battle_start_date.strftime('%Y-%m-%d 00:00'), "%Y-%m-%d %H:%M")
            announce_messeage = f"""
    <@&687433139345555456>
    本日5時よりクラバト開催前日までの期間中、凸管理システムの模擬操作期間となります。
    軽微なアップデートも行っているため、必ず全員一通り操作しておいてください。

    <@&687433546775789770>
    クラメン以外でもし触れてみたい人が居ましたら連絡ください。

    <#785864497583358012>
    こちらのチャンネルにクラバト期間中の操作法を記載しております。
    `必ずクラバト前までに実際に模擬操作して`慣れておいて下さい。
    《模擬操作は以下のチャンネルを使用します》
    （一番下の「凸管理チュートリアル」のカテゴリーです）

    <#750345732497735782> `（クラバト期間外専用チャンネル）`
    ┗進行の相談はこちら
    <#750345928678047744> `（クラバト期間外専用チャンネル）`
    ┗凸宣言はこちらから
    <#750345983661047949> `（クラバト期間外専用チャンネル）`
    ┗凸終了後、ログが記録されます
    <#774871889843453962> `（クラバト期間外専用チャンネル）`
    ┗持ち越しの状況です
    <#750346096156344450> `（クラバト期間外専用チャンネル）`
    ┗1凸毎の残り凸状況のメンバーリストです
    <#750351148841566248> `（クラバト期間外専用チャンネル）`
    ┗タスキルリアクションをすると書き込まれます。

    【模擬操作期間】
    ```py
    《開始》
    ┗{t_start_date.month}月{t_start_date.day}日 {t_start_date.hour}時{t_start_date.minute}分
    《終了》
    ┗{t_end_date.month}月{t_end_date.day}日 {t_end_date.hour}時{t_end_date.minute}分
    ```
    【クラバト開催予定日】
    ```py
    《開始》
    ┗{clan_battle_start_date.month}月{clan_battle_start_date.day}日 {clan_battle_start_date.hour}時{clan_battle_start_date.minute}分
    《終了》
    ┗{clan_battle_end_date.month}月{clan_battle_end_date.day}日 {clan_battle_end_date.hour}時{clan_battle_end_date.minute}分
    ```"""

            await announce_channel.send(announce_messeage)

        if any([
            all([
                now.day >= 5,
                now.strftime('%Y-%m-%d %H:%M') < clan_battle_start_date.strftime("%Y-%m-%d 00:00")
            ]),
            all([
                now.strftime('%Y-%m-%d %H:%M') >= clan_battle_start_date.strftime('%Y-%m-%d %H:%M'),
                now.strftime('%Y-%m-%d %H:%M') < clan_battle_end_date.strftime('%Y-%m-%d %H:%M')
            ])
        ]):

            # クラバト初日設定
            if any([
                all([now.day == 5, now.strftime('%H:%M') == set_rollover_time]),
                now.strftime('%Y-%m-%d %H:%M') == clan_battle_start_date.strftime('%Y-%m-%d %H:%M')
            ]):

                await clan_battl_start_up()

            # 日付変更リセット
            elif now.strftime('%H:%M') == set_rollover_time:

                if now_attack_list:
                    no_attack_role_reset = False
                    return

                else:
                    await clan_battl_role_reset(now)
                    no_attack_role_reset = True

        # クラバト終了処理
        if any([
            now.strftime('%Y-%m-%d %H:%M') == clan_battle_start_date.strftime("%Y-%m-%d 00:00"),
            now.strftime('%Y-%m-%d %H:%M') == clan_battle_end_date.strftime('%Y-%m-%d %H:%M')
        ]):

            if now_attack_list:
                no_attack_role_reset = False
                return

            else:
                await clan_battl_role_reset(now)
                no_attack_role_reset = True

        else:
            pass

    except Exception as e:
        await error_log(e_name=e.__class__.__name__, e_log=traceback.format_exc())

loop.start()


# リアクション操作
@client.event
async def on_raw_reaction_add(payload):
    try:
        now = datetime.datetime.now()
        guild = client.get_guild(599780162309062706)
        y = 0 if clan_battle_tutorial_days is True else 1
        battle_log_channel = guild.get_channel(int(clan_battle_channel_id[3][y]))  # バトルログ

        # サーバー案内チャンネルチェック
        if payload.channel_id == 749511208104755241:
            await server_rule_reaction_check(payload)

        # クラバト管理リアクション
        if payload.message_id == now_clan_battl_message.id:
            await clan_battl_call_reaction(payload)

        # バトルログ編集
        if payload.channel_id == battle_log_channel.id:
            await battle_log_add_information(payload)

        # クラバトミッション
        boss = 0
        ok_emoji = client.get_emoji(682357586062082083)
        for channel in boss_ch:
            if all([
                payload.member.id == 490682682880163850,
                payload.channel_id == channel,
                payload.emoji == ok_emoji
            ]):
                channel = client.get_channel(payload.channel_id)
                reaction_message = await channel.fetch_message(payload.message_id)
                for channel in boss_ch:
                    boss += 1
                    if payload.channel_id == channel:
                        await cb_mission(clear_missions=[f"mb_00{boss}"], user=reaction_message.author, clear_time=now)

        # 不人気ボス投票
        if payload.channel_id == 814132872045920257:
            await boss_election(payload)

    except Exception as e:
        await error_log(e_name=e.__class__.__name__, e_log=traceback.format_exc())


# リアクション操作
@client.event
async def on_raw_reaction_remove(payload):
    try:
        # 凸宣言キャンセル
        await clan_battl_clear_reaction(payload)

    except Exception as e:
        await error_log(e_name=e.__class__.__name__, e_log=traceback.format_exc())


@client.event
async def on_message(message):
    try:
        # BOT無視
        if message.author.bot:
            return

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

            if r.startswith("/集計"):
                await point_total(message)

            if message.channel.id == 814132872045920257:
                for reactiones in number_emoji:
                    await message.add_reaction(reactiones)

        # クラバトコマンド
            if "/残り凸状況" in message.content:
                no_attack_member_list_ch = message.channel
                await clan_battl_no_attack_member_list(no_attack_member_list_ch)
                await message.delete()

            if "/リセット" in message.content:
                await clan_battl_start_up()

            if "/edit_boss" in message.content:
                await clan_battl_edit_progress(message)

        # メッセージリンク展開
        await dispand(message)

        # 持ち越し時間算出
        await ok_time_plt(message)

        # 持ち越し時間用ＴＬ改変
        await ok_tl_edit(message)

        # パンツ交換
        if message.channel.id != 804272119982718978:
            await pants_trade(message)

        # メッセージログ
        await new_message(message)

    except Exception as e:
        await error_log(e_name=e.__class__.__name__, e_log=traceback.format_exc())

client.run(TOKEN)
