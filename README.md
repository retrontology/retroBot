# retroBot
Python IRC Twitch bot module integrating [twitchAPI](https://github.com/Teekeks/pyTwitchAPI) and [irc](https://github.com/jaraco/irc).

## Installation
clone this repository
```
git clone https://github.com/retrontology/retroBot
```
install the dependencies
```
cd retroBot
pip install -r requirements.txt
```
install the module
```
python setup.py install
```

## Overview
The bot is split into two main components: the ``retroBot.retroBot`` and the ``retroBot.channelHandler``. These are designed as a base skeleton class to be subtyped.

``retroBot.retroBot`` is the bot itself, a subtype derived from ``irc.bot.SingleServerIRCBot`` and controls the main thread. 

A ``retroBot.channelHandler`` is created for each channel in the channels parameter passed to ``retroBot.retroBot`` constructor. One can also pass their own ``retroBot.channelHandler`` subtype to the ``retroBot.retroBot`` constructor via the handler parameter, which is ideal as the base handler class does nothing. The ``retroBot.retroBot`` instance, when started, passes messages to the respective channel handler instance in a new thread. 

There is also the ``retroBot.config`` module which needs to be imported separately. This is a simple dict subtype that can save and load itself from a yaml file. I personally use it to supply the bots with the information they need to run, but it's not required.

## Examples
There are a few examples in the [examples](https://github.com/retrontology/retroBot/tree/main/examples) directory
- ### [TwitchMarkov](https://github.com/retrontology/TwitchMarkov)
    A fork of [TwitchMarkov](https://github.com/metalgearsvt/TwitchMarkov) written in retroBot.
- ### [atton](https://github.com/retrontology/Atton-Rand-Bot)
    A Twitch bot that sends a message in a channel when the channel goes live.
- ### [twitchlogger](https://github.com/retrontology/twitchlogger)
    A Twitch bot that listens to selected channels and logs the messages to a pre-configured PostgreSQL database.
- ### test
    The simplest bot that does nothing. Used as a test when developing.