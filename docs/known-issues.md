# Known Issues

## JOIN log spam: `on_join` logs every viewer's join as the bot's own

**Status:** fixed 2026-09-11 in 0.3.5 (branch `bugfix/join-log-spam`).

### Symptom

Container logs fill with bursts of identical lines, dozens at a time within the
same millisecond:

```
2026-09-11 21:58:02,771 [INFO]  retroBot.NeuralBronson: Joined Twitch IRC server!
2026-09-11 21:58:02,983 [DEBUG] retroBot.NeuralBronson: Joined #rlly!
...
2026-09-11 21:58:33,699 [DEBUG] retroBot.NeuralBronson: Joined #rlly!   <- x10, same ms
2026-09-11 21:59:31,575 [DEBUG] retroBot.NeuralBronson: Joined #rlly!   <- x4+
```

Reported downstream in TwitchMarkov, but the cause is here in retroBot.

### Root cause

Two things combine:

1. `bot.py:55` (`on_welcome`) requests `:twitch.tv/membership`. That capability
   makes Twitch deliver `JOIN`/`PART` for *every user* in the channel, not just
   the bot. Twitch batches these and flushes them in bursts, which is why the
   duplicates share a timestamp.

2. `bot.py:85-86` logs only the channel, never the joiner:

   ```python
   def on_join(self, c, e):
       self.logger.debug(f'Joined {e.target}!')
   ```

   `irc.client.SimpleIRCClient._dispatcher` (client.py:1215) calls `on_join` for
   *every* JOIN event with no source filtering — unlike the library's own
   `irc.bot.SingleServerIRCBot._on_join` (bot.py:203), which does gate on
   `nick == connection.get_nickname()`. So every viewer's join renders as an
   identical `Joined #rlly!`, indistinguishable from the bot's own.

The first line after `Joined Twitch IRC server!` is the bot's real join; every
one after it is ordinary chat traffic.

### Ruled out

- **Not a reconnect loop.** `Joined Twitch IRC server!` appears only once in the
  window, so `on_welcome` fired once.
- **Not the `join_channel` retry loop.** `bot.py:67-71` sends JOIN at 1-second
  intervals; it cannot emit 10 in 2ms. The `_joining` guard held, and message
  handling continued normally throughout.

### Fix

Nothing in retroBot or in TwitchMarkov consumes membership events — there is no
`on_part` and no user-list usage anywhere. The `self.channels` bookkeeping that
`join_channel()` depends on works without the capability, because Twitch always
echoes the client's *own* JOIN regardless of it.

Both were applied.

- Dropped `c.cap('REQ', ':twitch.tv/membership')` from `on_welcome`. This removes
  the network traffic, not just the logging.
- Made the log line honest about what it reports, in case membership is wanted
  again later:

  ```python
  def on_join(self, c, e):
      if e.source.nick == c.get_nickname():
          self.logger.debug(f'Joined {e.target}!')
  ```

### If membership is ever re-enabled

`_on_join` does `self.channels[ch].add_user(nick)` unconditionally. A JOIN or
PART for a channel missing from `self.channels` would raise `KeyError`. Not
currently reachable, but worth keeping in mind during the overhaul.
