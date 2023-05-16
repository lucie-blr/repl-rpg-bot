import os, discord, datetime
from discord.ext import commands, tasks
from discord.commands import SlashCommandGroup, Option


from api.actor import *
from api.character import *
from api.enemy import *
from api.area import *
from api.helper_function import *
from api.gamemode import *
from api.spell import *
from api.game import *

import yaml

# Helper functions

MODE_COLOR = {
    GameMode.BATTLE: 0xDC143C,
    GameMode.ADVENTURE: 0x005EB8,
    GameMode.DEAD: 0x333333,
}
def status_embed(ctx, character):

    # Current mode
    if character.mode == GameMode.BATTLE:
        mode_text = f"Entrain de combattre /"
    elif character.mode == GameMode.ADVENTURE:
        mode_text = "En pleine exploration."
    elif character.mode == GameMode.DEAD:
        mode_text = "Actuellement mort."

    # Create embed with description as current mode
    embed = discord.Embed(title=f"{character.name} status", description=mode_text, color=MODE_COLOR[character.mode])
    embed.set_author(name=ctx.author.display_name)

    return embed

DISCORD_TOKEN = (yaml.safe_load(open('./config.yml'))).get("token")

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!")
        self.game = Game()

bot = Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

    bot.game.loadDb()

    mob_attack.start()
    auto_heal.start()
    classement.start()

    await bot.change_presence(activity=discord.Game(name="/status"))

@tasks.loop(seconds=300)
async def auto_save():
    bot.game.save_to_db()

@tasks.loop(seconds=60)
async def classement():
    classement = yaml.safe_load(open('./classement.yml'))

    for message in classement:
        message = classement.get(message)
        guild = bot.get_guild(887675595419451396)

        channel = guild.get_channel(message[0])

        message = await channel.fetch_message(message[1])

        embed=discord.Embed(title="Classement", description="Classement du nombre de loups tués.", color=0xff0000)

        d = {}

        for character in bot.game.characters.characters.values():

            defeated = character.defeated

            v = 0

            try:
                v += defeated.get("lone_wolf")
            except:
                v = v
            try:
                v += defeated.get("boss_lone_wolf")
            except:
                v = v

            d[character.user_id] = v


        l = list(d.values())

        l.sort(reverse=True)

        ch = bot.game.characters.get(list(filter(lambda x: d[x] == l[0], d))[0])    

        embed.set_thumbnail(url=(ch.skin))

        for i in range(len(l)):
            key = list(filter(lambda x: d[x] == l[i], d))[0]

            ch = bot.game.characters.get(key)

            embed.add_field(name=f"{ch.name}", value=f"{(d[key])}")

            d.pop(key, None)

        await message.edit("", embed=embed)

@tasks.loop(seconds=10)
async def auto_heal():
    characters = bot.game.characters.characters

    for character in characters.values():

        ready, xp_needed = character.ready_to_level_up()

        if ready:

            area = bot.game.area.getArea(character.area_id)

            success, new_level = character.level_up("adb")

            guild = bot.get_guild(887675595419451396)

            channel = guild.get_channel(area.channel_id)

            if success:
                await channel.send(f"{character.name} est monté au niveau {new_level}, gagnant 1 adb.")
            else:
                await channel.send(f"{character.name} n'a pas réussi à monter de niveau.")

        if character.mode == GameMode.BATTLE:
            if character.mana < character.max_mana:
                character.mana += int(round(character.max_mana * (5/100)))

                character.save_to_db()

        if character.mode == GameMode.ADVENTURE:

            if character.mana < character.max_mana:
                character.mana += int(round(character.max_mana * (20/100)))

                if character.mana > character.max_mana:
                    character.mana = character.max_mana

            if character.hp < character.max_hp:

                character.hp += int(round(character.max_hp * (5/100)))

            if character.hp > character.max_hp:
                character.hp = character.max_hp

            character.save_to_db()

