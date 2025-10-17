import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp


queue = list()
current_song = None
#Cargar variables de entorno
load_dotenv()

#Obtener token de .env
token = os.getenv('discord_token')
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("spotipy_client_id"),
    client_secret=os.getenv("spotipy_client_secret")
))

#Definir intents y el bot
intents = discord.Intents.default()
intents.message_content = True #Para que pueda leer los mensajes
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f'¡{bot.user} se ha conectado a Discord y está listo')


@bot.command(name='play')
async def play_single_track(ctx, *, query: str):
    track_info = search_track(query)
    if not track_info:
        await ctx.send("No hallé esa rola")
        return

    # 1. Conectar al canal de voz si no está conectado
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Primero métete a un canal de voz y luego ya.")
            return

    # 2. Añadir la canción a la cola
    queue.append(track_info)
    await ctx.send(f"**{track_info}** añadida a la cola.")

    # 3. Iniciar la reproducción si no está sonando nada
    if not ctx.voice_client.is_playing():
        await play_next_song(ctx)

async def play_next_song(ctx):
    global current_song
    
    if queue:
        YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        query = queue.pop(0)
        current_song = query
        voice_client = ctx.voice_client
        
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch1:{query} audio", download=False)
                
                # Nos aseguramos de que 'entries' existe y no está vacío
                if 'entries' in info and len(info['entries']) > 0:
                    url = info['entries'][0]['url']
                    voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options), after=lambda e: bot.loop.create_task(play_next_song(ctx)))
                    await ctx.send(f"▶Ahora reproduciendo: **{query}**")
                else:
                    await ctx.send(f"No pude encontrar una fuente de audio para **{query}**.")
                    # Llama a la siguiente canción si falla
                    await play_next_song(ctx)

            except Exception as e:
                await ctx.send(f"Ocurrió un error al intentar reproducir **{query}**.")
                print(f"Error en yt-dlp con la query '{query}': {e}")
                # Llama a la siguiente canción si falla
                await play_next_song(ctx)
    else:
        await ctx.send("Se acabó la cola, pon más rolas pero ya.")
        current_song = None

def search_track(query: str) -> list | None:
    try:
        # Hacemos la búsqueda, limitando a 1 resultado de tipo 'track'
        results = sp.search(q=query, limit=1, type='track')
        
        # Verificamos si la búsqueda encontró algo
        if results and results['tracks']['items']:
            track_info = results['tracks']['items'][0]
            track_name = track_info['name']
            artist_names = ', '.join([artist['name'] for artist in track_info['artists']])
            return f"{track_name} - {artist_names}"            
            
    except Exception as e:
        print(f"Error al buscar la canción: {e}")
    
    # Si no se encuentra nada o hay un error, devolvemos None
    return None


@bot.command(name='playlist') #Para cuando en el chat pongan /playlist <link de la playlist>
async def play_playlist(ctx, *, url: str): #ctx es el contexto, proporciona info de donde se origino el comando (servidor, usuario etc)
    try:
        # Conectar al canal de voz ANTES de buscar las canciones
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Primero métete a un canal de voz y luego ya.")
                return

        playlist_id = get_playlist_id(url)        
        
        if not playlist_id:
            await ctx.send("Ese link no jala Pa; tiene que ser el link de una playlist.")
            return
        
        track_list = get_tracks_from_playlist(playlist_id)
        
        if not track_list:
            await ctx.send("Esa playlist está vacía, no te pases de cangreburguer.")
            return
        
        # Añade TODAS las canciones a la cola de una vez
        queue.extend(track_list)
        
        await ctx.send(f"Gucci, se añadieron {len(track_list)} rolas a la cola.")
        
        # Inicia la reproducción si no está sonando nada
        if not ctx.voice_client.is_playing():
            await play_next_song(ctx)
        
    except Exception as e:
        await ctx.send(f'Error al cargar la playlist: {e}')
        print(f'Error al cargar la playlist: {e}')

