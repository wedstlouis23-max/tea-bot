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

openai.api_key = "YOUR_OPENAI_KEY_HERE"  # ← Change this

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    await bot.change_presence(activity=discord.Game(name="☕ Brewing recaps"))
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print("Sync error:", e)

async def get_ai_summary(chat_text, context=""):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a helpful Discord recap assistant."},
                      {"role": "user", "content": f"{context}\n\nChat:\n{chat_text}"}]
        )
        return response.choices[0].message.content
    except:
        return "AI summary unavailable right now."

@tree.command(name="rewind", description="Detailed summary: who did what and when")
@app_commands.describe(hours="Hours back to summarize (default 24)")
async def rewind(interaction: discord.Interaction, hours: int = 24):
    await interaction.response.defer()

    after = datetime.utcnow() - timedelta(hours=hours)
    messages = []
    async for msg in interaction.channel.history(limit=500, after=after):
        if not msg.author.bot and msg.content.strip():
            messages.append((msg.author.display_name, msg.content, msg.created_at))

    if not messages:
        await interaction.followup.send(f"No messages found in the last {hours} hours.")
        return

    # Build detailed summary
    summary = f"""**📋 Rewind Summary** (last {hours} hours in #{interaction.channel.name})

**Active Members:** {', '.join(set(m[0] for m in messages[-30:]))}

**What the conversation was about:** Recent discussion in the channel (check messages for full details).

**Key Activity:**
"""
    for author, content, time in messages[-20:]:
        time_str = time.strftime('%I:%M %p')
        summary += f"**{author}** at {time_str}: {content[:120]}...\n"

    embed = discord.Embed(title="Rewind Summary", description=summary, color=0xFFD700)
    await interaction.followup.send(embed=embed)
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        token = input("Paste your Bot Token here: ")
    bot.run(token)
