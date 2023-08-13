# -*- coding: utf-8 -*-
import datetime
import itertools
from os.path import basename
import disnake

from utils.music.converters import fix_characters, time_format, get_button_style, music_source_image
from utils.music.models import LavalinkPlayer
from utils.others import ProgressBar, PlayerControls


class DefaultProgressbarSkin:

    __slots__ = ("name", "preview")

    def __init__(self):
        self.name = basename(__file__)[:-3]
        self.preview = ""

    def setup_features(self, player: LavalinkPlayer):
        player.mini_queue_feature = True
        player.controller_mode = True
        player.auto_update = 15
        player.hint_rate = player.bot.config["HINT_RATE"]
        player.static = False

    def load(self, player: LavalinkPlayer) -> dict:

        data = {
            "content": None,
            "embeds": []
        }

        embed = disnake.Embed(
            color=disnake.Color.random()
        )

        embed.set_author(
            name=f"{fix_characters(player.current.single_title, limit=24)}",
            url=player.current.uri or player.current.search_uri,
            icon_url=music_source_image(player.current.info["sourceName"]) if not player.paused else "https://cdn.discordapp.com/emojis/1140220668110180352.png"
        )

        embed.set_thumbnail(url=player.current.thumb)

        embed.description = f"<:author:1140220381320466452> <@{player.current.requester}> "

        if player.current.is_stream:
            embed.description += f"| 🔴 **LIVESTREAM**"
        else:
            embed.description += f"| 🕘 `{player.position} / {player.current.duration}`"

        if player.command_log:
            embed.description += f"\n\n> <:recent:1140220838470242355> {player.command_log}"

        song_info = f"> {player.current.authors_md}"

        if player.current.album_name:
            song_info += f"\n> <:library:1140220586640019556> [`{fix_characters(player.current.album_name, limit=16)}`]({player.current.album_url})"

        if player.current.playlist_name:
            song_info += f"\n> <:playlist:1140220773051678811> [`{fix_characters(player.current.playlist_name, limit=16)}`]({player.current.playlist_url})"

        if (qlenght:=len(player.queue)) and not player.mini_queue_enabled:
            song_info += f"\n> <a:raging:1117802405791268925> `{qlenght}` bài hát đang chờ"

        embed.add_field(
            name="<:music:1140220553135931392> **Thông tin**",
            value=song_info,
            inline=True
        )

        config = f"> <:volume:1140221293950668820> `{player.volume}%`"

        if player.loop:
            config += f"\n> <:loop:1140220877401772092> `{'Bài hát' if player.loop == 'current' else 'Toàn bộ'}`"

        if player.nightcore:
            config += f"\n> <:nightcore:1140227024108130314> Nightcore"

        if player.current.autoplay:
            config += f"> <:disc:1140220627781943339> Tự động phát "
            try: config += f" [`(ref.)`]({player.current.info['extra']['related']['uri']})"
            except: config += " "
        
        if player.keep_connected:
            txt += f"\n> <:247:1140230869643169863> 24/7"

        elif player.restrict_mode:
            txt += f"\n> 🔐 Hạn chế"

        embed.add_field(
            name=f"<:host:1140221179920138330> **{player.node.identifier}** [{player.ping}]",
            value=config,
            inline=True
        )

        if player.current_hint:
            embed.set_footer(
                text=f"{player.current_hint}",
                icon_url="https://cdn.discordapp.com/emojis/1105722934317826088.gif?size=96&quality=lossless"
            )

        if qlenght and player.mini_queue_enabled:

            queue_txt = "\n".join(
                f"`{(n + 1):02}) [{time_format(t.duration) if not t.is_stream else '🔴 Livestream'}]` [`{fix_characters(t.title, 38)}`]({t.uri})"
                for n, t in (enumerate(itertools.islice(player.queue, 3)))
            )

            embed_queue = disnake.Embed(title=f"Danh sách chờ:  {qlenght}", color=player.bot.get_color(player.guild.me),
                                        description=f"\n{queue_txt}")

            if not player.loop and not player.keep_connected and not player.paused and not player.current.is_stream:

                queue_duration = 0

                for t in player.queue:
                    if not t.is_stream:
                        queue_duration += t.duration

                if queue_duration:
                    embed_queue.description += f"\n`[⌛ ` <t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=(queue_duration + (player.current.duration if not player.current.is_stream else 0)) - player.position)).timestamp())}:R> `⌛]`"

        try:
            data["embeds"] = [embed_queue, embed]
        except:
            data["embeds"] = [embed]

        data["components"] = [
            disnake.ui.Button(emoji="<:previous:1140221118926553098>", custom_id=PlayerControls.back),
            disnake.ui.Button(
                emoji=f"{'<:play:1140220726327136427>' if not player.paused else '<:pause:1140220668110180352>'}",
                custom_id=PlayerControls.pause_resume
            ),
            disnake.ui.Button(emoji="<:next:1140220443098353695>", custom_id=PlayerControls.skip),
            disnake.ui.Button(emoji="<:stop:1140221258575925358>", custom_id=PlayerControls.stop),
            disnake.ui.Button(
                emoji="<:music_queue:703761160679194734>",
                custom_id=PlayerControls.queue,
                disabled=not player.queue
            ),
            disnake.ui.Select(
                placeholder="Lựa chọn khác:",
                custom_id="musicplayer_dropdown_inter",
                min_values=0, max_values=1,
                options=[
                    #   
                    disnake.SelectOption(
                        label="Thêm bài hát", emoji="<:addsong:1140220013580664853>",
                        value=PlayerControls.add_song,
                        description="Thêm một bài hát/danh sách phát vào trong Danh sách chờ."
                    ),
                    disnake.SelectOption(
                        label="Thêm bài hát từ danh sách yêu thích", emoji="⭐",
                        value=PlayerControls.enqueue_fav,
                        description="Thêm bài hát/danh sách phát yêu thích của bạn vào trong Danh sách chờ."
                    ),
                    disnake.SelectOption(
                            label="Yêu thích", emoji="💗",
                            value=PlayerControls.add_favorite,
                            description="Thêm bài hát hiện tại vào mục yêu thích của bạn."
                    ),
                    disnake.SelectOption(
                        label="Phát lại", emoji="<:rewind:1140221035799642174>",
                        value=PlayerControls.seek_to_start,
                        description="Phát lại bài hát hiện tại từ đầu."
                    ),
                    disnake.SelectOption(
                        label="Âm lượng", emoji="<:volume:1140221293950668820>",
                        value=PlayerControls.volume,
                        description="Điều chỉnh âm lượng"
                    ),
                    disnake.SelectOption(
                        label="Trộn", emoji="<:shuffle:1140221078095020062>",
                        value=PlayerControls.shuffle,
                        description="Trộn nhạc trong Danh sách chờ."
                    ),
                    disnake.SelectOption(
                        label="Thêm lại", emoji="<:library:1140220586640019556>",
                        value=PlayerControls.readd,
                        description="Đưa các bài hát đã phát trở lại danh sách chờ."
                    ),
                    disnake.SelectOption(
                        label="Chế độ lặp lại", emoji="<:loop:1140220877401772092>",
                        value=PlayerControls.loop_mode,
                        description="Bật/tắt chế độ lặp lại."
                    ),
                    disnake.SelectOption(
                        label=("Tắt" if player.autoplay else "Bật") + " tự động phát", emoji="<:music:1140220553135931392>",
                        value=PlayerControls.autoplay,
                        description="Tự động phát các bài hát được gợi ý khi danh sách chờ trống."
                    ),
                    disnake.SelectOption(
                        label="Nightcore", emoji="<:nightcore:1140227024108130314>",
                        value=PlayerControls.nightcore,
                        description="Bật/tắt hiệu ứng Nightcore."
                    ),
                    disnake.SelectOption(
                        label="Hạn chế", emoji="🔐",
                        value=PlayerControls.restrict_mode,
                        description="Hạn chế người khác điều khiển trình phát của bạn."
                    )
                ]
            ),
        ]

        if player.mini_queue_feature:
            data["components"][5].options.append(
                disnake.SelectOption(
                    label="Danh sách phát mini", emoji="<:music_queue:703761160679194734>",
                    value=PlayerControls.miniqueue,
                    description="Bật/tắt danh sách phát mini."
                )
            )

        if not player.static and not player.has_thread:
            data["components"][5].options.append(
                disnake.SelectOption(
                    label="Tạo chủ đề", emoji="💬",
                    value=PlayerControls.song_request_thread,
                    description="Tạo một chủ đề tạm thời để thêm nhạc bằng tên/liên kết."
                )
            )

        return data

def load():
    return DefaultProgressbarSkin()