def get_playlist_id(url: str) -> str:
    if '/playlist/' in url:
        # Se divide la URL a partir de '/playlist/' y solo se toma la segunda parte
        potential_id = url.split('/playlist/')[1]
        
        # Se eliminan parámetros adicionales (como ?si=...)
        playlist_id = potential_id.split('?')[0]
        return playlist_id
    
    return None

def get_tracks_from_playlist(playlist_id: str) -> list: #Esto debe devolver una lista de strings como [rola1-artista1, rola2-artista2]
    tracks = list()
    try:
        results = sp.playlist_items(playlist_id)
        
        #Itera sobre cada elemento 
        for item in results['items']:
            track_info = item.get('track')
            
            if track_info:
                track_name = track_info['name']
                artist_names = ', '.join([artist['name'] for artist in track_info['artists']])
                
                tracks.append(f'{track_name} - {artist_names}')
        
    except Exception as e:
        print(f"Error en get_tracks_from_playlist: {e}")
        return []
    
    return tracks


@bot.command(name='stop')
async def stop_music(ctx):
    global queue, current_song #Obtener la variable global para que no se cree otra local dentro de la función
    voice_client = ctx.voice_client

        # Comprueba si el bot está conectado a un canal de voz
    if voice_client and voice_client.is_connected():
        # Detiene la reproducción actual
        voice_client.stop()
        
        # Limpia la cola de reproducción
        queue = []
        current_song = None
        
        # Se desconecta del canal de voz
        await voice_client.disconnect()
        
        await ctx.send("Adiós")
    else:
        await ctx.send("El bot no está en ningún canal de voz.")
        
@bot.command(name='pause')
async def pause_music(ctx):
    voice_client = ctx.voice_client
    
    # Comprueba si el bot está reproduciendo algo
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Música pausada. Usa /resume para continuar.")
    else:
        await ctx.send("No hay música sonando para pausar.")
        
@bot.command(name='resume')
async def resume_music(ctx):
    voice_client = ctx.voice_client
    
    # Comprueba si el bot está pausado
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Reanudando la música.")
    else:
        await ctx.send("No hay música pausada para reanudar.")
        
@bot.command(name='skip')
async def skip_song(ctx):
    voice_client = ctx.voice_client
    
    if voice_client and voice_client.is_playing():
        voice_client.stop()
    else:
        await ctx.send('No hay ninguna rola sonando para saltar')
        
@bot.command(name='playnext')
async def play_next(ctx, *, query: str):
    track_info = search_track(query)
    
    if not track_info:
            await ctx.send(f"No encontré ninguna canción que se llame '{query}'.")
            return     
         
    if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Primero métete a un canal de voz.")
                return        
    queue.insert(0, track_info)    
    await ctx.send(f"**{track_info}** se reproducirá a continuación.")
          
@bot.command(name='queue')
async def show_queue(ctx):
    voice_client = ctx.voice_client    
    if not voice_client or not voice_client.is_connected():
        await ctx.send("No estoy en ningún canal de voz.")
        return
    
    embed = discord.Embed(title="🎵 Cola de Reproducción 🎵", color=discord.Color.blue())
    
    if voice_client.is_playing():
        embed.add_field(name="▶️ Ahora Sonando", value=f'**{current_song}**', inline=False)
    
    if not queue:
        embed.description = "La cola está vacía, pon rolas pero ya."
    else:
        # Formatea la lista de canciones
        song_list = ""
        # Mostramos solo las primeras 10 canciones para no saturar el chat
        for i, song in enumerate(queue[:10]):
            song_list += f"**{i + 1}.** {song}\n"
        
        embed.description = song_list
        
        if len(queue) > 10:
            embed.set_footer(text=f"Y {len(queue) - 10} más...")

    await ctx.send(embed=embed)

@bot.command(name='clear')
async def clear_queue(ctx):
    global queue
    voice_client = ctx.voice_client
    if queue:
        voice_client.stop()
        queue = [] 
    else:
        ctx.send('La cola de reproducción ya está vacía')
    
bot.run(token)