@tasks.loop(seconds=3)
async def mob_attack():

    areas = bot.game.areas.areas

    for area in areas.values():

        if area.type == AreaType.PVE_AREA:
            try:
                for enemy_id in area.battling.keys():
                    enemy = area.battling.get(enemy_id)

                    battling_dict = enemy.battling

                    l = list(battling_dict.values())

                    l.sort(reverse=True)

                    if len(list(battling_dict.keys())) <= 0:
                        enemy.hp = 0

                        area.battling.pop(enemy_id, None)

                        area.entitys[enemy_id] = enemy

                        area.save_to_db()

                        continue

                    key = list(filter(lambda x: battling_dict[x] == l[0], battling_dict))[0]

                    character = bot.game.characters.get(key)

                    damage, killed, _ = enemy.fight(character)

                    embed=discord.Embed(title="Fight", description=f"{character.name} vs {enemy.name}", color=0xff0000)
                    embed.set_thumbnail(url=f"{enemy.skin}")
                    embed.add_field(name=f"Historique", value=f"{enemy.name} a fait {damage} dégâts à {character.name}", inline=False)
                    embed.add_field(name=f"{character.name}", value=f"""{endurance_bar(character)}
""", inline=False)
                    embed.add_field(name=f"{enemy.name}", value=f"{endurance_bar(enemy)}", inline=True)

                    guild = bot.get_guild(enemy.battle_message[2])

                    channel = guild.get_channel(enemy.battle_message[1])

                    message = await channel.fetch_message(enemy.battle_message[0])

                    if killed:
                        enemy.battling.pop(key, None)

                        area.save_to_db()

                        character.die()

                        embed.add_field(name=f"Perdu !", value=f"{enemy.name} a tué {character.name}", inline=False)

                        await message.edit(embed=embed, view=None)
                    else:

                        await message.edit(embed=embed)

            except RuntimeError:
                continue

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond("This command is currently on cooldown!", ephemeral=True)
    else:
        raise error  # Here we raise other errors to ensure they aren't ignored

cmd = SlashCommandGroup("rpg", "Commands for server management!")

# Commands
@bot.slash_command(name="create", help="Create a character.")
async def create(ctx, character_name=None):
    user_id = ctx.author.id

    # if no name is specified, use the creator's nickname
    if character_name == None:
        character_name = ctx.author.name

    # create characters dictionary if it does not exist
    characters = bot.game.characters.characters

    # only create a new character if the user does not already have one
    if user_id not in characters:
        character = Character(**{
            "name": character_name,
            "hp": 20,
            "max_hp": 20,
            "attack": [30,90],
            "defense": 1,
            "mana": 0,
            "max_mana": 10,
            "spells": ["firebolt"],
            "level": 1,
            "xp": 0,
            "gold": 0,
            "inventory": [],
            "mode": ['ADVENTURE'],
            "battling": None,
            "user_id": user_id,
            "area_id": "forest",
            "adb": 10,
            "skin": "https://media.discordapp.net/attachments/619262155685888000/1064618259158147173/Illustration79.png"
        })
        character.save_to_db()
        character = bot.game.characters.load(user_id)
        await ctx.respond(f"Nouveau personnage niveau 1 créé : {character_name}. Entrez `/status` pour voir vos stats.")
    else:
        await ctx.respond("Vous avez déjà créé votre personnage.")

@bot.slash_command(name="pt")
async def pt(ctx):
    character = bot.game.characters.get(ctx.author.id)
    character.hp = character.hp/2

@bot.slash_command(name="status", help="Get information about your character.")
async def status(ctx):

    character = bot.game.characters.get(ctx.author.id)

    embed = status_embed(ctx, character)

        # Stats field
    _, xp_needed = character.ready_to_level_up()

    embed.add_field(name="Stats", value=f"""
**HP:**    {character.hp}/{character.max_hp}
{endurance_bar(character)}

**ATTACK:**   {character.adb}
**DEFENSE:**   {character.defense}

**LEVEL:** {character.level}
**XP:**    {character.xp}/{character.xp+xp_needed}
{xp_bar(character)}

**AREA:** {character.area_id}
    """, inline=True)

    # Inventory field
    inventory_text = f"Gold: {character.gold}\n"
    if character.inventory:
        for item_id in character.inventory.keys():
            item = Item(item_id)

            inventory_text += f"\n**{item.name}**\n{item.description}\n{character.inventory.get(item_id)}\n"

    embed.add_field(name="Inventory", value=inventory_text, inline=True)

    if character.skin != None:
        embed.set_thumbnail(url=character.skin)

    await ctx.respond(embed=embed)

