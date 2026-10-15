import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import datetime
import aiohttp
import asyncio

from config import (
    YARDIM_BEKLEME_VC_ID,
    YARDIM_VC_ID,
    ONEMLI_LOG_KANALI,
    ONLY_MOD_KANALI,
    DESTEK_CAGRI_KANALI,
    DESTEK_BEKLEME_YETKILISI_ROL,
    KURUCU_ROL_ID,
    UST_YONETIM_ROL_ID,
    ADMIN_ROLES,
    YETKILI_ROL_IDLERI,
    GUNLUK_HEDEF_SANIYE,
    ERLC_API_KEY
)
from utils.stats_manager import (
    load_stats,
    save_stats,
    update_mod_stat,
    add_mod_active_time,
    progress_bar,
    get_next_destek_id,
    archive_and_reset_daily,
    set_roblox_name,
    get_roblox_name,
    load_roblox_mapping
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_member_highest_role_name(member: discord.Member) -> str:
    """Üyenin yetkili rollerinden en yükseğini bulur."""
    for role_id, role_name in ADMIN_ROLES.items():
        if discord.utils.get(member.roles, id=role_id):
            return role_name
    return "Yetkili"


def build_leaderboard_embed(bot: commands.Bot, guild: discord.Guild, color: discord.Color = discord.Color.gold(), is_nightly: bool = False) -> discord.Embed:
    """
    Yetkili performans ve sıralama tablosu embed'ini oluşturur.
    Kullanıcının isteği: Yüksek dekorasyonlu, sarı renkli, beyaz/yeşil doluluk çubuklu.
    """
    data = load_stats()
    
    title = "📊 Günlük Yetkili İstatistikleri (Gece Raporu)" if is_nightly else "👑 Yetkili Performans & Sıralama Tablosu"
    desc = (
        "📊 **Günlük Yetkili Mesai, Destek ve Bilet İstatistikleri**\n"
        "🎯 **Günlük Discord Hedefi:** 3 Saat (`180 dk`)\n"
        "⏰ **Veri Sıfırlanma:** Her Gece 00:00 (TSİ)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    embed = discord.Embed(title=title, description=desc, color=color)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    if not data:
        embed.add_field(
            name="ℹ️ Bilgilendirme",
            value="Bugün için henüz kaydedilmiş bir yetkili verisi bulunmuyor.",
            inline=False
        )
        embed.set_footer(text="Piyade Roleplay Destek & Ticket Sistemi")
        embed.timestamp = discord.utils.utcnow()
        return embed

    # Sıralama: Discord aktiflik süresi ve oyun süresi toplamına göre
    sorted_items = sorted(
        data.items(),
        key=lambda item: (
            item[1].get("discord_time", 0) +
            item[1].get("game_time", 0) +
            (item[1].get("supports", 0) * 1800) +
            (item[1].get("tickets", 0) * 1800)
        ),
        reverse=True
    )

    rank_emojis = ["🥇", "🥈", "🥉", "🎖️", "🎖️", "🎖️", "🎖️", "🎖️", "🎖️", "🎖️"]

    total_supports = 0
    total_tickets = 0
    total_staff_active = len(sorted_items)

    count = 0
    for mod_id_str, stat in sorted_items:
        try:
            mod_id = int(mod_id_str)
        except ValueError:
            continue

        member = guild.get_member(mod_id) if guild else None
        user_name = member.display_name if member else f"Yetkili ({mod_id})"
        role_name = get_member_highest_role_name(member) if member else "Yetkili"

        discord_sec = stat.get("discord_time", 0)
        game_sec = stat.get("game_time", 0)
        supports = stat.get("supports", 0)
        tickets = stat.get("tickets", 0)

        total_supports += supports
        total_tickets += tickets

        # Süre formatları
        d_saat = int(discord_sec // 3600)
        d_dak = int((discord_sec % 3600) // 60)

        g_saat = int(game_sec // 3600)
        g_dak = int((game_sec % 3600) // 60)

        # Doluluk barları (Yeşil 🟩 / Beyaz ⬜)
        disc_bar = progress_bar(discord_sec, GUNLUK_HEDEF_SANIYE, length=10)
        game_bar = progress_bar(game_sec, GUNLUK_HEDEF_SANIYE, length=10)

        disc_durum = "✅ Tamamlandı" if discord_sec >= GUNLUK_HEDEF_SANIYE else f"⏳ %{int(min(1.0, discord_sec / GUNLUK_HEDEF_SANIYE) * 100)}"
        game_durum = f"%{int(min(1.0, game_sec / GUNLUK_HEDEF_SANIYE) * 100)}" if game_sec > 0 else "%0"

        rank_badge = rank_emojis[count] if count < len(rank_emojis) else f"#{count + 1}"
        count += 1

        field_title = f"{rank_badge} {user_name} • {role_name}"
        field_value = (
            f"🌐 **Discord Aktifliği:** `{d_saat}s {d_dak}dk` / `3s`\n"
            f"`{disc_bar}` ({disc_durum})\n"
            f"🎮 **ER:LC Oyun Aktifliği:** `{g_saat}s {g_dak}dk`\n"
            f"`{game_bar}` ({game_durum})\n"
            f"🎧 **Baktığı Destek:** `{supports}` adet  ┃  🎫 **Kapattığı Bilet:** `{tickets}` adet\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(name=field_title, value=field_value, inline=False)

    summary_text = f"👥 **Aktif Yetkili Sayısı:** {total_staff_active}  ┃  🎧 **Toplam Destek:** {total_supports}  ┃  🎫 **Toplam Bilet:** {total_tickets}"
    embed.set_footer(text=summary_text)
    embed.timestamp = discord.utils.utcnow()
    return embed


class DestekBitirModal(discord.ui.Modal, title="Desteği Sonlandır"):
    sonuc = discord.ui.TextInput(
        label="Katılımcı Neden Yardım İstedi? Sonuç Ne?",
        style=discord.TextStyle.paragraph,
        placeholder="Örn: Kullanıcının kayıt sorunu çözüldü, kurallar hatırlatıldı.",
        required=True,
        max_length=1000
    )

    def __init__(self, baslangic_zamani: datetime.datetime, yardim_isteyen_id: int):
        super().__init__()
        self.baslangic_zamani = baslangic_zamani
        self.yardim_isteyen_id = yardim_isteyen_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        bitis_zamani = discord.utils.utcnow()
        fark = bitis_zamani - self.baslangic_zamani
        dakika = int(fark.total_seconds() // 60)
        saniye = int(fark.total_seconds() % 60)
        sure_metni = f"{dakika} dk {saniye} sn"

        # Yetkilinin baktığı destek sayısını artır
        update_mod_stat(interaction.user.id, "supports", 1)

        log_kanal = interaction.guild.get_channel(ONLY_MOD_KANALI)
        if log_kanal:
            embed = discord.Embed(title="✅ Destek Sonlandırıldı", color=discord.Color.green())
            embed.description = (
                f"{interaction.user.mention}, <@{self.yardim_isteyen_id}> kullanıcısının desteğini sonlandırdı.\n"
                f"**Süre:** {sure_metni}\n"
                f"**Sonuç:** {self.sonuc.value}"
            )
            embed.set_footer(text="Piyade Roleplay Destek Sistemi")
            embed.timestamp = discord.utils.utcnow()
            try:
                await log_kanal.send(embed=embed)
            except Exception as e:
                print(f"[DESTEK LOG HATA] {e}", flush=True)

        await interaction.message.edit(content=f"✅ {interaction.user.mention} desteği sonlandırdı.", view=None, embed=None)
        await interaction.followup.send("✅ Destek başarıyla sonlandırıldı ve log iletildi.", ephemeral=True)


class DestekAktifView(discord.ui.View):
    def __init__(self, yetkili_id: int = None, yardim_isteyen_id: int = None, baslangic_zamani: datetime.datetime = None):
        super().__init__(timeout=None)
        self.yetkili_id = yetkili_id
        self.yardim_isteyen_id = yardim_isteyen_id
        self.baslangic_zamani = baslangic_zamani

    def _get_meta(self, interaction: discord.Interaction):
        yetkili_id = self.yetkili_id
        yardim_isteyen_id = self.yardim_isteyen_id
        baslangic = self.baslangic_zamani or discord.utils.utcnow()

        if interaction.message and interaction.message.embeds:
            footer = interaction.message.embeds[0].footer.text or ""
            for item in footer.split("|"):
                if item.startswith("yetkili:"):
                    try:
                        yetkili_id = int(item.split(":")[1])
                    except Exception:
                        pass
                elif item.startswith("kullanici:"):
                    try:
                        yardim_isteyen_id = int(item.split(":")[1])
                    except Exception:
                        pass
                elif item.startswith("baslangic:"):
                    try:
                        baslangic = datetime.datetime.fromtimestamp(int(item.split(":")[1]), tz=datetime.timezone.utc)
                    except Exception:
                        pass
        return yetkili_id, yardim_isteyen_id, baslangic

    @discord.ui.button(label="Desteği Bitir", style=discord.ButtonStyle.success, emoji="✅", custom_id="destek_bitir_btn")
    async def bitir_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        yetkili_id, yardim_isteyen_id, baslangic = self._get_meta(interaction)
        if yetkili_id and interaction.user.id != yetkili_id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Sadece desteği devralan yetkili bu işlemi yapabilir!", ephemeral=True)
        await interaction.response.send_modal(DestekBitirModal(baslangic, yardim_isteyen_id or 0))

    @discord.ui.button(label="Boş Çıktı", style=discord.ButtonStyle.secondary, emoji="🗑️", custom_id="destek_bos_btn")
    async def bos_cikti_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        yetkili_id, yardim_isteyen_id, _ = self._get_meta(interaction)
        if yetkili_id and interaction.user.id != yetkili_id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Sadece desteği devralan yetkili bu işlemi yapabilir!", ephemeral=True)
        await interaction.response.defer()

        log_kanal = interaction.guild.get_channel(ONLY_MOD_KANALI)
        if log_kanal:
            embed = discord.Embed(title="❌ Destek Boş Çıktı", color=discord.Color.light_grey())
            embed.description = f"{interaction.user.mention}, <@{yardim_isteyen_id}> kullanıcısının desteğini **'Boş'** olarak sonuçlandırdı."
            embed.set_footer(text="Piyade Roleplay Destek Sistemi")
            embed.timestamp = discord.utils.utcnow()
            try:
                await log_kanal.send(embed=embed)
            except Exception as e:
                print(f"[DESTEK BOŞ LOG HATA] {e}", flush=True)

        await interaction.message.edit(content=f"❌ {interaction.user.mention} desteği boş olarak sonlandırdı.", view=None, embed=None)
        await interaction.followup.send("Kullanıcı boş çıktığı için destek sonlandırıldı.", ephemeral=True)


class DevralView(discord.ui.View):
    def __init__(self, yardim_isteyen_id: int = None):
        super().__init__(timeout=None)
        self.yardim_isteyen_id = yardim_isteyen_id

    def _get_kullanici_id(self, interaction: discord.Interaction):
        if self.yardim_isteyen_id:
            return self.yardim_isteyen_id
        if interaction.message and interaction.message.embeds:
            footer = interaction.message.embeds[0].footer.text or ""
            if "destek_kullanici:" in footer:
                try:
                    return int(footer.split("destek_kullanici:")[1].strip())
                except Exception:
                    pass
        if interaction.message and interaction.message.mentions:
            return interaction.message.mentions[0].id
        return None

    @discord.ui.button(label="Katılımcıyı Devral", style=discord.ButtonStyle.success, emoji="👋", custom_id="destek_devral_btn")
    async def devral_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        kullanici_id = self._get_kullanici_id(interaction)
        yardim_isteyen = guild.get_member(kullanici_id) if kullanici_id else None
        yardim_kanal = guild.get_channel(YARDIM_VC_ID)

        if not yardim_isteyen or not yardim_isteyen.voice:
            await interaction.followup.send("❌ Katılımcı şu anda seste değil!", ephemeral=True)
            await interaction.message.edit(content="❌ Katılımcı sesten ayrıldığı için işlem iptal edildi.", view=None, embed=None)
            return

        try:
            await yardim_isteyen.move_to(yardim_kanal)
            await yardim_isteyen.edit(mute=False)
        except Exception:
            await interaction.followup.send("❌ Kullanıcı odaya çekilirken hata oluştu. (Belki sesten çıkmıştır)", ephemeral=True)
            return

        baslangic = discord.utils.utcnow()
        active_embed = discord.Embed(
            title="🎧 Destek Devralındı",
            description=f"👋 {interaction.user.mention}, <@{kullanici_id}> kullanıcısının desteğini devraldı.\n(Odaya çekildi ve susturması açıldı)",
            color=discord.Color.blue()
        )
        active_embed.set_footer(text=f"yetkili:{interaction.user.id}|kullanici:{kullanici_id}|baslangic:{int(baslangic.timestamp())}")
        active_embed.timestamp = discord.utils.utcnow()

        await interaction.message.edit(
            content=None,
            embed=active_embed,
            view=DestekAktifView(interaction.user.id, kullanici_id, baslangic)
        )
        await interaction.followup.send("Destek başarıyla devralındı.", ephemeral=True)

    @discord.ui.button(label="Beklemeden Çıkar", style=discord.ButtonStyle.danger, emoji="🚪", custom_id="destek_at_btn")
    async def at_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        kullanici_id = self._get_kullanici_id(interaction)
        yardim_isteyen = guild.get_member(kullanici_id) if kullanici_id else None

        if yardim_isteyen and yardim_isteyen.voice:
            try:
                await yardim_isteyen.move_to(None)
            except Exception:
                pass

        log_kanal = interaction.guild.get_channel(ONLY_MOD_KANALI)
        if log_kanal:
            embed = discord.Embed(title="🚪 Katılımcı Atıldı", color=discord.Color.red())
            embed.description = f"{interaction.user.mention}, <@{kullanici_id}> kullanıcısını **Yardım Bekleme** kanalından beklemeden çıkardı."
            embed.set_footer(text="Piyade Roleplay Destek Sistemi")
            embed.timestamp = discord.utils.utcnow()
            try:
                await log_kanal.send(embed=embed)
            except Exception as e:
                print(f"[BEKLEMEDEN ÇIKAR LOG HATA] {e}", flush=True)

        await interaction.message.edit(content=f"🚪 {interaction.user.mention}, katılımcıyı beklemeden çıkardı.", view=None, embed=None)


class YardimBekleme(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = None
        self.activity_tracker_loop.start()
        self.gunluk_rapor.start()

    def cog_unload(self):
        self.activity_tracker_loop.cancel()
        self.gunluk_rapor.cancel()
        if self.session and not self.session.closed:
            self.bot.loop.create_task(self.session.close())

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    # =========================================================================
    # ER:LC OYUN VE DISCORD AKTİFLİK DÖNGÜSÜ (30 Saniyede bir)
    # =========================================================================
    @tasks.loop(seconds=30)
    async def activity_tracker_loop(self):
        """
        Kullanıcının isteği:
        - Ses kanalı aktifliği okunmaz!
        - Discord aktifliği (Online, Idle, DND) okunur ve kaydedilir.
        - Roblox ER:LC oyunundaki yetkililerin oyun içi aktifliği okunur ve kaydedilir.
        """
        if not self.bot.is_ready():
            return

        guild = self.bot.get_guild(int(os.getenv("GUILD_ID", "1529545898294509589")))
        if not guild:
            return

        # 1. ER:LC API'sinden Aktif Oyuncuları Çek
        erlc_players = set()
        if ERLC_API_KEY:
            try:
                session = await self.get_session()
                headers = {"Server-Key": ERLC_API_KEY}
                async with session.get("https://api.erlc.gg/v2/server?Players=true", headers=headers, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        players = data.get("Players", [])
                        for p in players:
                            p_str = p.get("Player", "")
                            if p_str:
                                username = p_str.split(":")[0].strip().lower()
                                erlc_players.add(username)
            except Exception:
                pass

        # 2. Yetkililerin Aktifliğini Değerlendir
        roblox_mappings = load_roblox_mapping()

        for member in guild.members:
            if member.bot:
                continue

            # Yetkili rollerinden birine sahip mi?
            is_staff = any(r.id in YETKILI_ROL_IDLERI for r in member.roles) or member.guild_permissions.administrator
            if not is_staff:
                continue

            discord_active = False
            # Yeşil (aktif), ay (boşta), kırmızı (rahatsız etmeyin) aktif sayılır
            if member.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd):
                discord_active = True

            # Oyun içi aktif mi?
            game_active = False
            assigned_roblox = roblox_mappings.get(str(member.id), "").lower()
            if assigned_roblox and assigned_roblox in erlc_players:
                game_active = True
            elif erlc_players:
                # İsim eşleme kontrolü (display name veya nick eşleşmesi)
                name_clean = member.name.lower()
                display_clean = member.display_name.lower()
                for player_name in erlc_players:
                    if player_name == name_clean or player_name == display_clean or player_name in display_clean:
                        game_active = True
                        break

            # 30 saniye ekle
            sec_discord = 30 if discord_active else 0
            sec_game = 30 if game_active else 0

            if sec_discord > 0 or sec_game > 0:
                add_mod_active_time(member.id, discord_seconds=sec_discord, game_seconds=sec_game)

    # =========================================================================
    # SES KANALI OLAYLARI (Yardım Bekleme, Mute ve Bildirim)
    # =========================================================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        # Kullanıcı Yardım Bekleme odasına girdiğinde
        if after.channel and after.channel.id == YARDIM_BEKLEME_VC_ID and (before.channel is None or before.channel.id != YARDIM_BEKLEME_VC_ID):
            try:
                await member.edit(mute=True)
            except Exception:
                pass

            # Rol saatleri dışı (TSİ gece 01:00 - öğlen 12:00 arası) log bildirimi gönderilmez
            tz_tr = datetime.timezone(datetime.timedelta(hours=3))
            tr_saat = datetime.datetime.now(tz_tr).time()
            if datetime.time(1, 0) <= tr_saat < datetime.time(12, 0):
                return

            kanal = self.bot.get_channel(ONEMLI_LOG_KANALI)
            if kanal:
                embed = discord.Embed(
                    title="👀 Yardım Bekleyen Var!",
                    description=f"{member.mention} **Yardım Bekleme** kanalına giriş yaptı ve destek bekliyor.",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"destek_kullanici:{member.id}")
                embed.timestamp = discord.utils.utcnow()

                ping_msg = f"<@&{DESTEK_BEKLEME_YETKILISI_ROL}>"
                try:
                    await kanal.send(content=ping_msg, embed=embed, view=DevralView(member.id))
                except Exception as e:
                    print(f"[YARDIM BEKLEME BILDIRIM HATA] {e}", flush=True)

        # Kullanıcı Yardım Bekleme odasından çıktığında susturmasını aç
        elif before.channel and before.channel.id == YARDIM_BEKLEME_VC_ID:
            if after.channel is not None and after.channel.id != YARDIM_BEKLEME_VC_ID:
                try:
                    await member.edit(mute=False)
                except Exception:
                    pass

    # =========================================================================
    # KOMUTLAR
    # =========================================================================
    @app_commands.command(name="destek-bildir", description="Belirtilen kullanıcıyı resmi formatla destek bekleme odasına çağırır.")
    @app_commands.describe(
        kisi="Çağrılacak kişi",
        sebep="Çağrı sebebi",
        tahmini_sure="Tahmini destek süresi"
    )
    async def destek_bildir(self, interaction: discord.Interaction, kisi: discord.Member, sebep: str, tahmini_sure: str):
        yetkili_rol_adi = get_member_highest_role_name(interaction.user)

        user_roles = {
            1539249508314259567: "İllegal",
            1539318613498929193: "Legal"
        }

        kisi_rol_adi = "Sivil"
        for role_id, role_name in user_roles.items():
            if discord.utils.get(kisi.roles, id=role_id):
                kisi_rol_adi = role_name
                break

        destek_id = get_next_destek_id()

        embed = discord.Embed(
            description=(
                f"## ✉️ Destek Çağrı Bildirimi\n"
                f"Kullanıcı destek bekleme ses kanalına yönlendirildi.\n"
                f"{kisi.mention} | {kisi_rol_adi}\n\n"
                f"***\n\n"
                f"### 📌 Çağrı Bilgisi\n"
                f"• **Çağrı ID:** `{destek_id}`\n"
                f"• **Kullanıcı:** {kisi.mention} | {kisi_rol_adi}\n"
                f"• **Çağıran Yetkili:** {interaction.user.mention} | {yetkili_rol_adi}\n"
                f"• **Süre:** {tahmini_sure}\n\n"
                f"***\n\n"
                f"### ✨ Yönlendirme\n"
                f"• **Sebep:** {sebep}\n\n"
                f"Lütfen [Yardım bekleme](https://discord.com/channels/{interaction.guild.id}/{YARDIM_BEKLEME_VC_ID}) ses kanalına geçiniz. Yetkili hazır olduğunda destek odasına alınacaksınız."
            ),
            color=discord.Color.from_rgb(254, 231, 92)  # #FEE75C Sarı renk
        )

        embed.set_footer(text="© 2026 PRP • Destek Bildirim Servisi")

        logo_path = os.path.join(BASE_DIR, "assets", "uyari_logo.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(BASE_DIR, "assets", "yeni_banner.png")

        file_attachment = None
        if os.path.exists(logo_path):
            file_attachment = discord.File(logo_path, filename="logo.png")
            embed.set_thumbnail(url="attachment://logo.png")
        elif interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        target_channel = interaction.client.get_channel(DESTEK_CAGRI_KANALI)
        if target_channel:
            if file_attachment:
                await target_channel.send(content=f"{kisi.mention}", embed=embed, file=file_attachment)
            else:
                await target_channel.send(content=f"{kisi.mention}", embed=embed)
            await interaction.response.send_message("✅ Bildirim başarıyla gönderildi.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Hedef kanal bulunamadı (`{DESTEK_CAGRI_KANALI}`).", ephemeral=True)

    @app_commands.command(name="yetkili-tablo", description="Yetkili performans, aktiflik, destek ve bilet sıralama tablosunu gösterir.")
    async def yetkili_tablo(self, interaction: discord.Interaction):
        """
        Kullanıcının isteği:
        Kurucu veya Üst Yönetim tarafından kullanılabilen, sarı renkli, yüksek dekorasyonlu sıralama tablosu.
        """
        is_authorized = (
            any(r.id in (KURUCU_ROL_ID, UST_YONETIM_ROL_ID) for r in interaction.user.roles) or
            interaction.user.guild_permissions.administrator
        )
        if not is_authorized:
            return await interaction.response.send_message(
                "❌ Bu komutu yalnızca **Kurucu** veya **Üst Yönetim** kullanabilir!", ephemeral=True
            )

        await interaction.response.defer()
        embed = build_leaderboard_embed(self.bot, interaction.guild, color=discord.Color.gold(), is_nightly=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="roblox-bagla", description="Bir yetkilinin Roblox kullanıcı adını sisteme kaydeder.")
    @app_commands.describe(
        yetkili="Roblox hesabı bağlanacak yetkili",
        roblox_kullanici_adi="Yetkilinin tam Roblox kullanıcı adı"
    )
    async def roblox_bagla(self, interaction: discord.Interaction, yetkili: discord.Member, roblox_kullanici_adi: str):
        is_authorized = (
            any(r.id in (KURUCU_ROL_ID, UST_YONETIM_ROL_ID) for r in interaction.user.roles) or
            interaction.user.guild_permissions.administrator or
            interaction.user.id == yetkili.id
        )
        if not is_authorized:
            return await interaction.response.send_message("❌ Bu işlemi yapmaya yetkiniz yok.", ephemeral=True)

        set_roblox_name(yetkili.id, roblox_kullanici_adi)
        await interaction.response.send_message(
            f"✅ {yetkili.mention} için Roblox hesabı **{roblox_kullanici_adi}** olarak başarıyla kaydedildi.",
            ephemeral=True
        )

    # =========================================================================
    # OTOMATİK GECE 00:00 RAPORU VE SIFIRLAMA
    # =========================================================================
    @tasks.loop(time=datetime.time(hour=21, minute=0, tzinfo=datetime.timezone.utc))
    async def gunluk_rapor(self):
        """
        Her gece Türkiye saatiyle 00:00'da (21:00 UTC) otomatik tetiklenir.
        Rapor Only Mod kanalına sarı/altın şık bir embed ile iletilir ve veriler arşivlenerek sıfırlanır.
        """
        await self.bot.wait_until_ready()
        kanal = self.bot.get_channel(ONLY_MOD_KANALI)
        if not kanal:
            try:
                kanal = await self.bot.fetch_channel(ONLY_MOD_KANALI)
            except Exception:
                return

        guild = kanal.guild
        embed = build_leaderboard_embed(self.bot, guild, color=discord.Color.gold(), is_nightly=True)
        try:
            await kanal.send(content="🌙 **Günün Kapanış Raporu (00:00 TSİ)**", embed=embed)
        except Exception as e:
            print(f"[GUNLUK RAPOR GÖNDERME HATA] {e}", flush=True)

        # Günlük verileri arşive kaydet ve sıfırla
        archive_and_reset_daily()


async def setup(bot: commands.Bot):
    await bot.add_cog(YardimBekleme(bot))
