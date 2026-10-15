import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from config import (
    TICKET_KANAL_ID,
    BILET_LOG_KANAL_ID,
    YETKILI_ROL_IDLERI,
    KURUCU_ROL_ID,
    TICKET_YETKILISI_ROL,
    YONETICI_ROL_ID
)
from utils.stats_manager import update_mod_stat

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def yetkili_mi(member: discord.Member) -> bool:
    """Kullanıcının sunucu yöneticisi veya tanımlı yetkili rollerine sahip olup olmadığını kontrol eder."""
    if member.guild_permissions.administrator:
        return True
    return any(r.id in YETKILI_ROL_IDLERI for r in member.roles)


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Kapat", style=discord.ButtonStyle.red, custom_id="ticket_kapat_buton")
    async def kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not yetkili_mi(interaction.user):
            return await interaction.response.send_message(
                "❌ Bu işlemi sadece yetkililer yapabilir.", ephemeral=True
            )

        kanal = interaction.channel
        topic = kanal.topic or ""
        acan_id = None
        if "acan_id:" in topic:
            try:
                acan_id = int(topic.split("acan_id:")[1].strip())
            except Exception:
                acan_id = None

        acan_uye = kanal.guild.get_member(acan_id) if acan_id else None

        # Yetkilinin kapattığı bilet istatistiğini artır
        update_mod_stat(interaction.user.id, "tickets", 1)

        # Log kanalına bildir
        log_kanal = kanal.guild.get_channel(BILET_LOG_KANAL_ID)
        if log_kanal:
            embed = discord.Embed(
                title="🔒 Ticket Kapatıldı",
                color=discord.Color.red(),
            )
            embed.add_field(name="Kanal", value=f"#{kanal.name}", inline=True)
            embed.add_field(name="Açan Kişi", value=acan_uye.mention if acan_uye else f"Bilinmiyor (`ID: {acan_id}`)", inline=True)
            embed.add_field(name="Kapatan Yetkili", value=interaction.user.mention, inline=True)
            embed.add_field(name="Açılış Tarihi", value=discord.utils.format_dt(kanal.created_at, style="F"), inline=False)
            embed.add_field(name="Kapanış Tarihi", value=discord.utils.format_dt(discord.utils.utcnow(), style="F"), inline=False)
            embed.set_footer(text="Piyade Roleplay Bilet Sistemi")
            embed.timestamp = discord.utils.utcnow()
            try:
                await log_kanal.send(embed=embed)
            except Exception as e:
                print(f"[TICKET LOG HATA] {e}", flush=True)

        await interaction.response.send_message("Kanal 5 saniye içinde silinecek...")
        await asyncio.sleep(5)
        try:
            await kanal.delete(reason=f"Ticket kapatıldı - {interaction.user}")
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"[TICKET SİLME HATA] {e}", flush=True)


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket Aç", style=discord.ButtonStyle.green, custom_id="ticket_ac_buton")
    async def ticket_ac(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        kullanici_adi = interaction.user.name.lower()
        kanal_adi = f"ticket-{kullanici_adi}"
        acan_tag = f"acan_id:{interaction.user.id}"

        # Mükerrer bilet kontrolü: Topic veya kanal adı kontrolü
        var_olan = next((c for c in guild.text_channels if c.topic and acan_tag in c.topic), None)
        if not var_olan:
            var_olan = discord.utils.get(guild.text_channels, name=kanal_adi)
        if var_olan:
            return await interaction.response.send_message(
                f"Zaten açık bir ticket'ın var: {var_olan.mention}", ephemeral=True
            )

        # İzin haritası (Permissions)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True
            ),
        }

        # Ticket Yetkilisi ve diğer yetkili rollerine izin ver
        bilet_yetkili_rol = guild.get_role(TICKET_YETKILISI_ROL)
        if bilet_yetkili_rol:
            overwrites[bilet_yetkili_rol] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )

        for rol_id in YETKILI_ROL_IDLERI:
            rol = guild.get_role(rol_id)
            if rol and rol not in overwrites:
                overwrites[rol] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )

        kategori = interaction.channel.category

        try:
            kanal = await guild.create_text_channel(
                kanal_adi,
                overwrites=overwrites,
                category=kategori,
                topic=acan_tag,
            )
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Botun kanal oluşturma yetkisi yok.", ephemeral=True)
        except Exception as e:
            return await interaction.response.send_message(f"❌ Kanal oluşturulurken bir hata oluştu: `{e}`", ephemeral=True)

        embed = discord.Embed(
            title="🎫 Destek Talebi",
            description=f"{interaction.user.mention} bir destek talebi oluşturdu.\nYetkililerimiz en kısa sürede sizinle ilgilenecektir.",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Görüşme tamamlandığında yetkili aşağıdaki butondan bileti kapatabilir.")
        embed.timestamp = discord.utils.utcnow()

        rol_etiketi = f"<@&{TICKET_YETKILISI_ROL}>"
        await kanal.send(content=f"{interaction.user.mention} {rol_etiketi}", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket başarıyla açıldı: {kanal.mention}", ephemeral=True)


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ticket-panel", description="Ticket açma panelini bu kanala gönderir.")
    async def ticket_panel(self, interaction: discord.Interaction):
        # Sadece Kurucu veya Yönetici yetkisi olanlar
        is_kurucu = any(r.id == KURUCU_ROL_ID for r in interaction.user.roles)
        if not (is_kurucu or interaction.user.guild_permissions.administrator):
            return await interaction.response.send_message("❌ Bu komutu sadece **Kurucu** kullanabilir!", ephemeral=True)

        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Bu komut için `Kanalları Yönet` yetkiniz olmalıdır.", ephemeral=True)

        desc = (
            "### • Bilet açma işlemini boşa kullanmayınız. 😇\n\n"
            "### • Bilet butonuna basarak biletinizi açabilirsiniz.\n\n"
            f"### • Bileti açtıktan sonra bot yardımcı olacaktır fakat eğer bot istediğiniz yardımı sağlayamadıysa yönetim kadrosunu etiketleyebilirsiniz. [<@&{YONETICI_ROL_ID}>]\n\n"
            "### • Bileti açtığınızda saçma sorular sormayın, şımarmayın.\n\n"
            "### • Biz sizlere yardımcı olmak istiyoruz, nasıl yardım edebiliriz? 🌸"
        )
        embed = discord.Embed(
            title="🎫 Destek Sistemi",
            description=desc,
            color=discord.Color.blurple(),
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Piyade Roleplay Destek Sistemi")

        await interaction.response.defer(ephemeral=True)
        banner_path = os.path.join(BASE_DIR, "assets", "yeni_banner.png")
        if os.path.exists(banner_path):
            file = discord.File(banner_path, filename="yeni_banner.png")
            embed.set_image(url="attachment://yeni_banner.png")
            await interaction.channel.send(embed=embed, file=file, view=TicketPanelView())
        else:
            await interaction.channel.send(embed=embed, view=TicketPanelView())

        await interaction.followup.send("✅ Panel başarıyla gönderildi.", ephemeral=True)

    @app_commands.command(name="ekle", description="Mevcut bilete bir veya birden fazla kullanıcı ekler.")
    @app_commands.describe(
        kisi1="Bilete eklenecek 1. kullanıcı",
        kisi2="Bilete eklenecek 2. kullanıcı (İsteğe bağlı)",
        kisi3="Bilete eklenecek 3. kullanıcı (İsteğe bağlı)"
    )
    async def ekle(
        self,
        interaction: discord.Interaction,
        kisi1: discord.Member,
        kisi2: discord.Member = None,
        kisi3: discord.Member = None
    ):
        kanal = interaction.channel
        topic = kanal.topic or ""
        if "acan_id:" not in topic:
            return await interaction.response.send_message(
                "❌ Bu komut sadece bilet (ticket) kanallarında kullanılabilir.", ephemeral=True
            )

        acan_id = None
        try:
            acan_id = int(topic.split("acan_id:")[1].strip())
        except Exception:
            pass

        if interaction.user.id != acan_id and not yetkili_mi(interaction.user):
            return await interaction.response.send_message(
                "❌ Bu bilete kişi ekleme yetkiniz yok.", ephemeral=True
            )

        kisiler = [k for k in [kisi1, kisi2, kisi3] if k is not None]
        eklenenler = []
        for k in kisiler:
            await kanal.set_permissions(
                k,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
            eklenenler.append(k.mention)

        await interaction.response.send_message(f"✅ Başarıyla bilete eklendi: {', '.join(eklenenler)}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
