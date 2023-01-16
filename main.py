import os, discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option


from api.actor import *
from api.character import *
from api.enemy import *
from api.zone import *

import yaml

# Helper functions
def load_character(user_id):
    db = yaml.safe_load(open('./game.yml'))

    character_dict = db.get("characters").get(user_id)

    return Character(**character_dict)

MODE_COLOR = {
    GameMode.BATTLE: 0xDC143C,
    GameMode.ADVENTURE: 0x005EB8,
    GameMode.DEAD: 0x333333,
}
def status_embed(ctx, character):

    # Current mode
    if character.mode == GameMode.BATTLE:
        mode_text = f"Currently battling."
    elif character.mode == GameMode.ADVENTURE:
        mode_text = "Currently adventuring."
    elif character.mode == GameMode.DEAD:
        mode_text = "Currently dead."

    # Create embed with description as current mode
    embed = discord.Embed(title=f"{character.name} status", description=mode_text, color=MODE_COLOR[character.mode])
    embed.set_author(name=ctx.author.display_name)

    return embed

DISCORD_TOKEN = (yaml.safe_load(open('./config.yml'))).get("token")

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


cmd = SlashCommandGroup("rpg", "Commands for server management!")  

# Commands
@bot.slash_command(name="create", help="Create a character.")
async def create(ctx, character_name=None):
    user_id = ctx.author.id
    db = yaml.safe_load(open('./game.yml'))

    # if no name is specified, use the creator's nickname
    if character_name == None:
        character_name = ctx.author.name

    # create characters dictionary if it does not exist
    if "characters" not in db.keys():
        db["characters"] = {}

    # only create a new character if the user does not already have one
    if user_id not in db["characters"] or not db["characters"][user_id]:
        character = Character(**{
            "name": character_name,
            "hp": 20,
            "max_hp": 20,
            "attack": 2,
            "defense": 1,
            "mana": 0,
            "level": 1,
            "xp": 0,
            "gold": 0,
            "inventory": [],
            "mode": ['ADVENTURE'],
            "battling": None,
            "user_id": user_id,
            "skin": None
        })
        character.save_to_db()
        await ctx.respond(f"New level 1 character created: {character_name}. Enter `!status` to see your stats.")
    else:
        await ctx.respond("You have already created your character.")


@bot.slash_command(name="status", help="Get information about your character.")
async def status(ctx):

    character = load_character(ctx.author.id)

    embed = status_embed(ctx, character)

        # Stats field
    _, xp_needed = character.ready_to_level_up()

    embed.add_field(name="Stats", value=f"""
**HP:**    {character.hp}/{character.max_hp}
**ATTACK:**   {character.attack}
**DEFENSE:**   {character.defense}
**MANA:**  {character.mana}
**LEVEL:** {character.level}
**XP:**    {character.xp}/{character.xp+xp_needed}
**AREA:** {character.zone_id}
    """, inline=True)

    # Inventory field
    inventory_text = f"Gold: {character.gold}\n"
    if character.inventory:
        inventory_text += "\n".join(character.inventory)
    
    embed.add_field(name="Inventory", value=inventory_text, inline=True)

    if character.skin != None:
        embed.set_thumbnail(url=character.skin)

    await ctx.respond(embed=embed) 

@bot.slash_command(name="hunt", help="Look for an enemy to fight.")
async def hunt(ctx):
    character = load_character(ctx.author.id)

    if character.mode == GameMode.DEAD:
        await ctx.respond("You can't do anything when you're dead.")
        return

    if character.mode != GameMode.ADVENTURE:
        await ctx.respond("Can only call this command outside of battle!")
        return

    enemy_id = character.hunt()

    area = Zone(character.zone_id)

    if enemy_id == None:
        await ctx.respond("No enemy found in the area.")
        return
    
    if not enemy_id in area.battling.keys():
        await ctx.respond(f"{enemy_id} is not in the zone!")
        return

    enemy = Enemy(**(area.battling.get(enemy_id)))
    
    # Send reply
    await ctx.respond(f"You encounter a {enemy.name}. Do you `!fight` or `!flee`?")

