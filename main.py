import asyncio
import os
import sys
import dataset
import dotenv
import hikari
import lightbulb
from loguru import logger as log
from scraper import scrape_otomoto_updated, generate_embed

dotenv.load_dotenv()

bot = lightbulb.BotApp(token=os.getenv("TOKEN"))
db = dataset.connect("sqlite:///otomoto_offers.db")
table = db["subscriptions"]


def restart_program():
    try:
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        log.error(f"Failed to restart program: {e}")


async def run_background():
    log.info("Otomoto Scraper started.")
    while True:
        try:
            log.info("Executing Otomoto scraping loop")
            for sub in table:
                log.info(f"Processing subscription {sub['id']} for URL: {sub['url']}")
                items = scrape_otomoto_updated(sub["url"], db, sub["id"])
                for item in items:
                    try:
                        embed = generate_embed(item)
                        if embed:
                            await bot.rest.create_message(sub["channel_id"], embed=embed)
                        else:
                            log.warning(f"Failed to generate embed for item: {item}")
                    except Exception as e:
                        log.error(f"Failed to send message for item {item}: {e}")
                if items:
                    log.info(f"Found {len(items)} new offers for subscription {sub['id']}.")
            await asyncio.sleep(int(os.getenv("INTERVAL", 60)))
        except Exception as e:
            log.error(f"An error occurred: {e}. Restarting...")
            restart_program()


@bot.listen(hikari.ShardReadyEvent)
async def on_ready(_):
    log.info("Bot is ready.")
    log.info(f"{table.count()} subscriptions registered.")
    asyncio.create_task(run_background())


@bot.command()
@lightbulb.option("url", "URL to Otomoto search", type=str, required=True)
@lightbulb.option("channel", "Channel to receive alerts", type=hikari.TextableChannel, required=True)
@lightbulb.command("subscribe", "Subscribe to an Otomoto search")
@lightbulb.implements(lightbulb.SlashCommand)
async def subscribe(ctx: lightbulb.Context):
    table.insert({"url": ctx.options.url, "channel_id": ctx.options.channel.id, "last_sync": -1})
    log.info(f"Subscription created for URL: {ctx.options.url}")
    await ctx.respond("✅ Subscription created successfully!")


@bot.command()
@lightbulb.command("subscriptions", "List all subscriptions")
@lightbulb.implements(lightbulb.SlashCommand)
async def subscriptions(ctx: lightbulb.Context):
    embed = hikari.Embed(title="Subscriptions")
    for sub in table:
        embed.add_field(name=f"#{sub['id']}", value=sub["url"])
    await ctx.respond(embed=embed)


@bot.command()
@lightbulb.option("id", "ID of the subscription to remove", type=int, required=True)
@lightbulb.command("unsubscribe", "Remove a subscription")
@lightbulb.implements(lightbulb.SlashCommand)
async def unsubscribe(ctx: lightbulb.Context):
    table.delete(id=ctx.options.id)
    log.info(f"Subscription {ctx.options.id} removed.")
    await ctx.respond(f"🗑 Subscription #{ctx.options.id} removed.")


if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()
    bot.run(activity=hikari.Activity(name="Otomoto offers!", type=hikari.ActivityType.WATCHING))
