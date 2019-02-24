from celery import Celery

import requests
import datetime
import io, os
import re
import main
import apple
import random

import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)-2s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)

manager = Celery('telegram',broker='redis://smd:mThquQxrJbyVYVlmLLAmwzLd2t5vDWVO@redis-12274.c52.us-east-1-4.ec2.cloud.redislabs.com:12274')


class BotHandler(object):

    def __init__(self):
        self.token = '752979930:AAFhdyGx0CSOJ-m17wLGN0NhrxvpwCqCPoQ'
        self.token = '738408029:AAGdU7xFXn--qtRktVnk9J8zqz3mFmTYd_0' #unstable
        self.api_url = "https://api.telegram.org/bot{}/".format(self.token)

    def getUpdates(self, offset=None, timeout=30):

        method = 'getUpdates'
        params = {
            'timeout': timeout,
            'offset': offset
        }

        response = requests.get(self.api_url + method, params)
        try:
            return response.json()['result']
        except: return []

    def sendText(self, chat_id, text):

        params = {
            'chat_id': chat_id,
            'text': text
        }

        method = 'sendMessage'

        return requests.post(self.api_url + method, params)

    def sendHTML(self, chat_id, text):

        params = {
            'chat_id': chat_id,
            'parse_mode': 'HTML',
            'text': text,
        }

        method = 'sendMessage'

        return requests.post(self.api_url + method, params)


    def sendAudio(self, chat_id, name, artist, audio, thumb):

        method = 'sendAudio'

        files = {
            'audio': audio,
            'thumb':thumb
        }

        data = {
            'chat_id' : chat_id,
            'title': str(name),
            'performer':str(artist),
            'caption':f'<b>{str(artist)}</b> {str(name)}',
            'parse_mode':'HTML'
        }

        response = requests.post(
                        self.api_url + method,
                        files=files,
                        data=data
                    )
        #logging
        logging.info(f'SEND STATUS {response.status_code} {response.reason}')

        return response.status_code

    def sendPhoto(self, chat_id, photo, text):

        method = 'sendPhoto'

        files = {
            'photo': photo
        }

        data = {
            'chat_id' : chat_id,
            'caption':text,
            'parse_mode':'HTML'
        }

        response = requests.post(
                        self.api_url + method,
                        files=files,
                        data=data
                    )
        #logging
        logging.info(f'SEND STATUS {response.status_code} {response.reason}')

        return response.status_code


    def sendSticker(self, chat_id, sticker):

        method = 'sendSticker'

        files = {
            'sticker': sticker
        }

        data = {
            'chat_id' : chat_id,
        }

        response = requests.post(
                        self.api_url + method,
                        files=files,
                        data=data
                    )
        #logging
        logging.info(f'SEND STATUS {response.status_code} {response.reason}')

        return response.status_code

    def checkLastUpdates(self):

        result = self.getUpdates()

        if len(result) > 0:
            return result[-1]
        else:
            return False

