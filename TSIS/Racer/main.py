"""
main.py — PIXEL RACER TSIS-3 Edition
=========================================
Full arcade road-racer with:
• Main Menu → Name Entry → Race → Game Over → Leaderboard flow
• Three power-ups: Nitro / Shield / Repair
• Road obstacles: pothole / oil_spill / barrier
• NitroStrip road event
• Difficulty scaling (easy / normal / hard) loaded from settings.json
• Persistent leaderboard (top-10 in leaderboard.json)
• Car colour tint applied from settings
• Distance meter toward RACE_DISTANCE_M finish line
• Game-over crash sound (procedural, no external files)

Controls
--------
← / A move left
→ / D move right
Q / ESC quit (to main menu mid-game)
"""

import sys
import random
import io, math, struct, wave          # ← NEW: для генерации звука
import pygame

import settings as S
import persistence as P
from sprites import (
    PlayerCar, EnemyCar, Coin, Explosion, Obstacle, PowerUp, NitroStrip,
    pick_coin_type, pick_obstacle_type, pick_powerup_type,
)
from hud import HUD
from ui import (
    MainMenuScreen, NameEntryScreen,
    SettingsScreen, LeaderboardScreen, GameOverScreen,
)

# ════════════════════════════════════════════════════════════════════════════
# Game-over sound (генерируется один раз при старте, хранится глобально)
# ════════════════════════════════════════════════════════════════════════════

_snd_gameover: pygame.mixer.Sound | None = None   # ← NEW


def _make_gameover_sound() -> pygame.mixer.Sound:  # ← NEW
    """Три нисходящих тона: G4 → E4 → C4.  Только stdlib, без numpy."""
    SR = 44_100
    def _sine(freq, dur, vol=0.65, fade=True):
        n = int(SR * dur)
        out = []
        for i in range(n):
            s = vol * math.sin(2 * math.pi * freq * i / SR)
            if fade:
                s *= (1.0 - i / n) ** 2
            out.append(s)
        return out

    samples = (
        _sine(392.0, 0.14, fade=False) +   # G4
        _sine(330.0, 0.14, fade=False) +   # E4
        _sine(261.6, 0.28, fade=True)      # C4 (длиннее, затухает)
    )

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        raw = bytearray(len(samples) * 2)
        for i, s in enumerate(samples):
            v = max(-32_767, min(32_767, int(s * 32_767)))
            struct.pack_into('<h', raw, i * 2, v)
        wf.writeframes(bytes(raw))
    buf.seek(0)

    snd = pygame.mixer.Sound(file=buf)
    snd.set_volume(0.6)
    return snd


# ════════════════════════════════════════════════════════════════════════════
# Asset helpers
# ════════════════════════════════════════════════════════════════════════════

def _load(name: str) -> pygame.Surface:
    path = S.asset(name)
    try:
        return pygame.image.load(path).convert_alpha()
    except FileNotFoundError:
        import os, runpy
        gen = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "generate_assets.py")
        print(f"[INFO] '{name}' missing – running generate_assets.py …")
        runpy.run_path(gen)
        return pygame.image.load(path).convert_alpha()


def _load_explosion() -> list[pygame.Surface]:
    return [_load(f"explosion_{i}.png") for i in range(4)]


# ════════════════════════════════════════════════════════════════════════════
# Game class
# ════════════════════════════════════════════════════════════════════════════

