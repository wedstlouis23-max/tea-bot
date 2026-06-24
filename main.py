import discord
from discord import app_commands
from datetime import datetime, timedelta
import os
import openai

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

openai.api_key = "YOUR_OPENAI_KEY_HERE"   # ← Change this

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    await bot.change_presence(activity=discord.Game(name="☕ Brewing recaps"))
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print("Sync error:", e) bot.change_presence(activity=discord.Game(name="☕ Brewing recaps"))

async def get_ai_summary(chat_text, context=""):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a helpful Discord recap assistant."},
                      {"role": "user", "content": f"{context}\n\nChat:\n{chat_text}"}]
        )
        return response.choices[0].message.content
    except:
        return "AI summary unavailable."

@tree.command(name="rewind", description="Get a summary of recent messages")
@app_commands.describe(hours="Hours back (default 24)", user="Specific user", topic="Keyword")
async def rewind(interaction: discord.Interaction, hours: int = 24, user: discord.Member = None, topic: str = None):
    await interaction.response.defer()
    after = datetime.utcnow() - timedelta(hours=hours)
    messages = []
    async for msg in interaction.channel.history(limit=500, after=after):
        if msg.author.bot or not msg.content.strip(): continue
        if user and msg.author.id != user.id: continue
        if topic and topic.lower() not in msg.content.lower(): continue
        messages.append(f"{msg.author.display_name}: {msg.content}")

    if not messages:
        await interaction.followup.send("No matching messages found.")
        return

    chat_text = "\n".join(messages[-150:])
    context = f"Channel: {interaction.channel.name}"
    if user: context += f" | User: {user.display_name}"
    if topic: context += f" | Topic: {topic}"

    summary = await get_ai_summary(chat_text, context)
    embed = discord.Embed(title="📋 Rewind Summary", description=summary, color=0xFFD700)
    embed.set_footer(text=f"Last {hours} hours • {len(messages)} messages")
    await interaction.followup.send(embed=embed)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        token = input("Paste your Bot Token here: ")
    bot.run(token)
