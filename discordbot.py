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
import japanize_matplotlib
import numpy as np

print(type(japanize_matplotlib))

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

clan_battle_days = 5
rollover_time = "05:00"
clan_battle_start_date = ""
clan_battle_end_date = ""
boss_level_up = [1, 4, 11, 31, 41]  # ボスレベルアップ周回数設定
boss_lap = 1
boss_level = 1

boss_list = {
    "boss_1": {
        "boss_name": "boss_1",
        "boss_img_url": "url",
        "boss_hp": 6000000,
        "boss_max_hp": [6000000, 6000000, 12000000, 19000000, 85000000]
    },
    "boss_2": {
        "boss_name": "boss_2",
        "boss_img_url": "url",
        "boss_hp": 8000000,
        "boss_max_hp": [8000000, 8000000, 14000000, 20000000, 90000000]
    },
    "boss_3": {
        "boss_name": "boss_3",
        "boss_img_url": "url",
        "boss_hp": 10000000,
        "boss_max_hp": [10000000, 10000000, 17000000, 23000000, 95000000]
    },
    "boss_4": {
        "boss_name": "boss_4",
        "boss_img_url": "url",
        "boss_hp": 12000000,
        "boss_max_hp": [12000000, 12000000, 19000000, 25000000, 100000000]
    },
    "boss_5": {
        "boss_name": "boss_5",
        "boss_img_url": "url",
        "boss_hp": 15000000,
        "boss_max_hp": [15000000, 15000000, 22000000, 27000000, 110000000]
    }
}

carryover_list = {}
now_attack_list = {
    "boss_1": {},
    "boss_2": {},
    "boss_3": {},
    "boss_4": {},
    "boss_5": {}
}

boss_hp_check = 0
now_clan_battl_message = None
no_attack_role_reset = True
add_role_check = False
fast_attack_check = False

nl = "\n"
hp_fomat = "{:,}"
p_top = "《"
p_end = "》"

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

message_error_text = (
    """提出されたTLが正しくありません。
もう一度確認してください。

※現在のボスHPに対して「与えたダメージが大きい」可能性があります。"""
)

boss_edit_message = (
    r"""/edit_boss
(?P<now_lap>[0-9]+)
(?P<boss_no>[1-5])
(?P<boss_hp>[0-9]+)"""
)

timeline_format = (
    r"""クランモード (?P<boss_lvels>[1-5])段階目 (?P<boss_name>.*)
(?P<add_damage>[0-9]*)ダメージ
バトル時間 .*
バトル日時 (?P<time_stamp>.*)
----
◆パーティ編成
(?P<use_party>(.|\n)*)
----
◆ユニオンバースト発動時間"""
)

tl_data = re.compile(timeline_format)

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
    clan_battle_start_date = f"{get_data - datetime.timedelta(days=clan_battle_days)} {rollover_time}"
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
    guild = client.get_guild(message.guild_id)

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

    await message.channel.send(f"{guild.get_role(687433139345555456).mention}\n管理者によりキックコマンドが実行されました。", embed=embed)
    await channel.send(embed=embed)
    await kick_user.kick()


# ボスの登録
async def boss_ch_neme(message):
    global boss_name
    r = message.content
    role_m = discord.utils.get(message.guild.roles, name="クランメンバー")
    M = datetime.datetime.now().strftime("%m")

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
    global boss_list

    boss_data_ch = 784763031946264576
    channel_0 = client.get_channel(boss_data_ch)

    boss_img_url = []
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
    boss_img_url.append(boss_text_message.attachments[0].proxy_url)
    if len(message.attachments) == 2:
        embed.set_image(url=boss_text_message.attachments[1].proxy_url)

    for url, boss in zip(boss_img_url, boss_list.values()):
        boss["boss_img_url"] = url

    return embed


# クラバト凸管理 ###########################
# ボスの周回数
def now_boss_level(boss_lap):
    for i, level_up_start in enumerate(boss_level_up, 1):
        level_up_end = boss_level_up[i] if i != len(boss_level_up) else 99
        if level_up_start <= boss_lap < level_up_end:
            return i


# ボスの情報
def boss_hp(boss_no, boss_level):
    boss = boss_list[boss_no]
    now_hp = "{:,}".format(int(boss["boss_hp"]))
    y = int(boss_level) - 1
    boss_max_hp = "{:,}".format(int(boss["boss_max_hp"][y]))
    return now_hp, boss_max_hp


# 凸宣言有無チェック
async def attack_call_check(payload, reaction_message):
    for boss_no, attack_members in zip(now_attack_list, now_attack_list.values()):
        if attack_members.get(payload.member):
            return True
    else:
        # リアクションリセット
        for reaction in reaction_message.reactions:
            if reaction.emoji == payload.emoji.name:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)
                        return False


# 持ち越し時間算出
async def ok_time_plt(message):
    if not re.search("/持ち越しグラフ [0-9]+", message.content):
        return

    embed = discord.Embed(
        description="持ち越しに必要なダメージのグラフを生成してます。\nしばらくお待ちください。",
        colour=0xffff00
    )

    await message.delete()
    del_message = await message.channel.send(embed=embed)

    now_hp = int(re.search("(?<=/持ち越しグラフ )[0-9]+", message.content).group())
    set_max_damage = 2500

    m_content = f"ボスの残り「`{now_hp} 万`」を同時凸したときのダメージと持ち越せる時間をグラフにしました。"

    if now_hp * 4.5 <= set_max_damage:
        add_damage = now_hp * 4.6
        nx = now_hp * 4.3 / 17
        y_high = 91
        y_n = 5
    elif now_hp * 4.5 > set_max_damage:
        add_damage = set_max_damage
        y_high = math.ceil(90 - (now_hp * 90 / add_damage - 20)) + 5
        if y_high <= 65:
            nx = add_damage / 27
            y_n = 2
        else:
            nx = add_damage / 21
            y_n = 5

    n = 1 / 1000
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
    plt.xlabel("ダメージ")
    plt.ylabel("持ち越し時間 （ 秒 ）")
    plt.xticks(np.arange(now_hp, add_damage, nx))
    plt.yticks(np.arange(20, y_high, y_n))
    plt.minorticks_on()
    plt.grid(which="major", color="black", alpha=1)
    plt.grid(which="minor", color="gray", linestyle=":")

    await asyncio.sleep(2.5)
    plt_image = io.BytesIO()
    plt.savefig(plt_image, format="png", facecolor="azure", edgecolor="azure", bbox_inches='tight', pad_inches=0.5)

    plt_image.seek(0)
    plt_image_file = discord.File(plt_image, filename='image.png')

    await del_message.delete()
    await message.channel.send(m_content, file=plt_image_file)
    del plt_image


# スタートアップ
async def clan_battl_start_up(now, new_lap_check):
    global boss_lap
    global boss_level
    global boss_list

    boss_lap = 1
    boss_level = 1
    for boss, boss_data in zip(boss_list, boss_list.values()):
        boss_list[boss]["boss_hp"] = boss_data["boss_max_hp"][0]

    await clan_battl_role_reset(now, new_lap_check)


# 進捗状況の編集
async def clan_battl_edit_progress(message):
    global boss_list
    global boss_lap
    global boss_level

    now = datetime.datetime.now()
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

    guild = client.get_guild(599780162309062706)
    y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][y]))  # 進捗状況
    clan_member_mention = "クランメンバー" if clan_battle_tutorial_days is True else guild.get_role(687433139345555456).mention  # クランメンバーロール
    edit_message = await channel_0.fetch_message(now_clan_battl_message.id)
    embed = edit_message.embeds[0]

    attack_3 = len(guild.get_role(clan_battle_attack_role_id[1]).members) * 3
    attack_2 = len(guild.get_role(clan_battle_attack_role_id[2]).members) * 2
    attack_1 = len(guild.get_role(clan_battle_attack_role_id[3]).members)
    OK_n = len(guild.get_role(clan_battle_attack_role_id[0]).members)
    attack_n = attack_3 + attack_2 + attack_1

    for ids in re.finditer(boss_edit_message, message.content):
        boss_lap = int(ids["now_lap"])
        edit_boss = int(ids['boss_no']) - 1
        boss_no = f"boss_{int(ids['boss_no'])}"
        boss_list[boss_no]["boss_hp"] = int(ids["boss_hp"])
        embed_field_name = embed.fields[edit_boss].name

    # 段階取得
    boss_level = now_boss_level(boss_lap)
    mention_text = f"{clan_member_mention}\n{boss_lap}週目 ・ {boss_level}段階目"
    description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
