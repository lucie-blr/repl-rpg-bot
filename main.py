import os, discord
from discord.ext import commands, tasks
from discord.commands import SlashCommandGroup, Option


from api.actor import *
from api.character import *
from api.enemy import *
from api.area import *
from api.helper_function import *
from api.gamemode import *

import yaml

# Helper functions
def load_character(user_id):
    character_dict = yaml.safe_load(open(f'./database/characters/{user_id}.yml'))

    return Character(**character_dict)

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

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    mob_attack.start()

@tasks.loop(seconds=3)
async def mob_attack():
    areas = []
    for filename in os.listdir('./database/areas'):
        if filename.endswith('.yml'):
            areas.append(filename[:-4])
        
    for area_id in areas:
        area = Area(area_id)

        if area.type == AreaType.PVE_AREA:
            for enemy_id in area.battling.keys():
                enemy_dict = area.battling.get(enemy_id)

                enemy = Enemy(**enemy_dict)

                battling_dict = enemy.battling

                l = list(battling_dict.values())
                
                l.sort(reverse=True)

                if len(list(battling_dict.keys())) <= 0:
                    enemy.hp = 0

                    area.rehydrate()

                    area.save_enemy(enemy, enemy_id)

                    area.save_to_db()

                    continue
                
                key = list(filter(lambda x: battling_dict[x] == l[0], battling_dict))[0]

                character = load_character(key)

                damage, killed = enemy.fight(character)

                character.save_to_db()

                print(f"{enemy.name} damage {damage} to {character}.")

                embed=discord.Embed(title="Fight", description=f"{character.name} vs {enemy.name}", color=0xff0000)
                embed.set_thumbnail(url=f"{enemy.skin}")
                embed.add_field(name=f"{character.name} life", value=f"{endurance_bar(character)}", inline=True)
                embed.add_field(name=f"{enemy.name} life", value=f"{endurance_bar(enemy)}", inline=True)

                guild = bot.get_guild(enemy.battle_message[2])

                channel = guild.get_channel(enemy.battle_message[1])

                message = await channel.fetch_message(enemy.battle_message[0])

                await message.edit(embed=embed)

                if killed:
                    enemy.battling.pop(key, None)
                    
                    area.rehydrate()

                    area.save_enemy(enemy, enemy_id)

                    area.save_to_db()

                    character.die()


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
    characters = []
    for filename in os.listdir('./database/characters'):
        if filename.endswith('.yml'):
            characters.append(filename[:-4])

    # only create a new character if the user does not already have one
    if user_id not in characters:
        character = Character(**{
            "name": character_name,
            "hp": 20,
            "max_hp": 20,
            "attack": [30,90],
            "defense": 1,
            "mana": 0,
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
        await ctx.respond(f"Nouveau personnage niveau 1 créé : {character_name}. Entrez `/status` pour voir vos stats.")
    else:
        await ctx.respond("Vous avez déjà créé votre personnage.")


@bot.slash_command(name="status", help="Get information about your character.")
async def status(ctx):

    character = load_character(ctx.author.id)

    embed = status_embed(ctx, character)

        # Stats field
    _, xp_needed = character.ready_to_level_up()

    embed.add_field(name="Stats", value=f"""
**HP:**    {character.hp}/{character.max_hp}
{endurance_bar(character)}
**ATTACK:**   {character.adb}
**DEFENSE:**   {character.defense}
**MANA:**  {character.mana}
**LEVEL:** {character.level}
**XP:**    {character.xp}/{character.xp+xp_needed}
{xp_bar(character)}
**AREA:** {character.area_id}
    """, inline=True)

    # Inventory field
    inventory_text = f"Gold: {character.gold}\n"
    if character.inventory:
        inventory_text += "\n".join(character.inventory)
    
    embed.add_field(name="Inventory", value=inventory_text, inline=True)

    if character.skin != None:
        embed.set_thumbnail(url=character.skin)

    await ctx.respond(embed=embed) 

class FightView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    @discord.ui.button(label="Attack!", style=discord.ButtonStyle.primary, emoji="😎") # Create a button with the label "😎 Click me!" with color Blurple
    async def attack_callback(self, button, interaction):
        character = load_character(interaction.user.id)
        area = Area(character.area_id)

        if interaction.channel.id != area.channel_id:
            return

        if character.mode == GameMode.DEAD:
            return

        if character.mode != GameMode.BATTLE:
            return

        # Simulate battle
        enemy_id = character.battling
        area.rehydrate()
        enemy_dict = area.battling.get(enemy_id)
        enemy = Enemy(**enemy_dict)

        damage, killed = character.fight(enemy)

        embed=discord.Embed(title="Fight", description=f"{character.name} vs {enemy.name}", color=0xff0000)
        embed.set_thumbnail(url=f"{enemy.skin}")
        embed.add_field(name=f"{character.name} life", value=f"{endurance_bar(character)}", inline=True)
        
        if killed:
            t = ""
            for i in range(0, 10):
                t +=":red_square:"
            embed.add_field(name=f"{enemy.name} life", value=t, inline=True)
            xp, gold, ready_to_level_up = character.defeat(enemy)
            embed.add_field(name=f"{character.name} gagne !", value=f"Et gagne {gold} gold, {xp} XP !", inline=False)
        else:
            embed.add_field(name=f"{enemy.name} life", value=f"{endurance_bar(enemy)}", inline=True)

        guild = bot.get_guild(enemy.battle_message[2])

        channel = guild.get_channel(enemy.battle_message[1])

        message = await channel.fetch_message(enemy.battle_message[0])
        if killed:
            await message.edit(embed=embed, view=None)
        else:
            await message.edit(embed=embed, view=FightView())

        await interaction.response.send_message(f"Vous avez fait {damage} dégats !", ephemeral=True)


    @discord.ui.button(label="Flee!", style=discord.ButtonStyle.primary, emoji="😎") # Create a button with the label "😎 Click me!" with color Blurple
    async def flee_callback(self, button, interaction):

        character = load_character(interaction.user.id)
        area = Area(character.area_id)

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
        area.rehydrate()
        enemy_dict = area.battling.get(enemy_id)
        enemy = Enemy(**enemy_dict)
        damage, killed = character.flee(enemy)

        embed=discord.Embed(title="Fight", description=f"{character.name} vs {enemy.name}", color=0xff0000)
        embed.set_thumbnail(url=f"{enemy.skin}")
        

        if killed:
            character.die()
            embed.add_field(name=f"{character.name} life", value=f"{endurance_bar(character)}", inline=True)
            embed.add_field(name= "Fuite", value=f"{character.name} est mort en essayant de fuir {enemy.name}, et n'est plus. Rest in peace, brave aventurier.")
        elif damage:
            embed.add_field(name=f"{character.name} life", value=f"{endurance_bar(character)}", inline=True)
            embed.add_field(name= "Fuite", value=f"{character.name} fuit {enemy.name}, et prend {damage} dégâts. HP: {character.hp}/{character.max_hp}")
        else:
            embed.add_field(name=f"{character.name} life", value=f"{endurance_bar(character)}", inline=True)
            embed.add_field(name= "Fuite", value=f"{character.name} fuit {enemy.name} Avec sa vie intact, mais pas sa dignité. HP: {character.hp}/{character.max_hp}")

        await interaction.response.edit(embed) # Send a message when the button is clicked

    # @discord.ui.button(label="Spell!", style=discord.ButtonStyle.primary, emoji="😎")
    # async def spell_callback(self,button,interaction):
    #     character = load_character(interaction.user.id)
    #     area = Area(character.area_id)

    #     if interaction.channel.id != area.channel_id:
    #         return

    #     if character.mode == GameMode.DEAD:
    #         return

    #     if character.mode != GameMode.BATTLE:
    #         return

    #     # Simulate battle
    #     enemy_id = character.battling
    #     area.rehydrate()
    #     enemy_dict = area.battling.get(enemy_id)
    #     enemy = Enemy(**enemy_dict)

    #     damage, killed = character.fight(enemy)

    #     embed=discord.Embed(title="Fight", description=f"{character.name} vs {enemy.name}", color=0xff0000)
    #     embed.set_thumbnail(url=f"{enemy.skin}")
    #     embed.add_field(name=f"{character.name} life", value=f"{endurance_bar(character)}", inline=True)
        
    #     if killed:
    #         t = ""
    #         for i in range(0, 10):
    #             t +=":red_square:"
    #         embed.add_field(name=f"{enemy.name} life", value=t, inline=True)
    #         xp, gold, ready_to_level_up = character.defeat(enemy)
    #         embed.add_field(name=f"{character.name} gagne !", value=f"Et gagne {gold} gold, {xp} XP !", inline=False)
    #     else:
    #         embed.add_field(name=f"{enemy.name} life", value=f"{endurance_bar(enemy)}", inline=True)

    #     guild = bot.get_guild(enemy.battle_message[2])

    #     channel = guild.get_channel(enemy.battle_message[1])

    #     message = await channel.fetch_message(enemy.battle_message[0])
    #     if killed:
    #         await message.edit(embed=embed, view=None)
    #     else:
    #         await message.edit(embed=embed, view=FightView())

    #     await interaction.response.send_message(f"Vous avez fait {damage} dégats !", ephemeral=True)



@bot.slash_command(name="hunt", help="Look for an enemy to fight.")
@commands.cooldown(1,15)
async def hunt(ctx):
    character = load_character(ctx.author.id)
    area = Area(character.area_id)

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

    enemy_id = character.hunt()

    area.rehydrate()

    if enemy_id == None:
        await ctx.respond("Aucun ennemi trouvé dans la zone.")
        return
    
    if not enemy_id in area.battling.keys():
        await ctx.respond(f"{enemy_id} n'est pas dans la zone !")
        return

    enemy = Enemy(**(area.battling.get(enemy_id)))

    enemy.battling[ctx.author.id] = 0

    embed=discord.Embed(title="Fight", description=f"{character.name} vs {enemy.name}", color=0xff0000)
    embed.set_thumbnail(url=f"{enemy.skin}")
    embed.add_field(name=f"{character.name} life", value=f"{endurance_bar(character)}", inline=True)
    embed.add_field(name=f"{enemy.name} life", value=f"{endurance_bar(enemy)}", inline=True)

    # Send reply
    message = await ctx.send(embed=embed, view=FightView())

    await ctx.respond("You enter in fight !")

    enemy.battle_message = [message.id, message.channel.id, message.guild.id]

    area.save_enemy(enemy, enemy_id)

    area.save_to_db()
    

#@bot.slash_command(name="fight", help="Fight the current enemy.")
#@commands.cooldown(1,2)
#async def fight(ctx):
#    character = load_character(ctx.author.id)
#    area = Area(character.area_id)
#
#    if ctx.channel.id != area.channel_id:
#        await ctx.respond("Vous ne pouvez utiliser cette commande que quand des channels de jeu.!")
#        return
#    
#    if character.mode == GameMode.DEAD:
#        await ctx.respond("Vous ne pouvez rien faire tant que vous êtes morts.")
#        return
#
#    if character.mode != GameMode.BATTLE:
#        await ctx.respond("Vous ne pouvez pas appeler cette commande en combat!")
#        return
#        
#    # Simulate battle
#    enemy_id = character.battling
#    area.rehydrate()
#    enemy_dict = area.battling.get(enemy_id)
#    enemy = Enemy(**enemy_dict)
#
#    # Character attacks
#    damage, killed = character.fight(enemy)
#    if damage:
#        await ctx.respond(f"{character.name} attaque {enemy.name}, et fait {damage} dégâts !")
#    else:
#        await ctx.respond(f"{character.name} essaye d'attaquer {enemy.name}, mais râte !")
#
#        # End battle in victory if enemy killed
#    if killed:
#        xp, gold, ready_to_level_up = character.defeat(enemy)
#        
#        await ctx.respond(f"{character.name} a vaincu le {enemy.name}, et gagne {xp} XP et {gold} GOLD. HP: {character.hp}/{character.max_hp}.")
#        
#        if ready_to_level_up:
#            await ctx.respond(f"{character.name} a gagné assez d'XP pour monter au niveau {character.level+1}. Entrez `/levelup` avec la stat (ATTACK, DEFENSE) que vous voudriez amméliorer. e.g. `/levelup defense` ou `/levelup attack`.")
#            
#        return
#    
#        # No deaths, battle continues
#    await ctx.respond(f"La bataille fait rage ! Est-ce que vous `/fight` ou `/flee`?")

@bot.slash_command(name="flee", help="Flee the current enemy.")
@commands.cooldown(1,15)
async def flee(ctx):
    character = load_character(ctx.author.id)
    area = Area(character.area_id)

    if ctx.channel.id != area.channel_id:
        await ctx.respond("Vous ne pouvez utiliser cette commande que quand des channels de jeu.!")
        return

    if character.mode == GameMode.DEAD:
        await ctx.respond("Vous ne pouvez rien faire tant que vous êtes morts.")
        return
    
    if character.mode != GameMode.BATTLE:
        await ctx.respond("Vous ne pouvez pas appeler cette commande en combat!")
        return


    enemy_id = character.battling
    area.rehydrate()
    enemy_dict = area.battling.get(enemy_id)
    enemy = Enemy(**enemy_dict)
    damage, killed = character.flee(enemy)

    if killed:
        character.die()
        await ctx.respond(f"{character.name} est mort en essayant de fuir {enemy.name}, et n'est plus. Rest in peace, brave aventurier.")
    elif damage:
        await ctx.respond(f"{character.name} fuit {enemy.name}, et prend {damage} dégâts. HP: {character.hp}/{character.max_hp}")
    else:
        await ctx.respond(f"{character.name} fuit {enemy.name} Avec sa vie intact, mais pas sa dignité. HP: {character.hp}/{character.max_hp}")

@bot.slash_command(name="levelup", help="Advance to the next level. Specify a stat to increase (HP, ATTACK, DEFENSE).")
@commands.cooldown(1,15)
async def levelup(ctx, 
    increase:Option(str, "increase", choices=['ATTACK', 'DEFENSE'], required=True)):
    character = load_character(ctx.author.id)

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
    character = load_character(ctx.author.id)
    
    character.die()
    
    await ctx.respond(f"Le personnage {character.name} n'est plus. Créez-en un nouveau avec `/create`.")

@bot.slash_command(name="reset", help="[DEV] Destroy and recreate current character.")
async def reset(ctx):
    user_id = str(ctx.author.id)
    
    if user_id in db["characters"].keys():
        del db["characters"][user_id]

    await ctx.respond(f"Character deleted.")
    await create(ctx)

@bot.slash_command(name="heal", help="Heal character")
async def heal(ctx):
    character = load_character(ctx.author.id)
    
    if character.mode == GameMode.BATTLE:
        await ctx.respond("Vous ne pouvez pas appeler cette commande en combat.")
        return
    
    character.hp = character.max_hp

    if character.mode == GameMode.DEAD:
        character.mode = GameMode.ADVENTURE

    character.save_to_db()

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

    character = load_character(user.id)

    character.area_id = values[0]

    character.save_to_db()

    await new_channel.send(f"Bienvenue {character.name} dans {area.name} !")



@bot.slash_command(name="move", help="Change the area of the character")
async def move(ctx):
    character = load_character(ctx.author.id)

    if character.mode == GameMode.DEAD:
        await ctx.respond("Vous ne pouvez rien faire tant que vous êtes morts.")
        return

    if character.mode!= GameMode.ADVENTURE:
        await ctx.respond("Vous ne pouvez pas appeler cette commande en combat.")
        return

    area = Area(character.area_id)

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

    character.save_to_db()


bot.run(DISCORD_TOKEN)
