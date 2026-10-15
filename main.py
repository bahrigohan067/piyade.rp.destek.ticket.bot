import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import discord
from discord.ext import commands
from discord import app_commands
from config import TOKEN, GUILD_ID, KURUCU_ROL_ID

# Presences ve Members intentleri yetkili Discord aktiflik takibi için zorunludur
intents = discord.Intents.all()


class DestekTicketBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # ── Cogs Yükleme ──
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for filename in sorted(os.listdir(cogs_dir)):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    print(f"✅ Yüklendi: {cog_name}", flush=True)
                except Exception as e:
                    print(f"❌ Hata: {cog_name} → {e}", flush=True)

        # ── Kalıcı (Persistent) Buton Görünümleri ──
        # Bot veya Railway yeniden başlasa bile butonlar asla bozulmaz.
        from cogs.tickets import TicketPanelView, CloseTicketView
        from cogs.yardim_bekleme import DevralView, DestekAktifView

        self.add_view(TicketPanelView())
        self.add_view(CloseTicketView())
        self.add_view(DevralView())
        self.add_view(DestekAktifView())

        # ── Slash Komut Senkronizasyonu ──
        try:
            guild_obj = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild_obj)
            synced = await self.tree.sync(guild=guild_obj)
            print(f"⚡ [SYNC] {len(synced)} adet slash komutu sunucuya ({GUILD_ID}) anında senkronize edildi!", flush=True)
        except Exception as e:
            print(f"⚠️ [SYNC HATA] {e}", flush=True)


bot = DestekTicketBot()


@bot.command(name="sync")
async def sync_komutu(ctx: commands.Context):
    """Kurucu veya Yönetici yetkisine sahip kişilerin zorla komut senkronizasyonu yapmasını sağlar."""
    if not (ctx.author.guild_permissions.administrator or any(r.id == KURUCU_ROL_ID for r in getattr(ctx.author, "roles", []))):
        return await ctx.reply("❌ Bu komutu yalnızca **Kurucu** kullanabilir.")

    mesaj = await ctx.reply("🔄 Slash komutları Discord'a senkronize ediliyor, lütfen bekleyiniz...")
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild_obj)
        synced = await bot.tree.sync(guild=guild_obj)
        await mesaj.edit(content=f"✅ **{len(synced)} adet** slash komutu sunucuya başarıyla senkronize edildi! (Discord'u `Ctrl + R` ile yenileyebilirsiniz.)")
    except Exception as e:
        await mesaj.edit(content=f"❌ Senkronizasyon hatası: `{e}`")


@bot.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="🎫 Destek & Bilet Sistemi | Piyade RP"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print("=" * 60, flush=True)
    print(f"🤖 Bot Başarıyla Giriş Yaptı: {bot.user} (ID: {bot.user.id})", flush=True)
    print(f"🌐 Sunucu ID: {GUILD_ID}", flush=True)
    print(f"📡 Gecikme (Ping): {round(bot.latency * 1000)}ms", flush=True)
    print("🚀 Destek ve Ticket Botu Aktif ve Göreve Hazır!", flush=True)
    print("=" * 60, flush=True)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    import traceback
    traceback.print_exception(type(error), error, error.__traceback__)

    if isinstance(error, app_commands.CommandOnCooldown):
        kalan = int(error.retry_after)
        msg = f"⏳ Bu komutu tekrar kullanabilmek için **{kalan} saniye** beklemelisiniz."
    else:
        msg = "❌ Komut çalışırken beklenmeyen bir hata oluştu."

    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except Exception:
        pass


if __name__ == "__main__":
    if not TOKEN:
        print("❌ HATA: Discord Bot TOKEN tanımlı değil!", flush=True)
        print("Lütfen Railway panelinden veya .env dosyasından 'TOKEN_DESTEK' ortam değişkenini tanımlayın.", flush=True)
        sys.exit(1)

    bot.run(TOKEN)