class FightView(discord.ui.View):

    @discord.ui.button(label="Flee!", style=discord.ButtonStyle.grey, emoji="🏃") # Create a button with the label "😎 Click me!" with color Blurple
    async def flee_callback(self, button, interaction):

        character = bot.game.characters.get(interaction.user.id)

        area = bot.game.areas.get(character.area_id)

        if interaction.channel.id != area.channel_id:
            await interaction.reponse.respond("Vous ne pouvez utiliser cette commande que quand des channels de jeu.!")
            return

        if character.mode == GameMode.DEAD:
            await interaction.response.respond("Vous ne pouvez rien faire tant que vous êtes morts.")
            return

        if character.mode != GameMode.BATTLE:
            await interaction.response.respond("Vous ne pouvez pas appeler cette commande en combat!")
            return


        enemy_id = character.battling
        enemy = area.battling.get(enemy_id)
        damage, killed, _ = character.flee(enemy)

        embed=discord.Embed(title="Fight", description=f"{character.name} vs {enemy.name}", color=0xff0000)
        embed.set_thumbnail(url=f"{enemy.skin}")

        if killed:
            character.die()
            embed.add_field(name=f"{character.name}", value=f"""{endurance_bar(character)}
""", inline=False)
            embed.add_field(name= "Fuite", value=f"{character.name} est mort en essayant de fuir {enemy.name}, et n'est plus. Rest in peace, brave aventurier.")
        elif damage:
            embed.add_field(name=f"{character.name}", value=f"""{endurance_bar(character)}
""", inline=False)
            embed.add_field(name= "Fuite", value=f"{character.name} fuit {enemy.name}, et prend {damage} dégâts. HP: {character.hp}/{character.max_hp}")
        else:
            embed.add_field(name=f"{character.name}", value=f"""{endurance_bar(character)}
""", inline=False)
            embed.add_field(name= "Fuite", value=f"{character.name} fuit {enemy.name} Avec sa vie intact, mais pas sa dignité. HP: {character.hp}/{character.max_hp}")

        await interaction.response.edit_message(embed=embed) # Send a message when the button is clicked


async def spell_callback(interaction):
    channel = interaction.channel

    select = interaction.data

    values = select.get("values")

    user = interaction.user

    character = bot.game.characters.get(user.id)

    spell = character.spells.get(values[0])

    area = bot.game.areas.get(character.area_id)

    enemy = area.battling.get(character.battling)

    embed=discord.Embed(title="Fight", description=f"{character.name} vs {enemy.name}", color=0xff0000)
    embed.set_thumbnail(url=f"{enemy.skin}")


    damage, killed = 0, False
    if time.time() - spell.last_use >= spell.cooldown:
        spell.last_use = time.time()
        damage, killed, spell = character.fight(enemy=enemy, attack=spell)
        character.mana -= spell.mana_cost
        embed.add_field(name=f"Historique", value=f"{character.name} a fait {damage} dégâts à {enemy.name} avec {spell.name}", inline=False)
    else:
        embed.add_field(name=f"Historique", value=f"{character.name} tente de lancer {spell.name} mais n'y arrive pas !", inline=False)

    embed.add_field(name=f"{character.name}", value=f"""{endurance_bar(character)}
""", inline=False)
    if killed:
        enemy.battling = {}
        t = "<:emptybarleft:1068151816946204742><:emptybarmiddle:1068151825418702878><:emptybarmiddle:1068151825418702878><:emptybarmiddle:1068151825418702878><:emptybarmiddle:1068151825418702878><:emptybarmiddle:1068151825418702878><:emptybarmiddle:1068151825418702878><:emptybarright:1068151820922388510>"
        embed.add_field(name=f"{enemy.name}", value=f"{t}", inline=True)
        xp, gold, ready_to_level_up = character.defeat(enemy)
        embed.add_field(name=f"{character.name} gagne !", value=f"Et gagne {gold} gold, {xp} XP !", inline=False)
    else:
        embed.add_field(name=f"{enemy.name}", value=f"{endurance_bar(enemy)}", inline=True)

    message = interaction.response

    if killed:
        await message.edit_message(embed=embed, view=None)
    else:
        spells = character.spells

        options = []

        for spell in spells.values():

            options.append(discord.SelectOption(label=spell.name, value=spell.id, emoji=spell.emoji))

        select = discord.ui.Select(options = options, min_values=1, max_values=1)

        select.callback = spell_callback

        view = FightView()

        view.add_item(item=select)

        await message.edit_message(embed=embed, view=view)