class Controller(object):

    def __init__(self):
        self.bot = BotHandler()
        self.offset = None

        self.downloader = main.MusicDownloader()
        self.apple = apple.AppleMusic()

    def classify(self, message):

        if str(message).find('open.spotify.com') > 0:
            return 'link'

        elif str(message).find(':track:') > 0:
            return 'uri'

        elif str(message) == '/start':
            return 'start'

        else:
            return 'text'

    def getTrackFromShazam(self, message):

        slug = str(message).split('/')[-1].split('-')

        message = str(message).split('I used Shazam to discover ')[1]
        message = str(message).split('. https://www.shazam.com/track/')[0]
        message = message.replace("'",'')

        song, artist, title = message, [], []
        message = str(message).split(' ')

        count = 0
        for word in message:
            if str(word) == 'by':
                count+=1
        if count != 1:
            try:

                for word in message:
                    try:
                        if str(word).lower().find(slug[0]) > -1:
                            title.append(word)
                            slug.pop(0)

                        else:
                            artist.append(word)
                    except:
                        artist.append(word)

                artist = " ".join(artist[1:])
                title = " ".join(title)
                song = f"{artist} - {title}"

            except:pass
            return str(song).replace('&','')
        else:
            new = []
            [new.append(word if str(word) != 'by' else '-') for word in message]
            song = " ".join(new)
            song = str(song).replace('&','')
            return str(song)

    def convertToURI(self, link):
        return "spotify:track:" + str(str(link).split('/')[-1]).split('?')[0]

    def isIncorrect(self, text):
        r = re.compile("[а-яА-Я]+")
        text = str(text).split(' ')

        return True if len([w for w in filter(r.match, text)]) else False

    def controller(self, message, id):

        type = self.classify(message)

        #logging
        logging.info(f'TYPE [{type}] {message}')

        #start message
        if type == 'start':

            #logging
            logging.info('Sended hello message')

            self.bot.sendPhoto(
                chat_id=id,
                photo=open(f"Data/header1.png",'rb'),
                text=''
            )
            self.bot.sendPhoto(
                chat_id=id,
                photo=open(f"Data/header3.png",'rb'),
                text=''
            )
            self.bot.sendPhoto(
                chat_id=id,
                photo=open(f"Data/header5.png",'rb'),
                text=''
            )

            return True


        elif type == 'text':

            if str(message).find('I used Shazam to discover') > -1:
                #logging
                logging.info(f"SHAZAM SONG DETECTED")

                message = self.getTrackFromShazam(message)

                logging.info(f"NAME {message}")

            elif str(message).find('Мое открытие на Shazam:') > -1:
                #fix for russian lang
                new = str(message).split('Мое открытие на Shazam: ')[1]
                new = str(new).split('. https')[0]
                message = new
                #logging
                logging.info(f"NAME {message}")

            elif str(message).find('youtube.com/watch') > -1:
                #logging
                logging.info(f"YOUTUBE MUSIC DETECTED")

                link = 'http' + str(message).split('http')[-1]

                if str(message).find('music.') > -1:

                    self.downloader = main.MusicDownloader()

                    link = ''.join(str(link).split('music.')).split('&')[0]

                    #logging
                    logging.info(f"LINK {link}")

                    name = self.downloader.getYoutubeMusicInfo(link)
                    tags = self.downloader.getLastFMTags(name)

                    #logging
                    logging.info(f"NAME {name}")

                    try:
                        state, data = self.downloader.downloadFromYoutubeMusic(url=link, info=tags)

                        if state:

                            name = getCorrect(f'{data["artist"][0]} - {data["name"]}')
                            os.rename(
                                f"Downloads/{data['uri']}.mp3",
                                f"Downloads/{name}.mp3"
                            )

                            code = self.bot.sendAudio(
                                chat_id=id,
                                audio=open(f"Downloads/{name}.mp3",'rb'),
                                thumb=open(f"Downloads/{data['uri']}.png",'rb'),
                                name=f'{data["name"]}',
                                artist=f'{data["artist"][0]}'
                            )

                            if int(code) != 200:
                                try:
                                    os.rename(
                                        f"Downloads/{name}.mp3",
                                        f"Downloads/{data['uri']}.mp3"
                                    )

                                    code = self.bot.sendAudio(
                                        chat_id=id,
                                        audio=open(f"Downloads/{data['uri']}.mp3",'rb'),
                                        thumb=open(f"Downloads/{data['uri']}.png",'rb'),
                                        name=f'{data["name"]}',
                                        artist=f'{data["artist"][0]}'
                                    )
                                    os.remove(f"Downloads/{data['uri']}.mp3")
                                    #logging
                                    logging.info(f"DELETED Downloads/{data['uri']}.mp3")

                                    os.remove(f"Downloads/{data['uri']}.png")
                                    #logging
                                    logging.info(f'DELETED Downloads/{data["uri"]}.png')

                                    return True

                                except:
                                    #logging
                                    logging.warning(f'CODE {code}')
                                    self.bot.sendSticker(id,sticker=open(f"Data/s3.webp",'rb'),)
                                    self.bot.sendText(id,text='Something went wrong:(')

                                    return False


                            os.remove(f"Downloads/{name}.mp3")
                            #logging
                            logging.info(f"DELETED Downloads/{name}.mp3")

                            os.remove(f"Downloads/{data['uri']}.png")
                            #logging
                            logging.info(f"DELETED Downloads/{data['uri']}.png")


                        else:
                            #logging
                            logging.warning(f"This video is unavailable.")
                            self.bot.sendSticker(id,sticker=open(f"Data/s2.webp",'rb'),)
                            self.bot.sendText(id,text='This video is unavailable for me(')

                            return False

                    except:
                        try:
                            self.controller(name, id)
                        except:
                            #logging
                            logging.warning(f"This video is unavailable.")
                            self.bot.sendSticker(id,sticker=open(f"Data/s2.webp",'rb'),)
                            self.bot.sendText(id,text='This video is unavailable for me(')

                        return False

                    return True

                else:
                    logging.warning(f"YOUTUBE SONG DETECTED")
                    self.bot.sendSticker(id,sticker=open(f"Data/s5.webp",'rb'),)
                    self.bot.sendText(id,text='You need to use YouTube Music instead of YouTube.')

                return True

            elif str(message).find('youtu.be') > -1:
                logging.warning(f"YOUTUBE SONG DETECTED")
                self.bot.sendSticker(id,sticker=open(f"Data/s5.webp",'rb'),)
                self.bot.sendText(id,text='You need to use YouTube Music instead of YouTube.')
                return True

            elif str(message).find('itunes.apple.com') > 1:

                name = self.apple.getName(message)
                message = name
                if not name:
                    #logging
                    logging.error(f'SENDED "Couldn\'t find that" MESSAGE')
                    self.bot.sendSticker(id,sticker=open(f"Data/s3.webp",'rb'),)
                    self.bot.sendText(id,text='Couldn\'t find that:(')
                    return False

            state, data =  self.downloader.downloadBySearchQuery(message)

            #FIX
            if not state:
                #logging
                self.downloader = main.MusicDownloader()
                logging.warning(f'Restarting downloader')
                logging.warning(f'Trying do the same')

                state, data =  self.downloader.downloadBySearchQuery(message)


            if state:

                fixed_name = f'{data["artist"][0]} - {data["name"]}'
                fixed_name = data['uri']

                name = getCorrect(f'{data["artist"][0]} - {data["name"]}')
                os.rename(
                    f"Downloads/{data['uri']}.mp3",
                    f"Downloads/{name}.mp3"
                )

                code = self.bot.sendAudio(
                    chat_id=id,
                    audio=open(f"Downloads/{name}.mp3",'rb'),
                    thumb=open(f"Downloads/{data['uri']}.png",'rb'),
                    name=f'{data["name"]}',
                    artist=f'{data["artist"][0]}'
                )

                if int(code) != 200:

                    try:
                        os.rename(
                            f"Downloads/{name}.mp3",
                            f"Downloads/{data['uri']}.mp3"
                        )

                        code = self.bot.sendAudio(
                            chat_id=id,
                            audio=open(f"Downloads/{data['uri']}.mp3",'rb'),
                            thumb=open(f"Downloads/{data['uri']}.png",'rb'),
                            name=f'{data["name"]}',
                            artist=f'{data["artist"][0]}'
                        )
                        os.remove(f"Downloads/{data['uri']}.mp3")
                        #logging
                        logging.info(f"DELETED Downloads/{data['uri']}.mp3")

                        os.remove(f"Downloads/{data['uri']}.png")
                        #logging
                        logging.info(f'DELETED Downloads/{data["uri"]}.png')

                        return True

                    except:
                        #logging
                        logging.warning(f'CODE {code}')
                        self.bot.sendText(id,text='Something went wrong:(')

                        return False


                os.remove(f"Downloads/{name}.mp3")
                #logging
                logging.info(f"DELETED Downloads/{name}.mp3")

                os.remove(f"Downloads/{data['uri']}.png")
                #logging
                logging.info(f"DELETED Downloads/{data['uri']}.png")


            else:
                #logging
                logging.error(f'SENDED "Couldn\'t find that" MESSAGE')
                self.bot.sendSticker(id,sticker=open(f"Data/s3.webp",'rb'),)
                self.bot.sendText(id,text='Couldn\'t find that:(')
                return False
            return True


        elif type == 'link':

            #logging
            logging.info(f'Converted open.spotify.com link to spotify URI')

            message = self.convertToURI(message)


        #get data
        uri = str(message).split(':')[-1]
        data = self.downloader.getData(message)

        if not data:
            #logging
            logging.warning(f'Restarting downloader')
            logging.warning(f'Trying do the same')
            self.downloader = main.MusicDownloader()
            data = self.downloader.getData(message)

        if data:

            #logging
            logging.info(f'SONG  {data["artist"][0]} - {data["name"]}')

            if self.downloader.downloadBySpotifyUri(message):

                name = getCorrect(f'{data["artist"][0]} - {data["name"]}')
                os.rename(
                    f"Downloads/{data['uri']}.mp3",
                    f"Downloads/{name}.mp3"
                )


                code = self.bot.sendAudio(
                    chat_id=id,
                    audio=open(f"Downloads/{name}.mp3",'rb'),
                    thumb=open(f"Downloads/{uri}.png",'rb'),
                    name=f'{data["name"]}',
                    artist=f'{data["artist"][0]}'
                )


                if int(code) != 200:
                    try:
                        os.rename(
                            f"Downloads/{name}.mp3",
                            f"Downloads/{data['uri']}.mp3"
                        )

                        code = self.bot.sendAudio(
                            chat_id=id,
                            audio=open(f"Downloads/{data['uri']}.mp3",'rb'),
                            thumb=open(f"Downloads/{data['uri']}.png",'rb'),
                            name=f'{data["name"]}',
                            artist=f'{data["artist"][0]}'
                        )
                        os.remove(f"Downloads/{data['uri']}.mp3")
                        #logging
                        logging.info(f"DELETED Downloads/{data['uri']}.mp3")

                        os.remove(f"Downloads/{data['uri']}.png")
                        #logging
                        logging.info(f'DELETED Downloads/{data["uri"]}.png')

                        return True

                    except:
                        #logging
                        logging.warning(f'CODE {code}')
                        self.bot.sendSticker(id,sticker=open(f"Data/s3.webp",'rb'),)
                        self.bot.sendText(id,text='Something went wrong:(')

                        return False


                os.remove(f"Downloads/{name}.mp3")
                #logging
                logging.info(f'DELETED Downloads/{name}.mp3')

                os.remove(f"Downloads/{uri}.png")
                #logging
                logging.info(f'DELETED Downloads/{uri}.png')

                return True

        else:

            #logging
            logging.error(f'SENDED "Something went wrong" MESSAGE')
            self.bot.sendSticker(id,sticker=open(f"Data/s3.webp",'rb'),)
            self.bot.sendText(id,text='Couldn\'t find that:(')
            return False

    def worker(self,update):

        if 'message' in list(update.keys()):
            #in case of new message

            #get message data
            chat_id = update['message']['chat']['id']

            try:
                username = update['message']['chat']['username']
            except:
                username = 'unknown'

            if 'text' in list(update['message'].keys()):
                #skipping unsupported messages
                #get message
                message = update['message']['text']

                #logging
                logging.info(f'USER [{username}]')
                logging.info(f'MESSAGE {message}')


                try:

                    #start controller
                    self.controller(message, chat_id)

                except:
                    #logging
                    logging.error('ERROR IN CONTROLLER')

                    try:

                        self.downloader = main.MusicDownloader()
                        #restart controller
                        self.controller(message, chat_id)

                    except:

                        self.bot.sendSticker(chat_id, sticker=open(f"Data/s1.webp",'rb'))
                        self.bot.sendText(chat_id, 'Couldn\'t find that :(')

            else:
                #logging
                logging.warning('UNSUPPORTED MESSAGE')

                self.bot.sendSticker(chat_id, sticker=open(f"Data/s4.webp",'rb'))
                self.bot.sendText(chat_id, 'Wooops! Something went wrong.\nERROR CODE 42 - You are so funny!')


    def mainloop(self):
        while True:

            self.bot.getUpdates(self.offset)
            update = self.bot.checkLastUpdates()

            if update:
                update_id = update['update_id']

                self.worker.delay(update=update)


                self.offset = update_id + 1


def getCorrect(name):
    try:

        #check for incorrect words
        r = re.compile("[а-яА-Я]+")
        text = str(name).split(' ')

        status = True if len([w for w in filter(r.match, name)]) else False

        if status:
            return f'S{str(random.randint(1000000000,100000000000))}D'

        return re.sub(r"[\"#/@;:<>{}`+=~|.!?$%^&*№&]", string=name, repl='')

    except:

        return 'music'

@manager.task
def do(update):
    controller = Controller()
    controller.worker(update)
    del controller

def mainloop():

    offset = None
    bot = BotHandler()

    while True:

        bot.getUpdates(offset)
        update = bot.checkLastUpdates()

        if update:
            update_id = update['update_id']

            #celery task
            do.delay(update)

            offset = update_id + 1

if __name__ == '__main__':
    logging.info('Starting app')
    mainloop()