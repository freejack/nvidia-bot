import os

import click

from cli.utils import QuestionaryOption
from functools import wraps
from notifications.notifications import NotificationHandler
from stores.amazon import Amazon
from stores.amazon3rd import AmazonThird
from stores.bestbuy import BestBuyHandler
from stores.evga import Evga
from stores.nvidia import NvidiaBuyer, GPU_DISPLAY_NAMES, CURRENCY_LOCALE_MAP
from utils import selenium_utils

notification_handler = NotificationHandler()


def notify_on_crash(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            pass
        except:
            notification_handler.send_notification(f"nvidia-bot has crashed.")
            raise

    return decorator


@click.group()
def main():
    pass

# Nvidia

@click.command()
@click.option(
    "--gpu",
    type=click.Choice(GPU_DISPLAY_NAMES, case_sensitive=False),
    prompt="What GPU are you after?",
    cls=QuestionaryOption,
)
@click.option(
    "--locale",
    type=click.Choice(CURRENCY_LOCALE_MAP.keys(), case_sensitive=False),
    prompt="What locale shall we use?",
    cls=QuestionaryOption,
)
@click.option("--test", is_flag=True)
@click.option("--interval", type=int, default=5)
@notify_on_crash
def nvidia(gpu, locale, test, interval):
    nv = NvidiaBuyer(gpu, locale, test, interval)
    nv.run_items()

# Amazon Multi-Item

@click.command()
@click.option("--no-image", is_flag=True)
@click.option("--headless", is_flag=True)
@click.option("--test", is_flag=True)
@notify_on_crash
def amazon(no_image, headless, test):
    if no_image:
        selenium_utils.no_amazon_image()
    else:
        selenium_utils.yes_amazon_image()

    amzn_obj = Amazon(headless=headless)
    amzn_obj.run_item(test=test)


# Amazon Third Party

@click.command()
@click.option(
    "--amazon_email",
    type=str,
    prompt="Amazon Email",
    default=lambda: os.environ.get("amazon_email", ""),
    show_default="current user",
)
@click.option(
    "--amazon_password",
    type=str,
    prompt="Amazon Password",
    default=lambda: os.environ.get("amazon_password", ""),
    show_default="current user",
)
@click.option(
    "--amazon_item_url",
    type=str,
    prompt="Amazon Item URL",
    default=lambda: os.environ.get("amazon_item_url", ""),
    show_default="current user",
)
@click.option(
    "--amazon_price_limit",
    type=int,
    prompt="Maximum Price to Pay",
    default=lambda: int(os.environ.get("amazon_price_limit", 10000)),
    show_default="current user",
)
@click.option("--no-image", is_flag=True)
@click.option("--headless", is_flag=True)
def amazon3rd(
    amazon_email,
    amazon_password,
    amazon_item_url,
    amazon_price_limit,
    no_image,
    headless
):
    os.environ.setdefault("amazon_email", amazon_email)
    os.environ.setdefault("amazon_password", amazon_password)
    os.environ.setdefault("amazon_item_url", amazon_item_url)
    os.environ.setdefault("amazon_price_limit", str(amazon_price_limit))

    if no_image:
        selenium_utils.no_amazon_image()

    amzn_obj = AmazonThird(
        username=amazon_email,
        password=amazon_password,
        headless=headless,
        item_url=amazon_item_url
    )
    amzn_obj.run_item(item_url=amazon_item_url, price_limit=amazon_price_limit)

    if no_image:
        selenium_utils.no_amazon_image()


@click.command()
@click.option("--test", is_flag=True)
@click.option("--headless", is_flag=True)
@notify_on_crash
def evga(test, headless):
    ev = Evga(headless)
    ev.buy(test=test)


main.add_command(nvidia)
main.add_command(amazon)
main.add_command(amazon3rd)
main.add_command(evga)