@bot.slash_command(name="hunt", help="Look for an enemy to fight.")
@commands.cooldown(1,1)
async def hunt(ctx):
    character = bot.game.characters.get(ctx.author.id)
    area = bot.game.areas.get(character.area_id)

    if ctx.channel.id != area.channel_id:
        await ctx.respond("Vous ne pouvez utiliser cette commande que quand des channels de jeu.")
        return

    if area.type != AreaType.PVE_AREA:
        await ctx.respond("Vous ne pouvez pas chasser dans cette zone.")

    if character.mode == GameMode.DEAD:
        await ctx.respond("Vous ne pouvez rien faire tant que vous êtes morts.")
        return

    if character.mode != GameMode.ADVENTURE:
        await ctx.respond("Vous ne pouvez pas appeler cette commande en combat!")
        return

    enemys = []

    if area.type == AreaType.PVE_AREA:
        for entity in area.entitys.keys():

            enemy = area.entitys.get(entity)

            if time.time() - enemy.last_death >= enemy.respawn:

                enemys.append(entity)

    enemy_id = None
    enemy = None

    if len(enemys) <= 0:
        enemy_id = None

    else:
        enemy_id = random.choice(enemys)
        enemy = area.entitys.get(enemy_id)


    if enemy_id == None:
        await ctx.respond("Aucun ennemi trouvé dans la zone.")
        return

    if not enemy_id in area.entitys.keys():
        await ctx.respond(f"{enemy.name} n'est pas dans la zone !")
        return

    character.mode = GameMode.BATTLE
    character.battling = enemy_id

    area.entitys.pop(enemy_id, None)

    area.battling[enemy_id] = enemy


    enemy.battling = {}
    enemy.battling[ctx.author.id] = 0

    enemy.hp = enemy.max_hp

    embed=discord.Embed(title="Fight", description=f"{character.name} vs {enemy.name}", color=0xff0000)
    embed.set_thumbnail(url=f"{enemy.skin}")
    embed.add_field(name=f"{character.name}", value=f"""{endurance_bar(character)}
""", inline=False)
    embed.add_field(name=f"{enemy.name}", value=f"{endurance_bar(enemy)}", inline=True)

    spells = character.spells

    options = []

    for spell in spells.values():

        options.append(discord.SelectOption(label=spell.name, value=spell.id, emoji=spell.emoji))

    select = discord.ui.Select(options = options, min_values=1, max_values=1)

    select.callback = spell_callback

    view = FightView()

    view.add_item(item=select)

    # Send reply
    message = await ctx.send(embed=embed, view=view)

    await ctx.respond("You enter in fight !")

    enemy.battle_message = [message.id, message.channel.id, message.guild.id]

    area.save_to_db()


@bot.slash_command(name="levelup", help="Advance to the next level. Specify a stat to increase (HP, ATTACK, DEFENSE).")
@commands.cooldown(1,1)
async def levelup(ctx,
    increase:Option(str, "increase", choices=['ATTACK', 'DEFENSE'], required=True)):
    character = bot.game.characters.get(ctx.author.id)

    if character.mode == GameMode.DEAD:
        await ctx.respond("Vous ne pouvez rien faire tant que vous êtes morts.")
        return

    if character.mode != GameMode.ADVENTURE:
        await ctx.respond("Vous ne pouvez pas appeler cette commande en combat/")
        return

    ready, xp_needed = character.ready_to_level_up()
    if not ready:
        await ctx.respond(f"Vous avez besoin de {xp_needed} pour monter au niveau {character.level+1}")
        return

    if not increase:
        await ctx.respond("Veuillez spécifier une statistique à améliorer. (ATTACK, DEFENSE)")
        return

    increase = increase.lower()
    if increase == "hp" or increase == "hitpoints" or increase == "max_hp" or increase == "maxhp":
        increase = "max_hp"
    elif increase == "attack" or increase == "att":
        increase = "adb"
    elif increase == "defense" or increase == "def" or increase == "defence":
        increase = "defense"

    success, new_level = character.level_up(increase)
    if success:
        await ctx.respond(f"{character.name} est monté au niveau {new_level}, gagnant 1 {increase.upper().replace('_', ' ')}.")
    else:
        await ctx.respond(f"{character.name} n'a pas réussi à monter de niveau.")


@bot.slash_command(name="die", help="Destroy current character.")
async def die(ctx):
    character = bot.game.characters.get(ctx.author.id)

    character.die()

    await ctx.respond(f"Le personnage {character.name} n'est plus. soignez vous avec `/heal`.")

@bot.slash_command(name="reset", help="[DEV] Destroy and recreate current character.")
async def reset(ctx):
    user_id = str(ctx.author.id)

    if user_id in db["characters"].keys():
        del db["characters"][user_id]

    await ctx.respond(f"Character deleted.")
    await create(ctx)


@bot.slash_command(name="heal", help="Heal character")
async def heal(ctx):
    character = bot.game.characters.get(ctx.author.id)

    if character.mode == GameMode.BATTLE:
        await ctx.respond("Vous ne pouvez pas appeler cette commande en combat.")
        return

    character.hp = character.max_hp

    if character.mode == GameMode.DEAD:
        character.mode = GameMode.ADVENTURE

    await ctx.respond(f"Le personnage {character.name} a été soigné.")