@bot.slash_command(name="fight", help="Fight the current enemy.")
async def fight(ctx):
    character = load_character(ctx.author.id)
    
    if character.mode == GameMode.DEAD:
        await ctx.respond("You can't do anything when you're dead.")
        return

    if character.mode != GameMode.BATTLE:
        await ctx.respond("Can only call this command in battle!")
        return
        
    # Simulate battle
    enemy_id = character.battling
    area = Zone(character.zone_id)
    enemy_dict = area.battling.get(enemy_id)
    enemy = Enemy(**enemy_dict)

    # Character attacks
    damage, killed = character.fight(enemy)
    if damage:
        await ctx.respond(f"{character.name} attacks {enemy.name}, dealing {damage} damage!")
    else:
        await ctx.respond(f"{character.name} swings at {enemy.name}, but misses!")

        # End battle in victory if enemy killed
    if killed:
        xp, gold, ready_to_level_up = character.defeat(enemy)
        
        await ctx.respond(f"{character.name} vanquished the {enemy.name}, earning {xp} XP and {gold} GOLD. HP: {character.hp}/{character.max_hp}.")
        
        if ready_to_level_up:
            await ctx.respond(f"{character.name} has earned enough XP to advance to level {character.level+1}. Enter `!levelup` with the stat (HP, ATTACK, DEFENSE) you would like to increase. e.g. `!levelup hp` or `!levelup attack`.")
            
        return
    
        # Enemy attacks
    damage, killed = enemy.fight(character)
    if damage:
        await ctx.respond(f"{enemy.name} attacks {character.name}, dealing {damage} damage!")
    else:
        await ctx.respond(f"{enemy.name} tries to attack {character.name}, but misses!")

    character.save_to_db() #enemy.fight() does not save automatically

        # End battle in death if character killed
    if killed:
        character.die()
        
        await ctx.respond(f"{character.name} was defeated by a {enemy.name} and is no more. Rest in peace, brave adventurer.")
        return

        # No deaths, battle continues
    await ctx.respond(f"The battle rages on! Do you `!fight` or `!flee`?")

@bot.slash_command(name="flee", help="Flee the current enemy.")
async def flee(ctx):
    character = load_character(ctx.author.id)

    if character.mode == GameMode.DEAD:
        await ctx.respond("You can't do anything when you're dead.")
        return
    
    if character.mode != GameMode.BATTLE:
        await ctx.respond("Can only call this command in battle!")
        return

    enemy = character.battling
    damage, killed = character.flee(enemy)

    if killed:
        character.die()
        await ctx.respond(f"{character.name} was killed fleeing the {enemy.name}, and is no more. Rest in peace, brave adventurer.")
    elif damage:
        await ctx.respond(f"{character.name} flees the {enemy.name}, taking {damage} damage. HP: {character.hp}/{character.max_hp}")
    else:
        await ctx.respond(f"{character.name} flees the {enemy.name} with their life but not their dignity intact. HP: {character.hp}/{character.max_hp}")

@bot.slash_command(name="levelup", help="Advance to the next level. Specify a stat to increase (HP, ATTACK, DEFENSE).")
async def levelup(ctx, 
    increase:Option(str, "increase", choices=['ATTACK', 'DEFENSE'], required=True)):
    character = load_character(ctx.author.id)

    if character.mode == GameMode.DEAD:
        await ctx.respond("You can't do anything when you're dead.")
        return

    if character.mode != GameMode.ADVENTURE:
        await ctx.respond("Can only call this command outside of battle!")
        return

    ready, xp_needed = character.ready_to_level_up()
    if not ready:
        await ctx.respond(f"You need another {xp_needed} to advance to level {character.level+1}")
        return
        
    if not increase:
        await ctx.respond("Please specify a stat to increase (HP, ATTACK, DEFENSE)")
        return

    increase = increase.lower()
    if increase == "hp" or increase == "hitpoints" or increase == "max_hp" or increase == "maxhp":
        increase = "max_hp"
    elif increase == "attack" or increase == "att":
        increase = "attack"
    elif increase == "defense" or increase == "def" or increase == "defence":
        increase = "defense"

    success, new_level = character.level_up(increase)
    if success:
        await ctx.respond(f"{character.name} advanced to level {new_level}, gaining 1 {increase.upper().replace('_', ' ')}.")
    else:
        await ctx.respond(f"{character.name} failed to level up.")

@bot.slash_command(name="die", help="Destroy current character.")
async def die(ctx):
    character = load_character(ctx.author.id)
    
    character.die()
    
    await ctx.respond(f"Character {character.name} is no more. Create a new one with `!create`.")

@bot.slash_command(name="reset", help="[DEV] Destroy and recreate current character.")
async def reset(ctx):
    user_id = str(ctx.author.id)
    
    if user_id in db["characters"].keys():
        del db["characters"][user_id]

    await ctx.respond(f"Character deleted.")
    await create(ctx)

bot.run(DISCORD_TOKEN)