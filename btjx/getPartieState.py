import os
import json
import sys
import time
import traceback
from datetime import datetime

from btjx import decimalencoder
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "./vendored"))

import bs4, requests, humanize

from telegram import Update, Bot, ParseMode


def getPartieState(partieID, excludeUpdateChatIDs):
    partieUpdate, turn, turnUpdate, gameName = getPartieStateInDB(partieID)
    if partieUpdate < int((time.time() - 60) * 1000):
        partieUpdate, turn, turnUpdate, gameName = updatePartieState(partieID, excludeUpdateChatIDs, turn)

    since = humanize.naturaltime(datetime.fromtimestamp(float(turnUpdate) / 1000.0))
    updatedTime = humanize.naturaltime(datetime.fromtimestamp(float(partieUpdate) / 1000.0))
    return "<a href=\"http://www.boiteajeux.net/jeux/agr/partie.php?id={}\">{}</a>: {}'s turn, since {} (updated {})" \
        .format(partieID, gameName, turn, since, updatedTime)


def getPartieStateInDB(partieID):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result = table.get_item(
        Key={
            'idType': "partieState",
            'id': "{}".format(partieID)
        }
    )

    try:
        return (result['Item']['updatedAt'], result['Item']['turn'], result['Item']['turnUpdatedAt'], result['Item']['gameName'])
    except Exception:
        return (0, "", 0, "")


def updatePartieState(partieID, excludeUpdateChatIDs, previousTurn):
    turn, gameName = getPartieResponse(partieID)

    timestamp = int(time.time() * 1000)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    turnUpdatedAt = 0
    if turn == previousTurn:
        result = table.update_item(
            Key={
                'idType': "partieState",
                'id': "{}".format(partieID)
            },
            ExpressionAttributeValues={
                ':updatedAt': timestamp,
                ':gameName': gameName,
            },
            UpdateExpression='SET updatedAt = :updatedAt, '
                             'gameName = :gameName',
            ReturnValues='ALL_OLD',
        )
        try:
            turnUpdatedAt = result['Attributes']['turnUpdatedAt']
        except Exception:
            pass
    else:
        result = table.update_item(
            Key={
                'idType': "partieState",
                'id': "{}".format(partieID)
            },
            ExpressionAttributeValues={
                ':turn': turn,
                ':gameName': gameName,
                ':updatedAt': timestamp,
                ':turnUpdatedAt': timestamp,
            },
            UpdateExpression='SET turn = :turn, '
                             'gameName = :gameName, '
                             'updatedAt = :updatedAt, '
                             'turnUpdatedAt = :turnUpdatedAt',
            ReturnValues='ALL_OLD',
        )
        try:
            turnUpdatedAt = result['Attributes']['turnUpdatedAt']
        except Exception:
            pass
        informPlayersAboutTurn(partieID, turn, previousTurn, excludeUpdateChatIDs, gameName, turnUpdatedAt)

    return (timestamp, turn, turnUpdatedAt, gameName)


def informPlayersAboutTurn(partieID, turn, previousTurn, excludeUpdateChatIDs, gameName, turnUpdatedAt):
    updatedAt, chatUserIDs = getUsersByPartieInDB(partieID)

    TOKEN = os.environ['TELEGRAM_TOKEN']
    bot = Bot(token=TOKEN)

    for chatUserID in chatUserIDs:
        if chatUserID not in excludeUpdateChatIDs:
            names = getNamesForChatUserID(chatUserID)
            if turn in names:
                since = humanize.naturaltime(datetime.fromtimestamp(float(turnUpdatedAt) / 1000.0))
                text = "<a href=\"http://www.boiteajeux.net/jeux/agr/partie.php?id={}\">{}</a>: {}'s turn. Previously {}'s turn, since {}.".format(
                    partieID, gameName, turn, previousTurn, since)
                message = bot.send_message(chat_id=chatUserID.split(':')[0], text=text, parse_mode=ParseMode.HTML,
                                           disable_web_page_preview=True)
    return


def checkTurns():
    parties = getPartiesToUpdateInDB()
    for partie in parties:
        partieID = partie['id']
        partieUpdate, turn, turnUpdate, gameName = getPartieStateInDB(partieID)
        if partieUpdate < int((time.time() - 60) * 1000):
            partieUpdate, turn, turnUpdate, gameName = updatePartieState(partieID, [], turn)
    return


def getPartiesToUpdateInDB():
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result = table.query(
        KeyConditionExpression=Key('idType').eq('usersByPartie')
    )

    try:
        return result['Items']
    except Exception:
        return []


def getNamesForChatUserID(chatUserID):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result = table.get_item(
        Key={
            'idType': "playerName",
            'id': "{}".format(chatUserID)
        }
    )

    try:
        return result['Item']['playerNames']
    except Exception:
        return []


def getUsersByPartieInDB(partieID):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result = table.get_item(
        Key={
            'idType': "usersByPartie",
            'id': "{}".format(partieID)
        }
    )

    try:
        return (result['Item']['updatedAt'], result['Item']['chatUserIDs'])
    except Exception:
        return (0, [""])


def getPartieResponse(partieID):
    turn = "nobody"
    gameName = "no Name"
    try:
        partieURL = 'http://www.boiteajeux.net/jeux/agr/partie.php?id={}'.format(partieID)
        getPage = requests.get(partieURL)
        getPage.raise_for_status()  # if error it will stop the program
        site = bs4.BeautifulSoup(getPage.text, 'html.parser')
        clInfo = site.select('.clInfo')
        turn = clInfo[0].get_text().split("'s")[1].strip()
        dvEnteteInfo = site.select('#dvEnteteInfo')
        gameName = dvEnteteInfo[0].get_text(strip=True).split("\"")[1]
    except Exception as ex:
        print(partieID)
        print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
    return turn, gameName