async def area_callback(interaction):
    channel = interaction.channel

    select = interaction.data

    values = select.get("values")

    area = Area(values[0])

    user = interaction.user

    new_channel = interaction.guild.get_channel(area.channel_id)

    perms = channel.overwrites_for(user)

    perms.view_channel = False

    await channel.set_permissions(target=user,overwrite= perms)

    perms = new_channel.overwrites_for(user)

    perms.view_channel = True

    await new_channel.set_permissions(target=user, overwrite=perms)

    character = bot.game.characters.get(user.id)

    character.area_id = values[0]

    await new_channel.send(f"Bienvenue {character.name} dans {area.name} !")


@bot.slash_command(name="move", help="Change the area of the character")
async def move(ctx):
    character = bot.game.characters.get(ctx.author.id)

    if character.mode == GameMode.DEAD:
        await ctx.respond("Vous ne pouvez rien faire tant que vous êtes morts.")
        return

    if character.mode!= GameMode.ADVENTURE:
        await ctx.respond("Vous ne pouvez pas appeler cette commande en combat.")
        return

    area = bot.game.areas.get(character.area_id)

    nearby = area.nearby

    options = []

    for area_id in nearby:
        new_area = Area(area_id)

        options.append(discord.SelectOption(label=new_area.name, value=area_id))

    select = discord.ui.Select(options = options, min_values=1, max_values=1)

    select.callback = area_callback

    view = discord.ui.View()

    view.add_item(item=select)

    await ctx.respond("Où voulez-vous aller ?", view = view, ephemeral=True)


@bot.slash_command(name="statistics", help="Get how much mobs you have killed.")
async def statistics(ctx):
    character = bot.game.characters.get(ctx.author.id)

    t = ""

    for enemy_type in character.defeated:
        t += f"\n{enemy_type} : {character.defeated[enemy_type]}"

    embed=discord.Embed(title="Stats", description="Nombre de monstres que vous avez tué :", color=0xff0000)
    embed.add_field(name="", value=t, inline=False)
    await ctx.respond(embed=embed)


@bot.slash_command(name="save")
async def save(ctx):
    bot.game.save_to_db()

    await ctx.respond("Game saved.")

    await bot.change_presence(activity=None)

    os.system('pm2 restart PeripleRpg')

@bot.slash_command(name="stop")
async def stop(ctx):
    bot.game.save_to_db()

    await ctx.respond('Game saved')

    os.system('pm2 stop PeripleRpg')

async def equip_callback_one(interaction):
    character = bot.game.characters.get(interaction.user.id)

    message = interaction.response

    item_type = interaction.data

    options = []

    for item_id in character.inventory.keys():
        item = Item(item_id)

        options.append(discord.SelectOption(label="Aucun item", value="none"))

        if item.type == item_type:

            options.append(discord.SelectOption(label=item.name, value=item_id))

    select = discord.ui.Select(options = options, min_values=1, max_values=1)

    select.callback = equip_callback_two

    view = discord.ui.View()

    view.add_item(item=select)

    embed=discord.Embed(title="Stuff", description="With witch item ?", color=0xff0000)

    await message.edit_message(embed=embed, view = view)
        
async def equip_callback_two(interaction):

    if interaction.data != "none":

        character = bot.game.characters.get(interaction.user.id)

        message = interaction.message 

        character.inventory[interaction.data] = character.inventory.get(interaction.data) - 1

        if character.inventory[interaction.data] <= 0:
            character.inventory.pop(interaction.value, False)
        
        character.equip(Item(interaction.data))

        embed=discord.Embed(title="Stuff", description=f"You equiped {(Item(interaction.data)).name} ", color=0xff0000)

    else:
        character.equip(None)

        embed=discord.Embed(title="Stuff", description=f"You unequiped your item.", color=0xff0000)

    
    message.edit_message(embed=embed, view = None)


@bot.slash_command(name="equip", help="Equip an item in inventory slot")
async def equip(ctx):
    character = bot.game.characters.get(ctx.author.id)

    if character.mode == GameMode.DEAD:
        await ctx.respond("Vous ne pouvez rien faire tant que vous êtes morts.")
        return

    if character.mode != GameMode.ADVENTURE:
        await ctx.respond("Vous ne pouvez pas appeler cette commande en combat.")
        return

    item_types = character.stuff.keys()

    options = []

    for item_type in item_types:

        options.append(discord.SelectOption(label=item_type, value=item_type))

    select = discord.ui.Select(options = options, min_values=1, max_values=1)

    select.callback = equip_callback_one

    view = discord.ui.View()

    view.add_item(item=select)

    embed=discord.Embed(title="Stuff", description="What piece do you wanna change ?", color=0xff0000)

    await ctx.respond(embed=embed, view = view, ephemeral=True)

bot.run(DISCORD_TOKEN)
