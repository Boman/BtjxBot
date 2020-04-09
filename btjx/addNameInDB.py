import json
import os
import time

from btjx import decimalencoder
import boto3

dynamodb = boto3.resource('dynamodb')


def addNameInDB(playerName, chatID, userID):
    timestamp = int(time.time() * 1000)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result = table.update_item(
        Key={
            'idType': "playerName",
            'id': "{}:{}".format(chatID, userID)
        },
        ExpressionAttributeValues={
            ':playerName': {playerName},
            ':updatedAt': timestamp,
        },
        UpdateExpression='ADD playerNames :playerName '
                         'SET updatedAt = :updatedAt',
        ReturnValues='ALL_OLD',
    )

    try:
        beforeNames = ', '.join(result['Attributes']['playerNames'])
        return "Okay I will now look out for your turns: {} and {}".format(beforeNames, playerName)
    except:
        return "Okay I will now look out for your turns: {}.".format(playerName)


def removeNameInDB(playerName, chatID, userID):
    timestamp = int(time.time() * 1000)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result = table.update_item(
        Key={
            'idType': "playerName",
            'id': "{}:{}".format(chatID, userID)
        },
        ExpressionAttributeValues={
            ':playerName': {playerName},
            ':updatedAt': timestamp,
        },
        UpdateExpression='DELETE playerNames :playerName '
                         'SET updatedAt = :updatedAt',
        ReturnValues='ALL_OLD',
    )

    try:
        beforeNames = ', '.join(result['Attributes']['playerNames'])
        return "Okay I will no longer look out for your turns: {}, only: {}".format(playerName, beforeNames)
    except:
        return "Okay I will no longer look out for your turns: {}.".format(playerName)