class Game:
    """Owns game state for a single run; call run() to play one session."""

    def __init__(self, screen: pygame.Surface, clock,
                 player_name: str, cfg: dict):
        self.screen = screen
        self.clock  = clock
        self.player_name = player_name
        self.cfg = cfg

        self._img_player    = _load("player_car.png")
        self._img_enemy     = _load("enemy_car.png")
        self._img_road      = _load("road_bg.png")
        self._expl_frames   = _load_explosion()

        self.hud = HUD()

        diff = cfg.get("difficulty", "normal")
        self._preset = S.DIFFICULTY_PRESETS.get(diff, S.DIFFICULTY_PRESETS["normal"])

        self.reset()

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset(self):
        preset = self._preset

        self.all_sprites = pygame.sprite.Group()
        self.enemies     = pygame.sprite.Group()
        self.coins       = pygame.sprite.Group()
        self.explosions  = pygame.sprite.Group()
        self.obstacles   = pygame.sprite.Group()
        self.powerups    = pygame.sprite.Group()
        self.nitrostrips = pygame.sprite.Group()

        tint = S.CAR_COLOR_TINTS.get(self.cfg.get("car_color", "blue"),
                                      S.CAR_COLOR_TINTS["blue"])
        self.player = PlayerCar(self._img_player, tint)
        self.all_sprites.add(self.player)

        self._road_h = self._img_road.get_height()
        self._road_y = 0

        self.scroll_speed     = float(preset["scroll_speed_init"])
        self._enemy_timer     = 0
        self._enemy_delay     = preset["enemy_spawn_delay"]
        self._enemy_extra     = float(S.ENEMY_SPEED_EXTRA)
        self._boost_threshold = S.ENEMY_BOOST_EVERY_N
        self._danger_timer    = 0

        self.score      = 0
        self.coins_count = 0
        self.coin_value  = 0
        self._last_coin_type = None

        self.distance = 0.0

        self._active_pu        = None
        self._pu_timer         = 0.0
        self._nitro_bonus      = 0.0
        self._nitro_timer      = 0.0
        self._nitro_strip_timer = 0.0

        self.game_over     = False
        self._quit_to_menu = False

    # ── Events ────────────────────────────────────────────────────────────────

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self._quit_to_menu = True

    # ── Spawning ──────────────────────────────────────────────────────────────

    def _spawn_enemy(self):
        self._enemy_timer += 1
        if self._enemy_timer >= self._enemy_delay:
            self._enemy_timer = 0
            e = EnemyCar(self._img_enemy, self.scroll_speed, self._enemy_extra)
            self.enemies.add(e)
            self.all_sprites.add(e)
            base = self._preset["enemy_spawn_delay"]
            self._enemy_delay = max(30, base - self.score // 300)

    def _spawn_coin(self):
        if len(self.coins) < S.COIN_MAX_ON_ROAD:
            if random.random() < S.COIN_SPAWN_CHANCE:
                ct   = pick_coin_type()
                coin = Coin(ct, self.scroll_speed)
                self.coins.add(coin)
                self.all_sprites.add(coin)

    def _spawn_obstacle(self):
        if len(self.obstacles) < S.OBSTACLE_MAX_ON_ROAD:
            chance = self._preset["obstacle_chance"]
            chance *= (1 + self.distance / S.RACE_DISTANCE_M)
            if random.random() < chance:
                ot  = pick_obstacle_type()
                obs = Obstacle(ot, self.scroll_speed)
                if abs(obs.rect.centerx - self.player.rect.centerx) > 20:
                    self.obstacles.add(obs)
                    self.all_sprites.add(obs)

    def _spawn_powerup(self):
        if len(self.powerups) < S.POWERUP_MAX_ON_ROAD:
            chance = self._preset["powerup_spawn_chance"]
            if random.random() < chance:
                pt = pick_powerup_type()
                pu = PowerUp(pt, self.scroll_speed)
                self.powerups.add(pu)
                self.all_sprites.add(pu)

    def _spawn_nitro_strip(self):
        if len(self.nitrostrips) == 0:
            if random.random() < S.NITRO_STRIP_CHANCE:
                ns = NitroStrip(self.scroll_speed)
                self.nitrostrips.add(ns)
                self.all_sprites.add(ns)

    # ── Collisions ────────────────────────────────────────────────────────────

    def _collisions(self, dt: float):
        hit = pygame.sprite.spritecollide(
            self.player, self.enemies, dokill=True,
            collided=pygame.sprite.collide_mask)
        if hit:
            if self.player.shielded:
                self.player.consume_shield()
                self._active_pu = None
                self._pu_timer  = 0.0
                self.score += S.SHIELD_SCORE_BONUS
            else:
                self._do_crash()
                return

        obs_hit = pygame.sprite.spritecollide(self.player, self.obstacles, dokill=True)
        for obs in obs_hit:
            if obs.obs_type["lethal"]:
                if self.player.shielded:
                    self.player.consume_shield()
                    self._active_pu = None
                    self._pu_timer  = 0.0
                else:
                    self._do_crash()
                    return
            elif obs.obs_type.get("slow"):
                self.player.apply_oil()

        pu_hit = pygame.sprite.spritecollide(self.player, self.powerups, dokill=True)
        for pu in pu_hit:
            self._activate_powerup(pu.pu_type)

        ns_hit = pygame.sprite.spritecollide(self.player, self.nitrostrips, dokill=False)
        if ns_hit and self._nitro_strip_timer <= 0:
            self._nitro_strip_timer = S.NITRO_STRIP_DURATION
            self.score += S.NITRO_SCORE_BONUS

        collected = pygame.sprite.spritecollide(self.player, self.coins, dokill=True)
        for coin in collected:
            self.coins_count += 1
            self.coin_value  += coin.value
            self.score       += coin.value * 10
            self._last_coin_type = coin.coin_type
            if self.coins_count >= self._boost_threshold:
                self._fire_enemy_boost()

    def _do_crash(self):
        expl = Explosion(self._expl_frames, self.player.rect.center)
        self.explosions.add(expl)
        self.all_sprites.add(expl)
        self.player.kill()
        self.game_over = True
        if _snd_gameover:               # ← NEW: играем звук game over
            _snd_gameover.play()

    def _fire_enemy_boost(self):
        self._enemy_extra = min(
            self._enemy_extra + S.ENEMY_BOOST_AMOUNT,
            S.ENEMY_SPEED_EXTRA_MAX)
        self._danger_timer    = S.ENEMY_BOOST_FLASH_FRAMES
        self._boost_threshold += S.ENEMY_BOOST_EVERY_N

    # ── Power-up activation ───────────────────────────────────────────────────

    def _activate_powerup(self, pu_type: dict):
        name = pu_type["name"]
        if name == "nitro":
            self._active_pu   = pu_type
            self._pu_timer    = pu_type["duration"]
            self._nitro_bonus = S.NITRO_STRIP_SPEED_BONUS
            self.score       += S.NITRO_SCORE_BONUS
        elif name == "shield":
            self._active_pu = pu_type
            self._pu_timer  = 0.0
            self.player.activate_shield()
            self.score += S.SHIELD_SCORE_BONUS
        elif name == "repair":
            self.obstacles.empty()
            self._active_pu = pu_type
            self._pu_timer  = 1.5
            self.score += S.REPAIR_SCORE_BONUS

    # ── Road scrolling ────────────────────────────────────────────────────────

    def _scroll_road(self):
        self._road_y += int(self.scroll_speed)
        if self._road_y >= self._road_h:
            self._road_y -= self._road_h

    def _draw_road(self):
        self.screen.blit(self._img_road, (0, self._road_y))
        self.screen.blit(self._img_road, (0, self._road_y - self._road_h))

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self, dt: float):
        keys = pygame.key.get_pressed()

        ramp = self._preset["speed_increment"]
        self.scroll_speed = min(self.scroll_speed + ramp, S.SCROLL_SPEED_MAX)

        strip_bonus = 0.0
        if self._nitro_strip_timer > 0:
            self._nitro_strip_timer = max(0.0, self._nitro_strip_timer - dt)
            strip_bonus = S.NITRO_STRIP_SPEED_BONUS

        pu_bonus = 0.0
        if self._active_pu:
            name = self._active_pu["name"]
            if name == "nitro" and self._pu_timer > 0:
                self._pu_timer = max(0.0, self._pu_timer - dt)
                pu_bonus = self._nitro_bonus
                if self._pu_timer <= 0:
                    self._active_pu   = None
                    self._nitro_bonus = 0.0
            elif name == "repair" and self._pu_timer > 0:
                self._pu_timer = max(0.0, self._pu_timer - dt)
                if self._pu_timer <= 0:
                    self._active_pu = None
            elif name == "shield" and not self.player.shielded:
                self._active_pu = None

        effective_speed = self.scroll_speed + pu_bonus + strip_bonus
        self.distance  += effective_speed / S.PX_PER_METRE

        self._scroll_road()
        self._spawn_enemy()
        self._spawn_coin()
        self._spawn_obstacle()
        self._spawn_powerup()
        self._spawn_nitro_strip()

        self.player.update(keys, dt)
        self.enemies.update(self.scroll_speed, self._enemy_extra)
        self.coins.update(self.scroll_speed)
        self.obstacles.update(effective_speed)
        self.powerups.update(effective_speed, dt)
        self.nitrostrips.update(effective_speed)
        self.explosions.update()

        self._collisions(dt)

        self.score += S.SCORE_PER_FRAME
        self.score += int(self.distance * 0.01)

        if self._danger_timer > 0:
            self._danger_timer -= 1

    # ── Draw ──────────────────────────────────────────────────────────────────

    def _draw(self):
        self._draw_road()
        self.all_sprites.draw(self.screen)

        pu_timer_val = self._pu_timer if (
            self._active_pu and self._active_pu.get("duration")) else 0.0

        self.hud.draw(
            self.screen,
            score          = self.score,
            speed          = self.scroll_speed,
            coins_count    = self.coins_count,
            coin_value     = self.coin_value,
            last_coin_type = self._last_coin_type,
            danger_flash   = self._danger_timer,
            enemy_extra    = self._enemy_extra,
            distance       = self.distance,
            active_powerup = self._active_pu,
            powerup_timer  = pu_timer_val,
            shield_active  = self.player.shielded if self.player.alive() else False,
            oil_slowed     = self.player.oil_slowed if self.player.alive() else False,
        )
        pygame.display.flip()

    # ── Run one game session ──────────────────────────────────────────────────

    def run(self) -> str:
        """Play until crash or quit. Returns 'retry', 'menu', or 'quit'."""
        while True:
            dt = self.clock.tick(S.FPS) / 1000.0

            self._events()
            if self._quit_to_menu:
                return "menu"

            if not self.game_over:
                self._update(dt)
            else:
                self.explosions.update()

            self._draw()

            if self.game_over:
                pygame.time.wait(600)
                go     = GameOverScreen()
                result = go.run(
                    self.screen, self.clock,
                    score      = self.score,
                    distance   = self.distance,
                    coins      = self.coins_count,
                    coin_value = self.coin_value,
                    name       = self.player_name,
                )
                P.add_leaderboard_entry(
                    name       = self.player_name,
                    score      = self.score,
                    distance   = self.distance,
                    coins      = self.coins_count,
                    difficulty = self.cfg.get("difficulty", "normal"),
                )
                return result