【{boss_lap}週目 ・ {boss_level}段階目】"""

    if all([
        boss_list[boss_no]["boss_hp"] >= 0,
        len(now_attack_list[boss_no]) != 0
    ]):
        member_list = f"{nl.join([member + p_top + str(attack_type) + p_end for member, attack_type in zip(now_attack_list[boss_no].keys(), now_attack_list[boss_no].values())])}{nl}"
        embed_field_value = f"{boss_list[boss_no]['boss_hp']}/{boss_list[boss_no]['boss_max_hp']}\n━━━━━━━━━━━━━━━━━━━\n{member_list}"

    elif all([
        boss_list[boss_no]["boss_hp"] > 0,
        len(now_attack_list[boss_no]) == 0
    ]):
        member_list = f"```py{nl}\"本戦中のメンバーは現在いません。\"{nl}```"
        embed_field_value = f"{boss_list[boss_no]['boss_hp']}/{boss_list[boss_no]['boss_max_hp'][edit_boss]}\n━━━━━━━━━━━━━━━━━━━\n{member_list}"

    elif boss_list[boss_no]["boss_hp"] == 0:
        embed_field_value = f"{boss_list[boss_no]['boss_hp']}/{boss_list[boss_no]['boss_max_hp'][edit_boss]}\n━━━━━━━━━━━━━━━━━━━\n```py\n┗━ 終了日時》 {now_ymd} {now_hms}\n```"

    embed.description = description_text
    embed.set_field_at(
        edit_boss,
        name=embed_field_name,
        value=embed_field_value,
        inline=False
    )

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
    elif reaction_message.embeds[0].fields[0]:
        if reaction_message.embeds[0].fields[0].name != "【バトル詳細】":
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
        add_message = await new_message(battle_log_check_message)

        await asyncio.sleep(1.5)
        async for message in channel.history(limit=10):
            if not message.embeds:
                await message.delete()

            else:
                break

        battle_log_embed = reaction_message.embeds[0]
        if battle_log_check_message.content:
            if reaction_message.embeds[0].fields:
                field_index = len(reaction_message.embeds[0].fields) - 1
                if all([
                    reaction_message.embeds[0].fields[0].name == "【バトル編成情報】",
                    len(reaction_message.embeds[0].fields) == 1
                ]):
                    battle_log_embed.insert_field_at(
                        1,
                        name="【バトル詳細】",
                        value=battle_log_check_message.content,
                        inline=False
                    )
                elif any([
                    all([
                        reaction_message.embeds[0].fields[0].name == "【バトル編成情報】",
                        len(reaction_message.embeds[0].fields) == 2
                    ]),
                    all([
                        reaction_message.embeds[0].fields[0].name == "【バトル詳細】",
                        len(reaction_message.embeds[0].fields) == 1
                    ])
                ]):

                    battle_log_embed.set_field_at(
                        field_index,
                        name="【バトル詳細】",
                        value=battle_log_check_message.content,
                        inline=False
                    )

            else:
                battle_log_embed.add_field(
                    name="【バトル詳細】",
                    value=battle_log_check_message.content,
                    inline=False
                )

        # メッセージログからバトルログスクショを引き出す
        if battle_log_check_message.attachments:
            embed = add_message.embeds[0]
            if "書き込み" == embed.fields[0].value:
                if battle_log_check_message.id == int(embed.fields[6].value):
                    battle_log_imge = embed.image.proxy_url

                battle_log_embed.set_image(
                    url=battle_log_imge
                )

        # リアクションリセット
        for reaction in reaction_message.reactions:
            if reaction.emoji == add_information_reaction_name:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)

        await reaction_message.edit(embed=battle_log_embed)

        # ミッション達成処理
        if clear_missions:
            await cb_mission(clear_missions, user=payload.member, clear_time=now)


# 残り凸メンバーリスト
async def clan_battl_no_attack_member_list(no_attack_member_list_ch):
    guild = client.get_guild(599780162309062706)
    channel = no_attack_member_list_ch

    now = datetime.datetime.now()
    set_rollover_time = rollover_time

    start_y = clan_battle_start_date.year
    start_m = clan_battle_start_date.month
    start_d = clan_battle_start_date.day
    cb_day = (datetime.date(now.year, now.month, now.day) - datetime.date(start_y, start_m, start_d) + timedelta(days=1)).days

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
    carryover_role_check = False
    attack_role_check = False
    for role in member.roles:
        if role.id == clan_battle_attack_role_id[0]:
            carryover_role_check = True

        elif role.id == clan_battle_attack_role_id[1]:
            attack_role_check = True

        elif role.id == clan_battle_attack_role_id[2]:
            attack_role_check = True

        elif role.id == clan_battle_attack_role_id[3]:
            attack_role_check = True

    return attack_role_check, carryover_role_check


# 未凸ロールの更新
async def add_attack_role(member):
    guild = client.get_guild(599780162309062706)

    for role in member.roles:
        if role.id == clan_battle_attack_role_id[1]:
            attak_role = guild.get_role(clan_battle_attack_role_id[1])
            await member.remove_roles(attak_role)

            attak_role = guild.get_role(clan_battle_attack_role_id[2])
            await member.add_roles(attak_role)
            break

        elif role.id == clan_battle_attack_role_id[2]:
            attak_role = guild.get_role(clan_battle_attack_role_id[2])
            await member.remove_roles(attak_role)

            attak_role = guild.get_role(clan_battle_attack_role_id[3])
            await member.add_roles(attak_role)
            break

        elif role.id == clan_battle_attack_role_id[3]:
            attak_role = guild.get_role(clan_battle_attack_role_id[3])
            await member.remove_roles(attak_role)
            break


# 残り凸ロールリセット
async def clan_battl_role_reset(now, new_lap_check):
    global now_clan_battl_message
    global add_role_check
    global no_attack_role_reset
    global now_attack_list
    global fast_attack_check

    guild = client.get_guild(599780162309062706)
    channel = client.get_channel(741851480868519966)  # ミネルヴァ・動作ログ

    fast_attack_check = True
    if new_lap_check:
        now_clan_battl_message = ""

    y = 0 if clan_battle_tutorial_days is True else 1
    no_attack_member_list_ch = guild.get_channel(int(clan_battle_channel_id[5][y]))  # 残り凸状況
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][y]))  # 進捗状況
    channel_4 = guild.get_channel(int(clan_battle_channel_id[4][y]))  # 持ち越しメモ

    if add_role_check:
        add_role_check = False
        return
    elif not add_role_check:
        add_role_check = True

    if not no_attack_role_reset:
        no_attack_role_reset = True

    if now_clan_battl_message and not new_lap_check:
        edit_message = await channel_0.fetch_message(now_clan_battl_message.id)
        embed = edit_message.embeds[0]

        if not any([
            "【全ボス終了時間】" in embed.fields[5].name,
            "【本日の完凸時間】" in embed.fields[5].name
        ]):

            # 埋め込み情報の編集
            attack_3 = len(guild.get_role(clan_battle_attack_role_id[1]).members) * 3
            attack_2 = len(guild.get_role(clan_battle_attack_role_id[2]).members) * 2
            attack_1 = len(guild.get_role(clan_battle_attack_role_id[3]).members)
            OK_n = len(guild.get_role(clan_battle_attack_role_id[0]).members)
            attack_n = attack_3 + attack_2 + attack_1

            description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
【{boss_lap}週目 ・ {boss_level}段階目】"""

            now_ymd = f"{now.year}年{now.month}月{now.day}日"
            now_hms = f"{now.hour}時{now.minute}分{now.second}秒"

            embed.description = description_text
            embed.set_field_at(5, name="【終了時間】", value=f"{now_ymd}\n{now_hms}", inline=False)

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
            all([
                clan_battle_tutorial_days,
                now.strftime('%Y-%m-%d') == clan_battle_end_date.strftime('%Y-%m-%d')
            ])
        ]):
            await no_attack_member_list()

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
    await clan_battle_event(new_lap_check)


