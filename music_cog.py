import discord
from discord.ext import commands
import os
import logging

from yt_dlp import YoutubeDL

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord_bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

class music_cog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

        self.is_playing = False
        self.is_paused = False



        self.music_queue = []
        self.YDL_OPTIONS = {
                            'format': 'bestaudio/best',
                            'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',
                            }],
                            'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
                        }
        self.FFMPEG_OPTIONS = {
                            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                            'options': '-vn'
                        }
        
        self.vc = None
    
    
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception as e:
                print(f"Error: {e}")
                return False

        print("URL found:", info['url'])  
        return {'source': info['url'], 'title': info['title']}

    

    @commands.command(name="playlocal")
    async def play_local(self, ctx):
        logger.info("play_local command invoked") 

        file_path = "/Users/darosaleh/discord-music-bot/music_bot/output.mp3"
        if not os.path.exists(file_path):
            await ctx.send("File not found.")
            logger.error("File not found at specified path") 
            return

        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                logger.info("Connected to the voice channel") 
            else:
                await ctx.send("You are not connected to a voice channel.")
                return

        ctx.voice_client.play(discord.FFmpegPCMAudio(file_path), after=lambda e: logger.error(f'Player error: {e}') if e else None)
        logger.info(f"Started playing: {file_path}")  
    

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after= lambda e: self.play_next())
        else:
            self.is_playing = False
    
    async def play_music(self, ctx):
        print("play_music called")  

        if len(self.music_queue) > 0:
            print("Music queue is not empty")  

            self.is_playing = True
            m_url = self.music_queue[0][0]['source']
            print(f"URL to play: {m_url}")  

            if self.vc is None or not self.vc.is_connected():
                print("Connecting to the voice channel...")  
                self.vc = await self.music_queue[0][1].connect()

            if self.vc is None:
                print("Failed to connect to the voice channel")  
                await ctx.send("Could not connect to the voice channel")
                return
            else:
                print("Moving to the voice channel...")  
                await self.vc.move_to(self.music_queue[0][1])

            self.music_queue.pop(0)
            print(f"Starting playback: {m_url}")  
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            print("Music queue is empty")  
            self.is_playing = False

    
    @commands.command(name="play", aliases = ["p", "playing"], help="Play the selected song" )
    async def play(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format, try a different keyword")
            else:
                await ctx.send("Song added to the queue")
                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)
    
    @commands.command(name="pause",help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
    
    @commands.command(name="resume", aliases = ["r"], help = "Resumes playing current song")
    async def resume(self,ctx, *args):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
    
    @commands.command(name="skip", aliases = ["s"], help = "Skips the currently played songs")
    async def skip(self, ctx, *args):
        if self.vc != None and self.vc:
            self.vc.stop()
            await self.play_music(ctx)
        
    @commands.command(name="queue", aliases = ["q"], help="Displays all the songs currently in the queue")
    async def queue(self,ctx):
        retval = ""

        for i in range(0, len(self.music_queue)):
            if i > 4: break
            retval += self.music_queue[i][0]['title'] + '\n'
        
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in the queue")
    
    @commands.command(name="clear", aliases =["c", "bin"], help="Stops the current song and clears the queue")
    async def clear(self, ctx, *args):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue cleared")
    
    @commands.command(name="leave", aliases= ["disconnect", "l", "d"], help = "kick the bot from channel")
    async def leave(self ,ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()
                    

