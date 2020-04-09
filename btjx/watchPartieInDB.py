import json
import os
import time

from btjx import decimalencoder
import boto3

dynamodb = boto3.resource('dynamodb')


def watchPartieInDB(partieID, chatID, userID):
    timestamp = int(time.time() * 1000)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result = table.update_item(
        Key={
            'idType': "partiesByUser",
            'id': "{}:{}".format(chatID, userID)
        },
        ExpressionAttributeValues={
            ':partieID': {partieID},
            ':updatedAt': timestamp,
        },
        UpdateExpression='ADD partieIDs :partieID '
                         'SET updatedAt = :updatedAt',
        ReturnValues='UPDATED_OLD',
    )

    result = table.update_item(
        Key={
            'idType': "usersByPartie",
            'id': "{}".format(partieID)
        },
        ExpressionAttributeValues={
            ':chatUserID': {"{}:{}".format(chatID, userID)},
            ':updatedAt': timestamp
        },
        UpdateExpression='ADD chatUserIDs :chatUserID '
                         'SET updatedAt = :updatedAt',
        ReturnValues='UPDATED_OLD',
    )

    return "Okay I will now look out for your turns in the game {}.".format(partieID)