# 終了時状況
async def no_attack_member_list():
    global now_clan_battl_message
    global boss_list

    guild = client.get_guild(599780162309062706)
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][1]))  # 進捗状況
    no_attack_member_list_ch = guild.get_channel(int(clan_battle_channel_id[5][1]))  # 残り凸状況

    message_embed = await channel_0.fetch_message(now_clan_battl_message.id)
    message_embed = message_embed.embeds[0]
    async for message in no_attack_member_list_ch.history(limit=1):
        end_member_list_embed = message.embeds[0]

    top_text = f"{end_member_list_embed.embeds[0].description}\n【{boss_lap}週目 ・ {boss_level}段階目】\n"
    description_text = [top_text]
    for i, embed_fields, boss_no, boss in zip(range(5), message_embed.fields, boss_list, boss_list.values()):
        now_hp, boss_max_hp = boss_hp(boss_no, boss_level)
        boss_data = f"\n┗━ {now_hp}/{boss_max_hp}"
        text = f"{embed_fields.name}{boss_data}"
        description_text.append(text)

    embed = discord.Embed(
        title=message_embed.title,
        description="\n".join([text for text in description_text]),
        color=0x00b4ff
    )

    if message_embed.embeds[0].fields:
        for embed_field in message_embed.embeds[0].fields[0]:
            embed.add_field(embed_field)

    channel = guild.get_channel(793193683343114251)  # 凸漏れ記録
    await channel.send(embed=embed)


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
async def clan_battle_event(new_lap_check):
    global now_clan_battl_message
    global boss_lap
    global boss_level

    set_rollover_time = rollover_time
    now = datetime.datetime.now()

    start_y = clan_battle_start_date.year
    start_m = clan_battle_start_date.month
    start_d = clan_battle_start_date.day
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"
    cb_day = (datetime.date(now.year, now.month, now.day) - datetime.date(start_y, start_m, start_d) + timedelta(days=1)).days

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

    boss_level = now_boss_level(boss_lap)
    guild = client.get_guild(599780162309062706)

    y = 0 if clan_battle_tutorial_days is True else 1
    channel = guild.get_channel(int(clan_battle_channel_id[0][y]))  # 進捗状況
    if now_clan_battl_message:
        end_message = await channel.fetch_message(now_clan_battl_message.id)

    clan_member_mention = "クランメンバー" if clan_battle_tutorial_days is True else guild.get_role(687433139345555456).mention  # クランメンバーロール

    attack_3 = len(guild.get_role(clan_battle_attack_role_id[1]).members) * 3
    attack_2 = len(guild.get_role(clan_battle_attack_role_id[2]).members) * 2
    attack_1 = len(guild.get_role(clan_battle_attack_role_id[3]).members)
    OK_n = len(guild.get_role(clan_battle_attack_role_id[0]).members)
    attack_n = attack_3 + attack_2 + attack_1

    # メッセージを書きます
    attack_members = []
    embed_title = f"【{now.month}月度クランバトル {cb_day_text}】"
    description_text = f"""
残り凸数》{attack_n}凸
持ち越し》{OK_n}人
【{boss_lap}週目 ・ {boss_level}段階目】"""

    if not new_lap_check and now_clan_battl_message:
        embed = end_message.embeds[0]
        embed.title = embed_title
        embed.description = description_text
        if attack_n > 0:
            embed.set_field_at(5, name="【リアクション（スタンプ）説明】", value=help_emoji, inline=False)
        else:
            embed.set_field_at(5, name="【本日の完凸時間】", value=f"{now_ymd}\n{now_hms}", inline=False)

    elif new_lap_check:
        for boss, boss_data in zip(boss_list, boss_list.values()):
            boss_list[boss]["boss_hp"] = boss_data["boss_max_hp"][boss_level - 1]
        for i in range(5):
            attack_members.append(f"```py{nl}\"本戦中のメンバーは現在いません。\"{nl}```")
        else:
            embed = discord.Embed(
                title=embed_title,
                description=description_text,
                color=0x00b4ff
            )
            for boss_no_emoji, boss_no, boss, member_list in zip(number_emoji, boss_list, boss_list.values(), attack_members):
                now_hp, boss_max_hp = boss_hp(boss_no, boss_level)
                embed_field_name = f"{boss_no_emoji}》{boss['boss_name']}"
                embed_field_value = f"{now_hp}/{boss_max_hp}\n━━━━━━━━━━━━━━━━━━━\n"
                embed.add_field(name=embed_field_name, value=f"{embed_field_value}{member_list}", inline=False)
            else:
                embed.add_field(name="【リアクション（スタンプ）説明】", value=help_emoji, inline=False)

    mention_text = f"{clan_member_mention}\n{boss_lap}週目 ・ {boss_level}段階目"
    now_clan_battl_message = await channel.send(mention_text, embed=embed)

    for reactiones in emoji_list.values():
        await now_clan_battl_message.add_reaction(reactiones)


# キャンセルしたメンバーの削除
def attack_member_del(member):
    global now_attack_list
    global carryover_list

    for boss_no, member_list in zip(now_attack_list, now_attack_list.values()):
        if member_list.get(member):
            del member_list[member]
            break

    if member in carryover_list:
        del carryover_list[member]

    return boss_no


