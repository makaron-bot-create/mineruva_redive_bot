import os
import discord
from discord import Embed
from discord.ext import tasks
import re
import datetime
from datetime import timedelta
import io
import aiohttp
import asyncio


# BOTのトークン
TOKEN = os.environ['DISCORD_BOT_TOKEN']
# 接続に必要なオブジェクトを生成
client = discord.Client()

# オプション ################
pants_url = [
    "https://media.discordapp.net/attachments/599780162313256961/721356018789122104/127_20200613222952.png",
    "https://media.discordapp.net/attachments/599780162313256961/721356052083245086/127_20200613223037.png"
]
# 変数 ######################
kick_cmd = False
clan_battle_member_role_id = [
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
    [750346096156344450, 695958348264374343]  # 残り凸状況
]
BOSS_Ch = [680753487629385739, 680753616965206016, 680753627433795743, 680753699152199680, 680754056477671439]
BOSS_name = ["BOSS_1", "BOSS_2", "BOSS_3", "BOSS_4", "BOSS_5"]
clan_battle_days = ["2020/12/26 05:00", "2020/12/31 00:00"]
BOSS_lv = [1, 4, 11, 35]
BOSS_HP = [
    [6000000, 6000000, 7000000, 15000000],
    [8000000, 8000000, 9000000, 16000000],
    [10000000, 10000000, 13000000, 18000000],
    [12000000, 12000000, 15000000, 19000000],
    [15000000, 15000000, 20000000, 20000000]
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
BOSS_HP_check = 0
now_clan_battl_message = None
new_boss_check = False
ok_member = False
no_attack_role_reset = True
add_role_check = False
rollover_time = "05:00"


# 凸宣言絵文字リスト
emoji_list = {
    "attack_p": "\U00002694\U0000fe0f",
    "attack_m": "\U0001f9d9",
    "T_kill": "\U0001f502",
    "SOS": "\U0001f198",
    "attack_end": "\U00002705"
}

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

#############################
# メッセージリンク検知
regex_discord_message_url = (
    'https://(ptb.|canary.)?discord(app)?.com/channels/'
    '(?P<guild>[0-9]{18})/(?P<channel>[0-9]{18})/(?P<message>[0-9]{18})'
)


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
        boss = BOSS_name[x]

        message_description = f"{role_m.mention}\n\n {int(M)}月の{x + 1}ボスは『{BOSS_name[x]}』です。\nよろしくお願いします。"
        embed = await boss_description(boss)
        await channel.edit(name=r)
        await channel.send(message_description, embed=embed)
        BOSS_names += channel.mention + "\n"
        x += 1

    await message.delete()
    await message.channel.send(BOSS_names)

# ボス説明
async def boss_description(boss):
    boss_data_ch = 784763031946264576
    channel_0 = client.get_channel(boss_data_ch)

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
# スタートアップ
async def clan_battl_start_up():
    global now_boss_data

    now_boss_data["now_lap"] = 1
    now_boss_data["now_boss_level"] = 1
    now_boss_data["now_boss"] = 0
    now_boss_data["now_boss_hp"] = int(BOSS_HP[0][0])

    await clan_battl_role_reset()


# 編成登録
async def battle_log_add_information(payload):
    guild = client.get_guild(599780162309062706)
    add_information_reaction_name = "\U0001f4dd"  # メモ絵文字
    channel = guild.get_channel(payload.channel_id)

    y = 0 if clan_battle_tutorial_days is True else 1
    battle_log_channel = guild.get_channel(int(clan_battle_channel_id[3][y]))  # バトルログ
    reaction_message = await channel.fetch_message(payload.message_id)

    if any([
        payload.member.bot,
        not reaction_message.mentions
    ]):
        return

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
        await asyncio.sleep(1)
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


# 残り凸メンバーリスト
async def clan_battl_no_attack_member_list(no_attack_member_list_ch):
    guild = client.get_guild(599780162309062706)
    channel = no_attack_member_list_ch

    nl = "\n"
    now = datetime.datetime.now()
    set_rollover_time = rollover_time
    clan_battle_start_day = datetime.datetime.strptime(clan_battle_days[0], "%Y/%m/%d %H:%M")

    start_y = clan_battle_start_day.year
    start_m = clan_battle_start_day.month
    start_d = clan_battle_start_day.day
    now_y = now.year
    now_m = now.month
    now_d = now.day
    cb_day = (datetime.date(now_y, now_m, now_d) - datetime.date(start_y, start_m, start_d) + timedelta(days=1)).days

    if datetime.datetime.now().strftime("%H:%M") < set_rollover_time:
        cb_day = cb_day - 1

    OK_n = guild.get_role(clan_battle_member_role_id[0]).members
    noattack_member_list_0 = f"```{nl}{nl.join([member.display_name for member in OK_n])}{nl}```"

    attack_3 = guild.get_role(clan_battle_member_role_id[1]).members
    noattack_member_list_3 = f"```{nl}{nl.join([member.display_name for member in attack_3])}{nl}```"

    attack_2 = guild.get_role(clan_battle_member_role_id[2]).members
    noattack_member_list_2 = f"```{nl}{nl.join([member.display_name for member in attack_2])}{nl}```"

    attack_1 = guild.get_role(clan_battle_member_role_id[3]).members
    noattack_member_list_1 = f"```{nl}{nl.join([member.display_name for member in attack_1])}{nl}```"

    attack_members = (len(attack_3) * 3) + (len(attack_2) * 2) + len(attack_1)

    if attack_members == 0 and len(OK_n) == 0:
        description_text = "本日のクランバトルは全員終了しました。"

    else:
        description_text = f"残り凸数》\n{attack_members} 凸\n持ち越し残り凸》\n{len(OK_n)} 人"

    embed = discord.Embed(
        title=f"【{now.month}月度クランバトル day {cb_day}】",
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
async def no_attack_role_check(payload):
    guild = client.get_guild(599780162309062706)

    y = 0 if clan_battle_tutorial_days is True else 1
    channel = guild.get_channel(int(clan_battle_channel_id[0][y]))  # 進捗状況
    reaction_message = await channel.fetch_message(payload.message_id)

    # ロールの判定
    ok_role_check = False
    attack_role_check = False
    for role in payload.member.roles:
        if role.id == clan_battle_member_role_id[0]:
            ok_role_check = True

        elif role.id == clan_battle_member_role_id[1]:
            attack_role_check = True

        elif role.id == clan_battle_member_role_id[2]:
            attack_role_check = True

        elif role.id == clan_battle_member_role_id[3]:
            attack_role_check = True

    if not attack_role_check and not ok_role_check:
        for reaction in reaction_message.reactions:

            async for user in reaction.users():
                if user == payload.member:
                    await reaction.remove(user)

        await channel.send(f"{payload.member.mention}》\n本日の3凸は終了してます。")

    return attack_role_check, ok_role_check


# 未凸ロールの更新
async def add_attack_role(BOSS_HP_check_message):
    global ok_member

    guild = client.get_guild(599780162309062706)
    BOSS_HP_check_member = BOSS_HP_check_message.author

    for role in BOSS_HP_check_member.roles:
        if role.id == clan_battle_member_role_id[1]:
            attak_role = guild.get_role(clan_battle_member_role_id[1])
            await BOSS_HP_check_member.remove_roles(attak_role)

            attak_role = guild.get_role(clan_battle_member_role_id[2])
            await BOSS_HP_check_member.add_roles(attak_role)
            break

        elif role.id == clan_battle_member_role_id[2]:
            attak_role = guild.get_role(clan_battle_member_role_id[2])
            await BOSS_HP_check_member.remove_roles(attak_role)

            attak_role = guild.get_role(clan_battle_member_role_id[3])
            await BOSS_HP_check_member.add_roles(attak_role)
            break

        elif role.id == clan_battle_member_role_id[3]:
            attak_role = guild.get_role(clan_battle_member_role_id[3])
            await BOSS_HP_check_member.remove_roles(attak_role)
            break


# 残り凸ロールリセット
async def clan_battl_role_reset():
    global add_role_check
    global no_attack_role_reset
    global now_attack_list

    guild = client.get_guild(599780162309062706)
    channel = client.get_channel(741851480868519966)  # ミネルヴァ・動作ログ
    now_attack_list.clear()

    y = 0 if clan_battle_tutorial_days is True else 1
    no_attack_member_list_ch = guild.get_channel(int(clan_battle_channel_id[5][y]))  # 残り凸状況

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
            attack_3 = len(guild.get_role(clan_battle_member_role_id[1]).members) * 3
            attack_2 = len(guild.get_role(clan_battle_member_role_id[2]).members) * 2
            attack_1 = len(guild.get_role(clan_battle_member_role_id[3]).members)
            OK_n = len(guild.get_role(clan_battle_member_role_id[0]).members)

            attack_n = attack_3 + attack_2 + attack_1

            now_lap = now_boss_data["now_lap"]
            now_boss_level = now_boss_data["now_boss_level"]
            boss_name_index = int(now_boss_data["now_boss"])

            now_hp = "{:,}".format(int(now_boss_data["now_boss_hp"]))
            x = int(now_boss_data["now_boss"])
            y = int(now_boss_data["now_boss_level"]) - 1
            BOSS_MAX_HP = "{:,}".format(int(BOSS_HP[x][y]))

            description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
━━━━━━━━━━━━━━━━━━━━
{now_lap}週目
{now_boss_level}段階目
{BOSS_name[boss_name_index]}
{now_hp}/{BOSS_MAX_HP}
━━━━━━━━━━━━━━━━━━━━"""

            now = datetime.datetime.now()
            now_ymd = f"{now.year}年{now.month}月{now.day}日"
            now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

            embed.description = description_text
            embed.clear_fields()
            embed.add_field(name="【終了時間】", value=f"{now_ymd}\n{now_hms}", inline=False)

            # 終了したボス情報メッセージのリアクション削除
            await edit_message.clear_reactions()
            await edit_message.edit(embed=embed)

    clan_member_role = guild.get_role(687433139345555456)   # クラメンロール
    clan_member = clan_member_role.members
    for member in clan_member:
        await member.add_roles(guild.get_role(clan_battle_member_role_id[1]))

    if guild.get_role(clan_battle_member_role_id[0]).members:
        for member in guild.get_role(clan_battle_member_role_id[0]).members:
            await member.remove_roles(guild.get_role(clan_battle_member_role_id[0]))

    if guild.get_role(clan_battle_member_role_id[2]).members:
        for member in guild.get_role(clan_battle_member_role_id[2]).members:
            await member.remove_roles(guild.get_role(clan_battle_member_role_id[2]))

    if guild.get_role(clan_battle_member_role_id[3]).members:
        for member in guild.get_role(clan_battle_member_role_id[3]).members:
            await member.remove_roles(guild.get_role(clan_battle_member_role_id[3]))

    await channel.send(f"クランメンバーに「未3凸」ロールを付与しました。\n{datetime.datetime.now()}")
    await clan_battl_no_attack_member_list(no_attack_member_list_ch)
    await clan_battle_event()


# 進捗状況更新
async def clan_battle_event():
    global now_clan_battl_message
    global BOSS_name
    global BOSS_HP
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
    clan_battle_start_day = datetime.datetime.strptime(clan_battle_days[0], "%Y/%m/%d %H:%M")

    start_y = clan_battle_start_day.year
    start_m = clan_battle_start_day.month
    start_d = clan_battle_start_day.day
    now_y = now.year
    now_m = now.month
    now_d = now.day
    cb_day = (datetime.date(now_y, now_m, now_d) - datetime.date(start_y, start_m, start_d) + timedelta(days=1)).days

    if cb_day < 0:
        cb_day_text = f"__**クラバト開催前**__（{abs(cb_day)}日前）"
    else:
        if datetime.datetime.now().strftime("%H:%M") < set_rollover_time:
            cb_day = cb_day - 1
            cb_day_text = f"__**{abs(cb_day)}日目**__"

    guild = client.get_guild(599780162309062706)

    y = 0 if clan_battle_tutorial_days is True else 1
    channel = guild.get_channel(int(clan_battle_channel_id[0][y]))  # 進捗状況

    clan_member_mention = "クランメンバー" if clan_battle_tutorial_days is True else guild.get_role(687433139345555456)  # クランメンバーロール

    attack_3 = len(guild.get_role(clan_battle_member_role_id[1]).members) * 3
    attack_2 = len(guild.get_role(clan_battle_member_role_id[2]).members) * 2
    attack_1 = len(guild.get_role(clan_battle_member_role_id[3]).members)
    OK_n = len(guild.get_role(clan_battle_member_role_id[0]).members)
    attack_n = attack_3 + attack_2 + attack_1

    now_lap = now_boss_data["now_lap"]
    now_boss_level = now_boss_data["now_boss_level"]
    boss_name_index = int(now_boss_data["now_boss"])

    now_hp = "{:,}".format(int(now_boss_data["now_boss_hp"]))
    x = int(now_boss_data["now_boss"])
    y = int(now_boss_data["now_boss_level"]) - 1
    BOSS_MAX_HP = "{:,}".format(int(BOSS_HP[x][y]))

    description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
━━━━━━━━━━━━━━━━━━━━
{now_lap}週目
{now_boss_level}段階目
{BOSS_name[boss_name_index]}
{now_hp}/{BOSS_MAX_HP}
━━━━━━━━━━━━━━━━━━━━"""

    # メッセージを書きます
    nl = "\n"
    embed = discord.Embed(
        title=f"【{now.month}月度クランバトル {cb_day_text}】",
        description=description_text,
        color=0x00b4ff
    )

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

    mention_text = f"{clan_member_mention}\n{now_lap}週目 {BOSS_name[boss_name_index]}"
    now_clan_battl_message = await channel.send(mention_text, embed=embed)

    for reactiones in emoji_list.values():
        await now_clan_battl_message.add_reaction(reactiones)


# 凸管理リアクションイベント
async def clan_battl_call_reaction(payload):
    global BOSS_HP_check
    global now_attack_list
    global now_clan_battl_message
    global now_boss_data
    global new_boss_check
    global ok_member

    nl = "\n"
    hp_fomat = "{:,}"
    ok_attack_text = ""
    ok_attack_check = False
    last_attack_text = ""
    carry_over_time_message = ""
    carry_over_time = ""

    guild = client.get_guild(599780162309062706)
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
    x = int(now_boss_data["now_boss"])
    y = int(now_boss_data["now_boss_level"]) - 1
    BOSS_MAX_HP_NOW = "{:,}".format(int(BOSS_HP[x][y]))

    edit_message = now_clan_battl_message
    reac_member = payload.member
    guild = client.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    reaction_message = await channel.fetch_message(payload.message_id)

    if reac_member.bot:
        return

    if channel.id == int(clan_battle_channel_id[0][ch_id_index_y]):  # 進捗状況
        attack_role_check, ok_role_check = await no_attack_role_check(payload)

        if not attack_role_check and not ok_role_check:
            return

        if ok_role_check:
            # 持ち越し時間
            async for message in channel_4.history():
                if payload.member.mention in message.content:
                    carry_over_time = re.search(r"[0-9]:[0-9]{2}", message.content).group()
                    break

            ok_attack_text = f"__**（持ち越し凸）{carry_over_time}**__"

        if payload.emoji.name == emoji_list["attack_p"]:
            now_attack_list[payload.member] = f"《物理編成》{ok_attack_text}"

            for reaction in reaction_message.reactions:
                if reaction.emoji == emoji_list["attack_m"]:

                    async for user in reaction.users():

                        if user == payload.member:
                            await reaction.remove(user)

            await channel_1.send(f"{reac_member.display_name}》\n「物理編成」{ok_attack_text}で入りました。")
            await channel_0.send(f"{reac_member.mention}》\n凸宣言を受け付けました。")

        elif payload.emoji.name == emoji_list["attack_m"]:
            now_attack_list[payload.member] = f"《魔法編成》{ok_attack_text}"

            for reaction in reaction_message.reactions:
                if reaction.emoji == emoji_list["attack_p"]:

                    async for user in reaction.users():

                        if user == payload.member:
                            await reaction.remove(user)

            await channel_1.send(f"{reac_member.display_name}》\n「魔法編成」{ok_attack_text}で入りました。")
            await channel_0.send(f"{reac_member.mention}》\n凸宣言を受け付けました。")

        elif payload.emoji.name == emoji_list["T_kill"]:
            await channel_2.send(f"{reac_member.display_name}》\nタスキルしました。")

        elif payload.emoji.name == emoji_list["SOS"]:
            await channel_1.send(f"「{reac_member.display_name}」さんが救援を求めてます。")
            return

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
                await asyncio.sleep(10)
                await not_reaction_message.delete()
                return

            await channel_0.set_permissions(reac_member, send_messages=True)
            dmg_input_announce_message = await channel_0.send(f"""
{reac_member.mention}》
ボスに与えたダメージを「半角数字」のみで入力してください。

※ボスを倒した場合は「__{hp_fomat.format(int(now_boss_data['now_boss_hp']))}__」以上で入力してください。""")

            def attack_dmg_message_check(message):
                return all([
                    message.content.isdecimal() is True,
                    message.channel == channel_0,
                    message.author.id == payload.user_id,
                    not message.author.bot
                ])

            try:
                BOSS_HP_check_message = await client.wait_for('message', check=attack_dmg_message_check, timeout=90)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="タイムアウトエラー",
                    description=timeouterror_text,
                    colour=0xff0000
                )
                await dmg_input_announce_message.delete()
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

            async for message in channel_0.history(limit=10):
                if not message.embeds:
                    await message.delete()

                else:
                    break

            # 残り体力計算
            last_boss_hp = int(now_boss_data["now_boss_hp"]) - int(BOSS_HP_check_message.content)
            true_dmg = ""
            now_hp = 0
            if 0 >= last_boss_hp:
                ok_attack_check = True
                true_dmg = "" if last_boss_hp == 0 else f"\n　　({hp_fomat.format(int(now_boss_data['now_boss_hp']))})"
                if not ok_role_check:

                    time_input_announce_message = await channel_0.send(f"""
{reac_member.mention}》
持ち越し時間を入力してください、持ち越しメモに反映します。

※入力は全て「半角」にて「__**0:21～1:30**__」の範囲でお願いします。
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

                        await asyncio.sleep(10)
                        await timeout_message.delete()
                        return

                async for message in channel_0.history(limit=10):
                    if not message.embeds:
                        await message.delete()

                    else:
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

                    elif 35 <= int(now_boss_data["now_lap"]):
                        now_boss_data["now_boss_level"] = 4

                x = int(now_boss_data["now_boss"])
                y = int(now_boss_data["now_boss_level"]) - 1
                now_boss_data["now_boss_hp"] = int(BOSS_HP[x][y])

            for role in BOSS_HP_check_message.author.roles:
                if role.id == int(clan_battle_member_role_id[0]):
                    ok_role_check = True
                    attak_role = guild.get_role(int(clan_battle_member_role_id[0]))

                    # 持ち越しメッセージの削除
                    async for message in channel_4.history():
                        if BOSS_HP_check_message.author.mention in message.content:
                            carry_over_time = re.search(r"[0-9]:[0-9]{2}", message.content).group()

                            await message.delete()
                            break

                    await BOSS_HP_check_message.author.remove_roles(attak_role)
                    break

            if all([
                ok_attack_check,
                not ok_role_check
            ]):

                attak_role = guild.get_role(int(clan_battle_member_role_id[0]))
                await BOSS_HP_check_message.author.add_roles(attak_role)

            if 0 < last_boss_hp:
                now_boss_data["now_boss_hp"] = last_boss_hp
                now_hp = "{:,}".format(int(now_boss_data["now_boss_hp"]))

            dmg = "{:,}".format(int(BOSS_HP_check_message.content))
            battle_log = f"""
{now_lap}週目・{now_boss_level}段階目
{BOSS_name[boss_name_index]}
{BOSS_HP_check_message.author.mention}
({BOSS_HP_check_message.author.display_name})
┣{now_attack_list[BOSS_HP_check_message.author]}{last_attack_text}
┗ダメージ》
　┗{dmg}{true_dmg}"""

            embed = discord.Embed(
                description=battle_log,
                color=0x00b4ff
            )

            if carry_over_time_message:
                attak_type = re.sub(r"[《》]", "", now_attack_list[BOSS_HP_check_message.author])
                carry_over_time = re.match(r"[0-9]:[0-9]{2}", carry_over_time_message.content).group()

                last_attack_message = f"""
{BOSS_HP_check_message.author.mention}》
{now_lap}週目・{now_boss_level}段階目
{BOSS_name[boss_name_index]}
┃
┣┳ラスアタ時の編成
┃┗{attak_type}
┃
┗┳持ち越し時間
　┗__**{carry_over_time}**__"""

            # 凸宣言リアクションリセット
            for reaction in reaction_message.reactions:
                # 物理編成、凸宣言リアクションリセット
                if reaction.emoji == emoji_list["attack_p"]:
                    async for user in reaction.users():
                        if user == BOSS_HP_check_message.author:
                            await reaction.remove(user)

                # 魔法編成、凸宣言リアクションリセット
                if reaction.emoji == emoji_list["attack_m"]:
                    async for user in reaction.users():
                        if user == BOSS_HP_check_message.author:
                            await reaction.remove(user)

                # 凸終了宣言リアクションリセット
                if reaction.emoji == emoji_list["attack_end"]:
                    async for user in reaction.users():
                        if user == BOSS_HP_check_message.author:
                            await reaction.remove(user)

            if not ok_role_check:
                await add_attack_role(BOSS_HP_check_message)

            if ok_attack_check:
                now_attack_list.clear()
            elif not ok_attack_check:
                del now_attack_list[BOSS_HP_check_message.author]

            await channel_0.set_permissions(BOSS_HP_check_message.author, overwrite=None)
            await clan_battl_no_attack_member_list(no_attack_member_list_ch)
            await channel_1.send(f"{BOSS_HP_check_message.author.display_name}》\n凸が終了しました。")
            battl_log_message = await channel_3.send(BOSS_HP_check_message.author.mention, embed=embed)
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
        attack_3 = len(guild.get_role(clan_battle_member_role_id[1]).members) * 3
        attack_2 = len(guild.get_role(clan_battle_member_role_id[2]).members) * 2
        attack_1 = len(guild.get_role(clan_battle_member_role_id[3]).members)
        OK_n = len(guild.get_role(clan_battle_member_role_id[0]).members)

        attack_n = attack_3 + attack_2 + attack_1

        description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
━━━━━━━━━━━━━━━━━━━━
{now_lap}週目
{now_boss_level}段階目
{BOSS_name[boss_name_index]}
{now_hp}/{BOSS_MAX_HP_NOW}
━━━━━━━━━━━━━━━━━━━━"""

        embed = edit_message.embeds[0]
        embed.description = description_text
        embed.set_field_at(
            0,
            name="【現在本戦中メンバー】",
            value=member_list,
            inline=False
        )

        if 0 == now_hp or 0 == attack_n:
            now = datetime.datetime.now()
            now_ymd = f"{now.year}年{now.month}月{now.day}日"
            now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

            field_name = (
                "【本日の完凸時間】" if 0 >= attack_n else "【終了時間】"
            )

            if any([
                all([0 == now_hp, 0 == attack_n]),
                all([0 == now_hp, 0 <= attack_n]),
                all([0 <= now_hp, 0 == attack_n])
            ]):

                embed.clear_fields()
                embed.add_field(name=field_name, value=f"{now_ymd}\n{now_hms}", inline=False)

                # 終了したボス情報メッセージのリアクション削除
                await edit_message.clear_reactions()

            if all([0 == now_hp, 0 <= attack_n]):
                await clan_battle_event()

        await edit_message.edit(embed=embed)

        # クロスデイcheck
        if not no_attack_role_reset:
            if not now_attack_list:

                await clan_battl_role_reset()


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
    global now_boss_data
    global now_clan_battl_message
    global BOSS_name

    BOSS_name.clear()
    guild = client.get_guild(599780162309062706)
    CHANNEL_ID = 741851480868519966  # 動作ログ
    channel_bot_log = guild.get_channel(CHANNEL_ID)

    now = datetime.datetime.now()

    clan_battle_start_day = datetime.datetime.strptime(clan_battle_days[0], "%Y/%m/%d %H:%M")
    clan_battle_end_day = datetime.datetime.strptime(clan_battle_days[1], "%Y/%m/%d %H:%M")

    if clan_battle_start_day.strftime('%Y-%m-%d %H:%M') <= now.strftime('%Y-%m-%d %H:%M') < clan_battle_end_day.strftime('%Y-%m-%d %H:%M'):
        clan_battle_tutorial_days = False

    else:
        clan_battle_tutorial_days = True

    for channel_id in BOSS_Ch:
        channel = client.get_channel(channel_id)
        BOSS_name.append(re.sub(r"[0-9]ボス》", "", channel.name))

    BOSS_names = "【現在のボス名】"
    for name in BOSS_name:
        BOSS_names += f"\n{name}"

    if all([
        clan_battle_start_day.strftime('%Y-%m-%d %H:%M') <= now.strftime('%Y-%m-%d %H:%M'),
        clan_battle_end_day.strftime('%Y-%m-%d %H:%M') > now.strftime('%Y-%m-%d %H:%M')
    ]):

        text_1 = "現在クランバトル開催中です。"

    else:
        text_1 = "現在クランバトル期間外です。"

    ch_id_index_y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][ch_id_index_y]))  # 進捗状況

    async for message in channel_0.history(limit=10):
        if message.embeds:
            if re.search(r"[0-9]+月度クランバトル", message.embeds[0].title):
                now_clan_battl_message = message
                text = message.embeds[0].description

                # 現在ボスインデックス取得
                x = 0
                for boss in BOSS_name:

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

    elif 35 <= int(now_boss_data["now_lap"]):
        now_boss_data["now_boss_level"] = 4

    await channel_bot_log.send(f"ミネルヴァ起動しました。\n\n{text_1}\n\n{BOSS_names}")


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

            await channel.send(f"""
{payload.member.mention} さん　こんにちわ。
黒猫魔法学院への加入ありがとうございます。

リアクションの確認が取れましたので、各種機能の制限を解除しました。
改めまして今月よりよろしくお願いします。""")

            await payload.member.add_roles(general_member_role)


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
    global no_attack_role_reset
    global clan_battle_tutorial_days
    global now_boss_data

    await client.wait_until_ready()

    set_rollover_time = rollover_time
    now = datetime.datetime.now()
    clan_battle_start_day = datetime.datetime.strptime(clan_battle_days[0], "%Y/%m/%d %H:%M")
    clan_battle_end_day = datetime.datetime.strptime(clan_battle_days[1], "%Y/%m/%d %H:%M")

    guild = client.get_guild(599780162309062706)
    server_rule_channel = guild.get_channel(749511208104755241)  # サーバー案内

    now = datetime.datetime.now()

    clan_battle_start_day = datetime.datetime.strptime(clan_battle_days[0], "%Y/%m/%d %H:%M")
    clan_battle_end_day = datetime.datetime.strptime(clan_battle_days[1], "%Y/%m/%d %H:%M")

    if clan_battle_start_day.strftime('%Y-%m-%d %H:%M') <= now.strftime('%Y-%m-%d %H:%M') < clan_battle_end_day.strftime('%Y-%m-%d %H:%M'):
        clan_battle_tutorial_days = False

    else:
        clan_battle_tutorial_days = True

    y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][y]))

    if any([
        5 <= now.day < 20,
        clan_battle_start_day.strftime('%Y-%m-%d %H:%M') <= now.strftime('%Y-%m-%d %H:%M') < clan_battle_end_day.strftime('%Y-%m-%d %H:%M')
    ]):

        # クラバト初日設定
        if any([
            all([now.day == 5, now.strftime('%H:%M') == set_rollover_time]),
            now.strftime('%Y-%m-%d %H:%M') == clan_battle_start_day.strftime('%Y-%m-%d %H:%M')
        ]):

            await clan_battl_start_up()

        # 日付変更リセット
        elif now.strftime('%H:%M') == set_rollover_time:

            if now_attack_list:
                no_attack_role_reset = False
                return

            else:
                await clan_battl_role_reset()
                no_attack_role_reset = True

    else:
        pass

    # 不要メッセージの削除
    async for message in channel_0.history(limit=10):
        if all([
            not message.embeds,
            "ボスに与えたダメージを「半角数字」のみで入力してください。" not in message.content,
            "持ち越し時間を入力してください" not in message.content
        ]):
            await message.delete()

        elif all([
            not message.embeds,
            "ボスに与えたダメージを「半角数字」のみで入力してください。" in message.content,
            "持ち越し時間を入力してください" not in message.content
        ]):
            pass

        elif message.embeds:
            break

    # サーバー案内不要メッセージの削除
    async for message in server_rule_channel.history():
        if message.id != 749520003203596339:
            await message.delete()

loop.start()


# リアクション操作
@client.event
async def on_raw_reaction_add(payload):

    # サーバー案内チャンネルチェック
    if payload.channel_id == 749511208104755241:
        await server_rule_reaction_check(payload)

    # クラバト管理リアクション
    await clan_battl_call_reaction(payload)
    await battle_log_add_information(payload)


@client.event
async def on_message(message):

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

    # クラバトコマンド
        if "/残り凸状況" in message.content:
            no_attack_member_list_ch = message.channel.id
            await clan_battl_no_attack_member_list(no_attack_member_list_ch)
            await message.delete()

        if "/リセット" in message.content:
            await clan_battl_start_up()

    # メッセージリンク展開
    await dispand(message)

    # 持ち越し時間用ＴＬ改変
    await ok_tl_edit(message)

    # パンツ交換
    await pants_trade(message)

    # メッセージログ
    await new_message(message)


client.run(TOKEN)
