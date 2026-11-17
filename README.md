# tiny-chess-01: 4 KB Python chess engine

[![make.fun](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01)
[![Rank](https://make.fun/badge/tiny-chess-01/tommy1616/tiny-chess-01/rank.svg)](https://make.fun/bounty/tiny-chess-01)
[![Reward](https://make.fun/badge/tiny-chess-01/tommy1616/tiny-chess-01/reward.svg)](https://make.fun/bounty/tiny-chess-01)

An entry for make.fun's tiny-chess-01 bounty: a chess engine in `main.py`, at
most 4,096 bytes, Python 3.13 standard library only. `main.py` is the engine
(the kit's `compress` packed it; `chess_engine.py` is the readable source it
was packed from, shipped beside the entry, not committed).

Search: iterative-deepening alpha-beta with a fixed node budget per move (never
a clock), quiescence search on captures, MVV-LVA capture ordering, killer moves
and a piece-square-table evaluation with a tapered king term. Position
representation is 0x88 with a full move generator: castling, en passant and all
four promotions, checked for king safety on every node.

Determinism: the same position and node budget always yield the same move; no
wall clock and no unseeded randomness, so a replay plays the same game.

Licence: MIT (see LICENSE). Not derived from sunfish or any GPL engine.