# 凸宣言キャンセルリアクションイベント
async def clan_battl_clear_reaction(payload):
    global now_attack_list

    guild = client.get_guild(payload.guild_id)
    reaction_member = guild.get_member(payload.user_id)
    channel = guild.get_channel(payload.channel_id)
    edit_message = now_clan_battl_message
    reaction_change = False

    ch_id_index_y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][ch_id_index_y]))  # 進捗状況
    channel_1 = guild.get_channel(int(clan_battle_channel_id[1][ch_id_index_y]))  # 凸相談

    # BOTと進捗状況CH以外のリアクション無効
    if any([
        reaction_member.bot,
        channel.id != int(clan_battle_channel_id[0][ch_id_index_y]),  # 進捗状況
    ]):
        return

    # メンバーリストにメンバーがあるかチェック
    for boss_no, attack_member in zip(now_attack_list, now_attack_list.values()):
        if attack_member.get(reaction_member):
            break
    else:
        return

    if any([
        payload.emoji.name == emoji_list["attack_m"],
        payload.emoji.name == emoji_list["attack_p"]
    ]):
        for reaction in now_clan_battl_message.reactions:
            if reaction.emoji == emoji_list["attack_p"]:
                async for user in reaction.users():
                    member = guild.get_member(user.id)
                    if member == payload.member:
                        reaction_change = True
                        boss_no = attack_member_del(member=reaction_member)
                        break

            elif reaction.emoji == emoji_list["attack_m"]:
                async for user in reaction.users():
                    member = guild.get_member(user.id)
                    if member == payload.member:
                        reaction_change = True
                        boss_no = attack_member_del(member=reaction_member)
                        break

    elif any([
        payload.emoji.name == emoji_list["T_kill"],
        payload.emoji.name == emoji_list["SOS"],
        payload.emoji.name == emoji_list["attack_end"],
    ]):
        return

    if not reaction_change:
        embed = discord.Embed(
            description=f"{reaction_member.display_name}》{boss_list[boss_no]['boss_name']}\n凸宣言がキャンセルされました。",
            color=0xff0000
        )
        boss_no = attack_member_del(member=reaction_member)
        message_1 = await channel_1.send(embed=embed)
        message_2 = await channel_0.send(f"{reaction_member.mention}》\n凸宣言をキャンセルしました。")

    # メンバーリストの編集
    now_hp, boss_max_hp = boss_hp(boss_no, boss_level)
    field_index = int(boss_no.replace("boss_", "")) - 1
    boss = f"{now_hp}/{boss_max_hp}\n━━━━━━━━━━━━━━━━━━━\n"
    if len(now_attack_list[boss_no]) != 0:
        member_list = f"{boss}{nl.join([member.display_name + str(attack_type) for member, attack_type in zip(now_attack_list[boss_no].keys(), now_attack_list[boss_no].values())])}{nl}"

    else:
        member_list = f"{boss}```py{nl}\"本戦中のメンバーは現在いません。\"{nl}```"

    edit_message = await channel_0.fetch_message(now_clan_battl_message.id)
    embed = edit_message.embeds[0]
    embed.set_field_at(
        field_index,
        name=embed.fields[field_index].name,
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


# 凸宣言リアクションイベント
async def clan_battl_call_reaction(payload):
    global boss_list
    global carryover_list
    global now_attack_list
    global now_clan_battl_message
    global now_boss_data
    global new_boss_check
    global fast_attack_check

    now = datetime.datetime.now()
    start_y = clan_battle_start_date.year
    start_m = clan_battle_start_date.month
    start_d = clan_battle_start_date.day
    now_ymd = f"{now.year}年{now.month}月{now.day}日"
    now_hms = f"{now.hour}時{now.minute}分{now.second}秒"
    cb_day = (datetime.date(now.year, now.month, now.day) - datetime.date(start_y, start_m, start_d) + timedelta(days=1)).days

    reaction_change = False
    ok_attack_text = ""
    boss_no_message = ""
    message_1 = ""
    messages = []
    carryover_messages = {}

    reset_reaction = ["\U00002705", "\U0000274c"]

    guild = client.get_guild(599780162309062706)
    clan_member_role = guild.get_role(687433139345555456)  # クランメンバーロール
    ch_id_index_y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][ch_id_index_y]))  # 進捗状況
    channel_1 = guild.get_channel(int(clan_battle_channel_id[1][ch_id_index_y]))  # 凸相談
    channel_2 = guild.get_channel(int(clan_battle_channel_id[2][ch_id_index_y]))  # タスキル状況
    channel_4 = guild.get_channel(int(clan_battle_channel_id[4][ch_id_index_y]))  # 持ち越しメモ

    edit_message = await channel_0.fetch_message(now_clan_battl_message.id)
    channel = guild.get_channel(payload.channel_id)
    reaction_message = await channel.fetch_message(payload.message_id)

    if payload.member.bot:
        return

    if channel.id == int(clan_battle_channel_id[0][ch_id_index_y]):  # 進捗状況
        attack_role_check, carryover_role_check = no_attack_role_check(payload)

        if not attack_role_check and not carryover_role_check:
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

        # 凸宣言リアクション
        if any([
            payload.emoji.name == emoji_list["attack_p"],
            payload.emoji.name == emoji_list["attack_m"]
        ]):

            if carryover_role_check:
                # 持ち越し時間
                async for message in channel_4.history():
                    if payload.member.mention in message.content:
                        messages.append(message)

            # 持ち越し選択
            if messages:
                messages.reverse()
                for reaction, message in zip(number_emoji, messages):
                    carryover_messages[reaction] = message

                message_content = f"{payload.member.mention}》\n以下の持ち越し情報があります。"
                embed = discord.Embed(
                    description="使用する持ち越し、または通常凸する場合は該当するリアクションを押してください。",
                    color=0xffff00
                )
                for reaction, carryover_message in zip(carryover_messages.keys(), carryover_messages.values()):
                    embed.add_field(name=f"{reaction}》リアクション", value=carryover_message.content, inline=False)

                carryover_list_message = await channel_0.send(message_content, embed=embed)
                for reactione in carryover_messages.keys():
                    await carryover_list_message.add_reaction(reactione)

                # 残り凸ロールチェック
                for role in payload.member.roles:
                    if any([
                        role.id == clan_battle_attack_role_id[1],
                        role.id == clan_battle_attack_role_id[2],
                        role.id == clan_battle_attack_role_id[3]
                    ]):
                        embed.add_field(name=f"{reset_reaction[1]}》リアクション", value="持ち越し凸を使用せず、通常凸する場合。", inline=False)
                        await carryover_list_message.edit(embed=embed)
                        await carryover_list_message.add_reaction(reset_reaction[1])
                        break

                def role_reset_check(reaction, user):

                    return all([
                        reaction.message.id == carryover_list_message.id,
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

                    await carryover_list_message.delete()
                    return

                # 持ち越し情報
                if reaction.emoji != reset_reaction[1]:
                    carryover_message = carryover_messages[reaction.emoji]
                    carryover_list[payload.member] = carryover_message
                    carry_over_time = re.search(r"[0-9]:[0-9]{2}", carryover_message.content).group()
                    ok_attack_text = f"__**（持ち越し凸）{carry_over_time}**__"

                await carryover_list_message.delete()

            # 物理リアクション
            if payload.emoji.name == emoji_list["attack_p"]:
                attack_type = "物理編成"

                for reaction in reaction_message.reactions:
                    if reaction.emoji == emoji_list["attack_m"]:
                        async for user in reaction.users():
                            if user == payload.member:
                                reaction_change = True
                                boss_no = attack_member_del(member=payload.member)
                                await reaction.remove(user)
                                break

            # 魔法リアクション
            elif payload.emoji.name == emoji_list["attack_m"]:
                attack_type = "魔法編成"

                for reaction in reaction_message.reactions:
                    if reaction.emoji == emoji_list["attack_p"]:
                        async for user in reaction.users():
                            if user == payload.member:
                                reaction_change = True
                                boss_no = attack_member_del(member=payload.member)
                                await reaction.remove(user)
                                break

            # メンバーリストの編集
            if reaction_change:
                field_index = int(boss_no.replace("boss_", "")) - 1
                now_hp, boss_max_hp = boss_hp(boss_no, boss_level)
                boss = f"{now_hp}/{boss_max_hp}\n━━━━━━━━━━━━━━━━━━━\n"
                if len(now_attack_list[boss_no]) != 0:
                    member_list = f"{boss}{nl.join([member.display_name + str(attack_type) for member, attack_type in zip(now_attack_list[boss_no].keys(), now_attack_list[boss_no].values())])}{nl}"

                else:
                    member_list = f"{boss}```py{nl}\"本戦中のメンバーは現在いません。\"{nl}```"

                edit_message = await channel_0.fetch_message(now_clan_battl_message.id)
                embed = edit_message.embeds[0]
                embed.set_field_at(
                    field_index,
                    name=embed.fields[field_index].name,
                    value=member_list,
                    inline=False
                )
                await edit_message.edit(embed=embed)

            not_zero_hp = []
            for boss_no, boss_data in zip(boss_list, boss_list.values()):
                if boss_data["boss_hp"] != 0:
                    not_zero_hp.append(boss_no)

            # 残り2体以上の時のみボス番号入力
            if len(not_zero_hp) > 1:
                embed = discord.Embed(
                    description=f"{payload.member.mention}さんは、このメッセージの凸するボス番号のリアクションを押してください。\n※討伐済みボス番号のリアクションは表示されません。",
                    color=0xffff00
                )
                message_content = payload.member.mention
                boss_no_message = await channel_0.send(message_content, embed=embed)

                for boss_no_emoji, boss in zip(number_emoji, boss_list.values()):
                    if boss["boss_hp"] > 0:
                        await boss_no_message.add_reaction(boss_no_emoji)

                def role_reset_check(reaction, user):

                    return all([
                        any([
                            reaction.emoji == number_emoji[0],
                            reaction.emoji == number_emoji[1],
                            reaction.emoji == number_emoji[2],
                            reaction.emoji == number_emoji[3],
                            reaction.emoji == number_emoji[4]
                        ]),
                        reaction.message.id == boss_no_message.id,
                        user.id == payload.member.id,
                        not user.bot
                    ])

                try:
                    reaction, user = await client.wait_for('reaction_add', check=role_reset_check, timeout=10)

                except asyncio.TimeoutError:
                    embed = discord.Embed(
                        title="タイムアウトエラー",
                        description=timeouterror_text,
                        colour=0xff0000
                    )
                    await boss_no_message.delete()
                    timeout_message = await channel_0.send(payload.member.mention, embed=embed)
                    for reaction in reaction_message.reactions:
                        async for user in reaction.users():
                            if user == payload.member:
                                await reaction.remove(user)

                    delete_time = 10
                    await message_time_delete(timeout_message, delete_time)
                    return

                # リアクションされたボス番号
                for emoji, boss_no in zip(number_emoji, boss_list):
                    if reaction.emoji == emoji:
                        break

            else:
                boss_no = not_zero_hp[0]

            attack_boss = boss_list[boss_no]["boss_name"]
            field_index = int(re.search("(?<=boss_)[0-9]", boss_no).group()) - 1
            now_attack_list[boss_no][payload.member] = f"《{attack_type}》{ok_attack_text}"
            embed = discord.Embed(
                description=f"{payload.member.display_name}》\n「{attack_type}」{ok_attack_text}で「{attack_boss}」に入りました。",
                color=0x00b4ff
            )
            message_1 = await channel_1.send(embed=embed)
            if boss_no_message:
                await boss_no_message.delete()
            add_attack_message = await channel_0.send(f"{payload.member.mention}》\n`{attack_boss}`への凸宣言を受け付けました。")

        # タスキルリアクション
        elif payload.emoji.name == emoji_list["T_kill"]:
            # 凸宣言有無チェック
            attack_call = await attack_call_check(payload, reaction_message)
            if not attack_call:
                not_reaction_message = await channel_0.send(f"{payload.member.mention}》\n凸宣言が有りません。\n`※タスキルリアクションを利用できません。`")
                delete_time = 10
                await message_time_delete(not_reaction_message, delete_time)
                return

            if cb_day <= 0:
                if datetime.datetime.now().strftime("%H:%M") < rollover_time:
                    cb_day = cb_day - 1
                cb_day_text = f"`開催{abs(cb_day)}日目前 ┃ {now_ymd} {now_hms}`"
            else:
                if datetime.datetime.now().strftime("%H:%M") < rollover_time:
                    cb_day = cb_day - 1
                cb_day_text = f"`{abs(cb_day)}日目 ┃ {now_ymd} {now_hms}`"

            await channel_2.send(f"{payload.member.mention}》\nタスキルしました。\n{cb_day_text}")
            return

        elif payload.emoji.name == emoji_list["SOS"]:
            # 凸宣言有無チェック
            attack_call = await attack_call_check(payload, reaction_message)
            if not attack_call:

                not_reaction_message = await channel_0.send(f"{payload.member.mention}》\n凸宣言が有りません。\n`※SOSリアクションを利用できません。`")
                delete_time = 10
                await message_time_delete(not_reaction_message, delete_time)
                return

            clan_member_mention = "クランメンバー" if clan_battle_tutorial_days is True else clan_member_role.mention
            await channel_1.send(f"{clan_member_mention}\n「{payload.member.display_name}」さんが救援を求めてます。")
            return

        now_hp, boss_max_hp = boss_hp(boss_no, boss_level)
        boss = f"{now_hp}/{boss_max_hp}\n━━━━━━━━━━━━━━━━━━━\n"
        if len(now_attack_list[boss_no]) != 0:
            member_list = f"{boss}{nl.join([member.display_name + str(attack_type) for member, attack_type in zip(now_attack_list[boss_no].keys(), now_attack_list[boss_no].values())])}{nl}"

        else:
            member_list = f"{boss}```py{nl}\"本戦中のメンバーは現在いません。\"{nl}```"

        edit_message = await channel_0.fetch_message(now_clan_battl_message.id)
        embed = edit_message.embeds[0]
        embed.set_field_at(
            field_index,
            name=embed.fields[field_index].name,
            value=member_list,
            inline=False
        )
        await edit_message.edit(embed=embed)

    # アナウンスメッセージの削除
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


# 凸終了リアクションイベント
async def clan_battl_end_reaction(payload):
    global boss_lap
    global boss_level
    global boss_list
    global carryover_list
    global no_attack_role_reset
    global fast_attack_check

    guild = client.get_guild(599780162309062706)
    ch_id_index_y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][ch_id_index_y]))  # 進捗状況
    channel_1 = guild.get_channel(int(clan_battle_channel_id[1][ch_id_index_y]))  # 凸相談
    channel_3 = guild.get_channel(int(clan_battle_channel_id[3][ch_id_index_y]))  # バトルログ
    channel_4 = guild.get_channel(int(clan_battle_channel_id[4][ch_id_index_y]))  # 持ち越しメモ
    no_attack_member_list_ch = guild.get_channel(int(clan_battle_channel_id[5][ch_id_index_y]))  # 残り凸状況
    reaction_message = await channel_0.fetch_message(payload.message_id)
    carryover_attack_check = False
    carryover_role_check = False
    carryover_time_message = ""
    last_attack_text = ""
    time_stamp = ""
    use_party = ""
    damage = ""
    add_damage = ""
    true_dmg = ""
    la_mission = False
    message_1 = ""

    if payload.member.bot:
        return

    # 凸終了リアクション
    if payload.emoji.name == emoji_list["attack_end"]:
        attack_role_check, carryover_role_check = no_attack_role_check(payload)

        # 凸宣言有無チェック
        attack_call = await attack_call_check(payload, reaction_message)
        if not attack_call:
            not_reaction_message = await channel_0.send(f"{payload.member.mention}》\n凸宣言が有りません。")
            delete_time = 10
            await message_time_delete(not_reaction_message, delete_time)
            return

        member_check = False
        for boss_no in now_attack_list:
            for member, attack_type in zip(now_attack_list[boss_no].keys(), now_attack_list[boss_no].values()):
                if payload.member.id == member.id:
                    member_check = True
                    attack_boss = boss_list[boss_no]
                    break
            if member_check:
                break

        await channel_0.set_permissions(payload.member, send_messages=True)
        m_content = f"""
{payload.member.mention}》
「`バトルTLの提出`」および、ボスに与えたダメージを「`半角数字`」のみで入力してください。

※ボスを倒した場合は「__{hp_fomat.format(int(attack_boss['boss_hp']))}__」以上で入力してください。
※ボスの最大HP「__{hp_fomat.format(int(attack_boss['boss_max_hp'][boss_level - 1]))}__」以上は入力できません。
"""

        embed = discord.Embed(
            title="ラスアタ時は、「\U00002705」リアクションで入力を省略できます。\n※同時処理した場合は与えたダメージを直接入力してください。\n（同時処理ミッションが反映されます。）",
            description=int(attack_boss['boss_hp']),
            colour=0xffea00
        )
        announce_message_1 = await channel_0.send(m_content, embed=embed)
        await announce_message_1.add_reaction("\U00002705")

        def attack_dmg_message_check(message):
            if all([
                any([
                    message.content.isdecimal(),
                    tl_data.search(message.content)
                ]),
                message.channel == channel_0,
                message.author.id == payload.user_id,
                not message.author.bot
            ]):
                return True
            else:
                return False

        def last_attack_reaction_check(reaction, user):
            return all([
                reaction.emoji == "\U00002705",
                reaction.message.id == announce_message_1.id,
                user.id == payload.member.id,
                not user.bot
            ])

        boss_hp_check_message = asyncio.create_task(client.wait_for("message", check=attack_dmg_message_check), name="wait_message")
        last_attack_reaction = asyncio.create_task(client.wait_for("reaction_add", check=last_attack_reaction_check, timeout=60), name="wait_reaction")

        aws = {boss_hp_check_message, last_attack_reaction}
        done, pending = await asyncio.wait(aws, return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            # タイムアウト処理
            if isinstance(task.exception(), asyncio.TimeoutError):
                embed = discord.Embed(
                    title="タイムアウトエラー",
                    description=timeouterror_text,
                    colour=0xff0000
                )
                await announce_message_1.delete()
                await channel_0.set_permissions(payload.member, overwrite=None)
                timeout_message = await channel_0.send(payload.member.mention, embed=embed)
                # 凸宣言リアクションリセット
                for reaction in reaction_message.reactions:
                    # 凸終了宣言リアクションリセット
                    if reaction.emoji == emoji_list["attack_end"]:
                        async for user in reaction.users():
                            if user == payload.member:
                                await reaction.remove(user)

                await asyncio.sleep(10)
                await timeout_message.delete()
                return

            # ダメージ入力 or リアクション判定
            done_task_type = task.get_name()
            # 残り体力
            attack_boss = boss_list[boss_no]
            boss_hp_percentage = int(attack_boss["boss_hp"]) / int(attack_boss["boss_max_hp"][boss_level - 1]) * 100
            # 微残し判定
            if round(boss_hp_percentage, 2) <= 25.00:
                la_mission = True

            # 現在の周回数
            now_boss_lap = boss_lap
            now_boss_level = boss_level
            # ダメージの直接入力 TL提出
            if done_task_type == "wait_message":
                # TLテキストチェック
                boss_hp_check_message = task.result()
                if not task.result():
                    embed = discord.Embed(
                        title="TLテキストエラー",
                        description=message_error_text,
                        colour=0xff0000
                    )
                    await announce_message_1.delete()
                    await channel_0.set_permissions(payload.member, overwrite=None)
                    timeout_message = await channel_0.send(payload.member.mention, embed=embed)
                    # 凸宣言リアクションリセット
                    for reaction in reaction_message.reactions:
                        # 凸終了宣言リアクションリセット
                        if reaction.emoji == emoji_list["attack_end"]:
                            async for user in reaction.users():
                                if user == payload.member:
                                    await reaction.remove(user)

                    await asyncio.sleep(10)
                    await timeout_message.delete()
                    return

                if boss_hp_check_message.content.isdecimal():
                    damage = boss_hp_check_message.content
                # TL提出
                elif tl_data.search(boss_hp_check_message.content):
                    for add_attack_data in re.finditer(timeline_format, boss_hp_check_message.content):
                        time_stamp = datetime.datetime.strptime(add_attack_data["time_stamp"], '%Y/%m/%d %H:%M')
                        use_party = add_attack_data["use_party"]
                        damage = add_attack_data["add_damage"]

                # 残りHP入力チェック
                if int(damage) > int(attack_boss['boss_max_hp'][boss_level - 1]):
                    await boss_hp_check_message.delete()
                    embed = discord.Embed(
                        title="TLテキストエラー",
                        description=message_error_text,
                        colour=0xff0000
                    )
                    await announce_message_1.delete()
                    await channel_0.set_permissions(payload.member, overwrite=None)
                    timeout_message = await channel_0.send(payload.member.mention, embed=embed)
                    # 凸宣言リアクションリセット
                    for reaction in reaction_message.reactions:
                        # 凸終了宣言リアクションリセット
                        if reaction.emoji == emoji_list["attack_end"]:
                            async for user in reaction.users():
                                if user == payload.member:
                                    await reaction.remove(user)

                    await asyncio.sleep(10)
                    await timeout_message.delete()
                    return

                last_boss_hp = int(attack_boss["boss_hp"]) - int(damage)
                add_damage = int(damage)
                async for message in channel_0.history(limit=20):
                    if any([
                        message.id == announce_message_1.id,
                        message.id == boss_hp_check_message.id
                    ]):
                        await message.delete()

                    elif message.id == now_clan_battl_message.id:
                        break

            # ラスアタ入力、省略
            elif done_task_type == "wait_reaction":
                reaction, user = task.result()
                add_damage = int(attack_boss["boss_hp"])
                last_boss_hp = 0
                await announce_message_1.delete()

        if 0 >= last_boss_hp:
            true_dmg = "" if last_boss_hp == 0 else f"\n　　({hp_fomat.format(int(attack_boss['boss_hp']))})"
            last_boss_hp = 0
            now_hp = 0
            carryover_attack_check = True

            if payload.member not in carryover_list:
                time_input_announce_message = await channel_0.send(f"""
{payload.member.mention}》
持ち越し時間を入力してください、持ち越しメモに反映します。
※入力は全て「半角」にて「__**1:30～0:21**__」の範囲でお願いします。
【記入例】
1:30
0:25""")

                def carryover_time_message_check(message):
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
                    carryover_time_message = await client.wait_for('message', check=carryover_time_message_check, timeout=30)
                    carry_over_time = re.search(r"[0-9]:[0-9]{2}", carryover_time_message.content).group()

                except asyncio.TimeoutError:
                    embed = discord.Embed(
                        title="タイムアウトエラー",
                        description=timeouterror_text,
                        colour=0xff0000
                    )
                    await time_input_announce_message.delete()
                    await channel_0.set_permissions(payload.member, overwrite=None)
                    timeout_message = await channel_0.send(payload.member.mention, embed=embed)
                    # 凸宣言リアクションリセット
                    for reaction in reaction_message.reactions:
                        # 凸終了宣言リアクションリセット
                        if reaction.emoji == emoji_list["attack_end"]:
                            async for user in reaction.users():
                                if user == payload.member:
                                    await reaction.remove(user)

                    delete_time = 10
                    await message_time_delete(timeout_message, delete_time)
                    return

                async for message in channel_0.history(limit=20):
                    if any([
                        message.id == time_input_announce_message.id,
                        message.id == carryover_time_message.id
                    ]):
                        await message.delete()

                    elif message.id == now_clan_battl_message.id:
                        break

            if all([
                carryover_attack_check,
                payload.member not in carryover_list
            ]):
                last_attack_text = f"\n┣ラスアタ》\n┃┗__**持ち越し時間 ＝ {carry_over_time}**__"

            elif all([
                carryover_attack_check,
                payload.member in carryover_list
            ]):
                last_attack_text = "\n┣ラスアタ》\n┃┗__**持ち越し不可**__"

        # 残りHP上書き
        boss_list[boss_no]["boss_hp"] = last_boss_hp
        if last_boss_hp == 0:
            # 全ボスHPチェック,段階変更
            for boss in boss_list.values():
                if int(boss["boss_hp"]) > 0:
                    break
            else:
                boss_lap += 1

        # 持ち越しメッセージの削除
        if payload.member in carryover_list:
            await carryover_list[payload.member].delete()

        # 持ち越し残りチェック
        async for message in channel_4.history():
            if payload.member.mention in message.content:
                break
        else:
            attak_role = guild.get_role(int(clan_battle_attack_role_id[0]))
            await payload.member.remove_roles(attak_role)

        if all([
            carryover_attack_check,
            not carryover_role_check
        ]):

            carryover_attak_role = guild.get_role(int(clan_battle_attack_role_id[0]))
            await payload.member.add_roles(carryover_attak_role)

        # ダメージログ
        dmg = "{:,}".format(int(add_damage))
        battle_log = f"""
{now_boss_lap}週目・{now_boss_level}段階目
{boss_list[boss_no]["boss_name"]}
{payload.member.mention}
({payload.member.display_name})
┣{now_attack_list[boss_no][payload.member]}{last_attack_text}
┗ダメージ》
　┗{dmg}{true_dmg}"""

        embed = discord.Embed(
            description=battle_log,
            color=0x00b4ff
        )
        embed.set_thumbnail(url=boss_list[boss_no]["boss_img_url"])

        # バトル編成
        try:
            if tl_data.search(boss_hp_check_message.content):
                embed.add_field(name="【バトル編成情報】", value=f"```py\n{use_party}\n```", inline=False)
                embed.set_footer(text=f"バトル時間 ┃ {time_stamp.year}年{time_stamp.month}月{time_stamp.day}日 {time_stamp.hour}時{time_stamp.minute}分")
        except AttributeError:
            pass

        if carryover_time_message:
            attak_type = re.sub(r"[《》]", "", now_attack_list[boss_no][payload.member])
            carry_over_time = re.match(r"[0-9]:[0-9]{2}", carryover_time_message.content).group()

            last_attack_message = f"""
{payload.member.mention}》
{now_boss_lap}週目・{now_boss_level}段階目
{boss_list[boss_no]["boss_name"]}
┃
┣┳ラスアタ時の編成
┃┗{attak_type}
┃
┗┳持ち越し時間
　┗__**{carry_over_time}**__"""

        # 凸宣言リアクションリセット
        del now_attack_list[boss_no][payload.member]
        for reaction in reaction_message.reactions:
            # 物理編成、凸宣言リアクションリセット
            if reaction.emoji == emoji_list["attack_p"]:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)

            # 魔法編成、凸宣言リアクションリセット
            if reaction.emoji == emoji_list["attack_m"]:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)

            # 凸終了宣言リアクションリセット
            if reaction.emoji == emoji_list["attack_end"]:
                async for user in reaction.users():
                    if user == payload.member:
                        await reaction.remove(user)

        if payload.member not in carryover_list:
            await add_attack_role(member=payload.member)

        embed_end = discord.Embed(
            description=f"{payload.member.display_name}》\n凸が終了しました。",
            color=0x00b4ff
        )
        now = datetime.datetime.now()
        now_ymd = f"{now.year}年{now.month}月{now.day}日"
        now_hms = f"{now.hour}時{now.minute}分{now.second}秒"
        await channel_0.set_permissions(payload.member, overwrite=None)
        await clan_battl_no_attack_member_list(no_attack_member_list_ch)
        message_1 = await channel_1.send(embed=embed_end)
        battl_log_message = await channel_3.send(payload.member.mention, embed=embed)
        await battl_log_message.add_reaction("\U0001f4dd")

        if carryover_time_message:
            await channel_4.send(last_attack_message)

        if payload.member in carryover_list:
            del carryover_list[payload.member]

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
【{now_boss_lap}週目 ・ {now_boss_level}段階目】"""

    edit_message = await channel_0.fetch_message(now_clan_battl_message.id)
    embed = edit_message.embeds[0]
    embed.description = description_text
    field_index = int(re.search("(?<=boss_)[0-9]", boss_no).group()) - 1

    now_hp, boss_max_hp = boss_hp(boss_no, boss_level)
    embed_field_name = edit_message.embeds[0].fields[field_index].name

    if all([
        last_boss_hp >= 0,
        len(now_attack_list[boss_no]) != 0
    ]):
        member_list = f"{nl.join([member + p_top + str(attack_type) + p_end for member, attack_type in zip(now_attack_list[boss_no].keys(), now_attack_list[boss_no].values())])}{nl}"
        embed_field_value = f"{now_hp}/{boss_max_hp}\n━━━━━━━━━━━━━━━━━━━\n{member_list}"

    elif all([
        last_boss_hp > 0,
        len(now_attack_list[boss_no]) == 0
    ]):
        member_list = f"```py{nl}\"本戦中のメンバーは現在いません。\"{nl}```"
        embed_field_value = f"{now_hp}/{boss_max_hp}\n━━━━━━━━━━━━━━━━━━━\n{member_list}"

    elif last_boss_hp == 0:
        embed_field_value = f"{now_hp}/{boss_max_hp}\n━━━━━━━━━━━━━━━━━━━\n```py\n┗━ 終了日時》 {now_ymd} {now_hms}\n```"

    embed.set_field_at(
        field_index,
        name=embed_field_name,
        value=embed_field_value,
        inline=False
    )
    await edit_message.edit(embed=embed)

    if now_boss_lap != boss_lap or 0 == attack_total:
        for boss, boss_data in zip(boss_list, boss_list.values()):
            boss_list[boss]["boss_hp"] = boss_data["boss_max_hp"][boss_level - 1]

        if any([
            all([now_boss_lap == boss_lap, 0 == attack_total]),
            all([now_boss_lap != boss_lap, 0 <= attack_total]),
            all([now_boss_lap != boss_lap, 0 == attack_total])
        ]):

            field_name = "【全ボス終了時間】"
            embed.set_field_at(
                5,
                name=field_name,
                value=f"{now_ymd}\n{now_hms}",
                inline=False)

            # 終了したボス情報メッセージのリアクション削除
            await edit_message.clear_reactions()
            await edit_message.edit(embed=embed)

        if all([now_boss_lap != boss_lap, 0 <= attack_total]):
            now_attack_list[boss_no].clear()
            for boss, boss_data in zip(boss_list, boss_list.values()):
                boss_list[boss]["boss_hp"] = boss_data["boss_max_hp"][boss_level - 1]

            await clan_battle_event(new_lap_check=True)

    # クラバトミッション
    # ファーストアタック
    clear_missions = []
    attack_role_check, carryover_role_check = no_attack_role_check(payload)
    if all([
        fast_attack_check,
        payload.emoji.name == emoji_list["attack_end"]
    ]):
        fast_attack_check = False
        clear_missions.append("m_001")

    # ラスアタ
    if all([
        last_boss_hp == 0,
        payload.emoji.name == emoji_list["attack_end"]
    ]):
        clear_missions.append("m_002")

    # 残飯処理
    if all([
        last_boss_hp == 0,
        la_mission,
        not true_dmg,
        payload.emoji.name == emoji_list["attack_end"]
    ]):
        clear_missions.append("m_003")

    # 同時凸
    if all([
        last_boss_hp == 0,
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
            last_boss_hp > 0,
            all([
                last_boss_hp == 0,
                not carryover_role_check
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
        not carryover_role_check,
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
            last_boss_hp > 0,
            all([
                last_boss_hp == 0,
                not carryover_role_check
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
        not carryover_role_check,
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
        not carryover_role_check,
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
                no_attack_role_reset = True

    # 不要なメッセージの削除
    if not clan_battle_tutorial_days:
        if message_1:
            delete_time = 60
            await message_time_delete(message_1, delete_time)


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
    cb_day = (datetime.date(now.year, now.month, now.day) - datetime.date(start_y, start_m, start_d) + timedelta(days=1)).days

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

            if all([
                member,
                member not in clan_member
            ]):
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
# ファイル
async def img_file_list(message):
    img_files = []
    async with aiohttp.ClientSession() as session:
        for n, img_url in enumerate(message.attachments):
            async with session.get(img_url.proxy_url) as resp:

                if resp.status != 200:
                    return await message.channel.send('Could not download file...')

                data = io.BytesIO(await resp.read())
                img_files.append(discord.File(data, f'image_{n}.png'))

        return img_files

# 書き込み
async def new_message(message):
    img_files = None
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
            url="attachment://image_0.png"
        )

        img_files = await img_file_list(message)
        embed.add_field(name="添付ファイル一覧》", value="\n".join(img_urls), inline=False)

    add_message = await channel.send(files=img_files, embed=embed)
    return add_message


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
    global now_clan_battl_message
    global now_boss_data
    global boss_lap
    global boss_level
    global boss_list

    boss_names = []
    boss_img_urls = []
    boss_hp_list = []
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
        boss_names.append(re.sub(r"[0-9]ボス》", "", channel.name))

    # ボス名取得
    boss_name = "【現在のボス名】"
    for name in boss_names:
        boss_name += f"\n{name}"

        # ボスサムネ取得
        async for message in boss_data_channel.history():
            if f"\n{name}\n" in message.content:
                boss_img_urls.append(message.attachments[0].proxy_url)
                break

    # 最新の凸情報取
    y = 0 if clan_battle_tutorial_days is True else 1
    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][y]))  # 進捗状況
    async for message in channel_0.history(limit=10):
        if message.embeds:
            if message.embeds[0].title:
                if re.search("[0-9]+月度クランバトル", message.embeds[0].title):
                    now_clan_battl_message = message
                    description_text = message.embeds[0].description
                    break

    # 現在のボスHP取得
    for boss_text in now_clan_battl_message.embeds[0].fields:
        text = boss_text.value
        boss_hp_text = text.replace(",", "")
        if re.search("[0-9]+/[0-9]+\n", boss_hp_text):
            boss_hp_list.append(int(re.search("[0-9]+(?=/[0-9]+\n)", boss_hp_text).group()))

    if re.search("(?<=【)[0-9]+(?=週目 ・ [0-9]段階目】)", description_text):
        boss_lap = int(re.search("(?<=【)[0-9]+(?=週目 ・ [0-9]段階目】)", description_text).group())
    else:
        boss_lap = 1
    boss_level = now_boss_level(boss_lap)

    # 不要なメッセージの削除
    async for message in channel_0.history(limit=20):
        if message.id == now_clan_battl_message.id:
            break
        else:
            await message.delete()

    # ボス情報の書き込み
    for boss, name, img_url in zip(boss_list, boss_names, boss_img_urls):
        boss_list[boss]["boss_name"] = name
        boss_list[boss]["boss_img_url"] = img_url

    # ボスHP
    if boss_hp_list:
        for boss, hp in zip(boss_list, boss_hp_list):
            boss_list[boss]["boss_hp"] = hp

    text_2 = f"{clan_battle_start_date.strftime('%Y-%m-%d %H:%M')}\n{clan_battle_end_date.strftime('%Y-%m-%d %H:%M')}"
    await channel_bot_log.send(f"ミネルヴァ起動しました。\n\n{text_1}\n{text_2}\n\n{boss_name}")


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
    data_channel = guild.get_channel(744177273053118535)  # 連絡事項データー
    general_member_role = guild.get_role(687433546775789770)  # 一般メンバーロール

    # サーバー案内
    if channel.id == 749511208104755241:
        if payload.emoji.name == "\U00002705":
            messeage = await data_channel.fetch_message(848355656733425694)
            delete_message = await channel.send(f"{payload.member.mention}{messeage.content}")
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
        data_channel = guild.get_channel(744177273053118535)  # 連絡事項データー
        announce_channel = guild.get_channel(599784496866263050)  # 連絡事項

        y = 0 if clan_battle_tutorial_days is True else 1
        channel_0 = guild.get_channel(int(clan_battle_channel_id[0][y]))  # 進捗状況

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
            now.day == 2,
            now.strftime('%H:%M') == "00:00",
            now.strftime('%H:%M:%S') <= "00:00:30"
        ]):

            t_start_date = datetime.datetime.strptime(clan_battle_start_date.strftime('%Y-%m-02 %H:%M'), "%Y-%m-%d %H:%M")
            t_end_date = datetime.datetime.strptime(clan_battle_start_date.strftime('%Y-%m-%d 00:00'), "%Y-%m-%d %H:%M")
            messeage = await data_channel.fetch_message(840613809932206100)
            announce_messeage = f"""
{messeage.content}
【模擬操作期間】
```py
《開始》
┗━ {t_start_date.month}月{t_start_date.day}日 {t_start_date.hour}時{t_start_date.minute}分
《終了》
┗━ {t_end_date.month}月{t_end_date.day}日 {t_end_date.hour}時{t_end_date.minute}分
```
【クラバト開催予定日】
```py
《開始》
┗━ {clan_battle_start_date.month}月{clan_battle_start_date.day}日 {clan_battle_start_date.hour}時{clan_battle_start_date.minute}分
《終了》
┗━ {clan_battle_end_date.month}月{clan_battle_end_date.day}日 {clan_battle_end_date.hour}時{clan_battle_end_date.minute}分
```"""

            await announce_channel.send(announce_messeage)

        # クラバト日付リセット
        if any([
            all([
                now.day >= 3,
                now.strftime('%Y-%m-%d %H:%M') < clan_battle_start_date.strftime("%Y-%m-%d 00:00")
            ]),
            all([
                now.strftime('%Y-%m-%d %H:%M') >= clan_battle_start_date.strftime('%Y-%m-%d %H:%M'),
                now.strftime('%Y-%m-%d %H:%M') < clan_battle_end_date.strftime('%Y-%m-%d %H:%M')
            ])
        ]):

            # 初日～通常更新
            if any([
                # 模擬初日～クラバト最終日
                all([
                    now.day >= 2,
                    now.strftime('%Y-%m-%d %H:%M') <= clan_battle_end_date.strftime('%Y-%m-%d %H:%M'),
                    0 < abs((datetime.datetime.strptime(now.strftime(f"%Y-%m-%d {rollover_time}:00"), '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()).total_seconds()) <= 60,
                ]),
                # 模擬終了処理
                all([
                    now.day >= 2,
                    0 < abs((datetime.datetime.strptime(clan_battle_start_date.strftime("%Y-%m-%d 00:00:00"), '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()).total_seconds()) > 60,
                ]),
                # クラバト終了
                0 < abs((datetime.datetime.strptime(clan_battle_end_date.strftime("%Y-%m-%d 00:00:00"), '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()).total_seconds()) <= 60
            ]):

                next_time = abs((datetime.datetime.strptime(now.strftime(f"%Y-%m-%d {rollover_time}:00"), '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()).total_seconds())

            # 模擬操作初日
            if 0 < abs((datetime.datetime.strptime(now.strftime(f"%Y-%m-03 {rollover_time}:00"), '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()).total_seconds()) <= 60:
                next_time = abs((datetime.datetime.strptime(now.strftime(f"%Y-%m-03 {rollover_time}:00"), '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()).total_seconds())
            # 模擬操作最終日
            elif 0 < abs((datetime.datetime.strptime(clan_battle_start_date.strftime("%Y-%m-%d 00:00:00"), '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()).total_seconds()) <= 60:
                next_time = abs((datetime.datetime.strptime(clan_battle_start_date.strftime("%Y-%m-%d 00:00:00"), '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()).total_seconds())
            # クラバト模擬最終日処理
            elif 0 < abs((clan_battle_start_date - datetime.datetime.now()).total_seconds()) <= 60:
                next_time = abs((clan_battle_start_date - datetime.datetime.now()).total_seconds())
            # クラバト初日
            elif 0 < abs((clan_battle_start_date - datetime.datetime.now()).total_seconds()) <= 60:
                next_time = abs((clan_battle_start_date - datetime.datetime.now()).total_seconds())
            # クラバト最終日処理
            elif 0 < abs((clan_battle_end_date - datetime.datetime.now()).total_seconds()) <= 60:
                next_time = abs((clan_battle_end_date - datetime.datetime.now()).total_seconds())

            # 更新時間まで待機
            if 0 < next_time <= 60:
                await asyncio.sleep(next_time)
                now = datetime.datetime.now()

            # クラバト初日処理
            if any([
                now.strftime('%Y-%m-%d %H:%M') == clan_battle_start_date.strftime(f'%Y-%m-03 {rollover_time}'),
                now.strftime('%Y-%m-%d %H:%M') == clan_battle_start_date.strftime("%Y-%m-%d %H:%M")
            ]):

                if now.strftime('%Y-%m-%d %H:%M') == clan_battle_start_date.strftime("%Y-%m-%d %H:%M"):
                    clan_battle_tutorial_days = True
                    channel_0 = guild.get_channel(int(clan_battle_channel_id[0][1]))  # 進捗状況

                embed = discord.Embed(
                    description="残り凸情報のリセット処理中です。\nしばらくお待ちください。",
                    colour=0xffff00
                )
                reset_role_text = await channel_0.send(embed=embed)

                await clan_battl_start_up(now, new_lap_check=True)
                await reset_role_text.delete()
                await asyncio.sleep(60)

            # 日付変更リセット
            elif now.strftime('%H:%M') == set_rollover_time:

                for boss_no in now_attack_list:
                    if now_attack_list[boss_no]:
                        no_attack_role_reset = False
                        return

                else:
                    embed = discord.Embed(
                        description="残り凸情報のリセット処理中です。\nしばらくお待ちください。",
                        colour=0xffff00
                    )
                    reset_role_text = await channel_0.send(embed=embed)

                    await clan_battl_role_reset(now, new_lap_check=False)
                    await reset_role_text.delete()
                    no_attack_role_reset = True
                    await asyncio.sleep(60)

        # クラバト終了処理
        if any([
            now.strftime('%Y-%m-%d %H:%M') == clan_battle_start_date.strftime("%Y-%m-%d 00:00"),
            now.strftime('%Y-%m-%d %H:%M') == clan_battle_end_date.strftime('%Y-%m-%d %H:%M')
        ]):

            for boss_no in now_attack_list:
                if now_attack_list[boss_no]:
                    no_attack_role_reset = False
                    return

            else:
                await clan_battl_role_reset(now, new_lap_check=False)
                no_attack_role_reset = True
                await asyncio.sleep(60)

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
            if any([
                payload.emoji.name == emoji_list["attack_p"],
                payload.emoji.name == emoji_list["attack_m"],
                payload.emoji.name == emoji_list["T_kill"],
                payload.emoji.name == emoji_list["SOS"]
            ]):
                await clan_battl_call_reaction(payload)

            elif payload.emoji.name == emoji_list["attack_end"]:
                await clan_battl_end_reaction(payload)

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
                now = datetime.datetime.now()
                await clan_battl_start_up(now, new_lap_check=True)

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
        if message.channel.id != 750345983661047949 or message.channel.id != 772305554009620480:
            await new_message(message)

    except Exception as e:
        await error_log(e_name=e.__class__.__name__, e_log=traceback.format_exc())

client.run(TOKEN)