# ════════════════════════════════════════════════════════════════════════════
# Application shell
# ════════════════════════════════════════════════════════════════════════════

def main():
    global _snd_gameover                        # ← NEW

    import os, runpy
    if not os.path.exists(S.asset("player_car.png")):
        gen = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "generate_assets.py")
        print("[INFO] Generating assets …")
        runpy.run_path(gen)

    pygame.mixer.pre_init(44_100, -16, 1, 512)  # ← NEW: до pygame.init()
    pygame.init()
    _snd_gameover = _make_gameover_sound()       # ← NEW: строим звук

    screen = pygame.display.set_mode((S.WIN_W, S.WIN_H), pygame.SCALED)
    pygame.display.set_caption(S.TITLE)
    clock  = pygame.time.Clock()

    cfg = P.load_settings()

    menu     = MainMenuScreen()
    lb_scr   = LeaderboardScreen()
    set_scr  = SettingsScreen()
    name_scr = NameEntryScreen()

    player_name = "Player"

    while True:
        action = menu.run(screen, clock)

        if action == "quit":
            pygame.quit(); sys.exit()

        elif action in ("leaderboard", "lb"):
            lb_scr.run(screen, clock)

        elif action in ("settings", "set"):
            cfg = set_scr.run(screen, clock, cfg)

        elif action == "play":
            entered = name_scr.run(screen, clock)
            if entered is None:
                continue
            player_name = entered

            while True:
                game   = Game(screen, clock, player_name, cfg)
                result = game.run()

                if result == "retry":
                    continue
                elif result == "menu":
                    break
                else:
                    pygame.quit(); sys.exit()


if __name__ == "__main__":
    main()
