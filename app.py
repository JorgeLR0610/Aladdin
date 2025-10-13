import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

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


def get_playlist_id(url: str) -> str: #https://open.spotify.com/playlist/4E5ng7UkIH9tWiL2ZAopCk
    id = url[34:]
    return id

@bot.command(name='playlist') #Para cuando en el chat pongan /playlist <link de la playlist>
async def play_playlist(ctx, *, url: str): #ctx es el contexto, proporciona info de donde se origino el comando (servidor, usuario etc)
    await ctx.send('Procesando playlist')
    
    try:
        playlist_id = get_playlist_id(url)
        
        if not playlist_id:
            await ctx.send("Ese link no jala Pa; tiene que ser el link de una playlist.")
            return
        
        track_list = get_tracks_from_playlist(playlist_id)
        
        if not track_list:
            await ctx.send("Esa playlist está vacía, no te pases de cangreburguer.")
            return
        
        if ctx.author.voice is None:
            await ctx.send("Primero métete a un canal de voz y luego ya.")
            return
        
        
        await ctx.send(f"Gucci, se encontraron {len(track_list)} rolas.")
        
        #A partir de aquí, lógica para añadir a la cola del bot y empezar a reproducir
        
    except Exception as e:
        await ctx.send(f'Error al cargar la playlist: {e}')
        print(f'Error al cargar la playlist: {e}')


def get_tracks_from_playlist(playlist_id: str) -> list: #Esto debe devolver una lista de strings como [rola1-artista1, rola2-artista2]
    tracks = list()
    #Código de la búsqueda...
    return tracks
