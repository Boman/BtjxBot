import json
import os
import time

from btjx import decimalencoder
import boto3

dynamodb = boto3.resource('dynamodb')


def unwatchPartieInDB(partieID, chatID, userID):
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
        UpdateExpression='DELETE partieIDs :partieID '
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
            ':updatedAt': timestamp,
        },
        UpdateExpression='DELETE chatUserIDs :chatUserID '
                         'SET updatedAt = :updatedAt',
        ReturnValues='UPDATED_OLD',
    )

    return "Okay I will no longer look out for your turns in the game {}.".format(partieID)
